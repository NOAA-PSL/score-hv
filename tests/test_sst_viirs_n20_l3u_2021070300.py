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
                        'sst_viirs_n20_l3u.2021070300.nc4'
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
                     'variable': ['sst'],
                     }

def test_soca_harvester():
    data1 = harvest(VALID_CONFIG_DICT)
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==SOCA_PATH[0]

def verify_filename_components():
    data1 = harvest(VALID_CONFIG_DICT)
    data = data1[0]
    assert data.variable == 'seaSurfaceTemperature'
    assert data.sensor == 'viirs'
    assert data.satellite == 'n20'
    assert data.level == 'l3u'

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

def verify_group_mean_values(tolerance=0.001):
    """
      Mean values that are hard coded here were calculated offline.
      """
    data1 = harvest(VALID_CONFIG_DICT) 
    calculated_means = [18.924038657133483,0.06212510113054594,0.07588130216644204]
    groups_wanted = ['ObsValue','oman','ombg'] 
    group_index = 0
    # Filter out only the data that has the "mean" statistic
    harvested_data = [data for data in data1 if data.statistic == 'mean']
    if len(harvested_data) != len(groups_wanted):
       print("Error: Mismatch between expected groups and harvested data.")
       sys.exit(1)

    # Iterate over harvested data and check means for each group
    group_index = 0
    for data in harvested_data:
        group_name = data.group
        harvested_mean = data.value
        calculated_value = calculated_means[group_index]
        # Verify that the harvested mean is within tolerance of the calculated mean
        assert abs(harvested_mean - calculated_value) <= tolerance, f"Mean value mismatch for {group_name}"
        group_index += 1
       
def verify_group_median_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT) 
    calculated_medians = [22.409034729003906,0.029189025983214375,0.055334743112325675]
    groups_wanted = ['ObsValue','oman','ombg'] 
    group_index = 0
    harvested_data = [data for data in data1 if data.statistic == 'median']
    if len(harvested_data) != len(groups_wanted):
       print("Error: Mismatch between expected groups and harvested data.")
       sys.exit(1)

    group_index = 0
    for data in harvested_data:
        group_name = data.group
        harvested_medians = data.value
        calculated_value = calculated_medians[group_index]
        # Verify that the harvested mean is within tolerance of the calculated median 
        assert abs(harvested_medians - calculated_value) <= tolerance, f"Median value mismatch for {group_name}"
        group_index += 1

def verify_group_StdDev_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT) 
    calculated_StdDevs = [9.234388236283511,0.43633542496370253,0.4974935575667632]
    groups_wanted = ['ObsValue','oman','ombg'] 
    group_index = 0
    harvested_data = [data for data in data1 if data.statistic == 'StdDev']
    if len(harvested_data) != len(groups_wanted):
       print("Error: Mismatch between expected groups and harvested data.")
       sys.exit(1)

    group_index = 0
    for data in harvested_data:
        group_name = data.group
        harvested_StdDevs = data.value
        calculated_value = calculated_StdDevs[group_index]
        assert abs(harvested_StdDevs - calculated_value) <= tolerance, f"Standard Deviation value mismatch for {group_name}"
        group_index += 1

def verify_group_minimum_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    calculated_minimums = [-2.123818159103393,-6.02739143371582,-6.222834587097168]
    groups_wanted = ['ObsValue','oman','ombg']
    group_index = 0
    harvested_data = [data for data in data1 if data.statistic == 'minimum']
    if len(harvested_data) != len(groups_wanted):
       print("Error: Mismatch between expected groups and harvested data.")
       sys.exit(1)

    group_index = 0
    for data in harvested_data:
        group_name = data.group
        harvested_minimum = data.value
        calculated_value = calculated_minimums[group_index]
        assert abs(harvested_minimum - calculated_value) <= tolerance, f"Minimum value mismatch for {group_name}"
        group_index += 1

def verify_group_maximum_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    calculated_maximums = [34.480560302734375,11.538920402526855,11.55988597869873]
    groups_wanted = ['ObsValue','oman','ombg']
    group_index = 0
    harvested_data = [data for data in data1 if data.statistic == 'maximum']
    if len(harvested_data) != len(groups_wanted):
       print("Error: Mismatch between expected groups and harvested data.")
       sys.exit(1)

    # Iterate over harvested data and check means for each group
    group_index = 0
    for data in harvested_data:
        group_name = data.group
        harvested_maximum = data.value
        calculated_value = calculated_maximums[group_index]
        assert abs(harvested_maximum - calculated_value) <= tolerance, f" Maximum value mismatch for {group_name}"
        group_index += 1

def main():
    test_soca_harvester()
    verify_filename_components()
    verify_datetime()
    verify_groups()
    verify_group_mean_values()
    verify_group_median_values() 
    verify_group_StdDev_values()
    verify_group_minimum_values()
    verify_group_maximum_values()

if __name__=='__main__':
    main()
