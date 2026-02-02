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
            'mean':    {'ObsValue': 18.917865741653607, 'oman': -0.022735618263781874, 'ombg': -0.018309653345885482}, 
            'median':  {'ObsValue': 21.956811904907227, 'oman': -0.00784428883343935, 'ombg': 0.0009183410438708961},
            'StdDev':  {'ObsValue': 8.74209976196289, 'oman': 0.24208711087703705, 'ombg': 0.5164351463317871},
            'minimum': {'ObsValue': -2.002044677734375, 'oman': -5.484813213348389, 'ombg': -9.026327133178711},
            'maximum': {'ObsValue': 31.499406814575195, 'oman': 4.796906471252441 , 'ombg': 4.357113838195801}
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
            'mean':    {'ObsValue': 20.247601552227692 , 'oman': -0.011572417181327524 , 'ombg': 0.000774545869631855},
            'median':  {'ObsValue': 22.64992904663086 , 'oman': -0.005374964326620102, 'ombg': 0.006451743189245462 },
            'StdDev':  {'ObsValue': 7.433576757441979 , 'oman': 0.14116205549992755 , 'ombg': 0.44214249728158916},
            'minimum': {'ObsValue': -1.1881109476089478, 'oman': -2.1696481704711914 , 'ombg': -4.986067771911621 },
            'maximum': {'ObsValue': 31.44783592224121 , 'oman': 4.407961368560791 , 'ombg': 4.211721897125244}
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
            
            if not math.isclose(act_val, exp_val, rel_tol=1e-6):
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
