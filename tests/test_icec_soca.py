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
            'mean':    {'ObsValue': 0.503423, 'oman': 0.00413683, 'ombg': 0.00636585, 'ObsError':0.1}, 
            'median':  {'ObsValue': 0.7, 'oman': 2.54409e-33, 'ombg': 0.0,  'ObsError': 0.1},
            'StdDev':  {'ObsValue': 0.489884, 'oman': 0.0694154, 'ombg': 0.0876204, 'ObsError': 0.0},
            'minimum': {'ObsValue': 0.0, 'oman': -0.979116, 'ombg': -1.0, 'ObsError': 0.1},
            'maximum': {'ObsValue': 1.0, 'oman': 1.06013, 'ombg': 1.0, 'ObsError': 0.1},
            'rmse': {'ObsValue': 0.702439 , 'oman':0.0695385, 'ombg': 0.0878513, 'ObsError': 0.1}
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
            'mean':    {'ObsValue': 0.794636, 'oman':  -0.000387731, 'ombg': 0.00311572, 'ObsError': 0.1},
            'median':  {'ObsValue': 1.0, 'oman': 0.000454241, 'ombg': 2.39292e-05, 'ObsError': 0.1},
            'StdDev':  {'ObsValue': 0.389075, 'oman': 0.0325543, 'ombg': 0.0618738, 'ObsError': 0.0},
            'minimum': {'ObsValue': 0.0, 'oman': -0.495688, 'ombg': -0.499915, 'ObsError': 0.1},
            'maximum': {'ObsValue': 1.0, 'oman': 0.528345, 'ombg': 0.5, 'ObsError': 0.1},
            'rmse': {'ObsValue': 0.884774, 'oman':0.0325566, 'ombg': 0.0619521, 'ObsError': 0.1}
        }  
    }
}

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / 'data'

# --- 2. Verification Helpers ---

def verify_statistics(harvested_results, expected_stats, test_id):
    """
       Verifies harvested stats match expected values exactly by key.
       """
    tolerance = 0.001
    actual_map = {}
    for d in harvested_results:
        if d.statistics not in actual_map:
            actual_map[d.statistics] = {}
        # Mapping exactly to d.group as it comes from the harvester
        actual_map[d.statistics][d.group] = float(d.value)

    # 2. Compare against Registry
    for stat_name, expected_groups in expected_stats.items():
        # Check that the statistic itself was harvested
        assert stat_name in actual_map, f"Stat '{stat_name}' missing for {test_id}"
        
        for group_key, exp_val in expected_groups.items():
            # Check that the specific group (e.g. 'ObsValue') exists
            assert group_key in actual_map[stat_name], \
                f"Group '{group_key}' missing in {stat_name} for {test_id}"
            
            act_val = actual_map[stat_name][group_key]
            
            # 3. The Actual Math Comparison
            # We still use approx() because floating point math in NetCDF 
            # rarely matches literal Python floats to 15 decimal places.
            assert act_val == pytest.approx(exp_val, abs=1e-5), \
                f"Value mismatch in {test_id} | {stat_name}:{group_key} | Expected {exp_val}, got {act_val}"


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
        'statistics': ['mean', 'median', 'StdDev', 'minimum', 'maximum', 'rmse'],
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
