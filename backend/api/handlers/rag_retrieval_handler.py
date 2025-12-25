"""RAG retrieval handler for chat router.

This module contains RAG retrieval logic extracted from chat_router.py
to improve maintainability and reduce file size.
"""

import logging
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from backend.api.models import ChatRequest
from backend.api.config.chat_config import get_chat_config
from backend.vector_db.rag_retrieval import RAGRetrieval
from backend.core.stillme_detector import get_foundational_query_variants
from backend.core.query_preprocessor import is_historical_question, enhance_query_for_retrieval
from backend.core.decision_logger import DecisionLogger, AgentType, DecisionType

logger = logging.getLogger(__name__)


def _log_rag_retrieval_decision(
    decision_logger: DecisionLogger,
    context: Dict[str, Any],
    query: str,
    reasoning: str,
    similarity_threshold: Optional[float] = None,
    prioritize_foundational: bool = False,
    exclude_types: Optional[List[str]] = None,
    alternatives_considered: Optional[List[str]] = None
):
    """
    Helper function to log RAG retrieval decisions
    
    Args:
        decision_logger: DecisionLogger instance
        context: Retrieved context dictionary
        query: Query used for retrieval
        reasoning: Why this retrieval approach was chosen
        similarity_threshold: Similarity threshold used
        prioritize_foundational: Whether foundational knowledge was prioritized
        exclude_types: Content types excluded
        alternatives_considered: Alternative retrieval strategies considered
    """
    total_docs = context.get("total_context_docs", 0)
    knowledge_docs = context.get("knowledge_docs", [])
    
    # Extract document sources/types for context
    doc_sources = []
    for doc in knowledge_docs[:5]:  # Limit to 5 for logging
        if isinstance(doc, dict):
            metadata = doc.get("metadata", {})
            source = metadata.get("source", "unknown")
            doc_type = metadata.get("type", "unknown")
            doc_sources.append(f"{source}:{doc_type}")
    
    decision = f"Retrieved {total_docs} documents from ChromaDB"
    if prioritize_foundational:
        decision += " (prioritized foundational knowledge)"
    if similarity_threshold is not None:
        decision += f" (similarity threshold: {similarity_threshold})"
    
    context_data = {
        "total_docs": total_docs,
        "doc_sources": doc_sources[:5],  # Limit to 5
        "similarity_threshold": similarity_threshold,
        "prioritize_foundational": prioritize_foundational,
        "exclude_types": exclude_types
    }
    
    threshold_reasoning = None
    if similarity_threshold is not None:
        if similarity_threshold < 0.05:
            threshold_reasoning = f"Very low threshold ({similarity_threshold}) chosen to ensure StillMe foundational knowledge is retrieved even with low similarity scores"
        elif similarity_threshold < 0.1:
            threshold_reasoning = f"Low threshold ({similarity_threshold}) chosen for historical/factual questions to handle multilingual embedding mismatch"
        else:
            threshold_reasoning = f"Standard threshold ({similarity_threshold}) used for normal queries"
    
    decision_logger.log_decision(
        agent_type=AgentType.RAG_AGENT,
        decision_type=DecisionType.RETRIEVAL_DECISION,
        decision=decision,
        reasoning=reasoning,
        context=context_data,
        alternatives_considered=alternatives_considered,
        threshold_reasoning=threshold_reasoning,
        outcome=f"Successfully retrieved {total_docs} documents" if total_docs > 0 else "No documents retrieved",
        success=total_docs > 0
    )


def _prepare_exclude_types(is_philosophical: bool) -> List[str]:
    """
    Prepare exclude_types list based on query type.
    
    Args:
        is_philosophical: Whether this is a philosophical question
        
    Returns:
        List of content types to exclude
    """
    exclude_types = []
    if is_philosophical:
        exclude_types.append("technical")
    # Always exclude style_guide for user chat (prevents style drift from RAG)
    exclude_types.append("style_guide")
    return exclude_types


