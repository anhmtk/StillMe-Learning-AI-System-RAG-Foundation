"""Plan Types for StillMe Framework"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class PlanStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PlanPriority(Enum):
    LOW = 1
    MEDIUM = 5
    HIGH = 8
    CRITICAL = 10

@dataclass
class PlanStep:
    """Single step in a plan"""
    id: str
    action: str
    parameters: Dict[str, Any]
    expected_output: Optional[str] = None
    dependencies: List[str] = None
    status: PlanStatus = PlanStatus.PENDING
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class PlanItem:
    """Complete plan item"""
    id: str
    title: str
    description: str
    steps: List[PlanStep]
    priority: PlanPriority = PlanPriority.MEDIUM
    status: PlanStatus = PlanStatus.PENDING
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ExecutionResult:
    """Result of plan execution"""
    plan_id: str
    step_id: str
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
