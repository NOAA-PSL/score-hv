"""
Work by Jessica Knezha

Unit tests for observation information log harvester
Tests each variable for valid number of outputs
Tests valid dictionary and yaml input configurations covering all valid variables and various capitalization
Tests for invalid config inputs
"""

import os
import pathlib
import pytest
import yaml

from score_hv import hv_registry
from score_hv.harvester_base import harvest


PYTEST_CALLING_DIR = pathlib.Path(__file__).parent.resolve()
LOG_HARVESTER_CONFIG_TEMP__VALID = 'log_harvester_config_temp__valid.yaml'
LOG_HARVESTER_CONFIG_PRESSURE__VALID = 'log_harvester_config_pressure__valid.yaml'
LOG_HARVESTER_DATA__VALID = 'test_log_cmpbqm.txt'

DATA_DIR = 'data'
CONFIGS_DIR = 'configs'

file_path_obs_data = os.path.join(
    PYTEST_CALLING_DIR,
    DATA_DIR,
    LOG_HARVESTER_DATA__VALID
)


# TEMPERATURE TESTS
VALID_CONFIG_DICT_TEMP = {
    'harvester_name': hv_registry.OBS_INFO_LOG,
    'filename': file_path_obs_data,
    'variable': 'TEMPERATURE'
}


def test_log_harvester_temperature_valid_dict():
    data1 = harvest(VALID_CONFIG_DICT_TEMP)
    print(f'harvested {len(data1)} records using config: {VALID_CONFIG_DICT_TEMP}')
    assert len(data1) > 0
    assert len(data1) is 11


def test_log_harvester_temperature_valid_yaml():
    yaml_filename = os.path.join(
        PYTEST_CALLING_DIR,
        CONFIGS_DIR,
        LOG_HARVESTER_CONFIG_TEMP__VALID
    )

    with open(yaml_filename, 'w', encoding='utf8') as file:
        yaml.dump(VALID_CONFIG_DICT_TEMP, file)

    data1 = harvest(yaml_filename)
    print(f'harvested {len(data1)} records using config: {yaml_filename}')
    assert len(data1) > 0
    assert len(data1) is 11

    os.remove(yaml_filename)


# PRESSURE TESTS
VALID_CONFIG_DICT_PRESSURE = {
    'harvester_name' : hv_registry.OBS_INFO_LOG,
    'filename' : file_path_obs_data,
    'variable' : 'PRESSURE'
}


def test_log_harvester_pressure_valid_dict():
    data1 = harvest(VALID_CONFIG_DICT_PRESSURE)
    print(f'harvested {len(data1)} records using config: {VALID_CONFIG_DICT_PRESSURE}')
    assert len(data1) > 0
    assert len(data1) is 35


def test_log_harvester_pressure_valid_yaml():
    yaml_filename = os.path.join(
        PYTEST_CALLING_DIR,
        CONFIGS_DIR,
        LOG_HARVESTER_CONFIG_PRESSURE__VALID
    )

    with open(yaml_filename, 'w', encoding='utf8') as file:
        yaml.dump(VALID_CONFIG_DICT_PRESSURE, file)

    data1 = harvest(yaml_filename)
    print(f'harvested {len(data1)} records using config: {yaml_filename}')
    assert len(data1) > 0
    assert len(data1) is 35

    os.remove(yaml_filename)

# SPECIFIC HUMIDITY TESTS
VALID_CONFIG_DICT_SHUM_UPPER = {
    'harvester_name' : hv_registry.OBS_INFO_LOG,
    'filename' : file_path_obs_data,
    'variable' : 'SPECIFIC HUMIDITY'
}

VALID_CONFIG_DICT_SHUM_TITLE = {
    'harvester_name' : hv_registry.OBS_INFO_LOG,
    'filename' : file_path_obs_data,
    'variable' : 'Specific Humidity'
}

VALID_CONFIG_DICT_SHUM_LOWER = {
    'harvester_name' : hv_registry.OBS_INFO_LOG,
    'filename' : file_path_obs_data,
    'variable' : 'specific humidity'
}

def test_log_harvester_shum_valid_dict_uppercase():
    data1 = harvest(VALID_CONFIG_DICT_SHUM_UPPER)
    print(f'harvested {len(data1)} records using config: {VALID_CONFIG_DICT_SHUM_UPPER}')
    assert len(data1) > 0
    assert len(data1) is 7


def test_log_harvester_shum_valid_dict_titlecase():
    data1 = harvest(VALID_CONFIG_DICT_SHUM_TITLE)
    print(f'harvested {len(data1)} records using config: {VALID_CONFIG_DICT_SHUM_TITLE}')
    assert len(data1) > 0
    assert len(data1) is 7


def test_log_harvester_shum_valid_dict_lowercase():
    data1 = harvest(VALID_CONFIG_DICT_SHUM_LOWER)
    print(f'harvested {len(data1)} records using config: {VALID_CONFIG_DICT_SHUM_LOWER}')
    assert len(data1) > 0
    assert len(data1) is 7


