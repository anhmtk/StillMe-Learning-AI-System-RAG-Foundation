"""
Validation Handler for StillMe API
Handles validation logic with fallback mechanisms
"""

import logging
import os
import re
import time
from typing import Optional, Dict, Any, List, Tuple

from backend.api.config.chat_config import get_chat_config
from backend.api.handlers.prompt_builder import calculate_confidence_score
from backend.api.utils.response_formatters import append_validation_warnings_to_response
from backend.api.utils.chat_helpers import generate_ai_response

logger = logging.getLogger(__name__)


def _add_transparency_disclaimer_before_validation(
    raw_response: str,
    ctx_docs: List[str],
    is_philosophical: bool,
    detected_lang: str
) -> str:
    """
    Add transparency disclaimer BEFORE validation if no context.
    This prevents missing_uncertainty_no_context failures for responses without RAG context.
    """
    if len(ctx_docs) == 0 and not is_philosophical and raw_response:
        response_lower = raw_response.lower()
        transparency_indicators = [
            # English
            "general knowledge", "training data", "my training", "base knowledge", "pretrained", "pre-trained",
            "not from stillme", "not from rag", "without context", "no context",
            "based on general", "from my training", "from general knowledge",
            "note:", "this answer", "this response",
            # Vietnamese
            "kiến thức chung", "dữ liệu huấn luyện", "kiến thức cơ bản",
            "không từ stillme", "không từ rag", "không có context", "không có ngữ cảnh",
            "dựa trên kiến thức chung", "từ dữ liệu huấn luyện",
            "lưu ý:", "câu trả lời này",
            # Multilingual common patterns
            "note:", "nota:", "ملاحظة:", "примечание:", "注意:", "참고:",
            "connaissance générale", "données d'entraînement", "conocimiento general", "dados de entrenamiento",
            "allgemeines wissen", "trainingsdaten", "conhecimento geral", "dados de treinamento"
        ]
        has_transparency = any(indicator in response_lower for indicator in transparency_indicators)
        
        if not has_transparency:
            if detected_lang == 'vi':
                disclaimer = "⚠️ Lưu ý: Câu trả lời này dựa trên kiến thức chung từ training data, không có context từ RAG. Mình không chắc chắn về độ chính xác.\n\n"
            else:
                disclaimer = "⚠️ Note: This answer is based on general knowledge from training data, not from RAG context. I'm not certain about its accuracy.\n\n"
            
            raw_response = disclaimer + raw_response
            logger.info("ℹ️ Added transparency disclaimer BEFORE validation for response without context")
    
    return raw_response


def _get_adaptive_thresholds(
    is_philosophical: bool,
    ctx_docs: List[str],
    context: Dict[str, Any],
    chat_request
) -> Tuple[float, float]:
    """
    Get context-aware adaptive thresholds from Self-Distilled Learning.
    
    Returns:
        tuple: (adaptive_citation_overlap, adaptive_evidence_threshold)
    """
    try:
        from backend.services.self_distilled_learning import get_self_distilled_learning
        sdl = get_self_distilled_learning()
        
        threshold_context = {
            "is_philosophical": is_philosophical,
            "is_technical": False,
            "has_context": len(ctx_docs) > 0,
            "context_quality": context.get("context_quality", "medium"),
            "avg_similarity": context.get("avg_similarity_score", 0.5)
        }
        
        # Detect technical questions
        question_lower = chat_request.message.lower()
        technical_keywords = ["code", "function", "api", "implementation", "algorithm", "bug", "error", "debug"]
        if any(keyword in question_lower for keyword in technical_keywords):
            threshold_context["is_technical"] = True
        
        config = get_chat_config()
        adaptive_citation_overlap = sdl.get_adaptive_threshold(
            "citation_relevance_min_overlap",
            config.validation.ADAPTIVE_CITATION_OVERLAP_DEFAULT,
            context=threshold_context
        )
        adaptive_evidence_threshold = sdl.get_adaptive_threshold(
            "evidence_overlap_threshold",
            config.validation.ADAPTIVE_EVIDENCE_THRESHOLD_DEFAULT,
            context=threshold_context
        )
        logger.debug(f"🎯 [Self-Distilled] Using context-aware thresholds: citation_overlap={adaptive_citation_overlap:.3f}, evidence={adaptive_evidence_threshold:.3f} (philosophical={is_philosophical}, context_quality={threshold_context['context_quality']})")
        return adaptive_citation_overlap, adaptive_evidence_threshold
    except Exception as e:
        logger.warning(f"⚠️ [Self-Distilled] Failed to get adaptive thresholds, using defaults: {e}")
        config = get_chat_config()
        return (
            config.validation.ADAPTIVE_CITATION_OVERLAP_DEFAULT,
            config.validation.ADAPTIVE_EVIDENCE_THRESHOLD_DEFAULT
        )


