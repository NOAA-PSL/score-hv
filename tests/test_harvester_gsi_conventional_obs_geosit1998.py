#!/usr/bin/env python

#TODO: CRITICAL!!! refactor unit tests so that they assert exisitence of values to be checked under if statements, which can currently be bypassed if the data don't exist

"""Unit tests for gsi_satellite_radiance.py tested against NASA GEOS-IT sample
data
"""

import os
from pathlib import Path
from datetime import datetime

from score_hv import hv_registry
from score_hv.harvester_base import harvest

PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
                             
FIT_FILE_PATH_GEOS_IT_1998 = os.path.join(PYTEST_CALLING_DIR, 'data',
                    'x0123_abcdef_xyz01.xyz_stats.log.19980101_00z.txt')
                    
VALID_CONFIG_DICT_GEOS_IT_1998 = {
    'harvester_name': 
    hv_registry.GSI_CONVENTIONAL_OBS,
    'filename': FIT_FILE_PATH_GEOS_IT_1998,
    'variables': ('fit_psfc_data', # fit of surface pressure data (mb)
                  'fit_uv_data', # fit of u, v wind data (m/s),
                  'fit_t_data', # fit of temperature data (K)
                  'fit_q_data', # fit of moisture data (% of qsaturation guess)
                  ),
    'statistics': (
        'count', # number of obs summed under obs types and vertical layers
        'bias', # bias of obs departure for each outer loop (it)
        'rms', # root mean squre error of obs departure for each outer loop (it)
        'cpen', # obs part of penalty (cost function)
        'qcpen' # nonlinear qc penalty
        ),
    'plev_bounds': [
        (0.120E+04, 0.100E+04),
        (0.100E+04, 0.900E+03),
        (0.900E+03, 0.800E+03),
        (0.800E+03, 0.600E+03),
        (0.600E+03, 0.400E+03),
        (0.400E+03, 0.300E+03),
        (0.300E+03, 0.250E+03),
        (0.250E+03, 0.200E+03),
        (0.200E+03, 0.150E+03),
        (0.150E+03, 0.100E+03),
        (0.100E+03, 0.500E+02),
        (0.200E+04, 0.000E+00),
    ]
                    }
                    
VALID_CONFIG_DICT_GEOS_IT_1998_QSAT = {
    'harvester_name': 
    hv_registry.GSI_CONVENTIONAL_OBS,
    'filename': FIT_FILE_PATH_GEOS_IT_1998,
    'variables': ('fit_psfc_data', # fit of surface pressure data (mb)
                  'fit_uv_data', # fit of u, v wind data (m/s),
                  'fit_t_data', # fit of temperature data (K)
                  'fit_q_data', # fit of moisture data (% of qsaturation guess)
                  ),
    'statistics': (
        'count', # number of obs summed under obs types and vertical layers
        'bias', # bias of obs departure for each outer loop (it)
        'rms', # root mean squre error of obs departure for each outer loop (it)
        'cpen', # obs part of penalty (cost function)
        'qcpen' # nonlinear qc penalty
        ),
    'plev_bounds': [
        (0.120E+04, 0.100E+04),
        (0.100E+04, 0.950E+03),
        (0.950E+03, 0.900E+03),
        (0.900E+03, 0.850E+03),
        (0.850E+03, 0.800E+03),
        (0.800E+03, 0.700E+03),
        (0.700E+03, 0.600E+03),
        (0.600E+03, 0.500E+03),
        (0.500E+03, 0.400E+03),
        (0.400E+03, 0.300E+03),
        (0.300E+03, 0.000E+02),
        (0.200E+04, 0.000E+00),
    ]
                    }
        
def test_datetime_geos_it_1998():
    data_list = harvest(VALID_CONFIG_DICT_GEOS_IT_1998)
    test_datetime = datetime.strptime('1998010100', '%Y%m%d%H')
    for i, data_i in enumerate(data_list):
        assert test_datetime == data_i.datetime

def test_longnames():
    data_list = harvest(VALID_CONFIG_DICT_GEOS_IT_1998)
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_psfc_data':
            assert data_i.longname == 'fit of surface pressure data'
            
