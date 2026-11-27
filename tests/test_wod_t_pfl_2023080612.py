#!/usr/bin/env python
"""Verify soca_diags depth-binned statistics for the World Ocean Database
profiling float file wod_t_pfl.2023080612.nc.

The expected values were computed independently of score-hv (xarray/pandas)
with QC_threshold 0 (EffectiveQC1 for oman, EffectiveQC0 for the other
groups), half-open depth bins lo <= depth < hi, the sample standard deviation
(ddof=1), and mediantime as the median MetaData/dateTime of the observations
used, floored to the second. filetime is the 2023080612 cycle in the file name.
"""
import os
from datetime import datetime
from pathlib import Path

import pytest

from score_hv import hv_registry
from score_hv.harvester_base import harvest

TEST_DATA_PATH = os.path.join(Path(__file__).parent.resolve(), 'data')
SOCA_PATH = [os.path.join(TEST_DATA_PATH, 'wod_t_pfl.2023080612.nc')]

VALID_CONFIG_DICT = {'harvester_name': hv_registry.SOCA_DIAGS,
                     'filenames': SOCA_PATH,
                     'statistics': ['mean', 'median', 'StdDev', 'minimum', 'maximum', 'rms',
                                    'count'],
                     'variables': ['waterTemperature'],
                     'ocean_depth_bins': [0, 10, 50, 100, 500, 1000]}

STATISTICS = ('count', 'mean', 'median', 'StdDev', 'minimum', 'maximum', 'rms')
# depth bin: (mediantime, {group: values of STATISTICS})
EXPECTED = {
    (0, 10): (datetime(2023, 8, 6, 11, 48, 46), {
        'ObsValue': (1086, 19.61598, 22.1555, 8.529668, -1.767, 30.296, 21.38867),
        'oman': (1086, 0.02690667, 0.01507827, 0.2456789, -1.600366, 0.9726624, 0.2470355),
        'ombg': (1086, -0.0227276, 0.0195634, 0.5154725, -1.827266, 1.565654, 0.5157361),
        'ObsError': (1086, 0.5, 0.5, 0, 0.5, 0.5, 0.5),
    }),
    (10, 50): (datetime(2023, 8, 6, 11, 0, 57), {
        'ObsValue': (2883, 18.24359, 18.774, 9.038686, -1.851, 30.192, 20.35923),
        'oman': (2883, 0.0240833, 0.009913783, 0.2510165, -1.440295, 1.688091, 0.2521258),
        'ombg': (2883, 0.05565696, 0.08337782, 0.6426867, -1.997398, 1.997224, 0.6449811),
        'ObsError': (2883, 0.5, 0.5, 0, 0.5, 0.5, 0.5),
    }),
    (50, 100): (datetime(2023, 8, 6, 11, 34, 41), {
        'ObsValue': (3447, 15.81142, 15.192, 8.393386, -1.849, 29.909, 17.90054),
        'oman': (3447, -0.01437733, 0.001194983, 0.2955491, -1.728829, 1.577021, 0.2958557),
        'ombg': (3447, 0.01639983, 0.0438651, 0.6600188, -1.972986, 1.975288, 0.6601268),
        'ObsError': (3447, 0.5, 0.5, 0, 0.5, 0.5, 0.5),
    }),
    (100, 500): (datetime(2023, 8, 6, 11, 23, 27), {
        'ObsValue': (24543, 10.79046, 10.585, 5.38264, -1.918, 29.217, 12.05843),
        'oman': (24543, -0.007459531, 0.002279506, 0.3239951, -1.948685, 1.893383, 0.3240743),
        'ombg': (24543, -0.0429516, 0.007404115, 0.5972409, -1.99977, 1.998933, 0.5987712),
        'ObsError': (24543, 0.5, 0.5, 0, 0.5, 0.5, 0.5),
    }),
    (500, 1000): (datetime(2023, 8, 6, 11, 17, 48), {
        'ObsValue': (22395, 6.026007, 5.731, 2.554485, 0.22, 15.765, 6.545064),
        'oman': (22395, -0.2232245, -0.1648834, 0.4202607, -2.008858, 1.743043, 0.4758575),
        'ombg': (22395, -0.2275291, -0.1706144, 0.4394141, -1.999478, 1.996362, 0.4948187),
        'ObsError': (22395, 0.5, 0.5, 0, 0.5, 0.5, 0.5),
    }),
}


@pytest.fixture(scope='module')
def data1():
    if not os.path.exists(SOCA_PATH[0]):
        pytest.fail(f'Test data missing: {SOCA_PATH[0]}')
    return harvest(VALID_CONFIG_DICT)


def test_soca_harvester(data1):
    assert type(data1) is list
    assert len(data1) == len(EXPECTED) * 4 * len(STATISTICS)
    assert all(data.filenames == SOCA_PATH[0] for data in data1)


def test_verify_filename_components(data1):
    for data in data1:
        assert data.variables == 'waterTemperature'
        assert data.sensor == 'pfl'
        assert data.satellite is None
        assert data.level is None
        assert data.file_region == 'global'
        assert data.longname == 'waterTemperature'
        assert data.units == 'DegC'
        assert data.QC_threshold == 0


def test_verify_datetime(data1):
    for data in data1:
        assert data.filetime == datetime(2023, 8, 6, 12)
        assert data.mediantime == EXPECTED[data.ocean_depth_bins][0], \
            f'mediantime mismatch for {data.group} in depth bin {data.ocean_depth_bins}'


def test_verify_statistics(data1):
    harvested = {(data.ocean_depth_bins, data.group, data.statistics): data.value
                 for data in data1}
    expected = {(depth_bin, group, statistic): value
                for depth_bin, (_, groups) in EXPECTED.items()
                for group, values in groups.items()
                for statistic, value in zip(STATISTICS, values)}
    assert harvested.keys() == expected.keys()
    for key, value in expected.items():
        assert harvested[key] == pytest.approx(value, rel=1e-5, abs=1e-6), \
            f'{key}: harvested {harvested[key]}, expected {value}'
