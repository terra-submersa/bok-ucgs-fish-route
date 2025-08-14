"""
Flask command line application for route segment generation and map export.

This module provides CLI commands for generating route segments and exporting them to maps.
The coordinates can be provided in either WGS84 (longitude, latitude in degrees) or 
UTM (easting, northing in meters) format. When using UTM coordinates, the UTM zone must 
be specified using the --utm parameter (e.g., "34N").

The module computes and logs the appropriate EPSG code for the coordinates and ensures
that all waypoint coordinates are stored in the UTM referential.
"""
import logging
import os
import tempfile

import click
from flask import Flask

from bok_ucgs_fish_route.coordinates.conversion import convert_corners_from_wgs84_to_utm
from bok_ucgs_fish_route.coordinates.route import create_route_segment_from_coordinates, add_water_entry_exit_segments, RouteSegment
from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate
from bok_ucgs_fish_route.exporter.map_exporter import export_route_segment_to_png
from bok_ucgs_fish_route.exporter.ucgs_exporter import export_ucgs_json
from bok_ucgs_fish_route.route_planner.lawn_mower import create_lawn_mower_band_strips, stitch_strips, extend_strips_perpendicular_ending, \
    reorder_strips_turning_radius, add_circle_end_of_strips

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.cli.command("generate-lawn-mowing",
                 help="""\
 Generate a lawn mowing pattern route map from two corner coordinates, a speed, band distance, and optional angle.
 
 The function handles coordinates in two formats:
 
 1. WGS84 (longitude, latitude in degrees) - default when no --utm parameter is provided
 2. UTM (easting, northing in meters) - when --utm parameter is provided with the UTM zone
 
 In both cases, the coordinates are processed in UTM for route generation, and the EPSG code
 is computed and logged. Waypoint coordinates are stored in the UTM referential.
 
 Arguments:
 
 - LON1: X-coordinate of the first corner (longitude in WGS84 or easting in UTM)
 - LAT1: Y-coordinate of the first corner (latitude in WGS84 or northing in UTM)
 - LON2: X-coordinate of the second corner (longitude in WGS84 or easting in UTM)
 - LAT2: Y-coordinate of the second corner (latitude in WGS84 or northing in UTM)
 
 Options:
 
   - --angle: Angle in degrees for lawn mowing direction. 0 is South->North, 90 is East->West (default: 0.0)
   - --utm: UTM zone (e.g., '34N') if coordinates are in UTM instead of WGS84
   - --image: the png file name to export a route snapshot
   - --ucgs: the json file name to export to rute to be imported in UCGS
 
 Example:
     # Using WGS84 coordinates (degrees)
     flask generate-lawn-mowing 23.134 37.428 23.136 37.430 2.5 10.0
     flask generate-lawn-mowing 23.134 37.428 23.136 37.430 2.5 10.0 --angle 45.0
     
     # Using UTM coordinates (meters)
     flask generate-lawn-mowing 500000 4000000 500100 4000100 2.5 10.0 --utm 34N
 """)
@click.argument("lon1", type=float)
@click.argument("lat1", type=float)
@click.argument("lon2", type=float)
@click.argument("lat2", type=float)
@click.option("--altitude", type=float, default=4)
@click.option("--speed", type=float, default=2)
@click.option("--band-width", type=float, default=1)
@click.option("--turning_radius", type=float, default=0)
@click.option("--angle", type=float, default=0.0,
              help="Angle in degrees for lawn mowing direction. 0 is South->North, 90 is East->West (default: 0.0)")
@click.option("--utm", type=str, help="UTM zone (e.g., '34N') if coordinates are in UTM instead of WGS84")
@click.option("--epsg", type=int, default=3857, help="EPSG code for the map projection (default: 3857)")
@click.option("--name", "route_name", type=str, help="route name (optional)")
@click.option("--image", "out_image", type=str, help="output image file path (optional)")
@click.option("--ucgs", "out_ucgs", type=str, help="output ucgs json file path (optional)")
def generate_lawn_mowing(lon1, lat1, lon2, lat2, altitude, speed, turning_radius, band_width, angle, utm=None, epsg=None, route_name="to nowhere",
                         out_image=None,
                         out_ucgs=None):
    # Create the corner coordinates
    corner1, corner2, utm_corner1, utm_corner2, utm_epsg = extract_utm_corners_utm_epsg(lat1, lat2, lon1, lon2, utm)

    # Create the lawn mower coordinates using UTM coordinates
    strips = create_lawn_mower_band_strips(
        utm_corner1,
        utm_corner2,
        band_width,
        angle
    )

    if turning_radius > 0:
        strips = reorder_strips_turning_radius(strips, turning_radius)
    strips = extend_strips_perpendicular_ending(strips)
    coordinates = stitch_strips(strips, turning_radius=turning_radius)

    # Create the route segment from coordinates
    mowing_route_segment = create_route_segment_from_coordinates(coordinates, altitude, speed, utm_epsg)
    print(mowing_route_segment)

    # Determine output path
    if out_image:
        output_image_path = out_image
    else:
        # Create a temporary file if no output path is provided
        temp_dir = tempfile.gettempdir()
        output_image_path = os.path.join(temp_dir, f"lawn_mower_map_{corner1[0]}_{corner1[1]}_{corner2[0]}_{corner2[1]}_{speed}_{band_width}.png")

    # Export the route segment to a PNG image
    title = f"{route_name} (Speed: {speed} m/s, band delta: {band_width} m)"
    export_route_segment_to_png(
        route_segment=mowing_route_segment,
        epsg_code=epsg,
        output_path=output_image_path,
        area_corners=(corner1, corner2),
        title=title
    )
    click.echo(f"Map generated and saved to: {output_image_path} with {len(mowing_route_segment)} waypoints")

    full_segments = add_water_entry_exit_segments(mowing_route_segment, traveling_altitude=12)

    if out_ucgs:
        export_ucgs_json(full_segments, out_ucgs, route_name=route_name, epsg_code='4326')
        click.echo(f"Route exported to UCGS JSON file: {out_ucgs}")

    return output_image_path


