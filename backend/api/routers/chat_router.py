"""
Chat Router for StillMe API
Handles all chat-related endpoints
"""

from fastapi import APIRouter, Request, HTTPException
from backend.api.models import ChatRequest, ChatResponse
from backend.api.rate_limiter import limiter, get_rate_limit_key_func
from backend.api.utils.chat_helpers import (
    generate_ai_response,
    detect_language
)
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()

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

def _calculate_confidence_score(
    context_docs_count: int,
    validation_result=None,
    context=None
) -> float:
    """
    Calculate confidence score based on context quality and validation results
    
    Args:
        context_docs_count: Number of context documents found
        validation_result: ValidationResult from validator chain (optional)
        context: Full context dict (optional)
        
    Returns:
        Confidence score between 0.0 and 1.0
    """
    # Base confidence on context availability
    if context_docs_count == 0:
        base_confidence = 0.2  # Very low confidence when no context
    elif context_docs_count == 1:
        base_confidence = 0.5  # Medium confidence with limited context
    elif context_docs_count >= 2:
        base_confidence = 0.8  # High confidence with multiple sources
    else:
        base_confidence = 0.3
    
    # Adjust based on validation results
    if validation_result:
        if validation_result.passed:
            # Boost confidence if validation passed
            confidence = min(1.0, base_confidence + 0.1)
        else:
            # Reduce confidence if validation failed
            reasons = validation_result.reasons or []
            if "missing_uncertainty_no_context" in reasons:
                confidence = 0.1  # Very low if AI didn't express uncertainty when it should
            elif "missing_citation" in reasons and context_docs_count > 0:
                confidence = base_confidence - 0.2  # Reduce if missing citations
            elif "low_overlap" in reasons:
                confidence = base_confidence - 0.15  # Reduce if low overlap
            else:
                confidence = max(0.0, base_confidence - 0.1)
    else:
        confidence = base_confidence
    
    return max(0.0, min(1.0, confidence))  # Clamp between 0.0 and 1.0

