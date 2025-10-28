"""
Reflex Policy with Multi-Score Decision Making

Features:
- Multi-score calculation: pattern, context, history, abuse scores
- Policy levels: strict, balanced, creative with different thresholds
- ENV override support via STILLME__REFLEX__* variables
- Weighted decision making with confidence scoring
"""

from __future__ import annotations

import os


class ReflexPolicy:
    def __init__(self, policy_level: str = "balanced") -> None:
        self.level = policy_level
        self.weights = self._load_weights()
        self.thresholds = self._load_thresholds()

    def _load_weights(self) -> dict[str, float]:
        """Load scoring weights with ENV override support"""
        default_weights = {"pattern": 0.4, "context": 0.3, "history": 0.2, "abuse": 0.1}

        # ENV override support
        for key in default_weights:
            env_key = f"STILLME__REFLEX__WEIGHT_{key.upper()}"
            if env_key in os.environ:
                try:
                    default_weights[key] = float(os.environ[env_key])
                except ValueError:
                    pass  # Keep default if invalid

        return default_weights

    def _load_thresholds(self) -> dict[str, dict[str, float]]:
        """Load policy thresholds for different modes"""
        thresholds = {
            "strict": {"allow_reflex": 0.8, "confidence_min": 0.7},
            "balanced": {"allow_reflex": 0.6, "confidence_min": 0.5},
            "creative": {"allow_reflex": 0.4, "confidence_min": 0.3},
        }

        # ENV override for current policy level
        if f"STILLME__REFLEX__THRESHOLD_{self.level.upper()}" in os.environ:
            try:
                threshold = float(
                    os.environ[f"STILLME__REFLEX__THRESHOLD_{self.level.upper()}"]
                )
                thresholds[self.level]["allow_reflex"] = threshold
            except ValueError:
                pass

        return thresholds

    def _calculate_context_score(self, context: dict[str, any] | None = None) -> float:
        """Calculate context score based on app state and input clarity"""
        if not context:
            return 0.5  # Neutral context

        score = 0.5  # Base score

        # App state factors
        if context.get("mode") == "strict":
            score += 0.2  # Higher confidence in strict mode
        elif context.get("mode") == "creative":
            score -= 0.1  # Lower confidence in creative mode

        # Input clarity factors
        input_text = context.get("text", "")
        if len(input_text) > 50:
            score += 0.1  # Longer input = more context
        elif len(input_text) < 10:
            score -= 0.1  # Very short input = less context

        # Session factors
        if context.get("session_active", False):
            score += 0.1  # Active session = more context

        return max(0.0, min(1.0, score))

    def _calculate_history_score(self, context: dict[str, any] | None = None) -> float:
        """Calculate history score based on frequency and recency"""
        # Placeholder implementation - would integrate with habit store
        if not context:
            return 0.0

        # Simulate history scoring
        frequency = context.get("cue_frequency", 0)
        recency = context.get("cue_recency_hours", 999)

        # Higher frequency = higher score
        freq_score = min(1.0, frequency / 10.0)

        # More recent = higher score
        recency_score = max(0.0, 1.0 - (recency / 168.0))  # Decay over a week

        return freq_score * 0.6 + recency_score * 0.4

    def _calculate_abuse_score(self, context: dict[str, any] | None = None) -> float:
        """Calculate abuse score - placeholder for SafetyGuard integration"""
        # Placeholder - would integrate with abuse detection
        return 0.0

    def decide(
        self, scores: dict[str, float | None], context: dict[str, any] | None = None
    ) -> tuple[str, float]:
        """
        Make decision based on multi-score analysis.

        Args:
            scores: Dict with pattern_score, context_score, history_score, abuse_score
            context: Additional context for scoring

        Returns:
            decision: str - "allow_reflex" or "fallback"
            confidence: float - confidence of decision (0-1)
        """
        # Calculate missing scores
        if scores.get("context_score") is None:
            scores["context_score"] = self._calculate_context_score(context)

        if scores.get("history_score") is None:
            scores["history_score"] = self._calculate_history_score(context)

        if scores.get("abuse_score") is None:
            scores["abuse_score"] = self._calculate_abuse_score(context)

        # Calculate weighted total score
        total_score = 0.0
        for score_type, weight in self.weights.items():
            score_key = f"{score_type}_score"
            score_value = scores.get(score_key, 0.0) or 0.0
            total_score += score_value * weight

        # Apply abuse penalty
        abuse_penalty = scores.get("abuse_score", 0.0) or 0.0
        total_score = max(0.0, total_score - abuse_penalty)

        # Get thresholds for current policy level
        policy_thresholds = self.thresholds.get(self.level, self.thresholds["balanced"])
        allow_threshold = policy_thresholds["allow_reflex"]
        confidence_min = policy_thresholds["confidence_min"]

        # Make decision
        if total_score >= allow_threshold:
            decision = "allow_reflex"
            confidence = min(1.0, total_score)
        else:
            decision = "fallback"
            confidence = max(0.0, 1.0 - total_score)

        # Ensure confidence meets minimum threshold
        if decision == "allow_reflex" and confidence < confidence_min:
            decision = "fallback"
            confidence = 1.0 - confidence

        return decision, round(confidence, 3)

    def get_breakdown(
        self, scores: dict[str, float | None], context: dict[str, any] | None = None
    ) -> dict[str, any]:
        """Get detailed breakdown of decision making process"""
        # Create a copy to avoid modifying original scores
        scores_copy = scores.copy()

        # Calculate missing scores
        if scores_copy.get("context_score") is None:
            scores_copy["context_score"] = self._calculate_context_score(context)

        if scores_copy.get("history_score") is None:
            scores_copy["history_score"] = self._calculate_history_score(context)

        if scores_copy.get("abuse_score") is None:
            scores_copy["abuse_score"] = self._calculate_abuse_score(context)

        # Calculate weighted contributions
        contributions = {}
        for score_type, weight in self.weights.items():
            score_key = f"{score_type}_score"
            score_value = scores_copy.get(score_key, 0.0) or 0.0
            contributions[score_type] = {
                "raw_score": score_value,
                "weight": weight,
                "contribution": score_value * weight,
            }

        # Calculate total
        total_score = sum(contrib["contribution"] for contrib in contributions.values())
        abuse_penalty = scores_copy.get("abuse_score", 0.0) or 0.0
        final_score = max(0.0, total_score - abuse_penalty)

        # Get thresholds for current policy level
        policy_thresholds = self.thresholds.get(self.level, self.thresholds["balanced"])
        allow_threshold = policy_thresholds["allow_reflex"]
        confidence_min = policy_thresholds["confidence_min"]

        # Make decision
        if final_score >= allow_threshold:
            decision = "allow_reflex"
            confidence = min(1.0, final_score)
        else:
            decision = "fallback"
            confidence = max(0.0, 1.0 - final_score)

        # Ensure confidence meets minimum threshold
        if decision == "allow_reflex" and confidence < confidence_min:
            decision = "fallback"
            confidence = 1.0 - confidence

        return {
            "scores": scores_copy,
            "weights": self.weights,
            "contributions": contributions,
            "total_score": total_score,
            "abuse_penalty": abuse_penalty,
            "final_score": final_score,
            "decision": decision,
            "confidence": round(confidence, 3),
            "policy_level": self.level,
            "thresholds": self.thresholds[self.level],
        }
