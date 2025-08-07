from typing import Tuple

from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate
from bok_ucgs_fish_route.coordinates.route import RouteSegment


def create_route_segment_perimeter(
    corner1: Tuple[float, float],
    corner2: Tuple[float, float],
    speed: float
) -> RouteSegment:
    """
    Create a RouteSegment that passes through the 4 corners of a rectangle defined by two opposite corners.
    
    The function takes two corners of a rectangle in WGS coordinates (longitude, latitude) and creates
    a route segment that traverses the perimeter of the rectangle in a clockwise direction starting
    from the first corner.
    
    Args:
        corner1 (Tuple[float, float]): First corner coordinates as (longitude, latitude)
        corner2 (Tuple[float, float]): Second corner coordinates as (longitude, latitude)
        speed (float): Speed in meters per second
        
    Returns:
        RouteSegment: A route segment passing through all 4 corners of the rectangle
        
    Example:
        >>> corner1 = (23.134, 37.428)  # (lon, lat)
        >>> corner2 = (23.136, 37.430)  # (lon, lat)
        >>> segment = create_route_segment_perimeter(corner1, corner2, 2.5)
    """
    # Extract coordinates
    lon1, lat1 = corner1
    lon2, lat2 = corner2
    
    # Create all four corners of the rectangle
    # We'll go clockwise starting from corner1
    corner_coordinates = [
        (lon1, lat1),  # First corner (starting point)
        (lon2, lat1),  # Second corner
        (lon2, lat2),  # Third corner (opposite to starting point)
        (lon1, lat2),  # Fourth corner
        (lon1, lat1),  # Back to the starting point to complete the perimeter
    ]
    
    # Create waypoints from the corner coordinates
    waypoints = [
        WaypointCoordinate(lon, lat) for lon, lat in corner_coordinates
    ]
    
    # Create and return the route segment
    return RouteSegment(waypoints, speed)


