import logging
import math
from typing import Tuple, List

# Configure logging
logger = logging.getLogger(__name__)


def stitch_strips(strips: List[Tuple[Tuple[float, float], Tuple[float, float] | None]]) -> List[Tuple[float, float]]:
    coordinates = []
    for i, strip in enumerate(strips):
        if strip[1] is None:
            coordinates.append(strip[0])
            continue
        if i % 2 == 0:
            coordinates.append(strip[0])
            coordinates.append(strip[1])
        else:
            coordinates.append(strip[1])
            coordinates.append(strip[0])

    return coordinates


def extend_strip_perpendicular_ending(
        strips: List[Tuple[Tuple[float, float], Tuple[float, float] | None]]
) -> List[Tuple[Tuple[float, float], Tuple[float, float] | None]]:
    if len(strips) <= 1:
        return strips
    ret_strips = [((s[0][0], s[0][1]), None if s[1] is None else (s[1][0], s[1][1])) for s in strips]
    for i in range(len(strips) - 1):
        strip_1 = ret_strips[i]
        strip_2 = ret_strips[i + 1]
        start_point_1 = strip_1[0]
        start_point_2 = strip_2[0]
        end_point_1 = strip_1[0] if strip_1[1] is None else strip_1[1]
        end_point_2 = strip_2[0] if strip_2[1] is None else strip_2[1]

        # pushing ahead
        if i%2 == 0:
            if is_perpendicular_ahead_of_strip(end_point_1, strip_2):
                ret_strips[i+1] = (strip_2[0], get_projection_point_on_strip(end_point_1, strip_2))
            elif is_perpendicular_ahead_of_strip(end_point_2, strip_1):
                ret_strips[i] = (strip_1[0], get_projection_point_on_strip(end_point_2, strip_1))
        else:
            rev_strip_1 = reverse_strip(strip_1)
            rev_strip_2 = reverse_strip(strip_2)
            if is_perpendicular_ahead_of_strip(start_point_1, rev_strip_2):
                ret_strips[i+1] = (get_projection_point_on_strip(start_point_1, rev_strip_2), strip_2[1])
            elif is_perpendicular_ahead_of_strip(start_point_2, rev_strip_1):
                ret_strips[i] = (get_projection_point_on_strip(start_point_2, rev_strip_1), strip_1[1])

    return ret_strips

def create_lawn_mower_band_strips(
        corner1: Tuple[float, float],
        corner2: Tuple[float, float],
        band_distance: float,
        angle: float = 0.0
) -> List[Tuple[Tuple[float, float], Tuple[float, float] | None]]:
    """
    Create a list of coordinates with a lawn mower pattern within a rectangle.

    The function takes two corners of a rectangle and creates a list of coordinates
    that traverses the rectangle in parallel bands (lawn mower pattern).
    
    If the input coordinates are in WGS84 (longitude, latitude), they will be automatically
    converted to UTM coordinates for processing, and the result will be converted back to WGS84.

    Args:
        corner1 (Tuple[float, float]): First corner coordinates as (x, y) in UTM
        corner2 (Tuple[float, float]): Second corner coordinates as (x, y) in UTM
        band_distance (float): Maximum distance between parallel bands in meters
        angle (float, optional): Angle in degrees for lawn mowing direction. 0 is South->North, 90 is East->West. Defaults to 0.0.

    Returns:
        List[Tuple[float, float]]: A list of coordinate tuples in the same format as the input (UTM )

    Example:
        >>> utm_corner1 = (500000, 4000000)  # (easting, northing) in UTM
        >>> utm_corner2 = (500100, 4000100)  # (easting, northing) in UTM
        >>> utm_coordinates = create_lawn_mower_band_strips(utm_corner1, utm_corner2, 10.0)
    """

    # Extract coordinates (now in UTM)
    x1, y1 = corner1
    x2, y2 = corner2

    # Ensure x1 <= x2 and y1 <= y2
    x_min, x_max = min(x1, x2), max(x1, x2)
    y_min, y_max = min(y1, y2), max(y1, y2)

    # For standard angles (0, 90, 180), use the optimized approach
    # For angled lawn mowing, use the new approach
    return _create_lawn_mower_band_strips_utm(x_min, x_max, y_min, y_max, band_distance, angle)


