"""
Copyright 2025 NOAA
All rights reserved.

Collection of methods to retrieve metadata from formatted nc files for ozone data.

"""
from collections import namedtuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from netCDF4 import Dataset, num2date
import re
import os 
import numpy as np

from score_hv.config_base import ConfigInterface

HARVESTER_NAME = 'ozone_meta_netcdf'

HarvestedData = namedtuple(
    'HarvestedData',
    [
        'filename',
        'obs_day',
        'min_date_time',
        'max_date_time',
        'min_pressure',
        'max_pressure',
        'ozone_count',
        'sensor'
    ]
)

@dataclass
class OzoneMetaCfg(ConfigInterface):
    """
        Dataclass to hold and provide configuration information pertaining to
        how the harvester should retrieve the ozone metadata.
    
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
class OzoneMetaHv:
    """
    Harvester dataclass used to parse metadata from ozone nc files

    Parameters:
    -----------
    config: OzoneMetaCfg object containing information used to determine what file to get info for

    Methods:
    --------
    get_data: gets the metadata for a specified file in netcdf format
    """
    config: OzoneMetaCfg = field(default_factory=OzoneMetaCfg)

    def get_data(self):
        """
        Harvests metadata for ozone netcdf files including number of observations and min and max pressure. 

        Returns
        -------
        harvested_data: list of Harvested data for a given file, one per variable, some data is file level for every variable

        'filename',
        'obs_day',
        'min_date_time',
        'max_date_time',
        'min_pressure',
        'max_pressure',
        'ozone_count',
        'sensor
        """
        harvested_data = []
        dataset = Dataset(self.config.harvest_filename, 'r')


        # --- Get ozone data (2D: nprofiles x nlevs) ---
        ozone = dataset.variables['ozone'][:]  # shape: (nprofiles, nlevs)
        valid_ozone_count = np.count_nonzero(~np.isnan(ozone))

        # --- Read profile-level datetime components ---
        year   = np.ma.filled(dataset.variables['year'][:], np.nan)
        month  = np.ma.filled(dataset.variables['month'][:], np.nan)
        day    = np.ma.filled(dataset.variables['day'][:], np.nan)
        hour   = np.ma.filled(dataset.variables['hour'][:], np.nan)
        minute = np.ma.filled(dataset.variables['minute'][:], np.nan)
        second = np.ma.filled(dataset.variables['second'][:], np.nan)
        press = np.ma.filled(dataset.variables['press'][:], np.nan) 


        # --- Build datetime objects safely ---
        nprofiles = len(year)
        datetimes = []

        for i in range(nprofiles):
            components = [year[i], month[i], day[i], hour[i], minute[i], second[i]]
            if np.isnan(components).any():
                continue
            try:
                dt = datetime(int(year[i]), int(month[i]), int(day[i]),
                            int(hour[i]), int(minute[i]), int(second[i]))
                datetimes.append(dt)
            except (ValueError, TypeError):
                continue
        
        min_dt = None
        max_dt = None
        if datetimes:
            min_dt = format_datetime_string(min(datetimes))
            max_dt = format_datetime_string(max(datetimes))

        # --- Compute min and max pressure, excluding NaNs ---
        min_press = np.nanmin(press)
        max_press = np.nanmax(press)
       

        filename_parsed = parse_filename(self.config.harvest_filename) 
        sensor = filename_parsed['sensor']
        filename = filename_parsed['filename']
        obs_day = filename_parsed['formatted_datetime_str']

        harvested_data.append(
            HarvestedData(
                filename,
                obs_day,
                min_dt,
                max_dt,
                min_press, 
                max_press,
                valid_ozone_count,
                sensor, 
            )
        )

        return harvested_data


def format_datetime_string(datetime_obj):
    return datetime_obj.strftime("%Y-%m-%d %H:%M:%S")

def parse_filename(file_path):
    # Extract the file name from the full path
    filename = os.path.basename(file_path)
    
    # Regular expression to match the filename pattern
    pattern = r'^(?P<sensor>[^.]+)\.(?P<date>\d{8})_(?P<hour>\d{2})z\.nc$'
    
    match = re.match(pattern, filename)
    if match:
        sensor = match.group("sensor")
        date_str = match.group("date")
        hour_str = match.group("hour")

        dt_obj = datetime.strptime(date_str + hour_str, "%Y%m%d%H")        
        formatted_datetime_str = format_datetime_string(dt_obj)
        
        return {
            'filename': filename,
            'formatted_datetime_str': formatted_datetime_str,
            'datetime_obj': dt_obj,
            'sensor': sensor
        }
    else:
        raise ValueError(f"Filename '{filename}' does not match the expected ozone netcdf format pattern.")