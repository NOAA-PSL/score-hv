# score-hv/README.md
## Summary
Python package used to harvest metrics from reanalysis data.
This repositority is a standalone Python package that can be used as a part of
a larger workflow (e.g., with the score-db and score-monitoring repositories).

## Setup and installation
The repository can be downloaded using git:

```sh
git clone https://github.com/NOAA-PSL/score-hv.git
```

For testing and development, we recommend creating a new python environment 
(e.g., using [mamba](https://mamba.readthedocs.io/en/latest/index.html) as shown below or other options such as conda). To 
install the required dependencies into a new environment using the micromamba 
command-line interface, run the following after installing mamba/micromamba:

```sh
micromamba create -f environment.yml; micromamba activate score-hv-default-env
```

Depending on your use case, you can install score-hv using one of three methods using 
[pip](https://pip.pypa.io/en/stable/),

`pip install . # default installation into active environment`

`pip install -e . # editable installation into active enviroment, useful for development`

`pip install -t [TARGET_DIR] --upgrade . # target installation into TARGET_DIR, useful for deploying for cylc workflows (see https://cylc.github.io/cylc-doc/stable/html/tutorial/runtime/introduction.html#id3)`

Verify the installation by running the unit test suite. To run the full test 
suite, download the test data by running the `get_unit_test_data.sh` bash script and run `pytest` from within the top of the score-hv repository. There are no expected test failures.

```sh
score-hv/$ ./get_unit_test_data.sh
score-hv/$ pytest
```

## Harvesting metric data with score-hv
score-hv takes in either a yaml or dictionary via harvester_base.py which specifies the harvester to call, 
input data files and other inputs to the harvester (such as which variables and
statistics to harvest). Example input dictionaries for each harvester are provided in the Available Harvesters section below. Calls can be made directly in the command line or by importing the score-hv module and calling harvester_base.harvest([havester_config filename / config dictionary]). 

For example, the following dictionary could be used to request the global, gridcell area weighted statistics for the temporally (in this case daily)
weighted netcdf gridcell area data for tmp2m returning the mean, variance, minimum, and maximum.

Example input dictionary: 
```sh
VALID_CONFIG_DICT = {'harvester_name': 'daily_bfg',
                        'filenames' : [
                            '/filepath/tmp2m_bfg_2023032100_fhr09_control.nc',
                            '/filepath/tmp2m_bfg_2023032106_fhr06_control.nc',
                            '/filepath/tmp2m_bfg_2023032106_fhr09_control.nc',
                            '/filepath/tmp2m_bfg_2023032112_fhr06_control.nc',
                            '/filepath/tmp2m_bfg_2023032112_fhr09_control.nc',
                            '/filepath/tmp2m_bfg_2023032118_fhr06_control.nc',
                            '/filepath/tmp2m_bfg_2023032118_fhr09_control.nc',
                            '/filepath/tmp2m_bfg_2023032200_fhr06_control.nc'],
                     'statistic': ['mean', 'variance', 'minimum', 'maximum'],
                     'variable': ['tmp2m']}
```

A request dictionary must provide the harvester_name and filenames. Supported 
harvester_name(s) are provided below, and each harvester may have additional 
input options or requirements. 


## Available Harvesters

### inc_logs
increment descriptive statistics from log files

**Expected file format**: log output file

Returns the following named tuple: 
```sh
HarvestedData = namedtuple('HarvestedData', ['logfile',
                                             'cycletime',
                                             'statistic',
                                             'variable',
                                             'value', 
                                             'units'])
```

#### Available statistics
```sh
VALID_STATISTICS = ('mean', 'RMS')
```

#### Available variables
```sh
VALID_VARIABLES = ['pt_inc', 's_inc', 'u_inc', 'v_inc', 'SSH', 'Salinity',
                   'Temperature', 'Speed of Currents', 'o3mr_inc', 'sphum_inc',
                   'T_inc', 'delp_inc', 'delz_inc']
```
#### Example dictionary input
```sh
VALID_CONFIG_DICT = {'harvester_name': 'inc_logs',
                     'filename' : '/filepath/calc_atm_inc.out',
                     'cycletime': datetime(2019,3,21,0),
                     'statistic': ['mean', 'RMS'],
                     'variable': ['o3mr_inc', 'sphum_inc', 'T_inc', 'u_inc', 'v_inc',
                                  'delp_inc', 'delz_inc']}
```

### daily_bfg
The daily_bfg harvester pulls data from the background forecast (bfg) data files. It calculates daily, area-weighted statistics from the provided files, optionally over user-defined regions and surface masks.

A netcdf file containing area grid cell weights is required. It is included in the repository (`src/score_hv/data/`) for the supported resolution.

The daily_bfg harvester returns a list of the following named tuple, with one record per variable, region, surface mask and statistic:
```sh
HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'segment',
                                             'statistic',
                                             'variable',
                                             'value',
                                             'units',
                                             'mediantime',
                                             'longname',
                                             'surface_mask',
                                             'region'])
```

#### Input dictionary keys
| Key | Required | Description |
|---|---|---|
| `filenames` | yes | List of bfg netcdf files for one day. |
| `statistic` | yes | List of statistics from `['mean', 'variance', 'minimum', 'maximum', 'integral']`. |
| `variable` | yes | List of variables (see below). |
| `segment` | no | Model segment of the files. `background`, `first guess`, `first_guess`, `fg` or `predictor` give `'background'`; `analysis`, `corrector`, `an` or `replay` give `'analysis'`; `None`/`'none'` (the default) gives `None`. Other values raise a `ValueError`. |
| `resolution` | no | Grid resolution of the files. Only `'1536x768'` (the default) is supported; other values raise a `ValueError`. |
| `regions` | no | Dictionary of named regions (see below). Defaults to one `'global'` region. |
| `surface_mask` | no | A mask name or list of mask names from `['none', 'land', 'water', 'sea', 'ice']`. A record is produced for each mask. Defaults to no user mask; invalid masks raise a `ValueError`. |

#### Available Harvester variables:
```sh
VALID_VARIABLES = (
    'icec',        # sea ice concentration (ice=1; no ice=2)
    'icetk',       # sea ice thickness (m)
    'lhtfl_ave',   # surface latent heat flux (W/m**2)
    'shtfl_ave',   # surface sensible heat flux (W/m**2)
    'dlwrf_ave',   # surface downward longwave flux (W/m**2)
    'dswrf_ave',   # averaged surface downward shortwave flux (W/m**2)
    'ulwrf_ave',   # surface upward longwave flux (W/m**2)
    'uswrf_ave',   # averaged surface upward shortwave flux (W/m**2)
    'netrf_avetoa',# top of atmosphere net radiative flux (SW and LW) (W/m**2)
    'netef_ave',   # surface energy balance (W/m**2)
    'nsst',        # near sea surface temperature (K), using tref over the ocean only
    'prateb_ave',  # bucket surface precip rate (mm weq. s^-1)
    'prate_ave',   # surface precip rate (mm weq. s^-1)
    'pressfc',     # surface pressure (Pa)
    'snowc_ave',   # snow cover - GFS lsm
    'snod',        # surface snow depth (m)
    'soilm',       # total column soil moisture content (mm weq.)
    'soilt4',      # soil temperature unknown layer 4 (K)
    'sst',         # sea surface temperature (K), using tmpsfc over the ocean only
    'tg3',         # deep soil temperature (K)
    'tmp2m',       # 2m (surface air) temperature (K)
    'tsnowp',      # accumulated surface snow (kg/m**2)
    'ulwrf_avetoa',# top of atmosphere upward longwave flux (W m^-2)
    'weasd',       # surface snow water equivalent (kg/m**2)
)
```
The variable netrf_avetoa is calculated from the bfg variables:

       netrf_avetoa = dswrf_avetoa - uswrf_avetoa - ulwrf_avetoa

The variable netef_ave is calculated from the bfg variables:

       netef_ave = dswrf_ave + dlwrf_ave - ulwrf_ave - uswrf_ave - shtfl_ave - lhtfl_ave

#### Regions
Each region is given by name with its bounds in degrees:
```sh
'regions': {'<region name>': {'north_lat': <float>, 'south_lat': <float>,
                              'west_long': <float>, 'east_long': <float>}}
```
- Latitudes range from -90 to 90 and longitudes from 0 to 360 degrees east (the bfg grid is circular in longitude). Bounds are inclusive.
- If `east_long <= west_long`, the region crosses the prime meridian, e.g. `{'west_long': 343, 'east_long': 51}`.
- A missing bound takes its global default (`north_lat=90`, `south_lat=-90`, `west_long=0`, `east_long=360`).
- `west_lon` and `east_lon` are accepted as aliases of `west_long` and `east_long`. Any other key raises a `KeyError`.
- The region named `'global'` is treated as the full globe in the area-weighted statistics.

#### Surface masks
Some variables are always masked to their valid surface, before any user mask:
- `soilm`, `soilt4`, `tg3`, `snod`, `tsnowp`, `weasd`: land cells, excluding land ice (from the soil type).
- `icetk`: cells with sea ice (`icec > 0`).
- `sst`, `nsst`: open water cells (no land, no ice).

A user `surface_mask` is applied on top of this: `land`, `water` (or its alias `sea`), `ice`, or `none` (only the automatic masking). The masked statistics are weighted by both the grid cell area and the fraction of the cell covered by the selected surface.

#### Returned Results
- **segment:** the interpreted model segment (`'background'`, `'analysis'` or `None`).
- **value:** the requested statistic. `mean`, `variance` and `integral` are area weighted; `minimum` and `maximum` are taken over the daily-mean grid cells in the region.
- **units / longname:** taken from the variable attributes in the bfg files (`'None'` if missing), or set by the harvester for derived variables.
- **mediantime:** the median of the temporal midpoints of the file time stamps (a python `datetime`).
- **surface_mask:** the user mask name, or `None`.
- **region:** a dictionary `{'name': <region name>, 'latitude': <latitudes>, 'longitude': <longitudes>}` with the grid coordinates inside the region.

#### Example Input Dictionary
Example input dictionary for calling the daily_bfg harvester:
```sh
VALID_CONFIG_DICT = {'harvester_name': 'daily_bfg',
                     'filenames' : [
                         '/filepath/bfg_2023032100_fhr09_control.nc',
                         '/filepath/bfg_2023032106_fhr06_control.nc',
                         '/filepath/bfg_2023032106_fhr09_control.nc',
                         '/filepath/bfg_2023032112_fhr06_control.nc',
                         '/filepath/bfg_2023032112_fhr09_control.nc',
                         '/filepath/bfg_2023032118_fhr06_control.nc',
                         '/filepath/bfg_2023032118_fhr09_control.nc',
                         '/filepath/bfg_2023032200_fhr06_control.nc'],
                     'segment': 'background',
                     'statistic': ['mean', 'variance', 'minimum', 'maximum', 'integral'],
                     'variable': ['tmp2m', 'soilm'],
                     'regions': {
                         'global': {'north_lat': 90, 'south_lat': -90, 'west_long': 0, 'east_long': 360},
                         'africa': {'north_lat': 37, 'south_lat': -35, 'west_long': 343, 'east_long': 51},
                     },
                     'surface_mask': ['land', 'water']}
```

### obs_info_log
observation information for pressure, specific humidity, temperature, height, wind components, precipitable h2o, and relative humidity

**Expected file format**: text file 

File format generated from NCEPlibs cmpbqm command output 

Required dictionary inputs: 'variable'

#### Available variables 
Valid 'variable' options: 'Temperature', 'Pressure', 'Specific Humidity', 'Relative Humidity', 'Height', 'Wind Components', 'Precipitable H20' 

#### Example input dictionary
```sh
VALID_CONFIG_DICT_TEMP = {
    'harvester_name': 'obs_info_log',
    'filename': '/filepath/log_cmpbqm.txt',
    'variable': 'TEMPERATURE'
}
```


