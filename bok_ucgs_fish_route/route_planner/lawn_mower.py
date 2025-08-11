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


def extend_strips_perpendicular_ending(
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
        if i % 2 == 0:
            if is_perpendicular_ahead_of_strip(end_point_1, strip_2):
                ret_strips[i + 1] = (strip_2[0], get_projection_point_on_strip(end_point_1, strip_2))
            elif is_perpendicular_ahead_of_strip(end_point_2, strip_1):
                ret_strips[i] = (strip_1[0], get_projection_point_on_strip(end_point_2, strip_1))
        else:
            rev_strip_1 = reverse_strip(strip_1)
            rev_strip_2 = reverse_strip(strip_2)
            if is_perpendicular_ahead_of_strip(start_point_1, rev_strip_2):
                ret_strips[i + 1] = (get_projection_point_on_strip(start_point_1, rev_strip_2), strip_2[1])
            elif is_perpendicular_ahead_of_strip(start_point_2, rev_strip_1):
                ret_strips[i] = (get_projection_point_on_strip(start_point_2, rev_strip_1), strip_1[1])

    return ret_strips


def rearrange_index_shortest_path(n: int, lag: int) -> list[int]:
    """
    Return a list of index passing through all points 0 to n-1, with making jumps shorter than lag.
    We have the right to add points.

    Strategy: Eva's style: go back an forth.
    :param n: number of points
    :param lag: minimum jumping distance
    :return: reordered list of points numbers

    Example:
    n = 14
    lag = 3
    0, 3, 6, 9, 12, (+)16, 13, 10, 7, 4, 1, (+)-2, 2, 5, 8, 11

    """
    p = 0
    ret = []
    for i_pass in range(lag):
        shift = lag if i_pass % 2 == 0 else -lag
        while 0 <= p < n:
            ret.append(p)
            p += shift
        if i_pass < lag - 1:
            if shift > 0:
                p += 1
                ret.append(p)
                p -= lag
                if p > (n - 1):
                    p -= lag
            else:
                ret.append(p)
                p += lag + 1

    return ret


def reorder_strips_turning_radius(
        strips: List[Tuple[Tuple[float, float], Tuple[float, float] | None]],
        turning_radius: float
) -> list[Tuple[Tuple[float, float], Tuple[float, float] | None]]:
    if len(strips) <= 1:
        return strips
    print(f'signed distance between strips: {signed_distance_strips(strips[0], strips[1])}')
    if signed_distance_strips(strips[0], strips[1]) < 0:
        strips = strips[::-1]
    band_real_width = distance_strips(strips[0], strips[1])
    if turning_radius * 2 < band_real_width:
        return strips

    strip_lag = math.ceil(turning_radius * 2 / band_real_width)
    nb_strips = len(strips)

    last_strip = strips[-1]
    first_strip = strips[0]
    reorder_indexes = rearrange_index_shortest_path(n=nb_strips, lag=strip_lag)
    ret_strips = []
    print(f'nb_strip {nb_strips}, strip_lag={strip_lag} => reorder indexes={reorder_indexes}')
    for i in reorder_indexes:
        if 0 <= i < nb_strips:
            ret_strips.append(strips[i])
            continue
        if i < 0:
            ret_strips.append(create_parallel_strip(first_strip, i * band_real_width))
        else:
            ret_strips.append(create_parallel_strip(last_strip, (i - nb_strips + 1) * band_real_width))
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
            if abs((two_points_angle(intersects[0], intersects[1]) % 360 - (180 + angle) % 360)) < 1:
                intersects = [intersects[1], intersects[0]]
            all_strips.append((intersects[0], intersects[1]))
        else:
            raise RuntimeError(f'intersections get more than two elements: {intersects} ')

    return all_strips


def reverse_strip(strip: Tuple[Tuple[float, float], Tuple[float, float] | None]) -> Tuple[Tuple[float, float], Tuple[float, float] | None]:
    if strip[1] is None:
        return strip
    return strip[1], strip[0]


def create_parallel_strip(
        strip: Tuple[Tuple[float, float], Tuple[float, float] | None],
        distance: float
) -> Tuple[Tuple[float, float], Tuple[float, float] | None]:
    """
    Create a paralell strip to the given one at the passed distance.
    * If distance is a positive number, the strip is moved to the right.
    * If distance is a negative number, the strip is moved to the left.
    * If the strip is a point, the strip is moved horizontally by the distance, right if distance positive, left if distance negative.
    :param strip: A tuple of two points defining the strip ((x1, y1), (x2, y2)) or ((x1, y1), None)
    :param distance: The distance to move the strip (positive for right, negative for left)
    :return: A new strip parallel to the original one at the specified distance
    """
    # Extract the strip points
    p1, p2 = strip

    # Case 1: If the strip is a point (p2 is None)
    if p2 is None:
        # Move the point horizontally by the distance
        return (p1[0] + distance, p1[1]), None

    # Case 2: If the strip is a line (both p1 and p2 are points)
    # Calculate the strip vector
    vector = (p2[0] - p1[0], p2[1] - p1[1])

    # Calculate the length of the vector
    vector_length = math.sqrt(vector[0] ** 2 + vector[1] ** 2)

    # If the vector has zero length, treat it as a point
    if vector_length == 0:
        return (p1[0] + distance, p1[1]), None

    # Special case for horizontal lines (moving up/down)
    if abs(vector[1]) < 1e-10:  # y component is approximately zero
        # For horizontal lines, positive distance moves up, negative moves down
        new_p1 = (p1[0], p1[1] + distance)
        new_p2 = (p2[0], p2[1] + distance)
        return new_p1, new_p2

    # Calculate the unit normal vector (perpendicular to the strip)
    # For a vector (x, y), the perpendicular vector to the right is (y, -x) normalized
    # This ensures "right" is consistent with the coordinate system
    normal_vector = (vector[1] / vector_length, -vector[0] / vector_length)

    # Scale the normal vector by the distance
    offset_vector = (normal_vector[0] * distance, normal_vector[1] * distance)

    # Create the new strip by offsetting both points
    new_p1 = (p1[0] + offset_vector[0], p1[1] + offset_vector[1])
    new_p2 = (p2[0] + offset_vector[0], p2[1] + offset_vector[1])

    return new_p1, new_p2


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


def signed_distance_strips(
        strip1: Tuple[Tuple[float, float], Tuple[float, float] | None],
        strip2: Tuple[Tuple[float, float], Tuple[float, float] | None]
) -> float:
    """
    Compute the signed distance between two strips. A strip can be either a vector of two points or a point and None.
    We assume that if both strips are vectors (two points each), they are parallel.
    
    The distance is negative if the second strip is on the left of the first one, positive if it is on the right.
    If the two strips are points, the distance is always positive.
    
    This function handles four cases:
    1. Two parallel lines: Returns the signed perpendicular distance between them
    2. A point and a line: Returns the signed perpendicular distance from the point to the line
    3. A line and a point: Returns the signed perpendicular distance from the point to the line
    4. Two points: Returns the positive Euclidean distance between the points
    
    Args:
        strip1: First strip ((x1, y1), (x2, y2)) or ((x1, y1), None)
        strip2: Second strip ((x1, y1), (x2, y2)) or ((x1, y1), None)
        
    Returns:
        The signed distance between the strips
    """
    # Case 1: Both strips are points (one point each)
    if strip1[1] is None and strip2[1] is None:
        # For two points, always return positive distance
        return distance(strip1[0], strip2[0])

    # Case 2: First strip is a point, second is a line
    if strip1[1] is None:
        point = strip1[0]
        line = strip2
        # Project the point onto the line
        projection = get_projection_point_on_strip(point, line)
        # Calculate the distance between the point and its projection
        dist = distance(point, projection)

        # Determine if the point is on the left or right of the line
        line_vector = (line[1][0] - line[0][0], line[1][1] - line[0][1])
        point_vector = (point[0] - line[0][0], point[1] - line[0][1])

        # Cross product to determine left/right
        cross_product = line_vector[0] * point_vector[1] - line_vector[1] * point_vector[0]

        # If cross product is negative, point is on the right of the line
        return dist if cross_product > 0 else -dist

    # Case 3: First strip is a line, second is a point
    if strip2[1] is None:
        return - signed_distance_strips(strip2, strip1)

    # Case 4: Both strips are lines (assumed to be parallel)
    # Take a point from the first line
    point = strip1[0]
    # Project it onto the second line
    projection = get_projection_point_on_strip(point, strip2)
    # Calculate the distance between the point and its projection
    dist = distance(point, projection)

    # Determine if the second line is on the left or right of the first line
    # We use the normal vector of the first line to determine this
    line1_vector = (strip1[1][0] - strip1[0][0], strip1[1][1] - strip1[0][1])
    line1_length = math.sqrt(line1_vector[0] ** 2 + line1_vector[1] ** 2)

    # Calculate the normal vector (perpendicular to the right)
    normal_vector = (line1_vector[1] / line1_length, -line1_vector[0] / line1_length)

    # Vector from point on first line to its projection on second line
    projection_vector = (projection[0] - point[0], projection[1] - point[1])

    # Dot product to determine if projection is in the direction of the normal vector
    dot_product = normal_vector[0] * projection_vector[0] + normal_vector[1] * projection_vector[1]

    # If dot product is positive, second line is on the right of the first line
    return -dist if dot_product < 0 else dist


def distance_strips(
        strip1: Tuple[Tuple[float, float], Tuple[float, float] | None],
        strip2: Tuple[Tuple[float, float], Tuple[float, float] | None]
) -> float:
    """
    Compute the absolute distance between two strips. A strip can be either a vector of two points or a point and None.
    We assume that if both strips are vectors (two points each), they are parallel.
    
    This function handles four cases:
    1. Two parallel lines: Returns the perpendicular distance between them
    2. A point and a line: Returns the perpendicular distance from the point to the line
    3. A line and a point: Returns the perpendicular distance from the point to the line
    4. Two points: Returns the Euclidean distance between the points
    
    Args:
        strip1: First strip ((x1, y1), (x2, y2)) or ((x1, y1), None)
        strip2: Second strip ((x1, y1), (x2, y2)) or ((x1, y1), None)
        
    Returns:
        The absolute distance between the strips
    """
    return abs(signed_distance_strips(strip1, strip2))
