#!/usr/bin/env python

#TODO: CRITICAL!!! refactor unit tests so that they assert exisitence of values to be checked under if statements, which can currently be bypassed if the data don't exist

"""Unit tests for gsi_satellite_radiance.py
"""

import os,sys
from pathlib import Path
from datetime import datetime

from score_hv import hv_registry
from score_hv.harvester_base import harvest

PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
FIT_FILE_PATH = os.path.join(PYTEST_CALLING_DIR, 'data',
                             'gsistat.gdas.1979100100_clean')
                             
VALID_CONFIG_DICT = {
    'harvester_name': hv_registry.GSI_CONVENTIONAL_OBS,
    'filename': FIT_FILE_PATH,
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
        (1200.0, 1000.0),
        (999.9, 900.0),
        (899.9, 800.0),
        (799.9, 600.0),
        (599.9, 400.0),
        (399.9, 300.0),
        (299.9, 250.0),
        (249.9, 200.0),
        (199.9, 150.0),
        (149.9, 100.0),
        (99.9, 50.0),
        (2000.0, 0.0),
    ]
    }
    
VALID_CONFIG_DICT_QSAT = {
    'harvester_name': hv_registry.GSI_CONVENTIONAL_OBS,
    'filename': FIT_FILE_PATH,
    'variables': ('fit_psfc_data', # fit of surface pressure data (mb)
                  'fit_uv_data', # fit of u, v wind data (m/s),
                  'fit_t_data', # fit of temperature data (K)
                  'fit_q_data', # fit of moisture data (% of qsaturation guess)
                  ),
    'statistics': (
        'count', # number of obs summed under obs types and vertical layers
        'bias', # bias of obs departure for each outer loop (it)
        'rms', # root mean squre error of obs departure for each outer loop (it)
        #'cpen', # obs part of penalty (cost function)
        #'qcpen' # nonlinear qc penalty
        ),
        
    'plev_bounds': [
        (1200.0, 1000.0),
        (999.9, 950.0),
        (949.9, 900.0),
        (899.9, 850.0),
        (849.9, 800.0),
        (799.9, 700.0),
        (699.9, 600.0),
        (599.9, 500.0),
        (499.9, 400.0),
        (399.9, 300.0),
        (299.9, 0.0),
        (2000.0, 0.0),
    ]
}
                    
def test_datetime():
    data_list = harvest(VALID_CONFIG_DICT)
    test_datetime = datetime.strptime('1979100100', '%Y%m%d%H')
    for i, data_i in enumerate(data_list):
        print(f"{i=}, datetime from data_i: {data_i.datetime}")
        assert test_datetime == data_i.datetime

def test_longnames():
    data_list = harvest(VALID_CONFIG_DICT)
    test_complete = False
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_psfc_data':
            assert data_i.longname == 'fit of surface pressure data'
            test_complete = True

    assert test_complete

def test_units():
    data_list = harvest(VALID_CONFIG_DICT)
    test_count = False
    test_psfc = False
    test_q = False
    test_t = False
    test_uv = False
    for i, data_i in enumerate(data_list):
        if data_i.statistic == 'count':
            assert data_i.units == None
            test_count = True
        elif data_i.variable == 'fit_psfc_data':
            assert data_i.units == 'mb'
            test_psfc = True
        elif data_i.variable == 'fit_q_data':
            assert data_i.units == r'%'
            test_q = True
        elif data_i.variable == 'fit_t_data':
            assert data_i.units == 'K'
            test_t = True
        elif data_i.variable == 'fit_uv_data':
            assert data_i.units == 'm/s'
            test_uv = True

    assert test_count
    assert test_psfc
    assert test_q
    assert test_t
    assert test_uv

def test_bad_config():
    """test that a misconfigured config_dict does not result in data being
    returned by the harvester
    """

    bad_config_dict = {
        'harvester_name': 
        hv_registry.GSI_CONVENTIONAL_OBS,
        'filename': FIT_FILE_PATH,
        'variables': ('fit_psfc_data',
                      'bias_correction_coefficients'),
        'statistics': ('count',
                       'nobs_used',
                       'nobs_tossed',
                       'variance',
                       'bias_pre_corr',
                       'bias_post_corr',
                       'qcpenalty',
                       'sqrt_bias',
                       'std')
                   }

    try:
        data = harvest(bad_config_dict)
        exception_caught = False
    except KeyError:
        exception_caught = True

    assert exception_caught

def test_qsat_plevs():
    data_list = harvest(VALID_CONFIG_DICT_QSAT)
    test_complete = False
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
                                        999.9,
                                        949.9,
                                        899.9,
                                        849.9,
                                        799.9,
                                        699.9,
                                        599.9,
                                        499.9,
                                        399.9,
                                        299.9,
                                        2000.0]
            #assert data_i.plevs_units[1] == 'hPa'

            test_complete = True

    assert test_complete

def test_qsat_asm():
    data_list = harvest(VALID_CONFIG_DICT_QSAT)
    test_stage1_count = False
    test_stage1_bias = False
    test_stage1_rms = False
    test_stage2_count = False
    test_stage2_bias = False
    test_stage2_rms = False
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_q_data':
            if data_i.iteration == 1: # GSI stage 1 (o - b)
                if data_i.usage == 'asm': # assimilated
                    if data_i.type == 'all':
                        if data_i.statistic == 'count':
                            print("the q and count ",data_i.values)
                            assert data_i.values == [
                                                     1780, 719, 676, 1106, 442, 1731, 961, 1039, 1541, 1152, 0, 12277
                            ]
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [5.38,
                                                     3.35,
                                                     0.25,
                                                     2.09,
                                                     0.33,
                                                     -0.43,
                                                     -0.46,
                                                     -0.95, 
                                                     2.26, 
                                                     5.04, 
                                                     0.00, 
                                                     1.88]
                            test_stage1_bias = True
                            print("end of testing q")
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [13.67,
                                                     15.92,
                                                     15.71,
                                                     17.72,
                                                     17.95,
                                                     19.33,
                                                     20.92,
                                                     22.41,
                                                     22.82,
                                                     23.16,
                                                     0.00,
                                                     19.45]
                            test_stage1_rms = True
            elif data_i.iteration == 2: # GSI stage 2 (o - a)
                if data_i.usage == 'asm': # assimilated
                    if data_i.type == '180':
                        if data_i.statistic == 'count':
                            assert data_i.values == [1007,
                                                     39,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     1046]
                            test_stage2_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.660E+01,
                                                     0.218E+01,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.622E+01]
                            test_stage2_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.153E+02,
                                                     0.172E+02,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.155E+02]
                            test_stage2_rms = True

    assert test_stage1_count
    assert test_stage1_bias
    assert test_stage1_rms
    assert test_stage2_count
    assert test_stage2_bias
    assert test_stage2_rms