def _force_inject_manifest(
    context: dict,
    rag_retrieval: RAGRetrieval,
    exclude_types: List[str],
    is_philosophical: bool
) -> dict:
    """
    Force-inject manifest from file if not found in retrieved context.
    
    Args:
        context: Current context dict
        rag_retrieval: RAGRetrieval instance
        exclude_types: Content types to exclude
        is_philosophical: Whether this is a philosophical question
        
    Returns:
        Updated context dict with manifest injected
    """
    knowledge_docs = context.get("knowledge_docs", [])
    has_manifest = False
    manifest_has_correct_info = False
    
    # Check if manifest already exists in context
    for doc in knowledge_docs:
        if isinstance(doc, dict):
            metadata = doc.get("metadata", {})
            source = metadata.get("source", "") or ""
            title = metadata.get("title", "") or ""
            doc_content = str(doc.get("document", ""))
            if ("CRITICAL_FOUNDATION" in source or 
                "manifest" in title.lower() or 
                "validation_framework" in doc_content.lower() or
                "total_validators" in doc_content.lower()):
                has_manifest = True
                # CRITICAL: Check if manifest has correct info (19 validators, 7 layers)
                has_19 = "19 validators" in doc_content or "total_validators" in doc_content
                has_7 = "7 layers" in doc_content or "7 lớp" in doc_content
                if has_19 and has_7:
                    manifest_has_correct_info = True
                    logger.info(f"✅ Manifest found with correct info: 19 validators, 7 layers")
                else:
                    logger.warning(f"⚠️ Manifest found but has outdated info (has_19={has_19}, has_7={has_7}) - will force-inject correct manifest")
                break
    
    # Force-inject manifest if not found OR if found but has outdated info
    if not has_manifest or not manifest_has_correct_info:
        logger.warning(f"⚠️ Manifest not found or outdated in retrieved context - force-injecting from file")
        try:
            from scripts.inject_manifest_to_rag import manifest_to_text
            
            # Load manifest from file (source of truth)
            manifest_path = Path("data/stillme_manifest.json")
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                # Convert to text format
                manifest_text = manifest_to_text(manifest)
                
                # Create manifest document for injection
                manifest_doc = {
                    "document": manifest_text,
                    "metadata": {
                        "title": "StillMe Structural Manifest - Validation Framework",
                        "source": "CRITICAL_FOUNDATION",
                        "foundational": "stillme",
                        "type": "foundational",
                        "tags": "foundational:stillme,CRITICAL_FOUNDATION,stillme,validation,validators,validation-chain,structural-manifest,system-architecture,self-awareness",
                        "importance_score": 1.0,
                        "manifest_version": manifest.get("version", "1.2.0"),
                        "last_sync": manifest.get("last_sync", ""),
                        "description": "CRITICAL: Structural manifest of StillMe's validation framework - source of truth for validator count and architecture."
                    }
                }
                
                # Inject manifest at the beginning of knowledge_docs
                knowledge_docs = [manifest_doc] + knowledge_docs
                context["knowledge_docs"] = knowledge_docs
                context["total_context_docs"] = len(knowledge_docs) + len(context.get("conversation_docs", []))
                
                total_validators = manifest.get("validation_framework", {}).get("total_validators", 0)
                num_layers = len(manifest.get("validation_framework", {}).get("layers", []))
                logger.info(f"✅ Force-injected manifest from file into context: {total_validators} validators, {num_layers} layers")
            else:
                logger.error(f"❌ Manifest file not found: {manifest_path} - cannot force-inject")
                # Fallback: Try direct manifest retrieval from ChromaDB
                manifest_query = "StillMe Structural Manifest validation framework total_validators layers 19 validators 7 layers"
                manifest_context = rag_retrieval.retrieve_context(
                    query=manifest_query,
                    knowledge_limit=5,
                    conversation_limit=0,
                    prioritize_foundational=True,
                    similarity_threshold=get_chat_config().similarity.VALIDATOR_COUNT_QUESTION,
                    exclude_content_types=None,
                    is_philosophical=False
                )
                manifest_docs = manifest_context.get("knowledge_docs", [])
                filtered_manifest_docs = [
                    doc for doc in manifest_docs
                    if isinstance(doc, dict) and (
                        "CRITICAL_FOUNDATION" in str(doc.get("metadata", {}).get("source", "")) or
                        "manifest" in str(doc.get("metadata", {}).get("title", "")).lower()
                    )
                ]
                if filtered_manifest_docs:
                    knowledge_docs = filtered_manifest_docs + knowledge_docs
                    context["knowledge_docs"] = knowledge_docs
                    context["total_context_docs"] = len(knowledge_docs) + len(context.get("conversation_docs", []))
                    logger.info(f"✅ Force-injected manifest from ChromaDB: {len(filtered_manifest_docs)} manifest docs")
        except Exception as manifest_inject_error:
            logger.error(f"❌ Failed to force-inject manifest: {manifest_inject_error}", exc_info=True)
    
    return context


