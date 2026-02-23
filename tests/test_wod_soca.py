import math
import pytest
import json
from pathlib import Path
from score_hv import hv_registry
from score_hv.harvester_base import harvest

# --- 1. Global Registry of Test Cases ---
TEST_REGISTRY = {
    'SST_No_Filter': {
        'filename': 'wod_t_ctd.nc',
        'QC_threshold': 999999.0,
        'variable': 'sst',
        'components': {
            'variables': 'waterTemperature',
            'sensor': 'ctd', 
            'satellite': None, 
            'level': None
        },
        'expected_stats': {
            'mean':    {'ObsValue': -1.748781, 'oman': -1.64613, 'ombg': -1.63666, 'ObsError':0.5}, 
            'median':  {'ObsValue': -1.875,    'oman': -1.875,    'ombg': -1.86578, 'ObsError':0.5 },
            'StdDev':  {'ObsValue': 0.331523, 'oman': 0.547509, 'ombg': 0.534948, 'ObsError':0.0},
            'minimum': {'ObsValue': -1.916, 'oman': -1.916, 'ombg': -1.89749, 'ObsError':0.5},
            'maximum': {'ObsValue': -0.33, 'oman': 0.304453 , 'ombg': 0.1898, 'ObsError':0.5},
            'rmse': {'ObsValue': 1.77991 , 'oman':1.73473, 'ombg': 1.7218, 'ObsError': 0.5}            
        }

        }
    }
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / 'data'


def verify_statistics(harvested_results, expected_stats, test_id):
    """
      Verifies all requested stats.
      """
    tolerance = 0.001 
    actual_map = {}
    for d in harvested_results:
        stat_name = d.statistics
        group_name = d.group
        if stat_name not in actual_map:
            actual_map[stat_name] = {}
        actual_map[stat_name][group_name] = float(d.value)

    for stat_name, expected_groups in expected_stats.items():
        # Ensure the statistic (e.g., 'mean') exists in results
        assert stat_name in actual_map, f"Stat '{stat_name}' missing for {test_id}"
        
        for group_key, exp_val in expected_groups.items():
            assert group_key in actual_map[stat_name], \
                f"Group '{group_key}' missing in {stat_name} for {test_id}"
            
            act_val = actual_map[stat_name][group_key]
            assert act_val == pytest.approx(exp_val, abs=tolerance), \
                f"Value mismatch in {test_id} | {stat_name}:{group_key} | Expected {exp_val}, got {act_val}"

            


@pytest.mark.parametrize("test_id", TEST_REGISTRY.keys())
def test_soca_harvester(test_id):
    """Main test entry point parameterized by TEST_REGISTRY."""
    meta = TEST_REGISTRY[test_id]
    file_path = DATA_DIR / meta['filename']
    
    if not file_path.exists():
        pytest.fail(f"Test data missing: {file_path}")

    # Build the config for the harvester
    config_dict = {
        'harvester_name': hv_registry.SOCA_DIAGS,
        'filenames': [str(file_path)],
        'statistics': ['mean', 'median', 'StdDev', 'minimum', 'maximum', 'rmse'],
        'variables': [meta['variable']],
        'QC_threshold': meta['QC_threshold'],
    }

    all_data = harvest(config_dict)
    assert len(all_data) > 0, "No data was harvested."

    verify_statistics(all_data, meta['expected_stats'], test_id)

    print(f"Test {test_id} passed successfully.")
