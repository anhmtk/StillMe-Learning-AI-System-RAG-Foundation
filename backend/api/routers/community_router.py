"""
Community Router
Handles community proposals and voting
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ProposalRequest(BaseModel):
    """Request to create a proposal"""
    proposal_type: str = Field(..., description="Type of proposal (RSS Feed, Article, etc.)")
    source_url: str = Field(..., description="URL of the source")
    description: str = Field(..., description="Description of why this source is valuable")
    proposer_id: Optional[str] = Field(None, description="User identifier")


class VoteRequest(BaseModel):
    """Request to vote on a proposal"""
    proposal_id: str = Field(..., description="ID of the proposal")
    user_id: str = Field(..., description="User identifier")
    vote_type: str = Field(..., description="Vote type: 'for' or 'against'")


@router.post("/proposals")
async def create_proposal(request: Request, proposal_request: ProposalRequest):
    """Create a new community proposal"""
    try:
        from backend.services.community_proposals import get_community_proposals
        
        community = get_community_proposals()
        proposal_id = community.create_proposal(
            proposal_type=proposal_request.proposal_type,
            source_url=proposal_request.source_url,
            description=proposal_request.description,
            proposer_id=proposal_request.proposer_id
        )
        
        return {
            "proposal_id": proposal_id,
            "message": "Proposal created successfully! It will appear in the community voting section.",
            "status": "pending"
        }
    except Exception as e:
        logger.error(f"Error creating proposal: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating proposal: {str(e)}")


@router.post("/proposals/{proposal_id}/vote")
async def vote_on_proposal(proposal_id: str, vote_request: VoteRequest):
    """Vote on a proposal"""
    try:
        from backend.services.community_proposals import get_community_proposals
        
        if vote_request.proposal_id != proposal_id:
            raise HTTPException(status_code=400, detail="Proposal ID mismatch")
        
        community = get_community_proposals()
        result = community.vote_on_proposal(
            proposal_id=proposal_id,
            user_id=vote_request.user_id,
            vote_type=vote_request.vote_type
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error voting on proposal: {e}")
        raise HTTPException(status_code=500, detail=f"Error voting on proposal: {str(e)}")


@router.get("/proposals")
async def get_proposals(limit: int = 20):
    """Get pending proposals"""
    try:
        from backend.services.community_proposals import get_community_proposals
        
        community = get_community_proposals()
        proposals = community.get_pending_proposals(limit=limit)
        
        return {
            "proposals": proposals,
            "total": len(proposals)
        }
    except Exception as e:
        logger.error(f"Error getting proposals: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting proposals: {str(e)}")


@router.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str):
    """Get proposal by ID"""
    try:
        from backend.services.community_proposals import get_community_proposals
        
        community = get_community_proposals()
        proposal = community.get_proposal(proposal_id)
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        return proposal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting proposal: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting proposal: {str(e)}")


@router.get("/queue")
async def get_learning_queue():
    """Get learning queue: what's been learned and what's pending"""
    try:
        from backend.services.community_proposals import get_community_proposals
        
        community = get_community_proposals()
        queue = community.get_learning_queue()
        
        return queue
    except Exception as e:
        logger.error(f"Error getting learning queue: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting learning queue: {str(e)}")


@router.get("/stats")
async def get_daily_stats():
    """Get daily voting statistics"""
    try:
        from backend.services.community_proposals import get_community_proposals
        
        community = get_community_proposals()
        stats = community.get_daily_stats()
        
        return stats
    except Exception as e:
        logger.error(f"Error getting daily stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting daily stats: {str(e)}")

