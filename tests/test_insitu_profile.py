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
                     'statistics': ['mean', 'median', 'StdDev',  'minimum', 'maximum'],
                     'variables': ['salinity','waterTemperature'],
                     }

def test_soca_harvester():
    data1 = harvest(VALID_CONFIG_DICT)
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==SOCA_PATH[0]

def test_verify_filename_components():
    expected_variable_names = ['salinity','waterTemperature']
    data1 = harvest(VALID_CONFIG_DICT)
    for item in data1:
        if item.variables not in expected_variable_names:
           raise ValueError(f"Error: {item.variable} is not in the expected variable list.") 
        assert item.sensor == 'argo'   
        assert item.satellite == None
        assert item.level == None   

def test_verify_datetime():
    data1 = harvest(VALID_CONFIG_DICT) 
    expected_file_dt = datetime.strptime("2021-07-02 22:12:00","%Y-%m-%d %H:%M:%S") 
    harvester_file_dt = data1[0].filetime
    assert expected_file_dt ==  harvester_file_dt 

def test_verify_groups():
    data1 = harvest(VALID_CONFIG_DICT)
    groups_wanted = ['ObsValue', 'oman', 'ombg']
    for data in data1:
        assert data.group in groups_wanted, f"Unexpected group: {data.group}"
   
def test_verify_group_mean_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    salinity_means = [34.21835,-0.566438,-0.566423]
    waterTemperature_means = [7.605209,0.053602,0.049655]
    groups_wanted = ['ObsValue','oman','ombg']
    for item in data1:
        if item.variables == 'salinity' and item.statistics == 'mean':
           for i, group_name in enumerate(groups_wanted):
               if item.group == group_name:
                  calc_value = salinity_means[i]
                  harvested_value = item.value
                  assert abs(harvested_value - calc_value) <= tolerance 
        elif item.variables == 'waterTemperature' and item.statistics == 'mean':    
             for i, group_name in enumerate(groups_wanted):
                 if item.group == group_name:
                    calc_value = waterTemperature_means[i]
                    harvested_value = item.value
                    assert abs(harvested_value - calc_value) <= tolerance
                    
def test_verify_group_median_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    salinity_medians = [34.905998,0.132076,0.13207]
    waterTemperature_medians = [5.421991,0.00878,0.008301]
    groups_wanted = ['ObsValue','oman','ombg']
    for item in data1:
        if item.variables == 'salinity' and item.statistics == 'median':
           for i, group_name in enumerate(groups_wanted):
               if item.group == group_name:
                  calc_value = salinity_medians[i]
                  harvested_value = item.value
                  assert abs(harvested_value - calc_value) <= tolerance 
        elif item.variables == 'waterTemperature' and item.statistics == 'median':    
             for i, group_name in enumerate(groups_wanted):
                 if item.group == group_name:
                    calc_value = waterTemperature_medians[i]
                    harvested_value = item.value
                    assert abs(harvested_value - calc_value) <= tolerance

def test_verify_group_standard_deviation_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    salinity_StdDev = [3.976359,4.34975,4.349679]
    waterTemperature_StdDev = [6.19354,0.749902,0.772137]
    groups_wanted = ['ObsValue','oman','ombg']
    for item in data1:
        if item.variables == 'salinity' and item.statistics == 'StdDev':
           for i, group_name in enumerate(groups_wanted):
               if item.group == group_name:
                  calc_value = salinity_StdDev[i]
                  harvested_value = item.value
                  assert abs(harvested_value - calc_value) <= tolerance 
        elif item.variables == 'waterTemperature' and item.statistics == 'StdDev':    
             for i, group_name in enumerate(groups_wanted):
                 if item.group == group_name:
                    calc_value = waterTemperature_StdDev[i]
                    harvested_value = item.value
                    assert abs(harvested_value - calc_value) <= tolerance

def test_verify_group_minimum_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    salinity_minimums = [0.0,-35.445389,-35.445419]
    waterTemperature_minimums = [-1.015997,-8.81186,-8.81186]
    groups_wanted = ['ObsValue','oman','ombg']
    for item in data1:
        if item.variables == 'salinity' and item.statistics == 'minimum':
           for i, group_name in enumerate(groups_wanted):
               if item.group == group_name:
                  calc_value = salinity_minimums[i]
                  harvested_value = item.value
                  assert abs(harvested_value - calc_value) <= tolerance 
        elif item.variables == 'waterTemperature' and item.statistics == 'minimum':    
             for i, group_name in enumerate(groups_wanted):
                 if item.group == group_name:
                    calc_value = waterTemperature_minimums[i]
                    harvested_value = item.value
                    assert abs(harvested_value - calc_value) <= tolerance
    
def test_verify_group_maximum_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    salinity_maximums = [37.417999,34.542,34.542]
    waterTemperature_maximums = [30.451014,7.235542,7.235542]
    groups_wanted = ['ObsValue','oman','ombg']
    for item in data1:
        if item.variables == 'salinity' and item.statistics == 'maximum':
           for i, group_name in enumerate(groups_wanted):
               if item.group == group_name:
                  calc_value = salinity_maximums[i]
                  harvested_value = item.value
                  assert abs(harvested_value - calc_value) <= tolerance 
        elif item.variables == 'waterTemperature' and item.statistics == 'maximum':    
             for i, group_name in enumerate(groups_wanted):
                 if item.group == group_name:
                    calc_value = waterTemperature_maximums[i]
                    harvested_value = item.value
                    assert abs(harvested_value - calc_value) <= tolerance
def main():
    test_soca_harvester()
    test_verify_filename_components()
    test_verify_datetime()
    test_verify_groups()
    test_verify_group_mean_values()
    test_verify_group_median_values()
    test_verify_group_standard_deviation_values()
    test_verify_group_minimum_values()
    test_verify_group_maximum_values()

if __name__=='__main__':
    main()
