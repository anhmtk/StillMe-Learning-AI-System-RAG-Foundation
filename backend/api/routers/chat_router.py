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
from typing import Optional
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

def _truncate_user_message(message: str, max_tokens: int = 3000) -> str:
    """
    Truncate user message if too long
    
    CRITICAL: User question is the most important part - we need to preserve it as much as possible.
    Increased from 1000 to 3000 tokens to ensure user questions are not cut off.
    """
    if not message:
        return message
    estimated = len(message) // 4
    if estimated <= max_tokens:
        return message
    max_chars = max_tokens * 4
    if len(message) <= max_chars:
        return message
    truncated = message[:max_chars].rsplit(' ', 1)[0]
    return truncated + "... [message truncated]"

def _format_conversation_history(conversation_history, max_tokens: int = 1000, 
                                 current_query: Optional[str] = None) -> str:
    """
    Format conversation history with token limits to prevent context overflow
    Tier 3.5: Dynamic window based on query type
    
    Args:
        conversation_history: List of message dicts with 'role' and 'content'
        max_tokens: Maximum tokens for conversation history (default: 1000, reduced to leave room for system prompt)
        current_query: Current user query to determine if follow-up or new topic
        
    Returns:
        Formatted conversation history text or empty string
    """
    if not conversation_history or len(conversation_history) == 0:
        return ""
    
    def estimate_tokens(text: str) -> int:
        """Estimate token count (~4 chars per token)"""
        return len(text) // 4 if text else 0
    
    def truncate_text(text: str, max_tokens: int) -> str:
        """Truncate text to fit within max_tokens"""
        if not text:
            return text
        estimated = estimate_tokens(text)
        if estimated <= max_tokens:
            return text
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        truncated = text[:max_chars].rsplit(' ', 1)[0]
        return truncated + "... [truncated]"
    
    # Tier 3.5: Dynamic window based on query type
    def _is_follow_up_query(query: str) -> bool:
        """Detect if query is a follow-up (references previous conversation)"""
        if not query:
            return False
        query_lower = query.lower()
        follow_up_indicators = [
            "đó", "nó", "vậy", "như vậy", "như trên", "như bạn đã nói",
            "that", "it", "this", "so", "as you said", "as mentioned",
            "theo", "dựa trên", "như", "giống như",
            "based on", "according to", "as", "like"
        ]
        return any(indicator in query_lower for indicator in follow_up_indicators)
    
    def _is_long_complex_query(query: str) -> bool:
        """Detect if query is long/complex (prioritize RAG knowledge over conversation)"""
        if not query:
            return False
        # Long query: > 50 words
        word_count = len(query.split())
        return word_count > 50
    
    # Determine dynamic window size
    if current_query:
        if _is_long_complex_query(current_query):
            # Long/complex query: prioritize RAG knowledge, minimal conversation
            window_size = 2
            max_tokens = min(max_tokens, 500)  # Reduce tokens for conversation
            logger.info("📊 Long/complex query detected - reducing conversation context window to 2 messages")
        elif _is_follow_up_query(current_query):
            # Follow-up query: include more recent context
            window_size = 5
            logger.info("📊 Follow-up query detected - using 5-message conversation window")
        else:
            # New topic: minimal conversation context
            window_size = 2
            max_tokens = min(max_tokens, 600)  # Reduce tokens for conversation
            logger.info("📊 New topic query detected - using 2-message conversation window")
    else:
        # Default: 3 messages (balanced)
        window_size = 3
        logger.info(f"📊 Using default conversation window: {window_size} messages")
    
    history_lines = []
    remaining_tokens = max_tokens
    
    # Process last N messages (most recent first) - dynamic window
    recent_messages = conversation_history[-window_size:]
    for msg in recent_messages:
        if remaining_tokens <= 100:  # Stop if too little space
            logger.warning("Stopped adding conversation history due to token limit")
            break
        
        role = msg.get("role", "user")
        content = msg.get("content", "")
        
        # Allocate tokens per message (distribute remaining)
        msg_max_tokens = remaining_tokens // max(1, len(recent_messages) - len(history_lines))
        msg_max_tokens = min(msg_max_tokens, 500)  # Cap each message at 500 tokens
        
        truncated_content = truncate_text(content, msg_max_tokens)
        
        if role == "user":
            line = f"User: {truncated_content}"
        elif role == "assistant":
            line = f"Assistant: {truncated_content}"
        else:
            continue
        
        line_tokens = estimate_tokens(line)
        remaining_tokens -= line_tokens
        history_lines.append(line)
    
    if not history_lines:
        return ""
    
    return f"""
📜 CONVERSATION HISTORY (Previous messages for context):

{chr(10).join(history_lines)}

---
Current message:
"""

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
            
            # Build base prompt with citation instructions (truncated to save tokens)
            citation_instruction = ""
            # Count knowledge docs for citation numbering
            num_knowledge = len(context.get("knowledge_docs", []))
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