def test_temperature_plevs():
    data_list = harvest(VALID_CONFIG_DICT)
    test_complete = False
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_t_data':
            assert data_i.plevs_top == [0.100E+04,
                                           0.900E+03,
                                           0.800E+03,
                                           0.600E+03,
                                           0.400E+03,
                                           0.300E+03,
                                           0.250E+03,
                                           0.200E+03,
                                           0.150E+03,
                                           0.100E+03,
                                           0.500E+02,
                                           0.000E+00]
            assert data_i.plevs_bot == [0.120E+04,
                                           0.100E+04,
                                           0.900E+03,
                                           0.800E+03,
                                           0.600E+03,
                                           0.400E+03,
                                           0.300E+03,
                                           0.250E+03,
                                           0.200E+03,
                                           0.150E+03,
                                           0.100E+03,
                                           0.200E+04]
            #assert data_i.plevs_units[0] == 'hPa'
            test_complete = True

    assert test_complete

def test_temperature_rawinsonde():
    data_list = harvest(VALID_CONFIG_DICT)
    test_count = False
    test_bias = False
    test_rms = False
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_t_data': # temperature
            if data_i.type == '120': # rawinsonde
                if data_i.iteration == 1: # GSI stage 1 (o - b)
                    if data_i.usage == 'asm': # assimilated
                        if data_i.statistic == 'count':
                            assert data_i.values == [788,
                                                     1256,
                                                     1797,
                                                     3060,
                                                     2784,
                                                     2399,
                                                     522,
                                                     1349,
                                                     1498,
                                                     1999,
                                                     1781,
                                                     21940]
                            test_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.500E+00,
                                                     -0.275E-01,
                                                     -0.860E-01,
                                                     -0.153E+00,
                                                     -0.212E+00,
                                                     -0.373E+00,
                                                     -0.622E+00,
                                                     -0.425E+00,
                                                     0.111E+00,
                                                     0.969E+00,
                                                     0.177E+01,
                                                     0.114E+00]
                            test_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.361E+01,
                                                     0.299E+01,
                                                     0.223E+01,
                                                     0.183E+01,
                                                     0.164E+01,
                                                     0.176E+01,
                                                     0.238E+01,
                                                     0.218E+01,
                                                     0.231E+01,
                                                     0.218E+01,
                                                     0.293E+01,
                                                     0.235E+01]
                            test_rms = True

    assert test_count
    assert test_bias
    assert test_rms

def test_temperature_oma():
    data_list = harvest(VALID_CONFIG_DICT)
    test_asm_count = False
    test_asm_bias = False
    test_asm_rms = False
    test_mon_count = False
    test_mon_bias = False
    test_mon_rms = False
    
    
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_t_data':
            if data_i.statistic == 'count':
                assert data_i.units is None
            else:
                assert data_i.units == 'K'
            
            if data_i.iteration == 2:
                if data_i.usage == 'asm':
                    if data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [2205,
                                                     1419,
                                                     1802,
                                                     3066,
                                                     2818,
                                                     2548,
                                                     902,
                                                     1857,
                                                     1612,
                                                     1999,
                                                     1782,
                                                     24717]
                            test_asm_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.125E+00,
                                                     0.480E-01,
                                                     0.505E-01,
                                                     -0.311E-01,
                                                     -0.964E-01,
                                                     -0.245E+00,
                                                     -0.348E+00,
                                                     -0.224E+00,
                                                     0.396E-01,
                                                     0.788E+00,
                                                     0.157E+01,
                                                     0.154E+00]
                            test_asm_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.283E+01,
                                                     0.268E+01,
                                                     0.179E+01,
                                                     0.140E+01,
                                                     0.125E+01,
                                                     0.152E+01,
                                                     0.208E+01,
                                                     0.209E+01,
                                                     0.208E+01,
                                                     0.192E+01,
                                                     0.267E+01,
                                                     0.210E+01]
                            test_asm_rms = True
                if data_i.usage == 'mon':
                    if data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [44,
                                                     39,
                                                     13,
                                                     18,
                                                     40,
                                                     44,
                                                     126,
                                                     142,
                                                     48,
                                                     18,
                                                     14,
                                                     568]
                            test_mon_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.121E+01,
                                                     0.600E+00,
                                                     0.931E+01,
                                                     -0.298E+01,
                                                     -0.829E+00,
                                                     -0.240E+01,
                                                     -0.596E+00,
                                                     0.350E-02,
                                                     0.458E+00,
                                                     0.320E+00,
                                                     0.140E+01,
                                                     -0.529E+00]
                            test_mon_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.564E+01,
                                                     0.475E+01,
                                                     0.188E+02,
                                                     0.119E+02,
                                                     0.103E+02,
                                                     0.719E+01,
                                                     0.329E+01,
                                                     0.395E+01,
                                                     0.607E+01,
                                                     0.692E+01,
                                                     0.574E+01,
                                                     0.817E+01]
                            test_mon_rms = True
    assert test_asm_count
    assert test_asm_bias
    assert test_asm_rms
    assert test_mon_count
    assert test_mon_bias
    assert test_mon_rms
                                                     
