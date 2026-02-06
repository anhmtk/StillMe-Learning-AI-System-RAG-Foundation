"""
System Router - Core endpoints for API health, status, and metrics
Handles root, health check, system status, and validation metrics
"""

from fastapi import APIRouter, Request, HTTPException, Response, Depends, Security
import logging
import os
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import authentication dependency
try:
    from backend.api.auth import require_api_key
except ImportError:
    require_api_key = None
    logger.warning("⚠️ Authentication module not available. Admin endpoints will be unprotected.")

router = APIRouter()

# Feature flag for health/ready endpoints
ENABLE_HEALTH_READY = os.getenv("ENABLE_HEALTH_READY", "true").lower() == "true"

# Feature flag for dependency injection (currently disabled - using direct imports)
USE_DEPENDENCY_INJECTION = os.getenv("USE_DEPENDENCY_INJECTION", "false").lower() == "true"

# Import dependency injection types (if available)
try:
    from backend.api.dependencies import (
        RAGRetrievalDep, ChromaClientDep, EmbeddingServiceDep, KnowledgeRetentionDep,
        AccuracyScorerDep, RSSFetcherDep, LearningSchedulerDep, SelfDiagnosisAgentDep,
        ContentCuratorDep, RSSFetchHistoryDep, ContinuumMemoryDep, SourceIntegrationDep,
        FeedHealthMonitorDep, APIKeyRotationServiceDep
    )
except ImportError:
    # Fallback if dependencies module not available
    RAGRetrievalDep = None
    ChromaClientDep = None
    EmbeddingServiceDep = None
    KnowledgeRetentionDep = None
    AccuracyScorerDep = None
    RSSFetcherDep = None
    LearningSchedulerDep = None
    SelfDiagnosisAgentDep = None
    ContentCuratorDep = None
    RSSFetchHistoryDep = None
    ContinuumMemoryDep = None
    SourceIntegrationDep = None
    FeedHealthMonitorDep = None
    APIKeyRotationServiceDep = None

# Import global services from main (temporary - will refactor to dependency injection later)
def get_rag_retrieval():
    import backend.api.main as main_module
    return main_module.rag_retrieval

def get_initialization_error():
    import backend.api.main as main_module
    return main_module._initialization_error

def get_chroma_client():
    """Get ChromaDB client from main module"""
    import backend.api.main as main_module
    if hasattr(main_module, 'chroma_client') and main_module.chroma_client:
        return main_module.chroma_client
    return None

@router.get("/")
async def root(
    rag_retrieval_service: object = RAGRetrievalDep if USE_DEPENDENCY_INJECTION else None
):
    """Root endpoint"""
    if USE_DEPENDENCY_INJECTION and rag_retrieval_service:
        rag_retrieval = rag_retrieval_service
    else:
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
        import os
        enable_validators = os.getenv("ENABLE_VALIDATORS", "false").lower() == "true"
        
        status = {
            "stage": "Infant",
            "sessions_completed": 0,
            "milestone_sessions": 100,
            "system_age_days": 0,
            "validators_enabled": enable_validators
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
            "system_age_days": 0,
            "validators_enabled": False
        }

