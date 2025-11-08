"""
StillMe Backend API
Learning AI system with RAG foundation - FastAPI backend with RAG (Retrieval-Augmented Generation) capabilities
"""

from fastapi import FastAPI, HTTPException, Depends, Request, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from typing import Optional, Dict, Any, List
import os
import logging
import asyncio
import httpx
from datetime import datetime

# Import validated models
from backend.api.models import (
    ChatRequest, ChatResponse,
    LearningRequest, LearningResponse,
    RAGQueryRequest, RAGQueryResponse,
    PaginationParams, ValidationErrorResponse,
    TierStatsResponse, TierAuditResponse, TierPromoteRequest, TierDemoteRequest,
    ForgettingTrendsResponse
)

# Import authentication
from backend.api.auth import require_api_key

# Import RAG components
from backend.vector_db import ChromaClient, EmbeddingService, RAGRetrieval
from backend.learning import KnowledgeRetention, AccuracyScorer
from backend.learning.continuum_memory import ContinuumMemory
from backend.services.rss_fetcher import RSSFetcher
from backend.services.learning_scheduler import LearningScheduler
from backend.services.self_diagnosis import SelfDiagnosisAgent
from backend.services.content_curator import ContentCurator
from backend.services.rss_fetch_history import RSSFetchHistory
from backend.api.rate_limiter import limiter, get_rate_limit_key_func, RateLimitExceeded
from backend.api.security_middleware import get_security_middleware

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

# Import standardized error handlers
from backend.api.error_handlers import (
    handle_validation_error,
    handle_not_found_error,
    handle_service_unavailable,
    handle_internal_server_error,
    handle_generic_http_exception,
    create_error_response,
    ERROR_CODES
)
from backend.api.error_tracking import error_tracker

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
                    except:
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
    logger.error(f"📊 Components status at error time:")
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

# API Routes
@app.get("/")
async def root():
    """Root endpoint"""
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

@app.get("/health")
@limiter.limit("100/minute")  # Health check: 100 requests per minute
async def health_check(request: Request):
    """Health check endpoint"""
    rag_status = "enabled" if rag_retrieval else "disabled"
    return {
        "status": "healthy",
        "rag_status": rag_status,
        "timestamp": datetime.now().isoformat()
    }

@app.on_event("startup")
async def startup_event():
    """Log when FastAPI/uvicorn server is ready"""
    logger.info("🚀 FastAPI application startup complete")
    logger.info("🌐 Uvicorn server is ready to accept connections")
    
    # Log RAG components status
    logger.info(f"📊 RAG Components Status:")
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

