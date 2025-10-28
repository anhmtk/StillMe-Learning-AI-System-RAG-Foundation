"""
Learning API routes
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...services.evolution_manager import EvolutionManager
from ...core.learning_engine import EvolutionaryLearningEngine
from ...services.rss_pipeline import RSSLearningPipeline, get_pipeline_instance
from ...services.knowledge_consolidation_service import knowledge_consolidation_service
from ...core.memory import advanced_memory_manager
from ...core.safety import ethical_safety_filter
from ...services.daily_stats_service import get_daily_stats_service
from ...database.schema import LearningSession, get_db_session
from ..models.learning import (
    LearningSession as LearningSessionModel, 
    LearningStats,
    EvolutionStatus,
    DailySessionResult,
    ManualLearningRequest,
    ManualLearningResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/learning", tags=["learning"])

# Global instances
learning_engine = EvolutionaryLearningEngine()
evolution_manager: Optional[EvolutionManager] = None


def get_evolution_manager(db: Session = Depends(get_db_session)) -> EvolutionManager:
    """
    Dependency injection for EvolutionManager
    
    Args:
        db: Database session
        
    Returns:
        EvolutionManager instance
    """
    global evolution_manager
    if evolution_manager is None:
        evolution_manager = EvolutionManager(db)
    return evolution_manager


@router.get("/stats", response_model=LearningStats)
async def get_learning_stats(
    evolution_mgr: EvolutionManager = Depends(get_evolution_manager)
) -> LearningStats:
    """
    Get comprehensive learning statistics
    
    Returns:
        LearningStats: Comprehensive learning statistics
        
    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        logger.info("📊 Retrieving learning statistics")
        stats = evolution_mgr.get_evolution_status()
        
        return LearningStats(
            current_stage=stats.get("current_stage", "unknown"),
            system_age_days=stats.get("system_age_days", 0),
            accuracy=stats.get("accuracy", 0.0),
            knowledge_retention=stats.get("knowledge_retention", 0.0),
            response_quality=stats.get("response_quality", 0.0),
            safety_score=stats.get("safety_score", 0.0),
            total_sessions=stats.get("total_sessions", 0),
            successful_sessions=stats.get("successful_sessions", 0),
            total_proposals_learned=stats.get("total_proposals_learned", 0),
        )

    except Exception as e:
        logger.error(f"❌ Get learning stats error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve learning statistics: {str(e)}"
        )


@router.post("/session/start")
async def start_learning_session(
    proposals: List[Dict[str, Any]],
    evolution_mgr: EvolutionManager = Depends(get_evolution_manager)
) -> Dict[str, Any]:
    """
    Start a new learning session with specified proposals
    
    Args:
        proposals: List of proposals to learn
        evolution_mgr: Evolution manager instance
        
    Returns:
        Dict with session start results
        
    Raises:
        HTTPException: If session start fails
    """
    try:
        logger.info(f"🚀 Starting learning session with {len(proposals)} proposals")
        
        # Use EvolutionManager for comprehensive session handling
        result = evolution_mgr.trigger_manual_learning(
            [f"manual_{i}" for i in range(len(proposals))]
        )
        
        logger.info(
            f"🧠 Learning session started successfully: {result.get('session_id')}, "
            f"Proposals learned: {result.get('proposals_learned')}"
        )
        
        return {
            "session_id": result.get("session_id"),
            "status": "started",
            "proposals_count": result.get("proposals_learned", 0),
            "evolution_stage": result.get("evolution_stage"),
            "success": result.get("success", False),
            "timestamp": result.get("timestamp")
        }

    except Exception as e:
        logger.error(f"❌ Start learning session error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to start learning session: {str(e)}"
        )


