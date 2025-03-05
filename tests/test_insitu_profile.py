#!/usr/bin/env python

import os
import sys
import re
from pathlib import Path 
import numpy as np
from datetime import datetime
import pytest
import yaml
import netCDF4
from netCDF4 import Dataset

from score_hv import hv_registry
from score_hv.harvester_base import harvest
from score_hv.yaml_utils import YamlLoader
from score_hv.harvesters.innov_netcdf import Region, InnovStatsCfg

TEST_DATA_FILE_NAMES = [
                        'insitu_profile_argo.2021070300.nc4'
                       ]

DATA_DIR = os.path.join(Path(__file__).parent.parent.resolve(), 'src', 'score_hv', 'data')

CONFIGS_DIR = 'configs'
PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
TEST_DATA_PATH = os.path.join(PYTEST_CALLING_DIR, 'data')
SOCA_PATH = [os.path.join(TEST_DATA_PATH,
                         file_name) for file_name in TEST_DATA_FILE_NAMES]

VALID_CONFIG_DICT = {'harvester_name': hv_registry.SOCA_DIAGS,
                     'filenames' : SOCA_PATH,
                     'statistic': ['mean', 'median', 'StdDev',  'minimum', 'maximum'],
                     'variable': ['salinity','waterTemperature'],
                     }

def test_soca_harvester():
    data1 = harvest(VALID_CONFIG_DICT)
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==SOCA_PATH[0]

def verify_filename_components():
    expected_variable_names = ['salinity','waterTemperature']
    data1 = harvest(VALID_CONFIG_DICT)
    for item in data1:
        if item.variable not in expected_variable_names:
           raise ValueError(f"Error: {item.variable} is not in the expected variable list.") 
        assert item.sensor == None   
        assert item.satellite == 'argo'
        assert item.level == None   

def verify_datetime():
    data1 = harvest(VALID_CONFIG_DICT) 
    date_str = "2021070300"
    date_obj = datetime.strptime(date_str, "%Y%m%d%H")
    filetime_str = data1[0].filetime
    filetime_dt = datetime.strptime(filetime_str, "%Y-%m-%d %H:%M:%S")
    assert date_obj == filetime_dt 

def verify_groups():
    data1 = harvest(VALID_CONFIG_DICT)
    groups_wanted = ['ObsValue', 'oman', 'ombg']
    for data in data1:
        assert data.group in groups_wanted, f"Unexpected group: {data.group}"

def calculate_statistic(statistic,group,var_name):
    """
    Computes the specified statisticis for a given variable in the provided group.
    
    Parameters:
        group (netCDF4.Group): The group from the netCDF dataset.
        var_name (str): The name of the variable in the group.
    
    Returns:
        dict: A dictionary with statistic names as keys and computed values as values. 
    """
    variable = group.variables[var_name]
    data = variable[:]  

    # Check if the variable has a '_FillValue' attribute and replace it with NaN
    if '_FillValue' in variable.ncattrs():
        fill_value = variable.getncattr('_FillValue')

    if np.ma.isMaskedArray(data):
       data = np.ma.filled(data, np.nan)  
    else:
       data[data == fill_value] = np.nan  
  

    if statistic == 'mean':
         value = np.nanmean(data)

    elif statistic == 'median':
         value = np.nanmedian(data)

    elif statistic == 'StdDev':
         value = np.nanstd(data)

    elif statistic == 'minimum':
         value = np.nanmin(data)

    elif statistic == 'maximum':
         value = np.nanmax(data)
   
    return value

