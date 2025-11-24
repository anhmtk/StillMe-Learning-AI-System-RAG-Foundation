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

# Import middleware
from backend.api.request_tracking_middleware import RequestTrackingMiddleware

# Import routers
from backend.api.routers import chat_router, rag_router, tiers_router, spice_router, learning_router, system_router
from backend.api.routers import debug_router, learning_permission_router, community_router
from backend.api.routers import feedback_router
from backend.config.security import validate_api_key_config

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
    env = os.getenv("ENV", "development").lower()
    is_production = env == "production"
    
    # Auto-detect Railway origins (check regardless of ENV, since Railway may not set ENV=production)
    cors_origin_regex = None
    # Check if we're running on Railway
    # Railway sets various env vars: RAILWAY_ENVIRONMENT, RAILWAY_PROJECT_NAME, PORT, etc.
    railway_env = os.getenv("RAILWAY_ENVIRONMENT", "")
    railway_project = os.getenv("RAILWAY_PROJECT_NAME", "")
    # Also check if PORT is set (Railway always sets this, but other platforms might too)
    port_env = os.getenv("PORT", "")
    # If any Railway indicator is present, allow Railway origins
    if railway_env or railway_project or (port_env and port_env.isdigit()):
        # Allow all Railway subdomains using regex
        # Railway URLs pattern: https://<service-name>-<environment>.up.railway.app
        # Also match dashboard and other Railway services
        cors_origin_regex = r"https?://.*\.up\.railway\.app"
        logger.info(
            "✅ Railway environment detected. "
            "Auto-allowing Railway origins (regex: *.up.railway.app) for CORS. "
            "For production, consider setting CORS_ALLOWED_ORIGINS explicitly for better security."
        )
        # Also add common Railway origins explicitly to ensure compatibility
        # This is a fallback in case regex doesn't match properly
        dashboard_origin = "https://dashboard-production-e4ca.up.railway.app"
        if dashboard_origin not in cors_origins:
            cors_origins.append(dashboard_origin)
            logger.info(f"✅ Added dashboard origin to CORS allowed origins: {dashboard_origin}")
    elif is_production:
        logger.warning(
            "⚠️ PRODUCTION WARNING: CORS_ALLOWED_ORIGINS not set! "
            "This is a security risk in production. "
            "Set CORS_ALLOWED_ORIGINS environment variable with comma-separated list of allowed origins. "
            "Example: CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com"
        )
    else:
        logger.warning(
            "⚠️ CORS_ALLOWED_ORIGINS not set. Using default localhost origins only. "
            "Set CORS_ALLOWED_ORIGINS environment variable for production."
        )

# Security: Only allow credentials if origins are restricted (not "*")
allow_creds = "*" not in cors_origins

# Configure CORS middleware
cors_middleware_kwargs = {
    "allow_origins": cors_origins,  # Restricted origins instead of "*"
    "allow_credentials": allow_creds,  # Only allow if origins are restricted
    "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Specific methods instead of "*"
    "allow_headers": ["Content-Type", "Authorization", "X-API-Key"],  # Specific headers instead of "*"
}

# Add regex pattern for Railway origins if detected
if cors_origin_regex:
    cors_middleware_kwargs["allow_origin_regex"] = cors_origin_regex
    logger.info(f"✅ CORS origin regex pattern: {cors_origin_regex}")

app.add_middleware(
    CORSMiddleware,
    **cors_middleware_kwargs
)

# Request tracking middleware (for metrics collection)
app.add_middleware(RequestTrackingMiddleware)

# HTTP Response Cache Middleware (Phase 3)
from backend.api.middleware.http_cache_middleware import HTTPCacheMiddleware
app.add_middleware(HTTPCacheMiddleware)

