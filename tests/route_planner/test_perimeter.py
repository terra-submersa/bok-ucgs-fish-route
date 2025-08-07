import pytest

from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate
from bok_ucgs_fish_route.coordinates.route import RouteSegment
from bok_ucgs_fish_route.route_planner import create_route_segment_perimeter


@pytest.mark.parametrize("corner1, corner2, speed, expected_waypoints", [
    # Test case 1: Simple rectangle
    (
        (37.428, 23.134),  # corner1 (lat1, lon1)
        (37.430, 23.136),  # corner2 (lat2, lon2)
        2.5,  # speed
        [  # expected waypoints in clockwise order
            WaypointCoordinate(37.428, 23.134),  # Start at corner1
            WaypointCoordinate(37.428, 23.136),  # Move east
            WaypointCoordinate(37.430, 23.136),  # Move north
            WaypointCoordinate(37.430, 23.134),  # Move west
            WaypointCoordinate(37.428, 23.134),  # Back to start
        ]
    ),
    # Test case 2: Rectangle with negative coordinates
    (
        (-34.605, -58.370),  # corner1 (lat1, lon1)
        (-34.600, -58.365),  # corner2 (lat2, lon2)
        1.0,  # speed
        [  # expected waypoints in clockwise order
            WaypointCoordinate(-34.605, -58.370),
            WaypointCoordinate(-34.605, -58.365),
            WaypointCoordinate(-34.600, -58.365),
            WaypointCoordinate(-34.600, -58.370),
            WaypointCoordinate(-34.605, -58.370),
        ]
    ),
    # Test case 3: Rectangle with corners in different order
    (
        (42.350, -71.105),  # corner1 (lat1, lon1)
        (42.360, -71.095),  # corner2 (lat2, lon2)
        5.0,  # speed
        [  # expected waypoints in clockwise order
            WaypointCoordinate(42.350, -71.105),
            WaypointCoordinate(42.350, -71.095),
            WaypointCoordinate(42.360, -71.095),
            WaypointCoordinate(42.360, -71.105),
            WaypointCoordinate(42.350, -71.105),
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
    ((37.428, 23.134), (37.430, 23.136), 1.0),
    ((37.428, 23.134), (37.430, 23.136), 2.5),
    ((37.428, 23.134), (37.430, 23.136), 10.0),
])
def test_create_route_segment_perimeter_speed(corner1, corner2, speed):
    """Test that the speed is correctly set in the created route segment."""
    route_segment = create_route_segment_perimeter(corner1, corner2, speed)
    assert route_segment.speed == speed


def test_create_route_segment_perimeter_completes_loop():
    """Test that the created route segment forms a complete loop (first waypoint equals last waypoint)."""
    corner1 = (37.428, 23.134)
    corner2 = (37.430, 23.136)
    route_segment = create_route_segment_perimeter(corner1, corner2, 2.5)
    
    # First and last waypoints should be the same to complete the loop
    assert route_segment.waypoints[0] == route_segment.waypoints[-1]


