#!/usr/bin/env python

import os
import sys
import re
import faulthandler
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
faulthandler.enable()

TEST_DATA_FILE_NAMES = [
                        'insitu_surface_trkob.2021070300.nc4'
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
                     'variables': ['seaSurfaceSalinity','seaSurfaceTemperature'],
                     }

def test_soca_harvester():
    data1 = harvest(VALID_CONFIG_DICT)
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==SOCA_PATH[0]

def test_verify_filename_components():
    expected_variable_names = ['seaSurfaceSalinity','seaSurfaceTemperature']
    data1 = harvest(VALID_CONFIG_DICT)
    for item in data1:
        if item.variables not in expected_variable_names:
           raise ValueError(f"Error: {item.variables} is not in the expected variable list.")  
        assert item.sensor == None   
        assert item.satellite == 'trkob'
        assert item.level == None
        assert item.file_region == 'global'

def test_verify_datetime():
    data1 = harvest(VALID_CONFIG_DICT)
    date_str = "2021070300"
    date_obj = datetime.strptime(date_str, "%Y%m%d%H")
    filetime_str = data1[0].filetime
    filetime_dt = datetime.strptime(filetime_str, "%Y-%m-%d %H:%M:%S")
    assert date_obj == filetime_dt 

def test_verify_group_mean_values(tolerance=.001):
    data1 = harvest(VALID_CONFIG_DICT) 
    for item in data1:
        if item.statistics == 'mean':
           if item.group == 'ObsValue': 
              if item.variables == 'seaSurfaceSalinity':
                 calc_value = 35.432342
                 assert calc_value <= (1 + tolerance) * item.value
                 assert calc_value >= (1 - tolerance) * item.value
              elif item.variables == 'seaSurfaceTemperature':
                 calc_value = 23.566126
                 assert calc_value <= (1 + tolerance) * item.value
                 assert calc_value >= (1 - tolerance) * item.value
           elif item.group == 'oman':
                if item.variables == 'seaSurfaceTemperature':
                   calc_value = 0.310008
                   assert calc_value <= (1 + tolerance) * item.value
                   assert calc_value >= (1 - tolerance) * item.value
           elif item.group == 'ombg':
                if item.variables == 'seaSurfaceTemperature':
                   calc_value = 0.313802
                   assert calc_value <= (1 + tolerance) * item.value
                   assert calc_value >= (1 - tolerance) * item.value

def test_verify_group_median_values(tolerance=.001):
    data1 = harvest(VALID_CONFIG_DICT) 
    for item in data1:
        if item.statistics == 'median':
           if item.group == 'ObsValue': 
              if item.variables == 'seaSurfaceSalinity':
                 calc_value = 35.169998
                 assert calc_value <= (1 + tolerance) * item.value
                 assert calc_value >= (1 - tolerance) * item.value
              elif item.variables == 'seaSurfaceTemperature':
                 calc_value = 23.1
                 assert calc_value <= (1 + tolerance) * item.value
                 assert calc_value >= (1 - tolerance) * item.value
           elif item.group == 'oman':
                if item.variables == 'seaSurfaceTemperature':
                   calc_value = 0.482664
                   assert calc_value <= (1 + tolerance) * item.value
                   assert calc_value >= (1 - tolerance) * item.value
           elif item.group == 'ombg':
                if item.variables == 'seaSurfaceTemperature':
                   calc_value = 0.433351
                   assert calc_value <= (1 + tolerance) * item.value
                   assert calc_value >= (1 - tolerance) * item.value

def test_verify_group_standard_deviation_values(tolerance=.001):
    data1 = harvest(VALID_CONFIG_DICT) 
    for item in data1:
        if item.statistics == 'StdDev':
           if item.group == 'ObsValue':
              if item.variables == 'seaSurfaceSalinity':
                 calc_value = 1.547105 
                 assert calc_value <= (1 + tolerance) * item.value
                 assert calc_value >= (1 - tolerance) * item.value
              elif item.variables == 'seaSurfaceTemperature':
                 calc_value = 1.038353
                 assert calc_value <= (1 + tolerance) * item.value
                 assert calc_value >= (1 - tolerance) * item.value                
           elif item.group == 'oman':
                if item.variables == 'seaSurfaceTemperature':
                   calc_value = 0.33505
                   assert calc_value <= (1 + tolerance) * item.value
                   assert calc_value >= (1 - tolerance) * item.value
           elif item.group == 'ombg':
                if item.variables == 'seaSurfaceTemperature':
                   calc_value = 0.32389
                   assert calc_value <= (1 + tolerance) * item.value
                   assert calc_value >= (1 - tolerance) * item.value

def test_verify_group_minimum_values(tolerance=.001):
    data1 = harvest(VALID_CONFIG_DICT) 
    for item in data1:
        if item.statistics == 'minimum':
           if item.group == 'ObsValue':
              if item.variables == 'seaSurfaceSalinity':
                 calc_value = 32.0 
                 print(item.value)
                 assert calc_value <= (1 + tolerance) * item.value
                 assert calc_value >= (1 - tolerance) * item.value
              elif item.variables == 'seaSurfaceTemperature':
                 calc_value = 22.1 
                 assert calc_value <= (1 + tolerance) * item.value
                 assert calc_value >= (1 - tolerance) * item.value                
           elif item.group == 'oman':
                if item.variables == 'seaSurfaceTemperature':
                   calc_value = abs(-0.686694)
                   harvested = abs(item.value)
                   assert calc_value <= (1 + tolerance) * harvested 
                   assert calc_value >= (1 - tolerance) * harvested
           elif item.group == 'ombg':
                if item.variables == 'seaSurfaceTemperature':
                   calc_value = abs(-0.686694)
                   harveted = abs(item.value)
                   assert calc_value <= (1 + tolerance) * harvested   

def test_verify_group_maximum_values(tolerance=.001):
    data1 = harvest(VALID_CONFIG_DICT) 
    for item in data1:
        if item.statistics == 'maximum':
           if item.group == 'ObsValue':
              if item.variables == 'seaSurfaceSalinity':
                 calc_value = 40.990002 
                 assert calc_value <= (1 + tolerance) * item.value
                 assert calc_value >= (1 - tolerance) * item.value
              elif item.variables == 'seaSurfaceTemperature':
                 calc_value = 27.6
                 assert calc_value <= (1 + tolerance) * item.value
                 assert calc_value >= (1 - tolerance) * item.value                
           elif item.group == 'oman':
                if item.variables == 'seaSurfaceTemperature':
                   calc_value = 0.743538
                   assert calc_value <= (1 + tolerance) * item.value
                   assert calc_value >= (1 - tolerance) * item.value
           elif item.group == 'ombg':
                if item.variables == 'seaSurfaceTemperature':
                   calc_value = 0.743538 
                   assert calc_value <= (1 + tolerance) * item.value

def main():
    test_soca_harvester()
    test_verify_filename_components()
    test_verify_datetime()
    test_verify_group_mean_values()
    test_verify_group_median_values()
    test_verify_group_standard_deviation_values()
    test_verify_group_minimum_values()
    test_verify_group_maximum_values()

if __name__=='__main__':
    main()