def test_units():
    data_list = harvest(VALID_CONFIG_DICT_GEOS_IT_1998)
    for i, data_i in enumerate(data_list):
        if data_i.statistic == 'count':
            assert data_i.units == None
        elif data_i.variable == 'fit_psfc_data':
            assert data_i.units == 'mb'
        elif data_i.variable == 'fit_q_data':
            assert data_i.units == r'%'
        elif data_i.variable == 'fit_t_data':
            assert data_i.units == 'K'
        elif data_i.variable == 'fit_uv_data':
            assert data_i.units == 'm/s'
    
def test_qsat_plevs():
    data_list = harvest(VALID_CONFIG_DICT_GEOS_IT_1998_QSAT)
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_q_data':
            assert data_i.plevs_top == [1000.0,
                                           950.0,
                                           900.0,
                                           850.0,
                                           800.0,
                                           700.0,
                                           600.0,
                                           500.0,
                                           400.0,
                                           300.0,
                                           0.0,
                                           0.0]
            assert data_i.plevs_bot == [1200.0,
                                           1000.0,
                                           950.0,
                                           900.0,
                                           850.0,
                                           800.0,
                                           700.0,
                                           600.0,
                                           500.0,
                                           400.0,
                                           300.0,
                                           2000.0]
            #assert data_i.plevs_units[2] == 'hPa'

def test_qsat_asm():
    data_list = harvest(VALID_CONFIG_DICT_GEOS_IT_1998_QSAT)
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_q_data':
            if data_i.iteration == 1: # GSI stage 1 (o - b)
                if data_i.usage == 'asm': # assimilated
                    if data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [1316,
                                                     556,
                                                     800,
                                                     948,
                                                     469,
                                                     1459,
                                                     823,
                                                     873,
                                                     1350,
                                                     1403,
                                                     0,
                                                     9997]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [7.07,
                                                     5.09,
                                                     3.62,
                                                     5.00,
                                                     6.20,
                                                     3.82,
                                                     0.29,
                                                     1.68,
                                                     3.77,
                                                     1.67,
                                                     0.00,
                                                     3.74]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [16.38,
                                                     19.94,
                                                     17.47,
                                                     16.69,
                                                     20.20,
                                                     18.56,
                                                     19.97,
                                                     20.75,
                                                     20.22,
                                                     20.87,
                                                     0.00,
                                                     19.09]
            elif data_i.iteration == 3: # GSI stage 2 (o - a)
                if data_i.usage == 'asm': # assimilated
                    if data_i.type == '120':
                        if data_i.statistic == 'count':
                            assert data_i.values == [685,
                                                     462,
                                                     800,
                                                     948,
                                                     469,
                                                     1459,
                                                     823,
                                                     873,
                                                     1350,
                                                     1403,
                                                     0,
                                                     9272]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [2.39,
                                                     1.63,
                                                     2.16,
                                                     3.47,
                                                     4.38,
                                                     2.33,
                                                     0.08,
                                                     1.62,
                                                     3.11,
                                                     1.91,
                                                     0.00,
                                                     2.29]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [14.34,
                                                     16.32,
                                                     15.57,
                                                     13.70,
                                                     16.35,
                                                     14.32,
                                                     15.95,
                                                     16.48,
                                                     16.04,
                                                     17.62,
                                                     0.00,
                                                     15.72]
                                                     
def test_temperature_plevs():
    data_list = harvest(VALID_CONFIG_DICT_GEOS_IT_1998)
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_t_data':
            assert data_i.plevs_top == [1000.0,
                                           900.0,
                                           800.0,
                                           600.0,
                                           400.0,
                                           300.0,
                                           250.0,
                                           200.0,
                                           150.0,
                                           100.0,
                                           50.0,
                                           0.0]
            assert data_i.plevs_bot == [1200.0,
                                           1000.0,
                                           900.0,
                                           800.0,
                                           600.0,
                                           400.0,
                                           300.0,
                                           250.0,
                                           200.0,
                                           150.0,
                                           100.0,
                                           2000.0]
            #assert data_i.plevs_units[0] == 'hPa'
                                           