def find_horizontal_intersect(
        point: Tuple[float, float],
        vector: Tuple[float, float],
        y: float
) -> float | None:
    if vector[1] == 0:
        return None
    eps = 1e-10
    if abs(point[1] - y) < eps:
        return point[0]
    return point[0] + (y - point[1]) * vector[0] / vector[1]


def find_vertical_intersect(
        point: Tuple[float, float],
        vector: Tuple[float, float],
        y: float
) -> float | None:
    return find_horizontal_intersect((point[1], point[0]), (vector[1], vector[0]), y)


def find_line_rectangle_intersections(
        rectangle_corners: Tuple[Tuple[float, float], Tuple[float, float]],
        point: Tuple[float, float],
        vector: Tuple[float, float]
) -> List[Tuple[float, float]]:
    """
    Find the intersection points between a line and a rectangle.
    If the line aligned with an edge, we consider it doe not intersect
    
    Args:
        rectangle_corners: A tuple of two corner points (x_min, y_min), (x_max, y_max) defining the rectangle
        point: The starting point (x, y) of the line
        vector: The direction vector (dx, dy) of the line
        
    Returns:
        List[Tuple[float, float]]: 0, 1, or 2 unique positions where the line intersects the rectangle
    """
    # Extract rectangle coordinates
    (x_min, y_min), (x_max, y_max) = rectangle_corners

    # Extract line parameters
    px, py = point
    dx, dy = vector

    if dy == 0 and (py == y_max or py == y_min):
        return []
    if dx == 0 and (px == x_max or px == x_min):
        return []

    intersects = []

    # find each intersection with sideline and keep them if they are within the rectangle
    x_y_min = find_horizontal_intersect(point, vector, y_min)
    if x_y_min is not None and x_min <= x_y_min <= x_max:
        intersects.append((x_y_min, y_min))

    x_y_max = find_horizontal_intersect(point, vector, y_max)
    if x_y_max is not None and x_min <= x_y_max <= x_max:
        intersects.append((x_y_max, y_max))

    y_x_min = find_vertical_intersect(point, vector, x_min)
    if y_x_min is not None and y_min < y_x_min < y_max:
        intersects.append((x_min, y_x_min))

    y_x_max = find_vertical_intersect(point, vector, x_max)
    if y_x_max is not None and y_min < y_x_max < y_max:
        intersects.append((x_max, y_x_max))
    return intersects


def distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def two_points_angle(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.atan2(dx, dy) / math.pi * 180


def _create_lawn_mower_band_strips_utm(
        x_min: float,
        x_max: float,
        y_min: float,
        y_max: float,
        band_distance: float,
        angle: float
) -> List[Tuple[Tuple[float, float], Tuple[float, float] | None]]:
    """
    Create a lawn mower pattern with bands at the specified angle using UTM coordinates.
    
    Args:
        x_min: Minimum x (easting) of the rectangle in UTM
        x_max: Maximum x (easting) of the rectangle in UTM
        y_min: Minimum y (northing) of the rectangle in UTM
        y_max: Maximum y (northing) of the rectangle in UTM
        band_distance: Maximum distance between bands in meters
        angle: Angle in degrees (0-180)
    Returns:
        List[Tuple[float, float]]: List of coordinate tuples in the same format as the input
    """

    # Define the rectangle corners in clockwise order (x, y) format
    corners = [
        (x_min, y_min),  # Bottom-left
        (x_max, y_min),  # Bottom-right
        (x_max, y_max),  # Top-right
        (x_min, y_max),  # Top-left
    ]

    utm_coordinates = []

    center_x = (x_min + x_max) / 2
    center_y = (y_min + y_max) / 2

    normalized_angle = (90 - angle) % 180
    line_angle_rad = math.radians(normalized_angle % 180)

    dx = math.cos(line_angle_rad)
    dy = math.sin(line_angle_rad)

    width_meters = x_max - x_min
    height_meters = y_max - y_min

    # Calculate the projection of the rectangle onto the direction perpendicular to the bands
    # This gives us the maximum distance we need to cover with bands
    projection_length = abs(width_meters * dx) + abs(height_meters * dy)

    # Calculate the number of bands needed
    num_bands = max(2, math.ceil(projection_length / band_distance) + 1)

    # Calculate the actual band distance in meters
    actual_band_distance = projection_length / (num_bands - 1) if num_bands > 1 else projection_length

    # Calculate the starting position for the first band
    # We start from the furthest point in the negative direction perpendicular to the bands
    start_offset = -projection_length / 2

    # Calculate the band direction vector (perpendicular to the line direction)
    band_dx = -dy
    band_dy = dx

    # Store all intersections to ensure we don't have duplicate waypoints
    all_strips = []

    for i in range(num_bands):
        # Calculate the offset for this band
        offset = start_offset + i * actual_band_distance
        p_x = center_x + offset * band_dx
        p_y = center_y + offset * band_dy

        intersects = find_line_rectangle_intersections(
            ((x_min, y_min), (x_max, y_max)),
            (p_x, p_y),
            (dx, dy)
        )

        if len(intersects) == 0:
            pass
        elif len(intersects) == 1:
            all_strips.append((intersects[0], None))
        elif len(intersects) == 2:
            print(
                f'angle={angle} {intersects} -> {two_points_angle(intersects[0], intersects[1])}, {(180 + angle) % 360}')
            if abs((two_points_angle(intersects[0], intersects[1]) % 360 - (180 + angle) % 360)) < 1:
                print("REVERSE")
                intersects = [intersects[1], intersects[0]]
            all_strips.append((intersects[0], intersects[1]))
        else:
            raise RuntimeError(f'intersections get more than two elements: {intersects} ')

    return all_strips


def reverse_strip(strip: Tuple[Tuple[float, float], Tuple[float, float] | None]) -> Tuple[Tuple[float, float], Tuple[float, float] | None]:
    if strip[1] is None:
        return strip
    return strip[1], strip[0]


def is_perpendicular_ahead_of_strip(
        point: Tuple[float, float],
        strip: Tuple[Tuple[float, float], Tuple[float, float]],
) -> bool:
    """
    We project point perpendicularly to strip (defined as a vector of two points).
    if the projection is ahead of the strip (it means on the line defined by vector strip, but further that point strip[1[, return True, else False.
    """
    # Extract the strip start and end points
    strip_start, strip_end = strip

    # Check if the point is exactly at the end of the strip
    if point[0] == strip_end[0] and point[1] == strip_end[1]:
        return False

    # Calculate the strip vector
    strip_vector = (strip_end[0] - strip_start[0], strip_end[1] - strip_start[1])

    # Calculate the vector from strip_start to the point
    point_vector = (point[0] - strip_start[0], point[1] - strip_start[1])

    # Calculate the length of the strip vector
    strip_length = math.sqrt(strip_vector[0] ** 2 + strip_vector[1] ** 2)

    # Normalize the strip vector
    if strip_length > 0:
        strip_unit_vector = (strip_vector[0] / strip_length, strip_vector[1] / strip_length)
    else:
        return False  # If strip has zero length, return False

    # Calculate the dot product to find the projection length
    projection_length = point_vector[0] * strip_unit_vector[0] + point_vector[1] * strip_unit_vector[1]

    # If projection length is greater than strip length, the projection is ahead of strip end
    return projection_length > strip_length


def get_projection_point_on_strip(
        point: Tuple[float, float],
        strip: Tuple[Tuple[float, float], Tuple[float, float]],
) -> Tuple[float, float]:
    """
    Computes the perpendicular projection of a point onto the line defined by the strip vector.
    
    Args:
        point: The point to project (x, y)
        strip: A tuple of two points defining the strip line ((x1, y1), (x2, y2))
        
    Returns:
        The coordinates of the projection point (x, y)
    """
    # Extract the strip start and end points
    strip_start, strip_end = strip

    # Calculate the strip vector
    strip_vector = (strip_end[0] - strip_start[0], strip_end[1] - strip_start[1])

    # Calculate the vector from strip_start to the point
    point_vector = (point[0] - strip_start[0], point[1] - strip_start[1])

    # Calculate the length of the strip vector
    strip_length_squared = strip_vector[0] ** 2 + strip_vector[1] ** 2

    # If strip has zero length, return the strip start point
    if strip_length_squared == 0:
        return strip_start

    # Calculate the dot product to find the projection scalar
    dot_product = (point_vector[0] * strip_vector[0] + point_vector[1] * strip_vector[1])

    # Calculate the projection scalar (t)
    t = dot_product / strip_length_squared

    # Calculate the projection point coordinates
    projection_x = strip_start[0] + t * strip_vector[0]
    projection_y = strip_start[1] + t * strip_vector[1]

    return projection_x, projection_y

