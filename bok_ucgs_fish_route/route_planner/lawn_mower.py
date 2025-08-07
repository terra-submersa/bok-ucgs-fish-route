import math
from typing import Tuple, List

from bok_ucgs_fish_route.coordinates.route import RouteSegment
from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate


def create_route_segment_lawn_mower(
    corner1: Tuple[float, float],
    corner2: Tuple[float, float],
    speed: float,
    band_distance: float,
    angle: float = 0.0,
    epsg_code: str = "EPSG:4326"  # Default to WGS84
) -> RouteSegment:
    """
    Create a RouteSegment with a lawn mower pattern within a rectangle.

    The function takes two corners of a rectangle and creates a route segment
    that traverses the rectangle in parallel bands (lawn mower pattern).

    Args:
        corner1 (Tuple[float, float]): First corner coordinates as (latitude, longitude)
        corner2 (Tuple[float, float]): Second corner coordinates as (latitude, longitude)
        speed (float): Speed in meters per second
        band_distance (float): Maximum distance between parallel bands in meters
        angle (float, optional): Angle in degrees for lawn mowing direction. 0 is South->North, 90 is East->West. Defaults to 0.0.
        epsg_code (str, optional): EPSG code for the coordinate reference system. Defaults to "EPSG:4326" (WGS84).

    Returns:
        RouteSegment: A route segment with a lawn mower pattern within the rectangle

    Example:
        >>> corner1 = (37.428, 23.134)  # (lat, lon)
        >>> corner2 = (37.430, 23.136)  # (lat, lon)
        >>> segment = create_route_segment_lawn_mower(corner1, corner2, 2.5, 10.0)
        >>> segment_angled = create_route_segment_lawn_mower(corner1, corner2, 2.5, 10.0, 45.0)
    """
    # Extract coordinates
    lat1, lon1 = corner1
    lat2, lon2 = corner2

    # Ensure lat1 <= lat2 and lon1 <= lon2
    lat_min, lat_max = min(lat1, lat2), max(lat1, lat2)
    lon_min, lon_max = min(lon1, lon2), max(lon1, lon2)

    # Calculate the width and height of the rectangle in degrees
    width_deg = lon_max - lon_min
    height_deg = lat_max - lat_min

    # Convert band_distance from meters to degrees (approximate conversion)
    # 1 degree of latitude is approximately 111,000 meters
    # 1 degree of longitude varies with latitude, approximately 111,000 * cos(latitude) meters
    avg_lat = (lat_min + lat_max) / 2
    lat_meters_per_degree = 111000  # approximate
    lon_meters_per_degree = 111000 * math.cos(math.radians(avg_lat))

    # Normalize angle to 0-180 range (since 180-360 would be the same pattern in reverse)
    normalized_angle = angle % 180

    # For standard angles (0, 90, 180), use the optimized approach
    if normalized_angle == 0 or normalized_angle == 180:
        return _create_vertical_lawn_mower(lat_min, lat_max, lon_min, lon_max, 
                                          band_distance, lon_meters_per_degree, speed)
    elif normalized_angle == 90:
        return _create_horizontal_lawn_mower(lat_min, lat_max, lon_min, lon_max, 
                                            band_distance, lat_meters_per_degree, speed)
    else:
        # For angled lawn mowing, use the new approach
        return _create_angled_lawn_mower(lat_min, lat_max, lon_min, lon_max, 
                                        band_distance, normalized_angle, 
                                        lat_meters_per_degree, lon_meters_per_degree, speed)


