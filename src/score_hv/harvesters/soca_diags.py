#!/usr/bin/env python
"""
Copyright 2026 NOAA
All rights reserved.

Harvester for descriptive statistics from SOCA/JEDI ocean observation-space
diagnostic files ("ocean diags", IODA v3 netCDF layout), e.g. the files in
gdas.YYYYMMDD/HH/analysis/ocean/diags/.

One HarvestedData record is returned for every requested statistic of every
variable, depth bin and data group (ObsValue, oman, ombg, ObsError) found in
each file.
"""
import logging
import os
import re
from collections import namedtuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from numbers import Real

import netCDF4
import numpy as np

from score_hv.config_base import ConfigInterface

logger = logging.getLogger(__name__)

HARVESTER_NAME = 'soca_diags'

VALID_STATISTICS = ('mean', 'median', 'StdDev', 'minimum', 'maximum', 'rms', 'count')
# alternate spellings accepted in a request; records use VALID_STATISTICS names
STATISTIC_ALIASES = {'RMS': 'rms', 'n': 'count', 'nobs': 'count'}

VALID_VARIABLES = ('seaSurfaceTemperature',
                   'seaIceFraction',
                   'absoluteDynamicTopography',
                   'seaSurfaceSalinity',
                   'waterTemperature',
                   'salinity')
# legacy short names accepted in a request
VARIABLE_ALIASES = {'sst': 'seaSurfaceTemperature', 'icec': 'seaIceFraction'}

VALID_FILE_TYPE_IDS = ('sst', 'icec', 'adt', 'sss', 'wod', 'insitu', 'icoads')
DATA_GROUPS = ('ObsValue', 'oman', 'ombg', 'ObsError')
DEFAULT_STATISTICS = ('mean',)
DEFAULT_QC_THRESHOLD = 0.0
DEFAULT_TIME_UNITS = 'seconds since 1970-01-01T00:00:00Z'
# when the cycle is not recorded, filetime is the file median time rounded to
# the nearest synoptic time (00, 06, 12, 18 UTC)
SYNOPTIC_INTERVAL = timedelta(hours=6)

HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'sensor',
                                             'satellite',
                                             'level',
                                             'variables',
                                             'group',
                                             'longname',
                                             'units',
                                             'statistics',
                                             'value',
                                             'filetime',
                                             'mediantime',
                                             'file_region',
                                             'QC_threshold',
                                             'ocean_depth_bins'])

# altimeter id (adt_<source>_<id>) -> (satellite, sensor)
ADT_PLATFORMS = {
    'all': ('misc', 'misc'),
    'e1': ('ers1', 'Radar Altimeter'),
    'e2': ('ers2', 'Radar Altimeter'),
    'j1': ('jason1', 'Poseidon 2'),
    'j2': ('jason2', 'Poseidon 3'),
    'j3': ('jason3', 'Poseidon 3B'),
    '3a': ('Sentinel-3A', 'Synthetic aperture Radar Altimeter'),
    '3b': ('Sentinel-3B', 'Synthetic aperture Radar Altimeter'),
    '6a': ('Sentinel-6A', 'Poseidon 4'),
    'sa': ('saral', 'AltiKa'),
    'sw': ('swot', 'KaRIN'),
    'c2': ('cryosat2', 'SAR Interferometer Radar Altimeter'),
    'tx': ('topex-poseidon', 'NASA Radar Altimeter'),
    'n1': ('envisat', 'Radar Altimeter - 2'),
    'g1': ('gfo', 'GFO-Radar Altimeter'),
}
# sea ice product/sensor token -> (satellite, sensor)
ICEC_PLATFORMS = {'amsr2': ('gcom-w1', 'amsr2'),
                  'nsidc': ('dmsp', 'ssmis'),
                  'ssmis': ('dmsp', 'ssmis')}
HEMISPHERES = {'north': 'nh', 'nh': 'nh', 'south': 'sh', 'sh': 'sh'}
# sst product token -> (sensor, satellite, default level)
SST_PRODUCTS = {'nggodas': ('avhrr', 'metop', None),
                'odyssea': ('multiple', 'ODYSSEA', 'l3'),
                'amsr2': ('amsr2', 'gcom-w1', None)}
