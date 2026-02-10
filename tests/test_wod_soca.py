import math
from pathlib import Path
from score_hv import hv_registry
from score_hv.harvester_base import harvest

# --- 1. Global Registry of Test Cases ---
TEST_REGISTRY = {
    'wod_t_ctd.nc': {
        'QC_threshold': 0.0,
        'longname': 'Temperature',
        'units': 'DegC',
        'variable': 'waterTemperature',
        'ocean_depth_bins': [(0, 20), (20, 100), (100, 500)],
        # filename Component Expectations
        'components': {
            'variables': 'waterTemperature',
            'sensor': 'ctd',
            'satellite': None,
            'level': None
        },
        'expected_stats': {
            'mean':    {'ObsValue': -1.748781, 'oman': -1.64613, 'ombg': -1.63666}, 
            'median':  {'ObsValue': -1.875,    'oman': -1.875,    'ombg': -1.86578},
            'StdDev':  {'ObsValue': 0.331523, 'oman': 0.547509  , 'ombg': 0.534948},
            'minimum': {'ObsValue': -1.916, 'oman': -1.916, 'ombg': -1.89749},
            'maximum': {'ObsValue': -0.33, 'oman': 0.304453 , 'ombg': 0.1898}
        }
    }
}

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / 'data'


"""
  Methods for verification of harvested_results from soca_diags.py.
  """
def verify_filename_components(data_record, expected_components):
    """
    Validates that the harvester correctly parsed the filename into components.
    """
    assert data_record.variables == expected_components['variables'], \
        f"Variable mismatch! Got {data_record.variables}"
    assert data_record.sensor == expected_components['sensor'], \
        f"Sensor mismatch! Got {data_record.sensor}"
    assert data_record.satellite == expected_components['satellite'], \
        f"Satellite mismatch! Got {data_record.satellite}"
    assert data_record.level == expected_components['level'], \
        f"Level mismatch! Got {data_record.level}"

def verify_statistics(harvested_results, expected_stats, threshold):
    """Verifies numerical accuracy of the harvested data."""
    tolerance = 0.001
    print("  Verifying statistical values...")
    for stat_name, expected_groups in expected_stats.items():
        subset = [d for d in harvested_results if d.statistics == stat_name]
        
        actual_groups = {d.group: d.value for d in subset}
        for group, exp_val in expected_groups.items():
            act_val = actual_groups.get(group)
            assert act_val is not None, f"Missing group {group} in {stat_name}"
            assert math.isclose(act_val, exp_val, rel_tol=tolerance), \
                f"Value mismatch in {stat_name}:{group}. Got {act_val}, expected {exp_val}"

# --- 3. Main Loop ---

def test_main():
    print(f"{' HARVESTER TEST SUITE ':=^40}")
    
    for filename, meta in TEST_REGISTRY.items():
        file_path = DATA_DIR / filename
        print(f"\nProcessing: {filename}")
        
        if not file_path.exists():
           raise ValueError(f"CRITICAL: Test file not found at {file_path}")  

        try:
            # CALL HARVESTER ONCE 
            config_dict = {
                'harvester_name': hv_registry.SOCA_DIAGS,
                'filenames': [str(file_path)],
                'statistics': list(meta['expected_stats'].keys()),
                'variables': [meta['variable']],
                'QC_threshold': meta['QC_threshold'],
                'ocean_depth_bins': meta.get('ocean_depth_bins', [None]),
            }
            all_data = harvest(config_dict)

            # 1. Sanity Check
            assert isinstance(all_data, list) and len(all_data) > 0, "No data harvested."

            # 2. Test Filename Components (Using first record)
            verify_filename_components(all_data[0], meta['components'])

            # 3. Test Numerical Statistics
            verify_statistics(all_data, meta['expected_stats'], meta['QC_threshold'])
            
            print(f"RESULT: {filename} [PASS]")
            
        except AssertionError as e:
            print(f"RESULT: {filename} [FAIL] -> {e}")
        except Exception as e:
            print(f"RESULT: {filename} [ERROR] -> {e}")

if __name__ == '__main__':
    main()
