import pytest

from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate


@pytest.mark.parametrize("lon, lat, altitude", [
    (0.0, 0.0, 0.0),
    (23.1344738, 37.4285837, 10.5),  # Example with altitude
    (-74.0060, 40.7128, 0.0),  # New York City
    (139.6917, 35.6895, -10.0),  # Tokyo with negative altitude (below sea level)
])
def test_waypoint_coordinate_init(lon, lat, altitude):
    """
    Test the initialization of WaypointCoordinate with various coordinates.

    The class should correctly store longitude, latitude, and altitude values.
    """
    waypoint = WaypointCoordinate(lon, lat, altitude)

    assert waypoint.lon == lon
    assert waypoint.lat == lat
    assert waypoint.altitude == altitude


def test_waypoint_coordinate_default_altitude():
    """Test that the default altitude is 0.0 when not specified."""
    waypoint = WaypointCoordinate(-74.0060, 40.7128)
    assert waypoint.altitude == 0.0


@pytest.mark.parametrize("input_value, expected_value", [
    ("37.4285837", 37.4285837),  # String to float conversion
    (42, 42.0),  # Integer to float conversion
])
def test_waypoint_coordinate_type_conversion(input_value, expected_value):
    """Test that input values are converted to float."""
    waypoint = WaypointCoordinate(input_value, input_value, input_value)

    assert isinstance(waypoint.lat, float)
    assert isinstance(waypoint.lon, float)
    assert isinstance(waypoint.altitude, float)

    assert waypoint.lat == expected_value
    assert waypoint.lon == expected_value
    assert waypoint.altitude == expected_value


def test_waypoint_coordinate_equality():
    """Test the equality comparison of WaypointCoordinate objects."""
    waypoint1 = WaypointCoordinate(-74.0060, 40.7128, 10.0)
    waypoint2 = WaypointCoordinate(-74.0060, 40.7128, 10.0)
    waypoint3 = WaypointCoordinate(139.6917, 35.6895, 0.0)

    assert waypoint1 == waypoint2
    assert waypoint1 != waypoint3
    assert waypoint1 != "not a waypoint"


def test_waypoint_coordinate_repr():
    """Test the string representation of WaypointCoordinate."""
    waypoint = WaypointCoordinate(-74.0060, 40.7128, 10.0)
    expected_repr = "WaypointCoordinate(lon=-74.006, lat=40.7128, altitude=10.0)"

    # The string representation should contain all the values
    assert str(waypoint) == expected_repr
