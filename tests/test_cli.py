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
from bok_ucgs_fish_route.coordinates.conversion import convert_corners_if_wgs84


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
    
    def test_wgs84_coordinate_conversion(self, cli_runner, tmp_path):
        """Test that WGS84 coordinates are correctly detected and converted to UTM."""
        # Create a temporary output file
        output_path = os.path.join(tmp_path, "test_wgs84_conversion.png")
        
        # WGS84 coordinates
        lon1, lat1 = 23.134, 37.428  # Within WGS84 range
        lon2, lat2 = 23.136, 37.430  # Within WGS84 range
        speed = 2.5
        
        # Mock the convert_corners_if_wgs84 function to verify it's called
        with patch('cli.convert_corners_if_wgs84') as mock_convert:
            # Simulate conversion by returning UTM-like coordinates
            utm_corner1 = (500000, 5000000)
            utm_corner2 = (501000, 5001000)
            mock_convert.return_value = (utm_corner1, utm_corner2, True)
            
            # Mock the create_route_segment_perimeter function
            with patch('cli.create_route_segment_perimeter') as mock_create:
                coordinates = [
                    utm_corner1,
                    (utm_corner2[0], utm_corner1[1]),
                    utm_corner2,
                    (utm_corner1[0], utm_corner2[1]),
                    utm_corner1
                ]
                mock_create.return_value = coordinates
                
                # Mock create_route_segment_from_coordinates
                with patch('cli.create_route_segment_from_coordinates') as mock_create_from_coords:
                    waypoints = [
                        WaypointCoordinate(lon=coord[0], lat=coord[1], altitude=0.0)
                        for coord in coordinates
                    ]
                    mock_create_from_coords.return_value = RouteSegment(waypoints, speed)
                    
                    # Mock export_route_segment_to_png
                    with patch('cli.export_route_segment_to_png') as mock_export:
                        mock_export.return_value = output_path
                        
                        # Run the CLI command
                        args = [
                            "generate-perimeter-map",
                            str(lon1), str(lat1), str(lon2), str(lat2), str(speed),
                            "--output", output_path
                        ]
                        result = cli_runner.invoke(args=args)
                        
                        # Check the result
                        assert result.exit_code == 0
                        assert f"Map generated and saved to: {output_path}" in result.output
                        
                        # Verify that convert_corners_if_wgs84 was called with the correct arguments
                        mock_convert.assert_called_once_with((lon1, lat1), (lon2, lat2))
                        
                        # Verify that create_route_segment_perimeter was called with the converted coordinates
                        mock_create.assert_called_once_with(utm_corner1, utm_corner2)

    @pytest.mark.parametrize(
        "lat1, lon1, lat2, lon2, speed, utm, epsg, expected_success",
        [
            # WGS84 coordinates (no UTM specified)
            (37.428, 23.134, 37.430, 23.136, 2.5, None, 3857, True),  # Valid parameters
            (37.428, 23.134, 37.428, 23.134, 2.5, None, 3857, True),  # Same point (still valid)
            (37.428, 23.134, 37.430, 23.136, 0, None, 3857, False),   # Invalid speed (0)
            (37.428, 23.134, 37.430, 23.136, -1, None, 3857, False),  # Invalid speed (negative)
            
            # UTM coordinates (with UTM zone specified)
            (4000000, 500000, 4000100, 500100, 2.5, "34N", 3857, True),  # Valid UTM parameters
            (4000000, 500000, 4000000, 500000, 2.5, "34N", 3857, True),  # Same point (still valid)
            (4000000, 500000, 4000100, 500100, 0, "34N", 3857, False),   # Invalid speed (0)
            (4000000, 500000, 4000100, 500100, -1, "34N", 3857, False),  # Invalid speed (negative)
        ]
    )
    def test_generate_perimeter_map_cli(self, cli_runner, lat1, lon1, lat2, lon2, speed, utm, epsg, expected_success, tmp_path):
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
                    str(lon1), str(lat1), str(lon2), str(lat2), str(speed),
                    "--epsg", str(epsg),
                    "--output", output_path
                ]
                
                # Add UTM parameter if specified
                if utm:
                    args.extend(["--utm", utm])
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
    
    def test_wgs84_coordinate_conversion(self, cli_runner, tmp_path):
        """Test that WGS84 coordinates are correctly detected and converted to UTM for lawn mowing."""
        # Create a temporary output file
        output_path = os.path.join(tmp_path, "test_lawn_mower_wgs84_conversion.png")
        
        # WGS84 coordinates
        lon1, lat1 = 23.134, 37.428  # Within WGS84 range
        lon2, lat2 = 23.136, 37.430  # Within WGS84 range
        speed = 2.5
        band_distance = 10.0
        angle = 45.0
        
        # Mock the convert_corners_if_wgs84 function to verify it's called
        with patch('cli.convert_corners_if_wgs84') as mock_convert:
            # Simulate conversion by returning UTM-like coordinates
            utm_corner1 = (500000, 5000000)
            utm_corner2 = (501000, 5001000)
            mock_convert.return_value = (utm_corner1, utm_corner2, True)
            
            # Mock the create_route_segment_lawn_mower function
            with patch('cli.create_route_segment_lawn_mower') as mock_create:
                coordinates = [
                    utm_corner1,
                    (utm_corner2[0], utm_corner1[1]),
                    utm_corner2,
                    (utm_corner1[0], utm_corner2[1]),
                    utm_corner1
                ]
                mock_create.return_value = coordinates
                
                # Mock create_route_segment_from_coordinates
                with patch('cli.create_route_segment_from_coordinates') as mock_create_from_coords:
                    waypoints = [
                        WaypointCoordinate(lon=coord[0], lat=coord[1], altitude=0.0)
                        for coord in coordinates
                    ]
                    mock_create_from_coords.return_value = RouteSegment(waypoints, speed)
                    
                    # Mock export_route_segment_to_png
                    with patch('cli.export_route_segment_to_png') as mock_export:
                        mock_export.return_value = output_path
                        
                        # Run the CLI command
                        args = [
                            "generate-lawn-mowing",
                            str(lon1), str(lat1), str(lon2), str(lat2), str(speed), str(band_distance),
                            "--angle", str(angle),
                            "--output", output_path
                        ]
                        result = cli_runner.invoke(args=args)
                        
                        # Check the result
                        assert result.exit_code == 0
                        assert f"Map generated and saved to: {output_path}" in result.output
                        
                        # Verify that convert_corners_if_wgs84 was called with the correct arguments
                        mock_convert.assert_called_once_with((lon1, lat1), (lon2, lat2))
                        
                        # Verify that create_route_segment_lawn_mower was called with the converted coordinates
                        mock_create.assert_called_once()

    @pytest.mark.parametrize(
        "lat1, lon1, lat2, lon2, speed, band_distance, utm, epsg, expected_success",
        [
            # WGS84 coordinates (no UTM specified)
            (37.428, 23.134, 37.430, 23.136, 2.5, 10.0, None, 3857, True),  # Valid parameters
            (37.428, 23.134, 37.428, 23.134, 2.5, 10.0, None, 3857, True),  # Same point (still valid)
            (37.428, 23.134, 37.430, 23.136, 0, 10.0, None, 3857, False),   # Invalid speed (0)
            (37.428, 23.134, 37.430, 23.136, -1, 10.0, None, 3857, False),  # Invalid speed (negative)
            (37.428, 23.134, 37.430, 23.136, 2.5, 0, None, 3857, False),    # Invalid band distance (0)
            (37.428, 23.134, 37.430, 23.136, 2.5, -1, None, 3857, False),   # Invalid band distance (negative)
            
            # UTM coordinates (with UTM zone specified)
            (4000000, 500000, 4000100, 500100, 2.5, 10.0, "34N", 3857, True),  # Valid UTM parameters
            (4000000, 500000, 4000000, 500000, 2.5, 10.0, "34N", 3857, True),  # Same point (still valid)
            (4000000, 500000, 4000100, 500100, 0, 10.0, "34N", 3857, False),   # Invalid speed (0)
            (4000000, 500000, 4000100, 500100, -1, 10.0, "34N", 3857, False),  # Invalid speed (negative)
            (4000000, 500000, 4000100, 500100, 2.5, 0, "34N", 3857, False),    # Invalid band distance (0)
            (4000000, 500000, 4000100, 500100, 2.5, -1, "34N", 3857, False),   # Invalid band distance (negative)
        ]
    )
    def test_generate_lawn_mowing_cli(self, cli_runner, lat1, lon1, lat2, lon2, speed, band_distance, utm, epsg, expected_success, tmp_path):
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
                    str(lon1), str(lat1), str(lon2), str(lat2), str(speed), str(band_distance),
                    "--epsg", str(epsg),
                    "--output", output_path
                ]
                
                # Add UTM parameter if specified
                if utm:
                    args.extend(["--utm", utm])
                result = cli_runner.invoke(args=args)
                
                # Check the result
                if expected_success:
                    assert result.exit_code == 0
                    assert f"Map generated and saved to: {output_path}" in result.output
                    mock_export.assert_called_once()
                else:
                    assert result.exit_code != 0 or "Error generating map" in result.output


