"""
Feedback models for user ratings (like/dislike)
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class FeedbackRequest(BaseModel):
    """Request model for submitting feedback"""
    message_id: str = Field(..., description="Unique ID for the chat message")
    question: str = Field(..., description="Original user question")
    response: str = Field(..., description="StillMe's response")
    rating: int = Field(..., ge=-1, le=1, description="Rating: 1=like, -1=dislike, 0=neutral")
    feedback_text: Optional[str] = Field(None, description="Optional text feedback")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    metadata: Optional[dict] = Field(None, description="Additional metadata (confidence_score, validation_info, etc.)")


class FeedbackResponse(BaseModel):
    """Response model for feedback submission"""
    feedback_id: int
    message_id: str
    rating: int
    status: str = "success"
    message: str = "Feedback recorded successfully"


class FeedbackStats(BaseModel):
    """Statistics about feedback"""
    total_feedback: int
    likes: int
    dislikes: int
    neutral: int
    like_rate: float = Field(..., description="Percentage of likes (0-100)")
    recent_feedback: list = Field(default_factory=list, description="Recent feedback entries")


class FeedbackAnalysis(BaseModel):
    """Analysis of feedback patterns"""
    positive_patterns: list = Field(default_factory=list, description="Patterns in liked responses")
    negative_patterns: list = Field(default_factory=list, description="Patterns in disliked responses")
    recommendations: list = Field(default_factory=list, description="Recommendations for improvement")
    confidence_score_impact: Optional[dict] = Field(None, description="Impact of confidence scores on ratings")
    category_performance: Optional[dict] = Field(None, description="Performance by question category")

