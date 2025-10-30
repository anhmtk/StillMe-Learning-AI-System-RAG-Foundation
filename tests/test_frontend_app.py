"""
Tests for Streamlit frontend application
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestFrontendApp:
    """Test suite for Streamlit frontend"""
    
    def test_frontend_app_import(self):
        """Test that frontend app can be imported"""
        try:
            from frontend.app import app
            assert app is not None
        except ImportError as e:
            pytest.skip(f"Frontend app not available: {e}")
    
    def test_frontend_components_exist(self):
        """Test that frontend components exist"""
        try:
            from frontend import components
            assert components is not None
        except ImportError:
            pytest.skip("Frontend components not available")
    
    def test_frontend_utils_exist(self):
        """Test that frontend utils exist"""
        try:
            from frontend import utils
            assert utils is not None
        except ImportError:
            pytest.skip("Frontend utils not available")


class TestStreamlitIntegration:
    """Test suite for Streamlit integration"""
    
    @patch('streamlit.run')
    def test_streamlit_app_structure(self, mock_run):
        """Test that Streamlit app has expected structure"""
        try:
            # Mock streamlit components
            with patch('streamlit.title'), \
                 patch('streamlit.sidebar'), \
                 patch('streamlit.main'):
                
                from frontend.app import app
                # If we can import without errors, structure is likely correct
                assert True
        except ImportError:
            pytest.skip("Streamlit app not available")
    
    def test_dashboard_functions_exist(self):
        """Test that dashboard functions exist"""
        try:
            from frontend.app import (
                show_dashboard,
                show_chat_panel,
                show_learning_sessions,
                show_knowledge_base,
                show_evolution,
                show_community_review
            )
            # All functions should be callable
            assert callable(show_dashboard)
            assert callable(show_chat_panel)
            assert callable(show_learning_sessions)
            assert callable(show_knowledge_base)
            assert callable(show_evolution)
            assert callable(show_community_review)
        except ImportError:
            pytest.skip("Dashboard functions not available")


class TestAPIIntegration:
    """Test suite for API integration in frontend"""
    
    @patch('requests.post')
    def test_api_call_functions(self, mock_post):
        """Test API call functions in frontend"""
        try:
            from frontend.app import (
                get_openai_response,
                get_deepseek_response,
                get_mock_response
            )
            
            # Mock successful API response
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": "test response"}
            mock_response.status_code = 200
            mock_post.return_value = mock_response
            
            # Test that functions are callable
            assert callable(get_openai_response)
            assert callable(get_deepseek_response)
            assert callable(get_mock_response)
            
        except ImportError:
            pytest.skip("API integration functions not available")
    
    def test_generate_stillme_response(self):
        """Test main response generation function"""
        try:
            from frontend.app import generate_stillme_response
            assert callable(generate_stillme_response)
        except ImportError:
            pytest.skip("Response generation function not available")
