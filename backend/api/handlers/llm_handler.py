"""
LLM Handler for StillMe API
Handles LLM call logic with caching, retry, and token management
"""

import logging
import os
import re
import time
from typing import Optional, Dict, Any, List, Tuple

from backend.api.utils.chat_helpers import generate_ai_response
from backend.api.utils.llm_providers import ContextOverflowError
from backend.api.utils.error_detector import (
    is_fallback_message,
    is_technical_error,
    get_fallback_message_for_error
)
from backend.services.cache_service import get_cache_service, CACHE_PREFIX_LLM, TTL_LLM_RESPONSE
from backend.api.handlers.prompt_builder import build_minimal_philosophical_prompt

logger = logging.getLogger(__name__)


def _estimate_tokens(text: str) -> int:
    """
    Estimate token count more accurately (~3.5 chars per token for mixed content).
    
    Args:
        text: Text to estimate tokens for
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
    # More accurate estimation: Vietnamese/English mixed content ~3.5 chars/token
    # Pure English ~4 chars/token, Vietnamese ~3 chars/token
    return int(len(text) / 3.5)


def _pre_check_token_limit(
    enhanced_prompt: str,
    context_text: Optional[str],
    is_philosophical: bool,
    detected_lang: str,
    detected_lang_name: str,
    chat_request,
    context: Optional[Dict[str, Any]],
    processing_steps: List[str]
) -> Tuple[str, Optional[str]]:
    """
    Pre-check token count and truncate if needed.
    
    Args:
        enhanced_prompt: The enhanced prompt to check
        context_text: Context text (may be truncated)
        is_philosophical: Whether this is a philosophical question
        detected_lang: Detected language code
        detected_lang_name: Detected language name
        chat_request: Chat request object
        context: Context dict
        processing_steps: List to append processing steps to
        
    Returns:
        tuple: (adjusted_prompt, adjusted_context_text)
    """
    # Estimate total tokens: system prompt + enhanced_prompt + output buffer
    # System prompt is built separately in generate_ai_response() (~3300-3600 tokens)
    system_prompt_buffer = 3600  # Conservative estimate for system prompt
    enhanced_prompt_tokens = _estimate_tokens(enhanced_prompt) if enhanced_prompt else 0
    output_buffer_tokens = 1500  # Reserve for output
    total_estimated_tokens = system_prompt_buffer + enhanced_prompt_tokens + output_buffer_tokens
    
    # OpenRouter limit: 16385 tokens
    # Use safe margin: 15000 tokens max (leave 1385 tokens buffer)
    MAX_SAFE_TOKENS = 15000
    
    # Pre-check: If estimated tokens exceed safe limit, use minimal prompt
    if total_estimated_tokens > MAX_SAFE_TOKENS:
        logger.warning(
            f"⚠️ Pre-check: Estimated tokens ({total_estimated_tokens}) exceed safe limit ({MAX_SAFE_TOKENS}). "
            f"Using minimal prompt to prevent context overflow. "
            f"is_philosophical={is_philosophical}"
        )
        
        if is_philosophical:
            # Use minimal philosophical prompt
            minimal_prompt = build_minimal_philosophical_prompt(
                user_question=chat_request.message,
                language=detected_lang,
                detected_lang_name=detected_lang_name,
                context=context,
                validation_info=None  # Validation hasn't run yet
            )
            logger.info(f"🔄 Using minimal philosophical prompt (pre-check prevention)")
            processing_steps.append("⚠️ Pre-check: Using minimal prompt (token limit)")
            return minimal_prompt, context_text
        else:
            # For non-philosophical, truncate context_text aggressively
            if context_text:
                original_context_length = len(context_text)
                # Truncate to ~2000 tokens max
                max_context_chars = int(2000 * 3.5)  # ~7000 chars
                if original_context_length > max_context_chars:
                    truncated_context = context_text[:max_context_chars].rsplit('\n', 1)[0] + "\n\n[Context truncated to prevent overflow]"
                    logger.warning(f"⚠️ Pre-check: Truncated context_text from {original_context_length} to {len(truncated_context)} chars")
                    # Rebuild enhanced_prompt with truncated context
                    if "Context: " in enhanced_prompt:
                        # Find and replace context section
                        enhanced_prompt = re.sub(
                            r'Context:.*?(?=\n\n|$)',
                            f'Context: {truncated_context}',
                            enhanced_prompt,
                            flags=re.DOTALL
                        )
                        context_text = truncated_context
                    processing_steps.append("⚠️ Pre-check: Truncated context (token limit)")
    
    return enhanced_prompt, context_text


def _check_cache(
    cache_service,
    cache_key: str,
    is_validator_count_question: bool,
    processing_steps: List[str],
    timing_logs: Dict[str, Any]
) -> Tuple[Optional[str], bool, float]:
    """
    Check LLM response cache.
    
    Args:
        cache_service: Cache service instance
        cache_key: Cache key to check
        is_validator_count_question: Whether this is a validator count question (force cache miss)
        processing_steps: List to append processing steps to
        timing_logs: Dict to update timing logs
        
    Returns:
        tuple: (cached_response, cache_hit, latency)
    """
    # CRITICAL: Force cache miss for validator count questions to ensure fresh manifest data
    if is_validator_count_question:
        logger.info("🚫 Force cache miss for validator count question - ensuring fresh manifest data")
        return None, False, 0.0
    
    # Try to get from cache
    cached_response = cache_service.get(cache_key)
    if cached_response:
        cached_raw_response = cached_response.get("response")
        # CRITICAL: Only use cache if response is valid (not None/empty)
        if cached_raw_response and isinstance(cached_raw_response, str) and cached_raw_response.strip():
            # CRITICAL: Check if cached response is a fallback message
            if is_fallback_message(cached_raw_response):
                logger.warning(f"⚠️ Cache contains fallback message - ignoring cache and calling LLM")
                return None, False, 0.0
            else:
                # PHASE 3: Transparent caching - log clearly about cache hit
                saved_time = cached_response.get('latency', 0)
                logger.info(f"✅ Cache hit for similar query, skipped LLM call (saved {saved_time:.2f}s)")
                logger.info(f"🔍 [TRACE] Cached response: length={len(cached_raw_response)}, preview={cached_raw_response[:200]}")
                processing_steps.append("⚡ Response from cache (fast!)")
                latency = cached_response.get("latency", 0.01)
                timing_logs["llm_inference"] = f"{latency:.2f}s (cached)"
                # PHASE 3: Note that validation will still run (transparency)
                logger.debug("💡 PHASE 3: Validation chain will still run on cached response for quality assurance")
                return cached_raw_response, True, latency
        else:
            # Cache contains invalid response (None/empty) - ignore cache and call LLM
            logger.warning(f"⚠️ Cache contains invalid response (None/empty), ignoring cache and calling LLM")
            return None, False, 0.0
    
    return None, False, 0.0


def _store_cache(
    cache_service,
    cache_key: str,
    response: str,
    latency: float,
    cache_ttl_override: Optional[int],
    is_validator_count_question: bool
):
    """
    Store LLM response in cache.
    
    Args:
        cache_service: Cache service instance
        cache_key: Cache key to store
        response: Response to cache
        latency: LLM inference latency
        cache_ttl_override: Custom TTL override (None for default)
        is_validator_count_question: Whether this is a validator count question (skip cache)
    """
    # CRITICAL: Don't cache validator count questions - they need fresh manifest data
    if is_validator_count_question:
        logger.debug("🚫 Skipping cache for validator count question - requires fresh manifest data")
        return
    
    try:
        cache_value = {
            "response": response,
            "latency": latency,
            "timestamp": time.time()
        }
        # Use custom TTL if specified (e.g., 1h for self-reflection), otherwise use default
        ttl_to_use = cache_ttl_override if cache_ttl_override is not None else TTL_LLM_RESPONSE
        cache_service.set(cache_key, cache_value, ttl_seconds=ttl_to_use)
        logger.debug(f"💾 LLM response cached (key: {cache_key[:50]}..., TTL: {ttl_to_use}s)")
    except Exception as cache_error:
        logger.warning(f"Failed to cache LLM response: {cache_error}")


async def _call_llm_with_retry(
    enhanced_prompt: str,
    detected_lang: str,
    chat_request,
    use_server_keys: bool,
    is_philosophical: bool,
    context: Optional[Dict[str, Any]],
    detected_lang_name: str,
    processing_steps: List[str]
) -> str:
    """
    Call LLM with retry on context overflow.
    
    Args:
        enhanced_prompt: Enhanced prompt to send
        detected_lang: Detected language code
        chat_request: Chat request object
        use_server_keys: Whether to use server API keys
        is_philosophical: Whether this is a philosophical question
        context: Context dict
        detected_lang_name: Detected language name
        processing_steps: List to append processing steps to
        
    Returns:
        LLM response string
    """
    try:
        raw_response = await generate_ai_response(
            enhanced_prompt,
            detected_lang=detected_lang,
            llm_provider=chat_request.llm_provider,
            llm_api_key=chat_request.llm_api_key,
            llm_api_url=chat_request.llm_api_url,
            llm_model_name=chat_request.llm_model_name,
            use_server_keys=use_server_keys,
            question=chat_request.message,
            task_type="chat",
            is_philosophical=is_philosophical
        )
        return raw_response
    except ContextOverflowError as e:
        # Context overflow - rebuild prompt with minimal context (ultra-thin mode)
        logger.warning(f"⚠️ Context overflow detected: {e}. Rebuilding prompt with minimal context...")
        
        if is_philosophical:
            # Use minimal philosophical prompt helper
            minimal_prompt = build_minimal_philosophical_prompt(
                user_question=chat_request.message,
                language=detected_lang,
                detected_lang_name=detected_lang_name,
                context=context,
                validation_info=None  # Validation hasn't run yet in retry path
            )
            
            logger.info(f"🔄 Retrying with minimal philosophical prompt (no history, no RAG, no metrics, no provenance)")
            try:
                raw_response = await generate_ai_response(
                    minimal_prompt,
                    detected_lang=detected_lang,
                    llm_provider=chat_request.llm_provider,
                    llm_api_key=chat_request.llm_api_key,
                    llm_api_url=chat_request.llm_api_url,
                    llm_model_name=chat_request.llm_model_name,
                    use_server_keys=use_server_keys
                )
                logger.info(f"✅ Successfully generated response with minimal philosophical prompt")
                return raw_response
            except ContextOverflowError as retry_error:
                # Even minimal prompt failed - return fallback message
                logger.error(f"⚠️ Even minimal prompt failed: {retry_error}")
                return get_fallback_message_for_error("context_overflow", detected_lang)
        else:
            # For non-philosophical, return fallback message
            logger.warning(f"⚠️ Context overflow for non-philosophical question - using fallback message")
            return get_fallback_message_for_error("context_overflow", detected_lang)


async def generate_llm_response(
    enhanced_prompt: str,
    detected_lang: str,
    chat_request,
    context: Optional[Dict[str, Any]],
    is_philosophical: bool,
    is_validator_count_question: bool,
    is_origin_query: bool,
    is_stillme_query: bool,
    detected_lang_name: str,
    context_text: Optional[str],
    enable_validators: bool,
    use_option_b: bool,
    fps_result: Optional[Any],
    processing_steps: List[str],
    timing_logs: Dict[str, Any]
) -> Tuple[str, bool, float]:
    """
    Generate LLM response with caching and retry logic.
    
    Args:
        enhanced_prompt: Enhanced prompt to send
        detected_lang: Detected language code
        chat_request: Chat request object
        context: Context dict
        is_philosophical: Whether this is a philosophical question
        is_validator_count_question: Whether this is a validator count question
        is_origin_query: Whether this is an origin query
        is_stillme_query: Whether this is a StillMe query
        detected_lang_name: Detected language name
        context_text: Context text
        enable_validators: Whether validators are enabled
        use_option_b: Whether Option B pipeline is enabled
        fps_result: FPS result (for Option B)
        processing_steps: List to append processing steps to
        timing_logs: Dict to update timing logs
        
    Returns:
        tuple: (raw_response, cache_hit, llm_inference_latency)
    """
    provider_name = chat_request.llm_provider or "default"
    
    # Phase 1: LLM Response Cache - Check cache first
    # CRITICAL: Disable cache for origin queries to ensure provenance context is retrieved
    cache_service = get_cache_service()
    cache_enabled = os.getenv("ENABLE_LLM_CACHE", "true").lower() == "true"
    if is_origin_query:
        cache_enabled = False
        logger.info("⚠️ Cache disabled for origin query - ensuring fresh response with provenance context")
    
    # P3: Conditional cache for StillMe queries with knowledge versioning
    cache_ttl_override = None
    if is_stillme_query:
        question_lower = chat_request.message.lower()
        is_self_reflection = any(
            pattern in question_lower
            for pattern in [
                "điểm yếu", "weakness", "limitation", "hạn chế", "chí tử",
                "chỉ ra điểm yếu", "chỉ ra hạn chế", "what are your weaknesses"
            ]
        )
        
        if is_self_reflection:
            cache_ttl_override = 3600  # 1 hour
            logger.info("💾 P3: Caching StillMe self-reflection question with 1h TTL (knowledge version included in cache key)")
        elif context and context.get("knowledge_docs"):
            has_foundational = any(
                doc.get("metadata", {}).get("source") == "CRITICAL_FOUNDATION" or
                doc.get("metadata", {}).get("foundational") == "stillme" or
                doc.get("metadata", {}).get("type") == "foundational" or
                "CRITICAL_FOUNDATION" in str(doc.get("metadata", {}).get("tags", "")) or
                "foundational:stillme" in str(doc.get("metadata", {}).get("tags", ""))
                for doc in context.get("knowledge_docs", [])
            )
            if has_foundational:
                logger.info("💾 PHASE 3: Caching StillMe query with foundational knowledge (knowledge version included in cache key)")
    
    raw_response = None
    cache_hit = False
    llm_inference_latency = 0.0
    
    if cache_enabled:
        # P3: Include knowledge version in cache key for intelligent cache invalidation
        from backend.services.knowledge_version import get_knowledge_version
        knowledge_version = get_knowledge_version()
        
        # Generate cache key from query + context + settings + knowledge version
        cache_key = cache_service._generate_key(
            CACHE_PREFIX_LLM,
            chat_request.message,
            enhanced_prompt[:500] if len(enhanced_prompt) > 500 else enhanced_prompt,
            detected_lang,
            chat_request.llm_provider,
            chat_request.llm_model_name,
            enable_validators,
            knowledge_version=knowledge_version
        )
        
        # Check cache
        cached_response, cache_hit, cached_latency = _check_cache(
            cache_service,
            cache_key,
            is_validator_count_question,
            processing_steps,
            timing_logs
        )
        
        if cache_hit:
            raw_response = cached_response
            llm_inference_latency = cached_latency
    
    # If not in cache, call LLM
    if not raw_response:
        logger.debug(f"🔍 About to call LLM - raw_response is None, cache_hit={cache_hit}, cache_enabled={cache_enabled}")
        processing_steps.append(f"🤖 Calling AI model ({provider_name})...")
        llm_inference_start = time.time()
        
        # Support user-provided LLM config (for self-hosted deployments)
        use_server_keys = chat_request.llm_provider is None
        
        # Pre-check token limit and adjust prompt if needed
        enhanced_prompt, context_text = _pre_check_token_limit(
            enhanced_prompt,
            context_text,
            is_philosophical,
            detected_lang,
            detected_lang_name,
            chat_request,
            context,
            processing_steps
        )
        
        try:
            # OPTION B PIPELINE: Check if enabled
            if use_option_b:
                logger.info("🚀 Option B Pipeline enabled - processing with zero-tolerance hallucination + deep philosophy")
                processing_steps.append("🚀 Option B Pipeline: Enabled")
                
                from backend.core.option_b_pipeline import process_llm_response_with_option_b
                from backend.core.question_classifier_v2 import get_question_classifier_v2
                
                # Classify question
                classifier = get_question_classifier_v2()
                question_type_result, confidence, _ = classifier.classify(chat_request.message)
                question_type_str = question_type_result.value
                
                # Generate LLM response (Step 4)
                raw_response = await generate_ai_response(
                    enhanced_prompt,
                    detected_lang=detected_lang,
                    llm_provider=chat_request.llm_provider,
                    llm_api_key=chat_request.llm_api_key,
                    llm_api_url=chat_request.llm_api_url,
                    llm_model_name=chat_request.llm_model_name,
                    use_server_keys=use_server_keys,
                    question=chat_request.message,
                    task_type="chat",
                    is_philosophical=is_philosophical
                )
                
                # Validate raw_response
                if not raw_response or not isinstance(raw_response, str) or not raw_response.strip():
                    logger.error("⚠️ Option B: LLM returned empty response")
                    raw_response = get_fallback_message_for_error("generic", detected_lang)
                
                # Step 5-8: Post-LLM processing (Hallucination Guard V2, Rewrite 1, Rewrite 2)
                option_b_result = await process_llm_response_with_option_b(
                    llm_response=raw_response,
                    question=chat_request.message,
                    question_type=question_type_str,
                    ctx_docs=context.get("knowledge_docs", []) if context else [],
                    detected_lang=detected_lang,
                    fps_result=fps_result
                )
                
                # Use Option B processed response
                raw_response = option_b_result["response"]
                processing_steps.extend(option_b_result.get("processing_steps", []))
                timing_logs.update(option_b_result.get("timing_logs", {}))
                logger.info(f"✅ Option B Pipeline completed: {len(option_b_result.get('processing_steps', []))} steps")
            else:
                # EXISTING PIPELINE (legacy)
                raw_response = await _call_llm_with_retry(
                    enhanced_prompt,
                    detected_lang,
                    chat_request,
                    use_server_keys,
                    is_philosophical,
                    context,
                    detected_lang_name,
                    processing_steps
                )
            
            # CRITICAL: Log raw_response immediately after LLM call
            logger.info(
                f"🔍 DEBUG Q1/Q2/Q7/Q9: LLM call completed. "
                f"raw_response type={type(raw_response)}, "
                f"is None={raw_response is None}, "
                f"is str={isinstance(raw_response, str)}, "
                f"length={len(raw_response) if raw_response else 0}, "
                f"preview={raw_response[:200] if raw_response else 'None'}"
            )
            
            # CRITICAL: Check if raw_response is an error message BEFORE validation
            if raw_response and isinstance(raw_response, str):
                is_error, error_type = is_technical_error(raw_response)
                if is_error:
                    logger.error(
                        f"❌ LLM returned technical error as response (type: {error_type}): {raw_response[:200]}. "
                        f"Full response length: {len(raw_response)}, Question: {chat_request.message[:100]}"
                    )
                    raw_response = get_fallback_message_for_error(error_type, detected_lang)
                    processing_steps.append(f"⚠️ LLM returned technical error - replaced with fallback message")
            
            # CRITICAL: Validate raw_response immediately after LLM call
            if not raw_response or not isinstance(raw_response, str) or not raw_response.strip():
                logger.error(
                    f"⚠️ LLM returned None or empty response for question: {chat_request.message[:100]}"
                )
                raw_response = get_fallback_message_for_error("generic", detected_lang)
                processing_steps.append("⚠️ LLM returned empty response - using fallback")
        except ValueError as ve:
            # ValueError from generate_ai_response (missing API keys, etc.)
            error_msg = str(ve)
            logger.error(f"❌ ValueError from generate_ai_response: {error_msg}")
            
            # Check if it's a missing API key error
            if "llm_provider" in error_msg.lower() or "api_key" in error_msg.lower() or "api key" in error_msg.lower():
                has_server_keys = bool(
                    os.getenv('DEEPSEEK_API_KEY') or
                    os.getenv('OPENAI_API_KEY') or
                    os.getenv('OPENROUTER_API_KEY')
                )
                logger.error(
                    f"❌ CRITICAL: Missing LLM API keys! "
                    f"use_server_keys={use_server_keys}, "
                    f"llm_provider={chat_request.llm_provider}, "
                    f"has_server_keys={has_server_keys}"
                )
                # Provide more helpful error message when no server keys found
                if not has_server_keys:
                    raw_response = (
                        f"⚠️ Lỗi cấu hình: Backend cần có API keys trong file .env để hoạt động. "
                        f"Vui lòng thêm ít nhất một trong các keys sau vào file .env: "
                        f"DEEPSEEK_API_KEY, OPENAI_API_KEY, hoặc OPENROUTER_API_KEY. "
                        f"Chi tiết: {error_msg}"
                    )
                else:
                    raw_response = get_fallback_message_for_error("api_error", detected_lang)
                processing_steps.append("⚠️ Missing API keys - cannot generate response")
            else:
                raw_response = get_fallback_message_for_error("generic", detected_lang)
                processing_steps.append("⚠️ LLM configuration error - using fallback message")
        except Exception as e:
            # Catch any other unexpected exceptions
            logger.error(f"❌ Unexpected exception from generate_ai_response: {e}", exc_info=True)
            raw_response = get_fallback_message_for_error("generic", detected_lang)
            processing_steps.append("⚠️ LLM call exception - using fallback message")
        
        llm_inference_end = time.time()
        llm_inference_latency = llm_inference_end - llm_inference_start
        timing_logs["llm_inference"] = f"{llm_inference_latency:.2f}s"
        
        # CRITICAL: Only log "AI response generated" if we actually have a response
        if raw_response and isinstance(raw_response, str) and raw_response.strip():
            logger.info(f"⏱️ LLM inference took {llm_inference_latency:.2f}s")
            processing_steps.append(f"✅ AI response generated ({llm_inference_latency:.2f}s)")
            logger.debug(f"🔍 DEBUG: raw_response preview (first 200 chars): {raw_response[:200]}")
        else:
            logger.warning(
                f"⚠️ LLM inference failed or returned empty (took {llm_inference_latency:.2f}s). "
                f"raw_response type={type(raw_response)}, value={raw_response[:200] if raw_response else 'None'}"
            )
            # Ensure raw_response is set to fallback message if still None/empty
            if not raw_response or not isinstance(raw_response, str) or not raw_response.strip():
                raw_response = get_fallback_message_for_error("generic", detected_lang)
                processing_steps.append("⚠️ LLM failed - using fallback message")
                logger.warning(f"⚠️ Set raw_response to fallback message: {raw_response[:200]}")
        
        # Save to cache (only if not a cache hit and not a validator count question)
        if cache_enabled and not cache_hit and not is_validator_count_question:
            _store_cache(
                cache_service,
                cache_key,
                raw_response,
                llm_inference_latency,
                cache_ttl_override,
                is_validator_count_question
            )
    
    return raw_response, cache_hit, llm_inference_latency

