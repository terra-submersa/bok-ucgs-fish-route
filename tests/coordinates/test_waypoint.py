import pytest

from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate


@pytest.mark.parametrize("lat, lon, altitude", [
    (0.0, 0.0, 0.0),
    (37.4285837, 23.1344738, 10.5),  # Example with altitude
    (40.7128, -74.0060, 0.0),  # New York City
    (35.6895, 139.6917, -10.0),  # Tokyo with negative altitude (below sea level)
])
def test_waypoint_coordinate_init(lat, lon, altitude):
    """
    Test the initialization of WaypointCoordinate with various coordinates.

    The class should correctly store latitude, longitude, and altitude values.
    """
    waypoint = WaypointCoordinate(lat, lon, altitude)

    assert waypoint.lat == lat
    assert waypoint.lon == lon
    assert waypoint.altitude == altitude


def test_waypoint_coordinate_default_altitude():
    """Test that the default altitude is 0.0 when not specified."""
    waypoint = WaypointCoordinate(40.7128, -74.0060)
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
    waypoint1 = WaypointCoordinate(40.7128, -74.0060, 10.0)
    waypoint2 = WaypointCoordinate(40.7128, -74.0060, 10.0)
    waypoint3 = WaypointCoordinate(35.6895, 139.6917, 0.0)

    assert waypoint1 == waypoint2
    assert waypoint1 != waypoint3
    assert waypoint1 != "not a waypoint"


def test_waypoint_coordinate_repr():
    """Test the string representation of WaypointCoordinate."""
    waypoint = WaypointCoordinate(40.7128, -74.0060, 10.0)
    expected_repr = "WaypointCoordinate(lat=40.7128, lon=-74.006, altitude=10.0)"

    # The string representation should contain all the values
    assert str(waypoint) == expected_repr
