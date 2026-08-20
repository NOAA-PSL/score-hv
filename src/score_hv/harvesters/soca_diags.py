import os
import numpy as np
import netCDF4
import logging
from datetime import datetime as dt
from dataclasses import dataclass, field
from collections import namedtuple

# Standard definitions
VALID_STATISTICS = ('mean', 'median', 'StdDev', 'minimum', 'maximum', 'rms', 'count')
VALID_FILE_TYPE_IDS = ('sst', 'icec', 'adt', 'wod', 'sss')

HarvestedData = namedtuple('HarvestedData', [
    'filenames', 'sensor', 'satellite', 'level', 'variables', 
    'group', 'longname', 'units', 'statistics', 'value', 
    'filetime', 'file_region', 'QC_threshold', 'ocean_depth_bins'
])

def extract_soca_metadata(ds):
    """
    Extracts core spatial/temporal variables from MetaData group.
    Parameters: ds - netCDF4.Dataset  An open NetCDF file handle.
    Return:     A dictionary containing arrays for latitude, longitude, dateTime, 
                and optionally depth.
    """
    meta = ds.groups.get('MetaData')
    if not meta:
        raise KeyError("MetaData group missing in NetCDF file.")
    
    extracted = {}
    for var in ['latitude', 'longitude', 'dateTime']:
        if var in meta.variables:
            extracted[var] = meta.variables[var][:]
        else:
            raise KeyError(f"Mandatory variable '{var}' missing in MetaData.")
    
    extracted['depth'] = meta.variables['depth'][:] if 'depth' in meta.variables else None
    return extracted

def get_variable_metadata(file_type, var_name, mean_val=None):
    """
    Determines long names and units based on file type and variable name.
    """
    soca_map = {
        'waterTemperature': 't', 'seaSurfaceTemperature': 't',
        'salinity': 's', 'Salinity': 's', 'seaIceFraction': 'ice'
    }
    wod_meta = {
        't': ('waterTemperature', 'DegC'), 
        's': ('Practical Salinity Scale', 'PSS'),
        'o': ('Oxygen', 'umol/kg'), 
        'ice': ('Sea Ice Fraction', '%')
    }

    if file_type == 'wod':
        lookup = soca_map.get(var_name, var_name)
        return wod_meta.get(lookup, (var_name, 'Unknown'))

    units = 'Unknown'
    if file_type == 'icec': 
        units = '%'
    elif file_type == 'sst': 
        units = 'DegC' if (mean_val is not None and mean_val < 200) else 'DegK'
    elif file_type == 'adt': 
        units = 'm'
    elif file_type == 'sss': 
        units = 'psu'
        
    return var_name, units

@dataclass
class SOCADiagsConfig:
    config_data: dict = field(default_factory=dict)
    
    def __post_init__(self):
        self.harvest_filenames = self.config_data.get('filenames', [])
        self.variables = self.config_data.get('variables', [])
        self.stats = self.config_data.get('statistics', ['mean'])
        self.qc_threshold = self.config_data.get('QC_threshold', 0.0)
        self.ocean_depth_bins = self.config_data.get('ocean_depth_bins', [None])

