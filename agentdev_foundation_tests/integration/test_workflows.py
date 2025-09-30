"""
Integration tests for AgentDev workflows
Test complete workflows: Plan → Evaluate → Execute
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Add agent-dev path to sys.path
agent_dev_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'agent-dev', 'core')
if agent_dev_path not in sys.path:
    sys.path.insert(0, agent_dev_path)

from fixtures import TestFixtures

class TestWorkflows:
    """Test complete AgentDev workflows"""
    
    def test_plan_evaluate_execute_flow(self):
        """Test workflow: Plan → Evaluate → Execute"""
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            # Test complete workflow
            task = "Fix authentication bug in user login"
            result = agentdev.execute_task(task, AgentMode.SENIOR)
            
            # Assertions
            assert result is not None
            assert "✅" in result or "success" in result.lower()
            
            # Should include planning, evaluation, and execution
            assert "🧠" in result or "thinking" in result.lower()
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
    
    def test_learning_feedback_loop(self):
        """Test learning from experience feedback loop"""
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            # Execute multiple tasks to build experience
            tasks = [
                "Create user authentication module",
                "Add input validation to forms",
                "Implement error handling"
            ]
            
            results = []
            for task in tasks:
                result = agentdev.execute_task(task, AgentMode.SENIOR)
                results.append(result)
            
            # All tasks should complete successfully
            assert len(results) == 3
            for result in results:
                assert result is not None
                assert "✅" in result or "success" in result.lower()
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
    
    def test_policy_levels_impact(self):
        """Test how policy levels affect decision making"""
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            # Test with different modes
            task = "Implement new feature with potential security risks"
            
            # Test in simple mode
            simple_result = agentdev.execute_task(task, AgentMode.SIMPLE)
            
            # Test in senior mode
            senior_result = agentdev.execute_task(task, AgentMode.SENIOR)
            
            # Results should be different based on mode
            assert simple_result != senior_result
            
            # Senior mode should include more analysis
            assert "🧠" in senior_result or "thinking" in senior_result.lower()
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
    
    def test_error_handling_workflow(self):
        """Test error handling in workflows"""
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            # Test with invalid task
            invalid_task = ""
            result = agentdev.execute_task(invalid_task, AgentMode.SENIOR)
            
            # Should handle gracefully
            assert result is not None
            assert "❌" in result or "error" in result.lower() or "failed" in result.lower()
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
    
    def test_multi_module_integration(self):
        """Test integration between multiple modules"""
        try:
            from agentdev_unified_simple import AgentDevUnified, AgentMode
            
            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDevUnified(str(temp_project))
            
            # Test task that should trigger multiple modules
            task = "Fix security vulnerability and optimize performance"
            result = agentdev.execute_task(task, AgentMode.SENIOR)
            
            # Should include multiple types of analysis
            assert result is not None
            assert "✅" in result or "success" in result.lower()
            
            # Should show evidence of multiple modules working
            log_messages = agentdev.log_messages
            module_indicators = ["Impact", "Business", "Security", "Cleanup", "Conflict"]
            
            # At least some modules should be active
            active_modules = sum(1 for indicator in module_indicators 
                               if any(indicator in msg for msg in log_messages))
            assert active_modules > 0
            
            TestFixtures.cleanup_temp_project(temp_project)
            
        except ImportError:
            pytest.skip("AgentDevUnified not available")
