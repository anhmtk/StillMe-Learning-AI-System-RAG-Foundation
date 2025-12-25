"""
Post-processing handler for chat responses.

This module handles response sanitization, quality evaluation, rewriting,
and citation preservation after rewrite.
"""

import logging
import re
import time
from typing import Optional, Dict, Any, List, Tuple

from backend.api.config.chat_config import get_chat_config
from backend.api.utils.text_utils import safe_unicode_slice
from backend.api.utils.error_detector import is_technical_error, is_fallback_message, get_fallback_message_for_error

logger = logging.getLogger(__name__)


async def process_response(
    raw_response: str,
    context: Optional[Dict[str, Any]],
    detected_lang: str,
    is_philosophical: bool,
    is_stillme_query: bool,
    chat_request,
    validation_info: Optional[Dict[str, Any]],
    processing_steps: List[str],
    timing_logs: Dict[str, Any],
    ctx_docs: Optional[List[str]] = None
) -> Tuple[str, float]:
    """
    Process response through sanitization, evaluation, and rewriting.
    
    Args:
        raw_response: The raw LLM response
        context: RAG context dictionary
        detected_lang: Detected language code
        is_philosophical: Whether this is a philosophical question
        is_stillme_query: Whether this is a StillMe self-knowledge query
        chat_request: ChatRequest object
        validation_info: Validation result dictionary
        processing_steps: List to append processing steps
        timing_logs: Dictionary to log timing information
        ctx_docs: Context documents list (optional, for backward compatibility)
    
    Returns:
        tuple: (final_response, postprocessing_time)
    """
    postprocessing_start = time.time()
    
    try:
        from backend.postprocessing.style_sanitizer import get_style_sanitizer
        from backend.postprocessing.quality_evaluator import get_quality_evaluator
        from backend.postprocessing.rewrite_llm import get_rewrite_llm
        from backend.postprocessing.optimizer import get_postprocessing_optimizer
        
        optimizer = get_postprocessing_optimizer()
        
        # OPTIMIZATION: Check if we should skip post-processing
        should_skip, skip_reason = optimizer.should_skip_postprocessing(
            question=chat_request.message,
            response=raw_response,
            is_philosophical=is_philosophical
        )
        
        if should_skip:
            logger.info(f"⏭️ Skipping post-processing: {skip_reason}")
            timing_logs["postprocessing"] = "skipped"
            return raw_response, 0.0
        
        # Stage 2: Hard Filter (0 token) - Style Sanitization
        sanitized_response = _sanitize_response(
            response=raw_response,
            is_philosophical=is_philosophical,
            detected_lang=detected_lang
        )
        
        # CRITICAL: Check if sanitized response is a technical error or fallback message
        is_error, error_type = is_technical_error(sanitized_response)
        is_fallback = is_fallback_message(sanitized_response)
        
        if is_error or is_fallback:
            if is_error:
                logger.warning(
                    f"⚠️ Technical error detected in sanitized response (type: {error_type}), "
                    f"skipping quality evaluation and rewrite"
                )
                processing_steps.append(f"⚠️ Technical error detected - skipping post-processing")
            else:
                logger.info(
                    f"🛑 Fallback meta-answer detected in sanitized response, "
                    f"skipping quality evaluation and rewrite"
                )
                processing_steps.append(f"🛑 Fallback message detected - skipping post-processing")
            
            postprocessing_time = time.time() - postprocessing_start
            timing_logs["postprocessing"] = f"{postprocessing_time:.3f}s"
            return sanitized_response, postprocessing_time
        
        # Build context docs for rewrite
        ctx_docs_for_rewrite, has_reliable_context_for_rewrite, context_quality_for_rewrite, has_foundational_context = _build_ctx_docs_for_rewrite(
            context=context,
            ctx_docs=ctx_docs,
            is_stillme_query=is_stillme_query
        )
        
        # Stage 3: Quality Evaluator (0 token) - Rule-based Quality Check
        quality_result = _evaluate_response_quality(
            sanitized_response=sanitized_response,
            is_philosophical=is_philosophical,
            chat_request=chat_request,
            optimizer=optimizer,
            is_stillme_query=is_stillme_query
        )
        
        # Stage 4: Conditional rewrite with cost-benefit logic
        final_response = await _rewrite_response(
            sanitized_response=sanitized_response,
            quality_result=quality_result,
            context=context,
            ctx_docs_for_rewrite=ctx_docs_for_rewrite,
            has_reliable_context_for_rewrite=has_reliable_context_for_rewrite,
            context_quality_for_rewrite=context_quality_for_rewrite,
            has_foundational_context=has_foundational_context,
            detected_lang=detected_lang,
            is_philosophical=is_philosophical,
            is_stillme_query=is_stillme_query,
            chat_request=chat_request,
            validation_info=validation_info,
            processing_steps=processing_steps
        )
        
        # CRITICAL: Ensure citations are preserved after rewrite
        final_response = _re_add_citations_after_rewrite(
            final_response=final_response,
            context=context,
            ctx_docs_for_rewrite=ctx_docs_for_rewrite,
            is_philosophical=is_philosophical,
            chat_request=chat_request
        )
        
        # CRITICAL: Final check - ensure response is not a technical error
        if final_response:
            is_error, error_type = is_technical_error(final_response)
            if is_error:
                logger.error(f"⚠️ Final response is still a technical error (type: {error_type}) - replacing with fallback")
                final_response = get_fallback_message_for_error(error_type, detected_lang)
        
        # CRITICAL: Defensive check - ensure response is not empty after post-processing
        if not final_response or not isinstance(final_response, str) or not final_response.strip():
            logger.error(
                f"❌ CRITICAL: Response became empty after post-processing "
                f"(is_philosophical={is_philosophical}, detected_lang={detected_lang}), "
                f"falling back to raw_response"
            )
            final_response = raw_response if raw_response and raw_response.strip() else get_fallback_message_for_error("generic", detected_lang)
        
        postprocessing_time = time.time() - postprocessing_start
        timing_logs["postprocessing"] = f"{postprocessing_time:.3f}s"
        logger.info(f"⏱️ Post-processing took {postprocessing_time:.3f}s")
        
        return final_response, postprocessing_time
        
    except Exception as postprocessing_error:
        logger.error(f"Post-processing error: {postprocessing_error}", exc_info=True)
        # Fallback to original response if post-processing fails
        logger.warning(f"⚠️ Post-processing failed, using original response")
        timing_logs["postprocessing"] = "failed"
        postprocessing_time = time.time() - postprocessing_start
        return raw_response, postprocessing_time