def _retrieve_origin_context(
    chat_request: ChatRequest,
    rag_retrieval: RAGRetrieval,
    exclude_types: List[str],
    is_philosophical: bool
) -> dict:
    """
    Retrieve provenance knowledge for origin queries.
    
    Args:
        chat_request: ChatRequest from user
        rag_retrieval: RAGRetrieval instance
        exclude_types: Content types to exclude
        is_philosophical: Whether this is a philosophical question
        
    Returns:
        Context dict with provenance documents
    """
    logger.debug("Origin query detected - retrieving provenance knowledge")
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
            return context
        else:
            # Fallback to normal retrieval if provenance not found
            return _retrieve_historical_context(
                chat_request,
                rag_retrieval,
                exclude_types,
                is_philosophical
            )
    except Exception as provenance_error:
        logger.warning(f"Provenance retrieval failed: {provenance_error}, falling back to historical retrieval")
        return _retrieve_historical_context(
            chat_request,
            rag_retrieval,
            exclude_types,
            is_philosophical
        )


def _retrieve_historical_context(
    chat_request: ChatRequest,
    rag_retrieval: RAGRetrieval,
    exclude_types: List[str],
    is_philosophical: bool
) -> dict:
    """
    Retrieve context for historical questions with enhanced query.
    
    Args:
        chat_request: ChatRequest from user
        rag_retrieval: RAGRetrieval instance
        exclude_types: Content types to exclude
        is_philosophical: Whether this is a philosophical question
        
    Returns:
        Context dict with historical documents
    """
    config = get_chat_config()
    is_historical = is_historical_question(chat_request.message)
    retrieval_query = chat_request.message
    similarity_threshold = config.similarity.LOW_CONTEXT_QUALITY  # Default
    
    if is_historical:
        # Very low threshold to ensure we find historical facts even with multilingual mismatch
        similarity_threshold = config.similarity.VERY_LOW
        retrieval_query = enhance_query_for_retrieval(chat_request.message)
        logger.info(f"📜 Historical question - using very low threshold {similarity_threshold}, enhanced query: '{retrieval_query[:100]}...'")
    
    return rag_retrieval.retrieve_context(
        query=retrieval_query,
        knowledge_limit=chat_request.context_limit,
        conversation_limit=1,
        exclude_content_types=exclude_types if exclude_types else None,
        prioritize_style_guide=False,  # Never prioritize style guide for user chat
        similarity_threshold=similarity_threshold,
        is_philosophical=is_philosophical
    )


def _retrieve_validator_count_context(
    chat_request: ChatRequest,
    rag_retrieval: RAGRetrieval,
    exclude_types: List[str],
    is_philosophical: bool
) -> dict:
    """
    Retrieve manifest for validator count questions with force-injection.
    
    Args:
        chat_request: ChatRequest from user
        rag_retrieval: RAGRetrieval instance
        exclude_types: Content types to exclude
        is_philosophical: Whether this is a philosophical question
        
    Returns:
        Context dict with manifest injected
    """
    config = get_chat_config()
    logger.info(f"🎯 Validator count question - forcing manifest retrieval with very low similarity threshold ({config.similarity.VALIDATOR_COUNT_QUESTION})")
    
    # Force retrieve manifest with very low threshold to ensure we get it
    context = rag_retrieval.retrieve_context(
        query=chat_request.message,
        knowledge_limit=5,  # Get more docs to ensure manifest is included
        conversation_limit=1,
        prioritize_foundational=True,  # CRITICAL: Prioritize foundational knowledge
        similarity_threshold=config.similarity.VALIDATOR_COUNT_QUESTION,  # CRITICAL: Very low threshold to ensure manifest is retrieved
        exclude_content_types=exclude_types if exclude_types else None,
        is_philosophical=is_philosophical
    )
    
    # Force-inject manifest if not found
    context = _force_inject_manifest(context, rag_retrieval, exclude_types, is_philosophical)
    
    return context


