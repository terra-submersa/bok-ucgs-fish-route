import math
import logging
from typing import Tuple, List
from bok_ucgs_fish_route.coordinates.conversion import convert_corners_if_wgs84

# Configure logging
logger = logging.getLogger(__name__)

def create_route_segment_lawn_mower(
    corner1: Tuple[float, float],
    corner2: Tuple[float, float],
    band_distance: float,
    angle: float = 0.0
) -> List[Tuple[float, float]]:
    """
    Create a list of coordinates with a lawn mower pattern within a rectangle.

    The function takes two corners of a rectangle and creates a list of coordinates
    that traverses the rectangle in parallel bands (lawn mower pattern).
    
    If the input coordinates are in WGS84 (longitude, latitude), they will be automatically
    converted to UTM coordinates for processing, and the result will be converted back to WGS84.

    Args:
        corner1 (Tuple[float, float]): First corner coordinates as (x, y) in UTM or (longitude, latitude) in WGS84
        corner2 (Tuple[float, float]): Second corner coordinates as (x, y) in UTM or (longitude, latitude) in WGS84
        band_distance (float): Maximum distance between parallel bands in meters
        angle (float, optional): Angle in degrees for lawn mowing direction. 0 is South->North, 90 is East->West. Defaults to 0.0.

    Returns:
        List[Tuple[float, float]]: A list of coordinate tuples in the same format as the input (UTM or WGS84)

    Example:
        >>> corner1 = (23.134, 37.428)  # (lon, lat) in WGS84
        >>> corner2 = (23.136, 37.430)  # (lon, lat) in WGS84
        >>> coordinates = create_route_segment_lawn_mower(corner1, corner2, 10.0)
        >>> coordinates_angled = create_route_segment_lawn_mower(corner1, corner2, 10.0, 45.0)
        
        >>> utm_corner1 = (500000, 4000000)  # (easting, northing) in UTM
        >>> utm_corner2 = (500100, 4000100)  # (easting, northing) in UTM
        >>> utm_coordinates = create_route_segment_lawn_mower(utm_corner1, utm_corner2, 10.0)
    """
    # Check if the coordinates are in WGS84 and convert to UTM if needed
    utm_corner1, utm_corner2, was_converted = convert_corners_if_wgs84(corner1, corner2)
    
    # Extract coordinates (now in UTM)
    x1, y1 = utm_corner1
    x2, y2 = utm_corner2

    # Ensure x1 <= x2 and y1 <= y2
    x_min, x_max = min(x1, x2), max(x1, x2)
    y_min, y_max = min(y1, y2), max(y1, y2)

    # Normalize angle to 0-180 range (since 180-360 would be the same pattern in reverse)
    normalized_angle = angle % 180

    # For standard angles (0, 90, 180), use the optimized approach
    if normalized_angle == 0 or normalized_angle == 180:
        return _create_vertical_lawn_mower_utm(x_min, x_max, y_min, y_max, band_distance, was_converted, corner1, corner2)
    elif normalized_angle == 90:
        return _create_horizontal_lawn_mower_utm(x_min, x_max, y_min, y_max, band_distance, was_converted, corner1, corner2)
    else:
        # For angled lawn mowing, use the new approach
        return _create_angled_lawn_mower_utm(x_min, x_max, y_min, y_max, band_distance, normalized_angle, was_converted, corner1, corner2)


