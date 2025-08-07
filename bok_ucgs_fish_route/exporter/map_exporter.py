"""
Module for exporting route segments to map images.
"""
import matplotlib.pyplot as plt
import contextily as ctx
import geopandas as gpd
from shapely.geometry import LineString, Point
import os
from typing import Optional

from bok_ucgs_fish_route.coordinates.route import RouteSegment


def export_route_segment_to_png(
    route_segment: RouteSegment,
    epsg_code: int,
    output_path: str,
    width: int = 10,
    height: int = 10,
    dpi: int = 100,
    line_color: str = 'red',
    line_width: float = 2.0,
    marker_color: str = 'blue',
    marker_size: float = 50,
    title: Optional[str] = None
) -> str:
    """
    Export a RouteSegment to a PNG image with an OpenStreetMap base layer.

    Args:
        route_segment: The RouteSegment to export
        epsg_code: The EPSG code to set the coordinate reference system
        output_path: Path where the PNG file will be saved
        width: Width of the figure in inches (default: 10)
        height: Height of the figure in inches (default: 10)
        dpi: Resolution of the figure (default: 100)
        line_color: Color of the route line (default: 'red')
        line_width: Width of the route line (default: 2.0)
        marker_color: Color of the waypoint markers (default: 'blue')
        marker_size: Size of the waypoint markers (default: 50)
        title: Optional title for the map

    Returns:
        The path to the saved PNG file

    Raises:
        ValueError: If the route_segment is empty or if the output directory doesn't exist
    """
    if len(route_segment) < 1:
        raise ValueError("Route segment must contain at least one waypoint")

    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Extract coordinates from waypoints
    lons = [wp.lon for wp in route_segment.waypoints]
    lats = [wp.lat for wp in route_segment.waypoints]

    # Create a GeoDataFrame for the route line
    if len(route_segment) > 1:
        line = LineString([(lon, lat) for lon, lat in zip(lons, lats)])
        route_gdf = gpd.GeoDataFrame(geometry=[line], crs="EPSG:4326")
    else:
        # If there's only one waypoint, create a point
        point = Point(lons[0], lats[0])
        route_gdf = gpd.GeoDataFrame(geometry=[point], crs="EPSG:4326")

    # Create a GeoDataFrame for the waypoints
    waypoints_gdf = gpd.GeoDataFrame(
        geometry=[Point(lon, lat) for lon, lat in zip(lons, lats)],
        crs="EPSG:4326"
    )

    # Reproject to the specified CRS
    route_gdf = route_gdf.to_crs(epsg=epsg_code)
    waypoints_gdf = waypoints_gdf.to_crs(epsg=epsg_code)

    # Create the plot
    fig, ax = plt.subplots(figsize=(width, height))

    # Plot the route line
    route_gdf.plot(ax=ax, color=line_color, linewidth=line_width)

    # Plot the waypoints
    waypoints_gdf.plot(ax=ax, color=marker_color, markersize=marker_size)

    # Add OpenStreetMap base layer
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, crs=route_gdf.crs.to_string())

    # Add title if provided
    if title:
        ax.set_title(title)

    # Remove axis labels
    ax.set_axis_off()

    # Save the figure
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)

    return output_path