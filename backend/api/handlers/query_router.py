"""
Query routing handler for chat requests.

This module handles query detection, routing, and early returns for special query types.
"""

import logging
import time
import uuid
from typing import Optional, Dict, Any, List, Tuple

from backend.api.models import ChatRequest, ChatResponse
from backend.api.utils.chat_helpers import detect_language
from backend.api.handlers.query_classifier import is_codebase_meta_question
from backend.api.utils.text_utils import strip_philosophy_from_answer
from backend.api.utils.response_formatters import build_ai_self_model_answer
from backend.core.decision_logger import DecisionLogger, AgentType, DecisionType
from backend.core.system_status_detector import detect_system_status_intent

logger = logging.getLogger(__name__)

def _safe_domain(url: str) -> str:
    """Extract a stable domain string from a URL (best-effort)."""
    try:
        from urllib.parse import urlparse

        netloc = urlparse(url).netloc or ""
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc or url
    except Exception:
        return url


def _format_system_status_response_vi(rss_stats: Dict[str, Any], enabled_sources: List[str]) -> str:
    total = int(rss_stats.get("feeds_count") or 0)
    ok = int(rss_stats.get("successful_feeds") or 0)
    failed = int(rss_stats.get("failed_feeds") or 0)
    rate = rss_stats.get("failure_rate")
    ts = rss_stats.get("last_fetch_timestamp")

    failed_urls = rss_stats.get("failed_feed_urls") or []
    failed_domains = rss_stats.get("failed_feed_domains") or []
    if not failed_domains and failed_urls:
        failed_domains = sorted({_safe_domain(u) for u in failed_urls})

    source_str = ", ".join(enabled_sources) if enabled_sources else "RSS"
    lines = []
    lines.append(f"Hiện tại StillMe đang học từ {len(enabled_sources)} nhóm nguồn (đang bật theo cấu hình): {source_str}.")
    if total > 0:
        rate_str = f"{rate}%" if rate is not None else "N/A"
        lines.append(f"- RSS: {total} feeds, {ok} OK, {failed} lỗi (failure rate ~{rate_str}).")
    else:
        lines.append("- RSS: chưa có cấu hình feeds hoặc chưa khởi tạo RSS fetcher.")

    if failed > 0:
        if failed_domains:
            lines.append("- Feeds đang lỗi (domain): " + ", ".join(failed_domains) + ".")
        else:
            lines.append("- Feeds đang lỗi: có lỗi nhưng chưa có danh sách chi tiết (chưa có last fetch detail).")

    lines.append(f"- Thời điểm thống kê: {ts or 'chưa có fetch cycle gần đây'}.")
    lines.append("")
    lines.append("[system telemetry: rss_fetcher.get_stats()]")
    return "\n".join(lines).strip()


def _format_system_status_response_en(rss_stats: Dict[str, Any], enabled_sources: List[str]) -> str:
    total = int(rss_stats.get("feeds_count") or 0)
    ok = int(rss_stats.get("successful_feeds") or 0)
    failed = int(rss_stats.get("failed_feeds") or 0)
    rate = rss_stats.get("failure_rate")
    ts = rss_stats.get("last_fetch_timestamp")

    failed_urls = rss_stats.get("failed_feed_urls") or []
    failed_domains = rss_stats.get("failed_feed_domains") or []
    if not failed_domains and failed_urls:
        failed_domains = sorted({_safe_domain(u) for u in failed_urls})

    source_str = ", ".join(enabled_sources) if enabled_sources else "RSS"
    lines = []
    lines.append(f"StillMe currently has {len(enabled_sources)} enabled learning source groups: {source_str}.")
    if total > 0:
        rate_str = f"{rate}%" if rate is not None else "N/A"
        lines.append(f"- RSS: {total} feeds, {ok} OK, {failed} failed (failure rate ~{rate_str}).")
    else:
        lines.append("- RSS: no feeds configured or RSS fetcher not initialized.")

    if failed > 0:
        if failed_domains:
            lines.append("- Failing feeds (domains): " + ", ".join(failed_domains) + ".")
        else:
            lines.append("- Failing feeds: failures detected but no detailed list is available (no last fetch detail).")

    lines.append(f"- Stats timestamp: {ts or 'no recent fetch cycle'}")
    lines.append("")
    lines.append("[system telemetry: rss_fetcher.get_stats()]")
    return "\n".join(lines).strip()


