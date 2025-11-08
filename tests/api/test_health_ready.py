"""
Smoke tests for health and readiness endpoints.
These tests verify that /health (liveness) and /ready (readiness) endpoints work correctly.
"""
import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

client = TestClient(app)


def test_health_endpoint():
    """
    Test /health endpoint (liveness probe).
    This endpoint must ALWAYS return 200 OK, even during initialization.
    """
    response = client.get("/health")
    
    # Health endpoint must always return 200
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    # Verify response structure
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "service" in data
    assert "timestamp" in data


def test_ready_endpoint():
    """
    Test /ready endpoint (readiness probe).
    This endpoint may return 200 (ready) or 503 (not ready) depending on dependencies.
    """
    response = client.get("/ready")
    
    # Ready endpoint can return 200 (ready) or 503 (not ready)
    assert response.status_code in (200, 503), \
        f"Expected 200 or 503, got {response.status_code}: {response.text}"
    
    # Verify response structure
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "timestamp" in data
    
    # If ready (200), all checks should pass
    if response.status_code == 200:
        assert data["status"] == "ready"
        checks = data.get("checks", {})
        # At least one check should be present
        assert len(checks) > 0
    else:
        # If not ready (503), status should be "not_ready"
        assert data["status"] == "not_ready"
        assert "check_details" in data


def test_health_vs_ready():
    """
    Test that /health and /ready behave differently.
    /health should always be 200, /ready may be 503 during startup.
    """
    health_response = client.get("/health")
    ready_response = client.get("/ready")
    
    # Health must always be 200
    assert health_response.status_code == 200
    
    # Ready can be 200 or 503
    assert ready_response.status_code in (200, 503)
    
    # Health should be faster (no dependency checks)
    # This is a basic sanity check
    assert "healthy" in health_response.json()["status"]

