import yaml
TEST_REGISTRY = {
    'wod_t_ctd.nc': {
        'QC_threshold': 0.0,
        'longname': 'Temperature',
        'units': 'DegC',
        'variable': 'waterTemperature',
        'ocean_depth_bins': [(0, 20), (20, 100), (100, 500), (500,20000)],
        'components': {
            'variables': 'waterTemperature',
            'sensor': 'ctd',
            'satellite': None,
            'level': None
        },
        'expected_stats': {
             (0, 20): {
                 'mean':    {'ObsValue': -0.4939, 'oman': -0.3808, 'ombg': -0.126, 'ObsError': 0.5},
                 'median':  {'ObsValue': -0.5570, 'oman': -0.2889, 'ombg': -0.1516, 'ObsError': 0.5},
                 'StdDev':  {'ObsValue': 0.1086, 'oman':  0.4398, 'ombg': 0.1395, 'ObsError': 0.0},
                 'minimum': {'ObsValue': -0.5870, 'oman': -1.0777, 'ombg': -0.3383, 'ObsError': 0.5},
                 'maximum': {'ObsValue': -0.3300, 'oman': 0.2956,  'ombg': 0.1766,  'ObsError': 0.5},
                 'rmse':    {'ObsValue': 0.5055,  'oman': 0.5791,  'ombg': 0.1875,  'ObsError': 0.5},
                 'count':   {'ObsValue': 63,      'oman': 63,      'ombg': 63,      'ObsError': 63}
            },
            (20, 100): {
                 'mean':    {'ObsValue': -1.561, 'oman': -1.0075, 'ombg': -1.075, 'ObsError': 0.5},
                 'median':  {'ObsValue': -1.703, 'oman': -1.667, 'ombg': -1.663, 'ObsError': 0.5},
                 'StdDev':  {'ObsValue': 0.3245, 'oman': 0.779,  'ombg': 0.705,  'ObsError': 0.0},
                 'minimum': {'ObsValue': -1.754, 'oman': -1.754, 'ombg': -1.750, 'ObsError': 0.5},
                 'maximum': {'ObsValue': -0.423, 'oman': 0.304,  'ombg': 0.190,  'ObsError': 0.5},
                 'rmse':    {'ObsValue': 1.594,  'oman': 1.273,  'ombg': 1.284,  'ObsError': 0.5},
                 'count':   {'ObsValue': 243,    'oman': 243,    'ombg': 243,    'ObsError': 243}
            },
            (100, 500): {
                 'mean':    {'ObsValue': -1.859, 'oman': -1.859, 'ombg': -1.848, 'ObsError': 0.5},
                 'median':  {'ObsValue': -1.881, 'oman': -1.881, 'ombg': -1.870, 'ObsError': 0.5},
                 'StdDev':  {'ObsValue': 0.0513, 'oman': 0.051,  'ombg': 0.048,  'ObsError': 0.0},
                 'minimum': {'ObsValue': -1.915, 'oman': -1.915, 'ombg': -1.897, 'ObsError': 0.5},
                 'maximum': {'ObsValue': -1.694, 'oman': -1.694, 'ombg': -1.690, 'ObsError': 0.5},
                 'rmse':    {'ObsValue': 1.860,  'oman': 1.860,  'ombg': 1.848,  'ObsError': 0.5},
                 'count':   {'ObsValue': 944,    'oman': 944,    'ombg': 944,    'ObsError': 944}
            },
            (500, 20000): {
                 'mean':    {'ObsValue': -1.910,  'oman': -1.910,  'ombg': -1.890, 'ObsError': 0.5},
                 'median':  {'ObsValue': -1.913,  'oman': -1.913,  'ombg': -1.892, 'ObsError': 0.5},
                 'StdDev':  {'ObsValue': 0.00539, 'oman': 0.005,   'ombg': 0.005,  'ObsError': 0.0},
                 'minimum': {'ObsValue': -1.916,  'oman': -1.916,  'ombg': -1.895, 'ObsError': 0.5},
                 'maximum': {'ObsValue': -1.902,  'oman': -1.902,  'ombg': -1.882, 'ObsError': 0.5},
                 'rmse':    {'ObsValue': 1.910,  'oman': 1.910,   'ombg': 1.890,  'ObsError': 0.5},
                 'count':   {'ObsValue': 129,     'oman': 129,     'ombg': 129,    'ObsError': 129}
            }
        }
   }  
}    

print("YAML file created successfully!")
