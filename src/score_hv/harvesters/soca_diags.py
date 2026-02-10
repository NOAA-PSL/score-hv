import os,sys
import numpy as np
import netCDF4
from datetime import datetime as dt
from dataclasses import dataclass, field
from collections import namedtuple

"""
SOCA Diagnostic Harvester
-------------------------
Input: IODA-v3 NetCDF4 files (SST, ICEC, or WOD).
Structure:
    /MetaData: longitude, latitude, dateTime, depth (optional)
    /ObsValue: Raw observations
    /oman: Observation minus Analysis (Residuals)
    /ombg: Observation minus Background (Innovations)
    /EffectiveQC0: Quality Control flags (0 = Passed)
    
Masking Logic: 
    Combined Mask = (Data == FillValue) | (QC_Flag > Threshold)
"""

VALID_STATISTICS = ('mean', 'median', 'StdDev', 'minimum', 'maximum')
VALID_VARIABLES = ('sst', 'icec', 'salinity', 'waterTemperature', 
                   'seaSurfaceSalinity', 'seaSurfaceTemperature', 'seaIceFraction')

HarvestedData = namedtuple('HarvestedData', [
    'filenames', 'sensor', 'satellite', 'level', 'variables', 
    'group', 'longname', 'units', 'statistics', 'value', 
    'filetime', 'file_region', 'QC_threshold', 'ocean_depth_bins'
])


def parse_filename(filename):
    """
      Extract metadata attributes from SOCA/IODA file naming conventions.

      This parser decomposes the filename string into its constituent components 
      (sensor, satellite, region, etc.) based on the file prefix. It supports 
      World Ocean Database (WOD), Sea Ice Concentration (ICEC), and Sea 
      Surface Temperature (SST) naming schemes.

      Parameters:
        filename : str
        The path or name of the NetCDF file (e.g., 'sst_viirs_north_l3.nc').

       Returns:
         dict
             A dictionary containing the extracted metadata:
             - 'file_type': Primary category (e.g., 'sst', 'wod').
             - 'sensor': Instrument name (e.g., 'viirs', 'ctd').
             - 'satellite': Platform name if applicable.
             - 'file_region': 'global', 'north', or 'south'.
             - 'level': Data processing level (e.g., 'l3').
             - 'variable': Short name of the physical variable.

      Example file names:
         WOD:  `wod_t_ctd.nc` -> sensor: ctd, variable: t, region: global
         SST:  `sst_viirs_north_l3.nc` -> sensor: viirs, region: north, level: l3
         ICEC: `icec_amsr2_ghrsst.nc` -> sensor: amsr2, satellite: ghrsst
       """

    base = os.path.basename(filename).replace('.nc', '')
    parts = base.split('_')
    prefix = parts[0]
    
    info = {
        'file_type': prefix,
        'sensor': None,
        'satellite': None,
        'file_region': None,
        'level': None,
        'variable': prefix
    }

    if prefix == 'wod':
        info.update({
            'sensor': parts[2] if len(parts) > 2 else parts[0],
            'variable': parts[1] if len(parts) > 1 else None,
            'file_region': 'global'
        })
    elif prefix in ['icec', 'sst']:
        info['sensor'] = parts[1] if len(parts) > 1 else None
        part2 = parts[2] if len(parts) > 2 else None
        if part2 in ['north', 'south']:
            info['file_region'] = part2
        else:
            info['satellite'] = part2
        if len(parts) > 3 and parts[3].startswith('l'):
            info['level'] = parts[3]
    
    return info

def extract_soca_metadata(ds):
    """
    Extracts core spatial/temporal variables. 
    Exists on missing lat/lon/time.
    Returns None on missing depth for surface files.
    """
  
    meta = ds.groups.get('MetaData')
    if not meta:
        raise KeyError("MetaData group missing in the file.")
    
    mandatory = ['latitude', 'longitude', 'dateTime']
    extracted = {}

    for var in mandatory:
        if var in meta.variables:
            extracted[var] = meta.variables[var][:]
        else:
            raise KeyError(f"Mandatory variable '{var}' missing from MetaData.")

    """
      Some files do not have depth in them. We return None.
      """
    if 'depth' in meta.variables:
        extracted['depth'] = meta.variables['depth'][:]
    else:
        # Set to None for SST or ICEC files
        extracted['depth'] = None
    
    return extracted


