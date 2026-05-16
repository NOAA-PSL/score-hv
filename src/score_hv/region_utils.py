"""
Copyright 2024 NOAA
All rights reserved.

This module contains methods to work with user-requested geographic regions.
It includes functionality for defining default latitude and longitude ranges
and potentially more utilities for working with geospatial data.
"""

import numpy as np
import xarray as xr

# Default latitude and longitude ranges
# The minimum latitude is -90, and the maximum latitude is 90.
# The longitude in BFG files ranges from 0 to 360 degrees east (circular).
NORTH_LAT = 90
SOUTH_LAT = -90
WEST_LONG = 0
EAST_LONG = 360

class GeoRegionsCatalog:
    """
    A catalog of geographical regions, initialized from a dataset.

    Attributes:
        name (list): A list of region names.
        north_lat (dict): A dictionary mapping region names to northernmost latitudes.
        south_lat (dict): A dictionary mapping region names to southernmost latitudes.
        west_long (dict): A dictionary mapping region names to westernmost longitudes.
        east_long (dict): A dictionary mapping region names to easternmost longitudes.
        latitude_values (numpy.ndarray): Array of latitude values from the dataset.
        longitude_values (numpy.ndarray): Array of longitude values from the dataset.
    """

    def __init__(self, dataset):
        """
        Initializes the GeoRegionsCatalog with data from an xarray dataset.

        Args:
            dataset (xarray.Dataset): A dataset that has been opened with xarray.
        """
        # Check if the data has the expected dimensions
        if "grid_yt" not in dataset.dims or "grid_xt" not in dataset.dims:
            raise KeyError("Data does not have the expected 'grid_yt' or 'grid_xt' dimensions.")
        
        # Initialize dictionaries for region boundaries
        self.north_lat = {} 
        self.south_lat = {}
        self.west_long = {}
        self.east_long = {}
        
        self.lat_indices = {}
        self.long_indices = {}
        
        self.gridcell_area_weights = {}

        # Extract latitude and longitude values from the dataset
        self.latitude_values = dataset['grid_yt'].values
        self.longitude_values = dataset['grid_xt'].values

    def test_user_latitudes(self, north_lat, south_lat):
        """
        Validates that the given latitude values are within the valid range
        (-90 to 90) and that the southern latitude is less than the northern
        latitude.

        Args:
            north_lat (float): The northernmost latitude.
            south_lat (float): The southernmost latitude.

        Raises:
            ValueError: If any of the latitude values are out of bounds or if
                        the southern latitude is greater than the northern latitude.
        """
        # Check if latitudes are within bounds (-90 to 90)
        if not (-90 <= south_lat <= 90):
            raise ValueError(f"Southern latitude must be between -90 and 90. "
                             f"Received: {south_lat}")

        if not (-90 <= north_lat <= 90):
            raise ValueError(f"Northern latitude must be between -90 and 90. "
                             f"Received: {north_lat}")

        # Check if southern latitude is less than northern latitude
        if south_lat > north_lat:
            raise ValueError(f"Southern latitude must be less than northern latitude. "
                             f"Received: south_lat = {south_lat}, north_lat = {north_lat}")
    
    def test_user_longitudes(self, west_long, east_long):
        """
        Validates that the given longitude values are within the valid range
        (0 to 360).

        Args:
            west_long (float): The westernmost longitude.
            east_long (float): The easternmost longitude.

        Raises:
            ValueError: If any of the longitude values are out of bounds.
        """
        # Check if longitudes are within bounds (0 to 360)
        if not (0 <= east_long <= 360):
            raise ValueError(
                f"Eastern longitude must be between 0 and 360. Received: {east_long}"
            )

        if not (0 <= west_long <= 360):
            raise ValueError(
                f"Western longitude must be between 0 and 360. Received: {west_long}"
            )

    def add_user_region(self, dictionary):
        """
        Adds a user-defined region to the catalog.

        Parameters:
            dictionary (dict): A dictionary containing region information. 
                The dictionary should have the following structure:
                {
                    'region_name': {
                        'north_lat': <float>, 
                        'south_lat': <float>, 
                        'west_long': <float>, 
                        'east_long': <float>
                    }
                }

        If the dictionary is empty or missing any required keys, appropriate
        default values are used, and warnings are printed. If critical data is
        missing, an exception is raised.
        """
        if not dictionary:
            raise ValueError("The dictionary passed to add_user_region is empty.")

        for region_name, input_dict in dictionary.items():
            if not region_name:
                raise ValueError("No region name was given. Please enter a "
                                 "name for your region.")
            
            # Define default values and handle missing keys
            north_lat = input_dict.get("north_lat", NORTH_LAT)
            south_lat = input_dict.get("south_lat", SOUTH_LAT)
            west_long = input_dict.get("west_long", WEST_LONG)
            east_long = input_dict.get("east_long", EAST_LONG)

            # Handle missing latitude/longitude keys and print messages
            if "north_lat" not in input_dict:
                print(f"north_lat is missing. Using the default of north latitude = {north_lat}")
            if "south_lat" not in input_dict:
                print(f"south_lat is missing. Using the default of south latitude = {south_lat}")
            if "west_long" not in input_dict:
                print(f"west_long is missing. Using the default of west longitude = {west_long}")
            if "east_long" not in input_dict:
                print(f"east_long is missing. Using the default of east longitude = {east_long}")

            # Test user latitudes and longitudes
            self.test_user_latitudes(north_lat, south_lat)
            self.test_user_longitudes(west_long, east_long)

            # Store region boundaries in the dictionaries
            self.north_lat[region_name] = north_lat
            self.south_lat[region_name] = south_lat
            self.west_long[region_name] = west_long
            self.east_long[region_name] = east_long
            
            self.gridcell_area_weights[region_name] = dict()
            
    def get_region_indices(self, region_name):
        """
        Calculate separate boolean masks for latitude and longitude indicating which
        values are within the specified region.

        Parameters:
            region_name (str): The name of the region to process.
        """
        # Retrieve region boundaries
        north_lat = self.north_lat[region_name]
        south_lat = self.south_lat[region_name]
        east_long = self.east_long[region_name]
        west_long = self.west_long[region_name]

        # Calculate latitude mask
        latitude_values = np.array(self.latitude_values)
        lat_mask = (latitude_values >= south_lat) & (latitude_values <= north_lat)

        # Calculate longitude mask
        longitude_values = np.array(self.longitude_values)

        if east_long <= west_long:
            # Region crosses the Prime Meridian
            long_mask1 = (longitude_values >= west_long) & (longitude_values <= 360)
            long_mask2 = (longitude_values >= 0) & (longitude_values <= east_long)
            long_mask = long_mask1 | long_mask2
        else:
            # Standard longitude range, no crossing of the Prime Meridian
            long_mask = (longitude_values >= west_long) & (longitude_values <= east_long)

        # Get the indices where the mask is True
        self.lat_indices[region_name] = np.where(lat_mask)[0]
        self.long_indices[region_name] = np.where(long_mask)[0]

    def get_region_data(self, region_name, data):
        """
        Returns the subset of the data corresponding to the user-selected region.

        Parameters:
            region_name (str): The name of the region to extract.
            data (xarray.DataArray): The full grid variable data to be sub-setted.

        Returns:
            xarray.DataArray: The sub-setted region data.

        Raises:
            KeyError: If no valid region masks are returned or the region data 
                      is invalid.
        """

        # Check if any indices are valid, i.e., there should be at least one True mask
        if len(self.lat_indices[region_name]) == 0 or len(self.long_indices[region_name]) == 0:
            raise KeyError(f"No valid region found for region '{region_name}'.")

        # Select the region data using isel with the indices where the masks are True
        region_data = data.isel(
            #time=slice(None),
            grid_yt=self.lat_indices[region_name],
            grid_xt=self.long_indices[region_name]
        )
        
        region_lats = data.grid_yt.isel(grid_yt=self.lat_indices[region_name])
        region_lons = data.grid_xt.isel(grid_xt=self.long_indices[region_name])

        return (region_lats, region_lons, region_data)