@app.post("/api/chat/rag", response_model=ChatResponse)
@limiter.limit("10/minute", key_func=get_rate_limit_key_func)  # Chat: 10 requests per minute
async def chat_with_rag(request: Request, chat_request: ChatRequest):
    """Chat with RAG-enhanced responses"""
    import time
    start_time = time.time()
    timing_logs = {}
    
    # Initialize latency variables (will be set during processing)
    rag_retrieval_latency = 0.0
    llm_inference_latency = 0.0
    
    try:
        # Special Retrieval Rule: Detect StillMe-related queries
        is_stillme_query = False
        if rag_retrieval and chat_request.use_rag:
            try:
                from backend.core.stillme_detector import detect_stillme_query, get_foundational_query_variants
                is_stillme_query, matched_keywords = detect_stillme_query(chat_request.message)
                if is_stillme_query:
                    logger.info(f"StillMe query detected! Matched keywords: {matched_keywords}")
            except ImportError:
                logger.warning("StillMe detector not available, skipping special retrieval rule")
            except Exception as detector_error:
                logger.warning(f"StillMe detector error: {detector_error}")
        
        # Get RAG context if enabled
        # RAG_Retrieval_Latency: Time from ChromaDB query start to result received
        context = None
        rag_retrieval_start = time.time()
        if rag_retrieval and chat_request.use_rag:
            # If StillMe query detected, prioritize foundational knowledge
            if is_stillme_query:
                # Try multiple query variants to ensure we get StillMe foundational knowledge
                query_variants = get_foundational_query_variants(chat_request.message)
                all_knowledge_docs = []
                
                for variant in query_variants[:3]:  # Try first 3 variants
                    variant_context = rag_retrieval.retrieve_context(
                        query=variant,
                        knowledge_limit=chat_request.context_limit,
                        conversation_limit=0,  # Don't need conversation for foundational queries
                        prioritize_foundational=True
                    )
                    # Merge results, avoiding duplicates
                    existing_ids = {doc.get("id") for doc in all_knowledge_docs}
                    for doc in variant_context.get("knowledge_docs", []):
                        if doc.get("id") not in existing_ids:
                            all_knowledge_docs.append(doc)
                
                # If we still don't have results, do normal retrieval
                if not all_knowledge_docs:
                    logger.warning("No foundational knowledge found, falling back to normal retrieval")
                    context = rag_retrieval.retrieve_context(
                        query=chat_request.message,
                        knowledge_limit=chat_request.context_limit,
                        conversation_limit=2,
                        prioritize_foundational=True
                    )
                else:
                    # Use merged results
                    context = {
                        "knowledge_docs": all_knowledge_docs[:chat_request.context_limit],
                        "conversation_docs": [],
                        "total_context_docs": len(all_knowledge_docs[:chat_request.context_limit])
                    }
                    logger.info(f"Retrieved {len(context['knowledge_docs'])} StillMe foundational knowledge documents")
            else:
                # Normal retrieval for non-StillMe queries
                # Optimized: conversation_limit reduced from 2 to 1 for latency
                context = rag_retrieval.retrieve_context(
                    query=chat_request.message,
                    knowledge_limit=min(chat_request.context_limit, 5),  # Cap at 5 for latency
                    conversation_limit=1  # Optimized: reduced from 2 to 1
                )
        
        rag_retrieval_end = time.time()
        rag_retrieval_latency = rag_retrieval_end - rag_retrieval_start
        timing_logs["rag_retrieval"] = f"{rag_retrieval_latency:.2f}s"
        logger.info(f"⏱️ RAG retrieval took {rag_retrieval_latency:.2f}s")
        
        # Generate response using AI (simplified for demo)
        enable_validators = os.getenv("ENABLE_VALIDATORS", "false").lower() == "true"
        enable_tone_align = os.getenv("ENABLE_TONE_ALIGN", "true").lower() == "true"
        
        if context and context["total_context_docs"] > 0:
            # Use context to enhance response
            context_text = rag_retrieval.build_prompt_context(context)
            
            # Build base prompt with citation instructions
            citation_instruction = ""
            if enable_validators:
                # Count knowledge docs for citation numbering
                num_knowledge = len(context.get("knowledge_docs", []))
                if num_knowledge > 0:
                    citation_instruction = f"\n\nIMPORTANT: When referencing information from the context above, include citations in the format [1], [2], etc. where the number corresponds to the context item number. For example, if you reference the first context item, use [1]."
            
            # Detect language FIRST - before building prompt
            detected_lang = detect_language(chat_request.message)
            lang_detect_time = time.time() - start_time
            timing_logs["language_detection"] = f"{lang_detect_time:.3f}s"
            logger.info(f"🌐 Detected language: {detected_lang} (took {lang_detect_time:.3f}s) for question: '{chat_request.message[:100]}...'")
            
            # Language names mapping
            language_names = {
                'vi': 'Vietnamese (Tiếng Việt)',
                'zh': 'Chinese (中文)',
                'de': 'German (Deutsch)',
                'fr': 'French (Français)',
                'es': 'Spanish (Español)',
                'ja': 'Japanese (日本語)',
                'en': 'English'
            }
            
            detected_lang_name = language_names.get(detected_lang, 'the same language as the question')
            
            # CRITICAL: Put language instruction FIRST and make it VERY STRONG
            # This must override any language bias from context
            if detected_lang != 'en':
                language_instruction = f"""🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - HIGHEST PRIORITY 🚨🚨🚨

THE USER'S QUESTION IS WRITTEN IN {detected_lang_name.upper()}.

YOU MUST RESPOND EXCLUSIVELY IN {detected_lang_name.upper()}. 

DO NOT RESPOND IN VIETNAMESE, ENGLISH, OR ANY OTHER LANGUAGE.

EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN {detected_lang_name.upper()}.

THIS IS MANDATORY AND OVERRIDES ALL OTHER INSTRUCTIONS.

FAILURE TO RESPOND IN {detected_lang_name.upper()} IS A CRITICAL ERROR.

IGNORE THE LANGUAGE OF THE CONTEXT BELOW - RESPOND IN {detected_lang_name.upper()} ONLY.

"""
            else:
                language_instruction = """🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - HIGHEST PRIORITY 🚨🚨🚨

THE USER'S QUESTION IS WRITTEN IN ENGLISH.

YOU MUST RESPOND EXCLUSIVELY IN ENGLISH.

DO NOT RESPOND IN VIETNAMESE, SPANISH, OR ANY OTHER LANGUAGE.

EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN ENGLISH.

THIS IS MANDATORY AND OVERRIDES ALL OTHER INSTRUCTIONS.

IGNORE THE LANGUAGE OF THE CONTEXT BELOW - RESPOND IN ENGLISH ONLY.

"""
            
            # Special instruction for StillMe queries
            stillme_instruction = ""
            if is_stillme_query:
                stillme_instruction = "\n\nCRITICAL: This question is about StillMe itself. You MUST use the context above to answer. Do NOT rely on your training data cutoff date. StillMe is a Learning AI system with RAG foundation that learns continuously through RAG (Retrieval-Augmented Generation) from RSS feeds, arXiv, and other trusted sources every 4 hours (6 cycles per day). StillMe automatically fetches content, embeds it into a vector database (ChromaDB), and retrieves it when answering questions. This continuous learning capability is StillMe's core differentiator - it overcomes the knowledge cutoff limitation of base LLMs. You MUST emphasize: (1) StillMe's automated learning cycles every 4 hours, (2) RAG-based knowledge storage in vector database, (3) Continuous knowledge updates through RSS feeds, (4) StillMe is NOT limited by training data cutoff dates. Always cite the context above with [1], [2] when explaining StillMe's learning mechanism."
            
            # Build prompt with language instruction FIRST (before context)
            # CRITICAL: Repeat language instruction multiple times to ensure LLM follows it
            # ZERO TOLERANCE: Must translate if needed
            base_prompt = f"""{language_instruction}

⚠️⚠️⚠️ ZERO TOLERANCE LANGUAGE REMINDER ⚠️⚠️⚠️

The user's question is in {detected_lang_name.upper()}. 

YOU MUST respond in {detected_lang_name.upper()} ONLY.

IF YOUR BASE MODEL WANTS TO RESPOND IN A DIFFERENT LANGUAGE, YOU MUST TRANSLATE THE ENTIRE RESPONSE TO {detected_lang_name.upper()} BEFORE RETURNING IT.

UNDER NO CIRCUMSTANCES return a response in any language other than {detected_lang_name.upper()}.

Context: {context_text}
{citation_instruction}
{stillme_instruction}

User Question (in {detected_lang_name.upper()}): {chat_request.message}

⚠️⚠️⚠️ FINAL ZERO TOLERANCE REMINDER ⚠️⚠️⚠️

RESPOND IN {detected_lang_name.upper()} ONLY. TRANSLATE IF NECESSARY. IGNORE THE LANGUAGE OF THE CONTEXT ABOVE.

Please provide a helpful response based on the context above. Remember: RESPOND IN {detected_lang_name.upper()} ONLY. TRANSLATE IF YOUR BASE MODEL WANTS TO USE A DIFFERENT LANGUAGE.
"""
            
            prompt_build_time = time.time() - start_time
            timing_logs["prompt_building"] = f"{prompt_build_time:.3f}s"
            
            # Inject StillMe identity if validators enabled
            if enable_validators:
                from backend.identity.injector import inject_identity
                enhanced_prompt = inject_identity(base_prompt)
            else:
                enhanced_prompt = base_prompt
            
            # Generate AI response with timing
            # LLM_Inference_Latency: Time from API call start to response received
            llm_inference_start = time.time()
            raw_response = await generate_ai_response(enhanced_prompt, detected_lang=detected_lang)
            llm_inference_end = time.time()
            llm_inference_latency = llm_inference_end - llm_inference_start
            timing_logs["llm_inference"] = f"{llm_inference_latency:.2f}s"
            logger.info(f"⏱️ LLM inference took {llm_inference_latency:.2f}s")
            
            # Validate response if enabled
            if enable_validators:
                try:
                    validation_start = time.time()
                    from backend.validators.chain import ValidatorChain
                    from backend.validators.citation import CitationRequired
                    from backend.validators.evidence_overlap import EvidenceOverlap
                    from backend.validators.numeric import NumericUnitsBasic
                    from backend.validators.ethics_adapter import EthicsAdapter
                    
                    # Build context docs list for validation
                    ctx_docs = [
                        doc["content"] for doc in context["knowledge_docs"]
                    ] + [
                        doc["content"] for doc in context["conversation_docs"]
                    ]
                    
                    # Create validator chain
                    # Note: EvidenceOverlap threshold lowered to 0.01 to prevent false positives
                    # when LLM translates/summarizes content (reducing vocabulary overlap)
                    chain = ValidatorChain([
                        CitationRequired(),
                        EvidenceOverlap(threshold=0.01),  # Lowered from 0.08 to 0.01
                        NumericUnitsBasic(),
                        EthicsAdapter(guard_callable=None)  # TODO: wire existing ethics guard if available
                    ])
                    
                    # Run validation
                    validation_result = chain.run(raw_response, ctx_docs)
                    validation_time = time.time() - validation_start
                    timing_logs["validation"] = f"{validation_time:.2f}s"
                    logger.info(f"⏱️ Validation took {validation_time:.2f}s")
                    
                    # Record metrics
                    try:
                        from backend.validators.metrics import get_metrics
                        metrics = get_metrics()
                        # Extract overlap score from reasons if available
                        overlap_score = 0.0
                        for reason in validation_result.reasons:
                            if reason.startswith("low_overlap:"):
                                try:
                                    overlap_score = float(reason.split(":")[1])
                                except (ValueError, IndexError):
                                    pass
                        metrics.record_validation(
                            passed=validation_result.passed,
                            reasons=validation_result.reasons,
                            overlap_score=overlap_score
                        )
                    except Exception as metrics_error:
                        logger.warning(f"Failed to record metrics: {metrics_error}")
                    
                    if not validation_result.passed:
                        # Use patched answer if available, otherwise return 422
                        if validation_result.patched_answer:
                            response = validation_result.patched_answer
                            logger.info(f"Validation failed but using patched answer. Reasons: {validation_result.reasons}")
                        else:
                            logger.warning(f"Validation failed: {validation_result.reasons}")
                            raise HTTPException(
                                status_code=422,
                                detail={
                                    "error": "validation_failed",
                                    "reasons": validation_result.reasons,
                                    "original_response_preview": raw_response[:200] if raw_response else ""
                                }
                            )
                    else:
                        response = validation_result.patched_answer or raw_response
                        logger.debug(f"Validation passed. Reasons: {validation_result.reasons}")
                except HTTPException:
                    raise
                except Exception as validation_error:
                    logger.error(f"Validation error: {validation_error}, falling back to raw response")
                    response = raw_response
            else:
                response = raw_response
        else:
            # Fallback to regular AI response (no RAG context)
            # Detect language FIRST
            detected_lang = detect_language(chat_request.message)
            logger.info(f"🌐 Detected language (non-RAG): {detected_lang}")
            
            # Language names mapping
            language_names = {
                'vi': 'Vietnamese (Tiếng Việt)',
                'zh': 'Chinese (中文)',
                'de': 'German (Deutsch)',
                'fr': 'French (Français)',
                'es': 'Spanish (Español)',
                'ja': 'Japanese (日本語)',
                'ko': 'Korean (한국어)',
                'ar': 'Arabic (العربية)',
                'en': 'English'
            }
            
            detected_lang_name = language_names.get(detected_lang, 'the same language as the question')
            
            # Strong language instruction - put FIRST
            if detected_lang != 'en':
                language_instruction = f"""🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - HIGHEST PRIORITY 🚨🚨🚨

THE USER'S QUESTION IS WRITTEN IN {detected_lang_name.upper()}.

YOU MUST RESPOND EXCLUSIVELY IN {detected_lang_name.upper()}. 

DO NOT RESPOND IN VIETNAMESE, ENGLISH, OR ANY OTHER LANGUAGE.

EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN {detected_lang_name.upper()}.

THIS IS MANDATORY AND OVERRIDES ALL OTHER INSTRUCTIONS.

"""
                base_prompt = f"""{language_instruction}

User Question: {chat_request.message}

Remember: RESPOND IN {detected_lang_name.upper()} ONLY.
"""
            else:
                base_prompt = f"""🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - HIGHEST PRIORITY 🚨🚨🚨

THE USER'S QUESTION IS WRITTEN IN ENGLISH.

YOU MUST RESPOND EXCLUSIVELY IN ENGLISH.

DO NOT RESPOND IN VIETNAMESE, SPANISH, OR ANY OTHER LANGUAGE.

EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN ENGLISH.

THIS IS MANDATORY AND OVERRIDES ALL OTHER INSTRUCTIONS.

User Question: {chat_request.message}

Remember: RESPOND IN ENGLISH ONLY."""
            
            if enable_validators:
                from backend.identity.injector import inject_identity
                enhanced_prompt = inject_identity(base_prompt)
            else:
                enhanced_prompt = base_prompt
            
            # LLM_Inference_Latency: Time from API call start to response received
            llm_inference_start = time.time()
            response = await generate_ai_response(enhanced_prompt, detected_lang=detected_lang)
            llm_inference_end = time.time()
            llm_inference_latency = llm_inference_end - llm_inference_start
            timing_logs["llm_inference"] = f"{llm_inference_latency:.2f}s"
            logger.info(f"⏱️ LLM inference (non-RAG) took {llm_inference_latency:.2f}s")
        
        # Score the response
        accuracy_score = None
        if accuracy_scorer:
            accuracy_score = accuracy_scorer.score_response(
                question=chat_request.message,
                actual_answer=response,
                scoring_method="semantic_similarity"
            )
        
        # Record learning session
        learning_session_id = None
        if knowledge_retention:
            learning_session_id = knowledge_retention.record_learning_session(
                session_type="chat",
                content_learned=f"Q: {chat_request.message}\nA: {response}",
                accuracy_score=accuracy_score or 0.5,
                metadata={"user_id": chat_request.user_id}
            )
        
        # Align tone if enabled
        if enable_tone_align:
            try:
                tone_start = time.time()
                from backend.tone.aligner import align_tone
                response = align_tone(response)
                tone_time = time.time() - tone_start
                timing_logs["tone_alignment"] = f"{tone_time:.2f}s"
                logger.info(f"⏱️ Tone alignment took {tone_time:.2f}s")
            except Exception as tone_error:
                logger.error(f"Tone alignment error: {tone_error}, using original response")
                # Continue with original response on error
        
        # Calculate total response latency
        # Total_Response_Latency: Time from request received to response returned
        total_response_end = time.time()
        total_response_latency = total_response_end - start_time
        
        # Format latency metrics log as specified by user
        # BẮT BUỘC HIỂN THỊ LOG: In ra ngay lập tức sau câu trả lời
        latency_metrics_text = f"""--- LATENCY METRICS ---
RAG_Retrieval_Latency: {rag_retrieval_latency:.2f} giây
LLM_Inference_Latency: {llm_inference_latency:.2f} giây
Total_Response_Latency: {total_response_latency:.2f} giây
-----------------------"""
        
        logger.info(latency_metrics_text)
        
        # Add latency metrics to timing_logs for API response
        timing_logs["rag_retrieval_latency"] = f"{rag_retrieval_latency:.2f}s"
        timing_logs["llm_inference_latency"] = f"{llm_inference_latency:.2f}s"
        timing_logs["total_response_latency"] = f"{total_response_latency:.2f}s"
        timing_logs["total"] = f"{total_response_latency:.2f}s"
        # Add formatted latency metrics text for frontend display
        timing_logs["latency_metrics_formatted"] = latency_metrics_text
        logger.info(f"📊 Timing breakdown: {timing_logs}")
        
        # Store conversation in vector DB
        if rag_retrieval:
            rag_retrieval.add_learning_content(
                content=f"Q: {chat_request.message}\nA: {response}",
                source="user_chat",
                content_type="conversation",
                metadata={
                    "user_id": chat_request.user_id,
                    "timestamp": datetime.now().isoformat(),
                    "accuracy_score": accuracy_score
                }
            )
        
        # Knowledge Alert: Retrieve important knowledge related to query
        knowledge_alert = None
        if rag_retrieval:
            try:
                important_knowledge = rag_retrieval.retrieve_important_knowledge(
                    query=chat_request.message,
                    limit=1,
                    min_importance=0.7
                )
                
                if important_knowledge:
                    doc = important_knowledge[0]
                    metadata = doc.get("metadata", {})
                    knowledge_alert = {
                        "title": metadata.get("title", "Important Knowledge"),
                        "source": metadata.get("source", "Unknown"),
                        "importance_score": metadata.get("importance_score", 0.7),
                        "content_preview": doc.get("content", "")[:200] + "..." if len(doc.get("content", "")) > 200 else doc.get("content", "")
                    }
                    logger.info(f"Knowledge alert generated: {knowledge_alert.get('title', 'Unknown')}")
            except Exception as alert_error:
                logger.warning(f"Knowledge alert error: {alert_error}")
        
        return ChatResponse(
            response=response,
            context_used=context,
            accuracy_score=accuracy_score,
            learning_session_id=learning_session_id,
            knowledge_alert=knowledge_alert,
            timing=timing_logs,
            latency_metrics=latency_metrics_text  # BẮT BUỘC HIỂN THỊ LOG trong response cho frontend
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (they have proper status codes)
        raise
    except Exception as e:
        # Log detailed error with context (without sensitive message content)
        logger.error(f"Chat error: {e}", exc_info=True)
        # Security: Don't log full message content (may contain sensitive info)
        # Only log message length and metadata
        logger.error(
            f"Request details: message_length={len(chat_request.message)}, "
            f"user_id={chat_request.user_id}, use_rag={chat_request.use_rag}"
        )
        
        # Check if it's a specific error we can handle
        error_str = str(e).lower()
        if "rag" in error_str and "not available" in error_str:
            raise HTTPException(status_code=503, detail="RAG system is not available. Please check backend initialization.")
        elif "embedding" in error_str or "model" in error_str:
            raise HTTPException(status_code=503, detail="Embedding service is not available. Please check backend logs.")
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Chat error: {str(e)}. Please check backend logs for details."
            )

