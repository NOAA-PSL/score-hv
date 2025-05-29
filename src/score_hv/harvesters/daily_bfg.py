#!/usr/bin/env python

import ast
import copy
import os
import sys
import warnings
from datetime import datetime as dt
from pathlib import Path
from collections import namedtuple
from dataclasses import dataclass, field

import cftime
import numpy as np
import xarray as xr
from netCDF4 import MFDataset

from score_hv.config_base import ConfigInterface
from score_hv import stats_utils
from score_hv.region_utils import GeoRegionsCatalog
from score_hv.mask_utils import MaskCatalog
from score_hv.variable_utils import VarUtilsCatalog

HARVESTER_NAME = 'daily_bfg'
VALID_STATISTICS = ('mean', 'variance', 'minimum', 'maximum', 'integral')
VALID_REGION_BOUND_KEYS = ('south_lat', 'north_lat', 'west_lon', 'east_lon')
VALID_RESOLUTIONS = ('1536x768')

DEFAULT_REGION = {
    'global': {
        'north_lat': 90.0,
        'south_lat': -90.0,
        'west_lon': 0.0,
        'east_lon': 360.0
    }
}

"""
VALID_VARIABLES are the variables of interest that come from the 
background forecast data.
"""
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
    'nsst',        # near sea surface temperature(K), using tref over the ocean 
                   # only
    'prateb_ave',   # bucket surface precip rate (mm weq. s^-1)
    'prate_ave',   # surface precip rate (mm weq. s^-1)
    'pressfc',     # surface pressure (Pa)
    'snowc_ave',   # snow cover - GFS lsm
    'snod',        # surface snow depth (m)
    'soilm',       # total column soil moisture content (mm weq.)
    'soilt4',      # soil temperature unknown layer 4 (K)
    'sst',         # sea surface temperature (K), using tmpsfc over the ocean 
                   # only
    'tg3',         # deep soil temperature (K)
    'tmp2m',       # 2m (surface air) temperature (K)
    'tsnowp',      # accumulated surface snow (kg/m**2)
    'ulwrf_avetoa', # top of atmosphere upward longwave flux (W m^-2)
    'weasd',       # surface snow water equivalent (kg/m**2)
)

VALID_SEGMENTS = ('background', 'first guess', 'first_guess', 'fg', 'predictor',
                  'analysis', 'corrector', 'an', 'replay', 'none', 'None', None)

HarvestedData = namedtuple(
    'HarvestedData', [
        'filenames',
        'segment',
        'statistic',
        'variable',
        'value',
        'units',
        'mediantime',
        'longname',
        'surface_mask',
        'region'
    ]
)

def get_median_cftime(xr_dataset):
    """Returns the median time from the given xarray dataset.

    The dataset ("xr_dataset") is expected to have a "time" dimension, where
    each timestamp represents the endpoint of a time period. The function
    calculates the median time of the entire dataset using the temporal 
    midpoints.

    Parameters:
    -----------
    xr_dataset : xarray.Dataset
        The input dataset containing a "time" variable.

    Returns:
    --------
    median_cftime : cftime.Datetime
        The median time calculated from the dataset.
    """
    temporal_endpoints = sorted(np.array([
        cftime.date2num(time, 'hours since 1951-01-01 00:00:00')
        for time in xr_dataset['time']
    ]))
    
    if len(temporal_endpoints) > 1:
        # Estimate the time step if there is more than 1 timestamp
        temporal_midpoints = temporal_endpoints - np.gradient(
                                                     temporal_endpoints) / 2.0
        median_cftime = cftime.num2date(
            np.median(temporal_midpoints), 'hours since 1951-01-01 00:00:00'
        )
    else:
        median_cftime = cftime.num2date(
            np.median(temporal_endpoints), 'hours since 1951-01-01 00:00:00'
        )
    
    return median_cftime

def check_region_domain(coordinate_array_0, coordinate_array_1, region_name):
    if not coordinate_array_0.equals(coordinate_array_1):
        raise ValueError(
            f"Unequal region domains for {region_name}!\n"
            f"first coordinate array: {coordinate_array_0}\n"
            f"second coordinate array: {coordinate_array_1}"
        )