def test_temperature_rawinsonde():
    data_list = harvest(VALID_CONFIG_DICT_GEOS_IT_1998)
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_t_data': # temperature
            if data_i.type == '120': # rawinsonde
                if data_i.iteration == 1: # GSI stage 1 (o - b)
                    if data_i.usage == 'asm': # assimilated
                        if data_i.statistic == 'count':
                            assert data_i.values == [689,
                                                     1277,
                                                     1439,
                                                     2316,
                                                     2314,
                                                     2034,
                                                     457,
                                                     1066,
                                                     1184,
                                                     1870,
                                                     1837,
                                                     19226]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.64,
                                                     0.65,
                                                     0.10,
                                                     0.05,
                                                     0.00,
                                                     -0.02,
                                                     0.01,
                                                     0.22,
                                                     0.46,
                                                     0.21,
                                                     0.16,
                                                     0.20]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [2.25,
                                                     2.29,
                                                     1.69,
                                                     1.29,
                                                     1.16,
                                                     1.27,
                                                     1.42,
                                                     1.50,
                                                     1.77,
                                                     1.77,
                                                     2.12,
                                                     1.76]

def test_temperature_oma():
    data_list = harvest(VALID_CONFIG_DICT_GEOS_IT_1998)
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_t_data':
            data_i.units == 'K'
            if data_i.iteration == 2:
                if data_i.usage == 'asm':
                    if data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [2173,
                                                     2594,
                                                     2102,
                                                     3541,
                                                     3682,
                                                     3194,
                                                     2294,
                                                     5158,
                                                     2319,
                                                     1870,
                                                     1837,
                                                     33507]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.58,
                                                     0.14,
                                                     0.04,
                                                     0.03,
                                                     -0.01,
                                                     0.03,
                                                     0.03,
                                                     0.03,
                                                     0.19,
                                                     0.22,
                                                     0.17,
                                                     0.12]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [1.61,
                                                     1.28,
                                                     0.87,
                                                     0.65,
                                                     0.70,
                                                     0.64,
                                                     0.83,
                                                     0.95,
                                                     1.24,
                                                     1.46,
                                                     1.92,
                                                     1.21]
                if data_i.usage == 'mon':
                    if data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [13864,
                                                     12319,
                                                     1951,
                                                     690,
                                                     193,
                                                     140,
                                                     174,
                                                     150,
                                                     31,
                                                     32,
                                                     29,
                                                     29603]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.21,
                                                     -0.06,
                                                     -0.57,
                                                     0.29,
                                                     -0.20,
                                                     0.94,
                                                     0.48,
                                                     0.17,
                                                     0.92,
                                                     0.98,
                                                     0.13,
                                                     0.04]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [2.75,
                                                     3.21,
                                                     4.58,
                                                     4.59,
                                                     2.72,
                                                     3.89,
                                                     1.53,
                                                     3.51,
                                                     2.47,
                                                     5.29,
                                                     4.46,
                                                     3.20]
                                                     
def test_fit_of_surface_pressure_data():
    data_list = harvest(VALID_CONFIG_DICT_GEOS_IT_1998)    
    
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_psfc_data':
            assert data_i.plevs_top == [0.]
            assert data_i.plevs_bot == [2000]
            assert data_i.plevs_units == 'hPa'
            
            if data_i.iteration == 1:
                if data_i.usage == 'asm':
                    if data_i.type == '120':
                        if data_i.statistic == 'count':
                            assert data_i.values == [554]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.0782]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [1.2762]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.8038]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.8038]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [24671]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.0287]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [1.1103]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.3278]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.3278]
                elif data_i.usage == 'rej':
                    if data_i.type == '191':
                        if data_i.statistic == 'count':
                            assert data_i.values == [13]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [1.2394]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [11.2536]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [516]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [10.9602]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [128.1309]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0]
                elif data_i.usage == 'mon':
                    if data_i.type == '180' and data_i.subtype=='0000':
                        if data_i.statistic == 'count':
                            assert data_i.values == [56]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.2842]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [1.2113]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [2.0752]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [2.0752]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [5976]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.4145]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [1.7839]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.3715]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.3715]
            elif data_i.iteration == 2:
                if data_i.usage == 'asm':
                    if data_i.type == '199':
                        if data_i.statistic == 'count':
                            assert data_i.values == [636]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.1453]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.7877]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.4145]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.4145]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [24731]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.0048]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.9001]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.2089]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.2089]
                
                elif data_i.usage == 'rej':
                    if data_i.type == '180' and data_i.subtype == '0001':
                        if data_i.statistic == 'count':
                            assert data_i.values == [39]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-2.4857]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [9.3272]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [454]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [12.2027]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [136.5802]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0]
                            
                elif data_i.usage == 'mon':
                    if data_i.type == '180' and data_i.subtype == '0001':
                        if data_i.statistic == 'count':
                            assert data_i.values == [71]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.5283]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [1.7090]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [2.4770]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [2.4770]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [5978]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.2945]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [1.6624]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.3407]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.3407]
            
            elif data_i.iteration == 3:
                if data_i.usage == 'asm':
                    if data_i.type == '120':
                        if data_i.statistic == 'count':
                            assert data_i.values == [555]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.0520]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.9763]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.4866]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.4866]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [24730]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.0078]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.8955]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.2062]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.2062]

