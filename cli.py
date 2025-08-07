"""
Flask command line application for route segment generation and map export.

This module provides CLI commands for generating route segments and exporting them to maps.
The coordinates can be provided in either WGS84 (longitude, latitude in degrees) or 
UTM (easting, northing in meters) format. When using UTM coordinates, the UTM zone must 
be specified using the --utm parameter (e.g., "34N").

The module computes and logs the appropriate EPSG code for the coordinates and ensures
that all waypoint coordinates are stored in the UTM referential.
"""
import os
import tempfile
import logging
from flask import Flask, send_file, abort
import click

from bok_ucgs_fish_route.route_planner.perimeter import create_route_segment_perimeter
from bok_ucgs_fish_route.route_planner.lawn_mower import create_route_segment_lawn_mower
from bok_ucgs_fish_route.coordinates.route import create_route_segment_from_coordinates
from bok_ucgs_fish_route.coordinates.conversion import convert_corners_if_wgs84
from bok_ucgs_fish_route.exporter.map_exporter import export_route_segment_to_png

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.cli.command("generate-perimeter-map")
@click.argument("lon1", type=float)
@click.argument("lat1", type=float)
@click.argument("lon2", type=float)
@click.argument("lat2", type=float)
@click.argument("speed", type=float)
@click.option("--utm", type=str, help="UTM zone (e.g., '34N') if coordinates are in UTM instead of WGS84")
@click.option("--epsg", type=int, default=3857, help="EPSG code for the map projection (default: 3857)")
@click.option("--output", type=str, help="Output file path (optional)")
def generate_perimeter_map(lon1, lat1, lon2, lat2, speed, utm, epsg, output):
    """
    Generate a perimeter route map from two corner coordinates and a speed.
    
    The function handles coordinates in two formats:
    1. WGS84 (longitude, latitude in degrees) - default when no --utm parameter is provided
    2. UTM (easting, northing in meters) - when --utm parameter is provided with the UTM zone
    
    In both cases, the coordinates are processed in UTM for route generation, and the EPSG code
    is computed and logged. Waypoint coordinates are stored in the UTM referential.
    
    Arguments:
    LON1: X-coordinate of the first corner (longitude in WGS84 or easting in UTM)
    LAT1: Y-coordinate of the first corner (latitude in WGS84 or northing in UTM)
    LON2: X-coordinate of the second corner (longitude in WGS84 or easting in UTM)
    LAT2: Y-coordinate of the second corner (latitude in WGS84 or northing in UTM)
    SPEED: Speed in meters per second
    
    Options:
    --utm: UTM zone (e.g., '34N') if coordinates are in UTM instead of WGS84
    
    Example:
        # Using WGS84 coordinates (degrees)
        flask generate-perimeter-map 23.134 37.428 23.136 37.430 2.5
        
        # Using UTM coordinates (meters)
        flask generate-perimeter-map 500000 4000000 500100 4000100 2.5 --utm 34N
    """
    try:
        # Create the corner coordinates
        corner1 = (lon1, lat1)
        corner2 = (lon2, lat2)
        
        # Handle coordinates based on whether UTM zone is specified
        if utm:
            # Coordinates are in UTM
            utm_corner1 = corner1
            utm_corner2 = corner2
            was_converted = False
            
            # Extract zone number and hemisphere from UTM string (e.g., "34N")
            zone_number = int(utm.rstrip('NS'))
            hemisphere = utm[-1].upper()
            north = hemisphere == 'N'
            
            # Compute EPSG code for the UTM zone
            # UTM North zones: EPSG = 32600 + zone_number
            # UTM South zones: EPSG = 32700 + zone_number
            utm_epsg = 32600 + zone_number if north else 32700 + zone_number
            
            logger.info(f"Using UTM coordinates with zone {utm} (EPSG:{utm_epsg}): {utm_corner1}, {utm_corner2}")
        else:
            # Assume coordinates are in WGS84 and convert to UTM if needed
            utm_corner1, utm_corner2, was_converted = convert_corners_if_wgs84(corner1, corner2)
            
            if was_converted:
                # Determine UTM zone from the coordinates
                lon1, lat1 = corner1
                zone_number = int((lon1 + 180) / 6) + 1
                hemisphere = 'N' if lat1 >= 0 else 'S'
                utm_zone = f"{zone_number}{hemisphere}"
                
                # Compute EPSG code for the UTM zone
                utm_epsg = 32600 + zone_number if hemisphere == 'N' else 32700 + zone_number
                
                logger.info(f"Converted WGS84 coordinates to UTM zone {utm_zone} (EPSG:{utm_epsg}): {utm_corner1}, {utm_corner2}")
        
        # Create the perimeter coordinates using UTM coordinates
        coordinates = create_route_segment_perimeter(utm_corner1, utm_corner2)
        
        # Create the route segment from coordinates
        altitude = 0.0  # Default altitude
        route_segment = create_route_segment_from_coordinates(coordinates, altitude, speed)
        
        # Determine output path
        if output:
            output_path = output
        else:
            # Create a temporary file if no output path is provided
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"perimeter_map_{lon1}_{lat1}_{lon2}_{lat2}_{speed}.png")
        
        # Export the route segment to a PNG image
        title = f"Perimeter Route (Speed: {speed} m/s)"
        export_route_segment_to_png(
            route_segment=route_segment,
            epsg_code=epsg,
            output_path=output_path,
            title=title
        )
        
        click.echo(f"Map generated and saved to: {output_path}")
        return output_path
        
    except Exception as e:
        raise e
        click.echo(f"Error generating map: {str(e)}", err=True)
        return None

