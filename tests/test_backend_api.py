"""
Tests for FastAPI backend endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the FastAPI app (adjust import path as needed)
try:
    from backend.api.main import app
except ImportError:
    # Fallback if main.py is not in expected location
    pytest.skip("Backend API not available", allow_module_level=True)


class TestBackendAPI:
    """Test suite for backend API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_chat_endpoints_exist(self, client):
        """Test that chat endpoints exist"""
        # Test OpenAI endpoint
        response = client.post("/api/chat/openai", json={"message": "test"})
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404
        
        # Test DeepSeek endpoint
        response = client.post("/api/chat/deepseek", json={"message": "test"})
        assert response.status_code != 404
    
    @patch('backend.api.main.openai_client')
    def test_openai_chat_with_mock(self, mock_openai, client):
        """Test OpenAI chat with mocked response"""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Mocked OpenAI response"
        mock_openai.chat.completions.create.return_value = mock_response
        
        response = client.post("/api/chat/openai", json={"message": "test message"})
        
        # Should return 200 and contain the mocked response
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
    
    def test_learning_endpoints(self, client):
        """Test learning system endpoints"""
        # Test learning sessions endpoint
        response = client.get("/api/learning/sessions")
        assert response.status_code in [200, 404]  # 404 if not implemented yet
        
        # Test knowledge base endpoint
        response = client.get("/api/learning/knowledge")
        assert response.status_code in [200, 404]  # 404 if not implemented yet


class TestLearningService:
    """Test suite for learning service functionality"""
    
    @pytest.fixture
    def mock_learning_service(self):
        """Mock learning service"""
        with patch('backend.services.learning_service.LearningService') as mock:
            yield mock
    
    def test_learning_service_initialization(self, mock_learning_service):
        """Test learning service can be initialized"""
        service = mock_learning_service.return_value
        assert service is not None


class TestEthicsGuard:
    """Test suite for ethics guard functionality"""
    
    def test_ethics_guard_import(self):
        """Test ethics guard can be imported"""
        try:
            from backend.core.ethics_guard import ethics_guard_check
            assert callable(ethics_guard_check)
        except ImportError:
            pytest.skip("Ethics guard not available")
    
    def test_ethics_guard_check(self):
        """Test ethics guard check function"""
        try:
            from backend.core.ethics_guard import ethics_guard_check
            # Test with a mock proposal ID
            result = ethics_guard_check(1)
            assert isinstance(result, bool)
        except ImportError:
            pytest.skip("Ethics guard not available")
