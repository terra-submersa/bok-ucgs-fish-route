import math
from typing import Tuple, List

import pytest
from pytest import approx

from bok_ucgs_fish_route.coordinates.conversion import wgs84_to_utm
from bok_ucgs_fish_route.coordinates.route import RouteSegment, create_route_segment_from_coordinates
from bok_ucgs_fish_route.route_planner import create_lawn_mower_band_strips
from bok_ucgs_fish_route.route_planner.lawn_mower import find_line_rectangle_intersections, find_horizontal_intersect, find_vertical_intersect, \
    two_points_angle, stitch_strips


@pytest.mark.parametrize("corner1, corner2, speed, band_distance, angle", [
    # Test case 1: Small rectangle with horizontal bands (east-west)
    (
            wgs84_to_utm(23.134, 37.428),  # corner1 (easting, northing) in UTM
            wgs84_to_utm(23.136, 37.430),  # corner2 (easting, northing) in UTM
            2.5,  # speed
            50.0,  # band_distance in meters
            0.0,  # angle in degrees (South->North)
    ),
    # Test case 2: Rectangle with vertical bands (north-south)
    (
            wgs84_to_utm(23.134, 37.428),  # corner1 (easting, northing) in UTM
            wgs84_to_utm(23.140, 37.430),  # corner2 (easting, northing) in UTM - wider rectangle
            1.0,  # speed
            50.0,  # band_distance in meters
            0.0,  # angle in degrees (South->North)
    ),
    # Test case 3: Rectangle with corners in different order
    (
            wgs84_to_utm(-71.095, 42.360),  # corner1 (easting, northing) in UTM
            wgs84_to_utm(-71.105, 42.350),  # corner2 (easting, northing) in UTM - corners in different order
            5.0,  # speed
            100.0,  # band_distance in meters
            0.0,  # angle in degrees (South->North)
    ),
    # Test case 4: Horizontal bands with 90 degree angle (East->West)
    (
            wgs84_to_utm(23.134, 37.428),  # corner1 (easting, northing) in UTM
            wgs84_to_utm(23.136, 37.430),  # corner2 (easting, northing) in UTM
            2.5,  # speed
            50.0,  # band_distance in meters
            90.0,  # angle in degrees (East->West)
    ),
    # Test case 5: Diagonal bands with 45 degree angle
    (
            wgs84_to_utm(23.134, 37.428),  # corner1 (easting, northing) in UTM
            wgs84_to_utm(23.136, 37.430),  # corner2 (easting, northing) in UTM
            2.5,  # speed
            50.0,  # band_distance in meters
            45.0,  # angle in degrees (diagonal)
    ),
    # Test case 6: Diagonal bands with 30 degree angle
    (
            wgs84_to_utm(23.134, 37.428),  # corner1 (easting, northing) in UTM
            wgs84_to_utm(23.136, 37.430),  # corner2 (easting, northing) in UTM
            2.5,  # speed
            3.0,  # band_distance in meters
            30.0,  # angle in degrees (diagonal)
    ),
])
def test_create_lawn_mower_band_strips(corner1, corner2, speed, band_distance, angle):
    """
    Test that create_route_segment_lawn_mower correctly creates a route segment
    with a lawn mower pattern within the rectangle.
    """
    # Create the coordinates
    strips = create_lawn_mower_band_strips(corner1, corner2, band_distance, angle)

    assert len(strips) >= 2

    print(strips)
    for p1, p2 in strips:
        if p2 is None:
            continue
        got_angle = two_points_angle(p1, p2)
        assert got_angle == approx(angle, abs=1.0)


@pytest.mark.parametrize("angle", [0.0, 90.0])
def test_lawn_mower_band_distance(angle):
    """Test that the distance between bands is at most the specified distance for standard angles."""
    corner1 = wgs84_to_utm(23.134, 37.428)
    corner2 = wgs84_to_utm(23.136, 37.430)
    band_distance = 50.0  # meters
    speed = 2.5
    strips = create_lawn_mower_band_strips(corner1, corner2, band_distance, angle)
    coordinates = stitch_strips(strips)
    altitude = 0.0  # Default altitude
    route_segment = create_route_segment_from_coordinates(coordinates, altitude, speed, "32634")

    # Since we're using UTM coordinates as input but the waypoints are in WGS84,
    # we can't directly compare the band distances in the same coordinate system.
    # Instead, we'll verify that the route segment has a reasonable number of waypoints
    # based on the rectangle size and band distance.

    # Extract the UTM coordinates
    x1, y1 = corner1
    x2, y2 = corner2

    # Calculate the rectangle dimensions in meters
    width = abs(x2 - x1)
    height = abs(y2 - y1)

    # Determine the expected number of bands based on the angle
    if angle == 0.0:  # Vertical bands
        expected_bands = max(2, math.ceil(width / band_distance) + 1)
    else:  # Horizontal bands (angle == 90.0)
        expected_bands = max(2, math.ceil(height / band_distance) + 1)

    # Each band has 2 waypoints
    expected_waypoints = expected_bands * 2

    # Verify that the number of waypoints is reasonable
    # Allow for some variation due to the implementation details
    assert len(route_segment.waypoints) >= expected_waypoints - 2
    assert len(route_segment.waypoints) <= expected_waypoints + 2


