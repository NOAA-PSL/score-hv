import math
import pytest
import json
from pathlib import Path
from score_hv import hv_registry
from score_hv.harvester_base import harvest

# --- 1. Global Registry of Test Cases ---
TEST_REGISTRY = {
    'SST_No_Filter': {
        'filename': 'sst_avhrr_mb_l3u.nc',
        'QC_threshold': 999999.0,
        'variable': 'sst',
        'components': {
            'variables': 'seaSurfaceTemperature',
            'sensor': 'avhrr', 'satellite': 'mb', 'level': 'l3u'
        },
        'expected_stats': {
            'mean':    {'ObsValue': 19.5079, 'oman': -0.0107501, 'ombg': 0.0312382, 'ObsError': 0.279562}, 
            'median':  {'ObsValue': 23.1182, 'oman': -0.0106021, 'ombg': 0.0298276, 'ObsError': 0.270455},
            'StdDev':  {'ObsValue': 8.75835, 'oman': 0.479307, 'ombg': 0.604165, 'ObsError': 0.0607292},
            'minimum': {'ObsValue': -2.002, 'oman': -7.75589, 'ombg': -7.98368, 'ObsError': 0.174539},
            'maximum': {'ObsValue': 30.3152, 'oman': 26.013 , 'ombg': 26.1218, 'ObsError': 1.03273},
            'rmse': {'ObsValue': 21.3838, 'oman': 0.479428 , 'ombg': 0.604969, 'ObsError': 0.286082}
        }
    },
    'SST_Strict_Filter': {
        'filename': 'sst_avhrr_mb_l3u.nc',
        'QC_threshold': 10.0,
        'variable': 'sst',
        'components': {
            'variables': 'seaSurfaceTemperature',
            'sensor': 'avhrr', 'satellite': 'mb', 'level': 'l3u'
        },
        'expected_stats': {
            'mean':    {'ObsValue': 20.748, 'oman': -0.017232 , 'ombg': 0.0232067, 'ObsError': 0.272279},
            'median':  {'ObsValue': 23.6211 , 'oman': -0.00832773, 'ombg': 0.0352963, 'ObsError':0.264845},
            'StdDev':  {'ObsValue': 7.58406 , 'oman': 0.143061  , 'ombg': 0.331607, 'ObsError': 0.0548204},
            'minimum': {'ObsValue': -0.990161, 'oman': -1.83607 , 'ombg': -4.96913, 'ObsError': 0.174539},
            'maximum': {'ObsValue': 30.3152, 'oman': 7.2996, 'ombg': 4.986, 'ObsError': 1.03273},
            'rmse': {'ObsValue': 22.0906, 'oman': 0.144095 , 'ombg': 0.332416, 'ObsError': 0.277743}
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

    # 1. Execute Harvester
    all_data = harvest(config_dict)
    assert len(all_data) > 0, "No data was harvested."

    # 2. Verify Statistics
    verify_statistics(all_data, meta['expected_stats'], test_id)

    print(f"Test {test_id} passed successfully.")
