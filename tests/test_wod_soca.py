import math
from pathlib import Path
from score_hv import hv_registry
from score_hv.harvester_base import harvest

STANDARD_BINS = [(0, 20), (20, 100), (100, 500), (500, 20000)]
STANDARD_STATS = ['mean', 'median', 'StdDev', 'minimum', 'maximum', 'rms', 'count']

# --- 1. Global Registry of Test Cases ---
TEST_REGISTRY = {
    'wod_t_ctd.nc': {
        'QC_threshold': 0.0,
        'longname': 'Temperature',
        'units': 'DegC',
        'ocean_depth_bins': [(0, 20), (20, 100), (100, 500), (500,20000)],
        'expected_stats': {
             (0, 20): {
                 'mean':    {'ObsValue': -0.4939, 'oman': -0.3808, 'ombg': -0.126, 'ObsError': 0.5},
                 'median':  {'ObsValue': -0.5570, 'oman': -0.2889, 'ombg': -0.1516, 'ObsError': 0.5},
                 'StdDev':  {'ObsValue': 0.1086, 'oman':  0.4398, 'ombg': 0.1395, 'ObsError': 0.0},
                 'minimum': {'ObsValue': -0.5870, 'oman': -1.0777, 'ombg': -0.3383, 'ObsError': 0.5},
                 'maximum': {'ObsValue': -0.3300, 'oman': 0.2956,  'ombg': 0.1766,  'ObsError': 0.5},
                 'rms':    {'ObsValue': 0.5055,  'oman': 0.5791,  'ombg': 0.1875,  'ObsError': 0.5},
                 'count':   {'ObsValue': 63,      'oman': 63,      'ombg': 63,      'ObsError': 63}
            },
            (20, 100): {
                 'mean':    {'ObsValue': -1.561, 'oman': -1.0075, 'ombg': -1.075, 'ObsError': 0.5},
                 'median':  {'ObsValue': -1.703, 'oman': -1.667, 'ombg': -1.663, 'ObsError': 0.5},
                 'StdDev':  {'ObsValue': 0.3245, 'oman': 0.779,  'ombg': 0.705,  'ObsError': 0.0},
                 'minimum': {'ObsValue': -1.754, 'oman': -1.754, 'ombg': -1.750, 'ObsError': 0.5},
                 'maximum': {'ObsValue': -0.423, 'oman': 0.304,  'ombg': 0.190,  'ObsError': 0.5},
                 'rms':    {'ObsValue': 1.594,  'oman': 1.273,  'ombg': 1.284,  'ObsError': 0.5},
                 'count':   {'ObsValue': 243,    'oman': 243,    'ombg': 243,    'ObsError': 243}
            },
            (100, 500): {
                 'mean':    {'ObsValue': -1.859, 'oman': -1.859, 'ombg': -1.848, 'ObsError': 0.5},
                 'median':  {'ObsValue': -1.881, 'oman': -1.881, 'ombg': -1.870, 'ObsError': 0.5},
                 'StdDev':  {'ObsValue': 0.0513, 'oman': 0.051,  'ombg': 0.048,  'ObsError': 0.0},
                 'minimum': {'ObsValue': -1.915, 'oman': -1.915, 'ombg': -1.897, 'ObsError': 0.5},
                 'maximum': {'ObsValue': -1.694, 'oman': -1.694, 'ombg': -1.690, 'ObsError': 0.5},
                 'rms':    {'ObsValue': 1.860,  'oman': 1.860,  'ombg': 1.848,  'ObsError': 0.5},
                 'count':   {'ObsValue': 944,    'oman': 944,    'ombg': 944,    'ObsError': 944}
            },
            (500, 20000): {
                 'mean':    {'ObsValue': -1.910,  'oman': -1.910,  'ombg': -1.890, 'ObsError': 0.5},
                 'median':  {'ObsValue': -1.913,  'oman': -1.913,  'ombg': -1.892, 'ObsError': 0.5},
                 'StdDev':  {'ObsValue': 0.00539, 'oman': 0.005,   'ombg': 0.005,  'ObsError': 0.0},
                 'minimum': {'ObsValue': -1.916,  'oman': -1.916,  'ombg': -1.895, 'ObsError': 0.5},
                 'maximum': {'ObsValue': -1.902,  'oman': -1.902,  'ombg': -1.882, 'ObsError': 0.5},
                 'rms':    {'ObsValue': 1.910,  'oman': 1.910,   'ombg': 1.890,  'ObsError': 0.5},
                 'count':   {'ObsValue': 129,     'oman': 129,     'ombg': 129,    'ObsError': 129}
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
        
        # 2. Iterate through each statistic name (e.g., 'mean')
        for stat_name, group_map in stats_map.items():
            
            # 3. Iterate through each group (e.g., 'ObsValue', 'oman')
            for group_name, exp_val in group_map.items():
                
                # 4. Find the matching record in the flat list of HarvestedData
                # We match on: ocean_depth_bins, statistics, and group
                match = next((
                    d for d in harvested_results 
                    if d.ocean_depth_bins == depth_bin 
                    and d.statistics == stat_name 
                    and d.group == group_name
                ), None)

                # Assertion: Did we even find the record?
                assert match is not None, (
                    f"MISSING DATA: No record found for "
                    f"Bin: {depth_bin}, Stat: {stat_name}, Group: {group_name}"
                )

                # Assertion: Is the value numerically correct?
                act_val = float(match.value)
                assert math.isclose(act_val, exp_val, abs_tol=tolerance), (
                    f"VALUE MISMATCH in Bin {depth_bin}!\n"
                    f"  Stat:  {stat_name}\n"
                    f"  Group: {group_name}\n"
                    f"  Got:   {act_val}\n"
                    f"  Exp:   {exp_val}"
                )

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
                'statistics': STANDARD_STATS,
                'variables': [meta['components']['variables']], 
                'QC_threshold': meta['QC_threshold'],
                'ocean_depth_bins': STANDARD_BINS,
            }

            all_data = harvest(config_dict)

            assert isinstance(all_data, list) and len(all_data) > 0, "No data harvested."

            verify_filename_components(all_data[0], meta['components'])
            verify_statistics(all_data, meta['expected_stats'], meta['QC_threshold'])
            
            print(f"RESULT: {filename} [PASS]")
            
        except AssertionError as e:
            print(f"RESULT: {filename} [FAIL] -> {e}")
        except Exception as e:
            print(f"RESULT: {filename} [ERROR] -> {e}")

if __name__ == '__main__':
    test_main()
