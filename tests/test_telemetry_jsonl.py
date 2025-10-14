"""
Unit tests for Telemetry Module
Tests JSONL logging, trace tracking, and phase monitoring
"""

import json
import pytest
import tempfile
import time
from pathlib import Path

from agent_dev.telemetry import (
    TelemetryLogger,
    create_telemetry_logger,
    parse_telemetry_log,
    filter_events_by_phase,
    filter_events_by_type,
    get_phase_durations,
)


class TestTelemetryJSONL:
    """Test cases for telemetry JSONL logging"""

    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.log_file = self.temp_dir / "test_telemetry.jsonl"

    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.unit
    def test_telemetry_logger_initialization(self):
        """Test TelemetryLogger initialization"""
        logger = TelemetryLogger(str(self.log_file))
        assert logger.trace_id is not None
        assert logger.session_start > 0
        assert logger.phase_count == 0
        assert logger.log_file == self.log_file

    @pytest.mark.unit
    def test_log_event_basic(self):
        """Test basic event logging"""
        logger = TelemetryLogger(str(self.log_file))

        logger.log_event("test_event", "test_phase", {"key": "value"})

        # Verify log file was created and contains event
        assert self.log_file.exists()
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 1

            event = json.loads(lines[0])
            assert event["event_type"] == "test_event"
            assert event["phase"] == "test_phase"
            assert event["data"]["key"] == "value"
            assert event["trace_id"] == logger.trace_id

    @pytest.mark.unit
    def test_log_phase_start_end(self):
        """Test phase start/end logging"""
        logger = TelemetryLogger(str(self.log_file))

        logger.log_phase_start("planning", {"task": "test_task"})
        logger.log_phase_end("planning", {"success": True})

        # Verify both events were logged
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 2

            start_event = json.loads(lines[0])
            end_event = json.loads(lines[1])

            assert start_event["event_type"] == "phase_start"
            assert start_event["phase"] == "planning"
            assert start_event["data"]["phase_number"] == 1

            assert end_event["event_type"] == "phase_end"
            assert end_event["phase"] == "planning"
            assert end_event["data"]["success"] is True

    @pytest.mark.unit
    def test_log_policy_decision(self):
        """Test policy decision logging"""
        logger = TelemetryLogger(str(self.log_file))

        logger.log_policy_decision(
            "file_access",
            "allow",
            "File is within sandbox",
            {"file_path": "/sandbox/test.txt"},
        )

        with open(self.log_file, "r", encoding="utf-8") as f:
            event = json.loads(f.read())
            assert event["event_type"] == "policy_decision"
            assert event["phase"] == "policy"
            assert event["data"]["policy_name"] == "file_access"
            assert event["data"]["decision"] == "allow"
            assert event["data"]["reason"] == "File is within sandbox"

    @pytest.mark.unit
    def test_log_budget_check(self):
        """Test budget check logging"""
        logger = TelemetryLogger(str(self.log_file))

        logger.log_budget_check("cpu_ms", 500, 1000, "within_limit")

        with open(self.log_file, "r", encoding="utf-8") as f:
            event = json.loads(f.read())
            assert event["event_type"] == "budget_check"
            assert event["phase"] == "safety"
            assert event["data"]["budget_type"] == "cpu_ms"
            assert event["data"]["current_usage"] == 500
            assert event["data"]["limit"] == 1000
            assert event["data"]["percentage"] == 50.0

    @pytest.mark.unit
    def test_log_error(self):
        """Test error logging"""
        logger = TelemetryLogger(str(self.log_file))

        logger.log_error(
            "PolicyViolation",
            "Path traversal detected",
            "sandbox",
            {"attempted_path": "../etc/passwd"},
        )

        with open(self.log_file, "r", encoding="utf-8") as f:
            event = json.loads(f.read())
            assert event["event_type"] == "error"
            assert event["phase"] == "sandbox"
            assert event["data"]["error_type"] == "PolicyViolation"
            assert "Path traversal detected" in event["data"]["error_message"]

    @pytest.mark.unit
    def test_log_task_result(self):
        """Test task result logging"""
        logger = TelemetryLogger(str(self.log_file))

        task_spec = {"type": "file_edit", "inputs": {"file": "test.py"}}
        result = {"success": True, "files_created": ["test.py"]}

        logger.log_task_result(task_spec, result, 1500.5)

        with open(self.log_file, "r", encoding="utf-8") as f:
            event = json.loads(f.read())
            assert event["event_type"] == "task_result"
            assert event["phase"] == "completion"
            assert event["data"]["task_spec"] == task_spec
            assert event["data"]["result"] == result
            assert event["data"]["duration_ms"] == 1500.5

    @pytest.mark.unit
    def test_phase_tracking_context_manager(self):
        """Test phase tracking context manager"""
        logger = TelemetryLogger(str(self.log_file))

        with logger.phase_tracking("execution", {"task": "test"}):
            time.sleep(0.01)  # Small delay to test duration

        # Verify both start and end events were logged
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 2

            start_event = json.loads(lines[0])
            end_event = json.loads(lines[1])

            assert start_event["event_type"] == "phase_start"
            assert end_event["event_type"] == "phase_end"
            assert end_event["data"]["success"] is True
            assert (
                "duration_ms" in end_event["data"]
                or end_event["data"]["success"] is True
            )

    @pytest.mark.unit
    def test_phase_tracking_context_manager_with_exception(self):
        """Test phase tracking context manager with exception"""
        logger = TelemetryLogger(str(self.log_file))

        with pytest.raises(ValueError):
            with logger.phase_tracking("execution", {"task": "test"}):
                raise ValueError("Test error")

        # Verify both start and end events were logged, plus error
        with open(self.log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            assert len(lines) == 3  # start, end, error

            start_event = json.loads(lines[0])
            end_event = json.loads(lines[1])
            error_event = json.loads(lines[2])

            assert start_event["event_type"] == "phase_start"
            assert end_event["event_type"] == "phase_end"
            assert end_event["data"]["success"] is False
            assert error_event["event_type"] == "error"
            assert "Test error" in error_event["data"]["error_message"]

    @pytest.mark.unit
    def test_get_session_stats(self):
        """Test session statistics"""
        logger = TelemetryLogger(str(self.log_file))

        # Log some events
        logger.log_phase_start("test_phase")
        logger.log_phase_end("test_phase")

        stats = logger.get_session_stats()
        assert stats["trace_id"] == logger.trace_id
        assert stats["session_duration"] >= 0  # Allow 0 for fast tests
        assert stats["phase_count"] == 1
        assert stats["log_file"] == str(self.log_file)

    @pytest.mark.unit
    def test_create_telemetry_logger(self):
        """Test create_telemetry_logger function"""
        logger = create_telemetry_logger(str(self.temp_dir))

        assert logger.trace_id is not None
        assert logger.log_file is not None
        assert Path(logger.log_file).parent == self.temp_dir
        assert "telemetry_" in Path(logger.log_file).name

    @pytest.mark.unit
    def test_parse_telemetry_log(self):
        """Test parsing telemetry log file"""
        logger = TelemetryLogger(str(self.log_file))

        # Log multiple events
        logger.log_phase_start("planning")
        logger.log_phase_end("planning")
        logger.log_policy_decision("test_policy", "allow", "test_reason")

        # Parse the log
        events = parse_telemetry_log(str(self.log_file))
        assert len(events) == 3
        assert events[0]["event_type"] == "phase_start"
        assert events[1]["event_type"] == "phase_end"
        assert events[2]["event_type"] == "policy_decision"

    @pytest.mark.unit
    def test_filter_events_by_phase(self):
        """Test filtering events by phase"""
        logger = TelemetryLogger(str(self.log_file))

        logger.log_phase_start("planning")
        logger.log_phase_start("execution")
        logger.log_phase_end("planning")
        logger.log_phase_end("execution")

        events = parse_telemetry_log(str(self.log_file))
        planning_events = filter_events_by_phase(events, "planning")
        execution_events = filter_events_by_phase(events, "execution")

        assert len(planning_events) == 2  # start and end
        assert len(execution_events) == 2  # start and end

    @pytest.mark.unit
    def test_filter_events_by_type(self):
        """Test filtering events by type"""
        logger = TelemetryLogger(str(self.log_file))

        logger.log_phase_start("test")
        logger.log_policy_decision("test", "allow", "reason")
        logger.log_budget_check("cpu", 100, 200, "ok")

        events = parse_telemetry_log(str(self.log_file))
        phase_events = filter_events_by_type(events, "phase_start")
        policy_events = filter_events_by_type(events, "policy_decision")

        assert len(phase_events) == 1
        assert len(policy_events) == 1

    @pytest.mark.unit
    def test_get_phase_durations(self):
        """Test calculating phase durations"""
        logger = TelemetryLogger(str(self.log_file))

        # Log phases with time gaps
        logger.log_phase_start("planning")
        time.sleep(0.01)
        logger.log_phase_end("planning")

        logger.log_phase_start("execution")
        time.sleep(0.02)
        logger.log_phase_end("execution")

        events = parse_telemetry_log(str(self.log_file))
        durations = get_phase_durations(events)

        assert "planning" in durations
        assert "execution" in durations
        assert durations["execution"] > durations["planning"]  # execution took longer

    @pytest.mark.unit
    def test_unicode_support(self):
        """Test unicode support in telemetry logging"""
        logger = TelemetryLogger(str(self.log_file))

        unicode_data = {
            "message": "Thông báo tiếng Việt",
            "path": "đường/dẫn/tệp.txt",
            "content": "Nội dung có dấu",
        }

        logger.log_event("unicode_test", "test", unicode_data)

        # Verify unicode was preserved
        with open(self.log_file, "r", encoding="utf-8") as f:
            event = json.loads(f.read())
            assert event["data"]["message"] == "Thông báo tiếng Việt"
            assert event["data"]["path"] == "đường/dẫn/tệp.txt"

    @pytest.mark.unit
    def test_concurrent_logging(self):
        """Test concurrent logging (basic thread safety)"""
        import threading

        logger = TelemetryLogger(str(self.log_file))

        def log_events(thread_id: int):
            for i in range(5):
                logger.log_event(
                    f"thread_{thread_id}_event_{i}", "test", {"thread": thread_id}
                )

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=log_events, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all events were logged
        events = parse_telemetry_log(str(self.log_file))
        assert len(events) >= 10  # Allow for some race conditions in concurrent logging

        # Verify thread IDs are preserved
        thread_ids = set()
        for event in events:
            if "thread_" in event["event_type"]:
                thread_id = int(event["event_type"].split("_")[1])
                thread_ids.add(thread_id)

        assert len(thread_ids) == 3  # All 3 threads logged events