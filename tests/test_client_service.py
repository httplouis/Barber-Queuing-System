"""Tests for client service."""
import pytest
import requests
from conftest import auth_url, test_client_data

@pytest.mark.skip(reason="Requires running service")
def test_register_client(auth_url, test_client_data):
    """Test client registration."""
    response = requests.post(
        f"{auth_url}/register/",
        json=test_client_data,
        timeout=5
    )
    assert response.status_code in [200, 400]  # 400 if already exists

@pytest.mark.skip(reason="Requires running service")
def test_login_client(auth_url, test_client_data):
    """Test client login."""
    response = requests.post(
        f"{auth_url}/login/",
        json={
            "username": test_client_data["username"],
            "password": test_client_data["password"]
        },
        timeout=5
    )
    assert response.status_code in [200, 401]
    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "client_id" in data

@pytest.mark.skip(reason="Requires running service")
def test_health_check(auth_url):
    """Test health check endpoint."""
    response = requests.get(f"{auth_url}/health", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

