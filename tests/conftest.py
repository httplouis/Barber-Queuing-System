"""Pytest configuration and fixtures."""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.fixture
def base_url():
    """Base URL for API testing."""
    return "http://localhost:8000"

@pytest.fixture
def auth_url():
    """Authentication service URL."""
    return "http://localhost:8001"

@pytest.fixture
def test_client_data():
    """Sample client data for testing."""
    return {
        "username": "testuser",
        "password": "testpass123",
        "name": "Test User",
        "email": "test@example.com",
        "phone": "1234567890"
    }