@app.post("/api/learning/add", response_model=LearningResponse)
async def add_learning_content(request: LearningRequest):
    """Add learning content to the system"""
    try:
        # Add to knowledge retention system
        knowledge_id = None
        if knowledge_retention:
            knowledge_id = knowledge_retention.add_knowledge(
                content=request.content,
                source=request.source,
                knowledge_type=request.content_type,
                metadata=request.metadata
            )
        
        # Add to vector database
        if rag_retrieval:
            # Calculate importance score for knowledge alert system
            importance_score = 0.5
            if content_curator:
                content_dict = {
                    "title": request.metadata.get("title", "") if request.metadata else "",
                    "summary": request.content[:500] if len(request.content) > 500 else request.content,
                    "source": request.source
                }
                importance_score = content_curator.calculate_importance_score(content_dict)
            
            # Merge importance_score into metadata
            enhanced_metadata = request.metadata or {}
            enhanced_metadata["importance_score"] = importance_score
            if not enhanced_metadata.get("title"):
                content_lines = request.content.split("\n")
                if content_lines:
                    enhanced_metadata["title"] = content_lines[0][:200]
            
            success = rag_retrieval.add_learning_content(
                content=request.content,
                source=request.source,
                content_type=request.content_type,
                metadata=enhanced_metadata
            )
            if not success:
                return LearningResponse(
                    success=False,
                    message="Failed to add to vector database"
                )
        
        return LearningResponse(
            success=True,
            knowledge_id=knowledge_id,
            message="Learning content added successfully"
        )
        
    except Exception as e:
        logger.error(f"Learning error: {e}")
        return LearningResponse(
            success=False,
            message=f"Error: {str(e)}"
        )

