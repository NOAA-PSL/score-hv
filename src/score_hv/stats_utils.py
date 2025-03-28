"""Copyright 2024 NOAA
All rights reserved.

Methods to calculate gridcell area weighted statistics.
The functions generally take the following two input variables:
    xarray_variable - xarray variable data
    gridcell_area_data - xarray variable containing gridcell areas, in the
    same shape as xarray_variable
"""

import numpy as np

def area_weighted_mean(xarray_variable, gridcell_area_weights,
                       region_global=True, is_masked=False):
    """Returns the gridcell area weighted mean of xarray_variable and checks
    that gridcell_area_weights are valid.

    Args:
        xarray_variable: The data variable to calculate the weighted mean for.
        gridcell_area_weights: The area weights (steradians) for the grid cells
        region_global (bool): If True, checks if the sum of the weights is
            approximately 4*pi steradians (for global regions). Defaults to True.

    Returns:
        weighted_mean: The area-weighted mean of the xarray_variable.

    Raises:
        ValueError: If the sum of the gridcell area weights does not equal
                    approximately 4 pi steradians when region=global
    """
    weighted_mean, sumweights = np.ma.average(
        xarray_variable, weights=gridcell_area_weights, returned=True
    )

    # Explicit check for the sum of weights
    if region_global and not is_masked and not (0.999 * 4 * np.pi <= sumweights <= 1.001 * 4 * np.pi):
        msg = (
            f'expected region is global and {gridcell_area_weights}'
            '(gridcell area weights) sum does not equal 4 pi steradians; '
            'cannot calculate accurate gridcell weighted statistics'
        )
        raise ValueError(msg)

    return weighted_mean

def area_weighted_variance(xarray_variable, gridcell_area_weights,
                           region_global=True, is_masked=False,
                           expected_value=None):
    """Returns the gridcell weighted variance of the requested variables using
    the following formula:

        variance = sum_R{ w_i * (x_i - xbar)^2 },

    Where sum_R represents the summation for each value x_i over the region of 
    interest R with normalized gridcell area weights w_i and weighted mean xbar.

    Args:
        xarray_variable: The data variable to calculate the weighted variance for.
        gridcell_area_weights: The normalized weights for the grid cells.
        region_global (bool): If True, can check if the sum of the weights is
            approximately 4*pi steradians (for global regions). Defaults to True.                           
        expected_value: The expected value (usually the weighted mean). If not
                        provided, it will be calculated.

    Returns:
        weighted_variance: The gridcell area weighted variance of the variable.

    Raises:
        ValueError: If the shape of the weights array does not match the shape
                    of the xarray_variable.
    """
    if expected_value is None:
        expected_value = area_weighted_mean(xarray_variable, gridcell_area_weights,
                                            region_global=region_global,
                                            is_masked=is_masked)

    # Ensure that the weights and temporal_mean arrays have compatible shapes
    if xarray_variable.shape != gridcell_area_weights.shape:
        msg = (f'The shape of the xarray_variable {xarray_variable.shape} '
               f'does not match the shape of the gridcell_area_weights '
               f'{gridcell_area_weights.shape}.')
        raise ValueError(msg)

    # Calculate the weighted variance
    weighted_variance = -expected_value**2 + np.ma.sum(
        xarray_variable**2 * (gridcell_area_weights / gridcell_area_weights.sum())
    )
    
    return weighted_variance