def get_variable_metadata(file_type, var_name, mean_val=None):
    """
      Determines long names and units of the variable name(var_name) 
      Parameters:
         file_type : str
            The category of the file determined by `parse_filename`
            (e.g., 'wod', 'sst', 'icec').

         var_name : str
            The raw variable key found in the IODA 'ObsValue' group.

         mean_val : float, optional
            The calculated mean of the observations. Used to distinguish 
            between Celsius (< 200) and Kelvin (>= 200) for SST files.

    Returns
        tuple (str, str)
            - long_name: The descriptive name of the variable (e.g., 'Temperature').
            - units: The standardized unit string (e.g., 'DegC', 'PSS', '%').

    Notes
          For 'wod' file types, the function uses an internal mapping to align
          with WOD short-codes ('t', 's', 'o', etc.). For 'sst' types, a threshold
          of 200 is used to guess the unit if not explicitly provided in the
          NetCDF attributes.
      """

    # Map common SOCA/JEDI variable names to WOD short keys
    soca_to_wod_map = {
        'waterTemperature': 't',
        'seaSurfaceTemperature': 't',
        'salinity': 's',
        'seaSurfaceSalinity': 's',
        'seaIceFraction': 'ice'
    }  
    wod_meta = {
        't': ('Temperature', 'DegC'),
        's': ('Practical Salinity Scale', 'PSS'),
        'o': ('Oxygen', 'umol/kg'),
        'p': ('Phosphate', 'umol/kg'),
        'i': ('Silicate', 'umol/kg'),
        'n': ('Nitrate', 'umol/kg'),
        'h': ('pH', 'pH'),
        'l': ('Chlorophyll', 'ug/l'),
        'a': ('Alkalinity', 'umol/kg')
    }

    if file_type == 'wod':
        lookup_key = soca_to_wod_map.get(var_name, var_name)
        long_name, unit = wod_meta.get(lookup_key, (var_name, 'Unknown'))
        return long_name, unit

    units = 'Unknown'
    if file_type == 'icec' and var_name == 'seaIceFraction':
        units = "%"
    elif file_type == 'sst':
        # Dynamic unit selection based on magnitude
        if mean_val is not None:
            units = 'DegC' if mean_val < 200 else 'DegK'
        else:
            units = 'DegC'
            
    return var_name, units

def calculate_masked_stats(var_obj, qc_mask, requested_stats):
    """
      Apply Quality Control and compute requestd statistics.
      This method handles the intersection of missing values (FillValue) and 
      rejected observations (QC flags) to ensure statistics are only 
      calculated on 'clean' data.

      Parameters:
      var_obj : netCDF4.Variable
          A NetCDF variable object from groups 
          (e.g., ObsValue, oman, or ombg).
      qc_mask : np.ndarray (bool)
          A boolean array where True indicates the observation failed 
          Quality Control and should be excluded.
      requested_stats : tuple of str
          The statistics to calculate. Valid options include:
          ('mean', 'median', 'StdDev', 'minimum', 'maximum').

      Returns:
       dict
          A dictionary where keys are statistic names and values are 
          floats. Returns an empty dictionary if all data in the 
          variable is masked.

      Notes
       The final mask used for calculation is:
       mask = (data == _FillValue) | (EffectiveQC0 > QC_threshold)
      """

    raw_data = var_obj[:]
     
    # Handle FillValue
    if '_FillValue' in var_obj.ncattrs():
        fill_mask = (raw_data == var_obj.getncattr('_FillValue'))
    else:
        fill_mask = np.zeros_like(raw_data, dtype=bool)
        
    combined_mask = fill_mask | qc_mask
    masked_data = np.ma.masked_array(raw_data, mask=combined_mask)
    
  
    results = {}
    if masked_data.count() == 0:
        return results

    stat_map = {
        'mean': np.ma.mean,
        'median': np.ma.median,
        'StdDev': np.ma.std,
        'minimum': np.ma.min,
        'maximum': np.ma.max
    }

    for stat in requested_stats:
        if stat in stat_map:
            val = stat_map[stat](masked_data)
            results[stat] = float(val) if not np.ma.is_masked(val) else None
    
    return results

# --- Main Classes ---