def _create_vertical_lawn_mower_utm(x_min: float, x_max: float, y_min: float, y_max: float, 
                               band_distance: float, was_converted: bool, 
                               original_corner1: Tuple[float, float], original_corner2: Tuple[float, float]) -> List[Tuple[float, float]]:
    """
    Create a lawn mower pattern with vertical bands (south-north) using UTM coordinates.
    
    Args:
        x_min: Minimum x (easting) of the rectangle in UTM
        x_max: Maximum x (easting) of the rectangle in UTM
        y_min: Minimum y (northing) of the rectangle in UTM
        y_max: Maximum y (northing) of the rectangle in UTM
        band_distance: Maximum distance between bands in meters
        was_converted: Whether the original coordinates were converted from WGS84
        original_corner1: Original first corner coordinates
        original_corner2: Original second corner coordinates
        
    Returns:
        List[Tuple[float, float]]: List of coordinate tuples in the same format as the input
    """
    from bok_ucgs_fish_route.coordinates.conversion import wgs84_to_utm
    import pyproj
    
    # Calculate the width in meters (already in meters since using UTM)
    width_meters = x_max - x_min

    # Calculate the number of bands needed
    num_bands = max(2, math.ceil(width_meters / band_distance) + 1)

    # Calculate the actual band distance in meters
    actual_band_distance = width_meters / (num_bands - 1) if num_bands > 1 else width_meters

    # Verify the actual band distance is at most the specified distance
    if actual_band_distance > band_distance:
        # If it's still too large, increase the number of bands
        num_bands += 1
        actual_band_distance = width_meters / (num_bands - 1)

    # Create coordinates for vertical bands in UTM
    utm_coordinates = []
    for i in range(num_bands):
        x = x_min + i * actual_band_distance

        # For even-indexed bands, go from south to north
        if i % 2 == 0:
            utm_coordinates.append((x, y_min))
            utm_coordinates.append((x, y_max))
        # For odd-indexed bands, go from north to south
        else:
            utm_coordinates.append((x, y_max))
            utm_coordinates.append((x, y_min))
    
    # If the original coordinates were in WGS84, convert the result back to WGS84
    if was_converted:
        # Determine the UTM zone from the original coordinates
        lon1, lat1 = original_corner1
        
        # Create the transformer for the reverse conversion (UTM to WGS84)
        zone = int((lon1 + 180) / 6) + 1
        north = lat1 >= 0
        utm_proj_str = f"+proj=utm +zone={zone} {'+north' if north else '+south'} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
        transformer = pyproj.Transformer.from_crs(utm_proj_str, "EPSG:4326", always_xy=True)
        
        # Convert the coordinates back to WGS84
        wgs84_coordinates = []
        for x, y in utm_coordinates:
            lon, lat = transformer.transform(x, y)
            wgs84_coordinates.append((lon, lat))
        
        return wgs84_coordinates
    
    # If the original coordinates were already in UTM, return the UTM coordinates
    return utm_coordinates

def _create_vertical_lawn_mower(lat_min: float, lat_max: float, lon_min: float, lon_max: float, 
                               band_distance: float, lon_meters_per_degree: float) -> List[Tuple[float, float]]:
    """
    Create a lawn mower pattern with vertical bands (north-south).
    
    Args:
        lat_min: Minimum latitude of the rectangle
        lat_max: Maximum latitude of the rectangle
        lon_min: Minimum longitude of the rectangle
        lon_max: Maximum longitude of the rectangle
        band_distance: Maximum distance between bands in meters
        lon_meters_per_degree: Conversion factor from degrees to meters for longitude
        
    Returns:
        List[Tuple[float, float]]: List of coordinate tuples (longitude, latitude) with vertical lawn mower pattern
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

    # Create coordinates for vertical bands
    coordinates = []
    for i in range(num_bands):
        lon = lon_min + i * actual_band_distance_deg

        # For even-indexed bands, go from south to north
        if i % 2 == 0:
            coordinates.append((lon, lat_min))
            coordinates.append((lon, lat_max))
        # For odd-indexed bands, go from north to south
        else:
            coordinates.append((lon, lat_max))
            coordinates.append((lon, lat_min))
            
    return coordinates


def _create_horizontal_lawn_mower_utm(x_min: float, x_max: float, y_min: float, y_max: float, 
                                 band_distance: float, was_converted: bool, 
                                 original_corner1: Tuple[float, float], original_corner2: Tuple[float, float]) -> List[Tuple[float, float]]:
    """
    Create a lawn mower pattern with horizontal bands (west-east) using UTM coordinates.
    
    Args:
        x_min: Minimum x (easting) of the rectangle in UTM
        x_max: Maximum x (easting) of the rectangle in UTM
        y_min: Minimum y (northing) of the rectangle in UTM
        y_max: Maximum y (northing) of the rectangle in UTM
        band_distance: Maximum distance between bands in meters
        was_converted: Whether the original coordinates were converted from WGS84
        original_corner1: Original first corner coordinates
        original_corner2: Original second corner coordinates
        
    Returns:
        List[Tuple[float, float]]: List of coordinate tuples in the same format as the input
    """
    from bok_ucgs_fish_route.coordinates.conversion import wgs84_to_utm
    import pyproj
    
    # Calculate the height in meters (already in meters since using UTM)
    height_meters = y_max - y_min

    # Calculate the number of bands needed
    num_bands = max(2, math.ceil(height_meters / band_distance) + 1)

    # Calculate the actual band distance in meters
    actual_band_distance = height_meters / (num_bands - 1) if num_bands > 1 else height_meters

    # Verify the actual band distance is at most the specified distance
    if actual_band_distance > band_distance:
        # If it's still too large, increase the number of bands
        num_bands += 1
        actual_band_distance = height_meters / (num_bands - 1)

    # Create coordinates for horizontal bands in UTM
    utm_coordinates = []
    for i in range(num_bands):
        y = y_min + i * actual_band_distance

        # For even-indexed bands, go from west to east
        if i % 2 == 0:
            utm_coordinates.append((x_min, y))
            utm_coordinates.append((x_max, y))
        # For odd-indexed bands, go from east to west
        else:
            utm_coordinates.append((x_max, y))
            utm_coordinates.append((x_min, y))
    
    # If the original coordinates were in WGS84, convert the result back to WGS84
    if was_converted:
        # Determine the UTM zone from the original coordinates
        lon1, lat1 = original_corner1
        
        # Create the transformer for the reverse conversion (UTM to WGS84)
        zone = int((lon1 + 180) / 6) + 1
        north = lat1 >= 0
        utm_proj_str = f"+proj=utm +zone={zone} {'+north' if north else '+south'} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
        transformer = pyproj.Transformer.from_crs(utm_proj_str, "EPSG:4326", always_xy=True)
        
        # Convert the coordinates back to WGS84
        wgs84_coordinates = []
        for x, y in utm_coordinates:
            lon, lat = transformer.transform(x, y)
            wgs84_coordinates.append((lon, lat))
        
        return wgs84_coordinates
    
    # If the original coordinates were already in UTM, return the UTM coordinates
    return utm_coordinates

def _create_horizontal_lawn_mower(lat_min: float, lat_max: float, lon_min: float, lon_max: float, 
                                 band_distance: float, lat_meters_per_degree: float) -> List[Tuple[float, float]]:
    """
    Create a lawn mower pattern with horizontal bands (east-west).
    
    Args:
        lat_min: Minimum latitude of the rectangle
        lat_max: Maximum latitude of the rectangle
        lon_min: Minimum longitude of the rectangle
        lon_max: Maximum longitude of the rectangle
        band_distance: Maximum distance between bands in meters
        lat_meters_per_degree: Conversion factor from degrees to meters for latitude
        
    Returns:
        List[Tuple[float, float]]: List of coordinate tuples (longitude, latitude) with horizontal lawn mower pattern
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

    # Create coordinates for horizontal bands
    coordinates = []
    for i in range(num_bands):
        lat = lat_min + i * actual_band_distance_deg

        # For even-indexed bands, go from west to east
        if i % 2 == 0:
            coordinates.append((lon_min, lat))
            coordinates.append((lon_max, lat))
        # For odd-indexed bands, go from east to west
        else:
            coordinates.append((lon_max, lat))
            coordinates.append((lon_min, lat))
            
    return coordinates


