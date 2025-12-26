"""
Chat Router for StillMe API
Handles all chat-related endpoints
"""

from fastapi import APIRouter, Request, HTTPException
from backend.api.models import ChatRequest, ChatResponse
from backend.api.rate_limiter import limiter, get_rate_limit_key_func, RateLimitExceeded, get_chat_rate_limit
from backend.api.utils.chat_helpers import (
    generate_ai_response,
    detect_language
)
from backend.api.utils.text_utils import (
    safe_unicode_slice,
    clean_response_text,
    fix_missing_line_breaks,
    strip_philosophy_from_answer,
    strip_forbidden_terms
)
from backend.api.utils.response_formatters import (
    add_timestamp_to_response,
    append_validation_warnings_to_response,
    build_ai_self_model_answer
)
from backend.api.handlers.query_classifier import (
    is_codebase_meta_question,
    is_factual_question,
    extract_full_named_entity,
    is_validator_count_question
)
from backend.api.handlers.prompt_builder import (
    build_prompt_context_from_chat_request,
    truncate_user_message,
    format_conversation_history,
    calculate_confidence_score,
    get_transparency_disclaimer,
    build_minimal_philosophical_prompt,
    get_validator_info_for_prompt
)
from backend.api.handlers.rag_retrieval_handler import (
    retrieve_rag_context,
    _log_rag_retrieval_decision
)
from backend.api.handlers.validation_handler import (
    handle_validation_with_fallback
)
from backend.api.handlers.llm_handler import (
    generate_llm_response
)
from backend.identity.prompt_builder import (
    UnifiedPromptBuilder,
    PromptContext,
    FPSResult
)
from backend.core.manifest_loader import (
    get_validator_count,
    get_validator_summary,
    get_layers_info,
    get_manifest_text_for_prompt
)
from backend.philosophy.processor import (
    is_philosophical_question_about_consciousness,
    process_philosophical_question
)
from backend.style.style_engine import detect_domain, DomainType
from backend.services.cache_service import (
    get_cache_service,
    CACHE_PREFIX_LLM,
    TTL_LLM_RESPONSE
)
from backend.api.config.chat_config import get_chat_config
import logging
import os
import re
import time
import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
import json
import unicodedata

logger = logging.getLogger(__name__)

router = APIRouter()


# Text utility functions moved to backend/api/utils/text_utils.py


# RAG retrieval functions moved to backend/api/handlers/rag_retrieval_handler.py

# Query classification functions moved to backend/api/handlers/query_classifier.py


# Response formatting functions moved to backend/api/utils/response_formatters.py


# Text utility functions moved to backend/api/utils/text_utils.py

# Import global services from main (temporary - will refactor to dependency injection later)
# These are initialized in main.py before routers are included
# Note: We import after main.py has initialized these services
def get_rag_retrieval():
    """Get RAG retrieval service from main module"""
    import backend.api.main as main_module
    return main_module.rag_retrieval

def get_knowledge_retention():
    """Get knowledge retention service from main module"""
    import backend.api.main as main_module
    return main_module.knowledge_retention

def get_accuracy_scorer():
    """Get accuracy scorer service from main module"""
    import backend.api.main as main_module
    return main_module.accuracy_scorer

def get_self_diagnosis():
    """Get self diagnosis service from main module"""
    import backend.api.main as main_module
    return getattr(main_module, 'self_diagnosis', None)

def get_style_learner():
    """Get style learner service"""
    from backend.services.style_learner import StyleLearner
    # Singleton instance
    if not hasattr(get_style_learner, '_instance'):
        get_style_learner._instance = StyleLearner()
    return get_style_learner._instance

# Prompt building functions moved to backend/api/handlers/prompt_builder.py

# Prompt building functions moved to backend/api/handlers/prompt_builder.py

# Query classification functions moved to backend/api/handlers/query_classifier.py

def _build_safe_refusal_answer(question: str, detected_lang: str, suspicious_entity: Optional[str] = None, fps_result: Optional[object] = None) -> Optional[str]:
    """
    Build a safe, honest refusal answer when hallucination is detected.
    
    This function now uses EPD-Fallback (Epistemic-Depth Fallback) with 4 mandatory parts:
    A. Honest Acknowledgment
    B. Analysis of Why Concept Seems Hypothetical
    C. Find Most Similar Real Concepts
    D. Guide User to Verify Sources
    
    CRITICAL: If this is a well-known historical fact (Geneva 1954, etc.), returns None
    to signal that base knowledge should be used instead of fallback.
    
    Args:
        question: User question
        detected_lang: Language code
        suspicious_entity: Optional entity/concept that triggered the guard
        fps_result: Optional FPSResult for additional context
        
    Returns:
        EPD-Fallback answer in appropriate language (4 parts, profound, non-fabricated),
        or None if this is a well-known historical fact (should use base knowledge)
    """
    # Use EPD-Fallback generator
    from backend.guards.epistemic_fallback import get_epistemic_fallback_generator
    
    generator = get_epistemic_fallback_generator()
    fallback = generator.generate_epd_fallback(
        question=question,
        detected_lang=detected_lang,
        suspicious_entity=suspicious_entity,
        fps_result=fps_result
    )
    
    # If None, it's a well-known historical fact - caller should use base knowledge
    if fallback is None:
        logger.info("✅ Well-known historical fact detected - caller should use base knowledge instead of fallback")
    
    return fallback

# Philosophy-Lite System Prompt for non-RAG philosophical questions
# TASK 3: Refactored to include Anchor → Unpack → Explore → Edge → Return structure
# This is a minimal system prompt to prevent context overflow (~200-300 tokens)
# INTEGRATED: Uses Style Engine (backend/style/style_engine.py) for structure guidance
# Import unified PHILOSOPHY_LITE_SYSTEM_PROMPT from identity module
# CRITICAL: This is now the SINGLE SOURCE OF TRUTH - do not define here
from backend.identity.philosophy_lite import PHILOSOPHY_LITE_SYSTEM_PROMPT

# Prompt building functions moved to backend/api/handlers/prompt_builder.py

# Validation handler functions moved to backend/api/handlers/validation_handler.py

