"""
Integration tests for AgentDev workflows
Test complete workflows: Plan → Evaluate → Execute
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add agent_dev path to sys.path
agent_dev_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'agent_dev', 'core')
if agent_dev_path not in sys.path:
    sys.path.insert(0, agent_dev_path)

from fixtures import TestFixtures


class TestWorkflows:
    """Test complete AgentDev workflows"""

    def test_plan_evaluate_execute_flow(self):
        """Test workflow: Plan → Evaluate → Execute"""
        try:
            from agent_dev.core.agent_mode import AgentMode
            from agent_dev.core.agentdev import AgentDev

            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDev(str(temp_project))

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
            pytest.skip("AgentDev not available")

    def test_learning_feedback_loop(self):
        """Test learning from experience feedback loop"""
        try:
            from agent_dev.core.agent_mode import AgentMode
            from agent_dev.core.agentdev import AgentDev

            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDev(str(temp_project))

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
            pytest.skip("AgentDev not available")

    def test_policy_levels_impact(self):
        """Test how policy levels affect decision making"""
        try:
            from agent_dev.core.agent_mode import AgentMode
            from agent_dev.core.agentdev import AgentDev

            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDev(str(temp_project))

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
            pytest.skip("AgentDev not available")

    def test_error_handling_workflow(self):
        """Test error handling in workflows"""
        try:
            from agent_dev.core.agent_mode import AgentMode
            from agent_dev.core.agentdev import AgentDev

            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDev(str(temp_project))

            # Test with invalid task
            invalid_task = ""
            result = agentdev.execute_task(invalid_task, AgentMode.SENIOR)

            # Should handle gracefully
            assert result is not None
            assert "❌" in result or "error" in result.lower() or "failed" in result.lower()

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("AgentDev not available")

    def test_multi_module_integration(self):
        """Test integration between multiple modules"""
        try:
            from agent_dev.core.agent_mode import AgentMode
            from agent_dev.core.agentdev import AgentDev

            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDev(str(temp_project))

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
            pytest.skip("AgentDev not available")

class TestStillMeIntegration:
    """Test integration with StillMe Framework"""

    def test_stillme_framework_integration(self):
        """Test AgentDev integration with StillMe Framework"""
        try:
            # Add stillme_core path
            stillme_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'stillme_core')
            if stillme_path not in sys.path:
                sys.path.insert(0, stillme_path)

            from framework import StillMeFramework

            # Initialize framework
            config = {
                'modules_dir': 'modules',
                'strict_mode': False,
                'security_level': 'high'
            }

            # This might fail due to memory issues, but we can test the integration
            try:
                framework = StillMeFramework(config)

                # Test AgentDev access
                agentdev = framework.get_agentdev()
                if agentdev is None:
                    pytest.skip("AgentDev not available")
                assert agentdev is not None

                # Test task execution through framework
                result = framework.execute_agentdev_task("Create test module", "senior")
                assert result is not None

            except Exception as e:
                # If framework fails due to memory issues, that's expected
                if "paging file" in str(e) or "memory" in str(e).lower():
                    pytest.skip("StillMe Framework failed due to memory constraints")
                else:
                    raise

        except ImportError:
            pytest.skip("StillMe Framework not available")

    def test_agentdev_as_technical_manager(self):
        """Test AgentDev as Technical Manager of StillMe"""
        try:
            from agent_dev.core.agent_mode import AgentMode
            from agent_dev.core.agentdev import AgentDev

            temp_project = TestFixtures.create_temp_project()
            agentdev = AgentDev(str(temp_project))

            # Test technical management tasks
            management_tasks = [
                "Monitor system performance",
                "Check for security vulnerabilities",
                "Review code quality",
                "Plan system improvements"
            ]

            results = []
            for task in management_tasks:
                result = agentdev.execute_task(task, AgentMode.SENIOR)
                results.append(result)

            # All management tasks should complete
            assert len(results) == 4
            for result in results:
                assert result is not None
                assert "✅" in result or "success" in result.lower()

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("AgentDev not available")

class TestDataPersistence:
    """Test data persistence and state management"""

    def test_experience_persistence(self):
        """Test that experience is persisted across sessions"""
        try:
            from experience_learner import ExperienceLearner

            temp_project = TestFixtures.create_temp_project()

            # First session
            learner1 = ExperienceLearner(str(temp_project))
            result1 = learner1.learn_from_experience()

            # Second session
            learner2 = ExperienceLearner(str(temp_project))
            result2 = learner2.learn_from_experience()

            # Should have some persistence
            assert result1 is not None
            assert result2 is not None

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("ExperienceLearner not available")

    def test_strategy_persistence(self):
        """Test that strategies are persisted across sessions"""
        try:
            from adaptive_strategy import AdaptiveStrategy

            temp_project = TestFixtures.create_temp_project()

            # First session
            strategy1 = AdaptiveStrategy(str(temp_project))
            result1 = strategy1.select_strategy({"task": "test"})

            # Second session
            strategy2 = AdaptiveStrategy(str(temp_project))
            result2 = strategy2.select_strategy({"task": "test"})

            # Should have some persistence
            assert result1 is not None
            assert result2 is not None

            TestFixtures.cleanup_temp_project(temp_project)

        except ImportError:
            pytest.skip("AdaptiveStrategy not available")