@router.get("/sessions")
async def get_learning_sessions(
    limit: int = Query(10, ge=1, le=100, description="Number of sessions to retrieve"),
    days: int = Query(7, ge=1, le=365, description="Number of days of history"),
    evolution_mgr: EvolutionManager = Depends(get_evolution_manager)
) -> List[LearningSessionModel]:
    """
    Get recent learning sessions with pagination
    
    Args:
        limit: Maximum number of sessions to return
        days: Number of days of history to retrieve
        evolution_mgr: Evolution manager instance
        
    Returns:
        List of learning sessions
        
    Raises:
        HTTPException: If session retrieval fails
    """
    try:
        logger.info(f"📋 Retrieving last {limit} learning sessions from {days} days")
        
        # Use EvolutionManager to get learning history
        history = evolution_mgr.get_learning_history(days=days)
        
        # Convert to response model and apply limit
        sessions = [
            LearningSessionModel(
                session_id=session["session_id"],
                date=session["date"],
                proposals_learned=session["proposals_learned"],
                accuracy_delta=session.get("accuracy_delta", 0.0),
                evolution_stage=session["evolution_stage"],
                duration_minutes=session.get("duration_minutes", 0),
                success=session["success"],
            )
            for session in history[:limit]
        ]
        
        logger.info(f"✅ Retrieved {len(sessions)} learning sessions")
        return sessions

    except Exception as e:
        logger.error(f"❌ Get learning sessions error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve learning sessions: {str(e)}"
        )


@router.post("/assess")
async def self_assess(
    evolution_mgr: EvolutionManager = Depends(get_evolution_manager)
) -> Dict[str, Any]:
    """
    Perform comprehensive self-assessment
    
    Returns:
        Dict with assessment results
        
    Raises:
        HTTPException: If assessment fails
    """
    try:
        logger.info("🔍 Performing self-assessment")
        
        # Get current status for assessment context
        status = evolution_mgr.get_evolution_status()
        
        # Use the learning engine from evolution manager for consistency
        assessment = evolution_mgr.learning_engine.self_assess_performance()
        
        # Enhance assessment with evolution metrics
        enhanced_assessment = {
            **assessment,
            "evolution_stage": status.get("current_stage", "unknown"),
            "total_sessions": status.get("total_sessions", 0),
            "success_rate": status.get("success_rate", 0.0),
            "recent_performance": status.get("recent_sessions", [])
        }
        
        logger.info(f"✅ Self-assessment completed: {enhanced_assessment['overall_health']}")
        
        return enhanced_assessment

    except Exception as e:
        logger.error(f"❌ Self-assessment error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Self-assessment failed: {str(e)}"
        )


# =============================================================================
# NEW EVOLUTION ROUTES
# =============================================================================

@router.get("/evolution/status", response_model=EvolutionStatus)
async def get_evolution_status(
    evolution_mgr: EvolutionManager = Depends(get_evolution_manager)
) -> EvolutionStatus:
    """
    Get comprehensive evolution status
    
    Returns:
        EvolutionStatus: Current evolution status and metrics
        
    Raises:
        HTTPException: If status retrieval fails
    """
    try:
        logger.info("🔄 Retrieving evolution status")
        status = evolution_mgr.get_evolution_status()
        
        return EvolutionStatus(
            current_stage=status.get("current_stage", "unknown"),
            system_age_days=status.get("system_age_days", 0),
            total_sessions=status.get("total_sessions", 0),
            success_rate=status.get("success_rate", 0.0),
            recent_sessions=status.get("recent_sessions", []),
            learning_trend=status.get("learning_trend", "unknown"),
            overall_health=status.get("overall_health", "unknown")
        )

    except Exception as e:
        logger.error(f"❌ Get evolution status error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve evolution status: {str(e)}"
        )


@router.post("/evolution/run-session", response_model=DailySessionResult)
async def run_daily_learning_session(
    evolution_mgr: EvolutionManager = Depends(get_evolution_manager)
) -> DailySessionResult:
    """
    Run complete daily learning session
    
    Returns:
        DailySessionResult: Results of the daily learning session
        
    Raises:
        HTTPException: If session execution fails
    """
    try:
        logger.info("🚀 Starting automated daily learning session")
        
        result = evolution_mgr.run_daily_learning_session()
        
        logger.info(
            f"✅ Daily session completed: "
            f"Session: {result['session'].session_id}, "
            f"Auto-approved: {result['auto_approved']}, "
            f"Needs review: {result['needs_review']}"
        )
        
        return DailySessionResult(
            session_id=result["session"].session_id,
            proposals_processed=result["proposals_processed"],
            auto_approved=result["auto_approved"],
            needs_review=result["needs_review"],
            success=result.get("success", True),
            timestamp=result.get("timestamp", datetime.now().isoformat()),
            evolution_stage=result["session"].evolution_stage.value
        )

    except Exception as e:
        logger.error(f"❌ Daily learning session error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Daily learning session failed: {str(e)}"
        )