# sst sensor token -> {platform token: satellite}
SST_SATELLITES = {'avhrr': {'ma': 'metop-a', 'mb': 'metop-b', 'mc': 'metop-c'},
                  'viirs': {'npp': 'npp', 'snpp': 'npp', 'n20': 'n20', 'n21': 'n21'}}
# GDASApp spells the AVHRR full-resolution (FRAC) product 'avhrrf'
SST_SENSOR_ALIASES = {'avhrrf': 'avhrr'}
# data-source prefixes that may precede the file type, e.g. rads_adt_j3.nc
FILE_TYPE_PREFIXES = ('rads',)
SST_REGIONS = {'natl': 'North Atlantic',
               'satl': 'South Atlantic',
               'gom': 'Gulf of Mexico',
               'arctic': 'Arctic'}
WOD_PARAMETERS = ('t', 's')

# (longname, units) of WOD variables, which carry no units attribute
WOD_VARIABLES = {'waterTemperature': ('waterTemperature', 'DegC'),
                 'seaSurfaceTemperature': ('waterTemperature', 'DegC'),
                 'salinity': ('Practical Salinity Scale', 'PSS')}
DEFAULT_UNITS = {'icec': '1', 'adt': 'm', 'sss': 'psu'}
CELSIUS_UNITS = ('degc', 'deg_c', 'celsius', 'degree_celsius', 'degrees_celsius')
KELVIN_UNITS = ('k', 'degk', 'deg_k', 'kelvin')

_LEVEL_RE = re.compile(r'l[1-4][a-z]?')
_NOAA_RE = re.compile(r'noaa(\d{2})')
_CYCLE_RE = re.compile(r'\d{10}')
# a <run>.YYYYMMDD/HH directory, e.g. gdas.20230201/12
_PATH_CYCLE_RE = re.compile(r'[^/\\]\.(\d{8})[/\\](\d{2})(?=[/\\]|$)')


def split_filename(filename):
    """Split a SOCA diag file name into lower-case tokens and its cycle time.

    The .nc/.nc4 extension and an optional .YYYYMMDDHH cycle suffix are
    removed and the rest of the base name is split on underscores, e.g.
    'wod_t_pfl.2023080612.nc' -> (['wod', 't', 'pfl'], datetime(2023, 8, 6, 12)).
    The cycle is None when the name has no cycle suffix.
    """
    stem = os.path.basename(os.fspath(filename))
    root, ext = os.path.splitext(stem)
    if ext.lower() in ('.nc', '.nc4'):
        stem = root

    cycle = None
    root, ext = os.path.splitext(stem)
    if _CYCLE_RE.fullmatch(ext[1:]):
        try:
            cycle = datetime.strptime(ext[1:], '%Y%m%d%H')
            stem = root
        except ValueError:
            pass
    return stem.lower().split('_'), cycle


def _find_level(tokens, default):
    return next((t for t in tokens[1:] if _LEVEL_RE.fullmatch(t)), default)


def _parse_adt(tokens):
    satellite, sensor = ADT_PLATFORMS.get(tokens[-1] if len(tokens) > 1 else None,
                                          ('Unknown', 'Unknown'))
    return dict(sensor=sensor, satellite=satellite, level=None, file_region='global')


def _parse_icec(tokens):
    names = [t for t in tokens[1:]
             if not _LEVEL_RE.fullmatch(t) and t not in HEMISPHERES]
    platform = next((ICEC_PLATFORMS[t] for t in names if t in ICEC_PLATFORMS), None)
    if platform:
        satellite, sensor = platform
    else:
        sensor = names[0] if names else 'Unknown'
        satellite = names[1] if len(names) > 1 else 'Unknown'
    file_region = next((HEMISPHERES[t] for t in tokens[1:] if t in HEMISPHERES), 'global')
    return dict(sensor=sensor, satellite=satellite, level=_find_level(tokens, None),
                file_region=file_region)


