"""
Type definitions for AgentDev persistence layer
==============================================

TypedDict definitions for database rows and data structures.
"""

from typing import TypedDict
from datetime import datetime


class FeedbackRow(TypedDict):
    """Feedback database row structure"""
    id: int
    user_id: str
    feedback: str
    session_id: str
    timestamp: datetime
    feedback_type: str  # "positive", "negative", "neutral"
    context: str  # JSON string of context data


class UserPrefRow(TypedDict):
    """User preferences database row structure"""
    id: int
    user_id: str
    preference_key: str
    preference_value: str
    created_at: datetime
    updated_at: datetime


class RuleRow(TypedDict):
    """Rule database row structure"""
    id: int
    rule_name: str
    rule_definition: str  # JSON string of rule logic
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime


class LearnedSolutionRow(TypedDict):
    """Learned solution database row structure"""
    id: int
    error_type: str
    solution: str
    success_rate: float
    usage_count: int
    created_at: datetime
    last_used: datetime


class MetricRow(TypedDict):
    """Metric database row structure"""
    id: int
    metric_name: str
    metric_value: float
    metric_type: str  # "counter", "timer", "gauge"
    timestamp: datetime
    context: str  # JSON string of context data
