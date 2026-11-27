#!/usr/bin/env python
"""Unit tests of the soca_diags harvester that need no external test data.

The harvests read small IODA-layout diag files written to a temporary
directory, so every expected value below can be checked by hand.
"""
import logging
from datetime import datetime, timedelta
from math import sqrt

import netCDF4
import numpy as np
import pytest

from score_hv import hv_registry
from score_hv.harvester_base import harvest
from score_hv.harvesters.soca_diags import (SOCADiagsConfig,
                                            get_variable_metadata,
                                            normalize_depth_bins,
                                            parse_filename)

GROUPS = ('ObsValue', 'oman', 'ombg', 'ObsError')
TIME_UNITS = 'seconds since 2023-01-01T00:00:00Z'

# a WOD temperature file with six observations
WOD_DEPTH = [0, 5, 10, 10, np.nan, 50]
WOD_VALUES = {'ObsValue': [1, 2, 3, np.nan, 5, 6],
              'oman': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
              'ombg': [-1, -2, -3, -4, -5, -6],
              'ObsError': [0.5] * 6}
WOD_QC = {'EffectiveQC0': [0, 0, 0, 0, 0, 19],
          'EffectiveQC1': [0, 19, 0, 0, 0, 0]}
WOD_TIMES = [10, 21, 30, 40, 0, 2000]


def at(seconds):
    return datetime(2023, 1, 1) + timedelta(seconds=seconds)


def write_diag(path, variables, times, depth=None, qc=None, units=None):
    """Write a minimal IODA-layout SOCA diag file.

    variables: {variable name: {data group: values}}
    times: MetaData/dateTime values in TIME_UNITS, or None to leave it out
    qc: {EffectiveQC group: {variable name: flags}}
    units: {variable name: units attribute of the ObsValue variable}
    """
    size = len(next(iter(next(iter(variables.values())).values())))
    with netCDF4.Dataset(path, 'w') as dataset:
        dataset.createDimension('Location', size)
        metadata = dataset.createGroup('MetaData')
        if times is not None:
            time_var = metadata.createVariable('dateTime', 'i8', ('Location',),
                                               fill_value=-9999)
            time_var.units = TIME_UNITS
            time_var[:] = times
        if depth is not None:
            metadata.createVariable('depth', 'f4', ('Location',))[:] = depth
        for var_name, groups in variables.items():
            for group, values in groups.items():
                if group not in dataset.groups:
                    dataset.createGroup(group)
                variable = dataset.groups[group].createVariable(var_name, 'f4', ('Location',))
                variable[:] = values
                if group == 'ObsValue' and units and var_name in units:
                    variable.units = units[var_name]
        for qc_group, flags in (qc or {}).items():
            group = dataset.createGroup(qc_group)
            for var_name, values in flags.items():
                group.createVariable(var_name, 'i4', ('Location',))[:] = values
    return str(path)


def write_wod(path, qc=None):
    qc = {name: {'waterTemperature': flags}
          for name, flags in (WOD_QC if qc is None else qc).items()}
    return write_diag(path, {'waterTemperature': WOD_VALUES}, WOD_TIMES,
                      depth=WOD_DEPTH, qc=qc)


def harvest_records(filenames, **request):
    return harvest({'harvester_name': hv_registry.SOCA_DIAGS,
                    'filenames': filenames,
                    **request})


