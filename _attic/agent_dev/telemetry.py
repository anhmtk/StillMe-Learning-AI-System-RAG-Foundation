"""
Telemetry system for AgentDev Sprint 1
JSONL logging with trace_id for execution tracking
"""

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime
from contextlib import contextmanager


class TelemetryLogger:
    """JSONL telemetry logger for AgentDev execution tracking"""

    def __init__(self, log_file: Optional[str] = None):
        self.log_file = Path(log_file) if log_file else None
        self.trace_id = str(uuid.uuid4())
        self.session_start = time.time()
        self.phase_count = 0

    def log_event(
        self,
        event_type: str,
        phase: str,
        data: Dict[str, Any],
        timestamp: Optional[float] = None,
    ) -> None:
        """Log a telemetry event to JSONL format"""
        if timestamp is None:
            timestamp = time.time()

        event = {
            "trace_id": self.trace_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "phase": phase,
            "data": data,
            "session_duration": timestamp - self.session_start,
        }

        # Write to file if specified
        if self.log_file:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def log_phase_start(self, phase: str, context: Dict[str, Any] = None) -> None:
        """Log the start of an execution phase"""
        self.phase_count += 1
        self.log_event(
            "phase_start",
            phase,
            {"phase_number": self.phase_count, "context": context or {}},
        )

    def log_phase_end(self, phase: str, result: Dict[str, Any] = None) -> None:
        """Log the end of an execution phase"""
        self.log_event(
            "phase_end",
            phase,
            {
                "result": result or {},
                "success": result.get("success", True) if result else True,
            },
        )

    def log_policy_decision(
        self,
        policy_name: str,
        decision: str,
        reason: str,
        context: Dict[str, Any] = None,
    ) -> None:
        """Log a policy decision"""
        self.log_event(
            "policy_decision",
            "policy",
            {
                "policy_name": policy_name,
                "decision": decision,
                "reason": reason,
                "context": context or {},
            },
        )

    def log_budget_check(
        self, budget_type: str, current_usage: float, limit: float, status: str
    ) -> None:
        """Log budget usage check"""
        self.log_event(
            "budget_check",
            "safety",
            {
                "budget_type": budget_type,
                "current_usage": current_usage,
                "limit": limit,
                "status": status,
                "percentage": (current_usage / limit * 100) if limit > 0 else 0,
            },
        )

    def log_error(
        self,
        error_type: str,
        error_message: str,
        phase: str,
        context: Dict[str, Any] = None,
    ) -> None:
        """Log an error event"""
        self.log_event(
            "error",
            phase,
            {
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {},
            },
        )

    def log_task_result(
        self, task_spec: Dict[str, Any], result: Dict[str, Any], duration_ms: float
    ) -> None:
        """Log final task result"""
        self.log_event(
            "task_result",
            "completion",
            {
                "task_spec": task_spec,
                "result": result,
                "duration_ms": duration_ms,
                "success": result.get("success", False),
            },
        )

    @contextmanager
    def phase_tracking(self, phase: str, context: Dict[str, Any] = None):
        """Context manager for automatic phase tracking"""
        start_time = time.time()
        self.log_phase_start(phase, context)

        try:
            yield
            self.log_phase_end(
                phase,
                {"success": True, "duration_ms": (time.time() - start_time) * 1000},
            )
        except Exception as e:
            self.log_phase_end(
                phase,
                {
                    "success": False,
                    "error": str(e),
                    "duration_ms": (time.time() - start_time) * 1000,
                },
            )
            self.log_error(type(e).__name__, str(e), phase, context)
            raise

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return {
            "trace_id": self.trace_id,
            "session_duration": time.time() - self.session_start,
            "phase_count": self.phase_count,
            "log_file": str(self.log_file) if self.log_file else None,
        }


def create_telemetry_logger(
    log_dir: str = "./agentdev_tests/e2e_sandboxes",
) -> TelemetryLogger:
    """Create a telemetry logger with automatic log file"""
    log_dir_path = Path(log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)

    # Create unique log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir_path / f"telemetry_{timestamp}.jsonl"

    return TelemetryLogger(str(log_file))


def parse_telemetry_log(log_file: str) -> list[Dict[str, Any]]:
    """Parse a telemetry JSONL log file"""
    events = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line.strip()))
    return events


def filter_events_by_phase(
    events: list[Dict[str, Any]], phase: str
) -> list[Dict[str, Any]]:
    """Filter telemetry events by phase"""
    return [event for event in events if event.get("phase") == phase]


def filter_events_by_type(
    events: list[Dict[str, Any]], event_type: str
) -> list[Dict[str, Any]]:
    """Filter telemetry events by type"""
    return [event for event in events if event.get("event_type") == event_type]


def get_phase_durations(events: list[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate phase durations from telemetry events"""
    phase_starts = {}
    phase_durations = {}

    for event in events:
        if event["event_type"] == "phase_start":
            phase_starts[event["phase"]] = event["timestamp"]
        elif event["event_type"] == "phase_end":
            phase = event["phase"]
            if phase in phase_starts:
                duration = event["timestamp"] - phase_starts[phase]
                phase_durations[phase] = duration
                del phase_starts[phase]

    return phase_durations