@dataclass
class DailyBFGConfig(ConfigInterface):
    """Configuration class to handle the setup and validation of daily BFG 
    parameters for the harvest process.
    """
    
    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
        """Post-initialization method to set the configuration."""
        self.set_config()

    def set_config(self):
        """Set configuration variables from the given dictionary."""
        self.harvest_filenames = self.config_data.get('filenames')
        self.set_stats()
        self.set_segment()
        self.set_variables()
        self.set_surface_mask()
        self.set_regions()
        self.set_gridcell_area_data_path()

    def set_segment(self, analysis_segment_safe_list=['analysis',
                                                      'corrector',
                                                      'an',
                                                      'replay'],
                    background_segment_safe_list=['background', 
                                                  'first guess',
                                                  'first_guess',
                                                  'fg',
                                                  'predictor']):
        """Set the representing segment of the input bfg files ("background"
        versus "analysis"). The segment, which cannot be determined by the
        harvester itself, will be passed through as a harvested value.
        """
        segment = self.config_data.get('segment')
        
        if segment not in VALID_SEGMENTS:
            msg = (
                f'"{segment}" is not an interpretable model segment '
                f'type relevant to the bfg netCDF files. Please reconfigure '
                f'the input dictionary using only the following model segment '
                f'types: {VALID_SEGMENTS}'
            )
            raise KeyError(msg)
        
        elif segment in background_segment_safe_list:
            self.segment = 'background'
        elif segment in analysis_segment_safe_list:
            self.segment = 'analysis'
        else:
            self.segment = None
            warnings.warn(f'received model segment "{segment}" but this is '
                          f'neither understood as a background nor an '
                          f'analysis model segment type. Proceeding with no '
                          f'model segment type.')
                
    def set_variables(self):
        """Set the variables specified by the config dictionary.
        Raises:
            KeyError: If any of the variables are not in the valid list of 
                      background forecast data variables.
        """
        self.variables = self.config_data.get('variable', [])
        for var in self.variables:
            if var not in VALID_VARIABLES:
                msg = (
                    f"'{var}' is not a supported variable to harvest from the "
                    f"background forecast data. Please reconfigure the input "
                    f"dictionary using only the following variables: "
                    f"{VALID_VARIABLES!r}"
                )
                raise KeyError(msg)

    def set_surface_mask(self):
        """Set the surface mask from the configuration data."""
        self.surface_mask = self.config_data.get('surface_mask')

    def set_regions(self):
        """
        Set the regions specified by the config dictionary or use the default 
        region if none are provided.
        """
        self.regions = self.config_data.get('regions', DEFAULT_REGION)
        if self.regions is DEFAULT_REGION:
            print(f"Setting a default global region {self.regions}")

    def set_stats(self):
        """Set the statistics specified by the config dictionary.
        Raises:
            KeyError: If any of the statistics are not in the valid list of 
                      statistics for background forecast data.
        """
        self.stats = self.config_data.get('statistic', [])
        for stat in self.stats:
            if stat not in VALID_STATISTICS:
                msg = (
                    f"'{stat}' is not a supported statistic to harvest from "
                    f"daily mean background forecast data. Please reconfigure "
                    f"the input dictionary using only the following " 
                    f"statistics: {VALID_STATISTICS!r}"
                )
                raise KeyError(msg)
                
    def set_gridcell_area_data_path(self, default_resolution='1536x768'):
        """Set the path to the gridcell area data file.
        """
        self.resolution = self.config_data.get('resolution')
        
        if self.resolution == None:
            self.resolution = default_resolution
        
        if self.resolution not in VALID_RESOLUTIONS:
            raise ValueError(f'gridcell area weights for resolution '
                             f' {self.resolution} not available')
        elif self.resolution == '1536x768':
            self.gridcell_area_data_path =  os.path.join(
                Path(__file__).parent.parent.resolve(),
                'data',
                'gridcell-area' +
                '_noaa-ufs-gefsv13replay-pds' +
                '_bfg_control_1536x768_20231116.nc'
            )