@router.get("/api/health/detailed")
async def detailed_health_check():
    """
    Detailed health check endpoint with component-level status.
    Includes RSS feed performance, database health, and system metrics.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {}
    }
    
    # Check RSS Fetcher
    try:
        import backend.api.main as main_module
        if main_module.rss_fetcher:
            rss_stats = main_module.rss_fetcher.get_stats()
            health_status["components"]["rss_fetcher"] = {
                "status": rss_stats.get("status", "unknown"),
                "feeds_count": rss_stats.get("feeds_count", 0),
                "successful_feeds": rss_stats.get("successful_feeds", 0),
                "failed_feeds": rss_stats.get("failed_feeds", 0),
                "failure_rate": rss_stats.get("failure_rate", 0),
                "alert_threshold_exceeded": rss_stats.get("alert_threshold_exceeded", False),
                "last_success_time": rss_stats.get("last_success_time"),
                "last_error": rss_stats.get("last_error")
            }
            
            # Alert if failure rate > 10%
            if rss_stats.get("alert_threshold_exceeded", False):
                health_status["status"] = "degraded"
                health_status["alerts"] = health_status.get("alerts", [])
                health_status["alerts"].append({
                    "component": "rss_fetcher",
                    "severity": "warning",
                    "message": f"RSS feed failure rate is {rss_stats.get('failure_rate', 0):.1f}% (threshold: 10%)"
                })
        else:
            health_status["components"]["rss_fetcher"] = {
                "status": "not_initialized",
                "message": "RSS fetcher not initialized"
            }
    except Exception as e:
        health_status["components"]["rss_fetcher"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check Database
    try:
        db_paths = [
            "data/knowledge_retention.db",
            "data/continuum_memory.db",
            "data/rss_fetch_history.db",
            "data/accuracy_scores.db"
        ]
        
        db_status = []
        for db_path in db_paths:
            try:
                conn = sqlite3.connect(db_path, timeout=1.0)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                conn.close()
                db_status.append({"path": db_path, "status": "ok"})
            except Exception as db_error:
                db_status.append({"path": db_path, "status": "error", "error": str(db_error)})
        
        health_status["components"]["database"] = {
            "status": "ok" if all(db["status"] == "ok" for db in db_status) else "degraded",
            "databases": db_status
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check ChromaDB
    try:
        rag_retrieval = get_rag_retrieval()
        if rag_retrieval and rag_retrieval.chroma_client:
            health_status["components"]["vector_db"] = {
                "status": "ok",
                "message": "ChromaDB client available"
            }
        else:
            health_status["components"]["vector_db"] = {
                "status": "not_initialized",
                "message": "ChromaDB not initialized"
            }
    except Exception as e:
        health_status["components"]["vector_db"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check Embedding Service
    try:
        rag_retrieval = get_rag_retrieval()
        if rag_retrieval and rag_retrieval.embedding_service:
            health_status["components"]["embedding_service"] = {
                "status": "ok",
                "message": "Embedding service available"
            }
        else:
            health_status["components"]["embedding_service"] = {
                "status": "not_initialized",
                "message": "Embedding service not initialized"
            }
    except Exception as e:
        health_status["components"]["embedding_service"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Check Learning Scheduler
    try:
        import backend.api.main as main_module
        if main_module.learning_scheduler:
            scheduler_status = main_module.learning_scheduler.get_status()
            health_status["components"]["learning_scheduler"] = {
                "status": scheduler_status.get("status", "unknown"),
                "is_running": scheduler_status.get("is_running", False),
                "next_run": scheduler_status.get("next_run_time"),
                "last_run": scheduler_status.get("last_run_time"),
                "interval_hours": scheduler_status.get("interval_hours", 4)
            }
        else:
            health_status["components"]["learning_scheduler"] = {
                "status": "not_initialized",
                "message": "Learning scheduler not initialized"
            }
    except Exception as e:
        health_status["components"]["learning_scheduler"] = {
            "status": "error",
            "error": str(e)
        }
    
    return health_status

@router.get("/api/monitoring/rss-feeds")
async def rss_feeds_monitoring():
    """
    RSS Feeds monitoring endpoint with detailed performance metrics.
    """
    try:
        import backend.api.main as main_module
        if not main_module.rss_fetcher:
            return {
                "status": "error",
                "message": "RSS fetcher not initialized"
            }
        
        rss_stats = main_module.rss_fetcher.get_stats()
        
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "metrics": {
                "total_feeds": rss_stats.get("feeds_count", 0),
                "successful_feeds": rss_stats.get("successful_feeds", 0),
                "failed_feeds": rss_stats.get("failed_feeds", 0),
                "failure_rate": rss_stats.get("failure_rate", 0),
                "success_rate": round(100 - rss_stats.get("failure_rate", 0), 2),
                "error_count": rss_stats.get("error_count", 0),
                "last_success_time": rss_stats.get("last_success_time"),
                "last_error": rss_stats.get("last_error"),
                "alert_threshold_exceeded": rss_stats.get("alert_threshold_exceeded", False)
            },
            "alerts": [
                {
                    "severity": "warning",
                    "message": f"RSS feed failure rate is {rss_stats.get('failure_rate', 0):.1f}% (threshold: 10%)"
                }
            ] if rss_stats.get("alert_threshold_exceeded", False) else []
        }
    except Exception as e:
        logger.error(f"RSS feeds monitoring error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/api/validators/metrics")
async def get_validation_metrics(days: int = None):
    """
    Get validation metrics
    
    Args:
        days: Optional number of days to filter (e.g., 3 for last 3 days)
    
    Returns:
        Validation metrics including pass rate, error types, recent logs
    """
    try:
        from backend.validators.metrics import get_metrics
        metrics = get_metrics()
        return {"metrics": metrics.get_metrics(days=days)}
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

@router.get("/api/admin/validation-metrics")
async def get_admin_validation_metrics(days: int = 7):
    """
    Get detailed validation metrics for admin dashboard
    
    This endpoint provides per-validator breakdown including:
    - Total responses validated in the time period
    - Per-validator pass/fail counts and rates
    - Fallback usage statistics
    - Confidence score distribution
    
    Args:
        days: Number of days to analyze (default: 7)
    
    Returns:
        Dictionary with per-validator metrics and overall statistics
    """
    try:
        from backend.services.validation_metrics_service import get_validation_metrics_service
        service = get_validation_metrics_service()
        metrics = service.get_per_validator_metrics(days=days, use_persistent_tracker=True)
        return metrics
    except Exception as e:
        logger.error(f"Admin validation metrics error: {e}", exc_info=True)
        return {
            "total_responses": 0,
            "total_fallbacks": 0,
            "time_period_days": days,
            "validators": [],
            "confidence_distribution": {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "count": 0
            },
            "error": str(e)
        }

@router.get("/api/validators/metrics/patterns")
async def get_validation_patterns(days: int = 7):
    """
    Get validation patterns and improvement suggestions
    
    Args:
        days: Number of days to analyze (default: 7)
    
    Returns:
        Validation patterns with suggested improvements
    """
    try:
        from backend.validators.validation_metrics_tracker import get_validation_tracker
        tracker = get_validation_tracker()
        patterns = tracker.analyze_patterns(days=days)
        return {
            "patterns": [{
                "type": p.pattern_type,
                "frequency": p.frequency,
                "affected_categories": p.affected_categories,
                "suggested_improvement": p.suggested_improvement
            } for p in patterns],
            "analysis_period_days": days
        }
    except Exception as e:
        logger.error(f"Validation patterns error: {e}")
        return {"patterns": [], "error": str(e)}

@router.get("/api/validators/self-improvement/analyze")
async def get_self_improvement_analysis(days: int = 7):
    """
    Get self-improvement analysis with learning suggestions
    
    Args:
        days: Number of days to analyze (default: 7)
    
    Returns:
        Complete self-improvement analysis with patterns, suggestions, and recommendations
    """
    try:
        from backend.validators.self_improvement import get_self_improvement_analyzer
        analyzer = get_self_improvement_analyzer()
        return analyzer.analyze_and_suggest(days=days)
    except Exception as e:
        logger.error(f"Self-improvement analysis error: {e}")
        return {
            "error": str(e),
            "analysis_period_days": days
        }

@router.get("/api/validators/metrics/knowledge-gaps")
async def get_knowledge_gaps_from_failures(days: int = 7):
    """
    Get knowledge gaps identified from validation failures
    
    Args:
        days: Number of days to analyze (default: 7)
    
    Returns:
        List of knowledge gaps with suggested topics and sources
    """
    try:
        from backend.validators.self_improvement import get_self_improvement_analyzer
        analyzer = get_self_improvement_analyzer()
        gaps = analyzer.get_knowledge_gaps_from_failures(days=days)
        return {
            "knowledge_gaps": gaps,
            "analysis_period_days": days
        }
    except Exception as e:
        logger.error(f"Knowledge gaps analysis error: {e}")
        return {"knowledge_gaps": [], "error": str(e)}

@router.get("/api/validators/performance")
async def get_validator_performance_dashboard(days: int = 7):
    """
    Get Validator Performance Dashboard (Gemini's recommendation).
    
    This endpoint provides per-validator performance statistics including:
    - Total checks, pass/fail counts, pass rates
    - Failure detection rate (how often validators catch issues)
    - Average execution time (if tracked)
    - Common failure reasons per validator
    
    This helps identify:
    - Validators that rarely catch issues (candidates for consolidation)
    - Validators with high false positive rates
    - Performance bottlenecks (slow validators)
    
    Args:
        days: Number of days to analyze (default: 7)
    
    Returns:
        Dictionary mapping validator_name to performance stats:
        {
            "CitationRequired": {
                "total_checks": 100,
                "passed": 95,
                "failed": 5,
                "pass_rate": 0.95,
                "failure_detection_rate": 0.05,
                "avg_execution_time": 0.012,
                "common_failure_reasons": {"missing_citation": 5}
            },
            ...
        }
    """
    try:
        from backend.validators.validation_metrics_tracker import get_validation_tracker
        tracker = get_validation_tracker()
        stats = tracker.get_validator_performance_stats(days=days)
        
        # Calculate summary statistics
        total_validators = len(stats)
        total_checks = sum(s.get("total_checks", 0) for s in stats.values())
        
        # Identify validators with low failure detection (candidates for consolidation)
        low_detection_validators = [
            name for name, s in stats.items()
            if s.get("total_checks", 0) > 10 and s.get("failure_detection_rate", 0) < 0.01
        ]
        
        # Identify slow validators (if execution time tracked)
        slow_validators = [
            {
                "name": name,
                "avg_execution_time": s.get("avg_execution_time", 0)
            }
            for name, s in stats.items()
            if s.get("avg_execution_time") and s.get("avg_execution_time", 0) > 0.1
        ]
        slow_validators.sort(key=lambda x: x["avg_execution_time"], reverse=True)
        
        return {
            "status": "success",
            "analysis_period_days": days,
            "summary": {
                "total_validators": total_validators,
                "total_checks": total_checks,
                "validators_with_low_detection": low_detection_validators,
                "slow_validators": slow_validators[:5]  # Top 5 slowest
            },
            "validators": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Validator performance dashboard error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "analysis_period_days": days,
            "validators": {},
            "timestamp": datetime.now().isoformat()
        }

@router.get("/api/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        from backend.services.cache_service import get_cache_service
        cache_service = get_cache_service()
        stats = cache_service.get_stats()
        return {
            "cache_stats": stats,
            "cache_enabled": {
                "llm": os.getenv("ENABLE_LLM_CACHE", "true").lower() == "true",
                "rag": os.getenv("ENABLE_RAG_CACHE", "true").lower() == "true",
                "http": os.getenv("ENABLE_HTTP_CACHE", "true").lower() == "true"
            },
            "ttl_seconds": {
                "llm": int(os.getenv("CACHE_TTL_LLM", "3600")),
                "rag": int(os.getenv("CACHE_TTL_RAG", "21600")),
                "http": int(os.getenv("CACHE_TTL_HTTP", "300"))
            }
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus-compatible metrics endpoint.
    Returns metrics in Prometheus text format for monitoring tools.
    
    This endpoint exposes system metrics in standard Prometheus format,
    allowing integration with monitoring tools like Prometheus, Grafana, etc.
    """
    try:
        from backend.api.metrics_collector import get_metrics_collector
        from backend.validators.metrics import get_metrics as get_validation_metrics
        
        metrics_collector = get_metrics_collector()
        metrics_data = metrics_collector.get_metrics()
        
        lines = []
        
        # RAG Component Health Metrics
        lines.append("# HELP stillme_rag_initialized Whether RAG components are initialized (1=yes, 0=no)")
        lines.append("# TYPE stillme_rag_initialized gauge")
        lines.append(f"stillme_rag_initialized {metrics_data['component_health'].get('rag_initialized', 0)}")
        
        lines.append("# HELP stillme_chromadb_available Whether ChromaDB is available (1=yes, 0=no)")
        lines.append("# TYPE stillme_chromadb_available gauge")
        lines.append(f"stillme_chromadb_available {metrics_data['component_health'].get('chromadb_available', 0)}")
        
        lines.append("# HELP stillme_embedding_service_ready Whether embedding service is ready (1=yes, 0=no)")
        lines.append("# TYPE stillme_embedding_service_ready gauge")
        lines.append(f"stillme_embedding_service_ready {metrics_data['component_health'].get('embedding_service_ready', 0)}")
        
        lines.append("# HELP stillme_knowledge_retention_ready Whether knowledge retention is ready (1=yes, 0=no)")
        lines.append("# TYPE stillme_knowledge_retention_ready gauge")
        lines.append(f"stillme_knowledge_retention_ready {metrics_data['component_health'].get('knowledge_retention_ready', 0)}")
        
        # Request Metrics
        total_requests = sum(metrics_data['request_counters'].values())
        lines.append("# HELP stillme_requests_total Total number of HTTP requests")
        lines.append("# TYPE stillme_requests_total counter")
        lines.append(f"stillme_requests_total {total_requests}")
        
        # Request counters by endpoint
        for key, count in metrics_data['request_counters'].items():
            method, endpoint = key.split(':', 1) if ':' in key else ('UNKNOWN', key)
            lines.append(f'stillme_requests_total{{method="{method}",endpoint="{endpoint}"}} {count}')
        
        # Error Metrics
        total_errors = sum(metrics_data['error_counters'].values())
        lines.append("# HELP stillme_requests_errors_total Total number of HTTP errors")
        lines.append("# TYPE stillme_requests_errors_total counter")
        lines.append(f"stillme_requests_errors_total {total_errors}")
        
        # Error counters by endpoint and status
        for key, count in metrics_data['error_counters'].items():
            parts = key.split(':')
            if len(parts) >= 3:
                method, endpoint, status = parts[0], parts[1], parts[2]
                lines.append(f'stillme_requests_errors_total{{method="{method}",endpoint="{endpoint}",status="{status}"}} {count}')
        
        # Learning Metrics
        lines.append("# HELP stillme_knowledge_items_total Total number of knowledge items in the system")
        lines.append("# TYPE stillme_knowledge_items_total gauge")
        lines.append(f"stillme_knowledge_items_total {metrics_data['knowledge_items_total']}")
        
        # Validation Metrics
        try:
            validation_metrics = get_validation_metrics()
            val_data = validation_metrics.get_metrics()
            
            lines.append("# HELP stillme_validations_total Total number of validations performed")
            lines.append("# TYPE stillme_validations_total counter")
            lines.append(f"stillme_validations_total {val_data.get('total_validations', 0)}")
            
            lines.append("# HELP stillme_validations_passed_total Total number of passed validations")
            lines.append("# TYPE stillme_validations_passed_total counter")
            lines.append(f"stillme_validations_passed_total {val_data.get('passed_count', 0)}")
            
            lines.append("# HELP stillme_validations_failed_total Total number of failed validations")
            lines.append("# TYPE stillme_validations_failed_total counter")
            lines.append(f"stillme_validations_failed_total {val_data.get('failed_count', 0)}")
            
            lines.append("# HELP stillme_validation_pass_rate Validation pass rate (0.0 to 1.0)")
            lines.append("# TYPE stillme_validation_pass_rate gauge")
            lines.append(f"stillme_validation_pass_rate {val_data.get('pass_rate', 0.0)}")
            
            lines.append("# HELP stillme_validation_overlap_score_avg Average evidence overlap score")
            lines.append("# TYPE stillme_validation_overlap_score_avg gauge")
            lines.append(f"stillme_validation_overlap_score_avg {val_data.get('avg_overlap_score', 0.0)}")
        except Exception as val_error:
            logger.debug(f"Could not get validation metrics: {val_error}")
        
        # Knowledge Retention Metrics (if available)
        try:
            knowledge_retention = get_knowledge_retention()
            if knowledge_retention:
                retention_metrics = knowledge_retention.calculate_retention_metrics()
                if retention_metrics:
                    total_items = retention_metrics.get('total_items', 0)
                    lines.append("# HELP stillme_knowledge_retention_items_total Total items in knowledge retention")
                    lines.append("# TYPE stillme_knowledge_retention_items_total gauge")
                    lines.append(f"stillme_knowledge_retention_items_total {total_items}")
        except Exception as kr_error:
            logger.debug(f"Could not get knowledge retention metrics: {kr_error}")
        
        metrics_text = "\n".join(lines) + "\n"
        return Response(content=metrics_text, media_type="text/plain")
        
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}", exc_info=True)
        return Response(
            content="# Error generating metrics\n",
            media_type="text/plain",
            status_code=500
        )