def _sanitize_response(
    response: str,
    is_philosophical: bool,
    detected_lang: str
) -> str:
    """
    Sanitize response text with defensive checks.
    
    Args:
        response: Raw response text
        is_philosophical: Whether this is a philosophical question
        detected_lang: Detected language code
    
    Returns:
        Sanitized response text
    """
    from backend.postprocessing.style_sanitizer import get_style_sanitizer
    
    sanitizer = get_style_sanitizer()
    
    # CRITICAL: Log response state before sanitization (especially for Chinese/philosophical)
    if is_philosophical or detected_lang == "zh":
        logger.info(
            f"🔍 [SANITIZE TRACE] Before sanitize: "
            f"response_length={len(response) if response else 0}, "
            f"is_philosophical={is_philosophical}, "
            f"detected_lang={detected_lang}, "
            f"preview={safe_unicode_slice(response, 200) if response else 'None'}"
        )
    
    sanitized_response = sanitizer.sanitize(response, is_philosophical=is_philosophical)
    
    # CRITICAL: Log response state after sanitization (especially for Chinese/philosophical)
    if is_philosophical or detected_lang == "zh":
        logger.info(
            f"🔍 [SANITIZE TRACE] After sanitize: "
            f"response_length={len(response) if response else 0}, "
            f"sanitized_length={len(sanitized_response) if sanitized_response else 0}, "
            f"removed={len(response) - len(sanitized_response) if response and sanitized_response else 0} chars, "
            f"is_philosophical={is_philosophical}, "
            f"detected_lang={detected_lang}, "
            f"preview={safe_unicode_slice(sanitized_response, 200) if sanitized_response else 'None'}"
        )
    
    # CRITICAL: Ensure sanitized_response is not empty (defensive check)
    if not sanitized_response or not sanitized_response.strip():
        logger.warning(
            f"⚠️ Sanitized response is empty (original length: {len(response) if response else 0}), "
            f"falling back to original response"
        )
        sanitized_response = response
    # CRITICAL: If sanitize() removed more than 50% of content, it's likely wrong - fallback to original
    elif response and len(sanitized_response) < len(response) * 0.5:
        logger.error(
            f"❌ CRITICAL: sanitize() removed more than 50% of content "
            f"(original: {len(response)}, sanitized: {len(sanitized_response)}, "
            f"removed: {len(response) - len(sanitized_response)} chars, "
            f"{100 * (len(response) - len(sanitized_response)) / len(response):.1f}%). "
            f"Falling back to original response. "
            f"Preview original: {safe_unicode_slice(response, 200)}, "
            f"Preview sanitized: {safe_unicode_slice(sanitized_response, 200)}"
        )
        sanitized_response = response  # Fallback to original
    
    return sanitized_response


