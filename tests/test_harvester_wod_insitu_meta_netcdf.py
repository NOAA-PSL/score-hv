#!/usr/bin/env python

import os
from pathlib import Path
import numpy

from score_hv import hv_registry
from score_hv.harvester_base import harvest

WOD_APB_DATA = 'wod_apb_2005-02-01T06.nc'
WOD_CTD_DATA = 'wod_ctd_2014-06-02T06.nc'
WOD_DRB_DATA = 'wod_drb_2014-10-02T18.nc'
WOD_GLD_DATA = 'wod_gld_2013-06-02T06.nc'
WOD_MRB_DATA = 'wod_mrb_1983-06-03T12.nc'
WOD_OSD_DATA = 'wod_osd_1998-05-02T00.nc'
WOD_PFL_DATA = 'wod_pfl_2019-10-01T18.nc'
WOD_UOR_DATA = 'wod_uor_2002-10-06T18.nc'
WOD_XBT_DATA = 'wod_xbt_2009-08-02T18.nc'

PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
DATA_DIR = 'data'

file_path_wod_apb_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, WOD_APB_DATA)
file_path_wod_ctd_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, WOD_CTD_DATA)
file_path_wod_drb_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, WOD_DRB_DATA)
file_path_wod_gld_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, WOD_GLD_DATA)
file_path_wod_mrb_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, WOD_MRB_DATA)
file_path_wod_osd_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, WOD_OSD_DATA)
file_path_wod_pfl_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, WOD_PFL_DATA)
file_path_wod_uor_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, WOD_UOR_DATA)
file_path_wod_xbt_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, WOD_XBT_DATA)

VALID_CONFIG_WOD_APB = {
    'harvester_name': hv_registry.WOD_INSITU_META_NETCDF,
    'filename': file_path_wod_apb_data
}

VALID_CONFIG_WOD_CTD = {
    'harvester_name': hv_registry.WOD_INSITU_META_NETCDF,
    'filename': file_path_wod_ctd_data
}

VALID_CONFIG_WOD_DRB = {
    'harvester_name': hv_registry.WOD_INSITU_META_NETCDF,
    'filename': file_path_wod_drb_data
}

VALID_CONFIG_WOD_GLD = {
    'harvester_name': hv_registry.WOD_INSITU_META_NETCDF,
    'filename': file_path_wod_gld_data
}

VALID_CONFIG_WOD_MRB = {
    'harvester_name': hv_registry.WOD_INSITU_META_NETCDF,
    'filename': file_path_wod_mrb_data
}

VALID_CONFIG_WOD_OSD = {
    'harvester_name': hv_registry.WOD_INSITU_META_NETCDF,
    'filename': file_path_wod_osd_data
}

VALID_CONFIG_WOD_PFL = {
    'harvester_name': hv_registry.WOD_INSITU_META_NETCDF,
    'filename': file_path_wod_pfl_data
}

VALID_CONFIG_WOD_UOR = {
    'harvester_name': hv_registry.WOD_INSITU_META_NETCDF,
    'filename': file_path_wod_uor_data
}

VALID_CONFIG_WOD_XBT = {
    'harvester_name': hv_registry.WOD_INSITU_META_NETCDF,
    'filename': file_path_wod_xbt_data
}

def test_wod_apb_meta():
    data = harvest(VALID_CONFIG_WOD_APB)
    temperature_data = data[1]
    assert temperature_data.filename == WOD_APB_DATA
    assert temperature_data.obs_day == '2005-02-01 06:00:00'
    assert temperature_data.min_date_time == '2005-02-01 06:00:00'
    assert temperature_data.max_date_time == '2005-02-01 11:31:52'
    assert temperature_data.min_depth == 0.0
    assert temperature_data.max_depth == 584.0
    assert temperature_data.num_vars == 4
    assert temperature_data.variable_name == "Temperature"
    assert temperature_data.var_count == 676
    assert temperature_data.sensor == "apb"
    assert temperature_data.casts == 55

def test_wod_ctd_meta():
    data = harvest(VALID_CONFIG_WOD_CTD)
    nitrate_obs = data[5]
    salinity_obs = data[2]
    assert nitrate_obs.filename == WOD_CTD_DATA
    assert nitrate_obs.obs_day == '2014-06-02 06:00:00'
    assert salinity_obs.obs_day == '2014-06-02 06:00:00'
    assert salinity_obs.min_date_time == '2014-06-02 06:07:00'
    assert salinity_obs.max_date_time == '2014-06-02 11:57:59'
    assert salinity_obs.min_depth == 0.0
    assert numpy.isclose(salinity_obs.max_depth, 5636.777832)
    assert salinity_obs.num_vars == 8
    assert salinity_obs.variable_name == "Salinity"
    assert nitrate_obs.variable_name == "Nitrate"
    assert salinity_obs.var_count == 28376
    assert salinity_obs.sensor == "ctd"
    assert salinity_obs.casts == 79

def test_wod_drb_meta():
    data = harvest(VALID_CONFIG_WOD_DRB)
    pressure_obs = data[3]
    assert pressure_obs.filename == WOD_DRB_DATA
    assert pressure_obs.obs_day == '2014-10-02 18:00:00'
    assert pressure_obs.min_date_time == '2014-10-02 18:00:02'
    assert pressure_obs.max_date_time == '2014-10-02 21:02:27'
    assert numpy.isclose(pressure_obs.min_depth, 6.232697)
    assert numpy.isclose(pressure_obs.max_depth, 751.304993)
    assert pressure_obs.num_vars == 6
    assert pressure_obs.variable_name == "Pressure"
    assert pressure_obs.var_count == 1274
    assert pressure_obs.sensor == "drb"
    assert pressure_obs.casts == 7

def test_wod_gld_meta():
    data = harvest(VALID_CONFIG_WOD_GLD)
    chlorophyll_obs = data[3]
    assert chlorophyll_obs.filename == WOD_GLD_DATA
    assert chlorophyll_obs.obs_day == '2013-06-02 06:00:00'
    assert chlorophyll_obs.min_date_time == '2013-06-02 06:02:48'
    assert chlorophyll_obs.max_date_time == '2013-06-02 11:54:22'
    assert chlorophyll_obs.min_depth == 0.0
    assert numpy.isclose(chlorophyll_obs.max_depth, 995.717590)
    assert chlorophyll_obs.num_vars == 9
    assert chlorophyll_obs.variable_name == "Chlorophyll"
    assert chlorophyll_obs.var_count == 14677
    assert chlorophyll_obs.sensor == "gld"
    assert chlorophyll_obs.casts == 74



