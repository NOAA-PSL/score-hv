#!/usr/bin/env python

import sys,os
from pathlib import Path 

import numpy as np
from datetime import datetime
from netCDF4 import Dataset

from score_hv import hv_registry
from score_hv.harvester_base import harvest

TEST_DATA_FILE_NAMES = ['bfg_1994010100_fhr09_prateb_control.nc',
                        'bfg_1994010106_fhr06_prateb_control.nc',
                        'bfg_1994010106_fhr09_prateb_control.nc',
                        'bfg_1994010112_fhr06_prateb_control.nc',
                        'bfg_1994010112_fhr09_prateb_control.nc',
                        'bfg_1994010118_fhr06_prateb_control.nc',
                        'bfg_1994010118_fhr09_prateb_control.nc',
                        'bfg_1994010200_fhr06_prateb_control.nc']

DATA_DIR = os.path.join(Path(__file__).parent.parent.resolve(), 'src', 'score_hv', 'data')
GRIDCELL_AREA_DATA_PATH = os.path.join(DATA_DIR,
                                       'gridcell-area' + 
                                       '_noaa-ufs-gefsv13replay-pds' + 
                                       '_bfg_control_1536x768_20231116.nc')

PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
TEST_DATA_PATH = os.path.join(PYTEST_CALLING_DIR, 'data')
BFG_PATH = [os.path.join(TEST_DATA_PATH,
                         file_name) for file_name in TEST_DATA_FILE_NAMES]

VALID_CONFIG_DICT = {'harvester_name': hv_registry.DAILY_BFG,
                     'filenames' : BFG_PATH,
                     'statistic': ['mean', 'variance', 'minimum', 'maximum'],
                     'variable': ['prateb_ave']}

VALID_CONFIG_DICT1 = {'harvester_name': hv_registry.DAILY_BFG,
                     'filenames' : BFG_PATH,
                     'statistic': ['mean', 'variance', 'minimum', 'maximum'],
                     'variable': ['prateb_ave'],
                     'regions': {'conus':{'north_lat': 49, 'south_lat': 24, 'west_long': 235, 'east_long':293},
                                 'south_hemis': {'north_lat':0, 'south_lat':-90, 'west_long':0, 'east_long':360},
                                 'north_hemis': {'north_lat':90, 'south_lat':0, 'west_long':0, 'east_long':360},
                                 'tropics': {'north_lat': 24.0, 'south_lat': -24.0, 'west_long': 0.0, 'east_long': 360.0},
                                 'global': { }
                                }
                     }
                     
VALID_CONFIG_DICT2 = {'harvester_name': hv_registry.DAILY_BFG,
                     'filenames' : BFG_PATH,
                     'statistic': ['mean', 'variance', 'minimum', 'maximum'],
                     'variable': ['prateb_ave'],
                     'regions': {
                                 'arctic': {'north_lat': 90,
                                            'south_lat': 66},
                                 'antarctic': {'north_lat': -60,
                                               'south_lat': -90},
                                 'north_mid_lats': {'north_lat': 65,
                                                    'south_lat': 30},
                                 'global': {}
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
    data = harvest(VALID_CONFIG_DICT)
    assert data[0].variable == 'prateb_ave'
    data2 = harvest(VALID_CONFIG_DICT2)
    assert data2[10].variable == 'prateb_ave'

def test_mean_values_regions(tolerance=0.001):
    """
      The values of the calculated_means list were
      calculated from these eight forecast files:

        bfg_1994010100_fhr09_prate_control.nc
        bfg_1994010106_fhr06_prate_control.nc
        bfg_1994010106_fhr09_prate_control.nc
        bfg_1994010112_fhr06_prate_control.nc
        bfg_1994010112_fhr09_prate_control.nc
        bfg_1994010118_fhr06_prate_control.nc
        bfg_1994010118_fhr09_prate_control.nc
        bfg_1994010200_fhr06_prate_control.nc

      When averaged together, these files represent a 24 hour mean.
      In this test there are four regions.  The daily_bfg harvester will return
      the values of all three regions at once.  
      """
    data1 = harvest(VALID_CONFIG_DICT2)
     
    for item in data1:
        if item.statistic == 'mean':
           if item.region['name'] == 'arctic':
               calculated_mean = 6.199207771441263e-06 
           elif item.region['name'] == 'antarctic':
               calculated_mean = 1.0954673630587e-05 
           elif item.region['name'] == 'north_mid_lats':
               calculated_mean =  3.329268624311339e-05
           elif item.region['name'] == 'global':
               calculated_mean = 3.117380893272532e-05 
         
           assert calculated_mean <= (1 + tolerance) * item.value
           assert calculated_mean >= (1 - tolerance) * item.value
      
def test_gridcell_variance_regions(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT2)
   
    for item in data1:
        if item.statistic == 'variance':
            if item.region['name'] == 'arctic':
                calculated_var = 2.112175719948953e-10 
            elif item.region['name'] == 'antarctic':
                calculated_var = 5.849501742576292e-10 
            elif item.region['name'] == 'north_mid_lats':
                calculated_var = 4.597839679866114e-09 
            elif item.region['name'] == 'global':
                calculated_var = 5.738481800949724e-09 
            
            print(item.region['name'],"  ",item.value)
            
            assert calculated_var <= (1 + tolerance) * item.value
            assert calculated_var >= (1 - tolerance) * item.value
            
def test_gridcell_min_max_regions(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT2)
    
    for item in data1:
        if item.statistic == 'minimum':
            if item.region['name'] == 'arctic':
                calculated_min = 0.0
            elif item.region['name'] == 'antarctic':
                calculated_min = 0.0 
            elif item.region['name'] == 'north_min_lats':
                calculated_min = 0.0 
            elif item.region['name'] == 'global':
                calculated_min = 0.0 
            
            assert calculated_min <= (1 + tolerance) * item.value
            assert calculated_min >= (1 - tolerance) * item.value
           
        elif item.statistic == 'maximum':
            if item.region['name'] == 'arctic':
                calculated_max = 0.0005006104457834226 
            elif item.region['name'] == 'antarctic':
                calculated_max = 0.0005079157344880514 
            elif item.region['name'] == 'north_mid_lats':
                calculated_max = 0.0009919954550099419 
            elif item.region['name'] == 'global':
                calculated_max = 0.004360093198556569 
             
            assert calculated_max <= (1 + tolerance) * item.value
            assert calculated_max >= (1 - tolerance) * item.value
   
def test_units():
    data1 = harvest(VALID_CONFIG_DICT)
    assert data1[0].units == "kg/m**2/s"

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
    var_longname = "bucket surface precipitation rate"
    assert data1[0].longname == var_longname

def test_precip_harvester():
    data1 = harvest(VALID_CONFIG_DICT)  
    assert type(data1) is list
    assert len(data1) > 0
    assert data1[0].filenames==BFG_PATH

def main():
    test_gridcell_area_conservation()
    test_variable_names()
    test_mean_values_regions()
    test_gridcell_variance_regions()
    test_gridcell_min_max_regions()
    test_units()
    test_cycletime()
    test_longname()
    test_precip_harvester()

if __name__=='__main__':
    main()