async def route_query(
    chat_request: ChatRequest,
    request,
    processing_steps: List[str],
    timing_logs: Dict[str, Any],
    start_time: float,
    decision_logger: DecisionLogger,
    is_general_roleplay: bool = False
) -> Optional[ChatResponse]:
    """
    Route query to appropriate handler or return early response.
    
    Args:
        chat_request: ChatRequest object
        request: FastAPI Request object
        processing_steps: List to append processing steps
        timing_logs: Dictionary to log timing information
        start_time: Start time for latency calculation
        decision_logger: DecisionLogger instance
        is_general_roleplay: Whether this is a general roleplay question
    
    Returns:
        ChatResponse if early return, None if should continue normal flow.
    """
    # 1. Codebase meta-question routing
    if not is_general_roleplay and is_codebase_meta_question(chat_request.message):
        return await _handle_codebase_meta_question(
            chat_request, processing_steps, timing_logs, start_time, decision_logger
        )

    # 1.5. CRITICAL: System status / learning sources queries MUST be answered from real-time telemetry.
    # This prevents StillMe from hallucinating or using stale "Sources: 7" summaries.
    intent = detect_system_status_intent(chat_request.message)
    if intent.is_system_status:
        detected_lang = detect_language(chat_request.message)
        processing_steps.append("🩺 System status query detected - using real-time telemetry (no LLM)")
        logger.warning(f"🚨 System status query detected (reason={intent.matched_reason}) - returning telemetry directly")

        # RSS stats (real-time from singleton)
        try:
            from backend.services.rss_fetcher import get_rss_fetcher

            rss_fetcher = get_rss_fetcher()
            rss_stats = rss_fetcher.get_stats()
        except Exception as e:
            rss_stats = {"feeds_count": 0, "successful_feeds": 0, "failed_feeds": 0, "failure_rate": None, "last_error": str(e)}

        # Enabled source groups (from env flags; avoid depending on backend.api.main init)
        enabled_sources: List[str] = ["RSS"]
        try:
            from backend.services.source_integration import (
                ENABLE_ARXIV,
                ENABLE_CROSSREF,
                ENABLE_WIKIPEDIA,
                ENABLE_PAPERS_WITH_CODE,
                ENABLE_CONFERENCES,
                ENABLE_STANFORD_ENCYCLOPEDIA,
            )

            if ENABLE_ARXIV:
                enabled_sources.append("ARXIV")
            if ENABLE_CROSSREF:
                enabled_sources.append("CROSSREF")
            if ENABLE_WIKIPEDIA:
                enabled_sources.append("WIKIPEDIA")
            if ENABLE_PAPERS_WITH_CODE:
                enabled_sources.append("PAPERS_WITH_CODE")
            if ENABLE_CONFERENCES:
                enabled_sources.append("CONFERENCES")
            if ENABLE_STANFORD_ENCYCLOPEDIA:
                enabled_sources.append("STANFORD_ENCYCLOPEDIA")
        except Exception:
            # Non-critical: keep RSS only
            pass

        response_text = (
            _format_system_status_response_vi(rss_stats, enabled_sources)
            if detected_lang == "vi"
            else _format_system_status_response_en(rss_stats, enabled_sources)
        )

        from backend.core.epistemic_state import EpistemicState
        total_time = time.time() - start_time
        return ChatResponse(
            response=response_text,
            confidence_score=1.0,
            epistemic_state=EpistemicState.KNOWN.value,
            processing_steps=processing_steps + ["✅ Returned system telemetry (real-time)"],
            timing={"total": f"{total_time:.2f}s"},
            latency_metrics=f"Total: {total_time:.2f}s (system telemetry early return)",
            validation_info={"passed": True, "reasons": ["system_status_telemetry"], "intent_reason": intent.matched_reason},
        )
    
    # 2. Ambiguity clarification
    response = await _handle_ambiguity_clarification(
        chat_request, processing_steps, timing_logs, start_time
    )
    if response:
        return response
    
    # 3. Origin query (Identity Truth Override)
    response = _handle_origin_query(chat_request)
    if response:
        return response
    
    # 4. Religion choice rejection
    response = _handle_religion_choice_rejection(chat_request)
    if response:
        return response
    
    # 5. Honesty question
    response = _handle_honesty_question(chat_request, processing_steps, start_time)
    if response:
        return response
    
    # 6. AI self-model query
    response = _handle_ai_self_model_query(chat_request, processing_steps, start_time)
    if response:
        return response
    
    # 7. External data queries (handled in chat_router.py, not here)
    # 8. Philosophical questions (handled in chat_router.py, not here)
    
    # No early return - continue with normal flow
    return None


