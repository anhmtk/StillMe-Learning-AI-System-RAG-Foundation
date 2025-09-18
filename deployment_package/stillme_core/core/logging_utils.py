"""
Structured logging utilities for AgentDev
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


def ensure_parent_dir(file_path: str | Path) -> None:
    """Ensure parent directory exists for a file path"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)


class AgentDevLogger:
    """
    Structured JSONL logger for AgentDev steps
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / "agentdev.jsonl"

    def log_step(
        self,
        step_id: int,
        action: str,
        ok: bool,
        duration_s: float,
        stdout_tail: str = "",
        description: str = "",
        target: str = "",
        tests_run: Optional[list] = None,
    ) -> None:
        """
        Log a step execution to JSONL file

        Args:
            step_id: Step identifier
            action: Action performed (e.g., 'run_tests', 'edit_file')
            ok: Whether step succeeded
            duration_s: Duration in seconds
            stdout_tail: Last 500 chars of stdout/stderr
            description: Step description
            target: Target file or path
            tests_run: List of tests that were run
        """
        # Truncate stdout_tail to 500 chars
        stdout_tail = stdout_tail[:500] if len(stdout_tail) > 500 else stdout_tail

        record = {
            "timestamp": datetime.now().isoformat(),
            "step_id": step_id,
            "action": action,
            "ok": ok,
            "duration_s": round(duration_s, 3),
            "stdout_tail": stdout_tail,
            "description": description,
            "target": target,
            "tests_run": tests_run or [],
        }

        # Write to JSONL file
        ensure_parent_dir(self.log_file)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def log_session_start(self, goal: str, max_steps: int) -> None:
        """Log session start"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": "session_start",
            "goal": goal,
            "max_steps": max_steps,
        }

        ensure_parent_dir(self.log_file)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def log_session_end(
        self,
        goal: str,
        total_steps: int,
        passed_steps: int,
        pass_rate: float,
        total_duration_s: float,
    ) -> None:
        """Log session end"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": "session_end",
            "goal": goal,
            "total_steps": total_steps,
            "passed_steps": passed_steps,
            "pass_rate": round(pass_rate, 3),
            "total_duration_s": round(total_duration_s, 3),
        }

        ensure_parent_dir(self.log_file)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def get_recent_logs(self, limit: int = 10) -> list:
        """Get recent log entries"""
        if not self.log_file.exists():
            return []

        logs = []
        with open(self.log_file, encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    logs.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue

        return logs


# Global logger instance
_global_logger: Optional[AgentDevLogger] = None


def get_logger() -> AgentDevLogger:
    """Get global logger instance"""
    global _global_logger
    if _global_logger is None:
        _global_logger = AgentDevLogger()
    return _global_logger


def log_step(
    step_id: int,
    action: str,
    ok: bool,
    duration_s: float,
    stdout_tail: str = "",
    description: str = "",
    target: str = "",
    tests_run: Optional[list] = None,
) -> None:
    """Convenience function to log a step"""
    get_logger().log_step(
        step_id=step_id,
        action=action,
        ok=ok,
        duration_s=duration_s,
        stdout_tail=stdout_tail,
        description=description,
        target=target,
        tests_run=tests_run,
    )


def log_session_start(goal: str, max_steps: int) -> None:
    """Convenience function to log session start"""
    get_logger().log_session_start(goal=goal, max_steps=max_steps)


def log_session_end(
    goal: str,
    total_steps: int,
    passed_steps: int,
    pass_rate: float,
    total_duration_s: float,
) -> None:
    """Convenience function to log session end"""
    get_logger().log_session_end(
        goal=goal,
        total_steps=total_steps,
        passed_steps=passed_steps,
        pass_rate=pass_rate,
        total_duration_s=total_duration_s,
    )