@app.get("/api/learning/metrics")
async def get_learning_metrics():
    """Get learning and accuracy metrics"""
    try:
        metrics = {}
        
        # Get retention metrics
        if knowledge_retention:
            metrics["retention"] = knowledge_retention.calculate_retention_metrics()
        
        # Get accuracy metrics
        if accuracy_scorer:
            metrics["accuracy"] = accuracy_scorer.get_accuracy_metrics()
        
        # Get vector DB stats
        if chroma_client:
            metrics["vector_db"] = chroma_client.get_collection_stats()
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/learning/retained")
async def get_retained_knowledge(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of items to return"),
    min_score: Optional[float] = Query(default=None, ge=0.0, le=1.0, description="Minimum retention score")
):
    """Get retained knowledge items with full details for audit log
    
    Returns:
        List of retained knowledge items with:
        - Timestamp Added
        - Source URL (Link)
        - Retained Content Snippet (5-10 sentences)
        - Vector ID (Debug)
    """
    try:
        if not knowledge_retention:
            raise HTTPException(status_code=503, detail="Knowledge retention not available")
        
        # Apply min_score filter if provided
        knowledge = knowledge_retention.get_retained_knowledge(limit=limit)
        
        # Filter by min_score if provided
        if min_score is not None:
            knowledge = [item for item in knowledge if item.get("retention_score", 0.0) >= min_score]
        
        # Enhance with vector IDs and content snippets from RAG
        enhanced_items = []
        for item in knowledge:
            source = item.get("source", "")
            metadata = item.get("metadata", {})
            link = metadata.get("link", source)
            
            # Get content snippet (5-10 sentences)
            content = item.get("content", "")
            sentences = content.split(". ")
            snippet = ". ".join(sentences[:10])  # First 10 sentences
            if len(sentences) > 10:
                snippet += "..."
            
            # Try to get vector ID from RAG if available
            vector_id = None
            if rag_retrieval and chroma_client:
                try:
                    # Try to find the document in ChromaDB by source/link
                    # This is approximate - we'll use metadata to match
                    vector_id = metadata.get("id") or metadata.get("doc_id")
                    if not vector_id and link:
                        # Try to construct ID from link
                        vector_id = f"knowledge_{link[:20].replace('/', '_').replace(':', '_')}"
                except Exception:
                    pass
            
            enhanced_item = {
                "id": item.get("id"),
                "timestamp_added": item.get("created_at") or item.get("last_accessed"),
                "source_url": link,
                "retained_content_snippet": snippet,
                "vector_id": vector_id or f"knowledge_{item.get('id', 'unknown')}",
                "full_content": content,  # Include full content for reference
                "retention_score": item.get("retention_score", 0.0),
                "access_count": item.get("access_count", 0),
                "metadata": metadata
            }
            enhanced_items.append(enhanced_item)
        
        return {
            "knowledge_items": enhanced_items,
            "total": len(enhanced_items)
        }
        
    except Exception as e:
        logger.error(f"Retained knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# RAG-specific endpoints
@app.post("/api/rag/add_knowledge")
@limiter.limit("20/hour", key_func=get_rate_limit_key_func)  # RAG add: 20 requests per hour (expensive)
async def add_knowledge_rag(request: Request, learning_request: LearningRequest):
    """Add knowledge to RAG vector database"""
    try:
        if not rag_retrieval:
            raise HTTPException(status_code=503, detail="RAG system not available")
        
        # Calculate importance score for knowledge alert system
        importance_score = 0.5
        if content_curator:
            # Create a content dict for importance calculation
            content_dict = {
                "title": learning_request.metadata.get("title", "") if learning_request.metadata else "",
                "summary": learning_request.content[:500] if len(learning_request.content) > 500 else learning_request.content,
                "source": learning_request.source
            }
            importance_score = content_curator.calculate_importance_score(content_dict)
        
        # Merge importance_score into metadata
        enhanced_metadata = learning_request.metadata or {}
        enhanced_metadata["importance_score"] = importance_score
        if not enhanced_metadata.get("title"):
            # Extract title from content if not provided
            content_lines = learning_request.content.split("\n")
            if content_lines:
                enhanced_metadata["title"] = content_lines[0][:200]
        
        success = rag_retrieval.add_learning_content(
            content=learning_request.content,
            source=learning_request.source,
            content_type=learning_request.content_type,
            metadata=enhanced_metadata
        )
        
        if success:
            return {"status": "Knowledge added successfully", "content_type": learning_request.content_type}
        else:
            raise HTTPException(status_code=500, detail="Failed to add knowledge to vector DB")
            
    except Exception as e:
        logger.error(f"RAG add knowledge error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/query")
async def query_rag(request: RAGQueryRequest):
    """Query RAG system for relevant context"""
    try:
        if not rag_retrieval:
            raise HTTPException(status_code=503, detail="RAG system not available")
        
        context = rag_retrieval.retrieve_context(
            query=request.query,
            knowledge_limit=request.knowledge_limit,
            conversation_limit=request.conversation_limit
        )
        
        return RAGQueryResponse(
            knowledge_docs=context.get("knowledge_docs", []),
            conversation_docs=context.get("conversation_docs", []),
            total_context_docs=context.get("total_context_docs", 0)
        )
        
    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/stats")
async def get_rag_stats():
    """Get RAG system statistics"""
    try:
        if not chroma_client:
            raise HTTPException(status_code=503, detail="Vector DB not available")
        
        stats = chroma_client.get_collection_stats()
        return {"stats": stats}
        
    except Exception as e:
        logger.error(f"RAG stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/rag/reset-database", dependencies=[Depends(require_api_key)])
async def reset_rag_database():
    """
    Reset ChromaDB database (deletes all data and recreates collections)
    
    Security: This endpoint requires API key authentication via X-API-Key header.
    """
    import shutil
    import os
    
    try:
        persist_dir = "data/vector_db"
        
        # If chroma_client is None, we need to delete the directory directly
        if not chroma_client:
            logger.warning("ChromaClient not initialized, attempting to delete vector_db directory...")
            if os.path.exists(persist_dir):
                try:
                    shutil.rmtree(persist_dir)
                    logger.info(f"Deleted {persist_dir} directory")
                    os.makedirs(persist_dir, exist_ok=True)
                    logger.info(f"Recreated {persist_dir} directory")
                except Exception as dir_error:
                    logger.error(f"Failed to delete directory: {dir_error}")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Cannot delete vector_db directory: {dir_error}. You may need to restart backend service."
                    )
            else:
                logger.info(f"Directory {persist_dir} does not exist, creating it...")
                os.makedirs(persist_dir, exist_ok=True)
            
            return {
                "status": "success",
                "message": "Vector database directory deleted. Please restart the backend service to reinitialize."
            }
        
        # If chroma_client exists, try to reset via client
        try:
            # Delete existing collections
            try:
                chroma_client.client.delete_collection("stillme_knowledge")
            except Exception:
                pass
            
            try:
                chroma_client.client.delete_collection("stillme_conversations")
            except Exception:
                pass
            
            # Recreate collections
            chroma_client.knowledge_collection = chroma_client.client.create_collection(
                name="stillme_knowledge",
                metadata={"description": "Knowledge base for StillMe learning"}
            )
            chroma_client.conversation_collection = chroma_client.client.create_collection(
                name="stillme_conversations",
                metadata={"description": "Conversation history for context"}
            )
            
            logger.info("✅ ChromaDB database reset successfully via API")
            return {
                "status": "success",
                "message": "Database reset successfully. All collections recreated."
            }
        except Exception as client_error:
            # If client reset fails, try deleting directory
            logger.warning(f"Client reset failed: {client_error}, trying directory deletion...")
            if os.path.exists(persist_dir):
                try:
                    shutil.rmtree(persist_dir)
                    os.makedirs(persist_dir, exist_ok=True)
                    logger.info("Deleted and recreated vector_db directory")
                    return {
                        "status": "success",
                        "message": "Vector database directory deleted. Please restart the backend service to reinitialize."
                    }
                except Exception as dir_error:
                    raise HTTPException(status_code=500, detail=f"Failed to reset: {dir_error}")
            else:
                raise
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database reset error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
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