class SOCADiagsHv:
    def __init__(self, config: SOCADiagsConfig):
        self.config = config

    def get_icec_info(self, filename):
        fn = filename.lower()
        satellite, sensor, file_region = "Unknown", "Unknown", "global"
        if "amsr2" in fn:
            satellite, sensor = "gcom-w1", "amsr2"
        elif "ssmis" in fn or "nsidc" in fn:
            satellite, sensor = "dmsp", "ssmis"
        
        if "north" in fn or "_nh" in fn: file_region = "nh"
        elif "south" in fn or "_sh" in fn: file_region = "sh"
        
        return {"satellite": satellite, "sensor": sensor, "file_region": file_region}

    def get_sst_info(self, filename):
        fn = filename.lower()
        satellite, sensor, level = "unknown", "unknown", "unknown"

        if "avhrr" in fn:
            sensor = "avhrr"
            satellite = "metop-b" if "mb" in fn else "metop-c" if "mc" in fn else "unknown"
        elif "nggodas" in fn:
            sensor = "avhrr"
            satellite = "metop"
        elif "viirs" in fn:
            sensor = "viirs"
            if "npp" in fn or "snpp" in fn: satellite = "npp"
            elif "n20" in fn: satellite = "n20"
            elif "n21" in fn: satellite = "n21"
            #elif "n20" in fn or "j01" in fn: satellite = "NOAA-20"
            #elif "n21" in fn or "j02" in fn: satellite = "NOAA-21"
            #else: satellite = "VIIRS-Multi"
        elif "amsr2" in fn:
            sensor, satellite = "amsr2", "gcom-w1"

        elif "noaa15" in fn:
            sensor, satellite = "avhrr", "n15" 
        
        if "l3u" in fn: level = "l3u"
        elif "l2" in fn: level = "l2"
        elif "l3c" in fn: level = "l3c"

        # REFACTORED: Replaced explicit loop + break statement with next() generator expression
        regions = {"natl": "North Atlantic", "satl": "South Atlantic", "gom": "Gulf of Mexico", "arctic": "Arctic"}
        file_region = next((full_name for tag, full_name in regions.items() if tag in fn), "global")

        return {"satellite": satellite, "sensor": sensor, "file_region": file_region, "level": level}

    def get_adt_info(self, filename):
        parts = filename.replace('.nc', '').split('_')
        platform_id = parts[2] if len(parts) > 2 else None
        
        satellite, sensor = "Unknown", "Unknown"
        adt_mapping = {
            "all": {"satellite": "misc", "sensor": "misc"},
            "e1": {"satellite": "ers1", "sensor": "Radar Altimeter"}
            "e2": {"satellite": "ers2", "sensor": "Radar Altimeter"},
            "j1": {"satellite": "jason1", "sensor": "Poseidon 2"},
            "j2": {"satellite": "jason2", "sensor": "Poseidon 3"},
            "j3": {"satellite": "jason3", "sensor": "Poseidon 3B"},
            "3a": {"satellite": "Sentinel-3A", "sensor": "Synthetic aperture Radar Altimeter"},
            "3b": {"satellite": "Sentinel-3B", "sensor": "Synthetic aperture Radar Altimeter"},
            "6a": {"satellite": "Sentinel-6A", "sensor": "Poseidon 4"},
            "sa": {"satellite": "saral", "sensor": "AltiKa"},
            "sw": {"satellite": "swot", "sensor": "KaRIN"},
            "c2": {"satellite": "cryosat2", "sensor": "SAR Interferometer Radar Altimeter"},
            "tx": {"satellite": "topex-poseidon", "sensor": "NASA Radar Altimeter"},
            "n1": {"satellite": "envisat", "sensor": "Radar Altimeter - 2"},
            "g1": {"satellite": "gfo", "sensor": "GFO-Radar Altimeter"},
        }
        return adt_mapping.get(platform_id, {"satellite": satellite, "sensor": sensor})

    def get_wod_info(self, filename):
        parts = filename.replace('.nc', '').split('_')
        return {"sensor": parts[2] if len(parts) > 2 else "Unknown", "satellite": "In-Situ"}

    def parse_filename(self, filename):
        basename = os.path.basename(filename).lower()
        file_type = next((t for t in VALID_FILE_TYPE_IDS if t in basename), None)
        if not file_type: return None
          
        info = {'file_type': file_type, 'sensor': 'Unknown', 'satellite': 'Unknown', 
                'file_region': 'global', 'level': None}
            
        parsers = {
            'wod': self.get_wod_info,
            'icec': self.get_icec_info,
            'adt': self.get_adt_info,
            'sst': self.get_sst_info
        }
        
        if file_type in parsers:
            info.update(parsers[file_type](basename))
        return info

    def _calculate_rms(self, masked_data):
        valid = masked_data.compressed()
        if valid.size == 0: return None
        return float(np.sqrt(np.mean(np.square(valid.astype(np.float64)))))

    def calculate_masked_stats(self, var_obj, bin_mask, requested_stats):
        netcdf_data = var_obj[:]
        combined_mask = np.ma.getmaskarray(netcdf_data) | bin_mask
        masked_data = np.ma.masked_array(netcdf_data, mask=combined_mask).ravel()

        if masked_data.count() == 0:
            return {s: (0 if s == 'count' else None) for s in requested_stats}

        stat_map = {
            'mean':    lambda x: float(np.ma.mean(x)),
            'median':  lambda x: float(np.ma.median(x)),
            'StdDev':  lambda x: float(np.ma.std(x, ddof=1)) if x.count() > 1 else None,
            'minimum': lambda x: float(np.ma.min(x)),
            'maximum': lambda x: float(np.ma.max(x)),
            'rms':     self._calculate_rms,
            'count':   lambda x: int(x.count())
        }
        
        results = {}
        for stat in [s.strip() for s in requested_stats]:
            if stat in stat_map:
                try:
                    val = stat_map[stat](masked_data)
                    results[stat] = val if (val is not None and np.isfinite(val)) else None
                except Exception as e:
                    logging.debug(f"Failed calculating {stat}: {e}")
                    results[stat] = None
        return results

    def get_data(self):
        """
        Return: list A list of HarvestedData namedtuples.
        """
        harvested_results = []
        data_groups = ['ObsValue', 'oman', 'ombg', 'ObsError']
          
        for filename in self.config.harvest_filenames:
            if not os.path.exists(filename):
                raise FileNotFoundError(f"Missing required SOCA/JEDI file: {filename}")

            with netCDF4.Dataset(filename, 'r') as ds:
                file_info = self.parse_filename(filename)
                if file_info is None: continue 

                meta = extract_soca_metadata(ds)
                has_depth = meta.get('depth') is not None
                current_bins = self.config.ocean_depth_bins if has_depth else [None]

                for var_name in ds.groups['ObsValue'].variables.keys():
                    if self.config.variables and var_name not in self.config.variables:
                        continue

                    # --- BASELINE TIME QC (EffectiveQC0) ---
                    base_qc_grp = ds.groups.get('EffectiveQC0')
                    if not base_qc_grp:
                       qc_group_keys = []
                       for group_names in ds.groups.keys():
                           if group_names.startswith('EffectiveQC'):
                              qc_group_keys.append(group_names)
                       if qc_group_keys: #Get the first match if the list is not empty.
                           base_qc_grp = ds.groups[qc_group_keys[0]]
                    """
                      Now mask.
                      """
                    if base_qc_grp and var_name in base_qc_grp.variables:
                        base_qc_mask = base_qc_grp.variables[var_name][:] > self.config.qc_threshold
                    else:
                        base_qc_mask = np.zeros(ds.groups['ObsValue'].variables[var_name].shape, dtype=bool)

                    """
                      The variable current_bins is set to None on this line:
                      current_bins = self.config.ocean_depth_bins if has_depth else [None]
                      If the input data file does not contain depth bins or the config
                      dictionary does not contain bins then the current bins will be
                      set to none.  The for loop will execute only once.
                      """
                    for d_bin in current_bins:
                        # Build the mask window specifically for time math
                        time_mask = base_qc_mask.copy()
                        if d_bin and has_depth:
                            time_mask |= (meta['depth'] < d_bin[0]) | (meta['depth'] >= d_bin[1])

                        masked_times = np.ma.masked_array(meta['dateTime'], mask=time_mask)
                        
                        if masked_times.count() > 0:
                            median_time_num = np.ma.median(masked_times)
                            time_var = ds.groups['MetaData'].variables['dateTime']
                            
                            # Forced float cast to prevent netCDF wrapper object leakage into num2date
                            midpoint_date = netCDF4.num2date(float(median_time_num), units=time_var.units)
                            
                            if hasattr(midpoint_date, 'calendar'):
                                file_time = dt(midpoint_date.year, midpoint_date.month, midpoint_date.day,
                                               midpoint_date.hour, midpoint_date.minute, midpoint_date.second)
                            else:
                                file_time = dt(midpoint_date.year, midpoint_date.month, midpoint_date.day,
                                               midpoint_date.hour, midpoint_date.minute)
                        else:
                            file_time = None

                        # Now track data groups for structural metrics processing
                        for grp in data_groups:
                            if grp not in ds.groups or var_name not in ds.groups[grp].variables:
                                continue

                            # Use EffectiveQC1 exclusively for o-a ('oman'), fallback to EffectiveQC0 for others
                            target_qc_suffix = '1' if grp == 'oman' else '0'
                            qc_grp_name = f'EffectiveQC{target_qc_suffix}'
                            qc_grp = ds.groups.get(qc_grp_name, base_qc_grp)

                            if qc_grp and var_name in qc_grp.variables:
                                qc_mask = qc_grp.variables[var_name][:] > self.config.qc_threshold
                            else:
                                qc_mask = np.zeros(ds.groups['ObsValue'].variables[var_name].shape, dtype=bool)

                            # Combine specific group QC with depth filters for metrics math
                            bin_mask = qc_mask.copy()
                            if d_bin and has_depth:
                                bin_mask |= (meta['depth'] < d_bin[0]) | (meta['depth'] >= d_bin[1])
                            
                            if np.all(bin_mask): continue
                            
                            stats = self.calculate_masked_stats(
                                ds.groups[grp].variables[var_name], 
                                bin_mask, self.config.stats
                            )
                            lname, units = get_variable_metadata(
                                file_info['file_type'], var_name, stats.get('mean')
                            )
                            
                            for s_name, s_val in stats.items():
                                harvested_results.append(HarvestedData(
                                    filenames=filename, sensor=file_info['sensor'], 
                                    satellite=file_info['satellite'], level=file_info['level'], 
                                    variables=var_name, group=grp, longname=lname,
                                    units=units, statistics=s_name, value=s_val, 
                                    filetime=file_time, file_region=file_info['file_region'], 
                                    QC_threshold=self.config.qc_threshold, ocean_depth_bins=d_bin
                                ))
                
        return harvested_results