def _create_vertical_lawn_mower(lat_min: float, lat_max: float, lon_min: float, lon_max: float, 
                               band_distance: float, lon_meters_per_degree: float, speed: float) -> RouteSegment:
    """
    Create a lawn mower pattern with vertical bands (north-south).
    
    Args:
        lat_min: Minimum latitude of the rectangle
        lat_max: Maximum latitude of the rectangle
        lon_min: Minimum longitude of the rectangle
        lon_max: Maximum longitude of the rectangle
        band_distance: Maximum distance between bands in meters
        lon_meters_per_degree: Conversion factor from degrees to meters for longitude
        speed: Speed in meters per second
        
    Returns:
        RouteSegment with vertical lawn mower pattern
    """
    # Calculate the width in meters
    width_deg = lon_max - lon_min
    width_meters = width_deg * lon_meters_per_degree

    # Calculate the number of bands needed
    num_bands = max(2, math.ceil(width_meters / band_distance) + 1)

    # Calculate the actual band distance in degrees
    actual_band_distance_deg = width_deg / (num_bands - 1) if num_bands > 1 else width_deg

    # Verify the actual band distance is at most the specified distance
    actual_band_distance_meters = actual_band_distance_deg * lon_meters_per_degree
    if actual_band_distance_meters > band_distance:
        # If it's still too large, increase the number of bands
        num_bands += 1
        actual_band_distance_deg = width_deg / (num_bands - 1)

    # Create waypoints for vertical bands
    waypoints = []
    for i in range(num_bands):
        lon = lon_min + i * actual_band_distance_deg

        # For even-indexed bands, go from south to north
        if i % 2 == 0:
            waypoints.append(WaypointCoordinate(lat_min, lon))
            waypoints.append(WaypointCoordinate(lat_max, lon))
        # For odd-indexed bands, go from north to south
        else:
            waypoints.append(WaypointCoordinate(lat_max, lon))
            waypoints.append(WaypointCoordinate(lat_min, lon))
            
    return RouteSegment(waypoints, speed)


def _create_horizontal_lawn_mower(lat_min: float, lat_max: float, lon_min: float, lon_max: float, 
                                 band_distance: float, lat_meters_per_degree: float, speed: float) -> RouteSegment:
    """
    Create a lawn mower pattern with horizontal bands (east-west).
    
    Args:
        lat_min: Minimum latitude of the rectangle
        lat_max: Maximum latitude of the rectangle
        lon_min: Minimum longitude of the rectangle
        lon_max: Maximum longitude of the rectangle
        band_distance: Maximum distance between bands in meters
        lat_meters_per_degree: Conversion factor from degrees to meters for latitude
        speed: Speed in meters per second
        
    Returns:
        RouteSegment with horizontal lawn mower pattern
    """
    # Calculate the height in meters
    height_deg = lat_max - lat_min
    height_meters = height_deg * lat_meters_per_degree

    # Calculate the number of bands needed
    num_bands = max(2, math.ceil(height_meters / band_distance) + 1)

    # Calculate the actual band distance in degrees
    actual_band_distance_deg = height_deg / (num_bands - 1) if num_bands > 1 else height_deg

    # Verify the actual band distance is at most the specified distance
    actual_band_distance_meters = actual_band_distance_deg * lat_meters_per_degree
    if actual_band_distance_meters > band_distance:
        # If it's still too large, increase the number of bands
        num_bands += 1
        actual_band_distance_deg = height_deg / (num_bands - 1)

    # Create waypoints for horizontal bands
    waypoints = []
    for i in range(num_bands):
        lat = lat_min + i * actual_band_distance_deg

        # For even-indexed bands, go from west to east
        if i % 2 == 0:
            waypoints.append(WaypointCoordinate(lat, lon_min))
            waypoints.append(WaypointCoordinate(lat, lon_max))
        # For odd-indexed bands, go from east to west
        else:
            waypoints.append(WaypointCoordinate(lat, lon_max))
            waypoints.append(WaypointCoordinate(lat, lon_min))
            
    return RouteSegment(waypoints, speed)