def _retrieve_stillme_context(
    chat_request: ChatRequest,
    rag_retrieval: RAGRetrieval,
    exclude_types: List[str],
    is_philosophical: bool,
    is_validator_count_question: bool
) -> dict:
    """
    Retrieve foundational knowledge for StillMe queries with query variants.
    
    Args:
        chat_request: ChatRequest from user
        rag_retrieval: RAGRetrieval instance
        exclude_types: Content types to exclude
        is_philosophical: Whether this is a philosophical question
        is_validator_count_question: Whether this is a validator count question
        
    Returns:
        Context dict with foundational knowledge documents
    """
    config = get_chat_config()
    
    # CRITICAL: For validator count questions, force-inject manifest and use very low similarity threshold
    if is_validator_count_question:
        return _retrieve_validator_count_context(
            chat_request,
            rag_retrieval,
            exclude_types,
            is_philosophical
        )
    
    # Try multiple query variants to ensure we get StillMe foundational knowledge
    query_variants = get_foundational_query_variants(chat_request.message)
    all_knowledge_docs = []
    
    for variant in query_variants[:3]:  # Try first 3 variants
        variant_context = rag_retrieval.retrieve_context(
            query=variant,
            knowledge_limit=chat_request.context_limit,
            conversation_limit=0,  # Don't need conversation for foundational queries
            prioritize_foundational=True,
            similarity_threshold=0.01,  # CRITICAL: Use very low threshold for StillMe queries to ensure foundational knowledge is retrieved
            exclude_content_types=["technical", "style_guide"] if is_philosophical else ["style_guide"],
            prioritize_style_guide=is_philosophical,
            is_philosophical=is_philosophical
        )
        # Merge results, avoiding duplicates
        existing_ids = {doc.get("id") for doc in all_knowledge_docs}
        for doc in variant_context.get("knowledge_docs", []):
            if doc.get("id") not in existing_ids:
                all_knowledge_docs.append(doc)
    
    # If we still don't have results, do normal retrieval with very low threshold
    if not all_knowledge_docs:
        logger.warning("No foundational knowledge found, falling back to normal retrieval with very low threshold")
        context = rag_retrieval.retrieve_context(
            query=chat_request.message,
            knowledge_limit=chat_request.context_limit,
            conversation_limit=2,
            prioritize_foundational=True,
            similarity_threshold=0.01,  # CRITICAL: Use very low threshold for StillMe queries
            exclude_content_types=["technical", "style_guide"] if is_philosophical else ["style_guide"],
            prioritize_style_guide=is_philosophical,
            is_philosophical=is_philosophical
        )
        return context
    else:
        # Use merged results
        context = {
            "knowledge_docs": all_knowledge_docs[:chat_request.context_limit],
            "conversation_docs": [],
            "total_context_docs": len(all_knowledge_docs[:chat_request.context_limit])
        }
        logger.info(f"Retrieved {len(context['knowledge_docs'])} StillMe foundational knowledge documents")
        return context


def _check_and_filter_critical_foundation(context: dict) -> dict:
    """
    Post-filter to remove CRITICAL_FOUNDATION docs for news/article queries.
    
    Args:
        context: Context dict with knowledge_docs
        
    Returns:
        Filtered context dict
    """
    if not context or not context.get("knowledge_docs"):
        return context
    
    filtered_docs = []
    for doc in context.get("knowledge_docs", []):
        if isinstance(doc, dict):
            metadata = doc.get("metadata", {})
            source = metadata.get("source", "")
            doc_type = metadata.get("type", "")
            foundational = metadata.get("foundational", "")
            tags = str(metadata.get("tags", ""))
            
            is_critical_foundation = (
                source == "CRITICAL_FOUNDATION" or
                doc_type == "foundational" or
                foundational == "stillme" or
                "CRITICAL_FOUNDATION" in tags or
                "foundational:stillme" in tags
            )
            
            if not is_critical_foundation:
                filtered_docs.append(doc)
            else:
                logger.debug(f"Post-filter: Excluding CRITICAL_FOUNDATION doc: {metadata.get('title', 'N/A')}")
    
    context["knowledge_docs"] = filtered_docs
    context["total_context_docs"] = len(filtered_docs) + len(context.get("conversation_docs", []))
    logger.info(f"📰 Post-filtered: {len(filtered_docs)} non-foundational docs remaining (excluded {len(context.get('knowledge_docs', [])) - len(filtered_docs)} foundational docs)")
    
    return context