def _parse_sst(tokens):
    names = [t for t in tokens[1:]
             if not _LEVEL_RE.fullmatch(t) and t not in SST_REGIONS]
    sensor = names[0] if names else 'unknown'
    sensor = SST_SENSOR_ALIASES.get(sensor, sensor)
    satellite = names[1] if len(names) > 1 else 'unknown'
    default_level = 'unknown'
    noaa = _NOAA_RE.fullmatch(sensor)
    if sensor in SST_PRODUCTS:
        sensor, satellite, product_level = SST_PRODUCTS[sensor]
        default_level = product_level or default_level
    elif noaa:
        sensor, satellite = 'avhrr', f'n{noaa.group(1)}'
    elif sensor in SST_SATELLITES:
        noaa = _NOAA_RE.fullmatch(satellite)
        satellite = SST_SATELLITES[sensor].get(
            satellite, f'n{noaa.group(1)}' if noaa else satellite)
    file_region = next((SST_REGIONS[t] for t in tokens[1:] if t in SST_REGIONS), 'global')
    return dict(sensor=sensor, satellite=satellite,
                level=_find_level(tokens, default_level), file_region=file_region)


def _parse_sss(tokens):
    names = [t for t in tokens[1:] if not _LEVEL_RE.fullmatch(t)]
    return dict(sensor=names[0] if names else 'Unknown',
                satellite=names[1] if len(names) > 1 else 'Unknown',
                level=_find_level(tokens, None), file_region='global')


def _parse_wod(tokens):
    if len(tokens) < 3 or tokens[1] not in WOD_PARAMETERS:
        return None
    return dict(sensor=tokens[2], satellite=None, level=None, file_region='global')


def _parse_insitu(tokens):
    # insitu_<profile|surface>_<platform> or
    # insitu_<temp|salt>_<profile|surface>_<platform>; the sensor is the platform
    if len(tokens) < 3:
        return None
    return dict(sensor=tokens[-1], satellite=None, level=None, file_region='global')


def _parse_icoads(tokens):
    return dict(sensor='misc_icoads', satellite=None, level=None, file_region='global')


_FILENAME_PARSERS = {'adt': _parse_adt,
                     'icec': _parse_icec,
                     'sst': _parse_sst,
                     'sss': _parse_sss,
                     'wod': _parse_wod,
                     'insitu': _parse_insitu,
                     'icoads': _parse_icoads}


def parse_filename(filename):
    """Describe the observations in a SOCA diag file from its file name.

    Supported names (an optional .YYYYMMDDHH cycle may precede .nc/.nc4):
        [rads_]adt[_<source>]_<altimeter>   e.g. adt_glore_j3.nc, rads_adt_j3.nc
        icec_<sensor|product>[_<platform>][_<level>][_<north|south|nh|sh>]
                                     e.g. icec_amsr2_north.nc, icec_nsidc_sh.nc
        sst_<sensor|product>[_<platform>][_<level>][_<region>]
                                     e.g. sst_viirs_n20_l3u.nc, sst_odyssea.nc
        sss_<sensor>[_<platform>][_<level>]
        wod_<t|s>_<platform>         e.g. wod_t_pfl.nc (World Ocean Database)
        insitu_[<temp|salt>_]<profile|surface>_<platform>
                                     e.g. insitu_profile_argo.nc4,
                                     insitu_temp_surface_drifter.nc
        icoads_<...>

    Returns a dict with keys file_type, sensor, satellite, level, file_region
    and cycle, or None when the name does not match a supported pattern.
    """
    tokens, cycle = split_filename(filename)
    if (len(tokens) > 1 and tokens[0] in FILE_TYPE_PREFIXES
            and tokens[1] in _FILENAME_PARSERS):
        tokens = tokens[1:]
    file_type = tokens[0]
    if file_type not in _FILENAME_PARSERS:
        return None
    info = _FILENAME_PARSERS[file_type](tokens)
    if info is None:
        return None
    info.update(file_type=file_type, cycle=cycle)
    return info