@router.get("/evolution/history")
async def get_evolution_history(
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    evolution_mgr: EvolutionManager = Depends(get_evolution_manager)
) -> List[Dict[str, Any]]:
    """
    Get evolution history for specified period
    
    Args:
        days: Number of days of history to retrieve
        evolution_mgr: Evolution manager instance
        
    Returns:
        List of evolution history records
        
    Raises:
        HTTPException: If history retrieval fails
    """
    try:
        logger.info(f"📈 Retrieving evolution history for last {days} days")
        
        history = evolution_mgr.get_learning_history(days=days)
        
        logger.info(f"✅ Retrieved {len(history)} evolution history records")
        return history

    except Exception as e:
        logger.error(f"❌ Get evolution history error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve evolution history: {str(e)}"
        )


@router.get("/evolution/metrics")
async def get_evolution_metrics(
    evolution_mgr: EvolutionManager = Depends(get_evolution_manager)
) -> Dict[str, Any]:
    """
    Get comprehensive evolution metrics
    
    Returns:
        Dict with comprehensive evolution metrics
        
    Raises:
        HTTPException: If metrics retrieval fails
    """
    try:
        logger.info("📊 Retrieving comprehensive evolution metrics")
        
        metrics = evolution_mgr.get_evolution_metrics()
        
        logger.info("✅ Evolution metrics retrieved successfully")
        return metrics

    except Exception as e:
        logger.error(f"❌ Get evolution metrics error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve evolution metrics: {str(e)}"
        )


@router.post("/evolution/manual-learning", response_model=ManualLearningResponse)
async def trigger_manual_learning(
    request: ManualLearningRequest,
    evolution_mgr: EvolutionManager = Depends(get_evolution_manager)
) -> ManualLearningResponse:
    """
    Trigger manual learning for specific proposals
    
    Args:
        request: Manual learning request with proposal IDs
        evolution_mgr: Evolution manager instance
        
    Returns:
        ManualLearningResponse: Results of manual learning
        
    Raises:
        HTTPException: If manual learning fails
    """
    try:
        logger.info(f"🎯 Triggering manual learning for {len(request.proposal_ids)} proposals")
        
        result = evolution_mgr.trigger_manual_learning(request.proposal_ids)
        
        if result.get("success"):
            logger.info(
                f"✅ Manual learning completed: "
                f"Session: {result.get('session_id')}, "
                f"Proposals: {result.get('proposals_learned')}"
            )
        else:
            logger.warning(f"⚠️ Manual learning completed with issues: {result.get('error')}")
        
        return ManualLearningResponse(
            session_id=result.get("session_id"),
            proposals_learned=result.get("proposals_learned", 0),
            evolution_stage=result.get("evolution_stage", "unknown"),
            success=result.get("success", False),
            error_message=result.get("error"),
            timestamp=result.get("timestamp", datetime.now().isoformat())
        )

    except Exception as e:
        logger.error(f"❌ Manual learning error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Manual learning failed: {str(e)}"
        )