def get_harvested_statistic_value(statistic, thegroup, var_name):
    """
    Retrieve the harvested statistic value that matches the provided statistic,
    group, and variable name.

    Parameters:
        statistic (str): The statistic to look for (e.g., 'mean', 'median').
        thegroup (str): The group name to match (e.g., 'ObsValue').
        var_name (str): The variable name to match (e.g., 'salinity').

    Returns:
        The value associated with the matching HarvestedData record, or None if not found.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    for item in data1:
        if item.group == thegroup:
           if item.statistic == statistic:
              if item.variable == var_name:
                 return item.value

def verify_group_mean_values():

    filename = SOCA_PATH[0]  
    try: 
       dataset = netCDF4.Dataset(filename,'r')
    except Exception as e: 
       raise OSError(f"Failed to open NetCDF file : insitu_profile_argo.2021070300.nc4 {e}")
    """
      calculate the statistic from the open dataset..
    """
    
    statistic = 'mean'  
    groups_wanted = ['ObsValue','oman','ombg']
    for group_name in groups_wanted:
        requested_group = dataset.groups[group_name]
        num_variables = len(requested_group.variables)
        variable_names = list(requested_group.variables.keys())        
        for var_name in variable_names: 
            thegroup = dataset.groups[group_name]
            calculated_value = calculate_statistic(statistic,thegroup,var_name)
            harvested_value = get_harvested_statistic_value(statistic,group_name,var_name) 
            assert calculated_value == harvested_value
    dataset.close() 
    
def verify_group_median_values():

    filename = SOCA_PATH[0]  
    try: 
       dataset = netCDF4.Dataset(filename,'r')
    except Exception as e: 
       raise OSError(f"Failed to open NetCDF file : insitu_profile_argo.2021070300.nc4 {e}")
    """
      calculate the statistic from the open dataset..
      """
    
    statistic = 'median'  
    groups_wanted = ['ObsValue','oman','ombg']
    for group_name in groups_wanted:
        requested_group = dataset.groups[group_name]
        num_variables = len(requested_group.variables)
        variable_names = list(requested_group.variables.keys())        
        for var_name in variable_names: 
            thegroup = dataset.groups[group_name]
            calculated_value = calculate_statistic(statistic,thegroup,var_name)
            harvested_value = get_harvested_statistic_value(statistic,group_name,var_name) 
            print("median  ",var_name,"  ",group_name,"  ",calculated_value,"  ",harvested_value)
            assert calculated_value == harvested_value
    dataset.close() 

def verify_group_standard_deviation_values():

    filename = SOCA_PATH[0]  
    try: 
       dataset = netCDF4.Dataset(filename,'r')
    except Exception as e: 
       raise OSError(f"Failed to open NetCDF file : insitu_profile_argo.2021070300.nc4 {e}")
    
    """
      calculate the statistic from the open dataset..
      """
    statistic = 'StdDev'  
    groups_wanted = ['ObsValue','oman','ombg']
    for group_name in groups_wanted:
        requested_group = dataset.groups[group_name]
        num_variables = len(requested_group.variables)
        variable_names = list(requested_group.variables.keys())        
        for var_name in variable_names: 
            thegroup = dataset.groups[group_name]
            calculated_value = calculate_statistic(statistic,thegroup,var_name)
            harvested_value = get_harvested_statistic_value(statistic,group_name,var_name) 
            assert calculated_value == harvested_value
    dataset.close() 

def verify_group_minimum_values():

    filename = SOCA_PATH[0]  
    try: 
       dataset = netCDF4.Dataset(filename,'r')
    except Exception as e: 
       raise OSError(f"Failed to open NetCDF file : insitu_profile_argo.2021070300.nc4 {e}")
    
    """
      calculate the statistic from the open dataset..
      """
    statistic = 'minimum'  
    groups_wanted = ['ObsValue','oman','ombg']
    for group_name in groups_wanted:
        requested_group = dataset.groups[group_name]
        num_variables = len(requested_group.variables)
        variable_names = list(requested_group.variables.keys())        
        for var_name in variable_names: 
            thegroup = dataset.groups[group_name]
            calculated_value = calculate_statistic(statistic,thegroup,var_name)
            harvested_value = get_harvested_statistic_value(statistic,group_name,var_name) 
            assert calculated_value == harvested_value
    dataset.close() 

def verify_group_maximum_values():

    filename = SOCA_PATH[0]  
    try: 
       dataset = netCDF4.Dataset(filename,'r')
    except Exception as e: 
       sys.exit(1)
       raise OSError(f"Failed to open NetCDF file : insitu_profile_argo.2021070300.nc4 {e}")
    
    """
      calculate the statistic from the open dataset..
      """
    statistic = 'maximum'  
    groups_wanted = ['ObsValue','oman','ombg']
    for group_name in groups_wanted:
        requested_group = dataset.groups[group_name]
        num_variables = len(requested_group.variables)
        variable_names = list(requested_group.variables.keys())        
        for var_name in variable_names: 
            thegroup = dataset.groups[group_name]
            calculated_value = calculate_statistic(statistic,thegroup,var_name)
            harvested_value = get_harvested_statistic_value(statistic,group_name,var_name) 
            assert calculated_value == harvested_value
    dataset.close() 

def main():
    test_soca_harvester()
    verify_filename_components()
    verify_datetime()
    verify_groups()
    verify_group_mean_values()
    verify_group_median_values()
    verify_group_standard_deviation_values()
    verify_group_minimum_values()
    verify_group_maximum_values()

if __name__=='__main__':
    main()
