"""
Learning API models
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class LearningProposal(BaseModel):
    """Learning proposal"""

    proposal_id: str = Field(..., description="Unique proposal ID")
    title: str = Field(..., description="Proposal title")
    content: str = Field(..., description="Proposal content")
    source: str = Field(..., description="Content source")
    category: str = Field(..., description="Content category")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score")
    status: str = Field(..., description="Proposal status: pending, approved, rejected, learned")
    created_at: str = Field(..., description="Creation timestamp")


class LearningSession(BaseModel):
    session_id: str
    date: str
    proposals_learned: int
    accuracy_delta: float
    evolution_stage: str
    duration_minutes: int
    success: bool


class LearningStats(BaseModel):
    current_stage: str
    system_age_days: int
    accuracy: float
    knowledge_retention: float
    response_quality: float
    safety_score: float
    total_sessions: int
    successful_sessions: int
    total_proposals_learned: int


# NEW MODELS FOR EVOLUTION API
class EvolutionStatus(BaseModel):
    current_stage: str
    system_age_days: int
    total_sessions: int
    success_rate: float
    recent_sessions: List[Dict[str, Any]]
    learning_trend: str
    overall_health: str


class DailySessionResult(BaseModel):
    session_id: str
    proposals_processed: int
    auto_approved: int
    needs_review: int
    success: bool
    timestamp: str
    evolution_stage: str


class ManualLearningRequest(BaseModel):
    proposal_ids: List[str] = Field(..., description="List of proposal IDs to learn")


class ManualLearningResponse(BaseModel):
    session_id: Optional[str] = None
    proposals_learned: int
    evolution_stage: str
    success: bool
    error_message: Optional[str] = None
    timestamp: str