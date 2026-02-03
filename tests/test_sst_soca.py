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
            'mean':    {'ObsValue': 18.9179, 'oman': -0.0227356, 'ombg': -0.0183097}, 
            'median':  {'ObsValue': 21.9568, 'oman': -0.00784429, 'ombg': 0.000918341},
            'StdDev':  {'ObsValue': 8.74214, 'oman': 0.242088 , 'ombg': 0.516438},
            'minimum': {'ObsValue': -2.00204, 'oman': -5.48481, 'ombg': -9.02633},
            'maximum': {'ObsValue': 31.4994, 'oman': 4.79691 , 'ombg': 4.35711}
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
            'mean':    {'ObsValue': 20.2476, 'oman': -0.0115724 , 'ombg': 0.000774546},
            'median':  {'ObsValue': 22.6499, 'oman': -0.00537496, 'ombg': 0.00645174 },
            'StdDev':  {'ObsValue': 7.43362, 'oman': 0.141163 , 'ombg': 0.442145},
            'minimum': {'ObsValue': -1.18811, 'oman': -2.16965 , 'ombg': -4.98607},
            'maximum': {'ObsValue': 31.4478, 'oman': 4.40796, 'ombg': 4.21172}
        }  
    }
}

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / 'data'

# --- 2. Verification Helpers ---

def verify_statistics(harvested_results, expected_stats, test_id):
    """
      Verifies all requested stats.
      """
    tolerance = 0.001 
    # Organize actual data into a nested dict: {stat: {group: value}}
    actual_map = {}
    for d in harvested_results:
        if d.statistics not in actual_map:
            actual_map[d.statistics] = {}
        actual_map[d.statistics][d.group] = float(d.value)

    # If expectations are missing or mismatched, print the actual values for copy-pasting
    if not expected_stats or any(stat not in expected_stats for stat in actual_map):
        print(f"\n\n--- CURRENT OUTPUT FOR {test_id} (Copy into expected_stats) ---")
        print(json.dumps(actual_map, indent=4))
        if not expected_stats:
            pytest.fail(f"No baseline for {test_id}. Baseline generated in console.")

    # Compare actual vs expected
    for stat_name, expected_groups in expected_stats.items():
        actual_groups = actual_map.get(stat_name, {})
        for group, exp_val in expected_groups.items():
            act_val = actual_groups.get(group)
            
            assert act_val is not None, f"Group {group} missing in {stat_name} for {test_id}"
            
            if not math.isclose(act_val, exp_val, rel_tol=0.001):
                print(f"\n\n--- MISMATCH DETECTED: CURRENT DATA FOR {test_id} ---")
                print(json.dumps(actual_map, indent=4))
                pytest.fail(f"{test_id} mismatch in {stat_name}:{group}. Got {act_val}, expected {exp_val}")

# --- 3. The Pytest Function ---

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
        'statistics': ['mean', 'median', 'StdDev', 'minimum', 'maximum'],
        'variables': [meta['variable']],
        'QC_threshold': meta['QC_threshold'],
    }

    # 1. Execute Harvester
    all_data = harvest(config_dict)
    assert len(all_data) > 0, "No data was harvested."

    # 2. Verify Statistics
    verify_statistics(all_data, meta['expected_stats'], test_id)

    print(f"Test {test_id} passed successfully.")
