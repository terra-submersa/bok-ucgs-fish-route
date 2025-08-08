from typing import List, Tuple

from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate
from pyproj import CRS, Transformer

def create_route_segment_from_coordinates(
        coordinates: List[Tuple[float, float]],
        altitude: float,
        speed: float,
        utm_epsg: str
) -> 'RouteSegment':
    """
    Create a RouteSegment from a list of coordinate tuples, an altitude, and a speed.
    
    Args:
        coordinates (List[Tuple[float, float]]): List of coordinate tuples (northing, easting)
        altitude (float): Altitude in meters to apply to all waypoints
        speed (float): Speed in meters per second
        utm_epsg (str): EPSG code for the UTM zone to use for the route
        
    Returns:
        RouteSegment: A route segment containing waypoints created from the coordinates
        
    Raises:
        ValueError: If coordinates list is empty
    """
    if not coordinates:
        raise ValueError("Coordinates list must not be empty")

    crs_utm = CRS.from_epsg(utm_epsg)
    crs_wgs84 = CRS.from_epsg(4326)  # EPSG:4326 = WGS84

    # Set up transformer from UTM to WGS84
    transformer = Transformer.from_crs(crs_utm, crs_wgs84, always_xy=True)

    # Convert each coordinate tuple to a WaypointCoordinate
    waypoints = []
    for coord in coordinates:
        lon, lat = transformer.transform(coord[0], coord[1])
        waypoints.append(WaypointCoordinate(lon=lon, lat=lat, altitude=altitude))

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
        buf = "waypoints=\n\t"
        buf += '\n\t'.join(str(wp) for wp in self.waypoints)
        buf += f"\nspeed={self.speed}"
        return buf

    def __eq__(self, other):
        """Check if two route segments are equal."""
        if not isinstance(other, RouteSegment):
            return False
        return (self.waypoints == other.waypoints and
                self.speed == other.speed)