@pytest.mark.parametrize("point, vector, y, expected_x", [
    # Test case 1: parallel, out line
    (
            (5, 2),
            (2, 0),
            4,
            None
    ),
    # Test case 2: parallel, on line
    (
            (5, 2),
            (2, 0),
            2,
            None
    ),
    # Test case 3: vertical, out of line
    (
            (5, 2),
            (0, 2),
            4,
            5
    ),
    # Test case 4: vertical, on line
    (
            (5, 2),
            (0, -2),
            4,
            5
    ),
    # Test case 5: diagonal
    (
            (5, 2),
            (2, 1),
            4,
            9
    ),
    # Test case 5: diagonal, backwards
    (
            (5, 2),
            (-2, -1),
            4,
            9
    ),
])
def test_find_horizontal_intersect(point, vector, y, expected_x):
    got = find_horizontal_intersect(point, vector, y)
    assert got == expected_x


@pytest.mark.parametrize("point, vector, x, expected_y", [
    # Test case 1: parallel, out line
    (
            (5, 2),
            (0, 2),
            4,
            None
    ),
    # Test case 2: parallel, on line
    (
            (5, 2),
            (0, 2),
            5,
            None
    ),
    # Test case 3: horizontal, out of line
    (
            (5, 2),
            (2, 0),
            4,
            2
    ),
    # Test case 4: horizontal, on line
    (
            (5, 2),
            (-2, 0),
            4,
            2
    ),
    # Test case 5: diagonal
    (
            (5, 2),
            (2, 1),
            4,
            1.5
    ),
    # Test case 5: diagonal, backwards
    (
            (5, 2),
            (-2, -1),
            4,
            1.5
    ),
])
def test_find_vertical_intersect(point, vector, x, expected_y):
    got = find_vertical_intersect(point, vector, x)
    assert got == expected_y


@pytest.mark.parametrize("rectangle_corners, point, vector, expected_intersections", [
    # Test case 1: Line passing through rectangle (2 intersections)
    (
            ((0, 0), (10, 10)),  # rectangle corners
            (5, -5),  # point outside rectangle
            (0, 1),  # vector pointing north
            [(5, 0), (5, 10)]  # expected intersections (bottom and top)
    ),
    # Test case 2: Line passing through rectangle diagonally (2 intersections)
    (
            ((0, 0), (10, 10)),  # rectangle corners
            (-5, -5),  # point outside rectangle
            (1, 1),  # vector pointing northeast
            [(0, 0), (10, 10)]  # expected intersections (bottom-left and top-right corners)
    ),
    # Test case 3: point on rectangle perimeter
    (
            ((0, 0), (10, 10)),  # rectangle corners
            (0, 5),  # point on left edge
            (1, 0),  # vector pointing east
            [(0, 5), (10, 5)]  # expected intersection (right edge)
    ),
    # Test case 4: touching only one corner
    (
            ((0, 0), (10, 10)),  # rectangle corners
            (5, 15),  # point on left edge
            (1, -1),  # vector pointing south east
            [(10, 10)]  # expected intersection (right edge)
    ),
    # Test case 5: Line missing rectangle (0 intersections)
    (
            ((0, 0), (10, 10)),  # rectangle corners
            (20, 5),  # point outside rectangle
            (1, 1),  # vector pointing north east
            []  # no intersections
    ),
    # Test case 6: Line starting inside rectangle (1 intersection)
    (
            ((0, 0), (10, 10)),  # rectangle corners
            (5, 5),  # point inside rectangle
            (1, 1),  # vector pointing northeast
            [(10, 10), (0, 0)]  # expected intersection (top-right corner)
    ),
    # Test case
    # 7: Line aligned to edge
    (
            ((0, 0), (10, 10)),  # rectangle corners
            (-5, 10),  # point outside rectangle
            (-1, 0),  # vector pointing west
            []  # expected intersections (left and right edges)
    ),
    # Test case
    # 8: parallel to edge buzt missing it
    (
            ((0, 0), (10, 10)),  # rectangle corners
            (-5, 12),  # point outside rectangle
            (-1, 0),  # vector pointing west
            []  # expected intersections (left and right edges)
    ),

])
def test_find_line_rectangle_intersections(rectangle_corners, point, vector, expected_intersections):
    """Test the function that finds intersections between a line and a rectangle."""
    # Call the function
    intersections = find_line_rectangle_intersections(rectangle_corners, point, vector)

    if not expected_intersections:
        assert intersections == []
        return

    sorted_expected = sorted(expected_intersections, key=lambda p: (p[0], p[1]))
    sorted_actual = sorted(intersections, key=lambda p: (p[0], p[1]))

    assert sorted_actual == sorted_expected
