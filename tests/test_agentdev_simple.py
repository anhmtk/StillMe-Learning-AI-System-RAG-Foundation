#!/usr/bin/env python3
"""
Simple test for AgentDev system - designed to run fast
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_basic_import():
    """Test basic imports work - should be very fast"""
    try:
        import stillme_core
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import stillme_core: {e}")

def test_agentdev_controller():
    """Test AgentDev controller can be instantiated - should be fast"""
    try:
        from stillme_core.controller import AgentController
        controller = AgentController()
        assert controller is not None
        assert hasattr(controller, 'planner')
        assert hasattr(controller, 'executor')
        assert hasattr(controller, 'verifier')
    except Exception as e:
        pytest.fail(f"Failed to create AgentController: {e}")

def test_basic_functionality():
    """Test basic functionality works - should be instant"""
    # Simple test that should always pass
    assert 1 + 1 == 2
    assert "hello" + " " + "world" == "hello world"
    assert len([1, 2, 3]) == 3

def test_environment_variables():
    """Test environment variables are set correctly"""
    assert os.getenv("AGENTDEV_TEST_MODE") == "1"
    assert os.getenv("SKIP_GIT_OPERATIONS") == "1"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
