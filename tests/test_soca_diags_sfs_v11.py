#!/usr/bin/env python
"""soca_diags harvester regression tests on the SFS_v11 ocean diag files.

The files in tests/data/sfs_v11 are a full set of gdas ocean diags for the
2023020112 cycle of the SFS_v11 scout run; soca_diags_sfs_v11.yaml documents
their origin and how the expected values were computed.
"""
from datetime import datetime
from pathlib import Path

import pytest
import yaml

from score_hv import hv_registry
from score_hv.harvester_base import harvest

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / 'data' / 'sfs_v11'
STATISTICS = ['mean', 'median', 'StdDev', 'minimum', 'maximum', 'rms', 'count']
# the files have no cycle in their name or path; it is inferred from their times
CYCLE = datetime(2023, 2, 1, 12)

with open(BASE_DIR / 'soca_diags_sfs_v11.yaml') as stream:
    EXPECTED = yaml.safe_load(stream)


@pytest.mark.parametrize('filename', EXPECTED)
def test_sfs_v11_diag_file(filename):
    file_path = DATA_DIR / filename
    if not file_path.exists():
        pytest.fail(f'Test data missing: {file_path}')

    records = harvest({'harvester_name': hv_registry.SOCA_DIAGS,
                       'filenames': [str(file_path)],
                       'statistics': STATISTICS,
                       'QC_threshold': 0,
                       'ocean_depth_bins': [0, 20, 100, 500, 20000]})

    expected = EXPECTED[filename]
    expected_values = dict()
    expected_mediantimes = dict()
    for variable, metadata in expected['variables'].items():
        for entry in metadata['records']:
            depth_bin = tuple(entry['depth_bin']) if entry['depth_bin'] else None
            key = (variable, depth_bin, entry['group'])
            expected_mediantimes[key] = datetime.fromisoformat(entry['mediantime'])
            for statistic in STATISTICS:
                if statistic in entry:
                    expected_values[key + (statistic,)] = entry[statistic]

    harvested = dict()
    for record in records:
        for component, value in expected['components'].items():
            assert getattr(record, component) == value, f'{component} mismatch'
        assert record.variables in expected['variables'], \
            f'unexpected variable {record.variables}'
        metadata = expected['variables'][record.variables]
        assert (record.longname, record.units) == (metadata['longname'], metadata['units'])
        assert record.QC_threshold == 0
        key = (record.variables, record.ocean_depth_bins, record.group)
        assert key in expected_mediantimes, f'unexpected record {key}'
        assert record.filetime == CYCLE, f'filetime mismatch for {key}'
        assert record.mediantime == expected_mediantimes[key], f'mediantime mismatch for {key}'
        harvested[key + (record.statistics,)] = record.value

    assert len(records) == len(harvested)
    assert harvested.keys() == expected_values.keys()
    for key, value in expected_values.items():
        assert harvested[key] == pytest.approx(value, rel=1e-6, abs=1e-9), \
            f'{key}: harvested {harvested[key]}, expected {value}'
