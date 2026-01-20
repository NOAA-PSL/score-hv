#!/usr/bin/env python

import os
import sys
import numpy as np
import xarray as xr
import netCDF4
from datetime import datetime as dt
from pathlib import Path
from collections import namedtuple
from dataclasses import dataclass, field

# Mocking the base class if not available in your environment
try:
    from score_hv.config_base import ConfigInterface
except ImportError:
    class ConfigInterface: pass

HARVESTER_NAME = 'soca_diags'
VALID_STATISTICS = ('mean', 'median', 'StdDev', 'minimum', 'maximum')
VALID_VARIABLES = ('sst', 'icec', 'salinity', 'waterTemperature', 
                   'seaSurfaceSalinity', 'seaSurfaceTemperature', 'seaIceFraction')

HarvestedData = namedtuple('HarvestedData', [
    'filenames', 'sensor', 'satellite', 'level', 'variables', 
    'group', 'longname', 'units', 'statistics', 'value', 
    'filetime', 'file_region'
])

def parse_filename(filename):

    base = os.path.basename(filename)
    clean_name = base.replace('.nc', '')
    parts = clean_name.split('_')
    file_name_prefix = parts[0]
    sensor = None
    satellite = None
    file_region = None 
    processing_level = None
    file_date = None

    if file_name_prefix == 'wod':
       return {
            'file_type': 'wod',   
            'sensor': parts[2] if len(parts) > 2 else parts[0],
            'region': 'global',
            'satellite': None,
            'level': None,
            'variable': parts[1] if len(parts) > 1 else None, 
            'date': parts[3] if len(parts) > 3 else None
       }

    elif file_name_prefix == 'icec' or file_name_prefix == 'sst':
       sensor =  parts[1] if len(parts) > 1 else None 
       part2 = parts[2] if len(parts) > 2 else None
       if part2 == 'north' or part2 == 'south':
          file_region = part2 
       else:
          satellite = part2
       part3 = parts[3] if len(parts) > 3 else None
       if part3:
          if part3.startswith('l'):
             processing_level = part3 # Grab the 'l'
          elif part3[0].isdigit():
             file_date = part3 # Grab the date string
       return {
            'file_type': file_name_prefix,  
            'sensor': sensor,
            'region': file_region,
            'satellite': satellite,
            'level': processing_level,
            'variable': file_name_prefix,
            'date': file_date
        }  
    elif file_name_prefix == 'adt':
        print(file_name_prefix)
        satellite = parts[1] if len(parts) > 1 else None
        sys.exit(0)

def get_wod_metadata(variable):
    wod_meta = {
            't': {'unit': 'DegC',    'long_name': 'Temperature'},
            's': {'unit': 'PSS',     'long_name': 'Practical Salinity Scale'},
            'o': {'unit': 'umol/kg', 'long_name': 'Oxygen'},
            'p': {'unit': 'umol/kg', 'long_name': 'Phosphate'},
            'i': {'unit': 'umol/kg', 'long_name': 'Silicate'},
            'n': {'unit': 'umol/kg', 'long_name': 'Nitrate'},
            'h': {'unit': 'pH',      'long_name': 'pH'},
            'l': {'unit': 'ug/l',    'long_name': 'Chlorophyll'},
            'a': {'unit': 'umol/kg', 'long_name': 'Alkalinity'}
    }

    meta_info = wod_meta.get(variable, {'unit': 'Unknown', 'long_name': 'Unknown'})   
    return meta_info
    
def read_MetaData_group(dataset):
    if 'MetaData' not in dataset.groups:
        return None, None
    
    metadata_group = dataset.groups['MetaData']
    dates = metadata_group['dateTime'][:]
    first_timestamp = dates[0]
    dt_object = dt.fromtimestamp(first_timestamp)
    file_date = dt_object.strftime("%Y-%m-%d %H:%M:%S")
    lat = metadata_group['latitude'][:] if 'latitude' in metadata_group.variables else None
    lon = metadata_group['longitude'][:] if 'longitude' in metadata_group.variables else None
    depth = metadata_group['depth'][:] if 'depth' in metadata_group.variables else None
    return lat, lon, depth, file_date

def read_EffectiveQC_groups(dataset, QClevel,var_name):
    group_name = 'EffectiveQC0' if QClevel == 0 else 'EffectiveQC1'
    if group_name in dataset.groups:
        return dataset.groups[group_name]
    return None

@dataclass
class SOCADiagsConfig(ConfigInterface):
    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.set_config()

    def set_config(self):
        self.harvest_filenames = self.config_data.get('filenames', [])
        self.variables = self.config_data.get('variables', [])
        self.stats = self.config_data.get('statistics', ['mean'])
        self.depths = self.config_data.get('depths')
        self.regions = self.config_data.get('regions')
        self.qc_threshold = self.config_data.get('effective_QC_threshold', 0)
        self._validate()
       
    def _validate(self):
        for var in self.variables:
            if var not in VALID_VARIABLES:
                raise KeyError(f"Unsupported variable: {var}")
        for stat in self.stats:
            if stat not in VALID_STATISTICS:
                raise KeyError(f"Unsupported statistic: {stat}")

