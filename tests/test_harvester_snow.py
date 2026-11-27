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

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_snowiceocean_control.nc',
                        'bfg_1994010106_fhr06_snowiceocean_control.nc',
                        'bfg_1994010106_fhr09_snowiceocean_control.nc',
                        'bfg_1994010112_fhr06_snowiceocean_control.nc',
                        'bfg_1994010112_fhr09_snowiceocean_control.nc',
                        'bfg_1994010118_fhr06_snowiceocean_control.nc',
                        'bfg_1994010118_fhr09_snowiceocean_control.nc',
                        'bfg_1994010200_fhr06_snowiceocean_control.nc']

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
                     'statistic': ['mean','variance', 'minimum', 'maximum','integral'],
                     'variable': ['snod','weasd'],
                     'regions': {
                               'north_hemi': {'north_lat': 90.0, 'south_lat': 0.0, 'west_long': 0.0, 'east_long': 360.0},
                               'west_hemi': {'north_lat':90, 'south_lat':-90, 'west_long':180, 'east_long':360},
                               'south_hemi': {'north_lat':0, 'south_lat':-90, 'west_long':0, 'east_long':360},
                               }

                     }

def test_gridcell_area_conservation(tolerance=0.001):

    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    assert gridcell_area_data['area'].units == 'steradian'
    sum_gridcell_area = np.sum(gridcell_area_data.variables['area'])
    assert sum_gridcell_area < (1 + tolerance) * 4 * np.pi
    assert sum_gridcell_area > (1 - tolerance) * 4 * np.pi
    gridcell_area_data.close()

def test_variable_names():
    """Here we are testing two variables.  The daily_bfg harvester
       should return values for both variables at once.
       """
    expected_variables = ['snod','weasd'] 
    assert VALID_CONFIG_DICT['variable'] == expected_variables

def test_global_mean_values(tolerance=0.001):
    """ 
        The values of the calculated_means list were 
        calculated from these eight forecast files:

        bfg_1994010100_fhr09_snowiceocean_control.nc
        bfg_1994010106_fhr06_snowiceocean_control.nc
        bfg_1994010106_fhr09_snowiceocean_control.nc
        bfg_1994010112_fhr06_snowiceocean_control.nc
        bfg_1994010112_fhr09_snowiceocean_control.nc
        bfg_1994010118_fhr06_snowiceocean_control.nc
        bfg_1994010118_fhr09_snowiceocean_control.nc
        bfg_1994010200_fhr06_snowiceocean_control.nc
        
        When averaged together, these files represent a 24 hour mean. The 
        average values hard-coded in this test was calculated from 
        forecast files using a separate python code.
    """
    data1 = harvest(VALID_CONFIG_DICT)

    snod_means = [0.1187623217437368,0.09948296253129492,0.0009546454345915825]
    weasd_means = [24.52393639612293,21.54652866075145,0.4101186790391977]
    snod_index = 0;
    weasd_index = 0
    for item in data1:
        if item.variable == 'snod' and item.statistic == 'mean':
           assert snod_means[snod_index] <= (1 + tolerance) * item.value
           assert snod_means[snod_index] >= (1 - tolerance) * item.value                
           snod_index = snod_index + 1

        elif item.variable == 'weasd' and item.statistic == 'mean':
             assert weasd_means[weasd_index] <= (1 + tolerance) * item.value
             assert weasd_means[weasd_index] >= (1 - tolerance) * item.value
             weasd_index = weasd_index + 1

def test_gridcell_variance(tolerance=0.001):
    """
      The values of the calculated_variances list were calculated
      from the forecast files listed above in a separate python script.
      """
    data1 = harvest(VALID_CONFIG_DICT)
  
    snod_variance = [0.0415432724459786,0.04591085062170463,0.003400360547982462]
    weasd_variance = [2339.522045153808,3235.120468097893,661.3939365142375] 
    snod_index = 0
    weasd_index = 0

    for item in data1:
        if item.variable == 'snod' and item.statistic == 'variance':
           assert snod_variance[snod_index] <= (1 + tolerance) * item.value
           assert snod_variance[snod_index] >= (1 - tolerance) * item.value
           snod_index = snod_index + 1
        
        elif item.variable == 'weasd' and item.statistic == 'variance':
          assert weasd_variance[weasd_index] <= (1 + tolerance) * item.value
          assert weasd_variance[weasd_index] >= (1 - tolerance) * item.value
          weasd_index = weasd_index + 1

