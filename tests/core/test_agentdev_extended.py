"""
Extended tests for agent_dev/core/agentdev.py to achieve ≥ 90% coverage
"""

import os
import tempfile
from unittest.mock import patch

import pytest

from agent_dev.core.agentdev import AgentDev


class TestAgentDevExtended:
    """Extended tests for AgentDev to improve coverage"""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        try:
            os.unlink(db_path)
        except OSError:
            pass

    @pytest.fixture
    def agentdev(self, temp_db):
        """Create AgentDev instance with temp database"""
        with patch("agent_dev.core.agentdev.create_memory_database") as mock_create:
            from agent_dev.persistence.models import create_memory_database

            mock_create.return_value = create_memory_database(f"sqlite:///{temp_db}")
            agent = AgentDev()
            yield agent
            # Cleanup
            if hasattr(agent, "engine") and agent.engine:
                agent.engine.dispose()

    def test_agentdev_initialization_with_db(self, agentdev):
        """Test AgentDev initialization with database"""
        assert agentdev.engine is not None
        assert agentdev.session_factory is not None
        assert agentdev.feedback_repo is not None
        assert agentdev.rule_repo is not None
        assert agentdev.metric_repo is not None
        assert agentdev.rule_engine is not None
        assert agentdev.monitor is not None

    def test_load_initial_rules(self, agentdev):
        """Test loading initial rules"""
        # Test that default rules are created
        rules = agentdev.rule_repo.get_active_rules()
        assert (
            len(rules) >= 2
        )  # Should have test_before_claim and forbid_dangerous_shell

    def test_create_default_rules(self, agentdev):
        """Test creating default rules"""
        # Clear existing rules
        agentdev.rule_repo.session.query(agentdev.rule_repo.model).delete()
        agentdev.rule_repo.session.commit()

        # Create default rules
        agentdev._create_default_rules()

        # Verify rules were created
        rules = agentdev.rule_repo.get_active_rules()
        assert len(rules) >= 2

    def test_execute_with_rule_violation(self, agentdev):
        """Test execute method with rule violation"""
        # Test task that violates test_before_claim rule
        result = agentdev.execute("claim", {"task": "claim", "tested": False})

        assert "BLOCKED" in result
        assert "Must test before claiming task" in result

    def test_execute_with_dangerous_command(self, agentdev):
        """Test execute method with dangerous command"""
        # Test task that violates forbid_dangerous_shell rule
        result = agentdev.execute("shell", {"cmd": "rm -rf /tmp/*"})

        assert "BLOCKED" in result
        assert "Dangerous shell command detected" in result

    def test_execute_valid_task(self, agentdev):
        """Test execute method with valid task"""
        # Test valid task that doesn't violate any rules
        result = agentdev.execute("fix", {"task": "fix", "tested": True})

        assert "success" in result.lower() or "completed" in result.lower()

    def test_receive_feedback_success(self, agentdev):
        """Test receive_feedback method with valid feedback"""
        feedback = {
            "user_id": "test_user",
            "session_id": "test_session",
            "feedback_text": "Great work!",
            "rating": 5,
            "feedback_type": "positive",
        }

        result = agentdev.receive_feedback(feedback)
        assert "success" in result.lower()

    def test_receive_feedback_invalid_input(self, agentdev):
        """Test receive_feedback method with invalid input"""
        # Test with missing required fields
        invalid_feedback = {"user_id": "test_user"}

        result = agentdev.receive_feedback(invalid_feedback)
        assert "Error" in result

    def test_get_metrics_summary(self, agentdev):
        """Test get_metrics_summary method"""
        # Execute some tasks to generate metrics
        agentdev.execute("test", {"task": "test"})

        summary = agentdev.get_metrics_summary()
        assert isinstance(summary, dict)
        assert "counters" in summary
        assert "timers" in summary
        assert "gauges" in summary

    def test_dump_metrics(self, agentdev):
        """Test dump_metrics method"""
        # Execute some tasks to generate metrics
        agentdev.execute("test", {"task": "test"})

        metrics = agentdev.dump_metrics()
        assert isinstance(metrics, dict)

    def test_reset_metrics(self, agentdev):
        """Test reset_metrics method"""
        # Execute some tasks to generate metrics
        agentdev.execute("test", {"task": "test"})

        # Reset metrics
        agentdev.reset_metrics()

        # Verify metrics are reset
        summary = agentdev.get_metrics_summary()
        assert summary["counters"]["tasks_pass"] == 0.0

    def test_execute_with_monitoring(self, agentdev):
        """Test execute method with monitoring integration"""
        # Execute task and verify monitoring is working
        agentdev.execute("test", {"task": "test"})

        # Check that metrics were recorded
        summary = agentdev.get_metrics_summary()
        assert "tasks_pass" in summary["counters"]

    def test_rule_engine_integration(self, agentdev):
        """Test rule engine integration"""
        # Test that rules are properly loaded and working
        rules = agentdev.rule_engine.list_rules()
        assert len(rules) >= 2

    def test_persistence_integration(self, agentdev):
        """Test persistence integration"""
        # Test that feedback is properly saved
        feedback = {
            "user_id": "test_user",
            "session_id": "test_session",
            "feedback_text": "Test feedback",
            "rating": 4,
            "feedback_type": "positive",
        }

        result = agentdev.receive_feedback(feedback)
        assert "success" in result.lower()

        # Verify feedback was saved
        saved_feedback = agentdev.feedback_repo.get_feedback_by_user("test_user")
        assert len(saved_feedback) >= 1

    def test_error_handling_in_execute(self, agentdev):
        """Test error handling in execute method"""
        # Test with invalid context that might cause errors
        result = agentdev.execute("invalid", None)
        assert isinstance(result, str)

    def test_error_handling_in_feedback(self, agentdev):
        """Test error handling in receive_feedback method"""
        # Test with None input
        result = agentdev.receive_feedback(None)
        assert "Error" in result

    def test_metrics_collection_during_execute(self, agentdev):
        """Test that metrics are properly collected during execute"""
        # Execute multiple tasks
        agentdev.execute("task1", {"task": "task1"})
        agentdev.execute("task2", {"task": "task2"})

        # Check metrics
        summary = agentdev.get_metrics_summary()
        assert summary["counters"]["tasks_pass"] >= 2.0

    def test_rule_priority_handling(self, agentdev):
        """Test that rule priorities are handled correctly"""
        # Test that high priority rules are evaluated first
        result = agentdev.execute("claim", {"task": "claim", "tested": False})
        assert "BLOCKED" in result

    def test_context_parameter_handling(self, agentdev):
        """Test that context parameters are handled correctly"""
        # Test with various context types
        result1 = agentdev.execute("test", {"param1": "value1"})
        result2 = agentdev.execute("test", {"param2": 123})
        result3 = agentdev.execute("test", {"param3": True})

        # All should execute without errors
        assert isinstance(result1, str)
        assert isinstance(result2, str)
        assert isinstance(result3, str)
