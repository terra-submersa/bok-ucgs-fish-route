import pytest

from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate
from bok_ucgs_fish_route.coordinates.route import RouteSegment
from bok_ucgs_fish_route.route_planner import create_route_segment_perimeter


@pytest.mark.parametrize("corner1, corner2, speed, expected_waypoints", [
    # Test case 1: Simple rectangle
    (
        (23.134, 37.428),  # corner1 (lon1, lat1)
        (23.136, 37.430),  # corner2 (lon2, lat2)
        2.5,  # speed
        [  # expected waypoints in clockwise order
            WaypointCoordinate(23.134, 37.428),  # Start at corner1
            WaypointCoordinate(23.136, 37.428),  # Move east
            WaypointCoordinate(23.136, 37.430),  # Move north
            WaypointCoordinate(23.134, 37.430),  # Move west
            WaypointCoordinate(23.134, 37.428),  # Back to start
        ]
    ),
    # Test case 2: Rectangle with negative coordinates
    (
        (-58.370, -34.605),  # corner1 (lon1, lat1)
        (-58.365, -34.600),  # corner2 (lon2, lat2)
        1.0,  # speed
        [  # expected waypoints in clockwise order
            WaypointCoordinate(-58.370, -34.605),
            WaypointCoordinate(-58.365, -34.605),
            WaypointCoordinate(-58.365, -34.600),
            WaypointCoordinate(-58.370, -34.600),
            WaypointCoordinate(-58.370, -34.605),
        ]
    ),
    # Test case 3: Rectangle with corners in different order
    (
        (-71.105, 42.350),  # corner1 (lon1, lat1)
        (-71.095, 42.360),  # corner2 (lon2, lat2)
        5.0,  # speed
        [  # expected waypoints in clockwise order
            WaypointCoordinate(-71.105, 42.350),
            WaypointCoordinate(-71.095, 42.350),
            WaypointCoordinate(-71.095, 42.360),
            WaypointCoordinate(-71.105, 42.360),
            WaypointCoordinate(-71.105, 42.350),
        ]
    ),
])
def test_create_route_segment_perimeter(corner1, corner2, speed, expected_waypoints):
    """
    Test that create_route_segment_perimeter correctly creates a route segment
    that passes through the 4 corners of a rectangle.
    """
    # Create the route segment
    route_segment = create_route_segment_perimeter(corner1, corner2, speed)
    
    # Verify it's a RouteSegment instance
    assert isinstance(route_segment, RouteSegment)
    
    # Verify the speed is set correctly
    assert route_segment.speed == speed
    
    # Verify the waypoints are correct
    assert len(route_segment.waypoints) == 5  # 4 corners + return to start
    assert route_segment.waypoints == expected_waypoints


@pytest.mark.parametrize("corner1, corner2, speed", [
    # Test with different speed values
    ((23.134, 37.428), (23.136, 37.430), 1.0),
    ((23.134, 37.428), (23.136, 37.430), 2.5),
    ((23.134, 37.428), (23.136, 37.430), 10.0),
])
def test_create_route_segment_perimeter_speed(corner1, corner2, speed):
    """Test that the speed is correctly set in the created route segment."""
    route_segment = create_route_segment_perimeter(corner1, corner2, speed)
    assert route_segment.speed == speed


def test_create_route_segment_perimeter_completes_loop():
    """Test that the created route segment forms a complete loop (first waypoint equals last waypoint)."""
    corner1 = (23.134, 37.428)
    corner2 = (23.136, 37.430)
    route_segment = create_route_segment_perimeter(corner1, corner2, 2.5)
    
    # First and last waypoints should be the same to complete the loop
    assert route_segment.waypoints[0] == route_segment.waypoints[-1]


