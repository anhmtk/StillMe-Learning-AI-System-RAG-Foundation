#!/usr/bin/env python3
"""
Clarification Learning Module - Phase 2
Learns from user feedback and improves clarification patterns
"""

import json
import logging
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PatternStat:
    """Statistics for a clarification pattern"""

    success: int = 0
    failure: int = 0
    updated_at: float = time.time()
    total_attempts: int = 0

    @property
    def success_rate(self) -> float:
        if self.total_attempts == 0:
            return 0.0
        return self.success / self.total_attempts

    @property
    def confidence_score(self) -> float:
        """Calculate confidence score based on success rate and total attempts"""
        if self.total_attempts == 0:
            return 0.0
        # Higher confidence with more attempts and higher success rate
        base_confidence = self.success_rate
        attempt_bonus = min(0.2, self.total_attempts * 0.02)  # Max 20% bonus
        return min(1.0, base_confidence + attempt_bonus)


@dataclass
class ClarificationAttempt:
    """Record of a clarification attempt"""

    prompt: str
    question: str
    user_reply: str | None
    success: bool
    context: dict[str, Any]
    timestamp: float = time.time()
    trace_id: str | None = None


class ClarificationPatternStore:
    """
    Stores and manages clarification pattern statistics
    In-memory + file-backed persistence
    """

    def __init__(self, decay: float = 0.9, persistence_file: str | None = None):
        self.decay = decay
        self.store: dict[str, PatternStat] = defaultdict(PatternStat)
        self.persistence_file = persistence_file or "data/clarification_patterns.json"
        self._load_from_file()

    def _load_from_file(self):
        """Load patterns from persistence file"""
        try:
            persistence_path = Path(self.persistence_file)
            if persistence_path.exists():
                with open(persistence_path, encoding="utf-8") as f:
                    data = json.load(f)
                    for key, stat_data in data.items():
                        self.store[key] = PatternStat(**stat_data)
                logger.info(
                    f"Loaded {len(self.store)} patterns from {self.persistence_file}"
                )
        except Exception as e:
            logger.warning(f"Failed to load patterns from file: {e}")

    def _save_to_file(self):
        """Save patterns to persistence file"""
        try:
            persistence_path = Path(self.persistence_file)
            persistence_path.parent.mkdir(parents=True, exist_ok=True)

            data = {key: asdict(stat) for key, stat in self.store.items()}
            with open(persistence_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.store)} patterns to {self.persistence_file}")
        except Exception as e:
            logger.warning(f"Failed to save patterns to file: {e}")

    def update(self, key: str, *, success: bool):
        """Update pattern statistics with decay"""
        stat = self.store[key]

        # Apply decay to existing stats (only if there are multiple attempts)
        if stat.total_attempts > 1:
            stat.success = max(0, int(stat.success * self.decay))
            stat.failure = max(0, int(stat.failure * self.decay))

        # Add new result
        if success:
            stat.success += 1
        else:
            stat.failure += 1

        # Update total attempts
        stat.total_attempts = stat.success + stat.failure
        stat.updated_at = time.time()

        # Save periodically
        if stat.total_attempts % 10 == 0:
            self._save_to_file()

    def top_templates(self, domain: str, k: int = 3) -> list[dict[str, Any]]:
        """Get top performing templates for a domain"""
        # Filter keys by domain prefix "domain:template"
        domain_key = f"{domain}:"
        items = [(k, v) for k, v in self.store.items() if k.startswith(domain_key)]

        # Sort by confidence score
        items.sort(key=lambda kv: kv[1].confidence_score, reverse=True)

        return [
            {
                "template_key": k,
                "template": k.split(":", 1)[1] if ":" in k else k,
                "confidence": v.confidence_score,
                "success_rate": v.success_rate,
                "total_attempts": v.total_attempts,
            }
            for k, v in items[:k]
        ]

    def get_pattern_stats(self, key: str) -> PatternStat | None:
        """Get statistics for a specific pattern"""
        return self.store.get(key)

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get all pattern statistics"""
        return {
            key: {
                "success": stat.success,
                "failure": stat.failure,
                "success_rate": stat.success_rate,
                "confidence": stat.confidence_score,
                "total_attempts": stat.total_attempts,
                "updated_at": stat.updated_at,
            }
            for key, stat in self.store.items()
        }


class ClarificationLearner:
    """
    Learns from clarification feedback and improves patterns
    """

    def __init__(self, store: ClarificationPatternStore, memory=None):
        self.store = store
        self.memory = memory
        self.attempts: list[ClarificationAttempt] = []

    async def record_attempt(
        self,
        *,
        prompt: str,
        question: str,
        user_reply: str | None,
        success: bool,
        context: dict[str, Any],
        trace_id: str | None = None,
    ):
        """
        Record a clarification attempt and update patterns

        Args:
            prompt: Original user prompt
            question: Clarification question asked
            user_reply: User's response (None if skipped)
            success: Whether the clarification led to successful outcome
            context: Additional context (domain_hint, user_id, etc.)
            trace_id: Trace ID for observability
        """
        # Create attempt record
        attempt = ClarificationAttempt(
            prompt=prompt,
            question=question,
            user_reply=user_reply,
            success=success,
            context=context,
            trace_id=trace_id,
        )
        self.attempts.append(attempt)

        # Extract domain and create pattern key
        domain = context.get("domain_hint", "generic")
        template_key = f"{domain}:{question.strip().lower()}"

        # Update pattern statistics
        self.store.update(template_key, success=success)

        # Store in memory if available
        if self.memory:
            try:
                await self.memory.store_clarification(
                    prompt, question, user_reply, success, context
                )
            except Exception as e:
                logger.warning(f"Failed to store in memory: {e}")

        # Log the attempt
        logger.info(
            f"Recorded clarification attempt: {template_key}, success={success}, trace_id={trace_id}"
        )

    async def suggest_patterns(
        self, prompt: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Suggest clarification patterns based on learning

        Args:
            prompt: User prompt to clarify
            context: Context including domain_hint, history, etc.

        Returns:
            Dict with suggested template, confidence, and slots
        """
        domain = context.get("domain_hint", "generic")

        # Get top performing templates for this domain
        top_templates = self.store.top_templates(domain, k=1)

        if top_templates and top_templates[0]["confidence"] > 0.3:
            template_info = top_templates[0]
            return {
                "template": template_info["template"],
                "confidence": template_info["confidence"],
                "slots": {},
                "source": "learned",
                "success_rate": template_info["success_rate"],
            }

        # Fallback to generic template
        return {"template": None, "confidence": 0.0, "slots": {}, "source": "fallback"}

    def get_learning_stats(self) -> dict[str, Any]:
        """Get learning statistics"""
        total_attempts = len(self.attempts)
        successful_attempts = sum(1 for a in self.attempts if a.success)

        return {
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
            "success_rate": successful_attempts / total_attempts
            if total_attempts > 0
            else 0.0,
            "pattern_count": len(self.store.store),
            "recent_attempts": [
                {
                    "prompt": a.prompt[:50] + "..." if len(a.prompt) > 50 else a.prompt,
                    "question": a.question[:50] + "..."
                    if len(a.question) > 50
                    else a.question,
                    "success": a.success,
                    "timestamp": a.timestamp,
                }
                for a in self.attempts[-10:]  # Last 10 attempts
            ],
        }

    def clear_learning_data(self):
        """Clear all learning data (for testing)"""
        self.attempts.clear()
        self.store.store.clear()
        logger.info("Cleared all learning data")


# Example usage and testing
if __name__ == "__main__":
    # Test the learning system
    store = ClarificationPatternStore()
    learner = ClarificationLearner(store)

    # Simulate some learning
    import asyncio

    async def test_learning():
        # Record some attempts
        await learner.record_attempt(
            prompt="Write code for this",
            question="What exactly would you like me to write?",
            user_reply="A Python function to calculate factorial",
            success=True,
            context={"domain_hint": "programming", "user_id": "test_user"},
        )

        await learner.record_attempt(
            prompt="Build an app",
            question="What type of app would you like me to create?",
            user_reply="A web application",
            success=True,
            context={"domain_hint": "web", "user_id": "test_user"},
        )

        # Get suggestions
        suggestion = await learner.suggest_patterns(
            "Create something", {"domain_hint": "programming"}
        )
        print(f"Suggestion: {suggestion}")

        # Get stats
        stats = learner.get_learning_stats()
        print(f"Learning stats: {stats}")

    asyncio.run(test_learning())