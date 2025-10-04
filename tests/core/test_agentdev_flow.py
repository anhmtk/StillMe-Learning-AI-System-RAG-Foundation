#!/usr/bin/env python3
"""
Integration tests for agent_dev/core/agentdev.py with real database
"""

from unittest.mock import patch


class TestAgentDevFlow:
    """Test AgentDev execution flow with real database"""

    def test_execute_blocked_by_rule(self, mock_agentdev):
        """Test task execution blocked by rule"""
        # Add a rule that blocks dangerous commands
        dangerous_rule = {
            "rule_name": "block_dangerous",
            "description": "Block dangerous commands",
            "conditions": [
                {"field": "cmd", "operator": "contains", "value": ["rm -rf"]}
            ],
            "action": {"type": "block", "message": "Dangerous command blocked"},
        }
        mock_agentdev.rule_engine.add_rule(dangerous_rule)

        # Execute dangerous command
        result = mock_agentdev.execute("rm -rf /", {"command": "rm -rf /"})

        # Should be blocked
        assert "blocked" in result.lower() or "dangerous" in result.lower()

        # Check metrics
        metrics = mock_agentdev.get_metrics_summary()
        assert metrics["total_counters"] >= 1.0

    def test_execute_pass_persists_metrics(self, mock_agentdev):
        """Test valid task execution persists metrics"""
        # Execute valid task
        result = mock_agentdev.execute("echo hello", {"command": "echo hello"})

        # Should pass
        assert "hello" in result or "completed" in result.lower()

        # Check metrics
        metrics = mock_agentdev.get_metrics_summary()
        assert metrics["total_counters"] >= 1.0
        assert "task_execution" in metrics["timer_summary"]

    def test_feedback_processing(self, mock_agentdev):
        """Test feedback processing and persistence"""
        # Process feedback
        feedback_data = {
            "session_id": "test_session",
            "user_id": "test_user",
            "rating": 5,
            "comment": "Great work!",
        }

        result = mock_agentdev.receive_feedback(
            user_id=feedback_data["user_id"],
            feedback=str(feedback_data),
            session_id=feedback_data["session_id"],
        )

        # Should process successfully
        assert "feedback" in result.lower() or "saved" in result.lower()

        # Check metrics
        metrics = mock_agentdev.get_metrics_summary()
        assert metrics["total_counters"] >= 1.0

    def test_rule_engine_integration(self, mock_agentdev):
        """Test rule engine integration"""
        # Add multiple rules
        rule1 = {
            "rule_name": "block_sudo",
            "description": "Block sudo commands",
            "conditions": [{"field": "cmd", "operator": "contains", "value": ["sudo"]}],
            "action": {"type": "block", "message": "sudo blocked"},
        }
        rule2 = {
            "rule_name": "allow_safe",
            "description": "Allow safe commands",
            "conditions": [
                {"field": "cmd", "operator": "in", "value": ["echo", "ls", "cat"]}
            ],
            "action": {"type": "block", "message": "safe command"},
        }

        mock_agentdev.rule_engine.add_rule(rule1)
        mock_agentdev.rule_engine.add_rule(rule2)

        # Test blocked command
        result1 = mock_agentdev.execute("sudo rm -rf", {"command": "sudo rm -rf"})
        assert "blocked" in result1.lower()

        # Test allowed command
        result2 = mock_agentdev.execute("echo test", {"command": "echo test"})
        assert "test" in result2 or "completed" in result2.lower()

    def test_monitoring_integration(self, mock_agentdev):
        """Test monitoring integration"""
        # Execute multiple tasks
        mock_agentdev.execute("task1", {})
        mock_agentdev.execute("task2", {})
        mock_agentdev.execute("task3", {})

        # Check metrics
        metrics = mock_agentdev.get_metrics_summary()
        assert metrics["total_counters"] >= 3.0
        assert "task_execution" in metrics["timer_summary"]

        # Test metrics dump
        dump = mock_agentdev.dump_metrics()
        assert isinstance(dump, dict)
        assert len(dump) > 0

        # Test metrics reset
        mock_agentdev.reset_metrics()
        reset_metrics = mock_agentdev.get_metrics_summary()
        assert reset_metrics["total_counters"] == 0.0

    def test_error_handling(self, mock_agentdev):
        """Test error handling in execution"""
        # Mock rule engine to raise exception
        with patch.object(
            mock_agentdev.rule_engine,
            "check_compliance",
            side_effect=Exception("Rule engine error"),
        ):
            result = mock_agentdev.execute("test_task", {})
            assert "error" in result.lower()

        # Mock monitor to raise exception
        with patch.object(
            mock_agentdev.monitor,
            "record_event",
            side_effect=Exception("Monitor error"),
        ):
            result = mock_agentdev.execute("test_task", {})
            # Should still execute but with monitor error
            assert result is not None

    def test_full_workflow(self, mock_agentdev):
        """Test complete workflow"""
        # Add rules
        rule = {
            "rule_name": "test_rule",
            "description": "Test rule",
            "conditions": [{"field": "cmd", "operator": "eq", "value": ["test"]}],
            "action": {"type": "block", "message": "Test allowed"},
        }
        mock_agentdev.rule_engine.add_rule(rule)

        # Execute task
        result = mock_agentdev.execute("test", {"action": "test"})
        assert "test" in result or "completed" in result.lower()

        # Process feedback
        feedback = {
            "session_id": "workflow_test",
            "user_id": "test_user",
            "rating": 4,
            "comment": "Good workflow",
        }
        feedback_result = mock_agentdev.receive_feedback(
            user_id=feedback["user_id"],
            feedback=str(feedback),
            session_id=feedback["session_id"],
        )
        assert "feedback" in feedback_result.lower()

        # Check final metrics
        metrics = mock_agentdev.get_metrics_summary()
        assert metrics["total_counters"] >= 1.0
