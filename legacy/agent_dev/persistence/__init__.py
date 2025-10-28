#!/usr/bin/env python3
"""
AgentDev Persistence Package
============================

Database foundation for AgentDev with SQLite + SQLModel/SQLAlchemy.
Provides CRUD operations for feedback, user preferences, rules, learned solutions, and metrics.
"""

from .models import (
    FeedbackModel,
    LearnedSolutionModel,
    MetricModel,
    RuleModel,
    UserPreferencesModel,
)
from .repo import (
    FeedbackRepo,
    LearnedSolutionRepo,
    MetricRepo,
    RuleRepo,
    UserPreferencesRepo,
)
from .types import (
    FeedbackRow,
    LearnedSolutionRow,
    MetricRow,
    RuleRow,
    UserPrefRow,
)

__all__ = [
    # Models
    "FeedbackModel",
    "UserPreferencesModel",
    "RuleModel",
    "LearnedSolutionModel",
    "MetricModel",
    # Repositories
    "FeedbackRepo",
    "UserPreferencesRepo",
    "RuleRepo",
    "LearnedSolutionRepo",
    "MetricRepo",
    # Types
    "FeedbackRow",
    "UserPrefRow",
    "RuleRow",
    "LearnedSolutionRow",
    "MetricRow",
]
