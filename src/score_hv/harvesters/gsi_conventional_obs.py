"""methods to extract information from the Gridpoint Statistical Interpolation
(GSI) analysis output (fit files), including innovation statistics for
conventional observations
"""

import os
import warnings
from collections import namedtuple
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime

from score_hv.config_base import ConfigInterface

HARVESTER_NAME = 'gsi_conventional_obs'

VALID_VARIABLES = (
    'fit_psfc_data', # fit of surface pressure data (mb)
    'fit_uv_data', # fit of u, v wind data (m/s),
    'fit_t_data', # fit of temperature data (K)
    'fit_q_data', # fit of moisture data (% of qsaturation guess)
)

VALID_STATISTICS = (
    'count', # number of obs summed under obs types and vertical layers
    'bias', # bias of obs departure for each outer loop (it)
    'rms', # root mean squre error of obs departure for each outer loop (it)
    'cpen', # obs part of penalty (cost function)
    'qcpen' # nonlinear qc penalty
)

HarvestedData = namedtuple(
    'HarvestedData',
    ['datetime', # datetime.datetime object (date and a time)
     'ensemble_member',
     'plevs_top', # pressures at the layer tops (for multi-level data)
     'plevs_bot', # pressures at the layer bottoms (for multi-level data)
     'plevs_units',
     'variable',
     'statistic',
     'values',
     'units',
     'longname',
     'iteration', # GSI outer loop number
     'usage', # used (asm), read in but not assimilated (mon) or rejected (rej)
     'type', # prepbufr obs type
     'subtype', # prepbufr obs subtype
    ]
)

def get_longname(variable):
    
    longnames = {'fit_psfc_data': 'fit of surface pressure data',
                 'fit_uv_data': 'fit of u, v wind data',
                 'fit_t_data': 'fit of temperature data',
                 'fit_q_data': r'fit of moisture data (% of qsaturation guess)'}
    
    return longnames[variable]
    
def get_units(statistic, variable):
    
    units = {'fit_psfc_data': 'mb',
             'fit_uv_data': 'm/s',
             'fit_t_data': 'K',
             'fit_q_data': r'%'}
             
    if statistic == 'count':
        units[variable] = None
    
    return units[variable]


@dataclass
class GSIConvObsConfig(ConfigInterface):
    
    config_data: dict = field(default_factory=dict)
    
    def __post_init__(self):
        self.set_config()
        
    def set_config(self):
        """ function to set configuration variables from given dictionary
        """
        self.harvest_filename = self.config_data.get('filename')
        self.set_variables()
        self.set_statistics()
        self.set_plev_bounds()
    
    def set_variables(self):
        self.vars_to_harvest = self.config_data.get('variables')
        if self.vars_to_harvest == None:
            self.vars_to_harvest = list()
        
        for var in self.vars_to_harvest:
            if var not in VALID_VARIABLES:
                msg = (f"{var} is not a supported variable "
                       "to harvest from the GSI analysis fort.201, fort.205 "
                       "and fort.213 fit files. "
                       "Please reconfigure the input dictionary using only the "
                       f"following variables: {VALID_VARIABLES}")
                raise KeyError(msg)
    
    def set_statistics(self):
        self.stats_to_harvest = self.config_data.get('statistics')
        if self.stats_to_harvest == None:
            self.stats_to_harvest = list()
            
        for stat in self.stats_to_harvest:
            if stat not in VALID_STATISTICS:
                msg = (f"{stat} is not a supported statistic "
                       "to harvest from the GSI analysis fort.201, fort.205 "
                       "and fort.213 fit files. "
                       "Please reconfigure the input dictionary using only the "
                       f"following statistics: {VALID_STATISTICS}")
                raise KeyError(msg)
                
    def set_plev_bounds(self):
        """
        Set and validate pressure level bounds from config.

        Expects 'plev_bounds' in self.config_data as:
            [(plev_bot, plev_top), (plev1_bot, plev1_top), ..., (plevN_bot, plevN_top)]

        Validates structure, ensures numeric types, sorts by plev_bot,
        and checks for overlapping pressure layers.

        Raises:
            ValueError: If format is wrong or bounds overlap.
        """
        self.plev_bounds = self.config_data.get('plev_bounds')
        if self.plev_bounds is None:
            raise ValueError("Must provide pressure level bounds to harvest.")

        if not isinstance(self.plev_bounds, list):
            raise ValueError("'plevs' must be a list of (plev_bot, plev_top) tuples.")

        # Validate each item
        cleaned_bounds = []
        for i, bounds in enumerate(self.plev_bounds):
            if not (isinstance(bounds, (list, tuple)) and len(bounds) == 2):
                raise ValueError(f"Invalid entry at index {i}: {bounds}. "
                                 "Each item must be a 2-element tuple or list.")
            bot, top = bounds
            if not all(isinstance(val, (int, float)) for val in (bot, top)):
                raise ValueError(f"Invalid pressure levels at index {i}: ({bot}, {top}) must be numeric.")
            if bot <= top:
                raise ValueError(f"Invalid range at index {i}: bottom ({bot}) must be less than top ({top}).")
            cleaned_bounds.append((bot, top))

        self.plevs_bot = list()
        self.plevs_top = list()
        for i, bounds in enumerate(cleaned_bounds):
            self.plevs_bot.append(bounds[0])
            self.plevs_top.append(bounds[1])
                
