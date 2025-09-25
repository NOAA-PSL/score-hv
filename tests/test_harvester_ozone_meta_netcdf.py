#!/usr/bin/env python

import os
from pathlib import Path
import numpy

from score_hv import hv_registry
from score_hv.harvester_base import harvest

PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
DATA_DIR = 'data'

OZONE_MLS_DATA = 'MLS-v5.0-oz.20040803_00z.nc'
OZONE_OMI_EFF_DATA = 'OMIeff-adj.20130512_06z.nc'
OZONE_OMPSLP_DATA = 'OMPS-LPoz-Vis.20181003_18z.nc'
OZONE_OMPSNM_DATA = 'OMPSNM.20121203_00z.nc'
OZONE_OMPSNP_DATA = 'OMPSNP.20211002_18z.nc'
OZONE_OMPSNP_ZERO_DATA = 'OMPSNP.20130106_06z.nc'

file_path_ozone_mls_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, OZONE_MLS_DATA)
file_path_ozone_omi_eff_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, OZONE_OMI_EFF_DATA)
file_path_ozone_omsplp_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, OZONE_OMPSLP_DATA)
file_path_ozone_ompsnm_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, OZONE_OMPSNM_DATA)
file_path_ozone_ompsnp_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, OZONE_OMPSNP_DATA)
file_path_ozone_ompsnp_zero_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, OZONE_OMPSNP_ZERO_DATA)

VALID_CONFIG_OZONE_MLS = {
    'harvester_name': hv_registry.OZONE_META_NETCDF,
    'filename': file_path_ozone_mls_data
}

VALID_CONFIG_OZONE_OMI_EFF = {
    'harvester_name': hv_registry.OZONE_META_NETCDF,
    'filename': file_path_ozone_omi_eff_data
}

VALID_CONFIG_OZONE_OMPSLP = {
    'harvester_name': hv_registry.OZONE_META_NETCDF,
    'filename': file_path_ozone_omsplp_data
}

VALID_CONFIG_OZONE_OMPSNM = {
    'harvester_name': hv_registry.OZONE_META_NETCDF,
    'filename': file_path_ozone_ompsnm_data
}

VALID_CONFIG_OZONE_OMPSNP = {
    'harvester_name': hv_registry.OZONE_META_NETCDF,
    'filename': file_path_ozone_ompsnp_data
}

VALID_CONFIG_OZONE_OMPSNP_ZERO = {
    'harvester_name': hv_registry.OZONE_META_NETCDF,
    'filename': file_path_ozone_ompsnp_zero_data
}

def test_ozone_mls_meta():
    data = harvest(VALID_CONFIG_OZONE_MLS)
    ozone_data = data[0]
    assert ozone_data.filename == OZONE_MLS_DATA
    assert ozone_data.obs_day == '2004-08-03 00:00:00'
    assert ozone_data.min_date_time == '2004-08-02 22:36:58'
    assert ozone_data.max_date_time == '2004-08-03 02:59:38'
    assert ozone_data.levels == 55
    assert ozone_data.profiles == 631
    assert numpy.isclose(ozone_data.min_pressure, 0.001)
    assert numpy.isclose(ozone_data.max_pressure, 261.01572)
    assert ozone_data.ozone_count == 34705
    assert ozone_data.sensor == 'MLS-v5.0-oz'

def test_ozone_omi_eff_meta():
    data = harvest(VALID_CONFIG_OZONE_OMI_EFF)
    ozone_data = data[0]
    assert ozone_data.filename == OZONE_OMI_EFF_DATA
    assert ozone_data.obs_day == '2013-05-12 06:00:00'
    assert ozone_data.min_date_time == '2013-05-12 03:40:11'
    assert ozone_data.max_date_time == '2013-05-12 08:59:58'
    assert ozone_data.levels == 11
    assert ozone_data.profiles == 286368
    assert ozone_data.min_pressure == None
    assert ozone_data.max_pressure == None
    assert ozone_data.ozone_count == 286368
    assert ozone_data.sensor == 'OMIeff-adj'

def test_ozone_ompslp_meta():
    data = harvest(VALID_CONFIG_OZONE_OMPSLP)
    ozone_data = data[0]
    assert ozone_data.filename == OZONE_OMPSLP_DATA
    assert ozone_data.obs_day == '2018-10-03 18:00:00'
    assert ozone_data.min_date_time == '2018-10-03 15:34:02'
    assert ozone_data.max_date_time == '2018-10-03 20:59:43'
    assert ozone_data.levels == 56
    assert ozone_data.profiles == 414
    assert numpy.isclose(ozone_data.min_pressure, 2.568823)
    assert numpy.isclose(ozone_data.max_pressure, 200.8631)
    assert ozone_data.ozone_count == 23184
    assert ozone_data.sensor == 'OMPS-LPoz-Vis'

def test_ozone_ompsnm_meta():
    data = harvest(VALID_CONFIG_OZONE_OMPSNM)
    ozone_data = data[0]
    assert ozone_data.filename == OZONE_OMPSNM_DATA
    assert ozone_data.obs_day == '2012-12-03 00:00:00'
    assert ozone_data.min_date_time == '2012-12-02 23:05:23'
    assert ozone_data.max_date_time == '2012-12-03 02:59:57'
    assert ozone_data.levels == 11
    assert ozone_data.profiles == 34024
    assert ozone_data.min_pressure == None
    assert ozone_data.max_pressure == None
    assert ozone_data.ozone_count == 34024
    assert ozone_data.sensor == 'OMPSNM'

def test_ozone_ompsnp_meta():
    data = harvest(VALID_CONFIG_OZONE_OMPSNP)
    ozone_data = data[0]
    assert ozone_data.filename == OZONE_OMPSNP_DATA
    assert ozone_data.obs_day == '2021-10-02 18:00:00'
    assert ozone_data.min_date_time == '2021-10-02 15:00:06'
    assert ozone_data.max_date_time == '2021-10-02 20:47:38'
    assert ozone_data.levels == 21
    assert ozone_data.profiles == 250
    assert ozone_data.min_pressure == None
    assert ozone_data.max_pressure == None
    assert ozone_data.ozone_count == 5250
    assert ozone_data.sensor == 'OMPSNP'

def test_ozone_ompsnp_zero_meta():
    data = harvest(VALID_CONFIG_OZONE_OMPSNP_ZERO)
    ozone_data = data[0]
    assert ozone_data.filename == OZONE_OMPSNP_ZERO_DATA
    assert ozone_data.obs_day == '2013-01-06 06:00:00'
    assert ozone_data.min_date_time == None
    assert ozone_data.max_date_time == None
    assert ozone_data.levels == 0
    assert ozone_data.profiles == 0
    assert ozone_data.min_pressure == None
    assert ozone_data.max_pressure == None
    assert ozone_data.ozone_count == 0
    assert ozone_data.sensor == 'OMPSNP'