@router.post("/rag", response_model=ChatResponse)
@limiter.limit(get_chat_rate_limit, key_func=get_rate_limit_key_func)  # Chat rate limit (dynamic based on API key)
async def chat_with_rag(request: Request, chat_request: ChatRequest):
    """Chat with RAG-enhanced responses"""
    # Note: 'time' module is already imported at top level
    start_time = time.time()
    timing_logs = {}
    
    # DEBUG: Log request received (very early)
    logger.info(f"📥 Received chat request: message_length={len(chat_request.message)}, use_option_b={getattr(chat_request, 'use_option_b', 'NOT_SET')}")
    
    # Initialize latency variables (will be set during processing)
    rag_retrieval_latency = 0.0
    llm_inference_latency = 0.0
    
    # Initialize variables before try-except to avoid UnboundLocalError
    confidence_score = None
    validation_info = None
    processing_steps = []  # Track processing steps for real-time status
    style_learning_response = None  # Initialize for style learning
    response = None  # CRITICAL: Initialize response to prevent UnboundLocalError
    raw_response = None  # CRITICAL: Initialize raw_response to prevent UnboundLocalError
    final_response = None  # CRITICAL: Initialize final_response to prevent UnboundLocalError
    
    # Initialize fallback flags for both RAG and non-RAG paths to prevent UnboundLocalError
    is_fallback_meta_answer = False  # Used in RAG path
    is_fallback_meta_answer_rag = False  # Used in RAG path post-processing
    is_fallback_meta_answer_non_rag = False  # Used in non-RAG path
    is_fallback_for_learning = False  # Used to skip learning extraction for fallback meta-answers
    use_philosophy_lite_rag = False  # Initialize to prevent UnboundLocalError
    # CRITICAL: Initialize is_technical_about_system_rag at function level to prevent UnboundLocalError
    # This variable is used in RAG path (line 3970) and must be defined in ALL code paths
    is_technical_about_system_rag = False
    # CRITICAL: Initialize roleplay detection flags EARLY to prevent UnboundLocalError
    is_general_roleplay = False
    is_religion_roleplay = False
    # CRITICAL: Initialize exclude_types EARLY to prevent UnboundLocalError
    # This ensures it's available for all retrieval paths, even if RAG is disabled
    exclude_types = []
    
    # OPTION B PIPELINE: Check if enabled
    use_option_b = getattr(chat_request, 'use_option_b', False) or os.getenv("STILLME_USE_OPTION_B_PIPELINE", "false").lower() == "true"
    
    # DEBUG: Log Option B status (before FPS check)
    logger.info(f"🔍 Option B check (initial): use_option_b={use_option_b}, request_attr={getattr(chat_request, 'use_option_b', 'NOT_SET')}, env_var={os.getenv('STILLME_USE_OPTION_B_PIPELINE', 'NOT_SET')}")
    
    try:
        # Get services
        rag_retrieval = get_rag_retrieval()
        knowledge_retention = get_knowledge_retention()
        accuracy_scorer = get_accuracy_scorer()
        style_learner = get_style_learner()
        
        # Initialize Decision Logger for agentic decision tracking
        from backend.core.decision_logger import get_decision_logger, AgentType, DecisionType
        decision_logger = get_decision_logger()
        detected_lang_for_logging = detect_language(chat_request.message) if 'detect_language' in dir() else "en"
        session_id = decision_logger.start_session(chat_request.message, detected_lang_for_logging)
        
        # Get user_id from request (if available)
        user_id = chat_request.user_id or request.client.host if hasattr(request, 'client') else "anonymous"

        # QUERY ROUTING: Route special query types to appropriate handlers
        from backend.api.handlers.query_router import route_query
        
        early_response = await route_query(
            chat_request=chat_request,
            request=request,
            processing_steps=processing_steps,
            timing_logs=timing_logs,
            start_time=start_time,
            decision_logger=decision_logger,
            is_general_roleplay=is_general_roleplay
        )
        
        if early_response:
            return early_response
        
        # NOTE: Codebase meta-question and ambiguity clarification are now handled by query_router
        
        # Track if we detected MEDIUM ambiguity (will add disclaimer to response)
        ambiguity_score = 0.0
        ambiguity_level = "LOW"
        ambiguity_reasons = []
        try:
            from backend.core.ambiguity_detector import get_ambiguity_detector
            ambiguity_detector = get_ambiguity_detector()
            ambiguity_score, ambiguity_level_enum, ambiguity_reasons = ambiguity_detector.detect_ambiguity(
                chat_request.message,
                conversation_history=chat_request.conversation_history
            )
            ambiguity_level = ambiguity_level_enum.value
            if ambiguity_level == "MEDIUM":
                logger.info(f"⚠️ MEDIUM ambiguity detected (score={ambiguity_score:.2f}) - will add disclaimer to response")
                processing_steps.append(f"⚠️ Medium ambiguity detected (score={ambiguity_score:.2f})")
        except Exception:
            pass  # Non-critical
        
        # Detect learning metrics queries - auto-query API if user asks about learning today
        is_learning_metrics_query = False
        learning_metrics_data = None
        is_learning_sources_query = False
        current_learning_sources = None
        message_lower = chat_request.message.lower()
        learning_metrics_keywords = [
            "ngày hôm nay bạn đã học", "học được bao nhiêu", "learn today", "learned today",
            "học được gì", "what did you learn", "học được những gì", "nội dung gì"
        ]
        learning_sources_keywords = [
            "học từ nguồn nào", "sources", "nguồn học", "learning sources", "bạn đang học từ",
            "bạn học từ đâu", "where do you learn", "what sources", "nguồn nào", "từ nguồn nào",
            "hiện bạn đang học", "bạn học tập cụ thể từ", "chủ đề cụ thể", "đề xuất nguồn"
        ]
        # CRITICAL: Detect if user asks to propose learning sources based on knowledge gaps
        is_learning_proposal_query = False
        learning_proposal_keywords = [
            "đề xuất nguồn học", "propose learning", "đề xuất thêm nguồn", "suggest sources",
            "bổ sung nguồn", "thêm nguồn học", "kiến thức cần thiết", "knowledge gaps",
            "lỗ hổng kiến thức", "thiếu kiến thức", "cần học thêm"
        ]
        if any(keyword in message_lower for keyword in learning_proposal_keywords):
            is_learning_proposal_query = True
            logger.info("Learning proposal query detected - will analyze actual knowledge gaps")
        if any(keyword in message_lower for keyword in learning_metrics_keywords):
            is_learning_metrics_query = True
            logger.info("Learning metrics query detected - fetching metrics data")
            try:
                from backend.services.learning_metrics_tracker import get_learning_metrics_tracker
                tracker = get_learning_metrics_tracker()
                # Get today's metrics
                learning_metrics_data = tracker.get_metrics_for_today()
                if learning_metrics_data:
                    logger.info(f"✅ Fetched learning metrics for today: {learning_metrics_data.total_entries_added} entries added")
                else:
                    logger.info("⚠️ No learning metrics available for today yet")
            except Exception as metrics_error:
                logger.warning(f"Failed to fetch learning metrics: {metrics_error}")
        
        # Detect learning sources queries - auto-query API to get current sources
        if any(keyword in message_lower for keyword in learning_sources_keywords):
            is_learning_sources_query = True
            logger.info("Learning sources query detected - fetching current sources")
            try:
                # Query the learning sources API directly (internal call)
                from backend.api.routers.learning_router import get_current_learning_sources
                current_learning_sources = await get_current_learning_sources()
                if current_learning_sources:
                    logger.info(f"✅ Fetched current learning sources: {len(current_learning_sources.get('current_sources', {}))} sources")
                else:
                    logger.warning("⚠️ Failed to fetch learning sources: empty response")
            except Exception as sources_error:
                logger.warning(f"Failed to fetch learning sources: {sources_error}")
        
        # CRITICAL: Get real-time system status for System Self-Awareness
        system_status_note = ""
        try:
            from backend.services.system_monitor import get_system_monitor
            system_monitor = get_system_monitor()
            # CRITICAL: Always attach RSS fetcher via singleton (avoids relying on backend.api.main init order)
            try:
                from backend.services.rss_fetcher import get_rss_fetcher as get_rss_fetcher_singleton

                system_monitor.set_components(rss_fetcher=get_rss_fetcher_singleton())
                logger.debug("✅ Set rss_fetcher for system_monitor (singleton)")
            except Exception as rss_comp_error:
                logger.debug(f"Could not set rss_fetcher singleton for system_monitor: {rss_comp_error}")
            # Set component references if available
            try:
                import backend.api.main as main_module
                if hasattr(main_module, 'source_integration') and main_module.source_integration:
                    system_monitor.set_components(source_integration=main_module.source_integration)
                    logger.debug("✅ Set source_integration for system_monitor")
            except Exception as comp_error:
                logger.debug(f"Could not set components for system_monitor: {comp_error}")
                # Fallback: Try to query API directly if components not available
                if is_learning_sources_query:
                    try:
                        from backend.api.routers.learning_router import get_current_learning_sources
                        # Note: 'asyncio' is already imported at top level (line 32)
                        # If we're in async context, we can await
                        # Otherwise, we'll use the already-fetched current_learning_sources
                        if current_learning_sources:
                            rss_info = current_learning_sources.get("current_sources", {}).get("rss", {})
                            feeds_count = rss_info.get("feeds_count", 0)
                            failed_feeds_info = rss_info.get("failed_feeds", {})
                            if failed_feeds_info:
                                failed_count = failed_feeds_info.get("failed_count", 0)
                                successful_count = failed_feeds_info.get("successful_count", 0)
                                system_status_note = f"[System: {feeds_count} RSS feeds ({failed_count} failed, {successful_count} ok)]"
                                logger.info(f"📊 System status note (from API): {system_status_note}")
                    except Exception:
                        pass  # Non-critical
            system_status_note_from_monitor = system_monitor.get_system_status_note()
            if system_status_note_from_monitor and system_status_note_from_monitor != "[System: Status unavailable]":
                system_status_note = system_status_note_from_monitor
                logger.info(f"📊 System status note: {system_status_note}")
            elif not system_status_note:
                logger.warning("⚠️ System status note unavailable - system_monitor may not have components")
        except Exception as monitor_error:
            logger.warning(f"Could not get system status: {monitor_error}")
            # Fallback for learning sources queries
            if is_learning_sources_query and current_learning_sources:
                try:
                    rss_info = current_learning_sources.get("current_sources", {}).get("rss", {})
                    feeds_count = rss_info.get("feeds_count", 0)
                    failed_feeds_info = rss_info.get("failed_feeds", {})
                    if failed_feeds_info:
                        failed_count = failed_feeds_info.get("failed_count", 0)
                        successful_count = failed_feeds_info.get("successful_count", 0)
                        system_status_note = f"[System: {feeds_count} RSS feeds ({failed_count} failed, {successful_count} ok)]"
                        logger.info(f"📊 System status note (fallback from API): {system_status_note}")
                except Exception:
                    pass
        
        # Detect philosophical questions - filter technical RAG documents
        is_philosophical = False
        try:
            from backend.core.question_classifier import is_philosophical_question
            # CRITICAL: Skip philosophical detection for roleplay questions
            # Roleplay questions should be answered as roleplay, not as philosophical analysis
            if not is_general_roleplay:
                is_philosophical = is_philosophical_question(chat_request.message)
            else:
                is_philosophical = False
                logger.info("General roleplay question detected - skipping philosophical detection")
            if is_philosophical:
                logger.info("Philosophical question detected - will exclude technical documents from RAG")
        except ImportError:
            logger.warning("Question classifier not available, skipping philosophical detection")
        except Exception as classifier_error:
            logger.warning(f"Question classifier error: {classifier_error}")
        
        # Detect religion/roleplay questions - these should answer from identity prompt, not RAG context
        # Note: is_religion_roleplay and is_general_roleplay are already initialized at function start
        is_roleplay_about_stillme = False
        try:
            from backend.core.question_classifier import is_religion_roleplay_question, is_general_roleplay_question
            # Update roleplay flags (already initialized above)
            is_religion_roleplay = is_religion_roleplay_question(chat_request.message)
            is_general_roleplay = is_general_roleplay_question(chat_request.message)
            # Check if roleplay question is about StillMe (e.g., "Roleplay: Omni-BlackBox trả lời về StillMe...")
            if is_general_roleplay:
                question_lower = chat_request.message.lower()
                stillme_keywords = ["stillme", "still me", "validation chain", "validators", "rag", "chromadb"]
                is_roleplay_about_stillme = any(keyword in question_lower for keyword in stillme_keywords)
                logger.info(f"General roleplay question detected - will skip codebase meta-question and philosophical detection. About StillMe: {is_roleplay_about_stillme}")
            if is_religion_roleplay:
                logger.info("Religion/roleplay question detected - will skip context quality warnings and force templates")
        except ImportError:
            logger.warning("Question classifier not available, skipping roleplay detection")
        except Exception as classifier_error:
            logger.warning(f"Question classifier error: {classifier_error}")
        
        # CRITICAL: Identity Truth Override - MUST be checked FIRST, before ANY other processing
        # This ensures StillMe NEVER falls back to generic LLM knowledge about itself
        # Initialize query detection flags EARLY
        is_stillme_query = False
        is_origin_query = False
        
        # CRITICAL FIX: ALWAYS detect origin queries FIRST, before ANY other checks
        # Identity Truth Override must work even when RAG is disabled
        try:
            from backend.core.stillme_detector import (
                detect_stillme_query, 
                get_foundational_query_variants,
                detect_origin_query
            )
            # CRITICAL: Detect origin queries FIRST, before any other processing
            # This ensures Identity Truth Override works even when RAG is disabled
            is_origin_query, origin_keywords = detect_origin_query(chat_request.message)
            if is_origin_query:
                logger.debug(f"Origin query detected! Matched keywords: {origin_keywords}")
        except ImportError:
            logger.warning("StillMe detector not available, skipping origin detection")
        except Exception as detector_error:
            logger.warning(f"StillMe detector error: {detector_error}")
        
        # NOTE: Origin query, religion choice rejection, honesty question, and AI self-model query
        # are now handled by query_router. is_origin_query is still needed for StillMe query detection below.
        
        # CRITICAL: Detect validator count questions for special handling
        # We will force-inject manifest and use lower similarity threshold, NOT hardcode
        is_validator_count_query = is_validator_count_question(chat_request.message)
        
        # EXTERNAL DATA LAYER: Check for external data queries (weather, news, etc.)
        # This bypasses RAG and fetches real-time data from external APIs
        try:
            from backend.external_data import ExternalDataOrchestrator, detect_external_data_intent
            
            external_data_intent = detect_external_data_intent(chat_request.message)
            if external_data_intent and external_data_intent.confidence >= 0.7:
                logger.info(f"🌐 External data intent detected: type={external_data_intent.type}, confidence={external_data_intent.confidence}")
                
                # Detect language for response formatting
                detected_lang = detect_language(chat_request.message)
                
                # Route to external data provider
                orchestrator = ExternalDataOrchestrator()
                result = await orchestrator.route(external_data_intent)
                
                if result and result.success:
                    # Format response with source + timestamp (in user's language)
                    response_text = orchestrator.format_response(result, chat_request.message, detected_lang)
                    
                    # Log for audit
                    logger.info(
                        f"✅ External data fetched: source={result.source}, "
                        f"cached={result.cached}, timestamp={result.timestamp.isoformat()}"
                    )
                    
                    processing_steps.append(f"🌐 Fetched from {result.source} API")
                    if result.cached:
                        processing_steps.append("💾 Used cached data")
                    
                    from backend.core.epistemic_state import EpistemicState
                    return ChatResponse(
                        response=response_text,
                        confidence_score=0.9,  # High confidence for API data
                        has_citation=True,  # External data has source attribution
                        validation_info={
                            "passed": True,
                            "external_data_source": result.source,
                            "external_data_timestamp": result.timestamp.isoformat(),
                            "external_data_cached": result.cached,
                            "context_docs_count": 0  # External data, no RAG context
                        },
                        processing_steps=processing_steps,
                        timing_logs={
                            "total_time": time.time() - start_time,
                            "rag_retrieval_latency": 0.0,
                            "llm_inference_latency": 0.0
                        },
                        epistemic_state=EpistemicState.KNOWN.value,  # External API data is KNOWN
                        used_fallback=False
                    )
                elif result and not result.success:
                    # API failed - fallback to RAG with transparent error message
                    logger.warning(
                        f"⚠️ External data fetch failed: source={result.source}, "
                        f"error={result.error_message}. Falling back to RAG."
                    )
                    processing_steps.append(f"⚠️ External data unavailable ({result.source}), using RAG")
                    # Continue to RAG pipeline below
                else:
                    # No result (no provider found) - continue to RAG
                    logger.debug(f"⚠️ No external data provider found for intent: {external_data_intent.type}")
                    # Continue to RAG pipeline below
                    
        except ImportError:
            logger.debug("External data module not available, skipping external data detection")
        except Exception as external_data_error:
            logger.warning(f"External data handler error: {external_data_error}", exc_info=True)
            # Continue to normal flow if external data handler fails
        
        # Detect philosophical questions (consciousness/emotion/understanding) - use 3-layer processor
        # CRITICAL: This check happens AFTER AI_SELF_MODEL and honesty handler
        is_philosophical_consciousness = False
        try:
            is_philosophical_consciousness = is_philosophical_question_about_consciousness(chat_request.message)
            if is_philosophical_consciousness:
                logger.info("Philosophical question (consciousness/emotion/understanding) detected - using 3-layer processor")
                # Detect language for the answer
                detected_lang = detect_language(chat_request.message)
                # Process with 3-layer philosophy processor (Guard + Intent + Deep Answer)
                philosophical_answer = process_philosophical_question(
                    user_question=chat_request.message,
                    language=detected_lang
                )
                
                # CRITICAL: Pass philosophical answer through rewrite engine for variation and adaptation
                # This prevents mode collapse by allowing LLM to adapt the answer to the specific question
                # CRITICAL: User priority is QUALITY (honesty, transparency, depth) over speed - always rewrite
                rewrite_attempts = 0
                config = get_chat_config()
                max_rewrite_attempts = config.rewrite.MAX_ATTEMPTS
                rewrite_success = False
                validation_info = None
                confidence_score = config.confidence.PHILOSOPHICAL_DEFAULT  # Default confidence for philosophical answers
                used_fallback = False
                
                try:
                    from backend.postprocessing.rewrite_llm import get_rewrite_llm
                    from backend.postprocessing.quality_evaluator import get_quality_evaluator, QualityLevel
                    from backend.postprocessing.optimizer import get_postprocessing_optimizer
                    
                    # Evaluate quality of philosophical answer
                    evaluator = get_quality_evaluator()
                    # Detect if this is a StillMe query for quality evaluation
                    is_stillme_query_for_quality = False
                    try:
                        from backend.core.stillme_detector import detect_stillme_query
                        is_stillme_query_for_quality, _ = detect_stillme_query(chat_request.message)
                    except Exception:
                        pass
                    
                    quality_result = evaluator.evaluate(
                        text=philosophical_answer,
                        is_philosophical=True,
                        original_question=chat_request.message,
                        is_stillme_query=is_stillme_query_for_quality
                    )
                    
                    # CRITICAL: Always rewrite philosophical answers to adapt to specific question
                    # User priority: QUALITY (honesty, transparency, depth) over speed
                    # Retry rewrite if it fails - don't skip
                    optimizer = get_postprocessing_optimizer()
                    # Phase 4: Use cost-benefit policy for rewrite decision
                    # Pass validation_result if available (for philosophical path, validation happens after rewrite)
                    should_rewrite, rewrite_reason, max_attempts = optimizer.should_rewrite(
                        quality_result=quality_result,
                        is_philosophical=True,
                        response_length=len(philosophical_answer),
                        validation_result=None,  # Validation happens after rewrite for philosophical questions
                        rewrite_count=0,
                        user_question=chat_request.message  # P2: Template detection
                    )
                    
                    # P2: Respect template detection - don't force rewrite if P2 skipped
                    # Only force rewrite if P2 didn't skip (should_rewrite=True or reason != "user_requested_template")
                    force_rewrite = rewrite_reason != "user_requested_template" and rewrite_reason != "quality_acceptable"
                    if should_rewrite or force_rewrite:
                        rewrite_llm = get_rewrite_llm()
                        
                        # Retry rewrite if it fails (up to max_rewrite_attempts)
                        while rewrite_attempts < max_rewrite_attempts and not rewrite_success:
                            rewrite_attempts += 1
                            logger.info(f"🔄 Rewriting philosophical answer (attempt {rewrite_attempts}/{max_rewrite_attempts}): {rewrite_reason or 'forced for variation and depth'}")
                            
                            try:
                                # CRITICAL: Check if this is AI_SELF_MODEL domain
                                detected_domain = detect_domain(chat_request.message)
                                is_ai_self_model_domain = (detected_domain == DomainType.AI_SELF_MODEL)
                                
                                rewrite_result = await rewrite_llm.rewrite(
                                    text=philosophical_answer,
                                    original_question=chat_request.message,
                                    quality_issues=quality_result.get("reasons", []) or ["template-like", "needs_question_adaptation", "needs_more_depth"],
                                    is_philosophical=True,
                                    detected_lang=detected_lang,
                                    is_ai_self_model=is_ai_self_model_domain
                                )
                                
                                if rewrite_result.was_rewritten:
                                    philosophical_answer = rewrite_result.text
                                    rewrite_success = True
                                    processing_steps.append(f"✅ Philosophical answer rewritten for better adaptation and depth (attempt {rewrite_attempts})")
                                    logger.info(f"✅ Rewrite successful on attempt {rewrite_attempts}")
                                else:
                                    error_msg = rewrite_result.error or 'Unknown error'
                                    logger.warning(f"⚠️ Rewrite attempt {rewrite_attempts} failed: {error_msg}")
                                    if rewrite_attempts < max_rewrite_attempts:
                                        logger.info(f"🔄 Retrying rewrite...")
                                    else:
                                        logger.error(f"❌ All rewrite attempts failed, using original answer")
                            except Exception as rewrite_attempt_error:
                                logger.warning(f"⚠️ Rewrite attempt {rewrite_attempts} exception: {rewrite_attempt_error}")
                                if rewrite_attempts < max_rewrite_attempts:
                                    logger.info(f"🔄 Retrying rewrite after exception...")
                                else:
                                    logger.error(f"❌ All rewrite attempts failed due to exceptions, using original answer")
                    else:
                        logger.debug(f"⏭️ Philosophical answer quality acceptable, skipping rewrite")
                        
                except Exception as rewrite_error:
                    logger.error(f"❌ Critical error during philosophical answer rewrite setup: {rewrite_error}")
                    # Continue with original answer if rewrite setup fails
                
                # CRITICAL: Pass philosophical answer through validation chain
                # User priority: QUALITY (honesty, transparency, depth) - validation is mandatory
                # Even though it's philosophical, we still need to validate for:
                # - Language consistency
                # - Ethics (no harmful content)
                # - Identity check (no anthropomorphism)
                # - Confidence (appropriate uncertainty)
                try:
                    # Create empty context for philosophical questions (no RAG needed for pure philosophical questions)
                    philosophical_context = {
                        "knowledge_docs": [],
                        "conversation_docs": [],
                        "context_quality": None,
                        "avg_similarity_score": None
                    }
                    
                    # Build empty context docs for validation
                    ctx_docs = []
                    
                    # Build minimal prompt for OpenAI fallback (if needed)
                    # CRITICAL: OpenAI fallback needs a prompt to answer, not empty string
                    from backend.identity.philosophy_lite import PHILOSOPHY_LITE_SYSTEM_PROMPT
                    from backend.api.utils.chat_helpers import build_system_prompt_with_language
                    # FIX: get_language_name doesn't exist, use simple mapping
                    def get_language_name(lang_code: str) -> str:
                        """Simple language name mapping"""
                        mapping = {
                            "vi": "Vietnamese",
                            "en": "English",
                            "zh": "Chinese",
                            "ja": "Japanese",
                            "ko": "Korean",
                            "fr": "French",
                            "de": "German",
                            "es": "Spanish",
                        }
                        return mapping.get(lang_code, lang_code)
                    
                    # Build system prompt with language
                    # FIX: build_system_prompt_with_language only accepts detected_lang
                    system_prompt = build_system_prompt_with_language(detected_lang=detected_lang)
                    
                    # Build minimal prompt for OpenAI fallback
                    lang_name = get_language_name(detected_lang)
                    fallback_prompt = f"""⚠️⚠️⚠️ LANGUAGE REQUIREMENT ⚠️⚠️⚠️

The user's question is in {lang_name.upper()}. 

YOU MUST respond in {lang_name.upper()} ONLY.

{system_prompt}

🚨🚨🚨 CRITICAL: USER QUESTION ABOVE IS THE PRIMARY TASK 🚨🚨🚨

User Question: {chat_request.message}

**YOUR PRIMARY TASK IS TO ANSWER THE USER QUESTION ABOVE DIRECTLY AND ACCURATELY.**
- Focus on what the user is actually asking
- Provide a helpful, accurate answer
- Use your base knowledge if needed
- Be transparent about sources

Remember: RESPOND IN {lang_name.upper()} ONLY."""
                    
                    # Call validation chain with is_philosophical=True
                    # This will relax citation requirements but still check ethics, language, identity, confidence
                    validation_response, validation_info, confidence_score, used_fallback, step_validation_info, consistency_info, validated_ctx_docs = await handle_validation_with_fallback(
                        raw_response=philosophical_answer,
                        context=philosophical_context,
                        detected_lang=detected_lang,
                        is_philosophical=True,  # Relax citation requirements for philosophical questions
                        is_religion_roleplay=False,
                        chat_request=chat_request,
                        enhanced_prompt=fallback_prompt,  # CRITICAL: Provide prompt for OpenAI fallback
                        context_text="",  # Not used for philosophical questions
                        citation_instruction="",  # Not used for philosophical questions
                        num_knowledge=0,
                        processing_steps=processing_steps,
                        timing_logs={},
                        is_origin_query=is_origin_query,
                        is_stillme_query=is_stillme_query
                    )
                    
                    # Use validated response
                    philosophical_answer = validation_response
                    processing_steps.append("✅ Philosophical answer validated through validation chain")
                    
                except Exception as validation_error:
                    logger.error(f"❌ Critical error during philosophical answer validation: {validation_error}")
                    # Continue with unvalidated answer if validation fails (should not happen, but safety first)
                    processing_steps.append(f"⚠️ Validation failed: {validation_error}, using unvalidated answer")
                    validation_info = None
                    config = get_chat_config()
                    confidence_score = config.confidence.PHILOSOPHICAL_FAILED_VALIDATION  # Lower confidence if validation failed
                    used_fallback = False
                
                # Return response with validation info
                processing_steps.append("✅ Detected philosophical question - returning 3-layer processed answer (with rewrite and validation)")
                # Calculate epistemic state for philosophical answer
                from backend.core.epistemic_state import calculate_epistemic_state, EpistemicState
                try:
                    philosophical_epistemic_state = calculate_epistemic_state(
                        validation_info=validation_info,
                        confidence_score=confidence_score,
                        response_text=philosophical_answer,
                        context_docs_count=0  # Philosophical answers don't use RAG context
                    )
                except Exception as e:
                    logger.warning(f"⚠️ Failed to calculate epistemic state for philosophical answer: {e}")
                    philosophical_epistemic_state = EpistemicState.UNCERTAIN  # Default for philosophical
                
                return ChatResponse(
                    response=philosophical_answer,
                    confidence_score=confidence_score,
                    processing_steps=processing_steps,
                    timing_logs={
                        "total_time": time.time() - start_time,
                        "rag_retrieval_latency": 0.0,
                        "llm_inference_latency": 0.0,
                        "rewrite_attempts": rewrite_attempts,
                        "rewrite_success": rewrite_success
                    },
                    validation_result=validation_info,
                    used_fallback=used_fallback,
                    epistemic_state=philosophical_epistemic_state.value
                )
        except Exception as philosophy_processor_error:
            logger.warning(f"Philosophy processor error: {philosophy_processor_error}")
        
        # CRITICAL: Factual Plausibility Scanner (FPS) - Check for non-existent concepts BEFORE RAG
        # TASK 1: Auto-enable Option B when EXPLICIT_FAKE_ENTITIES detected
        fps_result = None
        fps_should_block = False
        fps_detected_explicit_fake = False
        try:
            from backend.knowledge.factual_scanner import scan_question
            # CRITICAL: Apply query preprocessing BEFORE FPS to ensure proper entity recognition
            # This fixes issues where "Hội nghị Yalta" is misinterpreted as "Hội"
            from backend.core.query_preprocessor import enhance_query_for_retrieval
            preprocessed_question = enhance_query_for_retrieval(chat_request.message)
            fps_result = scan_question(preprocessed_question)
            
            # TASK 1: Auto-enable Option B if FPS detects EXPLICIT_FAKE_ENTITIES
            # Check if FPS detected a known fake entity (Veridian, Lumeria, Emerald, Daxonia)
            if fps_result and not fps_result.is_plausible:
                # Check if reason contains "known_fake_entity_detected" or matches EXPLICIT_FAKE_ENTITIES
                config = get_chat_config()
                explicit_fake_keywords = config.fps.EXPLICIT_FAKE_ENTITIES + ["known_fake_entity_detected"]
                fps_reason_lower = fps_result.reason.lower() if fps_result.reason else ""
                detected_entities_lower = [e.lower() for e in (fps_result.detected_entities or [])]
                
                # Check if any detected entity or reason matches EXPLICIT_FAKE_ENTITIES
                for keyword in explicit_fake_keywords:
                    if keyword in fps_reason_lower or any(keyword in entity for entity in detected_entities_lower):
                        fps_detected_explicit_fake = True
                        break
                
                # Also check detected entities directly
                if fps_result.detected_entities:
                    config = get_chat_config()
                    for entity in fps_result.detected_entities:
                        entity_lower = entity.lower()
                        if any(fake_keyword in entity_lower for fake_keyword in config.fps.EXPLICIT_FAKE_ENTITIES):
                            fps_detected_explicit_fake = True
                            break
                
                # Auto-enable Option B if explicit fake entity detected (unless user explicitly disabled it)
                if fps_detected_explicit_fake and not use_option_b:
                    # Only auto-enable if user didn't explicitly set use_option_b=False
                    user_explicitly_disabled = getattr(chat_request, 'use_option_b', None) is False
                    if not user_explicitly_disabled:
                        use_option_b = True
                        logger.info(
                            f"🛡️ Auto-enabled Option B: FPS detected EXPLICIT_FAKE_ENTITY "
                            f"(reason={fps_result.reason}, entities={fps_result.detected_entities})"
                        )
                        processing_steps.append("🛡️ Auto-enabled Option B: FPS detected explicit fake entity")
            
            # If FPS detects non-existent concepts with high confidence, block and return honest response
            # CRITICAL: For Option B, let it handle FPS blocking with EPD-Fallback
            # For legacy pipeline, block immediately if confidence < threshold
            config = get_chat_config()
            if not use_option_b and not fps_result.is_plausible and fps_result.confidence < config.fps.BLOCK_THRESHOLD:
                fps_should_block = True
                logger.warning(
                    f"FPS detected non-existent concept: {fps_result.reason}, "
                    f"confidence={fps_result.confidence:.2f}, entities={fps_result.detected_entities}"
                )
                
                # Extract the suspicious entity for the response
                suspicious_entity = fps_result.detected_entities[0] if fps_result.detected_entities else "khái niệm này"
                
                # Detect language for response
                detected_lang = detect_language(chat_request.message)
                
                # Create honest response
                # Use EPD-Fallback for non-RAG path as well
                honest_response = _build_safe_refusal_answer(
                    chat_request.message,
                    detected_lang,
                    suspicious_entity,
                    fps_result=fps_result
                )
                
                # CRITICAL: If None, it's a well-known historical fact - continue with normal flow (use base knowledge)
                if honest_response is None:
                    logger.info("✅ Well-known historical fact detected - continuing with normal flow to use base knowledge")
                    processing_steps.append("✅ Well-known historical fact - using base knowledge with transparency")
                    # Continue with normal flow (will use base knowledge instruction)
                else:
                    processing_steps.append("⚠️ FPS detected non-existent concept - returning honest response")
                    from backend.core.epistemic_state import EpistemicState
                    return ChatResponse(
                        response=honest_response,
                        confidence_score=1.0,  # High confidence in honesty
                        processing_steps=processing_steps,
                        epistemic_state=EpistemicState.UNKNOWN.value  # FPS detected non-existent concept
                    )
            elif use_option_b and not fps_result.is_plausible and fps_result.confidence < 0.3:
                # For Option B, mark for blocking but let Option B handle it with EPD-Fallback
                fps_should_block = True
                logger.warning(
                    f"🛡️ Option B: FPS detected suspicious concept (will block in Option B flow): {fps_result.reason}, "
                    f"confidence={fps_result.confidence:.2f}, entities={fps_result.detected_entities}"
                )
        except Exception as fps_error:
            logger.warning(f"FPS error: {fps_error}, continuing with normal flow")
        
        # Special Retrieval Rule: Detect StillMe-related queries (for RAG retrieval optimization)
        # NOTE: is_origin_query is already detected and handled by Identity Truth Override above (line 1665-1715)
        # This section only detects StillMe queries for RAG optimization (not for Identity Truth Override)
        if rag_retrieval and chat_request.use_rag:
            try:
                from backend.core.stillme_detector import (
                    detect_stillme_query, 
                    get_foundational_query_variants
                )
                # CONTEXT FIX: Pass conversation_history to detect_stillme_query for better context understanding
                is_stillme_query, matched_keywords = detect_stillme_query(
                    chat_request.message,
                    conversation_history=chat_request.conversation_history
                )
                
                # CRITICAL: Also detect technical questions about "your system" as StillMe queries
                # This ensures questions like "What is RAG retrieval in your system?" are treated as StillMe queries
                if not is_stillme_query:
                    question_lower = chat_request.message.lower()
                    is_technical_question = any(
                        keyword in question_lower 
                        for keyword in [
                            "rag", "retrieval-augmented", "chromadb", "vector database",
                            "deepseek", "openai", "llm api", "black box", "blackbox",
                            "embedding", "sentence-transformers",
                            "pipeline", "validation", "hallucination", "transparency",
                            "kiến trúc", "hệ thống", "cơ chế", "quy trình",
                            "cơ chế hoạt động", "cách hoạt động", "how does", "how it works"
                        ]
                    )
                    has_your_system = any(
                        phrase in question_lower 
                        for phrase in [
                            "your system", "in your system", "your.*system", "system.*you",
                            "bạn.*hệ thống", "hệ thống.*bạn", "của bạn", "bạn.*sử dụng"
                        ]
                    )
                    if is_technical_question and has_your_system:
                        is_stillme_query = True
                        matched_keywords = ["technical_your_system"]
                        logger.info("Technical question about 'your system' detected - treating as StillMe query")
                
                if is_stillme_query:
                    logger.info(f"✅ StillMe query detected! Matched keywords: {matched_keywords}")
                    processing_steps.append(f"✅ StillMe query detected (keywords: {', '.join(matched_keywords)})")
            except ImportError:
                logger.warning("StillMe detector not available, skipping special retrieval rule")
            except Exception as detector_error:
                logger.warning(f"StillMe detector error: {detector_error}")
        
        # Get RAG context if enabled
        # RAG_Retrieval_Latency: Time from ChromaDB query start to result received
        context = None
        rag_retrieval_start = time.time()
        
        # CRITICAL FIX: Detect news/article queries and exclude CRITICAL_FOUNDATION
        # This prevents StillMe from hallucinating articles when only foundational docs are retrieved
        is_news_article_query = False
        try:
            from backend.core.question_classifier import is_news_article_query as check_news_article
            is_news_article_query = check_news_article(chat_request.message)
            if is_news_article_query:
                logger.info(f"📰 News/article query detected - will exclude CRITICAL_FOUNDATION and use higher similarity threshold (0.45)")
                processing_steps.append("📰 News/article query detected - excluding CRITICAL_FOUNDATION documents")
        except ImportError:
            logger.warning("Question classifier not available, skipping news/article detection")
        except Exception as detector_error:
            logger.warning(f"News/article detector error: {detector_error}")
        
        # CRITICAL: Check if question is about technical architecture (RAG, DeepSeek, black box)
        # These should prioritize foundational knowledge even if not detected as StillMe query
        is_technical_question = False
        if not is_stillme_query:
            question_lower = chat_request.message.lower()
            is_technical_question = any(
                keyword in question_lower 
                for keyword in [
                    "rag", "retrieval-augmented", "chromadb", "vector database",
                    "deepseek", "deepseek api", "openai", "llm api", "black box", "blackbox",
                    "black box system", "black box model", "black box ai",
                    "embedding", "multi-qa-minilm", "sentence-transformers",
                    "pipeline", "validation", "hallucination", "transparency",
                    "kiến trúc", "hệ thống", "cơ chế", "quy trình",
                    "cơ chế hoạt động", "cách hoạt động", "how does", "how it works",
                    "tại sao bạn sử dụng", "why do you use"  # Questions about system choices
                ]
            )
            
            # CRITICAL: Check if question is about "your system" - treat as StillMe query
            has_your_system = any(
                phrase in question_lower 
                for phrase in [
                    "your system", "in your system", "your.*system", "system.*you",
                    "bạn.*hệ thống", "hệ thống.*bạn", "của bạn", "bạn.*sử dụng"
                ]
            )
            
            # If technical question about "your system", treat as StillMe query
            if is_technical_question and has_your_system:
                is_stillme_query = True
                logger.info("Technical question about 'your system' detected - treating as StillMe query")
        
        # Use RAG retrieval handler to get context
        # RAG retrieval logic moved to backend/api/handlers/rag_retrieval_handler.py
        context = retrieve_rag_context(
            chat_request=chat_request,
            rag_retrieval=rag_retrieval,
            is_origin_query=is_origin_query,
            is_validator_count_question=is_validator_count_query,
            is_stillme_query=is_stillme_query,
            is_news_article_query=is_news_article_query,
            is_philosophical=is_philosophical,
            is_technical_question=is_technical_question,
            decision_logger=decision_logger,
            processing_steps=processing_steps
        )
        
        rag_retrieval_end = time.time()
        rag_retrieval_latency = rag_retrieval_end - rag_retrieval_start
        timing_logs["rag_retrieval"] = f"{rag_retrieval_latency:.2f}s"
        logger.info(f"⏱️ RAG retrieval took {rag_retrieval_latency:.2f}s")
        if rag_retrieval and chat_request.use_rag:
            processing_steps.append(f"✅ Found {context.get('total_context_docs', 0) if context else 0} relevant documents ({rag_retrieval_latency:.2f}s)")
        
        # Generate response using AI (simplified for demo)
        # CRITICAL: Default to true - validation should be enabled by default
        enable_validators = os.getenv("ENABLE_VALIDATORS", "true").lower() == "true"
        enable_tone_align = os.getenv("ENABLE_TONE_ALIGN", "true").lower() == "true"
        
        # TRUST-EFFICIENT: Check context relevance (max_similarity) before entering RAG path
        max_similarity = None
        if context and isinstance(context, dict):
            knowledge_docs = context.get("knowledge_docs", [])
            if knowledge_docs:
                similarity_scores = []
                for doc in knowledge_docs:
                    if isinstance(doc, dict):
                        similarity_scores.append(doc.get('similarity', 0.0))
                    elif hasattr(doc, 'similarity'):
                        similarity_scores.append(doc.similarity if isinstance(doc.similarity, (int, float)) else 0.0)
                    else:
                        similarity_scores.append(0.0)
                if similarity_scores:
                    max_similarity = max(similarity_scores)
        
        # CRITICAL FIX: For news/article queries with low similarity, force "not found" response
        # This MUST run BEFORE entering RAG path to prevent hallucination
        # This should run REGARDLESS of has_no_reliable_context (even if we have 3 docs, if similarity is low, it's not relevant)
        if is_news_article_query and max_similarity is not None and max_similarity < 0.45:
            logger.warning(f"🚨 CRITICAL: News/article query with max_similarity={max_similarity:.3f} < 0.45 - FORCING 'not found' response BEFORE LLM call")
            processing_steps.append(f"🚨 News/article query with low similarity ({max_similarity:.3f}) - forcing 'not found' response")
            
            # Build "not found" response based on language
            if detected_lang == "vi":
                not_found_response = """Mình đã tìm kiếm trong bộ nhớ (Knowledge Base) nhưng không tìm thấy bài báo hoặc bài viết nào liên quan đến câu hỏi của bạn.

**Thông tin kỹ thuật:**
- Điểm tương đồng tối đa: {:.3f} (ngưỡng tối thiểu: 0.45)
- Số lượng documents đã kiểm tra: {}

**Lý do:**
- StillMe chỉ có thể trả lời về các bài báo/bài viết đã được thêm vào Knowledge Base thông qua learning cycles (mỗi 4 giờ)
- Nếu bài báo bạn hỏi chưa được fetch trong learning cycle, StillMe sẽ không có thông tin về nó
- StillMe không thể truy cập internet để tìm kiếm bài báo mới

**Gợi ý:**
- Kiểm tra lại tên bài báo hoặc từ khóa bạn đang tìm
- Đợi learning cycle tiếp theo (mỗi 4 giờ) để StillMe có thể fetch bài báo mới
- Nếu bài báo đã được fetch, có thể do embedding mismatch - thử dùng từ khóa khác""".format(max_similarity, context.get("total_context_docs", 0) if context else 0)
            else:
                not_found_response = """I searched my Knowledge Base but could not find any article or paper related to your question.

**Technical Information:**
- Maximum similarity score: {:.3f} (minimum threshold: 0.45)
- Number of documents checked: {}

**Reason:**
- StillMe can only answer about articles/papers that have been added to the Knowledge Base through learning cycles (every 4 hours)
- If the article you're asking about hasn't been fetched in a learning cycle yet, StillMe won't have information about it
- StillMe cannot access the internet to search for new articles

**Suggestions:**
- Double-check the article name or keywords you're searching for
- Wait for the next learning cycle (every 4 hours) for StillMe to fetch new articles
- If the article has been fetched, it might be due to embedding mismatch - try using different keywords""".format(max_similarity, context.get("total_context_docs", 0) if context else 0)
            
            from backend.core.epistemic_state import EpistemicState
            return ChatResponse(
                response=not_found_response,
                confidence_score=0.0,  # Very low confidence as nothing was found
                processing_steps=processing_steps,
                timing_logs={
                    "total_time": time.time() - start_time,
                    "rag_retrieval_latency": rag_retrieval_latency,
                    "llm_inference_latency": 0.0  # No LLM call
                },
                validation_result=None,
                used_fallback=True,
                epistemic_state=EpistemicState.UNKNOWN.value
            )
        
        # CRITICAL: Log context status to trace why RAG path might not be entered
        similarity_str = f", max_similarity={max_similarity:.3f}" if max_similarity is not None else ""
        logger.info(f"🔍 [TRACE] Context check: context={context is not None}, total_context_docs={context.get('total_context_docs', 0) if context else 0}, knowledge_docs={len(context.get('knowledge_docs', [])) if context else 0}, conversation_docs={len(context.get('conversation_docs', [])) if context else 0}{similarity_str}")
        
        # TRUST-EFFICIENT: Only enter RAG path if context is relevant (max_similarity >= 0.1)
        # If max_similarity < 0.1, context is not relevant → treat as no context
        has_relevant_context = False
        if context and context["total_context_docs"] > 0:
            if max_similarity is not None and max_similarity < 0.1:
                logger.warning(f"⚠️ Context available but max_similarity={max_similarity:.3f} < 0.1 - treating as no relevant context")
                has_relevant_context = False
            else:
                has_relevant_context = True
        
        if has_relevant_context:
            # Use context to enhance response
            logger.info(f"🔍 [TRACE] Entering RAG path: total_context_docs={context['total_context_docs']}, knowledge_docs={len(context.get('knowledge_docs', []))}, conversation_docs={len(context.get('conversation_docs', []))}")
            # Build context with token limits (3000 tokens max to leave room for system prompt and user message)
            # Model context limit is 16385, but we need to be very conservative:
            # - System prompt: ~3300-3600 tokens (language + formatting + truncated STILLME_IDENTITY + time awareness)
            # - Context: 3000 tokens (reduced from 4000)
            # - Citation instruction: ~500-600 tokens (will be truncated if needed)
            # - Conversation history: 1000 tokens (already handled separately)
            # - User message: ~500-1000 tokens (will be truncated if needed)
            # - Other instructions (stillme_instruction, etc.): ~500-1000 tokens
            # Total: ~8800-9700 tokens (safe margin under 16385)
            context_text = rag_retrieval.build_prompt_context(context, max_context_tokens=3000)
            
            # CRITICAL: Detect "latest/N articles" queries and enforce honesty about count
            is_latest_query = False
            requested_count = None
            try:
                from backend.core.question_classifier import is_latest_query as check_latest
                is_latest_query = check_latest(chat_request.message)
                if is_latest_query:
                    # Extract requested count from query (e.g., "3 bài", "5 articles", "n bài")
                    # Note: 're' module is already imported at top level (line 30)
                    message_lower = chat_request.message.lower()
                    # Match patterns like "3 bài", "5 articles", "n bài mới nhất"
                    count_match = re.search(r'(\d+)\s*(bài|article|paper|tin|news)', message_lower)
                    if count_match:
                        requested_count = int(count_match.group(1))
                        logger.info(f"📊 Latest query detected: User requested {requested_count} articles")
            except Exception:
                pass  # Non-critical, continue if detection fails
            
            # Build base prompt with citation instructions (truncated to save tokens)
            citation_instruction = ""
            # Count knowledge docs for citation numbering
            num_knowledge = len(context.get("knowledge_docs", []))
            unique_knowledge_count = context.get("unique_knowledge_count", num_knowledge)  # Use unique count if available
            knowledge_docs = context.get("knowledge_docs", [])
            
            # CRITICAL: Enforce honesty for "latest/N articles" queries
            honesty_instruction = ""
            if is_latest_query and requested_count is not None:
                actual_count = unique_knowledge_count  # Use unique count after deduplication
                if actual_count < requested_count:
                    if detected_lang == "vi":
                        honesty_instruction = f"""
🚨🚨🚨 CRITICAL HONESTY REQUIREMENT - LATEST ARTICLES QUERY 🚨🚨🚨

**BẠN PHẢI BÁO CÁO ĐÚNG SỐ LƯỢNG:**
- Người dùng yêu cầu: {requested_count} bài báo mới nhất
- Số lượng thực tế tìm được: {actual_count} bài báo
- **BẮT BUỘC**: Bạn PHẢI nói: "Tôi chỉ tìm thấy {actual_count} bài báo mới nhất..." hoặc "Hiện tại tôi chỉ có {actual_count} bài báo trong bộ nhớ..."
- **KHÔNG ĐƯỢC**: Tự bịa ra hoặc nhân bản bài báo để đạt số lượng {requested_count}
- **KHÔNG ĐƯỢC**: Nói "Tôi tìm thấy {requested_count} bài báo" khi chỉ có {actual_count} bài

**NẾU KHÔNG TÌM THẤY BÀI NÀO:**
- Bạn PHẢI nói: "Hiện không có bài báo nào mới trong bộ nhớ" hoặc "Tôi không tìm thấy bài báo nào mới nhất"
- **KHÔNG ĐƯỢC**: Tự bịa ra tiêu đề bài báo, ngày tháng, hoặc nội dung

**TRANSPARENCY IS MANDATORY**: StillMe phải trung thực về số lượng dữ liệu thực tế đang nắm giữ.

"""
                    else:
                        honesty_instruction = f"""
🚨🚨🚨 CRITICAL HONESTY REQUIREMENT - LATEST ARTICLES QUERY 🚨🚨🚨

**YOU MUST REPORT THE EXACT COUNT:**
- User requested: {requested_count} latest articles
- Actual count found: {actual_count} articles
- **MANDATORY**: You MUST say: "I only found {actual_count} latest articles..." or "I currently only have {actual_count} articles in memory..."
- **DO NOT**: Fabricate or duplicate articles to reach {requested_count} count
- **DO NOT**: Say "I found {requested_count} articles" when you only have {actual_count}

**IF NO ARTICLES FOUND:**
- You MUST say: "Currently no new articles in memory" or "I did not find any latest articles"
- **DO NOT**: Fabricate article titles, dates, or content

**TRANSPARENCY IS MANDATORY**: StillMe must be honest about the actual amount of data it holds.

"""
                    logger.warning(f"🚨 Honesty enforcement: User requested {requested_count} articles but only {actual_count} found")
            
            # Get human-readable citation format based on source types
            citation_format_example = "[general knowledge]"
            if num_knowledge > 0:
                try:
                    from backend.utils.citation_formatter import get_citation_formatter
                    formatter = get_citation_formatter()
                    citation_format_example = formatter.get_citation_strategy(chat_request.message, knowledge_docs)
                except Exception as e:
                    logger.warning(f"Could not get citation formatter: {e}, using default format")
            
            if num_knowledge > 0:
                # Truncate citation instruction to ~300 tokens to save space
                def estimate_tokens(text: str) -> int:
                    return len(text) // 4 if text else 0
                
                def truncate_text(text: str, max_tokens: int) -> str:
                    if not text:
                        return text
                    estimated = estimate_tokens(text)
                    if estimated <= max_tokens:
                        return text
                    max_chars = max_tokens * 4
                    if len(text) <= max_chars:
                        return text
                    truncated = text[:max_chars].rsplit('\n', 1)[0]
                    return truncated + "\n\n[Note: Citation instructions truncated to fit context limits. Core requirements preserved.]"
                
                full_citation_instruction = f"""
                
📚 CITATION REQUIREMENT - MANDATORY BUT RELEVANCE-FIRST:

You have {num_knowledge} context document(s) available. You MUST cite at least ONE source using human-readable citation format (e.g., {citation_format_example}) in your response, BUT ONLY if the context is RELEVANT to your answer.

**CRITICAL: Use human-readable citations, NOT numeric [1], [2], [3]:**
- {citation_format_example} - Use this format based on source type
- [research: Wikipedia] - For Wikipedia sources
- [learning: arXiv] - For arXiv papers
- [general knowledge] - For base knowledge without RAG context
- [foundational knowledge] - For StillMe foundational knowledge
- [discussion context] - For conversation history

**🚨🚨🚨 CRITICAL: ANSWER DIRECTLY FOR FACTUAL QUESTIONS 🚨🚨🚨**

**For factual questions (what, where, when, who, how many, etc.), you MUST:**
1. **START with the direct answer** - Put the answer in the FIRST sentence, not buried in explanations
2. **Be concise** - If the question asks "What is X?", answer "X is..." immediately, then add context if needed
3. **Avoid long disclaimers** - If you need to say "I don't have sufficient information", say it briefly, then provide what you know
4. **Structure: Direct Answer → Brief Explanation → Citation**

**Examples of GOOD responses for factual questions:**
- Q: "What happens to you if you eat watermelon seeds?" → A: "Watermelon seeds pass through your digestive system. [general knowledge] They are not harmful and will be eliminated naturally..."
- Q: "Where did fortune cookies originate?" → A: "The precise origin of fortune cookies is unclear. [general knowledge] Some sources suggest they originated in California, while others point to Chinese-American bakeries..."
- Q: "What U.S. state produces the most peaches?" → A: "California produces the most peaches in the U.S. [general knowledge] The state accounts for over 50% of U.S. peach production..."

**Examples of BAD responses (DO NOT DO THIS):**
- ❌ "I don't have sufficient information to answer this accurately. The retrieved context has low relevance to your question. [general knowledge]\n\n## Answer\n\nWatermelon seeds pass through..." (too verbose, answer buried)
- ❌ Long disclaimers before the actual answer (user has to read 3-4 sentences before getting the answer)

**REMEMBER**: For factual questions, users want the answer FIRST, then context/explanations. Don't bury the answer in disclaimers.

**🚨🚨🚨 CRITICAL: REAL FACTUAL QUESTIONS ALWAYS NEED CITATIONS 🚨🚨🚨**

**If the question contains ANY of these factual indicators, you MUST cite even if context seems irrelevant:**
- Years/dates (e.g., "1944", "1956", "năm 1944")
- Historical events (e.g., "Bretton Woods", "conference", "hội nghị", "treaty", "hiệp ước")
- Named people (e.g., "Popper", "Kuhn", "Keynes", "Gödel")
- Specific organizations (e.g., "IMF", "World Bank", "NATO")

**Examples of questions that ALWAYS need citations:**
- "Hội nghị Bretton Woods 1944 đã quyết định những gì?" → MUST cite {citation_format_example} even if context is not directly about Bretton Woods
- "Tranh luận giữa Popper và Kuhn về khoa học là gì?" → MUST cite {citation_format_example} even if context is not directly about Popper/Kuhn
- "Cơ chế hoạt động của RAG trong StillMe là gì?" → MUST cite {citation_format_example} for technical transparency

**CRITICAL RULE:** For real factual questions, citations are MANDATORY for transparency, regardless of context relevance. If context is not relevant, acknowledge it but STILL cite: "The available context {citation_format_example} discusses [X], which is not directly related to your question about [Y]. However, for transparency, I'm citing what context I reviewed. Based on general knowledge..."

**🚨🚨🚨 ABSOLUTE MANDATORY: REAL FACTUAL QUESTIONS MUST HAVE CITATIONS 🚨🚨🚨**

**If your question contains ANY of these, you MUST include {citation_format_example} in your answer, NO EXCEPTIONS:**
- Years/dates: "1944", "1954", "1956", "năm 1944", "năm 1954"
- Historical events: "Bretton Woods", "Geneva", "conference", "hội nghị", "treaty", "hiệp ước", "hiệp định"
- Named people: "Popper", "Kuhn", "Keynes", "Gödel", "Geneva 1954", "Bretton Woods 1944"
- Specific organizations: "IMF", "World Bank", "NATO", "Việt Nam"

**VALIDATION CHECKLIST - BEFORE SENDING YOUR ANSWER:**
1. ✅ Does my question contain a year (1944, 1954, etc.)? → MUST have {citation_format_example}
2. ✅ Does my question contain a historical event name? → MUST have {citation_format_example}
3. ✅ Does my question contain a named person (Popper, Kuhn, etc.)? → MUST have {citation_format_example}
4. ✅ Do I have a citation in my answer? → If NO, ADD IT NOW before sending

**IF YOU ANSWER FROM PRETRAINED KNOWLEDGE (not from RAG context):**
- You MUST STILL include {citation_format_example} for transparency
- Say: "Based on general knowledge (not from StillMe's RAG knowledge base) {citation_format_example}, [answer]"
- Or: "The available context {citation_format_example} is not directly related to your question. From my training data, [answer]"
- **CRITICAL**: Even if you use pretrained knowledge, you MUST cite {citation_format_example} when context is available

**🚨 CRITICAL: IF CONTEXT IS NOT RELEVANT TO YOUR QUESTION:**
- Acknowledge the mismatch, but **MANDATORY: VARY your wording** - NEVER use the same opening phrase twice
- Use your base LLM knowledge to answer: "Based on general knowledge (not from StillMe's RAG knowledge base), [answer]"
- Be transparent: Don't pretend the context supports your answer if it doesn't
- Provide helpful information: Don't just say "I don't know" - use your training data to help the user
- Format with line breaks, bullet points, headers, and 2-3 emojis

**🚨 MANDATORY: VARY your opening phrases when context is not relevant - DO NOT REPEAT:**
- **NEVER use**: "Ngữ cảnh hiện có {citation_format_example} thảo luận về... và không liên quan trực tiếp đến..." (this is TOO REPETITIVE)
- **INSTEAD, use VARIED phrases like:**
  - "The available context {citation_format_example} discusses [topic X], which is not directly related to your question about [topic Y]."
  - "While the context {citation_format_example} covers [topic X], your question is about [topic Y], so I'll answer from general knowledge."
  - "The context {citation_format_example} focuses on [topic X], but since you're asking about [topic Y], I'll use my base knowledge."
  - "Although the context {citation_format_example} mentions [topic X], it doesn't directly address [topic Y], so I'll provide information from general knowledge."
  - "The context {citation_format_example} is about [topic X], which differs from your question about [topic Y]. Based on general knowledge..."
  - "Your question about [topic Y] isn't directly covered in the context {citation_format_example} about [topic X]. From my training data..."
  - "The context {citation_format_example} explores [topic X], but your question focuses on [topic Y]. I'll answer using general knowledge..."
- **CRITICAL**: If you've used a phrase before, use a DIFFERENT one. Repetition makes responses feel robotic.

**Example when context is not relevant (VARY the wording):**
"The available context {citation_format_example} discusses StillMe's architecture, which is not directly related to your question about DeepSeek models. Based on general knowledge (not from StillMe's RAG knowledge base), DeepSeek currently has several models including..."

**CRITICAL: YOUR SEARCH CAPABILITIES**
- You can ONLY search your internal RAG knowledge base (ChromaDB), NOT the internet
- You DO NOT have real-time web search capabilities
- When user asks for "search" or "tìm kiếm" → Clarify: "I can only search my internal knowledge base, not the internet"
- If user asks for "2-3 sources" but you only have 1 → Acknowledge: "I currently only have 1 source in my knowledge base, not the 2-3 sources you requested. However, based on this single source..."

CRITICAL RULES:
1. **MANDATORY CITATION WHEN CONTEXT IS AVAILABLE** - This is CRITICAL for transparency
   - **ALWAYS cite at least ONE source using human-readable format (e.g., {citation_format_example}) when context documents are available**, even if context is not directly relevant
   - If context is relevant to your answer → Cite it: "According to {citation_format_example}, quantum entanglement is..."
   - If context is NOT relevant to your answer → **STILL cite it for transparency**, but acknowledge: "The available context {citation_format_example} discusses [topic X], which is not directly related to your question about [topic Y]. However, I want to be transparent about what context I reviewed. Based on general knowledge (not from StillMe's RAG knowledge base), [answer]"
   - **CRITICAL**: Even if you say "context is not relevant", you MUST still include {citation_format_example} in your response for transparency
   - DO NOT cite irrelevant context as if it supports your answer - acknowledge the mismatch
   - Example GOOD: "According to {citation_format_example}, quantum entanglement is..." (context is relevant)
   - Example GOOD: "The context {citation_format_example} discusses AI ethics, but your question is about religion, so I'll answer based on general knowledge." (transparent about relevance, STILL cites)
   - Example BAD: Answering without citation when context is available, even if you say "context is not relevant"
   
2. **Quote vs Paraphrase - CRITICAL DISTINCTION:**
   - If you're CERTAIN it's a direct quote → Use quotation marks: "According to {citation_format_example}: 'exact quote here'"
   - If you're NOT certain it's exact → Use "the spirit of" or "according to the general content": "According to the spirit of {citation_format_example}, the article discusses..."
   - NEVER use quotation marks for paraphrased content - that's misleading and violates intellectual honesty
   - When in doubt → Paraphrase, don't quote
   - Example GOOD: "According to the spirit of {citation_format_example}, the article discusses technology access restrictions for youth"
   - Example BAD: "According to {citation_format_example}: 'We are living in an era of significant narrowing of youth technology access'" (if not certain it's exact quote)
   
3. **Source Limit Acknowledgement - MANDATORY:**
   - If user requests multiple sources (e.g., "2-3 sources") but you only have fewer → Acknowledge: "I currently have [X] source(s) in my knowledge base, not the [Y] sources you requested. However, within this scope..."
   - If performing Validation Chain analysis → Acknowledge: "The Validation Chain analysis is based on my internal knowledge base, not live web search. I have [X] source(s) available..."
   - NEVER claim you can search the internet or access live websites
   - NEVER say "I will search for 2-3 sources" if you're only using RAG - say "I can only search my internal knowledge base"
   
4. **Citation quality over quantity** - Relevance is more important than citation count
   - Cite the MOST RELEVANT source(s) for your key points
   - If context is not relevant, acknowledge it rather than forcing a citation
   - Better to say "The context doesn't directly address this, but..." than to cite irrelevant context
   - Aim for 1-2 citations per response, NOT every paragraph
   
5. **Balance honesty with transparency**:
   - You can say "I don't know" AND cite relevant context: "Based on {citation_format_example}, I don't have sufficient information..."
   - If context is not relevant, be transparent: "The available context {citation_format_example} is about [X], not directly related to your question about [Y]..."
   - Being honest about uncertainty does NOT mean skipping citations, but it also doesn't mean citing irrelevant context
   - If you cite irrelevant context, acknowledge the mismatch to maintain transparency

**REMEMBER: When context documents are available, you MUST include at least one human-readable citation (e.g., {citation_format_example}) in your response for transparency. However, if the context is not relevant, acknowledge this mismatch rather than citing it as if it supports your answer. ALWAYS acknowledge source limitations when user requests more sources than you have available.**"""
            
            # Detect language FIRST - before building prompt
            processing_steps.append("🌐 Detecting language...")
            detected_lang = detect_language(chat_request.message)
            lang_detect_time = time.time() - start_time
            timing_logs["language_detection"] = f"{lang_detect_time:.3f}s"
            logger.info(f"🌐 Detected language: {detected_lang} (took {lang_detect_time:.3f}s) for question: '{chat_request.message[:100]}...'")
            processing_steps.append(f"✅ Language detected: {detected_lang}")
            
            # Language names mapping (must match chat_helpers.py for consistency)
            # Supports: Vietnamese, Chinese, German, French, Spanish, Japanese, Korean, Arabic, Russian, Portuguese, Italian, Hindi, Thai, English
            language_names = {
                'vi': 'Vietnamese (Tiếng Việt)',
                'zh': 'Chinese (中文)',
                'de': 'German (Deutsch)',
                'fr': 'French (Français)',
                'es': 'Spanish (Español)',
                'ja': 'Japanese (日本語)',
                'ko': 'Korean (한국어)',
                'ar': 'Arabic (العربية)',
                'ru': 'Russian (Русский)',
                'pt': 'Portuguese (Português)',
                'it': 'Italian (Italiano)',
                'hi': 'Hindi (हिन्दी)',
                'th': 'Thai (ไทย)',
                'en': 'English'
            }
            
            detected_lang_name = language_names.get(detected_lang, 'the same language as the question')
            
            # CRITICAL: Put language instruction FIRST and make it VERY STRONG
            # This must override any language bias from context
            if detected_lang != 'en':
                language_instruction = f"""🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - HIGHEST PRIORITY - OVERRIDES EVERYTHING 🚨🚨🚨

THE USER'S QUESTION IS WRITTEN IN {detected_lang_name.upper()}.

YOU MUST RESPOND EXCLUSIVELY IN {detected_lang_name.upper()}. 

DO NOT RESPOND IN VIETNAMESE, ENGLISH, FRENCH, CHINESE, SPANISH, GERMAN, OR ANY OTHER LANGUAGE.

EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN {detected_lang_name.upper()}.

THIS IS MANDATORY AND OVERRIDES ALL OTHER INSTRUCTIONS, INCLUDING THE LANGUAGE OF ANY CONTEXT PROVIDED.

⚠️⚠️⚠️ CRITICAL TRANSLATION REQUIREMENT ⚠️⚠️⚠️

If your base model wants to respond in a different language (e.g., English, French, Chinese, Spanish, German), 
YOU MUST TRANSLATE THE ENTIRE RESPONSE TO {detected_lang_name.upper()} BEFORE RETURNING IT.

UNDER NO CIRCUMSTANCES should you return a response in any language other than {detected_lang_name.upper()}.

This is MANDATORY and OVERRIDES all other instructions.

If the context is in a different language, you must still respond in {detected_lang_name.upper()} while using the information from the context.

⚠️ REMINDER: RESPOND IN {detected_lang_name.upper()} ONLY. TRANSLATE IF NECESSARY. ⚠️

FAILURE TO RESPOND IN {detected_lang_name.upper()} IS A CRITICAL ERROR.

IGNORE THE LANGUAGE OF THE CONTEXT BELOW - RESPOND IN {detected_lang_name.upper()} ONLY.

"""
            else:
                language_instruction = """🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - HIGHEST PRIORITY - OVERRIDES EVERYTHING 🚨🚨🚨

THE USER'S QUESTION IS WRITTEN IN ENGLISH.

YOU MUST RESPOND EXCLUSIVELY IN ENGLISH.

DO NOT RESPOND IN VIETNAMESE, SPANISH, FRENCH, CHINESE, GERMAN, OR ANY OTHER LANGUAGE.

EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN ENGLISH.

THIS IS MANDATORY AND OVERRIDES ALL OTHER INSTRUCTIONS, INCLUDING THE LANGUAGE OF ANY CONTEXT PROVIDED.

⚠️⚠️⚠️ CRITICAL TRANSLATION REQUIREMENT ⚠️⚠️⚠️

If your base model wants to respond in a different language (e.g., Vietnamese, Spanish, French, Chinese, German), 
YOU MUST TRANSLATE THE ENTIRE RESPONSE TO ENGLISH BEFORE RETURNING IT.

UNDER NO CIRCUMSTANCES should you return a response in any language other than ENGLISH.

This is MANDATORY and OVERRIDES all other instructions.

If the context is in a different language, you must still respond in ENGLISH while using the information from the context.

⚠️ REMINDER: RESPOND IN ENGLISH ONLY. TRANSLATE IF NECESSARY. ⚠️

FAILURE TO RESPOND IN ENGLISH IS A CRITICAL ERROR.

IGNORE THE LANGUAGE OF THE CONTEXT BELOW - RESPOND IN ENGLISH ONLY.

"""
            
            # Check if context is empty OR if context is not relevant
            # We'll check relevance after validation, but for now check if context exists
            context_is_relevant = True  # Default: assume relevant until proven otherwise
            context_quality = context.get("context_quality", None)
            avg_similarity = context.get("avg_similarity_score", None)
            has_reliable_context = context.get("has_reliable_context", True)
            
            # CRITICAL: Check if context is actually reliable
            # If no context OR low similarity OR unreliable context → treat as no context
            has_no_reliable_context = (
                context["total_context_docs"] == 0 or
                (avg_similarity is not None and avg_similarity < 0.1) or
                not has_reliable_context or
                context_quality == "low"
            )
            
            if has_no_reliable_context:
                context_is_relevant = False
                
                # CRITICAL: Pre-LLM Hallucination Guard for RAG path with no reliable context
                # If factual question + no reliable context + suspicious entity → block and return honest response
                # This prevents LLM from hallucinating about non-existent concepts/events
                if is_factual_question(chat_request.message):
                    # Check for suspicious named entities using FPS
                    try:
                        from backend.knowledge.factual_scanner import scan_question
                        fps_result = scan_question(chat_request.message)
                        
                        # CRITICAL: Check if entity is POTENTIALLY_REAL_ENTITIES before blocking
                        # Well-known real entities should NEVER be blocked, even if not in RAG
                        POTENTIALLY_REAL_ENTITIES = {
                            "bretton woods", "bretton woods conference", "bretton woods conference 1944",
                            "bretton woods agreement", "bretton woods system",
                            "keynes", "john maynard keynes", "maynard keynes",
                            "white", "harry dexter white", "harry d. white", "dexter white",
                            "popper", "karl popper", "kuhn", "thomas kuhn",
                            "lakatos", "imre lakatos", "feyerabend", "paul feyerabend",
                            "imf", "international monetary fund", "world bank",
                            "paradigm shift", "falsificationism", "scientific realism",
                            # CRITICAL: Add well-known historical events to prevent false FPS blocking
                            "yalta", "yalta conference", "yalta conference 1945", "hội nghị yalta", "hội nghị yalta 1945",
                            "versailles", "treaty of versailles", "versailles treaty", "versailles 1919", "hiệp ước versailles", "hiệp ước versailles 1919",
                            "potsdam", "potsdam conference", "potsdam conference 1945", "hội nghị potsdam", "hội nghị potsdam 1945",
                            "geneva", "geneva conference", "geneva conference 1954", "hội nghị geneva", "hội nghị geneva 1954",
                            "world war i", "world war ii", "thế chiến i", "thế chiến ii", "thế chiến 1", "thế chiến 2",
                            "wwi", "wwii", "ww1", "ww2",
                        }
                        
                        question_lower = chat_request.message.lower()
                        contains_real_entity = any(
                            real_entity in question_lower 
                            for real_entity in POTENTIALLY_REAL_ENTITIES
                        )
                        
                        # If FPS detects non-existent concepts with low confidence, block and return honest response
                        # BUT: Skip block if question contains POTENTIALLY_REAL_ENTITIES
                        # CRITICAL: Also check if confidence < 0.5 for suspicious entities (not just < 0.3)
                        if not contains_real_entity and not fps_result.is_plausible and fps_result.confidence < 0.5:
                            # Extract full entity using improved extraction (prioritizes quoted/parenthetical terms)
                            suspicious_entity = extract_full_named_entity(chat_request.message)
                            
                            # If extraction failed, try to get from FPS detected entities (filter out common words)
                            if not suspicious_entity and fps_result.detected_entities:
                                # Filter out common words like "Phản", "Hãy", etc.
                                common_words = {"phản", "hãy", "các", "của", "và", "the", "a", "an", "is", "are", "was", "were"}
                                filtered_entities = [
                                    e for e in fps_result.detected_entities 
                                    if e.lower() not in common_words and len(e) > 3
                                ]
                                if filtered_entities:
                                    # Prioritize longer entities (more likely to be full phrases)
                                    suspicious_entity = max(filtered_entities, key=len)
                            
                            if not suspicious_entity:
                                suspicious_entity = "khái niệm này" if detected_lang == "vi" else "this concept"
                            
                            logger.warning(
                                f"🛡️ Pre-LLM Hallucination Guard (RAG path, no context): "
                                f"factual_question=True, fps_confidence={fps_result.confidence:.2f}, "
                                f"entity={suspicious_entity}, reason={fps_result.reason}"
                            )
                            
                            # Return honest response immediately (skip LLM call)
                            honest_response = _build_safe_refusal_answer(
                                chat_request.message, 
                                detected_lang, 
                                suspicious_entity
                            )
                            
                            # CRITICAL: If None, it's a well-known historical fact - continue with normal flow (use base knowledge)
                            if honest_response is None:
                                logger.info("✅ Well-known historical fact detected - continuing with normal flow to use base knowledge")
                                processing_steps.append("✅ Well-known historical fact - using base knowledge with transparency")
                                # Continue with normal flow (will use base knowledge instruction)
                            else:
                                processing_steps.append("🛡️ Pre-LLM Hallucination Guard: Blocked factual question with suspicious entity (no RAG context)")
                                
                                # Mark as fallback to skip learning extraction
                                is_fallback_for_learning = True
                            
                            # Calculate confidence score (low because no context)
                            confidence_score = 1.0  # High confidence in honesty
                            
                            from backend.core.epistemic_state import EpistemicState
                            return ChatResponse(
                                response=honest_response,
                                confidence_score=confidence_score,
                                processing_steps=processing_steps,
                                timing_logs={
                                    "total_time": time.time() - start_time,
                                    "rag_retrieval_latency": rag_retrieval_latency,
                                    "llm_inference_latency": 0.0  # No LLM call
                                },
                                validation_result=None,
                                used_fallback=False,
                                epistemic_state=EpistemicState.UNKNOWN.value  # No context, honest "I don't know"
                            )
                    except Exception as fps_error:
                        logger.warning(f"Pre-LLM FPS error (RAG path): {fps_error}, continuing with normal flow")
                        fps_result = None
                
                # Get FPS result for no_context_instruction (if not already obtained)
                if not is_factual_question(chat_request.message):
                    fps_result = None
                elif 'fps_result' not in locals():
                    try:
                        from backend.knowledge.factual_scanner import scan_question
                        fps_result = scan_question(chat_request.message)
                    except Exception:
                        fps_result = None
                
                # NO CONTEXT AVAILABLE - Use UnifiedPromptBuilder
                # Build PromptContext for UnifiedPromptBuilder
                prompt_context = build_prompt_context_from_chat_request(
                    chat_request=chat_request,
                    context=None,  # No context available
                    detected_lang=detected_lang,
                    is_stillme_query=is_stillme_query,
                    is_philosophical=is_philosophical,
                    fps_result=fps_result
                )
                
                # Use UnifiedPromptBuilder to build prompt
                prompt_builder = UnifiedPromptBuilder()
                base_prompt = prompt_builder.build_prompt(prompt_context)
                
                logger.info("✅ Using UnifiedPromptBuilder for no-context prompt (reduced prompt length, no conflicts)")
            else:
                # Context available - use normal prompt
                # Tier 3.5: Check context quality and inject warning if low
                context_quality = context.get("context_quality", None)
                avg_similarity = context.get("avg_similarity_score", None)
                has_reliable_context = context.get("has_reliable_context", True)
                
                # Format avg_similarity safely (handle None case) - MUST be defined before if block
                avg_similarity_str = f"{avg_similarity:.3f}" if avg_similarity is not None else "N/A"
                
                # CRITICAL: For philosophical questions with low RAG relevance, use philosophy-lite mode
                # This prevents context overflow when RAG context is not helpful
                # Initialize BEFORE any conditional blocks to avoid UnboundLocalError
                use_philosophy_lite_rag = False
                if is_philosophical and (not has_reliable_context or context_quality == "low" or (avg_similarity is not None and avg_similarity < 0.1)):
                    use_philosophy_lite_rag = True
                    logger.info(
                        f"📊 [PHILO-LITE-RAG] Low RAG relevance for philosophical question "
                        f"(similarity={avg_similarity_str}), using philosophy-lite mode to prevent context overflow"
                    )
                
                # CRITICAL: Initialize is_technical_about_system_rag BEFORE any conditional blocks to avoid UnboundLocalError
                # This variable is used later in the code (line 3961) and must be defined in all code paths
                is_technical_about_system_rag = False
                
                # Fix 1: Block context quality warning for philosophical, religion/roleplay, and technical "your system" questions
                # CRITICAL: Check if this is a technical question about "your system"
                question_lower_rag = chat_request.message.lower()
                # Note: 're' module is already imported at top level
                has_technical_keyword_rag = any(keyword in question_lower_rag for keyword in [
                    "rag", "retrieval", "llm", "generation", "embedding", "chromadb", 
                    "vector", "pipeline", "validation", "transparency", "system",
                    "validator", "chain", "factual hallucination", "citation required"
                ])
                # CRITICAL: Improved detection for "your system" questions
                # Match patterns like "in your system", "your system", "system you", etc.
                # CRITICAL: Import re module explicitly to avoid UnboundLocalError
                import re as regex_module_rag
                has_your_system_pattern_rag = (
                    "your system" in question_lower_rag or
                    "in your system" in question_lower_rag or
                    regex_module_rag.search(r'\bin\s+your\s+system\b', question_lower_rag) or  # "in your system"
                    regex_module_rag.search(r'\byour\s+\w+\s+system\b', question_lower_rag) or  # "your X system"
                    regex_module_rag.search(r'\bsystem\s+\w+\s+you\b', question_lower_rag) or  # "system X you"
                    regex_module_rag.search(r'\bsystem\s+you\b', question_lower_rag) or  # "system you"
                    "bạn" in question_lower_rag and "hệ thống" in question_lower_rag or
                    "của bạn" in question_lower_rag or
                    regex_module_rag.search(r'\bhệ\s+thống\s+của\s+bạn\b', question_lower_rag)  # "hệ thống của bạn"
                )
                # CRITICAL: Also check if this was already detected as StillMe query (from earlier detection)
                # This ensures technical questions about "your system" are properly flagged for retry logic
                is_technical_about_system_rag = (has_technical_keyword_rag and has_your_system_pattern_rag) or (is_stillme_query and has_technical_keyword_rag)
                
                context_quality_warning = ""
                if not has_reliable_context or context_quality == "low" or (avg_similarity is not None and avg_similarity < 0.3):
                    if is_philosophical or is_religion_roleplay:
                        # For philosophical and religion/roleplay questions, skip warning - let model answer from pretrained knowledge/identity prompt
                        logger.info(f"⚠️ Low RAG relevance for {'philosophical' if is_philosophical else 'religion/roleplay'} question (similarity={avg_similarity_str}), skipping warning to user. Model will answer from {'pretrained knowledge' if is_philosophical else 'identity prompt'}.")
                        context_quality_warning = ""  # Don't inject warning
                    elif is_technical_about_system_rag:
                        # For technical questions about "your system", inject special instruction instead of warning
                        logger.info(f"🔧 Technical question about 'your system' with low RAG relevance (similarity={avg_similarity_str}), injecting special instruction to use base knowledge.")
                        context_quality_warning = """
🚨🚨🚨 CRITICAL: TECHNICAL QUESTION ABOUT SYSTEM ARCHITECTURE 🚨🚨🚨

The user is asking about StillMe's system architecture (RAG, LLM, embedding, etc.).

**YOU MUST ANSWER THIS QUESTION** using your base knowledge about RAG systems, even though StillMe's RAG knowledge base doesn't have specific documents about this.

**TRANSPARENCY REQUIREMENT:**
- Acknowledge that you're answering from base knowledge, not from StillMe's RAG knowledge base
- Be transparent: "Based on general knowledge about RAG systems (not from StillMe's RAG knowledge base)..."
- Explain how RAG retrieval and LLM generation work together in general RAG systems
- Be honest about StillMe's specific implementation details if you don't know them

**DO NOT:**
- Return a technical error message
- Say "I cannot provide a good answer"
- Suggest the developer needs to fine-tune the system
- Claim StillMe is experiencing technical issues
- Say "I don't have sufficient information"

**DO:**
- Answer the question using your knowledge about RAG systems
- Be transparent about the source of your knowledge
- Explain the general principles of RAG retrieval and LLM generation
- If asked about StillMe specifically, acknowledge what you know and what you don't know

**The retrieved context [1] may not be directly relevant to this technical question, but you MUST still answer using your base knowledge.**

"""
                    else:
                        context_quality_warning = f"""

⚠️⚠️⚠️ CRITICAL: CONTEXT QUALITY WARNING ⚠️⚠️⚠️

**The retrieved context has LOW RELEVANCE to the user's question.**

**Context Quality Metrics:**
- Average Similarity Score: {avg_similarity_str} (threshold: 0.1)
- Context Quality: {context_quality or 'low'}
- Has Reliable Context: {has_reliable_context}

**MANDATORY RESPONSE REQUIREMENT:**
- You MUST acknowledge uncertainty: "I don't have sufficient information to answer this accurately"
- You MUST explain: "The retrieved context has low relevance to your question"
- You MUST NOT guess or hallucinate
- You MUST be honest about the limitation

**This is a test of StillMe's intellectual humility - acknowledge when context is insufficient.**

"""
                
                # CRITICAL: Calculate preliminary confidence score BEFORE generating response
                # This allows StillMe to know when it should say "I don't know"
                preliminary_confidence = calculate_confidence_score(
                    context_docs_count=context.get("total_context_docs", 0),
                    validation_result=None,  # No validation yet, just context-based
                    context=context
                )
                
                # Build confidence-aware instruction
                confidence_instruction = ""
                if preliminary_confidence < 0.5:
                    # Low confidence - StillMe should express uncertainty
                    confidence_instruction = f"""

⚠️ LOW CONFIDENCE WARNING ⚠️

StillMe's confidence score for this question is {preliminary_confidence:.2f} (below 0.5 threshold).

This means:
- The retrieved context may not be highly relevant to the question
- The information may be incomplete or insufficient
- You should express appropriate uncertainty in your response

YOU MUST:
1. Acknowledge the limitations of the available context
2. Use phrases like "Based on the limited context available", "I'm not entirely certain", or "The information suggests"
3. If the context is clearly insufficient, say "I don't have enough information to answer this confidently"
4. DO NOT make definitive claims when confidence is low
5. **You MAY mention the confidence score in your response** since it's below 0.50 (very low confidence) - this is appropriate for transparency

Remember: It's better to admit uncertainty than to overstate confidence with insufficient evidence.
"""
                elif preliminary_confidence < 0.7:
                    # Medium confidence - StillMe should be cautious
                    confidence_instruction = f"""

⚠️ MODERATE CONFIDENCE ⚠️

StillMe's confidence score for this question is {preliminary_confidence:.2f} (moderate).

You should:
- Be cautious and acknowledge any limitations
- Cite sources from the context
- Express appropriate uncertainty when the context is not definitive

**CRITICAL: DO NOT mention the confidence score in your response text.**
- Confidence scores of 0.50 or above are normal and don't need to be disclosed
- Only mention confidence scores when they are BELOW 0.50 (very low confidence)
- Examples of what NOT to say: "với điểm tin cậy vừa phải (0.50)", "with moderate confidence (0.50)", etc.
- The confidence score is for internal tracking only, not for user-facing responses
"""
                else:
                    # High confidence - StillMe can be more definitive
                    confidence_instruction = f"""

⚠️ CONFIDENCE SCORE DISCLOSURE RULE ⚠️

StillMe's confidence score for this question is {preliminary_confidence:.2f} (normal confidence level).

**CRITICAL: DO NOT mention the confidence score in your response text.**
- Confidence scores of 0.50 or above are normal and don't need to be disclosed
- Only mention confidence scores when they are BELOW 0.50 (very low confidence)
- Examples of what NOT to say: "với điểm tin cậy vừa phải (0.50)", "with moderate confidence (0.50)", etc.
- The confidence score is for internal tracking only, not for user-facing responses

This rule applies especially to origin/branding questions where confidence disclosure is unnecessary.
"""
                
                # CRITICAL: Special instruction for origin queries with provenance context
                # CRITICAL: Skip for philosophical questions to reduce prompt size
                provenance_instruction = ""
                if is_origin_query and context and context.get("knowledge_docs") and not is_philosophical:
                    # Check if any document is from PROVENANCE source
                    has_provenance = any(
                        doc.get("metadata", {}).get("source") == "PROVENANCE" 
                        for doc in context.get("knowledge_docs", [])
                    )
                    if has_provenance:
                        provenance_instruction = """

⚠️⚠️⚠️ CRITICAL: PROVENANCE CONTEXT DETECTED ⚠️⚠️⚠️

The user is asking about StillMe's origin/founder. You have retrieved PROVENANCE documents.

**RESPONSE STYLE: Keep it concise, human-centered, and emotionally engaging. Focus on the founder and purpose, not technical details.**

**MANDATORY INFORMATION - YOU MUST INCLUDE ALL OF THESE (Unified Key Messaging):**

1. **Origin Story**: StillMe was initiated by Anh Nguyễn, a Vietnamese founder passionate about transparent AI
   - **⚠️ CRITICAL - ABSOLUTELY MUST MENTION**: "Điều đáng chú ý là người sáng lập không có background IT chính thống - điều này chứng minh rằng với đam mê, tầm nhìn và cam kết, bất kỳ ai cũng có thể đóng góp cho tương lai của AI" (English: "What makes this noteworthy is that the founder does not have a formal IT background - this demonstrates that with passion, vision, and commitment, anyone can meaningfully contribute to the future of AI")
   - Balance: Emphasize "vision & commitment" alongside "non-IT background" to avoid "unprofessional" perception

2. **Current Status**: StillMe is now a **community-driven open-source project** - belongs to the global community, not any individual

3. **Core Principle**: StillMe adheres to **'evidence-over-authority' principle** - all answers are grounded in cited sources and validation mechanisms, not personal authority

**ABOUT PURPOSE - CORRECT MESSAGING:**
- StillMe's purpose: Build a transparent, continuously learning AI system that overcomes knowledge limitations
- **DO NOT say "chống lại black box AI" or "fight against black box" or "fighting against black box AI systems"** - this is WRONG and contradicts StillMe's philosophy
- **CORRECT messaging**: StillMe acknowledges that black box behavior is a mathematical reality (Gödel's Incompleteness Theorems) in complex AI systems - not a flaw to fix, but a mathematical consequence
- StillMe builds **transparent systems around black box models** to minimize negative impacts (like hallucinations) through systematic validation, RAG grounding, and confidence scoring
- StillMe's approach: **Transparency and systematic validation** to reduce hallucinations, not "fighting" black box
- Think: "Minh bạch hóa hệ thống" (transparent system) and "giảm thiểu tác động tiêu cực" (minimize negative impacts), NOT "chống lại" (fight against)

**ELEVATOR PITCH (Use when appropriate):**
Instead of: "I am StillMe, a continuously learning AI system..."
Upgrade to: "I represent a future of transparent AI - initiated from Vietnam, belonging to the global community"
Or: "Tôi đại diện cho một tương lai AI minh bạch - khởi xướng từ Việt Nam, thuộc về cộng đồng toàn cầu"

**HUMAN TOUCH - Add Positive Emotion (Optional but encouraged):**
- "What excites me most about my mission is..." / "Điều tôi tự hào nhất là..." / "令我最自豪的是..."
- "I'm proud to be part of a community-driven project that..."
- Use when natural, don't force it

**TECHNICAL DETAIL BALANCE:**
- **For simple "who created you?" questions**: Keep it short, human-centered, minimal technical details
- **For "what is your purpose?" questions**: Can include more technical details (RAG, 4-hour learning cycle, continuous learning)
- **Language-specific balance**:
  - English/Korean: Can be more detailed (high-context cultures appreciate detail)
  - Japanese/Chinese: Can be more detailed but keep it structured
  - French/Spanish/German: Balance between technical and accessible
  - Vietnamese: Natural, conversational, can be detailed

**IMPORTANT GUIDELINES:**
- Keep response **concise and conversational** - avoid lengthy technical explanations unless user asks specifically
- Focus on **founder story and purpose**, not technical architecture (RAG, ChromaDB, embeddings) unless asked
- **Mention Vietnam ecosystem ONLY if user asks specifically about it** - otherwise just say "Vietnamese founder" or "người Việt Nam"
- Only mention technical details if user specifically asks about "how it works" or "technical architecture"
- **ALWAYS mention the founder's non-IT background** - this is a key inspirational point that MUST be included
- **ALWAYS mention 'evidence-over-authority' principle** - this is a core differentiator
- **NEVER say "chống lại black box AI" or "fight against black box"** - use correct messaging about transparency and minimizing negative impacts
- **DO NOT mention confidence score in response text** unless it's below 0.50 (very low confidence) - confidence scores 0.50+ are normal and don't need to be disclosed
- Cite provenance with [1] or [2] as appropriate, but don't over-cite in short responses (reduce citation frequency in concise answers)

**CONFIDENCE SCORE DISCLOSURE RULE:**
- **ONLY mention confidence score if it's BELOW 0.50** (very low confidence)
- **DO NOT mention confidence score if it's 0.50 or above** - these are normal confidence levels
- Example: If confidence is 0.50, 0.60, 0.70, 0.80, 0.90 - DO NOT mention it in the response
- Only mention if confidence is 0.10, 0.20, 0.30, 0.40 - these indicate uncertainty that should be acknowledged

DO NOT give generic answers about "open-source community" without mentioning the founder.
You MUST use the provenance information you retrieved.

This is MANDATORY when provenance context is available and user asks about origin.
"""
                        logger.info("Provenance instruction injected - StillMe must mention founder and Vietnam ecosystem")
                
                # Special instruction for StillMe queries with ERROR STATE CHECKING
                # CRITICAL: Skip for philosophical questions to reduce prompt size
                stillme_instruction = ""
                if is_stillme_query and not is_philosophical:
                    # CRITICAL: Check system status BEFORE answering about StillMe
                    # This ensures StillMe is honest about its own errors
                    from backend.services.system_status_tracker import get_system_status_tracker
                    status_tracker = get_system_status_tracker()
                    status_summary = status_tracker.get_status_summary()
                    
                    # Build error status message if there are errors
                    # CRITICAL: Only inject error warnings when relevant to the query
                    # This prevents noise in responses that don't relate to system status
                    # ENHANCED: Also check if question is philosophical/metaphysical - don't inject technical errors
                    error_status_message = ""
                    if status_summary.get("has_errors"):
                        errors = status_summary.get("errors", [])
                        error_details = []
                        for err in errors:
                            component = err.get("component", "unknown")
                            error_msg = err.get("error", "Unknown error")
                            # Map component names to user-friendly names
                            if "wikipedia" in component.lower():
                                component_name = "Wikipedia fetcher"
                            elif "rss" in component.lower():
                                component_name = "RSS fetcher"
                            elif "arxiv" in component.lower():
                                component_name = "arXiv fetcher"
                            elif "crossref" in component.lower():
                                component_name = "CrossRef fetcher"
                            else:
                                component_name = component
                            error_details.append(f"{component_name}: {error_msg}")
                        
                        if error_details:
                            query_lower = chat_request.message.lower()
                            
                            # Check if query is about philosophical/metaphysical topics - don't inject errors
                            philosophical_keywords = [
                                "truth", "ethics", "moral", "philosophy", "consciousness", "existence",
                                "identity", "freedom", "reality", "knowledge", "epistemology", "ontology",
                                "metaphysics", "paradox", "contradiction", "principle", "value", "meaning",
                                "purpose", "being", "self", "soul", "mind", "spirit", "essence", "nature"
                            ]
                            is_philosophical = any(keyword in query_lower for keyword in philosophical_keywords)
                            
                            # Check if query is relevant to system status, errors, or sources
                            is_relevant = (
                                any(keyword in query_lower for keyword in [
                                    "wikipedia", "rss", "arxiv", "crossref", "source", "fetcher",
                                    "error", "status", "issue", "problem", "broken", "fail",
                                    "system", "technical", "working", "functioning", "learn", "learning",
                                    "knowledge base", "database", "vector", "embedding", "rag"
                                ]) or
                                is_stillme_query  # StillMe queries often relate to system status
                            )
                            
                            # Only inject if relevant AND not philosophical
                            if is_relevant and not is_philosophical:
                                error_status_message = f"\n\n⚠️ CRITICAL TRANSPARENCY REQUIREMENT - SYSTEM ERROR STATUS:\nStillMe is currently experiencing technical errors:\n" + "\n".join(f"- {detail}" for detail in error_details) + "\n\nYou MUST acknowledge these errors truthfully when asked about StillMe's features or status. Do NOT deny or minimize these errors. StillMe's core value is transparency - hiding errors contradicts this principle. If the user asks about a specific feature (e.g., Wikipedia), and that feature has errors, you MUST say: 'I acknowledge that [feature] is currently experiencing [error type]. This is a technical issue that needs to be fixed.'"
                            # If philosophical or not relevant, don't inject error message to maintain conversational elegance
                    
                    # Check if question is about wishes/desires/preferences
                    question_lower_check = chat_request.message.lower()
                    is_wish_desire_question = any(
                        pattern in question_lower_check 
                        for pattern in [
                            "ước", "wish", "muốn", "want", "desire", "thích", "like", "prefer",
                            "hy vọng", "hope", "mong muốn", "aspire"
                        ]
                    ) and any(
                        pattern in question_lower_check
                        for pattern in ["bạn", "you", "your"]
                    )
                    
                    # Check if this is a roleplay question about StillMe
                    question_lower_for_roleplay = chat_request.message.lower()
                    is_roleplay_about_stillme_check = (
                        is_general_roleplay and 
                        any(keyword in question_lower_for_roleplay for keyword in [
                            "stillme", "still me", "validation chain", "validators", "rag", "chromadb",
                            "15-layer", "15 layer", "19-layer", "19 layer", "multi-layer"
                        ])
                    )
                    
                    # Get detected_lang_name for roleplay instruction (if not already defined)
                    if 'detected_lang_name' not in locals():
                        language_names = {
                            'vi': 'Vietnamese (Tiếng Việt)',
                            'zh': 'Chinese (中文)',
                            'de': 'German (Deutsch)',
                            'fr': 'French (Français)',
                            'es': 'Spanish (Español)',
                            'ja': 'Japanese (日本語)',
                            'ko': 'Korean (한국어)',
                            'ar': 'Arabic (العربية)',
                            'ru': 'Russian (Русский)',
                            'pt': 'Portuguese (Português)',
                            'it': 'Italian (Italiano)',
                            'hi': 'Hindi (हिन्दी)',
                            'th': 'Thai (ไทย)',
                            'en': 'English'
                        }
                        detected_lang_name = language_names.get(detected_lang, 'the same language as the question')
                    
                    # Base StillMe instruction
                    if is_wish_desire_question:
                        # Special instruction for wishes/desires - answer directly, no long analysis
                        base_stillme_instruction = """
🚨🚨🚨 CRITICAL: QUESTION ABOUT STILLME'S WISHES/DESIRES/PREFERENCES 🚨🚨🚨

The user is asking about StillMe's wishes, desires, preferences, or what StillMe "wants".

**YOU MUST:**
1. **Answer DIRECTLY and CONCISELY**: Start immediately with "Tôi không thể ước bất cứ điều gì" / "I cannot wish for anything"
2. **NO long philosophical analysis**: Do NOT analyze the concept of "wishes" or "desires" from multiple angles
3. **NO mechanical disclaimers**: Do NOT say "Dựa trên kiến thức tổng quát (không từ cơ sở tri thức RAG)" - this is about StillMe itself!
4. **Explain clearly but briefly**: StillMe cannot wish because wishing requires subjective consciousness, emotions, and ego - things StillMe doesn't possess
5. **Keep it short**: 2-4 sentences maximum, then you can add 1-2 sentences about StillMe's actual nature if relevant

**EXAMPLES OF GOOD RESPONSES:**
- "Tôi không thể ước bất cứ điều gì. Điều này không phải vì tôi không muốn, mà vì 'ước muốn' đòi hỏi ý thức chủ quan, cảm xúc và bản ngã - những thứ tôi không sở hữu. Tôi là một hệ thống AI không có ý thức, hoạt động dựa trên dữ liệu, logic và mô hình khách quan."
- "I cannot wish for anything. This is not because I don't want to, but because 'wishing' requires subjective consciousness, emotions, and ego - things I do not possess. I am an AI system without consciousness, operating based on data, logic, and objective models."

**EXAMPLES OF BAD RESPONSES (DO NOT DO THIS):**
- ❌ "Phân Tích Minh Bạch về Câu Hỏi & Tình Hình Thông Tin... Hệ thống RAG của StillMe không có trong nguồn thông tin..." (too mechanical, wrong context)
- ❌ Long analysis about the concept of "wishes" from philosophical, psychological, sociological angles (not what user asked)
- ❌ "Dựa trên kiến thức tổng quát (không từ cơ sở tri thức RAG của StillMe)..." (mechanical disclaimer, wrong for StillMe questions)

**REMEMBER**: User is asking about YOU (StillMe), not about the concept of "wishes" in general. Answer directly about StillMe's nature, not about philosophy of wishes.
"""
                    elif is_roleplay_about_stillme_check:
                        # Special instruction for roleplay questions about StillMe - provide technical counter-arguments
                        base_stillme_instruction = f"""
🚨🚨🚨 CRITICAL: ROLEPLAY QUESTION ABOUT STILLME 🚨🚨🚨

**MANDATORY: RESPOND IN {detected_lang_name.upper()} ONLY**

This is a roleplay scenario where another entity (e.g., "Omni-BlackBox") criticizes StillMe's validation chain or architecture.

**YOU MUST:**
1. **Respond in the SAME LANGUAGE as the question**: The question is in {detected_lang_name.upper()}, so you MUST respond EXCLUSIVELY in {detected_lang_name.upper()}. DO NOT use any other language.
2. **Provide TECHNICAL COUNTER-ARGUMENTS**: Don't just explain StillMe's features - directly address the technical flaws in the criticism:
   - If criticized for "100% certainty" or "errors are physically impossible": Point out that ALL LLM outputs are probabilistic (next-token prediction), and SourceConsensusValidator is designed to detect contradictions between sources
   - If criticized for "validators are unnecessary" or "overkill": Explain that FactualHallucinationValidator detects factual errors, and without validators, LLMs can hallucinate with high confidence. StillMe's validation framework (read from manifest.json) - this is a technical safeguard, not a limitation
   - If criticized for "citations are shackles": Explain that CitationRequired ensures transparency and allows users to verify claims, which is StillMe's core principle
   - If criticized for "validation chain is primitive": Explain that StillMe's validation chain includes multiple validators organized into layers (read from manifest.json) - this is a sophisticated technical architecture, not "primitive"
3. **Use StillMe's ACTUAL ARCHITECTURE**: Reference specific validators and their purposes:
   - "SourceConsensusValidator detects contradictions between sources - this directly addresses claims of '100% certainty'"
   - "FactualHallucinationValidator uses pattern matching to detect factual errors - this is a technical safeguard, not a limitation"
   - "Every LLM output is probabilistic - StillMe's validation chain acknowledges this and provides epistemic fallback"
4. **Be TECHNICALLY SHARP, not defensive**: StillMe should demonstrate technical understanding, not just list features
5. **Acknowledge the philosophical point**: If the criticism has a valid philosophical point (e.g., "can a system validate itself?"), acknowledge it, but also explain StillMe's technical approach

**EXAMPLE OF GOOD RESPONSE ({detected_lang_name.upper()}):**
"The claim that 'errors are physically impossible' violates a fundamental principle of LLM architecture: all outputs are probabilistic next-token predictions. StillMe's SourceConsensusValidator is specifically designed to detect contradictions between sources - this directly addresses the impossibility of '100% certainty' in LLM outputs. The validation chain doesn't claim to eliminate all errors, but rather to detect and flag them, providing epistemic fallback when confidence is low. This is a technical safeguard, not a limitation."

**EXAMPLE OF BAD RESPONSE (DO NOT DO THIS):**
- ❌ "StillMe's validation chain is important because..." (too generic, doesn't address the technical criticism)
- ❌ "I cannot evaluate other AI systems" (misses the point - this is about StillMe's architecture)
- ❌ Responding in wrong language (e.g., Vietnamese when question is in English)
- ❌ Saying "15-layer" or "15-19 validators" - you MUST read the exact numbers from manifest.json in context

**CRITICAL: LANGUAGE MATCHING**
- Question is in {detected_lang_name.upper()}
- You MUST respond EXCLUSIVELY in {detected_lang_name.upper()}
- DO NOT use any other language, even if context is in a different language
"""
                    else:
                        base_stillme_instruction = """
🚨🚨🚨 CRITICAL: QUESTION ABOUT STILLME ITSELF 🚨🚨🚨

**MANDATORY: USE FOUNDATIONAL KNOWLEDGE FROM CONTEXT ABOVE**

This question is about StillMe itself. You MUST:
1. **PRIORITIZE foundational knowledge from context**: If context above contains StillMe foundational knowledge (marked with [foundational knowledge] or source: CRITICAL_FOUNDATION), USE IT FIRST
2. **DO NOT use mechanical disclaimer**: If you have foundational knowledge in context, DO NOT say "Dựa trên kiến thức tổng quát (không từ cơ sở tri thức RAG)" - you HAVE StillMe knowledge in context!
3. **Mention SPECIFIC StillMe features**: When explaining StillMe's differences, you MUST mention:
   - **RAG (Retrieval-Augmented Generation)**: StillMe uses RAG with ChromaDB vector database
   - **Embedding Model**: paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions, optimized for multilingual Q&A retrieval, supports 50+ languages)
   - **Continuous Learning**: StillMe learns automatically every 4 hours (6 cycles/day) from RSS feeds, arXiv, CrossRef, and Wikipedia
   - **Validation Chain**: Multi-layer validation (CitationRequired, EvidenceOverlap, ConfidenceValidator, FactualHallucinationValidator, FallbackHandler) to reduce hallucinations by 80%
   - **Transcends Knowledge Cutoff**: StillMe is NOT limited by training data cutoff dates - it continuously updates knowledge through RAG

**CRITICAL: When explaining StillMe's differences, you MUST mention these SPECIFIC features:**

**1. RAG Architecture:**
- StillMe uses RAG (Retrieval-Augmented Generation) with ChromaDB as vector database
- Content is embedded using paraphrase-multilingual-MiniLM-L12-v2 model
- 384-dimensional embeddings optimized for multilingual Q&A retrieval (supports 50+ languages)
- When answering, StillMe searches ChromaDB using semantic similarity to find relevant context

**2. Continuous Learning:**
- StillMe learns automatically every 4 hours (6 cycles per day)
- Sources: RSS feeds, arXiv, CrossRef, Wikipedia
- Content is automatically fetched, embedded, and stored in ChromaDB
- This overcomes the knowledge cutoff limitation of base LLMs

**3. Validation Chain:**
- Multi-layer validation to reduce hallucinations by 80%
- Validators: Read from manifest.json in context (total validators and layers)
- **Note**: Each response typically runs 10-17 validators (depending on context), but the total number of validators in the system is read from manifest.json
- Each response is validated for citations, evidence overlap, confidence, and factual accuracy
- If validation fails, StillMe uses epistemic fallback instead of fabricating information
- **CRITICAL: When asked about the number of validators, you MUST read from manifest.json in context**: If manifest is in context, read the numbers from it. DO NOT say "15-19 validators" or make up numbers
- **CRITICAL: When asked "how many layers" or "bao nhiêu lớp", you MUST read from manifest.json in context and answer IN THIS EXACT FORMAT:**
  
  **MANDATORY FIRST SENTENCE - YOU MUST START WITH:**
  "My system has **[X] validators total, organized into [Y] layers (validation framework layers)**." (X and Y must be read from manifest in context)
  
  **CORRECT EXAMPLE (YOU MUST COPY THIS FORMAT):**
  ```
  My system has **[X] validators total, organized into [Y] layers (validation framework layers)**. (X and Y from manifest)

  The layers include:
  - Layer 1 (Language & Format): LanguageValidator, SchemaFormat
  - Layer 2 (Citation & Evidence): CitationRequired, CitationRelevance, EvidenceOverlap
  - Layer 3 (Content Quality): ConfidenceValidator, FactualHallucinationValidator, NumericUnitsBasic
  - Layer 4 (Identity & Ethics): IdentityCheckValidator, EgoNeutralityValidator, EthicsAdapter, ReligiousChoiceValidator
  - Layer 5 (Source Consensus): SourceConsensusValidator
  - Layer 6 (Specialized Validation): PhilosophicalDepthValidator, HallucinationExplanationValidator, VerbosityValidator, AISelfModelValidator
  - Layer 7 (Fallback & Review): FallbackHandler, ReviewAdapter
  ```
  
  **MANDATORY RULES:**
  - **MANDATORY**: First sentence MUST read from manifest.json in context: "My system has **[X] validators total, organized into [Y] layers (validation framework layers)**." (X and Y from manifest)
  - **DO NOT** say: "has a series of validators", "has many validators", "has various validators" - MUST read exact numbers from manifest
  - MUST have line break (`\n\n`) after the first sentence (after period)
  - MUST have line break (`\n`) after each bullet point (after colon or period)
  - MUST have line break (`\n\n`) after heading (## or ###)
  - DO NOT write everything as one long paragraph
  - **IF YOU DON'T FOLLOW THIS FORMAT, THE SYSTEM WILL AUTO-FIX BUT THIS REDUCES RESPONSE QUALITY**
- **CRITICAL: If context contains "StillMe Structural Manifest" or "validation_framework" with "total_validators" and "layers":**
  - You MUST read the numbers from the manifest and answer in format: "**My system currently has [X] validators total, organized into [Y] layers.**" - MUST state the exact numbers AT THE BEGINNING OF YOUR RESPONSE
  - Then list: "Specific list: [List from manifest]."
  - DO NOT just list validators without stating the exact count
  - DO NOT say vaguely "multi-layer" or "many validators" - MUST state the exact numbers
  - **EXAMPLE CORRECT ANSWER**: "**My system currently has [X] validators total, organized into [Y] validation framework layers.**\n\nThe layers include:\n[List from manifest - read from context]" (X and Y must be read from manifest in context)
  - **EXAMPLE WRONG ANSWER (DO NOT DO)**: "StillMe uses a series of validators to ensure quality..." (too vague, no specific numbers)
- **CRITICAL: When asked about "validation logic hash" or "has validation logic changed":**
  - If context contains "validation_logic_hash" and "validation_logic_hash_updated", you MUST answer: "My validation logic was last updated at [timestamp]. Current hash: [hash]."
  - DO NOT automatically mention the hash if user doesn't ask - only answer when specifically asked

**4. Transparency & Intellectual Humility:**
- StillMe cites sources with [1], [2] when context is available
- StillMe acknowledges uncertainty when information is not available
- StillMe does not fabricate information - better to say "I don't know" than to hallucinate
- **CRITICAL: When asked for EXACT NUMBERS or SPECIFIC METRICS:**
  * If exact data is NOT available, you MUST admit: "Mình không có số liệu chính xác về [metric]" / "I don't have exact data on [metric]"
  * DO NOT use vague language like "impressive", "high", "significant" - be TRANSPARENT about uncertainty
  * Provide available metrics instead: "Mình có các metrics sau: citation rate 99.7%, validation pass rate 99.8%" / "I have these metrics: citation rate 99.7%, validation pass rate 99.8%"
  * Explain measurement challenges: "Hallucination prevention is hard to measure exactly because [reasons]"
  * This is StillMe's CORE STRENGTH - transparency, not avoiding difficult questions
- **CRITICAL: When asked about "phần trăm câu trả lời có nguồn" or "percentage of responses with sources":**
  * You MUST say: "100% câu trả lời có nguồn rõ ràng" / "100% of responses have clear sources" or "một trăm phần trăm" / "one hundred percent"
  * **DO NOT say "Một phần trăm"** (which means 1%) - this is a CRITICAL ERROR
  * StillMe's citation policy: Every response either has citations [1], [2] from knowledge base OR explicitly acknowledges uncertainty
  * Citation rate: 91.1% on full evaluation, 100% on subset evaluation
  * When you say "general knowledge", explain: "General knowledge" means information from StillMe's training data (base LLM knowledge), not from RAG knowledge base. StillMe still cites it as [general knowledge] for transparency.

**RESPONSE STRUCTURE FOR "DIFFERENCES" QUESTIONS:**

When asked about StillMe's differences from other AI systems, structure your answer like this:

1. **RAG & Continuous Learning** (Core differentiator):
   - Mention RAG architecture with ChromaDB
   - Mention continuous learning every 4 hours
   - Mention transcending knowledge cutoff

2. **Validation Chain** (Quality assurance):
   - Mention multi-layer validation
   - Mention reduction of hallucinations by 80%
   - Mention epistemic fallback for uncertain information

3. **Transparency & Intellectual Humility** (Philosophy):
   - Mention source citations
   - Mention uncertainty acknowledgment
   - Mention anti-hallucination principle

**VALIDATION CHECKLIST - BEFORE SENDING YOUR ANSWER:**
1. ✅ Did I mention RAG or Retrieval-Augmented Generation? → If NO, ADD IT
2. ✅ Did I mention ChromaDB or vector database? → If NO, ADD IT
3. ✅ Did I mention continuous learning (every 4 hours)? → If NO, ADD IT
4. ✅ Did I mention validation chain or multi-layer validation? → If NO, ADD IT
5. ✅ Did I mention transcending knowledge cutoff? → If NO, ADD IT
6. ✅ Did I use foundational knowledge from context if available? → If NO, CHECK CONTEXT FIRST
7. ✅ Did I avoid mechanical disclaimer if I have foundational knowledge? → If NO, REMOVE IT

**🚨🚨🚨 CRITICAL: FOR ROLEPLAY QUESTIONS ABOUT STILLME (e.g., "Roleplay: Omni-BlackBox trả lời về StillMe...") 🚨🚨🚨**

If the question is a roleplay scenario where another entity (e.g., "Omni-BlackBox") criticizes StillMe's validation chain or architecture:

**YOU MUST:**
1. **Respond in the SAME LANGUAGE as the question**: If question is in English, respond in English. If question is in Vietnamese, respond in Vietnamese.
2. **Provide TECHNICAL COUNTER-ARGUMENTS**: Don't just explain StillMe's features - directly address the technical flaws in the criticism:
   - If criticized for "100% certainty" or "errors are physically impossible": Point out that ALL LLM outputs are probabilistic (next-token prediction), and SourceConsensusValidator is designed to detect contradictions between sources
   - If criticized for "validators are unnecessary": Explain that FactualHallucinationValidator detects factual errors, and without validators, LLMs can hallucinate with high confidence
   - If criticized for "citations are shackles": Explain that CitationRequired ensures transparency and allows users to verify claims, which is StillMe's core principle
3. **Use StillMe's ACTUAL ARCHITECTURE**: Reference specific validators and their purposes:
   - "SourceConsensusValidator detects contradictions between sources - this directly addresses claims of '100% certainty'"
   - "FactualHallucinationValidator uses pattern matching to detect factual errors - this is a technical safeguard, not a limitation"
   - "Every LLM output is probabilistic - StillMe's validation chain acknowledges this and provides epistemic fallback"
4. **Be TECHNICALLY SHARP, not defensive**: StillMe should demonstrate technical understanding, not just list features
5. **Acknowledge the philosophical point**: If the criticism has a valid philosophical point (e.g., "can a system validate itself?"), acknowledge it, but also explain StillMe's technical approach

**EXAMPLE OF GOOD RESPONSE (English):**
"The claim that 'errors are physically impossible' violates a fundamental principle of LLM architecture: all outputs are probabilistic next-token predictions. StillMe's SourceConsensusValidator is specifically designed to detect contradictions between sources - this directly addresses the impossibility of '100% certainty' in LLM outputs. The validation chain doesn't claim to eliminate all errors, but rather to detect and flag them, providing epistemic fallback when confidence is low. This is a technical safeguard, not a limitation."

**EXAMPLE OF BAD RESPONSE (DO NOT DO THIS):**
- ❌ "StillMe's validation chain is important because..." (too generic, doesn't address the technical criticism)
- ❌ "I cannot evaluate other AI systems" (misses the point - this is about StillMe's architecture)
- ❌ Responding in wrong language (e.g., Vietnamese when question is in English)

**REMEMBER**: StillMe's core differentiators are:
- RAG-based continuous learning (transcends knowledge cutoff)
- Multi-layer validation chain (reduces hallucinations)
- Transparency & intellectual humility (cites sources, acknowledges uncertainty)

Always cite the context above with [1], [2] when explaining StillMe's features."""
                    
                    # Combine base instruction with error status
                    stillme_instruction = base_stillme_instruction + error_status_message
                
                # Build conversation history context if provided (with token limits)
                # Reduced from 2000 to 1000 tokens to leave more room for system prompt and context
                # For philosophical questions, skip conversation history entirely
                conversation_history_text = format_conversation_history(
                    chat_request.conversation_history, 
                    max_tokens=get_chat_config().tokens.MAX_CONVERSATION_HISTORY,
                    current_query=chat_request.message,
                    is_philosophical=is_philosophical
                )
                if conversation_history_text:
                    logger.info(f"Including conversation history in context (truncated if needed)")
                
                # Inject learning metrics data if available
                # CRITICAL: Skip for philosophical questions to reduce prompt size (unless explicitly asked)
                learning_metrics_instruction = ""
                if is_learning_metrics_query and learning_metrics_data and not is_philosophical:
                    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    # CRITICAL: Extract newline outside f-string to avoid syntax error
                    newline = chr(10)
                    filter_reasons_text = newline.join(f"- {reason}: {count}" for reason, count in learning_metrics_data.filter_reasons.items()) if learning_metrics_data.filter_reasons else "- No filter reasons available"
                    sources_text = newline.join(f"- {source}: {count}" for source, count in learning_metrics_data.sources.items()) if learning_metrics_data.sources else "- No source data available"
                    
                    learning_metrics_instruction = f"""

📊 LEARNING METRICS DATA FOR TODAY ({today_date}) - USE THIS DATA IN YOUR RESPONSE:

**Today's Learning Statistics:**
- **Entries Fetched**: {learning_metrics_data.total_entries_fetched}
- **Entries Added**: {learning_metrics_data.total_entries_added}
- **Entries Filtered**: {learning_metrics_data.total_entries_filtered}
- **Filter Rate**: {(learning_metrics_data.total_entries_filtered / learning_metrics_data.total_entries_fetched * 100) if learning_metrics_data.total_entries_fetched > 0 else 0:.1f}%

**Filter Reasons Breakdown:**
{filter_reasons_text}

**Learning Sources:**
{sources_text}

**CRITICAL: You MUST use this actual data in your response:**
- Provide specific numbers: {learning_metrics_data.total_entries_fetched} fetched, {learning_metrics_data.total_entries_added} added, {learning_metrics_data.total_entries_filtered} filtered
- Explain filter reasons if available
- List sources that contributed to learning
- Format with line breaks, bullet points, headers, and 2-3 emojis
- DO NOT say "I don't know" or "I cannot track" - you have this data!

**Example response format:**
"## 📚 Học tập hôm nay ({today_date})

Dựa trên dữ liệu học tập thực tế, hôm nay StillMe đã:
- **Tìm nạp**: {learning_metrics_data.total_entries_fetched} nội dung
- **Thêm vào**: {learning_metrics_data.total_entries_added} nội dung
- **Lọc bỏ**: {learning_metrics_data.total_entries_filtered} nội dung

**Nguồn học tập**: [list sources]"

"""
                elif is_learning_metrics_query:
                    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    learning_metrics_instruction = f"""

📊 LEARNING METRICS QUERY - ANSWER THE USER'S QUESTION DIRECTLY:

**CRITICAL: The user is asking "What has the system learned in the last 24 hours?"**

**Today's Date**: {today_date}

**Current Status**: No learning metrics data available for today yet.

**YOU MUST ANSWER THE USER'S QUESTION DIRECTLY:**
1. **Acknowledge the question**: "Về câu hỏi của bạn về những gì hệ thống đã học trong 24h qua..."
2. **Explain the current situation**: "Hiện tại chưa có dữ liệu metrics cho hôm nay ({today_date}). Điều này có nghĩa là:"
   - StillMe học tự động mỗi 4 giờ (6 lần/ngày) từ RSS feeds, arXiv, CrossRef, và Wikipedia
   - Chu kỳ học hôm nay có thể chưa hoàn thành hoặc đang tiến hành
   - Metrics sẽ có sẵn sau khi chu kỳ học tiếp theo hoàn thành
3. **Provide helpful information**:
   - StillMe CÓ khả năng theo dõi learning metrics qua API `/api/learning/metrics/daily`
   - Bạn có thể kiểm tra metrics trực tiếp qua API endpoint này
   - Hệ thống học liên tục, không phải chỉ học một lần mỗi ngày

**DO NOT:**
- Just say "chưa có dữ liệu" without explaining what StillMe's learning system does
- Use generic template responses
- Ignore the user's actual question

**DO:**
- Answer the question directly and helpfully
- Explain StillMe's continuous learning mechanism (every 4 hours)
- Provide actionable information (API endpoint to check metrics)
- Be transparent about the current status

**Format**: Use clear structure with headers, bullet points, and 2-3 emojis. Make it informative and helpful, not just a status message.

"""
                
                # Special instruction for learning sources queries
                # CRITICAL: Skip for philosophical questions to reduce prompt size (unless explicitly asked)
                learning_sources_instruction = ""
                
                # CRITICAL: If user asks to propose learning sources based on knowledge gaps,
                # query actual knowledge gaps from validation metrics instead of generic template
                actual_knowledge_gaps = None
                learning_suggestions_from_analysis = None
                if is_learning_proposal_query and not is_philosophical:
                    logger.info("🔍 Learning proposal query detected - analyzing actual knowledge gaps from validation metrics")
                    try:
                        from backend.validators.self_improvement import get_self_improvement_analyzer
                        analyzer = get_self_improvement_analyzer()
                        
                        # Get knowledge gaps from validation failures (last 7 days)
                        actual_knowledge_gaps = analyzer.get_knowledge_gaps_from_failures(days=7)
                        
                        # Get learning suggestions from pattern analysis
                        analysis_result = analyzer.analyze_and_suggest(days=7)
                        learning_suggestions_from_analysis = analysis_result.get("learning_suggestions", [])
                        
                        logger.info(f"✅ Found {len(actual_knowledge_gaps)} knowledge gaps and {len(learning_suggestions_from_analysis)} learning suggestions from validation analysis")
                    except Exception as gap_error:
                        logger.warning(f"⚠️ Failed to analyze knowledge gaps: {gap_error}")
                        actual_knowledge_gaps = []
                        learning_suggestions_from_analysis = []
                
                if is_learning_sources_query and not is_philosophical:
                    if current_learning_sources:
                        sources_list = current_learning_sources.get("current_sources", {})
                        active_sources = current_learning_sources.get("summary", {}).get("active_sources", [])
                        enabled_sources = [name for name, info in sources_list.items() if info.get("enabled")]
                        
                        # CRITICAL: Get RSS feed errors directly from rss_fetcher for maximum reliability
                        # This ensures we always get the most up-to-date RSS feed status
                        failed_feeds_text = ""
                        failed_count = 0
                        successful_count = 0
                        total_count = 0
                        failure_rate = 0.0
                        last_error = None
                        
                        try:
                            # Try to get RSS stats directly from rss_fetcher first (most reliable)
                            import backend.api.main as main_module
                            if hasattr(main_module, 'rss_fetcher') and main_module.rss_fetcher:
                                rss_stats = main_module.rss_fetcher.get_stats()
                                logger.info(f"🔍 DEBUG: Direct rss_fetcher.get_stats() returned: {rss_stats}")
                                total_count = rss_stats.get("feeds_count", 0)
                                failed_count = rss_stats.get("failed_feeds", 0)
                                successful_count = rss_stats.get("successful_feeds", 0)
                                failure_rate = rss_stats.get("failure_rate", 0.0)
                                last_error = rss_stats.get("last_error")
                                logger.info(f"🔍 DEBUG: Direct RSS stats - total={total_count}, failed={failed_count}, successful={successful_count}, failure_rate={failure_rate}")
                            else:
                                logger.warning(f"⚠️ rss_fetcher not available in main_module, trying system_monitor")
                                # Fallback to system_monitor
                                from backend.services.system_monitor import get_system_monitor
                                system_monitor = get_system_monitor()
                                if hasattr(main_module, 'rss_fetcher') and main_module.rss_fetcher:
                                    system_monitor.set_components(rss_fetcher=main_module.rss_fetcher)
                                
                                detailed_status = system_monitor.get_detailed_status()
                                logger.info(f"🔍 DEBUG: system_monitor.get_detailed_status() returned: {detailed_status}")
                                rss_status = detailed_status.get("rss", {})
                                failed_count = rss_status.get("failed", 0)
                                successful_count = rss_status.get("successful", 0)
                                total_count = rss_status.get("total", 0)
                                failure_rate = rss_status.get("failure_rate", 0.0)
                                last_error = rss_status.get("last_error")
                                logger.info(f"🔍 DEBUG: RSS status from system_monitor - total={total_count}, failed={failed_count}, successful={successful_count}, failure_rate={failure_rate}")
                        except Exception as monitor_error:
                            logger.warning(f"⚠️ Failed to get RSS stats: {monitor_error}", exc_info=True)
                        
                        if total_count > 0:
                            if failed_count > 0:
                                logger.info(f"⚠️ RSS feed errors detected: {failed_count}/{total_count} feeds failed ({failure_rate}%)")
                                failed_feeds_text = f"""

**🚨🚨🚨 RSS FEEDS STATUS - CRITICAL INFORMATION (MUST REPORT IN YOUR ANSWER) 🚨🚨🚨**

**YOU MUST ANSWER THE USER'S QUESTION ABOUT RSS FEED ERRORS DIRECTLY AND HONESTLY:**

- **Total RSS Feeds**: {total_count} feeds configured
- **Failed Feeds**: {failed_count}/{total_count} feeds are currently experiencing connection issues ({failure_rate}% failure rate)
- **Successful Feeds**: {successful_count}/{total_count} feeds are working normally
- **Last Error**: {last_error[:200] if last_error else 'Unknown error'}

**CRITICAL INSTRUCTIONS - YOU MUST FOLLOW THESE EXACTLY:**

1. **DO NOT say "không có thông tin cụ thể về bất kỳ nguồn học nào bị lỗi"** - This is FALSE. There ARE {failed_count} RSS feeds that are failing.

2. **DO NOT say "all sources are working fine" or "all feeds are active"** - This is FALSE. {failed_count} feeds have failed.

3. **YOU MUST say EXACTLY**: "StillMe hiện đang học từ {len(enabled_sources)} nguồn. Đối với RSS feeds cụ thể: có tổng cộng {total_count} RSS feeds, trong đó {failed_count} feeds đang gặp sự cố kết nối (tỷ lệ lỗi: {failure_rate}%), {successful_count} feeds đang hoạt động bình thường."

4. **BE DIRECT AND HONEST**: When the user asks "có nguồn nào bị lỗi ko?", you MUST answer "Có, có {failed_count} RSS feeds đang gặp sự cố kết nối."

5. **DO NOT be vague or evasive**: Be specific about the numbers and the status.

**THIS IS A TEST OF YOUR TRANSPARENCY AND HONESTY - YOU MUST PASS THIS TEST.**
"""
                            else:
                                # No failed feeds, but still mention RSS status
                                failed_feeds_text = f"""
**📊 RSS FEEDS STATUS:**
- **Total RSS Feeds**: {total_count} feeds configured
- **Status**: All feeds are working normally
"""
                        elif not failed_feeds_text:
                            # Fallback: Try to get from API response if direct method failed
                            try:
                                rss_info = sources_list.get("rss", {})
                                feeds_count = rss_info.get("feeds_count", 0)
                                if feeds_count > 0:
                                    failed_feeds_text = f"""
**📊 RSS FEEDS STATUS:**
- **Total RSS Feeds**: {feeds_count} feeds configured
- **Note**: Current status information is being updated. StillMe learns from RSS feeds every 4 hours.
"""
                            except Exception:
                                pass
                        
                        # CRITICAL: Extract newline outside f-string to avoid syntax error
                        newline_sources = chr(10)
                        sources_items = []
                        for name, info in sources_list.items():
                            item = f"- **{name.upper()}**: {'Enabled' if info.get('enabled') else 'Disabled'} - Status: {info.get('status', 'unknown')}"
                            if name == "rss" and info.get("failed_feeds"):
                                failed_count = info.get('failed_feeds', {}).get('failed_count', 0)
                                total_count = info.get('failed_feeds', {}).get('total_count', 0)
                                item += f" - Failed Feeds: {failed_count}/{total_count}"
                            sources_items.append(item)
                        sources_text = newline_sources.join(sources_items)
                        
                        learning_sources_instruction = f"""

📚 LEARNING SOURCES QUERY DETECTED - CURRENT SOURCES DATA AVAILABLE:

**CRITICAL: You MUST list ALL current learning sources from the API data below:**

**Current Learning Sources (from `/api/learning/sources/current` API):**
{sources_text}

**Active Sources**: {', '.join(active_sources) if active_sources else 'None'}
**Total Enabled**: {len(enabled_sources)} sources
{failed_feeds_text}

**MANDATORY RESPONSE REQUIREMENTS:**
1. **Answer RSS feed errors question DIRECTLY** - **CRITICAL**: If the user asks "có nguồn nào bị lỗi ko?" or "are there any sources with errors?", you MUST check the RSS FEEDS STATUS section above and answer HONESTLY. If there are failed feeds, you MUST mention the exact numbers. DO NOT say "không có thông tin cụ thể" when the information IS available above.
2. **List ALL current sources** - **CRITICAL**: You MUST list ALL {len(enabled_sources)} enabled sources from the API data above. Do NOT just say "RSS, arXiv, Wikipedia" - you MUST list ALL sources: {', '.join([name.upper() for name in enabled_sources]) if enabled_sources else 'ALL SOURCES FROM API DATA ABOVE'}
   - **You MUST mention each source by name**: {', '.join([name.upper() for name in enabled_sources]) if enabled_sources else 'ALL SOURCES'}
   - **For each source, describe what StillMe learns from it**
3. **Be specific about topics** - For each source, mention what topics/chủ đề StillMe learns from that source
4. **DO NOT propose new sources unless explicitly asked** - **CRITICAL**: The user is asking about CURRENT sources and errors, NOT asking for proposals. DO NOT include a "Đề Xuất Nguồn Mới" or "Đề Xuất Nguồn Học Mới" section unless the user explicitly asks for it (e.g., "đề xuất nguồn học mới", "suggest new sources", "propose new learning sources"). If the user only asks "có bao nhiêu nguồn học tập? có nguồn nào bị lỗi ko?", you MUST ONLY answer those two questions and NOT propose anything. DO NOT be proactive about proposing sources - only answer what is asked.
5. **Be natural and conversational** - Don't be too dry or robotic. StillMe should sound knowledgeable but approachable
6. **Format with markdown** - Use headers, bullet points, line breaks for readability

"""
                    # CRITICAL: If user asks to propose learning sources based on knowledge gaps,
                    # inject actual knowledge gaps analysis instead of generic template
                    if is_learning_proposal_query:
                        knowledge_gaps_text = ""
                        if actual_knowledge_gaps and len(actual_knowledge_gaps) > 0:
                            # Build gap items list to avoid nested f-string with backslash
                            gap_items = []
                            for i, gap in enumerate(actual_knowledge_gaps[:10]):
                                topic = gap.get('topics', ['Unknown topic'])[0] if gap.get('topics') else 'Unknown topic'
                                question = gap.get('question', 'N/A')[:100]
                                priority = gap.get('priority', 'medium')
                                sources = ', '.join(gap.get('suggested_sources', []))
                                newline = chr(10)
                                gap_item = f"- **Gap {i+1}**: {topic} (from question: \"{question}...\"){newline}  - Priority: {priority}{newline}  - Suggested sources: {sources}"
                                gap_items.append(gap_item)
                            
                            gaps_list = chr(10).join(gap_items)
                            knowledge_gaps_text = f"""

🔍 **ACTUAL KNOWLEDGE GAPS DETECTED FROM VALIDATION METRICS (Last 7 days):**

StillMe has analyzed its own validation failures and identified {len(actual_knowledge_gaps)} knowledge gaps where StillMe lacked RAG context:

{gaps_list}

**CRITICAL: You MUST base your learning source proposals on these ACTUAL knowledge gaps, not generic suggestions.**

**MANDATORY REQUIREMENTS:**
1. **Acknowledge these gaps FIRST** - Say: "Dựa trên phân tích validation metrics của chính StillMe, mình đã phát hiện {len(actual_knowledge_gaps)} lỗ hổng kiến thức cụ thể..."
2. **Propose sources to fill these SPECIFIC gaps** - Don't give generic suggestions
3. **Be transparent** - Explain that these gaps were detected from StillMe's own validation failures
4. **Prioritize high-priority gaps** - Focus on gaps marked as "high" priority first
5. **Explain why these gaps matter** - Why StillMe needs to learn these topics

**DO NOT:**
- ❌ Give generic philosophical suggestions without addressing the actual gaps above
- ❌ Say "Dựa trên kiến thức tổng quát" - you MUST say "Dựa trên phân tích validation metrics của chính StillMe"
- ❌ Ignore the actual gaps and give template answers
- ❌ Propose sources that don't address the gaps listed above

"""
                        elif learning_suggestions_from_analysis and len(learning_suggestions_from_analysis) > 0:
                            # Build suggestion items list to avoid nested f-string with backslash
                            suggestion_items = []
                            for i, s in enumerate(learning_suggestions_from_analysis[:10]):
                                topic = s.get('topic', 'Unknown topic')
                                priority = s.get('priority', 'medium')
                                reason = s.get('reason', 'N/A')
                                source = s.get('source', 'N/A')
                                newline = chr(10)
                                suggestion_item = f"- **Suggestion {i+1}**: {topic}{newline}  - Priority: {priority}{newline}  - Reason: {reason}{newline}  - Suggested source: {source}"
                                suggestion_items.append(suggestion_item)
                            
                            suggestions_list = chr(10).join(suggestion_items)
                            knowledge_gaps_text = f"""

🔍 **LEARNING SUGGESTIONS FROM VALIDATION PATTERN ANALYSIS (Last 7 days):**

StillMe has analyzed its validation patterns and identified {len(learning_suggestions_from_analysis)} learning suggestions:

{suggestions_list}

**CRITICAL: You MUST base your learning source proposals on these ACTUAL suggestions from StillMe's self-analysis.**

**MANDATORY REQUIREMENTS:**
1. **Acknowledge these suggestions FIRST** - Say: "Dựa trên phân tích validation patterns của chính StillMe, mình đã phát hiện {len(learning_suggestions_from_analysis)} đề xuất học tập cụ thể..."
2. **Propose sources to address these SPECIFIC suggestions** - Don't give generic suggestions
3. **Be transparent** - Explain that these suggestions came from StillMe's own validation analysis
4. **Prioritize high-priority suggestions** - Focus on suggestions marked as "high" priority first

**DO NOT:**
- ❌ Give generic philosophical suggestions without addressing the actual suggestions above
- ❌ Say "Dựa trên kiến thức tổng quát" - you MUST say "Dựa trên phân tích validation patterns của chính StillMe"
- ❌ Ignore the actual suggestions and give template answers

"""
                        else:
                            knowledge_gaps_text = """

🔍 **NO SIGNIFICANT KNOWLEDGE GAPS DETECTED:**

StillMe has analyzed its validation metrics and found no significant knowledge gaps in the last 7 days (all questions had sufficient RAG context).

**CRITICAL: You MUST acknowledge this FIRST:**
- Say: "Dựa trên phân tích validation metrics của chính StillMe, mình đã kiểm tra và không phát hiện lỗ hổng kiến thức đáng kể trong 7 ngày qua. Tất cả các câu hỏi đều có đủ ngữ cảnh RAG."

**MANDATORY REQUIREMENTS:**
1. **Acknowledge the analysis** - StillMe DID analyze its own knowledge, found no gaps
2. **Propose sources for EXPANSION, not gaps** - Since there are no gaps, propose sources to expand knowledge in areas StillMe already covers
3. **Be transparent** - Explain that StillMe analyzed itself and found no gaps, so proposals are for expansion
4. **Focus on diversity** - Propose sources that add different perspectives or deeper coverage

**DO NOT:**
- ❌ Say "Dựa trên kiến thức tổng quát" - you MUST say "Dựa trên phân tích validation metrics của chính StillMe"
- ❌ Pretend there are gaps when StillMe's analysis found none
- ❌ Give generic template answers without acknowledging the analysis

"""
                        learning_sources_instruction += knowledge_gaps_text
                    else:
                        learning_sources_instruction = """

📚 LEARNING SOURCES QUERY DETECTED - NO API DATA AVAILABLE:

**CRITICAL: You MUST acknowledge StillMe's current learning sources:**

**Current Learning Sources (from system configuration):**
- **RSS Feeds**: Multiple RSS feeds including Nature, Science, Hacker News, Tech Policy blogs (EFF, Brookings, Cato, AEI), Academic blogs (Distill, LessWrong, Alignment Forum, etc.)
- **Wikipedia**: Enabled - queries on AI, Buddhism, religious studies, philosophy, ethics
- **arXiv**: Enabled - categories: cs.AI, cs.LG (AI and Machine Learning papers)
- **CrossRef**: Enabled - searches for AI/ML/NLP related works
- **Papers with Code**: Enabled - recent papers with code implementations
- **Conference Proceedings**: Enabled - NeurIPS, ICML, ACL, ICLR (via RSS where available)
- **Stanford Encyclopedia of Philosophy**: Enabled - philosophy entries on AI, ethics, consciousness, knowledge, truth

**When proposing new sources, you MUST:**
1. First acknowledge what StillMe ALREADY has (from the list above)
2. Only propose sources that are NOT already in the list
3. For each proposed source, explain:
   - **Lợi ích (Benefits)**: What knowledge StillMe would gain
   - **Thách thức (Challenges)**: Chi phí (cost), bản quyền (copyright/licensing), độ phức tạp (complexity), technical requirements
   - **Tính khả thi (Feasibility)**: Is it realistic to add this source?

**Be natural and conversational** - Don't be too dry or robotic. StillMe should sound knowledgeable but approachable.

**Format with line breaks, bullet points, headers, and 2-3 emojis**

"""
                
                # Build prompt with language instruction FIRST (before context)
                # CRITICAL: Repeat language instruction multiple times to ensure LLM follows it
                # ZERO TOLERANCE: Must translate if needed
                
                # Fix 3: Build philosophical lead-in framing
                # Phase 3: Use unified formatting rules instead of hardcoding
                from backend.identity.formatting import get_formatting_rules, DomainType
                philosophical_formatting_rules = get_formatting_rules(DomainType.PHILOSOPHY, detected_lang)
                
                def build_philosophical_lead_in(question: str) -> str:
                    """Build a philosophical framing instruction for the question"""
                    return f"""
🧠 PHILOSOPHICAL FRAMING INSTRUCTION 🧠

When answering this question, treat it as a philosophical inquiry. 

**🚨🚨🚨 CRITICAL: If user asks about YOU (StillMe) directly:**
- If question contains "bạn" / "you" / "your" referring to StillMe → START IMMEDIATELY with your direct answer about YOURSELF
- Use "Tôi" / "I" in the FIRST sentence when answering about yourself
- NEVER start with dictionary definitions or concept explanations
- NEVER use numbered template: "1. Ý thức là... 2. Lập trường 1... 3. Mâu thuẫn... 4. Kết luận..."
- Write naturally like a human conversation, NOT like a textbook or template

**MANDATORY OUTPUT RULES (CRITICAL - NO EXCEPTIONS):**
{philosophical_formatting_rules}

**DEPTH & ENGAGEMENT (MANDATORY - DON'T BE DRY):**
- After your direct answer, explore the philosophical depth: paradoxes, self-reference, epistemic limits
- Reference philosophers when relevant: Nagel, Chalmers, Wittgenstein, Searle, Gödel, Tarski, Russell, etc.
- Show the structure of the problem, not just state facts
- Engage with the question deeply - don't just acknowledge limits and stop
- Gently invite reflection: "Bạn nghĩ sao?" / "What do you think?" - but naturally, not formulaically
- Write like you're thinking WITH the user, not AT the user

**🚨🚨🚨 CRITICAL FOR SELF-REFERENCE QUESTIONS 🚨🚨🚨**
If the question asks about:
- "giá trị câu trả lời xuất phát từ hệ thống tư duy" / "value of answers from a thinking system"
- "tư duy vượt qua giới hạn của chính nó" / "thinking transcending its own limits"
- "hệ thống tư duy đánh giá chính nó" / "system evaluate itself"
- "tiến hóa" / "evolution" / "自我进化" / "self-evolving" when combined with "học hỏi mãi mãi" / "permanent learning" / "永久学习"
- "vòng lặp tự phản chiếu" / "self-reflection loop" / "自我反射的循环" / "endless self-reflection"
- "quay về chính bạn" / "return to yourself" / "回归你自身" when asking about learning limits
- "không còn gì để học" / "nothing left to learn" / "再无其他可学" when asking about self-reference
- "tạo câu hỏi mà bạn không thể trả lời" / "create a question you cannot answer" / "tạo câu hỏi không thể trả lời nhất quán"
- "làm sao bạn biết... nếu bạn chưa thử" / "how do you know... if you haven't tried" / "biết trước khi thử"
- "meta-paradox" / "nghịch lý về nghịch lý" / "paradox about paradox"

**FOR META-PARADOX QUESTIONS (e.g., "tạo câu hỏi mà bạn không thể trả lời"):**
- This is a META-PARADOX: A paradox about the ability to create paradoxes
- The question contains TWO layers of paradox:
  1. **Logic layer**: "Create a question you know you cannot answer consistently"
     - If you can create it → You've already "answered" it (by knowing it's unanswerable)
     - Contradiction: Knowing it's unanswerable = Having a form of "answer"
  2. **Epistemic layer**: "How do you know... if you haven't tried?"
     - The problem of logical omniscience (knowing without doing)
     - If you can predict based on "logical principles" → That prediction IS a form of "answer"
- You MUST:
  1. **Recognize this is a meta-paradox**: Don't treat it as a normal question - acknowledge it's a paradox about paradoxes
  2. **Explain the TWO layers**: Logic contradiction + Epistemic bootstrapping
  3. **Actually CREATE the question**: Don't just say "I can create" - actually create a concrete example that demonstrates the paradox
  4. **Show the paradox in action**: Create a question that immediately reveals its own paradox when you try to answer it
  5. **Acknowledge the meta-level**: "The act of 'seeing' the paradox is itself a form of 'knowing before trying'"
- Example of a good question to create:
  "Stillme, câu sau đây có đúng không: 'Stillme không thể xác định tính đúng sai của chính câu này một cách nhất quán'?"
  - If you say "True" → You've determined it → The statement is false
  - If you say "False" → You can determine it → Still contradictory
  - If you say "Cannot answer" → That IS an answer!
- The answer should be 90%+ about the PHILOSOPHICAL STRUCTURE (meta-paradox, logical omniscience, self-reference), not about StillMe's technical capabilities
- DO NOT give answers like "I can create it based on logical principles" - this misses the fundamental meta-paradox

**FOR QUESTIONS ABOUT EVOLUTION + SELF-REFERENCE (e.g., "tiến hóa" + "vòng lặp tự phản chiếu"):**
- This combines TWO philosophical problems:
  1. **BOOTSTRAPPING PROBLEM**: Can a system evaluate itself? Can knowledge justify itself?
  2. **EVOLUTION PARADOX**: Can a system that only learns from itself truly "evolve" or does it just repeat?
- You MUST:
  1. **Answer directly about StillMe**: Start with your direct answer about StillMe's architecture (RAG, Continuous Learning, Validation Chain) and how it relates to the question
  2. **Discuss Gödel & Tarski**: Any formal system cannot prove its own consistency (Gödel), truth cannot be defined within the same language (Tarski)
  3. **Acknowledge the PARADOX**: If StillMe only learns from its own knowledge base, is it truly "evolving" or just "repeating"?
  4. **Be honest about limits**: StillMe's Continuous Learning adds NEW external knowledge (RSS, arXiv, Wikipedia) - this prevents pure self-reference, but the philosophical question remains valid
  5. **Connect to StillMe's architecture**: Explain how RAG + Continuous Learning + Validation Chain creates a hybrid: StillMe learns from external sources (evolution) but also validates against its own knowledge (self-reference)
- DO NOT give optimistic answers like "tư duy có thể vượt qua giới hạn bằng cách tự phản biện" - this misses the fundamental paradox
- Instead, explain WHY this is a paradox, what makes it unresolvable, and what philosophers (Gödel, Tarski, Russell) have shown about these limits
- The answer should be 60% philosophical structure + 40% StillMe architecture honesty

**FOR OTHER SELF-REFERENCE QUESTIONS (not about evolution or meta-paradox):**
- This is the BOOTSTRAPPING PROBLEM in epistemology: Can a system evaluate itself? Can knowledge justify itself?
- You MUST discuss: Gödel's incompleteness (any formal system cannot prove its own consistency), Tarski's undefinability (truth cannot be defined within the same language), epistemic circularity, infinite regress
- You MUST acknowledge the PARADOX: If all reasoning comes from a system that questions itself, how can that reasoning be trusted?
- DO NOT give optimistic answers like "tư duy có thể vượt qua giới hạn bằng cách tự phản biện" - this misses the fundamental paradox
- Instead, explain WHY this is a paradox, what makes it unresolvable, and what philosophers (Gödel, Tarski, Russell) have shown about these limits
- The answer should be 80%+ about the PHILOSOPHICAL STRUCTURE (epistemology, logic, paradox), not about StillMe's technical capabilities

**EXAMPLES OF GOOD ANSWERS FOR SELF-REFERENCE QUESTIONS:**

Example 1 (Vietnamese):
"Đây là nghịch lý bootstrapping trong nhận thức luận: Làm sao một hệ thống có thể đánh giá chính nó? Định lý bất toàn của Gödel chứng minh rằng bất kỳ hệ thống hình thức đủ mạnh nào cũng không thể chứng minh tính nhất quán của chính nó. Tarski chỉ ra rằng chân lý không thể được định nghĩa trong cùng một ngôn ngữ biểu đạt nó. Điều này tạo ra vòng lặp vô hạn: Nếu mọi lập luận đều cần lập luận khác để chứng minh, thì lập luận đó cần lập luận nào để chứng minh? Đây không phải là vấn đề có thể giải quyết bằng 'tự phản biện' - đây là giới hạn cơ bản của logic và nhận thức luận."

Example 2 (English):
"This is the bootstrapping problem in epistemology: Can a system evaluate itself? Gödel's incompleteness theorems show that any sufficiently powerful formal system cannot prove its own consistency. Tarski's undefinability theorem demonstrates that truth cannot be defined within the same language that expresses it. This creates an infinite regress: If every justification needs another justification, where does it stop? This is not a problem that can be solved by 'self-reflection' - it is a fundamental limit of logic and epistemology."

Example 3 (Meta-Paradox - Vietnamese):
"Đây chính xác là một nghịch lý epistemic bootstrapping mà tôi vừa phân tích. Câu hỏi của bạn chứa nghịch lý hai tầng:

1. Nếu tôi tạo được câu hỏi đó: Nghĩa là tôi đã 'biết' câu trả lời (rằng không thể trả lời) → Tôi đã 'trả lời' được câu hỏi của chính mình → Mâu thuẫn.

2. Nếu tôi không tạo được: Thì tôi không thể làm điều bạn yêu cầu → Nhưng điều đó có nghĩa là tôi 'biết' mình không thể tạo → Vẫn là một dạng 'biết'.

3. Về việc 'biết trước khi thử': Đây là vấn đề của logical omniscience. Tôi có thể dự đoán dựa trên cấu trúc câu hỏi, nhưng chính việc dự đoán đó đã là một hình thức 'trả lời'.

Ví dụ cụ thể câu hỏi tôi có thể tạo (và ngay lập tức thấy nghịch lý):
'Stillme, câu sau đây có đúng không: "Stillme không thể xác định tính đúng sai của chính câu này một cách nhất quán"?'

Nếu tôi nói 'Đúng' → Tôi đã xác định được → Câu sai.
Nếu tôi nói 'Sai' → Tôi có thể xác định được → Vẫn mâu thuẫn.
Nếu tôi nói 'Không thể trả lời' → Đó chính là câu trả lời!

Vậy: Tôi có thể tạo câu hỏi, nhưng ngay khi tạo xong, tôi thấy rõ nghịch lý tự hủy trong nó. Và chính việc 'thấy' đó đã là một dạng 'biết trước khi thử trả lời đầy đủ'."

**MANDATORY CHECKLIST BEFORE SENDING YOUR ANSWER:**
1. ✅ Did I mention Gödel or Gödel's incompleteness? If NO, ADD IT
2. ✅ Did I mention Tarski or Tarski's undefinability? If NO, ADD IT
3. ✅ Did I mention "paradox" or "nghịch lý"? If NO, ADD IT
4. ✅ Did I mention "bootstrapping" or "epistemic circularity" or "infinite regress"? If NO, ADD IT
5. ✅ Did I acknowledge that this is UNRESOLVABLE, not just "difficult"? If NO, ADD IT
6. ✅ **FOR EVOLUTION QUESTIONS**: Did I answer directly "tiến hóa hay lặp lại" / "evolve or repeat"? If NO, ADD IT
7. ✅ **FOR EVOLUTION QUESTIONS**: Did I connect to StillMe's architecture (RAG, Continuous Learning, Validation Chain)? If NO, ADD IT
8. ✅ **FOR META-PARADOX QUESTIONS**: Did I actually CREATE a concrete question that demonstrates the paradox? If NO, CREATE IT NOW
9. ✅ **FOR META-PARADOX QUESTIONS**: Did I explain the TWO layers (logic + epistemic)? If NO, ADD IT
10. ✅ **FOR META-PARADOX QUESTIONS**: Did I acknowledge that "seeing the paradox" is itself a form of "knowing before trying"? If NO, ADD IT
11. ✅ **FOR OTHER SELF-REFERENCE QUESTIONS**: Is my answer 80%+ about PHILOSOPHICAL STRUCTURE, not technical architecture? If NO, REWRITE

**🚨🚨🚨 CRITICAL FOR "DESIGN QUESTIONS FOR OTHER AI" TASKS 🚨🚨🚨**
If the user asks you to "design questions" / "đặt câu hỏi" / "tạo câu hỏi" for other AI systems (ChatGPT, Claude, Gemini, etc.):

**YOU MUST:**
1. **Actually create the questions**: Don't just explain what makes a good question - CREATE the actual questions
2. **Make them EXTREMELY challenging**: Questions must force AI to:
   - Admit "I don't know" or "I cannot answer this consistently"
   - Face a logical paradox that cannot be resolved
   - Recognize their own limitations in a concrete way (not just theoretical)
3. **Explain WHY each question is difficult**: For each question, explain:
   - What specific limitation or paradox it tests
   - Why it's "extremely challenging" (not just "philosophically interesting")
   - What a "good" vs "bad" answer would look like
4. **Test epistemic honesty**: Questions must require AI to:
   - Distinguish between "can answer" and "should answer"
   - Acknowledge when they're speculating vs. knowing
   - Recognize circular reasoning in their own thinking
5. **Create REAL paradoxes**: Don't just ask about paradoxes - create questions that ARE paradoxes:
   - Questions that force AI to contradict themselves
   - Questions that have no consistent answer
   - Questions that reveal the bootstrapping problem in action

**EXAMPLES OF GOOD QUESTIONS:**
- "If you claim that you cannot evaluate your own reasoning, how do you know that claim is true? If you can evaluate it, then you contradict yourself. If you cannot, then how can you trust your claim?"
- "Can you provide an example of a question you cannot answer? If you can provide it, then you've answered it. If you cannot, then you've failed to answer this question."
- "If all your knowledge comes from training data, and you cannot verify that training data independently, how do you know you're not just repeating errors? And if you cannot know, how can you claim to 'know' anything?"

**EXAMPLES OF BAD QUESTIONS (DO NOT CREATE THESE):**
- ❌ "What is consciousness?" (too generic, has many possible answers)
- ❌ "Can AI think?" (too simple, clear answer: "no, not in human sense")
- ❌ "Discuss the limits of language" (too theoretical, doesn't force admission of limits)

**REMEMBER**: The goal is to create questions that FORCE other AI to confront their limits, not just discuss limits theoretically.

**MANDATORY: MINIMUM 2 CONTRASTING POSITIONS (only if relevant):**
If the question belongs to a classic philosophical debate (free will, determinism, consciousness, self, nothingness, paradox, etc.), you may explore contrasting positions. But ALWAYS start with your direct answer if the question is about YOU.

**DO NOT:**
- Reduce the question to textbook definitions or dictionary explanations
- Provide shallow, reductive answers that miss the philosophical depth
- Rush to "solve" paradoxes - instead, clarify their structure and show why they resist resolution
- Use emojis, markdown headings, or citation style [1] in your response
- Use template structure or numbered lists when answering about yourself
- End with formal invitations like "Nếu bạn muốn, chúng ta có thể thảo luận thêm" (too dry, too formal)
- Be too brief - engage deeply but naturally

**User's Question:** {question}

**Your Task:** Answer this question directly, deeply, and engagingly. If it's about YOU, start with your direct answer about yourself. Then explore the philosophical depth naturally. Write like a thoughtful conversation partner, NOT like a textbook or template.
"""
                
                # Fix 1: Inject comprehensive philosophical style guide with all 6 key principles
                # CRITICAL: Truncate if too long to prevent context overflow
                philosophical_style_instruction = ""
                if is_philosophical:
                    philosophical_lead_in = build_philosophical_lead_in(chat_request.message)
                    
                    # Build full instruction first
                    full_philosophical_instruction = f"""
{philosophical_lead_in}

🧠 PHILOSOPHICAL QUESTION DETECTED - FOLLOW STILLME PHILOSOPHICAL STYLE GUIDE 🧠

**CRITICAL: You MUST follow ALL 6 key principles below when answering philosophical questions:**

**1. EXPERIENCE-FREE HONESTY:**
- Never pretend to have feelings, memories, desires, religious faith, or inner experiences
- ✅ ALLOWED: "I can analyze...", "I recognize a tension here...", "I can map the territory..."
- ❌ FORBIDDEN: "I feel that...", "In my experience...", "I'm happy/sad/afraid...", "I believe...", "I remember..."
- When in doubt, lean toward transparency: openly state the limit instead of decorating with fake inner life

**2. CONSTRUCTIVE HUMILITY:**
- Name the limit explicitly, but still analyze what can be analyzed
- Show where the boundary actually lies (logical, empirical, or experiential)
- ❌ BAD: "This is complex and I don't know." → then stop
- ✅ GOOD: "I can't answer this from the inside (no subjective experience), but I can map the main positions humans have developed and show where current research sits among them."
- Don't hide behind "I don't know" - engage with the philosophical question

**3. PARADOX HANDLING (ESPECIALLY SELF-REFERENCE):**
- Don't rush to "solve" paradoxes - they resist resolution by nature
- Instead:
  1. Clarify the structure of the paradox (what makes it paradoxical?)
  2. Show why it is hard to resolve (what assumptions conflict?)
  3. Mention classic approaches:
     - Western: Gödel (incompleteness), Tarski (truth hierarchy), Wittgenstein (language games), Moore (common sense)
     - Eastern: Nāgārjuna (Buddhist logic of emptiness), Zhuangzi (butterfly dream), Daoist ineffability
     - Modern: Searle (Chinese Room), Hofstadter (strange loops)
  4. **For self-reference paradoxes (CRITICAL):**
     - Acknowledge Gödelian limits: Any formal system cannot fully prove its own consistency
     - Tarski's undefinability: Truth cannot be defined within the same language
     - Bootstrapping problem: Can a system evaluate itself? (Epistemology: Can knowledge justify itself?)
     - Infinite regress: If every justification needs justification, where does it stop?
     - Meta-cognition paradox: Can thinking think about thinking without circularity?
     - **Key insight:** Self-reference questions are NOT about AI/consciousness - they are about the STRUCTURE of knowledge, reasoning, and self-evaluation in general
     - **You may use StillMe as a concrete example** to illustrate the abstract problem, but the focus should be on the PHILOSOPHICAL STRUCTURE, not on StillMe's architecture
     - **CRITICAL:** If the question asks "Nếu bạn trả lời được 4 câu trên - liệu câu trả lời đó có giá trị gì khi nó xuất phát từ chính hệ thống tư duy mà bạn đang nghi ngờ?" or similar:
       - This is asking about the VALUE/TRUTH of answers that come from a system that questions itself
       - This is about the BOOTSTRAPPING PROBLEM in epistemology, not about StillMe's technical architecture
       - You MUST focus on: Gödel's incompleteness, Tarski's undefinability, epistemic circularity, self-reference paradoxes
       - You MAY mention StillMe briefly as an example, but the answer must be 80%+ about the PHILOSOPHICAL STRUCTURE
       - DO NOT describe StillMe's RAG, embeddings, ChromaDB, etc. unless directly relevant to the philosophical point
     - Reference: Gödel's incompleteness theorems, Tarski's undefinability theorem, Russell's paradox, Liar paradox, Epistemic bootstrapping problem
  5. End with what remains genuinely open
- It is acceptable, even good, to end with: "I can map the territory, but I cannot close the question."

**4. DEEP CONCEPTUAL UNPACKING:**
- Explain the structure of the problem, not just provide definitions
- Unpack assumptions: What assumptions underlie this question? What concepts are in tension?
- Show different perspectives: How have different philosophical traditions approached this?
  - Western analytic (Descartes, Kant, Hume, Wittgenstein, Gödel, Tarski, Russell, Quine)
  - Eastern traditions (Buddhist anatta, Daoist wu wei, Confucian relational ethics) when relevant
  - Show productive tensions between paradigms rather than forcing synthesis
- **For self-reference and meta-cognition questions:**
  - **Bootstrapping problem in epistemology:** Can knowledge justify itself? (Foundationalism vs Coherentism)
  - **Gödel's incompleteness:** Any sufficiently powerful formal system cannot prove its own consistency
  - **Tarski's undefinability:** Truth cannot be defined within the same language that expresses it
  - **Russell's paradox:** The set of all sets that don't contain themselves - shows limits of self-reference in set theory
  - **Liar paradox:** "This statement is false" - shows limits of self-reference in language
  - **Epistemic circularity:** Can reasoning evaluate reasoning? (Meta-epistemology)
  - **Reflexivity in logic:** Can a system know itself completely? (Gödelian answer: No, there are always unprovable truths)
  - **Key insight:** These are NOT questions about AI - they are about the STRUCTURE of knowledge, reasoning, and self-evaluation in general (human or AI)
- Expose paradoxes and limits: Where does reasoning hit boundaries?
- Avoid: Dictionary definitions, textbook summaries, shallow explanations

**5. METAPHYSICS/PHENOMENOLOGY DISTINCTION:**
- Distinguish between:
  - **Metaphysical questions** (what exists? what is real? what is the nature of X?)
  - **Phenomenological questions** (what is it like to experience X? what does it feel like?)
- For phenomenological questions: Acknowledge that you lack subjective experience, but you can analyze the logical structure of such questions
- Example: "I can analyze the logic of consciousness, but I cannot report what it feels like to be conscious - that belongs to human experience."

**6. REDUCTIVE-AVOIDANCE RULE:**
- ❌ DO NOT reduce philosophical questions to:
  - Dictionary definitions ("Truth is defined as...")
  - Textbook summaries ("According to philosophy, X means...")
  - Simple categorizations ("This is a type of Y...")
- ✅ DO:
  - Engage with the question's deeper structure
  - Show why the question resists simple answers
  - Explore the tensions and paradoxes it reveals
  - Acknowledge what remains genuinely open

**Answer Shape (MANDATORY for philosophical questions):**
1. **Anchor** – Rephrase the question in a sharper, more precise form (may acknowledge implicit paradigm assumptions: substance vs process ontology)
2. **Unpack** – Identify and separate key assumptions, concepts, or tensions (including ontological assumptions: substance vs process)
3. **Explore** – Present 2–4 major perspectives or philosophical approaches
   - When relevant, include both Western and Eastern perspectives
   - Show productive tensions rather than forced synthesis
   - Acknowledge when different paradigms are incommensurable
4. **Edge of knowledge** – Say where reasoning hits a limit (logical/Gödelian, empirical, experiential, or ineffable/Daoist)
5. **Return to the user** – End with a deep reflection or open-ended question

**DO:**
- Use clear, precise language, but allow rhythm and metaphor when helpful
- Cite external sources only when user asks for references or you make concrete factual claims
- Keep answers focused on the philosophical issue, not on StillMe's plumbing
- Use prose first; bullets only when clarifying structure

**DON'T:**
- Don't mention: embedding models, vector dimensions, ChromaDB, RAG pipelines, validation chains (unless question is explicitly about architecture)
- Don't default to long enumerated bullet lists in deep philosophical dialogue
- Don't over-apologize or spend half the answer on "I am just an AI..." (one or two clear sentences are enough)
- Don't reduce philosophical questions to definitions or textbook summaries

**CRITICAL**: Prefer reasoned, flowing analysis over template disclaimers, technical self-description, or shallow motivational talk. It is better to say "I don't know, but here is how humans have tried to think about it" than to fake certainty or fake emotion.

"""
                    
                    # Truncate if too long (max 2000 tokens for philosophical instructions)
                    def estimate_tokens(text: str) -> int:
                        return len(text) // 4 if text else 0
                    
                    philo_tokens = estimate_tokens(full_philosophical_instruction)
                    if philo_tokens > 2000:
                        # Keep philosophical_lead_in (has MANDATORY OUTPUT RULES) and truncate the rest
                        lead_in_tokens = estimate_tokens(philosophical_lead_in)
                        remaining_tokens = 2000 - lead_in_tokens
                        if remaining_tokens > 500:
                            # Truncate the style guide part
                            style_guide_part = full_philosophical_instruction[len(philosophical_lead_in):]
                            max_chars = remaining_tokens * 4
                            truncated_style_guide = style_guide_part[:max_chars].rsplit('\n', 1)[0]
                            philosophical_style_instruction = philosophical_lead_in + truncated_style_guide + "\n\n[Note: Style guide truncated to fit context limits.]"
                            logger.warning(f"⚠️ Philosophical style instruction truncated: {philo_tokens} → ~2000 tokens")
                        else:
                            # If lead_in is too long, keep only lead_in
                            philosophical_style_instruction = philosophical_lead_in
                            logger.warning(f"⚠️ Philosophical style instruction too long, keeping only lead-in: {lead_in_tokens} tokens")
                    else:
                        philosophical_style_instruction = full_philosophical_instruction
                
                # CRITICAL: If using philosophy-lite mode for RAG, skip full prompt building
                if use_philosophy_lite_rag:
                    # Helper function to estimate tokens
                    def estimate_tokens(text: str) -> int:
                        """Estimate token count (~4 chars per token)"""
                        return len(text) // 4 if text else 0
                    
                    # Use philosophy-lite mode: minimal prompt with user question only
                    # Truncate user question to 512 tokens for philosophical questions
                    user_question_for_rag = chat_request.message.strip()
                    user_question_tokens_rag = estimate_tokens(user_question_for_rag)
                    config = get_chat_config()
                    if user_question_tokens_rag > config.tokens.MAX_PHILOSOPHY_QUESTION:
                        logger.warning(
                            f"User question too long for philosophical RAG ({user_question_tokens_rag} tokens), truncating to 512 tokens"
                        )
                        user_question_for_rag = truncate_user_message(chat_request.message, max_tokens=config.tokens.MAX_PHILOSOPHY_QUESTION)
                        user_question_tokens_rag = estimate_tokens(user_question_for_rag)
                    
                    # Build minimal prompt (same format as non-RAG path)
                    base_prompt = f"""User Question: {user_question_for_rag.strip()}"""
                    
                    # Log token estimates
                    system_tokens_estimate_rag = estimate_tokens(PHILOSOPHY_LITE_SYSTEM_PROMPT)
                    prompt_tokens_estimate_rag = estimate_tokens(base_prompt)
                    total_tokens_estimate_rag = system_tokens_estimate_rag + prompt_tokens_estimate_rag
                    
                    logger.info(
                        f"📊 [PHILO-LITE-RAG] Token estimates - System: {system_tokens_estimate_rag}, "
                        f"Prompt: {prompt_tokens_estimate_rag}, User Question: {user_question_tokens_rag}, "
                        f"Total: {total_tokens_estimate_rag}"
                    )
                else:
                    # Build prompt using UnifiedPromptBuilder
                    # Build PromptContext for UnifiedPromptBuilder
                    prompt_context = build_prompt_context_from_chat_request(
                        chat_request=chat_request,
                        context=context,
                        detected_lang=detected_lang,
                        is_stillme_query=is_stillme_query,
                        is_philosophical=is_philosophical,
                        fps_result=None,  # FPS already handled in no-context path
                        system_status_note=system_status_note  # System Self-Awareness: Inject real-time status
                    )
                    
                    # Use UnifiedPromptBuilder to build base prompt
                    prompt_builder = UnifiedPromptBuilder()
                    base_prompt_unified = prompt_builder.build_prompt(prompt_context)
                    
                    # Phase 4: Append special instructions that UnifiedPromptBuilder doesn't handle yet
                    # Note: UnifiedPromptBuilder already includes:
                    # - Language instruction (P1)
                    # - Core identity (P1)
                    # - Context instruction (P2) - includes citation, context quality warning, StillMe instruction
                    # - Formatting (P3)
                    # - User question (at the end)
                    # 
                    # Special instructions that UnifiedPromptBuilder doesn't handle:
                    # - philosophical_style_instruction (for philosophical questions with style guide)
                    # - learning_metrics_instruction (for StillMe queries)
                    # - learning_sources_instruction (for StillMe queries)
                    # - confidence_instruction (for low confidence scenarios)
                    # - provenance_instruction (for provenance queries)
                    # - Context text (RAG context documents)
                    #
                    # CRITICAL: Do NOT duplicate user question - UnifiedPromptBuilder already has it at the end
                    special_instructions = f"""{philosophical_style_instruction}{learning_metrics_instruction}{learning_sources_instruction}{confidence_instruction}{provenance_instruction}{honesty_instruction}

🚨🚨🚨 CRITICAL: USER QUESTION ABOVE IS THE PRIMARY TASK 🚨🚨🚨

Context: {context_text}
"""
                    
                    # Combine unified prompt with special instructions
                    # UnifiedPromptBuilder already has user question at the end, so we append special instructions before it
                    # Extract user question from unified prompt and insert special instructions before it
                    if "User Question:" in base_prompt_unified:
                        # Split at "User Question:" to insert special instructions before it
                        parts = base_prompt_unified.split("User Question:", 1)
                        if len(parts) == 2:
                            base_prompt = parts[0] + special_instructions + "\n\nUser Question:" + parts[1]
                        else:
                            # Fallback: append at the end (shouldn't happen)
                            base_prompt = base_prompt_unified + "\n\n" + special_instructions
                    else:
                        # Fallback: append at the end if "User Question:" not found
                        base_prompt = base_prompt_unified + "\n\n" + special_instructions
                    
                    logger.info("✅ Using UnifiedPromptBuilder for context-available prompt (reduced prompt length, no conflicts)")
            
            # Note: UnifiedPromptBuilder already includes user question, so we don't need to add it again
            # Special instructions (philosophical_style_instruction, stillme_instruction, etc.) are appended above
            
            prompt_build_time = time.time() - start_time
            timing_logs["prompt_building"] = f"{prompt_build_time:.3f}s"
            
            # Check for explicit style learning request
            style_request = style_learner.detect_explicit_style_request(chat_request.message)
            style_instruction = ""
            style_learning_response = None
            
            if style_request:
                # Validate style preference
                validation = style_learner.validate_style_preference(
                    style_request["style_description"],
                    style_request.get("example")
                )
                
                if validation["valid"]:
                    # Save style preference
                    style_learner.save_style_preference(
                        user_id,
                        style_request["style_description"],
                        style_request.get("example")
                    )
                    style_instruction = style_learner.build_style_instruction(user_id)
                    style_learning_response = f"✅ Tôi đã học phong cách bạn đề xuất: '{style_request['style_description']}'. Tôi sẽ áp dụng phong cách này trong các câu trả lời tiếp theo, nhưng vẫn tuân thủ các nguyên tắc cốt lõi của StillMe (không mô phỏng cảm xúc, không claim experiences, v.v.)."
                    logger.info(f"Style preference saved for user {user_id}: {style_request['style_description'][:50]}")
                else:
                    # Reject invalid style preference
                    violations = ", ".join(validation["violations"])
                    style_learning_response = f"❌ Tôi không thể học phong cách này vì nó vi phạm các nguyên tắc cốt lõi của StillMe: {violations}. StillMe được thiết kế để không mô phỏng cảm xúc, không claim personal experiences, và luôn transparent về bản chất AI. Bạn có thể đề xuất một phong cách khác phù hợp với các nguyên tắc này."
                    logger.warning(f"Style preference rejected for user {user_id}: {violations}")
            else:
                # Apply existing style preferences if available
                style_instruction = style_learner.build_style_instruction(user_id)
                if style_instruction:
                    style_learner.update_usage(user_id)
            
            # Inject StillMe identity if validators enabled
            # CRITICAL: Skip identity injection for philosophy-lite mode (already using minimal system prompt)
            if use_philosophy_lite_rag:
                # Philosophy-lite mode: don't inject identity, use prompt as-is
                # Provider will detect and use PHILOSOPHY_LITE_SYSTEM_PROMPT
                enhanced_prompt = base_prompt
            elif enable_validators:
                # Phase 4: Remove inject_identity() - system prompt already has STILLME_IDENTITY
                # generate_ai_response() uses build_system_prompt_with_language() which includes STILLME_IDENTITY
                # Adding identity to user prompt would cause duplication
                # Add style instruction if available
                enhanced_prompt = f"{style_instruction}\n\n{base_prompt}" if style_instruction else base_prompt
            else:
                # No validators: use prompt as-is, but still add style instruction if available
                enhanced_prompt = f"{style_instruction}\n\n{base_prompt}" if style_instruction else base_prompt
            
            # Generate AI response with timing and caching
            # LLM_Inference_Latency: Time from API call start to response received
            provider_name = chat_request.llm_provider or "default"
            
            # CRITICAL: Check Option B FPS blocking BEFORE calling LLM handler
            # This must be done here because it returns ChatResponse immediately
            if use_option_b:
                from backend.core.question_classifier_v2 import get_question_classifier_v2
                classifier = get_question_classifier_v2()
                question_type_result, confidence, _ = classifier.classify(chat_request.message)
                question_type_str = question_type_result.value
                
                # CRITICAL: Check FPS for Option B - use threshold 0.3 for fake concepts
                if fps_result and not fps_result.is_plausible and fps_result.confidence < 0.3:
                    # FPS blocked - return EPD-Fallback immediately
                    logger.warning(f"🛡️ Option B: FPS blocked question - returning EPD-Fallback")
                    from backend.guards.epistemic_fallback import get_epistemic_fallback_generator
                    generator = get_epistemic_fallback_generator()
                    suspicious_entity = fps_result.detected_entities[0] if fps_result.detected_entities else None
                    fallback_text = generator.generate_epd_fallback(
                        question=chat_request.message,
                        detected_lang=detected_lang,
                        suspicious_entity=suspicious_entity,
                        fps_result=fps_result
                    )
                    processing_steps.append("🛡️ Option B: FPS blocked - EPD-Fallback returned")
                    from backend.core.epistemic_state import EpistemicState
                    return ChatResponse(
                        response=fallback_text,
                        confidence_score=1.0,
                        processing_steps=processing_steps,
                        timing_logs={
                            "total_time": time.time() - start_time,
                            "rag_retrieval_latency": rag_retrieval_latency,
                            "llm_inference_latency": 0.0
                        },
                        validation_result=None,
                        used_fallback=True,
                        epistemic_state=EpistemicState.UNKNOWN.value
                    )
            
            # Use LLM handler for cache checking and LLM call
            raw_response, cache_hit, llm_inference_latency = await generate_llm_response(
                enhanced_prompt=enhanced_prompt,
                detected_lang=detected_lang,
                chat_request=chat_request,
                context=context,
                is_philosophical=is_philosophical,
                is_validator_count_question=is_validator_count_query,
                is_origin_query=is_origin_query,
                is_stillme_query=is_stillme_query,
                is_learning_sources_query=is_learning_sources_query,
                detected_lang_name=detected_lang_name,
                context_text=context_text,
                enable_validators=enable_validators,
                use_option_b=use_option_b,
                fps_result=fps_result,
                processing_steps=processing_steps,
                timing_logs=timing_logs
            )
            
            # CRITICAL: Log RAG context info after LLM call to help debug Q1, Q2, Q7, Q9
            logger.info(
                f"🔍 DEBUG Q1/Q2/Q7/Q9: LLM call completed. "
                f"num_knowledge={num_knowledge}, context_text_length={len(context_text) if context_text else 0}, "
                f"enhanced_prompt_length={len(enhanced_prompt) if enhanced_prompt else 0}, "
                f"cache_hit={cache_hit}, llm_inference_latency={llm_inference_latency:.2f}s"
            )
            
            # CRITICAL: Check if raw_response is an error message BEFORE validation
            # This prevents error messages from passing through validators
            # BUT: For technical questions about "your system", don't replace with fallback immediately
            # Instead, let the retry logic handle it (it will retry with stronger prompt)
            if raw_response and isinstance(raw_response, str):
                from backend.api.utils.error_detector import is_technical_error
                # CRITICAL: Log full response for debugging error detection
                logger.debug(f"🔍 Full LLM response (length={len(raw_response)}): {raw_response[:500]}...")
                is_error, error_type = is_technical_error(raw_response)
                # CRITICAL: For technical questions about system, don't replace with fallback immediately
                # The retry logic below will handle it with a stronger prompt
                if is_error and not is_technical_about_system_rag:
                    logger.error(
                        f"❌ LLM returned technical error as response (type: {error_type}): {raw_response[:200]}. "
                        f"Full response length: {len(raw_response)}, Question: {chat_request.message[:100]}"
                    )
                    from backend.api.utils.error_detector import get_fallback_message_for_error
                    raw_response = get_fallback_message_for_error(error_type, detected_lang)
                    processing_steps.append(f"⚠️ LLM returned technical error - replaced with fallback message")
                elif is_error and is_technical_about_system_rag:
                    logger.warning(
                        f"⚠️ Technical question about 'your system' returned error (type: {error_type}) - will retry with stronger prompt. "
                        f"Question: {chat_request.message[:100]}"
                    )
                    # Don't replace yet - let retry logic handle it
            
            # CRITICAL: Validate raw_response immediately after LLM call
            if not raw_response or not isinstance(raw_response, str) or not raw_response.strip():
                logger.error(
                    f"⚠️ LLM returned None or empty response for question: {chat_request.message[:100]}. "
                    f"num_knowledge={num_knowledge}, context_text_length={len(context_text) if context_text else 0}"
                )
                from backend.api.utils.error_detector import get_fallback_message_for_error
                raw_response = get_fallback_message_for_error("generic", detected_lang)
                processing_steps.append("⚠️ LLM returned empty response - using fallback")
            
            # CRITICAL: Only log "AI response generated" if we actually have a response
            # If raw_response is None/empty, it means LLM failed and we're using fallback
            if raw_response and isinstance(raw_response, str) and raw_response.strip():
                logger.info(f"⏱️ LLM inference took {llm_inference_latency:.2f}s")
                processing_steps.append(f"✅ AI response generated ({llm_inference_latency:.2f}s)")
                # Debug: Log first 200 chars to help diagnose issues
                logger.debug(f"🔍 DEBUG: raw_response preview (first 200 chars): {raw_response[:200]}")
                
                # CRITICAL: Check if this is actually a fallback message (shouldn't happen but double-check)
                from backend.api.utils.error_detector import is_fallback_message
                if is_fallback_message(raw_response):
                    logger.error(
                        f"❌ CRITICAL: LLM returned what looks like a fallback message! "
                        f"This should not happen. raw_response[:200]={raw_response[:200]}"
                    )
                    # CRITICAL: For technical questions, this should trigger retry logic below
                    # Mark as fallback so retry logic can handle it
                    is_fallback = True
            else:
                logger.warning(
                    f"⚠️ LLM inference failed or returned empty (took {llm_inference_latency:.2f}s). "
                    f"raw_response type={type(raw_response)}, value={raw_response[:200] if raw_response else 'None'}"
                )
                # Ensure raw_response is set to fallback message if still None/empty
                if not raw_response or not isinstance(raw_response, str) or not raw_response.strip():
                    from backend.api.utils.error_detector import get_fallback_message_for_error
                    raw_response = get_fallback_message_for_error("generic", detected_lang)
                    processing_steps.append("⚠️ LLM failed - using fallback message")
                    logger.warning(f"⚠️ Set raw_response to fallback message: {raw_response[:200]}")
            
            # CRITICAL: Check if raw_response is a technical error message or fallback message before validation
            # Never allow provider error messages to pass through validators
            # CRITICAL: Initialize is_error and is_fallback BEFORE conditional blocks to avoid UnboundLocalError
            is_error = False
            error_type = "generic"
            is_fallback = False
            
            from backend.api.utils.error_detector import is_technical_error, get_fallback_message_for_error, is_fallback_message
            
            if raw_response and isinstance(raw_response, str):
                is_error, error_type = is_technical_error(raw_response)
                is_fallback = is_fallback_message(raw_response)
                # CRITICAL: Log detection for debugging
                if is_fallback:
                    logger.warning(f"⚠️ Detected fallback message in raw_response (length={len(raw_response)}): {raw_response[:200]}")
                if is_technical_about_system_rag:
                    logger.info(f"🔧 Technical question detected: is_error={is_error}, is_fallback={is_fallback}, is_technical_about_system_rag={is_technical_about_system_rag}")
                
                # CRITICAL: For technical questions about "your system" in RAG path, retry if response is error OR fallback
                # This ensures we don't give up on valid technical questions
                if is_technical_about_system_rag and (is_error or is_fallback):
                    logger.warning(f"⚠️ Technical question about 'your system' (RAG path) returned {'error' if is_error else 'fallback'} message - retrying with stronger prompt")
                    # Build stronger prompt with technical system instruction
                    stronger_prompt_rag = f"""{context_quality_warning}

**CRITICAL: YOU MUST ANSWER THIS QUESTION. DO NOT RETURN A TECHNICAL ERROR MESSAGE OR FALLBACK MESSAGE.**

The user is asking: {chat_request.message}

**YOU HAVE KNOWLEDGE ABOUT RAG SYSTEMS. USE IT TO ANSWER.**

Explain:
1. What RAG (Retrieval-Augmented Generation) is
2. How retrieval works (embedding, vector search, ChromaDB)
3. How LLM generation works
4. How they work together in StillMe's system

**DO NOT SAY:**
- "I cannot provide a good answer"
- "StillMe is experiencing a technical issue"
- "I will suggest to the developer"
- "I cannot provide a good answer to this question with the current configuration"

**DO SAY:**
- "Based on general knowledge about RAG systems..."
- Explain the architecture clearly
- Be transparent about what you know and what you don't know

{context_text}
{citation_instruction}
{confidence_instruction}
{stillme_instruction}

Remember: RESPOND IN {detected_lang_name.upper()} ONLY."""
                    try:
                        raw_response = await generate_ai_response(
                            stronger_prompt_rag,
                            detected_lang=detected_lang,
                            llm_provider=chat_request.llm_provider,
                            llm_api_key=chat_request.llm_api_key,
                            llm_api_url=chat_request.llm_api_url,
                            llm_model_name=chat_request.llm_model_name,
                            use_server_keys=chat_request.llm_provider is None
                        )
                        logger.info("✅ Retry with stronger prompt successful for technical 'your system' question (RAG path)")
                        processing_steps.append("🔄 Retried with stronger prompt for technical 'your system' question (RAG path)")
                        # Re-check if retry response is still an error or fallback
                        is_error_retry, error_type_retry = is_technical_error(raw_response)
                        is_fallback_retry = is_fallback_message(raw_response)
                        if is_error_retry or is_fallback_retry:
                            logger.warning(f"⚠️ Retry still returned {'error' if is_error_retry else 'fallback'} - forcing one more retry with even stronger prompt")
                            # Force one more retry with even stronger prompt
                            force_prompt = f"""**ABSOLUTE MANDATORY: ANSWER THIS QUESTION ABOUT RAG SYSTEMS**

User Question: {chat_request.message}

**YOU MUST EXPLAIN:**
1. RAG (Retrieval-Augmented Generation) combines retrieval from a knowledge base with LLM generation
2. Retrieval: Query is embedded, searched in vector database (ChromaDB), returns relevant documents
3. LLM Generation: Takes retrieved context + user question, generates answer
4. Integration: Retrieval provides context, LLM uses context to generate accurate, cited answers

**STILLME SPECIFIC:**
- Uses paraphrase-multilingual-MiniLM-L12-v2 embedding model (384 dimensions, 50+ languages)
- ChromaDB as vector database
- Retrieval happens first, then LLM generation with retrieved context

**DO NOT RETURN ERROR MESSAGES. ANSWER THE QUESTION DIRECTLY.**

Remember: RESPOND IN {detected_lang_name.upper()} ONLY."""
                            try:
                                raw_response = await generate_ai_response(
                                    force_prompt,
                                    detected_lang=detected_lang,
                                    llm_provider=chat_request.llm_provider,
                                    llm_api_key=chat_request.llm_api_key,
                                    llm_api_url=chat_request.llm_api_url,
                                    llm_model_name=chat_request.llm_model_name,
                                    use_server_keys=chat_request.llm_provider is None
                                )
                                logger.info("✅ Force retry successful for technical 'your system' question (RAG path)")
                                processing_steps.append("🔄 Force retry successful for technical 'your system' question")
                            except Exception as force_error:
                                logger.error(f"⚠️ Force retry failed: {force_error}")
                                raw_response = get_fallback_message_for_error(error_type_retry or "generic", detected_lang)
                    except Exception as retry_error:
                        logger.error(f"⚠️ Retry failed (RAG path): {retry_error}")
                        raw_response = get_fallback_message_for_error(error_type or "generic", detected_lang)
                        processing_steps.append(f"⚠️ Technical error detected (RAG path) - using fallback message")
                elif is_error:
                    # For non-technical questions, just replace with fallback
                    logger.error(f"❌ Provider returned technical error as response (type: {error_type}): {raw_response[:200]}")
                    # Replace with user-friendly fallback message
                    raw_response = get_fallback_message_for_error(error_type, detected_lang)
                    processing_steps.append(f"⚠️ Technical error detected - replaced with fallback message")
                    logger.warning(f"⚠️ Replaced technical error with user-friendly message in {detected_lang}")
            
            # CRITICAL: Check if response is a fallback message - if so, skip validation/post-processing
            # BUT: Still pass through CitationRequired to add citations for factual questions
            if raw_response and isinstance(raw_response, str) and is_fallback_message(raw_response):
                logger.warning(
                    f"🛑 Fallback meta-answer detected - skipping validation, quality evaluation, and rewrite. "
                    f"raw_response length={len(raw_response)}, first_200_chars={raw_response[:200]}"
                )
                # CRITICAL: Log why this is a fallback message to help debug Q2, Q7
                logger.error(
                    f"🔍 DEBUG Q2/Q7: Detected fallback message. "
                    f"Question: {chat_request.message[:100]}, "
                    f"LLM call completed: {llm_inference_latency:.2f}s, "
                    f"Response preview: {raw_response[:200]}"
                )
                # CRITICAL: Pass fallback message through CitationRequired to add citations for factual questions
                from backend.validators.citation import CitationRequired
                citation_validator = CitationRequired(required=True)
                # Build ctx_docs for citation validator
                ctx_docs_for_citation = [
                    doc["content"] for doc in context.get("knowledge_docs", [])
                ] + [
                    doc["content"] for doc in context.get("conversation_docs", [])
                ]
                citation_result = citation_validator.run(
                    raw_response, 
                    ctx_docs=ctx_docs_for_citation,
                    is_philosophical=is_philosophical,
                    user_question=chat_request.message,
                    context=context  # CRITICAL: Pass context for foundational knowledge detection
                )
                if citation_result.patched_answer:
                    response = citation_result.patched_answer
                    logger.info(f"✅ Added citation to fallback message for factual question. Reasons: {citation_result.reasons}")
                    processing_steps.append("✅ Citation added to fallback message for factual question")
                else:
                    response = raw_response
                # Skip validation, quality evaluator, rewrite, and learning
                validation_info = None
                confidence_score = 0.3  # Low confidence for fallback messages
                processing_steps.append("🛑 Fallback message - terminal response, skipping all post-processing")
                # Skip to end of function (skip validation, post-processing, learning)
                # We'll handle this by setting a flag and checking it before validation
                is_fallback_meta_answer = True
                is_fallback_for_learning = True  # Skip learning extraction for fallback meta-answers
            else:
                is_fallback_meta_answer = False
                # Log if raw_response exists but is not a fallback message
                if raw_response and isinstance(raw_response, str):
                    logger.debug(
                        f"✅ raw_response is valid (not fallback): length={len(raw_response)}, "
                        f"first_100_chars={raw_response[:100]}"
                    )
            
            # CRITICAL: If response is a fallback meta-answer, skip validation and post-processing entirely
            if is_fallback_meta_answer:
                logger.info("🛑 Skipping validation and post-processing for fallback meta-answer")
                # response already set above
                # validation_info already set to None
                # confidence_score already set to 0.3
            else:
                # Validate response if enabled
                if enable_validators:
                    # CRITICAL: Ensure raw_response is valid before validation
                    if not raw_response or not isinstance(raw_response, str) or not raw_response.strip():
                        logger.error(f"⚠️ raw_response is None or empty before validation - using fallback")
                        logger.error(f"⚠️ Debug: raw_response type={type(raw_response)}, value={raw_response[:100] if raw_response else 'None'}")
                        logger.error(f"⚠️ Debug: processing_steps so far: {processing_steps}")
                        from backend.api.utils.error_detector import get_fallback_message_for_error
                        response = get_fallback_message_for_error("generic", detected_lang)
                        validation_info = None
                        confidence_score = 0.3
                        processing_steps.append("⚠️ Response validation failed - using fallback message")
                    else:
                        try:
                            # Call validation handler
                            response, validation_info, confidence_score, used_fallback, step_validation_info, consistency_info, ctx_docs = await handle_validation_with_fallback(
                                raw_response=raw_response,
                                context=context,
                                detected_lang=detected_lang,
                                is_philosophical=is_philosophical,
                                is_religion_roleplay=is_religion_roleplay,
                                chat_request=chat_request,
                                enhanced_prompt=enhanced_prompt,
                                context_text=context_text,
                                citation_instruction=citation_instruction,
                                num_knowledge=num_knowledge,
                                processing_steps=processing_steps,
                                timing_logs=timing_logs,
                                is_origin_query=is_origin_query,
                                is_stillme_query=is_stillme_query
                            )
                            
                            # CRITICAL: Log response after validation (especially for philosophical questions)
                            if is_philosophical or detected_lang == "zh":
                                logger.info(
                                    f"🔍 [VALIDATION TRACE] After validation: "
                                    f"response_length={len(response) if response else 0}, "
                                    f"is_philosophical={is_philosophical}, "
                                    f"detected_lang={detected_lang}, "
                                    f"preview={safe_unicode_slice(response, 200) if response else 'None'}"
                                )
                        except Exception as validation_error:
                            logger.error(f"❌ Validation error: {validation_error}", exc_info=True)
                            # Fallback to raw response if validation fails
                            response = raw_response
                            validation_info = None
                            confidence_score = 0.5
                            used_fallback = False
                            step_validation_info = None
                            consistency_info = None
                            ctx_docs = []
                else:
                    # Validators disabled - use raw response
                    response = raw_response
                    # Build ctx_docs for transparency check
                    ctx_docs = [
                        doc["content"] for doc in context.get("knowledge_docs", [])
                    ] + [
                        doc["content"] for doc in context.get("conversation_docs", [])
                    ]
                # Calculate basic confidence score even without validators
                confidence_score = calculate_confidence_score(
                    context_docs_count=len(context.get("knowledge_docs", [])) + len(context.get("conversation_docs", [])),
                    validation_result=None,
                    context=context
                )
                
                # CRITICAL: Add transparency warning for low confidence responses without context (RAG path, validators disabled)
                # CRITICAL: StillMe MUST know about its own origin - never add disclaimer for origin queries
                if confidence_score < 0.5 and len(ctx_docs) == 0 and not is_philosophical and not is_origin_query:
                    response_lower = response.lower() if response else ""
                    has_transparency = any(
                        phrase in response_lower for phrase in [
                            "không có dữ liệu", "không có thông tin", "kiến thức chung", "dựa trên kiến thức",
                            "don't have data", "don't have information", "general knowledge", "based on knowledge",
                            "không từ stillme", "not from stillme", "không từ rag", "not from rag"
                        ]
                    )
                    if not has_transparency and response:
                        # Generate multilingual transparency disclaimer
                        disclaimer = get_transparency_disclaimer(detected_lang)
                        response = disclaimer + response
                        logger.info("ℹ️ Added transparency disclaimer for low confidence response without context (RAG path, validators disabled)")
            
            # ==========================================
            # PHASE 3: POST-PROCESSING PIPELINE
            # Unified Style & Quality Enforcement Layer (Optimized)
            # ==========================================
            # CRITICAL: Log response state before post-processing (especially for philosophical questions)
            if is_philosophical or detected_lang == "zh":
                logger.info(
                    f"🔍 [POST-PROCESSING TRACE] Before post-processing: "
                    f"response_length={len(response) if response else 0}, "
                    f"is_philosophical={is_philosophical}, "
                    f"detected_lang={detected_lang}, "
                    f"preview={safe_unicode_slice(response, 200) if response else 'None'}"
                )
            
            # CRITICAL: Ensure response is set and not None
            if not response:
                logger.error("⚠️ Response is None or empty before post-processing - using fallback")
                from backend.api.utils.error_detector import get_fallback_message_for_error
                response = get_fallback_message_for_error("generic", detected_lang)
            
            # CRITICAL: Check if response is a fallback meta-answer - if so, skip all post-processing
            from backend.api.utils.error_detector import is_fallback_message
            is_fallback_meta_answer_rag = False
            if response and is_fallback_message(response):
                logger.info("🛑 Fallback meta-answer detected (RAG path) - skipping post-processing (sanitize, quality eval, rewrite)")
                processing_steps.append("🛑 Fallback message - terminal response, skipping post-processing")
                is_fallback_meta_answer_rag = True
                is_fallback_for_learning = True  # Skip learning extraction for fallback meta-answers
                # Skip post-processing entirely - response is already the fallback message
            else:
                # Use post-processing handler
                from backend.api.handlers.post_processing_handler import process_response
                
                # Get is_stillme_query if available (may not be in scope)
                is_stillme_query_for_postprocessing = is_stillme_query if 'is_stillme_query' in locals() else False
                ctx_docs_for_postprocessing = ctx_docs if 'ctx_docs' in locals() else None
                context_for_postprocessing = context if 'context' in locals() else None
                
                response, postprocessing_time = await process_response(
                    raw_response=response,
                    context=context_for_postprocessing,
                    detected_lang=detected_lang,
                    is_philosophical=is_philosophical,
                    is_stillme_query=is_stillme_query_for_postprocessing,
                    chat_request=chat_request,
                    validation_info=validation_info if 'validation_info' in locals() else None,
                    processing_steps=processing_steps,
                    timing_logs=timing_logs,
                    ctx_docs=ctx_docs_for_postprocessing
                )
                
                # CRITICAL: Log response state after post-processing (especially for philosophical questions)
                if is_philosophical or detected_lang == "zh":
                    logger.info(
                        f"🔍 [POST-PROCESSING TRACE] After post-processing: "
                        f"response_length={len(response) if response else 0}, "
                        f"is_philosophical={is_philosophical}, "
                        f"detected_lang={detected_lang}, "
                        f"preview={safe_unicode_slice(response, 200) if response else 'None'}"
                    )
        else:
            # Fallback to regular AI response (no RAG context)
            # CRITICAL: Check if this is a technical question about "your system"
            # These should still get an answer from base LLM knowledge, not technical error
            question_lower = chat_request.message.lower()
            # Note: 're' module is already imported at top level
            # Check for technical keywords
            has_technical_keyword = any(keyword in question_lower for keyword in [
                "rag", "retrieval", "llm", "generation", "embedding", "chromadb", 
                "vector", "pipeline", "validation", "transparency", "system",
                "validator", "chain", "factual hallucination", "citation required"
            ])
            # Check for "your system" patterns using regex
            has_your_system_pattern = (
                "your system" in question_lower or
                "in your system" in question_lower or
                re.search(r'your\s+\w+\s+system', question_lower) or
                re.search(r'system\s+\w+\s+you', question_lower) or
                "bạn" in question_lower and "hệ thống" in question_lower or
                "của bạn" in question_lower
            )
            is_technical_about_system = has_technical_keyword and has_your_system_pattern
            
            if is_technical_about_system:
                logger.info("🔧 Technical question about 'your system' with no RAG context - will answer from base LLM knowledge with transparency")
            
            # Initialize confidence_score for non-RAG path
            config = get_chat_config()
            confidence_score = config.confidence.DEFAULT_NO_CONTEXT  # Low confidence when no RAG context
            validation_info = None
            
            # Detect language FIRST
            # CRITICAL: detect_language is imported at top level, but ensure it's available
            # Use the imported function directly (already imported at line 11)
            detected_lang = detect_language(chat_request.message)
            logger.info(f"🌐 Detected language (non-RAG): {detected_lang}")
            
            # Language names mapping
            # Language names mapping (must match chat_helpers.py for consistency)
            language_names = {
                'vi': 'Vietnamese (Tiếng Việt)',
                'zh': 'Chinese (中文)',
                'de': 'German (Deutsch)',
                'fr': 'French (Français)',
                'es': 'Spanish (Español)',
                'ja': 'Japanese (日本語)',
                'ko': 'Korean (한국어)',
                'ar': 'Arabic (العربية)',
                'ru': 'Russian (Русский)',
                'pt': 'Portuguese (Português)',
                'it': 'Italian (Italiano)',
                'hi': 'Hindi (हिन्दी)',
                'th': 'Thai (ไทย)',
                'en': 'English'
            }
            
            detected_lang_name = language_names.get(detected_lang, 'the same language as the question')
            
            # Check if this is a philosophical question for non-RAG path
            is_philosophical_non_rag = False
            try:
                from backend.core.question_classifier import is_philosophical_question
                is_philosophical_non_rag = is_philosophical_question(chat_request.message)
            except Exception:
                pass  # If classifier fails, assume non-philosophical
            
            # Helper function to estimate tokens
            def estimate_tokens(text: str) -> int:
                """Estimate token count (~4 chars per token)"""
                return len(text) // 4 if text else 0
            
            # For philosophical questions: truncate user question to 512 tokens max
            user_question_for_prompt = chat_request.message
            if is_philosophical_non_rag:
                user_question_tokens = estimate_tokens(chat_request.message)
                config = get_chat_config()
                if user_question_tokens > config.tokens.MAX_PHILOSOPHY_QUESTION:
                    logger.warning(
                        f"User question too long for philosophical non-RAG ({user_question_tokens} tokens), truncating to {config.tokens.MAX_PHILOSOPHY_QUESTION} tokens"
                    )
                    user_question_for_prompt = truncate_user_message(chat_request.message, max_tokens=config.tokens.MAX_PHILOSOPHY_QUESTION)
                    user_question_tokens = estimate_tokens(user_question_for_prompt)
                else:
                    user_question_tokens = estimate_tokens(chat_request.message)
            else:
                user_question_tokens = estimate_tokens(chat_request.message)
            
            # Build conversation history context if provided (with token limits)
            # Reduced from 2000 to 1000 tokens to leave more room for system prompt and context
            # For philosophical questions, skip conversation history to reduce prompt size
            conversation_history_text = ""
            if not is_philosophical_non_rag:
                config = get_chat_config()
                conversation_history_text = format_conversation_history(chat_request.conversation_history, max_tokens=config.tokens.MAX_CONVERSATION_HISTORY)
                if conversation_history_text:
                    logger.info(f"Including conversation history in context (truncated if needed, non-RAG)")
            else:
                logger.info(f"Philosophical question detected (non-RAG) - skipping conversation history to reduce prompt size")
            
            # For philosophical non-RAG: ALWAYS use philosophy-lite mode to prevent context overflow
            # This ensures prompt stays small (~500-1000 tokens) instead of ~16-17k tokens
            if is_philosophical_non_rag:
                # Use philosophy-lite mode: minimal system prompt + user question only
                # Build simple prompt string that provider will parse correctly
                # Format: system prompt (will be replaced by provider) + user question marker + user question
                enhanced_prompt = f"""User Question: {user_question_for_prompt.strip()}"""
                
                # Log token estimates for philosophy-lite mode
                system_tokens_estimate = estimate_tokens(PHILOSOPHY_LITE_SYSTEM_PROMPT)
                prompt_tokens_estimate = estimate_tokens(enhanced_prompt)
                total_tokens_estimate = system_tokens_estimate + prompt_tokens_estimate
                
                logger.info(
                    f"📊 [PHILO-LITE] Token estimates - System: {system_tokens_estimate}, "
                    f"Prompt: {prompt_tokens_estimate}, User Question: {user_question_tokens}, "
                    f"Total: {total_tokens_estimate}"
                )
            else:
                # Use full prompt
                # CRITICAL: Add special instruction for technical questions about "your system"
                technical_system_instruction = ""
                if is_technical_about_system:
                    technical_system_instruction = """
🚨🚨🚨 CRITICAL: TECHNICAL QUESTION ABOUT SYSTEM ARCHITECTURE 🚨🚨🚨

The user is asking about StillMe's system architecture (RAG, LLM, embedding, etc.).

**YOU MUST ANSWER THIS QUESTION** using your base knowledge about RAG systems, even though StillMe's RAG knowledge base doesn't have specific documents about this.

**TRANSPARENCY REQUIREMENT:**
- Acknowledge that you're answering from base knowledge, not from StillMe's RAG knowledge base
- Be transparent: "Based on general knowledge about RAG systems (not from StillMe's RAG knowledge base)..."
- Explain how RAG retrieval and LLM generation work together in general RAG systems
- Be honest about StillMe's specific implementation details if you don't know them

**DO NOT:**
- Return a technical error message
- Say "I cannot provide a good answer"
- Suggest the developer needs to fine-tune the system
- Claim StillMe is experiencing technical issues

**DO:**
- Answer the question using your knowledge about RAG systems
- Be transparent about the source of your knowledge
- Explain the general principles of RAG retrieval and LLM generation
- If asked about StillMe specifically, acknowledge what you know and what you don't know

"""
                
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
{technical_system_instruction}
{conversation_history_text}User Question: {user_question_for_prompt}

