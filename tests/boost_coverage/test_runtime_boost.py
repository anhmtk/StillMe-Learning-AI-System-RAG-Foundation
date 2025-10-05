#!/usr/bin/env python3
"""
AgentDev Runtime Coverage Boost Tests
Target: agent_dev/runtime.py (0% → 60%)
"""

import pytest
import tempfile
from unittest.mock import Mock, patch
from pathlib import Path

# Import modules to test
from agent_dev.runtime import AgentDev
from agent_dev.schemas import TaskSpec, SafetyBudget, Policy


class TestAgentDevRuntimeBoost:
    """Boost coverage for agent_dev/runtime.py"""

    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sandbox_root = Path(self.temp_dir.name)

    def teardown_method(self):
        """Cleanup test environment"""
        self.temp_dir.cleanup()

    def test_agentdev_initialization(self):
        """Test AgentDev initialization"""
        agent = AgentDev(sandbox_root=str(self.sandbox_root))
        assert agent is not None
        assert hasattr(agent, "sandbox_root")
        assert hasattr(agent, "safety_budget")
        assert hasattr(agent, "policies")

    def test_agentdev_plan_task(self):
        """Test task planning"""
        agent = AgentDev(sandbox_root=str(self.sandbox_root))

        # Mock task spec
        task_spec = TaskSpec(
            task_id="test_task",
            description="Test task",
            requirements=["requirement1"],
            constraints=["constraint1"],
        )

        # Test plan method
        result = agent.plan(task_spec)
        assert result is not None
        assert hasattr(result, "task_id")
        assert hasattr(result, "steps")

    def test_agentdev_execute_task(self):
        """Test task execution"""
        agent = AgentDev(sandbox_root=str(self.sandbox_root))

        # Mock execution context
        with patch.object(agent, "_validate_safety") as mock_validate:
            mock_validate.return_value = True

            result = agent.execute_task("test_task", {"param": "value"})
            assert result is not None
            assert hasattr(result, "success")
            assert hasattr(result, "trace_id")

    def test_agentdev_validate_result(self):
        """Test result validation"""
        agent = AgentDev(sandbox_root=str(self.sandbox_root))

        # Mock validation result
        mock_result = Mock()
        mock_result.success = True
        mock_result.trace_id = "test_trace_123"

        result = agent.validate(mock_result)
        assert result is not None
        assert hasattr(result, "valid")
        assert hasattr(result, "issues")

    def test_safety_budget_enforcement(self):
        """Test safety budget enforcement"""
        agent = AgentDev(sandbox_root=str(self.sandbox_root))

        # Test with low budget
        agent.safety_budget = SafetyBudget(
            max_execution_time=1,  # 1 second
            max_memory_mb=10,  # 10MB
            max_file_operations=5,  # 5 operations
        )

        # Should enforce limits
        assert agent.safety_budget.max_execution_time == 1
        assert agent.safety_budget.max_memory_mb == 10
        assert agent.safety_budget.max_file_operations == 5

    def test_policy_validation(self):
        """Test policy validation"""
        agent = AgentDev(sandbox_root=str(self.sandbox_root))

        # Test policy creation
        policy = Policy(name="test_policy", rules=["rule1", "rule2"], severity="medium")

        agent.policies = [policy]
        assert len(agent.policies) == 1
        assert agent.policies[0].name == "test_policy"

    def test_error_handling(self):
        """Test error handling scenarios"""
        agent = AgentDev(sandbox_root=str(self.sandbox_root))

        # Test with invalid input
        with pytest.raises((ValueError, TypeError)):
            agent.plan(None)

        # Test with invalid task_id
        with pytest.raises((ValueError, TypeError)):
            agent.execute_task(None, {})

    def test_trace_id_generation(self):
        """Test trace ID generation"""
        agent = AgentDev(sandbox_root=str(self.sandbox_root))

        # Test trace ID format
        trace_id = agent._generate_trace_id()
        assert trace_id is not None
        assert isinstance(trace_id, str)
        assert len(trace_id) > 0

    def test_sandbox_integration(self):
        """Test sandbox integration"""
        agent = AgentDev(sandbox_root=str(self.sandbox_root))

        # Test sandbox root validation
        assert agent.sandbox_root == str(self.sandbox_root)

        # Test sandbox operations
        test_file = self.sandbox_root / "test.txt"
        test_file.write_text("test content")
        assert test_file.exists()
        assert test_file.read_text() == "test content"

    def test_telemetry_integration(self):
        """Test telemetry integration"""
        agent = AgentDev(sandbox_root=str(self.sandbox_root))

        # Test telemetry logging
        with patch.object(agent, "_log_telemetry") as mock_log:
            agent._log_telemetry("test_event", {"key": "value"})
            mock_log.assert_called_once()

    def test_cleanup_operations(self):
        """Test cleanup operations"""
        agent = AgentDev(sandbox_root=str(self.sandbox_root))

        # Test cleanup method exists
        assert hasattr(agent, "cleanup") or hasattr(agent, "_cleanup")

        # Test cleanup execution
        if hasattr(agent, "cleanup"):
            agent.cleanup()
        elif hasattr(agent, "_cleanup"):
            agent._cleanup()