@app.cli.command("generate-lawn-mowing")
@click.argument("lon1", type=float)
@click.argument("lat1", type=float)
@click.argument("lon2", type=float)
@click.argument("lat2", type=float)
@click.argument("speed", type=float)
@click.argument("band_distance", type=float)
@click.option("--angle", type=float, default=0.0, help="Angle in degrees for lawn mowing direction. 0 is South->North, 90 is East->West (default: 0.0)")
@click.option("--utm", type=str, help="UTM zone (e.g., '34N') if coordinates are in UTM instead of WGS84")
@click.option("--epsg", type=int, default=3857, help="EPSG code for the map projection (default: 3857)")
@click.option("--output", type=str, help="Output file path (optional)")
def generate_lawn_mowing(lon1, lat1, lon2, lat2, speed, band_distance, angle, utm, epsg, output):
    """
    Generate a lawn mowing pattern route map from two corner coordinates, a speed, band distance, and optional angle.
    
    The function handles coordinates in two formats:
    1. WGS84 (longitude, latitude in degrees) - default when no --utm parameter is provided
    2. UTM (easting, northing in meters) - when --utm parameter is provided with the UTM zone
    
    In both cases, the coordinates are processed in UTM for route generation, and the EPSG code
    is computed and logged. Waypoint coordinates are stored in the UTM referential.
    
    Arguments:
    LON1: X-coordinate of the first corner (longitude in WGS84 or easting in UTM)
    LAT1: Y-coordinate of the first corner (latitude in WGS84 or northing in UTM)
    LON2: X-coordinate of the second corner (longitude in WGS84 or easting in UTM)
    LAT2: Y-coordinate of the second corner (latitude in WGS84 or northing in UTM)
    SPEED: Speed in meters per second
    BAND_DISTANCE: Maximum distance between two bands in meters
    
    Options:
    --angle: Angle in degrees for lawn mowing direction. 0 is South->North, 90 is East->West (default: 0.0)
    --utm: UTM zone (e.g., '34N') if coordinates are in UTM instead of WGS84
    
    Example:
        # Using WGS84 coordinates (degrees)
        flask generate-lawn-mowing 23.134 37.428 23.136 37.430 2.5 10.0
        flask generate-lawn-mowing 23.134 37.428 23.136 37.430 2.5 10.0 --angle 45.0
        
        # Using UTM coordinates (meters)
        flask generate-lawn-mowing 500000 4000000 500100 4000100 2.5 10.0 --utm 34N
    """
    try:
        # Create the corner coordinates
        corner1 = (lon1, lat1)
        corner2 = (lon2, lat2)
        
        # Handle coordinates based on whether UTM zone is specified
        if utm:
            # Coordinates are in UTM
            utm_corner1 = corner1
            utm_corner2 = corner2
            was_converted = False
            
            # Extract zone number and hemisphere from UTM string (e.g., "34N")
            zone_number = int(utm.rstrip('NS'))
            hemisphere = utm[-1].upper()
            north = hemisphere == 'N'
            
            # Compute EPSG code for the UTM zone
            # UTM North zones: EPSG = 32600 + zone_number
            # UTM South zones: EPSG = 32700 + zone_number
            utm_epsg = 32600 + zone_number if north else 32700 + zone_number
            
            logger.info(f"Using UTM coordinates with zone {utm} (EPSG:{utm_epsg}): {utm_corner1}, {utm_corner2}")
        else:
            # Assume coordinates are in WGS84 and convert to UTM if needed
            utm_corner1, utm_corner2, was_converted = convert_corners_if_wgs84(corner1, corner2)
            
            if was_converted:
                # Determine UTM zone from the coordinates
                lon1, lat1 = corner1
                zone_number = int((lon1 + 180) / 6) + 1
                hemisphere = 'N' if lat1 >= 0 else 'S'
                utm_zone = f"{zone_number}{hemisphere}"
                
                # Compute EPSG code for the UTM zone
                utm_epsg = 32600 + zone_number if hemisphere == 'N' else 32700 + zone_number
                
                logger.info(f"Converted WGS84 coordinates to UTM zone {utm_zone} (EPSG:{utm_epsg}): {utm_corner1}, {utm_corner2}")
        
        # Create the lawn mower coordinates using UTM coordinates
        coordinates = create_route_segment_lawn_mower(
            utm_corner1, 
            utm_corner2, 
            band_distance,
            angle
        )
        
        # Create the route segment from coordinates
        altitude = 0.0  # Default altitude
        route_segment = create_route_segment_from_coordinates(coordinates, altitude, speed)
        
        # Determine output path
        if output:
            output_path = output
        else:
            # Create a temporary file if no output path is provided
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"lawn_mower_map_{lon1}_{lat1}_{lon2}_{lat2}_{speed}_{band_distance}.png")
        
        # Export the route segment to a PNG image
        title = f"Lawn Mowing Route (Speed: {speed} m/s, Band Distance: {band_distance} m)"
        export_route_segment_to_png(
            route_segment=route_segment,
            epsg_code=epsg,
            output_path=output_path,
            title=title
        )
        
        click.echo(f"Map generated and saved to: {output_path}")
        return output_path
        
    except Exception as e:
        raise e
        click.echo(f"Error generating map: {str(e)}", err=True)
        return None