def _build_validation_chain(
    detected_lang: str,
    is_philosophical: bool,
    ctx_docs: List[str],
    adaptive_citation_overlap: float,
    adaptive_evidence_threshold: float,
    context: Dict[str, Any]
) -> Tuple[Any, List]:  # Returns (ValidatorChain, validators list)
    """
    Build validator chain based on query type and context.
    
    Returns:
        tuple: (ValidatorChain, list of validators)
    """
    from backend.validators.chain import ValidatorChain
    from backend.validators.citation import CitationRequired
    from backend.validators.evidence_overlap import EvidenceOverlap
    from backend.validators.numeric import NumericUnitsBasic
    from backend.validators.ethics_adapter import EthicsAdapter
    from backend.validators.confidence import ConfidenceValidator
    from backend.validators.fallback_handler import FallbackHandler
    from backend.services.ethics_guard import check_content_ethics
    from backend.validators.language import LanguageValidator
    from backend.validators.citation_relevance import CitationRelevance
    from backend.validators.identity_check import IdentityCheckValidator
    from backend.validators.ego_neutrality import EgoNeutralityValidator
    from backend.validators.factual_hallucination import FactualHallucinationValidator
    from backend.validators.religion_choice import ReligiousChoiceValidator
    from backend.validators.source_consensus import SourceConsensusValidator
    
    # Enable Identity Check Validator (can be toggled via env var)
    enable_identity_check = os.getenv("ENABLE_IDENTITY_VALIDATOR", "true").lower() == "true"
    identity_validator_strict = os.getenv("IDENTITY_VALIDATOR_STRICT", "true").lower() == "true"
    
    # Critical validators (always run)
    validators = [
        LanguageValidator(input_language=detected_lang),
        CitationRequired(),
        CitationRelevance(min_keyword_overlap=adaptive_citation_overlap),
        NumericUnitsBasic(),
        ConfidenceValidator(require_uncertainty_when_no_context=not is_philosophical),
        FactualHallucinationValidator(),
        ReligiousChoiceValidator(),
    ]
    
    # Optional validators (run conditionally)
    # EvidenceOverlap: Only when has context
    if len(ctx_docs) > 0:
        validators.insert(3, EvidenceOverlap(threshold=adaptive_evidence_threshold))
        logger.debug(f"Phase 2: Added EvidenceOverlap validator (has context, threshold={adaptive_evidence_threshold:.3f})")
    
    # SourceConsensusValidator: Only when has multiple sources (≥2)
    config = get_chat_config()
    if len(ctx_docs) >= config.validation.MIN_SOURCES_FOR_CONSENSUS:
        insert_pos = 4 if len(ctx_docs) > 0 else 3
        validators.insert(insert_pos, SourceConsensusValidator(enabled=True, timeout=config.timeouts.SOURCE_CONSENSUS))
        logger.debug(f"Phase 2: Added SourceConsensusValidator (has {len(ctx_docs)} sources)")
    
    # EgoNeutralityValidator: Only when has context
    if len(ctx_docs) > 0:
        fact_halluc_idx = next(i for i, v in enumerate(validators) if type(v).__name__ == "FactualHallucinationValidator")
        validators.insert(fact_halluc_idx, EgoNeutralityValidator(strict_mode=True, auto_patch=True))
        logger.debug("Phase 2: Added EgoNeutralityValidator (has context)")
    
    # Add Identity Check Validator if enabled
    if enable_identity_check:
        validators.append(
            IdentityCheckValidator(
                strict_mode=identity_validator_strict,
                require_humility_when_no_context=True,
                allow_minor_tone_violations=False
            )
        )
    
    # Add PhilosophicalDepthValidator for philosophical questions
    if is_philosophical:
        from backend.validators.philosophical_depth import PhilosophicalDepthValidator
        validators.append(PhilosophicalDepthValidator(min_keywords=2, strict_mode=True))
        logger.debug("Phase 2: Added PhilosophicalDepthValidator (philosophical question detected)")
    
    # Add HallucinationExplanationValidator
    from stillme_core.validation.hallucination_explanation import HallucinationExplanationValidator
    validators.append(HallucinationExplanationValidator(strict_mode=False, auto_patch=True))
    logger.debug("Phase 2: Added HallucinationExplanationValidator")
    
    # Add VerbosityValidator
    from stillme_core.validation.verbosity import VerbosityValidator
    validators.append(VerbosityValidator(max_length_ratio=3.0, strict_mode=False))
    logger.debug("Phase 2: Added VerbosityValidator")
    
    # Add FutureDatesValidator
    from backend.validators.future_dates import FutureDatesValidator
    validators.append(FutureDatesValidator())
    logger.debug("Phase 2: Added FutureDatesValidator")
    
    # Add EthicsAdapter last (most critical)
    validators.append(EthicsAdapter(guard_callable=check_content_ethics))
    
    chain = ValidatorChain(validators)
    return chain, validators


