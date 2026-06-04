import math
import yaml 
import json
import pytest
from pathlib import Path
from score_hv import hv_registry
from score_hv.harvester_base import harvest

# --- 1. Load the Registry from YAML ---
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / 'data'
YAML_PATH = BASE_DIR / "icec_amsr2_north.yaml"

with open(YAML_PATH, 'r') as f:
    raw_data = yaml.safe_load(f) 
    TEST_REGISTRY = raw_data.get('TEST_REGISTRY', raw_data)

def verify_filename_components(data_record, expected_components, expected_variable):
    """
    Verifies the metadata tags attached to the harvested record.
    """
    # Check each component against the expected dictionary
    assert data_record.variables == expected_variable, \
        f"Variable mismatch! Got {data_record.variables}, expected {expected_variable}"
    
    # Use .get() for the rest to prevent more KeyErrors if a value is missing
    assert data_record.sensor == expected_components.get('sensor'), \
        f"Sensor mismatch! Got {data_record.sensor}"
   
    assert data_record.satellite == expected_components.get('satellite'), \
        f"Satellite mismatch! Got {data_record.satellite}"
    
    assert data_record.level == expected_components.get('level'), \
        f"Level mismatch! Got {data_record.level}"
    
    assert data_record.file_region == expected_components.get('file_region'), \
        f"Region mismatch! Got '{data_record.file_region}'"

def verify_statistics(harvested_results, expected_stats, test_id):
    """
    Verifies the statistical values (mean, std dev, etc.) against baselines.
    """
    
    rel_tol = 0.001  # 0.1% relative tolerance
    abs_tol = 1e-07  # Handles cases where expected value is 0 or near-zero

    actual_map = {}
    for d in harvested_results:
        if d.statistics not in actual_map:
            actual_map[d.statistics] = {}
        actual_map[d.statistics][d.group] = float(d.value)

    if not expected_stats or any(stat not in expected_stats for stat in actual_map):
        print(f"\n\n--- CURRENT OUTPUT FOR {test_id} (Copy into expected_stats) ---")
        print(json.dumps(actual_map, indent=4))
        if not expected_stats:
            pytest.fail(f"No baseline defined for {test_id}. See console for values.")

    for stat_name, expected_groups in expected_stats.items():
        actual_groups = actual_map.get(stat_name, {})
        
        for group, exp_val in expected_groups.items():
            act_val = actual_groups.get(group)
            assert act_val is not None, (
                f"Stat group '{group}' missing in '{stat_name}' for test: {test_id}"
            )
            
            if not math.isclose(act_val, exp_val, rel_tol=rel_tol, abs_tol=abs_tol):
                # Print context before failing
                print(f"\n\n--- MISMATCH DETECTED: {test_id} ---")
                print(f"Statistic: {stat_name} | Group: {group}")
                print(f"Expected:  {exp_val}")
                print(f"Actual:    {act_val}")
                print(f"Diff:      {abs(act_val - exp_val)}")
                
                assert False, f"{test_id} mismatch in {stat_name}:{group}. Got {act_val}, expected {exp_val}"

@pytest.mark.parametrize("test_id", TEST_REGISTRY.keys())
def test_soca_harvester(test_id):
    """Main test entry point parameterized by TEST_REGISTRY."""
    meta = TEST_REGISTRY[test_id]
    file_path = DATA_DIR / meta['filename']
    
    if not file_path.exists():
        pytest.fail(f"Test data missing: {file_path}")

    comp = meta.get('components', {})
    
    # Build the config dictionary for the harvester
    config_dict = {
        'harvester_name': hv_registry.SOCA_DIAGS,
        'filenames': [str(file_path)],
        'statistics': ['mean', 'median', 'StdDev', 'minimum', 'maximum', 'rmse'],
        'variables': [meta['variable']],
        'QC_threshold': meta['QC_threshold'],
        'ocean_depth_bins': meta.get('ocean_depth_bins') or comp.get('ocean_depth_bins'),
    }

    # 1. Execute Harvester
    all_data = harvest(config_dict)
    assert len(all_data) > 0, "No data was harvested."
    
    # 2. Verification (Using external helpers)
    verify_filename_components(all_data[0], comp, meta['variable'])
    verify_statistics(all_data, meta['expected_stats'], test_id)

    print(f"Test {test_id} passed successfully.")
