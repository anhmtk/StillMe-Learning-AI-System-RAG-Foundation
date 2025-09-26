"""
PatternMatcher (skeleton)

Phase 1: Provide a minimal interface used by ReflexEngine.
- Actual algorithms (Aho-Corasick/regex, normalization) will be implemented in next phases.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class PatternMatcher:
    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self.config = config or {}

    def match(self, text: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Return a deterministic structure consumed by ReflexEngine.
        In Phase 1 (shadow), we simply return empty results.
        """
        return {
            "matches": [],  # type: List[Dict[str, Any]]
            "pattern_score": None,  # type: Optional[float]
        }


