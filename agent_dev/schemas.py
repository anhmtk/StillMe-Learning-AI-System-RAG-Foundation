#!/usr/bin/env python3
"""
Pydantic schemas for AgentDev Sprint 1
Core data models for task execution pipeline
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class PolicyLevel(str, Enum):
    """Policy enforcement levels"""

    STRICT = "strict"
    BALANCED = "balanced"
    CREATIVE = "creative"


class ErrorType(str, Enum):
    """Error taxonomy for AgentDev"""

    USER_ERROR = "UserError"
    POLICY_VIOLATION = "PolicyViolation"
    ENV_ERROR = "EnvError"
    TRANSIENT = "Transient"
    PERMANENT = "Permanent"


class PolicyViolation(Exception):
    """Exception raised when policy violations are detected"""

    pass


class SafetyBudget(BaseModel):
    """Resource budgets for safety constraints"""

    cpu_ms: int = Field(
        default=1000, ge=0, description="CPU time limit in milliseconds"
    )
    mem_mb: int = Field(default=100, ge=0, description="Memory limit in MB")
    fs_quota_kb: int = Field(default=1024, ge=0, description="Filesystem quota in KB")
    timeout_s: int = Field(default=30, ge=1, description="Timeout in seconds")

    @field_validator("cpu_ms")
    @classmethod
    def cpu_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("CPU time must be positive")
        return v


class Policy(BaseModel):
    """Execution policy configuration"""

    level: PolicyLevel = Field(default=PolicyLevel.BALANCED)
    allow_network: bool = Field(default=False, description="Allow network access")
    allow_subprocess: bool = Field(
        default=False, description="Allow subprocess execution"
    )
    max_file_size_kb: int = Field(default=1024, description="Maximum file size in KB")
    allowed_extensions: list[str] = Field(
        default_factory=lambda: [".py", ".txt", ".md"]
    )

    @field_validator("max_file_size_kb")
    @classmethod
    def file_size_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Max file size must be positive")
        return v


class TaskSpec(BaseModel):
    """Task specification for AgentDev execution"""

    type: str = Field(description="Task type (e.g., 'file_edit')")
    inputs: dict[str, Any] = Field(description="Task input parameters")
    policy: Policy = Field(default_factory=Policy)
    budgets: SafetyBudget = Field(default_factory=SafetyBudget)
    timeouts: dict[str, int] = Field(default_factory=dict)
    options: dict[str, Any] = Field(default_factory=dict)

    @field_validator("type")
    @classmethod
    def type_must_be_valid(cls, v):
        allowed_types = ["file_edit", "code_analysis", "refactoring"]
        if v not in allowed_types:
            raise ValueError(f"Task type must be one of: {allowed_types}")
        return v


class Plan(BaseModel):
    """Execution plan for a task"""

    steps: list[dict[str, Any]] = Field(description="Execution steps")
    sandbox_path: str = Field(description="Sandbox directory path")
    checks: list[str] = Field(description="Validation checks to perform")
    estimated_duration_ms: int = Field(ge=0, description="Estimated duration in ms")

    @field_validator("sandbox_path")
    @classmethod
    def sandbox_path_must_be_absolute(cls, v):
        if not v.startswith("/") and not v.startswith("C:"):
            raise ValueError("Sandbox path must be absolute")
        return v


class ExecResult(BaseModel):
    """Result of task execution"""

    success: bool = Field(description="Whether execution succeeded")
    output: dict[str, Any] = Field(description="Execution output")
    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    duration_ms: int = Field(ge=0, description="Execution duration in ms")
    resources_used: dict[str, Any] = Field(default_factory=dict)


class ValidationReport(BaseModel):
    """Validation report for executed task"""

    valid: bool = Field(description="Whether validation passed")
    checks_passed: list[str] = Field(default_factory=list)
    checks_failed: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0, description="Validation confidence")

    @field_validator("confidence_score")
    @classmethod
    def confidence_must_be_valid(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v


class TaskResult(BaseModel):
    """Complete task result"""

    task_id: str = Field(description="Unique task identifier")
    spec: TaskSpec = Field(description="Original task specification")
    plan: Plan = Field(description="Execution plan")
    execution: ExecResult = Field(description="Execution result")
    validation: ValidationReport = Field(description="Validation report")
    trace_id: str = Field(description="Trace identifier for telemetry")
    timestamp: str = Field(description="ISO timestamp of completion")


class ErrorTaxonomy(BaseModel):
    """Error classification and handling"""

    error_type: ErrorType = Field(description="Error classification")
    message: str = Field(description="Error message")
    context: dict[str, Any] = Field(default_factory=dict)
    recoverable: bool = Field(description="Whether error is recoverable")
    suggested_action: str = Field(description="Suggested remediation")

    @field_validator("message")
    @classmethod
    def message_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Error message cannot be empty")
        return v.strip()


# ko dùng # type: ignore và ko dùng comment out để che giấu lỗi