def test_gridcell_min(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
   
    snod_min = [0.0,0.0,0.0]
    weasd_min = [0.0,0.0,0.0]
    snod_index = 0
    weasd_index = 0

    for item in data1:
        if item.variable == 'snod' and item.statistic == 'minimum':
           assert snod_min[snod_index] <= (1 + tolerance) * item.value
           assert snod_min[snod_index] >= (1 - tolerance) * item.value
           snod_index = snod_index + 1

        elif item.variable == 'weasd' and item.statistic == 'minimum':
             assert weasd_min[weasd_index] <= (1 + tolerance) * item.value
             assert weasd_min[weasd_index] >= (1 - tolerance) * item.value
             weasd_index = weasd_index + 1

def test_gridcell_max(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)

    snod_max = [4.501649975776672,6.169768452644348,6.169768452644348]
    weasd_max = [1630.2353464365858,2832.920043945312,2832.920043945312]
    snod_index = 0
    weasd_index = 0

    for item in data1:
        if item.variable == 'snod' and item.statistic == 'maximum':
           assert snod_max[snod_index] <= (1 + tolerance) * item.value
           assert snod_max[snod_index] >= (1 - tolerance) * item.value
           snod_index = snod_index + 1

        elif item.variable == 'weasd' and item.statistic == 'maximum':
             print(item.value,"  ",weasd_max[weasd_index])
             assert weasd_max[weasd_index] <= (1 + tolerance) * item.value
             assert weasd_max[weasd_index] >= (1 - tolerance) * item.value
             weasd_index = weasd_index + 1

def test_weighted_integral(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)

    snod_integral = [1.15e+13,4.51e+12 ,3.3e+10]
    weasd_integral = [2.38e+15,9.77e+14,1.42e+13]
    snod_index = 0
    weasd_index = 0

    for item in data1:
        if item.variable == 'snod' and item.statistic == 'integral':
           print(item.value,"  ",snod_integral) 
           assert snod_integral[snod_index] <= (1 + tolerance) * item.value
           assert snod_integral[snod_index] >= (1 - tolerance) * item.value
           snod_index = snod_index + 1
        elif item.variable == 'weasd' and item.statistic == 'integral':
           print(item.value,"  ",weasd_integral)   
           assert weasd_integral[weasd_index] <= (1 + tolerance) * item.value
           assert weasd_integral[weasd_index] >= (1 - tolerance) * item.value
           weasd_index = weasd_index + 1


    
def test_units():
    variable_dictionary = {}
    data1 = harvest(VALID_CONFIG_DICT)

    for item in data1:
        if item.variable == 'snod':
           expected_units = 'm'
           assert expected_units == item.units 
        elif item.variable == 'weasd':
           expected_units = 'kg/m**2'
           assert expected_units == item.units 

def test_cycletime():
    """ The hard coded datetimestr 1994-01-01 12:00:00
        is the median midpoint time of the filenames defined above in the 
        BFG_PATH.  We have to convert this into a datetime object in order
        to compare this string to what is returned by 
        global_bucket_precip_ave.py
    """
    data1 = harvest(VALID_CONFIG_DICT)
    expected_datetime = datetime.strptime("1994-01-01 12:00:00",
                                          "%Y-%m-%d %H:%M:%S")
    assert data1[0].mediantime == expected_datetime

def test_longname():
    data1 = harvest(VALID_CONFIG_DICT)

    for item in data1:
        if item.variable == 'snod':
           expected_longname = 'surface snow depth'
           assert expected_longname == item.longname 
        elif item.variable == 'weasd':
           expected_longname = 'surface snow water equivalent'
           assert expected_longname == item.longname

def test_snowiceocean_harvester():
    data1 = harvest(VALID_CONFIG_DICT) 
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH

def main():
    test_gridcell_area_conservation()
    test_variable_names()
    test_units()
    test_global_mean_values()
    test_gridcell_variance()
    test_gridcell_min()
    test_gridcell_max()
    test_weighted_integral()
    test_cycletime() 
    test_longname()
    test_snowiceocean_harvester()

if __name__=='__main__':
    main()
