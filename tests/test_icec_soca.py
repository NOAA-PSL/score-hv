import math
import pytest
import json
from pathlib import Path
from score_hv import hv_registry
from score_hv.harvester_base import harvest

# --- 1. Global Registry of Test Cases ---
TEST_REGISTRY = {
    'ICEC_No_Filter': {
        'filename': 'icec_amsr2_north.nc',
        'QC_threshold': 999999.0,
        'variable': 'icec',
        'components': {
            'variables': 'seaIceFraction',
            'sensor': 'amsr2', 'satellite': None, 'level': None
        },
        'expected_stats': {
            'mean':    {'ObsValue': 0.503423, 'oman': 0.00413683, 'ombg': 0.00636585}, 
            'median':  {'ObsValue': 0.7, 'oman': 2.54409e-33, 'ombg': 0.0},
            'StdDev':  {'ObsValue': 0.489884, 'oman': 0.0694154, 'ombg': 0.0876204},
            'minimum': {'ObsValue': 0.0, 'oman': -0.979116, 'ombg': -1.0},
            'maximum': {'ObsValue': 1.0, 'oman': 1.06013, 'ombg': 1.0}
        }
    },
    'ICEC_Strict_Filter': {
        'filename': 'icec_amsr2_north.nc',
        'QC_threshold': 10.0,
        'variable': 'icec',
        'components': {
            'variables': 'seaIceFraction',
            'sensor': 'amsr2', 'satellite': None, 'level': None
        },
        'expected_stats': {
            'mean':    {'ObsValue': 0.794636, 'oman':  -0.000387731, 'ombg': 0.00311572},
            'median':  {'ObsValue': 1.0, 'oman': 0.000454241, 'ombg': 2.39292e-05},
            'StdDev':  {'ObsValue': 0.389075, 'oman': 0.0325543, 'ombg': 0.0618738},
            'minimum': {'ObsValue': 0.0, 'oman': -0.495688, 'ombg': -0.499915},
            'maximum': {'ObsValue': 1.0, 'oman': 0.528345, 'ombg': 0.5}
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
            
            if not math.isclose(act_val, exp_val, rel_tol=tolerance):
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

    # 3. Cross-Test Logic: Compare Counts (Optional check)
    # If this is the filtered test, we can check that it has different values than No_Filter
    print(f"Test {test_id} passed successfully.")