def _build_ctx_docs_for_rewrite(
    context: Optional[Dict[str, Any]],
    ctx_docs: Optional[List[str]],
    is_stillme_query: bool
) -> Tuple[List[str], bool, Optional[str], bool]:
    """
    Build context documents for rewrite from context dict or ctx_docs.
    
    Returns:
        tuple: (ctx_docs_for_rewrite, has_reliable_context, context_quality, has_foundational_context)
    """
    ctx_docs_for_rewrite = []
    has_reliable_context_for_rewrite = False
    context_quality_for_rewrite = None
    has_foundational_context = False
    
    if context:
        ctx_docs_for_rewrite = [
            doc["content"] for doc in context.get("knowledge_docs", [])
        ] + [
            doc["content"] for doc in context.get("conversation_docs", [])
        ]
        has_reliable_context_for_rewrite = context.get("has_reliable_context", False)
        context_quality_for_rewrite = context.get("context_quality", None)
        
        # CRITICAL: Check if we have foundational knowledge (CRITICAL_FOUNDATION source)
        if is_stillme_query:
            for doc in context.get("knowledge_docs", []):
                metadata = doc.get("metadata", {})
                if metadata.get("source") == "CRITICAL_FOUNDATION":
                    has_foundational_context = True
                    logger.info("✅ Found foundational knowledge in context - will not use mechanical disclaimer")
                    break
    elif ctx_docs:
        ctx_docs_for_rewrite = ctx_docs
    
    return ctx_docs_for_rewrite, has_reliable_context_for_rewrite, context_quality_for_rewrite, has_foundational_context


def _evaluate_response_quality(
    sanitized_response: str,
    is_philosophical: bool,
    chat_request,
    optimizer,
    is_stillme_query: bool
) -> Dict[str, Any]:
    """
    Evaluate response quality with caching.
    
    Returns:
        Quality result dictionary
    """
    from backend.postprocessing.quality_evaluator import get_quality_evaluator
    
    evaluator = get_quality_evaluator()
    
    # OPTIMIZATION: Check cache first
    cached_quality = optimizer.get_cached_quality_result(
        question=chat_request.message,
        response=sanitized_response
    )
    
    if cached_quality:
        quality_result = cached_quality
        logger.debug("✅ Using cached quality evaluation")
    else:
        # Detect if this is a StillMe query for quality evaluation
        is_stillme_query_for_quality = False
        try:
            from backend.core.stillme_detector import detect_stillme_query
            is_stillme_query_for_quality, _ = detect_stillme_query(chat_request.message)
        except Exception:
            pass
        
        quality_result = evaluator.evaluate(
            text=sanitized_response,
            is_philosophical=is_philosophical,
            original_question=chat_request.message,
            is_stillme_query=is_stillme_query_for_quality
        )
        # Cache the result
        optimizer.cache_quality_result(
            question=chat_request.message,
            response=sanitized_response,
            quality_result=quality_result
        )
    
    return quality_result