# RELATIVE HUMIDITY TESTS
VALID_CONFIG_DICT_RHUM = {
    'harvester_name': hv_registry.OBS_INFO_LOG,
    'filename': file_path_obs_data,
    'variable': 'RELATIVE HUMIDITY'
}


def test_log_harvester_rhum_valid_dict():
    data1 = harvest(VALID_CONFIG_DICT_RHUM)
    print(f'harvested {len(data1)} records using config: {VALID_CONFIG_DICT_RHUM}')
    assert len(data1) is 0


# HEIGHT TESTS
VALID_CONFIG_DICT_HEIGHT_UPPER = {
    'harvester_name' : hv_registry.OBS_INFO_LOG,
    'filename' : file_path_obs_data,
    'variable' : 'HEIGHT'
}

VALID_CONFIG_DICT_HEIGHT_LOWER = {
    'harvester_name' : hv_registry.OBS_INFO_LOG,
    'filename' : file_path_obs_data,
    'variable' : 'height'
}

VALID_CONFIG_DICT_HEIGHT_RANDOM = {
    'harvester_name' : hv_registry.OBS_INFO_LOG,
    'filename' : file_path_obs_data,
    'variable' : 'HEighT'
}

def test_log_harvester_height_valid_dict_uppercase():
    data1 = harvest(VALID_CONFIG_DICT_HEIGHT_UPPER)
    print(f'harvested {len(data1)} records using config: {VALID_CONFIG_DICT_HEIGHT_UPPER}')
    assert len(data1) > 0
    assert len(data1) is 29


def test_log_harvester_height_valid_dict_lowercase():
    data1 = harvest(VALID_CONFIG_DICT_HEIGHT_LOWER)
    print(f'harvested {len(data1)} records using config: {VALID_CONFIG_DICT_HEIGHT_LOWER}')
    assert len(data1) > 0
    assert len(data1) is 29


def test_log_harvester_height_valid_dict_randomcase():
    data1 = harvest(VALID_CONFIG_DICT_HEIGHT_RANDOM)
    print(f'harvested {len(data1)} records using config: {VALID_CONFIG_DICT_HEIGHT_RANDOM}')
    assert len(data1) > 0
    assert len(data1) is 29


# WIND COMPONENTS TESTS
VALID_CONFIG_DICT_WIND = {
    'harvester_name' : hv_registry.OBS_INFO_LOG,
    'filename' : file_path_obs_data,
    'variable' : 'WIND COMPONENTS'
}


def test_log_harvester_wind_valid_dict():
    data1 = harvest(VALID_CONFIG_DICT_WIND)
    print(f'harvested {len(data1)} records using config: {VALID_CONFIG_DICT_WIND}')
    assert len(data1) > 0
    assert len(data1) is 24


# PRECIPITABLE H2O TESTS
VALID_CONFIG_DICT_H2O = {
    'harvester_name': hv_registry.OBS_INFO_LOG,
    'filename': file_path_obs_data,
    'variable': 'PRECIPITABLE H2O'
}


def test_log_harvester_h2o_valid_dict():
    data1 = harvest(VALID_CONFIG_DICT_H2O)
    print(f'harvested {len(data1)} records using config: {VALID_CONFIG_DICT_H2O}')
    assert len(data1) > 0
    assert len(data1) is 1


# INVALID INPUT TESTS
def test_log_invalid_no_file():
    invalid_config = {
        'harvester_name': hv_registry.OBS_INFO_LOG,
        'variable': 'TEMPERATURE'
    }
    with pytest.raises(KeyError):
        data1 = harvest(invalid_config)


def test_log_empty_filename():
    invalid_config = {
        'harvester_name': hv_registry.OBS_INFO_LOG,
        'filename': '',
        'variable': 'TEMPERATURE'
    }
    with pytest.raises(ValueError):
        data1 = harvest(invalid_config)


def test_log_invalid_var():
    invalid_config = {
        'harvester_name': hv_registry.OBS_INFO_LOG,
        'filename': file_path_obs_data,
        'variable': 'random name'
    }
    with pytest.raises(ValueError):
        data1 = harvest(invalid_config)


def test_log_invalid_no_var():
    invalid_config = {
        'harvester_name': hv_registry.OBS_INFO_LOG,
        'filename': file_path_obs_data
    }
    with pytest.raises(KeyError):
        data1 = harvest(invalid_config)


def test_log_invalid_misspelled_var():
    invalid_config = {
        'harvester_name': hv_registry.OBS_INFO_LOG,
        'filename': file_path_obs_data,
        'variable': 'presure'
    }
    with pytest.raises(ValueError):
        data1 = harvest(invalid_config)


def test_log_invalid_empty_var():
    invalid_config = {
        'harvester_name': hv_registry.OBS_INFO_LOG,
        'filename': file_path_obs_data,
        'variable': ''
    }
    with pytest.raises(ValueError):
        data1 = harvest(invalid_config)