"""
System Router - Core endpoints for API health, status, and metrics
Handles root, health check, system status, and validation metrics
"""

from fastapi import APIRouter, Request
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

# Import global services from main (temporary - will refactor to dependency injection later)
def get_rag_retrieval():
    import backend.api.main as main_module
    return main_module.rag_retrieval

def get_initialization_error():
    import backend.api.main as main_module
    return main_module._initialization_error

@router.get("/")
async def root():
    """Root endpoint"""
    rag_retrieval = get_rag_retrieval()
    _initialization_error = get_initialization_error()
    
    # Debug: Log RAG status for troubleshooting
    rag_status = rag_retrieval is not None
    if not rag_status:
        logger.warning(f"⚠️ RAG retrieval is None! Initialization error: {_initialization_error}")
    else:
        logger.debug(f"✓ RAG retrieval is available: {type(rag_retrieval).__name__}")
    
    return {
        "message": "StillMe API v0.4.0",
        "status": "running",
        "rag_enabled": rag_status,
        "rag_initialization_error": _initialization_error if _initialization_error else None,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/health")
async def health_check(request: Request):
    """
    Health check endpoint for Railway/Docker health probes.
    No rate limiting - must always be available for monitoring.
    """
    try:
        rag_retrieval = get_rag_retrieval()
        rag_status = "enabled" if rag_retrieval else "disabled"
        return {
            "status": "healthy",
            "rag_status": rag_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        # Health check should always return 200, even if there are minor issues
        # This ensures Railway/Docker doesn't kill the container
        logger.warning(f"Health check warning: {e}")
        return {
            "status": "healthy",
            "rag_status": "unknown",
            "timestamp": datetime.now().isoformat(),
            "warning": str(e)
        }

@router.get("/api/status")
async def get_status():
    """Get system status"""
    try:
        status = {
            "stage": "Infant",
            "sessions_completed": 0,
            "milestone_sessions": 100,
            "system_age_days": 0
        }
        
        # Try to get from database if available
        # For now, return default status
        
        return status
        
    except Exception as e:
        logger.error(f"Status error: {e}")
        return {
            "stage": "Unknown",
            "sessions_completed": 0,
            "milestone_sessions": 100,
            "system_age_days": 0
        }

@router.get("/api/validators/metrics")
async def get_validation_metrics():
    """Get validation metrics"""
    try:
        from backend.validators.metrics import get_metrics
        metrics = get_metrics()
        return {"metrics": metrics.get_metrics()}
    except Exception as e:
        logger.error(f"Validation metrics error: {e}")
        return {
            "metrics": {
                "total_validations": 0,
                "pass_rate": 0.0,
                "passed_count": 0,
                "failed_count": 0,
                "avg_overlap_score": 0.0,
                "reasons_histogram": {},
                "recent_logs": []
            }
        }