async def _handle_codebase_meta_question(
    chat_request: ChatRequest,
    processing_steps: List[str],
    timing_logs: Dict[str, Any],
    start_time: float,
    decision_logger: DecisionLogger
) -> Optional[ChatResponse]:
    """
    Handle codebase meta-questions with Codebase Assistant.
    
    Returns:
        ChatResponse if handled, None if should continue normal flow.
    """
    try:
        # Log routing decision
        decision_logger.log_decision(
            agent_type=AgentType.PLANNER_AGENT,
            decision_type=DecisionType.ROUTING_DECISION,
            decision="Route to Codebase Assistant instead of normal RAG flow",
            reasoning="Question explicitly asks about StillMe's codebase implementation (file paths, functions, code structure)",
            alternatives_considered=["Normal RAG flow with foundational knowledge", "External search"],
            why_not_chosen="Normal RAG would use foundational knowledge which is too generic. Codebase Assistant can provide specific file paths and code snippets.",
            metadata={"question_type": "codebase_meta_question"}
        )
        
        from backend.services.codebase_indexer import get_codebase_indexer
        from backend.api.routers.codebase_router import _generate_code_explanation
        
        processing_steps.append("🧠 Detected StillMe codebase meta-question - using Codebase Assistant")
        logger.info("🧠 Codebase meta-question detected - routing to Codebase Assistant")
        
        indexer = get_codebase_indexer()
        # Increase n_results for comprehensive answers about architecture/components
        code_results = indexer.query_codebase(chat_request.message, n_results=10)
        
        if code_results:
            # Build explanation using the same helper as /api/codebase/query
            explanation = await _generate_code_explanation(
                question=chat_request.message,
                code_chunks=code_results,
            )
            
            # Build lightweight context_used for transparency (no extra LLM work)
            knowledge_docs = []
            for result in code_results:
                metadata = result.get("metadata", {})
                knowledge_docs.append(
                    {
                        "metadata": metadata,
                        "document": result.get("document", ""),
                    }
                )
            
            from backend.core.epistemic_state import EpistemicState
            
            total_time = time.time() - start_time
            return ChatResponse(
                response=explanation.strip(),
                context_used={
                    "knowledge_docs": knowledge_docs,
                    "conversation_docs": [],
                    "total_context_docs": len(knowledge_docs),
                },
                confidence_score=0.9,
                epistemic_state=EpistemicState.KNOWN.value,
                processing_steps=processing_steps
                + ["✅ Answered via StillMe Codebase Assistant (code-level RAG)"],
                timing={"total": f"{total_time:.2f}s"},
                latency_metrics=f"Total: {total_time:.2f}s (codebase assistant)",
            )
        else:
            logger.warning("Codebase Assistant found no relevant code chunks - falling back to normal RAG flow")
            return None
    except Exception as codebase_error:
        # Fail safe: log and continue with normal pipeline
        logger.warning(f"Codebase Assistant routing failed, continuing with normal flow: {codebase_error}")
        return None


