import json
from datetime import datetime, timezone

from typing import List
from bok_ucgs_fish_route.coordinates.route import RouteSegment


def _load_from_json(filename: str) -> dict:
    with open(filename, 'r') as fd:
        return json.load(fd)


def _route_segments_to_ucgs_segment(segments: list[RouteSegment]):
    waypoint = _load_from_json('config/ucgs/waypoint.json')
    raise NotImplementedError


def _route_segments_to_ucgs_route(segments: List[RouteSegment], epsg_code: str = "4326") -> dict:
    """
    Convert a list of route segments to a UcGS route structure.
    
    Args:
        segments (List[RouteSegment]): List of route segments to convert
        epsg_code (str, optional): EPSG code for the coordinate reference system. Defaults to "4326" (WGS84).
        
    Returns:
        dict: UcGS route structure
    """
    import math
    from pyproj import CRS, Transformer

    route_structure = _load_from_json('config/ucgs/route-structure.json')
    route_waypoints = []

    # Set up transformer if needed (if not WGS84)
    if epsg_code != "4326":
        crs_source = CRS.from_epsg(epsg_code)
        crs_wgs84 = CRS.from_epsg(4326)  # WGS84
        transformer = Transformer.from_crs(crs_source, crs_wgs84, always_xy=True)

    for segment in segments:
        for waypoint in segment.waypoints:
            # Create a new waypoint from the template
            ucgs_waypoint = _load_from_json('config/ucgs/waypoint.json')

            # Get coordinates
            lon, lat = waypoint.lon, waypoint.lat

            # Transform coordinates if needed
            if epsg_code != "4326":
                lon, lat = transformer.transform(lon, lat)

            # Convert coordinates to radians and set them
            ucgs_waypoint["point"]["latitude"] = math.radians(lat)
            ucgs_waypoint["point"]["longitude"] = math.radians(lon)
            ucgs_waypoint["point"]["altitude"] = waypoint.altitude

            # Set the speed from the segment
            ucgs_waypoint["parameters"]["speed"] = segment.speed

            # Add the waypoint to the list
            route_waypoints.append(ucgs_waypoint)

    # Add the waypoints to the route structure
    route_structure["segments"] = route_waypoints
    return route_structure


# STRAIGHT, ADAPTIVE_BANK_TURN
def export_ucgs_json(route: RouteSegment, output: str, route_name: str = "To Nowhere", epsg_code: str = "4326") -> None:
    """
    Export a route segment to a UcGS JSON file.
    
    Args:
        route (RouteSegment): Route segment to export
        output (str): Output file path
        epsg_code (str, optional): EPSG code for the coordinate reference system. Defaults to "4326" (WGS84).
    """
    route_wrapper = _load_from_json('config/ucgs/route-wrapper.json')

    # Convert the route segment to a UcGS route structure
    route_structure = _route_segments_to_ucgs_route([route], epsg_code)
    route_structure["name"] = route_name

    # Add the route structure to the wrapper
    route_wrapper["route"] = route_structure
    route_wrapper["route"]["creationTime"] = int(datetime.now(tz=timezone.utc).timestamp() * 1000)

    # Write the JSON to the output file
    with open(output, 'w') as fd:
        json.dump(route_wrapper, fd, indent=2)
