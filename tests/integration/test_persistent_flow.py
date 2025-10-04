"""
Integration Tests for Persistent Flow
====================================

Test complete persistent flow with all components working together.
"""

from agent_dev.learning.engine import LearningEngine
from agent_dev.monitoring.metrics import MetricsCollector
from agent_dev.rules.engine import RuleEngine


def test_flow_with_rule_violation():
    """Test flow with rule violation"""
    # Initialize components
    rule_engine = RuleEngine()
    # learning_engine = LearningEngine()  # Not used in this test
    metrics = MetricsCollector()

    # Add a rule that blocks dangerous actions
    dangerous_rule = {
        "rule_name": "block_dangerous_actions",
        "description": "Block dangerous actions",
        "conditions": [
            {"field": "action", "operator": "eq", "value": ["dangerous_action"]}
        ],
        "action": {"type": "block", "message": "Dangerous action blocked"},
    }

    rule_engine.add_rule(dangerous_rule)

    # Test dangerous action - should be blocked
    context = {"user_id": "test_user"}
    result = rule_engine.check_compliance("dangerous_action", context)

    # Should be non-compliant
    assert result["compliant"] is False
    assert "block_dangerous_actions" in result["violated_rules"]

    # Record metrics for blocked action
    metrics.record_event("actions_blocked", 1.0, {"rule": "block_dangerous_actions"})

    # Verify metrics
    assert metrics.get_counter("actions_blocked") == 1


def test_flow_with_feedback_and_metrics():
    """Test flow with feedback and metrics"""
    # Initialize components
    learning_engine = LearningEngine()
    metrics = MetricsCollector()

    # Record feedback about performance
    feedback_success = learning_engine.record_feedback(
        user_id="test_user",
        feedback_text="The system is too slow, please optimize performance",
        session_id="test_session",
        context='{"component": "performance"}',
    )
    assert feedback_success is True

    # Record feedback about quality
    feedback_success = learning_engine.record_feedback(
        user_id="test_user",
        feedback_text="Great quality output, very accurate results - positive experience",
        session_id="test_session",
        context='{"component": "quality"}',
    )
    assert feedback_success is True

    # Get suggestions based on feedback
    suggestions = learning_engine.suggest_adjustments(user_id="test_user")
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0

    # Record metrics for feedback processing
    metrics.record_event("feedback_processed", 2.0)
    metrics.record_event("suggestions_generated", len(suggestions))

    # Verify metrics
    assert metrics.get_counter("feedback_processed") == 2
    assert metrics.get_counter("suggestions_generated") == len(suggestions)

    # Get feedback summary
    summary = learning_engine.get_feedback_summary(user_id="test_user")
    assert summary["total_feedback"] == 2
    assert summary["positive_count"] > 0
    assert "suggestions" in summary


def test_complete_agentdev_flow():
    """Test complete AgentDev flow with all components"""
    # Initialize all components
    rule_engine = RuleEngine()
    learning_engine = LearningEngine()
    metrics = MetricsCollector()

    # Add rules
    test_rule = {
        "rule_name": "test_before_execute",
        "description": "Must test before executing",
        "conditions": [
            {"field": "action", "operator": "eq", "value": ["execute"]},
            {"field": "context.tested", "operator": "eq", "value": [True]},
        ],
        "action": {"type": "block", "message": "Must test before executing"},
    }
    rule_engine.add_rule(test_rule)

    # Simulate AgentDev workflow
    user_id = "test_user"
    session_id = "test_session"

    # 1. Plan phase
    with metrics.timer("plan_duration"):
        plan_context = {"task": "execute", "tested": True}
        plan_result = rule_engine.check_compliance("plan", plan_context)
        assert plan_result["compliant"] is True
        metrics.record_event("plans_created", 1.0)

    # 2. Execute phase
    with metrics.timer("execute_duration"):
        execute_context = {"task": "execute", "tested": True}
        execute_result = rule_engine.check_compliance("execute", execute_context)
        assert execute_result["compliant"] is True
        metrics.record_event("tasks_executed", 1.0)

    # 3. Validate phase
    with metrics.timer("validate_duration"):
        validate_context = {"task": "validate"}
        validate_result = rule_engine.check_compliance("validate", validate_context)
        assert validate_result["compliant"] is True
        metrics.record_event("validations_performed", 1.0)

    # 4. Security phase
    with metrics.timer("security_duration"):
        security_context = {"task": "security_check"}
        security_result = rule_engine.check_compliance(
            "security_check", security_context
        )
        assert security_result["compliant"] is True
        metrics.record_event("security_checks", 1.0)

    # 5. Record feedback
    feedback_success = learning_engine.record_feedback(
        user_id=user_id,
        feedback_text="Great performance, fast execution!",
        session_id=session_id,
        context='{"phase": "complete_flow"}',
    )
    assert feedback_success is True

    # 6. Get suggestions
    suggestions = learning_engine.suggest_adjustments(user_id=user_id)
    assert isinstance(suggestions, list)

    # 7. Dump metrics
    metrics_summary = metrics.dump_metrics()
    assert "counters" in metrics_summary
    assert "timers" in metrics_summary

    # Verify all metrics were recorded
    assert metrics.get_counter("plans_created") == 1
    assert metrics.get_counter("tasks_executed") == 1
    assert metrics.get_counter("validations_performed") == 1
    assert metrics.get_counter("security_checks") == 1

    # Verify timer metrics exist
    assert "plan_duration" in metrics_summary["timers"]
    assert "execute_duration" in metrics_summary["timers"]
    assert "validate_duration" in metrics_summary["timers"]
    assert "security_duration" in metrics_summary["timers"]


