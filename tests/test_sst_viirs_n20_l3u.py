import math
import pytest
import json
from pathlib import Path
from score_hv import hv_registry
from score_hv.harvester_base import harvest

# --- 1. Global Registry of Test Cases ---
TEST_REGISTRY = {
    'SST_No_Filter': {
        'filename': 'sst_viirs_n20_l3u.2021070300.nc4',
        'QC_threshold': 999999.0,
        'variable': 'sst',
        'components': {
            'variables': 'seaSurfaceTemperature',
            'sensor': 'avhrr', 'satellite': 'mb', 'level': 'l3u'
        },
        'expected_stats': {
            'mean':    {'ObsValue': 18.92403793334961, 'oman': 0.06212509796023369, 'ombg': 0.07588130235671997}, 
            'median':  {'ObsValue': 22.409034729003906, 'oman': 0.02918902598321438 , 'ombg': 0.05533474311232567},
            'StdDev':  {'ObsValue': 9.234354972839355, 'oman': 0.4363338053226471, 'ombg': 0.497491717338562},
            'minimum': {'ObsValue': -2.1238181591033936, 'oman': -6.02739143371582, 'ombg': -6.222834587097168},
            'maximum': {'ObsValue': 34.480560302734375, 'oman': 11.538920402526855, 'ombg': 11.55988597869873}
        }
    },
    'SST_Strict_Filter': {
        'filename': 'sst_viirs_n20_l3u.2021070300.nc4',
        'QC_threshold': 10.0,
        'variable': 'sst',
        'components': {
            'variables': 'seaSurfaceTemperature',
            'sensor': 'viirs', 'satellite': 'mb', 'level': 'l3u'
        },
        'expected_stats': {
            'mean':    {'ObsValue': 19.986648559570312, 'oman': 0.02114727906882763, 'ombg': 0.03896670043468475},
            'median':  {'ObsValue': 23.214126586914062, 'oman': 0.02059902995824814, 'ombg': 0.04520326480269432},
            'StdDev':  {'ObsValue': 8.476527214050293, 'oman': 0.22127407789230347 , 'ombg': 0.3417792022228241},
            'minimum': {'ObsValue': 1.0003256797790527, 'oman': -2.5293326377868652, 'ombg': -4.99120569229126},
            'maximum': {'ObsValue': 33.745365142822266, 'oman': 4.883172988891602, 'ombg':4.84686279296875}
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
