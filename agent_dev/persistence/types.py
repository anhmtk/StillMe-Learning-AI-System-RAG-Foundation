#!/usr/bin/env python3
"""
AgentDev Persistence Types
==========================

TypedDict schemas for data transfer objects.
"""

from datetime import datetime
from typing import TypedDict


class FeedbackRow(TypedDict):
    """Feedback row type"""

    id: int
    user_id: str
    feedback: str
    session_id: str | None
    timestamp: datetime


class UserPrefRow(TypedDict):
    """User preference row type"""

    id: int
    user_id: str
    preference_key: str
    preference_value: str
    created_at: datetime
    updated_at: datetime


class RuleRow(TypedDict):
    """Rule row type"""

    id: int
    rule_name: str
    rule_definition: str
    priority: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LearnedSolutionRow(TypedDict):
    """Learned solution row type"""

    id: int
    error_type: str
    solution: str
    success_rate: float
    usage_count: int
    created_at: datetime
    last_used: datetime


class MetricRow(TypedDict):
    """Metric row type"""

    id: int
    metric_name: str
    metric_value: float
    metric_type: str
    timestamp: datetime
    context: str | None