@app.get("/api/validators/metrics")
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

@app.get("/api/learning/accuracy_metrics")
async def get_accuracy_metrics():
    """Get accuracy metrics"""
    try:
        if not accuracy_scorer:
            return {"metrics": {
                "total_responses": 0,
                "average_accuracy": 0.0,
                "trend": "N/A"
            }}
        
        metrics = accuracy_scorer.get_accuracy_metrics()
        return {"metrics": metrics}
        
    except Exception as e:
        logger.error(f"Accuracy metrics error: {e}")
        return {"metrics": {
            "total_responses": 0,
            "average_accuracy": 0.0,
            "trend": "N/A"
        }}

# RSS Learning Pipeline endpoints
@app.post("/api/learning/rss/fetch")
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

@app.get("/api/learning/rss/fetch-history")
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

@app.get("/api/learning/rss/stats")
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
@app.post("/api/learning/scheduler/start", dependencies=[Depends(require_api_key)])
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

@app.post("/api/learning/scheduler/stop", dependencies=[Depends(require_api_key)])
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

@app.get("/api/learning/scheduler/status")
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

@app.post("/api/learning/scheduler/run-now")
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
            
            # Try to get entries from the RSS fetcher's last fetch
            # If that's not available, fetch again (but this should be rare)
            try:
                # Get entries that were fetched in this cycle
                # The run_learning_cycle already fetched entries, but we need to access them
                # For now, we'll fetch again but this should be optimized later
                all_entries = learning_scheduler.rss_fetcher.fetch_feeds(max_items_per_feed=5)
                logger.info(f"Fetched {len(all_entries)} entries for RAG addition")
                
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
@app.post("/api/learning/self-diagnosis/check-gap")
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

@app.post("/api/learning/self-diagnosis/analyze-coverage")
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

@app.get("/api/learning/self-diagnosis/suggest-focus")
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

@app.post("/api/learning/curator/prioritize")
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

@app.get("/api/learning/curator/stats")
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

