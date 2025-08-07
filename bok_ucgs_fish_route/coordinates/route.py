from typing import List, Tuple

from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate


def create_route_segment_from_coordinates(coordinates: List[Tuple[float, float]], altitude: float, speed: float) -> 'RouteSegment':
    """
    Create a RouteSegment from a list of coordinate tuples, an altitude, and a speed.
    
    Args:
        coordinates (List[Tuple[float, float]]): List of coordinate tuples (longitude, latitude)
        altitude (float): Altitude in meters to apply to all waypoints
        speed (float): Speed in meters per second
        
    Returns:
        RouteSegment: A route segment containing waypoints created from the coordinates
        
    Raises:
        ValueError: If coordinates list is empty
    """
    if not coordinates:
        raise ValueError("Coordinates list must not be empty")
    
    # Convert each coordinate tuple to a WaypointCoordinate
    waypoints = [
        WaypointCoordinate(lon=coord[0], lat=coord[1], altitude=altitude)
        for coord in coordinates
    ]
    
    # Create and return a RouteSegment
    return RouteSegment(waypoints, speed)


class RouteSegment:
    """
    A class representing a segment of a route with waypoints and speed.

    Attributes:
        waypoints (List[WaypointCoordinate]): List of waypoint coordinates in the segment
        speed (float): Speed in meters per second
    """

    def __init__(self, waypoints: List[WaypointCoordinate], speed: float):
        """
        Initialize a RouteSegment.

        Args:
            waypoints (List[WaypointCoordinate]): List of waypoint coordinates in the segment
            speed (float): Speed in meters per second
        """
        if not waypoints:
            raise ValueError("RouteSegment must contain at least one waypoint")
        
        # Convert speed to float first, then validate
        self.speed = float(speed)
        
        if self.speed <= 0:
            raise ValueError("Speed must be positive")
            
        self.waypoints = list(waypoints)  # Create a copy of the list

    def __len__(self):
        """Return the number of waypoints in the route segment."""
        return len(self.waypoints)

    def __repr__(self):
        """Return string representation of the route segment."""
        return f"RouteSegment(waypoints={self.waypoints}, speed={self.speed})"

    def __eq__(self, other):
        """Check if two route segments are equal."""
        if not isinstance(other, RouteSegment):
            return False
        return (self.waypoints == other.waypoints and
                self.speed == other.speed)