def _run_step_validation(
    raw_response: str,
    ctx_docs: List[str],
    context: Dict[str, Any],
    adaptive_citation_overlap: float,
    adaptive_evidence_threshold: float,
    processing_steps: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Run step-level validation if enabled.
    
    Returns:
        Optional[dict]: Step validation info or None if disabled/failed
    """
    enable_step_validation = os.getenv("ENABLE_STEP_LEVEL_VALIDATION", "true").lower() == "true"
    step_min_steps = int(os.getenv("STEP_VALIDATION_MIN_STEPS", "2"))
    step_confidence_threshold = float(os.getenv("STEP_CONFIDENCE_THRESHOLD", "0.5"))
    
    logger.info(f"🔍 Step-level validation config: enabled={enable_step_validation}, min_steps={step_min_steps}, threshold={step_confidence_threshold}")
    
    if not enable_step_validation:
        return None
    
    try:
        from backend.validators.step_detector import StepDetector
        from backend.validators.step_validator import StepValidator
        
        step_detector = StepDetector()
        logger.debug(f"🔍 Checking if response is multi-step (min_steps: {step_min_steps})...")
        logger.debug(f"🔍 Response preview (first 200 chars): {raw_response[:200]}...")
        is_multi = step_detector.is_multi_step(raw_response)
        logger.debug(f"🔍 is_multi_step result: {is_multi}")
        
        if not is_multi:
            return None
        
        steps = step_detector.detect_steps(raw_response)
        logger.debug(f"🔍 StepDetector found {len(steps)} steps")
        
        if len(steps) < step_min_steps:
            return None
        
        logger.debug(f"🔍 Detected {len(steps)} steps - running step-level validation")
        processing_steps.append(f"🔍 Step-level validation ({len(steps)} steps)")
        
        step_validator = StepValidator(
            confidence_threshold=step_confidence_threshold,
            use_lightweight=True,
            use_batch=True
        )
        logger.debug(f"🔍 Validating {len(steps)} steps with threshold {step_confidence_threshold} (P1.1.b: batch validation)")
        
        step_results = step_validator.validate_all_steps(
            steps,
            ctx_docs,
            chain=None,
            parallel=True,
            adaptive_citation_overlap=adaptive_citation_overlap,
            adaptive_evidence_threshold=adaptive_evidence_threshold,
            context=context
        )
        logger.debug(f"🔍 Step validation completed: {len(step_results)} results")
        
        low_confidence_steps = [
            r.step.step_number
            for r in step_results
            if r.confidence < step_confidence_threshold
        ]
        
        if low_confidence_steps:
            logger.warning(f"⚠️ Low confidence steps detected: {low_confidence_steps}")
            logger.warning(f"⚠️ {len(low_confidence_steps)} step(s) with low confidence")
            processing_steps.append(f"⚠️ {len(low_confidence_steps)} step(s) with low confidence")
        else:
            logger.info(f"✅ All {len(steps)} steps passed validation")
            processing_steps.append(f"✅ All steps validated")
        
        return {
            "is_multi_step": True,
            "total_steps": len(steps),
            "steps": [
                {
                    "step_number": r.step.step_number,
                    "confidence": round(r.confidence, 2),
                    "passed": r.passed,
                    "issues": r.issues
                }
                for r in step_results
            ],
            "low_confidence_steps": low_confidence_steps,
            "all_steps_passed": all(r.passed for r in step_results),
            "average_confidence": round(
                sum(r.confidence for r in step_results) / len(step_results), 2
            ) if step_results else 0.0
        }
    except Exception as step_error:
        logger.warning(f"Step-level validation error: {step_error}", exc_info=True)
        return None


def _run_consistency_check(
    raw_response: str,
    ctx_docs: List[str],
    processing_steps: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Run consistency checks if enabled.
    
    Returns:
        Optional[dict]: Consistency info or None if disabled/failed
    """
    enable_consistency_checks = os.getenv("ENABLE_CONSISTENCY_CHECKS", "true").lower() == "true"
    logger.debug(f"🔍 Consistency checks config: enabled={enable_consistency_checks}")
    
    if not enable_consistency_checks:
        return None
    
    try:
        from backend.validators.consistency_checker import ConsistencyChecker
        
        checker = ConsistencyChecker()
        claims = checker.extract_claims(raw_response)
        logger.debug(f"🔍 Extracted {len(claims)} claims from response")
        
        if len(claims) <= 1:
            return None
        
        logger.debug(f"🔍 Checking consistency for {len(claims)} claims")
        
        # Check pairwise consistency
        consistency_results = checker.check_pairwise_consistency(claims)
        
        # Check KB consistency for each claim
        kb_results = {}
        for i, claim in enumerate(claims):
            kb_consistency = checker.check_kb_consistency(claim, ctx_docs)
            kb_results[f"claim_{i}_vs_kb"] = kb_consistency
        
        contradictions = [
            key for key, value in consistency_results.items()
            if value == "CONTRADICTION"
        ]
        
        kb_inconsistencies = [
            key for key, value in kb_results.items()
            if "INCONSISTENT" in value
        ]
        
        if contradictions or kb_inconsistencies:
            logger.warning(f"⚠️ Consistency issues detected: {len(contradictions)} contradictions, {len(kb_inconsistencies)} KB inconsistencies")
            processing_steps.append(f"⚠️ {len(contradictions)} contradiction(s) detected")
        
        return {
            "total_claims": len(claims),
            "contradictions": contradictions,
            "kb_inconsistencies": kb_inconsistencies,
            "has_issues": len(contradictions) > 0 or len(kb_inconsistencies) > 0
        }
    except Exception as consistency_error:
        logger.warning(f"Consistency check error: {consistency_error}", exc_info=True)
        return None


async def handle_validation_with_fallback(
    raw_response: str,
    context: dict,
    detected_lang: str,
    is_philosophical: bool,
    is_religion_roleplay: bool,
    chat_request,
    enhanced_prompt: str,
    context_text: str,
    citation_instruction: str,
    num_knowledge: int,
    processing_steps: list,
    timing_logs: dict,
    is_origin_query: bool = False,
    is_stillme_query: bool = False
) -> tuple:
    """
    Handle validation logic with fallback mechanisms.
    
    This function encapsulates the entire validation pipeline including:
    - Validator chain execution
    - Step-level validation
    - Consistency checks
    - OpenAI fallback
    - Validation failure handling with FallbackHandler
    
    Returns:
        tuple: (response, validation_info, confidence_score, used_fallback, 
                step_validation_info, consistency_info, ctx_docs)
    """
    processing_steps.append("🔍 Validating response...")
    validation_start = time.time()
    
    # Build context docs list for validation
    ctx_docs = [
        doc["content"] for doc in context["knowledge_docs"]
    ] + [
        doc["content"] for doc in context["conversation_docs"]
    ]
    
    # Add transparency disclaimer BEFORE validation if no context
    raw_response = _add_transparency_disclaimer_before_validation(
        raw_response, ctx_docs, is_philosophical, detected_lang
    )
    
    # Get adaptive thresholds
    adaptive_citation_overlap, adaptive_evidence_threshold = _get_adaptive_thresholds(
        is_philosophical, ctx_docs, context, chat_request
    )
    
    # Build validation chain
    chain, validators = _build_validation_chain(
        detected_lang, is_philosophical, ctx_docs,
        adaptive_citation_overlap, adaptive_evidence_threshold, context
    )
    
    # Pass context quality to ValidatorChain
    context_quality = context.get("context_quality", None)
    avg_similarity = context.get("avg_similarity_score", None)
    
    # Run validation
    validation_result = chain.run(
        raw_response,
        ctx_docs,
        context_quality=context_quality,
        avg_similarity=avg_similarity,
        is_philosophical=is_philosophical,
        is_religion_roleplay=is_religion_roleplay,
        user_question=chat_request.message,
        context=context
    )
    
    validation_time = time.time() - validation_start
    timing_logs["validation"] = f"{validation_time:.2f}s"
    logger.info(f"⏱️ Validation took {validation_time:.2f}s")
    processing_steps.append(f"✅ Validation completed ({validation_time:.2f}s)")
    
    # Log validation decision
    try:
        from backend.core.decision_logger import get_decision_logger, AgentType, DecisionType
        decision_logger = get_decision_logger()
        if decision_logger:
            validator_names = [type(v).__name__ for v in validators]
            decision_logger.log_decision(
                agent_type=AgentType.VALIDATOR_ORCHESTRATOR,
                decision_type=DecisionType.VALIDATION_DECISION,
                decision=f"Ran {len(validators)} validators: {', '.join(validator_names[:5])}{'...' if len(validator_names) > 5 else ''}",
                reasoning=f"Validation chain executed with {len(ctx_docs)} context documents. Adaptive thresholds: citation_overlap={adaptive_citation_overlap:.3f}, evidence={adaptive_evidence_threshold:.3f}",
                context={
                    "num_validators": len(validators),
                    "validator_names": validator_names,
                    "context_docs_count": len(ctx_docs),
                    "context_quality": context_quality,
                    "avg_similarity": avg_similarity,
                    "is_philosophical": is_philosophical
                },
                outcome=f"Validation {'passed' if validation_result.passed else 'failed'}. Reasons: {', '.join(validation_result.reasons[:3])}{'...' if len(validation_result.reasons) > 3 else ''}",
                success=validation_result.passed,
                metadata={
                    "validation_time": validation_time,
                    "adaptive_citation_overlap": adaptive_citation_overlap,
                    "adaptive_evidence_threshold": adaptive_evidence_threshold
                }
            )
    except Exception:
        pass  # decision_logger not available, skip logging
    
    # Calculate confidence score
    confidence_score = calculate_confidence_score(
        context_docs_count=len(ctx_docs),
        validation_result=validation_result,
        context=context
    )
    
    # Run step-level validation
    step_validation_info = _run_step_validation(
        raw_response, ctx_docs, context,
        adaptive_citation_overlap, adaptive_evidence_threshold, processing_steps
    )
    
    # Run consistency checks
    consistency_info = _run_consistency_check(
        raw_response, ctx_docs, processing_steps
    )
    
    # OpenAI Fallback Mechanism
    # Check if FactualHallucinationValidator detected explicit fake entities
    has_factual_hallucination = False
    if validation_result.reasons:
        factual_hallucination_indicators = [
            "non_existent_concept_mentioned",
            "explicit_fake_entity",
            "detailed_description_of_explicit_fake_entity",
            "assertive_description_of_explicit_fake_entity",
            "assertive_claim_without_citation_for_explicit_fake_entity"
        ]
        has_factual_hallucination = any(
            any(indicator in reason for indicator in factual_hallucination_indicators)
            for reason in validation_result.reasons
        )
        if has_factual_hallucination:
            logger.warning(
                f"🚨 CRITICAL: FactualHallucinationValidator detected explicit fake entity. "
                f"BLOCKING OpenAI fallback to prevent hallucination. Reasons: {validation_result.reasons}"
            )
    
    enable_openai_fallback = os.getenv("ENABLE_OPENAI_FALLBACK", "true").lower() == "true"
    openai_fallback_threshold = float(os.getenv("OPENAI_FALLBACK_CONFIDENCE_THRESHOLD", "0.5"))
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Check if we should try OpenAI fallback
    should_try_openai = (
        enable_openai_fallback and
        openai_api_key and
        not has_factual_hallucination and
        (
            confidence_score < openai_fallback_threshold or
            not validation_result.passed
        ) and
        chat_request.llm_provider != "openai"
    )
    
    if should_try_openai:
        logger.info(f"🔄 Low confidence ({confidence_score:.2f}) or validation failed. Attempting OpenAI fallback...")
        processing_steps.append("🔄 Attempting OpenAI fallback for better quality...")
        try:
            from backend.api.utils.llm_providers import InsufficientQuotaError
            
            use_server_keys_retry = chat_request.llm_provider is None
            openai_response = await generate_ai_response(
                enhanced_prompt,
                detected_lang=detected_lang,
                llm_provider="openai",
                llm_api_key=openai_api_key,
                llm_model_name="gpt-3.5-turbo",
                use_server_keys=use_server_keys_retry
            )
            
            # Re-validate OpenAI response
            openai_validation_result = chain.run(
                openai_response,
                ctx_docs,
                user_question=chat_request.message,
                context=context
            )
            openai_confidence = calculate_confidence_score(
                context_docs_count=len(ctx_docs),
                validation_result=openai_validation_result,
                context=context
            )
            
            # Check if OpenAI response also contains explicit fake entities
            openai_has_factual_hallucination = False
            if openai_validation_result.reasons:
                factual_hallucination_indicators = [
                    "non_existent_concept_mentioned",
                    "explicit_fake_entity",
                    "detailed_description_of_explicit_fake_entity",
                    "assertive_description_of_explicit_fake_entity",
                    "assertive_claim_without_citation_for_explicit_fake_entity"
                ]
                openai_has_factual_hallucination = any(
                    any(indicator in reason for indicator in factual_hallucination_indicators)
                    for reason in openai_validation_result.reasons
                )
                if openai_has_factual_hallucination:
                    logger.warning(
                        f"🚨 CRITICAL: OpenAI fallback response also contains explicit fake entity! "
                        f"REJECTING OpenAI fallback. Reasons: {openai_validation_result.reasons}"
                    )
            
            # Use OpenAI response if it's better AND doesn't contain explicit fake entities
            if not openai_has_factual_hallucination and (openai_confidence > confidence_score or openai_validation_result.passed):
                raw_response = openai_response
                validation_result = openai_validation_result
                confidence_score = openai_confidence
                logger.info(f"✅ OpenAI fallback succeeded (confidence: {openai_confidence:.2f})")
                processing_steps.append(f"✅ OpenAI fallback succeeded (confidence: {openai_confidence:.2f})")
            else:
                if openai_has_factual_hallucination:
                    logger.warning(f"⚠️ OpenAI fallback rejected: contains explicit fake entity")
                    processing_steps.append("⚠️ OpenAI fallback rejected: contains explicit fake entity")
                else:
                    logger.info(f"⚠️ OpenAI fallback didn't improve quality, using original response")
                    processing_steps.append("⚠️ OpenAI fallback didn't improve quality")
                
        except InsufficientQuotaError as quota_error:
            logger.warning(f"⚠️ OpenAI credit exhausted: {quota_error}. Using original DeepSeek response.")
            processing_steps.append("⚠️ OpenAI credit exhausted, using original response")
        except Exception as openai_error:
            logger.warning(f"⚠️ OpenAI fallback failed: {openai_error}. Using original response.")
            processing_steps.append("⚠️ OpenAI fallback failed, using original response")
    
    # Record metrics
    try:
        from backend.validators.metrics import get_metrics
        metrics = get_metrics()
        overlap_score = 0.0
        for reason in validation_result.reasons:
            if reason.startswith("low_overlap:"):
                try:
                    overlap_score = float(reason.split(":")[1])
                except (ValueError, IndexError):
                    pass
        
        category = None
        if is_philosophical:
            category = "philosophical"
        elif is_religion_roleplay:
            category = "religion_roleplay"
        else:
            question_lower = chat_request.message.lower()
            if any(kw in question_lower for kw in ["rag", "retrieval", "llm", "system", "embedding"]):
                category = "technical"
            elif any(kw in question_lower for kw in ["năm", "năm", "1944", "1954", "conference", "hội nghị"]):
                category = "factual"
        
        has_citations = bool(re.search(r'\[\d+\]', raw_response))
        
        metrics.record_validation(
            passed=validation_result.passed,
            reasons=validation_result.reasons,
            overlap_score=overlap_score,
            confidence_score=confidence_score,
            used_fallback=False,  # Will be updated below if fallback is used
            question=chat_request.message,
            answer=raw_response,
            context_docs_count=len(ctx_docs),
            has_citations=has_citations,
            category=category
        )
    except Exception:
        pass  # metrics not available, skip
    
    # Handle validation failures with FallbackHandler
    # This is a large block of logic - we'll keep it here but organized
    used_fallback = False
    response = raw_response
    
    if not validation_result.passed:
        # Import needed here to avoid circular imports
        from backend.validators.fallback_handler import FallbackHandler
        from backend.api.utils.error_detector import is_fallback_message, get_fallback_message_for_error
        from backend.validators.citation import CitationRequired
        
        # Check for critical failures
        has_language_mismatch = any("language_mismatch" in r for r in validation_result.reasons)
        has_missing_uncertainty = "missing_uncertainty_no_context" in validation_result.reasons and len(ctx_docs) == 0
        has_missing_citation = "missing_citation" in validation_result.reasons and len(ctx_docs) > 0
        
        # Check if response already has transparency
        response_lower = response.lower()
        transparency_indicators = [
            "general knowledge", "training data", "my training", "base knowledge", "pretrained", "pre-trained",
            "not from stillme", "not from rag", "without context", "no context",
            "based on general", "from my training", "from general knowledge",
            "note:", "this answer", "this response",
            "kiến thức chung", "dữ liệu huấn luyện", "kiến thức cơ bản",
            "không từ stillme", "không từ rag", "không có context", "không có ngữ cảnh",
            "dựa trên kiến thức chung", "từ dữ liệu huấn luyện",
            "lưu ý:", "câu trả lời này"
        ]
        has_transparency_in_response = any(indicator in response_lower for indicator in transparency_indicators)
        
        if has_missing_uncertainty and has_transparency_in_response:
            logger.info("✅ Response has transparency about base knowledge - accepting despite missing_uncertainty")
            has_missing_uncertainty = False
        
        has_critical_failure = has_language_mismatch or has_missing_uncertainty
        
        # If patched_answer is available, use it
        if validation_result.patched_answer:
            response = validation_result.patched_answer
            logger.info(f"✅ Using patched answer from validator (auto-fixed). Reasons: {validation_result.reasons}")
            if has_missing_citation and not has_critical_failure:
                validation_result.passed = True
                validation_result.reasons = [r for r in validation_result.reasons if r != "missing_citation"]
        elif has_missing_citation and not has_critical_failure:
            # Try to add citation via CitationRequired
            if not raw_response or not isinstance(raw_response, str) or not raw_response.strip():
                logger.error(f"⚠️ raw_response is None or empty when trying to add citation - using fallback")
                fallback_handler = FallbackHandler()
                response = fallback_handler.get_fallback_answer(
                    original_answer="",
                    validation_result=validation_result,
                    ctx_docs=ctx_docs,
                    user_question=chat_request.message,
                    detected_lang=detected_lang,
                    input_language=detected_lang
                )
                used_fallback = True
            else:
                citation_validator = CitationRequired(required=True)
                citation_result = citation_validator.run(
                    raw_response,
                    ctx_docs,
                    is_philosophical=is_philosophical,
                    user_question=chat_request.message,
                    context=context
                )
                if citation_result.patched_answer:
                    response = citation_result.patched_answer
                    logger.info(f"✅ Added citation via CitationRequired. Reasons: {validation_result.reasons}")
                else:
                    # Fallback to FallbackHandler
                    fallback_handler = FallbackHandler()
                    response = fallback_handler.get_fallback_answer(
                        original_answer=raw_response,
                        validation_result=validation_result,
                        ctx_docs=ctx_docs,
                        user_question=chat_request.message,
                        detected_lang=detected_lang,
                        input_language=detected_lang
                    )
                    if is_fallback_message(response):
                        used_fallback = True
                        # Try to add citation to fallback message
                        citation_validator = CitationRequired(required=True)
                        citation_result = citation_validator.run(
                            response,
                            ctx_docs=ctx_docs,
                            is_philosophical=is_philosophical,
                            user_question=chat_request.message,
                            context=context
                        )
                        if citation_result.patched_answer:
                            response = citation_result.patched_answer
                            logger.info(f"✅ Added citation to fallback message for factual question. Reasons: {citation_result.reasons}")
                    else:
                        logger.info(f"✅ Added citation via FallbackHandler. Reasons: {validation_result.reasons}")
                    
                    if not response or not isinstance(response, str) or not response.strip():
                        logger.error(f"⚠️ Response is None or empty after adding citation - using fallback")
                        response = get_fallback_message_for_error("generic", detected_lang)
                        used_fallback = True
        elif has_critical_failure:
            # For language mismatch, try retry with stronger prompt first
            if has_language_mismatch:
                logger.warning(f"⚠️ Language mismatch detected, attempting retry with stronger prompt...")
                try:
                    language_names = {
                        'vi': 'Tiếng Việt', 'en': 'English', 'zh': '中文', 'fr': 'Français',
                        'es': 'Español', 'de': 'Deutsch', 'ja': '日本語', 'ko': '한국어',
                        'ar': 'العربية', 'ru': 'Русский', 'pt': 'Português', 'it': 'Italiano',
                        'hi': 'हिन्दी', 'th': 'ไทย',
                    }
                    retry_lang_name = language_names.get(detected_lang, detected_lang.upper())
                    
                    retry_language_instruction = f"""🚨🚨🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - ABSOLUTE HIGHEST PRIORITY 🚨🚨🚨🚨🚨

THE USER'S QUESTION IS IN {retry_lang_name.upper()}.

YOU MUST RESPOND EXCLUSIVELY IN {retry_lang_name.upper()}. 

DO NOT USE VIETNAMESE, ENGLISH, FRENCH, CHINESE, SPANISH, GERMAN, OR ANY OTHER LANGUAGE.

EVERY SINGLE WORD MUST BE IN {retry_lang_name.upper()}.

IF YOUR BASE MODEL WANTS TO RESPOND IN ANOTHER LANGUAGE, YOU MUST TRANSLATE IT TO {retry_lang_name.upper()} BEFORE RETURNING.

THIS OVERRIDES EVERYTHING - NO EXCEPTIONS.

{context_text if context and context.get("total_context_docs", 0) > 0 else ""}
{citation_instruction if num_knowledge > 0 else ""}

🚨🚨🚨 CRITICAL: USER QUESTION ABOVE IS THE PRIMARY TASK 🚨🚨🚨

User Question (in {retry_lang_name.upper()}): {chat_request.message[:3000]}

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

Remember: RESPOND IN {retry_lang_name.upper()} ONLY. TRANSLATE IF NECESSARY. ANSWER THE QUESTION PROPERLY, NOT JUST ACKNOWLEDGE THE ERROR."""
                    
                    use_server_keys_retry = chat_request.llm_provider is None
                    retry_response = await generate_ai_response(
                        retry_language_instruction,
                        detected_lang=detected_lang,
                        llm_provider=chat_request.llm_provider,
                        llm_api_key=chat_request.llm_api_key,
                        use_server_keys=use_server_keys_retry
                    )
                    
                    retry_validation = chain.run(retry_response, ctx_docs, context=context)
                    retry_has_lang_mismatch = any("language_mismatch" in r for r in retry_validation.reasons)
                    
                    if not retry_has_lang_mismatch:
                        response = retry_validation.patched_answer or retry_response
                        logger.info(f"✅ Language mismatch fixed with retry! Using retry response.")
                    else:
                        logger.warning(f"⚠️ Retry also failed with language mismatch, using fallback")
                        fallback_handler = FallbackHandler()
                        response = fallback_handler.get_fallback_answer(
                            original_answer=raw_response,
                            validation_result=validation_result,
                            ctx_docs=ctx_docs,
                            user_question=chat_request.message,
                            detected_lang=detected_lang,
                            input_language=detected_lang
                        )
                        used_fallback = True
                        if is_fallback_message(response):
                            citation_validator = CitationRequired(required=True)
                            citation_result = citation_validator.run(
                                response,
                                ctx_docs=ctx_docs,
                                is_philosophical=is_philosophical,
                                user_question=chat_request.message,
                                context=context
                            )
                            if citation_result.patched_answer:
                                response = citation_result.patched_answer
                                logger.info(f"✅ Added citation to fallback message for factual question (language mismatch). Reasons: {citation_result.reasons}")
                except Exception as retry_error:
                    logger.error(f"Retry failed: {retry_error}, using fallback")
                    fallback_handler = FallbackHandler()
                    response = fallback_handler.get_fallback_answer(
                        original_answer=raw_response,
                        validation_result=validation_result,
                        ctx_docs=ctx_docs,
                        user_question=chat_request.message,
                        detected_lang=detected_lang,
                        input_language=detected_lang
                    )
                    used_fallback = True
                    if is_fallback_message(response):
                        citation_validator = CitationRequired(required=True)
                        citation_result = citation_validator.run(
                            response,
                            ctx_docs=ctx_docs,
                            is_philosophical=is_philosophical,
                            user_question=chat_request.message,
                            context=context
                        )
                        if citation_result.patched_answer:
                            response = citation_result.patched_answer
                            logger.info(f"✅ Added citation to fallback message for factual question (retry error). Reasons: {citation_result.reasons}")
            else:
                # Other critical failures - use fallback
                fallback_handler = FallbackHandler()
                response = fallback_handler.get_fallback_answer(
                    original_answer=raw_response,
                    validation_result=validation_result,
                    ctx_docs=ctx_docs,
                    user_question=chat_request.message,
                    detected_lang=detected_lang,
                    input_language=detected_lang
                )
                used_fallback = True
                logger.warning(f"⚠️ Validation failed with critical failure, using fallback answer. Reasons: {validation_result.reasons}")
                if is_fallback_message(response):
                    citation_validator = CitationRequired(required=True)
                    citation_result = citation_validator.run(
                        response,
                        ctx_docs=ctx_docs,
                        is_philosophical=is_philosophical,
                        user_question=chat_request.message,
                        context=context
                    )
                    if citation_result.patched_answer:
                        response = citation_result.patched_answer
                        logger.info(f"✅ Added citation to fallback message for factual question (critical failure). Reasons: {citation_result.reasons}")
        else:
            # For non-critical validation failures, check if they're just warnings
            has_identity_warnings_only = any(
                r.startswith("identity_warning:") for r in validation_result.reasons
            ) and not any(
                r.startswith("identity_violation:") for r in validation_result.reasons
            )
            
            has_only_warnings = (
                has_identity_warnings_only or
                any("citation_relevance_warning" in r for r in validation_result.reasons) or
                (any("low_overlap" in r for r in validation_result.reasons) and len(ctx_docs) > 0)
            ) and not any(
                r.startswith("identity_violation:") or
                r.startswith("missing_citation") or
                r.startswith("language_mismatch") or
                r.startswith("missing_uncertainty")
                for r in validation_result.reasons
            )
            
            if has_only_warnings:
                logger.info(f"✅ Validation has only warnings (not violations), accepting response. Reasons: {validation_result.reasons}")
                response = raw_response
                response = append_validation_warnings_to_response(
                    response=response,
                    validation_result=validation_result,
                    confidence_score=confidence_score,
                    context=context,
                    detected_lang=detected_lang
                )
            else:
                logger.warning(f"Validation failed but returning response anyway. Reasons: {validation_result.reasons}")
                response = raw_response
    else:
        # Validation passed
        if validation_result.patched_answer:
            response = validation_result.patched_answer
            logger.debug(f"✅ Validation passed. Using patched_answer. Reasons: {validation_result.reasons}")
        elif raw_response:
            response = raw_response
            logger.debug(f"✅ Validation passed. Using raw_response. Reasons: {validation_result.reasons}")
        else:
            logger.error(f"🚨 CRITICAL: Both patched_answer and raw_response are None after validation passed!")
            from backend.api.utils.error_detector import get_fallback_message_for_error
            response = get_fallback_message_for_error("generic", detected_lang)
            used_fallback = True
            logger.error(f"🚨 Using fallback message due to None response")
    
    # Ensure response is never None or empty
    if not response or not isinstance(response, str) or not response.strip():
        logger.error(f"⚠️ Response is None or empty after validation (raw_response length: {len(raw_response) if raw_response else 0}) - using fallback")
        from backend.api.utils.error_detector import get_fallback_message_for_error
        response = get_fallback_message_for_error("generic", detected_lang)
        used_fallback = True
    
    # Add transparency warning for low confidence responses without context
    from backend.api.utils.error_detector import is_fallback_message
    is_fallback_meta = is_fallback_message(response) if response else False
    
    if response:
        response_lower = response.lower()
        is_safe_refusal = any(
            phrase in response_lower for phrase in [
                "không tìm thấy bất kỳ nguồn đáng tin cậy nào",
                "cannot find any reliable evidence",
                "không thể mô tả các lập luận chính hay tác động lịch sử",
                "cannot truthfully describe the main arguments or historical impacts",
                "có thể đây là ví dụ giả định",
                "this could be a hypothetical example"
            ]
        )
    else:
        is_safe_refusal = False
    
    if (confidence_score < 0.5 and len(ctx_docs) == 0 and not is_philosophical and 
        not is_fallback_meta and not is_safe_refusal and not is_origin_query and not is_stillme_query):
        response_lower = response.lower()
        has_transparency = any(
            phrase in response_lower for phrase in [
                "không có dữ liệu", "không có thông tin", "kiến thức chung", "dựa trên kiến thức",
                "don't have data", "don't have information", "general knowledge", "based on knowledge",
                "không từ stillme", "not from stillme", "không từ rag", "not from rag"
            ]
        )
        
        if not has_transparency:
            if detected_lang == 'vi':
                disclaimer = "⚠️ Lưu ý: Câu trả lời này dựa trên kiến thức chung từ training data, không có context từ RAG. Mình không chắc chắn về độ chính xác.\n\n"
            else:
                disclaimer = "⚠️ Note: This answer is based on general knowledge from training data, not from RAG context. I'm not certain about its accuracy.\n\n"
            
            response = disclaimer + response
            logger.info("ℹ️ Added transparency disclaimer for low confidence response without context")
    
    # Build validation info for response
    validation_info = {
        "passed": validation_result.passed,
        "reasons": validation_result.reasons,
        "used_fallback": used_fallback,
        "confidence_score": confidence_score,
        "context_docs_count": len(ctx_docs),
        "step_validation": step_validation_info,
        "consistency": consistency_info
    }
    
    return response, validation_info, confidence_score, used_fallback, step_validation_info, consistency_info, ctx_docs

