#!/usr/bin/env python

import os
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
                     'regions': {'tropics': {'north_lat': 23,
                                             'south_lat': -23},
                                 'temperate': {'north_lat': 66,
                                               'south_lat': 23},
                                 'arctic': {'north_lat': 90,
                                            'south_lat': 66},
                                 'antarctic': {'north_lat': -60,
                                               'south_lat': -90},
                                 'equatorial': {'north_lat': 5,
                                                'south_lat': -5},
                                 'north_mid_lats': {'north_lat': 65,
                                                    'south_lat': 30},
                                 'south_mid_lats': {'north_lat': -30,
                                                    'south_lat': -65},
                                 'north_hemis': {'north_lat': 90,       
                                                 'south_lat': 0},
                                 'south_hemis': {'north_lat': 0,
                                                 'south_lat': -90},
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

def test_zonal_regions():
    data2 = harvest(VALID_CONFIG_DICT2)
    for item in data2:
        region_name = item.region['name']
        if region_name == 'global':
            expected_north_lat = 90
            expected_south_lat = -90
        else:
            expected_north_lat = VALID_CONFIG_DICT2['regions'][region_name]['north_lat']
            expected_south_lat = VALID_CONFIG_DICT2['regions'][region_name]['south_lat']
        
        assert expected_north_lat >= np.max(item.region['latitude'])
        assert expected_south_lat <= np.min(item.region['latitude'])

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
    data1 = harvest(VALID_CONFIG_DICT1)
    for item in data1:
        if item.statistic == 'mean':
           if item.region['name'] == 'conus':
               calculated_mean = 0.03251096850286386
           elif item.region['name'] == 'south_hemis':
               calculated_mean = 0.03876764799618554
           elif item.region['name'] == 'north_hemis':
               calculated_mean = 0.043024001372664884
           elif item.region['name'] == 'tropics':
               calculated_mean = 0.060860878009092546
           elif item.region['name'] == 'global':
               calculated_mean = 0.0408958246844251
        
        assert calculated_mean <= (1 + tolerance) * item.value
        assert calculated_mean >= (1 - tolerance) * item.value

def test_global_mean_values_offline(tolerance=0.001):
    """The value of 3.117e-05 is the mean value of the global means 
    calculated from eight forecast files:
        
        bfg_1994010100_fhr09_prateb_control.nc
        bfg_1994010106_fhr06_prateb_control.nc
        bfg_1994010106_fhr09_prateb_control.nc
        bfg_1994010112_fhr06_prateb_control.nc
        bfg_1994010112_fhr09_prateb_control.nc
        bfg_1994010118_fhr06_prateb_control.nc
        bfg_1994010118_fhr09_prateb_control.nc
        bfg_1994010200_fhr06_prateb_control.nc
        
    When averaged together, these files represent a 24 hour mean. The 
    average value hard-coded in this test was calculated from 
    these forecast files using a separate python code.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    global_mean = 3.1173840683271906e-05
    assert data1[0].value <= (1 + tolerance) * global_mean
    assert data1[0].value >= (1 - tolerance) * global_mean

def test_global_mean_values_netCDF4(tolerance=0.001):
    """Opens each background Netcdf file using the
    netCDF4 library function Dataset and computes the expected value
    of the provided variable.  In this case prateb_ave.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    
    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    norm_weights = gridcell_area_data.variables['area'][:] / np.sum(
                                        gridcell_area_data.variables['area'][:])
    
    summation = np.ma.zeros(gridcell_area_data.variables['area'].shape)
    for file_count, data_file in enumerate(BFG_PATH):
        test_rootgrp = Dataset(data_file)
    
        summation += test_rootgrp.variables[VALID_CONFIG_DICT['variable'][0]][0]
        
        test_rootgrp.close()
        
    temporal_mean = summation / (file_count + 1)
    global_mean = np.ma.sum(norm_weights * temporal_mean)    
    
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'mean':
            assert global_mean <= (1 + tolerance) * harvested_tuple.value
            assert global_mean >= (1 - tolerance) * harvested_tuple.value
            
    gridcell_area_data.close()
                
def test_gridcell_variance(tolerance=0.001):
    """Opens each background Netcdf file using the
    netCDF4 library function Dataset and computes the variance
    of the provided variable.  In this case prateb_ave.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    
    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    norm_weights = gridcell_area_data.variables['area'][:] / np.sum(
                                        gridcell_area_data.variables['area'][:])
    
    summation = np.ma.zeros(gridcell_area_data.variables['area'].shape)
    for file_count, data_file in enumerate(BFG_PATH):
        test_rootgrp = Dataset(data_file)
    
        summation += test_rootgrp.variables[VALID_CONFIG_DICT['variable'][0]][0]
        
        test_rootgrp.close()
        
    temporal_mean = summation / (file_count + 1)
    
    global_mean = np.ma.sum(norm_weights * temporal_mean)
    variance = np.ma.sum((temporal_mean - global_mean)**2 * norm_weights)
    
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'variance':
            assert variance <= (1 + tolerance) * harvested_tuple.value
            assert variance >= (1 - tolerance) * harvested_tuple.value
            
    gridcell_area_data.close()
    
def test_gridcell_min_max(tolerance=0.001):
    """Opens each background Netcdf file using the
    netCDF4 library function Dataset and computes the maximum
    of the provided variable.  In this case prateb_ave.
    """
    data1 = harvest(VALID_CONFIG_DICT)
    
    gridcell_area_data = Dataset(GRIDCELL_AREA_DATA_PATH)
    
    summation = np.ma.zeros(gridcell_area_data.variables['area'].shape)
    for file_count, data_file in enumerate(BFG_PATH):
        test_rootgrp = Dataset(data_file)
    
        summation += test_rootgrp.variables[VALID_CONFIG_DICT['variable'][0]][0]
        
        test_rootgrp.close()
        
    temporal_mean = summation / (file_count + 1)
    minimum = np.ma.min(temporal_mean)
    maximum = np.ma.max(temporal_mean)
    
    """The following offline min and max were calculated from an external 
    python code
    """
    offline_min = 0.0
    offline_max = 0.0043600933
    for i, harvested_tuple in enumerate(data1):
        if harvested_tuple.statistic == 'maximum':
            assert maximum <= (1 + tolerance) * harvested_tuple.value
            assert maximum >= (1 - tolerance) * harvested_tuple.value
            
            assert offline_max <= (1 + tolerance) * harvested_tuple.value
            assert offline_max >= (1 - tolerance) * harvested_tuple.value
            
            
        elif harvested_tuple.statistic == 'minimum':
            assert minimum <= (1 + tolerance) * harvested_tuple.value
            assert minimum >= (1 - tolerance) * harvested_tuple.value
            
            assert offline_min <= (1 + tolerance) * harvested_tuple.value
            assert offline_min >= (1 - tolerance) * harvested_tuple.value
            
    gridcell_area_data.close()

def test_gridcell_variance_regions(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT1)
    for item in data1:
        if item.statistic == 'variance':
            if item.region['name'] == 'conus':
                calculated_var = 0.000430468651630288
            elif item.region['name'] == 'south_hemis':
                calculated_var = 0.00108603948347438
            elif item.region['name'] == 'north_hemis':
                calculated_var = 0.0016457705882051094
            elif item.region['name'] == 'tropics':
                calculated_var = 0.002221834374899518
            elif item.region['name'] == 'global':
                calculated_var = 0.0013704341718561103
        
            assert calculated_var <= (1 + tolerance) * item.value
            assert calculated_var >= (1 - tolerance) * item.value
 
def test_gridcell_min_max_regions(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT1)
    for item in data1:
        if item.statistic == 'minimum':
            if item.region['name'] == 'conus':
                calculated_min = 0.0015120203606784344
            elif item.region['name'] == 'south_hemis':
                calculated_min = 1.5071715324666002e-06
            elif item.region['name'] == 'north_hemis':
                calculated_min = 4.0326767099252425e-11
            elif item.region['name'] == 'tropics':
                calculated_min = 4.032676709925242e-11
            elif item.region['name'] == 'global':
                calculated_min = 4.032676709925242e-11
        
            assert calculated_min <= (1 + tolerance) * item.value
            assert calculated_min >= (1 - tolerance) * item.value
           
        elif item.statistic == 'maximum':
            if item.region['name'] == 'conus':
                calculated_max = 0.10341465473175052
            elif item.region['name'] == 'south_hemis':
                calculated_max = 0.2618738580495119
            elif item.region['name'] == 'north_hemis':
                calculated_max = 0.543392937630415
            elif item.region['name'] == 'tropics':
                calculated_max = 0.543392937630415
            elif item.region['name'] == 'global':
                calculated_max = 0.5433929376304149
            
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
    test_zonal_regions()
    test_mean_values_regions()
    test_global_mean_values_offline()
    test_global_mean_values_netCDF4()
    test_gridcell_variance()
    test_gridcell_min_max()
    test_gridcell_variance_regions()
    test_gridcell_min_max_regions()
    test_units()
    test_cycletime()
    test_longname()
    test_precip_harvester()

if __name__=='__main__':
    main()