"""
Copyright 2025 NOAA
All rights reserved.

Collection of methods to retrieve metadata from ioda formatted nc files.

"""
from collections import namedtuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from netCDF4 import Dataset
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
        'file_date_time',
        'min_date_time',
        'max_date_time',
        'num_locs',
        'min_depth',
        'max_depth',
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
        'num_vars',
        'variable_name',
        'var_count',
        'sensor',
        'casts',
        """
        harvested_data = []
        dataset = Dataset(self.config.harvest_filename, 'r')

       

        filename_parsed = parse_filename(self.config.harvest_filename) 
        sensor = filename_parsed['sensor']
        filename = filename_parsed['filename']
        obs_day = filename_parsed['formatted_datetime_str']

     
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