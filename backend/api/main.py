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
        
        # For Dashboard service, always use reset_on_error=True to handle schema mismatches automatically
        # This is safe because Dashboard is typically a read-only service or can rebuild its database
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
        
        # CRITICAL: Initialize EmbeddingService FIRST so we can pass it to ChromaClient
        # This prevents ChromaDB from using default ONNX model (all-MiniLM-L6-v2)
        embedding_service = EmbeddingService()
        logger.info("✓ Embedding service initialized")
        
        if force_reset or is_dashboard:
            if force_reset:
                logger.warning("🔄 FORCE_DB_RESET_ON_STARTUP=True detected - will reset ChromaDB database")
            if is_dashboard:
                logger.info("📊 Dashboard service detected - will use auto-reset for ChromaDB schema mismatches")
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
            
            # Check if foundational knowledge exists
            foundational_exists = False
            try:
                # Try to find documents with CRITICAL_FOUNDATION source
                foundational_results = chroma_client.search_knowledge(
                    query_embedding=query_embedding,
                    limit=5,
                    where={"source": "CRITICAL_FOUNDATION"}
                )
                if foundational_results:
                    for result in foundational_results:
                        content = result.get("content", "")
                        metadata = result.get("metadata", {})
                        if "multi-qa-MiniLM-L6-dot-v1" in content and metadata.get("source") == "CRITICAL_FOUNDATION":
                            foundational_exists = True
                            logger.info(f"✅ Foundational knowledge found: {metadata.get('title', 'N/A')}")
                            break
            except Exception as filter_error:
                # If metadata filter fails, try without filter
                logger.debug(f"Metadata filter not supported, trying content search: {filter_error}")
                all_results = chroma_client.search_knowledge(
                    query_embedding=query_embedding,
                    limit=20
                )
                for result in all_results:
                    content = result.get("content", "")
                    metadata = result.get("metadata", {})
                    if ("multi-qa-MiniLM-L6-dot-v1" in content and 
                        ("CRITICAL_FOUNDATION" in str(metadata.get("source", "")) or 
                         "foundational" in str(metadata.get("type", "")).lower())):
                        foundational_exists = True
                        logger.info("✅ Foundational knowledge found (via content search)")
                        break
            
            if not foundational_exists:
                logger.info("⚠️ Foundational knowledge not found. Adding it now...")
                # Load foundational knowledge from separate files
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                technical_path = os.path.join(base_dir, "docs", "rag", "foundational_technical.md")
                philosophical_path = os.path.join(base_dir, "docs", "rag", "foundational_philosophical.md")
                
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
                
                # Load philosophical foundational knowledge
                if os.path.exists(philosophical_path):
                    with open(philosophical_path, "r", encoding="utf-8") as f:
                        philosophical_content = f.read()
                    # Remove frontmatter if present
                    if philosophical_content.startswith("---"):
                        parts = philosophical_content.split("---", 2)
                        if len(parts) >= 3:
                            philosophical_content = parts[2].strip()
                    
                    tags_list_philosophical = ["foundational:stillme", "CRITICAL_FOUNDATION", "stillme", "philosophical", "ethics", "transparency"]
                    tags_string_philosophical = ",".join(tags_list_philosophical)
                    
                    success_philosophical = rag_retrieval.add_learning_content(
                        content=philosophical_content,
                        source="CRITICAL_FOUNDATION",
                        content_type="knowledge",
                        metadata={
                            "title": "StillMe Core Principles - Philosophical Foundation",
                            "foundational": "stillme",
                            "type": "foundational",
                            "source": "CRITICAL_FOUNDATION",
                            "tags": tags_string_philosophical,
                            "importance_score": 1.0,
                            "content_type": "philosophical",
                            "domain": "stillme_foundation",
                            "description": "CRITICAL: Philosophical principles and ethical foundation of StillMe - MUST be retrieved when answering about StillMe's values and approach"
                        }
                    )
                    if success_philosophical:
                        logger.info("✅ Philosophical foundational knowledge added successfully!")
                    else:
                        logger.warning("⚠️ Failed to add philosophical foundational knowledge")
                else:
                    logger.warning(f"⚠️ Philosophical foundational knowledge file not found: {philosophical_path}")
                
                # Fallback: If files don't exist, use old string-based approach (for backward compatibility)
                # Initialize FOUNDATIONAL_KNOWLEDGE outside if block to avoid UnboundLocalError
                FOUNDATIONAL_KNOWLEDGE = None
                if not os.path.exists(technical_path) or not os.path.exists(philosophical_path):
                    logger.warning("⚠️ Foundational knowledge files not found, using fallback string-based approach")
                    # Phase 2 - Option A: Reduced to concise summary (~150 lines) - only core mechanism, no style guide
                    FOUNDATIONAL_KNOWLEDGE = """
[STILLME CORE MECHANISM] StillMe is a continuously self-learning AI system that uses RAG (Retrieval-Augmented Generation). This allows StillMe to transcend the knowledge limitation (2023) of base LLM models by automatically retrieving and learning from trusted sources (RSS Feeds, ArXiv, CrossRef, Wikipedia) every 4 hours (6 cycles per day). StillMe prioritizes the latest knowledge from its Vector Database.

**StillMe's Learning Process:**
1. Automated Learning Cycles: StillMe fetches content from multiple sources every 4 hours (6 times per day)
2. RAG-Based Knowledge Storage: All learned content is embedded using sentence-transformers model `multi-qa-MiniLM-L6-dot-v1` (384-dimensional embeddings) and stored in ChromaDB vector database
3. Semantic Search: When answering questions, StillMe retrieves relevant context from vector database using semantic similarity search
4. Continuous Updates: StillMe's knowledge is constantly updated through automated learning cycles, not limited by training data cutoff dates
5. Transparency: Every learning source is visible and auditable - users can see exactly what StillMe learns and from where

**Current Learning Sources:**
StillMe learns from: RSS Feeds (Nature, Science, Hacker News, Tech Policy blogs, Academic blogs), Wikipedia (AI, Buddhism, religious studies, philosophy, ethics), arXiv (cs.AI, cs.LG), CrossRef (AI/ML/NLP), Papers with Code, Conference Proceedings (NeurIPS, ICML, ACL, ICLR), Stanford Encyclopedia of Philosophy.

**Self-Awareness Mechanism:**
StillMe checks current sources via `GET /api/learning/sources/current` before proposing new ones. StillMe only proposes sources not already in the current list.

**Technical Architecture Details:**

**Embedding Model:**
- **Model Name**: `multi-qa-MiniLM-L6-dot-v1` (sentence-transformers, optimized for Q&A retrieval)
- **Embedding Dimensions**: 384
- **Purpose**: Converts text into vector embeddings for semantic search in ChromaDB
- **Library**: sentence-transformers (Hugging Face)

**LLM Models (Language Generation):**
- **Primary**: DeepSeek API (when DEEPSEEK_API_KEY is configured)
- **Fallback**: OpenAI GPT models (when OPENAI_API_KEY is configured)
- **Model Selection**: Automatic routing based on available API keys (priority: DeepSeek > OpenAI)
- **Purpose**: Generates responses based on retrieved RAG context

**Vector Database:**
- **Technology**: ChromaDB
- **Collections**: 
  - `stillme_knowledge`: Stores learned content from RSS, arXiv, CrossRef, Wikipedia
  - `stillme_conversations`: Stores conversation history for context retrieval
- **Search Method**: Semantic similarity search using cosine distance

**Conversation History Storage:**
StillMe stores conversation history in ChromaDB collection `stillme_conversations` for context retrieval. StillMe stores Q&A pairs (format: "Q: [user question]\nA: [StillMe response]") after each conversation completes. StillMe searches past conversations for relevant context when answering new questions. StillMe stores conversations for context retrieval only, not for learning from user data (StillMe learns from RSS, arXiv, Wikipedia, not from user conversations).

**Validation & Grounding Mechanism:**
StillMe uses a **ValidatorChain** to help ensure response quality and reduce hallucinations (enabled by default via ENABLE_VALIDATORS=true):

1. **CitationRequired**: Ensures responses cite sources from retrieved context
2. **EvidenceOverlap**: Validates that response content overlaps with retrieved context (threshold = 0.01 = 1% n-gram overlap minimum, configurable via VALIDATOR_EVIDENCE_THRESHOLD)
3. **NumericUnitsBasic**: Validates numeric claims and units
4. **ConfidenceValidator**: Detects when AI should express uncertainty, especially when no context is available
   - Requires AI to say "I don't know" when no context is found
   - Prevents overconfidence without evidence
5. **FallbackHandler**: Provides safe fallback answers when validation fails critically
   - Replaces hallucinated responses with honest "I don't know" messages
   - Explains StillMe's learning mechanism and suggests alternatives
6. **EthicsAdapter**: Ethical content filtering

**Validation Behavior:**
- **Critical failures** (missing citation with context, missing uncertainty with no context): Response is replaced with fallback answer
- **Non-critical failures** (low overlap with citation, numeric errors): Response is returned with warning logged
- **Note**: Validation helps reduce hallucinations but does not guarantee 100% accuracy

**Confidence Scoring:**
- StillMe calculates confidence scores (0.0-1.0) based on:
  - Context availability (0 docs = 0.2, 1 doc = 0.5, 2+ docs = 0.8)
  - Validation results (+0.1 if passed, -0.1 to -0.2 if failed)
  - Missing uncertainty when no context = 0.1 (very low)

**Key Differentiator**: Unlike traditional LLMs that are frozen at their training date, StillMe **continuously evolves** and updates its knowledge base through automated RAG learning cycles. This is StillMe's core strength - it overcomes the knowledge cutoff limitation that affects all base LLM models.

**Key Features:**
- **Continuous Learning**: StillMe automatically fetches and learns from RSS feeds, arXiv, CrossRef, Wikipedia every 4 hours (6 cycles per day)
- **RAG-Based Knowledge**: All knowledge is stored in ChromaDB vector database and retrieved using semantic search with `multi-qa-MiniLM-L6-dot-v1` embeddings
- **Transparency**: Every learning source is visible and auditable - no black box learning
- **Self-Diagnosis**: StillMe can identify knowledge gaps and prioritize what to learn next
- **Content Curation**: Intelligent filtering and prioritization of learning content based on quality and relevance
- **Pre-Filter System**: Filters content BEFORE embedding to reduce costs by 30-50%
- **Knowledge Alerts**: Proactively suggests important knowledge to users when StillMe learns something relevant
- **Validation Chain**: Helps reduce hallucinations through citation, evidence overlap, confidence validation, and ethics checks (enabled by default, can be disabled via ENABLE_VALIDATORS=false)

**How StillMe Learns:**
1. Automated scheduler fetches RSS feeds, arXiv, CrossRef, Wikipedia every 4 hours
2. Content is pre-filtered for quality (minimum length, keyword relevance)
3. High-quality content is embedded using `multi-qa-MiniLM-L6-dot-v1` model and stored in ChromaDB
4. When users ask questions, StillMe:
   - Embeds the query using `multi-qa-MiniLM-L6-dot-v1`
   - Retrieves relevant context from ChromaDB using semantic search
   - Generates response using LLM (DeepSeek or OpenAI) with retrieved context
   - Validates response using ValidatorChain
   - Calculates confidence score based on context quality and validation results
5. Responses are generated using retrieved context, ensuring accuracy and up-to-date information

**Transparency & Ethics:**
- 100% open source - every algorithm is public
- Complete audit trail of all learning decisions
- Community governance for ethical guidelines
- No black box - users can see exactly what StillMe learns and from where
- **Technical Transparency**: StillMe must be honest about technical errors and system limitations when asked

**StillMe's Position on "Black Box AI":**
StillMe fights against BLACK BOX SYSTEMS (closed, proprietary AI systems with hidden algorithms, data sources, decision-making), not black box models (LLM internal weights - a mathematical reality, not a flaw to fix). StillMe uses LLM APIs (DeepSeek, OpenAI) as "reasoning engines" but builds a transparent SYSTEM around them. System transparency: Every line of StillMe's code is public, every data flow is visible, every learning decision is logged. Model transparency: StillMe doesn't promise to "open the LLM black box" (mathematically impossible), but verifies outputs through Validator Chain, grounds responses in RAG context, and expresses uncertainty appropriately. Community control: Users control what StillMe learns, not corporations. StillMe doesn't claim to explain how LLMs work internally - it builds transparent systems that use LLMs responsibly, verify their outputs, and give users control over what the system learns and how it evolves.

**API Endpoints:**
StillMe provides API endpoints for: Ethical Safety (`GET /api/learning/ethics/violations`, `GET /api/learning/ethics/stats`, `POST /api/learning/ethics/check-content`), Self-Diagnosis & Coverage (`POST /api/learning/self-diagnosis/analyze-coverage`, `POST /api/learning/self-diagnosis/check-gap`, `GET /api/learning/self-diagnosis/suggest-focus`), Learning Sources (`GET /api/learning/sources/current`, `GET /api/learning/sources/stats`), Validator Metrics (`GET /api/validators/metrics`), Learning Metrics (`GET /api/learning/metrics/daily`, `GET /api/learning/metrics/range`, `GET /api/learning/metrics/summary`).

**Time Awareness & Learning Metrics:**
StillMe has access to current server time (UTC) and tracks learning metrics with timestamps. Metrics tracked: entries_fetched, entries_added, entries_filtered, filter_reasons, sources, duration. Metrics are persisted to `data/learning_metrics.jsonl`. Dashboard displays time-based learning analytics.

**Pre-Filter System:**
Pre-Filter rules: Minimum 150 characters, keyword scoring. Cost reduction: 30-50% (filters before embedding).
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
        
        logger.info("🎉 StillMe backend is ready!")
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
    logger.info("🚀 FastAPI application startup event triggered")
    logger.info("🌐 Uvicorn server is ready to accept connections")
    logger.info("📋 /health endpoint is available immediately")
    
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
