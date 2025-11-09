"""
StillMe Backend API
Learning AI system with RAG foundation - FastAPI backend with RAG (Retrieval-Augmented Generation) capabilities
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
import os
import logging

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
from backend.api.rate_limiter import limiter, RateLimitExceeded
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

# Import routers
from backend.api.routers import chat_router, rag_router, tiers_router, spice_router, learning_router, system_router

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

# Initialize RAG components - LAZY INITIALIZATION
# Track initialization errors for better diagnostics
# IMPORTANT: RAG initialization is now done in startup_event() to prevent blocking server startup
# This ensures /health endpoint is available immediately, even if RAG init takes time or fails
_initialization_error = None
_rag_initialization_started = False
_rag_initialization_complete = False
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

def _initialize_rag_components():
    """Initialize RAG components - called lazily during startup"""
    global _initialization_error, _rag_initialization_started, _rag_initialization_complete
    global chroma_client, embedding_service, rag_retrieval, knowledge_retention, accuracy_scorer
    global rss_fetcher, learning_scheduler, self_diagnosis, content_curator, rss_fetch_history
    global continuum_memory, source_integration
    
    if _rag_initialization_started:
        return  # Already started or completed
    
    _rag_initialization_started = True
    
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
        _rag_initialization_complete = True
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
app.include_router(chat_router.router, prefix="/api/chat", tags=["chat"])
app.include_router(rag_router.router, prefix="/api/rag", tags=["rag"])
app.include_router(tiers_router.router, prefix="/api/v1/tiers", tags=["tiers"])
app.include_router(spice_router.router, prefix="/api/spice", tags=["spice"])
app.include_router(learning_router.router, prefix="/api/learning", tags=["learning"])
app.include_router(system_router.router, tags=["system"])

# System endpoints moved to backend/api/routers/system_router.py

@app.on_event("startup")
async def startup_event():
    """Initialize RAG components and log when FastAPI/uvicorn server is ready"""
    logger.info("🚀 FastAPI application startup event triggered")
    logger.info("🌐 Uvicorn server is ready to accept connections")
    logger.info("📋 /health endpoint is available immediately")
    logger.info("⏳ Starting RAG components initialization in background...")
    
    # Initialize RAG components lazily (non-blocking)
    # This allows /health endpoint to work immediately
    import asyncio
    asyncio.create_task(asyncio.to_thread(_initialize_rag_components))
    
    # Give it a moment, then log status
    await asyncio.sleep(0.1)
    
    # Log RAG components status (may still be initializing)
    logger.info("📊 RAG Components Status (initialization may be in progress):")
    logger.info(f"  - ChromaDB: {'✓' if chroma_client else '⏳ Initializing...'}")
    logger.info(f"  - Embedding Service: {'✓' if embedding_service else '⏳ Initializing...'}")
    logger.info(f"  - RAG Retrieval: {'✓' if rag_retrieval else '⏳ Initializing...'}")
    logger.info(f"  - Knowledge Retention: {'✓' if knowledge_retention else '⏳ Initializing...'}")
    logger.info(f"  - Accuracy Scorer: {'✓' if accuracy_scorer else '⏳ Initializing...'}")

    # Log RAG components status
    logger.info("📊 RAG Components Status:")
    logger.info(f"  - ChromaDB: {'✓' if chroma_client else '✗'}")
    logger.info(f"  - Embedding Service: {'✓' if embedding_service else '✗'}")
    logger.info(f"  - RAG Retrieval: {'✓' if rag_retrieval else '✗'}")
    logger.info(f"  - Knowledge Retention: {'✓' if knowledge_retention else '✗'}")
    logger.info(f"  - Accuracy Scorer: {'✓' if accuracy_scorer else '✗'}")
    
    if _initialization_error:
        logger.warning(f"⚠️ Service started with initialization errors: {_initialization_error}")
    elif not _rag_initialization_complete and not _rag_initialization_started:
        logger.info("ℹ️ RAG initialization starting in background - /health endpoint is ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Log when FastAPI/uvicorn server is shutting down"""
    logger.info("🛑 FastAPI application shutting down")

# Chat endpoints moved to router - see backend/api/routers/chat_router.py

# Learning endpoints moved to backend/api/routers/learning_router.py

# Continuum Memory APIs (v1) - Tier Management moved to backend/api/routers/tiers_router.py

# System endpoints (root, health, status, validators/metrics) moved to backend/api/routers/system_router.py
# Accuracy metrics endpoint moved to backend/api/routers/learning_router.py

# Multi-Source Learning Pipeline endpoints moved to backend/api/routers/learning_router.py
# RSS Learning Pipeline endpoints moved to backend/api/routers/learning_router.py
# Scheduler endpoints moved to backend/api/routers/learning_router.py
# Self-Diagnosis & Content Curation endpoints moved to backend/api/routers/learning_router.py

# All endpoints have been moved to routers - see backend/api/routers/ for implementation

# ============================================================================
# SPICE (Self-Play In Corpus Environments) API Endpoints
# ============================================================================

# TODO: Initialize SPICE Engine (after RAG components are ready)
# spice_engine = None

# SPICE endpoints moved to backend/api/routers/spice_router.py

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
