"""
Meta-Learning API Router (Stage 2)

Provides endpoints for Meta-Learning features:
- Retention metrics
- Source trust scores
- Learning effectiveness analysis
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime

from backend.learning.document_usage_tracker import get_document_usage_tracker
from backend.learning.source_trust_calculator import get_source_trust_calculator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meta-learning", tags=["meta-learning"])


@router.get("/retention")
async def get_retention_metrics(days: int = Query(30, ge=1, le=365, description="Number of days to analyze")):
    """
    Get retention metrics per source
    
    Retention = (Documents used in responses) / (Total documents learned)
    
    Returns:
        Dictionary with retention metrics per source
    """
    try:
        tracker = get_document_usage_tracker()
        metrics = tracker.calculate_retention_metrics(days=days)
        
        return {
            "analysis_period_days": days,
            "timestamp": datetime.utcnow().isoformat(),
            "sources": metrics
        }
    except Exception as e:
        logger.error(f"Error getting retention metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get retention metrics: {str(e)}"
        )


@router.get("/source-trust")
async def get_source_trust_scores(days: int = Query(30, ge=1, le=365, description="Number of days to analyze")):
    """
    Get source trust scores based on retention
    
    Returns:
        Dictionary mapping source name to trust score (0.0-1.0)
    """
    try:
        calculator = get_source_trust_calculator()
        tracker = get_document_usage_tracker()
        
        # Get retention rates
        retention_rates = tracker.get_source_retention_rates(days=days)
        
        # Calculate trust scores
        trust_scores = {
            source: calculator.calculate_trust_score(retention_rate)
            for source, retention_rate in retention_rates.items()
        }
        
        return {
            "analysis_period_days": days,
            "timestamp": datetime.utcnow().isoformat(),
            "trust_scores": trust_scores,
            "retention_rates": retention_rates
        }
    except Exception as e:
        logger.error(f"Error getting source trust scores: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get source trust scores: {str(e)}"
        )


@router.post("/update-source-trust")
async def update_source_trust_scores(days: int = Query(30, ge=1, le=365, description="Number of days to analyze")):
    """
    Manually trigger source trust score update based on retention
    
    This will update ContentCurator.source_quality_scores automatically.
    
    Returns:
        Dictionary with updated trust scores
    """
    try:
        calculator = get_source_trust_calculator()
        updated_scores = calculator.update_source_trust_scores(days=days)
        
        return {
            "analysis_period_days": days,
            "timestamp": datetime.utcnow().isoformat(),
            "updated_sources": len(updated_scores),
            "trust_scores": updated_scores
        }
    except Exception as e:
        logger.error(f"Error updating source trust scores: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update source trust scores: {str(e)}"
        )


@router.get("/recommended-sources")
async def get_recommended_sources(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    min_retention: float = Query(0.20, ge=0.0, le=1.0, description="Minimum retention rate to recommend")
):
    """
    Get list of recommended sources based on retention
    
    Returns:
        List of source names with retention >= min_retention, sorted by retention (descending)
    """
    try:
        calculator = get_source_trust_calculator()
        recommended = calculator.get_recommended_sources(days=days, min_retention=min_retention)
        
        return {
            "analysis_period_days": days,
            "min_retention": min_retention,
            "timestamp": datetime.utcnow().isoformat(),
            "recommended_sources": recommended,
            "count": len(recommended)
        }
    except Exception as e:
        logger.error(f"Error getting recommended sources: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommended sources: {str(e)}"
        )

