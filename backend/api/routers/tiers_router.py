"""
Tiers Router for StillMe API
Handles all tier management endpoints (Continuum Memory v1)
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from backend.api.models import TierStatsResponse, TierAuditResponse, TierPromoteRequest, TierDemoteRequest, ForgettingTrendsResponse
from backend.api.auth import require_api_key
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()

# Import global services from main (temporary - will refactor to dependency injection later)
def get_continuum_memory():
    """Get ContinuumMemory service from main module"""
    import backend.api.main as main_module
    return main_module.continuum_memory

@router.get("/stats", response_model=TierStatsResponse)
async def get_tier_stats():
    """
    Get statistics for each tier (L0-L3)
    
    Returns tier counts, promotion/demotion counts (last 7 days)
    PR-2: Uses real data from ContinuumMemory
    """
    try:
        continuum_memory = get_continuum_memory()
        
        if not continuum_memory or not os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true":
            # Return empty stats if disabled
            return TierStatsResponse(
                L0=0, L1=0, L2=0, L3=0, total=0, promoted_7d=0, demoted_7d=0
            )
        
        stats = continuum_memory.get_tier_stats()
        return TierStatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Error getting tier stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit", response_model=TierAuditResponse)
async def get_tier_audit(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    item_id: Optional[str] = Query(None, description="Filter by item ID")
):
    """
    Get audit log of promotion/demotion events
    
    PR-2: Uses real data from ContinuumMemory
    """
    try:
        continuum_memory = get_continuum_memory()
        
        if not continuum_memory or not os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true":
            return TierAuditResponse(records=[], total=0)
        
        audit_log = continuum_memory.get_audit_log(limit=limit, item_id=item_id)
        from backend.api.models.tier_models import TierAuditRecord
        records = [TierAuditRecord(**record) for record in audit_log]
        return TierAuditResponse(records=records, total=len(records))
        
    except Exception as e:
        logger.error(f"Error getting tier audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/promote/{item_id}", dependencies=[Depends(require_api_key)])
async def promote_item_api(item_id: str, request: Optional[TierPromoteRequest] = None):
    """
    Promote a knowledge item to higher tier (admin only)
    
    PR-2: Real implementation using PromotionManager
    """
    try:
        continuum_memory = get_continuum_memory()
        
        if not continuum_memory or not os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true":
            raise HTTPException(status_code=503, detail="Continuum Memory is disabled")
        
        from backend.learning.promotion_manager import PromotionManager
        promotion_manager = PromotionManager()
        
        # Get current tier and metrics
        import sqlite3
        conn = sqlite3.connect(continuum_memory.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT tier, surprise_score, retrieval_count_7d, validator_overlap FROM tier_metrics WHERE item_id = ?", (item_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
        
        current_tier = result[0]
        surprise_score = result[1] or 0.0
        retrieval_count_7d = result[2] or 0
        validator_overlap = result[3] or 0.0
        conn.close()
        
        # Determine target tier
        if current_tier == "L0":
            target_tier = "L1"
        elif current_tier == "L1":
            target_tier = "L2"
        elif current_tier == "L2":
            target_tier = "L3"
        else:
            raise HTTPException(status_code=400, detail=f"Cannot promote from {current_tier}")
        
        reason = request.reason if request and request.reason else f"Manual promotion from {current_tier} to {target_tier}"
        
        success = promotion_manager.promote_item(
            item_id, current_tier, target_tier, reason,
            surprise_score, retrieval_count_7d, validator_overlap
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Promoted {item_id} from {current_tier} to {target_tier}",
                "item_id": item_id,
                "from_tier": current_tier,
                "to_tier": target_tier
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to promote item")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error promoting item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/demote/{item_id}", dependencies=[Depends(require_api_key)])
async def demote_item_api(item_id: str, request: Optional[TierDemoteRequest] = None):
    """
    Demote a knowledge item to lower tier (admin only)
    
    PR-2: Real implementation using PromotionManager
    """
    try:
        continuum_memory = get_continuum_memory()
        
        if not continuum_memory or not os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true":
            raise HTTPException(status_code=503, detail="Continuum Memory is disabled")
        
        from backend.learning.promotion_manager import PromotionManager
        promotion_manager = PromotionManager()
        
        # Get current tier and metrics
        import sqlite3
        conn = sqlite3.connect(continuum_memory.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT tier, surprise_score, retrieval_count_7d, validator_overlap FROM tier_metrics WHERE item_id = ?", (item_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
        
        current_tier = result[0]
        surprise_score = result[1] or 0.0
        retrieval_count_7d = result[2] or 0
        validator_overlap = result[3] or 0.0
        conn.close()
        
        # Determine target tier
        if current_tier == "L3":
            target_tier = "L2"
        elif current_tier == "L2":
            target_tier = "L1"
        elif current_tier == "L1":
            target_tier = "L0"
        else:
            raise HTTPException(status_code=400, detail=f"Cannot demote from {current_tier}")
        
        reason = request.reason if request and request.reason else f"Manual demotion from {current_tier} to {target_tier}"
        
        success = promotion_manager.demote_item(
            item_id, current_tier, target_tier, reason,
            surprise_score, retrieval_count_7d, validator_overlap
        )
        
        if success:
            return {
                "status": "success",
                "message": f"Demoted {item_id} from {current_tier} to {target_tier}",
                "item_id": item_id,
                "from_tier": current_tier,
                "to_tier": target_tier
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to demote item")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error demoting item: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forgetting-trends", response_model=ForgettingTrendsResponse)
async def get_forgetting_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back")
):
    """
    Get forgetting trends (Recall@k degradation) over time
    
    PR-2: Uses real data from ContinuumMemory
    """
    try:
        continuum_memory = get_continuum_memory()
        
        if not continuum_memory or not os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true":
            return ForgettingTrendsResponse(trends=[], days=days)
        
        trends = continuum_memory.get_forgetting_trends(days=days)
        return ForgettingTrendsResponse(trends=trends, days=days)
        
    except Exception as e:
        logger.error(f"Error getting forgetting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))

