"""
Metrics collection for AgentDev
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def ensure_parent_dir(file_path: str | Path) -> None:
    """Ensure parent directory exists for a file path"""
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)


class AgentDevMetrics:
    """
    Metrics collector for AgentDev performance
    """

    def __init__(self, metrics_dir: str = "metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_file = self.metrics_dir / "agentdev_metrics.json"

    def record_session(
        self,
        goal: str,
        total_steps: int,
        passed_steps: int,
        failed_steps: int,
        pass_rate: float,
        total_duration_s: float,
        steps_details: list | None = None,
    ) -> None:
        """
        Record session metrics

        Args:
            goal: Goal description
            total_steps: Total number of steps executed
            passed_steps: Number of passed steps
            failed_steps: Number of failed steps
            pass_rate: Pass rate (0.0 to 1.0)
            total_duration_s: Total duration in seconds
            steps_details: List of step details
        """
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "goal": goal,
            "total_steps": total_steps,
            "passed_steps": passed_steps,
            "failed_steps": failed_steps,
            "pass_rate": round(pass_rate, 3),
            "total_duration_s": round(total_duration_s, 3),
            "steps_details": steps_details or [],
        }

        # Load existing metrics
        existing_metrics = self.load_metrics()

        # Add new session
        if "sessions" not in existing_metrics:
            existing_metrics["sessions"] = []

        existing_metrics["sessions"].append(metrics)

        # Update summary statistics
        self._update_summary_stats(existing_metrics)

        # Save metrics
        self._save_metrics(existing_metrics)

    def _update_summary_stats(self, metrics: dict[str, Any]) -> None:
        """Update summary statistics"""
        sessions = metrics.get("sessions", [])

        if not sessions:
            return

        # Calculate summary stats
        total_sessions = len(sessions)
        total_steps = sum(s.get("total_steps", 0) for s in sessions)
        total_passed = sum(s.get("passed_steps", 0) for s in sessions)
        total_failed = sum(s.get("failed_steps", 0) for s in sessions)
        total_duration = sum(s.get("total_duration_s", 0) for s in sessions)

        # Calculate averages
        avg_pass_rate = total_passed / total_steps if total_steps > 0 else 0.0
        avg_duration = total_duration / total_sessions if total_sessions > 0 else 0.0
        avg_steps_per_session = (
            total_steps / total_sessions if total_sessions > 0 else 0.0
        )

        # Update summary
        metrics["summary"] = {
            "total_sessions": total_sessions,
            "total_steps": total_steps,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "overall_pass_rate": round(avg_pass_rate, 3),
            "avg_duration_s": round(avg_duration, 3),
            "avg_steps_per_session": round(avg_steps_per_session, 3),
            "last_updated": datetime.now().isoformat(),
        }

    def load_metrics(self) -> dict[str, Any]:
        """Load existing metrics from file"""
        if not self.metrics_file.exists():
            return {}

        try:
            with open(self.metrics_file, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_metrics(self, metrics: dict[str, Any]) -> None:
        """Save metrics to file"""
        ensure_parent_dir(self.metrics_file)
        with open(self.metrics_file, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics"""
        metrics = self.load_metrics()
        return metrics.get("summary", {})

    def get_recent_sessions(self, limit: int = 10) -> list:
        """Get recent sessions"""
        metrics = self.load_metrics()
        sessions = metrics.get("sessions", [])
        return sessions[-limit:] if sessions else []

    def get_action_stats(self) -> dict[str, dict[str, int]]:
        """Get statistics by action type"""
        metrics = self.load_metrics()
        sessions = metrics.get("sessions", [])

        action_stats = {}

        for session in sessions:
            steps_details = session.get("steps_details", [])
            for step in steps_details:
                action = step.get("action", "unknown")
                if action not in action_stats:
                    action_stats[action] = {"total": 0, "passed": 0, "failed": 0}

                action_stats[action]["total"] += 1
                if step.get("ok", False):
                    action_stats[action]["passed"] += 1
                else:
                    action_stats[action]["failed"] += 1

        return action_stats


# Global metrics instance
_global_metrics: AgentDevMetrics | None = None


def get_metrics() -> AgentDevMetrics:
    """Get global metrics instance"""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = AgentDevMetrics()
    return _global_metrics


def record_session(
    goal: str,
    total_steps: int,
    passed_steps: int,
    failed_steps: int,
    pass_rate: float,
    total_duration_s: float,
    steps_details: list | None = None,
) -> None:
    """Convenience function to record session metrics"""
    get_metrics().record_session(
        goal=goal,
        total_steps=total_steps,
        passed_steps=passed_steps,
        failed_steps=failed_steps,
        pass_rate=pass_rate,
        total_duration_s=total_duration_s,
        steps_details=steps_details,
    )


def get_summary() -> dict[str, Any]:
    """Convenience function to get summary statistics"""
    return get_metrics().get_summary()


def get_recent_sessions(limit: int = 10) -> list:
    """Convenience function to get recent sessions"""
    return get_metrics().get_recent_sessions(limit=limit)


def get_action_stats() -> dict[str, dict[str, int]]:
    """Convenience function to get action statistics"""
    return get_metrics().get_action_stats()
