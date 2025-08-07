class WaypointCoordinate:
    """
    A class representing a geographic waypoint with latitude, longitude, and altitude.

    Attributes:
        lat (float): Latitude in degrees
        lon (float): Longitude in degrees
        altitude (float): Altitude in meters
    """

    def __init__(self, lat, lon, altitude=0.0):
        """
        Initialize a WaypointCoordinate.

        Args:
            lat (float): Latitude in degrees
            lon (float): Longitude in degrees
            altitude (float, optional): Altitude in meters. Defaults to 0.0.
        """
        self.lat = float(lat)
        self.lon = float(lon)
        self.altitude = float(altitude)

    def __repr__(self):
        """Return string representation of the waypoint."""
        return f"WaypointCoordinate(lat={self.lat}, lon={self.lon}, altitude={self.altitude})"

    def __eq__(self, other):
        """Check if two waypoints are equal."""
        if not isinstance(other, WaypointCoordinate):
            return False
        return (self.lat == other.lat and
                self.lon == other.lon and
                self.altitude == other.altitude)
