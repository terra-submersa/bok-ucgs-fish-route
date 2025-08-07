import math

import pytest

from bok_ucgs_fish_route.coordinates.route import RouteSegment
from bok_ucgs_fish_route.route_planner import create_route_segment_lawn_mower


@pytest.mark.parametrize("corner1, corner2, speed, band_distance, expected_direction", [
    # Test case 1: Small rectangle with horizontal bands (east-west)
    (
        (37.428, 23.134),  # corner1 (lat1, lon1)
        (37.430, 23.136),  # corner2 (lat2, lon2)
        2.5,  # speed
        50.0,  # band_distance in meters
        "horizontal",  # expected direction of bands
    ),
    # Test case 2: Rectangle with vertical bands (north-south)
    (
        (37.428, 23.134),  # corner1 (lat1, lon1)
        (37.430, 23.140),  # corner2 (lat2, lon2) - wider rectangle
        1.0,  # speed
        50.0,  # band_distance in meters
        "vertical",  # expected direction of bands
    ),
    # Test case 3: Rectangle with corners in different order
    (
        (42.360, -71.095),  # corner1 (lat1, lon1)
        (42.350, -71.105),  # corner2 (lat2, lon2) - corners in different order
        5.0,  # speed
        100.0,  # band_distance in meters
        "horizontal",  # expected direction of bands
    ),
])
def test_create_route_segment_lawn_mower(corner1, corner2, speed, band_distance, expected_direction):
    """
    Test that create_route_segment_lawn_mower correctly creates a route segment
    with a lawn mower pattern within the rectangle.
    """
    # Create the route segment
    route_segment = create_route_segment_lawn_mower(corner1, corner2, speed, band_distance)

    # Verify it's a RouteSegment instance
    assert isinstance(route_segment, RouteSegment)

    # Verify the speed is set correctly
    assert route_segment.speed == speed

    # Verify there are at least 4 waypoints (minimum 2 bands * 2 points per band)
    assert len(route_segment.waypoints) >= 4

    # Verify the number of waypoints is even (each band has 2 points)
    assert len(route_segment.waypoints) % 2 == 0

    # Extract coordinates for verification
    lat1, lon1 = corner1
    lat2, lon2 = corner2
    lat_min, lat_max = min(lat1, lat2), max(lat1, lat2)
    lon_min, lon_max = min(lon1, lon2), max(lon1, lon2)

    # Verify the waypoints are within the rectangle bounds
    for waypoint in route_segment.waypoints:
        assert lat_min <= waypoint.lat <= lat_max
        assert lon_min <= waypoint.lon <= lon_max

    # Verify the direction of the bands (horizontal or vertical)
    if expected_direction == "horizontal":
        # For horizontal bands, consecutive waypoints should have the same latitude
        # but different longitudes, or different latitudes but same longitude
        for i in range(0, len(route_segment.waypoints) - 1, 2):
            if i + 1 < len(route_segment.waypoints):
                assert route_segment.waypoints[i].lat == route_segment.waypoints[i+1].lat
                assert route_segment.waypoints[i].lon != route_segment.waypoints[i+1].lon
    else:  # vertical
        # For vertical bands, consecutive waypoints should have the same longitude
        # but different latitudes, or different longitudes but same latitude
        for i in range(0, len(route_segment.waypoints) - 1, 2):
            if i + 1 < len(route_segment.waypoints):
                assert route_segment.waypoints[i].lon == route_segment.waypoints[i+1].lon
                assert route_segment.waypoints[i].lat != route_segment.waypoints[i+1].lat


def test_lawn_mower_band_distance():
    """Test that the distance between bands is at most the specified distance."""
    corner1 = (37.428, 23.134)
    corner2 = (37.430, 23.136)
    band_distance = 50.0  # meters
    route_segment = create_route_segment_lawn_mower(corner1, corner2, 2.5, band_distance)

    # Extract waypoints
    waypoints = route_segment.waypoints

    # Determine if the bands are horizontal or vertical
    # If the first two waypoints have the same latitude, the bands are horizontal
    horizontal_bands = waypoints[0].lat == waypoints[1].lat

    if horizontal_bands:
        # For horizontal bands, find consecutive waypoints with different latitudes
        for i in range(0, len(waypoints) - 2, 2):
            if i + 2 < len(waypoints):
                lat_diff = abs(waypoints[i].lat - waypoints[i+2].lat)

                # Convert to meters (approximate)
                lat_meters_per_degree = 111000  # approximate
                band_distance_meters = lat_diff * lat_meters_per_degree

                # The actual band distance should be at most the specified distance
                assert band_distance_meters <= band_distance
    else:
        # For vertical bands, find consecutive waypoints with different longitudes
        for i in range(0, len(waypoints) - 2, 2):
            if i + 2 < len(waypoints):
                lon_diff = abs(waypoints[i].lon - waypoints[i+2].lon)

                # Convert to meters (approximate)
                avg_lat = (waypoints[i].lat + waypoints[i+2].lat) / 2
                lon_meters_per_degree = 111000 * math.cos(math.radians(avg_lat))  # approximate
                band_distance_meters = lon_diff * lon_meters_per_degree

                # The actual band distance should be at most the specified distance
                assert band_distance_meters <= band_distance
