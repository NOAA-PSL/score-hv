#!/usr/bin/env python

import os
import sys
from pathlib import Path
from collections import namedtuple
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime as dt

import xarray as xr
import numpy as np
import cftime
import netCDF4 
from netCDF4 import Dataset

from score_hv.config_base import ConfigInterface

HARVESTER_NAME = 'soca_diags'
VALID_STATISTICS = ('mean', 'median', 'StdDev',  'minimum', 'maximum')

"""Variables of interest that come from the background forecast data.
Commented out variables can be uncommented to generate gridcell weighted
statistics but are in development and are currently not fully supported.
"""
VALID_VARIABLES  =  ('sst', #sea surface temperature
                     'icec', #seaIceFraction
                    )
HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'sensor',
                                             'satellite',
                                             'level',
                                             'variable',
                                             'group',
                                             'longname',
                                             'units',
                                             'statistic',
                                             'value',
                                             'filetime',
                                             'file_region'])
def parse_filename(filename):
    """
      This method parses the input SOCA file name for variable,
      satellite, level, region, file date and time.  If the 
      filename does not have the expected number of parts,
      the program exits.
      Parameters: The filename. 
      Return: The information listed above for the filename.
      """
    base = os.path.basename(filename)
    try:
       name_part, datetime_part, ext = base.rsplit('.', 2)
    except ValueError:
       print(f"Filename format unexpected: {filename}")
       sys.exit(1)

    parts = name_part.split('_')
    filename_info = {
              'variable_type': parts[0],
              'sensor':  parts[1],
    }         
    filename_info['datetime'] = datetime_part 
    filename_info['region'] = None
    filename_info['satellite'] = None
    filename_info['level'] = None
    if len(parts) == 3:
       filename_info['region'] = parts[2]
    elif len(parts) == 4:
       filename_info['satellite'] = parts[2]
       filename_info['level'] = parts[3]
    elif len(parts) == 5:
       filename_info['platform'] = parts[2]
       filename_info['level'] = parts[3]
       filename_info['region'] = parts[4]
    else:
       print(f"Unexpected number of parts in filename: {filename}")
       sys.exit(1) 

    return filename_info

def read_MetaData_group(dataset):
    """
       This method reads the MetaData group from the 
       opened data set.
       Parameters:
                dataset- Opened Netcdf4 file.

       Returns: latitude and longitude value 
                from the MetadData group.
       """
    metadata_group = dataset.groups['MetaData']
    if 'MetaData' not in dataset.groups:
       latitude = None
       longitude = None
    else: 
       if 'latitude' in metadata_group.variables:
          latitudes = metadata_group['latitude'][:]
       else:
          latitudes = None 
          print("'latitude' not found in metadata_vars")

       if 'longitude' in metadata_group.variables:
          longitudes = metadata_group['longitude'][:]
       else:
          longitudes = None 
          print("'longitude' not found in metadata_vars")

    return(latitudes,longitudes)

@dataclass
class SOCADiagsConfig(ConfigInterface):

    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.set_config()

    def set_config(self):
        """ 
          Function to set configuration variables from given dictionary
          """
        self.harvest_filenames = self.config_data.get('filenames')
        self.set_stats()
        self.set_variables()
        self.set_depths()
        self.set_regions()

    def set_variables(self):
        """
          Set the variables specified by the config dict
          """
        self.variables = self.config_data.get('variable')
        for var in self.variables:
            if var not in VALID_VARIABLES:
                msg = ("'%s' is not a supported "
                       "variable to harvest from the soca diag files "
                       "Please reconfigure the input dictionary using only the "
                       "following variables: %r" % (var, VALID_VARIABLES))
                raise KeyError(msg)

    def set_stats(self):
        """
           Set the statistics specified by the config dict
           """
        self.stats = self.config_data.get('statistic')
        for stat in self.stats:
            if stat not in VALID_STATISTICS:
                msg = ("'%s' is not a supported statistic to harvest from "
                       "the SOCA diag files.. "
                       "Please reconfigure the input dictionary using only the "
                       "following statistics: %r" % (stat, VALID_STATISTICS))
                raise KeyError(msg)

    def set_depths(self):
        self.depths = self.config_data.get('depths')
       
    def set_regions(self):
        self.regions = self.config_data.get('regions')

    def get_stats(self):
        ''' return list of all stat types based on harvest_config '''
        return self.stats

    def get_variables(self):
        ''' return list of all variable types based on harvest_config'''
        return self.variables
    

