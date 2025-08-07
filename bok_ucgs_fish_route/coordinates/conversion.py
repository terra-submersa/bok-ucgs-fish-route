"""
Utility functions for coordinate conversion between different coordinate systems.
"""
import logging
from typing import Tuple, Optional
import pyproj

# Configure logging
logger = logging.getLogger(__name__)

def is_wgs84_coordinates(lon: float, lat: float) -> bool:
    """
    Check if the given coordinates are within the WGS84 range.
    
    Args:
        lon (float): Longitude value
        lat (float): Latitude value
        
    Returns:
        bool: True if coordinates are within WGS84 range (-180/180 for longitude and -90/90 for latitude)
    """
    return -180 <= lon <= 180 and -90 <= lat <= 90

def get_utm_zone_for_coordinates(lon: float, lat: float) -> int:
    """
    Determine the UTM zone for the given WGS84 coordinates.
    
    Args:
        lon (float): Longitude in WGS84
        lat (float): Latitude in WGS84
        
    Returns:
        int: UTM zone number
    """
    # UTM zones are 6 degrees wide
    # Zone 1 starts at -180 degrees longitude
    zone = int((lon + 180) / 6) + 1
    return zone

def wgs84_to_utm(lon: float, lat: float) -> Tuple[float, float]:
    """
    Convert WGS84 coordinates (longitude, latitude) to UTM coordinates (easting, northing).
    
    Args:
        lon (float): Longitude in WGS84
        lat (float): Latitude in WGS84
        
    Returns:
        Tuple[float, float]: UTM coordinates as (easting, northing)
    """
    # Determine the UTM zone
    zone = get_utm_zone_for_coordinates(lon, lat)
    
    # Determine if the coordinate is in the northern or southern hemisphere
    north = lat >= 0
    
    # Create the UTM projection string
    utm_proj_str = f"+proj=utm +zone={zone} {'+north' if north else '+south'} +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    
    # Create the transformer
    transformer = pyproj.Transformer.from_crs("EPSG:4326", utm_proj_str, always_xy=True)
    
    # Transform the coordinates
    easting, northing = transformer.transform(lon, lat)
    
    return easting, northing

def convert_corners_from_wgs84_to_utm(corner1: Tuple[float, float], corner2: Tuple[float, float]) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Check if the given corner coordinates are in WGS84 range and convert them to UTM if they are.
    
    Args:
        corner1 (Tuple[float, float]): First corner coordinates as (x, y)
        corner2 (Tuple[float, float]): Second corner coordinates as (x, y)
        
    Returns:
        Tuple[Tuple[float, float], Tuple[float, float]]:
            - Converted or original corner1 coordinates
            - Converted or original corner2 coordinates
    """
    lon1, lat1 = corner1
    lon2, lat2 = corner2

    return wgs84_to_utm(lon1, lat1), wgs84_to_utm(lon2, lat2)
