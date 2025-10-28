"""
Proposals API routes
"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database.schema import Proposal, get_db_session
from ...services.rss_pipeline import RSSLearningPipeline
from ..models.proposals import (
    CreateProposalRequest,
    Proposal as ProposalModel,
    ProposalStatus,
    UpdateProposalRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/proposals", tags=["proposals"])

rss_pipeline = RSSLearningPipeline()


@router.post("/", response_model=ProposalModel)
async def create_proposal(
    request: CreateProposalRequest,
    db: Session = Depends(get_db_session),
):
    """Create a new learning proposal"""
    try:
        proposal_id = f"prop_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        proposal = Proposal(
            proposal_id=proposal_id,
            title=request.title,
            content=request.content,
            source_url=request.source_url,
            category=request.category,
            status=ProposalStatus.PENDING.value,
            quality_score=0.0,
            relevance_score=0.0,
            created_at=datetime.utcnow(),
        )
        
        db.add(proposal)
        db.commit()
        db.refresh(proposal)
        
        logger.info(f"📝 Proposal created: {proposal_id}")
        
        return ProposalModel(
            proposal_id=proposal.proposal_id,
            title=proposal.title,
            content=proposal.content,
            source_url=proposal.source_url,
            category=proposal.category,
            status=ProposalStatus(proposal.status),
            quality_score=proposal.quality_score,
            relevance_score=proposal.relevance_score,
            created_at=proposal.created_at.isoformat(),
            updated_at=proposal.updated_at.isoformat() if proposal.updated_at else None,
        )

    except Exception as e:
        logger.error(f"❌ Create proposal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=list[ProposalModel])
async def get_proposals(
    status: ProposalStatus | None = None,
    category: str | None = None,
    limit: int = 50,
    db: Session = Depends(get_db_session),
):
    """Get proposals with optional filtering"""
    try:
        query = db.query(Proposal)
        
        if status:
            query = query.filter(Proposal.status == status.value)
        
        if category:
            query = query.filter(Proposal.category == category)
        
        proposals = query.order_by(Proposal.created_at.desc()).limit(limit).all()
        
        return [
            ProposalModel(
                proposal_id=p.proposal_id,
                title=p.title,
                content=p.content,
                source_url=p.source_url,
                category=p.category,
                status=ProposalStatus(p.status),
                quality_score=p.quality_score,
                relevance_score=p.relevance_score,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat() if p.updated_at else None,
            )
            for p in proposals
        ]

    except Exception as e:
        logger.error(f"❌ Get proposals error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{proposal_id}", response_model=ProposalModel)
async def get_proposal(
    proposal_id: str,
    db: Session = Depends(get_db_session),
):
    """Get a specific proposal"""
    try:
        proposal = db.query(Proposal).filter(Proposal.proposal_id == proposal_id).first()
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        return ProposalModel(
            proposal_id=proposal.proposal_id,
            title=proposal.title,
            content=proposal.content,
            source_url=proposal.source_url,
            category=proposal.category,
            status=ProposalStatus(proposal.status),
            quality_score=proposal.quality_score,
            relevance_score=proposal.relevance_score,
            created_at=proposal.created_at.isoformat(),
            updated_at=proposal.updated_at.isoformat() if proposal.updated_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get proposal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{proposal_id}", response_model=ProposalModel)
async def update_proposal(
    proposal_id: str,
    request: UpdateProposalRequest,
    db: Session = Depends(get_db_session),
):
    """Update a proposal"""
    try:
        proposal = db.query(Proposal).filter(Proposal.proposal_id == proposal_id).first()
        
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposal not found")
        
        if request.status:
            proposal.status = request.status.value
        
        if request.quality_score is not None:
            proposal.quality_score = request.quality_score
        
        proposal.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(proposal)
        
        logger.info(f"📝 Proposal updated: {proposal_id}")
        
        return ProposalModel(
            proposal_id=proposal.proposal_id,
            title=proposal.title,
            content=proposal.content,
            source_url=proposal.source_url,
            category=proposal.category,
            status=ProposalStatus(proposal.status),
            quality_score=proposal.quality_score,
            relevance_score=proposal.relevance_score,
            created_at=proposal.created_at.isoformat(),
            updated_at=proposal.updated_at.isoformat() if proposal.updated_at else None,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Update proposal error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-rss")
async def fetch_rss_content():
    """Fetch new content from RSS sources"""
    try:
        content = rss_pipeline.fetch_daily_content()
        proposals = rss_pipeline.generate_proposals(content)
        
        auto_approved, needs_review = rss_pipeline.filter_proposals_for_auto_approval(proposals)
        
        logger.info(f"📡 RSS fetch completed: {len(proposals)} proposals generated")
        
        return {
            "total_content": len(content),
            "proposals_generated": len(proposals),
            "auto_approved": len(auto_approved),
            "needs_review": len(needs_review),
        }

    except Exception as e:
        logger.error(f"❌ RSS fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
