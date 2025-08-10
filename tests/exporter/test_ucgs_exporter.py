import json
import os
import tempfile
import unittest
from unittest.mock import patch, mock_open

from bok_ucgs_fish_route.coordinates.route import RouteSegment
from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate
from bok_ucgs_fish_route.exporter.ucgs_exporter import _route_segments_to_ucgs_route, export_ucgs_json


class TestUcgsExporter(unittest.TestCase):
    def setUp(self):
        # Create test waypoints
        self.waypoint1 = WaypointCoordinate(lon=10.0, lat=20.0, altitude=30.0)
        self.waypoint2 = WaypointCoordinate(lon=11.0, lat=21.0, altitude=31.0)
        self.waypoint3 = WaypointCoordinate(lon=12.0, lat=22.0, altitude=32.0)

        # Create test route segments
        self.segment1 = RouteSegment([self.waypoint1, self.waypoint2], speed=5.0)
        self.segment2 = RouteSegment([self.waypoint3], speed=7.0)

        # Mock JSON data
        self.mock_waypoint = {
            "type": "Waypoint",
            "actions": [],
            "point": {
                "latitude": None,
                "longitude": None,
                "altitude": None,
                "altitudeType": "AGL"
            },
            "parameters": {
                "avoidObstacles": True,
                "avoidTerrain": True,
                "speed": None,
                "wpTurnType": "STRAIGHT",
                "altitudeType": "AGL",
                "cornerRadius": None
            }
        }

        self.mock_route_structure = {
            "name": "Route 3",
            "segments": []
        }

        self.mock_route_wrapper = {
            "version": {
                "major": 5,
                "minor": 12
            },
            "route": None
        }

    @patch('bok_ucgs_fish_route.exporter.ucgs_exporter._load_from_json')
    def test_route_segments_to_ucgs_route(self, mock_load_from_json):
        # Configure the mock to return our test data
        # Use deepcopy to ensure a new object is returned each time
        import copy
        mock_load_from_json.side_effect = lambda filename: copy.deepcopy({
                                                                             'config/ucgs/route-structure.json': self.mock_route_structure,
                                                                             'config/ucgs/waypoint.json': self.mock_waypoint
                                                                         }[filename])

        # Call the function with our test segments
        result = _route_segments_to_ucgs_route([self.segment1, self.segment2])

        # Verify the result
        self.assertEqual(3, len(result["segments"]))

        # Check that all waypoints are present with correct values
        # Create sets of expected waypoints for easier comparison
        import math
        expected_waypoints = [
            {
                "latitude": math.radians(20.0),
                "longitude": math.radians(10.0),
                "altitude": 30.0,
                "speed": 5.0
            },
            {
                "latitude": math.radians(21.0),
                "longitude": math.radians(11.0),
                "altitude": 31.0,
                "speed": 5.0
            },
            {
                "latitude": math.radians(22.0),
                "longitude": math.radians(12.0),
                "altitude": 32.0,
                "speed": 7.0
            }
        ]

        # Print the result for debugging
        print("Result segments:", result)

        # Check that each expected waypoint is in the result
        for expected in expected_waypoints:
            found = False
            for waypoint in result["segments"]:
                print(f"Comparing expected {expected} with actual point: {waypoint['point']}, params: {waypoint['parameters']}")
                if (waypoint["point"]["latitude"] == expected["latitude"] and
                        waypoint["point"]["longitude"] == expected["longitude"] and
                        waypoint["point"]["altitude"] == expected["altitude"] and
                        waypoint["parameters"]["speed"] == expected["speed"]):
                    found = True
                    break
            self.assertTrue(found, f"Waypoint not found: {expected}")

    @patch('bok_ucgs_fish_route.exporter.ucgs_exporter._load_from_json')
    @patch('bok_ucgs_fish_route.exporter.ucgs_exporter._route_segments_to_ucgs_route')
    def test_export_ucgs_json(self, mock_route_segments_to_ucgs_route, mock_load_from_json):
        # Configure the mocks
        mock_load_from_json.return_value = self.mock_route_wrapper
        mock_route_segments_to_ucgs_route.return_value = self.mock_route_structure

        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            # Call the function with our test segment
            export_ucgs_json(self.segment1, temp_filename, epsg_code="4326")

            # Verify the file was created and contains the expected content
            with open(temp_filename, 'r') as f:
                result = json.load(f)

            # Check that the route was added to the wrapper
            self.assertEqual(result["route"], self.mock_route_structure)

            # Verify the mocks were called correctly
            mock_load_from_json.assert_called_once_with('config/ucgs/route-wrapper.json')
            mock_route_segments_to_ucgs_route.assert_called_once_with(self.segment1, "4326")
        finally:
            # Clean up the temporary file
            os.unlink(temp_filename)


if __name__ == '__main__':
    unittest.main()
