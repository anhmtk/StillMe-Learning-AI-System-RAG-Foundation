#!/usr/bin/env python3
"""
AgentDev Phase 4 Integration Tests
=================================

Integration tests for AgentDev with persistent capabilities.
"""

import os
import tempfile
import pytest
import time

from agent_dev.core.agentdev import AgentDev


class TestAgentDevPhase4:
    """Test AgentDev with persistent capabilities"""
    
    @pytest.fixture
    def agentdev(self):
        """Create AgentDev instance with temporary database"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test_agentdev.db")
            agent = AgentDev(db_path=db_path)
            try:
                yield agent
            finally:
                # Close database connections
                if hasattr(agent, 'session'):
                    agent.session.close()
                if hasattr(agent, 'engine'):
                    agent.engine.dispose()
    
    def test_agentdev_initialization(self, agentdev):
        """Test AgentDev initialization with persistent capabilities"""
        # Check that all components are initialized
        assert agentdev.feedback_repo is not None
        assert agentdev.rule_repo is not None
        assert agentdev.metric_repo is not None
        assert agentdev.rule_engine is not None
        assert agentdev.monitor is not None
        assert agentdev.planner is not None
        assert agentdev.executor is not None
        
        # Check that default rules are loaded
        rules = agentdev.rule_repo.get_active_rules()
        assert len(rules) == 2  # test_before_claim and forbid_dangerous_shell
        
        # Check rule names
        rule_names = [rule.rule_name for rule in rules]
        assert "test_before_claim" in rule_names
        assert "forbid_dangerous_shell" in rule_names
    
    def test_valid_task_execution(self, agentdev):
        """Test valid task execution - should PASS"""
        # Execute a valid task
        result = agentdev.execute("fix_bug", mode="development")
        
        # Should complete successfully
        assert "completed" in result or "error" in result
        
        # Check metrics
        metrics = agentdev.dump_metrics()
        assert metrics["counters"]["tasks_started"] == 1.0
        assert metrics["counters"]["tasks_pass"] == 1.0
        assert "task_execution" in metrics["timers"]
        
        # Check timer stats
        timer_stats = metrics["timers"]["task_execution"]
        assert timer_stats["count"] == 1
        assert timer_stats["avg"] > 0
    
    def test_rule_violation_blocking(self, agentdev):
        """Test rule violation - should BLOCK"""
        # Try to execute a task that violates test_before_claim rule
        result = agentdev.execute("claim", mode="production")
        
        # Should be blocked
        assert "BLOCKED" in result
        assert "Must test before claiming task" in result
        
        # Check metrics
        metrics = agentdev.dump_metrics()
        assert metrics["counters"]["tasks_started"] == 1.0
        assert metrics["counters"]["tasks_blocked"] == 1.0
        assert "tasks_pass" not in metrics["counters"]
    
    def test_dangerous_command_blocking(self, agentdev):
        """Test dangerous command blocking"""
        # Try to execute a dangerous command
        result = agentdev.execute("rm -rf /tmp/*", mode="production")
        
        # Should be blocked
        assert "BLOCKED" in result
        assert "Dangerous shell command detected" in result
        
        # Check metrics
        metrics = agentdev.dump_metrics()
        assert metrics["counters"]["tasks_blocked"] == 1.0
    
    def test_feedback_processing(self, agentdev):
        """Test feedback processing and storage"""
        # Send feedback
        result = agentdev.receive_feedback(
            user_id="test_user",
            feedback="The system is working well",
            session_id="test_session"
        )
        
        # Should save successfully
        assert "Feedback saved" in result
        assert "Suggestion:" in result
        
        # Check metrics
        metrics = agentdev.dump_metrics()
        assert metrics["counters"]["feedback_received"] == 1.0
        
        # Check database
        feedback_records = agentdev.feedback_repo.get_feedback_by_user("test_user")
        assert len(feedback_records) == 1
        assert feedback_records[0].feedback == "The system is working well"
        assert feedback_records[0].session_id == "test_session"
    
    def test_learning_suggestions(self, agentdev):
        """Test learning suggestion generation"""
        # Test different feedback types
        test_cases = [
            ("The system is slow", "Consider optimizing performance"),
            ("There was an error", "Review error handling"),
            ("Security issue detected", "Check security measures"),
            ("General feedback", "Continue monitoring for patterns")
        ]
        
        for feedback, expected_suggestion in test_cases:
            result = agentdev.receive_feedback("test_user", feedback)
            assert expected_suggestion in result
    
    def test_metrics_collection(self, agentdev):
        """Test comprehensive metrics collection"""
        # Execute multiple operations
        agentdev.execute("task1")
        agentdev.execute("task2")
        agentdev.execute("claim")  # Should be blocked
        agentdev.receive_feedback("user1", "Good work")
        agentdev.receive_feedback("user2", "Needs improvement")
        
        # Get metrics summary
        summary = agentdev.get_metrics_summary()
        
        # Check counters
        assert summary["total_events"] >= 5  # Multiple events recorded
        assert summary["counter_count"] >= 3  # Multiple counter types
        
        # Check specific metrics
        metrics = agentdev.dump_metrics()
        assert metrics["counters"]["tasks_started"] == 3.0
        assert metrics["counters"]["tasks_pass"] == 2.0
        assert metrics["counters"]["tasks_blocked"] == 1.0
        assert metrics["counters"]["feedback_received"] == 2.0
    
    def test_metrics_reset(self, agentdev):
        """Test metrics reset functionality"""
        # Generate some metrics
        agentdev.execute("task1")
        agentdev.receive_feedback("user1", "test")
        
        # Check metrics exist
        metrics_before = agentdev.dump_metrics()
        assert metrics_before["counters"]["tasks_started"] == 1.0
        
        # Reset metrics
        agentdev.reset_metrics()
        
        # Check metrics are cleared
        metrics_after = agentdev.dump_metrics()
        assert metrics_after["counters"] == {}
        assert metrics_after["gauges"] == {}
        assert metrics_after["timers"] == {}
        assert metrics_after["events"] == []
    
    def test_database_persistence(self, agentdev):
        """Test database persistence across operations"""
        # Create feedback
        agentdev.receive_feedback("user1", "Initial feedback", "session1")
        
        # Create rule
        agentdev.rule_repo.create_rule(
            "custom_rule",
            '{"description": "Custom rule", "conditions": [{"field": "task", "operator": "eq", "value": "custom"}], "action": {"type": "warn", "message": "Custom rule triggered"}}',
            priority=1
        )
        
        # Record metric
        agentdev.metric_repo.record_metric("custom_metric", 100.0, "gauge")
        
        # Verify persistence
        feedback_records = agentdev.feedback_repo.get_feedback_by_user("user1")
        assert len(feedback_records) == 1
        
        rules = agentdev.rule_repo.get_active_rules()
        rule_names = [rule.rule_name for rule in rules]
        assert "custom_rule" in rule_names
        
        metrics = agentdev.metric_repo.get_metrics_by_name("custom_metric")
        assert len(metrics) == 1
        assert metrics[0].metric_value == 100.0
    
    def test_rule_engine_integration(self, agentdev):
        """Test rule engine integration"""
        # Test rule compliance check
        context = {"task": "safe_task", "mode": "development"}
        results = agentdev.rule_engine.check_compliance("execute_task", context)
        assert len(results) == 0  # Should be compliant
        
        # Test rule violation
        context = {"task": "claim", "tested": False}
        results = agentdev.rule_engine.check_compliance("execute_task", context)
        assert len(results) == 1  # Should be non-compliant
        assert results[0].rule_name == "test_before_claim"
        assert results[0].action_type == "block"
    
    def test_monitoring_integration(self, agentdev):
        """Test monitoring integration"""
        # Execute task with timing
        start_time = time.time()
        result = agentdev.execute("timed_task")
        end_time = time.time()
        
        # Check timing metrics
        metrics = agentdev.dump_metrics()
        assert "task_execution" in metrics["timers"]
        
        timer_stats = metrics["timers"]["task_execution"]
        assert timer_stats["count"] == 1
        assert timer_stats["avg"] > 0
        assert timer_stats["avg"] < (end_time - start_time) * 1000 + 100  # Allow some margin
    
    def test_error_handling(self, agentdev):
        """Test error handling in persistent operations"""
        # Test feedback error handling
        result = agentdev.receive_feedback("", "")  # Invalid input
        assert "Error saving feedback" in result
        
        # Check error metrics
        metrics = agentdev.dump_metrics()
        assert metrics["counters"]["feedback_error"] == 1.0
    
    def test_full_workflow(self, agentdev):
        """Test complete AgentDev workflow"""
        # 1. Execute valid tasks
        result1 = agentdev.execute("fix_bug")
        result2 = agentdev.execute("optimize_code")
        
        # 2. Try to execute blocked task
        result3 = agentdev.execute("claim")
        
        # 3. Receive feedback
        feedback1 = agentdev.receive_feedback("user1", "Great work on the bug fix")
        feedback2 = agentdev.receive_feedback("user2", "The optimization is slow")
        
        # 4. Check all results
        assert "completed" in result1 or "error" in result1
        assert "completed" in result2 or "error" in result2
        assert "BLOCKED" in result3
        assert "Feedback saved" in feedback1
        assert "Feedback saved" in feedback2
        
        # 5. Verify metrics
        metrics = agentdev.dump_metrics()
        assert metrics["counters"]["tasks_started"] == 3.0
        assert metrics["counters"]["tasks_pass"] == 2.0
        assert metrics["counters"]["tasks_blocked"] == 1.0
        assert metrics["counters"]["feedback_received"] == 2.0
        
        # 6. Verify database persistence
        feedback_records = agentdev.feedback_repo.get_feedback_by_user("user1")
        assert len(feedback_records) == 1
        assert "Great work" in feedback_records[0].feedback
        
        # 7. Verify timer metrics
        assert "task_execution" in metrics["timers"]
        timer_stats = metrics["timers"]["task_execution"]
        assert timer_stats["count"] == 2  # Only successful tasks are timed
        
        # 8. Verify events
        assert len(metrics["events"]) >= 5  # Multiple events recorded
