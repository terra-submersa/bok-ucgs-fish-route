import math


def wgs_to_radians(lon_deg, lat_deg):
    """
    Transform WGS84 coordinates from degrees to radians.
    
    Args:
        lon_deg (float): Longitude in degrees
        lat_deg (float): Latitude in degrees
        
    Returns:
        tuple: (longitude in radians, latitude in radians)
    """
    lon_rad = math.radians(lon_deg)
    lat_rad = math.radians(lat_deg)
    return lon_rad, lat_rad