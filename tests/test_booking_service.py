"""Tests for booking service."""
import pytest
import requests
from conftest import base_url

@pytest.mark.skip(reason="Requires running service")
def test_health_check(base_url):
    """Test health check endpoint."""
    response = requests.get(f"{base_url}/health", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

@pytest.mark.skip(reason="Requires running service")
def test_get_queue_status(base_url):
    """Test getting queue status."""
    response = requests.get(f"{base_url}/queue/", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert "queue" in data

@pytest.mark.skip(reason="Requires running service")
def test_get_all_bookings(base_url):
    """Test getting all bookings."""
    response = requests.get(f"{base_url}/bookings/", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert "bookings" in data

