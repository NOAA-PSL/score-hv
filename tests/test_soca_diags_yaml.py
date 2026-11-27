#!/usr/bin/env python
"""soca_diags harvester tests driven by the YAML registries in this directory.

Each registry entry names a diag file in tests/data, the QC threshold and
variable to request, the components expected on every harvested record, and
the expected value of each statistic for each data group.
"""
from pathlib import Path

import pytest
import yaml

from score_hv import hv_registry
from score_hv.harvester_base import harvest

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / 'data'
REGISTRY_FILES = ('adt_glore.yaml',
                  'icec_amsr2_south.yaml',
                  'icec_nsidc_nh.yaml',
                  'sst_avhrr.yaml',
                  'sst_nggodas.yaml',
                  'sst_viirs.yaml')
STATISTICS = ['mean', 'median', 'StdDev', 'minimum', 'maximum', 'rms']


class UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate keys, which would silently drop
    registry entries."""

    def construct_mapping(self, node, deep=False):
        keys = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in keys:
                raise yaml.constructor.ConstructorError(
                    None, None, f'duplicate key {key!r}', key_node.start_mark)
            keys.add(key)
        return super().construct_mapping(node, deep=deep)


def registry_cases():
    cases = []
    for registry_file in REGISTRY_FILES:
        with open(BASE_DIR / registry_file) as stream:
            registry = yaml.load(stream, Loader=UniqueKeyLoader)
        for test_id, case in registry.items():
            cases.append(pytest.param(case, id=f'{Path(registry_file).stem}-{test_id}'))
    return cases


@pytest.mark.parametrize('case', registry_cases())
def test_soca_diags_registry(case):
    file_path = DATA_DIR / case['filename']
    if not file_path.exists():
        pytest.fail(f'Test data missing: {file_path}')

    records = harvest({'harvester_name': hv_registry.SOCA_DIAGS,
                       'filenames': [str(file_path)],
                       'statistics': STATISTICS,
                       'variables': [case['variable']],
                       'QC_threshold': case['QC_threshold']})

    for record in records:
        assert record.variables == case['variable']
        for component, expected in case['components'].items():
            assert getattr(record, component) == expected, f'{component} mismatch'

    harvested = {(record.statistics, record.group): record.value for record in records}
    expected = {(statistic, group): value
                for statistic, groups in case['expected_stats'].items()
                for group, value in groups.items()}
    assert len(records) == len(expected)
    assert harvested.keys() == expected.keys()
    for key, value in expected.items():
        assert harvested[key] == pytest.approx(value, rel=1e-3, abs=1e-7), \
            f'{key}: harvested {harvested[key]}, expected {value}'