def _retrieve_news_article_context(
    chat_request: ChatRequest,
    rag_retrieval: RAGRetrieval,
    exclude_types: List[str],
    is_philosophical: bool
) -> dict:
    """
    Retrieve context for news/article queries (exclude CRITICAL_FOUNDATION).
    
    Args:
        chat_request: ChatRequest from user
        rag_retrieval: RAGRetrieval instance
        exclude_types: Content types to exclude
        is_philosophical: Whether this is a philosophical question
        
    Returns:
        Context dict with news/article documents (CRITICAL_FOUNDATION excluded)
    """
    config = get_chat_config()
    logger.info(f"📰 News/article query - using higher similarity threshold ({config.similarity.HIGH_CONTEXT_QUALITY}) and excluding CRITICAL_FOUNDATION")
    
    # Increase knowledge_limit to get more results (since we're excluding foundational)
    context = rag_retrieval.retrieve_context(
        query=chat_request.message,
        knowledge_limit=min(chat_request.context_limit * 2, 20),  # Get more docs to compensate for exclusion
        conversation_limit=1,
        prioritize_foundational=False,  # CRITICAL: Don't prioritize foundational for news queries
        similarity_threshold=config.similarity.HIGH_CONTEXT_QUALITY,  # CRITICAL: Higher threshold to ensure relevance
        exclude_content_types=exclude_types if exclude_types else None,
        prioritize_style_guide=False,
        is_philosophical=is_philosophical
    )
    
    # CRITICAL: Post-filter to remove any CRITICAL_FOUNDATION docs that slipped through
    context = _check_and_filter_critical_foundation(context)
    
    return context


def _retrieve_normal_context(
    chat_request: ChatRequest,
    rag_retrieval: RAGRetrieval,
    exclude_types: List[str],
    is_philosophical: bool,
    is_technical_question: bool,
    decision_logger: Optional[DecisionLogger] = None
) -> dict:
    """
    Normal RAG retrieval with standard parameters.
    
    Args:
        chat_request: ChatRequest from user
        rag_retrieval: RAGRetrieval instance
        exclude_types: Content types to exclude
        is_philosophical: Whether this is a philosophical question
        is_technical_question: Whether this is a technical question
        decision_logger: Optional DecisionLogger for logging
        
    Returns:
        Context dict with retrieved documents
    """
    config = get_chat_config()
    
    # SOLUTION 1 & 3: Improve retrieval for historical/factual questions
    is_historical = is_historical_question(chat_request.message)
    retrieval_query = chat_request.message
    similarity_threshold = config.similarity.LOW_CONTEXT_QUALITY  # Default
    
    if is_historical:
        # SOLUTION 1: Very low threshold for historical questions (0.03 instead of 0.1)
        # This ensures we find historical facts even with multilingual embedding mismatch
        similarity_threshold = config.similarity.VERY_LOW
        logger.info(f"📜 Historical question detected - using very low similarity threshold: {similarity_threshold}")
        
        # SOLUTION 3: Enhance query with English keywords
        retrieval_query = enhance_query_for_retrieval(chat_request.message)
        logger.info(f"🔍 Enhanced query for better cross-lingual matching: '{chat_request.message}' -> '{retrieval_query}'")
    
    context = rag_retrieval.retrieve_context(
        query=retrieval_query,  # Use enhanced query
        knowledge_limit=min(chat_request.context_limit, 5),  # Cap at 5 for latency
        conversation_limit=1,  # Optimized: reduced from 2 to 1
        exclude_content_types=["technical"] if is_philosophical else None,
        prioritize_style_guide=is_philosophical,
        prioritize_foundational=is_technical_question,  # Prioritize foundational for technical questions
        similarity_threshold=similarity_threshold,  # Use adaptive threshold
        is_philosophical=is_philosophical
    )
    
    # Log RAG retrieval decision
    if decision_logger and context:
        reasoning = "Normal retrieval for non-StillMe queries"
        if is_historical:
            reasoning = "Historical question detected - using very low similarity threshold (0.03) and enhanced query for better cross-lingual matching"
        elif is_technical_question:
            reasoning = "Technical question detected - prioritizing foundational knowledge"
        _log_rag_retrieval_decision(
            decision_logger,
            context,
            retrieval_query,
            reasoning,
            similarity_threshold=similarity_threshold,
            prioritize_foundational=is_technical_question,
            exclude_types=["technical"] if is_philosophical else None,
            alternatives_considered=["Higher similarity threshold", "No query enhancement"] if is_historical else None
        )
    
    return context