async def _rewrite_response(
    sanitized_response: str,
    quality_result: Dict[str, Any],
    context: Optional[Dict[str, Any]],
    ctx_docs_for_rewrite: List[str],
    has_reliable_context_for_rewrite: bool,
    context_quality_for_rewrite: Optional[str],
    has_foundational_context: bool,
    detected_lang: str,
    is_philosophical: bool,
    is_stillme_query: bool,
    chat_request,
    validation_info: Optional[Dict[str, Any]],
    processing_steps: List[str]
) -> str:
    """
    Rewrite response to improve quality with retry logic.
    
    Returns:
        Final rewritten response (or original if no rewrite needed/failed)
    """
    from backend.postprocessing.rewrite_llm import get_rewrite_llm
    from backend.postprocessing.optimizer import get_postprocessing_optimizer
    from backend.postprocessing.quality_evaluator import get_quality_evaluator
    from backend.postprocessing.rewrite_decision_policy import get_rewrite_decision_policy
    from backend.postprocessing.style_sanitizer import get_style_sanitizer
    
    optimizer = get_postprocessing_optimizer()
    evaluator = get_quality_evaluator()
    sanitizer = get_style_sanitizer()
    
    # Phase 3: Only rewrite when CRITICAL issues are present
    # Pass validation_result to check for missing_citation and language_mismatch
    validation_result_dict = None
    if validation_info:
        validation_result_dict = {
            "passed": validation_info.get("passed", True),
            "reasons": validation_info.get("reasons", [])
        }
    
    # Stage 4: Conditional rewrite with cost-benefit logic
    rewrite_count = 0
    quality_before = quality_result.get("overall_score", 1.0)
    
    # CRITICAL: Skip rewrite for StillMe queries with foundational knowledge
    skip_rewrite_for_stillme = False
    if is_stillme_query and has_foundational_context:
        quality_score = quality_result.get("score", 1.0) if quality_result else 1.0
        if quality_score >= 0.5:
            skip_rewrite_for_stillme = True
            logger.info(
                f"⏭️ Skipping rewrite for StillMe query (quality={quality_score:.2f} >= 0.5): "
                "Response quality is acceptable, preserving foundational knowledge."
            )
        else:
            logger.info(
                f"✅ Allowing rewrite for StillMe query (quality={quality_score:.2f} < 0.5): "
                "Quality is too low (generic answer), will rewrite but preserve foundational knowledge."
            )
    
    if skip_rewrite_for_stillme:
        should_rewrite = False
        rewrite_reason = "StillMe query with acceptable quality - preserving accuracy"
        max_attempts = 0
    else:
        should_rewrite, rewrite_reason, max_attempts = optimizer.should_rewrite(
            quality_result=quality_result,
            is_philosophical=is_philosophical,
            response_length=len(sanitized_response),
            validation_result=validation_result_dict,
            rewrite_count=rewrite_count,
            user_question=chat_request.message  # P2: Template detection
        )
    
    # Rewrite loop: can rewrite multiple times if quality improves but still below threshold
    current_response = sanitized_response
    current_quality = quality_before
    
    if should_rewrite:
        logger.info(
            f"🔄 Cost-Benefit: Starting rewrite loop. "
            f"Quality before: {quality_before:.2f}, "
            f"Max attempts: {max_attempts}, "
            f"Issues: {quality_result['reasons'][:3]}"
        )
        processing_steps.append(f"🔄 Quality improvement needed - rewriting with DeepSeek (max {max_attempts} attempts)")
        
        rewrite_llm = get_rewrite_llm()
        policy = get_rewrite_decision_policy()
        
        # Rewrite loop: continue until quality is good or max attempts reached
        while rewrite_count < max_attempts:
            rewrite_count += 1
            logger.info(
                f"🔄 Rewrite attempt {rewrite_count}/{max_attempts}: "
                f"quality_before={current_quality:.2f}"
            )
            
            # Get current quality issues for this rewrite
            is_stillme_query_for_quality = False
            try:
                from backend.core.stillme_detector import detect_stillme_query
                is_stillme_query_for_quality, _ = detect_stillme_query(chat_request.message)
            except Exception:
                pass
            
            current_quality_result = evaluator.evaluate(
                text=current_response,
                is_philosophical=is_philosophical,
                original_question=chat_request.message,
                is_stillme_query=is_stillme_query_for_quality
            )
            
            # CRITICAL: Pass RAG context status to rewrite to enable base knowledge usage
            rewrite_result = await rewrite_llm.rewrite(
                text=current_response,
                original_question=chat_request.message,
                quality_issues=current_quality_result["reasons"],
                is_philosophical=is_philosophical,
                detected_lang=detected_lang,
                ctx_docs=ctx_docs_for_rewrite,
                has_reliable_context=has_reliable_context_for_rewrite,
                context_quality=context_quality_for_rewrite,
                is_stillme_query=is_stillme_query,
                has_foundational_context=has_foundational_context
            )
            
            if not rewrite_result.was_rewritten:
                # Rewrite failed - break loop and use current response
                error_detail = rewrite_result.error or "Unknown error"
                
                # CRITICAL: When rewrite fails, ALWAYS use current_response
                is_likely_corrupted = False
                if rewrite_result.text and current_response:
                    length_ratio = len(rewrite_result.text) / len(current_response) if len(current_response) > 0 else 1.0
                    if length_ratio < 0.5:
                        is_likely_corrupted = True
                        logger.error(
                            f"❌ CRITICAL: rewrite_result.text is likely corrupted "
                            f"(length: {len(rewrite_result.text)} vs current: {len(current_response)}, "
                            f"ratio: {length_ratio:.2f}), using current_response instead"
                        )
                
                # Also check for corruption patterns
                if (rewrite_result.text and 
                    (not isinstance(rewrite_result.text, str) or 
                     len(rewrite_result.text.strip()) < 10 or
                     rewrite_result.text.count("StillMe") > 5 or
                     is_likely_corrupted)):
                    logger.error(
                        f"❌ CRITICAL: rewrite_result.text is corrupted (length: {len(rewrite_result.text) if rewrite_result.text else 0}), "
                        f"using current_response instead. Error: {error_detail[:100]}"
                    )
                
                logger.warning(
                    f"⚠️ Rewrite attempt {rewrite_count} failed: {error_detail[:100]}, "
                    f"using current_response (length: {len(current_response) if current_response else 0}), "
                    f"stopping rewrite loop"
                )
                break
            
            # Re-sanitize rewritten output
            rewritten_response = sanitizer.sanitize(rewrite_result.text, is_philosophical=is_philosophical)
            
            # Evaluate quality after rewrite
            is_stillme_query_for_quality_after = False
            try:
                from backend.core.stillme_detector import detect_stillme_query
                is_stillme_query_for_quality_after, _ = detect_stillme_query(chat_request.message)
            except Exception:
                pass
            
            quality_after_result = evaluator.evaluate(
                text=rewritten_response,
                is_philosophical=is_philosophical,
                original_question=chat_request.message,
                is_stillme_query=is_stillme_query_for_quality_after
            )
            quality_after = quality_after_result.get("overall_score", 0.0)
            
            # Log rewrite metrics
            quality_improvement = quality_after - current_quality
            logger.info(
                f"📊 Rewrite metrics (attempt {rewrite_count}): "
                f"quality_before={current_quality:.2f}, "
                f"quality_after={quality_after:.2f}, "
                f"improvement={quality_improvement:+.2f}"
            )
            
            # Check if we should continue rewriting
            should_continue, continue_reason = policy.should_continue_rewrite(
                quality_before=current_quality,
                quality_after=quality_after,
                rewrite_count=rewrite_count,
                max_attempts=max_attempts
            )
            
            # Update current response and quality
            current_response = rewritten_response
            current_quality = quality_after
            
            if not should_continue:
                logger.info(
                    f"⏹️ Stopping rewrite loop: {continue_reason}, "
                    f"final_quality={quality_after:.2f}, "
                    f"total_rewrites={rewrite_count}"
                )
                break
            else:
                logger.info(
                    f"🔄 Continuing rewrite loop: {continue_reason}, "
                    f"current_quality={quality_after:.2f}"
                )
        
        # Final response is the last rewritten version (or original if no rewrites)
        if current_response and isinstance(current_response, str) and current_response.strip():
            final_response = current_response
        else:
            logger.error(
                f"❌ CRITICAL: current_response is empty or invalid (length: {len(current_response) if isinstance(current_response, str) else 'N/A'}), "
                f"falling back to sanitized_response"
            )
            final_response = sanitized_response if sanitized_response and sanitized_response.strip() else sanitized_response
        
        # Log final metrics
        logger.info(
            f"✅ Rewrite loop complete: "
            f"initial_quality={quality_before:.2f}, "
            f"final_quality={current_quality:.2f}, "
            f"total_rewrites={rewrite_count}, "
            f"quality_improvement={current_quality - quality_before:+.2f}"
        )
        
        if rewrite_count > 0:
            # Re-sanitize final response (in case last rewrite introduced issues)
            from backend.postprocessing.style_sanitizer import get_style_sanitizer
            sanitizer = get_style_sanitizer()
            re_sanitized = sanitizer.sanitize(final_response, is_philosophical=is_philosophical)
            # CRITICAL: Only use re-sanitized if it's not empty
            if re_sanitized and re_sanitized.strip():
                final_response = re_sanitized
            else:
                logger.warning(
                    f"⚠️ Re-sanitized response is empty (original length: {len(final_response) if final_response else 0}), "
                    f"keeping original final_response"
                )
        
        logger.debug(f"✅ Post-processing complete: sanitized → evaluated → rewritten ({rewrite_count}x) → re-sanitized")
    else:
        # Early exit - no rewrite needed (quality is acceptable)
        if is_philosophical or detected_lang == "zh":
            logger.info(
                f"🔍 [EARLY EXIT TRACE] Before final_response assignment: "
                f"sanitized_response_length={len(sanitized_response) if sanitized_response else 0}, "
                f"is_philosophical={is_philosophical}, "
                f"detected_lang={detected_lang}, "
                f"sanitized_preview={safe_unicode_slice(sanitized_response, 200) if sanitized_response else 'None'}"
            )
        
        final_response = sanitized_response
        
        # CRITICAL: Validate final_response after assignment
        if not final_response or not isinstance(final_response, str) or not final_response.strip():
            logger.error(
                f"❌ CRITICAL: final_response is empty after early exit assignment "
                f"(sanitized_response_length={len(sanitized_response) if sanitized_response else 0}), "
                f"falling back to original response"
            )
            final_response = sanitized_response
        
        if should_rewrite:
            logger.debug(f"⏭️ Skipping rewrite: {rewrite_reason}")
        logger.debug(f"✅ Post-processing complete: sanitized → evaluated → passed (quality: {quality_result.get('depth_score', 'N/A')})")
    
    return final_response