def get_variable_metadata(file_type, var_name, units=None, mean_value=None):
    """Return the (longname, units) reported for a harvested variable.

    Parameters:
        file_type: first token of the file name ('sst', 'wod', ...)
        var_name: IODA variable name, e.g. 'seaSurfaceTemperature'
        units: units attribute of the ObsValue variable, if it has one
        mean_value: mean of the valid ObsValue values, used to tell Celsius
                    from Kelvin for SST files without a units attribute

    A units attribute takes precedence; Celsius spellings (degC, Celsius, ...)
    are reported as 'DegC', Kelvin spellings as 'DegK' and anything else as
    given. Without a units attribute the units follow from the file type:
    WOD temperature 'DegC' and salinity 'PSS', sea ice fraction '1', ADT 'm',
    SSS 'psu', and SST 'DegC' (mean < 200) or 'DegK'. The longname is the
    variable name, except for WOD files.
    """
    if file_type == 'wod':
        longname, default_units = WOD_VARIABLES.get(var_name, (var_name, 'Unknown'))
    else:
        longname, default_units = var_name, DEFAULT_UNITS.get(file_type, 'Unknown')
        if file_type == 'sst' and mean_value is not None:
            default_units = 'DegC' if mean_value < 200 else 'DegK'

    units = str(units).strip() if units is not None else ''
    if not units:
        return longname, default_units
    if units.lower() in CELSIUS_UNITS:
        return longname, 'DegC'
    if units.lower() in KELVIN_UNITS:
        return longname, 'DegK'
    return longname, units


def _is_number(value):
    return isinstance(value, Real) and not isinstance(value, bool)


def normalize_depth_bins(ocean_depth_bins):
    """Convert the ocean_depth_bins request into a list of (lo, hi) bins.

    Depths are in meters (positive down) and each bin is half open,
    lo <= depth < hi. Two formats are accepted:

      * increasing bin edges, e.g. [0, 10, 50, 100] -> [(0, 10), (10, 50), (50, 100)]
      * [lo, hi] pairs, e.g. [[0, 20], [20, 100], [0, 100]] (pairs may overlap)

    None, [] and [None] request no depth binning and return [None].

    Raises:
        ValueError: for any other format, or a bin with lo >= hi.
    """
    if ocean_depth_bins is None:
        return [None]
    if isinstance(ocean_depth_bins, (str, bytes)) or \
            not isinstance(ocean_depth_bins, (list, tuple)):
        raise ValueError(f'ocean_depth_bins must be a list, got {ocean_depth_bins!r}')
    if len(ocean_depth_bins) == 0 or list(ocean_depth_bins) == [None]:
        return [None]

    if all(_is_number(edge) for edge in ocean_depth_bins):
        if len(ocean_depth_bins) < 2:
            raise ValueError('ocean_depth_bins needs at least two bin edges, '
                             f'got {ocean_depth_bins!r}')
        bins = list(zip(ocean_depth_bins[:-1], ocean_depth_bins[1:]))
    elif all(isinstance(pair, (list, tuple)) and len(pair) == 2 and
             all(_is_number(edge) for edge in pair) for pair in ocean_depth_bins):
        bins = [tuple(pair) for pair in ocean_depth_bins]
    else:
        raise ValueError('ocean_depth_bins must be a list of bin edges, e.g. '
                         '[0, 10, 50], or of [lo, hi] pairs, e.g. [[0, 10], [10, 50]]; '
                         f'got {ocean_depth_bins!r}')

    for lo, hi in bins:
        if not lo < hi:
            raise ValueError(f'invalid depth bin ({lo}, {hi}): lower edge must be '
                             'less than upper edge')
    return bins


def compute_statistics(values, statistics):
    """Compute the requested statistics of a 1-D array of valid values.

    StdDev is the sample standard deviation (ddof=1) and rms is
    sqrt(mean(values**2)). Statistics that are undefined for the sample size
    (anything but count for an empty sample, StdDev for a single value) are
    returned as None.
    """
    values = np.asarray(values, dtype=np.float64)
    n = int(values.size)
    functions = {'mean': np.mean,
                 'median': np.median,
                 'StdDev': lambda x: np.std(x, ddof=1),
                 'minimum': np.min,
                 'maximum': np.max,
                 'rms': lambda x: np.sqrt(np.mean(np.square(x)))}
    results = dict()
    for statistic in statistics:
        if statistic == 'count':
            results[statistic] = n
        elif n == 0 or (statistic == 'StdDev' and n < 2):
            results[statistic] = None
        else:
            results[statistic] = float(functions[statistic](values))
    return results


