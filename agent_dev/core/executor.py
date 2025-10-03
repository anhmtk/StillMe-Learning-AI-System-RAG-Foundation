#!/usr/bin/env python3
"""
AgentDev Executor - Thực thi tasks
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ExecutionResult:
    """Execution result"""

    status: str
    output: str
    metrics: dict[str, Any]


class Executor:
    """Executor for running tasks"""

    def run(self, plan: Any) -> ExecutionResult:
        """Execute a plan"""
        # Handle both object and dict plans
        if isinstance(plan, dict):
            tasks = plan.get("tasks", [])  # type: ignore
        else:
            tasks = getattr(plan, "tasks", [])  # type: ignore

        if not tasks:
            return ExecutionResult(
                status="failed", output="No tasks to execute", metrics={}
            )

        # Simulate execution
        task = tasks[0]  # type: ignore
        if isinstance(task, dict):
            command = task.get("command", "")  # type: ignore
        else:
            command = getattr(task, "command", "")  # type: ignore

        if command:
            return ExecutionResult(
                status="success",
                output=f"Executed: {command}",
                metrics={"execution_time": 0.1},
            )
        else:
            return ExecutionResult(
                status="failed", output="Invalid task command", metrics={}
            )