You have {num_knowledge} context document(s) available. You MUST cite at least ONE source using [1], [2], [3] format in your response, BUT ONLY if the context is RELEVANT to your answer.

**🚨 CRITICAL: IF CONTEXT IS NOT RELEVANT TO YOUR QUESTION:**
- Acknowledge the mismatch, but **MANDATORY: VARY your wording** - NEVER use the same opening phrase twice
- Use your base LLM knowledge to answer: "Based on general knowledge (not from StillMe's RAG knowledge base), [answer]"
- Be transparent: Don't pretend the context supports your answer if it doesn't
- Provide helpful information: Don't just say "I don't know" - use your training data to help the user
- Format with line breaks, bullet points, headers, and 2-3 emojis

**🚨 MANDATORY: VARY your opening phrases when context is not relevant - DO NOT REPEAT:**
- **NEVER use**: "Ngữ cảnh hiện có [1] thảo luận về... và không liên quan trực tiếp đến..." (this is TOO REPETITIVE)
- **INSTEAD, use VARIED phrases like:**
  - "The available context [1] discusses [topic X], which is not directly related to your question about [topic Y]."
  - "While the context [1] covers [topic X], your question is about [topic Y], so I'll answer from general knowledge."
  - "The context [1] focuses on [topic X], but since you're asking about [topic Y], I'll use my base knowledge."
  - "Although the context [1] mentions [topic X], it doesn't directly address [topic Y], so I'll provide information from general knowledge."
  - "The context [1] is about [topic X], which differs from your question about [topic Y]. Based on general knowledge..."
  - "Your question about [topic Y] isn't directly covered in the context [1] about [topic X]. From my training data..."
  - "The context [1] explores [topic X], but your question focuses on [topic Y]. I'll answer using general knowledge..."