def select_qc_group(dataset, group, var_name):
    """Name of the EffectiveQC group used to filter `group`, or None.

    oman (observation minus analysis) is filtered with EffectiveQC1, the QC of
    the analysis iteration; ObsValue, ombg and ObsError with EffectiveQC0, the
    QC of the background iteration. If the preferred group (or its variable) is
    missing, the next EffectiveQC* group that has the variable is used.
    """
    preferred = ['EffectiveQC1', 'EffectiveQC0'] if group == 'oman' else ['EffectiveQC0']
    others = sorted(name for name in dataset.groups
                    if name.startswith('EffectiveQC') and name not in preferred)
    for name in preferred + others:
        if name in dataset.groups and var_name in dataset.groups[name].variables:
            return name
    return None


def read_float(variable):
    """Read a netCDF variable as float64 with NaN at fill and invalid values."""
    data = np.ma.masked_invalid(np.ma.asarray(variable[:], dtype=np.float64))
    return np.ma.filled(data, np.nan)


def median_datetime(times, mask, units, calendar='standard'):
    """Median of the selected numeric times as a datetime, floored to the second.

    Parameters:
        times: float array of MetaData/dateTime values (NaN where missing)
        mask: boolean array selecting the observations to use
        units, calendar: CF time units and calendar of the dateTime variable

    Returns None when no valid time is selected.
    """
    selected = times[mask & np.isfinite(times)]
    if selected.size == 0:
        return None
    median = netCDF4.num2date(float(np.median(selected)), units=units, calendar=calendar,
                              only_use_cftime_datetimes=False,
                              only_use_python_datetimes=True)
    # num2date returns a cftime.real_datetime subclass; report a plain datetime
    return datetime(median.year, median.month, median.day,
                    median.hour, median.minute, median.second)


def nearest_synoptic_time(time):
    """Round a datetime to the nearest synoptic time (00, 06, 12 or 18 UTC)."""
    midnight = datetime(time.year, time.month, time.day)
    intervals = int(np.floor((time - midnight) / SYNOPTIC_INTERVAL + 0.5))
    return midnight + intervals * SYNOPTIC_INTERVAL


def path_cycle(filename):
    """Cycle of a <run>.YYYYMMDD/HH directory in the file path, or None.

    e.g. .../gdas.20230201/12/analysis/ocean/diags/sst_odyssea.nc -> 2023-02-01 12Z.
    The innermost such directory is used.
    """
    directory = os.path.dirname(os.path.abspath(os.fspath(filename)))
    for match in reversed(list(_PATH_CYCLE_RE.finditer(directory))):
        try:
            return datetime.strptime(match.group(1) + match.group(2), '%Y%m%d%H')
        except ValueError:
            continue
    return None


def attribute_cycle(dataset):
    """Cycle of the YYYYMMDDHH date_time global attribute, or None."""
    value = getattr(dataset, 'date_time', None)
    try:
        return datetime.strptime(f'{int(value):010d}', '%Y%m%d%H')
    except (TypeError, ValueError):
        return None


def analysis_cycle(filename, dataset, file_info, file_mediantime):
    """Analysis cycle reported as filetime, from the first available of:

    1. the .YYYYMMDDHH cycle in the file name,
    2. a <run>.YYYYMMDD/HH directory in the file path (e.g. gdas.20230201/12),
    3. the YYYYMMDDHH date_time global attribute,
    4. the median time of the whole file rounded to the nearest synoptic time.

    Raises:
        ValueError: if none is available (no cycle and no valid times).
    """
    cycle = file_info['cycle'] or path_cycle(filename) or attribute_cycle(dataset)
    if cycle is not None:
        return cycle
    if file_mediantime is None:
        raise ValueError(f'no cycle in the name, path or date_time attribute of {filename} '
                         'and no valid MetaData/dateTime to infer it from')
    cycle = nearest_synoptic_time(file_mediantime)
    logger.info('%s: no cycle recorded; using the median time %s rounded to %s',
                filename, file_mediantime, cycle)
    return cycle


