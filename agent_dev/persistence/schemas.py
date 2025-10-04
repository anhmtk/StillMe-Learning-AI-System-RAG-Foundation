"""
Pydantic schemas for AgentDev persistence
=======================================

Input/Output schemas using Pydantic v2 for data validation.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class FeedbackIn(BaseModel):
    """Input schema for feedback"""

    user_id: str = Field(..., description="User ID")
    feedback: str = Field(..., description="Feedback text")
    session_id: str = Field(..., description="Session ID")
    feedback_type: str = Field(default="neutral", description="Type of feedback")
    context: str | None = Field(default=None, description="Context as JSON string")


class FeedbackOut(BaseModel):
    """Output schema for feedback"""

    id: int
    user_id: str
    feedback: str
    session_id: str
    timestamp: datetime
    feedback_type: str
    context: str | None = None


class UserPreferenceIn(BaseModel):
    """Input schema for user preference"""

    user_id: str = Field(..., description="User ID")
    preference_key: str = Field(..., description="Preference key")
    preference_value: str = Field(..., description="Preference value")


class UserPreferenceOut(BaseModel):
    """Output schema for user preference"""

    id: int
    user_id: str
    preference_key: str
    preference_value: str
    created_at: datetime
    updated_at: datetime


class RuleIn(BaseModel):
    """Input schema for rule"""

    rule_name: str = Field(..., description="Rule name")
    rule_definition: str = Field(..., description="Rule definition as JSON")
    priority: int = Field(default=0, description="Rule priority")
    is_active: bool = Field(default=True, description="Whether rule is active")


class RuleOut(BaseModel):
    """Output schema for rule"""

    id: int
    rule_name: str
    rule_definition: str
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LearnedSolutionIn(BaseModel):
    """Input schema for learned solution"""

    error_type: str = Field(..., description="Type of error")
    solution: str = Field(..., description="Solution text")
    success_rate: float = Field(default=1.0, description="Success rate")


class LearnedSolutionOut(BaseModel):
    """Output schema for learned solution"""

    id: int
    error_type: str
    solution: str
    success_rate: float
    usage_count: int
    created_at: datetime
    last_used: datetime


class MetricIn(BaseModel):
    """Input schema for metric"""

    metric_name: str = Field(..., description="Metric name")
    metric_value: float = Field(..., description="Metric value")
    metric_type: str = Field(..., description="Metric type: counter, timer, gauge")
    context: str | None = Field(default=None, description="Context as JSON string")


class MetricOut(BaseModel):
    """Output schema for metric"""

    id: int
    metric_name: str
    metric_value: float
    metric_type: str
    timestamp: datetime
    context: str | None = None


class MetricsSummary(BaseModel):
    """Summary schema for metrics"""

    metric_name: str
    count: int
    total: float
    min: float
    max: float
    avg: float
    metric_type: str
