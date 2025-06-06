"""
Copyright 2024 NOAA
All rights reserved.

Collection of methods to work with masking of user requested variables
"""
import sys,os
import numpy as np
import xarray as xr
import pytest
import pdb

VARIABLES_TO_MASK = ['icec', 'icetk','nsst','snod','soilm','soilt4','sst','tg3','tsnowp','weasd']
VALID_MASKS = ['none','land','water', 'ice', 'sea']

class MaskCatalog:
    def __init__(self):
        """
          Here we initalize the MaskCatalog class.
          """
        self.soil_snow_variables = ['soilt4','soilm','snod','tg3','tsnowp', 'weasd']
        self.ice_variables = ['icetk']
        self.sst_variables = ['sst', 'nsst']

    def check_variable_to_mask(self,var_name):
        """
          This method check to see if the variable the user has 
          requested is in the above VARIABLES_TO_MASK list.  If 
          it is the method returns true, if not the method returns false.
          """
        return var_name in VARIABLES_TO_MASK

    def initial_mask_variable(self, var_name, variable_data, lfrac,
                              sotyp_data, icec=None):
        """
          This method does the masking of the variables requested by the user.
          There are some variables that are always masked. 
          The variables that are always masked:
              soil variables: soill4,soilm and tg3.
              snow variables: snod,tsnowp,weasd
              ice variables: icetk
              sea_surface_temp: sst and nsst
          The sotyp(soil type) is the main variable in the data set used for
          maksing..
          Parameters:
          var_name - The variable name.
          varaiable_data - The initial variable data by region with no masking.
          lfrac - land fraction variable (lfrac)
          sotyp_data - The sotyp variale from the data set that is by region.                        
          return - The variable data and fraction data are returned with the
                   unwanted grid cell
                   data masked.
          """
        if var_name in self.soil_snow_variables:        
           """We will need the sotyp(soil type) variable from the dataset.
             The values of 0 and 16 in the sotyp variable are used to delete values
             over water and land ice. This is used specifically for the 
             soil_snow variables: soilm,soilt4,tg3,snod and weasd. We also need
             the land fraction or the ice fraction variable depending on what
             variable the user has requested.
           """
           masked_variable = variable_data.where(
               (sotyp_data != 0) & (sotyp_data != 16)
           )
           masked_frac = lfrac.where(
               (sotyp_data != 0) & (sotyp_data != 16)
           )
        
        elif var_name in self.ice_variables:
           """The ice concentraion variable has 0 everwhere except where there is ice.
           """
           masked_variable = variable_data.where(icec > 0)
           masked_frac = icec.where(icec > 0)

        elif var_name in self.sst_variables:
            """For the sst (tmpsfc) variable we use the sotyp data and keep the
            values that are over the water.
            """
            masked_variable = variable_data.where(
                (sotyp_data == 0) & (icec == 0)
            )
            masked_frac = 1. - lfrac.where(icec==0)
            
        else:
            masked_variable = variable_data
            masked_frac = xr.where(variable_data.notnull(), 1.0, np.nan)
        
        return(masked_variable, masked_frac)

    '''
    def replace_bad_values_with_nan(self,variable_data):
        """
          Check for _FillValue or missing_values in the variable data.
          This method will replace the missing or fill values with 
          NaN.
          Parameters;
          variable_data - The variable field data. Variable_data is of
                          type class 'xarray.core.dataarray.DataArray.
          Return - The variable field data with NaN's for where the 
                   grid values are missing or fill values. The returned
                   masked_variable_data is of type 
                   class 'xarray.core.dataarray.DataArray.
          """         
        fill_value = variable_data.encoding.get('_FillValue', None)
        missing_value = variable_data.encoding.get('missing_value', None)
     
        """
          Create a combined mask for fill_values,missing_value and non
          finite values. 
          """
        if fill_value is not None and missing_value is not None:
           mask = (variable_data != fill_value) & (variable_data != missing_value)
        elif fill_value is not None:
           mask = variable_data != fill_value
        elif missing_value is not None:
           mask = variable_data != missing_value
        else:
           mask = np.isfinite(variable_data)

       # Apply the mask
        masked_variable = variable_data.where(mask,np.nan)
        return(masked_variable)
    '''
    
    def user_mask(self, mask_type, variable_data, fraction_data, lfrac,
                  sotyp_data, icec=None):
        """The user has requested a mask. Supported masks include: land, water,
        or ice
        """
        
        if mask_type == 'land':
            masked_variable = variable_data.where(
                (sotyp_data != 0) & (sotyp_data != 16)
            )
            masked_frac = lfrac.where(
                (sotyp_data != 0) & (sotyp_data != 16) & (fraction_data.notnull())
                & (fraction_data != 0)
            )
        
        elif mask_type == 'ice':
           """The ice thickness variable has 0 everwhere except where there is ice.
           """
           masked_variable = variable_data.where(icec > 0)
           masked_frac = icec.where(
               (icec > 0) & (fraction_data.notnull()) & (fraction_data != 0)
           )
           
        elif mask_type == 'water' or mask_type == 'sea':
            masked_variable = variable_data.where(
                (sotyp_data == 0) & (icec == 0)
            )
            masked_frac = 1. - lfrac.where((icec==0) & (fraction_data.notnull())
                                           & (fraction_data != 0))
        
        return(masked_variable, masked_frac)
     
    def check_surface_mask(self,user_surface_mask):
        for mask in user_surface_mask:
            if mask not in VALID_MASKS:
               msg = f'The mask: {mask} is not a supported mask. ' \
                     f'Valid masks are: "none, land, water, ice.'
               raise ValueError(msg)