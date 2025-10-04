"""
Learning Engine for AgentDev
===========================

Feedback analysis and behavior adjustment engine.
"""

from collections import Counter
from typing import Any

from sqlalchemy.orm import sessionmaker

from ..persistence.models import create_database_engine, create_memory_database
from ..persistence.repo import FeedbackRepo, LearnedSolutionRepo


class LearningEngine:
    """Learning engine for feedback analysis and suggestions"""

    def __init__(self, database_url: str = "sqlite:///:memory:"):
        """Initialize learning engine with database"""
        if database_url == "sqlite:///:memory:":
            engine = create_memory_database()
            self.SessionLocal = sessionmaker(bind=engine)
        else:
            engine = create_database_engine(database_url)
            self.SessionLocal = sessionmaker(bind=engine)
        self.feedback_patterns = self._load_feedback_patterns()
        self.suggestion_rules = self._load_suggestion_rules()

    def _load_feedback_patterns(self) -> dict[str, list[str]]:
        """Load common feedback patterns"""
        return {
            "performance": [
                "too slow",
                "slow",
                "performance",
                "fast",
                "speed",
                "latency",
                "timeout",
            ],
            "quality": [
                "quality",
                "good",
                "bad",
                "excellent",
                "poor",
                "accurate",
                "wrong",
                "correct",
            ],
            "usability": [
                "easy",
                "hard",
                "difficult",
                "simple",
                "complex",
                "user friendly",
                "confusing",
            ],
            "reliability": [
                "reliable",
                "stable",
                "crash",
                "error",
                "bug",
                "broken",
                "working",
            ],
            "security": [
                "secure",
                "safe",
                "vulnerable",
                "risk",
                "dangerous",
                "protected",
            ],
        }

    def _load_suggestion_rules(self) -> dict[str, str]:
        """Load suggestion rules based on feedback patterns"""
        return {
            "performance": "Consider optimizing performance: reduce timeout values, cache results, or parallelize operations",
            "quality": "Consider improving quality: add more validation, increase test coverage, or enhance error handling",
            "usability": "Consider improving usability: simplify interface, add help text, or improve user guidance",
            "reliability": "Consider improving reliability: add error recovery, increase monitoring, or enhance testing",
            "security": "Consider improving security: add input validation, implement access controls, or enhance encryption",
        }

    def record_feedback(
        self,
        user_id: str,
        feedback_text: str,
        session_id: str,
        context: str | None = None,
    ) -> bool:
        """Record user feedback and analyze patterns"""
        try:
            session = self.SessionLocal()
            try:
                feedback_repo = FeedbackRepo(session)

                # Analyze feedback sentiment and type
                # feedback_type = self._analyze_feedback_type(feedback_text)

                # Record feedback
                feedback_repo.create_feedback(
                    user_id=user_id, feedback=feedback_text, session_id=session_id
                )

                # Learn from feedback patterns
                self._learn_from_feedback(feedback_text, context)

                return True
            finally:
                session.close()
        except Exception:
            return False

    def _analyze_feedback_type(self, feedback_text: str) -> str:
        """Analyze feedback text to determine type"""
        feedback_lower = feedback_text.lower()

        # Check for positive indicators
        positive_words = [
            "good",
            "great",
            "excellent",
            "perfect",
            "amazing",
            "love",
            "like",
        ]
        if any(word in feedback_lower for word in positive_words):
            return "positive"

        # Check for negative indicators
        negative_words = [
            "bad",
            "terrible",
            "awful",
            "hate",
            "dislike",
            "wrong",
            "broken",
            "error",
        ]
        if any(word in feedback_lower for word in negative_words):
            return "negative"

        return "neutral"

    def _learn_from_feedback(
        self, feedback_text: str, context: str | None = None
    ) -> None:
        """Learn from feedback patterns and record solutions"""
        try:
            session = self.SessionLocal()
            try:
                solution_repo = LearnedSolutionRepo(session)

                # Analyze feedback for patterns
                patterns = self._extract_patterns(feedback_text)

                for _, category in patterns.items():
                    if category in self.suggestion_rules:
                        # Record learned solution
                        solution_repo.create_solution(
                            error_type=f"feedback_{category}",
                            solution=self.suggestion_rules[category],
                        )
            finally:
                session.close()
        except Exception:
            pass  # Fail silently for learning

    def _extract_patterns(self, feedback_text: str) -> dict[str, str]:
        """Extract patterns from feedback text"""
        feedback_lower = feedback_text.lower()
        patterns: dict[str, str] = {}

        for category, keywords in self.feedback_patterns.items():
            for keyword in keywords:
                if keyword in feedback_lower:
                    patterns[keyword] = category
                    break  # Only match first keyword per category

        return patterns

    def suggest_adjustments(
        self, user_id: str | None = None, session_id: str | None = None
    ) -> list[str]:
        """Suggest adjustments based on feedback analysis"""
        try:
            session = self.SessionLocal()
            try:
                feedback_repo = FeedbackRepo(session)
                solution_repo = LearnedSolutionRepo(session)

                # Get recent feedback
                if user_id:
                    recent_feedback = feedback_repo.get_feedback_by_user(
                        user_id, limit=10
                    )
                elif session_id:
                    recent_feedback = feedback_repo.get_feedback_by_session(session_id)
                else:
                    recent_feedback = feedback_repo.get_recent_feedback(hours=24)

                # Analyze feedback patterns
                suggestions: list[str] = []
                pattern_counts: Counter[str] = Counter()

                for feedback in recent_feedback:
                    patterns = self._extract_patterns(str(feedback.feedback))
                    for _, category in patterns.items():
                        pattern_counts[category] += 1

                # Generate suggestions based on most common patterns
                for category, _ in pattern_counts.most_common(3):
                    if category in self.suggestion_rules:
                        suggestions.append(self.suggestion_rules[category])

                # Add learned solutions
                learned_solutions = solution_repo.get_solutions_for_error(
                    "feedback_performance"
                )
                for solution in learned_solutions[:2]:  # Top 2 solutions
                    solution_text = str(solution.solution)
                    if solution_text not in suggestions:
                        suggestions.append(solution_text)

                return suggestions[:5]  # Return top 5 suggestions

            finally:
                session.close()
        except Exception:
            return []

    def get_feedback_summary(
        self, user_id: str | None = None, hours: int = 24
    ) -> dict[str, Any]:
        """Get feedback summary and statistics"""
        try:
            session = self.SessionLocal()
            try:
                feedback_repo = FeedbackRepo(session)

                # Get recent feedback
                if user_id:
                    recent_feedback = feedback_repo.get_feedback_by_user(
                        user_id, limit=100
                    )
                else:
                    recent_feedback = feedback_repo.get_recent_feedback(hours=hours)

                # Analyze feedback
                total_feedback = len(recent_feedback)
                positive_count = sum(
                    1 for f in recent_feedback if "positive" in str(f.feedback).lower()
                )
                negative_count = sum(
                    1 for f in recent_feedback if "negative" in str(f.feedback).lower()
                )
                neutral_count = total_feedback - positive_count - negative_count

                # Calculate sentiment score
                sentiment_score = 0.0
                if total_feedback > 0:
                    sentiment_score = (positive_count - negative_count) / total_feedback

                # Extract common patterns
                pattern_counts: Counter[str] = Counter()
                for feedback in recent_feedback:
                    patterns = self._extract_patterns(str(feedback.feedback))
                    for _, category in patterns.items():
                        pattern_counts[category] += 1

                return {
                    "total_feedback": total_feedback,
                    "positive_count": positive_count,
                    "negative_count": negative_count,
                    "neutral_count": neutral_count,
                    "sentiment_score": sentiment_score,
                    "common_patterns": dict(pattern_counts.most_common(5)),
                    "suggestions": self.suggest_adjustments(user_id=user_id),
                }

            finally:
                session.close()
        except Exception:
            return {
                "total_feedback": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "sentiment_score": 0.0,
                "common_patterns": {},
                "suggestions": [],
            }


def record_feedback(
    user_id: str,
    feedback_text: str,
    session_id: str,
    context: str | None = None,
    database_url: str = "sqlite:///:memory:",
) -> bool:
    """Record user feedback"""
    engine = LearningEngine(database_url)
    return engine.record_feedback(user_id, feedback_text, session_id, context)


def suggest_adjustments(
    user_id: str | None = None,
    session_id: str | None = None,
    database_url: str = "sqlite:///:memory:",
) -> list[str]:
    """Suggest adjustments based on feedback"""
    engine = LearningEngine(database_url)
    return engine.suggest_adjustments(user_id, session_id)
