"""
Simple test cases for AgentDev
"""

import pytest
import sys
import os
from pathlib import Path

# Add agent-dev path to sys.path
agent_dev_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'agent-dev', 'core')
if agent_dev_path not in sys.path:
    sys.path.insert(0, agent_dev_path)

from fixtures import TestFixtures

class TestSimpleAgentDev:
    """Simple tests for AgentDev"""
    
    def test_agentdev_basic_initialization(self):
        """Test basic AgentDev initialization"""
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            # Basic assertions
            assert agentdev is not None
            assert agentdev.mode == AgentMode.SENIOR
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
    
    def test_agentdev_simple_task(self):
        """Test simple task execution"""
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            # Test simple task
            task = "Create a simple test file"
            result = agentdev.execute_task(task, AgentMode.SIMPLE)
            
            # Should complete without error
            assert result is not None
            assert len(result) > 0
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
    
    def test_agentdev_performance_basic(self):
        """Test basic performance"""
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            import time
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            # Measure time
            start_time = time.time()
            result = agentdev.execute_task("Create test", AgentMode.SIMPLE)
            end_time = time.time()
            
            execution_time = (end_time - start_time) * 1000
            
            # Should be fast
            assert execution_time <= 5000  # 5 seconds max
            assert result is not None
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
