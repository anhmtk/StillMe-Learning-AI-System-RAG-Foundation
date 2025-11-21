"""
Option B Pipeline Integration Helper

This module provides a unified interface to process questions through
the Option B pipeline (zero-tolerance hallucination + deep philosophy).

INTEGRATED: Uses Style Engine (backend/style/style_engine.py) for domain detection
and template selection according to StillMe Style Spec v1.

Usage:
    from backend.core.option_b_pipeline import process_with_option_b
    
    response = await process_with_option_b(
        question=user_question,
        use_rag=True,
        detected_lang="vi"
    )
"""

import logging
from typing import Optional, Dict, Any, List
import time

logger = logging.getLogger(__name__)


async def process_with_option_b(
    question: str,
    use_rag: bool = True,
    detected_lang: str = "en",
    rag_retrieval=None,
    ctx_docs: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Process question through Option B pipeline
    
    Pipeline:
    1. Question Classifier V2
    2. FPS (Pre-LLM) - Block if suspicious
    3. RAG Retrieval (if enabled)
    4. LLM Raw Answer
    5. Hallucination Guard V2
    6. Rewrite 1 - Honesty & Boundary
    7. Rewrite 2 - Philosophical Depth
    8. Tone Alignment
    
    Args:
        question: User question
        use_rag: Whether to use RAG
        detected_lang: Detected language code
        rag_retrieval: RAG retrieval service (optional)
        ctx_docs: Pre-retrieved context documents (optional)
        
    Returns:
        Dict with:
            - response: Final response text
            - question_type: Question type from classifier
            - hallucination_detected: Whether hallucination was detected
            - used_fallback: Whether EPD-Fallback was used
            - processing_steps: List of processing steps
            - timing_logs: Timing information
    """
    start_time = time.time()
    processing_steps = []
    timing_logs = {}
    
    try:
        # Step 1: Question Classifier V2
        classifier_start = time.time()
        from backend.core.question_classifier_v2 import get_question_classifier_v2
        classifier = get_question_classifier_v2()
        question_type, confidence, detected_patterns = classifier.classify(question)
        is_suspected_fabricated, suspicious_patterns = classifier.is_suspected_fabricated(question)
        
        processing_steps.append(f"✅ Question classified: {question_type.value} (confidence: {confidence:.2f})")
        if is_suspected_fabricated:
            processing_steps.append(f"⚠️ Suspicious patterns detected: {suspicious_patterns}")
        
        timing_logs["question_classification"] = time.time() - classifier_start
        
        # Step 2: FPS (Pre-LLM) - Block if suspicious
        fps_start = time.time()
        from backend.knowledge.factual_scanner import scan_question
        fps_result = scan_question(question)
        
        if not fps_result.is_plausible and fps_result.confidence < 0.3:
            # Block immediately, return EPD-Fallback
            logger.warning(
                f"🛡️ FPS blocked question: {fps_result.reason}, "
                f"confidence={fps_result.confidence:.2f}"
            )
            
            from backend.guards.epistemic_fallback import get_epistemic_fallback_generator
            generator = get_epistemic_fallback_generator()
            
            suspicious_entity = (
                fps_result.detected_entities[0] 
                if fps_result.detected_entities 
                else None
            )
            
            fallback_text = generator.generate_epd_fallback(
                question=question,
                detected_lang=detected_lang,
                suspicious_entity=suspicious_entity,
                fps_result=fps_result
            )
            
            processing_steps.append("🛡️ FPS blocked - returned EPD-Fallback")
            timing_logs["fps_scan"] = time.time() - fps_start
            timing_logs["total_time"] = time.time() - start_time
            
            return {
                "response": fallback_text,
                "question_type": question_type.value,
                "hallucination_detected": True,
                "used_fallback": True,
                "processing_steps": processing_steps,
                "timing_logs": timing_logs
            }
        
        timing_logs["fps_scan"] = time.time() - fps_start
        
        # Step 3: RAG Retrieval (if enabled and not already retrieved)
        if use_rag and rag_retrieval and ctx_docs is None:
            rag_start = time.time()
            try:
                context = rag_retrieval.retrieve_context(
                    query=question,
                    knowledge_limit=5,
                    conversation_limit=1,
                    is_philosophical=(question_type.value == "philosophical_meta")
                )
                ctx_docs = context.get("knowledge_docs", [])
                processing_steps.append(f"🔍 RAG retrieved: {len(ctx_docs)} documents")
            except Exception as e:
                logger.warning(f"RAG retrieval error: {e}")
                ctx_docs = []
            timing_logs["rag_retrieval"] = time.time() - rag_start
        else:
            ctx_docs = ctx_docs or []
        
        # Step 4: LLM Raw Answer (Draft)
        # NOTE: This is a placeholder - actual LLM call should be done in chat_router
        # For now, we'll skip this step and assume the LLM response is provided
        # In actual integration, this would call the LLM here
        
        # For now, return a placeholder indicating Option B pipeline is ready
        # Actual integration will require modifying chat_router to use this pipeline
        
        processing_steps.append("⚠️ LLM Raw Answer: Placeholder (requires chat_router integration)")
        timing_logs["total_time"] = time.time() - start_time
        
        return {
            "response": None,  # Placeholder - requires LLM call
            "question_type": question_type.value,
            "hallucination_detected": False,
            "used_fallback": False,
            "processing_steps": processing_steps,
            "timing_logs": timing_logs,
            "note": "Option B pipeline ready - requires chat_router integration for LLM call"
        }
        
    except Exception as e:
        logger.error(f"❌ Option B pipeline error: {e}", exc_info=True)
        return {
            "response": None,
            "error": str(e),
            "processing_steps": processing_steps,
            "timing_logs": timing_logs
        }


async def process_llm_response_with_option_b(
    llm_response: str,
    question: str,
    question_type: str,
    ctx_docs: List[str],
    detected_lang: str = "en",
    fps_result: Optional[object] = None
) -> Dict[str, Any]:
    """
    Process LLM response through Option B pipeline (Steps 5-8)
    
    This function is called AFTER LLM generates raw response.
    It applies:
    - Hallucination Guard V2
    - Rewrite 1 - Honesty & Boundary
    - Rewrite 2 - Philosophical Depth
    
    Args:
        llm_response: Raw LLM response
        question: Original user question
        question_type: Question type from classifier
        ctx_docs: Context documents from RAG
        detected_lang: Detected language code
        fps_result: FPS scan result (optional)
        
    Returns:
        Dict with final response and processing info
    """
    start_time = time.time()
    processing_steps = []
    timing_logs = {}
    
    try:
        # Step 5: Hallucination Guard V2
        guard_start = time.time()
        from backend.guards.hallucination_guard_v2 import get_hallucination_guard_v2
        guard = get_hallucination_guard_v2()
        
        hallucination_detection = guard.detect(
            answer=llm_response,
            user_question=question,
            ctx_docs=ctx_docs,
            question_type=question_type,
            fps_result=fps_result
        )
        
        if hallucination_detection.is_hallucination:
            processing_steps.append(
                f"🛡️ Hallucination detected: {', '.join(hallucination_detection.reasons[:2])}"
            )
        else:
            processing_steps.append("✅ Hallucination Guard: No issues detected")
        
        guard_time = time.time() - guard_start
        timing_logs["hallucination_guard"] = f"{guard_time:.3f}s"
        
        # Step 6: Rewrite 1 - Honesty & Boundary
        rewrite1_start = time.time()
        from backend.postprocessing.rewrite_honesty import get_rewrite_honesty
        rewrite1 = get_rewrite_honesty()
        
        honesty_result = await rewrite1.rewrite(
            text=llm_response,
            original_question=question,
            hallucination_detection=hallucination_detection,
            ctx_docs=ctx_docs,
            question_type=question_type,
            detected_lang=detected_lang
        )
        
        if honesty_result.was_rewritten:
            if honesty_result.used_fallback:
                processing_steps.append("🔄 Rewrite 1: Used EPD-Fallback")
            else:
                processing_steps.append("🔄 Rewrite 1: Removed contradiction")
        else:
            processing_steps.append("✅ Rewrite 1: No changes needed")
        
        rewrite1_time = time.time() - rewrite1_start
        timing_logs["rewrite1_honesty"] = f"{rewrite1_time:.3f}s"
        
        # Step 7: Rewrite 2 - Philosophical Depth (only if not fallback)
        rewrite2_start = time.time()
        final_response = honesty_result.text
        
        if not honesty_result.used_fallback:
            from backend.postprocessing.rewrite_philosophical_depth import get_rewrite_philosophical_depth
            rewrite2 = get_rewrite_philosophical_depth()
            
            depth_result = await rewrite2.rewrite(
                text=final_response,
                original_question=question,
                question_type=question_type,
                detected_lang=detected_lang,
                is_fallback=False
            )
            
            if depth_result.was_rewritten:
                final_response = depth_result.text
                processing_steps.append("🔄 Rewrite 2: Added philosophical depth")
            else:
                processing_steps.append("✅ Rewrite 2: No changes needed")
        else:
            processing_steps.append("⏭️ Rewrite 2: Skipped (already EPD-Fallback)")
        
        rewrite2_time = time.time() - rewrite2_start
        total_time = time.time() - start_time
        timing_logs["rewrite2_depth"] = f"{rewrite2_time:.3f}s"
        timing_logs["total_time"] = f"{total_time:.3f}s"
        
        return {
            "response": final_response,
            "question_type": question_type,
            "hallucination_detected": hallucination_detection.is_hallucination,
            "used_fallback": honesty_result.used_fallback,
            "processing_steps": processing_steps,
            "timing_logs": timing_logs
        }
        
    except Exception as e:
        logger.error(f"❌ Option B post-processing error: {e}", exc_info=True)
        return {
            "response": llm_response,  # Return original if error
            "error": str(e),
            "processing_steps": processing_steps,
            "timing_logs": timing_logs
        }