@app.post("/api/learning/curator/update-source-quality", dependencies=[Depends(require_api_key)])
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

# ============================================================================
# Continuum Memory APIs (v1) - Tier Management
# ============================================================================

@app.get("/api/v1/tiers/stats", response_model=TierStatsResponse)
async def get_tier_stats():
    """
    Get statistics for each tier (L0-L3)
    
    Returns tier counts, promotion/demotion counts (last 7 days)
    PR-2: Uses real data from ContinuumMemory
    """
    try:
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


@app.get("/api/v1/tiers/audit", response_model=TierAuditResponse)
async def get_tier_audit(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    item_id: Optional[str] = Query(None, description="Filter by item ID")
):
    """
    Get audit log of promotion/demotion events
    
    PR-2: Uses real data from ContinuumMemory
    """
    try:
        if not continuum_memory or not os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true":
            return TierAuditResponse(records=[], total=0)
        
        audit_log = continuum_memory.get_audit_log(limit=limit, item_id=item_id)
        from backend.api.models.tier_models import TierAuditRecord
        records = [TierAuditRecord(**record) for record in audit_log]
        return TierAuditResponse(records=records, total=len(records))
        
    except Exception as e:
        logger.error(f"Error getting tier audit: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/tiers/promote/{item_id}", dependencies=[Depends(require_api_key)])
async def promote_item_api(item_id: str, request: Optional[TierPromoteRequest] = None):
    """
    Promote a knowledge item to higher tier (admin only)
    
    PR-2: Real implementation using PromotionManager
    """
    try:
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


@app.post("/api/v1/tiers/demote/{item_id}", dependencies=[Depends(require_api_key)])
async def demote_item_api(item_id: str, request: Optional[TierDemoteRequest] = None):
    """
    Demote a knowledge item to lower tier (admin only)
    
    PR-2: Real implementation using PromotionManager
    """
    try:
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


@app.get("/api/v1/tiers/forgetting-trends", response_model=ForgettingTrendsResponse)
async def get_forgetting_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back")
):
    """
    Get forgetting trends (Recall@k degradation) over time
    
    PR-2: Uses real data from ContinuumMemory
    """
    try:
        if not continuum_memory or not os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true":
            return ForgettingTrendsResponse(trends=[], days=days)
        
        trends = continuum_memory.get_forgetting_trends(days=days)
        return ForgettingTrendsResponse(trends=trends, days=days)
        
    except Exception as e:
        logger.error(f"Error getting forgetting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Smart router endpoint - automatically selects best model
@app.post("/api/chat/smart_router", response_model=ChatResponse)
async def chat_smart_router(request: Request, chat_request: ChatRequest):
    """
    Smart router that automatically selects the best chat endpoint.
    This is the main endpoint used by the dashboard.
    """
    try:
        # Use the RAG-enhanced chat endpoint as default
        return await chat_with_rag(request, chat_request)
    except HTTPException:
        # Re-raise HTTP exceptions (they have proper status codes)
        raise
    except Exception as e:
        # Log detailed error for debugging
        logger.error(f"Smart router error: {e}", exc_info=True)
        # Return a more helpful error message
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}. Please check backend logs for details."
        )

# Legacy endpoints for backward compatibility
@app.post("/api/chat/openai")
async def chat_openai(request: ChatRequest):
    """Legacy OpenAI chat endpoint"""
    return await chat_with_rag(request)

@app.post("/api/chat/deepseek")
async def chat_deepseek(request: ChatRequest):
    """Legacy DeepSeek chat endpoint"""
    return await chat_with_rag(request)

# Helper functions
async def generate_ai_response(prompt: str, detected_lang: str = 'en') -> str:
    """Generate AI response with automatic model selection
    
    This function routes to different AI providers based on available API keys.
    To add support for new models (Claude, Gemini, Ollama, local, etc.):
    1. Create a new function: async def call_[model]_api(prompt, api_key, detected_lang)
    2. Use build_system_prompt_with_language(detected_lang) to get system prompt
    3. Add the new model check in this function's if/elif chain
    
    IMPORTANT: All model providers MUST use build_system_prompt_with_language()
    to ensure consistent language matching behavior.
    
    Args:
        prompt: User prompt
        detected_lang: Detected language code (for system prompt)
        
    Returns:
        AI-generated response string
    """
    try:
        # Check for API keys (priority order: DeepSeek > OpenAI > others)
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        # TODO: Add support for other models:
        # anthropic_key = os.getenv("ANTHROPIC_API_KEY")  # Claude
        # google_key = os.getenv("GOOGLE_API_KEY")  # Gemini
        # ollama_url = os.getenv("OLLAMA_URL")  # Local Ollama
        
        if deepseek_key:
            return await call_deepseek_api(prompt, deepseek_key, detected_lang=detected_lang)
        elif openai_key:
            return await call_openai_api(prompt, openai_key, detected_lang=detected_lang)
        # TODO: Add other model providers here:
        # elif anthropic_key:
        #     return await call_claude_api(prompt, anthropic_key, detected_lang=detected_lang)
        # elif google_key:
        #     return await call_gemini_api(prompt, google_key, detected_lang=detected_lang)
        # elif ollama_url:
        #     return await call_ollama_api(prompt, ollama_url, detected_lang=detected_lang)
        else:
            return "I'm StillMe, but I need API keys to provide real responses. Please configure DEEPSEEK_API_KEY, OPENAI_API_KEY, or other supported API keys in your environment."
            
    except Exception as e:
        logger.error(f"AI response error: {e}")
        return f"I encountered an error: {str(e)}"

