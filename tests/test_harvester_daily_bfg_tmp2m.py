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
                     'variable': ['tmp2m']}

def test_variable_names():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].variable == 'tmp2m'

def test_global_mean_values_offline(tolerance=0.001):
    """The value of 287.0713362523281 is the mean value of the global means
    calculated from eight forecast files:
        
        tmp2m_bfg_2023032100_fhr09_control.nc
        tmp2m_bfg_2023032106_fhr06_control.nc
        tmp2m_bfg_2023032106_fhr09_control.nc
        tmp2m_bfg_2023032112_fhr06_control.nc
        tmp2m_bfg_2023032112_fhr09_control.nc
        tmp2m_bfg_2023032118_fhr06_control.nc
        tmp2m_bfg_2023032118_fhr09_control.nc
        tmp2m_bfg_2023032200_fhr06_control.nc
        
    When averaged together, these files represent a 24 hour mean. The average 
    value hard-coded in this test was calculated from these forecast files 
    using a separate python code.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    global_mean = 285.527800538339 
    assert data1[0].value <= (1 + tolerance) * global_mean
    assert data1[0].value >= (1 - tolerance) * global_mean 

def test_gridcell_variance(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
   
    variance = 273.2249248235133
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'variance':
            assert variance <= (1 + tolerance) * harvested_tuple.value
            assert variance >= (1 - tolerance) * harvested_tuple.value
            
    
def test_gridcell_min_max(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    
    maximum = 309.8211364746094
    minimum = 222.6378955841064
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'maximum':
            assert maximum <= (1 + tolerance) * harvested_tuple.value
            assert maximum >= (1 - tolerance) * harvested_tuple.value
        elif harvested_tuple.statistic == 'minimum':
            assert minimum <= (1 + tolerance) * harvested_tuple.value
            assert minimum >= (1 - tolerance) * harvested_tuple.value

def test_units():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == "K"

def test_cycletime():
    """The hard coded datetimestr 2023-03-21 12:00:00 is the median midpoint 
    time of the filenames defined above in the BFG_PATH. We have to convert 
    this into a datetime object in order to compare this string to what is 
    returned by daily_bfg.py
    """
    data1 = harvest(VALID_CONFIG_DICT)
    expected_datetime = datetime.strptime("1994-01-01 12:00:00",
                                          "%Y-%m-%d %H:%M:%S")
    assert data1[0].mediantime == expected_datetime

def test_longname():
    data1 = harvest(VALID_CONFIG_DICT)
    var_longname = "2m temperature"
    assert data1[0].longname == var_longname

def test_daily_bfg_harvester():
    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH

def main():
    test_daily_bfg_harvester()
    test_variable_names()
    test_units()
    test_global_mean_values_offline()
    test_gridcell_variance()
    test_gridcell_min_max()
    test_cycletime() 
    test_longname()

if __name__=='__main__':
    main()    