@dataclass
class SOCADiagsHv:
    config: SOCADiagsConfig

    def _save_diagnostic_nc(self, var_values, lat, lon, var_name, group_name, timestamp):
        """Saves masked data to a NetCDF for plotting."""
        output_name = f"diag_{group_name}_{var_name}_{timestamp}.nc"
        
        # Convert masked array to floats with NaNs for plotting compatibility
        plot_data = var_values.filled(np.nan)
        
        ds = xr.Dataset(
            {
                var_name: (["obs"], plot_data)
            },
            coords={
                "lat": (["obs"], lat),
                "lon": (["obs"], lon),
            },
            attrs={"description": f"Harvested {group_name} data for {var_name}"}
        )
        ds.to_netcdf(output_name)
        print(f"--> Diagnostic file saved: {output_name}")

    def get_data(self):
        harvested_data = []
        data_groups = ['ObsValue', 'oman', 'ombg']
        
        for filename in self.config.harvest_filenames:
            print(f"Processing: {os.path.basename(filename)}")
            info = parse_filename(filename)
            file_type = info.get('file_type')
            file_date = info.get('date')
            variable = info.get('variable')
            sensor = info.get('sensor')
            satellite = info.get('satellite')
            level = info.get('level')
            file_region = info.get('file_region')
            units = None
            if file_type == 'wod':
               wod_metadata = get_wod_metadata(variable)
               units = wod_metadata['unit']
               longname = wod_metadata['long_name']
            """
              Open the data set for reading.
              """
            try:
                dataset = netCDF4.Dataset(filename, 'r')
            except Exception as e:
                print(f"Error opening {filename}: {e}")
                continue

            lat, lon ,depth, file_date = read_MetaData_group(dataset)
            # Check if we have data to iterate over
            if 'ObsValue' not in dataset.groups:
                dataset.close()
                continue
            
            # --- START VARIABLE LOOP ---
            available_vars = dataset.groups['ObsValue'].variables.keys()
            for var_name in available_vars:
                longname = var_name
                if file_type == 'icec' and longname == 'seaIceFraction':
                   units = "%"
                """
                  Get the QC Mask onece for this variable.
                  """
                qc_mask = None
                try:
                    qc_group = dataset.groups.get('EffectiveQC0')
                    if qc_group and var_name in qc_group.variables:
                        qc_flags = qc_group.variables[var_name][:]
                        qc_mask = (qc_flags > self.config.qc_threshold) 
                    else:
                      # Fallback: keep all data if QC group is missing
                        shape = dataset.groups['ObsValue'].variables[var_name].shape
                        qc_mask = np.zeros(shape, dtype=bool)
                except Exception as e:
                    print(f"Warning: QC failed for {var_name}: {e}")
                    continue

                # 2. Apply this mask to each Group (ObsValue, oman, ombg)
                for group_name in data_groups:
                    if group_name not in dataset.groups or var_name not in dataset.groups[group_name].variables:
                        continue
                   
                    group = group_name
                    var_obj = dataset.groups[group_name].variables[var_name]
                    raw_data = var_obj[:]
                    
                    # Handle FillValues + QC Mask
                    fill_mask = (raw_data == var_obj.getncattr('_FillValue')) if '_FillValue' in var_obj.ncattrs() else False
                    combined_mask = fill_mask | qc_mask
                    
                    var_values = np.ma.masked_array(raw_data, mask=combined_mask)

                    if var_values.count() == 0:
                        continue
                 
                    # 3. Calculate requested Statistics
                    stats_results = {}
                    stat_map = {
                        'mean': np.ma.mean,
                        'median': np.ma.median,
                        'StdDev': np.ma.std,
                        'minimum': np.ma.min,
                        'maximum': np.ma.max
                    }
                    for stat_key in self.config.stats:
                        if stat_key in stat_map:
                            val = stat_map[stat_key](var_values)
                            final_val = float(val) if not np.ma.is_masked(val) else None
                            print(final_val,"  ",group_name,"  ",stat_key,"  ",units) 
                            if stat_key == "mean" and units == None:
                                if file_type == 'sst':
                                   if final_val < 200 : 
                                      units = 'DegC'
                                   else:
                                      units = 'DegK' 
                            print(units) 
                            if final_val is not None:
                                harvested_data.append(HarvestedData(
                                    filenames=filename,
                                    sensor=sensor,
                                    satellite=satellite,
                                    level=level,
                                    variables=var_name, # or 'variable' from filename
                                    group=group_name,
                                    longname=longname,
                                    units=units,
                                    statistics=stat_key,
                                    value=np.float32(final_val),
                                    filetime=file_date,
                                    file_region=file_region
                                ))
                    
            dataset.close()
        return harvested_data
