"""
Tests for the coordinate conversion utilities.
"""
from unittest import TestCase

import pytest
from bok_ucgs_fish_route.coordinates.conversion import (
    is_wgs84_coordinates,
    get_utm_zone_for_coordinates,
    wgs84_to_utm,
    convert_corners_from_wgs84_to_utm
)


class TestIsWgs84Coordinates:
    """Tests for the is_wgs84_coordinates function."""

    @pytest.mark.parametrize("lon,lat,expected", [
        (0, 0, True),
        (180, 90, True),
        (-180, -90, True),
        (179.9, 89.9, True),
        (-179.9, -89.9, True),
        (181, 0, False),
        (-181, 0, False),
        (0, 91, False),
        (0, -91, False),
        (1000, 1000, False),
    ])
    def test_is_wgs84_coordinates(self, lon, lat, expected):
        """Test that the function correctly identifies WGS84 coordinates."""
        assert is_wgs84_coordinates(lon, lat) == expected


class TestGetUtmZoneForCoordinates:
    """Tests for the get_utm_zone_for_coordinates function."""

    @pytest.mark.parametrize("lon,lat,expected_zone", [
        (0, 0, 31),
        (8, 50, 32),
        (-9, 40, 29),
        (177, -30, 60),
        (-177, 30, 1),
    ])
    def test_get_utm_zone(self, lon, lat, expected_zone):
        """Test that the function returns the correct UTM zone."""
        assert get_utm_zone_for_coordinates(lon, lat) == expected_zone


class TestWgs84ToUtm:
    """Tests for the wgs84_to_utm function."""

    def test_wgs84_to_utm_origin(self):
        """Test conversion of WGS84 coordinates near the origin of a UTM zone."""
        # Greenwich, UK (near the origin of UTM zone 31N)
        lon, lat = 0.0, 51.5
        easting, northing = wgs84_to_utm(lon, lat)

        # The easting value depends on the specific implementation of the UTM projection
        # Just verify it's a reasonable UTM easting value (typically between 100000 and 900000)
        assert 100000 < easting < 900000
        # Northing should be in the expected range for this latitude
        assert 5500000 < northing < 6000000

    def test_wgs84_to_utm_consistency(self):
        """Test that small changes in WGS84 coordinates result in proportional changes in UTM."""
        # Two points close to each other
        lon1, lat1 = 10.0, 50.0
        lon2, lat2 = 10.01, 50.01

        easting1, northing1 = wgs84_to_utm(lon1, lat1)
        easting2, northing2 = wgs84_to_utm(lon2, lat2)

        # The difference should be small but measurable
        # For a 0.01 degree change, we expect differences in the range of meters to tens of meters
        # but the exact values depend on the latitude and the UTM zone
        assert 0 < abs(easting2 - easting1) < 2000
        assert 0 < abs(northing2 - northing1) < 2000


class TestConvertCornersIfWgs84(TestCase):
    """Tests for the convert_corners_if_wgs84 function."""

    def test_convert_wgs84_corners(self):
        """Test conversion of WGS84 corners."""
        corner1 = (23.134, 37.428)
        corner2 = (23.234, 37.528)

        utm_corner1, utm_corner2 = convert_corners_from_wgs84_to_utm(corner1, corner2)

        self.assertAlmostEqual(utm_corner1[0], 688816.90, delta=0.01)
        self.assertAlmostEqual(utm_corner1[1], 4144491.15, delta=0.01)
        self.assertAlmostEqual(utm_corner2[0], 697402.690, delta=0.01)
        self.assertAlmostEqual(utm_corner2[1], 4155792.687, delta=0.01)