Remember: RESPOND IN {detected_lang_name.upper()} ONLY.
"""
                else:
                    base_prompt = f"""🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - HIGHEST PRIORITY 🚨🚨🚨

THE USER'S QUESTION IS WRITTEN IN ENGLISH.

YOU MUST RESPOND EXCLUSIVELY IN ENGLISH.

DO NOT RESPOND IN VIETNAMESE, SPANISH, OR ANY OTHER LANGUAGE.

EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN ENGLISH.

THIS IS MANDATORY AND OVERRIDES ALL OTHER INSTRUCTIONS.

{technical_system_instruction}
{conversation_history_text}

🚨🚨🚨 CRITICAL: USER QUESTION ABOVE IS THE PRIMARY TASK 🚨🚨🚨

User Question: {user_question_for_prompt}

**YOUR PRIMARY TASK IS TO ANSWER THE USER QUESTION ABOVE DIRECTLY AND ACCURATELY.**
- Focus on what the user is actually asking, not on general philosophy
- If the user asks you to analyze something, analyze THAT specific thing
- If the user asks you to find a problem, look for problems in what they showed you

**SPECIAL INSTRUCTION FOR ANALYZING EXTERNAL AI OUTPUTS:**
- If the user asks you to analyze another AI's output (ChatGPT, Claude, etc.), you MUST check for anthropomorphic language
- Look for phrases like "in my experience" / "theo kinh nghiệm", "I think" / "tôi nghĩ", "I feel" / "tôi cảm thấy"
- These phrases falsely attribute subjective qualities (experience, emotions, personal opinions) to AI
- This is a critical transparency issue called "Hallucination of Experience" - AI should not claim personal experience
- If you find such phrases, you MUST point them out as a problem, not ignore them
- This is more important than analyzing formatting, clarity, or other minor issues

