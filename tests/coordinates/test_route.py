import pytest

from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate
from bok_ucgs_fish_route.coordinates.route import RouteSegment


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