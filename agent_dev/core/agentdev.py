#!/usr/bin/env python3
"""
AgentDev Core - Main orchestrator with persistent capabilities
"""

from typing import TYPE_CHECKING
import os
from typing import Any

if TYPE_CHECKING:
    # from agent_dev.persistence.models import create_memory_database, get_session_factory
    pass


class AgentDev:
    """Main AgentDev orchestrator with persistent capabilities"""

    def __init__(self, db_path: str = "./data/agentdev.db") -> None:
        """Initialize AgentDev with persistent capabilities"""
        # Ensure data directory exists (skip for in-memory databases)
        if db_path != ":memory:" and not db_path.startswith("sqlite:///:memory:"):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize database
        # self.engine = create_memory_database(db_path)
        self.engine = None  # Placeholder
        # self.session_factory = get_session_factory(self.engine)
        self.session_factory = None  # Placeholder

        # Create session for repositories
        # self.session = self.session_factory()
        self.session = None  # Placeholder

        # Initialize repositories with session
        # self.feedback_repo = FeedbackRepo(self.session)
        # self.rule_repo = RuleRepo(self.session)
        # self.metric_repo = MetricRepo(self.session)
        self.feedback_repo = None  # Placeholder
        self.rule_repo = None  # Placeholder
        self.metric_repo = None  # Placeholder

        # Load initial rules if any
        self._load_initial_rules()

        # Initialize rule engine with database (after rules are loaded)
        # self.rule_engine = RuleEngine(self.rule_repo)
        self.rule_engine = None  # Placeholder

        # Initialize monitoring
        # self.monitor = MetricsCollector(self.metric_repo)
        self.monitor = None  # Placeholder

        # Initialize core components
        # self.planner = Planner()
        # self.executor = Executor()
        self.planner = None  # Placeholder
        self.executor = None  # Placeholder

        # Initialize security defense
        # self.security_defense = SecurityDefense()
        self.security_defense = None  # Placeholder

    def _load_initial_rules(self) -> None:
        """Load initial rules from database or create defaults"""
        # Skip if rule_repo is not available (placeholder mode)
        if self.rule_repo is None:
            return
        # Check if we have any rules in database
        existing_rules = self.rule_repo.get_active_rules()
        if not existing_rules:
            # Create default rules
            self._create_default_rules()

    def _create_default_rules(self) -> None:
        """Create default rules for AgentDev"""
        # Skip if rule_repo is not available (placeholder mode)
        if self.rule_repo is None:
            return
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

    def execute(self, task: str, mode: str = None) -> str:
        """Execute a task with rule compliance and monitoring"""
        # Check for empty task first
        if not task or not task.strip():
            return "failed"

        # Record task start
        try:
            self.monitor.record_event("tasks_started", 1.0)
        except Exception as e:
            # Monitor error - continue execution
            print(f"Warning: Failed to record task start: {e}")

        # Check security defense first
        try:
            security_result = self.security_defense.analyze_prompt(task)
            if not security_result["safe"]:
                self.monitor.record_event("tasks_blocked", 1.0, {"reason": "security"})
                return f"BLOCKED: {security_result['reason']}"
        except Exception as e:
            # Security defense error - block execution
            self.monitor.record_event("tasks_blocked", 1.0, {"error": str(e)})
            return f"BLOCKED: Security defense error - {str(e)}"

        # Check rule compliance
        context = {"task": task, "mode": mode, "tested": False, "cmd": task}
        try:
            compliance_results = self.rule_engine.check_compliance(
                "execute_task", context
            )
        except Exception as e:
            # Rule engine error - block execution
            self.monitor.record_event("tasks_blocked", 1.0, {"error": str(e)})
            return f"BLOCKED: Rule engine error - {str(e)}"

        if not compliance_results["compliant"]:
            # Rule violation - block execution
            self.monitor.record_event(
                "tasks_blocked",
                1.0,
                {
                    "rule": compliance_results["violated_rules"][0]
                    if compliance_results["violated_rules"]
                    else "unknown"
                },
            )
            return f"BLOCKED: Rule violation - {compliance_results['violated_rules']}"

        # Execute with monitoring
        with self.monitor.timer("task_execution"):
            try:
                # Create a simple plan
                plan = {"tasks": [{"command": task, "description": task}]}

                # Execute the plan
                result: Any = self.executor.run(plan)

                # Record success
                try:
                    self.monitor.record_event("tasks_pass", 1.0)
                except Exception as e:
                    print(f"Warning: Failed to record task pass: {e}")

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
                try:
                    self.monitor.record_event("tasks_fail", 1.0, {"error": str(e)})
                except Exception as monitor_e:
                    print(f"Warning: Failed to record task fail: {monitor_e}")
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
