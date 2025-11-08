"""
System Router - Core endpoints for API health, status, and metrics
Handles root, health check, system status, and validation metrics
"""

from fastapi import APIRouter, Request, HTTPException
import logging
import os
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()

# Feature flag for health/ready endpoints
ENABLE_HEALTH_READY = os.getenv("ENABLE_HEALTH_READY", "true").lower() == "true"

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
    Liveness probe endpoint for Railway/Docker health probes.
    Returns 200 if service is running (even with minor issues).
    No rate limiting - must always be available for monitoring.
    
    This endpoint is designed to be lightweight and always return 200,
    even during RAG component initialization, to prevent Railway from
    killing the container during startup.
    
    IMPORTANT: This endpoint must return 200 IMMEDIATELY, even before
    FastAPI app is fully initialized, to prevent Railway from marking
    deployment as failed during startup.
    
    This is a PURE LIVENESS check - it only verifies the process is running.
    For dependency checks (DB, ChromaDB, Embeddings), use /ready endpoint.
    """
    # Always return 200 - this endpoint only checks if the service is running
    # Use /ready endpoint for detailed readiness checks
    # This endpoint should NEVER fail - it's the first thing Railway checks
    
    # Pure liveness check - no dependencies, no try/except needed
    # Just return 200 OK immediately
    return {
        "status": "healthy",
        "service": "stillme-backend",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/ready")
async def readiness_check(request: Request):
    """
    Readiness probe endpoint for Kubernetes/Docker readiness checks.
    Returns 200 when all checks pass, 503 if any check fails.
    Checks: SQLite database, ChromaDB, Embedding service.
    No rate limiting - must always be available for monitoring.
    """
    if not ENABLE_HEALTH_READY:
        return {
            "status": "ready",
            "checks": {},
            "message": "Health/ready endpoints disabled via ENABLE_HEALTH_READY=false",
            "timestamp": datetime.now().isoformat()
        }
    
    checks: Dict[str, bool] = {
        "database": False,
        "vector_db": False,
        "embeddings": False
    }
    
    check_details: Dict[str, Any] = {}
    
    # Check 1: SQLite database connectivity
    try:
        db_paths = [
            "data/knowledge_retention.db",
            "data/continuum_memory.db",
            "data/rss_fetch_history.db",
            "data/accuracy_scores.db"
        ]
        
        db_check_passed = False
        for db_path in db_paths:
            try:
                conn = sqlite3.connect(db_path, timeout=1.0)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                conn.close()
                db_check_passed = True
                break
            except Exception as db_error:
                logger.debug(f"Database check failed for {db_path}: {db_error}")
                continue
        
        checks["database"] = db_check_passed
        check_details["database"] = {
            "status": "ok" if db_check_passed else "failed",
            "message": "At least one database accessible" if db_check_passed else "All databases failed"
        }
    except Exception as e:
        logger.warning(f"Database readiness check error: {e}")
        check_details["database"] = {"status": "error", "message": str(e)}
    
    # Check 2: ChromaDB heartbeat
    try:
        rag_retrieval = get_rag_retrieval()
        if rag_retrieval and rag_retrieval.chroma_client:
            # Try to access ChromaDB client
            client = rag_retrieval.chroma_client.client
            # ChromaDB PersistentClient doesn't have explicit heartbeat, but we can check if client exists
            if client is not None:
                checks["vector_db"] = True
                check_details["vector_db"] = {"status": "ok", "message": "ChromaDB client available"}
            else:
                check_details["vector_db"] = {"status": "failed", "message": "ChromaDB client is None"}
        else:
            check_details["vector_db"] = {"status": "failed", "message": "RAG retrieval or ChromaDB client not initialized"}
    except Exception as e:
        logger.warning(f"ChromaDB readiness check error: {e}")
        check_details["vector_db"] = {"status": "error", "message": str(e)}
    
    # Check 3: Embedding service
    try:
        rag_retrieval = get_rag_retrieval()
        if rag_retrieval and rag_retrieval.embedding_service:
            # Try encoding a test string with timeout
            test_text = "test"
            try:
                # Run encoding in executor to avoid blocking
                loop = asyncio.get_event_loop()
                embedding = await asyncio.wait_for(
                    loop.run_in_executor(None, rag_retrieval.embedding_service.encode_text, test_text),
                    timeout=2.0
                )
                if embedding is not None and len(embedding) > 0:
                    checks["embeddings"] = True
                    check_details["embeddings"] = {"status": "ok", "message": f"Embedding service working (dim={len(embedding)})"}
                else:
                    check_details["embeddings"] = {"status": "failed", "message": "Embedding returned empty result"}
            except asyncio.TimeoutError:
                check_details["embeddings"] = {"status": "timeout", "message": "Embedding service timeout (>2s)"}
            except Exception as embed_error:
                check_details["embeddings"] = {"status": "error", "message": str(embed_error)}
        else:
            check_details["embeddings"] = {"status": "failed", "message": "RAG retrieval or embedding service not initialized"}
    except Exception as e:
        logger.warning(f"Embedding service readiness check error: {e}")
        check_details["embeddings"] = {"status": "error", "message": str(e)}
    
    # Determine overall readiness
    all_ready = all(checks.values())
    status_code = 200 if all_ready else 503
    
    response = {
        "status": "ready" if all_ready else "not_ready",
        "checks": checks,
        "check_details": check_details,
        "timestamp": datetime.now().isoformat()
    }
    
    if not all_ready:
        logger.warning(f"Readiness check failed: {checks}")
        raise HTTPException(status_code=status_code, detail=response)
    
    return response

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