def test_fit_of_surface_pressure_data():
    data_list = harvest(VALID_CONFIG_DICT)    
    
    test_plevs = False
    test_gsistage1_asm_120_count = False
    test_gsistage1_asm_120_bias = False
    test_gsistage1_asm_120_rms = False
    test_gsistage1_asm_120_cpen = False
    test_gsistage1_asm_120_qcpen = False
    test_gsistage1_asm_all_count = False
    test_gsistage1_asm_all_bias = False
    test_gsistage1_asm_all_rms = False
    test_gsistage1_asm_all_cpen = False
    test_gsistage1_asm_all_qcpen = False
    test_gsistage1_rej_191_count = False
    test_gsistage1_rej_191_bias = False
    test_gsistage1_rej_191_rms = False
    test_gsistage1_rej_191_cpen = False
    test_gsistage1_rej_191_qcpen = False
    test_gsistage1_rej_all_count = False
    test_gsistage1_rej_all_bias = False
    test_gsistage1_rej_all_rms = False
    test_gsistage1_rej_all_cpen = False
    test_gsistage1_rej_all_qcpen = False
    test_gsistage1_mon_180_count = False
    test_gsistage1_mon_180_bias = False
    test_gsistage1_mon_180_rms = False
    test_gsistage1_mon_180_cpen = False
    test_gsistage1_mon_180_qcpen = False
    test_gsistage1_mon_all_count = False
    test_gsistage1_mon_all_bias = False
    test_gsistage1_mon_all_rms = False
    test_gsistage1_mon_all_cpen = False
    test_gsistage1_mon_all_qcpen = False
    test_gsistage2_asm_191_count = False
    test_gsistage2_asm_191_bias = False
    test_gsistage2_asm_191_rms = False
    test_gsistage2_asm_191_cpen = False
    test_gsistage2_asm_191_qcpen = False
    test_gsistage2_asm_all_count = False
    test_gsistage2_asm_all_bias = False
    test_gsistage2_asm_all_rms = False
    test_gsistage2_asm_all_cpen = False
    test_gsistage2_asm_all_qcpen = False
    test_gsistage2_rej_180_count = False
    test_gsistage2_rej_180_bias = False
    test_gsistage2_rej_180_rms = False
    test_gsistage2_rej_180_cpen = False
    test_gsistage2_rej_180_qcpen = False
    test_gsistage2_rej_all_count = False
    test_gsistage2_rej_all_bias = False
    test_gsistage2_rej_all_rms = False
    test_gsistage2_rej_all_cpen = False
    test_gsistage2_rej_all_qcpen = False
    test_gsistage2_mon_180_count = False
    test_gsistage2_mon_180_bias = False
    test_gsistage2_mon_180_rms = False
    test_gsistage2_mon_180_cpen = False
    test_gsistage2_mon_180_qcpen = False
    test_gsistage2_mon_all_count = False
    test_gsistage2_mon_all_bias = False
    test_gsistage2_mon_all_rms = False
    test_gsistage2_mon_all_cpen = False
    test_gsistage2_mon_all_qcpen = False

    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_psfc_data':
            assert data_i.plevs_top == [0.]
            assert data_i.plevs_bot == [2000]
            assert data_i.plevs_units == 'hPa'
            test_plevs = True
            
            if data_i.iteration == 1:
                if data_i.usage == 'asm':
                    if data_i.type == '120':
                        if data_i.statistic == 'count':
                            assert data_i.values == [672]
                            test_gsistage1_asm_120_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.224E+00]
                            test_gsistage1_asm_120_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.168E+01]
                            test_gsistage1_asm_120_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.569E+00]
                            test_gsistage1_asm_120_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.500E+00]
                            test_gsistage1_asm_120_qcpen = True
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [10716]
                            test_gsistage1_asm_all_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.411E+00]
                            test_gsistage1_asm_all_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.192E+01]
                            test_gsistage1_asm_all_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.827E+00]
                            test_gsistage1_asm_all_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.687E+00]
                            test_gsistage1_asm_all_qcpen = True
                elif data_i.usage == 'rej':
                    if data_i.type == '191':
                        if data_i.statistic == 'count':
                            assert data_i.values == [14]
                            test_gsistage1_rej_191_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.640E+01]
                            test_gsistage1_rej_191_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.100E+02]
                            test_gsistage1_rej_191_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00]
                            test_gsistage1_rej_191_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00]
                            test_gsistage1_rej_191_qcpen = True
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [551]
                            test_gsistage1_rej_all_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.559E+02]
                            test_gsistage1_rej_all_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.262E+03]
                            test_gsistage1_rej_all_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00]
                            test_gsistage1_rej_all_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00]
                            test_gsistage1_rej_all_qcpen = True
                elif data_i.usage == 'mon':
                    if data_i.type == '180' and data_i.subtype == '0001':
                        if data_i.statistic == 'count':
                            assert data_i.values == [25]
                            test_gsistage1_mon_180_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.245E+00]
                            test_gsistage1_mon_180_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.250E+01]
                            test_gsistage1_mon_180_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.122E+01]
                            test_gsistage1_mon_180_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.998E+00]
                            test_gsistage1_mon_180_qcpen = True
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [123]
                            test_gsistage1_mon_all_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.102E+01]
                            test_gsistage1_mon_all_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.294E+01]
                            test_gsistage1_mon_all_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.736E+00]
                            test_gsistage1_mon_all_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.513E+00]
                            test_gsistage1_mon_all_qcpen = True

            elif data_i.iteration == 2:
                if data_i.usage == 'asm':
                    if data_i.type == '191':
                        if data_i.statistic == 'count':
                            assert data_i.values == [38]
                            test_gsistage2_asm_191_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.438E+00]
                            test_gsistage2_asm_191_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.197E+01]
                            test_gsistage2_asm_191_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.173E+01]
                            test_gsistage2_asm_191_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.160E+01]
                            test_gsistage2_asm_191_qcpen = True
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [10745]
                            test_gsistage2_asm_all_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.319E+00]
                            test_gsistage2_asm_all_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.173E+01]
                            test_gsistage2_asm_all_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.650E+00]
                            test_gsistage2_asm_all_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.543E+00]
                            test_gsistage2_asm_all_qcpen = True

                elif data_i.usage == 'rej':
                    if data_i.type == '180' and data_i.subtype == '0001':
                        if data_i.statistic == 'count':
                            assert data_i.values == [55]
                            test_gsistage2_rej_180_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.555E+01]
                            test_gsistage2_rej_180_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.187E+02]
                            test_gsistage2_rej_180_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00]
                            test_gsistage2_rej_180_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00]
                            test_gsistage2_rej_180_qcpen = True
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [522]
                            test_gsistage2_rej_all_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.593E+02]
                            test_gsistage2_rej_all_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.269E+03]
                            test_gsistage2_rej_all_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00]
                            test_gsistage2_rej_all_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00]
                            test_gsistage2_rej_all_qcpen = True

                elif data_i.usage == 'mon':
                    if data_i.type == '180' and data_i.subtype == '0000':
                        if data_i.statistic == 'count':
                            assert data_i.values == [2]
                            test_gsistage2_mon_180_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.634E+00]
                            test_gsistage2_mon_180_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.634E+00]
                            test_gsistage2_mon_180_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.197E+00]
                            test_gsistage2_mon_180_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.197E+00]
                            test_gsistage2_mon_180_qcpen = True
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [123]
                            test_gsistage2_mon_all_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [-0.839E+00]
                            test_gsistage2_mon_all_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.288E+01]
                            test_gsistage2_mon_all_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.714E+00]
                            test_gsistage2_mon_all_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.483E+00]
                            test_gsistage2_mon_all_qcpen = True

    # Assert all flags to confirm all tests passed
    assert test_plevs
    assert test_gsistage1_asm_120_count
    assert test_gsistage1_asm_120_bias
    assert test_gsistage1_asm_120_rms
    assert test_gsistage1_asm_120_cpen
    assert test_gsistage1_asm_120_qcpen
    assert test_gsistage1_asm_all_count
    assert test_gsistage1_asm_all_bias
    assert test_gsistage1_asm_all_rms
    assert test_gsistage1_asm_all_cpen
    assert test_gsistage1_asm_all_qcpen
    assert test_gsistage1_rej_191_count
    assert test_gsistage1_rej_191_bias
    assert test_gsistage1_rej_191_rms
    assert test_gsistage1_rej_191_cpen
    assert test_gsistage1_rej_191_qcpen
    assert test_gsistage1_rej_all_count
    assert test_gsistage1_rej_all_bias
    assert test_gsistage1_rej_all_rms
    assert test_gsistage1_rej_all_cpen
    assert test_gsistage1_rej_all_qcpen
    assert test_gsistage1_mon_180_count
    assert test_gsistage1_mon_180_bias
    assert test_gsistage1_mon_180_rms
    assert test_gsistage1_mon_180_cpen
    assert test_gsistage1_mon_180_qcpen
    assert test_gsistage1_mon_all_count
    assert test_gsistage1_mon_all_bias
    assert test_gsistage1_mon_all_rms
    assert test_gsistage1_mon_all_cpen
    assert test_gsistage1_mon_all_qcpen
    assert test_gsistage2_asm_191_count
    assert test_gsistage2_asm_191_bias
    assert test_gsistage2_asm_191_rms
    assert test_gsistage2_asm_191_cpen
    assert test_gsistage2_asm_191_qcpen
    assert test_gsistage2_asm_all_count
    assert test_gsistage2_asm_all_bias
    assert test_gsistage2_asm_all_rms
    assert test_gsistage2_asm_all_cpen
    assert test_gsistage2_asm_all_qcpen
    assert test_gsistage2_rej_180_count
    assert test_gsistage2_rej_180_bias
    assert test_gsistage2_rej_180_rms
    assert test_gsistage2_rej_180_cpen
    assert test_gsistage2_rej_180_qcpen
    assert test_gsistage2_rej_all_count
    assert test_gsistage2_rej_all_bias
    assert test_gsistage2_rej_all_rms
    assert test_gsistage2_rej_all_cpen
    assert test_gsistage2_rej_all_qcpen
    assert test_gsistage2_mon_180_count
    assert test_gsistage2_mon_180_bias
    assert test_gsistage2_mon_180_rms
    assert test_gsistage2_mon_180_cpen
    assert test_gsistage2_mon_180_qcpen
    assert test_gsistage2_mon_all_count
    assert test_gsistage2_mon_all_bias
    assert test_gsistage2_mon_all_rms
    assert test_gsistage2_mon_all_cpen
    assert test_gsistage2_mon_all_qcpen

