#!/usr/bin/env python

import os
from pathlib import Path
import numpy

from score_hv import hv_registry
from score_hv.harvester_base import harvest

PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
DATA_DIR = 'data'

OZONE_MLS_DATA = 'MLS-v5.0-oz.20040803_00z.nc'

file_path_ozone_mls_data = os.path.join(PYTEST_CALLING_DIR, DATA_DIR, OZONE_MLS_DATA)

VALID_CONFIG_OZONE_MLS = {
    'harvester_name': hv_registry.OZONE_META_NETCDF,
    'filename': file_path_ozone_mls_data
}

def test_ozone_mls_meta():
    data = harvest(VALID_CONFIG_OZONE_MLS)
    ozone_data = data[0]
    assert ozone_data.filename == OZONE_MLS_DATA
    assert ozone_data.obs_day == '2004-08-03 00:00:00'
    assert ozone_data.min_date_time == '2004-08-02 22:36:58'
    assert ozone_data.max_date_time == '2004-08-03 02:59:38'
    assert numpy.isclose(ozone_data.min_pressure, 0.001)
    assert numpy.isclose(ozone_data.max_pressure, 261.01572)
    assert ozone_data.ozone_count == 34705
    assert ozone_data.sensor == 'MLS-v5.0-oz'
