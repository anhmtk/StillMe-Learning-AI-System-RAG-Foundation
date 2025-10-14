#!/usr/bin/env python3
"""
AgentDev Executor - Thực thi tasks
"""

from typing import TYPE_CHECKING
from dataclasses import dataclass
from typing import Any, cast


@dataclass
class ExecutionResult:
    """Execution result"""

    status: str
    output: str
    metrics: dict[str, Any]


class Executor:
    """Executor for running tasks"""

    def run(self, plan: dict[str, Any] | Any) -> ExecutionResult:
        """Execute a plan"""
        # Handle both object and dict plans with proper type checking
        tasks_raw: Any
        if isinstance(plan, dict):
            # Safe dict access with proper typing
            plan_dict = cast(dict[str, Any], plan)
            tasks_raw = plan_dict.get("tasks", [])
        else:
            tasks_raw = getattr(plan, "tasks", [])

        # Validate tasks is a list with proper type checking
        if not isinstance(tasks_raw, list):
            return ExecutionResult(
                status="failed", output="Tasks must be a list", metrics={}
            )

        # Safe cast after validation
        tasks = cast(list[Any], tasks_raw)
        if not tasks:
            return ExecutionResult(
                status="failed", output="No tasks to execute", metrics={}
            )

        # Simulate execution - safe access to first task
        task: Any = tasks[0]
        command: str = ""
        if isinstance(task, dict):
            # Safe dict access with proper typing
            task_dict = cast(dict[str, Any], task)
            command = str(task_dict.get("command", ""))
        else:
            command = str(getattr(task, "command", ""))

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
