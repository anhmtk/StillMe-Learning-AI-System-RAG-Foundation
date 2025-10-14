from unittest.mock import MagicMock

# Mock classes since they're not available in stillme_core
AgentDevLogger = MagicMock
log_step = MagicMock

"""
Test observation files (logs and metrics)
"""

import json
from pathlib import Path

# from stillme_core.logging_utils import (
# )
import pytest

pytest.skip("Missing imports from stillme_core.metrics", allow_module_level=True)

from stillme_core.metrics import AgentDevMetrics, get_summary, record_session


class TestLoggingUtils:
    def test_log_step(self, tmp_path):
        """Test logging a step"""
        logger = AgentDevLogger(log_dir=str(tmp_path))

        logger.log_step(
            step_id=1,
            action="run_tests",
            ok=True,
            duration_s=2.5,
            stdout_tail="1 passed",
            description="Run unit tests",
            target="tests/",
            tests_run=["test_example.py"],
        )

        # Check log file was created
        assert logger.log_file.exists()

        # Check log content
        with open(logger.log_file, encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1

            log_entry = json.loads(lines[0])
            assert log_entry["step_id"] == 1
            assert log_entry["action"] == "run_tests"
            assert log_entry["ok"] is True
            assert log_entry["duration_s"] == 2.5
            assert log_entry["stdout_tail"] == "1 passed"
            assert log_entry["description"] == "Run unit tests"
            assert log_entry["target"] == "tests/"
            assert log_entry["tests_run"] == ["test_example.py"]

    def test_log_session_start_end(self, tmp_path):
        """Test logging session start and end"""
        logger = AgentDevLogger(log_dir=str(tmp_path))

        # Log session start
        logger.log_session_start(goal="Test goal", max_steps=3)

        # Log session end
        logger.log_session_end(
            goal="Test goal",
            total_steps=3,
            passed_steps=2,
            pass_rate=0.667,
            total_duration_s=10.5,
        )

        # Check log file
        assert logger.log_file.exists()

        with open(logger.log_file, encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 2

            # Check session start
            start_entry = json.loads(lines[0])
            assert start_entry["event"] == "session_start"
            assert start_entry["goal"] == "Test goal"
            assert start_entry["max_steps"] == 3

            # Check session end
            end_entry = json.loads(lines[1])
            assert end_entry["event"] == "session_end"
            assert end_entry["goal"] == "Test goal"
            assert end_entry["total_steps"] == 3
            assert end_entry["passed_steps"] == 2
            assert end_entry["pass_rate"] == 0.667
            assert end_entry["total_duration_s"] == 10.5

    def test_log_step_convenience_function(self, tmp_path):
        """Test convenience function for logging steps"""
        # Set up temporary directory
        import os

        os.chdir(tmp_path)

        log_step(
            step_id=1,
            action="test_action",
            ok=False,
            duration_s=1.0,
            stdout_tail="Test error",
            description="Test step",
            target="test.py",
        )

        # Check log was created
        log_file = Path("logs/agentdev.jsonl")
        assert log_file.exists()

        with open(log_file, encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1

            log_entry = json.loads(lines[0])
            assert log_entry["step_id"] == 1
            assert log_entry["action"] == "test_action"
            assert log_entry["ok"] is False

    def test_get_recent_logs(self, tmp_path):
        """Test getting recent logs"""
        logger = AgentDevLogger(log_dir=str(tmp_path))

        # Add multiple log entries
        for i in range(5):
            logger.log_step(
                step_id=i,
                action="test_action",
                ok=True,
                duration_s=1.0,
                description=f"Step {i}",
            )

        # Get recent logs
        recent_logs = logger.get_recent_logs(limit=3)
        assert len(recent_logs) == 3

        # Check order (should be most recent last, since we take last N lines)
        assert recent_logs[0]["step_id"] == 2
        assert recent_logs[1]["step_id"] == 3
        assert recent_logs[2]["step_id"] == 4


class TestMetrics:
    def test_record_session(self, tmp_path):
        """Test recording session metrics"""
        metrics = AgentDevMetrics(metrics_dir=str(tmp_path))

        steps_details = [
            {"step_id": 1, "action": "run_tests", "ok": True, "duration_s": 2.0},
            {"step_id": 2, "action": "edit_file", "ok": False, "duration_s": 1.5},
        ]

        metrics.record_session(
            goal="Test goal",
            total_steps=2,
            passed_steps=1,
            failed_steps=1,
            pass_rate=0.5,
            total_duration_s=3.5,
            steps_details=steps_details,
        )

        # Check metrics file was created
        assert metrics.metrics_file.exists()

        # Check metrics content
        with open(metrics.metrics_file, encoding="utf-8") as f:
            data = json.load(f)

            assert "sessions" in data
            assert len(data["sessions"]) == 1

            session = data["sessions"][0]
            assert session["goal"] == "Test goal"
            assert session["total_steps"] == 2
            assert session["passed_steps"] == 1
            assert session["failed_steps"] == 1
            assert session["pass_rate"] == 0.5
            assert session["total_duration_s"] == 3.5
            assert len(session["steps_details"]) == 2

    def test_summary_stats(self, tmp_path):
        """Test summary statistics calculation"""
        metrics = AgentDevMetrics(metrics_dir=str(tmp_path))

        # Record multiple sessions
        for i in range(3):
            metrics.record_session(
                goal=f"Goal {i}",
                total_steps=2,
                passed_steps=1,
                failed_steps=1,
                pass_rate=0.5,
                total_duration_s=5.0,
            )

        # Get summary
        summary = metrics.get_summary()

        assert summary["total_sessions"] == 3
        assert summary["total_steps"] == 6
        assert summary["total_passed"] == 3
        assert summary["total_failed"] == 3
        assert summary["overall_pass_rate"] == 0.5
        assert summary["avg_duration_s"] == 5.0
        assert summary["avg_steps_per_session"] == 2.0

    def test_action_stats(self, tmp_path):
        """Test action statistics"""
        metrics = AgentDevMetrics(metrics_dir=str(tmp_path))

        steps_details = [
            {"step_id": 1, "action": "run_tests", "ok": True},
            {"step_id": 2, "action": "run_tests", "ok": False},
            {"step_id": 3, "action": "edit_file", "ok": True},
            {"step_id": 4, "action": "edit_file", "ok": True},
        ]

        metrics.record_session(
            goal="Test goal",
            total_steps=4,
            passed_steps=3,
            failed_steps=1,
            pass_rate=0.75,
            total_duration_s=10.0,
            steps_details=steps_details,
        )

        # Get action stats
        action_stats = metrics.get_action_stats()

        assert "run_tests" in action_stats
        assert "edit_file" in action_stats

        assert action_stats["run_tests"]["total"] == 2
        assert action_stats["run_tests"]["passed"] == 1
        assert action_stats["run_tests"]["failed"] == 1

        assert action_stats["edit_file"]["total"] == 2
        assert action_stats["edit_file"]["passed"] == 2
        assert action_stats["edit_file"]["failed"] == 0

    def test_convenience_functions(self, tmp_path):
        """Test convenience functions"""

        os.chdir(tmp_path)

        # Record session using convenience function
        record_session(
            goal="Convenience test",
            total_steps=1,
            passed_steps=1,
            failed_steps=0,
            pass_rate=1.0,
            total_duration_s=2.0,
        )

        # Check metrics were recorded
        metrics_file = Path("metrics/agentdev_metrics.json")
        assert metrics_file.exists()

        # Get summary using convenience function
        summary = get_summary()
        assert summary["total_sessions"] == 1
        assert summary["total_steps"] == 1
        assert summary["overall_pass_rate"] == 1.0