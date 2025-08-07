import math
from typing import Tuple

from bok_ucgs_fish_route.coordinates.route import RouteSegment
from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate


def create_route_segment_lawn_mower(
    corner1: Tuple[float, float],
    corner2: Tuple[float, float],
    speed: float,
    band_distance: float,
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
        epsg_code (str, optional): EPSG code for the coordinate reference system. Defaults to "EPSG:4326" (WGS84).

    Returns:
        RouteSegment: A route segment with a lawn mower pattern within the rectangle

    Example:
        >>> corner1 = (37.428, 23.134)  # (lat, lon)
        >>> corner2 = (37.430, 23.136)  # (lat, lon)
        >>> segment = create_route_segment_lawn_mower(corner1, corner2, 2.5, 10.0)
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

    # Convert band_distance to degrees for latitude and longitude
    band_distance_lat_deg = band_distance / lat_meters_per_degree
    band_distance_lon_deg = band_distance / lon_meters_per_degree

    # Determine if bands should be horizontal (east-west) or vertical (north-south)
    # Choose the direction that results in fewer bands
    horizontal_bands = width_deg / band_distance_lon_deg <= height_deg / band_distance_lat_deg

    # Calculate the number of bands and the actual band distance
    if horizontal_bands:
        # Horizontal bands (east-west)
        # Calculate the number of bands that would fit with the specified distance
        # We want the highest number that divides the rectangle with a distance lower than the given
        height_meters = height_deg * lat_meters_per_degree

        # Calculate the number of bands needed to ensure the distance is at most the specified distance
        # We need at least 2 bands, and we add 1 to ensure the distance is strictly less than band_distance
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
    else:
        # Vertical bands (north-south)
        # Calculate the number of bands that would fit with the specified distance
        width_meters = width_deg * lon_meters_per_degree

        # Calculate the number of bands needed to ensure the distance is at most the specified distance
        # We need at least 2 bands, and we add 1 to ensure the distance is strictly less than band_distance
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

    # Create and return the route segment
    return RouteSegment(waypoints, speed)
