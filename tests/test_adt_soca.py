import math
import pytest
import yaml
import json
from pathlib import Path
from score_hv import hv_registry
from score_hv.harvester_base import harvest

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / 'data'
YAML_PATH = BASE_DIR / "adt_glore.yaml"

with open(YAML_PATH, 'r') as f:
    raw_data = yaml.safe_load(f) 
    TEST_REGISTRY = raw_data.get('TEST_REGISTRY', raw_data)
"""
  Verification Helpers.
  """
def verify_filename_components(data_record, expected_components):
    assert data_record.variables == expected_components['variables'], f"Variable mismatch! Got {data_record.variables}"
    assert data_record.sensor == expected_components['sensor'], f"Sensor mismatch! Got {data_record.sensor}"
    assert data_record.satellite == expected_components['satellite'], f"Satellite mismatch! Got {data_record.satellite}"
    assert data_record.level == expected_components['level'], f"Level mismatch! Got {data_record.level}"

def verify_statistics(harvested_results, expected_stats, test_id):
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
        'statistics': ['mean', 'median', 'StdDev', 'minimum', 'maximum', 'rms'],
        'variables': [meta['variable']],
        'QC_threshold': meta['QC_threshold'],
    }

    all_data = harvest(config_dict)
    assert len(all_data) > 0, "No data was harvested."

    verify_filename_components(all_data[0], meta['components']) 
    verify_statistics(all_data, meta['expected_stats'], test_id)

    print(f"Test {test_id} passed successfully.")
