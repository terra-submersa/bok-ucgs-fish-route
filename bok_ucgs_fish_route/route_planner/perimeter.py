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
    
    The function takes two corners of a rectangle in WGS coordinates (latitude, longitude) and creates
    a route segment that traverses the perimeter of the rectangle in a clockwise direction starting
    from the first corner.
    
    Args:
        corner1 (Tuple[float, float]): First corner coordinates as (latitude, longitude)
        corner2 (Tuple[float, float]): Second corner coordinates as (latitude, longitude)
        speed (float): Speed in meters per second
        
    Returns:
        RouteSegment: A route segment passing through all 4 corners of the rectangle
        
    Example:
        >>> corner1 = (37.428, 23.134)  # (lat, lon)
        >>> corner2 = (37.430, 23.136)  # (lat, lon)
        >>> segment = create_route_segment_perimeter(corner1, corner2, 2.5)
    """
    # Extract coordinates
    lat1, lon1 = corner1
    lat2, lon2 = corner2
    
    # Create all four corners of the rectangle
    # We'll go clockwise starting from corner1
    corner_coordinates = [
        (lat1, lon1),  # First corner (starting point)
        (lat1, lon2),  # Second corner
        (lat2, lon2),  # Third corner (opposite to starting point)
        (lat2, lon1),  # Fourth corner
        (lat1, lon1),  # Back to the starting point to complete the perimeter
    ]
    
    # Create waypoints from the corner coordinates
    waypoints = [
        WaypointCoordinate(lat, lon) for lat, lon in corner_coordinates
    ]
    
    # Create and return the route segment
    return RouteSegment(waypoints, speed)


