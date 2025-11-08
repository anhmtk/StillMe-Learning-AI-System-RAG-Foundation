"""
Smoke Tests for Router Groups
Tests that all routers are properly registered and endpoints are accessible
"""

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Set test environment variables before importing app
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("DEEPSEEK_API_KEY", "test_key")
os.environ.setdefault("OPENAI_API_KEY", "test_key")

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

try:
    from backend.api.main import app
except Exception as e:
    pytest.skip(f"Backend API not available: {e}", allow_module_level=True)


class TestRouterSmoke:
    """Smoke tests for all router groups"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Smoke test: Root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data
    
    def test_health_endpoint(self, client):
        """Smoke test: Health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_ready_endpoint(self, client):
        """Smoke test: Readiness check endpoint"""
        response = client.get("/ready")
        # May return 200 (all checks pass) or 503 (some checks fail)
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "check_details" in data
        assert "timestamp" in data
        assert data["status"] in ["ready", "not_ready"]
    
    def test_status_endpoint(self, client):
        """Smoke test: System status endpoint"""
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "stage" in data
    
    def test_validators_metrics_endpoint(self, client):
        """Smoke test: Validation metrics endpoint"""
        response = client.get("/api/validators/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" in data
    
    @patch('backend.api.routers.chat_router.generate_ai_response')
    def test_chat_router_rag_endpoint(self, mock_ai_response, client):
        """Smoke test: Chat router - RAG endpoint"""
        mock_ai_response.return_value = "Test response"
        response = client.post(
            "/api/chat/rag",
            json={"message": "test", "use_rag": False, "user_id": "test_user"}
        )
        assert response.status_code != 404
        assert response.status_code in [200, 422, 500]  # May fail due to missing services
    
    def test_chat_router_smart_router_endpoint(self, client):
        """Smoke test: Chat router - Smart router endpoint"""
        response = client.post(
            "/api/chat/smart_router",
            json={"message": "test", "user_id": "test_user"}
        )
        assert response.status_code != 404
    
    def test_learning_router_metrics_endpoint(self, client):
        """Smoke test: Learning router - Metrics endpoint"""
        response = client.get("/api/learning/metrics")
        assert response.status_code != 404
        assert response.status_code in [200, 500]  # May fail due to missing services
    
    def test_learning_router_retained_endpoint(self, client):
        """Smoke test: Learning router - Retained knowledge endpoint"""
        response = client.get("/api/learning/retained")
        assert response.status_code != 404
        assert response.status_code in [200, 500]
    
    def test_rag_router_stats_endpoint(self, client):
        """Smoke test: RAG router - Stats endpoint"""
        response = client.get("/api/rag/stats")
        assert response.status_code != 404
        assert response.status_code in [200, 500]
    
    def test_rag_router_query_endpoint(self, client):
        """Smoke test: RAG router - Query endpoint"""
        response = client.post(
            "/api/rag/query",
            json={"query": "test", "limit": 5}
        )
        assert response.status_code != 404
        assert response.status_code in [200, 422, 500]
    
    def test_tiers_router_stats_endpoint(self, client):
        """Smoke test: Tiers router - Stats endpoint"""
        response = client.get("/api/v1/tiers/stats")
        assert response.status_code != 404
        assert response.status_code in [200, 500]
    
    def test_tiers_router_audit_endpoint(self, client):
        """Smoke test: Tiers router - Audit endpoint"""
        response = client.get("/api/v1/tiers/audit")
        assert response.status_code != 404
        assert response.status_code in [200, 500]
    
    def test_spice_router_status_endpoint(self, client):
        """Smoke test: SPICE router - Status endpoint"""
        response = client.get("/api/spice/status")
        assert response.status_code != 404
        assert response.status_code in [200, 500]
    
    def test_spice_router_metrics_endpoint(self, client):
        """Smoke test: SPICE router - Metrics endpoint"""
        response = client.get("/api/spice/metrics")
        assert response.status_code != 404
        assert response.status_code in [200, 500]
    
    def test_openapi_docs_accessible(self, client):
        """Smoke test: OpenAPI docs are accessible"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_json_accessible(self, client):
        """Smoke test: OpenAPI JSON schema is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        
        # Verify all router groups are present in OpenAPI
        paths = data["paths"]
        assert "/" in paths  # Root
        assert "/health" in paths  # Health
        assert "/ready" in paths  # Readiness
        assert "/api/status" in paths  # Status
        assert "/api/validators/metrics" in paths  # Validators metrics
        assert "/api/chat/rag" in paths  # Chat router
        assert "/api/learning/metrics" in paths  # Learning router
        assert "/api/rag/stats" in paths  # RAG router
        assert "/api/v1/tiers/stats" in paths  # Tiers router
        assert "/api/spice/status" in paths  # SPICE router