@router.get("/evolution/pending-review")
async def get_pending_review_proposals(
    evolution_mgr: EvolutionManager = Depends(get_evolution_manager)
) -> List[Dict[str, Any]]:
    """
    Get proposals pending manual review
    
    Returns:
        List of proposals requiring manual review
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info("📝 Retrieving pending review proposals")
        
        proposals = evolution_mgr.get_pending_review_proposals()
        
        logger.info(f"✅ Retrieved {len(proposals)} pending review proposals")
        return proposals

    except Exception as e:
        logger.error(f"❌ Get pending review proposals error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve pending review proposals: {str(e)}"
        )


@router.get("/rss/pipeline-stats")
async def get_rss_pipeline_stats() -> Dict[str, Any]:
    """
    Get RSS pipeline statistics including Public APIs
    
    Returns:
        Dict with RSS pipeline statistics
        
    Raises:
        HTTPException: If stats retrieval fails
    """
    try:
        logger.info("📊 Retrieving RSS pipeline statistics")
        
        pipeline = get_pipeline_instance()
        stats = pipeline.get_pipeline_stats()
        
        logger.info("✅ RSS pipeline stats retrieved successfully")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Get RSS pipeline stats error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to retrieve RSS pipeline stats: {str(e)}"
        )


@router.get("/rss/fetched-content")
async def get_fetched_content(
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    category: Optional[str] = Query(None, description="Filter by category")
) -> Dict[str, Any]:
    """
    Get recently fetched content items
    
    Args:
        limit: Maximum number of items to return
        category: Optional category filter
        
    Returns:
        Dict with fetched content items
        
    Raises:
        HTTPException: If content retrieval fails
    """
    try:
        logger.info(f"📰 Retrieving fetched content (limit: {limit}, category: {category})")
        
        pipeline = get_pipeline_instance()
        content_items = pipeline.fetched_content
        
        # Filter by category if specified
        if category:
            content_items = [item for item in content_items if item.get("source_category", "").lower() == category.lower()]
        
        # Sort by creation time (newest first) and limit
        content_items = sorted(content_items, key=lambda x: x.get("created_at", ""), reverse=True)[:limit]
        
        # Format for display
        formatted_items = []
        for item in content_items:
            formatted_items.append({
                "title": item.get("title", "No title"),
                "content_preview": item.get("content", "")[:200] + "..." if len(item.get("content", "")) > 200 else item.get("content", ""),
                "source_name": item.get("source_name", "Unknown"),
                "source_category": item.get("source_category", "general"),
                "created_at": item.get("created_at", ""),
                "content_hash": item.get("content_hash", "")[:12] + "..." if item.get("content_hash") else ""
            })
        
        logger.info(f"✅ Retrieved {len(formatted_items)} fetched content items")
        return {
            "total_items": len(formatted_items),
            "items": formatted_items,
            "filtered_by_category": category
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get fetched content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proposals/learned")
async def get_learned_proposals(
    limit: int = Query(20, ge=1, le=100, description="Number of proposals to return"),
    status: Optional[str] = Query(None, description="Filter by status (approved/pending)")
) -> Dict[str, Any]:
    """
    Get learned proposals
    
    Args:
        limit: Maximum number of proposals to return
        status: Optional status filter
        
    Returns:
        Dict with learned proposals
        
    Raises:
        HTTPException: If proposals retrieval fails
    """
    try:
        logger.info(f"📚 Retrieving learned proposals (limit: {limit}, status: {status})")
        
        pipeline = get_pipeline_instance()
        proposals = pipeline.proposals
        
        # Filter by status if specified
        if status:
            proposals = [prop for prop in proposals if prop.status.lower() == status.lower()]
        
        # Sort by creation time (newest first) and limit
        proposals = sorted(proposals, key=lambda x: x.created_at, reverse=True)[:limit]
        
        # Format for display
        formatted_proposals = []
        for proposal in proposals:
            formatted_proposals.append({
                "proposal_id": proposal.proposal_id,
                "title": proposal.title,
                "content_preview": proposal.content[:200] + "..." if len(proposal.content) > 200 else proposal.content,
                "source_name": proposal.source_name,
                "category": proposal.category,
                "quality_score": proposal.quality_score,
                "relevance_score": proposal.relevance_score,
                "novelty_score": proposal.novelty_score,
                "status": proposal.status,
                "created_at": proposal.created_at,
                "source_url": proposal.source_url
            })
        
        logger.info(f"✅ Retrieved {len(formatted_proposals)} learned proposals")
        return {
            "total_proposals": len(formatted_proposals),
            "proposals": formatted_proposals,
            "filtered_by_status": status
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get learned proposals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Historical Learning Analytics endpoints
@router.get("/analytics/historical")
async def get_historical_stats(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get historical learning statistics for a date range
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        db: Database session
        
    Returns:
        Dict with historical statistics
        
    Raises:
        HTTPException: If stats retrieval fails
    """
    try:
        logger.info(f"📊 Retrieving historical stats from {start_date} to {end_date}")
        
        stats_service = get_daily_stats_service(db)
        historical_stats = stats_service.get_historical_stats(start_date, end_date)
        
        logger.info(f"✅ Retrieved {len(historical_stats)} historical records")
        return {
            "period": f"{start_date} to {end_date}",
            "total_days": len(historical_stats),
            "stats": historical_stats
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get historical stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/comparison")
async def get_comparison_stats(
    current_date: str = Query(..., description="Current date (YYYY-MM-DD)"),
    compare_date: str = Query(..., description="Compare date (YYYY-MM-DD)"),
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get comparison between two dates
    
    Args:
        current_date: Current date in YYYY-MM-DD format
        compare_date: Date to compare against in YYYY-MM-DD format
        db: Database session
        
    Returns:
        Dict with comparison data
        
    Raises:
        HTTPException: If comparison fails
    """
    try:
        logger.info(f"📈 Comparing {current_date} vs {compare_date}")
        
        stats_service = get_daily_stats_service(db)
        comparison = stats_service.get_comparison_stats(current_date, compare_date)
        
        logger.info("✅ Generated comparison stats")
        return comparison
        
    except Exception as e:
        logger.error(f"❌ Failed to get comparison stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/trends")
async def get_learning_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """
    Get learning trends over the last N days
    
    Args:
        days: Number of days to analyze (1-365)
        db: Database session
        
    Returns:
        Dict with learning trends
        
    Raises:
        HTTPException: If trends analysis fails
    """
    try:
        logger.info(f"📊 Analyzing learning trends for {days} days")
        
        stats_service = get_daily_stats_service(db)
        trends = stats_service.get_learning_trends(days)
        
        logger.info("✅ Generated learning trends")
        return trends
        
    except Exception as e:
        logger.error(f"❌ Failed to get learning trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Ethical Safety Filter endpoints
@router.get("/ethics/stats")
async def get_ethical_stats():
    """Get ethical safety filter statistics"""
    try:
        stats = ethical_safety_filter.get_safety_stats()
        ethical_summary = ethical_safety_filter.get_ethical_summary()
        
        return {
            "success": True,
            "safety_stats": stats,
            "ethical_summary": ethical_summary
        }
    except Exception as e:
        logger.error(f"Failed to get ethical stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ethics/check-content")
async def check_content_ethics(
    content: str = Query(..., description="Content to check"),
    source_url: Optional[str] = Query(None, description="Source URL"),
    context: Optional[str] = Query("", description="Context information")
):
    """Check content for ethical compliance"""
    try:
        safety_result = ethical_safety_filter.check_content_safety(
            content=content,
            source_url=source_url,
            context=context
        )
        
        return {
            "success": True,
            "is_safe": safety_result.is_safe,
            "level": safety_result.level.value,
            "reason": safety_result.reason,
            "confidence": safety_result.confidence,
            "violations": [
                {
                    "violation_id": v.violation_id,
                    "principle": v.principle.value,
                    "severity": v.severity.value,
                    "description": v.description,
                    "suggested_action": v.suggested_action,
                    "timestamp": v.timestamp.isoformat()
                }
                for v in safety_result.ethical_violations
            ],
            "details": safety_result.details
        }
    except Exception as e:
        logger.error(f"Failed to check content ethics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ethics/violations")
async def get_ethical_violations(
    principle: Optional[str] = Query(None, description="Filter by ethical principle"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=200, description="Number of violations to return")
):
    """Get ethical violations"""
    try:
        violations = ethical_safety_filter.violations
        
        # Filter by principle if specified
        if principle:
            violations = [v for v in violations if v.principle.value == principle]
        
        # Filter by severity if specified
        if severity:
            violations = [v for v in violations if v.severity.value == severity]
        
        # Sort by timestamp (newest first) and limit
        violations = sorted(violations, key=lambda x: x.timestamp, reverse=True)[:limit]
        
        formatted_violations = []
        for violation in violations:
            formatted_violations.append({
                "violation_id": violation.violation_id,
                "principle": violation.principle.value,
                "severity": violation.severity.value,
                "description": violation.description,
                "context": violation.context,
                "suggested_action": violation.suggested_action,
                "timestamp": violation.timestamp.isoformat(),
                "metadata": violation.metadata
            })
        
        return {
            "success": True,
            "violations": formatted_violations,
            "total_count": len(formatted_violations),
            "filters": {
                "principle": principle,
                "severity": severity
            }
        }
    except Exception as e:
        logger.error(f"Failed to get ethical violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ethics/clear-violations")
async def clear_ethical_violations():
    """Clear all ethical violations"""
    try:
        ethical_safety_filter.clear_violations()
        return {"success": True, "message": "All ethical violations cleared"}
    except Exception as e:
        logger.error(f"Failed to clear ethical violations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ethics/add-blacklist-keyword")
async def add_blacklist_keyword(
    keyword: str = Query(..., description="Keyword to add to blacklist")
):
    """Add keyword to ethical blacklist"""
    try:
        ethical_safety_filter.add_blacklist_keyword(keyword)
        return {"success": True, "message": f"Added keyword '{keyword}' to blacklist"}
    except Exception as e:
        logger.error(f"Failed to add blacklist keyword: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ethics/remove-blacklist-keyword")
async def remove_blacklist_keyword(
    keyword: str = Query(..., description="Keyword to remove from blacklist")
):
    """Remove keyword from ethical blacklist"""
    try:
        ethical_safety_filter.remove_blacklist_keyword(keyword)
        return {"success": True, "message": f"Removed keyword '{keyword}' from blacklist"}
    except Exception as e:
        logger.error(f"Failed to remove blacklist keyword: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ethics/blacklist-keywords")
async def get_blacklist_keywords():
    """Get current blacklist keywords"""
    try:
        return {
            "success": True,
            "keywords": ethical_safety_filter.blacklist_keywords,
            "count": len(ethical_safety_filter.blacklist_keywords)
        }
    except Exception as e:
        logger.error(f"Failed to get blacklist keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rss/fetch-content")
async def fetch_rss_content(
    max_items_per_source: int = Query(5, ge=1, le=20, description="Max items per source")
) -> Dict[str, Any]:
    """
    Fetch content from RSS and Public APIs
    
    Args:
        max_items_per_source: Maximum items to fetch per source
        
    Returns:
        Dict with fetch results
        
    Raises:
        HTTPException: If fetch fails
    """
    try:
        logger.info(f"📡 Fetching content from RSS and Public APIs (max {max_items_per_source} per source)")
        
        pipeline = get_pipeline_instance()
        content = pipeline.fetch_daily_content(max_items_per_source=max_items_per_source)
        
        logger.info(f"✅ Fetched {len(content)} items successfully")
        
        return {
            "total_items": len(content),
            "items": content[:10],  # Return first 10 items for preview
            "sources_used": len(pipeline.rss_sources) + len(pipeline.api_sources),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"❌ Fetch RSS content error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch RSS content: {str(e)}"
        )

# Knowledge Consolidation endpoints
@router.get("/knowledge/stats")
async def get_knowledge_stats():
    """Get knowledge base statistics"""
    try:
        stats = knowledge_consolidation_service.get_knowledge_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Failed to get knowledge stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge/consolidate")
async def consolidate_knowledge():
    """Manually trigger knowledge consolidation"""
    try:
        result = knowledge_consolidation_service.consolidate_knowledge()
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Failed to consolidate knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge/search")
async def search_knowledge(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Search knowledge base"""
    try:
        results = knowledge_consolidation_service.search_knowledge(query, category)
        return {"success": True, "results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Failed to search knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge/items")
async def get_knowledge_items(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(20, description="Number of items to return")
):
    """Get knowledge items"""
    try:
        items = []
        for item in knowledge_consolidation_service.knowledge_items.values():
            if category and item.category != category:
                continue
            
            items.append({
                "id": item.id,
                "title": item.title,
                "content": item.content[:200] + "..." if len(item.content) > 200 else item.content,
                "source": item.source,
                "category": item.category,
                "quality_score": item.quality_score,
                "trust_score": item.trust_score,
                "created_at": item.created_at,
                "tags": item.tags
            })
        
        # Sort by creation date
        items.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {"success": True, "items": items[:limit], "total": len(items)}
    except Exception as e:
        logger.error(f"Failed to get knowledge items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge/clusters")
async def get_consolidated_clusters(
    limit: int = Query(20, description="Number of clusters to return")
):
    """Get consolidated knowledge clusters"""
    try:
        clusters = []
        for cluster in knowledge_consolidation_service.consolidated_clusters.values():
            clusters.append({
                "id": cluster.cluster_id,
                "topic": cluster.topic,
                "summary": cluster.summary,
                "key_points": cluster.key_points,
                "sources": cluster.sources,
                "confidence_score": cluster.confidence_score,
                "created_at": cluster.created_at,
                "last_updated": cluster.last_updated,
                "item_count": len(cluster.knowledge_items)
            })
        
        # Sort by confidence score
        clusters.sort(key=lambda x: x["confidence_score"], reverse=True)
        
        return {"success": True, "clusters": clusters[:limit], "total": len(clusters)}
    except Exception as e:
        logger.error(f"Failed to get consolidated clusters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Advanced Memory Management endpoints
@router.get("/memory/stats")
async def get_memory_stats():
    """Get advanced memory management statistics"""
    try:
        stats = advanced_memory_manager.get_memory_stats()
        return {"success": True, "stats": stats}
    except Exception as e:
        logger.error(f"Failed to get memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/add")
async def add_memory(
    content: str = Query(..., description="Memory content"),
    category: str = Query(..., description="Memory category"),
    context_tags: Optional[str] = Query(None, description="Context tags (comma-separated)"),
    memory_type: str = Query("semantic", description="Memory type")
):
    """Add new memory to advanced memory manager"""
    try:
        tags = context_tags.split(",") if context_tags else []
        memory_id = advanced_memory_manager.add_memory(
            content=content,
            category=category,
            context_tags=tags,
            memory_type=memory_type
        )
        
        if memory_id:
            return {"success": True, "memory_id": memory_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to add memory")
            
    except Exception as e:
        logger.error(f"Failed to add memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/retrieve")
async def retrieve_memory(
    query: str = Query(..., description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(10, description="Number of results to return")
):
    """Retrieve relevant memories"""
    try:
        context = {"category": category} if category else None
        memories = advanced_memory_manager.retrieve_memory(query, context, limit)
        return {"success": True, "memories": memories, "count": len(memories)}
    except Exception as e:
        logger.error(f"Failed to retrieve memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/memory/optimize")
async def optimize_memory():
    """Manually trigger memory optimization"""
    try:
        advanced_memory_manager.optimize_memory()
        return {"success": True, "message": "Memory optimization completed"}
    except Exception as e:
        logger.error(f"Failed to optimize memory: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/items")
async def get_memory_items(
    category: Optional[str] = Query(None, description="Filter by category"),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    limit: int = Query(20, description="Number of items to return")
):
    """Get memory items"""
    try:
        items = []
        for memory_item in advanced_memory_manager.memory_items.values():
            if category and memory_item.category != category:
                continue
            if memory_type and memory_item.memory_type != memory_type:
                continue
            
            items.append({
                "id": memory_item.id,
                "content": memory_item.content,
                "category": memory_item.category,
                "priority": memory_item.priority,
                "access_count": memory_item.access_count,
                "importance_score": memory_item.importance_score,
                "memory_type": memory_item.memory_type,
                "context_tags": memory_item.context_tags,
                "created_at": memory_item.created_at,
                "last_accessed": memory_item.last_accessed
            })
        
        # Sort by priority
        items.sort(key=lambda x: x["priority"], reverse=True)
        
        return {"success": True, "items": items[:limit], "total": len(items)}
    except Exception as e:
        logger.error(f"Failed to get memory items: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/memory/clusters")
async def get_memory_clusters(
    limit: int = Query(20, description="Number of clusters to return")
):
    """Get memory clusters"""
    try:
        clusters = []
        for cluster in advanced_memory_manager.memory_clusters.values():
            clusters.append({
                "id": cluster.cluster_id,
                "topic": cluster.topic,
                "memories": cluster.memories,
                "coherence_score": cluster.coherence_score,
                "access_frequency": cluster.access_frequency,
                "last_updated": cluster.last_updated,
                "memory_count": len(cluster.memories)
            })
        
        # Sort by coherence score
        clusters.sort(key=lambda x: x["coherence_score"], reverse=True)
        
        return {"success": True, "clusters": clusters[:limit], "total": len(clusters)}
    except Exception as e:
        logger.error(f"Failed to get memory clusters: {e}")
        raise HTTPException(status_code=500, detail=str(e))