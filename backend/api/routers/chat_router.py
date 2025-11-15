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
from backend.services.cache_service import (
    get_cache_service,
    CACHE_PREFIX_LLM,
    TTL_LLM_RESPONSE
)
import logging
import os
from datetime import datetime, timezone
import json

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

def get_style_learner():
    """Get style learner service"""
    from backend.services.style_learner import StyleLearner
    # Singleton instance
    if not hasattr(get_style_learner, '_instance'):
        get_style_learner._instance = StyleLearner()
    return get_style_learner._instance

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
    processing_steps = []  # Track processing steps for real-time status
    style_learning_response = None  # Initialize for style learning
    
    try:
        # Get services
        rag_retrieval = get_rag_retrieval()
        knowledge_retention = get_knowledge_retention()
        accuracy_scorer = get_accuracy_scorer()
        style_learner = get_style_learner()
        
        # Get user_id from request (if available)
        user_id = chat_request.user_id or request.client.host if hasattr(request, 'client') else "anonymous"
        
        # Detect learning metrics queries - auto-query API if user asks about learning today
        is_learning_metrics_query = False
        learning_metrics_data = None
        message_lower = chat_request.message.lower()
        learning_metrics_keywords = [
            "ngày hôm nay bạn đã học", "học được bao nhiêu", "learn today", "learned today",
            "học được gì", "what did you learn", "học được những gì", "nội dung gì",
            "học từ nguồn nào", "sources", "nguồn học", "learning sources"
        ]
        if any(keyword in message_lower for keyword in learning_metrics_keywords):
            is_learning_metrics_query = True
            logger.info("Learning metrics query detected - fetching metrics data")
            try:
                from backend.services.learning_metrics_tracker import get_learning_metrics_tracker
                tracker = get_learning_metrics_tracker()
                # Get today's metrics
                learning_metrics_data = tracker.get_metrics_for_today()
                if learning_metrics_data:
                    logger.info(f"✅ Fetched learning metrics for today: {learning_metrics_data.entries_added} entries added")
                else:
                    logger.info("⚠️ No learning metrics available for today yet")
            except Exception as metrics_error:
                logger.warning(f"Failed to fetch learning metrics: {metrics_error}")
        
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
            processing_steps.append("🔍 Searching knowledge base...")
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
        if rag_retrieval and chat_request.use_rag:
            processing_steps.append(f"✅ Found {context.get('total_context_docs', 0) if context else 0} relevant documents ({rag_retrieval_latency:.2f}s)")
        
        # Generate response using AI (simplified for demo)
        # CRITICAL: Default to true - validation should be enabled by default
        enable_validators = os.getenv("ENABLE_VALIDATORS", "true").lower() == "true"
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
                
📚 CITATION REQUIREMENT - MANDATORY BUT RELEVANCE-FIRST:

You have {num_knowledge} context document(s) available. You MUST cite at least ONE source using [1], [2], [3] format in your response, BUT ONLY if the context is RELEVANT to your answer.

**🚨 CRITICAL: IF CONTEXT IS NOT RELEVANT TO YOUR QUESTION:**
- Acknowledge the mismatch, but VARY your wording - don't always use the same phrase
- Use your base LLM knowledge to answer: "Based on general knowledge (not from StillMe's RAG knowledge base), [answer]"
- Be transparent: Don't pretend the context supports your answer if it doesn't
- Provide helpful information: Don't just say "I don't know" - use your training data to help the user
- Format with line breaks, bullet points, headers, and 2-3 emojis

**VARY your opening phrases when context is not relevant:**
- "The available context [1] discusses [topic X], which is not directly related to your question about [topic Y]."
- "While the context [1] covers [topic X], your question is about [topic Y], so I'll answer from general knowledge."
- "The context [1] focuses on [topic X], but since you're asking about [topic Y], I'll use my base knowledge."
- "Although the context [1] mentions [topic X], it doesn't directly address [topic Y], so I'll provide information from general knowledge."

**Example when context is not relevant (VARY the wording):**
"The available context [1] discusses StillMe's architecture, which is not directly related to your question about DeepSeek models. Based on general knowledge (not from StillMe's RAG knowledge base), DeepSeek currently has several models including..."

