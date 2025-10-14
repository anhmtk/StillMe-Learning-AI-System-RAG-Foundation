#!/usr/bin/env python3
"""
Tests for agent_dev.persistence.repo module
CRUD operations and data persistence
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

from agent_dev.persistence.repo import FeedbackRepo, MetricRepo, RuleRepo
from agent_dev.persistence.models import FeedbackEvent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class TestRepoCRUD:
    """Test CRUD operations for AgentDev Repository modules"""

    def setup_method(self):
        """Setup test database"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.db_path = self.temp_dir / "test.db"

        # Create in-memory SQLite database for testing
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Initialize repositories
        self.feedback_repo = FeedbackRepo(self.session)
        self.metrics_repo = MetricRepo(self.session)
        self.rule_repo = RuleRepo(self.session)

    def teardown_method(self):
        """Cleanup test database"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_create_and_get_feedback_event_happy_path(self):
        """Test creating and retrieving feedback events"""
        # Create feedback event using the actual model
        feedback_data = {
            "session_id": "test_session_123",
            "task_type": "file_edit",
            "success": True,
            "feedback_text": "Task completed successfully",
            "timestamp": datetime.now(),
        }

        # Save to repository
        feedback_id = self.feedback_repo.create_feedback(feedback_data)
        assert feedback_id is not None

        # Retrieve and verify
        retrieved = self.feedback_repo.get_feedback(feedback_id)
        assert retrieved is not None
        assert retrieved.session_id == "test_session_123"
        assert retrieved.task_type == "file_edit"
        assert retrieved.success is True
        assert retrieved.feedback_text == "Task completed successfully"

    @pytest.mark.unit
    def test_update_rule_hits_and_last_applied(self):
        """Test updating rule hits and last applied timestamp"""
        # Create initial rule hit
        rule_hit = RuleHit(
            rule_name="test_rule",
            file_path="test_file.py",
            line_number=42,
            hits_count=1,
            last_applied=datetime.now() - timedelta(hours=1),
        )

        rule_id = self.repo.create_rule_hit(rule_hit)

        # Update hits count and last applied
        new_timestamp = datetime.now()
        self.repo.update_rule_hits(rule_id, hits_count=5, last_applied=new_timestamp)

        # Verify update
        updated = self.repo.get_rule_hit(rule_id)
        assert updated.hits_count == 5
        assert updated.last_applied == new_timestamp

    @pytest.mark.unit
    def test_record_metrics_daily_and_query_window(self):
        """Test recording metrics and querying by time window"""
        # Record multiple metrics
        base_time = datetime.now()

        for i in range(3):
            metrics = MetricsRecord(
                date=base_time.date() + timedelta(days=i),
                total_tasks=10 + i,
                successful_tasks=8 + i,
                failed_tasks=2,
                avg_duration_ms=1000 + i * 100,
            )
            self.repo.record_metrics(metrics)

        # Query metrics for date range
        start_date = base_time.date()
        end_date = start_date + timedelta(days=2)

        results = self.repo.get_metrics_by_date_range(start_date, end_date)
        assert len(results) == 3

        # Verify data integrity
        total_tasks = sum(r.total_tasks for r in results)
        assert total_tasks == 33  # 10 + 11 + 12

    @pytest.mark.unit
    def test_patch_history_roundtrip(self):
        """Test creating and retrieving patch history"""
        # Create patch history
        patch = PatchHistory(
            file_path="test_file.py",
            original_content="old content",
            patched_content="new content",
            patch_type="refactoring",
            applied_at=datetime.now(),
            success=True,
        )

        patch_id = self.repo.create_patch_history(patch)
        assert patch_id is not None

        # Retrieve and verify
        retrieved = self.repo.get_patch_history(patch_id)
        assert retrieved.file_path == "test_file.py"
        assert retrieved.original_content == "old content"
        assert retrieved.patched_content == "new content"
        assert retrieved.patch_type == "refactoring"
        assert retrieved.success is True

    @pytest.mark.unit
    def test_repo_raises_on_invalid_input_schema(self):
        """Test repository raises appropriate errors for invalid input"""
        # Test with invalid data type
        with pytest.raises((TypeError, ValueError, AttributeError)):
            self.repo.create_feedback_event("invalid_string")

        # Test with None input
        with pytest.raises((TypeError, ValueError, AttributeError)):
            self.repo.create_feedback_event(None)

        # Test with missing required fields
        incomplete_feedback = FeedbackEvent(
            session_id="test",
            # Missing required fields
        )
        with pytest.raises((TypeError, ValueError, AttributeError)):
            self.repo.create_feedback_event(incomplete_feedback)

    @pytest.mark.unit
    def test_repo_handles_empty_queries_gracefully(self):
        """Test repository handles empty query results gracefully"""
        # Query non-existent data
        result = self.repo.get_feedback_event("non_existent_id")
        assert result is None

        # Query empty date range
        future_date = datetime.now().date() + timedelta(days=365)
        results = self.repo.get_metrics_by_date_range(future_date, future_date)
        assert results == []

    @pytest.mark.unit
    def test_repo_connection_handling(self):
        """Test repository connection and error handling"""
        # Test with invalid database path
        with pytest.raises((OSError, IOError, Exception)):
            invalid_repo = AgentDevRepository("/invalid/path/that/does/not/exist.db")

        # Test repository initialization
        assert self.repo is not None
        assert hasattr(self.repo, "create_feedback_event")
        assert hasattr(self.repo, "get_feedback_event")
        assert hasattr(self.repo, "update_rule_hits")
        assert hasattr(self.repo, "record_metrics")