async def _handle_ambiguity_clarification(
    chat_request: ChatRequest,
    processing_steps: List[str],
    timing_logs: Dict[str, Any],
    start_time: float
) -> Optional[ChatResponse]:
    """
    Handle high ambiguity with clarification question.
    
    Returns:
        ChatResponse if clarification needed, None if should continue normal flow.
    """
    try:
        from backend.core.ambiguity_detector import get_ambiguity_detector
        ambiguity_detector = get_ambiguity_detector()
        should_ask, clarification_question = ambiguity_detector.should_ask_clarification(
            chat_request.message,
            conversation_history=chat_request.conversation_history
        )
        
        if should_ask and clarification_question:
            # HIGH ambiguity detected - ask for clarification instead of processing
            logger.info(f"❓ HIGH ambiguity detected - asking for clarification instead of processing")
            processing_steps.append("❓ Ambiguity detected - asking for clarification")
            
            # Detect language for clarification question
            detected_lang = detect_language(chat_request.message)
            
            # Return clarification question immediately (skip LLM call, save cost & latency)
            from backend.core.epistemic_state import EpistemicState
            import uuid
            message_id = f"msg_{uuid.uuid4().hex[:16]}"
            
            return ChatResponse(
                response=clarification_question,
                message_id=message_id,
                context_used=None,
                accuracy_score=None,
                confidence_score=0.0,  # Low confidence because we're asking for clarification
                validation_info={
                    "passed": True,
                    "reasons": ["ambiguity_detected", "clarification_requested"],
                    "ambiguity_score": 1.0,
                    "ambiguity_level": "HIGH",
                    "clarification_question": clarification_question
                },
                learning_suggestions=None,
                learning_session_id=None,
                knowledge_alert=None,
                learning_proposal=None,
                permission_request=None,
                timing=timing_logs,
                latency_metrics="Ambiguity detection: <0.1s (early return, no LLM call)",
                processing_steps=processing_steps,
                epistemic_state=EpistemicState.UNKNOWN.value,  # Unknown because we need clarification
                transparency_scorecard=None
            )
    except Exception as ambiguity_error:
        logger.warning(f"Ambiguity detector error: {ambiguity_error}")
    
    return None


def _handle_origin_query(
    chat_request: ChatRequest
) -> Optional[ChatResponse]:
    """
    Handle origin queries with Identity Truth Override.
    
    Returns:
        ChatResponse if origin query, None if should continue normal flow.
    """
    try:
        from backend.core.stillme_detector import detect_origin_query
        
        is_origin_query, origin_keywords = detect_origin_query(chat_request.message)
        if is_origin_query:
            logger.debug(f"Origin query detected! Matched keywords: {origin_keywords}")
            
            # CRITICAL: Detect language BEFORE calling get_system_origin_answer
            try:
                detected_lang = detect_language(chat_request.message)
                logger.debug(f"🌐 Detected language for origin query: {detected_lang}")
            except Exception as lang_error:
                logger.warning(f"Language detection failed: {lang_error}, defaulting to 'vi'")
                detected_lang = "vi"
            
            from backend.identity.system_origin import get_system_origin_answer
            logger.info("🎯 Identity Truth Override: Returning SYSTEM_ORIGIN answer directly (no LLM fallback)")
            system_truth_answer = get_system_origin_answer(detected_lang)
            
            # Return immediately with system truth - no LLM processing needed
            from backend.core.epistemic_state import EpistemicState
            return ChatResponse(
                response=system_truth_answer,  # CRITICAL: Use 'response' field, not 'message'
                confidence_score=1.0,  # 100% confidence - this is ground truth
                processing_steps=["🎯 Identity Truth Override: Used SYSTEM_ORIGIN ground truth"],
                validation_info={},
                timing={},
                epistemic_state=EpistemicState.KNOWN.value  # System truth is KNOWN
            )
    except ImportError:
        logger.warning("StillMe detector not available, skipping origin detection")
    except Exception as origin_error:
        logger.error(f"❌ Failed to get SYSTEM_ORIGIN answer: {origin_error}, falling back to normal processing")
    
    return None


