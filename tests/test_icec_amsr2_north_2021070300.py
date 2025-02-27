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
                        'icec_amsr2_north.2021070300.nc4'
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
                     'variable': ['icec'],
                     }

def test_soca_harvester():
    data1 = harvest(VALID_CONFIG_DICT)
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==SOCA_PATH[0]

def verify_filename_components():
    data1 = harvest(VALID_CONFIG_DICT)
    data = data1[0]
    assert data.variable == 'icec'
    assert data.sensor == 'amsr2'
    assert data.file_region == 'north'   

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
        if data.group not in groups_wanted:
           print(f"{data.group} is not in the wanted groups.")
           sys.exit(1)

def calculate_statistic(statistic,thegroup):
    print("in calculate statistic ",statistic)
    for var_name in thegroup.variables:
        variable = thegroup.variables[var_name] 
        var_values = np.array(variable[:]) 
        if '_FillValue' in variable.ncattrs():
           fill_value = variable.getncattr('_FillValue')
           var_values[var_values == fill_value] = np.nan
           if statistic == 'mean':
              statistic_value = np.nanmean(var_values)
           elif statistic == 'median':
              statistic_value = np.nanmedian(var_values)
           elif statistic == 'StdDev':
              print("in the StdDev")
              statistic_value = np.nanstd(var_values)

    return(statistic_value)

def get_harvested_statistic_value(statistic):
    data1 = harvest(VALID_CONFIG_DICT)
    harvested_data = {
        data.group: data.value for data in data1 if data.statistic == statistic
    }
    return harvested_data    

def verify_group_mean_values():
    print("in verify group mean values")
    statistic = 'mean'
    
    filename = SOCA_PATH[0]  
    try: 
       dataset = netCDF4.Dataset(filename,'r')
    except Exception as e: 
       raise OSError(f"Failed to open NetCDF file : icec_amsr2_north.2021070300.nc4 {e}")
       sys.exit(1)
    """
      calculate the statistic from the open dataset..
      """
    groups_wanted = ['ObsValue','oman','ombg']
    for group_name in groups_wanted: 
        thegroup = dataset.groups[group_name]
        calculated_mean = calculate_statistic(statistic,thegroup)
        harvested_mean = get_harvested_statistic_value(statistic)       
#        print(group_name,"  ",calculated_mean,"  ",harvested_mean)
        assert calculated_mean == harvested_mean[group_name]
    dataset.close() 

def verify_group_median_values():
    statistic = 'median'

    filename = SOCA_PATH[0]
    try:
       dataset = netCDF4.Dataset(filename,'r')
    except Exception as e:
       raise OSError(f"Failed to open NetCDF file : icec_amsr2_north.2021070300.nc4 {e}")
       sys.exit(1)
    """
      calculate the statistic from the open dataset..
      """
    groups_wanted = ['ObsValue','oman','ombg']
    for group_name in groups_wanted:
        thegroup = dataset.groups[group_name]
        calculated_median = calculate_statistic(statistic,thegroup)
        harvested_median = get_harvested_statistic_value(statistic)
#        print(group_name,"  ",calculated_median,"  ",harvested_median)
        assert calculated_median == harvested_median[group_name]
    dataset.close()

def verify_group_StdDev_values():
    print("in verify_group_StdDev")
    statistic = 'StdDev'

    filename = SOCA_PATH[0]  
    try: 
       dataset = netCDF4.Dataset(filename,'r')
    except Exception as e: 
       raise OSError(f"Failed to open NetCDF file : icec_amsr2_north.2021070300.nc4 {e}")
       sys.exit(1)

    groups_wanted = ['ObsValue','oman','ombg']
    for group_name in groups_wanted: 
        thegroup = dataset.groups[group_name]
        calculated_std = calculate_statistic(statistic,thegroup)
        harvested_std = get_harvested_statistic_value(statistic)       
        #print(group_name,"  ",calculated_std,"  ",harvested_std)
        assert calculated_std == harvested_std[group_name]
    dataset.close() 

def main():
    test_soca_harvester()
    verify_filename_components()
    verify_datetime()
    verify_groups()
    verify_group_mean_values()
    verify_group_median_values() 
    verify_group_StdDev_values()

if __name__=='__main__':
    main()