@dataclass
class DailyBFGHv(object):
    """Harvester dataclass used to parse daily mean statistics from background 
    forecast data.

    Parameters:
    -----------
    config: DailyBFGConfig object containing information used to determine
            which variable to parse from the log file

    Methods:
    --------
    get_data: 
        Parse descriptive statistics from log files based on input config file 
        and return a list of tuples containing the harvested data.
    """
    config: DailyBFGConfig = field(default_factory=DailyBFGConfig)

    def get_data(self):
        """Harvests requested statistics and variables from background 
        forecast data and returns harvested_data, a list of HarvestedData 
        tuples.

        The routine extracts timestamps from the input data (forecast files), 
        calculates the temporal midpoint, and estimates the time step using 
        finite difference.
        """
        harvested_data = []
        if self.config.surface_mask is None:
            surface_mask_list = [None]
        else:
            surface_mask_list = self.config.surface_mask
            
        # Open datasets
        xr_dataset = xr.open_mfdataset(
            self.config.harvest_filenames, combine='nested', 
            concat_dim='time', decode_times=True
        )
        
        var_utils_catalog = VarUtilsCatalog(xr_dataset)
        
        gridcell_area_data = xr.open_dataset(self.config.gridcell_area_data_path)
        gridcell_area_weights = gridcell_area_data['area']

        # Calculate median cftime
        median_cftime = get_median_cftime(xr_dataset)

        # Initialize regions catalog
        regions_catalog = GeoRegionsCatalog(xr_dataset)
        regions_catalog.add_user_region(self.config.regions)
        for region_name, region_bounds in self.config.regions.items():
            regions_catalog.get_region_indices(region_name)
            (regions_catalog.gridcell_area_weights[region_name]['latitude'],
             regions_catalog.gridcell_area_weights[region_name]['longitude'],
             regions_catalog.gridcell_area_weights[region_name]['data']
            ) = regions_catalog.get_region_data(region_name, gridcell_area_weights)

        # Process each variable
        for i, var_name in enumerate(self.config.variables):
            global_variable_data, longname, units = var_utils_catalog.extract_variable_info(var_name)
                
            # Initialize mask catalog
            mask_catalog = MaskCatalog()
            mask_variable = mask_catalog.check_variable_to_mask(var_name)
            if self.config.surface_mask != None or mask_variable:
                global_soil_type_data = var_utils_catalog.get_soil_type_data()
                global_land_fraction_data, global_icec_data = var_utils_catalog.get_fraction_data()

            # Process each region
            for region_name, region_bounds in self.config.regions.items():
                if region_name == 'global':
                    region_global = True
                else:
                    region_global = False
                # Extract region data
                (regional_variable_lats, regional_variable_lons,
                regional_variable_data) = regions_catalog.get_region_data(
                    region_name, global_variable_data
                )
                
                # Assure equal domains
                check_region_domain(
                    regional_variable_lats,
                    regions_catalog.gridcell_area_weights[region_name]['latitude'],
                    region_name
                )
                check_region_domain(
                    regional_variable_lons,
                    regions_catalog.gridcell_area_weights[region_name]['longitude'],
                    region_name
                )
                 
                if self.config.surface_mask is not None or mask_variable:
                    is_masked = True
                    # Extract the region-specific fraction data and soil type
                    (land_fraction_lats, land_fraction_lons, land_fraction_data
                    ) = regions_catalog.get_region_data(
                        region_name, global_land_fraction_data
                    )
                    
                     # Assure equal domains
                    check_region_domain(
                        land_fraction_lats,
                        regions_catalog.gridcell_area_weights[region_name]['latitude'],
                        region_name
                    )
                    
                    check_region_domain(
                        land_fraction_lons,
                        regions_catalog.gridcell_area_weights[region_name]['longitude'],
                        region_name
                    )
                    
                    (icec_lats, icec_lons, icec_data
                    ) = regions_catalog.get_region_data(
                        region_name, global_icec_data
                    )
                    
                     # Assure equal domains
                    check_region_domain(
                        icec_lats,
                        regions_catalog.gridcell_area_weights[region_name]['latitude'],
                        region_name
                    )
                    
                    check_region_domain(
                        icec_lons,
                        regions_catalog.gridcell_area_weights[region_name]['longitude'],
                        region_name
                    )
                    
                    (soil_type_lats, soil_type_lons, soil_type_data
                    ) = regions_catalog.get_region_data(region_name, global_soil_type_data)
                    
                     # Assure equal domains
                    check_region_domain(
                        soil_type_lats,
                        regions_catalog.gridcell_area_weights[region_name]['latitude'],
                        region_name
                    )
                    
                    check_region_domain(
                        soil_type_lons,
                        regions_catalog.gridcell_area_weights[region_name]['longitude'],
                        region_name
                    )
                    
                    masked_variable, masked_fraction_data = mask_catalog.initial_mask_variable(
                        var_name, regional_variable_data, land_fraction_data,
                        soil_type_data, icec=icec_data)
                    
                else:
                    is_masked = False
                
                for j, surface_mask in enumerate(surface_mask_list):
                    if not is_masked:
                        """No masking applied
                        """
                        region_gridcell_area_weights = regions_catalog.gridcell_area_weights[region_name]['data']
                        
                        temporal_mean_regional_variable_data = np.ma.masked_invalid(
                            regional_variable_data.mean(
                                dim = 'time', skipna = False
                            )
                        )
                    elif surface_mask is None:
                        """No user specified mask but auto masking applied previously
                        for select variables
                        """
                        temporal_mean_fraction_data = masked_fraction_data.sum(
                            dim = 'time', skipna = True
                        ) / float(masked_fraction_data.time.size)
                    
                        region_gridcell_area_weights = np.ma.masked_invalid(
                            temporal_mean_fraction_data *
                            regions_catalog.gridcell_area_weights[region_name]['data']
                        )
                        
                        temporal_mean_regional_variable_data = np.ma.masked_invalid(
                            masked_variable.mean(
                                dim = 'time', skipna = False    
                            )
                        )
                    
                    elif surface_mask is not None:
                        """apply user specified mask
                        """
                        mask_catalog.check_surface_mask([surface_mask])
                        
                        user_masked_variable, user_masked_fraction_data = mask_catalog.user_mask(
                            surface_mask, masked_variable, masked_fraction_data,
                            land_fraction_data, soil_type_data
                        )
                        
                        temporal_mean_fraction_data = user_masked_fraction_data.sum(
                            dim = 'time', skipna = True
                        ) / float(user_masked_fraction_data.time.size)
                    
                        region_gridcell_area_weights = np.ma.masked_invalid(
                            temporal_mean_fraction_data *
                            regions_catalog.gridcell_area_weights[region_name]['data']
                        )
                        
                        temporal_mean_regional_variable_data = np.ma.masked_invalid(
                            user_masked_variable.mean(
                                dim = 'time', skipna = False    
                            )
                        )
                    
                    """proceed for all cases
                    """
                    # Add statistics to harvested_data
                    for k, statistic in enumerate(self.config.stats):
                        if statistic == 'mean':
                            value = stats_utils.area_weighted_mean(
                                temporal_mean_regional_variable_data,
                                region_gridcell_area_weights,
                                region_global=region_global,
                                is_masked=is_masked
                            )
                        
                            #value = self.config.regions[region_name]['mean']
                        elif statistic == 'variance':
                            #value = self.config.regions[region_name]['variance']
                            value = stats_utils.area_weighted_variance(
                                temporal_mean_regional_variable_data,
                                region_gridcell_area_weights,
                                region_global=region_global,
                                is_masked=is_masked
                            )
                        elif statistic == 'maximum':
                            #value = self.config.regions[region_name]['maximum']
                            value = np.ma.max(temporal_mean_regional_variable_data)
                        elif statistic == 'minimum':
                            #value = self.config.regions[region_name]['minimum']
                            value = np.ma.min(temporal_mean_regional_variable_data)
                        elif statistic == 'integral':
                            value = stats_utils.area_weighted_integral(
                                temporal_mean_regional_variable_data,
                                region_gridcell_area_weights,
                                region_global=region_global,
                                is_masked=is_masked
                                )

                        harvested_data.append(HarvestedData(
                            self.config.harvest_filenames,
                            self.config.segment,
                            statistic,
                            var_name,
                            value,
                            units,
                            dt.fromisoformat(median_cftime.isoformat()),
                            longname,
                            surface_mask,
                            {'name': region_name,
                             'latitude': regional_variable_lats,
                             'longitude': regional_variable_lons
                            }
                        ))

        # Close datasets
        gridcell_area_data.close()
        xr_dataset.close()

        return harvested_data