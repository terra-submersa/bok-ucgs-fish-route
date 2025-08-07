"""
Tests for the Flask CLI application.
"""
import os
import tempfile
import pytest
from flask import Flask
from flask.testing import FlaskCliRunner
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli import app, generate_perimeter_map, generate_lawn_mowing
from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate
from bok_ucgs_fish_route.coordinates.route import RouteSegment, create_route_segment_from_coordinates


@pytest.fixture
def cli_runner():
    """Fixture to provide a CLI runner for testing Flask CLI commands."""
    return FlaskCliRunner(app)


@pytest.fixture
def client():
    """Fixture to provide a test client for the Flask app."""
    with app.test_client() as client:
        yield client


class TestGeneratePerimeterMap:
    """Tests for the generate-perimeter-map CLI command."""

    @pytest.mark.parametrize(
        "lat1, lon1, lat2, lon2, speed, epsg, expected_success",
        [
            (37.428, 23.134, 37.430, 23.136, 2.5, 3857, True),  # Valid parameters
            (37.428, 23.134, 37.428, 23.134, 2.5, 3857, True),  # Same point (still valid)
            (37.428, 23.134, 37.430, 23.136, 0, 3857, False),   # Invalid speed (0)
            (37.428, 23.134, 37.430, 23.136, -1, 3857, False),  # Invalid speed (negative)
        ]
    )
    def test_generate_perimeter_map_cli(self, cli_runner, lat1, lon1, lat2, lon2, speed, epsg, expected_success, tmp_path):
        """Test the generate-perimeter-map CLI command with various parameters."""
        # Create a temporary output file
        output_path = os.path.join(tmp_path, "test_map.png")
        
        # Mock the export_route_segment_to_png function to avoid actual file creation
        with patch('cli.export_route_segment_to_png') as mock_export:
            mock_export.return_value = output_path if expected_success else None
            
            # Mock the create_route_segment_perimeter function
            with patch('cli.create_route_segment_perimeter') as mock_create:
                # For valid speed, return a valid list of coordinates
                if speed > 0:
                    coordinates = [
                        (lon1, lat1),
                        (lon2, lat1),
                        (lon2, lat2),
                        (lon1, lat2),
                        (lon1, lat1)
                    ]
                    mock_create.return_value = coordinates
                else:
                    # For invalid speed, raise ValueError
                    mock_create.side_effect = ValueError("Speed must be positive")
                    
                # Also mock create_route_segment_from_coordinates
                with patch('cli.create_route_segment_from_coordinates') as mock_create_from_coords:
                    if speed > 0:
                        waypoints = [
                            WaypointCoordinate(lon=lon1, lat=lat1, altitude=0.0),
                            WaypointCoordinate(lon=lon2, lat=lat1, altitude=0.0),
                            WaypointCoordinate(lon=lon2, lat=lat2, altitude=0.0),
                            WaypointCoordinate(lon=lon1, lat=lat2, altitude=0.0),
                            WaypointCoordinate(lon=lon1, lat=lat1, altitude=0.0)
                        ]
                        mock_create_from_coords.return_value = RouteSegment(waypoints, speed)
                
                # Run the CLI command
                args = [
                    "generate-perimeter-map",
                    str(lat1), str(lon1), str(lat2), str(lon2), str(speed),
                    "--epsg", str(epsg),
                    "--output", output_path
                ]
                result = cli_runner.invoke(args=args)
                
                # Check the result
                if expected_success:
                    assert result.exit_code == 0
                    assert f"Map generated and saved to: {output_path}" in result.output
                    mock_export.assert_called_once()
                else:
                    assert result.exit_code != 0 or "Error generating map" in result.output


class TestGenerateLawnMowning:
    """Tests for the generate-lawn-mowing CLI command."""

    @pytest.mark.parametrize(
        "lat1, lon1, lat2, lon2, speed, band_distance, epsg, expected_success",
        [
            (37.428, 23.134, 37.430, 23.136, 2.5, 10.0, 3857, True),  # Valid parameters
            (37.428, 23.134, 37.428, 23.134, 2.5, 10.0, 3857, True),  # Same point (still valid)
            (37.428, 23.134, 37.430, 23.136, 0, 10.0, 3857, False),   # Invalid speed (0)
            (37.428, 23.134, 37.430, 23.136, -1, 10.0, 3857, False),  # Invalid speed (negative)
            (37.428, 23.134, 37.430, 23.136, 2.5, 0, 3857, False),    # Invalid band distance (0)
            (37.428, 23.134, 37.430, 23.136, 2.5, -1, 3857, False),   # Invalid band distance (negative)
        ]
    )
    def test_generate_lawn_mowing_cli(self, cli_runner, lat1, lon1, lat2, lon2, speed, band_distance, epsg, expected_success, tmp_path):
        """Test the generate-lawn-mowning CLI command with various parameters."""
        # Create a temporary output file
        output_path = os.path.join(tmp_path, "test_lawn_mower_map.png")
        
        # Mock the export_route_segment_to_png function to avoid actual file creation
        with patch('cli.export_route_segment_to_png') as mock_export:
            mock_export.return_value = output_path if expected_success else None
            
            # Mock the create_route_segment_lawn_mower function
            with patch('cli.create_route_segment_lawn_mower') as mock_create:
                # For valid parameters, return a valid list of coordinates
                if speed > 0 and band_distance > 0:
                    coordinates = [
                        (lon1, lat1),
                        (lon2, lat1),
                        (lon2, lat2),
                        (lon1, lat2),
                        (lon1, lat1)
                    ]
                    mock_create.return_value = coordinates
                else:
                    # For invalid parameters, raise ValueError
                    if speed <= 0:
                        mock_create.side_effect = ValueError("Speed must be positive")
                    else:
                        mock_create.side_effect = ValueError("Band distance must be positive")
                        
                # Also mock create_route_segment_from_coordinates
                with patch('cli.create_route_segment_from_coordinates') as mock_create_from_coords:
                    if speed > 0 and band_distance > 0:
                        waypoints = [
                            WaypointCoordinate(lon=lon1, lat=lat1, altitude=0.0),
                            WaypointCoordinate(lon=lon2, lat=lat1, altitude=0.0),
                            WaypointCoordinate(lon=lon2, lat=lat2, altitude=0.0),
                            WaypointCoordinate(lon=lon1, lat=lat2, altitude=0.0),
                            WaypointCoordinate(lon=lon1, lat=lat1, altitude=0.0)
                        ]
                        mock_create_from_coords.return_value = RouteSegment(waypoints, speed)
                
                # Run the CLI command
                args = [
                    "generate-lawn-mowing",
                    str(lat1), str(lon1), str(lat2), str(lon2), str(speed), str(band_distance),
                    "--epsg", str(epsg),
                    "--output", output_path
                ]
                result = cli_runner.invoke(args=args)
                
                # Check the result
                if expected_success:
                    assert result.exit_code == 0
                    assert f"Map generated and saved to: {output_path}" in result.output
                    mock_export.assert_called_once()
                else:
                    assert result.exit_code != 0 or "Error generating map" in result.output


