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
from backend.learning.learning_pattern_analyzer import get_learning_pattern_analyzer
from backend.learning.curriculum_generator import get_curriculum_generator
from backend.learning.curriculum_applier import get_curriculum_applier

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


# Phase 2: Curriculum Learning Endpoints

@router.get("/learning-effectiveness")
async def get_learning_effectiveness(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    top_n: int = Query(10, ge=1, le=50, description="Number of top topics to return")
):
    """
    Get learning effectiveness analysis
    
    Shows which topics provide the most validation improvement after learning.
    
    Returns:
        List of LearningEffectiveness objects, sorted by improvement (descending)
    """
    try:
        analyzer = get_learning_pattern_analyzer()
        effectiveness_list = analyzer.get_top_effective_topics(days=days, top_n=top_n)
        
        return {
            "analysis_period_days": days,
            "top_n": top_n,
            "timestamp": datetime.utcnow().isoformat(),
            "effectiveness": [
                {
                    "topic": e.topic,
                    "source": e.source,
                    "before_pass_rate": e.before_learning_pass_rate,
                    "after_pass_rate": e.after_learning_pass_rate,
                    "improvement": e.improvement,
                    "questions_affected": e.questions_affected,
                    "learned_timestamp": e.learned_timestamp
                }
                for e in effectiveness_list
            ],
            "count": len(effectiveness_list)
        }
    except Exception as e:
        logger.error(f"Error getting learning effectiveness: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get learning effectiveness: {str(e)}"
        )


@router.get("/curriculum")
async def get_curriculum(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    max_items: int = Query(20, ge=1, le=100, description="Maximum number of curriculum items")
):
    """
    Get optimal learning curriculum
    
    Returns prioritized list of topics to learn, based on:
    - Learning effectiveness (which topics provide most improvement)
    - Knowledge gaps (topics with high failure rates)
    - Source quality (retention-based trust scores)
    
    Returns:
        List of CurriculumItem objects, sorted by priority (descending)
    """
    try:
        generator = get_curriculum_generator()
        curriculum = generator.generate_curriculum(days=days, max_items=max_items)
        
        return {
            "analysis_period_days": days,
            "max_items": max_items,
            "timestamp": datetime.utcnow().isoformat(),
            "curriculum": [
                {
                    "topic": item.topic,
                    "source": item.source,
                    "priority": item.priority,
                    "reason": item.reason,
                    "estimated_improvement": item.estimated_improvement,
                    "knowledge_gap_urgency": item.knowledge_gap_urgency
                }
                for item in curriculum
            ],
            "summary": generator.get_curriculum_summary(days=days),
            "count": len(curriculum)
        }
    except Exception as e:
        logger.error(f"Error getting curriculum: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get curriculum: {str(e)}"
        )


@router.post("/apply-curriculum")
async def apply_curriculum(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    update_curator: bool = Query(True, description="Update ContentCurator priorities"),
    update_scheduler: bool = Query(True, description="Update LearningScheduler source priorities")
):
    """
    Apply curriculum to learning system
    
    This will:
    1. Update ContentCurator priorities based on curriculum
    2. Update LearningScheduler source priorities
    3. Adjust search keyword priorities
    
    Returns:
        Dictionary with application results
    """
    try:
        # Get curator instance
        try:
            import backend.api.main as main_module
            curator = main_module.content_curator
        except Exception:
            curator = None
        
        applier = get_curriculum_applier(curator=curator)
        results = applier.apply_curriculum(
            days=days,
            update_curator=update_curator,
            update_scheduler=update_scheduler
        )
        
        return results
    except Exception as e:
        logger.error(f"Error applying curriculum: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to apply curriculum: {str(e)}"
        )