@app.cli.command("generate-backand-forth",
                 help="""\
 Generate a lawn mowing pattern route map from two corner coordinates, a speed, band distance, and optional angle.
 
 The function handles coordinates in two formats:
 
 1. WGS84 (longitude, latitude in degrees) - default when no --utm parameter is provided
 2. UTM (easting, northing in meters) - when --utm parameter is provided with the UTM zone
 
 In both cases, the coordinates are processed in UTM for route generation, and the EPSG code
 is computed and logged. Waypoint coordinates are stored in the UTM referential.
 
 Arguments:
 
 - LON1: X-coordinate of the first corner (longitude in WGS84 or easting in UTM)
 - LAT1: Y-coordinate of the first corner (latitude in WGS84 or northing in UTM)
 - LON2: X-coordinate of the second corner (longitude in WGS84 or easting in UTM)
 - LAT2: Y-coordinate of the second corner (latitude in WGS84 or northing in UTM)
 
 Options:
 
   - --utm: UTM zone (e.g., '34N') if coordinates are in UTM instead of WGS84
   - --ucgs: the json file name to export to rute to be imported in UCGS
   - --altitude=z altitude in meters (default: 4)
   - --speed=v speed in meters per second (default: 2)
   - --nb-times=n number of times to repeat the route (default: 2). 0 means only onw way
   - --name: the route name (optional)
 
 Example:
     # Using WGS84 coordinates (degrees)
     flask generate-backand-forth 23.134 37.428 23.136 37.430 2.5 10.0 3
     
     # Using UTM coordinates (meters)
     flask generate-backand-forth 500000 4000000 500100 4000100 2.5 10.0 3 --utm 34N
 """)
@click.argument("lon1", type=float)
@click.argument("lat1", type=float)
@click.argument("lon2", type=float)
@click.argument("lat2", type=float)
@click.option("--altitude", type=float, default=4)
@click.option("--speed", type=float, default=2)
@click.option("--nb-times", type=int, default=2)
@click.option("--utm", type=str, help="UTM zone (e.g., '34N') if coordinates are in UTM instead of   WGS84")
@click.option("--name", "route_name", type=str, help="route name (optional)", default="to nowhere")
@click.option("--ucgs", "out_ucgs", type=str, help="output ucgs json file path (optional)")
def generate_back_and_forth(lon1, lat1, lon2, lat2, altitude, speed, nb_times: int, utm, route_name, out_ucgs=None):
    # Create the corner coordinates
    corner1, corner2, utm_corner1, utm_corner2, utm_epsg = extract_utm_corners_utm_epsg(lat1, lat2, lon1, lon2, utm)

    # Create the lawn mower coordinates using UTM coordinates
    route_1 = RouteSegment(
        [WaypointCoordinate(corner1[0], corner1[1], altitude), WaypointCoordinate(corner2[0], corner2[1], altitude)],
        speed=speed
    )
    route_1_segments = add_water_entry_exit_segments(route_1, traveling_altitude=10)

    route_2 = RouteSegment(
        [WaypointCoordinate(corner2[0], corner2[1], altitude), WaypointCoordinate(corner1[0], corner1[1], altitude)],
        speed=speed
    )
    route_2_segments = add_water_entry_exit_segments(route_2, traveling_altitude=10)

    route_seggments = []
    if nb_times == 0:
        route_seggments.extend(route_1_segments)
    else:
        for _ in range(nb_times):
            route_seggments.extend(route_1_segments)
            route_seggments.extend(route_2_segments)

    if out_ucgs:
        export_ucgs_json(route_seggments, out_ucgs, route_name=route_name, epsg_code='4326')
        click.echo(f"Route exported to UCGS JSON file: {out_ucgs}")


def extract_utm_corners_utm_epsg(lat1, lat2, lon1, lon2, utm):
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
        if corner1[0] < -180 or corner1[0] > 180 or corner2[0] < -180 or corner2[0] > 180:
            raise ValueError("Longitude coordinates must be in the range [-180, 180] or set --utm parameter")
        if corner1[1] < -90 or corner1[1] > 90 or corner2[1] < -90 or corner2[1] > 90:
            raise ValueError("Latitude coordinates must be in the range [-90, 90] or set --utm parameter")
        utm_corner1, utm_corner2 = convert_corners_from_wgs84_to_utm(corner1, corner2)

        lon1, lat1 = corner1
        zone_number = int((lon1 + 180) / 6) + 1
        hemisphere = 'N' if lat1 >= 0 else 'S'
        utm_zone = f"{zone_number}{hemisphere}"

        # Compute EPSG code for the UTM zone
        utm_epsg = 32600 + zone_number if hemisphere == 'N' else 32700 + zone_number

        logger.info(f"Converted WGS84 coordinates to UTM zone {utm_zone} (EPSG:{utm_epsg}): {utm_corner1}, {utm_corner2}")
    return corner1, corner2, utm_corner1, utm_corner2, utm_epsg