def _create_angled_lawn_mower_utm(x_min: float, x_max: float, y_min: float, y_max: float, 
                             band_distance: float, angle: float, was_converted: bool, 
                             original_corner1: Tuple[float, float], original_corner2: Tuple[float, float]) -> List[Tuple[float, float]]:
    """
    Create a lawn mower pattern with bands at the specified angle using UTM coordinates.
    
    Args:
        x_min: Minimum x (easting) of the rectangle in UTM
        x_max: Maximum x (easting) of the rectangle in UTM
        y_min: Minimum y (northing) of the rectangle in UTM
        y_max: Maximum y (northing) of the rectangle in UTM
        band_distance: Maximum distance between bands in meters
        angle: Angle in degrees (0-180)
        was_converted: Whether the original coordinates were converted from WGS84
        original_corner1: Original first corner coordinates
        original_corner2: Original second corner coordinates
        
    Returns:
        List[Tuple[float, float]]: List of coordinate tuples in the same format as the input
    """
    from bok_ucgs_fish_route.coordinates.conversion import wgs84_to_utm
    import pyproj
    
    # Define the rectangle corners in clockwise order (x, y) format
    corners = [
        (x_min, y_min),  # Bottom-left
        (x_max, y_min),  # Bottom-right
        (x_max, y_max),  # Top-right
        (x_min, y_max),  # Top-left
    ]
    
    # Initialize the list of coordinates
    utm_coordinates = []
    
    # Calculate the center of the rectangle
    center_x = (x_min + x_max) / 2
    center_y = (y_min + y_max) / 2
    
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
    
    # Calculate the rectangle's dimensions in meters (already in meters since using UTM)
    width_meters = x_max - x_min
    height_meters = y_max - y_min
    
    # Calculate the projection of the rectangle onto the direction perpendicular to the bands
    # This gives us the maximum distance we need to cover with bands
    projection_length = abs(width_meters * dx) + abs(height_meters * dy)
    
    # Calculate the number of bands needed
    num_bands = max(2, math.ceil(projection_length / band_distance) + 1)
    
    # Calculate the actual band distance in meters
    actual_band_distance = projection_length / (num_bands - 1) if num_bands > 1 else projection_length
    
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
            
            # Convert to local coordinates (in meters) relative to center
            start_x = start_corner[0] - center_x
            start_y = start_corner[1] - center_y
            end_x = end_corner[0] - center_x
            end_y = end_corner[1] - center_y
            
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
                
                # Convert back to absolute coordinates
                intersection_x_abs = center_x + intersection_x
                intersection_y_abs = center_y + intersection_y
                
                # Add to the list of intersections
                band_intersections.append((intersection_x_abs, intersection_y_abs))
        
        # If we found exactly 2 intersections, add them as waypoints
        if len(band_intersections) == 2:
            # Sort the intersections to ensure consistent direction along the angle
            # We want to sort them in the direction of the angle
            # Calculate the dot product of the vector from point1 to point2 with the band direction
            p1_x, p1_y = band_intersections[0]
            p2_x, p2_y = band_intersections[1]
            
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
            
            for idx, (new_x, new_y) in enumerate(band_intersections):
                # Check if this point is a duplicate of any existing point
                is_duplicate = False
                for ex_x, ex_y in all_intersections:
                    if (abs(ex_x - new_x) < epsilon and abs(ex_y - new_y) < epsilon):
                        is_duplicate = True
                        break
                
                if is_duplicate:
                    # Adjust the point based on which edge it's on
                    adjusted_x, adjusted_y = new_x, new_y
                    
                    # Determine which edge the point is on and adjust accordingly
                    if abs(new_y - y_min) < epsilon:  # Bottom edge
                        adjusted_x = new_x + 1e-8
                    elif abs(new_y - y_max) < epsilon:  # Top edge
                        adjusted_x = new_x - 1e-8
                    elif abs(new_x - x_min) < epsilon:  # Left edge
                        adjusted_y = new_y + 1e-8
                    elif abs(new_x - x_max) < epsilon:  # Right edge
                        adjusted_y = new_y - 1e-8
                    
                    # Add the adjusted point
                    adjusted_intersections.append((adjusted_x, adjusted_y))
                else:
                    # Add the original point
                    adjusted_intersections.append((new_x, new_y))
            
            # Replace band_intersections with the adjusted points
            band_intersections = adjusted_intersections
            
            # Add the intersections to the list of all intersections
            all_intersections.extend(band_intersections)
            
            # Add the coordinates
            utm_coordinates.append(band_intersections[0])
            utm_coordinates.append(band_intersections[1])
    
    # If the original coordinates were in WGS84, convert the result back to WGS84
    if was_converted:
        # Determine the UTM zone from the original coordinates
        lon1, lat1 = original_corner1
        
        # Create the transformer for the reverse conversion (UTM to WGS84)
        zone = int((lon1 + 180) / 6) + 1
        north = lat1 >= 0
        utm_proj_str = f"+proj=utm +zone={zone} {'+north' if north else '+south'} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
        transformer = pyproj.Transformer.from_crs(utm_proj_str, "EPSG:4326", always_xy=True)
        
        # Convert the coordinates back to WGS84
        wgs84_coordinates = []
        for x, y in utm_coordinates:
            lon, lat = transformer.transform(x, y)
            wgs84_coordinates.append((lon, lat))
        
        return wgs84_coordinates
    
    # If the original coordinates were already in UTM, return the UTM coordinates
    return utm_coordinates

def _create_angled_lawn_mower(lat_min: float, lat_max: float, lon_min: float, lon_max: float, 
                             band_distance: float, angle: float, 
                             lat_meters_per_degree: float, lon_meters_per_degree: float) -> List[Tuple[float, float]]:
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
        
    Returns:
        List[Tuple[float, float]]: List of coordinate tuples (longitude, latitude) with angled lawn mower pattern
    """
    # Define the rectangle corners in clockwise order
    corners = [
        (lat_min, lon_min),  # Bottom-left
        (lat_min, lon_max),  # Bottom-right
        (lat_max, lon_max),  # Top-right
        (lat_max, lon_min),  # Top-left
    ]
    
    # Initialize the list of coordinates
    coordinates = []
    
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
    # Initialize the list of coordinates (already done above)
    # coordinates = []
    
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
            
            # Add the coordinates
            coordinates.append((band_intersections[0][1], band_intersections[0][0]))
            coordinates.append((band_intersections[1][1], band_intersections[1][0]))
    
    return coordinates
