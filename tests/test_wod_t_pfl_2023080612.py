#!/usr/bin/env python

import os
from pathlib import Path 
import cftime

from score_hv import hv_registry
from score_hv.harvester_base import harvest

TEST_TOLERANCE = 0.001

TEST_DATA_FILE_NAMES = ['wod_t_pfl.2023080612.nc']

DATA_DIR = os.path.join(Path(__file__).parent.parent.resolve(), 'src', 'score_hv', 'data')

CONFIGS_DIR = 'configs'
PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
TEST_DATA_PATH = os.path.join(PYTEST_CALLING_DIR, 'data')
SOCA_PATH = [os.path.join(TEST_DATA_PATH, file_name) for file_name in TEST_DATA_FILE_NAMES]

VALID_CONFIG_DICT = {'harvester_name': hv_registry.SOCA_DIAGS,
                     'filenames' : SOCA_PATH,
                     'statistics': ['mean', 'median', 'StdDev',  'minimum', 'maximum', 'rms', 'count'],
                     'variables': ['waterTemperature'],
                     'ocean_depth_bins': [0, 10, 50, 100, 500, 1000]
                 }

def test_soca_harvester():
    data1 = harvest(VALID_CONFIG_DICT)
    
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==SOCA_PATH[0]

def test_verify_filename_components():
    data1 = harvest(VALID_CONFIG_DICT)
    data = data1[0]
    assert data.variables == 'waterTemperature'
    assert data.sensor == 'pfl'
    assert data.file_region == 'global'   

def test_verify_datetime():
    data1 = harvest(VALID_CONFIG_DICT) 
    date_obj = cftime.DatetimeGregorian(2023, 8, 6, 11, 0, 57, 0)
    filetime_dt = data1[0].filetime
    assert date_obj == filetime_dt 

def test_verify_groups():
    data1 = harvest(VALID_CONFIG_DICT)
    groups_wanted = ['ObsValue', 'oman', 'ombg', 'ObsError']
    for data in data1:
        assert data.group in groups_wanted, f"Unexpected group: {data.group}"

def get_harvested_statistic_value(statistic):
    data1 = harvest(VALID_CONFIG_DICT)
    harvested_data = {data.group: data.value for data in data1 if data.statistics == statistic}
    return harvested_data

def test_verify_group_mean_values(tolerance=TEST_TOLERANCE):
    data1 = harvest(VALID_CONFIG_DICT) 
    
    import ipdb
    ipdb.set_trace()
    
    calculated_means = [0.798, 0.0169, 0.0398, 0.1]
    groups_wanted = ['ObsValue','oman','ombg', 'ObsError'] 
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
        assert abs(harvested_mean - calculated_value) <= tolerance, f"Mean value mismatch for {group_name}"
        group_index += 1
       
def test_verify_group_median_values(tolerance=TEST_TOLERANCE):
    data1 = harvest(VALID_CONFIG_DICT) 
    calculated_medians = [1.0, 0.0157, 0.0344, 0.1]
    groups_wanted = ['ObsValue','oman','ombg', 'ObsError'] 
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

def test_verify_group_rms_values(tolerance=TEST_TOLERANCE):
    data1 = harvest(VALID_CONFIG_DICT) 
    calculated_rms = [0.868,0.0681,0.119,0.1]
    groups_wanted = ['ObsValue','oman','ombg', 'ObsError'] 
    group_index = 0
    harvested_data = [data for data in data1 if data.statistics == 'rmse']
    assert len(harvested_data) == len(groups_wanted), "Error: Mismatch between expected groups and harvested data."
  
    group_index = 0
    for data in harvested_data:
        group_name = data.group
        harvested_rms = data.value
        calculated_value = calculated_rms[group_index]
        assert abs(harvested_rms - calculated_value) <= tolerance, f"RMS value mismatch for {group_name}"
        group_index += 1

def test_verify_group_count_values(tolerance=TEST_TOLERANCE):
    """
    """
    data1 = harvest(VALID_CONFIG_DICT)
    calculated_count = [174727, 174727, 174727, 174727]
    groups_wanted = ['ObsValue','oman','ombg', 'ObsError']
    group_index = 0
    harvested_data = [data for data in data1 if data.statistics == 'count']
    assert len(harvested_data) == len(groups_wanted), "Error: Mismatch between expected groups and harvested data."
  
    group_index = 0
    for data in harvested_data:
        group_name = data.group
        harvested_minimum = data.value
        calculated_value = calculated_count[group_index]
        assert abs(harvested_minimum - calculated_value) <= tolerance, f"Count value mismatch for {group_name}"
        group_index += 1

def test_verify_group_StdDev_values(tolerance=TEST_TOLERANCE):
    data1 = harvest(VALID_CONFIG_DICT) 
    calculated_StdDevs = [0.343, 0.0660, 0.113, 0]
    groups_wanted = ['ObsValue','oman','ombg', 'ObsError'] 
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

def test_verify_group_minimum_values(tolerance=TEST_TOLERANCE):
    """
    """
    data1 = harvest(VALID_CONFIG_DICT)
    calculated_minimums = [0, -0.589, -0.5, 0.1]
    groups_wanted = ['ObsValue','oman','ombg', 'ObsError']
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

def test_verify_group_maximum_values(tolerance=TEST_TOLERANCE):
    """
    """
    data1 = harvest(VALID_CONFIG_DICT)
    calculated_maximums = [1.0 , 0.511, 0.5, 0.1]
    groups_wanted = ['ObsValue','oman','ombg', 'ObsError']
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
    test_verify_group_rms_values()
    test_verify_group_count_values()
    test_verify_group_minimum_values()
    test_verify_group_maximum_values()

if __name__=='__main__':
    main()