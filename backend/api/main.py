"""
StillMe Backend API
Learning AI system with RAG foundation - FastAPI backend with RAG (Retrieval-Augmented Generation) capabilities
"""

from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from typing import Optional, Dict, Any, List
import os
import logging
import httpx
from datetime import datetime

# Import validated models
from backend.api.models import ChatResponse

# Import chat helpers
from backend.api.utils import (
    detect_language,
    build_system_prompt_with_language,
    call_deepseek_api,
    call_openai_api,
    generate_ai_response
)

# Import RAG components
from backend.vector_db import ChromaClient, EmbeddingService, RAGRetrieval
from backend.learning import KnowledgeRetention, AccuracyScorer
from backend.learning.continuum_memory import ContinuumMemory
from backend.services.rss_fetcher import RSSFetcher
from backend.services.learning_scheduler import LearningScheduler
from backend.services.self_diagnosis import SelfDiagnosisAgent
from backend.services.content_curator import ContentCurator
from backend.services.rss_fetch_history import RSSFetchHistory
from backend.services.source_integration import SourceIntegration
from backend.api.rate_limiter import limiter, get_rate_limit_key_func, RateLimitExceeded
from backend.api.security_middleware import get_security_middleware

# Import standardized error handlers
from backend.api.error_handlers import (
    handle_validation_error,
    handle_not_found_error,
    handle_service_unavailable,
    handle_internal_server_error,
    handle_generic_http_exception
)
from backend.api.error_tracking import error_tracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="StillMe API",
    description="Learning AI system with RAG foundation",
    version="0.4.0"
)

# CORS middleware - Security: Restrict origins to prevent unauthorized access
# Read allowed origins from environment variable, default to safe localhost only
cors_origins_env = os.getenv("CORS_ALLOWED_ORIGINS", "")
if cors_origins_env:
    # Parse comma-separated list of allowed origins
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
else:
    # Default: Only allow localhost for development
    # In production, set CORS_ALLOWED_ORIGINS environment variable
    cors_origins = [
        "http://localhost:8501",  # Streamlit dashboard
        "http://localhost:3000",  # Common React dev port
        "http://127.0.0.1:8501",
        "http://127.0.0.1:3000",
    ]
    logger.warning(
        "⚠️ CORS_ALLOWED_ORIGINS not set. Using default localhost origins only. "
        "Set CORS_ALLOWED_ORIGINS environment variable for production."
    )

# Security: Only allow credentials if origins are restricted (not "*")
allow_creds = "*" not in cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Restricted origins instead of "*"
    allow_credentials=allow_creds,  # Only allow if origins are restricted
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Specific methods instead of "*"
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],  # Specific headers instead of "*"
)

# Security middleware (HTTPS enforcement, HSTS headers, etc.)
security_middleware_list = get_security_middleware()
for middleware_class in security_middleware_list:
    app.add_middleware(middleware_class)

# Rate limiting middleware
app.state.limiter = limiter

# Custom rate limit error handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded"""
    from backend.api.rate_limiter import get_remote_address
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
    raise HTTPException(
        status_code=429,
        detail={
            "error": "rate_limit_exceeded",
            "message": f"Rate limit exceeded: {exc.detail}. Please try again later.",
            "retry_after": 60
        },
        headers={"Retry-After": "60"}
    )

# Validation error handler
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Custom handler for validation errors"""
    return handle_validation_error(request, exc)

# HTTP Exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom handler for HTTP exceptions"""
    # Route to specific handlers based on status code
    if exc.status_code == 404:
        return handle_not_found_error(request, exc)
    elif exc.status_code == 503:
        return handle_service_unavailable(request, exc)
    else:
        return handle_generic_http_exception(request, exc)