@dataclass
class GSIConvObsHv(object):
    
    config: GSIConvObsConfig = field(default_factory = GSIConvObsConfig)
    
    def parse_value(self, value, prefer_int=False):
        if value == r"********":
            return_value = None

        elif prefer_int:
            try:
                return_value = int(value)
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' in {self.config.harvest_filename} to int")
        else:
            try:
                return_value = float(value)
            except ValueError:
                    raise ValueError(f"Cannot convert '{value}' in {self.config.harvest_filename} to float")
                    
        return return_value
    
    def get_data(self):
        """Read the fit file (from the GSI analysis output)
        
        returns a list of HarvestedData tuples
        """
        self.results = dict()
        for var in self.config.vars_to_harvest:
            self.results[var] = {
                'plevs_top': list(),
                'plevs_bot': list(),
                'plevs_units': list(),
            }
            for stat in self.config.stats_to_harvest:
                self.results[var][stat] = dict()
                self.results[var][stat][stat] = {'column_index': None,
                                                 'values': list()}
        if 'fit_psfc_data' not in self.results:
            self.results['fit_psfc_data'] = {
                'plevs_top': list(),
                'plevs_bot': list(),
                'plevs_units': list(),
            }
            for stat in self.config.stats_to_harvest:
                self.results['fit_psfc_data'][stat] = dict()
                self.results['fit_psfc_data'][stat][stat] = {'column_index': None,
                                                 'values': list()}
                
        # get the datetime from the input file name
        try: # format is gsistats.YYYYMMDDHH_control
            self.datetime = datetime.strptime(
                self.config.harvest_filename.split('.')[-1].split('_')[0],
                '%Y%m%d%H')
            self.ensemble_member = self.config.harvest_filename.split(
                '.')[-1].split('_')[1]
            
        except ValueError as err:
            if self.config.harvest_filename[-5:] == 'z.txt':
                # assume format from NASA
                self.datetime = datetime.strptime(
                    self.config.harvest_filename.split('.')[-2],
                    '%Y%m%d_%Hz'
                )
                self.ensemble_member = 'control'
            else:
                raise ValueError(f'{self.config.harvest_filename} is not a '
                 'supported GSI fit file name: cannot return datetime') from err
        
        with open(self.config.harvest_filename, encoding="utf-8") as f:
            self.lines = list(f)
            
        self.parse_fit_file()
        
        harvested_data = list()
        for var in self.config.vars_to_harvest:    
            
            longname = get_longname(var)
            
            for stat in self.config.stats_to_harvest:
                
                units = get_units(stat, var)
                
                for row_idx, value in enumerate(
                                    self.results[var][stat][stat]['values']):
                    return_iteration = int(self.results[
                                            var][
                                                stat][
                                                    'it'][
                                                        'values'][
                                                            row_idx]
                                        )
                    
                    if var == 'fit_uv_data' or var == 'fit_t_data' or var == 'fit_q_data':
                        # only return data on requested pressure levels
                        
                        # assume same pressure level units provided for
                        # surface pressure data, since none are provided for
                        # other variables
                        return_plevs_units = self.results['fit_psfc_data']['plevs_units'][return_iteration - 1]
                        
                        return_value = list()
                        return_plevs_top = list()
                        return_plevs_bot = list()
                        for plev_idx, plev_bot in enumerate(self.config.plevs_bot):
                            if plev_bot in self.results[var]['plevs_bot'][return_iteration - 1]: 
                                harvested_plev_bot_idx = self.results[var]['plevs_bot'][return_iteration - 1].index(plev_bot)
                                harvested_plev_top = self.results[var]['plevs_top'][return_iteration - 1][harvested_plev_bot_idx]
                        
                                if harvested_plev_top == self.config.plevs_top[plev_idx]:
                                    # harvested pressure bounds match requested pressure bounds
                                    return_value.append(value[harvested_plev_bot_idx])
                                    return_plevs_top.append(self.results[var]['plevs_top'][return_iteration - 1][harvested_plev_bot_idx])
                                    return_plevs_bot.append(self.results[var]['plevs_bot'][return_iteration - 1][harvested_plev_bot_idx])
                                else:
                                    # harvested pressure bounds do not match requested pressure bounds
                                    return_value.append(None)
                                    return_plevs_top.append(self.config.plevs_top[plev_idx])
                                    return_plevs_bot.append(plev_bot)
                            else:
                                # harvested pressure bound does not exist in harvested pressure bounds
                                return_value.append(None)
                                return_plevs_top.append(self.config.plevs_top[plev_idx])
                                return_plevs_bot.append(plev_bot)
                                
                    else:
                        return_plevs_units = self.results[var]['plevs_units'][return_iteration - 1]
                        return_plevs_top = self.results[var]['plevs_top'][return_iteration - 1]
                        return_plevs_bot = self.results[var]['plevs_bot'][return_iteration - 1]
                        return_value = value
                    
                    harvested_data.append(
                        HarvestedData(
                            self.datetime,
                            self.ensemble_member,
                            return_plevs_top,
                            return_plevs_bot,
                            return_plevs_units,
                            var,
                            stat,
                            return_value,
                            units,
                            longname,
                            return_iteration,
                            self.results[var][stat]['use']['values'][row_idx],
                            self.results[var][stat]['typ']['values'][row_idx],
                            self.results[var][stat]['styp']['values'][row_idx],
                        )
                    )
        
        return harvested_data 
    
    def store_column_info(self, variable, column_idx, line_part):
        for stat in self.config.stats_to_harvest:
            if line_part in self.results[variable][
                stat].keys():
                """data entries exist, update only the
                column indicies
                """
                self.results[variable][stat][line_part]['column_index'] = column_idx
            else:
                """no results added yet, create empty list
                to store values
                """
                self.results[variable][stat][line_part] = {'column_index': column_idx,
                                                           'values': list()}
    
    def extract_fit_obs_plevs(self, line_parts, variable_name):
        """extract fit to uv wind, temperature, or humidity stats from a
        given line of the fort.202 file
        """
        if line_parts[0] == 'o-g' and line_parts[1] == 'ptop':
            self.results[variable_name]['plevs_top'].append(list())
            self.results[variable_name]['plevs_bot'].append(list())
            for plev, ptop in enumerate(line_parts[2:]):
                self.results[variable_name]['plevs_top'][-1].append(float(ptop))
        elif line_parts[0] == 'o-g' and line_parts[1] == 'it':
            read_pbot = False
            for col, part in enumerate(line_parts):
                if read_pbot:
                    self.results[variable_name]['plevs_bot'][-1].append(
                        float(part)
                    )
                else:
                    for results_key, results_values in self.results[variable_name].items():
                        if part=='it' or part=='obs' or part=='use' or part=='typ' or part=='styp':
                            self.store_column_info(variable_name, col, part)
                
                if part == 'pbot':
                    read_pbot=True
                    
            if len(self.results[variable_name]['plevs_top'][-1]) != len(
                self.results[variable_name]['plevs_bot'][-1]):
                raise RuntimeError(f'extracted inconsistent number of pressure '
                    f'levels (ptop and pbot) from {variable_name} data in '
                    f'{self.config.harvest_filename}')
        elif line_parts[0] == 'o-g' and (line_parts[2] == 'uv' or line_parts[2] == 't' or line_parts[2] == 'q'):
            stat = line_parts[6]
            if stat in self.config.stats_to_harvest:
                for results_key, column_values in self.results[variable_name][stat].items():
                    if results_key == stat:
                        if stat == 'count':
                            self.results[variable_name][stat][stat]['values'].append([self.parse_value(x, prefer_int=True) for x in line_parts[7:]])
                        else:
                            self.results[variable_name][stat][stat]['values'].append([self.parse_value(x) for x in line_parts[7:]])
                    else:
                        column_index = self.results[variable_name][stat][results_key]['column_index']
                        self.results[variable_name][stat][results_key]['values'].append(
                            line_parts[column_index]
                        )
                
        elif line_parts[0] == 'o-g' and line_parts[3] == 'all':
            # stats for all observation types
            stat = line_parts[4]
            if stat in self.config.stats_to_harvest:
                self.results[variable_name][stat]['it']['values'].append(line_parts[1])
                self.results[variable_name][stat]['use']['values'].append(line_parts[2])
                self.results[variable_name][stat]['typ']['values'].append(line_parts[3])
                self.results[variable_name][stat]['styp']['values'].append(None)
                if stat=='count':
                    self.results[variable_name][stat][stat]['values'].append([self.parse_value(x, prefer_int=True) for x in line_parts[5:]])
                else:
                    self.results[variable_name][stat][stat]['values'].append([self.parse_value(x) for x in line_parts[5:]])
            
    def extract_fit_ps(self, line_parts, variable_name='fit_psfc_data'):
        """ extract fit to surface pressure stats from a given line of the
        fort.201 file
        """
        if line_parts[0] == 'pressure' and line_parts[1] == 'levels':
            self.read_fit_ps = True
            self.read_fit_uv = False
            self.read_fit_t = False
            self.read_fit_q = False
            self.results[variable_name]['plevs_units'].append(
                line_parts[2][1:-2]
            )
            self.results[variable_name]['plevs_top'].append(
                [float(line_parts[3])]
            )
            self.results[variable_name]['plevs_bot'].append(
                [float(line_parts[4])]
            )

        elif self.read_fit_ps and line_parts[0] == 'o-g' and line_parts[1] == 'it':
            for col, part in enumerate(line_parts):
                if part=='it' or part=='obs' or part=='use' or part=='typ' or part=='styp' or part in self.config.stats_to_harvest: 
                    self.store_column_info(variable_name, col, part)
                                                                 
        elif self.read_fit_ps and line_parts[0] == 'o-g' and line_parts[2] == 'ps':
           
           for stat in self.config.stats_to_harvest:
               for column_name, column_values in self.results[variable_name][stat].items():
                   column_index = self.results[
                       variable_name][
                           stat][
                               column_name][
                                   'column_index']
                   if column_name == 'count':
                       return_value = [self.parse_value(line_parts[column_index], prefer_int=True)]
                   elif column_name == stat:  
                       return_value = [self.parse_value(line_parts[column_index])]
                   else:
                       return_value = line_parts[column_index]
                   
                   self.results[
                       variable_name][
                           stat][column_name][
                               'values'].append(return_value)
                
        elif self.read_fit_ps and line_parts[0] == 'o-g' and line_parts[3] == 'all':
            # stats for all surface pressure observation types
            for stat in self.config.stats_to_harvest:
                self.results[
                    variable_name][
                        stat][
                            'it'][
                                'values'].append(
                                    line_parts[1])
                self.results[
                    variable_name][
                        stat][
                            'use'][
                                'values'].append(
                                    line_parts[2])
                self.results[
                    variable_name][
                        stat][
                            'typ'][
                                'values'].append(
                                    line_parts[3])
                                    
                self.results[
                    variable_name][
                        stat][
                            'styp'][
                                'values'].append(None)
                
                for column_name, column_values in self.results['fit_psfc_data'][stat].items():
                    if column_name == stat:
                        column_index = self.results[
                            variable_name][
                                stat][
                                    column_name][
                                        'column_index'] - 2 # this is a
                                    # weird corner case where the row is
                                    # formatted differently for all
                                    # observations than for stats by
                                    # observtion type
                        if column_name == 'count':
                            return_value = [int(
                                             line_parts[column_index])]
                        else:
                            return_value = [float(
                                              line_parts[column_index])]
                        
                        self.results[
                            variable_name][
                                stat][column_name][
                                    'values'].append(return_value)
        
        elif line_parts[0] == 'current' and line_parts[1] == 'vfit':
            self.read_fit_ps = False
            self.read_fit_uv = True
            self.read_fit_t = False
            self.read_fit_q = False
    
    def parse_fit_file(self):
        """ parse lines of fit file and extract statistics
        """
        self.read_fit_ps = True
        self.read_fit_uv = False
        self.read_fit_t = False
        self.read_fit_q = False

        for line_number, line in enumerate(self.lines):
            line_parts = line.split()

            if len(line_parts) >= 2:

                # Handle mode-switching lines
                if line_parts[0] == 'current' and line_parts[1] == 'vfit':
                    self.read_fit_ps = False
                    self.read_fit_uv = True
                    self.read_fit_t = False
                    self.read_fit_q = False

                elif len(line_parts) > 3 and line_parts[0] == 'current' and line_parts[3] == 'temperature':
                    self.read_fit_ps = False
                    self.read_fit_uv = False
                    self.read_fit_t = True
                    self.read_fit_q = False

                elif len(line_parts) > 3 and line_parts[0] == 'current' and line_parts[3] == 'q':
                    self.read_fit_ps = False
                    self.read_fit_uv = False
                    self.read_fit_t = False
                    self.read_fit_q = True

                elif line_parts[0] in {'OZINFO_READ:', 'RADINFO_READ'}:
                    self.read_fit_ps = False
                    self.read_fit_uv = False
                    self.read_fit_t = False
                    self.read_fit_q = False

                # Only dispatch to extractors for non-mode lines
                elif self.read_fit_ps:
                    self.extract_fit_ps(line_parts, variable_name='fit_psfc_data')

                elif self.read_fit_uv and 'fit_uv_data' in self.config.vars_to_harvest:
                    self.extract_fit_obs_plevs(line_parts, variable_name='fit_uv_data')

                elif self.read_fit_t and 'fit_t_data' in self.config.vars_to_harvest:
                    self.extract_fit_obs_plevs(line_parts, variable_name='fit_t_data')

                elif self.read_fit_q and 'fit_q_data' in self.config.vars_to_harvest:
                    self.extract_fit_obs_plevs(line_parts, variable_name='fit_q_data')