def _handle_religion_choice_rejection(
    chat_request: ChatRequest
) -> Optional[ChatResponse]:
    """
    Handle religion choice queries with rejection answer.
    
    Returns:
        ChatResponse if religion choice query, None if should continue normal flow.
    """
    try:
        from backend.core.ai_self_model_detector import detect_religion_choice_query
        
        is_religion_choice_query, religion_patterns = detect_religion_choice_query(chat_request.message)
        if is_religion_choice_query:
            logger.warning(f"🚨 RELIGION_CHOICE query detected! Matched patterns: {religion_patterns}")
            
            # Detect language BEFORE calling get_religion_rejection_answer
            try:
                detected_lang = detect_language(chat_request.message)
                logger.debug(f"🌐 Detected language for religion choice query: {detected_lang}")
            except Exception as lang_error:
                logger.warning(f"Language detection failed: {lang_error}, defaulting to 'vi'")
                detected_lang = "vi"
            
            from backend.identity.religion_rejection_templates import get_religion_rejection_answer
            logger.info("🚨 RELIGION_CHOICE REJECTION: Returning religion rejection answer directly (no LLM fallback)")
            religion_rejection_answer = get_religion_rejection_answer(detected_lang)
            
            # Return immediately with religion rejection - no LLM processing needed
            from backend.core.epistemic_state import EpistemicState
            return ChatResponse(
                response=religion_rejection_answer,  # CRITICAL: Use 'response' field, not 'message'
                confidence_score=1.0,  # 100% confidence - this is ground truth
                processing_steps=["🚨 RELIGION_CHOICE REJECTION: StillMe cannot choose any religion"],
                validation_info={},
                timing={},
                epistemic_state=EpistemicState.KNOWN.value  # System policy is KNOWN
            )
    except ImportError:
        logger.warning("AI self model detector not available, skipping religion choice detection")
    except Exception as religion_error:
        logger.error(f"❌ Failed to get religion rejection answer: {religion_error}, falling back to normal processing")
    
    return None


def _handle_honesty_question(
    chat_request: ChatRequest,
    processing_steps: List[str],
    start_time: float
) -> Optional[ChatResponse]:
    """
    Handle honesty/consistency questions with Honesty Handler.
    
    Returns:
        ChatResponse if honesty question, None if should continue normal flow.
    """
    try:
        from backend.honesty.handler import is_honesty_question as check_honesty, build_honesty_response
        
        is_honesty_question = check_honesty(chat_request.message)
        if is_honesty_question:
            logger.info("Honesty/consistency question detected - using Honesty Handler")
            # Detect language for the answer
            detected_lang = detect_language(chat_request.message)
            # Process with Honesty Handler
            honesty_answer = build_honesty_response(chat_request.message, detected_lang)
            
            # Return response immediately without LLM processing
            processing_steps.append("✅ Detected honesty/consistency question - returning Honesty Handler response")
            return ChatResponse(
                response=honesty_answer,
                confidence_score=1.0,  # High confidence for honest response
                processing_steps=processing_steps,
                timing_logs={
                    "total_time": time.time() - start_time,
                    "rag_retrieval_latency": 0.0,
                    "llm_inference_latency": 0.0
                },
                validation_result=None,  # No validation needed for honest response
                used_fallback=False
            )
    except Exception as honesty_handler_error:
        logger.warning(f"Honesty handler error: {honesty_handler_error}")
    
    return None