# Generic exception handler (catches all unhandled exceptions)
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions"""
    # Track error
    error_tracker.capture_exception(
        exc,
        context={
            "path": request.url.path,
            "method": request.method,
            "query_params": dict(request.query_params)
        }
    )
    return handle_internal_server_error(request, exc)

# Initialize RAG components
# Track initialization errors for better diagnostics
_initialization_error = None
chroma_client = None
embedding_service = None
rag_retrieval = None
knowledge_retention = None
accuracy_scorer = None
rss_fetcher = None
learning_scheduler = None
self_diagnosis = None
content_curator = None
rss_fetch_history = None
continuum_memory = None
source_integration = None

try:
    logger.info("Initializing RAG components...")
    
    # Check for FORCE_DB_RESET_ON_STARTUP environment variable
    force_reset = os.getenv("FORCE_DB_RESET_ON_STARTUP", "false").lower() == "true"
    if force_reset:
        logger.warning("🔄 FORCE_DB_RESET_ON_STARTUP=True detected - will reset ChromaDB database")
        chroma_client = ChromaClient(reset_on_error=True)
        logger.info("✓ ChromaDB client initialized (forced reset)")
    else:
        # Try with reset_on_error=False first (preserve data)
        # If schema error, will try with reset_on_error=True (which deletes directory first)
        chroma_client_ref = None
        try:
            chroma_client = ChromaClient(reset_on_error=False)
            logger.info("✓ ChromaDB client initialized")
        except (RuntimeError, Exception) as e:
            error_str = str(e).lower()
            if "schema mismatch" in error_str or "no such column" in error_str or "topic" in error_str:
                logger.warning("⚠️ Schema mismatch detected!")
                logger.warning("Attempting to reset database by deleting directory...")
                
                # Store reference to old client if exists (for cleanup)
                if chroma_client_ref:
                    try:
                        # Try to close/disconnect old client
                        if hasattr(chroma_client_ref, 'client'):
                            logger.info("Closing old ChromaDB client connection...")
                            # ChromaDB PersistentClient doesn't have explicit close, but we can try to delete reference
                            del chroma_client_ref
                    except Exception:
                        pass
                
                # Force garbage collection to ensure old client is freed
                import gc
                gc.collect()
                logger.info("Garbage collected old client references")
                
                # Try resetting database - this will delete the directory before creating client
                chroma_client = ChromaClient(reset_on_error=True)
                logger.info("✓ ChromaDB client initialized (after directory reset)")
                logger.warning("⚠️ IMPORTANT: If errors persist, please RESTART the backend service on Railway to clear process cache.")
            else:
                raise
    
    embedding_service = EmbeddingService()
    logger.info("✓ Embedding service initialized")
    
    rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
    logger.info("✓ RAG retrieval initialized")
    
    knowledge_retention = KnowledgeRetention()
    logger.info("✓ Knowledge retention initialized")
    
    accuracy_scorer = AccuracyScorer()
    logger.info("✓ Accuracy scorer initialized")
    
    rss_fetcher = RSSFetcher()
    logger.info("✓ RSS fetcher initialized")
    
    learning_scheduler = LearningScheduler(
        rss_fetcher=rss_fetcher,
        interval_hours=4,
        auto_add_to_rag=True,
        continuum_memory=continuum_memory if os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true" else None
    )
    logger.info("✓ Learning scheduler initialized")
    
    self_diagnosis = SelfDiagnosisAgent(rag_retrieval=rag_retrieval)
    logger.info("✓ Self-diagnosis agent initialized")
    
    content_curator = ContentCurator()
    logger.info("✓ Content curator initialized")
    
    rss_fetch_history = RSSFetchHistory()
    logger.info("✓ RSS fetch history initialized")
    
    # Initialize Source Integration (arXiv, CrossRef, Wikipedia)
    source_integration = SourceIntegration(content_curator=content_curator)
    logger.info("✓ Source Integration initialized")
    
    # Initialize Continuum Memory (if enabled)
    continuum_memory = ContinuumMemory()
    if continuum_memory and os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true":
        logger.info("✓ Continuum Memory initialized")
    else:
        logger.info("⊘ Continuum Memory disabled (ENABLE_CONTINUUM_MEMORY=false)")
    
    logger.info("✅ All RAG components initialized successfully")
    logger.info("🎉 StillMe backend is ready!")
except Exception as e:
    _initialization_error = str(e)
    logger.error(f"❌ Failed to initialize RAG components: {e}", exc_info=True)
    
    # Log which components were successfully initialized before the error
    logger.error("📊 Components status at error time:")
    logger.error(f"  - ChromaDB: {'✓' if chroma_client else '✗'}")
    logger.error(f"  - Embedding Service: {'✓' if embedding_service else '✗'}")
    logger.error(f"  - RAG Retrieval: {'✓' if rag_retrieval else '✗'}")
    logger.error(f"  - Knowledge Retention: {'✓' if knowledge_retention else '✗'}")
    logger.error(f"  - Accuracy Scorer: {'✓' if accuracy_scorer else '✗'}")
    
    if "schema mismatch" in str(e).lower() or "no such column" in str(e).lower() or "topic" in str(e).lower():
        logger.error("⚠️ CRITICAL: Schema mismatch detected!")
        logger.error("⚠️ This usually means ChromaDB database has old schema.")
        logger.error("⚠️ ACTION REQUIRED: Please RESTART the backend service on Railway.")
        logger.error("⚠️ On restart, the code will automatically reset the database.")
        
        # If RAG components were already initialized, don't reset them
        # They might still work for some operations
        if rag_retrieval is not None:
            logger.warning("⚠️ RAG retrieval was initialized before error - keeping it available")
            logger.warning("⚠️ Some operations may fail, but basic RAG might still work")
    else:
        # For non-schema errors, reset components to None
        logger.warning("⚠️ Resetting RAG components to None due to initialization error")
        # Note: We don't explicitly set to None here because they're already None
        # from the initial declaration, unless they were set before the exception

# Pydantic models
# Models are now imported from backend.api.models (see imports above)

# Include routers (imported at top level to avoid E402)
from backend.api.routers import chat_router, rag_router, tiers_router, spice_router, learning_router, system_router
app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])
app.include_router(rag_router.router, prefix="/api/rag", tags=["rag"])
app.include_router(tiers_router.router, prefix="/api/v1/tiers", tags=["tiers"])
app.include_router(spice_router.router, prefix="/api/spice", tags=["spice"])
app.include_router(learning_router.router, prefix="/api/learning", tags=["learning"])
app.include_router(system_router.router, tags=["system"])

# System endpoints moved to backend/api/routers/system_router.py

@app.on_event("startup")
async def startup_event():
    """Log when FastAPI/uvicorn server is ready"""
    logger.info("🚀 FastAPI application startup complete")
    logger.info("🌐 Uvicorn server is ready to accept connections")
    
    # Log RAG components status
    logger.info("📊 RAG Components Status:")
    logger.info(f"  - ChromaDB: {'✓' if chroma_client else '✗'}")
    logger.info(f"  - Embedding Service: {'✓' if embedding_service else '✗'}")
    logger.info(f"  - RAG Retrieval: {'✓' if rag_retrieval else '✗'}")
    logger.info(f"  - Knowledge Retention: {'✓' if knowledge_retention else '✗'}")
    logger.info(f"  - Accuracy Scorer: {'✓' if accuracy_scorer else '✗'}")
    
    if _initialization_error:
        logger.warning(f"⚠️ Service started with initialization errors: {_initialization_error}")
    elif rag_retrieval is None:
        logger.error("❌ CRITICAL: RAG retrieval is None despite successful initialization logs!")
        logger.error("   This may indicate a race condition or variable scope issue.")

@app.on_event("shutdown")
async def shutdown_event():
    """Log when FastAPI/uvicorn server is shutting down"""
    logger.info("🛑 FastAPI application shutting down")

# Chat endpoints moved to router - see backend/api/routers/chat_router.py

# Learning endpoints moved to backend/api/routers/learning_router.py

# Continuum Memory APIs (v1) - Tier Management moved to backend/api/routers/tiers_router.py

# System endpoints (root, health, status, validators/metrics) moved to backend/api/routers/system_router.py
# Accuracy metrics endpoint moved to backend/api/routers/learning_router.py

# Multi-Source Learning Pipeline endpoints
@limiter.limit("5/hour", key_func=get_rate_limit_key_func)  # Multi-source fetch: 5 requests per hour
async def fetch_all_sources(
    request: Request,
    max_items_per_source: int = Query(default=5, ge=1, le=20, description="Maximum items per source"),
    auto_add: bool = Query(default=False, description="Automatically add to RAG"),
    use_pre_filter: bool = Query(default=True, description="Apply pre-filter before adding to RAG")
):
    """Fetch content from all enabled sources (RSS, arXiv, CrossRef, Wikipedia) with detailed status tracking
    
    Args:
        max_items_per_source: Maximum items per source
        auto_add: If True, automatically add to RAG vector DB
        use_pre_filter: If True, apply pre-filter before adding
    """
    try:
        if not source_integration:
            raise HTTPException(status_code=503, detail="Source integration not available")
        
        # Create fetch cycle for tracking
        cycle_id = None
        if rss_fetch_history:
            cycle_id = rss_fetch_history.create_fetch_cycle(cycle_number=0)  # Manual fetch = cycle 0
        
        # Fetch from all sources
        entries = source_integration.fetch_all_sources(
            max_items_per_source=max_items_per_source,
            use_pre_filter=use_pre_filter
        )
        
        # Track each entry with status (similar to RSS fetch)
        tracked_entries = []
        added_count = 0
        
        if auto_add and rag_retrieval:
            # Process entries (pre-filter already applied if use_pre_filter=True)
            for entry in entries:
                content = f"{entry.get('title', '')}\n{entry.get('summary', entry.get('content', ''))}"
                
                # Check for duplicates
                is_duplicate = False
                if rag_retrieval:
                    try:
                        existing = rag_retrieval.retrieve_context(
                            query=entry.get('title', ''),
                            knowledge_limit=1,
                            conversation_limit=0
                        )
                        if existing.get("knowledge_docs"):
                            existing_doc = existing["knowledge_docs"][0]
                            existing_metadata = existing_doc.get("metadata", {})
                            existing_link = existing_metadata.get("link", "")
                            if existing_link == entry.get("link", "") or existing_link == entry.get("source_url", ""):
                                is_duplicate = True
                    except Exception:
                        pass
                
                if is_duplicate:
                    status = "Filtered: Duplicate"
                    reason = "Content already exists in RAG"
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source_url", entry.get("source", "")),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                    tracked_entries.append({**entry, "status": status, "status_reason": reason})
                    continue
                
                # Try to add to RAG
                vector_id = None
                try:
                    success = rag_retrieval.add_learning_content(
                        content=content,
                        source=entry.get("source", "unknown"),
                        content_type="knowledge",
                        metadata={
                            "link": entry.get("link", ""),
                            "source_url": entry.get("source_url", ""),
                            "published": entry.get("published", datetime.now().isoformat()),
                            "type": entry.get("metadata", {}).get("source_type", "unknown"),
                            "title": entry.get("title", "")[:200],
                            "license": entry.get("metadata", {}).get("license", "Unknown")
                        }
                    )
                    
                    if success:
                        added_count += 1
                        status = "Added to RAG"
                        vector_id = f"knowledge_{entry.get('link', entry.get('source_url', ''))[:8]}"
                        if rss_fetch_history and cycle_id:
                            rss_fetch_history.add_fetch_item(
                                cycle_id=cycle_id,
                                title=entry.get("title", ""),
                                source_url=entry.get("source_url", entry.get("source", "")),
                                link=entry.get("link", ""),
                                summary=entry.get("summary", ""),
                                status=status,
                                vector_id=vector_id,
                                added_to_rag_at=datetime.now().isoformat()
                            )
                        tracked_entries.append({**entry, "status": status, "vector_id": vector_id})
                    else:
                        status = "Filtered: Low Score"
                        reason = "Failed to add to RAG"
                        if rss_fetch_history and cycle_id:
                            rss_fetch_history.add_fetch_item(
                                cycle_id=cycle_id,
                                title=entry.get("title", ""),
                                source_url=entry.get("source_url", entry.get("source", "")),
                                link=entry.get("link", ""),
                                summary=entry.get("summary", ""),
                                status=status,
                                status_reason=reason
                            )
                        tracked_entries.append({**entry, "status": status, "status_reason": reason})
                except Exception as add_error:
                    status = "Filtered: Low Score"
                    reason = f"Error adding to RAG: {str(add_error)[:100]}"
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source_url", entry.get("source", "")),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                    tracked_entries.append({**entry, "status": status, "status_reason": reason})
        else:
            # If not auto_add, just track as fetched
            for entry in entries:
                status = "Fetched (not added)"
                if rss_fetch_history and cycle_id:
                    rss_fetch_history.add_fetch_item(
                        cycle_id=cycle_id,
                        title=entry.get("title", ""),
                        source_url=entry.get("source_url", entry.get("source", "")),
                        link=entry.get("link", ""),
                        summary=entry.get("summary", ""),
                        status=status
                    )
                tracked_entries.append({**entry, "status": status})
        
        # Complete cycle
        if rss_fetch_history and cycle_id:
            rss_fetch_history.complete_fetch_cycle(cycle_id)
        
        return {
            "status": "success",
            "entries_fetched": len(entries),
            "entries_added": added_count,
            "entries_filtered": len(tracked_entries) - added_count,
            "entries": tracked_entries[:50],  # Limit response size
            "cycle_id": cycle_id
        }
        
    except Exception as e:
        logger.error(f"Multi-source fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_source_stats():
    """Get statistics for all enabled sources"""
    try:
        if not source_integration:
            return {"status": "not_available"}
        
        stats = source_integration.get_source_stats()
        return {
            "status": "ok",
            **stats
        }
    except Exception as e:
        logger.error(f"Source stats error: {e}")
        return {"status": "error", "message": str(e)}


# RSS Learning Pipeline endpoints (kept for backward compatibility)
@limiter.limit("5/hour", key_func=get_rate_limit_key_func)  # RSS fetch: 5 requests per hour (can be expensive)
async def fetch_rss_content(
    request: Request,
    max_items: int = Query(default=5, ge=1, le=50, description="Maximum items per feed"),
    auto_add: bool = Query(default=False, description="Automatically add to RAG")
):
    """Fetch content from RSS feeds with detailed status tracking
    
    Args:
        max_items: Maximum items per feed
        auto_add: If True, automatically add to RAG vector DB
    """
    try:
        if not rss_fetcher:
            raise HTTPException(status_code=503, detail="RSS fetcher not available")
        
        # Create fetch cycle for tracking
        cycle_id = None
        if rss_fetch_history:
            cycle_id = rss_fetch_history.create_fetch_cycle(cycle_number=0)  # Manual fetch = cycle 0
        
        entries = rss_fetcher.fetch_feeds(max_items_per_feed=max_items)
        
        # Track each entry with status
        tracked_entries = []
        added_count = 0
        
        if auto_add and rag_retrieval:
            # Pre-filter if content curator available
            if content_curator:
                filtered_entries, rejected_entries = content_curator.pre_filter_content(entries)
                
                # Track rejected entries (Low Score)
                for rejected in rejected_entries:
                    status = "Filtered: Low Score"
                    reason = rejected.get("rejection_reason", "Low quality/Short content")
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=rejected.get("title", ""),
                            source_url=rejected.get("source", ""),
                            link=rejected.get("link", ""),
                            summary=rejected.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                    tracked_entries.append({
                        **rejected,
                        "status": status,
                        "status_reason": reason
                    })
                
                entries = filtered_entries
            
            # Process filtered entries
            for entry in entries:
                content = f"{entry['title']}\n{entry['summary']}"
                
                # Check for duplicates (simple check - could be enhanced with semantic similarity)
                is_duplicate = False
                if rag_retrieval:
                    try:
                        # Try to find similar content in RAG
                        existing = rag_retrieval.retrieve_context(
                            query=entry['title'],
                            knowledge_limit=1,
                            conversation_limit=0
                        )
                        if existing.get("knowledge_docs"):
                            # Check if title matches closely
                            existing_doc = existing["knowledge_docs"][0]
                            existing_metadata = existing_doc.get("metadata", {})
                            existing_link = existing_metadata.get("link", "")
                            if existing_link == entry.get("link", ""):
                                is_duplicate = True
                    except Exception:
                        pass  # If check fails, assume not duplicate
                
                if is_duplicate:
                    status = "Filtered: Duplicate"
                    reason = "Content already exists in RAG"
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source", ""),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                    tracked_entries.append({
                        **entry,
                        "status": status,
                        "status_reason": reason
                    })
                    continue
                
                # Try to add to RAG
                vector_id = None
                try:
                    success = rag_retrieval.add_learning_content(
                        content=content,
                        source=entry['source'],
                        content_type="knowledge",
                        metadata={
                            "link": entry['link'],
                            "published": entry['published'],
                            "type": "rss_feed",
                            "title": entry.get('title', '')[:200]
                        }
                    )
                    
                    if success:
                        added_count += 1
                        status = "Added to RAG"
                        # Try to get vector ID (may not be available immediately)
                        vector_id = f"knowledge_{entry.get('link', '')[:8]}"
                        if rss_fetch_history and cycle_id:
                            rss_fetch_history.add_fetch_item(
                                cycle_id=cycle_id,
                                title=entry.get("title", ""),
                                source_url=entry.get("source", ""),
                                link=entry.get("link", ""),
                                summary=entry.get("summary", ""),
                                status=status,
                                vector_id=vector_id,
                                added_to_rag_at=datetime.now().isoformat()
                            )
                        tracked_entries.append({
                            **entry,
                            "status": status,
                            "vector_id": vector_id
                        })
                    else:
                        status = "Filtered: Low Score"
                        reason = "Failed to add to RAG"
                        if rss_fetch_history and cycle_id:
                            rss_fetch_history.add_fetch_item(
                                cycle_id=cycle_id,
                                title=entry.get("title", ""),
                                source_url=entry.get("source", ""),
                                link=entry.get("link", ""),
                                summary=entry.get("summary", ""),
                                status=status,
                                status_reason=reason
                            )
                        tracked_entries.append({
                            **entry,
                            "status": status,
                            "status_reason": reason
                        })
                except Exception as add_error:
                    status = "Filtered: Low Score"
                    reason = f"Error adding to RAG: {str(add_error)[:100]}"
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source", ""),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                    tracked_entries.append({
                        **entry,
                        "status": status,
                        "status_reason": reason
                    })
        else:
            # If not auto_add, just track as fetched
            for entry in entries:
                status = "Fetched (not added)"
                if rss_fetch_history and cycle_id:
                    rss_fetch_history.add_fetch_item(
                        cycle_id=cycle_id,
                        title=entry.get("title", ""),
                        source_url=entry.get("source", ""),
                        link=entry.get("link", ""),
                        summary=entry.get("summary", ""),
                        status=status
                    )
                tracked_entries.append({
                    **entry,
                    "status": status
                })
        
        # Complete cycle
        if rss_fetch_history and cycle_id:
            rss_fetch_history.complete_fetch_cycle(cycle_id)
        
        return {
            "status": "success",
            "entries_fetched": len(entries),
            "entries_added": added_count if auto_add else 0,
            "entries": tracked_entries[:10]  # Return first 10 for preview
        }
        
    except Exception as e:
        logger.error(f"RSS fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_rss_fetch_history(limit: int = 100):
    """Get latest RSS fetch items with detailed status from the most recent cycle
    
    Args:
        limit: Maximum number of items to return
        
    Returns:
        List of fetch items with status (Source URL, Title, Fetch Timestamp, STATUS)
    """
    try:
        if not rss_fetch_history:
            raise HTTPException(status_code=503, detail="RSS fetch history not available")
        
        items = rss_fetch_history.get_latest_fetch_items(limit=limit)
        return {
            "items": items,
            "total": len(items)
        }
        
    except Exception as e:
        logger.error(f"RSS fetch history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_rss_stats():
    """Get RSS pipeline statistics"""
    try:
        if not rss_fetcher:
            return {"feeds_configured": 0, "status": "not_available"}
        
        return {
            "feeds_configured": len(rss_fetcher.feeds),
            "status": "ready",
            "feeds": rss_fetcher.feeds
        }
    except Exception as e:
        logger.error(f"RSS stats error: {e}")
        return {"feeds_configured": 0, "status": "error"}

# Automated Scheduler endpoints
async def start_scheduler():
    """
    Start automated learning scheduler
    
    Security: This endpoint requires API key authentication via X-API-Key header.
    """
    try:
        if not learning_scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not available")
        
        if learning_scheduler.is_running:
            return {"status": "already_running", "message": "Scheduler is already running"}
        
        await learning_scheduler.start()
        return {
            "status": "started",
            "message": "Scheduler started successfully",
            "interval_hours": learning_scheduler.interval_hours,
            "next_run": learning_scheduler.next_run_time.isoformat() if learning_scheduler.next_run_time else None
        }
    except Exception as e:
        logger.error(f"Start scheduler error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def stop_scheduler():
    """
    Stop automated learning scheduler
    
    Security: This endpoint requires API key authentication via X-API-Key header.
    """
    try:
        if not learning_scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not available")
        
        if not learning_scheduler.is_running:
            return {"status": "not_running", "message": "Scheduler is not running"}
        
        await learning_scheduler.stop()
        return {
            "status": "stopped",
            "message": "Scheduler stopped successfully"
        }
    except Exception as e:
        logger.error(f"Stop scheduler error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_scheduler_status():
    """Get scheduler status"""
    try:
        # Debug logging
        logger.info(f"get_scheduler_status called. learning_scheduler is None: {learning_scheduler is None}")
        logger.info(f"_initialization_error: {_initialization_error}")
        
        if not learning_scheduler:
            # Provide more detailed error message
            error_msg = "Scheduler not initialized"
            if _initialization_error:
                error_msg = f"Scheduler not initialized: {_initialization_error}"
            logger.warning(f"Returning not_available status: {error_msg}")
            return {
                "status": "not_available",
                "message": error_msg,
                "initialization_error": _initialization_error if _initialization_error else None
            }
        
        # Get status from scheduler
        status = learning_scheduler.get_status()
        logger.info(f"Scheduler status retrieved successfully: {status}")
        
        return {
            "status": "ok",
            **status
        }
    except Exception as e:
        logger.error(f"Scheduler status error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}

async def run_scheduler_now():
    """Manually trigger a learning cycle immediately with detailed status tracking"""
    try:
        if not learning_scheduler:
            raise HTTPException(status_code=503, detail="Scheduler not available")
        
        result = await learning_scheduler.run_learning_cycle()
        cycle_number = result.get("cycle_number", 0)
        
        # Create fetch cycle for tracking
        cycle_id = None
        if rss_fetch_history:
            cycle_id = rss_fetch_history.create_fetch_cycle(cycle_number=cycle_number)
        
        # If auto_add_to_rag is enabled, add to RAG
        if learning_scheduler.auto_add_to_rag and rag_retrieval:
            # Use entries from the learning cycle result (already fetched)
            # Don't fetch again - use the entries that were already fetched in run_learning_cycle
            entries_to_add = []
            filtered_count = 0
            
            # Fetch from all sources using SourceIntegration
            try:
                # Use SourceIntegration to fetch from all enabled sources
                if source_integration:
                    all_entries = source_integration.fetch_all_sources(
                        max_items_per_source=5,
                        use_pre_filter=False  # We'll apply pre-filter manually to track rejected items
                    )
                    logger.info(f"Fetched {len(all_entries)} entries from all sources (RSS + arXiv + CrossRef + Wikipedia)")
                else:
                    # Fallback to RSS only
                    all_entries = learning_scheduler.rss_fetcher.fetch_feeds(max_items_per_feed=5)
                    logger.info(f"Fetched {len(all_entries)} entries from RSS (SourceIntegration not available)")
                
                # STEP 1: Pre-Filter (BEFORE embedding) to reduce costs
                if content_curator:
                    filtered_entries, rejected_entries = content_curator.pre_filter_content(all_entries)
                    filtered_count = len(rejected_entries)
                    logger.info(
                        f"Pre-Filter: {len(filtered_entries)}/{len(all_entries)} passed. "
                        f"Rejected {filtered_count} items (saving embedding costs)"
                    )
                    
                    # Track rejected entries (Low Score)
                    for rejected in rejected_entries:
                        status = "Filtered: Low Score"
                        reason = rejected.get("rejection_reason", "Low quality/Short content")
                        if rss_fetch_history and cycle_id:
                            rss_fetch_history.add_fetch_item(
                                cycle_id=cycle_id,
                                title=rejected.get("title", ""),
                                source_url=rejected.get("source", ""),
                                link=rejected.get("link", ""),
                                summary=rejected.get("summary", ""),
                                status=status,
                                status_reason=reason
                    )
                    
                    # Use filtered entries for further processing
                    all_entries = filtered_entries
                else:
                    logger.warning("Content curator not available, skipping pre-filter (may increase costs)")
                
                # STEP 2: Prioritize content if curator and self_diagnosis available
                if content_curator and self_diagnosis:
                    # Get knowledge gaps to prioritize
                    recent_gaps = []  # Could be from query history
                    prioritized = content_curator.prioritize_learning_content(
                        all_entries,
                        knowledge_gaps=recent_gaps
                    )
                    # Take top entries (up to 5, but can be fewer if prioritized list is shorter)
                    entries_to_add = prioritized[:min(5, len(prioritized))]
                    logger.info(f"Content curator prioritized {len(entries_to_add)} entries from {len(all_entries)} total")
                else:
                    # If no curator, add all entries (or limit to reasonable number)
                    entries_to_add = all_entries[:min(10, len(all_entries))]
                    logger.info(f"No content curator, adding {len(entries_to_add)} entries directly")
                
            except Exception as e:
                logger.error(f"Error preparing entries for RAG: {e}")
                entries_to_add = []
            
            added_count = 0
            for entry in entries_to_add:
                try:
                    content = f"{entry.get('title', '')}\n{entry.get('summary', '')}"
                    if not content.strip():
                        logger.warning(f"Skipping empty entry: {entry.get('title', 'No title')}")
                        continue
                    
                    # Check for duplicates
                    is_duplicate = False
                    try:
                        existing = rag_retrieval.retrieve_context(
                            query=entry.get('title', ''),
                            knowledge_limit=1,
                            conversation_limit=0
                        )
                        if existing.get("knowledge_docs"):
                            existing_doc = existing["knowledge_docs"][0]
                            existing_metadata = existing_doc.get("metadata", {})
                            existing_link = existing_metadata.get("link", "")
                            if existing_link == entry.get("link", ""):
                                is_duplicate = True
                    except Exception:
                        pass
                    
                    if is_duplicate:
                        status = "Filtered: Duplicate"
                        reason = "Content already exists in RAG"
                        if rss_fetch_history and cycle_id:
                            rss_fetch_history.add_fetch_item(
                                cycle_id=cycle_id,
                                title=entry.get("title", ""),
                                source_url=entry.get("source", ""),
                                link=entry.get("link", ""),
                                summary=entry.get("summary", ""),
                                status=status,
                                status_reason=reason
                            )
                        continue
                    
                    # Calculate importance score for knowledge alert system
                    importance_score = 0.5
                    if content_curator:
                        importance_score = content_curator.calculate_importance_score(entry)
                    
                    vector_id = None
                    success = rag_retrieval.add_learning_content(
                        content=content,
                        source=entry.get('source', 'rss'),
                        content_type="knowledge",
                        metadata={
                            "link": entry.get('link', ''),
                            "published": entry.get('published', ''),
                            "type": "rss_feed",
                            "scheduler_cycle": result.get("cycle_number", 0),
                            "priority_score": entry.get("priority_score", 0.5),
                            "importance_score": importance_score,
                            "title": entry.get('title', '')[:200]  # Store title for knowledge alert
                        }
                    )
                    if success:
                        added_count += 1
                        status = "Added to RAG"
                        vector_id = f"knowledge_{entry.get('link', '')[:8]}"
                        if rss_fetch_history and cycle_id:
                            rss_fetch_history.add_fetch_item(
                                cycle_id=cycle_id,
                                title=entry.get("title", ""),
                                source_url=entry.get("source", ""),
                                link=entry.get("link", ""),
                                summary=entry.get("summary", ""),
                                status=status,
                                vector_id=vector_id,
                                added_to_rag_at=datetime.now().isoformat()
                            )
                        logger.info(f"Added entry to RAG: {entry.get('title', 'No title')[:50]}")
                    else:
                        status = "Filtered: Low Score"
                        reason = "Failed to add to RAG"
                        if rss_fetch_history and cycle_id:
                            rss_fetch_history.add_fetch_item(
                                cycle_id=cycle_id,
                                title=entry.get("title", ""),
                                source_url=entry.get("source", ""),
                                link=entry.get("link", ""),
                                summary=entry.get("summary", ""),
                                status=status,
                                status_reason=reason
                            )
                        logger.warning(f"Failed to add entry to RAG: {entry.get('title', 'No title')[:50]}")
                except Exception as e:
                    status = "Filtered: Low Score"
                    reason = f"Error adding to RAG: {str(e)[:100]}"
                    if rss_fetch_history and cycle_id:
                        rss_fetch_history.add_fetch_item(
                            cycle_id=cycle_id,
                            title=entry.get("title", ""),
                            source_url=entry.get("source", ""),
                            link=entry.get("link", ""),
                            summary=entry.get("summary", ""),
                            status=status,
                            status_reason=reason
                        )
                    logger.error(f"Error adding entry to RAG: {e}")
                    continue
            
            result["entries_added_to_rag"] = added_count
            result["entries_filtered"] = filtered_count
            
            # Complete cycle
            if rss_fetch_history and cycle_id:
                rss_fetch_history.complete_fetch_cycle(cycle_id)
            
            logger.info(
                f"Learning cycle: Fetched {result.get('entries_fetched', 0)} entries, "
                f"Filtered {filtered_count} (Low quality/Short), "
                f"Added {added_count} to RAG"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Run scheduler now error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Self-Diagnosis & Content Curation endpoints
async def check_knowledge_gap(query: str, threshold: float = 0.5):
    """Check if there's a knowledge gap for a query"""
    try:
        if not self_diagnosis:
            raise HTTPException(status_code=503, detail="Self-diagnosis not available")
        
        result = self_diagnosis.identify_knowledge_gaps(query, threshold)
        return result
    except Exception as e:
        logger.error(f"Knowledge gap check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_coverage(topics: List[str]):
    """Analyze knowledge coverage across multiple topics"""
    try:
        if not self_diagnosis:
            raise HTTPException(status_code=503, detail="Self-diagnosis not available")
        
        result = self_diagnosis.analyze_knowledge_coverage(topics)
        return result
    except Exception as e:
        logger.error(f"Coverage analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def suggest_learning_focus(recent_queries: Optional[List[str]] = None, limit: int = 5):
    """Suggest learning focus based on knowledge gaps"""
    try:
        if not self_diagnosis:
            return {"suggestions": [], "reason": "Self-diagnosis not available"}
        
        # If no queries provided, return empty
        if not recent_queries:
            recent_queries = []
        
        suggestions = self_diagnosis.suggest_learning_focus(recent_queries, limit)
        return {
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        logger.error(f"Learning focus suggestion error: {e}")
        return {"suggestions": [], "error": str(e)}

async def prioritize_content(content_list: List[Dict[str, Any]]):
    """Prioritize learning content"""
    try:
        if not content_curator:
            raise HTTPException(status_code=503, detail="Content curator not available")
        
        # Get knowledge gaps from self-diagnosis
        knowledge_gaps = []
        if self_diagnosis and content_list:
            # Extract topics from content
            topics = [item.get("title", "")[:50] for item in content_list[:10]]
            coverage = self_diagnosis.analyze_knowledge_coverage(topics)
            knowledge_gaps = coverage.get("gap_topics", [])
        
        prioritized = content_curator.prioritize_learning_content(
            content_list,
            knowledge_gaps=knowledge_gaps
        )
        return {
            "prioritized_content": prioritized,
            "total_items": len(prioritized)
        }
    except Exception as e:
        logger.error(f"Content prioritization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_curation_stats():
    """Get content curation statistics"""
    try:
        if not content_curator:
            return {"status": "not_available"}
        
        stats = content_curator.get_curation_stats()
        return {
            "status": "ok",
            **stats
        }
    except Exception as e:
        logger.error(f"Curation stats error: {e}")
        return {"status": "error", "message": str(e)}

async def update_source_quality(source: str, quality_score: float):
    """
    Update quality score for a source
    
    Security: This endpoint requires API key authentication via X-API-Key header.
    """
    try:
        if not content_curator:
            raise HTTPException(status_code=503, detail="Content curator not available")
        
        if not 0.0 <= quality_score <= 1.0:
            raise HTTPException(status_code=400, detail="Quality score must be between 0.0 and 1.0")
        
        content_curator.update_source_quality(source, quality_score)
        return {
            "status": "updated",
            "source": source,
            "quality_score": quality_score
        }
    except Exception as e:
        logger.error(f"Update source quality error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Continuum Memory APIs (v1) - Tier Management moved to backend/api/routers/tiers_router.py


# Chat endpoints moved to backend/api/routers/chat_router.py

# Helper functions are now in backend/api/utils/chat_helpers.py

# Legacy functions removed - use backend.api.utils instead

# ============================================================================
# SPICE (Self-Play In Corpus Environments) API Endpoints
# ============================================================================

# TODO: Initialize SPICE Engine (after RAG components are ready)
# spice_engine = None

# SPICE endpoints moved to backend/api/routers/spice_router.py

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
