#!/usr/bin/env python
"""soca_diags harvester tests for World Ocean Database (WOD) diag files.

The depth-binned expected values (rounded) were computed independently of
score-hv with QC_threshold 0, i.e. EffectiveQC1 for oman and EffectiveQC0 for
the other groups.
"""
from datetime import datetime
from pathlib import Path

import pytest

from score_hv import hv_registry
from score_hv.harvester_base import harvest

DATA_DIR = Path(__file__).parent.resolve() / 'data'

STANDARD_BINS = [(0, 20), (20, 100), (100, 500), (500, 20000)]
STANDARD_STATS = ['mean', 'median', 'StdDev', 'minimum', 'maximum', 'rms', 'count']
GROUPS = ('ObsValue', 'oman', 'ombg', 'ObsError')
TOLERANCE = 0.001

# file name: expected record metadata
TEST_METADATA = {
    'wod_t_ctd.nc': dict(variables='waterTemperature', sensor='ctd',
                         longname='waterTemperature', units='DegC'),
    'wod_s_pfl.nc': dict(variables='salinity', sensor='pfl',
                         longname='Practical Salinity Scale', units='PSS'),
}

# file name: {depth bin: {statistic: values for GROUPS}}
TEST_REGISTRY = {
    'wod_t_ctd.nc': {
        (0, 20): {
            'mean': (-0.4939, -0.3808, -0.126, 0.5),
            'median': (-0.557, -0.2889, -0.1516, 0.5),
            'StdDev': (0.1086, 0.4398, 0.1395, 0.0),
            'minimum': (-0.587, -1.0777, -0.3383, 0.5),
            'maximum': (-0.33, 0.2956, 0.1766, 0.5),
            'rms': (0.5055, 0.5791, 0.1875, 0.5),
            'count': (63, 63, 63, 63),
        },
        (20, 100): {
            'mean': (-1.561, -1.0075, -1.075, 0.5),
            'median': (-1.703, -1.667, -1.663, 0.5),
            'StdDev': (0.3245, 0.779, 0.705, 0.0),
            'minimum': (-1.754, -1.754, -1.75, 0.5),
            'maximum': (-0.423, 0.304, 0.19, 0.5),
            'rms': (1.594, 1.273, 1.284, 0.5),
            'count': (243, 243, 243, 243),
        },
        (100, 500): {
            'mean': (-1.859, -1.859, -1.848, 0.5),
            'median': (-1.881, -1.881, -1.87, 0.5),
            'StdDev': (0.0513, 0.051, 0.048, 0.0),
            'minimum': (-1.915, -1.915, -1.897, 0.5),
            'maximum': (-1.694, -1.694, -1.69, 0.5),
            'rms': (1.86, 1.86, 1.848, 0.5),
            'count': (944, 944, 944, 944),
        },
        (500, 20000): {
            'mean': (-1.91, -1.91, -1.89, 0.5),
            'median': (-1.913, -1.913, -1.892, 0.5),
            'StdDev': (0.00539, 0.005, 0.005, 0.0),
            'minimum': (-1.916, -1.916, -1.895, 0.5),
            'maximum': (-1.902, -1.902, -1.882, 0.5),
            'rms': (1.91, 1.91, 1.89, 0.5),
            'count': (129, 129, 129, 129),
        },
    },
    'wod_s_pfl.nc': {
        (0, 20): {
            'mean': (35.008, 0.007, 0.01, 0.5),
            'median': (35.141, 0.002, 0.005, 0.5),
            'StdDev': (3.3964, 0.149, 0.213, 0.0),
            'minimum': (5.663, -0.611, -1.022, 0.5),
            'maximum': (38.633, 1.09, 1.211, 0.5),
            'rms': (35.172, 0.149, 0.213, 0.5),
            'count': (1701, 1701, 1701, 1701),
        },
        (20, 100): {
            'mean': (35.066, 0.008, 0.014, 0.5),
            'median': (35.387, 0.005, 0.009, 0.5),
            'StdDev': (3.5517, 0.156, 0.205, 0.0),
            'minimum': (5.669, -1.493, -1.849, 0.5),
            'maximum': (38.839, 1.315, 1.425, 0.5),
            'rms': (35.245, 0.156, 0.205, 0.5),
            'count': (5084, 5084, 5084, 5084),
        },
        (100, 500): {
            'mean': (35.286, -0.001, 0.008, 0.5),
            'median': (35.002, 0.005, 0.01, 0.5),
            'StdDev': (0.9287, 0.114, 0.143, 0.0),
            'minimum': (33.82, -0.666, -0.743, 0.5),
            'maximum': (38.689, 0.696, 0.901, 0.5),
            'rms': (35.299, 0.114, 0.143, 0.5),
            'count': (19901, 19901, 19901, 19901),
        },
        (500, 20000): {
            'mean': (34.716, 0.009, 0.009, 0.5),
            'median': (34.619, 0.0, 0.0, 0.5),
            'StdDev': (0.5211, 0.201, 0.202, 0.0),
            'minimum': (33.974, -0.619, -0.627, 0.5),
            'maximum': (38.629, 2.418, 2.418, 0.5),
            'rms': (34.72, 0.202, 0.202, 0.5),
            'count': (42893, 42893, 42893, 42893),
        },
    },
}