def test_rule_violation_with_metrics():
    """Test rule violation with metrics recording"""
    rule_engine = RuleEngine()
    metrics = MetricsCollector()

    # Add rule that blocks certain actions
    block_rule = {
        "rule_name": "block_risky_actions",
        "description": "Block risky actions",
        "conditions": [
            {"field": "action", "operator": "eq", "value": ["risky_action"]}
        ],
        "action": {"type": "block", "message": "Risky action blocked"},
    }
    rule_engine.add_rule(block_rule)

    # Test risky action
    context = {"user_id": "test_user", "risk_level": "high"}
    result = rule_engine.check_compliance("risky_action", context)

    # Should be blocked
    assert result["compliant"] is False
    assert "block_risky_actions" in result["violated_rules"]

    # Record metrics for blocked action
    metrics.record_event(
        "actions_blocked",
        1.0,
        {"rule": "block_risky_actions", "reason": "Risky action blocked"},
    )

    # Record security event
    metrics.record_event(
        "security_violations",
        1.0,
        {"type": "rule_violation", "rule": "block_risky_actions"},
    )

    # Verify metrics
    assert metrics.get_counter("actions_blocked") == 1
    assert metrics.get_counter("security_violations") == 1

    # Dump metrics and verify
    metrics_summary = metrics.dump_metrics()
    assert metrics_summary["counters"]["actions_blocked"] == 1
    assert metrics_summary["counters"]["security_violations"] == 1


def test_learning_with_metrics():
    """Test learning system with metrics integration"""
    learning_engine = LearningEngine()
    metrics = MetricsCollector()

    # Record multiple feedback samples
    feedback_samples = [
        "The system is too slow, please optimize",
        "Great quality output, very accurate - positive experience",
        "The interface is confusing and hard to use",
        "Excellent reliability, no crashes - positive experience",
        "Security is good, feels safe - positive experience",
    ]

    # Record feedback with metrics
    for i, feedback in enumerate(feedback_samples):
        with metrics.timer("feedback_processing"):
            success = learning_engine.record_feedback(
                user_id="test_user",
                feedback_text=feedback,
                session_id=f"session_{i}",
                context=f'{{"sample": {i}}}',
            )
            assert success is True
            metrics.record_event("feedback_recorded", 1.0)

    # Get suggestions with metrics
    with metrics.timer("suggestion_generation"):
        suggestions = learning_engine.suggest_adjustments(user_id="test_user")
        metrics.record_event("suggestions_generated", len(suggestions))

    # Get summary with metrics
    with metrics.timer("summary_generation"):
        summary = learning_engine.get_feedback_summary(user_id="test_user")
        metrics.record_event("summaries_generated", 1.0)

    # Verify metrics
    assert metrics.get_counter("feedback_recorded") == 5
    assert metrics.get_counter("suggestions_generated") == len(suggestions)
    assert metrics.get_counter("summaries_generated") == 1

    # Verify summary
    assert summary["total_feedback"] == 5
    assert summary["positive_count"] > 0
    assert len(summary["suggestions"]) > 0

    # Dump metrics
    metrics_summary = metrics.dump_metrics()
    assert "feedback_processing" in metrics_summary["timers"]
    assert "suggestion_generation" in metrics_summary["timers"]
    assert "summary_generation" in metrics_summary["timers"]
