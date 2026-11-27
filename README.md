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
The daily_bfg harvester pulls data from the background forecast data files. It calculates daily statistics from the provided files.

A netcdf file containing area grid cell weights is required.  This file should be included in the github repository with the download found in the data folder.

The daily_bfg harvester returns the following named tuple:
```sh
HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'statistics',
                                             'variable',
                                             'value',
                                             'units',
                                             'mediantime',
                                             'longname',
                                             'surface_mask', 
                                             'region'])
```

The example filenames are listed in the dictionary example below.

#### Available Harvester statistics:
A list of statistics.  Valid statistics are ['mean', 'variance', 'minimum', 'maximum']

#### Available Harvester variables:
```sh
VALID_VARIABLES  = (
                    'lhtfl_ave',# surface latent heat flux (W/m**2)
                    'shtfl_ave', # surface sensible heat flux (W/m**2)
                    'dlwrf_ave', # surface downward longwave flux (W/m**2)
                    'dswrf_ave', # averaged surface downward shortwave flux (W/m**2)
                    'ulwrf_ave', # surface upward longwave flux (W/m**2)
                    'uswrf_ave', # averaged surface upward shortwave flux (W/m**2)
                    'netrf_avetoa', #top of atmosphere net radiative flux (SW and LW) (W/m**2)
                    'netef_ave', #surface energy balance (W/m**2)
                    'prateb_ave', # surface precip rate (mm weq. s^-1)
                    'soil4', # liquid soil moisture at layer-4 (?)
                    'soilm', # total column soil moisture content (mm weq.)
                    'soilt4', # soil temperature unknown layer 4 (K)
                    'tg3', # deep soil temperature (K)
                    'tmp2m', # 2m (surface air) temperature (K)
                    'ulwrf_avetoa', # top of atmos upward longwave flux (W m^-2)
                    )
```
The variable netrf_avetoa is calculated from:

       dswrf_avetoa:averaged surface - downward shortwave flux
       uswrf_avetoa:averaged surface upward shortwave flux
       ulwrf_avetoa:surface upward longwave flux

       Theses variables are found in the bfg control files.
       netrf_avetoa = dswrf_avetoa - uswrf_avetoa - ulwrf_avetoa

The variable netef_ave is calculated from:

       dswrf_ave : averaged surface downward shortwave flux
       dlwrf_ave : surface downward longwave flux
       ulwrf_ave : surface upward longwave flux
       uswrf_ave : averaged surface upward shortwave flux
       shtfl_ave : surface sensible heat flux
       lhtfl_ave : surface latent heat flux

       These variables are found in the bfg control files.
       netef_ave = dswrf_ave + dlwrf_ave - ulwrf_ave - uswrf_ave - shtfl_ave - lhtfl_ave


#### Returned Results
Value:  The value entry of the harvested tuple contains the calculated value of valid 
        statistic that was requested by the user.
           
Units:  The units entry of the harvested tuple contains the untis associated with the
        requested variable from the BFG Netcdf file.  If no units were given on the 
        file then a value of None is returned.

Mediantime: The mediantime of the harvested tuple is calculated from the 
            endpoints of the variable time stamps on the BFG Netcdf file.

Longname: The long name entry of the harvested tuple is taken from the variable
          long name on the BFG Netcdf file.

Region: This entry of the harvested tuple is a nested dictionary. The region dictionary 
        contains the following information.
        regon name: this is a name given to the region by the user.  It is a required 
                    key word.
        latitude_range(min_latitude,max_latitude) 
        longitude range(east_lon,west_lon).
         The following nested dictionaries for region are accepted:
                    
              user name of region': {'latitude_range' : (min_lat,max_lat)}
              The user has not specified a longitude range.  The default will be applied. 
              default longitude is (360, 0)
              NOTE:  The longitude values on the bfg files are grid_xt : 0 to 359.7656 by 0.234375 degrees_E  circular

              'user name of region': {'longitude_range' : (min_lon,max_lon}
               The user has not specified a latitude_range.  The default will be applied.
               default latitude is (-90,90)
               NOTE:  The latitude values on the bfg files are grid_yt : 89.82071 to -89.82071 degrees_N
                    
               examples: 'region' : {
                                     'conus': {'latitude_range': (24.0, 49.0), 'longitude_range': (294.0, 235.0)},
                                     'western_hemis': 'longitude_range': (200,360)},
                                     'southern hemis': 'latitude_range': (20,-90)}
                                    }
                    
                  