def retrieve_rag_context(
    chat_request: ChatRequest,
    rag_retrieval: Optional[RAGRetrieval],
    is_origin_query: bool,
    is_validator_count_question: bool,
    is_stillme_query: bool,
    is_news_article_query: bool,
    is_philosophical: bool,
    is_technical_question: bool = False,
    decision_logger: Optional[DecisionLogger] = None,
    processing_steps: Optional[List[str]] = None
) -> Optional[dict]:
    """
    Unified RAG retrieval handler that routes to appropriate retrieval strategy.
    
    Args:
        chat_request: ChatRequest from user
        rag_retrieval: RAGRetrieval instance (can be None if RAG disabled)
        is_origin_query: Whether this is an origin query
        is_validator_count_question: Whether this is a validator count question
        is_stillme_query: Whether this is a StillMe query
        is_news_article_query: Whether this is a news/article query
        is_philosophical: Whether this is a philosophical question
        is_technical_question: Whether this is a technical question
        decision_logger: Optional DecisionLogger for logging
        
    Returns:
        Context dict if RAG enabled and retrieval successful, None otherwise
    """
    if not rag_retrieval or not chat_request.use_rag:
        return None
    
    # Add processing step if provided
    if processing_steps is not None:
        processing_steps.append("🔍 Searching knowledge base...")
    
    # Prepare exclude_types
    exclude_types = _prepare_exclude_types(is_philosophical)
    
    # CRITICAL: Check if technical question about "your system" - treat as StillMe query
    if not is_stillme_query and is_technical_question:
        question_lower = chat_request.message.lower()
        has_your_system = any(
            phrase in question_lower 
            for phrase in [
                "your system", "in your system", "your.*system", "system.*you",
                "bạn.*hệ thống", "hệ thống.*bạn", "của bạn", "bạn.*sử dụng"
            ]
        )
        if has_your_system:
            is_stillme_query = True
            logger.info("Technical question about 'your system' detected - treating as StillMe query")
    
    # Route to appropriate retrieval strategy
    if is_origin_query:
        # CRITICAL: If origin query detected, retrieve provenance knowledge ONLY
        return _retrieve_origin_context(
            chat_request,
            rag_retrieval,
            exclude_types,
            is_philosophical
        )
    elif is_validator_count_question:
        # CRITICAL: Handle validator count questions FIRST (even if not detected as stillme_query)
        return _retrieve_validator_count_context(
            chat_request,
            rag_retrieval,
            exclude_types,
            is_philosophical
        )
    elif is_stillme_query:
        # If StillMe query detected (but not origin), prioritize foundational knowledge
        return _retrieve_stillme_context(
            chat_request,
            rag_retrieval,
            exclude_types,
            is_philosophical,
            is_validator_count_question
        )
    elif is_news_article_query:
        # CRITICAL FIX: For news/article queries, exclude CRITICAL_FOUNDATION and use higher similarity threshold
        return _retrieve_news_article_context(
            chat_request,
            rag_retrieval,
            exclude_types,
            is_philosophical
        )
    else:
        # Normal retrieval for non-StillMe queries
        return _retrieve_normal_context(
            chat_request,
            rag_retrieval,
            exclude_types,
            is_philosophical,
            is_technical_question,
            decision_logger
        )

