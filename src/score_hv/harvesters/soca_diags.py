#!/usr/bin/env python

import os, sys
import numpy as np
import netCDF4
from datetime import datetime as dt
from dataclasses import dataclass, field
from collections import namedtuple

"""
SOCA Diagnostic Harvester
-------------------------
Input: IODA-v3 NetCDF4 files (SST, ICEC, or WOD).
Masking Logic: 
    Combined Mask = (Data == FillValue) | (QC_Flag > Threshold)
"""

VALID_STATISTICS = ('mean', 'median', 'StdDev', 'minimum', 'maximum','rmse')
VALID_VARIABLES = ('sst', 'icec', 'salinity', 'waterTemperature', 
                   'seaSurfaceSalinity', 'seaSurfaceTemperature', 'seaIceFraction')

HarvestedData = namedtuple('HarvestedData', [
    'filenames', 'sensor', 'satellite', 'level', 'variables', 
    'group', 'longname', 'units', 'statistics', 'value', 
    'filetime', 'file_region', 'QC_threshold',
])

def parse_filename(filename):
    base = os.path.basename(filename).split('.')[0]
    parts = base.split('_')
    prefix = parts[0]
    
    info = {
        'file_type': prefix,
        'sensor': None,
        'satellite': None,
        'file_region': None,
        'level': None,
        'variable': prefix
    }

    if prefix == 'wod':
        info.update({
            'sensor': parts[2] if len(parts) > 2 else parts[0],
            'variable': parts[1] if len(parts) > 1 else None,
            'file_region': 'global'
        })
    elif prefix in ['icec', 'sst']:
        info['variable'] = 'seaIceFraction' if prefix == 'icec' else 'seaSurfaceTemperature'
        info['sensor'] = parts[1] if len(parts) > 1 else None
        
        for p in parts[1:]:
            clean_p = p.lower().strip()
            if clean_p in ['north', 'south']:
                info['file_region'] = clean_p
            elif clean_p.startswith('l') and any(c.isdigit() for c in clean_p):
                info['level'] = clean_p
            elif clean_p != info['sensor'] and info['satellite'] is None:
                info['satellite'] = clean_p
    elif prefix == 'insitu':
        info['file_region'] = 'global'
   
        if len(parts) > 2:
            data_type = parts[1].lower()  # 'profile' or 'surface'
            info['sensor'] = parts[2]
            
            # For insitu, the actual variable name (e.g., 'waterTemperature' or 'salinity') 
            # is usually determined by looking inside the NetCDF file later, 
            # but we can set a default here or keep it as 'insitu'.
            info['variable'] = f"insitu_{data_type}" 
            info['level'] = None 
        
    return info

def extract_soca_metadata(ds):
    meta = ds.groups.get('MetaData')
    if not meta:
        raise KeyError("MetaData group missing in the file.")
    
    mandatory = ['latitude', 'longitude', 'dateTime']
    extracted = {}
    for var in mandatory:
        if var in meta.variables:
            extracted[var] = meta.variables[var][:]
        else:
            raise KeyError(f"Mandatory variable '{var}' missing from MetaData.")

    extracted['depth'] = meta.variables['depth'][:] if 'depth' in meta.variables else None
    return extracted

def get_variable_metadata(file_type, var_name, mean_val=None):
    soca_to_wod_map = {
        'waterTemperature': 't', 'seaSurfaceTemperature': 't',
        'salinity': 's', 'seaSurfaceSalinity': 's', 'seaIceFraction': 'ice'
    }  
    wod_meta = {
        't': ('Temperature', 'DegC'), 's': ('Practical Salinity Scale', 'PSS'),
        'o': ('Oxygen', 'umol/kg'), 'p': ('Phosphate', 'umol/kg'),
        'i': ('Silicate', 'umol/kg'), 'n': ('Nitrate', 'umol/kg'),
        'h': ('pH', 'pH'), 'l': ('Chlorophyll', 'ug/l'), 'a': ('Alkalinity', 'umol/kg')
    }

    if file_type == 'wod':
        lookup_key = soca_to_wod_map.get(var_name, var_name)
        return wod_meta.get(lookup_key, (var_name, 'Unknown'))

    units = 'Unknown'
    if file_type == 'icec': units = "%"
    elif file_type == 'sst':
        units = 'DegC' if (mean_val is None or mean_val < 200) else 'DegK'
            
    return var_name, units