The daily_bfg.py file returns the following for each variable and statistic requested.
```sh
(HarvestedData(
                                      self.config.harvest_filenames,
                                       statistic, 
                                       variable,
                                       np.float32(value),
                                       units,
                                       dt.fromisoformat(median_cftime.isoformat()),
                                       longname,
                                       user_regions))
```
#### Example Input Dictionary
Example input dictionary for calling the daily_bfg harvester: 
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


### soca_diags
Descriptive statistics of the observations in SOCA/JEDI ocean observation-space
diagnostic files ("ocean diags"), e.g. the files in
`gdas.YYYYMMDD/HH/analysis/ocean/diags/`. One record is returned for every
requested statistic of every variable, depth bin and data group (`ObsValue`,
`oman`, `ombg`, `ObsError`) found in each file.

**Expected file format**: IODA netCDF with a `MetaData` group holding `dateTime`
(and `depth` for profile data), an `ObsValue` group, and optionally the `oman`,
`ombg`, `ObsError`, `EffectiveQC0` and `EffectiveQC1` groups.

#### Supported file names
An optional `.YYYYMMDDHH` cycle may precede the `.nc`/`.nc4` extension, e.g.
`wod_t_pfl.2023080612.nc`.
```
[rads_]adt[_<source>]_<altimeter>                             e.g. adt_glore_j3.nc, rads_adt_j3.nc
icec_<sensor|product>[_<platform>][_<level>][_<north|south|nh|sh>]
                                                              e.g. icec_amsr2_north.nc, icec_nsidc_sh.nc
sst_<sensor|product>[_<platform>][_<level>][_<region>]        e.g. sst_viirs_n20_l3u.nc, sst_avhrrf_mb_l3u.nc, sst_odyssea.nc
sss_<sensor>[_<platform>][_<level>]                           e.g. sss_smap_l2.nc
wod_<t|s>_<platform>                                          e.g. wod_t_pfl.nc, wod_s_ctd.nc
insitu_[<temp|salt>_]<profile|surface>_<platform>             e.g. insitu_profile_argo.nc4, insitu_temp_surface_drifter.nc
icoads_<...>
```
`sst_avhrrf_<ma|mb|mc>` is reported as sensor `avhrr` and satellite
`metop-a|b|c`. For WOD and insitu files the sensor is the platform (`pfl`,
`argo`, `drifter`, ...) and the satellite is `None`.

Files with any other name (including the `moana`, `pirata_t`, `rama_t` and
`tao_t` mooring files, and the GDASApp `nasa_swk` and `icefb_*` obs spaces) are
skipped with a logged warning. The record metadata
parsed from the current GDAS ocean diag file names is:

| File name | sensor | satellite | level | file_region |
|---|---|---|---|---|
| adt_glore_3a.nc, adt_glore_3b.nc | Synthetic aperture Radar Altimeter | Sentinel-3A, Sentinel-3B | None | global |
| adt_glore_6a.nc | Poseidon 4 | Sentinel-6A | None | global |
| adt_glore_c2.nc | SAR Interferometer Radar Altimeter | cryosat2 | None | global |
| adt_glore_j3.nc | Poseidon 3B | jason3 | None | global |
| icec_amsr2_north.nc, icec_amsr2_south.nc | amsr2 | gcom-w1 | None | nh, sh |
| icec_nsidc_nh.nc, icec_nsidc_sh.nc | ssmis | dmsp | None | nh, sh |
| sst_odyssea.nc | multiple | ODYSSEA | l3 | global |
| wod_t_\<platform\>.nc, wod_s_\<platform\>.nc | \<platform\> (apb, ctd, drb, pfl, xbt, ...) | None | None | global |

#### Request keys
- `filenames`: list of diag file paths (required)
- `statistics`: list of statistics, default `['mean']`
- `variables`: list of variables, default (`[]` or missing) is every variable in each file
- `QC_threshold`: observations are used when their EffectiveQC flag is
  `<= QC_threshold` (default `0`); `None` turns QC filtering off. `oman` is
  filtered with `EffectiveQC1` (the analysis QC), and `ObsValue`, `ombg` and
  `ObsError` with `EffectiveQC0` (the background QC). If the preferred group is
  missing, another `EffectiveQC*` group is used; if none has the variable, a
  warning is logged and the group is not QC filtered.
- `ocean_depth_bins`: depth bins in meters (positive down), either as increasing
  bin edges, e.g. `[0, 20, 100]` for the bins `(0, 20)` and `(20, 100)`, or as
  `[lo, hi]` pairs, e.g. `[[0, 20], [0, 100]]` (pairs may overlap). Bins are
  half open, `lo <= depth < hi`, and observations without a depth are in no
  bin. Default (`None` or `[]`) is no depth binning. Files without
  `MetaData/depth` (e.g. ADT, ICEC and SST) are never binned.

