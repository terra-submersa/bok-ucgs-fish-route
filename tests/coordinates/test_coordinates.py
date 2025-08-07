import pytest
import math
from pytest import approx
from bok_ucgs_fish_route.coordinates import wgs_to_radians


@pytest.mark.parametrize("lon_deg, lat_deg", [
    (0.0, 0.0),
    (180.0, 0.0),
    (0.0, 90.0),
    (23.1344738, 37.4285837),  # Example from try_pyproj.py
    (-74.0060, 40.7128),  # New York City
    (139.6917, 35.6895),  # Tokyo
])
def test_wgs_to_radians(lon_deg, lat_deg):
    """
    Test the wgs_to_radians function with various coordinates.
    
    The function should correctly convert WGS84 coordinates from degrees to radians.
    """
    # Calculate expected values using math.radians
    expected_lon_rad = math.radians(lon_deg)
    expected_lat_rad = math.radians(lat_deg)
    
    # Get actual values from our function
    lon_rad, lat_rad = wgs_to_radians(lon_deg, lat_deg)
    
    # Use pytest's approx for floating point comparison
    assert lon_rad == approx(expected_lon_rad, abs=1e-10)
    assert lat_rad == approx(expected_lat_rad, abs=1e-10)


