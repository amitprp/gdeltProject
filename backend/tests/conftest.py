import pytest
import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

# Configure pytest
def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "unit: mark test as unit test")

@pytest.fixture
def client():
    return TestClient(app)
