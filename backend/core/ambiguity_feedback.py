"""
Ambiguity Feedback Mechanism for StillMe

Allows StillMe to learn from user feedback to improve ambiguity detection.
This enables personalization: StillMe adapts to each user's communication style.

Philosophy:
- StillMe learns from feedback to better understand each user
- This learning is TRANSPARENT - StillMe tells users it's learning
- No frequency limits - tư duy phi tuyến tính, không áp dụng giới hạn tuyến tính
- Goal: StillMe tự động cá nhân hóa theo user

Based on StillMe Manifesto Principle 6: "LOG EVERYTHING BECAUSE SECRETS CORRUPT TRUST"
- We are transparent about learning from feedback
- We log all feedback for auditability
- We don't hide that we're personalizing
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class AmbiguityFeedback:
    """
    Feedback from user about ambiguity detection.
    
    Examples:
    - User asked for clarification, but question was actually clear → negative feedback
    - StillMe didn't ask, but user had to clarify → positive feedback (should have asked)
    - StillMe asked and user confirmed it was needed → positive feedback
    """
    user_id: str
    original_query: str
    ambiguity_score: float
    ambiguity_level: str  # HIGH, MEDIUM, LOW
    stillme_asked_clarification: bool
    user_feedback: str  # "should_have_asked", "should_not_have_asked", "correct", "unclear"
    user_clarification: Optional[str] = None  # What user actually meant
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class AmbiguityFeedbackTracker:
    """
    Tracks feedback from users to improve ambiguity detection.
    
    Philosophy:
    - StillMe learns from each user's communication style
    - This enables personalization: StillMe adapts to user preferences
    - All learning is transparent - StillMe tells users it's learning
    """
    
    def __init__(self):
        self.feedback_history: Dict[str, List[AmbiguityFeedback]] = {}  # user_id -> list of feedback
        logger.info("AmbiguityFeedbackTracker initialized")
    
    def record_feedback(
        self,
        user_id: str,
        original_query: str,
        ambiguity_score: float,
        ambiguity_level: str,
        stillme_asked_clarification: bool,
        user_feedback: str,
        user_clarification: Optional[str] = None
    ) -> None:
        """
        Record user feedback about ambiguity detection.
        
        Args:
            user_id: User identifier
            original_query: Original ambiguous query
            ambiguity_score: Ambiguity score that was calculated
            ambiguity_level: Ambiguity level (HIGH, MEDIUM, LOW)
            stillme_asked_clarification: Whether StillMe asked for clarification
            user_feedback: User's feedback ("should_have_asked", "should_not_have_asked", "correct", "unclear")
            user_clarification: What user actually meant (if provided)
        """
        feedback = AmbiguityFeedback(
            user_id=user_id,
            original_query=original_query,
            ambiguity_score=ambiguity_score,
            ambiguity_level=ambiguity_level,
            stillme_asked_clarification=stillme_asked_clarification,
            user_feedback=user_feedback,
            user_clarification=user_clarification
        )
        
        if user_id not in self.feedback_history:
            self.feedback_history[user_id] = []
        
        self.feedback_history[user_id].append(feedback)
        logger.info(
            f"📝 Recorded ambiguity feedback from user {user_id}: "
            f"query='{original_query[:50]}...', feedback={user_feedback}, "
            f"score={ambiguity_score:.2f}, level={ambiguity_level}"
        )
    
    def get_user_preferences(self, user_id: str) -> Dict[str, any]:
        """
        Get user's preferences for ambiguity detection based on feedback history.
        
        Returns:
            Dictionary with user preferences:
            - preferred_threshold: Adjusted threshold for this user (if enough feedback)
            - ask_clarification_frequency: How often user wants clarification
            - communication_style: "direct", "detailed", "conversational"
        """
        if user_id not in self.feedback_history or len(self.feedback_history[user_id]) == 0:
            return {
                "preferred_threshold": None,  # Use default
                "ask_clarification_frequency": "default",
                "communication_style": "unknown",
                "feedback_count": 0
            }
        
        feedbacks = self.feedback_history[user_id]
        
        # Analyze feedback patterns
        should_have_asked_count = sum(
            1 for f in feedbacks if f.user_feedback == "should_have_asked"
        )
        should_not_have_asked_count = sum(
            1 for f in feedbacks if f.user_feedback == "should_not_have_asked"
        )
        correct_count = sum(
            1 for f in feedbacks if f.user_feedback == "correct"
        )
        
        total_feedback = len(feedbacks)
        
        # Calculate preferred threshold adjustment
        # If user often says "should have asked", lower threshold (ask more)
        # If user often says "should not have asked", raise threshold (ask less)
        threshold_adjustment = 0.0
        if total_feedback >= 3:  # Need at least 3 feedbacks to adjust
            should_ask_ratio = should_have_asked_count / total_feedback
            should_not_ask_ratio = should_not_have_asked_count / total_feedback
            
            # Adjust threshold: -0.1 for each 20% of "should have asked", +0.1 for each 20% of "should not have asked"
            threshold_adjustment = (should_not_ask_ratio - should_ask_ratio) * 0.5
        
        # Determine communication style
        if should_not_have_asked_count > should_have_asked_count:
            communication_style = "direct"  # User prefers direct answers
        elif should_have_asked_count > should_not_have_asked_count:
            communication_style = "detailed"  # User prefers detailed clarification
        else:
            communication_style = "conversational"  # Balanced
        
        return {
            "preferred_threshold": 0.7 + threshold_adjustment if total_feedback >= 3 else None,
            "ask_clarification_frequency": "more" if should_ask_ratio > 0.3 else ("less" if should_not_ask_ratio > 0.3 else "default"),
            "communication_style": communication_style,
            "feedback_count": total_feedback,
            "should_have_asked_ratio": should_have_asked_count / total_feedback if total_feedback > 0 else 0.0,
            "should_not_have_asked_ratio": should_not_have_asked_count / total_feedback if total_feedback > 0 else 0.0,
            "correct_ratio": correct_count / total_feedback if total_feedback > 0 else 0.0
        }
    
    def should_ask_for_this_user(
        self,
        user_id: str,
        ambiguity_score: float,
        default_threshold: float = 0.7
    ) -> Tuple[bool, float]:
        """
        Determine if should ask for clarification for this specific user.
        
        Uses user's feedback history to personalize threshold.
        
        Returns:
            Tuple of (should_ask, adjusted_threshold)
        """
        preferences = self.get_user_preferences(user_id)
        
        # Use user's preferred threshold if available, otherwise use default
        threshold = preferences.get("preferred_threshold") or default_threshold
        
        should_ask = ambiguity_score >= threshold
        
        if preferences["preferred_threshold"] is not None:
            logger.debug(
                f"🎯 Personalized threshold for user {user_id}: {threshold:.2f} "
                f"(default: {default_threshold:.2f}, feedback_count: {preferences['feedback_count']})"
            )
        
        return should_ask, threshold


# Global instance
_ambiguity_feedback_tracker: Optional[AmbiguityFeedbackTracker] = None


def get_ambiguity_feedback_tracker() -> AmbiguityFeedbackTracker:
    """Get global ambiguity feedback tracker instance"""
    global _ambiguity_feedback_tracker
    if _ambiguity_feedback_tracker is None:
        _ambiguity_feedback_tracker = AmbiguityFeedbackTracker()
    return _ambiguity_feedback_tracker

