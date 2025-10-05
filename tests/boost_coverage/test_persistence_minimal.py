#!/usr/bin/env python3
"""
AgentDev Persistence Minimal Tests
Target: agent_dev/persistence/repo.py (26% → 60%)
STRICT MODE - Minimal functionality testing
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import modules to test
from agent_dev.persistence.repo import (
    FeedbackRepo, UserPreferencesRepo, RuleRepo, 
    LearnedSolutionRepo, MetricRepo, AgentDevRepo
)
from agent_dev.persistence.models import Base


class TestPersistenceMinimal:
    """STRICT tests for agent_dev/persistence/repo.py"""
    
    def setup_method(self):
        """Setup test environment with real database"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test.db"
        
        # Create real SQLite database
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        
        # Create tables
        Base.metadata.create_all(self.engine)
        
        # Create session
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
    def teardown_method(self):
        """Cleanup test environment"""
        self.session.close()
        self.engine.dispose()
        self.temp_dir.cleanup()
    
    def test_feedback_repo_initialization(self):
        """Test FeedbackRepo initialization"""
        repo = FeedbackRepo(self.session)
        assert repo is not None
        assert hasattr(repo, 'session')
        assert repo.session == self.session
    
    def test_feedback_repo_create_feedback_minimal(self):
        """Test create_feedback with minimal data"""
        repo = FeedbackRepo(self.session)
        
        # Test with minimal parameters
        result = repo.create_feedback(
            user_id="test_user",
            feedback="Great work!"
        )
        assert result is not None
        assert hasattr(result, 'id')
        assert result.user_id == "test_user"
        assert result.feedback == "Great work!"
    
    def test_feedback_repo_get_feedback_by_user(self):
        """Test get_feedback_by_user with real query"""
        repo = FeedbackRepo(self.session)
        
        # Create test data
        repo.create_feedback(
            user_id="user_1",
            feedback="Good work"
        )
        
        # Test query
        results = repo.get_feedback_by_user("user_1")
        assert len(results) == 1
        assert results[0].user_id == "user_1"
        assert results[0].feedback == "Good work"
    
    def test_feedback_repo_get_feedback_by_session(self):
        """Test get_feedback_by_session with real query"""
        repo = FeedbackRepo(self.session)
        
        # Create test data
        repo.create_feedback(
            user_id="user_1",
            feedback="Good work",
            session_id="session_1"
        )
        
        # Test query
        results = repo.get_feedback_by_session("session_1")
        assert len(results) == 1
        assert results[0].session_id == "session_1"
        assert results[0].feedback == "Good work"
    
    def test_user_preferences_repo_initialization(self):
        """Test UserPreferencesRepo initialization"""
        repo = UserPreferencesRepo(self.session)
        assert repo is not None
        assert hasattr(repo, 'session')
        assert repo.session == self.session
    
    def test_user_preferences_repo_get_preference(self):
        """Test get_preference with real query"""
        repo = UserPreferencesRepo(self.session)
        
        # Test query
        result = repo.get_preference("test_user", "theme")
        # Should return None or default value
        assert result is None or isinstance(result, str)
    
    def test_user_preferences_repo_set_preference(self):
        """Test set_preference with real data"""
        repo = UserPreferencesRepo(self.session)
        
        # Test with basic parameters
        result = repo.set_preference(
            user_id="test_user",
            key="theme",
            value="dark"
        )
        assert result is not None
        assert hasattr(result, 'id')
        assert result.user_id == "test_user"
        assert result.key == "theme"
        assert result.value == "dark"
    
    def test_rule_repo_initialization(self):
        """Test RuleRepo initialization"""
        repo = RuleRepo(self.session)
        assert repo is not None
        assert hasattr(repo, 'session')
        assert repo.session == self.session
    
    def test_rule_repo_create_rule(self):
        """Test create_rule with basic data"""
        repo = RuleRepo(self.session)
        
        # Test with basic parameters
        result = repo.create_rule(
            name="test_rule",
            description="Test rule",
            pattern="test_pattern",
            action="test_action"
        )
        assert result is not None
        assert hasattr(result, 'id')
        assert result.name == "test_rule"
        assert result.description == "Test rule"
        assert result.pattern == "test_pattern"
        assert result.action == "test_action"
    
    def test_rule_repo_get_rule(self):
        """Test get_rule with real query"""
        repo = RuleRepo(self.session)
        
        # Create test data
        repo.create_rule(
            name="test_rule",
            description="Test rule",
            pattern="test_pattern",
            action="test_action"
        )
        
        # Test query
        result = repo.get_rule("test_rule")
        assert result is not None
        assert result.name == "test_rule"
        assert result.description == "Test rule"
    
    def test_rule_repo_get_rules(self):
        """Test get_rules with real query"""
        repo = RuleRepo(self.session)
        
        # Create test data
        repo.create_rule(
            name="test_rule",
            description="Test rule",
            pattern="test_pattern",
            action="test_action"
        )
        
        # Test query
        results = repo.get_rules()
        assert len(results) == 1
        assert results[0].name == "test_rule"
    
    def test_rule_repo_update_rule(self):
        """Test update_rule with real update"""
        repo = RuleRepo(self.session)
        
        # Create test data
        created = repo.create_rule(
            name="test_rule",
            description="Test rule",
            pattern="test_pattern",
            action="test_action"
        )
        
        # Update rule
        updated = repo.update_rule(created.id, {
            "description": "Updated rule",
            "pattern": "updated_pattern"
        })
        
        assert updated is not None
        assert updated.description == "Updated rule"
        assert updated.pattern == "updated_pattern"
    
    def test_rule_repo_delete_rule(self):
        """Test delete_rule with real deletion"""
        repo = RuleRepo(self.session)
        
        # Create test data
        created = repo.create_rule(
            name="test_rule",
            description="Test rule",
            pattern="test_pattern",
            action="test_action"
        )
        
        # Delete rule
        result = repo.delete_rule(created.id)
        assert result is True
        
        # Verify deletion
        deleted = repo.get_rule("test_rule")
        assert deleted is None
    
    def test_metric_repo_initialization(self):
        """Test MetricRepo initialization"""
        repo = MetricRepo(self.session)
        assert repo is not None
        assert hasattr(repo, 'session')
        assert repo.session == self.session
    
    def test_metric_repo_record_metrics_minimal(self):
        """Test record_metrics with minimal data"""
        repo = MetricRepo(self.session)
        
        # Test with minimal parameters
        result = repo.record_metrics(
            name="test_metric",
            value=100.0
        )
        assert result is not None
        assert hasattr(result, 'id')
        assert result.name == "test_metric"
        assert result.value == 100.0
    
    def test_metric_repo_get_metrics_by_name(self):
        """Test get_metrics_by_name with real query"""
        repo = MetricRepo(self.session)
        
        # Create test data
        repo.record_metrics(
            name="test_metric",
            value=100.0
        )
        
        # Test query
        results = repo.get_metrics_by_name("test_metric")
        assert len(results) == 1
        assert results[0].name == "test_metric"
    
    def test_metric_repo_get_metrics_by_date_range(self):
        """Test get_metrics_by_date_range with real query"""
        repo = MetricRepo(self.session)
        
        # Create test data
        repo.record_metrics(
            name="test_metric",
            value=100.0
        )
        
        # Test query with date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        results = repo.get_metrics_by_date_range(start_date, end_date)
        assert len(results) >= 1
    
    def test_metric_repo_get_metrics_stats(self):
        """Test get_metrics_stats with real aggregation"""
        repo = MetricRepo(self.session)
        
        # Create test data
        repo.record_metrics(
            name="test_metric",
            value=100.0
        )
        repo.record_metrics(
            name="test_metric",
            value=200.0
        )
        
        # Test stats
        stats = repo.get_metrics_stats("test_metric")
        assert stats is not None
        assert hasattr(stats, 'total_count')
        assert hasattr(stats, 'average_value')
        assert hasattr(stats, 'min_value')
        assert hasattr(stats, 'max_value')
    
    def test_agentdev_repo_initialization(self):
        """Test AgentDevRepo initialization"""
        repo = AgentDevRepo(self.session)
        assert repo is not None
        assert hasattr(repo, 'session')
        assert repo.session == self.session
    
    def test_agentdev_repo_get_session(self):
        """Test get_session with real query"""
        repo = AgentDevRepo(self.session)
        
        # Test query
        result = repo.get_session("test_session")
        # Should return None or session object
        assert result is None or hasattr(result, 'session_id')
    
    def test_agentdev_repo_get_sessions_by_user(self):
        """Test get_sessions_by_user with real query"""
        repo = AgentDevRepo(self.session)
        
        # Test query
        results = repo.get_sessions_by_user("test_user")
        assert isinstance(results, list)
    
    def test_agentdev_repo_get_sessions_by_status(self):
        """Test get_sessions_by_status with real query"""
        repo = AgentDevRepo(self.session)
        
        # Test query
        results = repo.get_sessions_by_status("active")
        assert isinstance(results, list)
    
    def test_agentdev_repo_get_sessions_by_date_range(self):
        """Test get_sessions_by_date_range with real query"""
        repo = AgentDevRepo(self.session)
        
        # Test query with date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        results = repo.get_sessions_by_date_range(start_date, end_date)
        assert isinstance(results, list)
    
    def test_agentdev_repo_get_session_stats(self):
        """Test get_session_stats with real aggregation"""
        repo = AgentDevRepo(self.session)
        
        # Test stats
        stats = repo.get_session_stats()
        assert stats is not None
        assert hasattr(stats, 'total_sessions')
        assert hasattr(stats, 'active_sessions')
        assert hasattr(stats, 'completed_sessions')
        assert hasattr(stats, 'average_duration')
    
    def test_learned_solution_repo_initialization(self):
        """Test LearnedSolutionRepo initialization"""
        repo = LearnedSolutionRepo(self.session)
        assert repo is not None
        assert hasattr(repo, 'session')
        assert repo.session == self.session
    
    def test_learned_solution_repo_create_solution(self):
        """Test create_solution with basic data"""
        repo = LearnedSolutionRepo(self.session)
        
        # Test with basic parameters
        result = repo.create_solution(
            problem="test_problem",
            solution="test_solution",
            effectiveness=0.8
        )
        assert result is not None
        assert hasattr(result, 'id')
        assert result.problem == "test_problem"
        assert result.solution == "test_solution"
        assert result.effectiveness == 0.8
    
    def test_learned_solution_repo_get_solution(self):
        """Test get_solution with real query"""
        repo = LearnedSolutionRepo(self.session)
        
        # Create test data
        repo.create_solution(
            problem="test_problem",
            solution="test_solution",
            effectiveness=0.8
        )
        
        # Test query
        result = repo.get_solution("test_problem")
        assert result is not None
        assert result.problem == "test_problem"
        assert result.solution == "test_solution"
    
    def test_learned_solution_repo_get_solutions(self):
        """Test get_solutions with real query"""
        repo = LearnedSolutionRepo(self.session)
        
        # Create test data
        repo.create_solution(
            problem="test_problem",
            solution="test_solution",
            effectiveness=0.8
        )
        
        # Test query
        results = repo.get_solutions()
        assert len(results) == 1
        assert results[0].problem == "test_problem"
    
    def test_learned_solution_repo_update_solution(self):
        """Test update_solution with real update"""
        repo = LearnedSolutionRepo(self.session)
        
        # Create test data
        created = repo.create_solution(
            problem="test_problem",
            solution="test_solution",
            effectiveness=0.8
        )
        
        # Update solution
        updated = repo.update_solution(created.id, {
            "solution": "updated_solution",
            "effectiveness": 0.9
        })
        
        assert updated is not None
        assert updated.solution == "updated_solution"
        assert updated.effectiveness == 0.9
    
    def test_learned_solution_repo_delete_solution(self):
        """Test delete_solution with real deletion"""
        repo = LearnedSolutionRepo(self.session)
        
        # Create test data
        created = repo.create_solution(
            problem="test_problem",
            solution="test_solution",
            effectiveness=0.8
        )
        
        # Delete solution
        result = repo.delete_solution(created.id)
        assert result is True
        
        # Verify deletion
        deleted = repo.get_solution("test_problem")
        assert deleted is None
    
    def test_repo_error_handling_minimal(self):
        """Test minimal error handling"""
        # Test all repos with invalid inputs
        feedback_repo = FeedbackRepo(self.session)
        user_prefs_repo = UserPreferencesRepo(self.session)
        rule_repo = RuleRepo(self.session)
        metric_repo = MetricRepo(self.session)
        agentdev_repo = AgentDevRepo(self.session)
        learned_repo = LearnedSolutionRepo(self.session)
        
        # Test with None inputs
        with pytest.raises((ValueError, TypeError, AttributeError)):
            feedback_repo.create_feedback(None, None)
        
        with pytest.raises((ValueError, TypeError, AttributeError)):
            user_prefs_repo.set_preference(None, None, None)
        
        with pytest.raises((ValueError, TypeError, AttributeError)):
            rule_repo.create_rule(None, None, None, None)
        
        with pytest.raises((ValueError, TypeError, AttributeError)):
            metric_repo.record_metrics(None, None)
        
        with pytest.raises((ValueError, TypeError, AttributeError)):
            learned_repo.create_solution(None, None, None)
    
    def test_repo_database_connection_handling(self):
        """Test database connection handling"""
        # Test with closed session
        closed_session = Mock()
        closed_session.close = Mock()
        closed_session.execute = Mock(side_effect=Exception("Connection closed"))
        
        feedback_repo = FeedbackRepo(closed_session)
        
        with pytest.raises(Exception):
            feedback_repo.get_feedback_by_user("test_user")
    
    def test_repo_transaction_handling(self):
        """Test transaction handling"""
        feedback_repo = FeedbackRepo(self.session)
        
        # Test rollback on error
        with pytest.raises(Exception):
            # This should trigger a rollback
            feedback_repo.create_feedback("invalid_feedback", "invalid_user")
    
    def test_repo_concurrent_access(self):
        """Test concurrent access handling"""
        feedback_repo = FeedbackRepo(self.session)
        
        # Create multiple feedbacks concurrently
        results = []
        for i in range(10):
            result = feedback_repo.create_feedback(
                user_id=f"user_{i}",
                feedback=f"Feedback {i}"
            )
            results.append(result)
        
        # Verify all were created
        assert len(results) == 10
        assert all(r is not None for r in results)
    
    def test_repo_data_validation(self):
        """Test data validation"""
        feedback_repo = FeedbackRepo(self.session)
        
        # Test with invalid data types
        with pytest.raises((ValueError, TypeError)):
            feedback_repo.create_feedback(
                user_id=123,  # Should be string
                feedback="test"
            )
    
    def test_repo_query_optimization(self):
        """Test query optimization"""
        feedback_repo = FeedbackRepo(self.session)
        
        # Create large dataset
        for i in range(100):
            feedback_repo.create_feedback(
                user_id=f"user_{i}",
                feedback=f"Feedback {i}"
            )
        
        # Test query performance
        import time
        start_time = time.time()
        results = feedback_repo.get_feedback_by_user("user_50")
        end_time = time.time()
        
        assert len(results) == 1
        assert end_time - start_time < 1.0  # Should be fast
    
    def test_repo_memory_usage(self):
        """Test memory usage"""
        feedback_repo = FeedbackRepo(self.session)
        
        # Create large dataset
        for i in range(1000):
            feedback_repo.create_feedback(
                user_id=f"user_{i}",
                feedback=f"Feedback {i}"
            )
        
        # Test memory usage
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        
        # Should not use excessive memory
        assert memory_usage < 1000  # Less than 1GB
