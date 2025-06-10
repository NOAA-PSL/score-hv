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
VALID_STATISTICS = ('rms', 'RMS', 'mean', 'median', 'StdDev','minimum', 'maximum')

"""Variables of interest that come from the background forecast data.
Commented out variables can be uncommented to generate gridcell weighted
statistics but are in development and are currently not fully supported.
"""
VALID_VARIABLES  =  ('sst', #sea surface temperature
                     'icec', #seaIceFraction
                     'salinity',
                     'waterTemperature',
                     'seaSurfaceSalinity',
                     'seaSurfaceTemperature',
                     ''
                    )
HarvestedData = namedtuple(
    #TODO: implement depths as harvested coordinate array
    'HarvestedData',
                                            ['filenames',
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
                                             'file_region'])
def parse_filename(filename):
    """
      This method parses the input SOCA file name for variable,
      satellite, level, region, file date and time.  If the 
      filename does not have the expected number of parts,
      the program exits.
      Parameters: The filename. 
      Return: The information listed above for the filename in
              the form of the dictionary filename_info.
              - variable_type (str)
              - sensor (str or None)
              - satellite (str or None)
              - level (str or None)
              - region (str or None)
              - datetime (str)
      Raises:
              ValueError: If the filename format is unexpected or has an invalid number of parts.        
      """
    base = os.path.basename(filename)
    try:
        name_part, datetime_part, ext = base.rsplit('.', 2)
    except ValueError:
        raise ValueError(f"Filename format unexpected: {filename}")

    parts = name_part.split('_')
    # Initialize dictionary with default values
    filename_info = {'datetime': datetime_part,
                     'region': 'global',
                     'satellite': None,
                     'level': None,
                     'variable_type': parts[0],
                     'data_source': None,
                     'sensor': parts[1]}
    
    if parts[0] == 'wod' and parts[1] == 't':
        # source is World Ocean Data
        filename_info['data_source'] = parts[0]
        filename_info['variable_type'] = parts[1]
        filename_info['sensor'] = parts[2]
    elif parts[0] == 'insitu':
        # defaults for insitu data
        filename_info['sensor'] = parts[2]
    elif parts[0] == 'icec':
        filename_info['sensor'] = parts[1]
        filename_info['region'] = parts[2]
    elif parts[0] == 'sst':
        filename_info['sensor'] = parts[1]
        filename_info['satellite'] = parts[2]
        filename_info['level'] = parts[3]
    
    elif False and len(parts) == 5:
        # disabled until further information provided and boolean made more specific
        filename_info['level'] = parts[3]
        filename_info['region'] = parts[4]
    
    else:
        raise ValueError(f"ocean diags file not supported in score-hv: {filename}")

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
    if 'MetaData' not in dataset.groups:
        latitude = None
        longitude = None
    else: 
        metadata_group = dataset.groups['MetaData'] 
        if 'latitude' in metadata_group.variables:
            latitude = metadata_group['latitude'][:]
        else:
            latitude = None 
            print("'latitude' not found in metadata_vars")

        if 'longitude' in metadata_group.variables:
            longitude = metadata_group['longitude'][:]
        else:
           longitude = None 
           print("'longitude' not found in metadata_vars")

    return(latitude,longitude)

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
        self.variables = self.config_data.get('variables')
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
        self.stats = self.config_data.get('statistics')
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
            try:
                dataset = netCDF4.Dataset(filename, 'r')
            except Exception as e: 
                raise OSError (f"Failed to open NetCDF file {filename}: {e}")

            """The information about the file from the 
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
            latitude,longitude = read_MetaData_group(dataset)
            
            """We can now loop through the list of wanted groups.
            We get the values from the wanted groups and the FillValue.
            """
            for group in groups_wanted:
                if group not in dataset.groups:
                    raise ValueError(f"{group} is not in dataset.groups: {dataset.groups}")   
                else:     
                    requested_group = dataset.groups[group]
                    num_variables = len(requested_group.variables)
                    for var_name in requested_group.variables:
                        var = requested_group.variables[var_name]
                        longname = var_name 
                        if "units" in var.ncattrs():
                            units = str(var.getncattr("units"))
   
                        if '_FillValue' in groupvalue_variable.ncattrs():
                            fill_value = groupvalue_variable.getncattr('_FillValue')
                            masked_var = np.ma.masked_where(var[:] == fill_value, 
                                                            var[:])
                        else:   
                            masked_var =  np.ma.array(var[:])
                        """
                        Mask out the nans in place.
                        """
                        np.ma.masked_where(masked_var == np.nan, masked_var,
                                          copy=False)
                       
                        # Calculate the requested statistics
                        for k, statistic in enumerate(self.config.get_stats()):
                           
                            if statistic == 'rms' or statistic == 'RMS':
                                value = np.sqrt(np.ma.mean(masked_var**2))
                           
                            if statistic == 'mean':
                                value = np.ma.mean(masked_var)
                               
                            elif statistic == 'median':
                                value = np.ma.median(masked_var)
                                
                            elif statistic == 'StdDev':
                                value = np.ma.std(masked_var)
                               
                            elif statistic == 'minimum':
                                value = np.ma.min(masked_var)
                           
                            elif statistic == 'maximum':
                                value = np.ma.max(masked_var)
                                
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
                                                  float(value),
                                                  filetime,
                                                  file_region))
            dataset.close()               
            return(harvested_data)