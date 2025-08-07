class WaypointCoordinate:
    """
    A class representing a geographic waypoint with longitude, latitude, and altitude.

    Attributes:
        lon (float): Longitude in degrees (x-coordinate)
        lat (float): Latitude in degrees (y-coordinate)
        altitude (float): Altitude in meters
    """

    def __init__(self, lon, lat, altitude=0.0):
        """
        Initialize a WaypointCoordinate.

        Args:
            lon (float): Longitude in degrees (x-coordinate)
            lat (float): Latitude in degrees (y-coordinate)
            altitude (float, optional): Altitude in meters. Defaults to 0.0.
        """
        self.lon = float(lon)
        self.lat = float(lat)
        self.altitude = float(altitude)

    def __repr__(self):
        """Return string representation of the waypoint."""
        return f"WaypointCoordinate(lon={self.lon}, lat={self.lat}, altitude={self.altitude})"

    def __eq__(self, other):
        """Check if two waypoints are equal."""
        if not isinstance(other, WaypointCoordinate):
            return False
        return (self.lon == other.lon and
                self.lat == other.lat and
                self.altitude == other.altitude)
