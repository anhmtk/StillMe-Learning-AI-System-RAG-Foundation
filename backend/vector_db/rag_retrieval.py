"""
RAG (Retrieval-Augmented Generation) Service for StillMe
Combines vector search with knowledge retrieval
"""

from typing import List, Dict, Any, Optional
from .chroma_client import ChromaClient
from .embeddings import EmbeddingService
from backend.services.cache_service import (
    get_cache_service,
    CACHE_PREFIX_RAG,
    TTL_RAG_RETRIEVAL
)
import logging
import os
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class RAGRetrieval:
    """RAG service for knowledge retrieval and context building"""
    
    def __init__(self, chroma_client: ChromaClient, embedding_service: EmbeddingService):
        """Initialize RAG service
        
        Args:
            chroma_client: ChromaDB client instance
            embedding_service: Embedding service instance
        """
        self.chroma_client = chroma_client
        self.embedding_service = embedding_service
        logger.info("RAG Retrieval service initialized")
    
    def retrieve_context(self, 
                        query: str, 
                        knowledge_limit: int = 3,  # Increased from 2 to 3 for better coverage
                        conversation_limit: int = 1,  # Optimized: reduced from 2 to 1 for latency
                        prioritize_foundational: bool = False,
                        tier_preference: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve relevant context for a query
        
        Args:
            query: Query string
            knowledge_limit: Number of knowledge documents to retrieve
            conversation_limit: Number of conversation documents to retrieve
            prioritize_foundational: If True, prioritize foundational knowledge (tagged with 'foundational:stillme')
            tier_preference: Optional tier preference (L0, L1, L2, L3) for Nested Learning retrieval strategy
        """
        try:
            import os
            ENABLE_CONTINUUM_MEMORY = os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true"
            
            # Phase 2: RAG Retrieval Cache - Check cache first
            cache_service = get_cache_service()
            cache_enabled = os.getenv("ENABLE_RAG_CACHE", "true").lower() == "true"
            cached_result = None
            cache_hit = False
            cache_key = None
            
            if cache_enabled:
                # Generate cache key from query + parameters
                # Use query text hash (embedding is expensive, we'll generate it once below)
                cache_key = cache_service._generate_key(
                    CACHE_PREFIX_RAG,
                    query,
                    knowledge_limit,
                    conversation_limit,
                    prioritize_foundational,
                    tier_preference
                )
                
                # Try to get from cache
                cached_result = cache_service.get(cache_key)
                if cached_result:
                    cache_hit = True
                    logger.info(f"✅ RAG cache HIT (saved {cached_result.get('latency', 0):.2f}s)")
                    return cached_result.get("context")
            
            # If not in cache, perform retrieval
            # Generate query embedding (only once, used for both cache key and search)
            query_embedding = self.embedding_service.encode_text(query)
            
            # Nested Learning: If tier_preference is specified, use tier-based retrieval
            if tier_preference and ENABLE_CONTINUUM_MEMORY:
                knowledge_results = self.retrieve_by_tier(query, tier_preference, knowledge_limit)
                logger.info(f"Using tier-based retrieval (tier={tier_preference}): {len(knowledge_results)} results")
            else:
                logger.info(f"Query embedding generated: {len(query_embedding)} dimensions")
                
                # OPTIMIZATION: Run knowledge and conversation search in parallel for better latency
                # Helper function to run knowledge search (with all the complex logic)
                def _search_knowledge():
                    knowledge_results = []
                    if prioritize_foundational:
                        try:
                            # Try to retrieve foundational knowledge first
                            try:
                                critical_results = self.chroma_client.search_knowledge(
                                    query_embedding=query_embedding,
                                    limit=knowledge_limit,
                                    where={"source": "CRITICAL_FOUNDATION"}
                                )
                                if critical_results:
                                    foundational_results = critical_results
                                    logger.info(f"Found {len(critical_results)} CRITICAL_FOUNDATION documents")
                                else:
                                    foundational_results = self.chroma_client.search_knowledge(
                                        query_embedding=query_embedding,
                                        limit=knowledge_limit,
                                        where={"$or": [
                                            {"foundational": "stillme"},
                                            {"source": "foundational"},
                                            {"type": "foundational"},
                                            {"tags": {"$contains": "foundational:stillme"}},
                                            {"tags": {"$contains": "CRITICAL_FOUNDATION"}}
                                        ]}
                                    )
                            except Exception as filter_error:
                                logger.debug(f"Metadata filter not supported: {filter_error}")
                                foundational_results = []
                            if foundational_results:
                                knowledge_results.extend(foundational_results)
                                logger.info(f"Found {len(foundational_results)} foundational knowledge documents")
                        except Exception as foundational_error:
                            logger.debug(f"Foundational knowledge filter not available: {foundational_error}")
                    
                    # If we don't have enough results, do normal search
                    if len(knowledge_results) < knowledge_limit:
                        normal_results = self.chroma_client.search_knowledge(
                            query_embedding=query_embedding,
                            limit=knowledge_limit * 2  # Get more to filter out provenance
                        )
                        # Merge results, avoiding duplicates
                        existing_ids = {doc.get("id") for doc in knowledge_results}
                        for doc in normal_results:
                            if doc.get("id") not in existing_ids:
                                # Filter out provenance documents
                                doc_metadata = doc.get("metadata", {})
                                doc_source = doc_metadata.get("source", "")
                                doc_type = doc_metadata.get("type", "")
                                doc_tags = doc_metadata.get("tags", "")
                                
                                is_provenance = (
                                    doc_source == "PROVENANCE" or
                                    doc_type == "provenance" or
                                    "provenance" in str(doc_tags).lower() or
                                    "intent:origin" in str(doc_tags).lower() or
                                    "intent:founder" in str(doc_tags).lower()
                                )
                                
                                if is_provenance:
                                    continue
                                
                                knowledge_results.append(doc)
                                if len(knowledge_results) >= knowledge_limit:
                                    break
                    return knowledge_results
                
                # Helper function to run conversation search
                def _search_conversations():
                    if conversation_limit > 0:
                        return self.chroma_client.search_conversations(
                            query_embedding=query_embedding,
                            limit=conversation_limit
                        )
                    return []
                
                # OPTIMIZATION: Run both searches in parallel using ThreadPoolExecutor
                # This works in both sync and async contexts without breaking backward compatibility
                try:
                    if conversation_limit > 0:
                        # Run both searches in parallel
                        with ThreadPoolExecutor(max_workers=2) as executor:
                            knowledge_future = executor.submit(_search_knowledge)
                            conversation_future = executor.submit(_search_conversations)
                            
                            # Wait for both to complete
                            knowledge_results = knowledge_future.result()
                            conversation_results = conversation_future.result()
                    else:
                        # Only knowledge search needed
                        knowledge_results = _search_knowledge()
                        conversation_results = []
                except Exception as parallel_error:
                    # Fallback to sequential if parallel fails
                    logger.debug(f"Parallel search failed, using sequential: {parallel_error}")
                    knowledge_results = _search_knowledge()
                    conversation_results = _search_conversations()
                
                logger.info(f"Knowledge search returned {len(knowledge_results)} results")
                if conversation_results:
                    logger.info(f"Conversation search returned {len(conversation_results)} results")
            
            # Build context result
            context_result = {
                "knowledge_docs": knowledge_results[:knowledge_limit],
                "conversation_docs": conversation_results,
                "total_context_docs": len(knowledge_results[:knowledge_limit]) + len(conversation_results)
            }
            
            # Save to cache (only if not a cache hit)
            if cache_enabled and not cache_hit:
                try:
                    import time
                    cache_value = {
                        "context": context_result,
                        "latency": 0.0,  # Could track actual latency if needed
                        "timestamp": time.time()
                    }
                    cache_service.set(cache_key, cache_value, ttl_seconds=TTL_RAG_RETRIEVAL)
                    logger.debug(f"💾 RAG retrieval cached (key: {cache_key[:50]}...)")
                except Exception as cache_error:
                    logger.warning(f"Failed to cache RAG retrieval: {cache_error}")
            
            return context_result
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return {
                "knowledge_docs": [],
                "conversation_docs": [],
                "total_context_docs": 0
            }
    
    def retrieve_by_tier(self, 
                        query: str,
                        tier: str,
                        knowledge_limit: int = 2) -> List[Dict[str, Any]]:
        """
        Nested Learning: Retrieve knowledge from a specific tier.
        
        Tier-based retrieval strategy:
        - L0: Recent knowledge (short-term, task-specific)
        - L1: Medium-term knowledge (in-context learning)
        - L2: Long-term knowledge (domain knowledge)
        - L3: Core knowledge (permanent, high importance)
        
        Args:
            query: Query string
            tier: Tier name (L0, L1, L2, L3)
            knowledge_limit: Number of knowledge documents to retrieve
            
        Returns:
            List of knowledge documents from the specified tier
        """
        try:
            import os
            ENABLE_CONTINUUM_MEMORY = os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true"
            
            if not ENABLE_CONTINUUM_MEMORY:
                # Fallback to normal retrieval if Continuum Memory is disabled
                context = self.retrieve_context(query, knowledge_limit=knowledge_limit, conversation_limit=0)
                return context.get("knowledge_docs", [])
            
            # Generate query embedding
            query_embedding = self.embedding_service.encode_text(query)
            
            # Build tier-based filter
            where_filter = {"tier": tier}
            
            # Additional filters based on tier
            if tier == "L0":
                # L0: Recent knowledge (last 4 hours = last cycle)
                # Filter by scheduler_cycle >= (current_cycle - 1)
                # Note: This requires cycle_number to be passed, but for now we'll just filter by tier
                pass
            elif tier == "L1":
                # L1: Medium-term (last 40 hours = last 10 cycles)
                # Could filter by scheduler_cycle, but tier filter is sufficient
                pass
            elif tier == "L2":
                # L2: Long-term (last 17 days = last 100 cycles)
                pass
            elif tier == "L3":
                # L3: Core knowledge (permanent, high importance)
                # Filter by tier="L3" and optionally surprise_score >= 0.8
                where_filter = {"tier": "L3"}
            
            # Retrieve from specified tier
            try:
                tier_results = self.chroma_client.search_knowledge(
                    query_embedding=query_embedding,
                    limit=knowledge_limit,
                    where=where_filter
                )
                logger.info(f"Retrieved {len(tier_results)} documents from tier {tier}")
                return tier_results
            except Exception as filter_error:
                # If metadata filter fails, try without filter (ChromaDB version compatibility)
                logger.debug(f"Tier filter not supported, trying without filter: {filter_error}")
                # Fallback: retrieve all and filter by tier in metadata
                all_results = self.chroma_client.search_knowledge(
                    query_embedding=query_embedding,
                    limit=knowledge_limit * 2  # Get more to filter
                )
                # Filter by tier in metadata
                tier_results = [
                    doc for doc in all_results
                    if doc.get("metadata", {}).get("tier") == tier
                ][:knowledge_limit]
                logger.info(f"Retrieved {len(tier_results)} documents from tier {tier} (fallback filtering)")
                return tier_results
                
        except Exception as e:
            logger.error(f"Error retrieving by tier {tier}: {e}")
            # Fallback to normal retrieval
            context = self.retrieve_context(query, knowledge_limit=knowledge_limit, conversation_limit=0)
            return context.get("knowledge_docs", [])
        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            return {
                "knowledge_docs": [],
                "conversation_docs": [],
                "total_context_docs": 0
            }
    
    def retrieve_important_knowledge(self, 
                                    query: str,
                                    limit: int = 1,
                                    min_importance: float = 0.7) -> List[Dict[str, Any]]:
        """
        Retrieve high-importance knowledge related to query
        
        Args:
            query: Query string to find related knowledge
            limit: Maximum number of important knowledge items to return
            min_importance: Minimum importance score (0.0-1.0)
            
        Returns:
            List of important knowledge documents
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.encode_text(query)
            
            # Retrieve knowledge documents (get more to filter by importance)
            knowledge_results = self.chroma_client.search_knowledge(
                query_embedding=query_embedding,
                limit=limit * 3  # Get more to filter by importance
            )
            
            # Filter by importance score
            important_knowledge = []
            for doc in knowledge_results:
                metadata = doc.get("metadata", {})
                importance_score = metadata.get("importance_score", 0.0)
                
                if importance_score >= min_importance:
                    important_knowledge.append(doc)
                    if len(important_knowledge) >= limit:
                        break
            
            logger.info(f"Retrieved {len(important_knowledge)} important knowledge items (min_importance={min_importance})")
            return important_knowledge
            
        except Exception as e:
            logger.error(f"Error retrieving important knowledge: {e}")
            return []
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: ~4 chars per token)"""
        if not text:
            return 0
        # Rough estimate: 1 token ≈ 4 characters (conservative for English)
        # For mixed languages, this is still a reasonable approximation
        return len(text) // 4
    
    def _truncate_text_by_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to fit within max_tokens limit"""
        if not text:
            return text
        
        estimated_tokens = self._estimate_tokens(text)
        if estimated_tokens <= max_tokens:
            return text
        
        # Truncate to approximately max_tokens
        # Use character-based truncation (max_tokens * 4 chars)
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text
        
        # Truncate and add ellipsis
        truncated = text[:max_chars].rsplit(' ', 1)[0]  # Cut at word boundary
        return truncated + "... [truncated]"
    
    def build_prompt_context(self, context: Dict[str, Any], max_context_tokens: int = 8000) -> str:
        """
        Build formatted context for LLM prompt with token limits
        
        Args:
            context: Context dictionary with knowledge_docs and conversation_docs
            max_context_tokens: Maximum tokens for context (default: 8000 to leave room for system prompt and user message)
        """
        try:
            context_parts = []
            remaining_tokens = max_context_tokens
            
            # Add knowledge context
            if context.get("knowledge_docs"):
                header = "## Relevant Knowledge:"
                header_tokens = self._estimate_tokens(header)
                remaining_tokens -= header_tokens
                context_parts.append(header)
                
                for i, doc in enumerate(context["knowledge_docs"], 1):
                    if remaining_tokens <= 100:  # Stop if too little space left
                        logger.warning(f"Stopped adding knowledge docs at {i}/{len(context['knowledge_docs'])} due to token limit")
                        break
                    
                    source = doc.get("metadata", {}).get("source", "Unknown")
                    content = doc.get("content", "")
                    
                    # Allocate tokens per document (distribute remaining tokens)
                    # Reserve some tokens for formatting
                    doc_max_tokens = remaining_tokens // max(1, len(context["knowledge_docs"]) - i + 1)
                    doc_max_tokens = min(doc_max_tokens, 2000)  # Cap each doc at 2000 tokens
                    
                    truncated_content = self._truncate_text_by_tokens(content, doc_max_tokens)
                    doc_text = f"{i}. {truncated_content} (Source: {source})"
                    
                    doc_tokens = self._estimate_tokens(doc_text)
                    remaining_tokens -= doc_tokens
                    context_parts.append(doc_text)
            
            # Add conversation context
            if context.get("conversation_docs") and remaining_tokens > 500:
                header = "\n## Recent Conversations:"
                header_tokens = self._estimate_tokens(header)
                remaining_tokens -= header_tokens
                context_parts.append(header)
                
                for i, doc in enumerate(context["conversation_docs"], 1):
                    if remaining_tokens <= 100:
                        logger.warning(f"Stopped adding conversation docs at {i}/{len(context['conversation_docs'])} due to token limit")
                        break
                    
                    timestamp = doc.get("metadata", {}).get("timestamp", "Unknown")
                    content = doc.get("content", "")
                    
                    # Allocate tokens per conversation doc
                    conv_max_tokens = remaining_tokens // max(1, len(context["conversation_docs"]) - i + 1)
                    conv_max_tokens = min(conv_max_tokens, 1000)  # Cap each conversation at 1000 tokens
                    
                    truncated_content = self._truncate_text_by_tokens(content, conv_max_tokens)
                    doc_text = f"{i}. {truncated_content} (Time: {timestamp})"
                    
                    doc_tokens = self._estimate_tokens(doc_text)
                    remaining_tokens -= doc_tokens
                    context_parts.append(doc_text)
            
            result = "\n".join(context_parts) if context_parts else "No relevant context found."
            
            # Final check: if result is still too long, truncate the entire result
            result_tokens = self._estimate_tokens(result)
            if result_tokens > max_context_tokens:
                logger.warning(f"Context still too long ({result_tokens} tokens), truncating entire result")
                result = self._truncate_text_by_tokens(result, max_context_tokens)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to build prompt context: {e}")
            return "Error building context."
    
    def add_learning_content(self, 
                           content: str, 
                           source: str, 
                           content_type: str = "knowledge",
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add new learning content to vector database"""
        try:
            import uuid
            from datetime import datetime
            
            # Prepare metadata
            doc_metadata = {
                "source": source,
                "type": content_type,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            doc_id = f"{content_type}_{uuid.uuid4().hex[:8]}"
            
            # Add to appropriate collection
            if content_type == "knowledge":
                success = self.chroma_client.add_knowledge(
                    documents=[content],
                    metadatas=[doc_metadata],
                    ids=[doc_id]
                )
            else:
                success = self.chroma_client.add_conversation(
                    documents=[content],
                    metadatas=[doc_metadata],
                    ids=[doc_id]
                )
            
            if success:
                logger.info(f"Added {content_type} content from {source}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add learning content: {e}")
            return False