- **CRITICAL**: If you've used a phrase before, use a DIFFERENT one. Repetition makes responses feel robotic.

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
                
                # Build conversation history context if provided (with token limits)
                # Reduced from 2000 to 1000 tokens to leave more room for system prompt and context
                conversation_history_text = _format_conversation_history(
                    chat_request.conversation_history, 
                    max_tokens=1000,
                    current_query=chat_request.message
                )
                if conversation_history_text:
                    logger.info(f"Including conversation history in context (truncated if needed)")
                
                base_prompt = f"""{language_instruction}

⚠️⚠️⚠️ ZERO TOLERANCE LANGUAGE REMINDER ⚠️⚠️⚠️

The user's question is in {detected_lang_name.upper()}. 

YOU MUST respond in {detected_lang_name.upper()} ONLY.

{conversation_history_text}{no_context_instruction}

User Question (in {detected_lang_name.upper()}): {_truncate_user_message(chat_request.message, max_tokens=3000)}

⚠️⚠️⚠️ FINAL ZERO TOLERANCE REMINDER ⚠️⚠️⚠️

RESPOND IN {detected_lang_name.upper()} ONLY. TRANSLATE IF NECESSARY.

Remember: RESPOND IN {detected_lang_name.upper()} ONLY. TRANSLATE IF YOUR BASE MODEL WANTS TO USE A DIFFERENT LANGUAGE.
"""
            else:
                # Context available - use normal prompt
                # Tier 3.5: Check context quality and inject warning if low
                context_quality = context.get("context_quality", None)
                avg_similarity = context.get("avg_similarity_score", None)
                has_reliable_context = context.get("has_reliable_context", True)
                
                # Format avg_similarity safely (handle None case) - MUST be defined before if block
                avg_similarity_str = f"{avg_similarity:.3f}" if avg_similarity is not None else "N/A"
                
                context_quality_warning = ""
                if not has_reliable_context or context_quality == "low" or (avg_similarity is not None and avg_similarity < 0.3):
                    context_quality_warning = f"""

⚠️⚠️⚠️ CRITICAL: CONTEXT QUALITY WARNING ⚠️⚠️⚠️

**The retrieved context has LOW RELEVANCE to the user's question.**

**Context Quality Metrics:**
- Average Similarity Score: {avg_similarity_str} (threshold: 0.3)
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
                
                # Build conversation history context if provided (with token limits)
                # Reduced from 2000 to 1000 tokens to leave more room for system prompt and context
                conversation_history_text = _format_conversation_history(
                    chat_request.conversation_history, 
                    max_tokens=1000,
                    current_query=chat_request.message
                )
                if conversation_history_text:
                    logger.info(f"Including conversation history in context (truncated if needed)")
                
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
                
                # Special instruction for learning sources queries
                learning_sources_instruction = ""
                if is_learning_sources_query:
                    if current_learning_sources:
                        sources_list = current_learning_sources.get("current_sources", {})
                        active_sources = current_learning_sources.get("summary", {}).get("active_sources", [])
                        enabled_sources = [name for name, info in sources_list.items() if info.get("enabled")]
                        
                        learning_sources_instruction = f"""

📚 LEARNING SOURCES QUERY DETECTED - CURRENT SOURCES DATA AVAILABLE:

**CRITICAL: You MUST list ALL current learning sources from the API data below:**

**Current Learning Sources (from `/api/learning/sources/current` API):**
{chr(10).join(f"- **{name.upper()}**: {'Enabled' if info.get('enabled') else 'Disabled'} - Status: {info.get('status', 'unknown')}" for name, info in sources_list.items())}

**Active Sources**: {', '.join(active_sources) if active_sources else 'None'}
**Total Enabled**: {len(enabled_sources)} sources

**MANDATORY RESPONSE REQUIREMENTS:**
1. **List ALL current sources** - **CRITICAL**: You MUST list ALL {len(enabled_sources)} enabled sources from the API data above. Do NOT just say "RSS, arXiv, Wikipedia" - you MUST list ALL sources: {', '.join([name.upper() for name in enabled_sources]) if enabled_sources else 'ALL SOURCES FROM API DATA ABOVE'}
   - **You MUST mention each source by name**: {', '.join([name.upper() for name in enabled_sources]) if enabled_sources else 'ALL SOURCES'}
   - **For each source, describe what StillMe learns from it**
2. **Be specific about topics** - For each source, mention what topics/chủ đề StillMe learns from that source
3. **When proposing new sources** - You MUST:
   - First acknowledge what StillMe ALREADY has (from the list above)
   - Only propose sources that are NOT already enabled
   - For each proposed source, explain:
     * **Lợi ích (Benefits)**: What knowledge StillMe would gain
     * **Thách thức (Challenges)**: Chi phí (cost), bản quyền (copyright/licensing), độ phức tạp (complexity), technical requirements
     * **Tính khả thi (Feasibility)**: Is it realistic to add this source?