def calc_rmse(data):
    """
    Calculates root mean squated error on a masked array. 
    The 'data' argument is received from the dictionary call below.
    """
    squared_data = data**2 
    mean_squared = np.ma.mean(squared_data)
    rmse = np.ma.sqrt(mean_squared)
    print("the rmse ",rmse)
   
    return rmse


def calculate_masked_stats(var_obj, qc_mask, requested_stats):
    raw_data = var_obj[:]
    if '_FillValue' in var_obj.ncattrs():
        fill_mask = (raw_data == var_obj.getncattr('_FillValue'))
    else:
        fill_mask = np.zeros_like(raw_data, dtype=bool)
        
    combined_mask = fill_mask | qc_mask
    masked_data = np.ma.masked_array(raw_data, mask=combined_mask)
    
    if masked_data.count() == 0:
        return {}

    stat_map = {
        'mean': np.ma.mean, 'median': np.ma.median,
        'StdDev': np.ma.std, 'minimum': np.ma.min, 'maximum': np.ma.max,
        'rmse': calc_rmse 
    }

    results = {}
    for stat in requested_stats:
        if stat in stat_map:
            val = stat_map[stat](masked_data)
            results[stat] = float(val) if not np.ma.is_masked(val) else None

    return results

@dataclass
class SOCADiagsConfig:
    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.harvest_filenames = self.config_data.get('filenames', [])
        self.variables = self.config_data.get('variables', [])
        self.stats = self.config_data.get('statistics', ['mean'])
        
        # Use 999999.0 as default so missing keys don't filter all data
        user_threshold = self.config_data.get('QC_threshold', 999999.0)
        
        if isinstance(user_threshold, (list, np.ndarray)):
            self.qc_threshold = float(user_threshold[0]) 
        else:
            self.qc_threshold = float(user_threshold) if user_threshold is not None else 999999.0

@dataclass
class SOCADiagsHv:
    config: SOCADiagsConfig

    def get_data(self):
        harvested_results = []
        data_groups = ['ObsValue', 'oman', 'ombg', 'ObsError']

        for filename in self.config.harvest_filenames:
            if not os.path.exists(filename): continue
            try:
                with netCDF4.Dataset(filename, 'r') as ds:
                    file_info = parse_filename(filename)
                    obs_metadata = extract_soca_metadata(ds)
                    times = obs_metadata['dateTime']
                    
                    time_meta = ds.groups['MetaData'].variables['dateTime'] 
                    dates = netCDF4.num2date(times, units=time_meta.units, 
                            calendar=getattr(time_meta, 'calendar', 'standard'))
                    file_time = dt.fromisoformat(dates[0].strftime("%Y-%m-%d %H:%M:%S"))                   

                    obs_group = ds.groups.get('ObsValue')
                    if not obs_group: continue

                    for var_name in obs_group.variables.keys():
                        qc_group = ds.groups.get('EffectiveQC0')
                        if qc_group and var_name in qc_group.variables:
                            qc_flags = qc_group.variables[var_name][:]
                            qc_mask = (qc_flags > self.config.qc_threshold)
                        else:
                            qc_mask = np.zeros(obs_group.variables[var_name].shape, dtype=bool)

                        for group_name in data_groups:
                            if group_name not in ds.groups or var_name not in ds.groups[group_name].variables:
                               continue
               
                            var_obj = ds.groups[group_name].variables[var_name]
                            stats = calculate_masked_stats(var_obj, qc_mask, self.config.stats)
                            if not stats: continue

                            long_name, units = get_variable_metadata(
                                file_info['file_type'], var_name, mean_val=stats.get('mean'))

                            for stat_name, stat_val in stats.items():
                                if stat_val is None: continue
                                harvested_results.append(HarvestedData(
                                    filenames=filename, sensor=file_info['sensor'],
                                    satellite=file_info['satellite'], level=file_info['level'],
                                    variables=var_name, group=group_name, longname=long_name,
                                    units=units, statistics=stat_name, value=np.float32(stat_val),
                                    filetime=file_time, file_region=file_info['file_region'],
                                    QC_threshold=self.config.qc_threshold
                                ))
            except Exception as e:
                print(f"Error processing {os.path.basename(filename)}: {e}")
        return harvested_results
