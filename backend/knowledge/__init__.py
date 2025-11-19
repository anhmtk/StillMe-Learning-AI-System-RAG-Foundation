"""
Knowledge module - Contains Factual Plausibility Scanner and Known Concept Index
"""

from .factual_scanner import (
    FactualPlausibilityScanner,
    KnownConceptIndex,
    FPSResult,
    scan_question,
    get_fps
)

__all__ = [
    "FactualPlausibilityScanner",
    "KnownConceptIndex",
    "FPSResult",
    "scan_question",
    "get_fps"
]