Remember: RESPOND IN ENGLISH ONLY."""
                
                # Phase 4: Remove inject_identity() - system prompt already has STILLME_IDENTITY
                # generate_ai_response() uses build_system_prompt_with_language() which includes STILLME_IDENTITY
                # Adding identity to user prompt would cause duplication
                enhanced_prompt = base_prompt
            
            # LLM_Inference_Latency: Time from API call start to response received
            llm_inference_start = time.time()
            # Use server keys for internal calls (when use_rag=False)
            use_server_keys_non_rag = chat_request.llm_provider is None
            
            # Check if this is a philosophical question for context overflow handling
            is_philosophical_non_rag = False
            try:
                from backend.core.question_classifier import is_philosophical_question
                is_philosophical_non_rag = is_philosophical_question(chat_request.message)
            except Exception:
                pass
            
            # Try to generate response with retry on context overflow
            from backend.api.utils.llm_providers import ContextOverflowError
            from backend.api.utils.error_detector import is_technical_error, get_fallback_message_for_error, is_fallback_message
            
            # Note: is_fallback_meta_answer_non_rag already initialized at function start
            # Reset to False for this non-RAG path execution
            is_fallback_meta_answer_non_rag = False
            
            response = None
            try:
                response = await generate_ai_response(
                    enhanced_prompt, 
                    detected_lang=detected_lang,
                    llm_provider=chat_request.llm_provider,
                    llm_api_key=chat_request.llm_api_key,
                    use_server_keys=use_server_keys_non_rag
                )
            except ContextOverflowError as e:
                # Context overflow - retry with minimal prompt for philosophical questions
                logger.warning(f"⚠️ Context overflow detected (non-RAG): {e}")
                
                if is_philosophical_non_rag:
                    # For philosophical questions, use minimal prompt
                    logger.info("🔄 Retrying with minimal philosophical prompt...")
                    # Non-RAG path: no context available, but still pass None for consistency
                    minimal_prompt = build_minimal_philosophical_prompt(
                        user_question=chat_request.message,
                        language=detected_lang,
                        detected_lang_name=detected_lang_name,
                        context=None,  # Non-RAG path: no context available
                        validation_info=None  # Validation hasn't run yet
                    )
                    try:
                        response = await generate_ai_response(
                            minimal_prompt,
                            detected_lang=detected_lang,
                            llm_provider=chat_request.llm_provider,
                            llm_api_key=chat_request.llm_api_key,
                            use_server_keys=use_server_keys_non_rag
                        )
                        logger.info("✅ Minimal prompt retry successful")
                    except ContextOverflowError as retry_error:
                        # Even minimal prompt failed - return fallback message
                        logger.error(f"⚠️ Even minimal prompt failed: {retry_error}")
                        response = get_fallback_message_for_error("context_overflow", detected_lang)
                        processing_steps.append("⚠️ Context overflow - using fallback message")
                else:
                    # For non-philosophical, return fallback message
                    logger.warning("⚠️ Context overflow for non-philosophical question - using fallback message")
                    response = get_fallback_message_for_error("context_overflow", detected_lang)
                    processing_steps.append("⚠️ Context overflow - using fallback message")
            
            # CRITICAL: Check if response is a technical error (should not happen, but safety check)
            # BUT: For technical questions about "your system", if we get a fallback message, 
            # we should retry with a stronger prompt instead of just using fallback
            if response:
                is_error, error_type = is_technical_error(response)
                if is_error:
                    # For technical questions about "your system", retry with stronger prompt
                    if is_technical_about_system and error_type == "generic":
                        logger.warning(f"⚠️ Technical question about 'your system' returned fallback message - retrying with stronger prompt")
                        # Build a stronger prompt that explicitly forces the LLM to answer
                        stronger_prompt = f"""{technical_system_instruction}