def test_depth_bins_qc_and_filetime(tmp_path):
    filename = write_wod(tmp_path / 'wod_t_ctd.nc')
    records = harvest_records([filename],
                              statistics=['mean', 'StdDev', 'count'],
                              QC_threshold=0,
                              ocean_depth_bins=[0, 10, 100, 200])

    # (depth bin, group): (statistics, median time of the observations used)
    # Bins are half open, so depth 10 is in (10, 100) and the NaN depth is in
    # no bin. oman is filtered with EffectiveQC1, the other groups with
    # EffectiveQC0, and NaN values are dropped per group. StdDev of a single
    # value is not reported.
    expected = {
        ((0, 10), 'ObsValue'): ({'mean': 1.5, 'StdDev': sqrt(0.5), 'count': 2}, at(15)),
        ((0, 10), 'oman'): ({'mean': 0.1, 'count': 1}, at(10)),
        ((0, 10), 'ombg'): ({'mean': -1.5, 'StdDev': sqrt(0.5), 'count': 2}, at(15)),
        ((0, 10), 'ObsError'): ({'mean': 0.5, 'StdDev': 0.0, 'count': 2}, at(15)),
        ((10, 100), 'ObsValue'): ({'mean': 3.0, 'count': 1}, at(30)),
        ((10, 100), 'oman'): ({'mean': 1.3 / 3, 'StdDev': sqrt(0.07 / 3), 'count': 3},
                              at(40)),
        ((10, 100), 'ombg'): ({'mean': -3.5, 'StdDev': sqrt(0.5), 'count': 2}, at(35)),
        ((10, 100), 'ObsError'): ({'mean': 0.5, 'StdDev': 0.0, 'count': 2}, at(35)),
    }
    # an empty bin reports only count, with the median time of the whole file
    expected.update({((100, 200), group): ({'count': 0}, at(25)) for group in GROUPS})

    harvested = {(record.ocean_depth_bins, record.group, record.statistics): record
                 for record in records}
    assert len(records) == len(harvested)
    assert harvested.keys() == {(depth_bin, group, statistic)
                                for (depth_bin, group), (stats, _) in expected.items()
                                for statistic in stats}
    for (depth_bin, group), (stats, filetime) in expected.items():
        for statistic, value in stats.items():
            record = harvested[(depth_bin, group, statistic)]
            assert record.value == pytest.approx(value, rel=1e-6), (depth_bin, group, statistic)
            assert record.filetime == filetime, (depth_bin, group, statistic)
    for record in records:
        assert type(record.filetime) is datetime
        assert (record.sensor, record.satellite, record.level, record.file_region) == \
            ('ctd', None, None, 'global')
        assert (record.longname, record.units) == ('waterTemperature', 'DegC')
        assert record.QC_threshold == 0


def test_without_qc_or_depth_bins(tmp_path):
    filename = write_wod(tmp_path / 'wod_t_ctd.nc')
    records = harvest_records([filename],
                              statistics=['mean', 'RMS', 'nobs'],
                              variables=['waterTemperature'],
                              QC_threshold=None)

    harvested = {(record.group, record.statistics): record for record in records}
    assert len(records) == len(harvested) == 12
    # every observation with a valid value is used, including the NaN depth
    assert harvested[('ObsValue', 'count')].value == 5
    assert harvested[('ObsValue', 'mean')].value == pytest.approx(3.4)
    assert harvested[('ObsValue', 'rms')].value == pytest.approx(sqrt(15))
    assert harvested[('ObsValue', 'mean')].filetime == at(21)
    for group in ('oman', 'ombg', 'ObsError'):
        assert harvested[(group, 'count')].value == 6
        assert harvested[(group, 'count')].filetime == at(25)
    assert harvested[('oman', 'mean')].value == pytest.approx(0.35)
    for record in records:
        assert record.ocean_depth_bins is None
        assert record.QC_threshold is None


def test_overlapping_depth_bin_pairs(tmp_path):
    filename = write_wod(tmp_path / 'wod_t_ctd.nc')
    records = harvest_records([filename], statistics=['count'],
                              ocean_depth_bins=[[0, 100], [0, 10]])
    counts = {record.ocean_depth_bins: record.value
              for record in records if record.group == 'ObsValue'}
    assert counts == {(0, 100): 3, (0, 10): 2}


def test_oman_falls_back_to_effective_qc0(tmp_path):
    filename = write_wod(tmp_path / 'wod_t_ctd.nc',
                         qc={'EffectiveQC0': WOD_QC['EffectiveQC0']})
    records = harvest_records([filename], statistics=['mean'])
    oman = [record for record in records if record.group == 'oman']
    assert len(oman) == 1
    assert oman[0].value == pytest.approx(0.3)