Missing values are dropped separately for each data group. Unknown statistics or
variables raise a `KeyError`, an invalid `QC_threshold` or `ocean_depth_bins` a
`ValueError`, and a missing file a `FileNotFoundError`.

#### Available statistics
```python
VALID_STATISTICS = ('mean', 'median', 'StdDev', 'minimum', 'maximum', 'rms', 'count')
STATISTIC_ALIASES = {'RMS': 'rms', 'n': 'count', 'nobs': 'count'}
```
`StdDev` is the sample standard deviation (ddof=1) and `rms` is
`sqrt(mean(x**2))`; statistics are computed in double precision. A record with
no observations reports only `count` (0), and `StdDev` is not reported for a
single observation.

#### Available variables
```python
VALID_VARIABLES = ('seaSurfaceTemperature',
                   'seaIceFraction',
                   'absoluteDynamicTopography',
                   'seaSurfaceSalinity',
                   'waterTemperature',
                   'salinity')
VARIABLE_ALIASES = {'sst': 'seaSurfaceTemperature', 'icec': 'seaIceFraction'}
```

#### Returned results
```python
HarvestedData = namedtuple('HarvestedData', ['filenames',
                                             'sensor',
                                             'satellite',
                                             'level',
                                             'variables',
                                             'group',
                                             'longname',
                                             'units',
                                             'statistics',
                                             'value',
                                             'filetime',
                                             'mediantime',
                                             'file_region',
                                             'QC_threshold',
                                             'ocean_depth_bins'])
```
- `group`: the data group, one of `ObsValue`, `oman`, `ombg` or `ObsError`
- `filetime`: a `datetime.datetime`, the analysis cycle of the file, the same
  for every record of the file. It is taken from the first available of the
  `.YYYYMMDDHH` cycle in the file name, a `<run>.YYYYMMDD/HH` directory in the
  file path (e.g. `gdas.20230201/12/analysis/ocean/diags/`), and the
  `YYYYMMDDHH` `date_time` global attribute. Otherwise the median time of the
  whole file is rounded to the nearest synoptic time (00, 06, 12 or 18 UTC),
  which assumes the assimilation window is centered on a 6-hourly cycle. A file
  with none of these raises a `ValueError`.
- `mediantime`: a `datetime.datetime`, the median `MetaData/dateTime` of the
  observations used for the record, floored to the second. Records without
  observations use the median time of the whole file (or `filetime` if the
  file has no valid times).
- `units`: the units attribute of the `ObsValue` variable, with Celsius
  spellings reported as `DegC` and Kelvin spellings as `DegK`. Without a units
  attribute: `DegC` for WOD temperature, `PSS` for WOD salinity, `1` for
  `seaIceFraction`, `m` for ADT, `psu` for SSS, and `DegC` or `DegK` for SST
  (from the magnitude of the values).
- `longname`: the variable name, except for WOD files (`waterTemperature` for
  temperature and `Practical Salinity Scale` for salinity)
- `ocean_depth_bins`: the `(lo, hi)` depth bin of the record, or `None`

#### Example input dictionary
```python
VALID_CONFIG_DICT = {'harvester_name': 'soca_diags',
                     'filenames': ['/filepath/diags/wod_t_pfl.nc',
                                   '/filepath/diags/adt_glore_j3.nc'],
                     'statistics': ['mean', 'rms', 'count'],
                     'variables': ['waterTemperature', 'absoluteDynamicTopography'],
                     'QC_threshold': 0,
                     'ocean_depth_bins': [0, 100, 500]}
```
which returns records such as
```python
HarvestedData(filenames='/filepath/diags/wod_t_pfl.nc', sensor='pfl', satellite=None,
              level=None, variables='waterTemperature', group='oman',
              longname='waterTemperature', units='DegC', statistics='rms',
              value=0.16662825309021626,
              filetime=datetime.datetime(2023, 2, 1, 12, 0),
              mediantime=datetime.datetime(2023, 2, 1, 11, 48, 46),
              file_region='global', QC_threshold=0, ocean_depth_bins=(0, 100))
```

#### Test data
`tests/test_soca_diags_unit.py` writes its own small diag files and needs no
test data. `tests/test_soca_diags_sfs_v11.py` checks the statistics of the 17
supported SFS_v11 ocean diag files from
`s3://noaa-reanalyses-pds/analyses/scout_runs/exper/SFS_v11/2023/02/2023020112/gdas.20230201/12/analysis/ocean/diags/`.
`get_unit_test_data.sh` downloads copies of them from
`s3://noaa-reanalyses-pds/score_suite/test_data/sfs_v11/` to `tests/data/sfs_v11/`.
