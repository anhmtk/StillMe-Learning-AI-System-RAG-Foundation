"""
Pytest configuration and fixtures for StillMe tests
"""

import pytest
import os
import tempfile
from pathlib import Path


@pytest.fixture(scope="session")
def test_data_dir():
    """Create temporary directory for test data"""
    temp_dir = tempfile.mkdtemp(prefix="stillme_test_")
    yield Path(temp_dir)
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture(scope="session")
def test_env_vars():
    """Set up test environment variables"""
    test_vars = {
        "ENVIRONMENT": "test",
        "DEEPSEEK_API_KEY": "test_deepseek_key",
        "OPENAI_API_KEY": "test_openai_key",
        "LEARNING_INTERVAL_HOURS": "1",
        "MIN_VOTES": "5",
        "APPROVAL_THRESHOLD": "0.6",
        "COOLDOWN_HOURS": "0.5"
    }
    
    # Set environment variables
    for key, value in test_vars.items():
        os.environ[key] = value
    
    yield test_vars
    
    # Cleanup
    for key in test_vars:
        os.environ.pop(key, None)


@pytest.fixture
def mock_api_responses():
    """Mock API responses for testing"""
    return {
        "openai": {
            "choices": [{"message": {"content": "Mocked OpenAI response"}}]
        },
        "deepseek": {
            "choices": [{"message": {"content": "Mocked DeepSeek response"}}]
        }
    }


@pytest.fixture
def sample_knowledge_item():
    """Sample knowledge item for testing"""
    return {
        "id": "test_001",
        "title": "Test Knowledge Item",
        "content": "This is a test knowledge item for unit testing.",
        "source": "test_source",
        "trust_score": 0.8,
        "quality_score": 0.9,
        "timestamp": "2025-01-27T10:00:00Z",
        "tags": ["test", "unit_test"]
    }


@pytest.fixture
def sample_learning_session():
    """Sample learning session for testing"""
    return {
        "id": "session_001",
        "start_time": "2025-01-27T10:00:00Z",
        "end_time": "2025-01-27T10:30:00Z",
        "status": "completed",
        "knowledge_items_processed": 5,
        "quality_score": 0.85
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Add unit marker to tests in test_*.py files
        if "test_" in item.nodeid and "integration" not in item.nodeid:
            item.add_marker(pytest.mark.unit)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.nodeid for keyword in ["api", "network", "database"]):
            item.add_marker(pytest.mark.slow)