def test_no_qc_flags_in_file(tmp_path, caplog):
    filename = write_wod(tmp_path / 'wod_t_ctd.nc', qc={})
    with caplog.at_level(logging.WARNING):
        records = harvest_records([filename], statistics=['count'], QC_threshold=0)
    assert {record.group: record.value for record in records} == \
        {'ObsValue': 5, 'oman': 6, 'ombg': 6, 'ObsError': 6}
    assert 'no EffectiveQC group has waterTemperature' in caplog.text


def test_sst_kelvin_units_without_units_attribute(tmp_path):
    # the units must not depend on the requested statistics or the data group
    filename = write_diag(tmp_path / 'sst_viirs_n20_l3u.nc',
                          {'seaSurfaceTemperature': {'ObsValue': [290.0, 300.0],
                                                     'oman': [0.1, -0.1],
                                                     'ombg': [0.2, -0.2],
                                                     'ObsError': [0.4, 0.4]}},
                          [0, 10])
    records = harvest_records([filename], statistics=['count'], QC_threshold=None)
    assert len(records) == 4
    assert {record.units for record in records} == {'DegK'}


def test_file_without_depth(tmp_path):
    filename = write_diag(tmp_path / 'icec_amsr2_north.nc',
                          {'seaIceFraction': {group: [0.2, 0.4] for group in GROUPS}},
                          [0, 10])
    records = harvest_records([filename], variables=['icec'], QC_threshold=None,
                              ocean_depth_bins=[0, 10, 100])
    assert len(records) == 4
    for record in records:
        assert record.ocean_depth_bins is None
        assert (record.variables, record.units) == ('seaIceFraction', '1')
        assert (record.sensor, record.satellite, record.file_region) == \
            ('amsr2', 'gcom-w1', 'nh')


def test_all_variables_harvested_by_default(tmp_path):
    filename = write_diag(tmp_path / 'insitu_surface_trkob.2021070300.nc4',
                          {'seaSurfaceTemperature': {group: [20.0, 21.0] for group in GROUPS},
                           'seaSurfaceSalinity': {'ObsValue': [35.0, 36.0],
                                                  'ObsError': [1.0, 1.0]}},
                          [0, 10],
                          units={'seaSurfaceSalinity': 'psu',
                                 'seaSurfaceTemperature': 'degC'})
    records = harvest_records([filename], QC_threshold=None)
    groups = {(record.variables, record.group) for record in records}
    assert groups == {('seaSurfaceTemperature', group) for group in GROUPS} | \
        {('seaSurfaceSalinity', 'ObsValue'), ('seaSurfaceSalinity', 'ObsError')}
    for record in records:
        assert (record.sensor, record.satellite) == ('trkob', None)
    assert {record.variables: record.units for record in records} == \
        {'seaSurfaceTemperature': 'DegC', 'seaSurfaceSalinity': 'psu'}


def test_filetime_falls_back_to_file_name_cycle(tmp_path):
    filename = write_diag(tmp_path / 'wod_t_pfl.2023080612.nc',
                          {'waterTemperature': {group: [1.0, 2.0] for group in GROUPS}},
                          np.ma.masked_all(2, dtype='i8'))
    records = harvest_records([filename], QC_threshold=None)
    assert {record.filetime for record in records} == {datetime(2023, 8, 6, 12)}


def test_multiple_files_and_unsupported_file_names(tmp_path, caplog):
    wod = write_wod(tmp_path / 'wod_t_ctd.nc')
    sst = write_diag(tmp_path / 'sst_nggodas.nc',
                     {'seaSurfaceTemperature': {group: [20.0, 21.0] for group in GROUPS}},
                     [0, 10])
    mooring = write_diag(tmp_path / 'moana.nc',
                         {'waterTemperature': {group: [1.0, 2.0] for group in GROUPS}},
                         [0, 10])
    with caplog.at_level(logging.WARNING):
        records = harvest_records([wod, mooring, sst], statistics=['count'],
                                  QC_threshold=None)
    assert [record.filenames for record in records] == [wod] * 4 + [sst] * 4
    assert 'moana.nc is not a supported SOCA diag file name' in caplog.text


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        harvest_records([str(tmp_path / 'wod_t_ctd.nc')])


