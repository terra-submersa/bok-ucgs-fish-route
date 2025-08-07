import pytest

from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate
from bok_ucgs_fish_route.coordinates.route import RouteSegment, create_route_segment_from_coordinates


@pytest.fixture
def sample_waypoints():
    """Fixture providing a list of sample waypoints for testing."""
    return [
        WaypointCoordinate(37.4285837, 23.1344738, 0.0),
        WaypointCoordinate(37.4286000, 23.1345000, 1.0),
        WaypointCoordinate(37.4286500, 23.1346000, 2.0),
    ]


@pytest.mark.parametrize("speed", [
    1.0,
    2.5,
    10.0,
])
def test_route_segment_init(sample_waypoints, speed):
    """
    Test the initialization of RouteSegment with various speeds.
    
    The class should correctly store waypoints and speed values.
    """
    route_segment = RouteSegment(sample_waypoints, speed)
    
    assert route_segment.waypoints == sample_waypoints
    assert route_segment.speed == speed
    
    # Ensure the waypoints list is a copy, not the original reference
    assert route_segment.waypoints is not sample_waypoints


def test_route_segment_empty_waypoints():
    """Test that RouteSegment raises ValueError when initialized with empty waypoints list."""
    with pytest.raises(ValueError, match="RouteSegment must contain at least one waypoint"):
        RouteSegment([], 1.0)


@pytest.mark.parametrize("invalid_speed", [
    0.0,
    -1.0,
    -10.5,
])
def test_route_segment_invalid_speed(sample_waypoints, invalid_speed):
    """Test that RouteSegment raises ValueError when initialized with non-positive speed."""
    with pytest.raises(ValueError, match="Speed must be positive"):
        RouteSegment(sample_waypoints, invalid_speed)


@pytest.mark.parametrize("input_value, expected_value", [
    ("2.5", 2.5),  # String to float conversion
    (5, 5.0),      # Integer to float conversion
])
def test_route_segment_speed_type_conversion(sample_waypoints, input_value, expected_value):
    """Test that speed input value is converted to float."""
    route_segment = RouteSegment(sample_waypoints, input_value)
    
    assert isinstance(route_segment.speed, float)
    assert route_segment.speed == expected_value


def test_route_segment_equality(sample_waypoints):
    """Test the equality comparison of RouteSegment objects."""
    route_segment1 = RouteSegment(sample_waypoints, 2.5)
    route_segment2 = RouteSegment(sample_waypoints, 2.5)
    route_segment3 = RouteSegment(sample_waypoints, 3.0)
    route_segment4 = RouteSegment(sample_waypoints[:2], 2.5)  # Different waypoints
    
    assert route_segment1 == route_segment2
    assert route_segment1 != route_segment3
    assert route_segment1 != route_segment4
    assert route_segment1 != "not a route segment"


def test_route_segment_repr(sample_waypoints):
    """Test the string representation of RouteSegment."""
    route_segment = RouteSegment(sample_waypoints, 2.5)
    repr_str = repr(route_segment)
    
    # The string representation should contain all the values
    assert "RouteSegment" in repr_str
    assert "waypoints=" in repr_str
    assert "speed=2.5" in repr_str
    
    for waypoint in sample_waypoints:
        assert str(waypoint) in repr_str


@pytest.fixture
def sample_coordinates_wgs():
    """Fixture providing a list of sample coordinate tuples for testing."""
    return [
        (23.1344738, 37.4285837),  # (lon, lat) format
        (23.1345000, 37.4286000),
        (23.1346000, 37.4286500),
    ]

@pytest.fixture
def sample_coordinates_utm():
    """Fixture providing a list of sample coordinate tuples for testing."""
    return [
        (688857.37, 4144556.90),  # (lon, lat) format
        (688859.63, 4144558.73),
        (688868.36, 4144564.48),
    ]


@pytest.mark.parametrize("altitude, speed", [
    (0.0, 1.0),
    (10.5, 2.5),
    (-5.0, 10.0),
])
def test_create_route_segment_from_coordinates(sample_coordinates_wgs, altitude, speed, sample_coordinates_utm):
    """
    Test that create_route_segment_from_coordinates correctly creates a route segment
    with the specified coordinates, altitude, and speed.
    """
    route_segment = create_route_segment_from_coordinates(sample_coordinates_utm, altitude, speed, "32634")
    
    # Check that the route segment has the correct speed
    assert route_segment.speed == speed
    
    # Check that the correct number of waypoints were created
    assert len(route_segment.waypoints) == len(sample_coordinates_utm)
    
    # Check that each waypoint has the correct coordinates and altitude
    for i, (lon, lat) in enumerate(sample_coordinates_wgs):
        waypoint = route_segment.waypoints[i]
        pytest.approx(lon, waypoint.lon, abs=1e-3)
        pytest.approx(lat, waypoint.lat, abs=1e-3)
        assert waypoint.altitude == altitude


def test_create_route_segment_from_coordinates_empty_list():
    """Test that create_route_segment_from_coordinates raises ValueError when given an empty list."""
    with pytest.raises(ValueError, match="Coordinates list must not be empty"):
        create_route_segment_from_coordinates([], 0.0, 1.0, "")


def test_create_route_segment_from_coordinates_invalid_speed():
    """Test that create_route_segment_from_coordinates raises ValueError when given a non-positive speed."""
    with pytest.raises(ValueError, match="Speed must be positive"):
        create_route_segment_from_coordinates([(23.1344738, 37.4285837)], 0.0, 0.0, "32634")