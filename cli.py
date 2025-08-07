"""
Flask command line application for route segment generation and map export.
"""
import os
import tempfile
from flask import Flask, send_file, abort
import click

from bok_ucgs_fish_route.route_planner.perimeter import create_route_segment_perimeter
from bok_ucgs_fish_route.route_planner.lawn_mower import create_route_segment_lawn_mower
from bok_ucgs_fish_route.exporter.map_exporter import export_route_segment_to_png

app = Flask(__name__)

@app.cli.command("generate-perimeter-map")
@click.argument("lat1", type=float)
@click.argument("lon1", type=float)
@click.argument("lat2", type=float)
@click.argument("lon2", type=float)
@click.argument("speed", type=float)
@click.option("--epsg", type=int, default=3857, help="EPSG code for the map projection (default: 3857)")
@click.option("--output", type=str, help="Output file path (optional)")
def generate_perimeter_map(lat1, lon1, lat2, lon2, speed, epsg, output):
    """
    Generate a perimeter route map from two corner coordinates and a speed.
    
    Arguments:
    LAT1: Latitude of the first corner in WGS84
    LON1: Longitude of the first corner in WGS84
    LAT2: Latitude of the second corner in WGS84
    LON2: Longitude of the second corner in WGS84
    SPEED: Speed in meters per second
    
    Example:
        flask generate-perimeter-map 37.428 23.134 37.430 23.136 2.5
    """
    try:
        # Create the perimeter route segment
        corner1 = (lat1, lon1)
        corner2 = (lat2, lon2)
        route_segment = create_route_segment_perimeter(corner1, corner2, speed)
        
        # Determine output path
        if output:
            output_path = output
        else:
            # Create a temporary file if no output path is provided
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"perimeter_map_{lat1}_{lon1}_{lat2}_{lon2}_{speed}.png")
        
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
@click.argument("lat1", type=float)
@click.argument("lon1", type=float)
@click.argument("lat2", type=float)
@click.argument("lon2", type=float)
@click.argument("speed", type=float)
@click.argument("band_distance", type=float)
@click.option("--angle", type=float, default=0.0, help="Angle in degrees for lawn mowing direction. 0 is South->North, 90 is East->West (default: 0.0)")
@click.option("--epsg", type=int, default=3857, help="EPSG code for the map projection (default: 3857)")
@click.option("--output", type=str, help="Output file path (optional)")
def generate_lawn_mowing(lat1, lon1, lat2, lon2, speed, band_distance, angle, epsg, output):
    """
    Generate a lawn mowing pattern route map from two corner coordinates, a speed, band distance, and optional angle.
    
    Arguments:
    LAT1: Latitude of the first corner in WGS84
    LON1: Longitude of the first corner in WGS84
    LAT2: Latitude of the second corner in WGS84
    LON2: Longitude of the second corner in WGS84
    SPEED: Speed in meters per second
    BAND_DISTANCE: Maximum distance between two bands in meters
    
    Options:
    --angle: Angle in degrees for lawn mowing direction. 0 is South->North, 90 is East->West (default: 0.0)
    
    Example:
        flask generate-lawn-mowing 37.428 23.134 37.430 23.136 2.5 10.0
        flask generate-lawn-mowing 37.428 23.134 37.430 23.136 2.5 10.0 --angle 45.0
    """
    try:
        # Create the lawn mower route segment
        corner1 = (lat1, lon1)
        corner2 = (lat2, lon2)
        route_segment = create_route_segment_lawn_mower(
            corner1, 
            corner2, 
            speed, 
            band_distance,
            angle,
            f"EPSG:{epsg}"
        )
        
        # Determine output path
        if output:
            output_path = output
        else:
            # Create a temporary file if no output path is provided
            temp_dir = tempfile.gettempdir()
            output_path = os.path.join(temp_dir, f"lawn_mower_map_{lat1}_{lon1}_{lat2}_{lon2}_{speed}_{band_distance}.png")
        
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
