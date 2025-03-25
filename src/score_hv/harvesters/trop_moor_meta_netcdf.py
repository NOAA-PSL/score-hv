"""
Copyright 2025 NOAA
All rights reserved.

Collection of methods to retrieve metadata from ioda formatted nc files.

"""
from collections import namedtuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from netCDF4 import Dataset, num2date
import re
import os 
import numpy as np

from score_hv.config_base import ConfigInterface

HARVESTER_NAME = 'trop_moor_meta_netcdf'

AVAILABLE_VARIABLES = ('T_25', 'S_41', 'U_320', 'V_321', 'T_20')

VAR_DICT = {'T_25' : "SST", 'S_41': "SALINITY", 'U_320': "ZONAL CURRENT",
             'V_321' : "MERIDIONAL CURRENT", 'T_20': "TEMPERATURE"}

HarvestedData = namedtuple(
    'HarvestedData',
    [
        'filename',
        'obs_day',
        'min_date_time',
        'max_date_time',
        'array',
        'platform_code',
        'variable_name',
        'variable_code',
        'var_count',
        'min_depth',
        'max_depth',
    ]
)

@dataclass
class TropMoorMetaCfg(ConfigInterface):
    """
        Dataclass to hold and provide configuration information pertaining to
        how the harvester should retrieve the ioda metadata.
    
        Parameters:
        -----------
        config_data: dict - contains configuration data parsed from either an
                            input yaml file or input dict
    """

    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
         self.set_config()
    
    def set_config(self):
        """ function to set configuration variables from given dictionary
        """ 
        self.harvest_filename = self.config_data.get('filename')

@dataclass
class TropMoorMetaHv:
    """
        Harvester dataclass used to parse metadata from tropical mooring nc files

        Parameters:
        -----------
        config: TropMoorMetaCfg object containing information used to determine what file to get info for

        Methods:
        --------
        get_data: gets the metadata for a specified file in netcdf format
    """
    config: TropMoorMetaCfg = field(default_factory=TropMoorMetaCfg)

    def get_data(self):
        """
            Harvests metadata for wod insitu files including number of observations and variables contained within. 

            Returns
            -------
            harvested_data: list of Harvested data for a given file, one per variable, some data is file level for every variable

            'filename',
            'obs_day',
            'min_date_time',
            'max_date_time',
            'array',
            'platform_code',
            'variable_name',
            'variable_code',
            'var_count',
            'min_depth',
            'max_depth',
        """
        harvested_data = []
        dataset = Dataset(self.config.harvest_filename, 'r')

        platform_code = dataset.getncattr('platform_code') if 'platform_code' in dataset.ncattrs() else None
        array = dataset.getncattr('array') if 'array' in dataset.ncattrs() else None

        filename_parsed = parse_filename(self.config.harvest_filename) 
        filename = filename_parsed['filename']
        obs_day = filename_parsed['formatted_datetime_str']

        depth = dataset.variables['depth'][:]
        time = dataset.variables['time'][:]
        time_units = dataset.variables['time'].units
        #get the variable, remove NaN, then take count 
        for var in AVAILABLE_VARIABLES:
            if var in dataset.variables:
                variable = dataset.variables[var][:]

                fill_value = getattr(dataset.variables[var], '_FillValue', 
                      getattr(dataset.variables['var'], 'missing_value', np.nan))

                variable = np.where(variable == fill_value, np.nan, variable)

                # Remove NaN values
                variable_no_nan = variable[~np.isnan(variable)]

                # Get the total number of values
                var_count = variable_no_nan.size

                # Find valid (non-NaN) values
                valid_mask = ~np.isnan(variable)

                # Get the corresponding depths where var has valid values
                valid_depths = depth[np.any(valid_mask, axis=(0, 2, 3))]

                # Get min and max depth
                min_depth = np.min(valid_depths)
                max_depth = np.max(valid_depths)

                # Get the corresponding times where var has valid values
                valid_times = time[np.any(valid_mask, axis=(1, 2, 3))]

                # Convert times to datetime using num2date
                valid_times_converted = num2date(valid_times, units=time_units)

                # Get min and max valid time
                min_time = np.min(valid_times_converted)
                max_time = np.max(valid_times_converted)

                min_date_time = format_datetime_string(min_time)
                max_date_time = format_datetime_string(max_time)

                harvested_data.append(
                    HarvestedData(
                        filename, 
                        obs_day,
                        min_date_time,
                        max_date_time,
                        array,
                        platform_code,
                        VAR_DICT[var],
                        var,
                        var_count,
                        min_depth,
                        max_depth
                    )
                )
                
def format_datetime_string(datetime_obj):
    return datetime_obj.strftime("%Y-%m-%d %H:%M:%S")

def parse_filename(file_path):
    # Extract the file name from the full path
    filename = os.path.basename(file_path)
    
    # Regular expression to match the filename pattern
    #TODO: put the correct pattern here based on the finalized file pattern
    pattern = r'^wod_(?P<sensor>[^_]+)_(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2})\.nc$'
    
    match = re.match(pattern, filename)
    if match:
        datetime_str = match.group("datetime")

        dt_obj = datetime.strptime(datetime_str, "%Y-%m-%dT%H")
        
        formatted_datetime_str = format_datetime_string(dt_obj)
        
        return {
            'filename': filename,
            'formatted_datetime_str': formatted_datetime_str,
            'datetime_obj': dt_obj,
        }
    else:
        raise ValueError(f"Filename '{filename}' does not match the expected tropical mooring format pattern.")


