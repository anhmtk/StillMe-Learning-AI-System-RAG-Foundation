"""
Tier Models for Continuum Memory System
Pydantic models for tier-related APIs
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class TierStatsResponse(BaseModel):
    """Response model for tier statistics"""
    L0: int = Field(0, description="Number of items in L0 tier")
    L1: int = Field(0, description="Number of items in L1 tier")
    L2: int = Field(0, description="Number of items in L2 tier")
    L3: int = Field(0, description="Number of items in L3 tier")
    total: int = Field(0, description="Total number of items")
    promoted_7d: int = Field(0, description="Number of items promoted in last 7 days")
    demoted_7d: int = Field(0, description="Number of items demoted in last 7 days")
    
    class Config:
        schema_extra = {
            "example": {
                "L0": 150,
                "L1": 45,
                "L2": 12,
                "L3": 3,
                "total": 210,
                "promoted_7d": 8,
                "demoted_7d": 2
            }
        }


class TierAuditRecord(BaseModel):
    """Single audit record for promotion/demotion"""
    id: int
    item_id: str
    from_tier: Optional[str] = Field(None, description="Previous tier (L0/L1/L2/L3)")
    to_tier: str = Field(..., description="New tier (L0/L1/L2/L3)")
    reason: str = Field(..., description="Reason for promotion/demotion")
    surprise_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    retrieval_count_7d: Optional[int] = Field(None, ge=0)
    validator_overlap: Optional[float] = Field(None, ge=0.0, le=1.0)
    performed_by: str = Field("system", description="Who performed the action")
    created_at: str = Field(..., description="ISO timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "item_id": "knowledge_abc123",
                "from_tier": "L0",
                "to_tier": "L1",
                "reason": "surprise_score >= 0.65 and retrieval_count_7d increased",
                "surprise_score": 0.72,
                "retrieval_count_7d": 15,
                "validator_overlap": 0.85,
                "performed_by": "system",
                "created_at": "2025-01-08T10:30:00"
            }
        }


class TierAuditResponse(BaseModel):
    """Response model for tier audit log"""
    records: List[TierAuditRecord] = Field(default_factory=list)
    total: int = Field(0, description="Total number of records")
    
    class Config:
        schema_extra = {
            "example": {
                "records": [],
                "total": 0
            }
        }


class TierPromoteRequest(BaseModel):
    """Request model for promoting an item"""
    item_id: str = Field(..., description="Knowledge item ID to promote")
    reason: Optional[str] = Field(None, description="Optional reason for promotion")
    target_tier: Optional[str] = Field(None, description="Target tier (auto if not specified)")


class TierDemoteRequest(BaseModel):
    """Request model for demoting an item"""
    item_id: str = Field(..., description="Knowledge item ID to demote")
    reason: Optional[str] = Field(None, description="Optional reason for demotion")
    target_tier: Optional[str] = Field(None, description="Target tier (auto if not specified)")


class ForgettingMetric(BaseModel):
    """Single forgetting metric record"""
    id: int
    regression_item_id: str
    regression_query: str
    recall_at_k_before: float = Field(..., ge=0.0, le=1.0)
    recall_at_k_after: float = Field(..., ge=0.0, le=1.0)
    forgetting_delta: float = Field(..., description="recall_before - recall_after")
    faithfulness_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    overlap_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    evaluation_timestamp: str = Field(..., description="ISO timestamp")
    knowledge_update_timestamp: Optional[str] = Field(None, description="ISO timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "regression_item_id": "reg_001",
                "regression_query": "What is StillMe?",
                "recall_at_k_before": 0.95,
                "recall_at_k_after": 0.88,
                "forgetting_delta": 0.07,
                "faithfulness_score": 0.92,
                "overlap_score": 0.85,
                "evaluation_timestamp": "2025-01-08T10:30:00",
                "knowledge_update_timestamp": "2025-01-08T09:00:00"
            }
        }


class ForgettingTrendsResponse(BaseModel):
    """Response model for forgetting trends"""
    trends: List[Dict[str, Any]] = Field(default_factory=list, description="Trend data points")
    days: int = Field(30, description="Number of days analyzed")
    
    class Config:
        schema_extra = {
            "example": {
                "trends": [
                    {
                        "evaluation_timestamp": "2025-01-08T00:00:00",
                        "avg_forgetting_delta": 0.05,
                        "avg_recall_before": 0.92,
                        "avg_recall_after": 0.87,
                        "evaluation_count": 10
                    }
                ],
                "days": 30
            }
        }