def test_fit_of_uv_wind_data():
    data_list = harvest(VALID_CONFIG_DICT)    
    
    test_plevs = False

    test_gsistage1_asm_220_count = False
    test_gsistage1_asm_220_bias = False
    test_gsistage1_asm_220_rms = False
    test_gsistage1_asm_220_cpen = False
    test_gsistage1_asm_220_qcpen = False

    test_gsistage1_asm_all_count = False
    test_gsistage1_asm_all_bias = False
    test_gsistage1_asm_all_rms = False
    test_gsistage1_asm_all_cpen = False
    test_gsistage1_asm_all_qcpen = False

    test_gsistage1_rej_280_count = False
    test_gsistage1_rej_280_bias = False
    test_gsistage1_rej_280_rms = False
    test_gsistage1_rej_280_cpen = False
    test_gsistage1_rej_280_qcpen = False

    test_gsistage1_rej_all_count = False
    test_gsistage1_rej_all_bias = False
    test_gsistage1_rej_all_rms = False
    test_gsistage1_rej_all_cpen = False
    test_gsistage1_rej_all_qcpen = False

    test_gsistage1_mon_230_count = False
    test_gsistage1_mon_230_bias = False
    test_gsistage1_mon_230_rms = False
    test_gsistage1_mon_230_cpen = False
    test_gsistage1_mon_230_qcpen = False

    test_gsistage1_mon_all_count = False
    test_gsistage1_mon_all_bias = False
    test_gsistage1_mon_all_rms = False
    test_gsistage1_mon_all_cpen = False
    test_gsistage1_mon_all_qcpen = False

    test_gsistage2_asm_252_count = False
    test_gsistage2_asm_252_bias = False
    test_gsistage2_asm_252_rms = False
    test_gsistage2_asm_252_cpen = False
    test_gsistage2_asm_252_qcpen = False

    test_gsistage2_asm_all_count = False
    test_gsistage2_asm_all_bias = False
    test_gsistage2_asm_all_rms = False
    test_gsistage2_asm_all_cpen = False
    test_gsistage2_asm_all_qcpen = False

    test_gsistage2_rej_280_count = False
    test_gsistage2_rej_280_bias = False
    test_gsistage2_rej_280_rms = False
    test_gsistage2_rej_280_cpen = False
    test_gsistage2_rej_280_qcpen = False

    test_gsistage2_rej_all_count = False
    test_gsistage2_rej_all_bias = False
    test_gsistage2_rej_all_rms = False
    test_gsistage2_rej_all_cpen = False
    test_gsistage2_rej_all_qcpen = False

    test_gsistage2_mon_280_count = False
    test_gsistage2_mon_280_bias = False
    test_gsistage2_mon_280_rms = False
    test_gsistage2_mon_280_cpen = False
    test_gsistage2_mon_280_qcpen = False

    test_gsistage2_mon_all_count = False
    test_gsistage2_mon_all_bias = False
    test_gsistage2_mon_all_rms = False
    test_gsistage2_mon_all_cpen = False
    test_gsistage2_mon_all_qcpen = False
    
    for i, data_i in enumerate(data_list):
        if data_i.variable == 'fit_uv_data':
            assert data_i.plevs_top == [0.100E+04,
                                         0.900E+03,
                                         0.800E+03,
                                         0.600E+03,
                                         0.400E+03,
                                         0.300E+03,
                                         0.250E+03,
                                         0.200E+03,
                                         0.150E+03,
                                         0.100E+03,
                                         0.500E+02,
                                         0.000E+00
                                    ]
            assert data_i.plevs_bot == [0.120E+04,
                                         0.100E+04,
                                         0.900E+03,
                                         0.800E+03,
                                         0.600E+03,
                                         0.400E+03,
                                         0.300E+03,
                                         0.250E+03,
                                         0.200E+03,
                                         0.150E+03,
                                         0.100E+03,
                                         0.200E+04]
            #assert data_i.plevs_units == ['hPa', 'hPa']
            test_plevs = True
            
            if data_i.iteration == 1:
                if data_i.usage == 'asm':
                    if data_i.type == '220':
                        if data_i.statistic == 'count':
                            assert data_i.values == [787,  
                                                     2255,
                                                     1960,
                                                     3803,
                                                     4061,
                                                     2156,    
                                                     747,    
                                                     921,
                                                     1660,
                                                     2066,
                                                     2120, 
                                                     26895]

                            test_gsistage1_asm_220_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.14,
                                                     0.20,
                                                     0.45,
                                                     0.28,
                                                     0.26,
                                                     -0.12,
                                                     0.37,
                                                     0.61,
                                                     0.77,
                                                     0.50,
                                                     0.33,
                                                     0.33]
                            test_gsistage1_asm_220_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [3.66,
                                                     3.91,
                                                     4.06,
                                                     4.46,
                                                     5.21,
                                                     6.39,
                                                     7.37,
                                                     7.20,
                                                     6.21,
                                                     5.20,
                                                     4.29,
                                                     5.16] 
                            test_gsistage1_asm_220_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [1.32,
                                                     1.87, 
                                                     2.53,
                                                     2.61,
                                                     2.06,
                                                     1.79,
                                                     1.93,
                                                     2.20,
                                                     2.33,
                                                     2.14,
                                                     1.83,
                                                     2.05]
                            test_gsistage1_asm_220_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [1.24,
                                                     1.76,
                                                     2.37,
                                                     2.46,
                                                     1.97,   
                                                     1.66,
                                                     1.85,
                                                     2.05,
                                                     2.16,
                                                     1.98,
                                                     1.79,
                                                     1.93]
                            test_gsistage1_asm_220_qcpen = True
                            print("after the 220 uv ")
                            sys.exit(0)
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [2058,
                                                     3563,
                                                     3109,
                                                     5333,
                                                     4246,
                                                     3370,
                                                     1290,
                                                     2650,
                                                     2033,
                                                     2830,
                                                     1832,
                                                     35669]
                            test_gsistage1_asm_all_count = True

                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.476E+00,
                                                     0.853E+00,
                                                     0.931E+00,
                                                     0.868E+00,
                                                     0.963E+00,
                                                     0.609E+00,
                                                     0.483E+00,
                                                     0.328E+00,
                                                     0.750E-01,
                                                     0.187E+00,
                                                     -0.170E+00,
                                                     0.570E+00]
                            test_gsistage1_asm_all_bias = True

                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.481E+01,
                                                     0.490E+01,
                                                     0.455E+01,
                                                     0.494E+01,
                                                     0.614E+01,
                                                     0.756E+01,
                                                     0.857E+01,
                                                     0.855E+01,
                                                     0.772E+01,
                                                     0.579E+01,
                                                     0.529E+01,
                                                     0.614E+01]
                            test_gsistage1_asm_all_rms = True

                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.111E+01,
                                                     0.138E+01,
                                                     0.181E+01,
                                                     0.187E+01,
                                                     0.201E+01,
                                                     0.182E+01,
                                                     0.181E+01,
                                                     0.168E+01,
                                                     0.184E+01,
                                                     0.176E+01,
                                                     0.183E+01,
                                                     0.172E+01]
                            test_gsistage1_asm_all_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.847E+00,
                                                     0.121E+01,
                                                     0.169E+01,
                                                     0.173E+01,
                                                     0.188E+01,
                                                     0.171E+01,
                                                     0.166E+01,
                                                     0.155E+01,
                                                     0.168E+01,
                                                     0.164E+01,
                                                     0.173E+01,
                                                     0.158E+01]
                            test_gsistage1_asm_all_qcpen = True
                elif data_i.usage == 'rej':
                    if data_i.type == '280':
                        if data_i.statistic == 'count':
                            assert data_i.values == [18,
                                                     7,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     25]
                            test_gsistage1_rej_280_count = True

                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.470E+01,
                                                     0.328E+01,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.430E+01]
                            test_gsistage1_rej_280_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.237E+02,
                                                     0.186E+02,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.224E+02]
                            test_gsistage1_rej_280_rms = True 
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00]
                            test_gsistage1_rej_280_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00]
                            test_gsistage1_rej_280_qcpen = True
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [27,
                                                     110,
                                                     42,
                                                     161,
                                                     152,
                                                     99,
                                                     37,
                                                     109,
                                                     70,
                                                     69,
                                                     48,
                                                     976]
                            test_gsistage1_rej_all_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.896E+01,
                                                     0.551E+02,
                                                     0.273E+02,
                                                     0.983E+01,
                                                     0.844E+01,
                                                     0.138E+02,
                                                     0.722E+01,
                                                     0.139E+01,
                                                     0.365E+01,
                                                     0.423E+00,
                                                     0.149E+02,
                                                     0.134E+02]
                            test_gsistage1_rej_all_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.364E+02,
                                                     0.970E+02,
                                                     0.661E+02,
                                                     0.335E+02,
                                                     0.280E+02,
                                                     0.491E+02,
                                                     0.328E+02,
                                                     0.473E+02,
                                                     0.403E+02,
                                                     0.282E+02,
                                                     0.297E+02,
                                                     0.490E+02]
                            test_gsistage1_rej_all_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00]
                            test_gsistage1_rej_all_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00]
                            test_gsistage1_rej_all_qcpen = True
                elif data_i.usage == 'mon':
                    if data_i.type == '230' and data_i.subtype=='0000':
                        if data_i.statistic == 'count':
                            assert data_i.values == [0,
                                                     2,
                                                     0,
                                                     3,
                                                     21,
                                                     28,
                                                     108,
                                                     115,
                                                     43,
                                                     0,
                                                     0,
                                                     320]
                            test_gsistage1_mon_230_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.000E+00,
                                                     0.315E+01,
                                                     0.000E+00,
                                                     0.848E+00,
                                                     0.253E+01,
                                                     0.166E+01,
                                                     -0.334E+00,
                                                     -0.626E+00,
                                                     -0.152E+01,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     -0.204E+00]
                            test_gsistage1_mon_230_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.000E+00,
                                                     0.366E+01,
                                                     0.000E+00,
                                                     0.273E+01,
                                                     0.706E+01,
                                                     0.715E+01,
                                                     0.903E+01,
                                                     0.102E+02,
                                                     0.996E+01,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.927E+01]
                            test_gsistage1_mon_230_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00,
                                                     0.472E-01,
                                                     0.000E+00,
                                                     0.184E-12,
                                                     0.123E+01,
                                                     0.902E+00,
                                                     0.152E+01,
                                                     0.220E+01,
                                                     0.218E+01,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.175E+01]
                            test_gsistage1_mon_230_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00,
                                                     0.472E-01,
                                                     0.000E+00,
                                                     0.184E-12,
                                                     0.115E+01,
                                                     0.826E+00,
                                                     0.141E+01,
                                                     0.187E+01,
                                                     0.193E+01,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.156E+01]
                            test_gsistage1_mon_230_qcpen = True

                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [116,
                                                     131,
                                                     28,
                                                     22,
                                                     31,
                                                     36,
                                                     141,
                                                     135,
                                                     45,
                                                     2,
                                                     0,
                                                     687]
                            test_gsistage1_mon_all_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.157E+01,
                                                     0.130E+01,
                                                     0.188E+01,
                                                     0.118E+01,
                                                     0.252E+01,
                                                     0.875E+00,
                                                     -0.629E-01,
                                                     -0.372E+00,
                                                     -0.158E+01,
                                                     -0.139E-01,
                                                     0.000E+00,
                                                     0.597E+00]
                            test_gsistage1_mon_all_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.554E+01,
                                                     0.517E+01,
                                                     0.526E+01,
                                                     0.558E+01,
                                                     0.730E+01,
                                                     0.721E+01,
                                                     0.850E+01,
                                                     0.963E+01,
                                                     0.976E+01,
                                                     0.140E+01,
                                                     0.000E+00,
                                                     0.754E+01]
                            test_gsistage1_mon_all_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.475E+00,
                                                     0.198E+00,
                                                     0.390E-11,
                                                     0.847E+00,
                                                     0.150E+01,
                                                     0.113E+01,
                                                     0.151E+01,
                                                     0.203E+01,
                                                     0.211E+01,
                                                     0.701E-01,
                                                     0.000E+00,
                                                     0.112E+01]
                            test_gsistage1_mon_all_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.392E+00,
                                                     0.121E+00,
                                                     0.348E-11,
                                                     0.808E+00,
                                                     0.140E+01,
                                                     0.105E+01,
                                                     0.140E+01,
                                                     0.175E+01,
                                                     0.187E+01,
                                                     0.701E-01,
                                                     0.000E+00,
                                                     0.986E+00]
                            test_gsistage1_mon_all_qcpen = True
            elif data_i.iteration == 2:
                if data_i.usage == 'asm':
                    if data_i.type == '252':
                        if data_i.statistic == 'count':
                            assert data_i.values == [0,
                                                     4,
                                                     34,
                                                     0,
                                                     5,
                                                     4,
                                                     15,
                                                     29,
                                                     25,
                                                     9,
                                                     0,
                                                     125]
                            test_gsistage2_asm_252_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.000E+00,
                                                     -0.937E+00,
                                                     0.915E+00,
                                                     0.000E+00,
                                                     -0.199E+01,
                                                     -0.573E+01,
                                                     -0.395E+01,
                                                     -0.392E+01,
                                                     -0.168E+02,
                                                     -0.854E+01,
                                                     0.000E+00,
                                                     -0.541E+01]
                            test_gsistage2_asm_252_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.000E+00,
                                                     0.158E+01,
                                                     0.436E+01,
                                                     0.000E+00,
                                                     0.109E+02,
                                                     0.137E+02,
                                                     0.112E+02,
                                                     0.892E+01,
                                                     0.199E+02,
                                                     0.129E+02,
                                                     0.000E+00,
                                                     0.119E+02]
                            test_gsistage2_asm_252_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00,
                                                     0.541E-02,
                                                     0.412E-01,
                                                     0.000E+00,
                                                     0.190E+00,
                                                     0.141E+00,
                                                     0.859E-01,
                                                     0.507E-01,
                                                     0.253E+00,
                                                     0.106E+00,
                                                     0.000E+00,
                                                     0.104E+00]
                            test_gsistage2_asm_252_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00,
                                                     0.541E-02,
                                                     0.412E-01,
                                                     0.000E+00,
                                                     0.190E+00,
                                                     0.141E+00,
                                                     0.859E-01,
                                                     0.507E-01,
                                                     0.253E+00,
                                                     0.106E+00,
                                                     0.000E+00,
                                                     0.104E+00]
                            test_gsistage2_asm_252_qcpen = True
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [2062,
                                                     3575,
                                                     3128,
                                                     5352,
                                                     4273,
                                                     3383,
                                                     1300,
                                                     2675,
                                                     2052,
                                                     2843,
                                                     1836,
                                                     35839]
                            test_gsistage2_asm_all_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.550E+00,
                                                     0.676E+00,
                                                     0.676E+00,
                                                     0.556E+00,
                                                     0.690E+00,
                                                     0.516E+00,
                                                     0.441E+00,
                                                     0.289E+00,
                                                     0.267E+00,
                                                     0.238E+00,
                                                     0.148E+00,
                                                     0.481E+00]
                            test_gsistage2_asm_all_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.420E+01,
                                                     0.369E+01,
                                                     0.265E+01,
                                                     0.263E+01,
                                                     0.357E+01,
                                                     0.495E+01,
                                                     0.606E+01,
                                                     0.642E+01,
                                                     0.567E+01,
                                                     0.382E+01,
                                                     0.401E+01,
                                                     0.430E+01]
                            test_gsistage2_asm_all_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.785E+00,
                                                     0.577E+00,
                                                     0.604E+00,
                                                     0.543E+00,
                                                     0.683E+00,
                                                     0.750E+00,
                                                     0.847E+00,
                                                     0.744E+00,
                                                     0.836E+00,
                                                     0.771E+00,
                                                     0.105E+01,
                                                     0.746E+00]
                            test_gsistage2_asm_all_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.592E+00,
                                                     0.513E+00,
                                                     0.575E+00,
                                                     0.520E+00,
                                                     0.651E+00,
                                                     0.718E+00,
                                                     0.790E+00,
                                                     0.709E+00,
                                                     0.785E+00,
                                                     0.745E+00,
                                                     0.102E+01,
                                                     0.694E+00]
                            test_gsistage2_asm_all_qcpen = True
                elif data_i.usage == 'rej':
                    if data_i.type == '280' and data_i.subtype == '0001':
                        if data_i.statistic == 'count':
                            assert data_i.values == [17,
                                                     5,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     22]
                            test_gsistage2_rej_280_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.501E+01,
                                                     0.680E+01,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.542E+01]
                            test_gsistage2_rej_280_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.240E+02,
                                                     0.186E+02,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.229E+02]
                            test_gsistage2_rej_280_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00]
                            test_gsistage2_rej_280_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00]
                            test_gsistage2_rej_280_qcpen = True
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [25,
                                                     95,
                                                     24,
                                                     142,
                                                     124,
                                                     87,
                                                     27,
                                                     79,
                                                     51,
                                                     56,
                                                     44,
                                                     801]
                            test_gsistage2_rej_all_count = True

                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.989E+01,
                                                     0.627E+02,
                                                     0.416E+02,
                                                     0.998E+01,
                                                     0.858E+01,
                                                     0.149E+02,
                                                     0.106E+02,
                                                     0.226E+01,
                                                     0.136E+01,
                                                     0.103E+01,
                                                     0.159E+02,
                                                     0.153E+02]
                            test_gsistage2_rej_all_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.377E+02,
                                                     0.104E+03,
                                                     0.864E+02,
                                                     0.344E+02,
                                                     0.289E+02,
                                                     0.509E+02,
                                                     0.341E+02,
                                                     0.528E+02,
                                                     0.432E+02,
                                                     0.291E+02,
                                                     0.303E+02,
                                                     0.528E+02]
                            test_gsistage2_rej_all_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00]
                            test_gsistage2_rej_all_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00]
                            test_gsistage2_rej_all_qcpen = True
                elif data_i.usage == 'mon':
                    if data_i.type == '280' and data_i.subtype == '0000':
                        if data_i.statistic == 'count':
                            assert data_i.values == [2,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     0,
                                                     2]
                            test_gsistage2_mon_280_count = True

                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.956E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.956E+00]
                            test_gsistage2_mon_280_bias = True
                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.168E+01,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.168E+01]
                            test_gsistage2_mon_280_rms = True
                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.134E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.134E+00]
                            test_gsistage2_mon_280_cpen = True
                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.134E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.000E+00,
                                                     0.134E+00]
                            test_gsistage2_mon_280_qcpen = True
                    elif data_i.type == 'all':
                        if data_i.statistic == 'count':
                            assert data_i.values == [118,
                                                     129,
                                                     28,
                                                     22,
                                                     31,
                                                     36,
                                                     141,
                                                     140,
                                                     45,
                                                     2,
                                                     0,
                                                     692]
                            test_gsistage2_mon_all_count = True
                        elif data_i.statistic == 'bias':
                            assert data_i.values == [0.141E+01,
                                                     0.126E+01,
                                                     0.104E+01,
                                                     0.110E+01,
                                                     0.179E+01,
                                                     0.106E+01,
                                                     -0.668E-01,
                                                     -0.233E+00,
                                                     -0.527E+00,
                                                     0.172E+01,
                                                     0.000E+00,
                                                     0.597E+00]
                            test_gsistage2_mon_all_bias = True

                        elif data_i.statistic == 'rms':
                            assert data_i.values == [0.493E+01,
                                                     0.468E+01,
                                                     0.361E+01,
                                                     0.546E+01,
                                                     0.703E+01,
                                                     0.584E+01,
                                                     0.781E+01,
                                                     0.893E+01,
                                                     0.873E+01,
                                                     0.195E+01,
                                                     0.000E+00,
                                                     0.687E+01]
                            test_gsistage2_mon_all_rms = True

                        elif data_i.statistic == 'cpen':
                            assert data_i.values == [0.470E+00,
                                                     0.198E+00,
                                                     0.183E-11,
                                                     0.762E+00,
                                                     0.137E+01,
                                                     0.767E+00,
                                                     0.127E+01,
                                                     0.176E+01,
                                                     0.174E+01,
                                                     0.136E+00,
                                                     0.000E+00,
                                                     0.972E+00]
                            test_gsistage2_mon_all_cpen = True

                        elif data_i.statistic == 'qcpen':
                            assert data_i.values == [0.391E+00,
                                                     0.116E+00,
                                                     0.168E-11,
                                                     0.746E+00,
                                                     0.124E+01,
                                                     0.723E+00,
                                                     0.117E+01,
                                                     0.154E+01,
                                                     0.160E+01,
                                                     0.136E+00,
                                                     0.000E+00,
                                                     0.860E+00]
                            test_gsistage2_mon_all_qcpen = True

                                                     
    assert test_plevs
    assert test_gsistage1_asm_220_count
    assert test_gsistage1_asm_220_bias
    assert test_gsistage1_asm_220_rms
    assert test_gsistage1_asm_220_cpen
    assert test_gsistage1_asm_220_qcpen
    assert test_gsistage1_asm_all_count
    assert test_gsistage1_asm_all_bias
    assert test_gsistage1_asm_all_rms
    assert test_gsistage1_asm_all_cpen
    assert test_gsistage1_asm_all_qcpen
    assert test_gsistage1_rej_280_count
    assert test_gsistage1_rej_280_bias
    assert test_gsistage1_rej_280_rms
    assert test_gsistage1_rej_280_cpen
    assert test_gsistage1_rej_280_qcpen
    assert test_gsistage1_rej_all_count
    assert test_gsistage1_rej_all_bias
    assert test_gsistage1_rej_all_rms
    assert test_gsistage1_rej_all_cpen
    assert test_gsistage1_rej_all_qcpen
    assert test_gsistage1_mon_230_count
    assert test_gsistage1_mon_230_bias
    assert test_gsistage1_mon_230_rms
    assert test_gsistage1_mon_230_cpen
    assert test_gsistage1_mon_230_qcpen
    assert test_gsistage1_mon_all_count
    assert test_gsistage1_mon_all_bias
    assert test_gsistage1_mon_all_rms
    assert test_gsistage1_mon_all_cpen
    assert test_gsistage1_mon_all_qcpen
    assert test_gsistage2_asm_252_count
    assert test_gsistage2_asm_252_bias
    assert test_gsistage2_asm_252_rms
    assert test_gsistage2_asm_252_cpen
    assert test_gsistage2_asm_252_qcpen
    assert test_gsistage2_asm_all_count
    assert test_gsistage2_asm_all_bias
    assert test_gsistage2_asm_all_rms
    assert test_gsistage2_asm_all_cpen
    assert test_gsistage2_asm_all_qcpen
    assert test_gsistage2_rej_280_count
    assert test_gsistage2_rej_280_bias
    assert test_gsistage2_rej_280_rms
    assert test_gsistage2_rej_280_cpen
    assert test_gsistage2_rej_280_qcpen
    assert test_gsistage2_rej_all_count
    assert test_gsistage2_rej_all_bias
    assert test_gsistage2_rej_all_rms
    assert test_gsistage2_rej_all_cpen
    assert test_gsistage2_rej_all_qcpen
    assert test_gsistage2_mon_280_count
    assert test_gsistage2_mon_280_bias
    assert test_gsistage2_mon_280_rms
    assert test_gsistage2_mon_280_cpen
    assert test_gsistage2_mon_280_qcpen
    assert test_gsistage2_mon_all_count
    assert test_gsistage2_mon_all_bias
    assert test_gsistage2_mon_all_rms
    assert test_gsistage2_mon_all_cpen
    assert test_gsistage2_mon_all_qcpen

def run_all():
    test_datetime()
    test_longnames()
    test_bad_config()
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
