"""
Tests for the map_exporter module.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
import tempfile

from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate
from bok_ucgs_fish_route.coordinates.route import RouteSegment
from bok_ucgs_fish_route.exporter import export_route_segment_to_png


class TestMapExporter:
    """Tests for the map_exporter module."""

    @pytest.fixture
    def sample_route_segment(self):
        """Create a sample route segment for testing."""
        waypoints = [
            WaypointCoordinate(37.7749, -122.4194),  # San Francisco
            WaypointCoordinate(34.0522, -118.2437),  # Los Angeles
            WaypointCoordinate(32.7157, -117.1611),  # San Diego
        ]
        return RouteSegment(waypoints, 10.0)  # 10 m/s speed

    @pytest.fixture
    def single_point_route_segment(self):
        """Create a route segment with a single waypoint for testing."""
        waypoints = [WaypointCoordinate(37.7749, -122.4194)]  # San Francisco
        return RouteSegment(waypoints, 5.0)  # 5 m/s speed

    @pytest.mark.parametrize(
        "epsg_code", 
        [
            3857,  # Web Mercator
            4326,  # WGS84
        ]
    )
    @patch("bok_ucgs_fish_route.exporter.map_exporter.plt")
    @patch("bok_ucgs_fish_route.exporter.map_exporter.gpd")
    @patch("bok_ucgs_fish_route.exporter.map_exporter.ctx")
    def test_export_route_segment_to_png_mocked(
        self, mock_ctx, mock_gpd, mock_plt, sample_route_segment, epsg_code
    ):
        """Test export_route_segment_to_png with mocked dependencies."""
        # Setup mocks
        mock_gdf = MagicMock()
        mock_gpd.GeoDataFrame.return_value = mock_gdf
        mock_gdf.to_crs.return_value = mock_gdf
        mock_gdf.crs.to_string.return_value = f"EPSG:{epsg_code}"
        mock_gdf.boundary = mock_gdf
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Call the function with a temporary file
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp_file:
            output_path = tmp_file.name
            result = export_route_segment_to_png(
                sample_route_segment, epsg_code, output_path
            )
            
            # Assertions
            assert result == output_path
            mock_gpd.GeoDataFrame.assert_called()
            mock_gdf.to_crs.assert_called_with(epsg=epsg_code)
            mock_gdf.plot.assert_called()
            mock_ctx.add_basemap.assert_called()
            mock_plt.savefig.assert_called_with(
                output_path, dpi=100, bbox_inches='tight'
            )
            mock_plt.close.assert_called()

    @patch("bok_ucgs_fish_route.exporter.map_exporter.plt")
    @patch("bok_ucgs_fish_route.exporter.map_exporter.gpd")
    @patch("bok_ucgs_fish_route.exporter.map_exporter.ctx")
    def test_export_single_point_route_segment(
        self, mock_ctx, mock_gpd, mock_plt, single_point_route_segment
    ):
        """Test export_route_segment_to_png with a single point route segment."""
        # Setup mocks
        mock_gdf = MagicMock()
        mock_gpd.GeoDataFrame.return_value = mock_gdf
        mock_gdf.to_crs.return_value = mock_gdf
        mock_gdf.crs.to_string.return_value = "EPSG:3857"
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Call the function with a temporary file
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp_file:
            output_path = tmp_file.name
            result = export_route_segment_to_png(
                single_point_route_segment, 3857, output_path
            )
            
            # Assertions
            assert result == output_path
            mock_gpd.GeoDataFrame.assert_called()
            mock_gdf.to_crs.assert_called_with(epsg=3857)
            mock_gdf.plot.assert_called()
            mock_ctx.add_basemap.assert_called()
            mock_plt.savefig.assert_called_with(
                output_path, dpi=100, bbox_inches='tight'
            )
            mock_plt.close.assert_called()

    def test_export_route_segment_to_png_invalid_route(self):
        """Test export_route_segment_to_png with an invalid route segment."""
        # Create a route segment with no waypoints - this should raise a ValueError
        # in the RouteSegment constructor
        with pytest.raises(ValueError):
            RouteSegment([], 10.0)

    @patch("bok_ucgs_fish_route.exporter.map_exporter.os.path.exists")
    @patch("bok_ucgs_fish_route.exporter.map_exporter.os.makedirs")
    @patch("bok_ucgs_fish_route.exporter.map_exporter.plt")
    @patch("bok_ucgs_fish_route.exporter.map_exporter.gpd")
    @patch("bok_ucgs_fish_route.exporter.map_exporter.ctx")
    def test_export_creates_directory(
        self, mock_ctx, mock_gpd, mock_plt, mock_makedirs, mock_exists, 
        sample_route_segment
    ):
        """Test that export_route_segment_to_png creates the output directory if needed."""
        # Setup mocks
        mock_gdf = MagicMock()
        mock_gpd.GeoDataFrame.return_value = mock_gdf
        mock_gdf.to_crs.return_value = mock_gdf
        mock_gdf.crs.to_string.return_value = "EPSG:3857"
        mock_gdf.boundary = mock_gdf
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Mock os.path.exists to return False
        mock_exists.return_value = False
        
        # Call the function with a path that includes a directory
        output_path = "test_dir/test_output.png"
        export_route_segment_to_png(sample_route_segment, 3857, output_path)
        
        # Assertions
        mock_exists.assert_called_with("test_dir")
        mock_makedirs.assert_called_with("test_dir")
        
    @patch("bok_ucgs_fish_route.exporter.map_exporter.plt")
    @patch("bok_ucgs_fish_route.exporter.map_exporter.gpd")
    @patch("bok_ucgs_fish_route.exporter.map_exporter.ctx")
    def test_export_with_area_corners(
        self, mock_ctx, mock_gpd, mock_plt, sample_route_segment
    ):
        """Test export_route_segment_to_png with area_corners parameter."""
        # Setup mocks
        mock_gdf = MagicMock()
        mock_gpd.GeoDataFrame.return_value = mock_gdf
        mock_gdf.to_crs.return_value = mock_gdf
        mock_gdf.crs.to_string.return_value = "EPSG:3857"
        mock_gdf.boundary = mock_gdf
        
        mock_fig = MagicMock()
        mock_ax = MagicMock()
        mock_plt.subplots.return_value = (mock_fig, mock_ax)
        
        # Define area corners
        area_corners = ((37.7, -122.5), (37.8, -122.4))  # Example coordinates
        
        # Call the function with a temporary file and area_corners
        with tempfile.NamedTemporaryFile(suffix=".png") as tmp_file:
            output_path = tmp_file.name
            result = export_route_segment_to_png(
                sample_route_segment, 3857, output_path, area_corners=area_corners
            )
            
            # Assertions
            assert result == output_path
            # Verify that GeoDataFrame was called at least 3 times (route, waypoints, and border)
            assert mock_gpd.GeoDataFrame.call_count >= 3
            mock_gdf.to_crs.assert_called_with(epsg=3857)
            mock_gdf.plot.assert_called()
            mock_gdf.boundary.plot.assert_called()
            mock_ctx.add_basemap.assert_called()
            mock_plt.savefig.assert_called_with(
                output_path, dpi=100, bbox_inches='tight'
            )
            mock_plt.close.assert_called()