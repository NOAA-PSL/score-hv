import math
import pytest
import json
from pathlib import Path
from score_hv import hv_registry
from score_hv.harvester_base import harvest

# --- 1. Global Registry of Test Cases ---
TEST_REGISTRY = {
    'ICEC_No_Filter': {
        'filename': 'adt_glore_e2.nc',
        'QC_threshold': 999999.0,
        'variable': 'absoluteDynamicTopography',
        'components': {
            'variables': 'absoluteDynamicTopography',
            'sensor': 'RA-2', 'satellite': 'ERS2', 'level': None
        },
        'expected_stats': {
            'mean':    {'ObsValue': 0.380361, 'oman': -0.0033328 , 'ombg': -0.00408677, 'ObsError': 0.1}, 
            'median':  {'ObsValue': 0.6423, 'oman': -0.00881378, 'ombg': -0.0118032, 'ObsError': 0.1},
            'StdDev':  {'ObsValue': 0.695176, 'oman': 0.100901, 'ombg': 0.120154, 'ObsError': 0.0},
            'minimum': {'ObsValue': -1.4647, 'oman': -0.386282, 'ombg': -0.443521, 'ObsError': 0.1},
            'maximum': {'ObsValue': 1.7431, 'oman': 1.10506 , 'ombg': 1.21564, 'ObsError': 0.1},
            'rmse':    {'ObsValue': 0.792401, 'oman': 0.100951, 'ombg': 0.120218, 'ObsError': 0.1}  
        }
    },
    'ICEC_Strict_Filter': {
        'filename': 'adt_glore_e2.nc',
        'QC_threshold': 10.0,
        'variable': 'absoluteDynamicTopography',
        'components': {
            'variables': 'absoluteDynamicTopography',
            'sensor': 'RA-2', 'satellite': 'ERS2', 'level': None
        },
        'expected_stats': {
            'mean':    {'ObsValue': 0.67733, 'oman': -3.40937e-11, 'ombg': -0.0019098, 'ObsError': 0.1},
            'median':  {'ObsValue': 0.71695, 'oman': -0.00638066, 'ombg': -0.00961795, 'ObsError': 0.1},
            'StdDev':  {'ObsValue': 0.331167, 'oman': 0.0784638, 'ombg': 0.106203, 'ObsError': 0.0},
            'minimum': {'ObsValue': -0.6917, 'oman': -0.360815, 'ombg': -0.443521, 'ObsError': 0.1},
            'maximum': {'ObsValue': 1.7431, 'oman': 0.772016, 'ombg': 0.99856, 'ObsError': 0.1},
            'rmse':    {'ObsValue': 0.753946, 'oman': 0.078459, 'ombg': 0.106213, 'ObsError': 0.1}
        }  
    }
}

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / 'data'

"""
  Verification Helpers.
  """
def verify_filename_components(data_record, expected_components):
    assert data_record.variables == expected_components['variables'], f"Variable mismatch! Got {data_record.variables}"
    assert data_record.sensor == expected_components['sensor'], f"Sensor mismatch! Got {data_record.sensor}"
    assert data_record.satellite == expected_components['satellite'], f"Satellite mismatch! Got {data_record.satellite}"
    assert data_record.level == expected_components['level'], f"Level mismatch! Got {data_record.level}"
    assert data_record.file_region == expected_components['file_region'], \
        f"Region mismatch! Got '{data_record.file_region}', expected '{expected_components['file_region']}'"


def verify_statistics(harvested_results, expected_stats, test_id):
    print("Verifying stats")
    rel_tol = 0.001
    abs_tol = 1e-07 

    actual_map = {}
    for d in harvested_results:
        if d.statistics not in actual_map:
            actual_map[d.statistics] = {}
        actual_map[d.statistics][d.group] = float(d.value)

    if not expected_stats or any(stat not in expected_stats for stat in actual_map):
        print(f"\n\n--- CURRENT OUTPUT FOR {test_id} (Copy into expected_stats) ---")
        print(json.dumps(actual_map, indent=4))
        if not expected_stats:
            pytest.fail(f"No baseline defined for {test_id}. See console for current values.")

    for stat_name, expected_groups in expected_stats.items():
        actual_groups = actual_map.get(stat_name, {})
        
        for group, exp_val in expected_groups.items():
            act_val = actual_groups.get(group)
            
            assert act_val is not None, (
                f"Stat group '{group}' missing in '{stat_name}' for test: {test_id}"
            )
            
            if not math.isclose(act_val, exp_val, rel_tol=rel_tol, abs_tol=abs_tol):
                # If it fails, print the full context to the console for debugging
                print(f"\n\n--- MISMATCH DETECTED: {test_id} ---")
                print(f"Statistic: {stat_name} | Group: {group}")
                print(f"Expected:  {exp_val}")
                print(f"Actual:    {act_val}")
                print(f"Diff:      {abs(act_val - exp_val)}")
                # Final assertion to trigger pytest failure
                assert math.isclose(act_val, exp_val, rel_tol=rel_tol, abs_tol=abs_tol), \
                    f"{test_id} mismatch in {stat_name}:{group}. Got {act_val}, expected {exp_val}"

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