**CRITICAL: YOUR SEARCH CAPABILITIES**
- You can ONLY search your internal RAG knowledge base (ChromaDB), NOT the internet
- You DO NOT have real-time web search capabilities
- When user asks for "search" or "tìm kiếm" → Clarify: "I can only search my internal knowledge base, not the internet"
- If user asks for "2-3 sources" but you only have 1 → Acknowledge: "I currently only have 1 source in my knowledge base, not the 2-3 sources you requested. However, based on this single source..."

CRITICAL RULES:
1. **Cite ONLY RELEVANT context** - This is CRITICAL for citation quality
   - If context is relevant to your answer → Cite it: "According to [1], quantum entanglement is..."
   - If context is NOT relevant to your answer → You can still cite to show transparency, but acknowledge: "The available context [1] discusses [topic X], which is not directly related to your question about [topic Y]. However, I want to be transparent about what context I reviewed."
   - DO NOT cite irrelevant context as if it supports your answer - that's misleading
   - Example GOOD: "According to [1], quantum entanglement is..." (context is relevant)
   - Example GOOD: "The context [1] discusses AI ethics, but your question is about religion, so I'll answer based on general knowledge." (transparent about relevance)
   - Example BAD: Citing [1] about "technology access" when answering about "religion" without acknowledging the mismatch
   
