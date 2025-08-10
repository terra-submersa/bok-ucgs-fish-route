"""
Tests for the Flask CLI application.
"""
import os
import sys
from unittest.mock import patch

import pytest
from flask.testing import FlaskCliRunner

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cli import app
from bok_ucgs_fish_route.coordinates.waypoint import WaypointCoordinate
from bok_ucgs_fish_route.coordinates.route import RouteSegment


@pytest.fixture
def cli_runner():
    """Fixture to provide a CLI runner for testing Flask CLI commands."""
    return FlaskCliRunner(app)


@pytest.fixture
def client():
    """Fixture to provide a test client for the Flask app."""
    with app.test_client() as client:
        yield client

