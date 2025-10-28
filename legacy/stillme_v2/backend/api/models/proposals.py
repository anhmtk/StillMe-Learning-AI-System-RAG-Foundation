"""
Proposals API models
"""

from enum import Enum

from pydantic import BaseModel, Field


class ProposalStatus(str, Enum):
    """Proposal status values"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    LEARNED = "learned"


class CreateProposalRequest(BaseModel):
    """Request to create a new proposal"""

    title: str = Field(..., min_length=5, max_length=500, description="Proposal title")
    content: str = Field(..., min_length=20, description="Proposal content")
    source_url: str | None = Field(None, description="Optional source URL")
    category: str = Field("general", description="Content category")


class UpdateProposalRequest(BaseModel):
    """Request to update proposal"""

    status: ProposalStatus | None = Field(None, description="New status")
    quality_score: float | None = Field(None, ge=0.0, le=1.0, description="Quality score")
    notes: str | None = Field(None, description="Additional notes")


class Proposal(BaseModel):
    """Proposal details"""

    proposal_id: str = Field(..., description="Unique proposal ID")
    title: str = Field(..., description="Proposal title")
    content: str = Field(..., description="Proposal content")
    source_url: str | None = Field(None, description="Source URL")
    category: str = Field(..., description="Content category")
    status: ProposalStatus = Field(..., description="Current status")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Quality score")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str | None = Field(None, description="Last update timestamp")