def harvest_file(filename, **request):
    file_path = DATA_DIR / filename
    if not file_path.exists():
        pytest.fail(f'Test data missing: {file_path}')
    return harvest({'harvester_name': hv_registry.SOCA_DIAGS,
                    'filenames': [str(file_path)],
                    **request})


@pytest.mark.parametrize('filename', TEST_REGISTRY)
def test_wod_depth_bins(filename):
    metadata = TEST_METADATA[filename]
    records = harvest_file(filename,
                           statistics=STANDARD_STATS,
                           variables=[metadata['variables']],
                           QC_threshold=0.0,
                           ocean_depth_bins=STANDARD_BINS)

    for record in records:
        for field, expected in metadata.items():
            assert getattr(record, field) == expected, f'{field} mismatch'
        assert record.satellite is None
        assert record.level is None
        assert record.file_region == 'global'

    harvested = {(record.ocean_depth_bins, record.statistics, record.group): record.value
                 for record in records}
    expected = {(depth_bin, statistic, group): value
                for depth_bin, statistics in TEST_REGISTRY[filename].items()
                for statistic, values in statistics.items()
                for group, value in zip(GROUPS, values)}
    assert harvested.keys() == expected.keys()
    for key, value in expected.items():
        assert harvested[key] == pytest.approx(value, abs=TOLERANCE), \
            f'{filename} {key}: harvested {harvested[key]}, expected {value}'


def test_wod_cycle_file_name():
    """Harvest a WOD file with a .YYYYMMDDHH cycle and .nc4 extension in its name."""
    records = harvest_file('wod_t_ctd.1979010200.nc4',
                           statistics=['rms', 'mean', 'count'],
                           variables=['waterTemperature'])
    assert len(records) == 3 * len(GROUPS)
    for record in records:
        assert record.variables == 'waterTemperature'
        assert record.sensor == 'ctd'
        assert record.satellite is None
        assert record.level is None
        assert record.file_region == 'global'
        assert record.ocean_depth_bins is None
        # median time of the observations used, not the cycle in the file name
        assert record.filetime == datetime(1979, 1, 1, 23, 22)

    harvested = {(record.group, record.statistics): record.value for record in records}
    assert harvested[('ombg', 'rms')] == pytest.approx(1.642326233143017, rel=TOLERANCE)
    assert harvested[('ObsError', 'mean')] == pytest.approx(0.5, rel=TOLERANCE)
    assert harvested[('ObsValue', 'count')] == 579