@dataclass
class SOCADiagsHv(object):
    """ Harvester dataclass used to parse SOCA output.
    
        Parameters:
        -----------
        config: SOCADiagsConfig object containing information used to determine
                which variable to parse SOCA output.
        Methods:
        --------
        get_data: parse descriptive statistics from SOCA output.
    
                  returns a list of tuples containing specific data
    """
    config: SOCADiagsConfig = field(default_factory=SOCADiagsConfig)
     
    def get_data(self):
        depths = self.config.depths
        groups_wanted = ['ObsValue','oman','ombg']
        units = None
        for filename in self.config.harvest_filenames:
            harvested_data = list()
            filename_info = parse_filename(filename)
            print("Opening file: ",filename)
            try:
               dataset = netCDF4.Dataset(filename, 'r')
            except Exception as e: 
               raise OSError (f"Failed to open NetCDF file {filename}: {e}")
               sys.exit(1)

            print("file is open ",filename)
            """
              The information about the file from the 
              file name.
              """
            variable = filename_info['variable_type']  
            filetime_str = filename_info['datetime']
            dt_obj = dt.strptime(filetime_str, "%Y%m%d%H")
            filetime = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
            sensor = filename_info['sensor']
            file_region = filename_info['region']
            satellite = filename_info['satellite']
            level = filename_info['level']
            print(variable,"  ",sensor,"  ",file_region," ",satellite,"  ",level)
            latitude,longitude = read_MetaData_group(dataset)
            """
              We can now loop through the list of wanted groups.
              We get the values from the wanted groups and the FillValue.
              """
            for group in groups_wanted:
                if group not in dataset.groups:
                   print(group," is not in the dataset.groups ",dataset.groups)
                   sys.exit(1)
                else:            
                   requested_group = dataset.groups[group]
                   group_name = group
                   longname = list(requested_group.variables.keys())[0] 
                   for var_name in requested_group.variables:
                       groupvalue_variable = requested_group.variables[var_name]
                       var_values = np.array(groupvalue_variable[:])
                       if '_FillValue' in groupvalue_variable.ncattrs():
                          fill_value = groupvalue_variable.getncattr('_FillValue')
                          var_values[var_values == fill_value] = np.nan                                       
                   """
                     Calculate the requested statistics. Our var_values arrays are 
                     all of type <class 'numpy.ndarray'>.  We have used the fill_value
                     to put np.nan's in the for all values to to the fill_values so we 
                     can calculate the statistics.
                     """
                   for j, statistic in enumerate(self.config.get_stats()):
                       #print(statistic,"  ",group,"  ",longname,"  ",variable)
                       group = group_name
                       if statistic == 'mean':
                          value = np.nanmean(var_values)
                             
                       elif statistic == 'median':
                            value = np.nanmedian(var_values)

                       elif statistic == 'StdDev':
                            value = np.nanstd(var_values)

                       elif statistic == 'minimum':
                            value = np.nanmin(var_values)

                       elif statistic == 'maximum':
                            value = np.nanmax(var_values)

                       harvested_data.append(HarvestedData(
                                            filename,
                                            sensor,
                                            satellite,
                                            level,
                                            variable,
                                            group,
                                            longname,
                                            units,
                                            statistic,
                                            np.float32(value),
                                            filetime,
                                            file_region))
        print("at end ",filename)
        dataset.close() 
        return(harvested_data)
