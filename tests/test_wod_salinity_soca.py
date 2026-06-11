import math
from pathlib import Path
from score_hv import hv_registry
from score_hv.harvester_base import harvest

STANDARD_BINS = [(0, 20), (20, 100), (100, 500), (500, 20000)]
STANDARD_STATS = ['mean', 'median', 'StdDev', 'minimum', 'maximum', 'rms', 'count']

# --- 1. Global Registry of Test Cases ---
TEST_REGISTRY = {
    'wod_s_pfl.nc': {
        'QC_threshold': 0.0,
        'longname': 'salinity',
        'units': 'DegC',
        'ocean_depth_bins': [(0, 20), (20, 100), (100, 500), (500,20000)],
        'components': {
            'variables': 'salinity',
            'sensor': 'pfl',
            'satellite': 'In-Situ',
            'level': None
        },
        'expected_stats': {
             (0, 20): {
                 'mean':    {'ObsValue': 35.008, 'oman': 0.007, 'ombg': 0.010, 'ObsError': 0.5},
                 'median':  {'ObsValue': 35.141, 'oman': 0.002, 'ombg': 0.005, 'ObsError': 0.5},
                 'StdDev':  {'ObsValue': 3.3964, 'oman': 0.149, 'ombg': 0.213, 'ObsError': 0.0},
                 'minimum': {'ObsValue': 5.663,  'oman': -0.611, 'ombg': -1.022, 'ObsError': 0.5},
                 'maximum': {'ObsValue': 38.633, 'oman': 1.090, 'ombg': 1.211,  'ObsError': 0.5},
                 'rms':    {'ObsValue': 35.172, 'oman': 0.149, 'ombg': 0.213,  'ObsError': 0.5},
                 'count':   {'ObsValue': 1701,   'oman': 1701,  'ombg': 1701,   'ObsError': 1701} 
            },
            (20, 100): {
                 'mean':    {'ObsValue': 35.066,  'oman': 0.008,  'ombg': 0.014,  'ObsError': 0.5},
                 'median':  {'ObsValue': 35.387,  'oman': 0.005,  'ombg': 0.009,  'ObsError': 0.5},
                 'StdDev':  {'ObsValue': 3.5517,  'oman': 0.156,  'ombg': 0.205,  'ObsError': 0.0},
                 'minimum': {'ObsValue': 5.669,   'oman': -1.493, 'ombg': -1.849, 'ObsError': 0.5},
                 'maximum': {'ObsValue': 38.839,  'oman': 1.315,  'ombg': 1.425 , 'ObsError': 0.5},
                 'rms':    {'ObsValue': 35.245,  'oman': 0.156,  'ombg': 0.205,  'ObsError': 0.5},
                 'count':   {'ObsValue': 5084,    'oman': 5084,   'ombg': 5084,   'ObsError': 5084}
            },
            (100, 500): {
                 'mean':    {'ObsValue': 35.286, 'oman': -0.001, 'ombg': 0.008,  'ObsError': 0.5},
                 'median':  {'ObsValue': 35.002, 'oman': 0.005,  'ombg': 0.010,  'ObsError': 0.5},
                 'StdDev':  {'ObsValue': 0.9287, 'oman': 0.114,  'ombg': 0.143,  'ObsError': 0.0},
                 'minimum': {'ObsValue': 33.820, 'oman': -0.666, 'ombg': -0.743, 'ObsError': 0.5},
                 'maximum': {'ObsValue': 38.689, 'oman': 0.696,  'ombg': 0.901,  'ObsError': 0.5},
                 'rms':    {'ObsValue': 35.299, 'oman': 0.114,  'ombg': 0.143,  'ObsError': 0.5},
                 'count':   {'ObsValue': 19901,  'oman': 19901,  'ombg': 19901,  'ObsError': 19901}
            },
            (500, 20000): {
                 'mean':    {'ObsValue': 34.716, 'oman': 0.009, 'ombg': 0.009,  'ObsError': 0.5},
                 'median':  {'ObsValue': 34.619, 'oman': 0.0,   'ombg': 0.0,    'ObsError': 0.5},
                 'StdDev':  {'ObsValue': 0.5211, 'oman': 0.201, 'ombg': 0.202,  'ObsError': 0.0},
                 'minimum': {'ObsValue': 33.974, 'oman': -0.619,'ombg': -0.627, 'ObsError': 0.5},
                 'maximum': {'ObsValue': 38.629, 'oman': 2.418, 'ombg': 2.418,  'ObsError': 0.5},
                 'rms':    {'ObsValue': 34.720, 'oman': 0.202, 'ombg': 0.202,  'ObsError': 0.5},
                 'count':   {'ObsValue': 42893,  'oman': 42893, 'ombg': 42893,  'ObsError': 42893}
            }
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
    """
    Verifies numerical accuracy by depth bin, statistic name, and group.
    """
    tolerance = 0.001

    for depth_bin, stats_map in expected_stats.items():
        
        for stat_name, group_map in stats_map.items():
            for group_name, exp_val in group_map.items():
                
                match = next((
                    d for d in harvested_results 
                    if d.ocean_depth_bins == depth_bin 
                    and d.statistics == stat_name 
                    and d.group == group_name
                ), None)

                assert match is not None, (
                    f"MISSING DATA: No record found for "
                    f"Bin: {depth_bin}, Stat: {stat_name}, Group: {group_name}"
                )

                act_val = float(match.value)
                assert math.isclose(act_val, exp_val, abs_tol=tolerance), (
                    f"VALUE MISMATCH in Bin {depth_bin}!\n"
                    f"  Stat:  {stat_name}\n"
                    f"  Group: {group_name}\n"
                    f"  Got:   {act_val}\n"
                    f"  Exp:   {exp_val}"
                )

    print("  [SUCCESS] All statistics verified against registry.")
# --- 3. Main Loop ---

def test_main():
    
    for filename, meta in TEST_REGISTRY.items():
        file_path = DATA_DIR / filename
        
        if not file_path.exists():
           raise ValueError(f"CRITICAL: Test file not found at {file_path}")  

        try:
            # CALL HARVESTER ONCE 
            config_dict = {
                'harvester_name': hv_registry.SOCA_DIAGS,
                'filenames': [str(file_path)],
                'statistics': STANDARD_STATS,
                'variables': [meta['components']['variables']],
                'QC_threshold': meta['QC_threshold'],
                'ocean_depth_bins': STANDARD_BINS,
            }

            all_data = harvest(config_dict)
            assert isinstance(all_data, list) and len(all_data) > 0, "No data harvested."

            verify_filename_components(all_data[0], meta['components'])

            verify_statistics(all_data, meta['expected_stats'], meta['QC_threshold'])
            
            
        except AssertionError as e:
            print(f"RESULT: {filename} [FAIL] -> {e}")
        except Exception as e:
            print(f"RESULT: {filename} [ERROR] -> {e}")

if __name__ == '__main__':
    test_main()