def test_missing_date_time(tmp_path):
    filename = write_diag(tmp_path / 'wod_t_ctd.nc',
                          {'waterTemperature': {'ObsValue': [1.0, 2.0]}}, None)
    with pytest.raises(KeyError, match='dateTime'):
        harvest_records([filename])


def test_statistic_and_variable_aliases():
    config = SOCADiagsConfig({'statistics': ['RMS', 'n', 'nobs', 'StdDev'],
                              'variables': ['sst', 'icec', 'salinity']})
    assert config.get_stats() == ['rms', 'count', 'StdDev']
    assert config.get_variables() == ['seaSurfaceTemperature', 'seaIceFraction', 'salinity']


@pytest.mark.parametrize('request_dict', [{'statistics': ['rmse']},
                                          {'statistics': ['variance']},
                                          {'variables': ['temperature']}])
def test_unsupported_statistic_or_variable(request_dict):
    with pytest.raises(KeyError):
        SOCADiagsConfig(request_dict)


@pytest.mark.parametrize('threshold', ['0', True, [0]])
def test_invalid_qc_threshold(threshold):
    with pytest.raises(ValueError):
        SOCADiagsConfig({'QC_threshold': threshold})


@pytest.mark.parametrize('ocean_depth_bins, expected', [
    (None, [None]),
    ([], [None]),
    ([None], [None]),
    ([0, 10, 50.5], [(0, 10), (10, 50.5)]),
    ([[0, 20], [20, 100], [0, 100]], [(0, 20), (20, 100), (0, 100)]),
    (((0, 20),), [(0, 20)]),
])
def test_normalize_depth_bins(ocean_depth_bins, expected):
    assert normalize_depth_bins(ocean_depth_bins) == expected


@pytest.mark.parametrize('ocean_depth_bins', [
    [10],
    [0, 10, 5],
    [[10, 0]],
    [[0, 10], 20],
    [[0, 10, 20]],
    [0, '10'],
    '0, 10',
    10,
])
def test_invalid_depth_bins(ocean_depth_bins):
    with pytest.raises(ValueError):
        normalize_depth_bins(ocean_depth_bins)