def _create_angled_lawn_mower(lat_min: float, lat_max: float, lon_min: float, lon_max: float, 
                             band_distance: float, angle: float, 
                             lat_meters_per_degree: float, lon_meters_per_degree: float, 
                             speed: float) -> RouteSegment:
    """
    Create a lawn mower pattern with bands at the specified angle.
    
    Args:
        lat_min: Minimum latitude of the rectangle
        lat_max: Maximum latitude of the rectangle
        lon_min: Minimum longitude of the rectangle
        lon_max: Maximum longitude of the rectangle
        band_distance: Maximum distance between bands in meters
        angle: Angle in degrees (0-180)
        lat_meters_per_degree: Conversion factor from degrees to meters for latitude
        lon_meters_per_degree: Conversion factor from degrees to meters for longitude
        speed: Speed in meters per second
        
    Returns:
        RouteSegment with angled lawn mower pattern
    """
    # Define the rectangle corners in clockwise order
    corners = [
        (lat_min, lon_min),  # Bottom-left
        (lat_min, lon_max),  # Bottom-right
        (lat_max, lon_max),  # Top-right
        (lat_max, lon_min),  # Top-left
    ]
    
    # Calculate the center of the rectangle
    center_lat = (lat_min + lat_max) / 2
    center_lon = (lon_min + lon_max) / 2
    
    # Convert angle to radians
    # Adjust the angle to match the expected convention:
    # 0 degrees is South->North, 90 degrees is East->West
    # For the line direction vector, we need the perpendicular to the band direction
    # So we add 90 degrees to the angle
    line_angle_rad = math.radians((angle + 90) % 180)
    
    # Calculate the direction vector for the lines
    # This vector is perpendicular to the band direction
    dx = math.sin(line_angle_rad)
    dy = math.cos(line_angle_rad)
    
    # Calculate the rectangle's dimensions in meters
    width_meters = (lon_max - lon_min) * lon_meters_per_degree
    height_meters = (lat_max - lat_min) * lat_meters_per_degree
    
    # Calculate the projection of the rectangle onto the direction perpendicular to the bands
    # This gives us the maximum distance we need to cover with bands
    projection_length = abs(width_meters * dx) + abs(height_meters * dy)
    
    # Calculate the number of bands needed
    num_bands = max(2, math.ceil(projection_length / band_distance) + 1)
    
    # Calculate the actual band distance in meters
    actual_band_distance = projection_length / (num_bands - 1) if num_bands > 1 else projection_length
    
    # Calculate the start and end points for each band
    waypoints = []
    
    # Calculate the starting position for the first band
    # We start from the furthest point in the negative direction perpendicular to the bands
    start_offset = -projection_length / 2
    
    # Calculate the band direction vector (perpendicular to the line direction)
    band_dx = -dy  # Perpendicular to line direction
    band_dy = dx   # Perpendicular to line direction
    
    # Store all intersections to ensure we don't have duplicate waypoints
    all_intersections = []
    
    for i in range(num_bands):
        # Calculate the offset for this band
        offset = start_offset + i * actual_band_distance
        
        # Find the intersections of this band with the rectangle edges
        band_intersections = []
        
        # Check each edge of the rectangle
        for j in range(4):
            # Get the current edge
            start_corner = corners[j]
            end_corner = corners[(j + 1) % 4]
            
            # Convert to local coordinates (in meters)
            start_x = (start_corner[1] - center_lon) * lon_meters_per_degree
            start_y = (start_corner[0] - center_lat) * lat_meters_per_degree
            end_x = (end_corner[1] - center_lon) * lon_meters_per_degree
            end_y = (end_corner[0] - center_lat) * lat_meters_per_degree
            
            # Check if the line intersects with this edge
            # Line equation: dx * (x - offset * band_dx) + dy * (y - offset * band_dy) = 0
            # Edge equation: y = start_y + (end_y - start_y) * t, x = start_x + (end_x - start_x) * t, 0 <= t <= 1
            
            # Calculate the denominator
            denominator = dx * (end_x - start_x) + dy * (end_y - start_y)
            
            # If the denominator is close to zero, the line is parallel to the edge
            if abs(denominator) < 1e-10:
                continue
                
            # Calculate t
            t = (dx * (offset * band_dx - start_x) + dy * (offset * band_dy - start_y)) / denominator
            
            # Check if the intersection is on the edge
            if 0 <= t <= 1:
                # Calculate the intersection point
                intersection_x = start_x + (end_x - start_x) * t
                intersection_y = start_y + (end_y - start_y) * t
                
                # Convert back to lat/lon
                intersection_lon = center_lon + (intersection_x / lon_meters_per_degree)
                intersection_lat = center_lat + (intersection_y / lat_meters_per_degree)
                
                # Add to the list of intersections
                band_intersections.append((intersection_lat, intersection_lon))
        
        # If we found exactly 2 intersections, add them as waypoints
        if len(band_intersections) == 2:
            # Sort the intersections to ensure consistent direction along the angle
            # We want to sort them in the direction of the angle
            # Calculate the dot product of the vector from point1 to point2 with the band direction
            p1_lat, p1_lon = band_intersections[0]
            p2_lat, p2_lon = band_intersections[1]
            
            # Convert to local coordinates (in meters)
            p1_x = (p1_lon - center_lon) * lon_meters_per_degree
            p1_y = (p1_lat - center_lat) * lat_meters_per_degree
            p2_x = (p2_lon - center_lon) * lon_meters_per_degree
            p2_y = (p2_lat - center_lat) * lat_meters_per_degree
            
            # Calculate the vector from p1 to p2
            vec_x = p2_x - p1_x
            vec_y = p2_y - p1_y
            
            # Calculate the dot product with the band direction
            dot_product = vec_x * band_dx + vec_y * band_dy
            
            # For even-indexed bands, go in the direction of the angle
            # For odd-indexed bands, go in the opposite direction
            if (i % 2 == 0 and dot_product < 0) or (i % 2 == 1 and dot_product > 0):
                # Swap the points to get the correct direction
                band_intersections[0], band_intersections[1] = band_intersections[1], band_intersections[0]
            
            # Check if these intersections are too close to any existing waypoints
            # This prevents having consecutive bands with the same waypoints
            epsilon = 1e-10
            
            # Create a copy of band_intersections that we can modify
            adjusted_intersections = []
            
            for idx, (new_lat, new_lon) in enumerate(band_intersections):
                # Check if this point is a duplicate of any existing point
                is_duplicate = False
                for ex_lat, ex_lon in all_intersections:
                    if (abs(ex_lat - new_lat) < epsilon and abs(ex_lon - new_lon) < epsilon):
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    # Adjust the point based on which edge it's on
                    adjusted_lat, adjusted_lon = new_lat, new_lon
                    
                    # Determine which edge the point is on and adjust accordingly
                    if abs(new_lat - lat_min) < epsilon:  # Bottom edge
                        adjusted_lon = new_lon + 1e-8
                    elif abs(new_lat - lat_max) < epsilon:  # Top edge
                        adjusted_lon = new_lon - 1e-8
                    elif abs(new_lon - lon_min) < epsilon:  # Left edge
                        adjusted_lat = new_lat + 1e-8
                    elif abs(new_lon - lon_max) < epsilon:  # Right edge
                        adjusted_lat = new_lat - 1e-8
                    
                    # Add the adjusted point
                    adjusted_intersections.append((adjusted_lat, adjusted_lon))
                else:
                    # Add the original point
                    adjusted_intersections.append((new_lat, new_lon))
            
            # Replace band_intersections with the adjusted points
            band_intersections = adjusted_intersections
            
            # Add the intersections to the list of all intersections
            all_intersections.extend(band_intersections)
            
            # Add the waypoints
            waypoints.append(WaypointCoordinate(band_intersections[0][0], band_intersections[0][1]))
            waypoints.append(WaypointCoordinate(band_intersections[1][0], band_intersections[1][1]))
    
    return RouteSegment(waypoints, speed)
