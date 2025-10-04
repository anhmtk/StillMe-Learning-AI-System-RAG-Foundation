#!/usr/bin/env python3
"""
AgentDev Core - Main orchestrator with persistent capabilities
"""

import os
from typing import Any

from agent_dev.core.executor import Executor
from agent_dev.core.planner import Planner
from agent_dev.monitoring.metrics import MetricsCollector
from agent_dev.persistence.models import create_memory_database, get_session_factory
from agent_dev.persistence.repo import FeedbackRepo, MetricRepo, RuleRepo
from agent_dev.rules.engine import RuleEngine


class AgentDev:
    """Main AgentDev orchestrator with persistent capabilities"""

    def __init__(self, db_path: str = "./data/agentdev.db"):
        """Initialize AgentDev with persistent capabilities"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        self.engine = create_memory_database(db_path)
        self.session_factory = get_session_factory(self.engine)

        # Create session for repositories
        self.session = self.session_factory()

        # Initialize repositories with session
        self.feedback_repo = FeedbackRepo(self.session)
        self.rule_repo = RuleRepo(self.session)
        self.metric_repo = MetricRepo(self.session)

        # Load initial rules if any
        self._load_initial_rules()

        # Initialize rule engine with database (after rules are loaded)
        self.rule_engine = RuleEngine(self.rule_repo)

        # Initialize monitoring
        self.monitor = MetricsCollector(self.metric_repo)

        # Initialize core components
        self.planner = Planner()
        self.executor = Executor()

    def _load_initial_rules(self) -> None:
        """Load initial rules from database or create defaults"""
        # Check if we have any rules in database
        existing_rules = self.rule_repo.get_active_rules()
        if not existing_rules:
            # Create default rules
            self._create_default_rules()

    def _create_default_rules(self) -> None:
        """Create default rules for AgentDev"""
        # Rule 1: Test before claim
        self.rule_repo.create_rule(
            "test_before_claim",
            '{"description": "Must test before claiming task", "conditions": [{"field": "task", "operator": "eq", "value": ["claim"]}, {"field": "tested", "operator": "eq", "value": [false]}], "action": {"type": "block", "message": "Must test before claiming task", "severity": "high"}}',
            priority=10,
        )

        # Rule 2: Forbid dangerous shell commands
        self.rule_repo.create_rule(
            "forbid_dangerous_shell",
            '{"description": "Block dangerous shell commands", "conditions": [{"field": "cmd", "operator": "contains", "value": ["rm -rf"]}], "action": {"type": "block", "message": "Dangerous shell command detected", "severity": "critical"}}',
            priority=5,
        )

    def execute(self, task: str, mode: Any = None) -> str:
        """Execute a task with rule compliance and monitoring"""
        # Record task start
        self.monitor.record_event("tasks_started", 1.0)

        # Check rule compliance
        context = {"task": task, "mode": mode, "tested": False, "cmd": task}
        compliance_results = self.rule_engine.check_compliance("execute_task", context)

        if compliance_results:
            # Rule violation - block execution
            self.monitor.record_event(
                "tasks_blocked", 1.0, {"rule": compliance_results[0].rule_name}
            )
            return f"BLOCKED: {compliance_results[0].message}"

        # Execute with monitoring
        with self.monitor.timer("task_execution"):
            try:
                # Create a simple plan
                plan = {"tasks": [{"command": task, "description": task}]}

                # Execute the plan
                result: Any = self.executor.run(plan)

                # Record success
                self.monitor.record_event("tasks_pass", 1.0)

                # Return result
                if result and hasattr(result, "status"):
                    status = str(result.status)
                    # Map success to completed for consistency
                    if status == "success":
                        return "completed"
                    return status
                return "completed"

            except Exception as e:
                # Record failure
                self.monitor.record_event("tasks_fail", 1.0, {"error": str(e)})
                return f"error: {str(e)}"

    def receive_feedback(
        self, user_id: str, feedback: str, session_id: str | None = None
    ) -> str:
        """Receive and process user feedback"""
        # Validate input
        if not user_id or not feedback:
            self.monitor.record_event("feedback_error", 1.0, {"error": "Invalid input"})
            return "Error saving feedback: Invalid input"

        try:
            # Save feedback to database
            self.feedback_repo.create_feedback(
                user_id=user_id, feedback=feedback, session_id=session_id
            )

            # Record metrics
            self.monitor.record_event("feedback_received", 1.0, {"user_id": user_id})

            # Generate learning suggestion (MVP)
            suggestion = self._generate_learning_suggestion(feedback)

            return f"Feedback saved. Suggestion: {suggestion}"

        except Exception as e:
            self.monitor.record_event("feedback_error", 1.0, {"error": str(e)})
            return f"Error saving feedback: {str(e)}"

    def _generate_learning_suggestion(self, feedback: str) -> str:
        """Generate learning suggestion from feedback (MVP)"""
        # Simple keyword-based suggestion
        if "slow" in feedback.lower():
            return "Consider optimizing performance"
        elif "error" in feedback.lower():
            return "Review error handling"
        elif "security" in feedback.lower():
            return "Check security measures"
        else:
            return "Continue monitoring for patterns"

    def get_metrics_summary(self) -> dict[str, Any]:
        """Get comprehensive metrics summary"""
        return self.monitor.get_metrics_summary()

    def dump_metrics(self) -> dict[str, Any]:
        """Dump all metrics as JSON"""
        return self.monitor.dump_metrics()

    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.monitor.reset_metrics()
