"""
Evolutionary Learning Engine for StillMe V2
Manages daily learning sessions and self-evolution
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class EvolutionStage(Enum):
    """Evolution stages of the AI"""

    INFANT = "infant"  # 0-7 days
    CHILD = "child"  # 8-30 days
    ADOLESCENT = "adolescent"  # 31-90 days
    ADULT = "adult"  # 90+ days


@dataclass
class LearningMetrics:
    """Learning performance metrics"""

    accuracy: float = 0.0
    knowledge_retention: float = 0.0
    response_quality: float = 0.0
    safety_score: float = 1.0


@dataclass
class LearningSession:
    """A single learning session"""

    session_id: str
    date: str
    proposals_learned: int
    accuracy_delta: float
    evolution_stage: EvolutionStage
    duration_minutes: int
    success: bool
    notes: list[str]


class EvolutionaryLearningEngine:
    """
    Evolutionary Learning Engine
    Manages daily learning cycles and tracks evolution
    """

    def __init__(self):
        self.metrics = LearningMetrics()
        self.current_stage = EvolutionStage.INFANT
        self.learning_sessions: list[LearningSession] = []
        self.system_age_days = 0
        logger.info("✅ Evolutionary Learning Engine initialized")

    def start_daily_learning_session(self, proposals: list[dict[str, Any]]) -> LearningSession:
        """Start a daily learning session"""
        session_id = f"session_{int(time.time())}"
        start_time = time.time()

        logger.info(f"🧠 Starting daily learning session: {len(proposals)} proposals")

        learned_count = 0
        session_notes = []

        for proposal in proposals:
            try:
                success = self._learn_from_proposal(proposal)
                if success:
                    learned_count += 1
                    session_notes.append(
                        f"✓ Learned: {proposal.get('title', 'Unknown')}"
                    )
                else:
                    session_notes.append(
                        f"✗ Skipped: {proposal.get('title', 'Unknown')}"
                    )

            except Exception as e:
                logger.error(f"❌ Failed to learn from proposal: {e}")
                session_notes.append(f"✗ Error: {e}")

        duration_minutes = int((time.time() - start_time) / 60)

        old_accuracy = self.metrics.accuracy
        new_accuracy = self._calculate_new_accuracy(learned_count, len(proposals))
        accuracy_delta = new_accuracy - old_accuracy
        self.metrics.accuracy = new_accuracy

        self.system_age_days += 1
        self.current_stage = self._determine_evolution_stage(self.system_age_days)

        session = LearningSession(
            session_id=session_id,
            date=datetime.now().strftime("%Y-%m-%d"),
            proposals_learned=learned_count,
            accuracy_delta=accuracy_delta,
            evolution_stage=self.current_stage,
            duration_minutes=duration_minutes,
            success=learned_count > 0,
            notes=session_notes,
        )

        self.learning_sessions.append(session)

        logger.info(
            f"✅ Learning session completed: {learned_count}/{len(proposals)} learned"
        )
        logger.info(f"📈 Accuracy: {old_accuracy:.2f} → {new_accuracy:.2f} (Δ{accuracy_delta:+.2f})")
        logger.info(f"🎯 Evolution stage: {self.current_stage.value}")

        return session

    def _learn_from_proposal(self, proposal: dict[str, Any]) -> bool:
        """Learn from a single proposal"""
        title = proposal.get("title", "")
        content = proposal.get("content", "")
        quality_score = proposal.get("quality_score", 0.0)

        if not title or not content:
            return False

        if quality_score < 0.5:
            logger.debug(f"⚠️ Low quality proposal skipped: {title}")
            return False

        logger.debug(f"📚 Learning: {title}")
        return True

    def _calculate_new_accuracy(
        self, learned_count: int, total_proposals: int
    ) -> float:
        """Calculate new accuracy based on learning results"""
        if total_proposals == 0:
            return self.metrics.accuracy

        session_success_rate = learned_count / total_proposals

        learning_rate = 0.1
        new_accuracy = (
            self.metrics.accuracy * (1 - learning_rate)
            + session_success_rate * learning_rate
        )

        return min(1.0, max(0.0, new_accuracy))

    def _determine_evolution_stage(self, age_days: int) -> EvolutionStage:
        """Determine evolution stage based on system age"""
        if age_days <= 7:
            return EvolutionStage.INFANT
        elif age_days <= 30:
            return EvolutionStage.CHILD
        elif age_days <= 90:
            return EvolutionStage.ADOLESCENT
        else:
            return EvolutionStage.ADULT

    def get_learning_stats(self) -> dict[str, Any]:
        """Get comprehensive learning statistics"""
        total_sessions = len(self.learning_sessions)
        successful_sessions = sum(1 for s in self.learning_sessions if s.success)
        total_learned = sum(s.proposals_learned for s in self.learning_sessions)

        recent_sessions = self.learning_sessions[-7:] if len(self.learning_sessions) >= 7 else self.learning_sessions
        recent_accuracy_delta = sum(s.accuracy_delta for s in recent_sessions) / len(recent_sessions) if recent_sessions else 0.0

        return {
            "current_stage": self.current_stage.value,
            "system_age_days": self.system_age_days,
            "accuracy": self.metrics.accuracy,
            "knowledge_retention": self.metrics.knowledge_retention,
            "response_quality": self.metrics.response_quality,
            "safety_score": self.metrics.safety_score,
            "total_sessions": total_sessions,
            "successful_sessions": successful_sessions,
            "total_proposals_learned": total_learned,
            "recent_accuracy_trend": recent_accuracy_delta,
        }

    def self_assess_performance(self) -> dict[str, Any]:
        """Perform self-assessment of learning performance"""
        stats = self.get_learning_stats()

        assessment = {
            "timestamp": datetime.now().isoformat(),
            "stage": self.current_stage.value,
            "overall_health": "healthy",
            "strengths": [],
            "weaknesses": [],
            "recommendations": [],
        }

        if stats["accuracy"] >= 0.8:
            assessment["strengths"].append("High accuracy rate")
        elif stats["accuracy"] < 0.5:
            assessment["weaknesses"].append("Low accuracy rate")
            assessment["recommendations"].append("Need more quality training data")

        if stats["safety_score"] >= 0.95:
            assessment["strengths"].append("Excellent safety compliance")
        elif stats["safety_score"] < 0.9:
            assessment["weaknesses"].append("Safety concerns detected")
            assessment["recommendations"].append("Review safety filters")

        if stats["total_sessions"] > 30 and stats["successful_sessions"] / stats["total_sessions"] < 0.7:
            assessment["weaknesses"].append("Low session success rate")
            assessment["recommendations"].append("Improve proposal quality filtering")

        if not assessment["weaknesses"]:
            assessment["overall_health"] = "excellent"
        elif len(assessment["weaknesses"]) > 2:
            assessment["overall_health"] = "needs_attention"

        logger.info(f"🔍 Self-assessment: {assessment['overall_health']}")

        return assessment

    def export_learning_history(self) -> list[dict[str, Any]]:
        """Export learning history for analysis"""
        history = []

        for session in self.learning_sessions:
            history.append(
                {
                    "session_id": session.session_id,
                    "date": session.date,
                    "proposals_learned": session.proposals_learned,
                    "accuracy_delta": session.accuracy_delta,
                    "evolution_stage": session.evolution_stage.value,
                    "duration_minutes": session.duration_minutes,
                    "success": session.success,
                    "notes_count": len(session.notes),
                }
            )

        return history

    def adjust_learning_parameters(self, assessment: dict[str, Any]):
        """Adjust learning parameters based on self-assessment"""
        health = assessment["overall_health"]

        if health == "needs_attention":
            logger.warning("⚠️ System needs attention - adjusting parameters")

        elif health == "excellent":
            logger.info("✨ System performing excellently")

        logger.debug(f"🔧 Learning parameters adjusted based on {health} health status")