def _detect_factual_question(question: str) -> bool:
    """
    Detect if this is a factual question that requires citations.
    
    Args:
        question: User question text
    
    Returns:
        True if this is a factual question
    """
    if not question:
        return False
    
    question_lower = question.lower()
    # Check for factual indicators (same patterns as in CitationRequired)
    factual_patterns = [
        r"\b\d{4}\b",  # Years
        r"\b(bretton\s+woods|gödel|godel|searle|dennett|russell|plato|aristotle|kant|hume|descartes|spinoza)\b",
        r"\b(paradox|theorem|incompleteness|chinese\s+room|geneva|genève)\b",
        r"\b([A-Z][a-z]+)\s+(và|and|vs|versus)\s+([A-Z][a-z]+)\b",  # "Searle và Dennett"
    ]
    for pattern in factual_patterns:
        if re.search(pattern, question_lower, re.IGNORECASE):
            return True
    
    return False


def _re_add_citations_after_rewrite(
    final_response: str,
    context: Optional[Dict[str, Any]],
    ctx_docs_for_rewrite: List[str],
    is_philosophical: bool,
    chat_request
) -> str:
    """
    Re-add citations after rewrite if needed.
    
    Args:
        final_response: Final response after rewrite
        context: RAG context dictionary
        ctx_docs_for_rewrite: Context documents for rewrite
        is_philosophical: Whether this is a philosophical question
        chat_request: ChatRequest object
    
    Returns:
        Response with citations re-added if needed
    """
    # CRITICAL: Ensure citations are preserved after rewrite
    cite_pattern = re.compile(r"\[(\d+)\]")
    has_citations_after_rewrite = bool(cite_pattern.search(final_response))
    
    # CRITICAL: Check if this is a real factual question that requires citations
    is_factual_question = _detect_factual_question(chat_request.message)
    
    # Re-add citation if missing AND (context available OR factual question)
    if not has_citations_after_rewrite and ((ctx_docs_for_rewrite and len(ctx_docs_for_rewrite) > 0) or is_factual_question):
        from backend.validators.citation import CitationRequired
        citation_validator = CitationRequired(required=True)
        # Get context for foundational knowledge detection
        context_for_citation = context
        citation_result = citation_validator.run(
            final_response, 
            ctx_docs_for_rewrite if ctx_docs_for_rewrite else [], 
            is_philosophical=is_philosophical,
            user_question=chat_request.message,
            context=context_for_citation  # CRITICAL: Pass context for foundational knowledge detection
        )
        if citation_result.patched_answer:
            # CRITICAL: Only use patched_answer if it's not empty
            if citation_result.patched_answer.strip():
                final_response = citation_result.patched_answer
                logger.info(f"✅ Re-added citations after rewrite (factual_question={is_factual_question}, has_context={bool(ctx_docs_for_rewrite and len(ctx_docs_for_rewrite) > 0)})")
            else:
                logger.warning(
                    f"⚠️ Citation patched_answer is empty, keeping original final_response "
                    f"(original length: {len(final_response) if final_response else 0})"
                )
    
    return final_response

