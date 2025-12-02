"""
StillMe Core Self-Improvement System

Provides self-improvement mechanisms for the framework:
- Pattern analysis from validation metrics
- Improvement suggestions
- Feedback loop from validation → learning
- Automated improvement engine
"""

from .analyzer import SelfImprovementAnalyzer, get_self_improvement_analyzer
from .improvement_engine import ImprovementEngine, get_improvement_engine
from .feedback_loop import FeedbackLoop, get_feedback_loop

__all__ = [
    "SelfImprovementAnalyzer",
    "get_self_improvement_analyzer",
    "ImprovementEngine",
    "get_improvement_engine",
    "FeedbackLoop",
    "get_feedback_loop",
]