def depth_bin_mask(depth, depth_bin, size):
    """Boolean mask of the observations with lo <= depth < hi.

    depth_bin None selects all `size` observations; observations with a
    missing depth fall outside every bin.
    """
    if depth_bin is None:
        return np.ones(size, dtype=bool)
    lo, hi = depth_bin
    with np.errstate(invalid='ignore'):
        return np.isfinite(depth) & (depth >= lo) & (depth < hi)


@dataclass
class SOCADiagsConfig(ConfigInterface):
    """Validated request for the soca_diags harvester.

    Request keys (see the README for an example):
        filenames: SOCA diag file paths (a single path string is accepted)
        statistics: subset of VALID_STATISTICS (aliases RMS, n and nobs are
                    accepted), default ['mean']
        variables: subset of VALID_VARIABLES (aliases sst and icec are
                   accepted), default: every variable in each file
        QC_threshold: use observations whose EffectiveQC flag is <=
                      QC_threshold, default 0; None turns QC filtering off
        ocean_depth_bins: depth bins in meters, see normalize_depth_bins;
                          default: no depth binning
    """
    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.set_config()

    def set_config(self):
        """Set the configuration variables from the request dictionary."""
        if self.config_data is None:
            self.config_data = dict()
        self.set_filenames()
        self.set_stats()
        self.set_variables()
        self.set_qc_threshold()
        self.set_ocean_depth_bins()

    def set_filenames(self):
        filenames = self.config_data.get('filenames') or []
        if isinstance(filenames, (str, os.PathLike)):
            filenames = [filenames]
        self.harvest_filenames = [os.fspath(filename) for filename in filenames]

    @staticmethod
    def _validate(requested, valid, aliases, kind):
        if isinstance(requested, str):
            requested = [requested]
        validated = list()
        for item in requested:
            name = str(item).strip()
            name = aliases.get(name, name)
            if name not in valid:
                raise KeyError(f"'{item}' is not a supported {kind} to harvest from "
                               "the SOCA diag files. Please reconfigure the input "
                               f"dictionary using only the following {kind}s: "
                               f"{valid!r} (or aliases {list(aliases)!r})")
            if name not in validated:
                validated.append(name)
        return validated

    def set_stats(self):
        """Set the statistics specified by the config dict."""
        requested = self.config_data.get('statistics') or list(DEFAULT_STATISTICS)
        self.stats = self._validate(requested, VALID_STATISTICS, STATISTIC_ALIASES,
                                    'statistic')

    def set_variables(self):
        """Set the variables specified by the config dict; [] means all."""
        requested = self.config_data.get('variables') or []
        self.variables = self._validate(requested, VALID_VARIABLES, VARIABLE_ALIASES,
                                        'variable')

    def set_qc_threshold(self):
        threshold = self.config_data.get('QC_threshold', DEFAULT_QC_THRESHOLD)
        if threshold is not None and not _is_number(threshold):
            raise ValueError(f'QC_threshold must be a number or None, got {threshold!r}')
        self.qc_threshold = threshold

    def set_ocean_depth_bins(self):
        self.ocean_depth_bins = normalize_depth_bins(self.config_data.get('ocean_depth_bins'))

    def get_stats(self):
        """Return the list of validated statistics."""
        return self.stats

    def get_variables(self):
        """Return the list of validated variables ([] means all)."""
        return self.variables