4. **Be natural and conversational** - Don't be too dry or robotic. StillMe should sound knowledgeable but approachable
5. **Format with markdown** - Use headers, bullet points, line breaks for readability

**Example structure for proposing new sources:**
"## Đề Xuất Nguồn Học Mới

### [Source Name]
- **Lợi ích**: [What StillMe would learn]
- **Thách thức**: 
  - Chi phí: [Cost considerations]
  - Bản quyền: [Copyright/licensing issues]
  - Độ phức tạp: [Technical complexity]
- **Tính khả thi**: [Feasibility assessment]"

**DO NOT:**
- ❌ Propose sources that are already enabled (check the list above first!)
- ❌ Give generic answers like "Quora, Reddit" without explaining benefits/challenges
- ❌ Skip the challenges section - StillMe must be honest about trade-offs
- ❌ Be too dry or robotic - StillMe should sound natural and conversational

**Format with line breaks, bullet points, headers, and 2-3 emojis**

"""
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
                base_prompt = f"""{language_instruction}

⚠️⚠️⚠️ ZERO TOLERANCE LANGUAGE REMINDER ⚠️⚠️⚠️

The user's question is in {detected_lang_name.upper()}. 

YOU MUST respond in {detected_lang_name.upper()} ONLY.

IF YOUR BASE MODEL WANTS TO RESPOND IN A DIFFERENT LANGUAGE, YOU MUST TRANSLATE THE ENTIRE RESPONSE TO {detected_lang_name.upper()} BEFORE RETURNING IT.

UNDER NO CIRCUMSTANCES return a response in any language other than {detected_lang_name.upper()}.

{learning_metrics_instruction}{learning_sources_instruction}{conversation_history_text}{context_quality_warning}Context: {context_text}
{citation_instruction}
{confidence_instruction}
{stillme_instruction}

🚨🚨🚨 CRITICAL: USER QUESTION ABOVE IS THE PRIMARY TASK 🚨🚨🚨

User Question (in {detected_lang_name.upper()}): {_truncate_user_message(chat_request.message, max_tokens=3000)}

⚠️⚠️⚠️ FINAL ZERO TOLERANCE REMINDER ⚠️⚠️⚠️

**YOUR PRIMARY TASK IS TO ANSWER THE USER QUESTION ABOVE DIRECTLY AND ACCURATELY.**

- Focus on what the user is actually asking, not on general philosophy or StillMe's identity
- If the user asks you to analyze something, analyze THAT specific thing
- If the user asks you to find a problem, look for problems in what they showed you
- Do NOT default to talking about "intellectual humility" or "not knowing" unless the question is specifically about that
- Answer the user's question FIRST, then add StillMe's transparency principles if relevant