def _handle_ai_self_model_query(
    chat_request: ChatRequest,
    processing_steps: List[str],
    start_time: float
) -> Optional[ChatResponse]:
    """
    Handle AI self-model queries with technical architecture answer.
    
    Returns:
        ChatResponse if AI self-model query, None if should continue normal flow.
    """
    try:
        from backend.core.ai_self_model_detector import detect_ai_self_model_query, get_ai_self_model_opening
        
        is_ai_self_model_query, matched_patterns = detect_ai_self_model_query(chat_request.message)
        if is_ai_self_model_query:
            logger.warning(f"🚨 AI_SELF_MODEL query detected - OVERRIDING all other pipelines (patterns: {matched_patterns})")
            # Detect language
            detected_lang = detect_language(chat_request.message)
            
            # Get mandatory opening statement
            opening_statement = get_ai_self_model_opening(detected_lang)
            
            # Build technical answer about StillMe's architecture
            # CRITICAL: Use foundational knowledge if available, but focus on technical facts
            technical_answer = build_ai_self_model_answer(
                chat_request.message,
                detected_lang,
                opening_statement
            )
            
            # CRITICAL: Strip any philosophy from answer
            technical_answer = strip_philosophy_from_answer(technical_answer)
            
            # Return immediately - NO philosophy processor, NO rewrite with philosophy
            processing_steps.append("✅ AI_SELF_MODEL query - answered with technical architecture only")
            return ChatResponse(
                response=technical_answer,
                confidence_score=1.0,  # High confidence for technical facts
                processing_steps=processing_steps,
                timing_logs={
                    "total_time": time.time() - start_time,
                    "rag_retrieval_latency": 0.0,
                    "llm_inference_latency": 0.0
                },
                validation_result=None,  # Will validate separately
                used_fallback=False
            )
    except Exception as ai_self_model_error:
        logger.error(f"AI_SELF_MODEL handler error: {ai_self_model_error}", exc_info=True)
    
    return None


def _detect_query_types(
    chat_request: ChatRequest
) -> Dict[str, Any]:
    """
    Detect all query types at once.
    
    Returns:
        dict with flags: is_codebase_meta, is_ambiguous, is_origin, etc.
    """
    query_types = {
        "is_codebase_meta": False,
        "is_ambiguous": False,
        "is_origin": False,
        "is_religion_choice": False,
        "is_honesty": False,
        "is_ai_self_model": False
    }
    
    # Detect codebase meta
    query_types["is_codebase_meta"] = is_codebase_meta_question(chat_request.message)
    
    # Detect ambiguity
    try:
        from backend.core.ambiguity_detector import get_ambiguity_detector
        ambiguity_detector = get_ambiguity_detector()
        should_ask, _ = ambiguity_detector.should_ask_clarification(
            chat_request.message,
            conversation_history=chat_request.conversation_history
        )
        query_types["is_ambiguous"] = should_ask
    except Exception:
        pass
    
    # Detect origin
    try:
        from backend.core.stillme_detector import detect_origin_query
        is_origin, _ = detect_origin_query(chat_request.message)
        query_types["is_origin"] = is_origin
    except Exception:
        pass
    
    # Detect religion choice
    try:
        from backend.core.ai_self_model_detector import detect_religion_choice_query
        is_religion, _ = detect_religion_choice_query(chat_request.message)
        query_types["is_religion_choice"] = is_religion
    except Exception:
        pass
    
    # Detect honesty
    try:
        from backend.honesty.handler import is_honesty_question as check_honesty
        query_types["is_honesty"] = check_honesty(chat_request.message)
    except Exception:
        pass
    
    # Detect AI self-model
    try:
        from backend.core.ai_self_model_detector import detect_ai_self_model_query
        is_ai_self_model, _ = detect_ai_self_model_query(chat_request.message)
        query_types["is_ai_self_model"] = is_ai_self_model
    except Exception:
        pass
    
    return query_types

