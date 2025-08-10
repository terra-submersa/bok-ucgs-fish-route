from typing import List, Tuple

from pyproj import Geod

from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate
from pyproj import CRS, Transformer


def add_water_entry_exit_segments(route_segment: 'RouteSegment', traveling_altitude: float) -> 'RouteSegment':
    """Add water entry and exit waypoints to a route segment."""
    return [
        *create_water_landing_segments(
            route_segment,
            traveling_altitude=traveling_altitude,
        ),
        route_segment,
        *create_water_take_off_segment(
            route_segment,
            traveling_altitude=traveling_altitude,
        )
    ]


def create_water_landing_segments(
        scanning_segment: 'RouteSegment',
        traveling_altitude: float,
        safe_altitude: float = 7,
        distance_to_start: float = 5,
        speed_air=3,
        speed_water=0.2,

) -> list['RouteSegment']:
    scan_0 = scanning_segment.waypoints[0]
    scan_1 = scanning_segment.waypoints[1]

    geod = Geod(ellps="WGS84")
    _, azimuth, _ = geod.inv(scan_0.lon, scan_0.lat, scan_1.lon, scan_1.lat)
    drop_lon, drop_lat, _ = geod.fwd(scan_0.lon, scan_0.lat, azimuth, distance_to_start)
    down_lon, down_lat, _ = geod.fwd(drop_lon, drop_lat, azimuth, 2)

    air_segment = RouteSegment([
        WaypointCoordinate(lon=down_lon, lat=down_lat, altitude=traveling_altitude),
    ],
        speed=speed_air
    )
    water_segment = RouteSegment([
        WaypointCoordinate(lon=down_lon, lat=down_lat, altitude=safe_altitude),
        WaypointCoordinate(lon=drop_lon, lat=drop_lat, altitude=scan_0.altitude),
    ],
        speed=speed_water)

    return [air_segment, water_segment]


def create_water_take_off_segment(
        scanning_segment: 'RouteSegment',
        traveling_altitude: float,
        safe_altitude: float = 7,
        speed_air=2,
        speed_water=0.5,
) -> list['RouteSegment']:
    scan_last = scanning_segment.waypoints[-1]
    water_segment = RouteSegment(
        [WaypointCoordinate(lon=scan_last.lon, lat=scan_last.lat, altitude=safe_altitude)],
        speed=speed_water
    )
    air_segment = RouteSegment(
        [WaypointCoordinate(lon=scan_last.lon, lat=scan_last.lat, altitude=traveling_altitude)],
        speed=speed_air
    )
    return [water_segment, air_segment]


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
