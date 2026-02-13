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
                     'statistics': ['mean', 'median', 'StdDev',  'minimum', 'maximum'],
                     'variables': ['icec'],
                     }

def test_soca_harvester():
    data1 = harvest(VALID_CONFIG_DICT)
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==SOCA_PATH[0]

def test_verify_filename_components():
    data1 = harvest(VALID_CONFIG_DICT)
    data = data1[0]
    assert data.variables == 'seaIceFraction'
    assert data.sensor == 'amsr2'
    assert data.file_region == 'north'   
    
def test_verify_datetime():
    data1 = harvest(VALID_CONFIG_DICT) 
    expected_file_dt = datetime.strptime("2021-07-02 23:16:58", "%Y-%m-%d %H:%M:%S")
    harvester_file_dt = data1[0].filetime
    print(expected_file_dt,"  ",harvester_file_dt)
    assert expected_file_dt ==  harvester_file_dt 

def test_verify_groups():
    data1 = harvest(VALID_CONFIG_DICT)
    groups_wanted = ['ObsValue', 'oman', 'ombg']
    for data in data1:
        assert data.group in groups_wanted, f"Unexpected group: {data.group}"

def get_harvested_statistic_value(statistic):
    data1 = harvest(VALID_CONFIG_DICT)
    harvested_data = {
        data.group: data.value for data in data1 if data.statistics == statistic
    }
    return harvested_data    

def test_verify_group_mean_values(tolerance=0.001):
    """
      The mean values that are hard coded in this method were
      calculated with the NCO function 
      ncwa -g groupname -v seaIceFraction -a Location icec_amsr2_north.2021070300.nc4 mean.nc
      mean.nc is then read with ncks -H -C -v seaIceFraction mean.nc to get the mean value.
      calculated_values are 0.5933418, 0.06660749, 0.1327579
      """
    data1 = harvest(VALID_CONFIG_DICT) 
    calculated_means = [0.5933418,0.06660749,0.1327579]
    groups_wanted = ['ObsValue','oman','ombg'] 
    group_index = 0
    # Filter out only the data that has the "mean" statistic
    harvested_data = [data for data in data1 if data.statistics == 'mean']
    assert len(harvested_data) == len(groups_wanted), "Error: Mismatch between expected groups and harvested data."
   
   # Iterate over harvested data and check means for each group
    group_index = 0
    for data in harvested_data:
        group_name = data.group
        harvested_mean = data.value
        calculated_value = calculated_means[group_index]
        # Verify that the harvested mean is within tolerance of the calculated mean
        print(harvested_mean,"  ",calculated_value)
        assert abs(harvested_mean - calculated_value) <= tolerance, f"Mean value mismatch for {group_name}"
        group_index += 1
       
def test_verify_group_median_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT) 
    calculated_medians = [0.949999988079071,0.01528690755367279,0.043333768844604485]
    groups_wanted = ['ObsValue','oman','ombg'] 
    group_index = 0
    harvested_data = [data for data in data1 if data.statistics == 'median']
    assert len(harvested_data) == len(groups_wanted), "Error: Mismatch between expected groups and harvested data."

    group_index = 0
    for data in harvested_data:
        group_name = data.group
        harvested_medians = data.value
        calculated_value = calculated_medians[group_index]
        # Verify that the harvested mean is within tolerance of the calculated median 
        assert abs(harvested_medians - calculated_value) <= tolerance, f"Median value mismatch for {group_name}"
        group_index += 1

def test_verify_group_StdDev_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT) 
    calculated_StdDevs = [0.46483881994362,0.15594015101052516,0.20401885665594757]
    groups_wanted = ['ObsValue','oman','ombg'] 
    group_index = 0
    harvested_data = [data for data in data1 if data.statistics == 'StdDev']
    assert len(harvested_data) == len(groups_wanted), "Error: Mismatch between expected groups and harvested data."
  
    group_index = 0
    for data in harvested_data:
        group_name = data.group
        harvested_StdDevs = data.value
        calculated_value = calculated_StdDevs[group_index]
        assert abs(harvested_StdDevs - calculated_value) <= tolerance, f"Standard Deviation value mismatch for {group_name}"
        group_index += 1

def test_verify_group_minimum_values(tolerance=0.001):
    """
      The mean values that are hard coded in this method were
      calculated with the NCO function
      ncwa -g groupname -v seaIceFraction -a Location icec_amsr2_north.2021070300.nc4 mean.nc
      mean.nc is then read with ncks -H -C -v seaIceFraction mean.nc to get the mean value.
      calculated_values are 0.5933418, 0.06660749, 0.1327579
      """
    data1 = harvest(VALID_CONFIG_DICT)
    calculated_minimums = [0.0,-0.8637589812278748,-0.8629218339920045]
    groups_wanted = ['ObsValue','oman','ombg']
    group_index = 0
    harvested_data = [data for data in data1 if data.statistics == 'minimum']
    assert len(harvested_data) == len(groups_wanted), "Error: Mismatch between expected groups and harvested data."
  
    group_index = 0
    for data in harvested_data:
        group_name = data.group
        harvested_minimum = data.value
        calculated_value = calculated_minimums[group_index]
        assert abs(harvested_minimum - calculated_value) <= tolerance, f"Minimum value mismatch for {group_name}"
        group_index += 1

def test_verify_group_maximum_values(tolerance=0.001):
    """
      The mean values that are hard coded in this method were
      calculated with the NCO function
      ncwa -g groupname -v seaIceFraction -a Location icec_amsr2_north.2021070300.nc4 mean.nc
      mean.nc is then read with ncks -H -C -v seaIceFraction mean.nc to get the mean value.
      calculated_values are 0.5933418, 0.06660749, 0.1327579
      """
    data1 = harvest(VALID_CONFIG_DICT)
    calculated_maximums = [1.0,1.0,1.0]
    groups_wanted = ['ObsValue','oman','ombg']
    group_index = 0
    harvested_data = [data for data in data1 if data.statistics == 'maximum']
    assert len(harvested_data) == len(groups_wanted), "Error: Mismatch between expected groups and harvested data."
    
    group_index = 0
    for data in harvested_data:
        group_name = data.group
        harvested_maximum = data.value
        calculated_value = calculated_maximums[group_index]
        assert abs(harvested_maximum - calculated_value) <= tolerance, f" Maximum value mismatch for {group_name}"
        group_index += 1

def main():
    test_soca_harvester()
    test_verify_filename_components()
    test_verify_datetime()
    test_verify_groups()
    test_verify_group_mean_values()
    test_verify_group_median_values() 
    test_verify_group_StdDev_values()
    test_verify_group_minimum_values()
    test_verify_group_maximum_values()

if __name__=='__main__':
    main()
