import math

import pytest

from bok_ucgs_fish_route.coordinates.route import RouteSegment
from bok_ucgs_fish_route.route_planner import create_route_segment_lawn_mower


@pytest.mark.parametrize("corner1, corner2, speed, band_distance, angle, expected_direction", [
    # Test case 1: Small rectangle with horizontal bands (east-west)
    (
        (37.428, 23.134),  # corner1 (lat1, lon1)
        (37.430, 23.136),  # corner2 (lat2, lon2)
        2.5,  # speed
        50.0,  # band_distance in meters
        0.0,   # angle in degrees (South->North)
        "vertical",  # expected direction of bands
    ),
    # Test case 2: Rectangle with vertical bands (north-south)
    (
        (37.428, 23.134),  # corner1 (lat1, lon1)
        (37.430, 23.140),  # corner2 (lat2, lon2) - wider rectangle
        1.0,  # speed
        50.0,  # band_distance in meters
        0.0,   # angle in degrees (South->North)
        "vertical",  # expected direction of bands
    ),
    # Test case 3: Rectangle with corners in different order
    (
        (42.360, -71.095),  # corner1 (lat1, lon1)
        (42.350, -71.105),  # corner2 (lat2, lon2) - corners in different order
        5.0,  # speed
        100.0,  # band_distance in meters
        0.0,   # angle in degrees (South->North)
        "vertical",  # expected direction of bands
    ),
    # Test case 4: Horizontal bands with 90 degree angle (East->West)
    (
        (37.428, 23.134),  # corner1 (lat1, lon1)
        (37.430, 23.136),  # corner2 (lat2, lon2)
        2.5,  # speed
        50.0,  # band_distance in meters
        90.0,  # angle in degrees (East->West)
        "horizontal",  # expected direction of bands
    ),
    # Test case 5: Diagonal bands with 45 degree angle
    (
        (37.428, 23.134),  # corner1 (lat1, lon1)
        (37.430, 23.136),  # corner2 (lat2, lon2)
        2.5,  # speed
        50.0,  # band_distance in meters
        45.0,  # angle in degrees (diagonal)
        "rotated",  # expected direction of bands
    ),
])
def test_create_route_segment_lawn_mower(corner1, corner2, speed, band_distance, angle, expected_direction):
    """
    Test that create_route_segment_lawn_mower correctly creates a route segment
    with a lawn mower pattern within the rectangle.
    """
    # Create the route segment
    route_segment = create_route_segment_lawn_mower(corner1, corner2, speed, band_distance, angle)

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

    # Verify the direction of the bands (horizontal, vertical, or rotated)
    if expected_direction == "horizontal":
        # For horizontal bands, consecutive waypoints should have the same latitude
        # but different longitudes, or different latitudes but same longitude
        for i in range(0, len(route_segment.waypoints) - 1, 2):
            if i + 1 < len(route_segment.waypoints):
                assert route_segment.waypoints[i].lat == pytest.approx(route_segment.waypoints[i+1].lat, abs=1e-10)
                assert route_segment.waypoints[i].lon != pytest.approx(route_segment.waypoints[i+1].lon, abs=1e-10)
    elif expected_direction == "vertical":
        # For vertical bands, consecutive waypoints should have the same longitude
        # but different latitudes, or different longitudes but same latitude
        for i in range(0, len(route_segment.waypoints) - 1, 2):
            if i + 1 < len(route_segment.waypoints):
                assert route_segment.waypoints[i].lon == pytest.approx(route_segment.waypoints[i+1].lon, abs=1e-10)
                assert route_segment.waypoints[i].lat != pytest.approx(route_segment.waypoints[i+1].lat, abs=1e-10)
    else:  # rotated
        # For rotated bands, we can't easily check the exact pattern
        # but we can verify that the waypoints form a zigzag pattern
        # by checking that consecutive pairs of waypoints have different coordinates
        for i in range(0, len(route_segment.waypoints) - 1, 2):
            if i + 1 < len(route_segment.waypoints):
                # Each pair of waypoints should be different
                assert (route_segment.waypoints[i].lat != pytest.approx(route_segment.waypoints[i+1].lat, abs=1e-10) or 
                        route_segment.waypoints[i].lon != pytest.approx(route_segment.waypoints[i+1].lon, abs=1e-10))


@pytest.mark.parametrize("angle", [0.0, 90.0])
def test_lawn_mower_band_distance(angle):
    """Test that the distance between bands is at most the specified distance for standard angles."""
    corner1 = (37.428, 23.134)
    corner2 = (37.430, 23.136)
    band_distance = 50.0  # meters
    route_segment = create_route_segment_lawn_mower(corner1, corner2, 2.5, band_distance, angle)

    # Extract waypoints
    waypoints = route_segment.waypoints

    # Determine if the bands are horizontal or vertical
    # If the first two waypoints have the same latitude, the bands are horizontal
    horizontal_bands = abs(waypoints[0].lat - waypoints[1].lat) < 1e-10

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


