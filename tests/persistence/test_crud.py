#!/usr/bin/env python3
"""
AgentDev Persistence CRUD Tests
===============================

Test CRUD operations for all persistence models.
"""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from agent_dev.persistence.models import (
    create_memory_database,
    get_session_factory,
    FeedbackModel,
    UserPreferencesModel,
    RuleModel,
    LearnedSolutionModel,
    MetricModel,
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
    engine = create_memory_database()
    SessionLocal = get_session_factory(engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def feedback_repo(db_session: Session):
    """Create feedback repository"""
    return FeedbackRepo(db_session)


@pytest.fixture
def user_prefs_repo(db_session: Session):
    """Create user preferences repository"""
    return UserPreferencesRepo(db_session)


@pytest.fixture
def rule_repo(db_session: Session):
    """Create rule repository"""
    return RuleRepo(db_session)


@pytest.fixture
def solution_repo(db_session: Session):
    """Create learned solution repository"""
    return LearnedSolutionRepo(db_session)


@pytest.fixture
def metric_repo(db_session: Session):
    """Create metric repository"""
    return MetricRepo(db_session)


class TestFeedbackRepo:
    """Test feedback repository operations"""
    
    def test_create_feedback(self, feedback_repo: FeedbackRepo):
        """Test creating feedback"""
        feedback = feedback_repo.create_feedback(
            user_id="test_user",
            feedback="This is a test feedback",
            session_id="test_session"
        )
        
        assert feedback.id is not None
        assert feedback.user_id == "test_user"
        assert feedback.feedback == "This is a test feedback"
        assert feedback.session_id == "test_session"
        assert feedback.timestamp is not None
    
    def test_get_feedback_by_user(self, feedback_repo: FeedbackRepo):
        """Test getting feedback by user"""
        # Create test feedback
        feedback_repo.create_feedback("user1", "Feedback 1")
        feedback_repo.create_feedback("user1", "Feedback 2")
        feedback_repo.create_feedback("user2", "Feedback 3")
        
        # Get feedback for user1
        user1_feedback = feedback_repo.get_feedback_by_user("user1")
        assert len(user1_feedback) == 2
        assert all(f.user_id == "user1" for f in user1_feedback)
    
    def test_get_feedback_by_session(self, feedback_repo: FeedbackRepo):
        """Test getting feedback by session"""
        # Create test feedback
        feedback_repo.create_feedback("user1", "Feedback 1", "session1")
        feedback_repo.create_feedback("user1", "Feedback 2", "session2")
        
        # Get feedback for session1
        session1_feedback = feedback_repo.get_feedback_by_session("session1")
        assert len(session1_feedback) == 1
        assert session1_feedback[0].session_id == "session1"


class TestUserPreferencesRepo:
    """Test user preferences repository operations"""
    
    def test_set_and_get_preference(self, user_prefs_repo: UserPreferencesRepo):
        """Test setting and getting preference"""
        # Set preference
        pref = user_prefs_repo.set_preference("user1", "theme", "dark")
        assert pref.user_id == "user1"
        assert pref.preference_key == "theme"
        assert pref.preference_value == "dark"
        
        # Get preference
        value = user_prefs_repo.get_preference("user1", "theme")
        assert value == "dark"
    
    def test_get_all_preferences(self, user_prefs_repo: UserPreferencesRepo):
        """Test getting all preferences"""
        # Set multiple preferences
        user_prefs_repo.set_preference("user1", "theme", "dark")
        user_prefs_repo.set_preference("user1", "language", "en")
        user_prefs_repo.set_preference("user2", "theme", "light")
        
        # Get all preferences for user1
        prefs = user_prefs_repo.get_all_preferences("user1")
        assert len(prefs) == 2
        assert prefs["theme"] == "dark"
        assert prefs["language"] == "en"
    
    def test_update_existing_preference(self, user_prefs_repo: UserPreferencesRepo):
        """Test updating existing preference"""
        # Set initial preference
        user_prefs_repo.set_preference("user1", "theme", "dark")
        
        # Update preference
        updated_pref = user_prefs_repo.set_preference("user1", "theme", "light")
        assert updated_pref.preference_value == "light"
        
        # Verify update
        value = user_prefs_repo.get_preference("user1", "theme")
        assert value == "light"


class TestRuleRepo:
    """Test rule repository operations"""
    
    def test_create_rule(self, rule_repo: RuleRepo):
        """Test creating rule"""
        rule = rule_repo.create_rule(
            rule_name="test_rule",
            rule_definition='{"type": "validation", "condition": "required"}',
            priority=10
        )
        
        assert rule.id is not None
        assert rule.rule_name == "test_rule"
        assert rule.rule_definition == '{"type": "validation", "condition": "required"}'
        assert rule.priority == 10
        assert rule.is_active is True
    
    def test_get_rule_by_name(self, rule_repo: RuleRepo):
        """Test getting rule by name"""
        # Create rule
        rule_repo.create_rule("test_rule", '{"type": "validation"}')
        
        # Get rule
        rule = rule_repo.get_rule_by_name("test_rule")
        assert rule is not None
        assert rule.rule_name == "test_rule"
        
        # Get non-existent rule
        non_existent = rule_repo.get_rule_by_name("non_existent")
        assert non_existent is None
    
    def test_get_active_rules(self, rule_repo: RuleRepo):
        """Test getting active rules"""
        # Create rules with different priorities
        rule_repo.create_rule("rule1", '{"type": "validation"}', priority=10)
        rule_repo.create_rule("rule2", '{"type": "security"}', priority=5)
        
        # Get active rules (should be ordered by priority desc)
        active_rules = rule_repo.get_active_rules()
        assert len(active_rules) == 2
        assert active_rules[0].priority >= active_rules[1].priority
    
    def test_update_rule(self, rule_repo: RuleRepo):
        """Test updating rule"""
        # Create rule
        rule_repo.create_rule("test_rule", '{"type": "validation"}', priority=5)
        
        # Update rule
        updated_rule = rule_repo.update_rule(
            "test_rule",
            '{"type": "security", "level": "high"}',
            priority=10,
            is_active=False
        )
        
        assert updated_rule is not None
        assert updated_rule.rule_definition == '{"type": "security", "level": "high"}'
        assert updated_rule.priority == 10
        assert updated_rule.is_active is False


class TestLearnedSolutionRepo:
    """Test learned solution repository operations"""
    
    def test_create_solution(self, solution_repo: LearnedSolutionRepo):
        """Test creating learned solution"""
        solution = solution_repo.create_solution(
            error_type="syntax_error",
            solution="Check for missing semicolon"
        )
        
        assert solution.id is not None
        assert solution.error_type == "syntax_error"
        assert solution.solution == "Check for missing semicolon"
        assert solution.success_rate == 1.0
        assert solution.usage_count == 0
    
    def test_get_solutions_for_error(self, solution_repo: LearnedSolutionRepo):
        """Test getting solutions for error type"""
        # Create solutions
        solution_repo.create_solution("syntax_error", "Solution 1")
        solution_repo.create_solution("syntax_error", "Solution 2")
        solution_repo.create_solution("runtime_error", "Solution 3")
        
        # Get solutions for syntax_error
        solutions = solution_repo.get_solutions_for_error("syntax_error")
        assert len(solutions) == 2
        assert all(s.error_type == "syntax_error" for s in solutions)
    
    def test_update_success_rate(self, solution_repo: LearnedSolutionRepo):
        """Test updating success rate"""
        # Create solution
        solution = solution_repo.create_solution("syntax_error", "Test solution")
        solution_id = solution.id
        
        # Update success rate (successful)
        updated_solution = solution_repo.update_success_rate(solution_id, success=True)
        assert updated_solution is not None
        assert updated_solution.usage_count == 1
        assert updated_solution.success_rate > 0.9  # Should be high after success
        
        # Update success rate (failed)
        updated_solution = solution_repo.update_success_rate(solution_id, success=False)
        assert updated_solution.usage_count == 2
        assert updated_solution.success_rate <= 0.9  # Should be lower or equal after failure


class TestMetricRepo:
    """Test metric repository operations"""
    
    def test_record_metric(self, metric_repo: MetricRepo):
        """Test recording metric"""
        metric = metric_repo.record_metric(
            name="execution_time",
            value=1.5,
            metric_type="timer",
            context='{"operation": "test"}'
        )
        
        assert metric.id is not None
        assert metric.metric_name == "execution_time"
        assert metric.metric_value == 1.5
        assert metric.metric_type == "timer"
        assert metric.context == '{"operation": "test"}'
    
    def test_get_metrics_by_name(self, metric_repo: MetricRepo):
        """Test getting metrics by name"""
        # Record metrics
        metric_repo.record_metric("execution_time", 1.0, "timer")
        metric_repo.record_metric("execution_time", 2.0, "timer")
        metric_repo.record_metric("memory_usage", 100.0, "gauge")
        
        # Get metrics by name
        metrics = metric_repo.get_metrics_by_name("execution_time")
        assert len(metrics) == 2
        assert all(m.metric_name == "execution_time" for m in metrics)
    
    def test_get_metrics_by_type(self, metric_repo: MetricRepo):
        """Test getting metrics by type"""
        # Record metrics
        metric_repo.record_metric("execution_time", 1.0, "timer")
        metric_repo.record_metric("memory_usage", 100.0, "gauge")
        metric_repo.record_metric("request_count", 5.0, "counter")
        
        # Get metrics by type
        timer_metrics = metric_repo.get_metrics_by_type("timer")
        assert len(timer_metrics) == 1
        assert timer_metrics[0].metric_type == "timer"
    
    def test_get_metrics_summary(self, metric_repo: MetricRepo):
        """Test getting metrics summary"""
        # Record metrics
        metric_repo.record_metric("execution_time", 1.0, "timer")
        metric_repo.record_metric("execution_time", 2.0, "timer")
        metric_repo.record_metric("execution_time", 3.0, "timer")
        
        # Get summary
        summary = metric_repo.get_metrics_summary("execution_time")
        assert summary["count"] == 3
        assert summary["avg"] == 2.0
        assert summary["min"] == 1.0
        assert summary["max"] == 3.0


class TestIntegration:
    """Integration tests for multiple repositories"""
    
    def test_full_workflow(self, feedback_repo: FeedbackRepo, user_prefs_repo: UserPreferencesRepo, 
                          rule_repo: RuleRepo, solution_repo: LearnedSolutionRepo, metric_repo: MetricRepo):
        """Test complete workflow across all repositories"""
        user_id = "integration_test_user"
        
        # 1. Set user preferences
        user_prefs_repo.set_preference(user_id, "theme", "dark")
        user_prefs_repo.set_preference(user_id, "language", "en")
        
        # 2. Create rules
        rule_repo.create_rule("validation_rule", '{"type": "validation"}', priority=10)
        rule_repo.create_rule("security_rule", '{"type": "security"}', priority=5)
        
        # 3. Record feedback
        feedback_repo.create_feedback(user_id, "Great system!", "session1")
        feedback_repo.create_feedback(user_id, "Need improvement", "session1")
        
        # 4. Create learned solutions
        solution_repo.create_solution("syntax_error", "Check semicolon")
        solution_repo.create_solution("runtime_error", "Check variable scope")
        
        # 5. Record metrics
        metric_repo.record_metric("execution_time", 1.5, "timer")
        metric_repo.record_metric("memory_usage", 100.0, "gauge")
        
        # Verify all data exists
        prefs = user_prefs_repo.get_all_preferences(user_id)
        assert len(prefs) == 2
        
        active_rules = rule_repo.get_active_rules()
        assert len(active_rules) == 2
        
        user_feedback = feedback_repo.get_feedback_by_user(user_id)
        assert len(user_feedback) == 2
        
        solutions = solution_repo.get_solutions_for_error("syntax_error")
        assert len(solutions) == 1
        
        metrics = metric_repo.get_metrics_by_name("execution_time")
        assert len(metrics) == 1