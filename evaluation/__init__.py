"""
StillMe Evaluation Framework

This module provides comprehensive evaluation tools for benchmarking StillMe
against standard datasets (TruthfulQA, HaluEval) and comparing with baseline systems.
"""

from .base import BaseEvaluator, EvaluationResult
from .truthfulqa import TruthfulQAEvaluator
from .halu_eval import HaluEvalEvaluator
from .metrics import MetricsCalculator
from .comparison import SystemComparator
from .transparency_study import TransparencyStudy

__all__ = [
    "BaseEvaluator",
    "EvaluationResult",
    "TruthfulQAEvaluator",
    "HaluEvalEvaluator",
    "MetricsCalculator",
    "SystemComparator",
    "TransparencyStudy",
]