def test_lawn_mower_rotated_bands():
    """Test that rotated bands (45 degrees) create a valid pattern."""
    corner1 = (37.428, 23.134)
    corner2 = (37.430, 23.136)
    band_distance = 50.0  # meters
    angle = 45.0  # degrees
    
    route_segment = create_route_segment_lawn_mower(corner1, corner2, 2.5, band_distance, angle)
    
    # Extract waypoints
    waypoints = route_segment.waypoints
    
    # Verify it's a RouteSegment instance
    assert isinstance(route_segment, RouteSegment)
    
    # Verify there are at least 4 waypoints (minimum 2 bands * 2 points per band)
    assert len(waypoints) >= 4
    
    # Verify the number of waypoints is even (each band has 2 points)
    assert len(waypoints) % 2 == 0
    
    # Extract coordinates for verification
    lat1, lon1 = corner1
    lat2, lon2 = corner2
    lat_min, lat_max = min(lat1, lat2), max(lat1, lat2)
    lon_min, lon_max = min(lon1, lon2), max(lon1, lon2)
    
    # Verify the waypoints are within the rectangle bounds
    for waypoint in waypoints:
        assert lat_min <= waypoint.lat <= lat_max
        assert lon_min <= waypoint.lon <= lon_max
    
    # For rotated bands, we can't easily check the exact pattern
    # but we can verify that the waypoints form a zigzag pattern
    # by checking that consecutive pairs of waypoints have different coordinates
    for i in range(0, len(waypoints) - 1, 2):
        if i + 1 < len(waypoints):
            # Each pair of waypoints should be different
            assert (waypoints[i].lat != pytest.approx(waypoints[i+1].lat, abs=1e-10) or 
                    waypoints[i].lon != pytest.approx(waypoints[i+1].lon, abs=1e-10))


def test_angled_lawn_mower_waypoints_on_perimeter():
    """Test that waypoints for angled lawn mowing are on the rectangle perimeter."""
    corner1 = (37.428, 23.134)
    corner2 = (37.430, 23.136)
    band_distance = 50.0  # meters
    angle = 45.0  # degrees
    
    route_segment = create_route_segment_lawn_mower(corner1, corner2, 2.5, band_distance, angle)
    
    # Extract waypoints and rectangle bounds
    waypoints = route_segment.waypoints
    lat1, lon1 = corner1
    lat2, lon2 = corner2
    lat_min, lat_max = min(lat1, lat2), max(lat1, lat2)
    lon_min, lon_max = min(lon1, lon2), max(lon1, lon2)
    
    # Define a small epsilon for floating-point comparisons
    epsilon = 1e-10
    
    # Verify that each waypoint is on the perimeter of the rectangle
    for waypoint in waypoints:
        # A point is on the perimeter if at least one of its coordinates is at the boundary
        on_perimeter = (
            abs(waypoint.lat - lat_min) < epsilon or
            abs(waypoint.lat - lat_max) < epsilon or
            abs(waypoint.lon - lon_min) < epsilon or
            abs(waypoint.lon - lon_max) < epsilon
        )
        assert on_perimeter, f"Waypoint {waypoint} is not on the perimeter"
        
    # Verify that the lines between consecutive waypoint pairs are parallel to the angle
    for i in range(0, len(waypoints) - 1, 2):
        if i + 1 < len(waypoints):
            wp1 = waypoints[i]
            wp2 = waypoints[i+1]
            
            # Calculate the angle of the line between the two waypoints
            # Convert to a local coordinate system (meters)
            avg_lat = (lat_min + lat_max) / 2
            lat_meters_per_degree = 111000  # approximate
            lon_meters_per_degree = 111000 * math.cos(math.radians(avg_lat))
            
            dx = (wp2.lon - wp1.lon) * lon_meters_per_degree
            dy = (wp2.lat - wp1.lat) * lat_meters_per_degree
            
            # Calculate the angle in degrees (0 is North, 90 is East)
            if abs(dx) < epsilon and abs(dy) < epsilon:
                continue  # Skip if points are too close
                
            line_angle = math.degrees(math.atan2(dx, dy)) % 180
            
            # The line angle should be approximately equal to the input angle
            # Allow for some numerical error
            angle_diff = min(abs(line_angle - angle), abs(line_angle - (angle + 180) % 180))
            assert angle_diff < 1.0, f"Line angle {line_angle} differs from expected angle {angle}"
