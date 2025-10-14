#!/usr/bin/env python3
"""
Scoring Engine - Đánh giá kết quả
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ScoreResult:
    """Score result"""

    status: str  # "pass", "warn", "fail"
    confidence: float  # 0.0 - 1.0
    details: dict[str, Any]


class ScoringEngine:
    """Scoring engine for evaluating results"""

    def score_result(self, result: dict[str, Any]) -> ScoreResult:
        """Score a result"""
        status = result.get("status", "unknown")
        metrics = result.get("metrics", {})

        # Simple scoring logic
        if status == "success":
            confidence = 0.9
            score_status = "pass"
        elif status == "failed":
            confidence = 0.2
            score_status = "fail"
        else:
            confidence = 0.5
            score_status = "warn"

        # Adjust confidence based on metrics
        if "accuracy" in metrics:
            accuracy = metrics["accuracy"]
            confidence = (confidence + accuracy) / 2

        return ScoreResult(
            status=score_status,
            confidence=max(0.0, min(1.0, confidence)),
            details={"original_status": status, "metrics": metrics},
        )