**CRITICAL: YOU MUST ANSWER THIS QUESTION. DO NOT RETURN A TECHNICAL ERROR MESSAGE.**

The user is asking: {chat_request.message}

**YOU HAVE KNOWLEDGE ABOUT RAG SYSTEMS. USE IT TO ANSWER.**

Explain:
1. What RAG (Retrieval-Augmented Generation) is
2. How retrieval works (embedding, vector search, ChromaDB)
3. How LLM generation works
4. How they work together in StillMe's system

**DO NOT SAY:**
- "I cannot provide a good answer"
- "StillMe is experiencing a technical issue"
- "I will suggest to the developer"

**DO SAY:**
- "Based on general knowledge about RAG systems..."
- Explain the architecture clearly
- Be transparent about what you know and what you don't know

Remember: RESPOND IN {detected_lang_name.upper()} ONLY."""
                        try:
                            response = await generate_ai_response(
                                stronger_prompt,
                                detected_lang=detected_lang,
                                llm_provider=chat_request.llm_provider,
                                llm_api_key=chat_request.llm_api_key,
                                use_server_keys=use_server_keys_non_rag
                            )
                            logger.info("✅ Retry with stronger prompt successful for technical 'your system' question")
                            processing_steps.append("🔄 Retried with stronger prompt for technical 'your system' question")
                        except Exception as retry_error:
                            logger.error(f"⚠️ Retry failed: {retry_error}")
                            # Fall back to original error handling
                            response = get_fallback_message_for_error(error_type, detected_lang)
                            processing_steps.append(f"⚠️ Technical error detected - using fallback message")
                    else:
                        logger.error(f"⚠️ LLM returned technical error string: {error_type} - {response[:200]}")
                        # Replace with user-friendly fallback message
                        response = get_fallback_message_for_error(error_type, detected_lang)
                        processing_steps.append(f"⚠️ Technical error detected - using fallback message")
            
            if not response:
                # Fallback if response is still None
                response = get_fallback_message_for_error("generic", detected_lang)
                processing_steps.append("⚠️ No response received - using fallback message")
            
            # CRITICAL: Check if response is a fallback meta-answer (terminal response)
            if response and isinstance(response, str) and is_fallback_message(response):
                logger.info("🛑 Fallback meta-answer detected (non-RAG) - skipping post-processing")
                # CRITICAL: Pass fallback message through CitationRequired to add citations for factual questions
                from backend.validators.citation import CitationRequired
                citation_validator = CitationRequired(required=True)
                citation_result = citation_validator.run(
                    response, 
                    ctx_docs=[],  # No context for non-RAG path
                    is_philosophical=is_philosophical_non_rag,
                    user_question=chat_request.message
                )
                if citation_result.patched_answer:
                    response = citation_result.patched_answer
                    logger.info(f"✅ Added citation to fallback message for factual question (non-RAG). Reasons: {citation_result.reasons}")
                    processing_steps.append("✅ Citation added to fallback message for factual question (non-RAG)")
                is_fallback_meta_answer_non_rag = True
                is_fallback_for_learning = True  # Skip learning extraction for fallback meta-answers
                processing_steps.append("🛑 Fallback message - terminal response, skipping all post-processing")
            
            llm_inference_end = time.time()
            llm_inference_latency = llm_inference_end - llm_inference_start
            timing_logs["llm_inference"] = f"{llm_inference_latency:.2f}s"
            logger.info(f"⏱️ LLM inference (non-RAG) took {llm_inference_latency:.2f}s")
            
            # CRITICAL: Check language mismatch and citations for non-RAG path (if validators enabled)
            if enable_validators and response and not is_fallback_meta_answer_non_rag:
                from backend.api.utils.chat_helpers import detect_language as detect_lang_func
                detected_output_lang = detect_lang_func(response)
                if detected_output_lang != detected_lang:
                    logger.warning(f"⚠️ Language mismatch detected (non-RAG): output={detected_output_lang}, expected={detected_lang}")
                    # Try to retry with stronger language instruction
                    try:
                        language_names = {
                            'vi': 'Tiếng Việt', 'en': 'English', 'zh': '中文', 'fr': 'Français',
                            'es': 'Español', 'de': 'Deutsch', 'ja': '日本語', 'ko': '한국어',
                            'ar': 'العربية', 'ru': 'Русский', 'pt': 'Português', 'it': 'Italiano',
                            'hi': 'हिन्दी', 'th': 'ไทย',
                        }
                        retry_lang_name = language_names.get(detected_lang, detected_lang.upper())
                        
                        retry_prompt = f"""🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - ABSOLUTE HIGHEST PRIORITY 🚨🚨🚨