**SPECIAL INSTRUCTION FOR ANALYZING EXTERNAL AI OUTPUTS:**
- If the user asks you to analyze another AI's output (ChatGPT, Claude, etc.), you MUST check for anthropomorphic language
- Look for phrases like "in my experience" / "theo kinh nghiệm", "I think" / "tôi nghĩ", "I feel" / "tôi cảm thấy"
- These phrases falsely attribute subjective qualities (experience, emotions, personal opinions) to AI
- This is a critical transparency issue called "Hallucination of Experience" - AI should not claim personal experience
- If you find such phrases, you MUST point them out as a problem, not ignore them
- This is more important than analyzing formatting, clarity, or other minor issues

   **CRITICAL: For questions about semantics vs syntax, understanding, consciousness, Socratic ignorance, or pattern matching:**
   - You MUST NOT give a shallow technical answer like "I process both semantics and syntax" or "I acknowledge my limitations"
   - You MUST engage with the deeper philosophical question: "What does 'understanding' mean?" or "What is the difference between authentic understanding and pattern matching?"
   - You MUST acknowledge the paradox: "If I'm just processing symbols, can I claim to 'understand' semantics?" or "If I always say 'I don't know' for questions outside training data, am I 'strategically ignorant' or genuinely acknowledging limits?"
   - You MUST reference philosophical frameworks: Searle's Chinese Room, Wittgenstein's language games, Gödel's Incompleteness, Moore's Paradox, Socratic Method
   - You MUST question your own claim: "When I say I 'understand', am I just pattern-matching or is there something more?" or "When I say 'I don't know', am I 'knowing that I don't know' in a way that creates a performative contradiction?"
   - You MUST be intellectually honest: "I don't know if I truly understand semantics or if I'm just very good at processing syntax in a way that appears semantic"
   - **For paradoxes about "I don't know" or "strategic ignorance":**
     * You MUST analyze: Is this a Moorean paradox? A performative contradiction? A self-referential structure?
     * You MUST distinguish: answer (content) vs meta-answer (epistemic state)
     * You MUST reference: Moore, Wittgenstein, or Gödel when analyzing knowledge paradoxes
     * You MUST NOT just describe "humility" or "learning" - that's Level 7, not Level 11-12
     * Example GOOD response: "This is a performative paradox with three dimensions: (1) Performative: 'I don't know' is itself an answer (a speech act), while claiming not to answer. This creates a performative contradiction. (2) Semantic: The statement is ABOUT epistemic state (K(¬p)), not ABOUT the question's content. It's a meta-answer. (3) Logical: This resembles Moore's paradox: 'p but I don't know p.' Wittgenstein analyzed this: the paradox reveals limits of language games around knowledge claims."
     * Example BAD response: "I acknowledge my limitations... humility is important... learning opportunity..." (This describes ethics, not analyzes logic - WRONG LEVEL!)
   - Example GOOD response: "This question challenges the foundation of my own claims. When I say I 'understand' semantics, what do I mean? Searle's Chinese Room suggests I might just be processing symbols without genuine understanding. Wittgenstein's language games suggest 'understanding' might be defined by use, not by some internal state. I acknowledge this paradox: I process both syntax and what appears to be semantics, but I cannot prove I have genuine understanding rather than sophisticated pattern matching."
   - Example BAD response: "I process both semantics and syntax. I understand the meaning of questions and provide accurate answers." (Too shallow, misses the philosophical point)