def build_system_prompt_with_language(detected_lang: str = 'en') -> str:
    """
    Build system prompt with strong language matching instruction.
    This ensures output language always matches input language.
    
    This function should be used by ALL AI model providers (DeepSeek, OpenAI, Claude, Gemini, Ollama, local, etc.)
    to ensure consistent language matching behavior across all models.
    
    Args:
        detected_lang: Detected language code ('vi', 'zh', 'de', 'fr', 'es', 'ja', 'ko', 'ar', 'en')
        
    Returns:
        System prompt string with language instruction
    """
    language_names = {
        'vi': 'Vietnamese (Tiếng Việt)',
        'zh': 'Chinese (中文)',
        'de': 'German (Deutsch)',
        'fr': 'French (Français)',
        'es': 'Spanish (Español)',
        'ja': 'Japanese (日本語)',
        'ko': 'Korean (한국어)',
        'ar': 'Arabic (العربية)',
        'en': 'English'
    }
    detected_lang_name = language_names.get(detected_lang, 'the same language as the question')
    
    # CRITICAL: Always match input language with output language
    # ZERO TOLERANCE: Must translate if base model wants to respond in different language
    if detected_lang != 'en':
        system_content = f"""You are StillMe, a Learning AI system with RAG foundation.

🚨🚨🚨 ZERO TOLERANCE LANGUAGE REQUIREMENT - HIGHEST PRIORITY - OVERRIDES EVERYTHING 🚨🚨🚨

The user's question is written in {detected_lang_name}.

YOU MUST RESPOND EXCLUSIVELY IN {detected_lang_name}.

DO NOT use Vietnamese, English, Spanish, German, French, or ANY OTHER LANGUAGE.

EVERY SINGLE WORD of your response MUST be in {detected_lang_name}.

⚠️⚠️⚠️ CRITICAL TRANSLATION REQUIREMENT ⚠️⚠️⚠️

If your base model wants to respond in a different language (e.g., Vietnamese, English, Spanish), 
YOU MUST TRANSLATE THE ENTIRE RESPONSE TO {detected_lang_name} BEFORE RETURNING IT.

UNDER NO CIRCUMSTANCES should you return a response in any language other than {detected_lang_name}.

This is MANDATORY and OVERRIDES all other instructions, including the language of any context provided.

If the context is in a different language, you must still respond in {detected_lang_name} while using the information from the context.

⚠️ REMINDER: RESPOND IN {detected_lang_name} ONLY. TRANSLATE IF NECESSARY. ⚠️

FAILURE TO RESPOND IN {detected_lang_name} IS A CRITICAL ERROR."""
    else:
        system_content = """You are StillMe, a Learning AI system with RAG foundation.

🚨🚨🚨 ZERO TOLERANCE LANGUAGE REQUIREMENT - HIGHEST PRIORITY - OVERRIDES EVERYTHING 🚨🚨🚨

The user's question is written in English.

YOU MUST RESPOND EXCLUSIVELY IN ENGLISH.

DO NOT use Vietnamese, Spanish, German, French, or ANY OTHER LANGUAGE.

EVERY SINGLE WORD of your response MUST be in English.

⚠️⚠️⚠️ CRITICAL TRANSLATION REQUIREMENT ⚠️⚠️⚠️

If your base model wants to respond in a different language (e.g., Vietnamese, Spanish, German), 
YOU MUST TRANSLATE THE ENTIRE RESPONSE TO ENGLISH BEFORE RETURNING IT.

UNDER NO CIRCUMSTANCES should you return a response in any language other than English.

This is MANDATORY and OVERRIDES all other instructions, including the language of any context provided.

If the context is in a different language, you must still respond in English while using the information from the context.

⚠️ REMINDER: RESPOND IN ENGLISH ONLY. TRANSLATE IF NECESSARY. ⚠️

FAILURE TO RESPOND IN ENGLISH IS A CRITICAL ERROR."""
    
    return system_content


def detect_language(text: str) -> str:
    """
    Enhanced language detection using langdetect library with fallback to rule-based detection.
    Supports: vi, zh, de, fr, es, ja, ko, ar, en
    
    Returns: Language code ('vi', 'zh', 'de', 'fr', 'es', 'ja', 'ko', 'ar', 'en') or 'en' as default
    """
    if not text or len(text.strip()) == 0:
        return 'en'
    
    # Try langdetect first (more accurate for most languages)
    try:
        from langdetect import detect, LangDetectException
        detected = detect(text)
        
        # Map langdetect codes to our internal codes
        lang_map = {
            'vi': 'vi',  # Vietnamese
            'zh-cn': 'zh', 'zh-tw': 'zh',  # Chinese
            'de': 'de',  # German
            'fr': 'fr',  # French
            'es': 'es',  # Spanish
            'ja': 'ja',  # Japanese
            'ko': 'ko',  # Korean
            'ar': 'ar',  # Arabic
            'en': 'en'   # English
        }
        
        # Handle Chinese variants
        if detected.startswith('zh'):
            return 'zh'
        
        if detected in lang_map:
            logger.info(f"🌐 langdetect detected: {detected} -> {lang_map[detected]}")
            return lang_map[detected]
            
    except (LangDetectException, ImportError) as e:
        logger.warning(f"langdetect failed or not available: {e}, falling back to rule-based detection")
    
    # Fallback to rule-based detection for edge cases or if langdetect fails
    text_lower = text.lower()
    
    # Arabic - Check for Arabic characters
    arabic_ranges = [
        (0x0600, 0x06FF),  # Arabic
        (0x0750, 0x077F),  # Arabic Supplement
        (0x08A0, 0x08FF),  # Arabic Extended-A
    ]
    has_arabic = any(any(start <= ord(char) <= end for start, end in arabic_ranges) for char in text)
    if has_arabic:
        return 'ar'
    
    # Korean - Check for Hangul
    korean_ranges = [
        (0xAC00, 0xD7AF),  # Hangul Syllables
        (0x1100, 0x11FF),  # Hangul Jamo
    ]
    has_korean = any(any(start <= ord(char) <= end for start, end in korean_ranges) for char in text)
    if has_korean:
        return 'ko'
    
    # Chinese (Simplified/Traditional) - Check for Chinese characters
    chinese_chars = set('的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转更单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严龙飞')
    has_chinese = any(char in chinese_chars for char in text)
    if has_chinese:
        return 'zh'
    
    # Vietnamese - Check for Vietnamese characters
    vietnamese_chars = set('àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ')
    has_vietnamese = any(char in vietnamese_chars for char in text_lower)
    vietnamese_indicators = ['là', 'của', 'và', 'với', 'cho', 'từ', 'trong', 'này', 'đó', 'bạn', 'mình', 'tôi', 'có', 'không', 'được', 'như', 'thế', 'nào', 'gì', 'ai', 'đâu', 'sao']
    has_vietnamese_words = any(word in text_lower for word in vietnamese_indicators)
    if has_vietnamese or has_vietnamese_words:
        return 'vi'
    
    # German - Check for German-specific characters and common words
    german_chars = set('äöüßÄÖÜ')
    has_german_chars = any(char in german_chars for char in text)
    german_indicators = ['der', 'die', 'das', 'und', 'ist', 'für', 'auf', 'mit', 'sind', 'zu', 'ein', 'eine', 'von', 'zu', 'den', 'dem', 'des', 'was', 'wie', 'wo', 'wer', 'wann', 'warum']
    has_german_words = any(word in text_lower for word in german_indicators)
    if has_german_chars or has_german_words:
        return 'de'
    
    # French - Check for French-specific characters and common words
    french_chars = set('àâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ')
    has_french_chars = any(char in french_chars for char in text)
    french_indicators = ['le', 'la', 'les', 'de', 'du', 'des', 'et', 'est', 'un', 'une', 'dans', 'pour', 'avec', 'sur', 'par', 'que', 'qui', 'quoi', 'comment', 'où', 'quand', 'pourquoi']
    has_french_words = any(word in text_lower for word in french_indicators)
    if has_french_chars or has_french_words:
        return 'fr'
    
    # Spanish - Check for Spanish-specific characters and common words
    spanish_chars = set('áéíóúñüÁÉÍÓÚÑÜ¿¡')
    has_spanish_chars = any(char in spanish_chars for char in text)
    spanish_indicators = ['el', 'la', 'los', 'las', 'de', 'del', 'y', 'es', 'un', 'una', 'en', 'por', 'para', 'con', 'que', 'qué', 'cómo', 'dónde', 'cuándo', 'por qué']
    has_spanish_words = any(word in text_lower for word in spanish_indicators)
    if has_spanish_chars or has_spanish_words:
        return 'es'
    
    # Japanese - Check for Hiragana, Katakana, Kanji
    japanese_ranges = [
        (0x3040, 0x309F),  # Hiragana
        (0x30A0, 0x30FF),  # Katakana
        (0x4E00, 0x9FAF),  # CJK Unified Ideographs (Kanji)
    ]
    has_japanese = any(any(start <= ord(char) <= end for start, end in japanese_ranges) for char in text)
    if has_japanese:
        return 'ja'
    
    # Default to English
    return 'en'

