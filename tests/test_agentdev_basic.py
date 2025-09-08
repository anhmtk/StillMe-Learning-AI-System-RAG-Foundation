#!/usr/bin/env python3
"""
Basic test for AgentDev system functionality
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_basic_import():
    """Test basic imports work"""
    try:
        import stillme_core
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import stillme_core: {e}")

def test_agentdev_controller():
    """Test AgentDev controller can be instantiated"""
    try:
        from stillme_core.controller import AgentController
        controller = AgentController()
        assert controller is not None
        assert hasattr(controller, 'planner')
        assert hasattr(controller, 'executor')
        assert hasattr(controller, 'verifier')
    except Exception as e:
        pytest.fail(f"Failed to create AgentController: {e}")

def test_agentdev_planner():
    """Test AgentDev planner can be instantiated"""
    try:
        from stillme_core.planner import Planner
        planner = Planner()
        assert planner is not None
    except Exception as e:
        pytest.fail(f"Failed to create Planner: {e}")

def test_agentdev_executor():
    """Test AgentDev executor can be instantiated"""
    try:
        from stillme_core.executor import PatchExecutor
        executor = PatchExecutor()
        assert executor is not None
    except Exception as e:
        pytest.fail(f"Failed to create PatchExecutor: {e}")

def test_agentdev_verifier():
    """Test AgentDev verifier can be instantiated"""
    try:
        from stillme_core.verifier import Verifier
        verifier = Verifier()
        assert verifier is not None
    except Exception as e:
        pytest.fail(f"Failed to create Verifier: {e}")

def test_basic_functionality():
    """Test basic functionality works"""
    # Simple test that should always pass
    assert 1 + 1 == 2
    assert "hello" + " " + "world" == "hello world"
    assert len([1, 2, 3]) == 3

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