@dataclass
class SOCADiagsHv(object):
    """Harvester dataclass used to compute statistics from SOCA ocean diag files.

    Parameters:
    -----------
    config: SOCADiagsConfig object holding the validated request

    Methods:
    --------
    get_data: return a list of HarvestedData named tuples
    """
    config: SOCADiagsConfig = field(default_factory=SOCADiagsConfig)

    def get_data(self):
        """Harvest the requested statistics from every requested file.

        Files whose names do not match a supported pattern are skipped with a
        warning; see parse_filename.

        Raises:
            FileNotFoundError: if a requested file does not exist.
        """
        harvested_data = list()
        for filename in self.config.harvest_filenames:
            if not os.path.isfile(filename):
                raise FileNotFoundError(f'SOCA diag file not found: {filename}')
            file_info = parse_filename(filename)
            if file_info is None:
                logger.warning('%s is not a supported SOCA diag file name; skipping it',
                               filename)
                continue
            with netCDF4.Dataset(filename, 'r') as dataset:
                harvested_data.extend(self._harvest_dataset(filename, dataset, file_info))
        return harvested_data

    def _qc_pass(self, dataset, group, var_name, size, filename, cache):
        """Boolean mask of observations passing QC (missing QC flags fail)."""
        threshold = self.config.qc_threshold
        if threshold is None:
            return np.ones(size, dtype=bool)
        qc_group = select_qc_group(dataset, group, var_name)
        if qc_group is None:
            logger.warning('no EffectiveQC group has %s in %s; QC_threshold is not '
                           'applied to %s', var_name, filename, group)
            return np.ones(size, dtype=bool)
        if qc_group not in cache:
            qc_flags = read_float(dataset.groups[qc_group].variables[var_name])
            with np.errstate(invalid='ignore'):
                cache[qc_group] = qc_flags <= threshold
        return cache[qc_group]

    def _harvest_dataset(self, filename, dataset, file_info):
        """Harvest the records of one open SOCA diag dataset.

        filetime is the analysis cycle of the file (see analysis_cycle).
        For each variable, depth bin and data group, the statistics and the
        median time (mediantime) are computed from the same observations:
        those with a valid value that pass QC and lie inside the depth bin.
        When no observation is left only count (0) is reported, with the
        median time of the whole file as mediantime (filetime if the file has
        no valid times).
        """
        for group in ('MetaData', 'ObsValue'):
            if group not in dataset.groups:
                raise KeyError(f"group '{group}' missing from SOCA diag file {filename}")
        metadata = dataset.groups['MetaData']
        if 'dateTime' not in metadata.variables:
            raise KeyError(f"MetaData/dateTime missing from SOCA diag file {filename}")

        time_var = metadata.variables['dateTime']
        time_units = getattr(time_var, 'units', DEFAULT_TIME_UNITS)
        calendar = getattr(time_var, 'calendar', 'standard')
        times = read_float(time_var)
        file_mediantime = median_datetime(times, np.ones(times.size, dtype=bool),
                                          time_units, calendar)
        filetime = analysis_cycle(filename, dataset, file_info, file_mediantime)

        depth = read_float(metadata.variables['depth']) if 'depth' in metadata.variables \
            else None
        depth_bins = self.config.ocean_depth_bins if depth is not None else [None]

        harvested_data = list()
        obs_group = dataset.groups['ObsValue']
        for var_name in obs_group.variables:
            if self.config.variables and var_name not in self.config.variables:
                continue

            qc_cache = dict()
            group_data = dict()
            for group in DATA_GROUPS:
                if group not in dataset.groups or \
                        var_name not in dataset.groups[group].variables:
                    continue
                values = read_float(dataset.groups[group].variables[var_name])
                usable = np.isfinite(values) & self._qc_pass(
                    dataset, group, var_name, values.size, filename, qc_cache)
                group_data[group] = (values, usable)

            obs_values = group_data['ObsValue'][0]
            valid_obs = obs_values[np.isfinite(obs_values)]
            longname, units = get_variable_metadata(
                file_info['file_type'], var_name,
                getattr(obs_group.variables[var_name], 'units', None),
                float(np.mean(valid_obs)) if valid_obs.size else None)

            for depth_bin in depth_bins:
                in_bin = depth_bin_mask(depth, depth_bin, obs_values.size)
                for group, (values, usable) in group_data.items():
                    used = usable & in_bin
                    statistics = compute_statistics(values[used], self.config.stats)
                    mediantime = median_datetime(times, used, time_units, calendar) or \
                        file_mediantime or filetime
                    for statistic, value in statistics.items():
                        if value is None:
                            continue
                        harvested_data.append(HarvestedData(
                            filenames=filename,
                            sensor=file_info['sensor'],
                            satellite=file_info['satellite'],
                            level=file_info['level'],
                            variables=var_name,
                            group=group,
                            longname=longname,
                            units=units,
                            statistics=statistic,
                            value=value,
                            filetime=filetime,
                            mediantime=mediantime,
                            file_region=file_info['file_region'],
                            QC_threshold=self.config.qc_threshold,
                            ocean_depth_bins=depth_bin))
        return harvested_data