@dataclass
class SOCADiagsConfig:
    config_data: dict = field(default_factory=dict)

    def __post_init__(self):
        self.harvest_filenames = self.config_data.get('filenames', [])
        self.variables = self.config_data.get('variables', [])
        self.stats = self.config_data.get('statistics', ['mean'])
        self.qc_threshold = self.config_data.get('QC_threshold', 0.0)
        self.ocean_depth_bins = self.config_data.get('ocean_depth_bins', [None])

@dataclass
class SOCADiagsHv:
    config: SOCADiagsConfig

    def get_data(self):
        harvested_results = []
        print("in the harvester")
        data_groups = ['ObsValue', 'oman', 'ombg']
        print(self.config.ocean_depth_bins)
         
        for filename in self.config.harvest_filenames:
            if not os.path.exists(filename):
                raise FileNotFoundError(f"The file '{filename}' does not exist in the current directory.")                 
            try:
                with netCDF4.Dataset(filename, 'r') as ds:
                    file_info = parse_filename(filename)
                  
                    try:
                        obs_metadata = extract_soca_metadata(ds)
                        lats = obs_metadata['latitude']
                        lons = obs_metadata['longitude']
                        times = obs_metadata['dateTime']
                        depths = obs_metadata['depth']
                    except KeyError as e:
                        print(f"Error: The variable {e} was not found in the metadata group.") 
                    
                    time_metadata = ds.groups['MetaData'].variables['dateTime'] 
                    dates = netCDF4.num2date(times, units=time_metadata.units, 
                            calendar=getattr(time_metadata, 'calendar', 'standard'))
                    file_time = dt.fromisoformat(dates[0].strftime("%Y-%m-%d %H:%M:%S"))                   

                    """
                      Read the ObsValue goup in the data set. Exit if it
                      does not exits.
                      """
                    obs_group = ds.groups.get('ObsValue')
                    if not obs_group:
                        raise RuntimeError(
                                           f"Data processing failed: {filename}"
                                           "does not contain an 'ObsValue' group.")

                    for var_name in obs_group.variables.keys():
                        #Build QC Mask once per variable
                        qc_group = ds.groups.get('EffectiveQC0')
                        if qc_group and var_name in qc_group.variables:
                            qc_flags = qc_group.variables[var_name][:]
                            qc_mask = (qc_flags > self.config.qc_threshold)
                        else:
                            qc_mask = np.zeros(obs_group.variables[var_name].shape, dtype=bool)

                        for d_bin in self.config.ocean_depth_bins:
                            # Handle potential depth masking
                            if d_bin is not None and obs_metadata['depth'] is not None:
                                d_min, d_max = d_bin
                                print("the min and max ",d_min,d_max)
                                # Mask data outside the current depth range
                                depth_mask = (obs_metadata['depth'] < d_min) | (obs_metadata['depth'] > d_max)
                                combined_mask = qc_mask | depth_mask
                                bin_label = f"{d_min}-{d_max}m"
                            else:
                                # Fallback for surface data (SST/ICEC) or if no bins provided
                                combined_mask = qc_mask
                                bin_label = "surface"
                                
                            for group_name in data_groups:
                                if group_name not in ds.groups or var_name not in ds.groups[group_name].variables:
                                   raise ValueError(
                                         f"Missing data group '{group_name}' in {os.path.basename(filename)}.")
               
                                var_obj = ds.groups[group_name].variables[var_name]
                                stats = calculate_masked_stats(var_obj, combined_mask, self.config.stats)
                                if not stats:
                                    print("no stats") 
                                    continue

                                current_mean = stats.get('mean')
                                long_name, units = get_variable_metadata(
                                    file_info['file_type'], var_name, mean_val=current_mean)

                                for stat_name, stat_val in stats.items():
                                    if stat_val is None: continue
                                        print(stat_val,"  ",stat_name,"  ",group_name,"  ",self.config.qc_threshold) 
                                   
                                     harvested_results.append(HarvestedData(
                                        filenames=filename,
                                        sensor=file_info['sensor'],
                                        satellite=file_info['satellite'],
                                        level=file_info['level'],
                                        variables=var_name,
                                        group=group_name,
                                        longname=long_name,
                                        units=units,
                                        statistics=stat_name,
                                        value=np.float32(stat_val),
                                        filetime=file_time,
                                        file_region=file_info['file_region'],
                                        QC_threshold=self.config.qc_threshold
                                   ))

            except Exception as e:
                print(f"Error processing {os.path.basename(filename)}: {e}")
        
        return harvested_results
