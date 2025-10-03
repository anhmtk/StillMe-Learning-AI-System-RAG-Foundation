"""
Test CRUD operations for persistence layer
=========================================

Test database operations with SQLite in-memory database.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from agent_dev.persistence.models import (
    FeedbackModel,
    UserPreferencesModel,
    RuleModel,
    LearnedSolutionModel,
    MetricModel,
    create_memory_database,
)
from agent_dev.persistence.repo import (
    FeedbackRepo,
    UserPreferencesRepo,
    RuleRepo,
    LearnedSolutionRepo,
    MetricRepo,
)


@pytest.fixture
def db_session():
    """Create in-memory database session for testing"""
    engine, SessionLocal = create_memory_database()
    session = SessionLocal()
    yield session
    session.close()


def test_insert_and_fetch_feedback(db_session: Session):
    """Test feedback CRUD operations"""
    repo = FeedbackRepo(db_session)
    
    # Create feedback
    feedback = repo.create(
        user_id="test_user",
        feedback="This is a test feedback",
        session_id="test_session",
        feedback_type="positive",
        context='{"test": true}'
    )
    
    assert feedback.id is not None
    assert feedback.user_id == "test_user"
    assert feedback.feedback == "This is a test feedback"
    assert feedback.session_id == "test_session"
    assert feedback.feedback_type == "positive"
    assert feedback.context == '{"test": true}'
    assert isinstance(feedback.timestamp, datetime)
    
    # Fetch by user
    user_feedbacks = repo.get_by_user("test_user")
    assert len(user_feedbacks) == 1
    assert user_feedbacks[0].feedback == "This is a test feedback"
    
    # Fetch by session
    session_feedbacks = repo.get_by_session("test_session")
    assert len(session_feedbacks) == 1
    assert session_feedbacks[0].user_id == "test_user"


def test_insert_and_fetch_rule(db_session: Session):
    """Test rule CRUD operations"""
    repo = RuleRepo(db_session)
    
    # Create rule
    rule = repo.create_rule(
        rule_name="test_rule",
        rule_definition='{"condition": "test", "action": "block"}',
        priority=1,
        is_active=True
    )
    
    assert rule.id is not None
    assert rule.rule_name == "test_rule"
    assert rule.rule_definition == '{"condition": "test", "action": "block"}'
    assert rule.priority == 1
    assert rule.is_active is True
    assert isinstance(rule.created_at, datetime)
    
    # Fetch active rules
    active_rules = repo.get_active_rules()
    assert len(active_rules) == 1
    assert active_rules[0].rule_name == "test_rule"
    
    # Fetch by name
    fetched_rule = repo.get_rule_by_name("test_rule")
    assert fetched_rule is not None
    assert fetched_rule.rule_name == "test_rule"
    
    # Update rule
    updated_rule = repo.update_rule(
        "test_rule",
        '{"condition": "updated", "action": "allow"}',
        priority=2,
        is_active=False
    )
    assert updated_rule is not None
    assert updated_rule.rule_definition == '{"condition": "updated", "action": "allow"}'
    assert updated_rule.priority == 2
    assert updated_rule.is_active is False


def test_user_preferences_crud(db_session: Session):
    """Test user preferences CRUD operations"""
    repo = UserPreferencesRepo(db_session)
    
    # Set preference
    pref = repo.set_preference("test_user", "theme", "dark")
    assert pref.id is not None
    assert pref.user_id == "test_user"
    assert pref.preference_key == "theme"
    assert pref.preference_value == "dark"
    
    # Get preference
    value = repo.get_preference("test_user", "theme")
    assert value == "dark"
    
    # Get all preferences
    all_prefs = repo.get_all_preferences("test_user")
    assert len(all_prefs) == 1
    assert all_prefs["theme"] == "dark"
    
    # Update preference
    updated_pref = repo.set_preference("test_user", "theme", "light")
    assert updated_pref.preference_value == "light"
    
    # Verify update
    updated_value = repo.get_preference("test_user", "theme")
    assert updated_value == "light"


def test_learned_solutions_crud(db_session: Session):
    """Test learned solutions CRUD operations"""
    repo = LearnedSolutionRepo(db_session)
    
    # Record solution
    solution = repo.record_solution(
        error_type="TypeError",
        solution="Add type annotation",
        success_rate=0.8
    )
    
    assert solution.id is not None
    assert solution.error_type == "TypeError"
    assert solution.solution == "Add type annotation"
    assert solution.success_rate == 0.8
    assert solution.usage_count == 1
    
    # Get solutions for error type
    solutions = repo.get_solutions_for_error("TypeError")
    assert len(solutions) == 1
    assert solutions[0].solution == "Add type annotation"
    
    # Update success rate
    updated_solution = repo.update_success_rate(solution.id, True)
    assert updated_solution is not None
    assert updated_solution.usage_count == 2
    assert updated_solution.success_rate > 0.8  # Should increase


def test_metrics_crud(db_session: Session):
    """Test metrics CRUD operations"""
    repo = MetricRepo(db_session)
    
    # Record metric
    metric = repo.record_metric(
        metric_name="tasks_completed",
        metric_value=5.0,
        metric_type="counter",
        context='{"source": "test"}'
    )
    
    assert metric.id is not None
    assert metric.metric_name == "tasks_completed"
    assert metric.metric_value == 5.0
    assert metric.metric_type == "counter"
    assert metric.context == '{"source": "test"}'
    assert isinstance(metric.timestamp, datetime)
    
    # Get metrics by name
    metrics = repo.get_metrics_by_name("tasks_completed", hours=24)
    assert len(metrics) == 1
    assert metrics[0].metric_value == 5.0
    
    # Record more metrics
    repo.record_metric("tasks_completed", 3.0, "counter")
    repo.record_metric("tasks_completed", 7.0, "counter")
    
    # Get metrics summary
    summary = repo.get_metrics_summary(hours=24)
    assert "tasks_completed" in summary
    stats = summary["tasks_completed"]
    assert stats["count"] == 3
    assert stats["total"] == 15.0
    assert stats["min"] == 3.0
    assert stats["max"] == 7.0
    assert stats["avg"] == 5.0
    assert stats["type"] == "counter"


def test_recent_feedback(db_session: Session):
    """Test recent feedback filtering"""
    repo = FeedbackRepo(db_session)
    
    # Create old feedback (should not appear in recent)
    old_feedback = repo.create(
        user_id="test_user",
        feedback="Old feedback",
        session_id="old_session",
        feedback_type="neutral"
    )
    
    # Create recent feedback
    recent_feedback = repo.create(
        user_id="test_user",
        feedback="Recent feedback",
        session_id="recent_session",
        feedback_type="positive"
    )
    
    # Get recent feedback (last 1 hour)
    recent_feedbacks = repo.get_recent(hours=1)
    assert len(recent_feedbacks) >= 1
    
    # Should include recent feedback
    recent_texts = [f.feedback for f in recent_feedbacks]
    assert "Recent feedback" in recent_texts


def test_rule_priority_ordering(db_session: Session):
    """Test rule ordering by priority"""
    repo = RuleRepo(db_session)
    
    # Create rules with different priorities
    repo.create_rule("low_priority", '{"action": "log"}', priority=10)
    repo.create_rule("high_priority", '{"action": "block"}', priority=1)
    repo.create_rule("medium_priority", '{"action": "warn"}', priority=5)
    
    # Get active rules (should be ordered by priority)
    active_rules = repo.get_active_rules()
    assert len(active_rules) == 3
    assert active_rules[0].rule_name == "high_priority"  # priority 1
    assert active_rules[1].rule_name == "medium_priority"  # priority 5
    assert active_rules[2].rule_name == "low_priority"  # priority 10