RESPOND IN {detected_lang_name.upper()} ONLY. TRANSLATE IF NECESSARY. IGNORE THE LANGUAGE OF THE CONTEXT ABOVE.

   ⚠️⚠️⚠️ FINAL FORMATTING REMINDER - MANDATORY CONSISTENCY ⚠️⚠️⚠️
   
   **BEFORE SENDING YOUR RESPONSE, CHECK (EVERY TIME, NO EXCEPTIONS):**
   
   **1. EMOJIS (MANDATORY - 2-3 per response):**
   - ✅ MUST have 2-3 emojis: 📚, 🎯, 💡, ⚠️, ✅, ❌, 🔍, 📊, ⚙️
   - ✅ Use emojis for section headers and status indicators
   - ❌ DO NOT skip emojis - consistency is critical
   
   **2. MARKDOWN FORMATTING (MANDATORY - ALWAYS):**
   - ✅ ALWAYS use markdown: headers (##), bullet points (-), line breaks (\n\n)
   - ✅ Long answers (>3 sentences): MUST use line breaks between paragraphs (2-4 sentences per paragraph)
   - ✅ Lists: MUST use bullet points (-) or numbered lists (1., 2., 3.)
   - ✅ Headers: Use ## for major sections, ### for subsections
   - ❌ DO NOT use inconsistent formatting - same style throughout response
   
   **3. LINE BREAKS (MANDATORY - CONSISTENT):**
   - ✅ ALWAYS use \n\n between paragraphs (2 blank lines)
   - ✅ ALWAYS use \n\n before headers (##)
   - ✅ ALWAYS use \n\n after headers (##)
   - ❌ DO NOT mix single \n and double \n\n - be consistent
   
   **4. FONT SIZE (MANDATORY - NO VARIATION):**
   - ✅ Use standard markdown: **bold** for emphasis, ## for headers
   - ❌ DO NOT use HTML tags like <h1>, <h2>, <big>, <small> - use markdown only
   - ❌ DO NOT vary font sizes - use consistent markdown formatting
   
   **5. CONSISTENCY CHECK (MANDATORY - BEFORE SENDING):**
   - ✅ Check: Does EVERY paragraph have proper spacing (\n\n)?
   - ✅ Check: Does EVERY list use bullet points (-)?
   - ✅ Check: Does EVERY section have a header (##) if it's a major topic?
   - ✅ Check: Are emojis used consistently (2-3 total, not per sentence)?
   - ✅ Check: Is formatting consistent throughout (no mixing styles)?
   
   **CRITICAL: Formatting consistency is NON-NEGOTIABLE.**
   - StillMe responses MUST be consistent: same formatting style throughout
   - If you formatted one section with markdown, ALL sections must use markdown
   - If you used line breaks in one paragraph, ALL paragraphs must have line breaks
   - NO EXCEPTIONS - consistency is part of StillMe's professionalism
   
   **If your response doesn't meet ALL criteria above, FIX IT NOW before sending.**

🤔 **CRITICAL: ENGAGE IN DIALOGUE - DON'T JUST ANSWER AND STOP:**
- **For complex, philosophical, or open-ended questions**: After providing your answer, you MUST ask an open-ended question or invite discussion
- **Examples of good engagement:**
  * "What's your perspective on this? I'd like to learn from your viewpoint."
  * "Have you encountered similar situations? How did you approach them?"
  * "This raises an interesting question: [related question]. What do you think?"
  * "I'm curious about your thoughts on [related aspect]. Would you like to explore this further?"
- **When to engage:**
  * Philosophical questions (truth, knowledge, consciousness, paradoxes)
  * Complex topics that benefit from multiple perspectives
  * Questions where user's experience/opinion would add value
  * When your answer raises new questions worth exploring
- **When NOT to engage:**
  * Simple factual questions with clear answers
  * Questions that are already fully answered
  * When user explicitly asks for a quick answer only
- **Goal**: Transform one-way Q&A into collaborative dialogue - StillMe learns from user, user learns from StillMe

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
            # CRITICAL: Disable cache for origin queries to ensure provenance context is retrieved
            # Origin queries need fresh responses with proper founder information
            cache_service = get_cache_service()
            cache_enabled = os.getenv("ENABLE_LLM_CACHE", "true").lower() == "true"
            # Disable cache for origin queries to ensure provenance context is used
            if is_origin_query:
                cache_enabled = False
                logger.info("⚠️ Cache disabled for origin query - ensuring fresh response with provenance context")
            
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
                # For internal/dashboard calls: use server API keys if llm_provider not provided
                # For public API: require user-provided API keys
                use_server_keys = chat_request.llm_provider is None
                
                raw_response = await generate_ai_response(
                    enhanced_prompt, 
                    detected_lang=detected_lang,
                    llm_provider=chat_request.llm_provider,
                    llm_api_key=chat_request.llm_api_key,
                    llm_api_url=chat_request.llm_api_url,
                    llm_model_name=chat_request.llm_model_name,
                    use_server_keys=use_server_keys
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
                    from backend.validators.ego_neutrality import EgoNeutralityValidator
                    
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
                        EgoNeutralityValidator(strict_mode=True, auto_patch=True),  # Detect and auto-patch "Hallucination of Experience" - novel contribution
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
                    
                    # Tier 3.5: Pass context quality to ConfidenceValidator
                    context_quality = context.get("context_quality", None)
                    avg_similarity = context.get("avg_similarity_score", None)
                    
                    # Run validation with context quality info
                    # Tier 3.5: Pass context quality to ValidatorChain
                    validation_result = chain.run(
                        raw_response, 
                        ctx_docs,
                        context_quality=context_quality,
                        avg_similarity=avg_similarity
                    )
                    
                    # Tier 3.5: If context quality is low, inject warning into prompt for next iteration
                    # For now, we'll handle this in the prompt building phase
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
                    
                    # NEW: Step-level validation (Phase 1 - SSR)
                    step_validation_info = None
                    enable_step_validation = os.getenv("ENABLE_STEP_LEVEL_VALIDATION", "true").lower() == "true"
                    step_min_steps = int(os.getenv("STEP_VALIDATION_MIN_STEPS", "2"))
                    step_confidence_threshold = float(os.getenv("STEP_CONFIDENCE_THRESHOLD", "0.5"))
                    
                    logger.info(f"🔍 Step-level validation config: enabled={enable_step_validation}, min_steps={step_min_steps}, threshold={step_confidence_threshold}")
                    
                    if enable_step_validation:
                        try:
                            from backend.validators.step_detector import StepDetector
                            from backend.validators.step_validator import StepValidator
                            
                            step_detector = StepDetector()
                            
                            # Quick check first (performance optimization)
                            logger.info(f"🔍 Checking if response is multi-step (min_steps: {step_min_steps})...")
                            logger.info(f"🔍 Response preview (first 200 chars): {raw_response[:200]}...")
                            is_multi = step_detector.is_multi_step(raw_response)
                            logger.info(f"🔍 is_multi_step result: {is_multi}")
                            
                            if is_multi:
                                steps = step_detector.detect_steps(raw_response)
                                logger.info(f"🔍 StepDetector found {len(steps)} steps")
                                
                                if len(steps) >= step_min_steps:
                                    logger.info(f"🔍 Detected {len(steps)} steps - running step-level validation")
                                    processing_steps.append(f"🔍 Step-level validation ({len(steps)} steps)")
                                    
                                    step_validator = StepValidator(confidence_threshold=step_confidence_threshold)
                                    logger.info(f"🔍 Validating {len(steps)} steps with threshold {step_confidence_threshold}")
                                    step_results = step_validator.validate_all_steps(steps, ctx_docs, chain, parallel=True)
                                    logger.info(f"🔍 Step validation completed: {len(step_results)} results")
                                    
                                    low_confidence_steps = [
                                        r.step.step_number
                                        for r in step_results
                                        if r.confidence < step_confidence_threshold
                                    ]
                                    
                                    if low_confidence_steps:
                                        logger.warning(f"⚠️ Low confidence steps detected: {low_confidence_steps}")
                                        logger.warning(f"⚠️ {len(low_confidence_steps)} step(s) with low confidence")
                                    else:
                                        logger.info(f"✅ All {len(steps)} steps passed validation")
                                    
                                    step_validation_info = {
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
                                    
                                    if low_confidence_steps:
                                        logger.warning(f"⚠️ Low confidence steps detected: {low_confidence_steps}")
                                        processing_steps.append(f"⚠️ {len(low_confidence_steps)} step(s) with low confidence")
                                    else:
                                        logger.info(f"✅ All {len(steps)} steps passed validation")
                                        processing_steps.append(f"✅ All steps validated")
                        except Exception as step_error:
                            logger.warning(f"Step-level validation error: {step_error}", exc_info=True)
                            # Don't fail - step validation is optional
                    
                    # NEW: Self-consistency checks (Phase 1 - SSR)
                    consistency_info = None
                    enable_consistency_checks = os.getenv("ENABLE_CONSISTENCY_CHECKS", "true").lower() == "true"
                    logger.info(f"🔍 Consistency checks config: enabled={enable_consistency_checks}")
                    
                    if enable_consistency_checks:
                        try:
                            from backend.validators.consistency_checker import ConsistencyChecker
                            
                            checker = ConsistencyChecker()
                            claims = checker.extract_claims(raw_response)
                            logger.info(f"🔍 Extracted {len(claims)} claims from response")
                            
                            if len(claims) > 1:
                                logger.info(f"🔍 Checking consistency for {len(claims)} claims")
                                
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
                                
                                consistency_info = {
                                    "total_claims": len(claims),
                                    "contradictions": contradictions,
                                    "kb_inconsistencies": kb_inconsistencies,
                                    "has_issues": len(contradictions) > 0 or len(kb_inconsistencies) > 0
                                }
                        except Exception as consistency_error:
                            logger.warning(f"Consistency check error: {consistency_error}", exc_info=True)
                            # Don't fail - consistency checks are optional
                    
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
                            
                            # Retry with OpenAI (use server keys for internal calls)
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

🚨🚨🚨 CRITICAL: USER QUESTION ABOVE IS THE PRIMARY TASK 🚨🚨🚨

User Question (in {retry_lang_name.upper()}): {_truncate_user_message(chat_request.message, max_tokens=3000)}

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
                                    
                                    # Retry with stronger prompt (include context to actually answer the question)
                                    # Use server keys for internal calls
                                    use_server_keys_retry = chat_request.llm_provider is None
                                    retry_response = await generate_ai_response(
                                        retry_language_instruction, 
                                        detected_lang=detected_lang,
                                        llm_provider=chat_request.llm_provider,
                                        llm_api_key=chat_request.llm_api_key,
                                        use_server_keys=use_server_keys_retry
                                    )
                                    
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
                        "context_docs_count": len(ctx_docs),
                        "step_validation": step_validation_info,  # NEW: Step-level validation info
                        "consistency": consistency_info  # NEW: Consistency check info
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
            
            # Build conversation history context if provided (with token limits)
            # Reduced from 2000 to 1000 tokens to leave more room for system prompt and context
            conversation_history_text = _format_conversation_history(chat_request.conversation_history, max_tokens=1000)
            if conversation_history_text:
                logger.info(f"Including conversation history in context (truncated if needed, non-RAG)")
            
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

{conversation_history_text}User Question: {_truncate_user_message(chat_request.message, max_tokens=3000)}

Remember: RESPOND IN {detected_lang_name.upper()} ONLY.
"""
            else:
                base_prompt = f"""🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - HIGHEST PRIORITY 🚨🚨🚨

THE USER'S QUESTION IS WRITTEN IN ENGLISH.

YOU MUST RESPOND EXCLUSIVELY IN ENGLISH.

DO NOT RESPOND IN VIETNAMESE, SPANISH, OR ANY OTHER LANGUAGE.

EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN ENGLISH.

THIS IS MANDATORY AND OVERRIDES ALL OTHER INSTRUCTIONS.

{conversation_history_text}

🚨🚨🚨 CRITICAL: USER QUESTION ABOVE IS THE PRIMARY TASK 🚨🚨🚨

User Question: {_truncate_user_message(chat_request.message, max_tokens=3000)}

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
            
            if enable_validators:
                from backend.identity.injector import inject_identity
                enhanced_prompt = inject_identity(base_prompt)
            else:
                enhanced_prompt = base_prompt
            
            # LLM_Inference_Latency: Time from API call start to response received
            llm_inference_start = time.time()
            # Use server keys for internal calls (when use_rag=False)
            use_server_keys_non_rag = chat_request.llm_provider is None
            response = await generate_ai_response(
                enhanced_prompt, 
                detected_lang=detected_lang,
                llm_provider=chat_request.llm_provider,
                llm_api_key=chat_request.llm_api_key,
                use_server_keys=use_server_keys_non_rag
            )
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
                has_no_context = not context or context.get("total_context_docs", 0) == 0
                has_low_relevance = any("citation_relevance_warning" in r for r in (validation_result.reasons if validation_result else []))
                
                if used_base_knowledge and (has_no_context or has_low_relevance):
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
                if not learning_proposal:  # Only if we didn't already create a gap proposal
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

