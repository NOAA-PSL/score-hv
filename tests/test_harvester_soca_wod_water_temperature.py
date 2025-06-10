#!/usr/bin/env python

import os
from pathlib import Path
from datetime import datetime

from score_hv import hv_registry
from score_hv.harvester_base import harvest

TEST_DATA_FILE_NAMES = [
                        'wod_t_ctd.1979010200.nc4'
                       ]

PYTEST_CALLING_DIR = Path(__file__).parent.resolve()
TEST_DATA_PATH = os.path.join(PYTEST_CALLING_DIR, 'data_dev')
SOCA_PATH = [os.path.join(TEST_DATA_PATH,
                         file_name) for file_name in TEST_DATA_FILE_NAMES]

VALID_CONFIG_DICT = {'harvester_name': hv_registry.SOCA_DIAGS,
                     'filenames' : SOCA_PATH,
                     'statistics': ['rms', 'mean'],
                     'variables': ['waterTemperature'],
                     }

def test_waterTemperature(tolerance=0.001):
    data1 = harvest(VALID_CONFIG_DICT)
    dt = datetime.strptime('1979010200', "%Y%m%d%H")
    
    ombg_exists = False
    obs_error_exists = False
    for item in data1:
        assert item.filenames.split('/')[-1] == 'wod_t_ctd.1979010200.nc4'
        assert item.sensor == 'ctd'
        assert item.satellite == None
        assert item.level == None
        assert item.variables == 'waterTemperature'
        assert item.statistics == 'rms' or item.statistics == 'mean'
        assert item.filetime == dt
        assert item.file_region == 'global'
        
        if item.group == 'ombg' and item.statistics == 'rms':
            ombg_exists = True
            offline_rms = 1.642326233143017
            assert item.value <= (1+tolerance) * offline_rms
            assert item.value >= (1-tolerance) * offline_rms
            
        if item.group == 'ObsError' and item.statistics == 'mean':
            obs_error_exists = True
            offline_mean = 0.5
            assert item.value <= (1+tolerance) * offline_mean
            assert item.value >= (1-tolerance) * offline_mean
            
    assert ombg_exists
    assert obs_error_exists

def main():
    test_waterTemperature()

if __name__=='__main__':
    main()
