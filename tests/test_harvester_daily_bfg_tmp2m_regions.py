#!/usr/bin/env python

import os
import sys
from pathlib import Path 

import numpy as np
from datetime import datetime
import pytest
import yaml
from netCDF4 import Dataset

from score_hv import hv_registry
from score_hv.harvester_base import harvest
from score_hv.yaml_utils import YamlLoader
from score_hv.harvesters.innov_netcdf import Region, InnovStatsCfg

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_tmp2m_control.nc',
                        'bfg_1994010106_fhr06_tmp2m_control.nc',
                        'bfg_1994010106_fhr09_tmp2m_control.nc',
                        'bfg_1994010112_fhr06_tmp2m_control.nc',
                        'bfg_1994010112_fhr09_tmp2m_control.nc',
                        'bfg_1994010118_fhr06_tmp2m_control.nc',
                        'bfg_1994010118_fhr09_tmp2m_control.nc',
                        'bfg_1994010200_fhr06_tmp2m_control.nc'
                        ]

DATA_DIR = os.path.join(Path(__file__).parent.parent.resolve(), 'src', 'score_hv', 'data')
GRIDCELL_AREA_DATA_PATH = os.path.join(DATA_DIR,
                                       'gridcell-area' + 
                                       '_noaa-ufs-gefsv13replay-pds' + 
                                       '_bfg_control_1536x768_20231116.nc')

CONFIGS_DIR = 'configs'
PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
TEST_DATA_PATH = os.path.join(PYTEST_CALLING_DIR, 'data')
BFG_PATH = [os.path.join(TEST_DATA_PATH,
                         file_name) for file_name in TEST_DATA_FILE_NAMES]
                     
VALID_CONFIG_DICT = {'harvester_name': hv_registry.DAILY_BFG,
                      'filenames' : BFG_PATH,
                      'statistic': ['mean', 'variance', 'minimum', 'maximum'],
                      'variable': ['tmp2m'],
                      'regions': {'africa':{'north_lat': 37, 'south_lat': -35, 'west_long': 343, 'east_long':51},
                                  'south_ameri': {'north_lat':12.5, 'south_lat':-55.5, 'west_long':279, 'east_long':325},
                                  'china': {'north_lat':53, 'south_lat':18, 'west_long':73, 'east_long':135},
                                  'global':{}
                                 },
                      }
                      
def test_mean_values(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    expected_count = 4
    count = 0
    for item in data1:
        if item.statistic == 'mean':
            count += 1
            if item.region['name'] == 'africa':
                offline_value = 294.8423867978033 
            elif item.region['name'] == 'south_ameri':
                offline_value = 294.0046580025675 
            elif item.region['name'] == 'china':
                offline_value = 273.355559219607 
            elif item.region['name'] == 'global':
                offline_value = 285.527800538339
    
            assert item.value <= (1 + tolerance) * offline_value
            assert item.value >= (1 - tolerance) * offline_value
    assert count == expected_count
     
def test_gridcell_variance(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    expected_count = 4
    count = 0
    for item in data1:
        if item.statistic == 'variance':
            count += 1
            if item.region['name'] == 'africa':
                offline_value =  28.53235414209546
            elif item.region['name'] == 'south_ameri':
                offline_value = 42.03888308741612 
            elif item.region['name'] == 'china':
                offline_value = 240.814026301364 
            elif item.region['name'] == 'global':
                offline_value = 273.2249248235133
            
            assert item.value <= (1 + tolerance) * offline_value
            assert item.value >= (1 - tolerance) * offline_value
    
    assert count == expected_count
    
def test_gridcell_min(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    expected_count = 4
    count = 0
    for item in data1:
        if item.statistic == 'minimum':
            count += 1
            if item.region['name'] == 'africa':
                offline_value = 271.8699607849121 
            elif item.region['name'] == 'south_ameri':
                offline_value = 271.61420180096843
            elif item.region['name'] == 'china':
                offline_value = 239.53879547119143
            elif item.region['name'] == 'global':
                offline_value = 222.6378955841064
                
            assert item.value <= (1 + tolerance) * offline_value
            assert item.value >= (1 - tolerance) * offline_value
    
    assert count == expected_count

def test_gridcell_max(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    expected_count = 4
    count = 0
    for item in data1:
        if item.statistic == 'maximum':
            count += 1
            if item.region['name'] == 'africa':
                offline_value = 306.265567779541 
            elif item.region['name'] == 'south_ameri':
                offline_value = 305.3447341918945
            elif item.region['name'] == 'china':
                offline_value = 300.0520133972168
            elif item.region['name'] == 'global':
                offline_value = 309.8211364746094
               
            assert item.value <= (1 + tolerance) * offline_value
            assert item.value >= (1 - tolerance) * offline_value
    
    assert count == expected_count

def test_cycletime():
    """The hard coded datetimestr 1994-01-01 12:00:00 is the median midpoint 
    time of the filenames defined above in the BFG_PATH. We have to convert 
    this into a datetime object in order to compare this string to what is 
    returned by daily_bfg.py
    """
    data1 = harvest(VALID_CONFIG_DICT)
    expected_datetime = datetime.strptime("1994-01-01 12:00:00",
                                          "%Y-%m-%d %H:%M:%S")
    assert data1[-1].mediantime == expected_datetime

def main():
    test_mean_values()
    test_gridcell_variance()
    test_gridcell_min()
    test_gridcell_max()
    test_cycletime()

if __name__=='__main__':
    main()
