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

HARVESTER_NAME = 'wod_insitu_meta_netcdf'

HarvestedData = namedtuple(
    'HarvestedData',
    [
        'filename',
        'obs_day',
        'min_date_time',
        'max_date_time',
        'min_depth',
        'max_depth',
        'min_file_depth',
        'max_file_depth',
        'num_vars',
        'variable_name',
        'var_count',
        'sensor',
        'casts',
    ]
)

@dataclass
class WodInsituMetaCfg(ConfigInterface):
    """
        Dataclass to hold and provide configuration information pertaining to
        how the harvester should retrieve the ioda metadata..
    
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
class WodInsituMetaHv:
    """
    Harvester dataclass used to parse metadata from wod insitu nc files

    Parameters:
    -----------
    config: WodInsituMetaCfg object containing information used to determine what file to get info for

    Methods:
    --------
    get_data: gets the metadata for a specified file in netcdf format
    """
    config: WodInsituMetaCfg = field(default_factory=WodInsituMetaCfg)

    def get_data(self):
        """
        Harvests metadata for wod insitu files including number of observations and variables contained within. 

        Returns
        -------
        harvested_data: list of Harvested data for a given file, one per variable, some data is file level for every variable

        'filename',
        'obs_day',
        'file_date_time',
        'min_date_time',
        'max_date_time',
        'num_locs',
        'min_depth',
        'max_depth',
        'min_file_depth',
        'max_file_depth',
        'num_vars',
        'variable_name',
        'var_count',
        'sensor',
        'casts'
        """
        harvested_data = []
        dataset = Dataset(self.config.harvest_filename, 'r')

        #get the basic variable obs counts for all _obs dimensions in the file
        #exclude depth and JulianDay which are not scientific variables but additional dimensions 
        variable_counts = {
            dim[:-4]: {'count': dataset.dimensions[dim].size, 'min_depth': None, 'max_depth': None}
            for dim in dataset.dimensions
            if dim.endswith("_obs") and dim not in {"z_obs", "JulianDay_obs", "Latitude_obs", "Longitude_obs"}
        }
        
        min_file_depth = None
        max_file_depth = None
        #get the min and max depth as appropriate
        if 'z' in dataset.variables:
            z_var = dataset.variables['z'][:]
            min_file_depth = np.min(z_var) if np.issubdtype(z_var.dtype, np.floating) else None
            max_file_depth = np.max(z_var) if np.issubdtype(z_var.dtype, np.floating) else None

            #make sure to get min and max depth for the variable size, in case it differs 
            start = 0
            for var, stats in variable_counts.items():
                size = stats['count']
                if size == 0:
                    continue

                # Extract corresponding depths using the range from start to start+size
                var_depths = z_var[start:start+size]
                if len(var_depths) > 0:
                    variable_counts[var]['min_depth'] = np.nanmin(var_depths)
                    variable_counts[var]['max_depth'] = np.nanmax(var_depths)

        #get the number of casts
        casts = None
        if 'casts' in dataset.dimensions:
            casts = dataset.dimensions['casts'].size

        time_min = None
        time_max = None
        if 'time' in dataset.variables:
            time_var = dataset.variables['time']
            time_values = time_var[:]
            
            # Extract time units
            time_units = time_var.units if hasattr(time_var, 'units') else None
            
            if time_units:
                # Convert time values to datetime
                time_dates = num2date(time_values, units=time_units)
                
                # Get min and max
                time_min = format_datetime_string(min(time_dates))
                time_max = format_datetime_string(max(time_dates))

        filename_parsed = parse_filename(self.config.harvest_filename) 
        sensor = filename_parsed['sensor']
        filename = filename_parsed['filename']
        obs_day = filename_parsed['formatted_datetime_str']

        num_vars = len(variable_counts)
        for variable_name, data in variable_counts.items():
            harvested_data.append(
                HarvestedData(
                    filename,
                    obs_day,
                    time_min,
                    time_max,
                    data['min_depth'],
                    data['max_depth'],
                    min_file_depth,
                    max_file_depth,
                    num_vars,
                    variable_name,
                    data['count'],
                    sensor, 
                    casts,
                )
            )

        return harvested_data


def format_datetime_string(datetime_obj):
    return datetime_obj.strftime("%Y-%m-%d %H:%M:%S")

def parse_filename(file_path):
    # Extract the file name from the full path
    filename = os.path.basename(file_path)
    
    # Regular expression to match the filename pattern
    pattern = r'^wod_(?P<sensor>[^_]+)_(?P<datetime>\d{4}-\d{2}-\d{2}T\d{2})\.nc$'
    
    match = re.match(pattern, filename)
    if match:
        sensor = match.group("sensor")
        datetime_str = match.group("datetime")

        dt_obj = datetime.strptime(datetime_str, "%Y-%m-%dT%H")
        
        formatted_datetime_str = format_datetime_string(dt_obj)
        
        return {
            'filename': filename,
            'formatted_datetime_str': formatted_datetime_str,
            'datetime_obj': dt_obj,
            'sensor': sensor
        }
    else:
        raise ValueError(f"Filename '{filename}' does not match the expected wod insitu format pattern.")