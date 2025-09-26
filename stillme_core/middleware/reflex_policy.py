"""
Reflex Policy (skeleton)

Defines policy levels and a simple decision interface used by ReflexEngine.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple


class ReflexPolicy:
    def __init__(self, policy_level: str = "balanced") -> None:
        self.level = policy_level

    def decide(self, scores: Dict[str, Optional[float]]) -> Tuple[str, float]:
        """
        Decide what to do based on scores. Phase 1: always fallback.

        Returns:
            decision: str - one of {"fallback", "act"}
            confidence: float - confidence of decision
        """
        return "fallback", 0.0


