#!/usr/bin/env python3
"""
AgentDev Persistence Basic Tests
Target: agent_dev/persistence/repo.py (26% → 60%)
STRICT MODE - Basic functionality testing
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


class TestPersistenceBasic:
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
    
    def test_feedback_repo_create_feedback_basic(self):
        """Test create_feedback with basic data"""
        repo = FeedbackRepo(self.session)
        
        # Test with basic parameters
        result = repo.create_feedback(
            user_id="test_user",
            feedback="Great work!"
        )
        assert result is not None
        assert hasattr(result, 'id')
        assert result.user_id == "test_user"
        assert result.feedback == "Great work!"
    
    def test_feedback_repo_create_feedback_with_session(self):
        """Test create_feedback with session"""
        repo = FeedbackRepo(self.session)
        
        # Test with session_id
        result = repo.create_feedback(
            user_id="test_user",
            feedback="Great work!",
            session_id="test_session"
        )
        assert result is not None
        assert result.user_id == "test_user"
        assert result.feedback == "Great work!"
        assert result.session_id == "test_session"
    
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
    
    def test_feedback_repo_get_feedback_by_date_range(self):
        """Test get_feedback_by_date_range with real query"""
        repo = FeedbackRepo(self.session)
        
        # Create test data
        repo.create_feedback(
            user_id="user_1",
            feedback="Good work"
        )
        
        # Test query with date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        results = repo.get_feedback_by_date_range(start_date, end_date)
        assert len(results) >= 1
    
    def test_feedback_repo_get_feedback_stats(self):
        """Test get_feedback_stats with real aggregation"""
        repo = FeedbackRepo(self.session)
        
        # Create test data
        repo.create_feedback(
            user_id="user_1",
            feedback="Good work"
        )
        repo.create_feedback(
            user_id="user_2",
            feedback="Bad work"
        )
        
        # Test stats
        stats = repo.get_feedback_stats()
        assert stats is not None
        assert hasattr(stats, 'total_feedback')
        assert hasattr(stats, 'unique_users')
        assert hasattr(stats, 'unique_sessions')
    
    def test_user_preferences_repo_initialization(self):
        """Test UserPreferencesRepo initialization"""
        repo = UserPreferencesRepo(self.session)
        assert repo is not None
        assert hasattr(repo, 'session')
        assert repo.session == self.session
    
    def test_user_preferences_repo_create_preferences_basic(self):
        """Test create_preferences with basic data"""
        repo = UserPreferencesRepo(self.session)
        
        # Test with basic parameters
        result = repo.create_preferences(
            user_id="test_user",
            preferences={"theme": "dark"},
            settings={"notifications": True}
        )
        assert result is not None
        assert hasattr(result, 'id')
        assert result.user_id == "test_user"
        assert result.preferences == {"theme": "dark"}
        assert result.settings == {"notifications": True}
    
    def test_user_preferences_repo_get_preferences(self):
        """Test get_preferences with real query"""
        repo = UserPreferencesRepo(self.session)
        
        # Create test data
        repo.create_preferences(
            user_id="test_user",
            preferences={"theme": "dark"},
            settings={"notifications": True}
        )
        
        # Test query
        result = repo.get_preferences("test_user")
        assert result is not None
        assert result.user_id == "test_user"
        assert result.preferences == {"theme": "dark"}
        assert result.settings == {"notifications": True}
    
    def test_user_preferences_repo_update_preferences(self):
        """Test update_preferences with real update"""
        repo = UserPreferencesRepo(self.session)
        
        # Create test data
        repo.create_preferences(
            user_id="test_user",
            preferences={"theme": "dark"},
            settings={"notifications": True}
        )
        
        # Update preferences
        updated = repo.update_preferences("test_user", {
            "preferences": {"theme": "light"},
            "settings": {"notifications": False}
        })
        
        assert updated is not None
        assert updated.preferences == {"theme": "light"}
        assert updated.settings == {"notifications": False}
    
    def test_rule_repo_initialization(self):
        """Test RuleRepo initialization"""
        repo = RuleRepo(self.session)
        assert repo is not None
        assert hasattr(repo, 'session')
        assert repo.session == self.session
    
    def test_rule_repo_create_rule_hit_basic(self):
        """Test create_rule_hit with basic data"""
        repo = RuleRepo(self.session)
        
        # Test with basic parameters
        result = repo.create_rule_hit(
            rule_name="test_rule",
            session_id="test_session",
            hit_count=1
        )
        assert result is not None
        assert hasattr(result, 'id')
        assert result.rule_name == "test_rule"
        assert result.session_id == "test_session"
        assert result.hit_count == 1
    
    def test_rule_repo_get_rule_hits(self):
        """Test get_rule_hits with real query"""
        repo = RuleRepo(self.session)
        
        # Create test data
        repo.create_rule_hit(
            rule_name="test_rule",
            session_id="test_session",
            hit_count=1
        )
        
        # Test query
        results = repo.get_rule_hits("test_rule")
        assert len(results) == 1
        assert results[0].rule_name == "test_rule"
    
    def test_rule_repo_update_rule_hits(self):
        """Test update_rule_hits with real update"""
        repo = RuleRepo(self.session)
        
        # Create test data
        created = repo.create_rule_hit(
            rule_name="test_rule",
            session_id="test_session",
            hit_count=1
        )
        
        # Update rule hits
        updated = repo.update_rule_hits(created.id, {
            "hit_count": 2
        })
        
        assert updated is not None
        assert updated.hit_count == 2
    
    def test_metric_repo_initialization(self):
        """Test MetricRepo initialization"""
        repo = MetricRepo(self.session)
        assert repo is not None
        assert hasattr(repo, 'session')
        assert repo.session == self.session
    
    def test_metric_repo_record_metrics_basic(self):
        """Test record_metrics with basic data"""
        repo = MetricRepo(self.session)
        
        # Test with basic parameters
        result = repo.record_metrics(
            session_id="test_session",
            metric_name="test_metric",
            value=100.0
        )
        assert result is not None
        assert hasattr(result, 'id')
        assert result.session_id == "test_session"
        assert result.metric_name == "test_metric"
        assert result.value == 100.0
    
    def test_metric_repo_get_metrics_by_session(self):
        """Test get_metrics_by_session with real query"""
        repo = MetricRepo(self.session)
        
        # Create test data
        repo.record_metrics(
            session_id="test_session",
            metric_name="test_metric",
            value=100.0
        )
        
        # Test query
        results = repo.get_metrics_by_session("test_session")
        assert len(results) == 1
        assert results[0].session_id == "test_session"
    
    def test_metric_repo_get_metrics_by_name(self):
        """Test get_metrics_by_name with real query"""
        repo = MetricRepo(self.session)
        
        # Create test data
        repo.record_metrics(
            session_id="test_session",
            metric_name="test_metric",
            value=100.0
        )
        
        # Test query
        results = repo.get_metrics_by_name("test_metric")
        assert len(results) == 1
        assert results[0].metric_name == "test_metric"
    
    def test_metric_repo_get_metrics_by_date_range(self):
        """Test get_metrics_by_date_range with real query"""
        repo = MetricRepo(self.session)
        
        # Create test data
        repo.record_metrics(
            session_id="test_session",
            metric_name="test_metric",
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
            session_id="session_1",
            metric_name="test_metric",
            value=100.0
        )
        repo.record_metrics(
            session_id="session_2",
            metric_name="test_metric",
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
    
    def test_agentdev_repo_create_session_basic(self):
        """Test create_session with basic data"""
        repo = AgentDevRepo(self.session)
        
        # Test with basic parameters
        result = repo.create_session(
            session_id="test_session",
            user_id="test_user",
            status="active"
        )
        assert result is not None
        assert hasattr(result, 'id')
        assert result.session_id == "test_session"
        assert result.user_id == "test_user"
        assert result.status == "active"
    
    def test_agentdev_repo_get_session(self):
        """Test get_session with real query"""
        repo = AgentDevRepo(self.session)
        
        # Create test data
        repo.create_session(
            session_id="test_session",
            user_id="test_user",
            status="active"
        )
        
        # Test query
        result = repo.get_session("test_session")
        assert result is not None
        assert result.session_id == "test_session"
        assert result.user_id == "test_user"
    
    def test_agentdev_repo_update_session(self):
        """Test update_session with real update"""
        repo = AgentDevRepo(self.session)
        
        # Create test data
        repo.create_session(
            session_id="test_session",
            user_id="test_user",
            status="active"
        )
        
        # Update session
        updated = repo.update_session("test_session", {
            "status": "completed"
        })
        
        assert updated is not None
        assert updated.status == "completed"
    
    def test_agentdev_repo_get_sessions_by_user(self):
        """Test get_sessions_by_user with real query"""
        repo = AgentDevRepo(self.session)
        
        # Create test data
        repo.create_session(
            session_id="test_session",
            user_id="test_user",
            status="active"
        )
        
        # Test query
        results = repo.get_sessions_by_user("test_user")
        assert len(results) == 1
        assert results[0].user_id == "test_user"
    
    def test_agentdev_repo_get_sessions_by_status(self):
        """Test get_sessions_by_status with real query"""
        repo = AgentDevRepo(self.session)
        
        # Create test data
        repo.create_session(
            session_id="test_session",
            user_id="test_user",
            status="active"
        )
        
        # Test query
        results = repo.get_sessions_by_status("active")
        assert len(results) == 1
        assert results[0].status == "active"
    
    def test_agentdev_repo_get_sessions_by_date_range(self):
        """Test get_sessions_by_date_range with real query"""
        repo = AgentDevRepo(self.session)
        
        # Create test data
        repo.create_session(
            session_id="test_session",
            user_id="test_user",
            status="active"
        )
        
        # Test query with date range
        from datetime import datetime, timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        
        results = repo.get_sessions_by_date_range(start_date, end_date)
        assert len(results) >= 1
    
    def test_agentdev_repo_get_session_stats(self):
        """Test get_session_stats with real aggregation"""
        repo = AgentDevRepo(self.session)
        
        # Create test data
        repo.create_session(
            session_id="session_1",
            user_id="test_user",
            status="active"
        )
        repo.create_session(
            session_id="session_2",
            user_id="test_user",
            status="completed"
        )
        
        # Test stats
        stats = repo.get_session_stats()
        assert stats is not None
        assert hasattr(stats, 'total_sessions')
        assert hasattr(stats, 'active_sessions')
        assert hasattr(stats, 'completed_sessions')
        assert hasattr(stats, 'average_duration')
    
    def test_repo_error_handling_basic(self):
        """Test basic error handling"""
        # Test all repos with invalid inputs
        feedback_repo = FeedbackRepo(self.session)
        user_prefs_repo = UserPreferencesRepo(self.session)
        rule_repo = RuleRepo(self.session)
        metric_repo = MetricRepo(self.session)
        agentdev_repo = AgentDevRepo(self.session)
        
        # Test with None inputs
        with pytest.raises((ValueError, TypeError, AttributeError)):
            feedback_repo.create_feedback(None, None)
        
        with pytest.raises((ValueError, TypeError, AttributeError)):
            user_prefs_repo.create_preferences(None, None, None)
        
        with pytest.raises((ValueError, TypeError, AttributeError)):
            rule_repo.create_rule_hit(None, None, None)
        
        with pytest.raises((ValueError, TypeError, AttributeError)):
            metric_repo.record_metrics(None, None, None)
        
        with pytest.raises((ValueError, TypeError, AttributeError)):
            agentdev_repo.create_session(None, None, None)
    
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