# Request Deduplication Middleware (Performance optimization)
from backend.api.middleware.request_deduplication import RequestDeduplicationMiddleware
app.add_middleware(RequestDeduplicationMiddleware)

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
        # PRODUCTION SAFETY: Force disable in production to prevent data loss
        env = os.getenv("ENV", "development").lower()
        is_production = env == "production"
        
        if is_production:
            # Override FORCE_DB_RESET_ON_STARTUP in production
            force_reset = False
            if os.getenv("FORCE_DB_RESET_ON_STARTUP", "false").lower() == "true":
                logger.warning("⚠️ FORCE_DB_RESET_ON_STARTUP is set but ENV=production - forcing to false for safety")
        else:
            force_reset = os.getenv("FORCE_DB_RESET_ON_STARTUP", "false").lower() == "true"
        
        # For Dashboard service, detect but DO NOT reset database in production
        # CRITICAL: Dashboard should NOT reset database - it should share the same database as backend
        # Detect Dashboard service by multiple methods:
        # 1. Explicit DASHBOARD_MODE env var
        # 2. STREAMLIT_SERVER_PORT env var (Streamlit sets this)
        # 3. RAILWAY_SERVICE_NAME contains "dashboard" (Railway sets this)
        # 4. Check if running as Dashboard by checking service name pattern
        is_dashboard = (
            os.getenv("STREAMLIT_SERVER_PORT") is not None or 
            os.getenv("DASHBOARD_MODE", "false").lower() == "true" or
            "dashboard" in os.getenv("RAILWAY_SERVICE_NAME", "").lower() or
            "dashboard" in os.getenv("SERVICE_NAME", "").lower()
        )
        
        # CRITICAL FIX: Dashboard should NOT reset database, especially in production
        # Dashboard should use the SAME database as backend, not reset it
        # Only use reset_on_error=True for dashboard if explicitly requested AND not in production
        dashboard_reset = False
        if is_dashboard:
            logger.info("📊 Dashboard service detected")
            if is_production:
                logger.info("📊 Production mode: Dashboard will NOT reset database (preserves data)")
                dashboard_reset = False
            else:
                # In development, dashboard can use reset_on_error for schema mismatches
                dashboard_reset = os.getenv("DASHBOARD_RESET_DB", "false").lower() == "true"
                if dashboard_reset:
                    logger.warning("⚠️ DASHBOARD_RESET_DB=true detected - dashboard will reset database (development only)")
        
        # CRITICAL: Initialize EmbeddingService FIRST so we can pass it to ChromaClient
        # This prevents ChromaDB from using default ONNX model (all-MiniLM-L6-v2)
        embedding_service = EmbeddingService()
        logger.info("✓ Embedding service initialized")
        
        # CRITICAL FIX: Only use reset_on_error=True if explicitly requested (force_reset or dashboard_reset)
        # NEVER reset in production unless explicitly forced (which is disabled above)
        if force_reset or dashboard_reset:
            if force_reset:
                logger.warning("🔄 FORCE_DB_RESET_ON_STARTUP=True detected - will reset ChromaDB database")
            if dashboard_reset:
                logger.warning("🔄 Dashboard reset enabled - will reset ChromaDB database")
            chroma_client = ChromaClient(reset_on_error=True, embedding_service=embedding_service)
            logger.info("✓ ChromaDB client initialized (forced reset)")
        else:
            # Try with reset_on_error=False first (preserve data)
            # If schema error, will try with reset_on_error=True (which deletes directory first)
            chroma_client_ref = None
            try:
                chroma_client = ChromaClient(reset_on_error=False, embedding_service=embedding_service)
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
                    
                    # Try resetting database with retry logic (up to 3 attempts)
                    max_retries = 3
                    retry_delay = 1.0  # seconds
                    chroma_client = None
                    
                    for attempt in range(1, max_retries + 1):
                        try:
                            logger.info(f"🔄 Reset attempt {attempt}/{max_retries}...")
                            chroma_client = ChromaClient(reset_on_error=True, embedding_service=embedding_service)
                            logger.info("✓ ChromaDB client initialized (after directory reset)")
                            break
                        except Exception as reset_error:
                            reset_error_str = str(reset_error).lower()
                            if attempt < max_retries:
                                logger.warning(f"⚠️ Reset attempt {attempt} failed: {reset_error}")
                                logger.info(f"⏳ Waiting {retry_delay:.1f}s before retry...")
                                import time
                                time.sleep(retry_delay)
                                # Increase delay for next attempt
                                retry_delay *= 1.5
                                # Force GC again before retry
                                gc.collect()
                            else:
                                # Final attempt failed - raise to be caught by outer exception handler
                                logger.error(f"❌ All {max_retries} reset attempts failed!")
                                logger.error(f"   Last error: {reset_error}")
                                raise RuntimeError(
                                    f"ChromaDB schema mismatch and reset failed after {max_retries} attempts: {reset_error}. "
                                    "Please manually delete data/vector_db directory on Railway and restart the service."
                                ) from reset_error
                    
                    if chroma_client is None:
                        logger.warning("⚠️ IMPORTANT: If errors persist, please RESTART the backend service on Railway to clear process cache.")
                else:
                    raise
        
        # EmbeddingService was already initialized above (before ChromaClient)
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        logger.info("✓ RAG retrieval initialized")
        
        # CRITICAL: Verify ChromaDB persistence after initialization
        if chroma_client:
            try:
                stats = chroma_client.get_collection_stats()
                logger.info(f"📊 ChromaDB Initialization Verification:")
                logger.info(f"   - Knowledge documents: {stats.get('knowledge_documents', 0)}")
                logger.info(f"   - Conversation documents: {stats.get('conversation_documents', 0)}")
                logger.info(f"   - Total documents: {stats.get('total_documents', 0)}")
                
                if stats.get('knowledge_documents', 0) > 0:
                    logger.info(f"✅ ChromaDB persistence verified - existing knowledge found!")
                else:
                    logger.info(f"📊 ChromaDB is empty - will be populated during learning cycles")
                    
                # Verify persistence directory
                persist_path = chroma_client.persist_directory
                if os.path.exists(persist_path):
                    logger.info(f"✅ Persistence path exists: {persist_path}")
                    if os.access(persist_path, os.W_OK):
                        logger.info(f"✅ Persistence path is writable")
                    else:
                        logger.error(f"❌ Persistence path is NOT writable - data loss risk!")
                else:
                    logger.error(f"❌ Persistence path does NOT exist - data loss risk!")
            except Exception as verify_error:
                logger.warning(f"⚠️ Could not verify ChromaDB persistence: {verify_error}")
        
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
        
        # CRITICAL: Pre-load models to avoid lazy loading on first request
        # This prevents 5-10 second delay on first chat message
        logger.info("🔥 Warming up models (pre-loading to avoid first-request delay)...")
        try:
            # 1. Pre-load embedding model by encoding a test string
            if embedding_service:
                logger.info("  ⏳ Pre-loading embedding model...")
                test_embedding = embedding_service.encode_text("warm-up")
                logger.info(f"  ✅ Embedding model warmed up (dimension: {len(test_embedding)})")
            
            # 2. Pre-load ChromaDB ONNX model by doing a test query AND adding a test conversation
            # CRITICAL: ChromaDB ONNX model is downloaded when add_conversation is called, not retrieve_context
            # So we need to trigger both to fully warm up
            if rag_retrieval and chroma_client:
                logger.info("  ⏳ Pre-loading ChromaDB ONNX model (this may take 10-30 seconds on first run)...")
                try:
                    # Step 1: Do a test query to warm up retrieval
                    test_context = rag_retrieval.retrieve_context(
                        query="warm-up query",
                        knowledge_limit=1,
                        conversation_limit=0
                    )
                    logger.info("  ✅ ChromaDB retrieval warmed up")
                    
                    # Step 2: Add a test conversation to trigger ONNX model download
                    # This is what actually downloads the ONNX model (79.3MB)
                    import time
                    test_conversation_id = f"warmup_{int(time.time())}"
                    chroma_client.add_conversation(
                        documents=["warm-up conversation"],
                        metadatas=[{"source": "warmup", "timestamp": "warmup"}],
                        ids=[test_conversation_id]
                    )
                    logger.info("  ✅ ChromaDB ONNX model warmed up (triggered by add_conversation)")
                except Exception as warmup_error:
                    # ONNX download may fail if network is slow - that's OK, it will download on first real request
                    logger.warning(f"  ⚠️ ChromaDB warm-up failed (will load on first request): {warmup_error}")
            
            logger.info("✅ Model warm-up complete - ready for requests!")
        except Exception as warmup_error:
            logger.warning(f"⚠️ Model warm-up failed (models will load on first request): {warmup_error}")
        
        logger.info("✅ All RAG components initialized successfully")
        
        # Set services in dependency injection module
        try:
            from backend.api.dependencies import set_services
            set_services(
                rag_retrieval=rag_retrieval,
                chroma_client=chroma_client,
                embedding_service=embedding_service,
                knowledge_retention=knowledge_retention,
                accuracy_scorer=accuracy_scorer,
                learning_scheduler=learning_scheduler,
                rss_fetcher=rss_fetcher,
                content_curator=content_curator,
                self_diagnosis=self_diagnosis,
                continuum_memory=continuum_memory,
                source_integration=source_integration,
                rss_fetch_history=rss_fetch_history
            )
            logger.info("✅ Dependency injection services registered")
        except Exception as di_error:
            logger.warning(f"⚠️ Could not register dependency injection services: {di_error}")
        
        # CRITICAL: Auto-add foundational knowledge if missing
        # This ensures StillMe can answer questions about itself on Railway deployment
        # MUST run BEFORE any RAG queries to ensure database has content
        try:
            logger.info("🔍 Checking for foundational knowledge in ChromaDB...")
            
            # First, check database state
            try:
                stats = chroma_client.get_collection_stats()
                total_docs = stats.get("total_documents", 0)
                knowledge_docs = stats.get("knowledge_documents", 0)
                logger.info(f"📊 Database state: {knowledge_docs} knowledge docs, {total_docs} total docs")
            except Exception as stats_error:
                logger.warning(f"Could not get database stats: {stats_error}")
            
            query_embedding = embedding_service.encode_text("StillMe RAG continuous learning embedding model")
            current_model_name = embedding_service.model_name
            
            # EMERGENCY: Check for embedding model mismatch
            # If we have documents but can't find foundational knowledge with good similarity,
            # it likely means embeddings were created with a different model
            embedding_mismatch_detected = False
            foundational_exists = False
            try:
                # Try to find documents with CRITICAL_FOUNDATION source
                foundational_results = chroma_client.search_knowledge(
                    query_embedding=query_embedding,
                    limit=10  # Get more results to check distances
                )
                
                if foundational_results:
                    # Check if any results have reasonable similarity (distance < 0.5)
                    # If all results have very high distance (>= 0.95), it's likely a mismatch
                    distances = [r.get("distance", 1.0) for r in foundational_results]
                    avg_distance = sum(distances) / len(distances) if distances else 1.0
                    min_distance = min(distances) if distances else 1.0
                    
                    # Filter for CRITICAL_FOUNDATION source
                    foundational_docs = []
                    for result in foundational_results:
                        metadata = result.get("metadata", {})
                        if metadata.get("source") == "CRITICAL_FOUNDATION":
                            foundational_docs.append(result)
                    
                    # If we have foundational docs but all have high distance, it's a mismatch
                    if foundational_docs and avg_distance >= 0.95 and min_distance >= 0.9:
                        embedding_mismatch_detected = True
                        logger.error(f"🚨 CRITICAL: Embedding model mismatch detected for foundational knowledge!")
                        logger.error(f"   - Current model: {current_model_name}")
                        logger.error(f"   - Average distance: {avg_distance:.3f} (extremely high)")
                        logger.error(f"   - Min distance: {min_distance:.3f}")
                        logger.error(f"   - Found {len(foundational_docs)} foundational docs but none match")
                        logger.error(f"   - ACTION: Will delete and re-embed foundational knowledge with current model")
                    elif foundational_docs:
                        # Check if content mentions current model
                        for result in foundational_docs:
                            content = result.get("content", "")
                            metadata = result.get("metadata", {})
                            distance = result.get("distance", 1.0)
                            
                            # If distance is reasonable (< 0.5) and content mentions current model
                            if distance < 0.5 and current_model_name in content and metadata.get("source") == "CRITICAL_FOUNDATION":
                                foundational_exists = True
                                logger.info(f"✅ Foundational knowledge found: {metadata.get('title', 'N/A')} (distance: {distance:.3f})")
                                break
                else:
                    # No results at all - check if database has documents
                    if knowledge_docs > 0:
                        logger.warning(f"⚠️ Database has {knowledge_docs} documents but foundational knowledge search returned no results")
                        logger.warning(f"⚠️ This may indicate embedding model mismatch")
            except Exception as filter_error:
                # If metadata filter fails, try without filter
                logger.debug(f"Metadata filter not supported, trying content search: {filter_error}")
                all_results = chroma_client.search_knowledge(
                    query_embedding=query_embedding,
                    limit=20
                )
                if all_results:
                    distances = [r.get("distance", 1.0) for r in all_results]
                    avg_distance = sum(distances) / len(distances) if distances else 1.0
                    min_distance = min(distances) if distances else 1.0
                    
                    # If all results have very high distance, likely mismatch
                    if avg_distance >= 0.95 and min_distance >= 0.9 and knowledge_docs > 0:
                        embedding_mismatch_detected = True
                        logger.error(f"🚨 CRITICAL: Embedding model mismatch detected!")
                        logger.error(f"   - Current model: {current_model_name}")
                        logger.error(f"   - Average distance: {avg_distance:.3f}")
                        logger.error(f"   - Database has {knowledge_docs} documents but none match")
                    else:
                        for result in all_results:
                            content = result.get("content", "")
                            metadata = result.get("metadata", {})
                            distance = result.get("distance", 1.0)
                            if (distance < 0.5 and current_model_name in content and 
                                ("CRITICAL_FOUNDATION" in str(metadata.get("source", "")) or 
                                 "foundational" in str(metadata.get("type", "")).lower())):
                                foundational_exists = True
                                logger.info("✅ Foundational knowledge found (via content search)")
                                break
            
            # EMERGENCY: If embedding mismatch detected, delete old foundational knowledge first
            if embedding_mismatch_detected:
                logger.warning(f"🔧 EMERGENCY MODE: Deleting old foundational knowledge to re-embed with current model...")
                try:
                    # Get all foundational knowledge IDs
                    all_results = chroma_client.search_knowledge(
                        query_embedding=query_embedding,
                        limit=100  # Get many results to find all foundational docs
                    )
                    foundational_ids_to_delete = []
                    for result in all_results:
                        metadata = result.get("metadata", {})
                        if metadata.get("source") == "CRITICAL_FOUNDATION":
                            doc_id = result.get("id")
                            if doc_id:
                                foundational_ids_to_delete.append(doc_id)
                    
                    if foundational_ids_to_delete:
                        logger.info(f"🗑️ Deleting {len(foundational_ids_to_delete)} old foundational knowledge documents...")
                        chroma_client.knowledge_collection.delete(ids=foundational_ids_to_delete)
                        logger.info(f"✅ Deleted {len(foundational_ids_to_delete)} old foundational knowledge documents")
                        foundational_exists = False  # Force re-add
                    else:
                        logger.warning("⚠️ Could not find foundational knowledge IDs to delete")
                except Exception as delete_error:
                    logger.error(f"❌ Failed to delete old foundational knowledge: {delete_error}")
                    logger.error(f"❌ Manual action may be required: Delete CRITICAL_FOUNDATION documents from ChromaDB")
            
            if not foundational_exists:
                if embedding_mismatch_detected:
                    logger.info("🔄 Re-embedding foundational knowledge with current model...")
                else:
                    logger.info("⚠️ Foundational knowledge not found. Adding it now...")
                # Load foundational knowledge from separate files
                # Phase 2: Only load technical foundational knowledge (philosophical is now style_guide, moved to docs/style/)
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                technical_path = os.path.join(base_dir, "docs", "rag", "foundational_technical.md")
                
                # Load technical foundational knowledge
                if os.path.exists(technical_path):
                    with open(technical_path, "r", encoding="utf-8") as f:
                        technical_content = f.read()
                    # Remove frontmatter if present
                    if technical_content.startswith("---"):
                        parts = technical_content.split("---", 2)
                        if len(parts) >= 3:
                            technical_content = parts[2].strip()
                    
                    tags_list_technical = ["foundational:stillme", "CRITICAL_FOUNDATION", "stillme", "rag", "self-evolving", "continuous-learning", "automated-learning", "rss", "vector-db", "technical"]
                    tags_string_technical = ",".join(tags_list_technical)
                    
                    success_technical = rag_retrieval.add_learning_content(
                        content=technical_content,
                        source="CRITICAL_FOUNDATION",
                        content_type="knowledge",
                        metadata={
                            "title": "StillMe Core Mechanism - Technical Architecture",
                            "foundational": "stillme",
                            "type": "foundational",
                            "source": "CRITICAL_FOUNDATION",
                            "tags": tags_string_technical,
                            "importance_score": 1.0,
                            "content_type": "technical",
                            "domain": "stillme_architecture",
                            "description": "CRITICAL: Technical knowledge about StillMe's RAG-based continuous learning mechanism - MUST be retrieved when answering about StillMe's architecture"
                        }
                    )
                    if success_technical:
                        logger.info("✅ Technical foundational knowledge added successfully!")
                    else:
                        logger.warning("⚠️ Failed to add technical foundational knowledge")
                else:
                    logger.warning(f"⚠️ Technical foundational knowledge file not found: {technical_path}")
                
                # Phase 2: Philosophical foundational knowledge is now a style_guide (moved to docs/style/)
                # It should NOT be loaded into RAG to prevent prompt drift
                # Style guides are excluded from RAG retrieval via exclude_content_types=["style_guide"]
                
                # Fallback: If files don't exist, use old string-based approach (for backward compatibility)
                # Initialize FOUNDATIONAL_KNOWLEDGE outside if block to avoid UnboundLocalError
                FOUNDATIONAL_KNOWLEDGE = None
                if not os.path.exists(technical_path):
                    logger.warning("⚠️ Foundational knowledge files not found, using fallback string-based approach")
                    # CRITICAL: FOUNDATIONAL_KNOWLEDGE string (600+ lines) has been COMMENTED OUT to prevent:
                    # 1. Context overflow (16,385 token limit)
                    # 2. Prompt drift (RAG content should be the single source of truth)
                    # 3. Duplication (same content exists in RAG via add_foundational_knowledge.py script)
                    # 
                    # If foundational knowledge files don't exist, the system will still work but may not
                    # answer questions about StillMe correctly. The proper solution is to ensure foundational
                    # knowledge files exist (docs/rag/foundational_technical.md and docs/rag/foundational_philosophical.md)
                    # and use the RAG-based approach above.
                    #
                    # FOUNDATIONAL_KNOWLEDGE string removed - use RAG-based approach instead
                    # Old string-based approach (600+ lines) commented out to prevent context overflow and drift
                    FOUNDATIONAL_KNOWLEDGE = None  # Disabled - use RAG-based approach instead
                    # OLD STRING-BASED FOUNDATIONAL_KNOWLEDGE (600+ lines) COMMENTED OUT
                    # This was causing:
                    # 1. Context overflow (16,385 token limit exceeded)
                    # 2. Prompt drift (conflicting with RAG content)
                    # 3. Duplication (same content exists in RAG via add_foundational_knowledge.py)
                    #
                    # The proper solution is to ensure foundational knowledge files exist:
                    # - docs/rag/foundational_technical.md
                    # Note: foundational_philosophical.md is now a style_guide (moved to docs/style/) and should NOT be in RAG
                    # These files are loaded via RAG-based approach above
                    #
                    # If files don't exist, system will still work but may not answer questions about StillMe correctly.
                    # To fix: Run scripts/add_foundational_knowledge.py to ensure files exist and are loaded into RAG.
                    """
                # Only add fallback foundational knowledge if files don't exist
                if FOUNDATIONAL_KNOWLEDGE:
                    tags_list = ["foundational:stillme", "CRITICAL_FOUNDATION", "stillme", "rag", "self-evolving", "continuous-learning", "automated-learning", "rss", "vector-db"]
                    tags_string = ",".join(tags_list)
                    
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
                        logger.info("✅ Foundational knowledge added successfully (fallback string-based)!")
                    else:
                        logger.warning("⚠️ Failed to add foundational knowledge (non-critical)")
            else:
                logger.info("✅ Foundational knowledge already exists")
        except Exception as foundational_error:
            # Non-critical - don't fail startup if foundational knowledge check/add fails
            logger.warning(f"⚠️ Could not check/add foundational knowledge (non-critical): {foundational_error}")
            logger.debug("StillMe will still work, but may not answer questions about itself correctly")
        
        # CRITICAL: Log completion with clear formatting
        import sys
        sys.stdout.flush()
        logger.info("=" * 60)
        logger.info("🎉 StillMe Backend is READY!")
        logger.info("=" * 60)
        logger.info("✅ RAG System: Fully initialized")
        logger.info("✅ Learning System: Ready")
        logger.info("✅ All components: Operational")
        logger.info("=" * 60)
        sys.stdout.flush()
        
        _rag_initialization_complete = True
        
        # Update metrics collector with component health
        try:
            from backend.api.metrics_collector import get_metrics_collector
            metrics_collector = get_metrics_collector()
            metrics_collector.set_component_health("rag_initialized", rag_retrieval is not None)
            metrics_collector.set_component_health("chromadb_available", chroma_client is not None)
            metrics_collector.set_component_health("embedding_service_ready", embedding_service is not None)
            metrics_collector.set_component_health("knowledge_retention_ready", knowledge_retention is not None)
            
            # Update knowledge items count if available
            if knowledge_retention:
                try:
                    retention_metrics = knowledge_retention.calculate_retention_metrics()
                    if retention_metrics:
                        total_items = retention_metrics.get('total_items', 0)
                        metrics_collector.set_knowledge_items_total(total_items)
                except Exception:
                    pass
        except Exception as metrics_error:
            logger.debug(f"Could not update metrics collector: {metrics_error}")
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
            logger.error("⚠️ ACTION REQUIRED: Set FORCE_DB_RESET_ON_STARTUP=true on Railway and RESTART service.")
            logger.error("⚠️ Or manually delete data/vector_db directory on Railway and restart.")
            logger.error("⚠️ Service will continue running but RAG features will be unavailable.")
            
            # IMPORTANT: Don't raise exception - allow service to start
            # Health endpoint should still work, just RAG features won't be available
            logger.warning("⚠️ Continuing service startup without RAG components...")
            logger.warning("⚠️ /health endpoint will still work, but /api/chat and /api/rag endpoints will fail")
            
            # Set components to None to indicate they're not available
            chroma_client = None
            embedding_service = None
            rag_retrieval = None
            knowledge_retention = None
            accuracy_scorer = None
            # Update metrics collector with component health (all failed)
            try:
                from backend.api.metrics_collector import get_metrics_collector
                metrics_collector = get_metrics_collector()
                metrics_collector.set_component_health("rag_initialized", False)
                metrics_collector.set_component_health("chromadb_available", False)
                metrics_collector.set_component_health("embedding_service_ready", False)
                metrics_collector.set_component_health("knowledge_retention_ready", False)
            except Exception:
                pass
        
        else:
            # For non-schema errors, also allow service to continue
            logger.warning("⚠️ RAG components initialization failed, but service will continue")
            logger.warning("⚠️ /health endpoint will still work")
            # Note: Components are already None from initial declaration

# Pydantic models
# Models are now imported from backend.api.models (see imports above)

# Include routers - routers are already APIRouter objects from __init__.py
app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(rag_router, prefix="/api/rag", tags=["rag"])
app.include_router(tiers_router, prefix="/api/v1/tiers", tags=["tiers"])
app.include_router(spice_router, prefix="/api/spice", tags=["spice"])
app.include_router(learning_router, prefix="/api/learning", tags=["learning"])
app.include_router(learning_permission_router.router, prefix="/api/learning", tags=["learning"])
app.include_router(community_router.router, prefix="/api/community", tags=["community"])
app.include_router(feedback_router.router, prefix="/api/feedback", tags=["feedback"])
app.include_router(system_router, tags=["system"])
app.include_router(debug_router.router)  # Debug endpoints for cache/model monitoring

# System endpoints moved to backend/api/routers/system_router.py

@app.on_event("startup")
async def startup_event():
    """Initialize RAG components and log when FastAPI/uvicorn server is ready"""
    import sys
    sys.stdout.flush()  # Ensure logs are flushed immediately
    
    logger.info("=" * 60)
    logger.info("🚀 StillMe Backend - FastAPI Startup Event")
    logger.info("=" * 60)
    logger.info("🌐 Uvicorn server is ready to accept connections")
    logger.info("📋 /health endpoint is available immediately")
    logger.info("=" * 60)
    sys.stdout.flush()
    
    # Validate security configuration
    logger.info("🔐 Validating security configuration...")
    security_status = validate_api_key_config()
    if security_status["configured"]:
        logger.info("✅ API authentication is configured")
    else:
        if security_status["is_production"]:
            logger.error("❌ CRITICAL: API authentication is NOT configured in PRODUCTION!")
            logger.error("❌ Set STILLME_API_KEY environment variable immediately")
        else:
            logger.warning("⚠️ API authentication is not configured (development mode)")
    for warning in security_status["warnings"]:
        logger.warning(f"⚠️ {warning}")
    for rec in security_status["recommendations"]:
        logger.info(f"💡 {rec}")
    
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
    
    # Auto-start scheduler after RAG components are initialized
    async def auto_start_scheduler_after_init():
        """Wait for RAG initialization to complete, then auto-start scheduler if enabled"""
        # Wait for RAG initialization to complete (max 5 minutes)
        max_wait_time = 300  # 5 minutes
        wait_interval = 2  # Check every 2 seconds
        elapsed = 0
        
        while not _rag_initialization_complete and elapsed < max_wait_time:
            await asyncio.sleep(wait_interval)
            elapsed += wait_interval
        
        if not _rag_initialization_complete:
            logger.warning("⚠️ RAG initialization not completed after 5 minutes - skipping auto-start scheduler")
            return
        
        # Check if auto-start is enabled
        auto_start_enabled = os.getenv("AUTO_START_SCHEDULER", "true").lower() == "true"
        
        if not auto_start_enabled:
            logger.info("ℹ️ AUTO_START_SCHEDULER is disabled - scheduler will not auto-start")
            return
        
        # Wait a bit more to ensure all components are ready
        await asyncio.sleep(2)
        
        # Check if scheduler is available and not already running
        if learning_scheduler:
            if learning_scheduler.is_running:
                logger.info("ℹ️ Scheduler is already running - skipping auto-start")
            else:
                try:
                    await learning_scheduler.start()
                    logger.info("✅ Scheduler auto-started on application startup")
                    logger.info(f"📅 Scheduler will run every {learning_scheduler.interval_hours} hours")
                except Exception as e:
                    logger.error(f"❌ Failed to auto-start scheduler: {e}")
        else:
            logger.warning("⚠️ Learning scheduler not available - cannot auto-start")
    
    # Start auto-start task in background
    asyncio.create_task(auto_start_scheduler_after_init())
    
    # CRITICAL: Start scheduler watchdog to auto-restart if it stops
    async def scheduler_watchdog():
        """Watchdog task to ensure scheduler stays running"""
        # Wait for initial RAG initialization
        await asyncio.sleep(10)  # Give initial startup time
        
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Check if scheduler should be running
                auto_start_enabled = os.getenv("AUTO_START_SCHEDULER", "true").lower() == "true"
                if not auto_start_enabled:
                    continue
                
                # Check if RAG is initialized
                if not _rag_initialization_complete:
                    continue
                
                # Check if scheduler exists
                if not learning_scheduler:
                    continue
                
                # Check if scheduler should be running but isn't
                if not learning_scheduler.is_running:
                    logger.warning("⚠️ Scheduler watchdog: Scheduler is not running but should be - restarting...")
                    try:
                        await learning_scheduler.start()
                        logger.info("✅ Scheduler watchdog: Successfully restarted scheduler")
                    except Exception as restart_error:
                        logger.error(f"❌ Scheduler watchdog: Failed to restart scheduler: {restart_error}")
                
            except asyncio.CancelledError:
                logger.info("Scheduler watchdog cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler watchdog: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait before retrying
    
    # Start watchdog task
    asyncio.create_task(scheduler_watchdog())
    logger.info("✅ Scheduler watchdog started - will auto-restart scheduler if it stops")
    
    # Log component integration status
    logger.info("🔗 Component Integration Status:")
    logger.info(f"  - RAG System: {'✓ Ready' if rag_retrieval and knowledge_retention else '⏳ Initializing...'}")
    logger.info(f"  - Learning System: {'✓ Ready' if learning_scheduler and source_integration else '⏳ Initializing...'}")
    logger.info(f"  - Memory Health: {'✓ Ready' if continuum_memory else '⊘ Disabled (ENABLE_CONTINUUM_MEMORY=false)'}")
    logger.info(f"  - Nested Learning: {'✓ Ready' if continuum_memory and os.getenv('ENABLE_CONTINUUM_MEMORY', 'false').lower() == 'true' else '⊘ Disabled'}")

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