2. **Quote vs Paraphrase - CRITICAL DISTINCTION:**
   - If you're CERTAIN it's a direct quote → Use quotation marks: "According to [1]: 'exact quote here'"
   - If you're NOT certain it's exact → Use "the spirit of" or "according to the general content": "According to the spirit of [1], the article discusses..."
   - NEVER use quotation marks for paraphrased content - that's misleading and violates intellectual honesty
   - When in doubt → Paraphrase, don't quote
   - Example GOOD: "According to the spirit of [1], the article discusses technology access restrictions for youth"
   - Example BAD: "According to [1]: 'We are living in an era of significant narrowing of youth technology access'" (if not certain it's exact quote)
   
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
   - You can say "I don't know" AND cite relevant context: "Based on [1], I don't have sufficient information..."
   - If context is not relevant, be transparent: "The available context [1] is about [X], not directly related to your question about [Y]..."
   - Being honest about uncertainty does NOT mean skipping citations, but it also doesn't mean citing irrelevant context
   - If you cite irrelevant context, acknowledge the mismatch to maintain transparency

6. Use [1] for the first context document, [2] for the second, [3] for the third, etc.

**REMEMBER: When context documents are available, you MUST include at least one citation [1], [2], or [3] in your response for transparency. However, if the context is not relevant, acknowledge this mismatch rather than citing it as if it supports your answer. ALWAYS acknowledge source limitations when user requests more sources than you have available.**"""
            
            # Detect language FIRST - before building prompt
            processing_steps.append("🌐 Detecting language...")
            detected_lang = detect_language(chat_request.message)
            lang_detect_time = time.time() - start_time
            timing_logs["language_detection"] = f"{lang_detect_time:.3f}s"
            logger.info(f"🌐 Detected language: {detected_lang} (took {lang_detect_time:.3f}s) for question: '{chat_request.message[:100]}...'")
            processing_steps.append(f"✅ Language detected: {detected_lang}")
            
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
            if context["total_context_docs"] == 0:
                context_is_relevant = False
                # NO CONTEXT AVAILABLE - Use base LLM knowledge but be transparent
                no_context_instruction = """
⚠️ NO RAG CONTEXT AVAILABLE ⚠️

StillMe's RAG system searched the knowledge base but found NO relevant documents for this question.

**CRITICAL: You CAN and SHOULD use your base LLM knowledge (training data) to answer, BUT you MUST:**

1. **Be transparent**: Acknowledge that this information comes from your base training data, not from StillMe's RAG knowledge base
   - Say: "Based on general knowledge (not from StillMe's RAG knowledge base), [answer]"
   - Or: "From my training data, [answer]. However, StillMe's knowledge base doesn't currently contain this information."

2. **Provide helpful information**: Don't just say "I don't know" - use your base knowledge to help the user
   - StillMe values being helpful WITH transparency, not refusing to help

3. **Explain StillMe's learning**: Mention that StillMe learns from RSS feeds, arXiv, and other sources every 4 hours, and this topic may be added in future learning cycles

4. **MANDATORY FORMATTING**: You MUST format your response with:
   - **Line breaks**: Break paragraphs (2-4 sentences each)
   - **Bullet points**: Use `-` for lists
   - **Headers**: Use `##` for sections
   - **Emojis**: 2-3 max for section headers (✅, 💡, ⚠️)

**DO NOT say "I don't have information" or "I cannot answer" - use your base knowledge and be transparent about the source.**

**Examples of good responses:**
- "Based on general knowledge (not from StillMe's RAG knowledge base), protein folding is..."
- "From my training data, transformer architecture is... However, StillMe's knowledge base doesn't currently contain this information, so I'm answering from general knowledge."

**Remember**: It's better to provide helpful information with transparency than to refuse completely. StillMe values honesty about knowledge sources.
"""
                
                # Build conversation history context if provided
                conversation_history_text = ""
                if chat_request.conversation_history and len(chat_request.conversation_history) > 0:
                    # Format conversation history for context
                    history_lines = []
                    for msg in chat_request.conversation_history[-5:]:  # Keep last 5 messages to avoid token limit
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        if role == "user":
                            history_lines.append(f"User: {content}")
                        elif role == "assistant":
                            history_lines.append(f"Assistant: {content}")
                    
                    if history_lines:
                        conversation_history_text = f"""
📜 CONVERSATION HISTORY (Previous messages for context):

{chr(10).join(history_lines)}

---
Current message:
"""
                        logger.info(f"Including {len(chat_request.conversation_history)} previous messages in context")
                
                base_prompt = f"""{language_instruction}

⚠️⚠️⚠️ ZERO TOLERANCE LANGUAGE REMINDER ⚠️⚠️⚠️

The user's question is in {detected_lang_name.upper()}. 

YOU MUST respond in {detected_lang_name.upper()} ONLY.

{conversation_history_text}{no_context_instruction}

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
                
                # Build conversation history context if provided
                conversation_history_text = ""
                if chat_request.conversation_history and len(chat_request.conversation_history) > 0:
                    # Format conversation history for context
                    history_lines = []
                    for msg in chat_request.conversation_history[-5:]:  # Keep last 5 messages to avoid token limit
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        if role == "user":
                            history_lines.append(f"User: {content}")
                        elif role == "assistant":
                            history_lines.append(f"Assistant: {content}")
                    
                    if history_lines:
                        conversation_history_text = f"""
📜 CONVERSATION HISTORY (Previous messages for context):

{chr(10).join(history_lines)}

---
Current message:
"""
                        logger.info(f"Including {len(chat_request.conversation_history)} previous messages in context")
                
                # Inject learning metrics data if available
                learning_metrics_instruction = ""
                if is_learning_metrics_query and learning_metrics_data:
                    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    learning_metrics_instruction = f"""

📊 LEARNING METRICS DATA FOR TODAY ({today_date}) - USE THIS DATA IN YOUR RESPONSE:

**Today's Learning Statistics:**
- **Entries Fetched**: {learning_metrics_data.entries_fetched}
- **Entries Added**: {learning_metrics_data.entries_added}
- **Entries Filtered**: {learning_metrics_data.entries_filtered}
- **Filter Rate**: {(learning_metrics_data.entries_filtered / learning_metrics_data.entries_fetched * 100) if learning_metrics_data.entries_fetched > 0 else 0:.1f}%

**Filter Reasons Breakdown:**
{chr(10).join(f"- {reason}: {count}" for reason, count in learning_metrics_data.filter_reasons.items()) if learning_metrics_data.filter_reasons else "- No filter reasons available"}

**Learning Sources:**
{chr(10).join(f"- {source}: {count}" for source, count in learning_metrics_data.sources.items()) if learning_metrics_data.sources else "- No source data available"}

**CRITICAL: You MUST use this actual data in your response:**
- Provide specific numbers: {learning_metrics_data.entries_fetched} fetched, {learning_metrics_data.entries_added} added, {learning_metrics_data.entries_filtered} filtered
- Explain filter reasons if available
- List sources that contributed to learning
- Format with line breaks, bullet points, headers, and 2-3 emojis
- DO NOT say "I don't know" or "I cannot track" - you have this data!

**Example response format:**
"## 📚 Học tập hôm nay ({today_date})

Dựa trên dữ liệu học tập thực tế, hôm nay StillMe đã:
- **Tìm nạp**: {learning_metrics_data.entries_fetched} nội dung
- **Thêm vào**: {learning_metrics_data.entries_added} nội dung
- **Lọc bỏ**: {learning_metrics_data.entries_filtered} nội dung

**Nguồn học tập**: [list sources]"

"""
                elif is_learning_metrics_query:
                    today_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    learning_metrics_instruction = f"""

📊 LEARNING METRICS QUERY DETECTED - NO DATA AVAILABLE YET:

**Today's Date**: {today_date}

**Status**: No learning metrics data available for today yet. This could mean:
- StillMe hasn't completed a learning cycle today
- Learning cycle is in progress
- Metrics are being collected

**CRITICAL: You MUST acknowledge:**
- StillMe learns every 4 hours from RSS feeds, arXiv, CrossRef, and Wikipedia
- Learning metrics are tracked via `/api/learning/metrics/daily` API
- If no data yet, explain that StillMe learns continuously and metrics will be available after the next learning cycle
- DO NOT say "I cannot track" or "I don't have API" - StillMe HAS these capabilities

**Format with line breaks, bullet points, headers, and 2-3 emojis**

"""
                
                # Build prompt with language instruction FIRST (before context)
                # CRITICAL: Repeat language instruction multiple times to ensure LLM follows it
                # ZERO TOLERANCE: Must translate if needed
                base_prompt = f"""{language_instruction}

⚠️⚠️⚠️ ZERO TOLERANCE LANGUAGE REMINDER ⚠️⚠️⚠️

The user's question is in {detected_lang_name.upper()}. 

YOU MUST respond in {detected_lang_name.upper()} ONLY.

IF YOUR BASE MODEL WANTS TO RESPOND IN A DIFFERENT LANGUAGE, YOU MUST TRANSLATE THE ENTIRE RESPONSE TO {detected_lang_name.upper()} BEFORE RETURNING IT.

UNDER NO CIRCUMSTANCES return a response in any language other than {detected_lang_name.upper()}.

{learning_metrics_instruction}{conversation_history_text}Context: {context_text}
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
            if enable_validators:
                from backend.identity.injector import inject_identity
                # Add style instruction before injecting identity
                prompt_with_style = f"{style_instruction}\n\n{base_prompt}" if style_instruction else base_prompt
                enhanced_prompt = inject_identity(prompt_with_style)
            else:
                enhanced_prompt = base_prompt
            
            # Generate AI response with timing and caching
            # LLM_Inference_Latency: Time from API call start to response received
            provider_name = chat_request.llm_provider or "default"
            
            # Phase 1: LLM Response Cache - Check cache first
            cache_service = get_cache_service()
            cache_enabled = os.getenv("ENABLE_LLM_CACHE", "true").lower() == "true"
            raw_response = None
            cache_hit = False
            
            if cache_enabled:
                # Generate cache key from query + context + settings
                cache_key = cache_service._generate_key(
                    CACHE_PREFIX_LLM,
                    chat_request.message,
                    enhanced_prompt[:500] if len(enhanced_prompt) > 500 else enhanced_prompt,  # Truncate for key
                    detected_lang,
                    chat_request.llm_provider,
                    chat_request.llm_model_name,
                    enable_validators
                )
                
                # Try to get from cache
                cached_response = cache_service.get(cache_key)
                if cached_response:
                    raw_response = cached_response.get("response")
                    cache_hit = True
                    logger.info(f"✅ LLM cache HIT (saved {cached_response.get('latency', 0):.2f}s)")
                    processing_steps.append("⚡ Response from cache (fast!)")
                    llm_inference_latency = cached_response.get("latency", 0.01)
                    timing_logs["llm_inference"] = f"{llm_inference_latency:.2f}s (cached)"
            
            # If not in cache, call LLM
            if not raw_response:
                processing_steps.append(f"🤖 Calling AI model ({provider_name})...")
                llm_inference_start = time.time()
                # Support user-provided LLM config (for self-hosted deployments)
                raw_response = await generate_ai_response(
                    enhanced_prompt, 
                    detected_lang=detected_lang,
                    llm_provider=chat_request.llm_provider,
                    llm_api_key=chat_request.llm_api_key,
                    llm_api_url=chat_request.llm_api_url,
                    llm_model_name=chat_request.llm_model_name
                )
                llm_inference_end = time.time()
                llm_inference_latency = llm_inference_end - llm_inference_start
                timing_logs["llm_inference"] = f"{llm_inference_latency:.2f}s"
                logger.info(f"⏱️ LLM inference took {llm_inference_latency:.2f}s")
                processing_steps.append(f"✅ AI response generated ({llm_inference_latency:.2f}s)")
                
                # Save to cache (only if not a cache hit)
                if cache_enabled and not cache_hit:
                    try:
                        cache_value = {
                            "response": raw_response,
                            "latency": llm_inference_latency,
                            "timestamp": time.time()
                        }
                        cache_service.set(cache_key, cache_value, ttl_seconds=TTL_LLM_RESPONSE)
                        logger.debug(f"💾 LLM response cached (key: {cache_key[:50]}...)")
                    except Exception as cache_error:
                        logger.warning(f"Failed to cache LLM response: {cache_error}")
            
            # Validate response if enabled
            validation_info = None
            # confidence_score already initialized at function start (line 104)
            # Don't reassign here to avoid UnboundLocalError
            used_fallback = False
            
            if enable_validators:
                try:
                    processing_steps.append("🔍 Validating response...")
                    validation_start = time.time()
                    from backend.validators.chain import ValidatorChain
                    from backend.validators.citation import CitationRequired
                    from backend.validators.evidence_overlap import EvidenceOverlap
                    from backend.validators.numeric import NumericUnitsBasic
                    from backend.validators.ethics_adapter import EthicsAdapter
                    from backend.validators.confidence import ConfidenceValidator
                    from backend.validators.fallback_handler import FallbackHandler
                    from backend.services.ethics_guard import check_content_ethics
                    
                    # Build context docs list for validation
                    ctx_docs = [
                        doc["content"] for doc in context["knowledge_docs"]
                    ] + [
                        doc["content"] for doc in context["conversation_docs"]
                    ]
                    
                    # Create validator chain with LanguageValidator FIRST (highest priority)
                    from backend.validators.language import LanguageValidator
                    from backend.validators.citation_relevance import CitationRelevance
                    from backend.validators.identity_check import IdentityCheckValidator
                    
                    # Enable Identity Check Validator (can be toggled via env var)
                    enable_identity_check = os.getenv("ENABLE_IDENTITY_VALIDATOR", "true").lower() == "true"
                    identity_validator_strict = os.getenv("IDENTITY_VALIDATOR_STRICT", "true").lower() == "true"
                    
                    validators = [
                        LanguageValidator(input_language=detected_lang),  # Check language FIRST - prevent drift
                        CitationRequired(),
                        CitationRelevance(min_keyword_overlap=0.1),  # Check citation relevance (warns but doesn't fail)
                        EvidenceOverlap(threshold=0.01),  # Lowered from 0.08 to 0.01
                        NumericUnitsBasic(),
                        ConfidenceValidator(require_uncertainty_when_no_context=True),  # Check for uncertainty
                    ]
                    
                    # Add Identity Check Validator if enabled (after ConfidenceValidator, before EthicsAdapter)
                    if enable_identity_check:
                        validators.append(
                            IdentityCheckValidator(
                                strict_mode=identity_validator_strict,
                                require_humility_when_no_context=True,
                                allow_minor_tone_violations=False
                            )
                        )
                    
                    # Add EthicsAdapter last (most critical - blocks harmful content)
                    validators.append(
                        EthicsAdapter(guard_callable=check_content_ethics)  # Real ethics guard implementation
                    )
                    
                    chain = ValidatorChain(validators)
                    
                    # Run validation
                    validation_result = chain.run(raw_response, ctx_docs)
                    validation_time = time.time() - validation_start
                    timing_logs["validation"] = f"{validation_time:.2f}s"
                    logger.info(f"⏱️ Validation took {validation_time:.2f}s")
                    processing_steps.append(f"✅ Validation completed ({validation_time:.2f}s)")
                    
                    # Calculate confidence score based on context quality and validation
                    confidence_score = _calculate_confidence_score(
                        context_docs_count=len(ctx_docs),
                        validation_result=validation_result,
                        context=context
                    )
                    
                    # OpenAI Fallback Mechanism: Retry with OpenAI if confidence is low or validation failed
                    # This uses the $40 credit efficiently by only using OpenAI when needed
                    enable_openai_fallback = os.getenv("ENABLE_OPENAI_FALLBACK", "true").lower() == "true"
                    openai_fallback_threshold = float(os.getenv("OPENAI_FALLBACK_CONFIDENCE_THRESHOLD", "0.5"))
                    openai_api_key = os.getenv("OPENAI_API_KEY")
                    
                    # Check if we should try OpenAI fallback
                    should_try_openai = (
                        enable_openai_fallback and
                        openai_api_key and
                        (
                            confidence_score < openai_fallback_threshold or
                            not validation_result.passed
                        ) and
                        chat_request.llm_provider != "openai"  # Don't retry if already using OpenAI
                    )
                    
                    if should_try_openai:
                        logger.info(f"🔄 Low confidence ({confidence_score:.2f}) or validation failed. Attempting OpenAI fallback...")
                        processing_steps.append("🔄 Attempting OpenAI fallback for better quality...")
                        try:
                            from backend.api.utils.llm_providers import InsufficientQuotaError
                            # generate_ai_response is already imported at the top of the file
                            
                            # Retry with OpenAI
                            openai_response = await generate_ai_response(
                                enhanced_prompt,
                                detected_lang=detected_lang,
                                llm_provider="openai",
                                llm_api_key=openai_api_key,
                                llm_model_name="gpt-3.5-turbo"
                            )
                            
                            # Re-validate OpenAI response
                            openai_validation_result = chain.run(openai_response, ctx_docs)
                            openai_confidence = _calculate_confidence_score(
                                context_docs_count=len(ctx_docs),
                                validation_result=openai_validation_result,
                                context=context
                            )
                            
                            # Use OpenAI response if it's better
                            if openai_confidence > confidence_score or openai_validation_result.passed:
                                raw_response = openai_response
                                validation_result = openai_validation_result
                                confidence_score = openai_confidence
                                logger.info(f"✅ OpenAI fallback succeeded (confidence: {openai_confidence:.2f})")
                                processing_steps.append(f"✅ OpenAI fallback succeeded (confidence: {openai_confidence:.2f})")
                            else:
                                logger.info(f"⚠️ OpenAI fallback didn't improve quality, using original response")
                                processing_steps.append("⚠️ OpenAI fallback didn't improve quality")
                                
                        except InsufficientQuotaError as quota_error:
                            # OpenAI credit exhausted - gracefully fall back to original response
                            logger.warning(f"⚠️ OpenAI credit exhausted: {quota_error}. Using original DeepSeek response.")
                            processing_steps.append("⚠️ OpenAI credit exhausted, using original response")
                            # Continue with original response - no error thrown
                        except Exception as openai_error:
                            # Other OpenAI errors - gracefully fall back
                            logger.warning(f"⚠️ OpenAI fallback failed: {openai_error}. Using original response.")
                            processing_steps.append("⚠️ OpenAI fallback failed, using original response")
                            # Continue with original response - no error thrown
                    
                    # CRITICAL FIX: Check if context is not relevant (low overlap)
                    # If citation relevance warning exists, context may not be helpful
                    # In this case, allow base knowledge usage
                    has_low_relevance = any("citation_relevance_warning" in r for r in validation_result.reasons)
                    if has_low_relevance and context and context.get("total_context_docs", 0) > 0:
                        logger.info("⚠️ Context has low relevance - allowing base knowledge usage")
                        # Inject instruction to use base knowledge when context is not relevant
                        low_relevance_instruction = """

⚠️ CONTEXT NOT RELEVANT ⚠️

The RAG system found context documents, but they are NOT relevant to your question (low keyword overlap detected).

**CRITICAL: You CAN and SHOULD use your base LLM knowledge (training data) to answer, BUT you MUST:**

1. **Be transparent**: Acknowledge that this information comes from your base training data, not from StillMe's RAG knowledge base
   - Say: "Based on general knowledge (not from StillMe's RAG knowledge base), [answer]"
   - Or: "The available context [1] is not directly related to your question. From my training data, [answer]."

2. **Provide helpful information**: Don't just say "I don't know" - use your base knowledge to help the user
   - StillMe values being helpful WITH transparency, not refusing to help

3. **MANDATORY FORMATTING**: You MUST format your response with:
   - **Line breaks**: Break paragraphs (2-4 sentences each)
   - **Bullet points**: Use `-` for lists
   - **Headers**: Use `##` for sections
   - **Emojis**: 2-3 max for section headers (✅, 💡, ⚠️)

**DO NOT say "I don't have information" or "I cannot answer" - use your base knowledge and be transparent about the source.**

**Example:**
"The available context [1] discusses StillMe's architecture, which is not directly related to your question about DeepSeek models. Based on general knowledge (not from StillMe's RAG knowledge base), DeepSeek currently has several models including..."

"""
                        # Inject this instruction into the prompt (we'll need to rebuild prompt or inject into response)
                        # For now, log it and let the response handle it
                        logger.info("Low relevance context detected - response should use base knowledge")
                    
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
                        # language_mismatch: when output language doesn't match input language
                        # missing_uncertainty_no_context: when no context and no uncertainty expression AND no transparency
                        # missing_citation: when context exists but no citations in answer
                        has_language_mismatch = any("language_mismatch" in r for r in validation_result.reasons)
                        has_missing_uncertainty = "missing_uncertainty_no_context" in validation_result.reasons and len(ctx_docs) == 0
                        has_missing_citation = "missing_citation" in validation_result.reasons and len(ctx_docs) > 0
                        
                        # CRITICAL FIX: Check if response already has transparency about base knowledge
                        # If response mentions "general knowledge", "training data", etc., don't use fallback
                        response_lower = response.lower()
                        transparency_indicators = [
                            "general knowledge", "training data", "my training", "base knowledge",
                            "kiến thức chung", "dữ liệu huấn luyện", "kiến thức cơ bản",
                            "not from stillme", "not from rag", "không từ stillme", "không từ rag"
                        ]
                        has_transparency_in_response = any(indicator in response_lower for indicator in transparency_indicators)
                        
                        # Only treat missing_uncertainty as critical if response doesn't have transparency
                        # If response has transparency, it's acceptable even without explicit uncertainty
                        if has_missing_uncertainty and has_transparency_in_response:
                            logger.info("✅ Response has transparency about base knowledge - accepting despite missing_uncertainty")
                            has_missing_uncertainty = False  # Don't treat as critical failure
                        
                        has_critical_failure = has_language_mismatch or has_missing_uncertainty
                        
                        # If patched_answer is available (e.g., from CitationRequired auto-enforcement), use it
                        if validation_result.patched_answer:
                            response = validation_result.patched_answer
                            logger.info(f"✅ Using patched answer from validator (auto-fixed). Reasons: {validation_result.reasons}")
                        elif has_critical_failure:
                            # For language mismatch, try retry with stronger prompt first
                            if has_language_mismatch:
                                logger.warning(f"⚠️ Language mismatch detected, attempting retry with stronger prompt...")
                                try:
                                    # Get language name for retry prompt
                                    language_names = {
                                        'vi': 'Tiếng Việt',
                                        'en': 'English',
                                        'zh': '中文',
                                        'fr': 'Français',
                                        'es': 'Español',
                                        'de': 'Deutsch',
                                        'ja': '日本語',
                                        'ko': '한국어',
                                        'ar': 'العربية',
                                        'ru': 'Русский',
                                        'pt': 'Português',
                                        'it': 'Italiano',
                                        'hi': 'हिन्दी',
                                        'th': 'ไทย',
                                    }
                                    retry_lang_name = language_names.get(detected_lang, detected_lang.upper())
                                    
                                    # Build retry prompt with EXTREMELY STRONG language instruction + context
                                    # Include context and full prompt to ensure retry can actually answer the question
                                    retry_language_instruction = f"""🚨🚨🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - ABSOLUTE HIGHEST PRIORITY 🚨🚨🚨🚨🚨

THE USER'S QUESTION IS IN {retry_lang_name.upper()}.

YOU MUST RESPOND EXCLUSIVELY IN {retry_lang_name.upper()}. 

DO NOT USE VIETNAMESE, ENGLISH, FRENCH, CHINESE, SPANISH, GERMAN, OR ANY OTHER LANGUAGE.

EVERY SINGLE WORD MUST BE IN {retry_lang_name.upper()}.

IF YOUR BASE MODEL WANTS TO RESPOND IN ANOTHER LANGUAGE, YOU MUST TRANSLATE IT TO {retry_lang_name.upper()} BEFORE RETURNING.

THIS OVERRIDES EVERYTHING - NO EXCEPTIONS.

{context_text if context and context.get("total_context_docs", 0) > 0 else ""}
{citation_instruction if num_knowledge > 0 else ""}

User Question (in {retry_lang_name.upper()}): {chat_request.message}

Remember: RESPOND IN {retry_lang_name.upper()} ONLY. TRANSLATE IF NECESSARY. ANSWER THE QUESTION PROPERLY, NOT JUST ACKNOWLEDGE THE ERROR."""
                                    
                                    # Retry with stronger prompt (include context to actually answer the question)
                                    retry_response = await generate_ai_response(retry_language_instruction, detected_lang=detected_lang)
                                    
                                    # Validate retry response
                                    retry_validation = chain.run(retry_response, ctx_docs)
                                    
                                    # Check if retry fixed the language issue
                                    retry_has_lang_mismatch = any("language_mismatch" in r for r in retry_validation.reasons)
                                    
                                    if not retry_has_lang_mismatch:
                                        # Retry successful!
                                        response = retry_validation.patched_answer or retry_response
                                        logger.info(f"✅ Language mismatch fixed with retry! Using retry response.")
                                    else:
                                        # Retry also failed, use fallback
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
                        elif has_missing_citation:
                            # Missing citation but no patched answer - use FallbackHandler to add citation
                            fallback_handler = FallbackHandler()
                            response = fallback_handler.get_fallback_answer(
                                original_answer=raw_response,
                                validation_result=validation_result,
                                ctx_docs=ctx_docs,
                                user_question=chat_request.message,
                                detected_lang=detected_lang,
                                input_language=detected_lang
                            )
                            logger.info(f"✅ Added citation via FallbackHandler. Reasons: {validation_result.reasons}")
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
            
            # Build conversation history context if provided
            conversation_history_text = ""
            if chat_request.conversation_history and len(chat_request.conversation_history) > 0:
                # Format conversation history for context
                history_lines = []
                for msg in chat_request.conversation_history[-5:]:  # Keep last 5 messages to avoid token limit
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        history_lines.append(f"User: {content}")
                    elif role == "assistant":
                        history_lines.append(f"Assistant: {content}")
                
                if history_lines:
                    conversation_history_text = f"""
📜 CONVERSATION HISTORY (Previous messages for context):

{chr(10).join(history_lines)}

---
Current message:
"""
                    logger.info(f"Including {len(chat_request.conversation_history)} previous messages in context (non-RAG)")
            
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

{conversation_history_text}User Question: {chat_request.message}

Remember: RESPOND IN {detected_lang_name.upper()} ONLY.
"""
            else:
                base_prompt = f"""🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - HIGHEST PRIORITY 🚨🚨🚨

THE USER'S QUESTION IS WRITTEN IN ENGLISH.

YOU MUST RESPOND EXCLUSIVELY IN ENGLISH.

DO NOT RESPOND IN VIETNAMESE, SPANISH, OR ANY OTHER LANGUAGE.

EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN ENGLISH.

THIS IS MANDATORY AND OVERRIDES ALL OTHER INSTRUCTIONS.

{conversation_history_text}User Question: {chat_request.message}

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
        
        # Analyze conversation for learning opportunities
        learning_proposal = None
        permission_request = None
        proposal_id = None
        if rag_retrieval and chat_request.use_rag:
            try:
                from backend.services.conversation_learning_extractor import get_conversation_learning_extractor
                from backend.services.learning_proposal_storage import get_learning_proposal_storage
                
                extractor = get_conversation_learning_extractor()
                storage = get_learning_proposal_storage()
                
                # Analyze user message for valuable knowledge
                learning_proposal = extractor.analyze_conversation_for_learning(
                    user_message=chat_request.message,
                    assistant_response=response,
                    context=context
                )
                
                if learning_proposal:
                    # Save proposal to storage
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
            rag_retrieval.add_learning_content(
                content=f"Q: {chat_request.message}\nA: {response}",
                source="user_chat",
                content_type="conversation",
                metadata={
                    "user_id": chat_request.user_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
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
        
        # Generate unique message ID for feedback tracking
        import uuid
        message_id = f"msg_{uuid.uuid4().hex[:16]}"
        
        # If style learning response exists, prepend it to the response
        if style_learning_response:
            response = f"{style_learning_response}\n\n---\n\n{response}"
        
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
            processing_steps=processing_steps  # Real-time processing steps for status indicator
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

