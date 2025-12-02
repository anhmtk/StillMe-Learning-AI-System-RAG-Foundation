"""
StillMe Core Learning System

Provides abstract learning pipeline for continuous knowledge acquisition.

This module will be migrated from backend/learning/ and backend/services/
"""

from .base import LearningPipeline, LearningFetcher, LearningResult

__all__ = [
    "LearningPipeline",
    "LearningFetcher",
    "LearningResult",
]