@pytest.mark.parametrize('filename, expected', [
    ('adt_glore_3a.nc', ('adt', 'Synthetic aperture Radar Altimeter', 'Sentinel-3A', None,
                         'global', None)),
    ('adt_glore_6a.nc', ('adt', 'Poseidon 4', 'Sentinel-6A', None, 'global', None)),
    ('adt_glore_c2.nc', ('adt', 'SAR Interferometer Radar Altimeter', 'cryosat2', None,
                         'global', None)),
    ('adt_glore_j3.nc', ('adt', 'Poseidon 3B', 'jason3', None, 'global', None)),
    ('adt_rads_all.2021070300.nc4', ('adt', 'misc', 'misc', None, 'global',
                                     datetime(2021, 7, 3))),
    ('icec_amsr2_north.nc', ('icec', 'amsr2', 'gcom-w1', None, 'nh', None)),
    ('icec_amsr2_south.nc', ('icec', 'amsr2', 'gcom-w1', None, 'sh', None)),
    ('icec_nsidc_nh.nc', ('icec', 'ssmis', 'dmsp', None, 'nh', None)),
    ('icec_nsidc_sh.nc', ('icec', 'ssmis', 'dmsp', None, 'sh', None)),
    ('icec_ssmis_f17_l2.2021070300.nc4', ('icec', 'ssmis', 'dmsp', 'l2', 'global',
                                          datetime(2021, 7, 3))),
    ('icec_viirs_n20_l2_south.nc', ('icec', 'viirs', 'n20', 'l2', 'sh', None)),
    ('sst_odyssea.nc', ('sst', 'multiple', 'ODYSSEA', 'l3', 'global', None)),
    ('sst_avhrr_mb_l3u.nc', ('sst', 'avhrr', 'metop-b', 'l3u', 'global', None)),
    ('sst_nggodas.nc', ('sst', 'avhrr', 'metop', 'unknown', 'global', None)),
    ('sst_viirs_npp_l3u.nc', ('sst', 'viirs', 'npp', 'l3u', 'global', None)),
    ('sst_abi_g16_l3c.nc', ('sst', 'abi', 'g16', 'l3c', 'global', None)),
    ('sss_smap_l2.nc', ('sss', 'smap', 'Unknown', 'l2', 'global', None)),
    ('wod_s_ctd.nc', ('wod', 'ctd', None, None, 'global', None)),
    ('wod_t_xbt.nc', ('wod', 'xbt', None, None, 'global', None)),
    ('/path/to/wod_t_ctd.1979010200.nc4', ('wod', 'ctd', None, None, 'global',
                                           datetime(1979, 1, 2))),
    ('wod_t_pfl.2023080612.nc', ('wod', 'pfl', None, None, 'global',
                                 datetime(2023, 8, 6, 12))),
    ('insitu_profile_argo.2021070300.nc4', ('insitu', 'argo', None, None, 'global',
                                            datetime(2021, 7, 3))),
    ('insitu_surface_trkob.nc4', ('insitu', 'trkob', None, None, 'global', None)),
    # GDASApp obs-space names (parm/marine/obs/obs_list.yaml.j2)
    ('rads_adt_j3.nc', ('adt', 'Poseidon 3B', 'jason3', None, 'global', None)),
    ('rads_adt_sa.nc', ('adt', 'AltiKa', 'saral', None, 'global', None)),
    ('sst_avhrrf_ma_l3u.nc', ('sst', 'avhrr', 'metop-a', 'l3u', 'global', None)),
    ('sst_avhrrf_mb_l3u.nc', ('sst', 'avhrr', 'metop-b', 'l3u', 'global', None)),
    ('sst_viirs_n21_l3u.nc', ('sst', 'viirs', 'n21', 'l3u', 'global', None)),
    ('insitu_temp_profile_argo.nc', ('insitu', 'argo', None, None, 'global', None)),
    ('insitu_salt_profile_glider.nc', ('insitu', 'glider', None, None, 'global', None)),
    ('insitu_temp_surface_drifter.nc', ('insitu', 'drifter', None, None, 'global',
                                        None)),
])
def test_parse_filename(filename, expected):
    info = parse_filename(filename)
    assert (info['file_type'], info['sensor'], info['satellite'], info['level'],
            info['file_region'], info['cycle']) == expected


@pytest.mark.parametrize('filename', ['moana.nc', 'pirata_t.nc', 'rama_t.nc', 'tao_t.nc',
                                      'wod_x_ctd.nc', 'diag_conv_t_ges.nc4'])
def test_unsupported_file_names(filename):
    assert parse_filename(filename) is None


@pytest.mark.parametrize('file_type, var_name, units, mean_value, expected', [
    ('sst', 'seaSurfaceTemperature', None, 290.0, ('seaSurfaceTemperature', 'DegK')),
    ('sst', 'seaSurfaceTemperature', None, 20.0, ('seaSurfaceTemperature', 'DegC')),
    ('sst', 'seaSurfaceTemperature', 'degC', 290.0, ('seaSurfaceTemperature', 'DegC')),
    ('sst', 'seaSurfaceTemperature', 'K', 20.0, ('seaSurfaceTemperature', 'DegK')),
    ('icec', 'seaIceFraction', None, None, ('seaIceFraction', '1')),
    ('adt', 'absoluteDynamicTopography', None, None, ('absoluteDynamicTopography', 'm')),
    ('sss', 'seaSurfaceSalinity', None, None, ('seaSurfaceSalinity', 'psu')),
    ('wod', 'waterTemperature', None, None, ('waterTemperature', 'DegC')),
    ('wod', 'salinity', None, None, ('Practical Salinity Scale', 'PSS')),
    ('insitu', 'salinity', 'psu', None, ('salinity', 'psu')),
])
def test_variable_metadata(file_type, var_name, units, mean_value, expected):
    assert get_variable_metadata(file_type, var_name, units, mean_value) == expected
