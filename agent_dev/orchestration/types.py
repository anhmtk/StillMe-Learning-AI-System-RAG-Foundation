from datetime import datetime
from typing import Literal, NotRequired, TypedDict


class TaskSpec(TypedDict, total=False):
    id: str
    name: str
    description: str
    parameters: dict[str, str]
    status: Literal["pending", "running", "completed", "failed"]
    created_at: datetime
    updated_at: datetime

class ExecutionStep(TypedDict, total=False):
    step_id: str
    task_id: str
    action: str
    retries: int
    timeout: int

class ExecutionPlan(TypedDict, total=False):
    plan_id: str
    tasks: list[TaskSpec]
    steps: list[ExecutionStep]
    created_by: str
    created_at: datetime

class FlowContext(TypedDict, total=False):
    flow_id: str
    current_task: TaskSpec
    execution_plan: ExecutionPlan
    metadata: dict[str, str]
    state: Literal["initialized", "in_progress", "paused", "completed", "error"]

class DAGNode(TypedDict, total=False):
    node_id: str
    task: TaskSpec
    dependencies: list[str]
    status: Literal["pending", "running", "completed", "failed"]
    retries: int
    timeout: int

class DAGExecution(TypedDict, total=False):
    execution_id: str
    dag_id: str
    nodes: dict[str, DAGNode]
    status: Literal["initialized", "running", "completed", "failed"]
    start_time: datetime
    end_time: NotRequired[datetime]
    error_message: NotRequired[str]