def get_knowledge_retention():
    """Get knowledge retention service from main module"""
    import backend.api.main as main_module
    return main_module.knowledge_retention

# ChromaDB Backup Endpoints
@router.post("/api/backup/chromadb/create")
async def create_chromadb_backup(
    backup_name: Optional[str] = None,
    chroma_client_service: object = ChromaClientDep if USE_DEPENDENCY_INJECTION else None
):
    """Create a backup of ChromaDB data"""
    if USE_DEPENDENCY_INJECTION and chroma_client_service:
        chroma_client = chroma_client_service
    else:
        chroma_client = get_chroma_client()
    if not chroma_client:
        raise HTTPException(status_code=503, detail="ChromaDB client not available")
    
    try:
        backup_path = chroma_client.create_backup(backup_name)
        if backup_path:
            return {
                "status": "success",
                "backup_path": backup_path,
                "message": "Backup created successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Backup creation failed")
    except Exception as e:
        logger.error(f"Backup creation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Backup creation failed: {str(e)}")

@router.get("/api/backup/chromadb/list")
async def list_chromadb_backups():
    """List all available ChromaDB backups"""
    chroma_client = get_chroma_client()
    if not chroma_client:
        raise HTTPException(status_code=503, detail="ChromaDB client not available")
    
    try:
        backups = chroma_client.list_backups()
        stats = chroma_client.get_backup_stats()
        return {
            "backups": backups,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Backup list error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")

@router.post("/api/backup/chromadb/restore")
async def restore_chromadb_backup(backup_name: str, verify: bool = True):
    """Restore ChromaDB from backup"""
    chroma_client = get_chroma_client()
    if not chroma_client:
        raise HTTPException(status_code=503, detail="ChromaDB client not available")
    
    try:
        success = chroma_client.restore_backup(backup_name, verify)
        if success:
            return {
                "status": "success",
                "message": f"Restored from backup: {backup_name}"
            }
        else:
            raise HTTPException(status_code=500, detail="Backup restore failed")
    except Exception as e:
        logger.error(f"Backup restore error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Backup restore failed: {str(e)}")

@router.get("/api/backup/chromadb/stats")
async def get_chromadb_backup_stats():
    """Get ChromaDB backup statistics"""
    chroma_client = get_chroma_client()
    if not chroma_client:
        raise HTTPException(status_code=503, detail="ChromaDB client not available")
    
    try:
        stats = chroma_client.get_backup_stats()
        return stats
    except Exception as e:
        logger.error(f"Backup stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get backup stats: {str(e)}")

# Redis Cache Endpoints
@router.get("/api/cache/stats")
async def get_cache_stats():
    """Get Redis cache statistics"""
    try:
        from backend.services.redis_cache import get_cache_service
        cache_service = get_cache_service()
        if not cache_service:
            return {
                "enabled": False,
                "message": "Redis cache not available"
            }
        
        stats = cache_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Cache stats error: {e}", exc_info=True)
        return {
            "enabled": False,
            "error": str(e)
        }

@router.post("/api/cache/clear")
async def clear_cache(pattern: Optional[str] = None):
    """Clear cache (use with caution!)
    
    Args:
        pattern: Optional pattern to match (e.g., "llm:response:*" to clear only LLM cache)
                 If not provided, clears all cache
    """
    try:
        from backend.services.cache_service import get_cache_service, CACHE_PREFIX_LLM
        
        cache_service = get_cache_service()
        if not cache_service:
            raise HTTPException(status_code=503, detail="Cache service not available")
        
        if pattern:
            # Clear by pattern
            if hasattr(cache_service, 'clear_pattern'):
                cleared = cache_service.clear_pattern(pattern)
                return {
                    "status": "success",
                    "message": f"Cleared {cleared} cache entries matching pattern: {pattern}",
                    "pattern": pattern,
                    "cleared_count": cleared
                }
            else:
                raise HTTPException(status_code=400, detail="Pattern clearing not supported by cache backend")
        else:
            # Clear all cache
            if hasattr(cache_service, 'clear_all'):
                success = cache_service.clear_all()
                if success:
                    return {
                        "status": "success",
                        "message": "All cache cleared"
                    }
                else:
                    raise HTTPException(status_code=500, detail="Failed to clear cache")
            elif hasattr(cache_service, 'clear_pattern'):
                # Fallback: clear by known patterns
                patterns = [
                    f"{CACHE_PREFIX_LLM}:*",
                    "rag:retrieval:*",
                    "http:response:*"
                ]
                total_cleared = 0
                for p in patterns:
                    cleared = cache_service.clear_pattern(p)
                    total_cleared += cleared
                
                return {
                    "status": "success",
                    "message": f"Cleared {total_cleared} cache entries",
                    "cleared_count": total_cleared
                }
            else:
                raise HTTPException(status_code=500, detail="Cache clearing not supported")
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear cache error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@router.post("/api/admin/foundational-knowledge/add")
async def add_foundational_knowledge_endpoint(
    api_key: Optional[str] = Depends(require_api_key) if require_api_key else Depends(lambda: None)
):
    """
    Add or update foundational knowledge in RAG.
    
    This endpoint triggers the foundational knowledge update process,
    ensuring StillMe can answer questions about itself using RAG knowledge.
    
    **Authentication Required**: This is an admin endpoint protected by API key.
    Provide API key in `X-API-Key` header.
    
    **Example:**
    ```bash
    curl -X POST https://stillme-backend-production.up.railway.app/api/admin/foundational-knowledge/add \
      -H "X-API-Key: your-api-key-here"
    ```
    """
    logger.debug(f"API key verified for foundational knowledge update")
    try:
        logger.info("🔧 Admin endpoint: Adding foundational knowledge to RAG...")
        
        # Import RAG components
        rag_retrieval = get_rag_retrieval()
        if not rag_retrieval:
            raise HTTPException(status_code=503, detail="RAG retrieval not available")
        
        chroma_client = get_chroma_client()
        if not chroma_client:
            raise HTTPException(status_code=503, detail="ChromaDB client not available")
        
        # Import foundational knowledge content
        from scripts.add_foundational_knowledge import FOUNDATIONAL_KNOWLEDGE
        
        # Prepare metadata
        tags_list = ["foundational:stillme", "CRITICAL_FOUNDATION", "stillme", "rag", "self-evolving", "continuous-learning", "automated-learning", "rss", "vector-db", "self-tracking", "time-estimation"]
        tags_string = ",".join(tags_list)
        
        # Add foundational knowledge
        logger.info(f"📝 Adding foundational knowledge (length: {len(FOUNDATIONAL_KNOWLEDGE)} characters)...")
        
        # Get collection stats before add
        try:
            stats_before = chroma_client.get_collection_stats()
            knowledge_count_before = stats_before.get("knowledge_documents", 0)
            logger.info(f"📊 Knowledge documents before add: {knowledge_count_before}")
        except Exception as e:
            logger.warning(f"⚠️  Could not get stats before add: {e}")
            knowledge_count_before = None
        
        success = rag_retrieval.add_learning_content(
            content=FOUNDATIONAL_KNOWLEDGE,
            source="CRITICAL_FOUNDATION",
            content_type="knowledge",
            metadata={
                "title": "StillMe Core Mechanism - Continuous RAG Learning",
                "foundational": "stillme",
                "type": "foundational",
                "source": "CRITICAL_FOUNDATION",
                "tags": tags_string,
                "importance_score": 1.0,
                "description": "CRITICAL: Core knowledge about StillMe's RAG-based continuous learning mechanism - MUST be retrieved when answering about StillMe"
            }
        )
        
        if success:
            # Verify document was actually added
            knowledge_count_after = None
            try:
                stats_after = chroma_client.get_collection_stats()
                knowledge_count_after = stats_after.get("knowledge_documents", 0)
                logger.info(f"📊 Knowledge documents after add: {knowledge_count_after}")
                
                if knowledge_count_before is not None:
                    if knowledge_count_after > knowledge_count_before:
                        logger.info(f"✅ Verified: Document count increased from {knowledge_count_before} to {knowledge_count_after}")
                    elif knowledge_count_after == knowledge_count_before:
                        logger.warning(f"⚠️  WARNING: Document count unchanged ({knowledge_count_after}) - document may not have been added!")
                    else:
                        logger.warning(f"⚠️  WARNING: Document count decreased from {knowledge_count_before} to {knowledge_count_after} - possible collection recreation!")
                
                if knowledge_count_after == 0:
                    logger.error("❌ CRITICAL: add_learning_content returned success but collection is still empty!")
                    logger.error("❌ This indicates collection was recreated or add operation failed silently")
            except Exception as verify_error:
                logger.warning(f"⚠️  Could not verify document count: {verify_error}")
            
            logger.info("✅ Foundational knowledge add operation completed")
            return {
                "status": "success",
                "message": "Foundational knowledge added successfully",
                "timestamp": datetime.now().isoformat(),
                "knowledge_documents_before": knowledge_count_before,
                "knowledge_documents_after": knowledge_count_after
            }
        else:
            logger.error("❌ add_learning_content returned False - foundational knowledge add failed")
            raise HTTPException(status_code=500, detail="Failed to add foundational knowledge")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Add foundational knowledge error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to add foundational knowledge: {str(e)}")

@router.post("/api/admin/foundational-knowledge/re-embed")
async def re_embed_foundational_knowledge_endpoint(
    api_key: Optional[str] = Depends(require_api_key) if require_api_key else Depends(lambda: None)
):
    """
    Re-embed all CRITICAL_FOUNDATION documents with the current embedding model.
    
    This fixes high distance/similarity issues by ensuring all foundational knowledge
    uses the same embedding model as queries.
    
    **Authentication Required**: This is an admin endpoint protected by API key.
    Provide API key in `X-API-Key` header.
    
    **Example:**
    ```bash
    curl -X POST https://stillme-backend-production.up.railway.app/api/admin/foundational-knowledge/re-embed \
      -H "X-API-Key: your-api-key-here"
    ```
    
    **Returns:**
    - `status`: "success" or "error"
    - `message`: Human-readable message
    - `documents_found`: Number of CRITICAL_FOUNDATION documents found
    - `documents_re_embedded`: Number of documents successfully re-embedded
    - `test_results`: Distance metrics after re-embedding (for verification)
    - `timestamp`: ISO timestamp
    """
    if require_api_key:
        logger.debug(f"API key verified for foundational knowledge re-embedding")
    try:
        logger.info("🔧 Admin endpoint: Re-embedding foundational knowledge...")
        
        # Import RAG components
        chroma_client = get_chroma_client()
        if not chroma_client:
            raise HTTPException(status_code=503, detail="ChromaDB client not available")
        
        from backend.vector_db.embeddings import get_embedding_service
        embedding_service = get_embedding_service()
        
        # Get collection
        collection = chroma_client.knowledge_collection
        
        # Get all CRITICAL_FOUNDATION documents
        logger.info("📋 Finding all CRITICAL_FOUNDATION documents...")
        results = collection.get(
            where={"source": "CRITICAL_FOUNDATION"},
            include=["documents", "metadatas", "embeddings"]
        )
        
        foundational_docs = []
        if results and results.get("ids"):
            embeddings_list = results.get("embeddings")
            documents_list = results.get("documents")
            metadatas_list = results.get("metadatas")
            
            for i, doc_id in enumerate(results["ids"]):
                foundational_docs.append({
                    "id": doc_id,
                    "content": documents_list[i] if (documents_list is not None and i < len(documents_list)) else "",
                    "metadata": metadatas_list[i] if (metadatas_list is not None and i < len(metadatas_list)) else {},
                    "old_embedding": embeddings_list[i] if (embeddings_list is not None and i < len(embeddings_list)) else None
                })
        
        if not foundational_docs:
            logger.warning("⚠️  No CRITICAL_FOUNDATION documents found!")
            return {
                "status": "error",
                "message": "No CRITICAL_FOUNDATION documents found. Please add foundational knowledge first.",
                "documents_found": 0,
                "documents_re_embedded": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"✅ Found {len(foundational_docs)} CRITICAL_FOUNDATION documents")
        embedding_dim = embedding_service.get_embedding_dimension()
        logger.info(f"🔄 Re-embedding with model: {embedding_service.model_name} ({embedding_dim} dimensions)")
        
        # Re-embed each document
        re_embedded_count = 0
        errors = []
        
        for i, doc in enumerate(foundational_docs, 1):
            doc_title = doc['metadata'].get('title', doc['id'])
            logger.info(f"   [{i}/{len(foundational_docs)}] Re-embedding: {doc_title}")
            
            try:
                # Generate new embedding
                new_embedding = embedding_service.encode_text(doc["content"])
                logger.debug(f"      ✅ Generated new embedding: {len(new_embedding)} dimensions")
                
                # Delete old document
                collection.delete(ids=[doc["id"]])
                logger.debug(f"      ✅ Deleted old document")
                
                # Add new document with new embedding
                collection.add(
                    ids=[doc["id"]],
                    documents=[doc["content"]],
                    metadatas=[doc["metadata"]],
                    embeddings=[new_embedding]
                )
                logger.debug(f"      ✅ Added document with new embedding")
                re_embedded_count += 1
                
            except Exception as e:
                error_msg = f"Failed to re-embed document {doc['id']}: {str(e)}"
                logger.error(f"      ❌ {error_msg}")
                errors.append(error_msg)
                
                # Try to restore old document if possible
                if doc.get("old_embedding"):
                    try:
                        collection.add(
                            ids=[doc["id"]],
                            documents=[doc["content"]],
                            metadatas=[doc["metadata"]],
                            embeddings=[doc["old_embedding"]]
                        )
                        logger.info(f"      ✅ Restored old document")
                    except Exception as restore_error:
                        logger.error(f"      ❌ Failed to restore old document: {restore_error}")
        
        logger.info(f"✅ Re-embedding complete: {re_embedded_count}/{len(foundational_docs)} documents")
        
        # Test retrieval
        test_results = None
        try:
            logger.info("🧪 Testing retrieval with re-embedded documents...")
            test_query = "Do you track your own execution time?"
            test_embedding = embedding_service.encode_text(test_query)
            
            test_query_results = collection.query(
                query_embeddings=[test_embedding],
                n_results=5,
                where={"source": "CRITICAL_FOUNDATION"}
            )
            
            if test_query_results and test_query_results.get("distances") and test_query_results["distances"][0]:
                distances = test_query_results["distances"][0]
                min_distance = min(distances)
                max_distance = max(distances)
                avg_distance = sum(distances) / len(distances)
                
                # Estimate similarity (approximate for L2 distance)
                # For normalized vectors: cosine_sim ≈ 1 - (L2^2 / 2)
                min_similarity = 1.0 - (min_distance ** 2 / 2) if min_distance < 2.0 else -1.0
                
                test_results = {
                    "test_query": test_query,
                    "distance_range": {
                        "min": round(min_distance, 3),
                        "max": round(max_distance, 3),
                        "average": round(avg_distance, 3)
                    },
                    "estimated_similarity": round(min_similarity, 3),
                    "documents_retrieved": len(distances),
                    "status": "good" if min_distance < 1.0 else "moderate" if min_distance < 2.0 else "high"
                }
                
                logger.info(f"   ✅ Test query: '{test_query}'")
                logger.info(f"   Distance range: {min_distance:.3f} - {max_distance:.3f}")
                logger.info(f"   Average distance: {avg_distance:.3f}")
                logger.info(f"   Estimated similarity: {min_similarity:.3f}")
                
                if min_distance < 1.0:
                    logger.info("   ✅ Distance looks good! Documents should be retrievable")
                elif min_distance < 2.0:
                    logger.warning("   ⚠️  Distance is moderate - may need lower threshold")
                else:
                    logger.warning("   ⚠️  Distance is still high - may need to check embedding model or normalization")
            else:
                logger.warning("   ⚠️  No test results returned")
                test_results = {
                    "test_query": test_query,
                    "status": "no_results",
                    "message": "No documents retrieved in test query"
                }
        except Exception as test_error:
            logger.error(f"   ❌ Test retrieval failed: {test_error}")
            test_results = {
                "status": "error",
                "message": f"Test retrieval failed: {str(test_error)}"
            }
        
        # Prepare response
        response = {
            "status": "success" if re_embedded_count == len(foundational_docs) else "partial",
            "message": f"Re-embedded {re_embedded_count}/{len(foundational_docs)} documents successfully" + (f" ({len(errors)} errors)" if errors else ""),
            "documents_found": len(foundational_docs),
            "documents_re_embedded": re_embedded_count,
            "model_used": embedding_service.model_name,
            "embedding_dimensions": embedding_service.get_embedding_dimension(),
            "test_results": test_results,
            "timestamp": datetime.now().isoformat()
        }
        
        if errors:
            response["errors"] = errors
        
        logger.info("✅ Foundational knowledge re-embedding complete via admin endpoint")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Re-embed foundational knowledge error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to re-embed foundational knowledge: {str(e)}")

@router.post("/api/admin/collections/migrate-to-cosine")
async def migrate_collection_to_cosine_endpoint(
    collection_name: str = "stillme_knowledge",
    api_key: Optional[str] = Depends(require_api_key) if require_api_key else Depends(lambda: None)
):
    """
    Migrate a ChromaDB collection from L2 distance to cosine distance.
    
    This fixes high distance issues by:
    1. Backing up all documents from existing collection
    2. Deleting old collection (with L2 distance)
    3. Creating new collection with cosine distance
    4. Re-adding all documents with normalized embeddings
    
    **CRITICAL**: This operation preserves all data but requires re-embedding.
    For large collections (6000+ documents), this may take 10-30 minutes.
    
    **Authentication Required**: This is an admin endpoint protected by API key.
    Provide API key in `X-API-Key` header.
    
    **Example:**
    ```bash
    curl -X POST "https://stillme-backend-production.up.railway.app/api/admin/collections/migrate-to-cosine?collection_name=stillme_knowledge" \
      -H "X-API-Key: your-api-key-here"
    ```
    
    **Returns:**
    - `status`: "success", "error", or "partial"
    - `message`: Human-readable message
    - `collection_name`: Name of migrated collection
    - `documents_backed_up`: Number of documents backed up
    - `documents_migrated`: Number of documents successfully migrated
    - `time_elapsed_seconds`: Time taken for migration
    - `timestamp`: ISO timestamp
    """
    if require_api_key:
        logger.debug(f"API key verified for collection migration")
    try:
        logger.info(f"🔧 Admin endpoint: Migrating collection '{collection_name}' to cosine distance...")
        
        # Import RAG components
        chroma_client = get_chroma_client()
        if not chroma_client:
            raise HTTPException(status_code=503, detail="ChromaDB client not available")
        
        from backend.vector_db.embeddings import get_embedding_service
        embedding_service = get_embedding_service()
        
        # Check if collection exists
        try:
            collection = chroma_client.client.get_collection(name=collection_name)
            logger.info(f"✅ Found collection: {collection_name}")
        except Exception as e:
            logger.error(f"❌ Collection '{collection_name}' not found: {e}")
            raise HTTPException(status_code=404, detail=f"Collection '{collection_name}' not found: {e}")
        
        # Check collection metadata to see current distance metric
        metadata = collection.metadata or {}
        current_metric = metadata.get("hnsw:space", "unknown")
        logger.info(f"📊 Current distance metric: {current_metric}")
        
        if current_metric == "cosine":
            logger.info("✅ Collection already uses cosine distance - no migration needed")
            return {
                "status": "success",
                "message": f"Collection '{collection_name}' already uses cosine distance - no migration needed",
                "collection_name": collection_name,
                "documents_backed_up": collection.count(),
                "documents_migrated": collection.count(),
                "time_elapsed_seconds": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        # Step 1: Backup all documents
        logger.info(f"📦 Step 1: Backing up all documents from '{collection_name}'...")
        import time
        start_time = time.time()
        
        try:
            all_data = collection.get(include=["documents", "metadatas", "embeddings"])
            
            if not all_data or not all_data.get("ids"):
                logger.warning(f"⚠️ Collection '{collection_name}' is empty")
                return {
                    "status": "success",
                    "message": "Collection is empty - no migration needed",
                    "collection_name": collection_name,
                    "documents_backed_up": 0,
                    "documents_migrated": 0,
                    "time_elapsed_seconds": 0,
                    "timestamp": datetime.now().isoformat()
                }
            
            ids = all_data["ids"]
            documents = all_data.get("documents", [])
            metadatas = all_data.get("metadatas", [])
            
            num_docs = len(ids)
            logger.info(f"   ✅ Backed up {num_docs} documents")
            
        except Exception as e:
            logger.error(f"❌ Failed to backup documents: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to backup documents: {str(e)}")
        
        # Step 2: Delete old collection
        logger.info(f"🗑️ Step 2: Deleting old collection '{collection_name}' (with {current_metric} distance)...")
        try:
            chroma_client.client.delete_collection(name=collection_name)
            logger.info(f"   ✅ Deleted old collection")
        except Exception as e:
            logger.error(f"❌ Failed to delete collection: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to delete collection: {str(e)}")
        
        # Step 3: Create new collection with cosine distance
        logger.info(f"🆕 Step 3: Creating new collection '{collection_name}' with cosine distance...")
        try:
            description = "Knowledge base for StillMe learning" if "knowledge" in collection_name.lower() else "Conversation history for context"
            
            new_collection = chroma_client.client.create_collection(
                name=collection_name,
                metadata={
                    "description": description,
                    "hnsw:space": "cosine"  # CRITICAL: Use cosine distance for normalized embeddings
                }
            )
            logger.info(f"   ✅ Created new collection with cosine distance metric")
        except Exception as e:
            logger.error(f"❌ Failed to create new collection: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Failed to create new collection: {str(e)}")
        
        # Step 4: Re-embed and re-add documents in batches
        logger.info(f"🔄 Step 4: Re-embedding and re-adding {num_docs} documents...")
        logger.info(f"   Model: {embedding_service.model_name}")
        logger.info(f"   This may take 10-30 minutes for large collections...")
        
        batch_size = 50
        re_embedded_count = 0
        errors = []
        
        for i in range(0, num_docs, batch_size):
            batch_end = min(i + batch_size, num_docs)
            batch_ids = ids[i:batch_end]
            batch_documents = documents[i:batch_end]
            batch_metadatas = metadatas[i:batch_end] if metadatas else [{}] * (batch_end - i)
            
            logger.info(f"   Processing batch {i//batch_size + 1}/{(num_docs + batch_size - 1)//batch_size} ({i+1}-{batch_end}/{num_docs})...")
            
            try:
                # Re-embed documents with normalized embeddings
                batch_embeddings = []
                for doc in batch_documents:
                    embedding = embedding_service.encode_text(doc)
                    batch_embeddings.append(embedding)
                
                # Add to new collection
                new_collection.add(
                    ids=batch_ids,
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    embeddings=batch_embeddings
                )
                
                re_embedded_count += len(batch_ids)
                logger.info(f"      ✅ Added {len(batch_ids)} documents to new collection")
                
            except Exception as e:
                error_msg = f"Failed to process batch {i//batch_size + 1}: {str(e)}"
                logger.error(f"      ❌ {error_msg}", exc_info=True)
                errors.append(error_msg)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Migration complete: {re_embedded_count}/{num_docs} documents")
        logger.info(f"   Time elapsed: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
        
        # Step 5: Verify migration
        logger.info(f"✅ Step 5: Verifying migration...")
        try:
            verify_count = new_collection.count()
            if verify_count == num_docs:
                logger.info(f"   ✅ Verification passed: {verify_count} documents in new collection")
            else:
                logger.warning(f"   ⚠️ Verification warning: Expected {num_docs}, found {verify_count}")
        except Exception as e:
            logger.warning(f"   ⚠️ Verification failed: {e}")
        
        # Prepare response
        response = {
            "status": "success" if re_embedded_count == num_docs else "partial",
            "message": f"Migrated {re_embedded_count}/{num_docs} documents successfully" + (f" ({len(errors)} errors)" if errors else ""),
            "collection_name": collection_name,
            "documents_backed_up": num_docs,
            "documents_migrated": re_embedded_count,
            "time_elapsed_seconds": round(elapsed, 2),
            "time_elapsed_minutes": round(elapsed / 60, 2),
            "timestamp": datetime.now().isoformat()
        }
        
        if errors:
            response["errors"] = errors
        
        logger.info("✅ Collection migration complete via admin endpoint")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Migrate collection error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to migrate collection: {str(e)}")

@router.get("/api/admin/collections/status")
async def get_collection_status_endpoint(
    collection_name: str = "stillme_knowledge",
    api_key: Optional[str] = Depends(require_api_key) if require_api_key else Depends(lambda: None)
):
    """
    Get ChromaDB collection status including distance metric and document count.
    
    Useful for checking if migration completed successfully.
    
    **Authentication Required**: This is an admin endpoint protected by API key.
    Provide API key in `X-API-Key` header.
    
    **Example:**
    ```bash
    curl -X GET "https://stillme-backend-production.up.railway.app/api/admin/collections/status?collection_name=stillme_knowledge" \
      -H "X-API-Key: your-api-key-here"
    ```
    
    **Returns:**
    - `collection_name`: Name of collection
    - `exists`: Whether collection exists
    - `distance_metric`: Current distance metric ("cosine", "l2", or "unknown")
    - `document_count`: Number of documents in collection
    - `metadata`: Full collection metadata
    - `timestamp`: ISO timestamp
    """
    if require_api_key:
        logger.debug(f"API key verified for collection status check")
    try:
        logger.info(f"🔍 Admin endpoint: Checking collection '{collection_name}' status...")
        
        # Import RAG components
        chroma_client = get_chroma_client()
        if not chroma_client:
            raise HTTPException(status_code=503, detail="ChromaDB client not available")
        
        # Check if collection exists
        try:
            collection = chroma_client.client.get_collection(name=collection_name)
            logger.info(f"✅ Found collection: {collection_name}")
            
            # Get collection info
            metadata = collection.metadata or {}
            distance_metric = metadata.get("hnsw:space", "unknown")
            document_count = collection.count()
            
            response = {
                "collection_name": collection_name,
                "exists": True,
                "distance_metric": distance_metric,
                "document_count": document_count,
                "metadata": metadata,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add helpful status message
            if distance_metric == "cosine":
                response["status"] = "✅ Collection uses cosine distance (correct)"
            elif distance_metric == "l2":
                response["status"] = "⚠️ Collection uses L2 distance (should migrate to cosine)"
            else:
                response["status"] = f"⚠️ Unknown distance metric: {distance_metric}"
            
            logger.info(f"   Distance metric: {distance_metric}, Documents: {document_count}")
            return response
            
        except Exception as e:
            error_msg = str(e).lower()
            if "not found" in error_msg or "does not exist" in error_msg:
                logger.warning(f"⚠️ Collection '{collection_name}' not found")
                return {
                    "collection_name": collection_name,
                    "exists": False,
                    "distance_metric": None,
                    "document_count": 0,
                    "status": "❌ Collection does not exist",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                logger.error(f"❌ Error checking collection: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Failed to check collection status: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get collection status error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get collection status: {str(e)}")

