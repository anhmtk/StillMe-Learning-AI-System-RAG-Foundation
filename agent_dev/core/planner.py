#!/usr/bin/env python3
"""
AgentDev Planner - Tạo execution plans
"""

from typing import TYPE_CHECKING
from dataclasses import dataclass
from typing import Any


@dataclass
class TaskSpec:
    """Task specification"""

    id: str
    name: str
    command: str
    parameters: dict[str, Any]


@dataclass
class ExecutionPlan:
    """Execution plan"""

    tasks: list[TaskSpec]
    goal: str


class Planner:
    """Planner for creating execution plans"""

    def create_plan(self, goal: str) -> ExecutionPlan:
        """Create execution plan from goal"""
        # Simple implementation for testing
        task = TaskSpec(
            id="task_1",
            name="simple_task",
            command="echo",
            parameters={"message": goal},
        )

        return ExecutionPlan(tasks=[task], goal=goal)