"""Data-free tests of the daily_bfg request validation, regions and masks."""
import numpy as np
import pytest
import xarray as xr

from score_hv.harvesters.daily_bfg import DailyBFGConfig, DEFAULT_REGION
from score_hv.mask_utils import MaskCatalog
from score_hv.region_utils import GeoRegionsCatalog

BASE_CONFIG = {'harvester_name': 'daily_bfg',
               'filenames': ['bfg.nc'],
               'statistic': ['mean'],
               'variable': ['tmp2m']}


def make_config(**kwargs):
    return DailyBFGConfig(dict(BASE_CONFIG, **kwargs))


def grid_dataset():
    lat = np.array([60.0, 0.0, -60.0])
    lon = np.array([0.0, 90.0, 180.0, 270.0, 350.0])
    return xr.Dataset({'tmp2m': (('grid_yt', 'grid_xt'), np.zeros((3, 5)))},
                      coords={'grid_yt': lat, 'grid_xt': lon})


@pytest.mark.parametrize('resolution', ['1536', '768', '1536x768x1'])
def test_invalid_resolution(resolution):
    with pytest.raises(ValueError):
        make_config(resolution=resolution)


def test_default_resolution_and_region():
    config = make_config()
    assert config.resolution == '1536x768'
    assert config.gridcell_area_data_path.endswith('1536x768_20231116.nc')
    assert config.regions is DEFAULT_REGION


@pytest.mark.parametrize('surface_mask, expected', [
    (None, None), ([], None), ('land', ['land']), (['water', 'none'], ['water', 'none'])])
def test_surface_mask_normalized(surface_mask, expected):
    assert make_config(surface_mask=surface_mask).surface_mask == expected


@pytest.mark.parametrize('surface_mask', ['lnd', ['land', 'ocean']])
def test_invalid_surface_mask(surface_mask):
    with pytest.raises(ValueError):
        make_config(surface_mask=surface_mask)


def test_default_region_is_global():
    catalog = GeoRegionsCatalog(grid_dataset())
    catalog.add_user_region(DEFAULT_REGION)
    assert (catalog.west_long['global'], catalog.east_long['global']) == (0.0, 360.0)
    catalog.get_region_indices('global')
    assert len(catalog.lat_indices['global']) == 3
    assert len(catalog.long_indices['global']) == 5


def test_region_longitude_aliases_and_wrap():
    catalog = GeoRegionsCatalog(grid_dataset())
    catalog.add_user_region({'wrap': {'north_lat': 30, 'south_lat': -30,
                                      'west_lon': 340, 'east_lon': 95}})
    assert (catalog.west_long['wrap'], catalog.east_long['wrap']) == (340, 95)
    catalog.get_region_indices('wrap')
    assert list(catalog.lat_indices['wrap']) == [1]
    assert list(catalog.long_indices['wrap']) == [0, 1, 4]


@pytest.mark.parametrize('bounds', [{'north_lat': 10, 'west_longitude': 5},
                                    {'west_lon': 5, 'west_long': 5}])
def test_invalid_region_bounds(bounds):
    catalog = GeoRegionsCatalog(grid_dataset())
    with pytest.raises(KeyError):
        catalog.add_user_region({'bad': bounds})


def test_none_mask_keeps_automatic_mask():
    variable = xr.DataArray([1.0, np.nan, 3.0])
    fraction = xr.DataArray([1.0, np.nan, 0.5])
    lfrac = xr.DataArray([0.0, 0.0, 1.0])
    sotyp = xr.DataArray([0, 0, 1])
    masked_variable, masked_frac = MaskCatalog().user_mask(
        'none', variable, fraction, lfrac, sotyp, icec=xr.DataArray([0, 0, 0]))
    assert masked_variable.equals(variable)
    assert masked_frac.equals(fraction)


def test_user_mask_rejects_unknown_mask():
    data = xr.DataArray([1.0])
    with pytest.raises(ValueError):
        MaskCatalog().user_mask('ocean', data, data, data, data, icec=data)