def test_fit_of_uv_wind_data():
    data_list = harvest(VALID_CONFIG_DICT_GEOS_IT_1998)    
    
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_uv_data':
            assert data_i.plevs_top == [1000.0,
                                         900.0,
                                         800.0,
                                         600.0,
                                         400.0,
                                         300.0,
                                         250.0,
                                         200.0,
                                         150.0,
                                         100.0,
                                         50.0,
                                         0.0]
            assert data_i.plevs_bot == [1200.0,
                                         1000.0,
                                         900.0,
                                         800.0,
                                         600.0,
                                         400.0,
                                         300.0,
                                         250.0,
                                         200.0,
                                         150.0,
                                         100.0,
                                         2000.0]
            #assert data_i.plevs_units == ['hPa', 'hPa']
            
            if data_i.iteration == 1:
                if data_i.usage == 'asm':
                    if data_i.type == '220':
                        if data_i.statistic == 'count':
                            assert data_i.values == [657,
                                                     1614,
                                                     1503,
                                                     2621,
                                                     2419,
                                                     1987,
                                                     544,
                                                     1210,
                                                     1277,
                                                     2190,
                                                     1997,
                                                     21022]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.13,
                                                     0.44,
                                                     0.51,
                                                     0.40,
                                                     0.37,
                                                     0.49,
                                                     0.74,
                                                     0.64,
                                                     0.55,
                                                     0.05,
                                                     0.02,
                                                     0.37]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [3.14,
                                                     3.77,
                                                     3.93,
                                                     4.34,
                                                     5.17,
                                                     5.63,
                                                     6.24,
                                                     5.90,
                                                     5.94,
                                                     5.42,
                                                     5.40,
                                                     5.20]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.99,
                                                     2.05,
                                                     2.66,
                                                     2.76,
                                                     2.35,
                                                     2.43,
                                                     2.44,
                                                     2.30,
                                                     2.41,
                                                     1.94,
                                                     1.92,
                                                     2.16]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.99,
                                                     2.05,
                                                     2.66,
                                                     2.76,
                                                     2.35,
                                                     2.43,
                                                     2.44,
                                                     2.30,
                                                     2.41,
                                                     1.94,
                                                     1.92,
                                                     2.16]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [2332,
                                                     5239,
                                                     5264,
                                                     6959,
                                                     8120,
                                                     12572,
                                                     5729,
                                                     9977,
                                                     6663,
                                                     4492,
                                                     2340,
                                                     72691]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.83,
                                                     0.18,
                                                     0.10,
                                                     0.26,
                                                     0.16,
                                                     0.44,
                                                     0.85,
                                                     0.96,
                                                     0.52,
                                                     0.40,
                                                     -0.06,
                                                     0.45]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [3.67,
                                                     3.66,
                                                     3.50,
                                                     3.85,
                                                     4.33,
                                                     4.84,
                                                     5.30,
                                                     5.24,
                                                     5.47,
                                                     5.42,
                                                     5.33,
                                                     4.77]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.96,
                                                     1.08,
                                                     1.21,
                                                     1.47,
                                                     1.08,
                                                     0.65,
                                                     0.86,
                                                     1.05,
                                                     1.00,
                                                     1.13,
                                                     1.72,
                                                     1.06]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.96,
                                                     1.08,
                                                     1.21,
                                                     1.47,
                                                     1.08,
                                                     0.65,
                                                     0.86,
                                                     1.05,
                                                     1.00,
                                                     1.13,
                                                     1.72,
                                                     1.06]
                elif data_i.usage == 'rej':
                    if data_i.type == '299':
                        if data_i.statistic == 'count':
                            assert data_i.values == [0,
                                                     1,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     1]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.00,
                                                     10.69,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     10.69]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.00,
                                                     48.11,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     48.11]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [23,
                                                     72,
                                                     156,
                                                     267,
                                                     283,
                                                     1638,
                                                     372,
                                                     396,
                                                     289,
                                                     163,
                                                     12,
                                                     3695]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [50.77,
                                                     0.86,
                                                     -6.77,
                                                     -7.48,
                                                     -5.54,
                                                     0.16,
                                                     8.12,
                                                     6.85,
                                                     3.64,
                                                     4.20,
                                                     41.94,
                                                     1.51]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [89.36,
                                                     18.24,
                                                     13.97,
                                                     21.22,
                                                     16.92,
                                                     15.08,
                                                     28.32,
                                                     21.09,
                                                     28.47,
                                                     21.54,
                                                     65.49,
                                                     21.61]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00]
                elif data_i.usage == 'mon':
                    if data_i.type == '240' and data_i.subtype=='0252':
                        if data_i.statistic == 'count':
                            assert data_i.values == [0,
                                                     12131,
                                                     24464,
                                                     2452,
                                                     34,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     39081]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.00,
                                                     0.19,
                                                     0.39,
                                                     0.39,
                                                     -1.40,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.33]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.00,
                                                     2.37,
                                                     2.60,
                                                     3.94,
                                                     8.61,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     2.65]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [27247,
                                                     33974,
                                                     28711,
                                                     4329,
                                                     365,
                                                     197,
                                                     197,
                                                     182,
                                                     68,
                                                     94,
                                                     110,
                                                     95633]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.44,
                                                     0.45,
                                                     0.44,
                                                     0.20,
                                                     -2.54,
                                                     0.64,
                                                     -1.32,
                                                     -1.21,
                                                     -1.57,
                                                     3.25,
                                                     7.70,
                                                     0.43]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [2.76,
                                                     2.99,
                                                     2.99,
                                                     5.28,
                                                     11.65,
                                                     14.12,
                                                     9.96,
                                                     10.46,
                                                     19.24,
                                                     18.64,
                                                     23.02,
                                                     3.53]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.36,
                                                     0.14,
                                                     0.05,
                                                     0.25,
                                                     1.50,
                                                     3.03,
                                                     3.22,
                                                     2.94,
                                                     0.27,
                                                     0.05,
                                                     0.00,
                                                     0.21]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.36,
                                                     0.14,
                                                     0.05,
                                                     0.25,
                                                     1.50,
                                                     3.03,
                                                     3.22,
                                                     2.94,
                                                     0.27,
                                                     0.05,
                                                     0.00,
                                                     0.21]
            elif data_i.iteration == 2:
                if data_i.usage == 'asm':
                    if data_i.type == '247' and data_i.subtype == '0253':
                        if data_i.statistic == 'count':
                            assert data_i.values == [0,
                                                     0,
                                                     0,
                                                     0,
                                                     588,
                                                     3283,
                                                     711,
                                                     804,
                                                     720,
                                                     392,
                                                     0,
                                                     6498]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.35,
                                                     0.66,
                                                     1.07,
                                                     0.67,
                                                     0.68,
                                                     1.91,
                                                     0.00,
                                                     0.76]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     3.54,
                                                     3.93,
                                                     4.27,
                                                     4.37,
                                                     4.17,
                                                     4.34,
                                                     0.00,
                                                     4.04]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.06,
                                                     0.05,
                                                     0.05,
                                                     0.05,
                                                     0.04,
                                                     0.05,
                                                     0.00,
                                                     0.05]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.06,
                                                     0.05,
                                                     0.05,
                                                     0.05,
                                                     0.04,
                                                     0.05,
                                                     0.00,
                                                     0.05]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [2334,
                                                     5241,
                                                     5275,
                                                     6977,
                                                     8190,
                                                     12887,
                                                     5835,
                                                     10136,
                                                     6808,
                                                     4597,
                                                     2337,
                                                     73627]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.73,
                                                     0.32,
                                                     0.16,
                                                     0.24,
                                                     0.07,
                                                     0.25,
                                                     0.41,
                                                     0.46,
                                                     0.40,
                                                     0.46,
                                                     0.38,
                                                     0.33]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [3.13,
                                                     2.75,
                                                     2.44,
                                                     2.60,
                                                     3.08,
                                                     3.88,
                                                     4.16,
                                                     4.01,
                                                     4.12,
                                                     3.90,
                                                     4.17,
                                                     3.65]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.65,
                                                     0.47,
                                                     0.45,
                                                     0.53,
                                                     0.42,
                                                     0.27,
                                                     0.42,
                                                     0.55,
                                                     0.49,
                                                     0.52,
                                                     1.07,
                                                     0.49]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.65,
                                                     0.47,
                                                     0.45,
                                                     0.53,
                                                     0.42,
                                                     0.27,
                                                     0.42,
                                                     0.55,
                                                     0.49,
                                                     0.52,
                                                     1.07,
                                                     0.49]
                
            elif data_i.iteration == 3:    
                if data_i.usage == 'asm':
                    if data_i.type == '280' and data_i.subtype == '0001':
                        if data_i.statistic == 'count':
                            assert data_i.values == [830,
                                                     196,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     1026]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [1.49,
                                                     2.15,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     1.62]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [3.85,
                                                     4.78,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     4.05]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.91,
                                                     0.96,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.92]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.91,
                                                     0.96,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.92]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [2334,
                                                     5241,
                                                     5277,
                                                     6978,
                                                     8192,
                                                     12939,
                                                     5844,
                                                     10145,
                                                     6818,
                                                     4600,
                                                     2336,
                                                     73714]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.73,
                                                     0.31,
                                                     0.16,
                                                     0.24,
                                                     0.06,
                                                     0.26,
                                                     0.40,
                                                     0.45,
                                                     0.39,
                                                     0.43,
                                                     0.38,
                                                     0.32]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [3.13,
                                                     2.74,
                                                     2.43,
                                                     2.57,
                                                     3.03,
                                                     3.86,
                                                     4.12,
                                                     3.99,
                                                     4.10,
                                                     3.84,
                                                     4.16,
                                                     3.62]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.65,
                                                     0.47,
                                                     0.44,
                                                     0.52,
                                                     0.40,
                                                     0.26,
                                                     0.42,
                                                     0.54,
                                                     0.49,
                                                     0.51,
                                                     1.07,
                                                     0.49]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.65,
                                                     0.47,
                                                     0.44,
                                                     0.52,
                                                     0.40,
                                                     0.26,
                                                     0.42,
                                                     0.54,
                                                     0.49,
                                                     0.51,
                                                     1.07,
                                                     0.49]
                
                elif data_i.usage == 'mon':
                    if data_i.type == '280' and data_i.subtype == '0000':
                        if data_i.statistic == 'count':
                            assert data_i.values == [10,
                                                     32,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     42]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.47,
                                                     4.29,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     3.38]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [7.93,
                                                     7.98,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     7.97]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [4.99,
                                                     2.58,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     3.15]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [4.99,
                                                     2.58,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     0.00,
                                                     3.15]
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [27170,
                                                     34045,
                                                     28713,
                                                     4334,
                                                     367,
                                                     193,
                                                     196,
                                                     182,
                                                     69,
                                                     95,
                                                     111,
                                                     95636]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.41,
                                                     0.41,
                                                     0.46,
                                                     0.14,
                                                     -2.82,
                                                     0.39,
                                                     -1.25,
                                                     -0.88,
                                                     -2.02,
                                                     2.72,
                                                     8.41,
                                                     0.41]
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [2.68,
                                                     2.98,
                                                     2.67,
                                                     4.92,
                                                     11.22,
                                                     13.79,
                                                     10.02,
                                                     10.52,
                                                     18.81,
                                                     18.04,
                                                     23.06,
                                                     3.39]
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.34,
                                                     0.17,
                                                     0.04,
                                                     0.28,
                                                     1.51,
                                                     3.30,
                                                     2.99,
                                                     2.64,
                                                     0.21,
                                                     0.07,
                                                     0.00,
                                                     0.21]
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.34,
                                                     0.17,
                                                     0.04,
                                                     0.28,
                                                     1.51,
                                                     3.30,
                                                     2.99,
                                                     2.64,
                                                     0.21,
                                                     0.07,
                                                     0.00,
                                                     0.21]

def run_all():
    test_datetime_geos_it_1998()
    test_longnames()
    test_units()
    test_qsat_plevs()
    test_qsat_asm()
    test_temperature_plevs()
    test_temperature_rawinsonde()
    test_temperature_oma()
    test_fit_of_surface_pressure_data()
    test_fit_of_uv_wind_data()
    
def main():
    run_all()
    
if __name__=='__main__':
    main()