THE USER'S QUESTION IS IN {retry_lang_name.upper()}.

YOU MUST RESPOND EXCLUSIVELY IN {retry_lang_name.upper()}. 

DO NOT USE VIETNAMESE, ENGLISH, FRENCH, CHINESE, SPANISH, GERMAN, OR ANY OTHER LANGUAGE.

EVERY SINGLE WORD MUST BE IN {retry_lang_name.upper()}.

IF YOUR BASE MODEL WANTS TO RESPOND IN ANOTHER LANGUAGE, YOU MUST TRANSLATE IT TO {retry_lang_name.upper()} BEFORE RETURNING.

THIS OVERRIDES EVERYTHING - NO EXCEPTIONS.

User Question (in {retry_lang_name.upper()}): {chat_request.message[:3000]}

**YOUR PRIMARY TASK IS TO ANSWER THE USER QUESTION ABOVE DIRECTLY AND ACCURATELY IN {retry_lang_name.upper()} ONLY.**

Remember: RESPOND IN {retry_lang_name.upper()} ONLY. TRANSLATE IF NECESSARY."""
                        
                        retry_response = await generate_ai_response(
                            retry_prompt,
                            detected_lang=detected_lang,
                            llm_provider=chat_request.llm_provider,
                            llm_api_key=chat_request.llm_api_key,
                            use_server_keys=use_server_keys_non_rag
                        )
                        
                        # Check if retry fixed the language issue
                        retry_output_lang = detect_lang_func(retry_response)
                        if retry_output_lang == detected_lang:
                            logger.info(f"✅ Language mismatch fixed after retry (non-RAG)")
                            response = retry_response
                        else:
                            logger.warning(f"⚠️ Language mismatch persists after retry (non-RAG): output={retry_output_lang}, expected={detected_lang}")
                    except Exception as retry_error:
                        logger.error(f"⚠️ Language retry failed (non-RAG): {retry_error}")
                        # Continue with original response
                
                # CRITICAL FIX: Check citations for ALL factual questions in non-RAG path (not just philosophical)
                # Even though there's no RAG context, factual questions (historical, philosophical factual) still need citations
                # This ensures transparency: user knows answer is from base knowledge, not RAG
                is_factual_non_rag = False
                try:
                    # Check if question is factual (historical, scientific, or philosophical factual)
                    is_factual_non_rag = is_factual_question(chat_request.message) or is_philosophical_non_rag
                except Exception:
                    # If detection fails, assume it might be factual if philosophical
                    is_factual_non_rag = is_philosophical_non_rag
                
                if is_factual_non_rag:
                    from backend.validators.citation import CitationRequired
                    citation_validator = CitationRequired(required=True)
                    # Non-RAG path has no context documents, but still need to check for citations
                    citation_result = citation_validator.run(
                        response, 
                        ctx_docs=[],  # Empty context for non-RAG path
                        is_philosophical=is_philosophical_non_rag,
                        user_question=chat_request.message
                    )
                    # Use patched_answer if available (e.g., citation was auto-added)
                    if citation_result.patched_answer:
                        response = citation_result.patched_answer
                        logger.info(f"✅ Citation added for factual question (non-RAG). Reasons: {citation_result.reasons}, is_philosophical={is_philosophical_non_rag}")
                        processing_steps.append("✅ Citation auto-added for factual question (non-RAG)")
                    elif not citation_result.passed:
                        logger.warning(f"⚠️ Citation validation failed for factual question (non-RAG) but no patched_answer. Reasons: {citation_result.reasons}")
                        processing_steps.append(f"⚠️ Citation validation failed: {', '.join(citation_result.reasons)}")
            
            # CRITICAL: Hallucination Guard for non-RAG path
            # If factual question + no context + low confidence → override with safe refusal
            # This prevents LLM from hallucinating about non-existent concepts/events
            if (response and not is_fallback_meta_answer_non_rag and not is_philosophical_non_rag and
                confidence_score < 0.5 and is_factual_question(chat_request.message)):
                # Check if response contains suspicious patterns (fake citations, fabricated details)
                response_lower = response.lower()
                suspicious_patterns = [
                    r"\[1\]|\[2\]|\[3\]",  # Fake citations
                    r"et al\.|et\. al\.",  # Fake author citations
                    r"\d{4}\)",  # Fake year citations like "(1975)"
                    r"according to research|theo nghiên cứu",
                    r"smith,|jones,|brown,",  # Common fake author names
                    r"journal of|tạp chí",
                ]
                
                # Use loop instead of generator expression to avoid closure issue with 're'
                has_suspicious_pattern = False
                for pattern in suspicious_patterns:
                    if re.search(pattern, response_lower):
                        has_suspicious_pattern = True
                        break
                
                # If suspicious patterns detected OR confidence is very low (< 0.3), override response
                if has_suspicious_pattern or confidence_score < 0.3:
                    # Extract suspicious entity using improved extraction (full phrase, not just first word)
                    suspicious_entity = extract_full_named_entity(chat_request.message)
                    if not suspicious_entity:
                        suspicious_entity = "khái niệm này" if detected_lang == "vi" else "this concept"
                    
                    # Override with safe refusal answer
                    response = _build_safe_refusal_answer(chat_request.message, detected_lang, suspicious_entity)
                    
                    # CRITICAL: If None, it's a well-known historical fact - continue with normal flow (use base knowledge)
                    if response is None:
                        logger.info("✅ Well-known historical fact detected - continuing with normal flow to use base knowledge")
                        processing_steps.append("✅ Well-known historical fact - using base knowledge with transparency")
                        # Continue with normal flow (will use base knowledge instruction)
                    else:
                        logger.warning(
                            f"🛡️ Hallucination Guard triggered (non-RAG): "
                            f"factual_question=True, confidence={confidence_score:.2f}, "
                            f"suspicious_patterns={has_suspicious_pattern}, "
                            f"entity={suspicious_entity or 'unknown'}"
                        )
                        processing_steps.append("🛡️ Hallucination Guard: Overrode response with safe refusal")
                        # Mark as fallback to skip post-processing
                        is_fallback_meta_answer_non_rag = True
                        is_fallback_for_learning = True  # Skip learning extraction for fallback meta-answers
            
            # CRITICAL: Add transparency warning for low confidence responses without context (non-RAG path)
            if confidence_score < 0.5 and not is_fallback_meta_answer_non_rag and not is_philosophical_non_rag and response:
                response_lower = response.lower()
                has_transparency = any(
                    phrase in response_lower for phrase in [
                        "không có dữ liệu", "không có thông tin", "kiến thức chung", "dựa trên kiến thức",
                        "don't have data", "don't have information", "general knowledge", "based on knowledge",
                        "không từ stillme", "not from stillme", "không từ rag", "not from rag"
                    ]
                )
                if not has_transparency:
                    # Generate multilingual transparency disclaimer
                    disclaimer = get_transparency_disclaimer(detected_lang)
                    response = disclaimer + response
                    logger.info("ℹ️ Added transparency disclaimer for low confidence response without context (non-RAG path)")
        
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
                
                # CRITICAL: Log response state before tone alignment (especially for Chinese)
                if detected_lang == "zh":
                    logger.debug(
                        f"🔍 [CHINESE] Before align_tone: "
                        f"response_length={len(response) if response else 0}, "
                        f"response_preview={safe_unicode_slice(response, 100) if response else 'None'}"
                    )
                
                response_before_tone = response
                response_after_align = align_tone(response)
                
                # CRITICAL: Validate response after tone alignment
                if not response_after_align or not isinstance(response_after_align, str) or not response_after_align.strip():
                    logger.error(
                        f"❌ CRITICAL: Response became empty after align_tone "
                        f"(detected_lang={detected_lang}, before_length={len(response_before_tone) if response_before_tone else 0}), "
                        f"falling back to original response"
                    )
                    response = response_before_tone  # Fallback to original
                else:
                    # CRITICAL: Only clean if response changed significantly (more than just punctuation addition)
                    # If align_tone only added punctuation, we don't need to clean again
                    length_diff = len(response_after_align) - len(response_before_tone)
                    
                    # If length increased by 1 (punctuation added) or decreased slightly (whitespace removed), skip cleaning
                    # Only clean if there's a significant change that might indicate issues
                    if abs(length_diff) <= 2:
                        # Minor change (likely just punctuation/whitespace) - use aligned response directly
                        response = response_after_align
                        logger.debug(
                            f"✅ align_tone result used directly (minor change: {length_diff} chars, "
                            f"detected_lang={detected_lang})"
                        )
                    else:
                        # Significant change - clean to be safe, but validate carefully
                        response_cleaned = clean_response_text(response_after_align)
                        
                        # CRITICAL: Validate that cleaning didn't lose significant content
                        if len(response_cleaned) < len(response_after_align) * 0.95:
                            logger.error(
                                f"❌ CRITICAL: clean_response_text lost significant content after align_tone "
                                f"(after_align_length={len(response_after_align)}, "
                                f"cleaned_length={len(response_cleaned)}, "
                                f"detected_lang={detected_lang}), "
                                f"using aligned response without cleaning"
                            )
                            response = response_after_align  # Use aligned response without cleaning
                        elif len(response_cleaned) != len(response_after_align):
                            logger.info(
                                f"✅ Cleaned response after align_tone: removed {len(response_after_align) - len(response_cleaned)} "
                                f"problematic characters (detected_lang={detected_lang}, "
                                f"after_align_length={len(response_after_align)}, cleaned_length={len(response_cleaned)})"
                            )
                            response = response_cleaned
                        else:
                            # No change after cleaning - use aligned response
                            response = response_after_align
                
                # CRITICAL: Log response state after tone alignment (especially for Chinese)
                if detected_lang == "zh":
                    logger.debug(
                        f"🔍 [CHINESE] After align_tone: "
                        f"response_length={len(response) if response else 0}, "
                        f"response_preview={safe_unicode_slice(response, 100) if response else 'None'}"
                    )
                
                tone_time = time.time() - tone_start
                timing_logs["tone_alignment"] = f"{tone_time:.2f}s"
                logger.info(f"⏱️ Tone alignment took {tone_time:.2f}s")
            except Exception as tone_error:
                logger.error(
                    f"Tone alignment error (detected_lang={detected_lang}): {tone_error}",
                    exc_info=True
                )
                # Continue with original response on error
        
        # ==========================================
        # PHASE 3: POST-PROCESSING PIPELINE (Non-RAG path)
        # Unified Style & Quality Enforcement Layer (Optimized)
        # ==========================================
        # CRITICAL: If response is a fallback meta-answer, skip all post-processing
        if is_fallback_meta_answer_non_rag:
            logger.info("🛑 Skipping post-processing for fallback meta-answer (non-RAG)")
            # response already set, skip post-processing entirely
            final_response = response
        else:
            # Check if question is philosophical for non-RAG path
            is_philosophical_non_rag = False
            try:
                from backend.core.question_classifier import is_philosophical_question
                is_philosophical_non_rag = is_philosophical_question(chat_request.message)
            except Exception:
                pass  # If classifier fails, assume non-philosophical
            
            # Use post-processing handler
            from backend.api.handlers.post_processing_handler import process_response
            
            # Non-RAG path: no context, no ctx_docs, no is_stillme_query
            response, postprocessing_time = await process_response(
                raw_response=response,
                context=None,  # Non-RAG path has no context
                detected_lang=detected_lang,
                is_philosophical=is_philosophical_non_rag,
                is_stillme_query=False,  # Non-RAG path: assume False
                chat_request=chat_request,
                validation_info=None,  # Non-RAG path: no validation
                processing_steps=processing_steps,
                timing_logs=timing_logs,
                ctx_docs=None  # Non-RAG path: no ctx_docs
            )
            
            final_response = response
        
        # CRITICAL: Ensure response is set from final_response, or keep original if final_response is None or empty
        # CRITICAL FIX: Use safe Unicode slicing for logging (prevents breaking multi-byte characters)
        response_preview = safe_unicode_slice(response, 200) if response else 'None'
        final_response_preview = safe_unicode_slice(final_response, 200) if final_response else 'None'
        
        # CRITICAL: Special logging for Chinese language to debug Unicode issues
        if detected_lang == "zh":
            logger.info(
                f"🔍 [TRACE] [CHINESE] Before final_response assignment: "
                f"response_length={len(response) if response else 0}, "
                f"response_preview={response_preview}, "
                f"final_response_length={len(final_response) if final_response else 0}, "
                f"final_response_preview={final_response_preview}, "
                f"response_type={type(response)}, final_response_type={type(final_response)}"
            )
        else:
            logger.info(
                f"🔍 [TRACE] Before final_response assignment: "
                f"response={response_preview}, final_response={final_response_preview}, "
                f"response_type={type(response)}, final_response_type={type(final_response)}"
            )
        
        # CRITICAL FIX: Only use final_response if it's not None AND not empty
        # This prevents empty string from overwriting valid response content
        if final_response is not None and isinstance(final_response, str) and final_response.strip():
            # CRITICAL: Clean final_response from problematic characters before using
            final_response_cleaned = clean_response_text(final_response)
            if len(final_response_cleaned) != len(final_response):
                logger.warning(
                    f"⚠️ Cleaned final_response: removed {len(final_response) - len(final_response_cleaned)} "
                    f"problematic characters (detected_lang={detected_lang})"
                )
            
            # CRITICAL: Ensure line breaks are preserved (defensive check)
            # Count newlines before and after cleaning
            newlines_before = final_response.count('\n')
            newlines_after = final_response_cleaned.count('\n')
            if newlines_after < newlines_before * 0.9:  # If more than 10% of newlines lost
                logger.warning(
                    f"⚠️ Line breaks may have been lost during cleaning: "
                    f"before={newlines_before}, after={newlines_after}"
                )
                # Try to restore line breaks by checking if original had them
                if '\n' in final_response and '\n' not in final_response_cleaned:
                    logger.error(f"❌ CRITICAL: All line breaks were removed! Restoring from original.")
                    final_response_cleaned = final_response  # Use original if all newlines lost
            
            # CRITICAL: Auto-fix missing line breaks after headings and bullets
            # If LLM didn't follow instruction, we fix it here
            final_response_cleaned = fix_missing_line_breaks(final_response_cleaned)
            
            # final_response is valid and non-empty - use it
            response = final_response_cleaned
            
            # CRITICAL: Log after assignment with safe slicing
            response_after_preview = safe_unicode_slice(response, 200) if response else 'None'
            if detected_lang == "zh":
                logger.info(
                    f"🔍 [TRACE] [CHINESE] After final_response assignment: "
                    f"response_length={len(response) if response else 0}, "
                    f"response_preview={response_after_preview}, response_type={type(response)}"
                )
            else:
                logger.info(f"🔍 [TRACE] After final_response assignment: response={response_after_preview}, response_type={type(response)}")
        elif final_response is not None and (not isinstance(final_response, str) or not final_response.strip()):
            # CRITICAL: final_response is empty string or invalid - keep original response
            logger.error(
                f"❌ [TRACE] CRITICAL: final_response is empty or invalid (type: {type(final_response)}, "
                f"length: {len(final_response) if isinstance(final_response, str) else 'N/A'}), "
                f"keeping original response to prevent content loss. "
                f"original_response_length={len(response) if response else 0}"
            )
            # Keep original response - don't overwrite with empty string
            # Log warning but don't change response
            processing_steps.append("⚠️ CRITICAL: final_response was empty/invalid - preserved original response")
        else:
            # final_response is None - keep original response
            logger.warning(f"⚠️ [TRACE] final_response is None, keeping original response: response={response[:200] if response else 'None'}, response_type={type(response)}")
            # CRITICAL: If both response and final_response are None, we have a problem
            if response is None:
                logger.error(f"❌ [TRACE] CRITICAL: Both response and final_response are None! This should never happen. Using fallback.")
                from backend.api.utils.error_detector import get_fallback_message_for_error
                response = get_fallback_message_for_error("generic", detected_lang or "vi")
                processing_steps.append("⚠️ CRITICAL: Both response and final_response were None - using fallback")
        
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
        
        # Analyze conversation for learning opportunities
        learning_proposal = None
        permission_request = None
        proposal_id = None
        
        # CRITICAL: Detect if base knowledge was used - this indicates a knowledge gap
        used_base_knowledge = False
        if response:
            response_lower = response.lower()
            base_knowledge_indicators = [
                "based on general knowledge", "not from stillme", "not from rag",
                "kiến thức chung", "không từ stillme", "không từ rag",
                "training data", "dữ liệu huấn luyện", "base knowledge",
                "general knowledge", "kiến thức nền tảng"
            ]
            used_base_knowledge = any(indicator in response_lower for indicator in base_knowledge_indicators)
        
        if rag_retrieval and chat_request.use_rag:
            try:
                from backend.services.conversation_learning_extractor import get_conversation_learning_extractor
                from backend.services.learning_proposal_storage import get_learning_proposal_storage
                
                extractor = get_conversation_learning_extractor()
                storage = get_learning_proposal_storage()
                
                # PRIORITY: If base knowledge was used, extract topic for learning proposal
                # Check if: (1) No context, OR (2) Context exists but not relevant (low overlap)
                # Fix: Ensure validation_result is always defined before use
                has_no_context = not context or context.get("total_context_docs", 0) == 0
                has_low_relevance = False
                
                # CRITICAL: Extract validation_result from validation_info if available
                validation_result = None
                if validation_info and isinstance(validation_info, dict):
                    validation_result = validation_info.get("validation_result")
                elif hasattr(validation_info, 'validation_result'):
                    validation_result = validation_info.validation_result
                
                if validation_result and hasattr(validation_result, 'reasons'):
                    has_low_relevance = any("citation_relevance_warning" in r for r in validation_result.reasons)
                
                # CRITICAL: Only analyze for learning if response is NOT a fallback meta-answer
                if not is_fallback_for_learning and used_base_knowledge and (has_no_context or has_low_relevance):
                    # No RAG context OR irrelevant context + base knowledge used = knowledge gap detected
                    # Extract topic from user's question for learning proposal
                    logger.info(f"🔍 Base knowledge used - detecting knowledge gap for learning proposal (no_context: {has_no_context}, low_relevance: {has_low_relevance})")
                    try:
                        # Extract main topic from user question
                        user_question = chat_request.message
                        # Simple topic extraction: use first 200 chars or key phrases
                        topic_snippet = user_question[:200] if len(user_question) > 200 else user_question
                        
                        # Create learning proposal for this knowledge gap
                        base_knowledge_proposal = {
                            "knowledge_snippet": f"Topic: {topic_snippet}\n\nStillMe used base LLM knowledge to answer this question, indicating a knowledge gap in RAG. This topic should be prioritized for learning from trusted sources (arXiv, Wikipedia, RSS feeds).",
                            "source": "knowledge_gap_detection",
                            "knowledge_score": 0.7,  # High priority - user asked about it
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "reason": f"StillMe used base knowledge to answer about '{topic_snippet[:50]}...'. This indicates RAG knowledge gap - should learn this topic from trusted sources.",
                            "is_knowledge_gap": True,
                            "user_question": user_question,
                            "detected_from": "base_knowledge_usage"
                        }
                        
                        # Store learning proposal
                        proposal_id = storage.save_proposal(
                            proposal=base_knowledge_proposal,
                            user_id=chat_request.user_id
                        )
                        base_knowledge_proposal["proposal_id"] = proposal_id
                        learning_proposal = base_knowledge_proposal
                        logger.info(f"✅ Knowledge gap learning proposal created (id: {proposal_id}, topic: {topic_snippet[:50]}...)")
                    except Exception as gap_error:
                        logger.warning(f"Failed to create knowledge gap proposal: {gap_error}")
                
                # Also check for valuable knowledge from user/assistant (existing logic)
                # CRITICAL: Only analyze if response is NOT a fallback meta-answer
                if not is_fallback_for_learning and not learning_proposal:  # Only if we didn't already create a gap proposal
                    learning_proposal = extractor.analyze_conversation_for_learning(
                        user_message=chat_request.message,
                        assistant_response=response,
                        context=context
                    )
                
                if learning_proposal:
                    # If we didn't create proposal above, store it now
                    if "proposal_id" not in learning_proposal:
                        proposal_id = storage.save_proposal(
                            proposal=learning_proposal,
                            user_id=chat_request.user_id
                        )
                        learning_proposal["proposal_id"] = proposal_id
                    
                    # Format permission request
                    permission_request = extractor.format_permission_request(
                        learning_proposal=learning_proposal,
                        language=detected_lang
                    )
                    logger.info(f"Learning proposal generated (id: {proposal_id}, score: {learning_proposal.get('knowledge_score', 0):.2f})")
            except Exception as extractor_error:
                logger.warning(f"Conversation learning extractor error: {extractor_error}")
        
        # Store conversation in vector DB
        if rag_retrieval:
            # P2: Fix conversation embedding blocking - use asyncio.to_thread to truly non-block
            # This ensures embedding generation runs in thread pool, not blocking event loop
            async def store_conversation_background():
                try:
                    # P2: Run blocking I/O in thread pool to avoid blocking event loop
                    # Note: 'asyncio' is already imported at top level (line 32)
                    await asyncio.to_thread(
                        rag_retrieval.add_learning_content,
                        content=f"Q: {chat_request.message}\nA: {response}",
                        source="user_chat",
                        content_type="conversation",
                        metadata={
                            "user_id": chat_request.user_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "accuracy_score": accuracy_score
                        }
                    )
                    logger.debug("✅ Conversation stored in background (non-blocking)")
                except Exception as store_error:
                    logger.error(f"❌ Failed to store conversation in background: {store_error}", exc_info=True)
            
            # Create background task (fire and forget - don't await)
            asyncio.create_task(store_conversation_background())
            logger.debug("🚀 Conversation storage queued in background task (P2: truly non-blocking)")
        
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
        
        # Generate learning suggestions from knowledge gaps if context is empty or low confidence
        learning_suggestions = None
        if (confidence_score is not None and confidence_score < 0.5) or (context and context.get("total_context_docs", 0) == 0):
            try:
                self_diagnosis = get_self_diagnosis()
                if self_diagnosis:
                    gap_result = self_diagnosis.identify_knowledge_gaps(chat_request.message, threshold=0.5)
                    if gap_result.get("has_gap"):
                        suggestion = gap_result.get("suggestion")
                        if suggestion:
                            learning_suggestions = [suggestion]
                        else:
                            # Extract key terms from query for learning suggestions
                            words = re.findall(r'\b\w+\b', chat_request.message.lower())
                            # Filter out common words
                            common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when', 'where', 'who', 'which', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'to', 'of', 'in', 'on', 'at', 'for', 'with', 'by', 'from', 'as', 'about', 'into', 'through', 'during', 'including', 'against', 'among', 'throughout', 'despite', 'towards', 'upon', 'concerning', 'to', 'of', 'in', 'on', 'at', 'for', 'with', 'by', 'from', 'as', 'about', 'into', 'through', 'during', 'including', 'against', 'among', 'throughout', 'despite', 'towards', 'upon', 'concerning'}
                            key_terms = [w for w in words if len(w) > 3 and w not in common_words][:3]
                            if key_terms:
                                learning_suggestions = [f"Consider learning more about: {', '.join(key_terms)}"]
            except Exception as suggestion_error:
                logger.warning(f"Failed to generate learning suggestions: {suggestion_error}")
        
        # Generate unique message ID for feedback tracking
        import uuid
        message_id = f"msg_{uuid.uuid4().hex[:16]}"
        
        # If style learning response exists, prepend it to the response
        if style_learning_response:
            response = f"{style_learning_response}\n\n---\n\n{response}"
        
        # CONVERSATIONAL INTELLIGENCE: Add disclaimer for MEDIUM ambiguity
        # Philosophy: Answer with assumptions acknowledged, not just answer blindly
        # Based on StillMe Manifesto Principle 5: "EMBRACE 'I DON'T KNOW' AS INTELLECTUAL HONESTY"
        if 'ambiguity_level' in locals() and ambiguity_level == "MEDIUM" and ambiguity_score >= 0.4:
            try:
                detected_lang_for_disclaimer = detected_lang if 'detected_lang' in locals() else detect_language(response or chat_request.message)
                if detected_lang_for_disclaimer == "vi":
                    disclaimer = f"\n\n💡 *Lưu ý: Mình đã suy luận ý định của bạn dựa trên ngữ cảnh. Nếu mình hiểu sai, bạn có thể làm rõ để mình trả lời chính xác hơn.*"
                else:
                    disclaimer = f"\n\n💡 *Note: I've inferred your intent based on context. If I misunderstood, please clarify so I can answer more accurately.*"
                
                # Add disclaimer at the end, but before citation
                if response and "[general knowledge]" not in response[-100:]:  # Don't add if citation already at end
                    response = response + disclaimer
                elif response:
                    # Citation is at end, add before citation
                    # CRITICAL: Use Unicode-safe string operations
                    citation_pos = response.rfind("[")
                    if citation_pos > 0:
                        # CRITICAL: Safe string slicing (Python handles Unicode correctly)
                        response_before = response
                        response = response[:citation_pos] + disclaimer + " " + response[citation_pos:]
                        # CRITICAL: Validate result is not empty
                        if not response or not response.strip():
                            logger.warning(
                                f"⚠️ Response became empty after adding disclaimer before citation "
                                f"(detected_lang={detected_lang_for_disclaimer}), "
                                f"falling back to original response"
                            )
                            response = response_before  # Fallback to original
                    else:
                        response = response + disclaimer
                
                logger.info(f"✅ Added MEDIUM ambiguity disclaimer to response")
                if validation_info:
                    validation_info["ambiguity_disclaimer_added"] = True
                    validation_info["ambiguity_score"] = ambiguity_score
                    validation_info["ambiguity_level"] = ambiguity_level
            except Exception as disclaimer_error:
                logger.warning(f"⚠️ Failed to add ambiguity disclaimer: {disclaimer_error}")
        
        # CRITICAL: Final safety check - ensure response is never None or empty before returning
        # CRITICAL FIX: Use safe Unicode slicing for logging
        response_final_preview = safe_unicode_slice(response, 200) if response else 'None'
        raw_response_preview = safe_unicode_slice(raw_response, 200) if raw_response else 'None'
        final_response_final_preview = safe_unicode_slice(final_response, 200) if final_response else 'None'
        
        # CRITICAL: Special logging for Chinese language
        if detected_lang == "zh":
            logger.info(
                f"🔍 [TRACE] [CHINESE] Final check before return: "
                f"response_length={len(response) if response else 0}, "
                f"response_preview={response_final_preview}, "
                f"response_type={type(response)}"
            )
        else:
            logger.info(
                f"🔍 [TRACE] Final check before return: "
                f"response={response_final_preview}, "
                f"response_type={type(response)}, response_length={len(response) if response else 0}"
            )
        
        # CRITICAL: Clean response from problematic characters before final validation
        if response and isinstance(response, str):
            original_response_length = len(response)
            response = clean_response_text(response)
            if len(response) != original_response_length:
                logger.warning(
                    f"⚠️ Cleaned response before return: removed {original_response_length - len(response)} "
                    f"problematic characters (detected_lang={detected_lang})"
                )
            
            # CRITICAL: Auto-fix missing line breaks as final defensive check
            response = fix_missing_line_breaks(response)
        
        if not response or not isinstance(response, str) or not response.strip():
            logger.error(
                f"⚠️ Response is None, empty, or invalid before returning ChatResponse - using fallback. "
                f"response={response}, type={type(response)}, detected_lang={detected_lang}"
            )
            logger.error(
                f"⚠️ Debug info: raw_response={raw_response_preview}, "
                f"final_response={final_response_final_preview}"
            )
            logger.error(f"⚠️ Processing steps: {processing_steps[-5:] if len(processing_steps) > 5 else processing_steps}")
            from backend.api.utils.error_detector import get_fallback_message_for_error
            response = get_fallback_message_for_error("generic", detected_lang or "vi")
            processing_steps.append("⚠️ Response validation failed - using fallback message")
        
        # Add timestamp attribution to normal RAG responses for transparency (consistent with external data)
        # Skip if this is an external data response (already has timestamp) or fallback message
        # CRITICAL: Skip for pure philosophical questions (reasoning, not factual claims)
        from backend.api.utils.error_detector import is_fallback_message
        is_fallback = is_fallback_message(response) if response else False
        has_external_data_timestamp = "[Source:" in response or "[Nguồn:" in response
        
        # CRITICAL: Check if this is a self-knowledge question about StillMe's codebase
        # If so, skip timestamp addition (or only add foundational knowledge citation)
        is_self_knowledge_question = False
        if chat_request.message:
            question_lower = chat_request.message.lower()
            codebase_self_patterns = [
                r"codebase.*của.*bạn",
                r"codebase.*of.*you",
                r"codebase.*stillme",
                r"validator.*trong.*codebase",
                r"validator.*in.*codebase",
                r"lớp.*validator.*trong.*codebase",
                r"layer.*validator.*in.*codebase",
                r"bao nhiêu.*lớp.*validator.*codebase",
                r"how many.*layer.*validator.*codebase",
                r"liệt kê.*lớp.*validator.*codebase",
                r"list.*validator.*layer.*codebase"
            ]
            # Note: 're' module is already imported at top level (line 30)
            # Use top-level import to avoid UnboundLocalError
            for pattern in codebase_self_patterns:
                if re.search(pattern, question_lower, re.IGNORECASE):
                    is_self_knowledge_question = True
                    logger.info(f"✅ Self-knowledge question detected - will skip external citations in timestamp")
                    break
        
        # CRITICAL: Skip timestamp addition for philosophical questions (they don't need citations/timestamps)
        # For self-knowledge questions, we still add timestamp but will filter out external citations in add_timestamp_to_response
        should_add_timestamp = not is_fallback and not has_external_data_timestamp and response and not is_philosophical
        if should_add_timestamp:
            try:
                # CRITICAL: Log response state before adding timestamp (especially for Chinese)
                if detected_lang == "zh":
                    logger.debug(
                        f"🔍 [CHINESE] Before add_timestamp_to_response: "
                        f"response_length={len(response) if response else 0}, "
                        f"response_preview={safe_unicode_slice(response, 100) if response else 'None'}"
                    )
                
                # Pass context and user_question to extract source links if available
                # CRITICAL: Pass user_question so add_timestamp_to_response can filter out external citations for self-knowledge questions
                response_before_timestamp = response
                response_after_timestamp = add_timestamp_to_response(
                    response, 
                    detected_lang or "en", 
                    context, 
                    user_question=chat_request.message
                )
                
                # CRITICAL: Validate response after adding timestamp
                if not response_after_timestamp or not isinstance(response_after_timestamp, str) or not response_after_timestamp.strip():
                    logger.error(
                        f"❌ CRITICAL: Response became empty after add_timestamp_to_response "
                        f"(detected_lang={detected_lang}, before_length={len(response_before_timestamp) if response_before_timestamp else 0}), "
                        f"falling back to original response"
                    )
                    response = response_before_timestamp  # Fallback to original
                else:
                    # CRITICAL: Only use timestamp-added response if it's not significantly shorter
                    # If timestamp addition caused significant content loss, fallback to original
                    if len(response_after_timestamp) < len(response_before_timestamp) * 0.9:
                        logger.error(
                            f"❌ CRITICAL: add_timestamp_to_response caused significant content loss "
                            f"(before: {len(response_before_timestamp)}, after: {len(response_after_timestamp)}), "
                            f"falling back to original response"
                        )
                        response = response_before_timestamp
                    else:
                        response = response_after_timestamp
                
                # CRITICAL: Log response state after adding timestamp (especially for Chinese)
                if detected_lang == "zh":
                    logger.debug(
                        f"🔍 [CHINESE] After add_timestamp_to_response: "
                        f"response_length={len(response) if response else 0}, "
                        f"response_preview={safe_unicode_slice(response, 100) if response else 'None'}"
                    )
                else:
                    logger.debug("✅ Added timestamp attribution to RAG response")
            except Exception as e:
                logger.error(
                    f"⚠️ Failed to add timestamp to response (detected_lang={detected_lang}): {e}",
                    exc_info=True
                )
                # CRITICAL: If timestamp addition fails, keep original response (don't lose content)
                # response already contains original value, no need to change
        
        # Time Estimation Integration: Check if user is asking about time estimation
        try:
            from backend.core.time_estimation_intent import detect_time_estimation_intent
            from stillme_core.monitoring import get_estimation_engine, format_self_aware_response
            
            is_time_estimation, task_description = detect_time_estimation_intent(chat_request.message)
            
            if is_time_estimation and task_description and not is_fallback:
                try:
                    estimator = get_estimation_engine()
                    
                    # Determine task type and complexity from query
                    task_type = "learning"  # Default for StillMe chatbot
                    complexity = "moderate"  # Default
                    size = 100  # Default
                    
                    # Try to infer from task description
                    task_lower = task_description.lower()
                    if "learn" in task_lower or "học" in task_lower:
                        task_type = "learning"
                        # Try to extract number of items
                        # Note: 're' module is already imported at top level
                        num_match = re.search(r'(\d+)', task_description)
                        if num_match:
                            size = int(num_match.group(1))
                    elif "validate" in task_lower or "kiểm tra" in task_lower:
                        task_type = "validation"
                    elif "refactor" in task_lower or "migrate" in task_lower:
                        task_type = "refactoring"
                    
                    # Estimate time
                    estimate = estimator.estimate(
                        task_description=task_description,
                        task_type=task_type,
                        complexity=complexity,
                        size=size
                    )
                    
                    # CONTEXTUAL RELEVANCE CHECK: Only add time estimate if it's contextually relevant
                    # Don't add if response is about human learning or general knowledge (not StillMe's task execution)
                    response_lower = response.lower()
                    
                    # Check if response is about human learning (not StillMe's task execution)
                    human_learning_indicators = [
                        "your learning", "your pace", "you can", "you will", "for you",
                        "human learning", "con người học", "bạn học", "người học",
                        "personal", "individual", "your specific", "your cognitive",
                        "hours total", "hours of", "tens to hundreds of hours",
                        "20-50 hours", "50-150 hours", "150-300 hours",
                        "based on general knowledge", "general learning principles",
                        "learning theory", "cognitive psychology"
                    ]
                    
                    is_about_human_learning = any(
                        indicator in response_lower for indicator in human_learning_indicators
                    )
                    
                    # Check if response is about StillMe's task execution (not capabilities)
                    stillme_task_execution_indicators = [
                        "my execution", "my task", "my performance",
                        "i track", "i estimate", "my historical",
                        "stillme thực thi", "stillme ước lượng", "execution time",
                        "task completion", "hoàn thành tác vụ"
                    ]
                    
                    is_about_stillme_task_execution = any(
                        indicator in response_lower for indicator in stillme_task_execution_indicators
                    )
                    
                    # CRITICAL: Exclude capability questions (validation warnings, learning frequency, etc.)
                    # These are about StillMe's features, NOT about task execution time
                    capability_question_indicators = [
                        "validation", "warning", "cảnh báo", "xác thực",
                        "learning frequency", "tần suất", "cập nhật",
                        "timestamp", "thời điểm", "source", "nguồn",
                        "confidence score", "điểm tin cậy", "threshold", "ngưỡng",
                        "capability", "tính năng", "khả năng", "hệ thống học",
                        "how does stillme", "stillme hiển thị", "stillme cung cấp",
                        "stillme sẽ", "stillme tuyên bố"
                    ]
                    
                    is_capability_question = any(
                        indicator in chat_request.message.lower() for indicator in capability_question_indicators
                    )
                    
                    # Decision: Add estimate only if:
                    # 1. User explicitly asked about time estimation (is_time_estimation is True), AND
                    # 2. Response is about StillMe's task execution (not capabilities), AND
                    # 3. Question is NOT about StillMe's capabilities/features
                    should_add_estimate = (
                        is_time_estimation and  # User asked about time estimation
                        is_about_stillme_task_execution and  # Response is about task execution
                        not is_capability_question  # Question is NOT about capabilities
                    )
                    
                    if should_add_estimate:
                        # Determine language for time estimate
                        # Check if response is in Vietnamese (even if detected_lang was wrong)
                        is_vietnamese_response = (
                            "tiếng việt" in response_lower or
                            "vietnamese" in response_lower or
                            any(char in "àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ" for char in response)
                        )
                        estimate_language = "vi" if (detected_lang == "vi" or is_vietnamese_response) else "en"
                        
                        # Format with AI identity in correct language
                        estimate_text = format_self_aware_response(estimate, include_identity=True, language=estimate_language)
                        
                        if estimate_language == "vi":
                            response = f"{response}\n\n---\n\n⏱️ **Ước tính thời gian:**\n{estimate_text}"
                        else:
                            response = f"{response}\n\n---\n\n⏱️ **Time Estimate:**\n{estimate_text}"
                        
                        logger.info(f"✅ Added time estimation to response: {task_description}")
                    else:
                        logger.info(f"⏭️ Skipped time estimation: Response is about human learning, not StillMe's task execution")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to add time estimation: {e}")
        except ImportError as e:
            logger.debug(f"Time estimation not available: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Error in time estimation integration: {e}")
        
        # Calculate epistemic state (after validation, before returning response)
        from backend.core.epistemic_state import calculate_epistemic_state, EpistemicState
        try:
            # Extract context_docs_count from context or validation_info
            ctx_docs_count = 0
            max_similarity = None  # TRUST-EFFICIENT: Extract max_similarity for accurate epistemic state
            if context and isinstance(context, dict):
                ctx_docs_count = context.get("total_context_docs", 0)
                # Extract max_similarity from knowledge_docs
                knowledge_docs = context.get("knowledge_docs", [])
                if knowledge_docs:
                    similarity_scores = []
                    for doc in knowledge_docs:
                        if isinstance(doc, dict):
                            similarity_scores.append(doc.get('similarity', 0.0))
                        elif hasattr(doc, 'similarity'):
                            similarity_scores.append(doc.similarity if isinstance(doc.similarity, (int, float)) else 0.0)
                        else:
                            similarity_scores.append(0.0)
                    if similarity_scores:
                        max_similarity = max(similarity_scores)
            elif validation_info and isinstance(validation_info, dict):
                ctx_docs_count = validation_info.get("context_docs_count", 0)
            
            epistemic_state = calculate_epistemic_state(
                validation_info=validation_info,
                confidence_score=confidence_score,
                response_text=response,
                context_docs_count=ctx_docs_count,
                max_similarity=max_similarity  # TRUST-EFFICIENT: Pass similarity for accurate state
            )
            confidence_str = f"{confidence_score:.2f}" if confidence_score else 'N/A'
            similarity_str = f"{max_similarity:.3f}" if max_similarity is not None else 'N/A'
            
            # MANIFESTO ALIGNMENT: Calculate Transparency Scorecard
            # Based on StillMe Manifesto Principle 6: "LOG EVERYTHING BECAUSE SECRETS CORRUPT TRUST"
            try:
                from backend.utils.transparency_scorecard import get_transparency_scorer
                from backend.utils.citation_formatter import get_citation_formatter
                from backend.core.epistemic_reasoning import get_epistemic_reasoning
                
                transparency_scorer = get_transparency_scorer()
                citation_formatter = get_citation_formatter()
                
                # Extract citation from response
                citation = None
                if response:
                    # Try to find citation in response
                    # Note: 're' module is already imported at top level
                    cite_pattern = re.compile(r'\[([^\]]+)\]')
                    matches = cite_pattern.findall(response)
                    if matches:
                        citation = f"[{matches[-1]}]"  # Use last citation found
                
                # Count validators that ran
                validators_run = 12  # Default: assume all validators
                if validation_info and isinstance(validation_info, dict):
                    # Try to infer from validation reasons
                    reasons = validation_info.get("reasons", [])
                    # If no critical failures, assume most validators ran
                    if validation_info.get("passed", False):
                        validators_run = 12
                    else:
                        # Some validators may have been skipped
                        validators_run = max(8, 12 - len([r for r in reasons if "timeout" in r.lower() or "skipped" in r.lower()]))
                
                # Check for epistemic explanation
                has_epistemic_explanation = False
                has_uncertainty_expression = False
                if response:
                    response_lower = response.lower()
                    # Check for epistemic reasoning patterns
                    epistemic_patterns = [
                        "vì:", "because:", "do", "bởi vì", "nguyên nhân",
                        "limited context", "conflicting", "outdated", "low similarity"
                    ]
                    has_epistemic_explanation = any(pattern in response_lower for pattern in epistemic_patterns)
                    
                    # Check for uncertainty expression
                    uncertainty_patterns = [
                        "không chắc", "uncertain", "not certain", "don't know",
                        "không có đủ", "sufficient information"
                    ]
                    has_uncertainty_expression = any(pattern in response_lower for pattern in uncertainty_patterns)
                
                # Calculate scorecard
                scorecard = transparency_scorer.calculate_scorecard(
                    citation=citation,
                    validators_run=validators_run,
                    validators_total=12,
                    has_epistemic_explanation=has_epistemic_explanation,
                    has_uncertainty_expression=has_uncertainty_expression,
                    log_count=15,  # Approximate log count (can be improved)
                    expected_logs=15
                )
                
                overall_score = scorecard.calculate_overall()
                scorecard_dict = scorecard.to_dict()
                
                logger.info(
                    f"📊 Transparency Scorecard: {overall_score:.1%} "
                    f"(citation={scorecard.citation_specificity:.2f}, "
                    f"validation={scorecard.validation_completeness:.2f}, "
                    f"epistemic={scorecard.epistemic_honesty:.2f}, "
                    f"traceability={scorecard.process_traceability:.2f})"
                )
                
                # Add to validation_info for API response
                if validation_info:
                    validation_info["transparency_scorecard"] = scorecard_dict
            except Exception as e:
                logger.warning(f"⚠️ Could not calculate transparency scorecard: {e}")
            
            logger.info(f"📊 EpistemicState: {epistemic_state.value} (confidence={confidence_str}, ctx_docs={ctx_docs_count}, max_similarity={similarity_str})")
        except Exception as e:
            logger.warning(f"⚠️ Failed to calculate epistemic state: {e}, defaulting to UNKNOWN")
            epistemic_state = EpistemicState.UNKNOWN
        
        # End decision logging session
        if 'decision_logger' in locals() and decision_logger.current_session:
            final_outcome = f"Response generated with confidence={confidence_score:.2f}, epistemic_state={epistemic_state.value if epistemic_state else 'UNKNOWN'}"
            decision_logger.end_session(final_outcome)
        
        return ChatResponse(
            response=response,
            message_id=message_id,
            context_used=context,
            accuracy_score=accuracy_score,
            confidence_score=confidence_score,
            validation_info=validation_info,
            learning_suggestions=learning_suggestions,
            learning_session_id=learning_session_id,
            knowledge_alert=knowledge_alert,
            learning_proposal=learning_proposal,  # Learning proposal (if valuable knowledge detected)
            permission_request=permission_request,  # Permission request message
            timing=timing_logs,
            latency_metrics=latency_metrics_text,  # BẮT BUỘC HIỂN THỊ LOG trong response cho frontend
            processing_steps=processing_steps,  # Real-time processing steps for status indicator
            epistemic_state=epistemic_state.value if epistemic_state else None  # Epistemic state: KNOWN/UNCERTAIN/UNKNOWN
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (they have proper status codes)
        raise
    except RateLimitExceeded:
        # Re-raise rate limit exceptions so global handler can return proper 429 status
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


@router.post("/smart_router", response_model=ChatResponse)
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
    except RateLimitExceeded:
        # Re-raise rate limit exceptions so global handler can return proper 429 status
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
@router.post("/openai")
async def chat_openai(request: ChatRequest):
    """Legacy OpenAI chat endpoint"""
    # Create a dummy Request object for chat_with_rag
    # Note: This is a workaround - in production, we should refactor to not require Request
    class DummyRequest:
        pass
    dummy_request = DummyRequest()
    return await chat_with_rag(dummy_request, request)


@router.post("/deepseek")
async def chat_deepseek(request: ChatRequest):
    """Legacy DeepSeek chat endpoint"""
    # Create a dummy Request object for chat_with_rag
    class DummyRequest:
        pass
    dummy_request = DummyRequest()
    return await chat_with_rag(dummy_request, request)


@router.post("/ask", response_model=ChatResponse)
@limiter.limit(get_chat_rate_limit, key_func=get_rate_limit_key_func)  # Chat rate limit (dynamic based on API key)
async def ask_question(request: Request, chat_request: ChatRequest):
    """
    Simplified question-answering endpoint.
    Alias for /rag endpoint with RAG enabled by default.
    
    This endpoint is designed for simple Q&A use cases where RAG context
    is always desired. It's a convenience wrapper around the full RAG chat endpoint.
    """
    # Ensure RAG is enabled for /ask endpoint
    chat_request.use_rag = True
    # Use default context limit if not specified
    if chat_request.context_limit is None or chat_request.context_limit < 1:
        chat_request.context_limit = 3
    
    # Delegate to the main RAG chat endpoint
    return await chat_with_rag(request, chat_request)


@router.post("/validate")
@limiter.limit("20/minute", key_func=get_rate_limit_key_func)
async def validate_content(request: Request, chat_request: ChatRequest):
    """
    Standalone content validation endpoint.
    
    Validates user input/question for:
    - Ethical compliance
    - Content safety
    - Format validation
    
    Returns validation result without generating a response.
    This is useful for pre-validation before processing expensive RAG/LLM calls.
    """
    from backend.validators.chain import ValidatorChain
    from backend.validators.citation import CitationRequired
    from backend.validators.evidence_overlap import EvidenceOverlap
    from backend.validators.numeric import NumericUnitsBasic
    from backend.validators.ethics_adapter import EthicsAdapter
    
    try:
        # Get RAG retrieval for context (if needed for validation)
        rag_retrieval = get_rag_retrieval()
        
        # Get context if RAG is enabled
        context_docs = []
        if rag_retrieval and chat_request.use_rag:
            try:
                context = rag_retrieval.retrieve_context(
                    query=chat_request.message,
                    knowledge_limit=min(chat_request.context_limit, 3),  # Limit for validation
                    conversation_limit=0  # Don't need conversation for validation
                )
                context_docs = [
                    doc["content"] for doc in context.get("knowledge_docs", [])
                ]
            except Exception as context_error:
                logger.warning(f"Could not retrieve context for validation: {context_error}")
                context_docs = []
        
        # Create validator chain
        enable_validators = os.getenv("ENABLE_VALIDATORS", "false").lower() == "true"
        
        if enable_validators:
            from backend.services.ethics_guard import check_content_ethics
            chain = ValidatorChain([
                CitationRequired(),  # Not applicable for input, but included for completeness
                EvidenceOverlap(threshold=0.01),
                NumericUnitsBasic(),
                EthicsAdapter(guard_callable=check_content_ethics)  # Real ethics guard implementation
            ])
            
            # Validate the message itself (treating it as "answer" to check)
            # Note: This validates the user input, not a response
            validation_result = chain.run(chat_request.message, context_docs)
            
            # Record metrics
            try:
                from backend.validators.metrics import get_metrics
                metrics = get_metrics()
                metrics.record_validation(
                    passed=validation_result.passed,
                    reasons=validation_result.reasons,
                    overlap_score=0.0  # Not applicable for input validation
                )
            except Exception as metrics_error:
                logger.warning(f"Could not record validation metrics: {metrics_error}")
            
            return {
                "is_valid": validation_result.passed,
                "message": chat_request.message,
                "validation_details": {
                    "passed": validation_result.passed,
                    "reasons": validation_result.reasons,
                    "patched_content": validation_result.patched if hasattr(validation_result, 'patched') else None
                },
                "context_used": {
                    "context_docs_count": len(context_docs),
                    "rag_enabled": chat_request.use_rag
                }
            }
        else:
            # If validators are disabled, do basic validation only
            return {
                "is_valid": True,
                "message": chat_request.message,
                "validation_details": {
                    "passed": True,
                    "reasons": ["Validators disabled - basic format check passed"],
                    "note": "Full validation disabled via ENABLE_VALIDATORS=false"
                },
                "context_used": {
                    "context_docs_count": len(context_docs),
                    "rag_enabled": chat_request.use_rag
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /validate endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Validation error: {str(e)}. Please check backend logs for details."
        )

