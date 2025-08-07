import pytest

from bok_ucgs_fish_route.coordinates.route import RouteSegment, create_route_segment_from_coordinates
from bok_ucgs_fish_route.route_planner import create_route_segment_perimeter


@pytest.mark.parametrize("corner1, corner2, expected_coordinates", [
    # Test case 1: Simple rectangle
    (
        (23.134, 37.428),  # corner1 (lon1, lat1)
        (23.136, 37.430),  # corner2 (lon2, lat2)
        [  # expected coordinates in clockwise order
            (23.134, 37.428),  # Start at corner1
            (23.136, 37.428),  # Move east
            (23.136, 37.430),  # Move north
            (23.134, 37.430),  # Move west
            (23.134, 37.428),  # Back to start
        ]
    ),
    # Test case 2: Rectangle with negative coordinates
    (
        (-58.370, -34.605),  # corner1 (lon1, lat1)
        (-58.365, -34.600),  # corner2 (lon2, lat2)
        [  # expected coordinates in clockwise order
            (-58.370, -34.605),
            (-58.365, -34.605),
            (-58.365, -34.600),
            (-58.370, -34.600),
            (-58.370, -34.605),
        ]
    ),
    # Test case 3: Rectangle with corners in different order
    (
        (-71.105, 42.350),  # corner1 (lon1, lat1)
        (-71.095, 42.360),  # corner2 (lon2, lat2)
        [  # expected coordinates in clockwise order
            (-71.105, 42.350),
            (-71.095, 42.350),
            (-71.095, 42.360),
            (-71.105, 42.360),
            (-71.105, 42.350),
        ]
    ),
])
def test_create_route_segment_perimeter(corner1, corner2, expected_coordinates):
    """
    Test that create_route_segment_perimeter correctly creates a list of coordinates
    that passes through the 4 corners of a rectangle.
    """
    # Create the coordinates
    coordinates = create_route_segment_perimeter(corner1, corner2)
    
    # Verify it's a list
    assert isinstance(coordinates, list)
    
    # Verify the coordinates are correct
    assert len(coordinates) == 5  # 4 corners + return to start
    assert coordinates == expected_coordinates


@pytest.mark.parametrize("corner1, corner2, speed", [
    # Test with different speed values
    ((23.134, 37.428), (23.136, 37.430), 1.0),
    ((23.134, 37.428), (23.136, 37.430), 2.5),
    ((23.134, 37.428), (23.136, 37.430), 10.0),
])
def test_create_route_segment_perimeter_speed(corner1, corner2, speed):
    """Test that the speed is correctly set in the created route segment."""
    coordinates = create_route_segment_perimeter(corner1, corner2)
    altitude = 0.0  # Default altitude
    route_segment = create_route_segment_from_coordinates(coordinates, altitude, speed)
    assert route_segment.speed == speed


def test_create_route_segment_perimeter_completes_loop():
    """Test that the created route segment forms a complete loop (first waypoint equals last waypoint)."""
    corner1 = (23.134, 37.428)
    corner2 = (23.136, 37.430)
    coordinates = create_route_segment_perimeter(corner1, corner2)
    altitude = 0.0  # Default altitude
    speed = 2.5
    route_segment = create_route_segment_from_coordinates(coordinates, altitude, speed)
    
    # First and last waypoints should be the same to complete the loop
    assert route_segment.waypoints[0] == route_segment.waypoints[-1]