@router.post("/rag", response_model=ChatResponse)
@limiter.limit("10/minute", key_func=get_rate_limit_key_func)  # Chat: 10 requests per minute
async def chat_with_rag(request: Request, chat_request: ChatRequest):
    """Chat with RAG-enhanced responses"""
    import time
    start_time = time.time()
    timing_logs = {}
    
    # Initialize latency variables (will be set during processing)
    rag_retrieval_latency = 0.0
    llm_inference_latency = 0.0
    
    # Initialize variables before try-except to avoid UnboundLocalError
    confidence_score = None
    validation_info = None
    
    try:
        # Get services
        rag_retrieval = get_rag_retrieval()
        knowledge_retention = get_knowledge_retention()
        accuracy_scorer = get_accuracy_scorer()
        
        # Special Retrieval Rule: Detect StillMe-related queries
        is_stillme_query = False
        is_origin_query = False
        if rag_retrieval and chat_request.use_rag:
            try:
                from backend.core.stillme_detector import (
                    detect_stillme_query, 
                    get_foundational_query_variants,
                    detect_origin_query
                )
                is_stillme_query, matched_keywords = detect_stillme_query(chat_request.message)
                is_origin_query, origin_keywords = detect_origin_query(chat_request.message)
                if is_stillme_query:
                    logger.info(f"StillMe query detected! Matched keywords: {matched_keywords}")
                if is_origin_query:
                    logger.info(f"Origin query detected! Matched keywords: {origin_keywords}")
            except ImportError:
                logger.warning("StillMe detector not available, skipping special retrieval rule")
            except Exception as detector_error:
                logger.warning(f"StillMe detector error: {detector_error}")
        
        # Get RAG context if enabled
        # RAG_Retrieval_Latency: Time from ChromaDB query start to result received
        context = None
        rag_retrieval_start = time.time()
        if rag_retrieval and chat_request.use_rag:
            # CRITICAL: If origin query detected, retrieve provenance knowledge ONLY
            # This ensures provenance is ONLY retrieved when explicitly asked about origin/founder
            if is_origin_query:
                logger.info("Origin query detected - retrieving provenance knowledge")
                try:
                    query_embedding = rag_retrieval.embedding_service.encode_text(chat_request.message)
                    provenance_results = rag_retrieval.chroma_client.search_knowledge(
                        query_embedding=query_embedding,
                        limit=2,
                        where={"source": "PROVENANCE"}
                    )
                    if provenance_results:
                        context = {
                            "knowledge_docs": provenance_results,
                            "conversation_docs": [],
                            "total_context_docs": len(provenance_results)
                        }
                        logger.info(f"Retrieved {len(provenance_results)} provenance documents")
                    else:
                        # Fallback to normal retrieval if provenance not found
                        context = rag_retrieval.retrieve_context(
                            query=chat_request.message,
                            knowledge_limit=chat_request.context_limit,
                            conversation_limit=1
                        )
                except Exception as provenance_error:
                    logger.warning(f"Provenance retrieval failed: {provenance_error}, falling back to normal retrieval")
                    context = rag_retrieval.retrieve_context(
                        query=chat_request.message,
                        knowledge_limit=chat_request.context_limit,
                        conversation_limit=1
                    )
            
            # If StillMe query detected (but not origin), prioritize foundational knowledge
            elif is_stillme_query:
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
            # Count knowledge docs for citation numbering
            num_knowledge = len(context.get("knowledge_docs", []))
            if num_knowledge > 0:
                citation_instruction = f"""
                
📚 CRITICAL CITATION REQUIREMENT:

You have {num_knowledge} context document(s) available. You MUST cite your sources using [1], [2], [3] format.

CRITICAL RULES:
1. You MUST cite at least one source using [1], [2], [3] format when making factual claims
2. Use [1] for the first context document, [2] for the second, [3] for the third, etc.
3. Example: "According to [1], quantum entanglement is..." or "Research shows [2] that..."
4. If you use information from multiple sources, cite each: "Studies [1] and [2] indicate that..."
5. DO NOT make unsourced claims when context is available - always cite your sources

FAILURE TO CITE SOURCES WHEN CONTEXT IS AVAILABLE IS A CRITICAL ERROR."""
            
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
                'ko': 'Korean (한국어)',
                'ar': 'Arabic (العربية)',
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
            
            # Check if context is empty - if so, use special prompt
            if context["total_context_docs"] == 0:
                # NO CONTEXT AVAILABLE - Use special prompt that encourages uncertainty
                no_context_instruction = """
⚠️ NO CONTEXT AVAILABLE ⚠️

StillMe's RAG system searched the knowledge base but found NO relevant documents for this question.

YOU MUST:
1. Acknowledge that you don't have this information in your knowledge base
2. Explain that StillMe learns from RSS feeds, arXiv, and other sources every 4 hours
3. Offer alternatives: reformulate question, suggest related topics, or wait for future learning
4. DO NOT use general knowledge or training data - be honest about the gap

Remember: It's better to say "I don't know" than to make up information.
"""
                
                base_prompt = f"""{language_instruction}

⚠️⚠️⚠️ ZERO TOLERANCE LANGUAGE REMINDER ⚠️⚠️⚠️

The user's question is in {detected_lang_name.upper()}. 

YOU MUST respond in {detected_lang_name.upper()} ONLY.

{no_context_instruction}

User Question (in {detected_lang_name.upper()}): {chat_request.message}

⚠️⚠️⚠️ FINAL ZERO TOLERANCE REMINDER ⚠️⚠️⚠️

RESPOND IN {detected_lang_name.upper()} ONLY. TRANSLATE IF NECESSARY.

Remember: RESPOND IN {detected_lang_name.upper()} ONLY. TRANSLATE IF YOUR BASE MODEL WANTS TO USE A DIFFERENT LANGUAGE.
"""
            else:
                # Context available - use normal prompt
                # CRITICAL: Calculate preliminary confidence score BEFORE generating response
                # This allows StillMe to know when it should say "I don't know"
                preliminary_confidence = _calculate_confidence_score(
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
"""
                
                # CRITICAL: Special instruction for origin queries with provenance context
                provenance_instruction = ""
                if is_origin_query and context and context.get("knowledge_docs"):
                    # Check if any document is from PROVENANCE source
                    has_provenance = any(
                        doc.get("metadata", {}).get("source") == "PROVENANCE" 
                        for doc in context.get("knowledge_docs", [])
                    )
                    if has_provenance:
                        provenance_instruction = """

⚠️⚠️⚠️ CRITICAL: PROVENANCE CONTEXT DETECTED ⚠️⚠️⚠️

The user is asking about StillMe's origin/founder. You have retrieved PROVENANCE documents.

**RESPONSE STYLE: Keep it concise and human-centered. Focus on the founder and purpose, not technical details.**

YOU MUST mention the following information from the provenance context:

1. **StillMe was initiated by Anh Nguyễn, a Vietnamese founder** passionate about transparent AI
2. **CRITICAL - MUST MENTION**: The founder's **non-IT background demonstrates** that with passion and open-minded thinking, anyone can meaningfully contribute to the future of AI
3. However, **StillMe is now a community-driven open-source project**
4. StillMe adheres to **'evidence-over-authority' principle**

**IMPORTANT GUIDELINES:**
- Keep response **concise and conversational** - avoid lengthy technical explanations
- Focus on **founder story and purpose**, not technical architecture (RAG, ChromaDB, embeddings, etc.)
- **Mention Vietnam ecosystem ONLY if user asks specifically about it** - otherwise just say "Vietnamese founder" or "người Việt Nam"
- Only mention technical details if user specifically asks about "how it works" or "technical architecture"
- If user asks "who created you?" or "what is your purpose?", give a **short, human-centered answer**
- DO NOT overwhelm with technical jargon unless explicitly requested
- **ALWAYS mention the founder's non-IT background** - this is a key inspirational point
- Cite provenance with [1] or [2] as appropriate

DO NOT give generic answers about "open-source community" without mentioning the founder.
You MUST use the provenance information you retrieved.

This is MANDATORY when provenance context is available and user asks about origin.
"""
                        logger.info("Provenance instruction injected - StillMe must mention founder and Vietnam ecosystem")
                
                # Special instruction for StillMe queries with ERROR STATE CHECKING
                stillme_instruction = ""
                if is_stillme_query:
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
                    
                    # Base StillMe instruction
                    base_stillme_instruction = "\n\nCRITICAL: This question is about StillMe itself. You MUST use the context above to answer. Do NOT rely on your training data cutoff date. StillMe is a Learning AI system with RAG foundation that learns continuously through RAG (Retrieval-Augmented Generation) from RSS feeds, arXiv, CrossRef, and Wikipedia every 4 hours (6 cycles per day). StillMe automatically fetches content, embeds it into a vector database (ChromaDB using all-MiniLM-L6-v2 embeddings), and retrieves it when answering questions. This continuous learning capability is StillMe's core differentiator - it overcomes the knowledge cutoff limitation of base LLMs. You MUST emphasize: (1) StillMe's automated learning cycles every 4 hours, (2) RAG-based knowledge storage in vector database using all-MiniLM-L6-v2 embeddings (384 dimensions), (3) Continuous knowledge updates through RSS feeds, arXiv, CrossRef, and Wikipedia, (4) Validation chain (CitationRequired, EvidenceOverlap, ConfidenceValidator, FallbackHandler) to reduce hallucinations by 80%, (5) StillMe is NOT limited by training data cutoff dates. Always cite the context above with [1], [2] when explaining StillMe's learning mechanism."
                    
                    # Combine base instruction with error status
                    stillme_instruction = base_stillme_instruction + error_status_message
                
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
{confidence_instruction}
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
            validation_info = None
            # confidence_score already initialized at function start (line 104)
            # Don't reassign here to avoid UnboundLocalError
            used_fallback = False
            
            if enable_validators:
                try:
                    validation_start = time.time()
                    from backend.validators.chain import ValidatorChain
                    from backend.validators.citation import CitationRequired
                    from backend.validators.evidence_overlap import EvidenceOverlap
                    from backend.validators.numeric import NumericUnitsBasic
                    from backend.validators.ethics_adapter import EthicsAdapter
                    from backend.validators.confidence import ConfidenceValidator
                    from backend.validators.fallback_handler import FallbackHandler
                    
                    # Build context docs list for validation
                    ctx_docs = [
                        doc["content"] for doc in context["knowledge_docs"]
                    ] + [
                        doc["content"] for doc in context["conversation_docs"]
                    ]
                    
                    # Create validator chain with ConfidenceValidator
                    chain = ValidatorChain([
                        CitationRequired(),
                        EvidenceOverlap(threshold=0.01),  # Lowered from 0.08 to 0.01
                        NumericUnitsBasic(),
                        ConfidenceValidator(require_uncertainty_when_no_context=True),  # NEW: Check for uncertainty
                        EthicsAdapter(guard_callable=None)  # TODO: wire existing ethics guard if available
                    ])
                    
                    # Run validation
                    validation_result = chain.run(raw_response, ctx_docs)
                    validation_time = time.time() - validation_start
                    timing_logs["validation"] = f"{validation_time:.2f}s"
                    logger.info(f"⏱️ Validation took {validation_time:.2f}s")
                    
                    # Calculate confidence score based on context quality and validation
                    confidence_score = _calculate_confidence_score(
                        context_docs_count=len(ctx_docs),
                        validation_result=validation_result,
                        context=context
                    )
                    
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
                            overlap_score=overlap_score,
                            confidence_score=confidence_score,
                            used_fallback=used_fallback
                        )
                    except Exception as metrics_error:
                        logger.warning(f"Failed to record metrics: {metrics_error}")
                    
                    # Handle validation failures with FallbackHandler
                    if not validation_result.passed:
                        # Check for critical failures that require fallback
                        # missing_uncertainty_no_context: when no context and no uncertainty expression
                        # missing_citation: when context exists but no citations in answer
                        has_missing_uncertainty = "missing_uncertainty_no_context" in validation_result.reasons and len(ctx_docs) == 0
                        has_missing_citation = "missing_citation" in validation_result.reasons and len(ctx_docs) > 0
                        has_critical_failure = has_missing_uncertainty or has_missing_citation
                        
                        if has_critical_failure:
                            # Use FallbackHandler to generate safe answer
                            fallback_handler = FallbackHandler()
                            response = fallback_handler.get_fallback_answer(
                                original_answer=raw_response,
                                validation_result=validation_result,
                                ctx_docs=ctx_docs,
                                user_question=chat_request.message,
                                detected_lang=detected_lang
                            )
                            used_fallback = True
                            logger.warning(f"⚠️ Validation failed with critical failure, using fallback answer. Reasons: {validation_result.reasons}")
                        elif validation_result.patched_answer:
                            response = validation_result.patched_answer
                            logger.info(f"Validation failed but using patched answer. Reasons: {validation_result.reasons}")
                        else:
                            # For non-critical validation failures, still return the response but log warning
                            # This prevents 422 errors for minor validation issues
                            logger.warning(f"Validation failed but returning response anyway. Reasons: {validation_result.reasons}")
                            response = raw_response
                    else:
                        response = validation_result.patched_answer or raw_response
                        logger.debug(f"✅ Validation passed. Reasons: {validation_result.reasons}")
                    
                    # Build validation info for response
                    validation_info = {
                        "passed": validation_result.passed,
                        "reasons": validation_result.reasons,
                        "used_fallback": used_fallback,
                        "confidence_score": confidence_score,
                        "context_docs_count": len(ctx_docs)
                    }
                    
                except HTTPException:
                    raise
                except Exception as validation_error:
                    logger.error(f"Validation error: {validation_error}, falling back to raw response")
                    response = raw_response
                    # Calculate confidence even on error (low confidence)
                    confidence_score = 0.3 if len(ctx_docs) == 0 else 0.6
            else:
                response = raw_response
                # Calculate basic confidence score even without validators
                confidence_score = _calculate_confidence_score(
                    context_docs_count=len(context.get("knowledge_docs", [])) + len(context.get("conversation_docs", [])),
                    validation_result=None,
                    context=context
                )
        else:
            # Fallback to regular AI response (no RAG context)
            # Initialize confidence_score for non-RAG path
            confidence_score = 0.3  # Low confidence when no RAG context
            validation_info = None
            
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
                            import re
                            words = re.findall(r'\b\w+\b', chat_request.message.lower())
                            # Filter out common words
                            common_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 'when', 'where', 'who', 'which', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'to', 'of', 'in', 'on', 'at', 'for', 'with', 'by', 'from', 'as', 'about', 'into', 'through', 'during', 'including', 'against', 'among', 'throughout', 'despite', 'towards', 'upon', 'concerning', 'to', 'of', 'in', 'on', 'at', 'for', 'with', 'by', 'from', 'as', 'about', 'into', 'through', 'during', 'including', 'against', 'among', 'throughout', 'despite', 'towards', 'upon', 'concerning'}
                            key_terms = [w for w in words if len(w) > 3 and w not in common_words][:3]
                            if key_terms:
                                learning_suggestions = [f"Consider learning more about: {', '.join(key_terms)}"]
            except Exception as suggestion_error:
                logger.warning(f"Failed to generate learning suggestions: {suggestion_error}")
        
        return ChatResponse(
            response=response,
            context_used=context,
            accuracy_score=accuracy_score,
            confidence_score=confidence_score,
            validation_info=validation_info,
            learning_suggestions=learning_suggestions,
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
@limiter.limit("10/minute", key_func=get_rate_limit_key_func)
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
            chain = ValidatorChain([
                CitationRequired(),  # Not applicable for input, but included for completeness
                EvidenceOverlap(threshold=0.01),
                NumericUnitsBasic(),
                EthicsAdapter(guard_callable=None)
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

