"""
AgentDev Data Models
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class Job:
    id: str
    name: str
    description: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

@dataclass
class JobStep:
    id: str
    job_id: str
    name: str
    status: StepStatus
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

@dataclass
class Artifact:
    id: str
    job_id: str
    step_id: Optional[str]
    name: str
    path: str
    size: int
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class Checkpoint:
    id: str
    job_id: str
    step_id: Optional[str]
    name: str
    data: Dict[str, Any]
    created_at: datetime
    metadata: Dict[str, Any]