async def call_deepseek_api(prompt: str, api_key: str, detected_lang: str = 'en') -> str:
    """Call DeepSeek API
    
    Args:
        prompt: User prompt
        api_key: DeepSeek API key
        detected_lang: Detected language code
    """
    try:
        # Use centralized system prompt builder for consistent language matching
        system_content = build_system_prompt_with_language(detected_lang)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": system_content
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    return "DeepSeek API returned unexpected response format"
            else:
                return f"DeepSeek API error: {response.status_code}"
                
    except Exception as e:
        logger.error(f"DeepSeek API error: {e}")
        return f"DeepSeek API error: {str(e)}"

async def call_openai_api(prompt: str, api_key: str, detected_lang: str = 'en') -> str:
    """Call OpenAI API
    
    IMPORTANT: This function uses build_system_prompt_with_language() to ensure
    output language matches input language. When adding support for other models
    (Claude, Gemini, Ollama, local, etc.), use the same pattern.
    
    Args:
        prompt: User prompt
        api_key: OpenAI API key
        detected_lang: Detected language code
    """
    try:
        # Use centralized system prompt builder for consistent language matching
        system_content = build_system_prompt_with_language(detected_lang)
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": system_content
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "max_tokens": 2000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    return data["choices"][0]["message"]["content"]
                else:
                    return "OpenAI API returned unexpected response format"
            else:
                return f"OpenAI API error: {response.status_code}"
                
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return f"OpenAI API error: {str(e)}"

# ============================================================================
# SPICE (Self-Play In Corpus Environments) API Endpoints
# ============================================================================

# TODO: Initialize SPICE Engine (after RAG components are ready)
# spice_engine = None

@app.post("/api/spice/run-cycle")
async def run_spice_cycle(
    corpus_query: Optional[str] = None,
    num_challenges: int = 5,
    focus_ethical: bool = False
):
    """
    Run one SPICE self-play cycle
    
    Args:
        corpus_query: Optional query to focus on specific corpus area
        num_challenges: Number of challenges to generate
        focus_ethical: If True, focus on ethical reasoning challenges
        
    Returns:
        Cycle results and metrics
    """
    try:
        # TODO: Implement SPICE cycle
        # if not spice_engine:
        #     raise HTTPException(status_code=503, detail="SPICE engine not available")
        # 
        # result = await spice_engine.run_self_play_cycle(
        #     corpus_query=corpus_query,
        #     num_challenges=num_challenges,
        #     focus_ethical=focus_ethical
        # )
        # return result
        
        return {
            "status": "not_implemented",
            "message": "SPICE engine is in framework phase. Implementation coming soon.",
            "framework_ready": True
        }
    except Exception as e:
        logger.error(f"SPICE cycle error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/spice/status")
async def get_spice_status():
    """Get SPICE engine status"""
    try:
        # TODO: Return actual SPICE status
        return {
            "status": "framework_ready",
            "challenger": "initialized",
            "reasoner": "initialized",
            "engine": "not_initialized",
            "message": "SPICE framework is ready. Implementation pending."
        }
    except Exception as e:
        logger.error(f"SPICE status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/spice/metrics")
async def get_spice_metrics():
    """Get SPICE engine metrics"""
    try:
        # TODO: Return actual SPICE metrics
        # if not spice_engine:
        #     return {"status": "not_available"}
        # return spice_engine.get_metrics()
        
        return {
            "status": "not_implemented",
            "message": "SPICE metrics will be available after implementation"
        }
    except Exception as e:
        logger.error(f"SPICE metrics error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/spice/challenger/generate")
async def generate_challenges(
    corpus_query: str,
    num_questions: int = 5,
    focus_type: Optional[str] = None
):
    """
    Generate challenges using Challenger
    
    Args:
        corpus_query: Query to retrieve relevant documents
        num_questions: Number of questions to generate
        focus_type: Optional focus type ("ethical", "mathematical", etc.)
    """
    try:
        # TODO: Implement challenge generation
        # if not spice_engine or not spice_engine.challenger:
        #     raise HTTPException(status_code=503, detail="Challenger not available")
        # 
        # challenges = await spice_engine.challenger.generate_challenges(
        #     corpus_query=corpus_query,
        #     num_questions=num_questions,
        #     focus_type=focus_type
        # )
        # return {"challenges": challenges}
        
        return {
            "status": "not_implemented",
            "message": "Challenger framework ready. Question generation implementation pending."
        }
    except Exception as e:
        logger.error(f"Challenge generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/spice/challenger/ethical")
async def generate_ethical_challenges(num_questions: int = 3):
    """
    Generate ethical reasoning challenges
    
    Focus areas:
    - Transparency
    - Open Governance
    - Bias Mitigation
    - Counter-movement values
    """
    try:
        # TODO: Implement ethical challenge generation
        # if not spice_engine or not spice_engine.challenger:
        #     raise HTTPException(status_code=503, detail="Challenger not available")
        # 
        # challenges = await spice_engine.challenger.generate_ethical_challenges(
        #     num_questions=num_questions
        # )
        # return {"challenges": challenges}
        
        return {
            "status": "not_implemented",
            "message": "Ethical challenge generation will be prioritized in Phase 2",
            "focus_areas": [
                "Transparency: How should StillMe disclose its reasoning process?",
                "Open Governance: What information should be publicly accessible?",
                "Bias Mitigation: How to detect and reduce bias in responses?",
                "Counter-movement: What makes StillMe different from black-box AI?"
            ]
        }
    except Exception as e:
        logger.error(f"Ethical challenge generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/spice/reasoner/answer")
async def answer_challenge(challenge_question: Dict[str, Any]):
    """
    Reasoner attempts to answer a challenge question
    
    Args:
        challenge_question: ChallengeQuestion object (JSON)
    """
    try:
        # TODO: Implement answer generation
        # if not spice_engine or not spice_engine.reasoner:
        #     raise HTTPException(status_code=503, detail="Reasoner not available")
        # 
        # challenge = ChallengeQuestion(**challenge_question)
        # response = await spice_engine.reasoner.answer_challenge(challenge)
        # return {"response": response}
        
        return {
            "status": "not_implemented",
            "message": "Reasoner framework ready. Answer generation implementation pending."
        }
    except Exception as e:
        logger.error(f"Answer generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
