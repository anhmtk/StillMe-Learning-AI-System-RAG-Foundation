"""
RAG (Retrieval-Augmented Generation) Service for StillMe
Combines vector search with knowledge retrieval
"""

from typing import List, Dict, Any, Optional
from .chroma_client import ChromaClient
from .embeddings import EmbeddingService
# Try to import Redis cache service (new), fallback to old cache_service if not available
try:
    from backend.services.redis_cache import get_cache_service as get_redis_cache_service
    REDIS_CACHE_AVAILABLE = True
except ImportError:
    REDIS_CACHE_AVAILABLE = False
    get_redis_cache_service = None

# Fallback to old cache_service if Redis not available
try:
    from backend.services.cache_service import (
        get_cache_service as get_old_cache_service,
        CACHE_PREFIX_RAG,
        TTL_RAG_RETRIEVAL
    )
    OLD_CACHE_AVAILABLE = True
except ImportError:
    OLD_CACHE_AVAILABLE = False
    get_old_cache_service = None
    CACHE_PREFIX_RAG = "rag"
    TTL_RAG_RETRIEVAL = 3600

def get_cache_service():
    """Get cache service (prefer Redis, fallback to old cache)"""
    if REDIS_CACHE_AVAILABLE:
        cache_service = get_redis_cache_service()
        if cache_service:
            return cache_service
    if OLD_CACHE_AVAILABLE:
        return get_old_cache_service()
    return None
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
    
    def _calculate_adaptive_threshold(self, base_threshold: float) -> float:
        """
        Calculate adaptive similarity threshold based on database state.
        
        Strategy:
        - New/empty database (< 10 docs): Use very low threshold (0.01-0.05)
        - Small database (10-50 docs): Use low threshold (0.05-0.08)
        - Medium database (50-200 docs): Use normal threshold (0.08-0.1)
        - Mature database (> 200 docs): Use base threshold (0.1)
        
        Args:
            base_threshold: Base threshold from caller
            
        Returns:
            Adjusted threshold based on database state
        """
        try:
            stats = self.chroma_client.get_collection_stats()
            total_docs = stats.get("total_documents", 0)
            knowledge_docs = stats.get("knowledge_documents", 0)
            
            # Use knowledge_docs as primary indicator (conversations are less relevant for similarity)
            doc_count = knowledge_docs
            
            if doc_count == 0:
                # Empty database - use minimal threshold to allow any matches
                adaptive_threshold = 0.01
                logger.debug(f"📊 Database empty ({doc_count} docs) - using minimal threshold {adaptive_threshold}")
            elif doc_count < 10:
                # Very new database - use very low threshold
                adaptive_threshold = 0.02
                logger.debug(f"📊 Database very new ({doc_count} docs) - using low threshold {adaptive_threshold}")
            elif doc_count < 50:
                # Small database - use low threshold
                adaptive_threshold = 0.05
                logger.debug(f"📊 Database small ({doc_count} docs) - using low threshold {adaptive_threshold}")
            elif doc_count < 200:
                # Medium database - use slightly lower threshold
                adaptive_threshold = 0.08
                logger.debug(f"📊 Database medium ({doc_count} docs) - using threshold {adaptive_threshold}")
            else:
                # Mature database - use base threshold
                adaptive_threshold = base_threshold
                logger.debug(f"📊 Database mature ({doc_count} docs) - using base threshold {adaptive_threshold}")
            
            return adaptive_threshold
        except Exception as e:
            logger.warning(f"Failed to calculate adaptive threshold: {e}, using base threshold {base_threshold}")
            return base_threshold
    
    def retrieve_context(self, 
                        query: str, 
                        knowledge_limit: int = 3,  # Increased from 2 to 3 for better coverage
                        conversation_limit: int = 1,  # Optimized: reduced from 2 to 1 for latency
                        prioritize_foundational: bool = False,
                        tier_preference: Optional[str] = None,
                        similarity_threshold: float = 0.1,  # Reduced from 0.3 to 0.1 for better context retrieval
                        use_mmr: bool = True,  # Tier 3.5: Use MMR for diversity
                        mmr_lambda: float = 0.7,
                        exclude_content_types: Optional[List[str]] = None,
                        prioritize_style_guide: bool = False,
                        is_philosophical: bool = False,
                        # NPR Phase 2.1: Parallel RAG Retrieval
                        include_codebase: bool = False,  # Query stillme_codebase collection
                        include_git_history: bool = False,  # Query stillme_git_history collection
                        codebase_limit: int = 2,  # Number of code chunks to retrieve
                        git_history_limit: int = 2) -> Dict[str, Any]:  # Number of git history items to retrieve
        """Retrieve relevant context for a query
        
        Args:
            query: Query string
            knowledge_limit: Number of knowledge documents to retrieve
            conversation_limit: Number of conversation documents to retrieve
            prioritize_foundational: If True, prioritize foundational knowledge (tagged with 'foundational:stillme')
            tier_preference: Optional tier preference (L0, L1, L2, L3) for Nested Learning retrieval strategy
            similarity_threshold: Minimum similarity score (0.0-1.0) to include document. Default: 0.1
            use_mmr: If True, use Max Marginal Relevance for diversity. Default: True
            mmr_lambda: MMR lambda parameter (0.0-1.0). Higher = more relevance, lower = more diversity. Default: 0.7
            exclude_content_types: List of content_type values to exclude (e.g., ["technical"] for philosophical questions)
            prioritize_style_guide: If True, force retrieve style guide documents (domain="style_guide") for philosophical questions
            is_philosophical: If True, skip context if similarity is too low (better to answer from pretrained knowledge than feed low-quality context)
        
        Note:
            Phase 2: style_guide content_type is ALWAYS excluded by default to prevent prompt drift.
            Style guides are moved to docs/style/ and should NOT appear in user-facing context.
        """
        # Phase 2: Always exclude style_guide by default to prevent prompt drift
        if exclude_content_types is None:
            exclude_content_types = ["style_guide"]
        elif "style_guide" not in exclude_content_types:
            exclude_content_types = exclude_content_types + ["style_guide"]
        try:
            import os
            ENABLE_CONTINUUM_MEMORY = os.getenv("ENABLE_CONTINUUM_MEMORY", "false").lower() == "true"
            
            # Phase 2: RAG Retrieval Cache - Check cache first
            # CRITICAL: Disable cache for validator count questions to ensure fresh retrieval
            # This prevents using stale cached results with low similarity scores
            cache_service = get_cache_service()
            cache_enabled = os.getenv("ENABLE_RAG_CACHE", "true").lower() == "true"
            
            # CRITICAL: Disable cache if this is a validator count question
            # Validator count questions need fresh retrieval to get latest foundational knowledge
            is_validator_count_query = any(
                keyword in query.lower() for keyword in [
                    "bao nhiêu", "how many", "số", "number", "count",
                    "lớp validator", "validator layer", "validator count"
                ]
            )
            if is_validator_count_query:
                cache_enabled = False
                logger.info(f"🚫 Cache disabled for validator count question to ensure fresh retrieval")
            
            cached_result = None
            cache_hit = False
            cache_key = None
            
            if cache_enabled and cache_service:
                # Generate cache key from query + parameters
                # Use Redis cache service's method if available, otherwise use old method
                if REDIS_CACHE_AVAILABLE and hasattr(cache_service, '_generate_key'):
                    cache_key = cache_service._generate_key(
                        "rag_query",
                        query,
                        knowledge_limit
                    )
                    # Try to get from Redis cache
                    cached_result = cache_service.get_query_result(query, knowledge_limit)
                else:
                    # Use old cache service method
                    cache_key = cache_service._generate_key(
                        CACHE_PREFIX_RAG,
                        query,
                        knowledge_limit,
                        conversation_limit,
                        prioritize_foundational,
                        tier_preference,
                        similarity_threshold,
                        use_mmr,
                        mmr_lambda,
                        exclude_content_types,
                        prioritize_style_guide,
                        is_philosophical
                    )
                    cached_result = cache_service.get(cache_key)
                
                if cached_result:
                    cache_hit = True
                    # Handle both Redis cache format (dict) and old cache format
                    if isinstance(cached_result, dict):
                        logger.info(f"✅ RAG cache HIT (saved {cached_result.get('latency', 0):.2f}s)")
                        return cached_result.get("context") or cached_result
                    else:
                        logger.info(f"✅ RAG cache HIT")
                        return cached_result
            
            # If not in cache, perform retrieval
            # Generate query embedding (only once, used for both cache key and search)
            query_embedding = self.embedding_service.encode_text(query)
            
            # ADAPTIVE THRESHOLD: Adjust similarity threshold based on database state
            # This ensures new/empty databases can still retrieve documents
            original_threshold = similarity_threshold
            similarity_threshold = self._calculate_adaptive_threshold(similarity_threshold)
            if similarity_threshold != original_threshold:
                logger.debug(f"🔧 Adaptive threshold: {original_threshold:.3f} → {similarity_threshold:.3f} (based on database state)")
            
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
                    
                    # Fix 2: Force retrieve style guide for philosophical questions
                    if prioritize_style_guide:
                        try:
                            style_guide_results = self.chroma_client.search_knowledge(
                                query_embedding=query_embedding,
                                limit=1,  # Force retrieve at least 1 style guide document
                                where={"domain": "style_guide"}
                            )
                            if style_guide_results:
                                # Prioritize style guide by adding to front of results
                                existing_ids = {doc.get("id") for doc in knowledge_results}
                                for doc in style_guide_results:
                                    if doc.get("id") not in existing_ids:
                                        knowledge_results.insert(0, doc)  # Insert at front for priority
                                        logger.info(f"✅ Force retrieved style guide document: {doc.get('metadata', {}).get('title', 'N/A')}")
                            else:
                                # Try alternative search if domain filter doesn't work
                                logger.debug("Style guide not found with domain filter, trying alternative search")
                                alt_results = self.chroma_client.search_knowledge(
                                    query_embedding=query_embedding,
                                    limit=5
                                )
                                for doc in alt_results:
                                    doc_metadata = doc.get("metadata", {})
                                    if ("style_guide" in str(doc_metadata.get("domain", "")).lower() or
                                        "philosophical" in str(doc_metadata.get("title", "")).lower() or
                                        "StillMe_StyleGuide" in str(doc_metadata.get("title", ""))):
                                        if doc.get("id") not in {d.get("id") for d in knowledge_results}:
                                            knowledge_results.insert(0, doc)
                                            logger.info(f"✅ Found style guide via alternative search: {doc.get('metadata', {}).get('title', 'N/A')}")
                                            break
                        except Exception as style_guide_error:
                            logger.debug(f"Style guide retrieval failed: {style_guide_error}")
                    
                    # CRITICAL FIX: Check if this is a news/article query - if so, SKIP foundational retrieval
                    # This prevents CRITICAL_FOUNDATION from dominating results when user asks about external articles
                    is_news_article_query = False
                    try:
                        from backend.core.question_classifier import is_news_article_query as check_news_article
                        is_news_article_query = check_news_article(query)
                        if is_news_article_query:
                            logger.info(f"📰 News/article query detected - SKIPPING foundational knowledge retrieval to avoid hallucination")
                    except Exception:
                        pass  # Non-critical, continue if detection fails
                    
                    if prioritize_foundational and not is_news_article_query:
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
                                # Filter foundational results by exclude_content_types if specified
                                filtered_foundational = []
                                for doc in foundational_results:
                                    doc_metadata = doc.get("metadata", {})
                                    doc_content_type = doc_metadata.get("content_type", "")
                                    if exclude_content_types and doc_content_type:
                                        if doc_content_type in exclude_content_types:
                                            logger.debug(f"Excluding foundational document with content_type={doc_content_type}")
                                            continue
                                    filtered_foundational.append(doc)
                                
                                # CRITICAL: Prioritize foundational results by inserting at the beginning
                                # This ensures foundational knowledge is always first in results
                                knowledge_results = filtered_foundational + knowledge_results
                                logger.info(f"Found {len(filtered_foundational)} foundational knowledge documents (prioritized at front)")
                                
                                # CRITICAL: Re-rank results to boost documents with relevant keywords
                                # This helps when query is about validator count or StillMe architecture
                                query_lower = query.lower()
                                if any(keyword in query_lower for keyword in ["validator", "layer", "lớp", "19", "7", "bao nhiêu", "how many"]):
                                    # Re-rank: boost documents containing relevant keywords
                                    def calculate_relevance_score(doc):
                                        content = str(doc.get("document", "")).lower()
                                        metadata = doc.get("metadata", {})
                                        title = str(metadata.get("title", "")).lower()
                                        
                                        score = 0.0
                                        # Boost for foundational source
                                        if metadata.get("source") == "CRITICAL_FOUNDATION":
                                            score += 2.0
                                        # Boost for relevant keywords in content
                                        if "19 validators" in content or "19 validators total" in content:
                                            score += 1.5
                                        if "7 layers" in content or "7 lớp" in content:
                                            score += 1.5
                                        if "validator" in content and "layer" in content:
                                            score += 1.0
                                        if "validation framework" in content:
                                            score += 0.5
                                        # Boost for relevant keywords in title
                                        if "technical" in title or "architecture" in title:
                                            score += 0.5
                                        
                                        return score
                                    
                                    # Sort by relevance score (highest first)
                                    knowledge_results.sort(key=calculate_relevance_score, reverse=True)
                                    logger.info(f"✅ Re-ranked {len(knowledge_results)} results based on keyword relevance")
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
                                doc_content_type = doc_metadata.get("content_type", "")
                                
                                is_provenance = (
                                    doc_source == "PROVENANCE" or
                                    doc_type == "provenance" or
                                    "provenance" in str(doc_tags).lower() or
                                    "intent:origin" in str(doc_tags).lower() or
                                    "intent:founder" in str(doc_tags).lower()
                                )
                                
                                if is_provenance:
                                    continue
                                
                                # CRITICAL FIX: Exclude CRITICAL_FOUNDATION for news/article queries
                                # This prevents foundational docs from dominating when user asks about external articles
                                if is_news_article_query:
                                    is_critical_foundation = (
                                        doc_source == "CRITICAL_FOUNDATION" or
                                        doc_type == "foundational" or
                                        doc_metadata.get("foundational") == "stillme" or
                                        "CRITICAL_FOUNDATION" in str(doc_tags) or
                                        "foundational:stillme" in str(doc_tags)
                                    )
                                    if is_critical_foundation:
                                        logger.debug(f"Excluding CRITICAL_FOUNDATION document for news/article query: {doc_metadata.get('title', 'N/A')}")
                                        continue
                                
                                # Filter out excluded content types (e.g., "technical" for philosophical questions)
                                if exclude_content_types and doc_content_type:
                                    if doc_content_type in exclude_content_types:
                                        logger.debug(f"Excluding document with content_type={doc_content_type}")
                                        continue
                                
                                knowledge_results.append(doc)
                                if len(knowledge_results) >= knowledge_limit:
                                    break
                    
                    # CRITICAL FIX: Detect "latest/newest" queries and sort by timestamp
                    is_latest_query = False
                    try:
                        from backend.core.question_classifier import is_latest_query as check_latest
                        is_latest_query = check_latest(query)
                        if is_latest_query:
                            logger.info(f"🕐 Latest/newest query detected - will sort by timestamp descending")
                    except Exception:
                        pass  # Non-critical, continue if detection fails
                    
                    # CRITICAL FIX: Sort by timestamp for "latest/newest" queries
                    if is_latest_query and knowledge_results:
                        logger.info(f"🕐 Sorting {len(knowledge_results)} documents by timestamp (newest first)")
                        from datetime import datetime
                        
                        def get_timestamp_for_sorting(doc):
                            """Extract timestamp from document metadata for sorting"""
                            metadata = doc.get("metadata", {})
                            
                            # Try multiple timestamp fields
                            timestamp_fields = [
                                "added_to_kb",
                                "timestamp",
                                "created_at",
                                "date",
                                "published_date",
                                "learned_at"
                            ]
                            
                            for field in timestamp_fields:
                                timestamp_str = metadata.get(field, "")
                                if not timestamp_str:
                                    continue
                                
                                try:
                                    # Try various timestamp formats
                                    if "UTC" in str(timestamp_str):
                                        date_str = str(timestamp_str).split("UTC")[0].strip()
                                        parsed_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                                        return parsed_date
                                    elif "T" in str(timestamp_str):
                                        # ISO format: 2025-12-22T10:30:00Z or 2025-12-22T10:30:00+00:00
                                        date_str = str(timestamp_str).replace("Z", "").replace("+00:00", "").split("T")
                                        if len(date_str) == 2:
                                            parsed_date = datetime.strptime(f"{date_str[0]} {date_str[1]}", "%Y-%m-%d %H:%M:%S")
                                            return parsed_date
                                        else:
                                            parsed_date = datetime.strptime(date_str[0], "%Y-%m-%d")
                                            return parsed_date
                                    elif len(str(timestamp_str).split("-")) == 3:
                                        # Date format: 2025-12-22
                                        parsed_date = datetime.strptime(str(timestamp_str).split()[0], "%Y-%m-%d")
                                        return parsed_date
                                except Exception:
                                    continue  # Try next field
                            
                            # If no timestamp found, return very old date (will be sorted last)
                            return datetime(1970, 1, 1)
                        
                        # Sort by timestamp descending (newest first)
                        knowledge_results.sort(key=get_timestamp_for_sorting, reverse=True)
                        logger.info(f"✅ Sorted {len(knowledge_results)} documents by timestamp (newest first)")
                    
                    # CRITICAL FIX: Re-ranking for news/article queries - boost recent knowledge
                    # This ensures articles from RSS feeds, arXiv, etc. are prioritized over old foundational docs
                    if is_news_article_query and knowledge_results and not is_latest_query:
                        logger.info(f"📰 Re-ranking {len(knowledge_results)} documents for news/article query - boosting recent knowledge")
                        
                        def calculate_news_relevance_score(doc):
                            """Calculate relevance score for news/article queries"""
                            metadata = doc.get("metadata", {})
                            source = metadata.get("source", "")
                            doc_type = metadata.get("type", "")
                            tags = str(metadata.get("tags", ""))
                            
                            score = 0.0
                            
                            # Boost for news/article sources
                            if "rss" in source.lower() or "arxiv" in source.lower() or "hacker" in source.lower():
                                score += 2.0
                            if "news" in source.lower() or "article" in doc_type.lower():
                                score += 1.5
                            
                            # Boost for recent timestamps (if available)
                            added_to_kb = metadata.get("added_to_kb", "")
                            if added_to_kb:
                                try:
                                    # Try to parse timestamp
                                    from datetime import datetime
                                    # Common formats: "2025-12-22 10:30:00 UTC" or ISO format
                                    if "UTC" in added_to_kb:
                                        date_str = added_to_kb.split("UTC")[0].strip()
                                        parsed_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                                    elif "T" in added_to_kb:
                                        # ISO format: 2025-12-22T10:30:00Z
                                        date_str = added_to_kb.replace("Z", "").split("T")[0]
                                        parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
                                    else:
                                        parsed_date = None
                                    
                                    if parsed_date:
                                        # Boost if added within last 7 days
                                        days_ago = (datetime.now() - parsed_date).days
                                        if days_ago <= 7:
                                            score += 1.0
                                        elif days_ago <= 30:
                                            score += 0.5
                                except:
                                    pass  # Skip if timestamp parsing fails
                            
                            # Penalize foundational docs for news queries
                            is_critical_foundation = (
                                source == "CRITICAL_FOUNDATION" or
                                doc_type == "foundational" or
                                metadata.get("foundational") == "stillme" or
                                "CRITICAL_FOUNDATION" in tags or
                                "foundational:stillme" in tags
                            )
                            if is_critical_foundation:
                                score -= 3.0  # Heavy penalty
                            
                            # Use similarity/distance if available
                            distance = doc.get("distance", 1.0)
                            similarity = 1.0 - distance if distance <= 1.0 else 0.0
                            score += similarity * 0.5  # Add similarity as part of score
                            
                            return score
                        
                        # Sort by relevance score (highest first)
                        knowledge_results.sort(key=calculate_news_relevance_score, reverse=True)
                        logger.info(f"✅ Re-ranked {len(knowledge_results)} documents for news/article query")
                    
                    return knowledge_results
                
                # Helper function to run conversation search
                def _search_conversations():
                    if conversation_limit > 0:
                        return self.chroma_client.search_conversations(
                            query_embedding=query_embedding,
                            limit=conversation_limit
                        )
                    return []
                
                # NPR Phase 2.1: Helper functions for parallel codebase and git history retrieval
                def _search_codebase():
                    """Query stillme_codebase collection"""
                    if not include_codebase:
                        return []
                    try:
                        from backend.services.codebase_indexer import get_codebase_indexer
                        indexer = get_codebase_indexer()
                        results = indexer.query_codebase(query, n_results=codebase_limit)
                        # Format results to match knowledge_results structure
                        formatted = []
                        for result in results:
                            formatted.append({
                                "content": result.get("document", ""),
                                "metadata": result.get("metadata", {}),
                                "distance": result.get("distance", 1.0),
                                "source": "codebase",
                                "collection": "stillme_codebase"
                            })
                        return formatted
                    except Exception as e:
                        logger.warning(f"Codebase search failed: {e}")
                        return []
                
                def _search_git_history():
                    """Query stillme_git_history collection"""
                    if not include_git_history:
                        return []
                    try:
                        from backend.services.git_history_retriever import get_git_history_retriever
                        git_retriever = get_git_history_retriever()
                        results = git_retriever.query_history(query, n_results=git_history_limit)
                        # Format results to match knowledge_results structure
                        formatted = []
                        for result in results:
                            formatted.append({
                                "content": result.get("message", ""),
                                "metadata": result.get("metadata", {}),
                                "distance": result.get("distance", 1.0),
                                "source": "git_history",
                                "collection": "stillme_git_history"
                            })
                        return formatted
                    except Exception as e:
                        logger.warning(f"Git history search failed: {e}")
                        return []
                
                # NPR Phase 2.1: Run all searches in parallel using ThreadPoolExecutor
                # This works in both sync and async contexts without breaking backward compatibility
                import time
                parallel_start = time.time()
                
                # Determine which searches to run
                searches_to_run = []
                if True:  # Always run knowledge search
                    searches_to_run.append(("knowledge", _search_knowledge))
                if conversation_limit > 0:
                    searches_to_run.append(("conversation", _search_conversations))
                if include_codebase:
                    searches_to_run.append(("codebase", _search_codebase))
                if include_git_history:
                    searches_to_run.append(("git_history", _search_git_history))
                
                try:
                    if len(searches_to_run) > 1:
                        # Run all searches in parallel
                        logger.debug(f"🚀 [NPR] Running {len(searches_to_run)} RAG searches in parallel...")
                        with ThreadPoolExecutor(max_workers=min(len(searches_to_run), 4)) as executor:
                            futures = {
                                executor.submit(search_func): name
                                for name, search_func in searches_to_run
                            }
                            
                            # Collect results as they complete
                            results_dict = {}
                            for future in futures:
                                name = futures[future]
                                try:
                                    results_dict[name] = future.result()
                                except Exception as e:
                                    logger.error(f"Parallel search '{name}' failed: {e}")
                                    results_dict[name] = []
                        
                        # Extract results
                        knowledge_results = results_dict.get("knowledge", [])
                        conversation_results = results_dict.get("conversation", [])
                        codebase_results = results_dict.get("codebase", [])
                        git_history_results = results_dict.get("git_history", [])
                        
                        parallel_time = time.time() - parallel_start
                        logger.info(f"✅ [NPR] Parallel RAG retrieval completed in {parallel_time:.3f}s ({len(searches_to_run)} collections)")
                    else:
                        # Only one search needed (knowledge)
                        knowledge_results = _search_knowledge()
                        conversation_results = []
                        codebase_results = []
                        git_history_results = []
                        
                except Exception as parallel_error:
                    # Fallback to sequential if parallel fails
                    logger.warning(f"⚠️ [NPR] Parallel RAG retrieval failed, using sequential: {parallel_error}")
                    knowledge_results = _search_knowledge()
                    conversation_results = _search_conversations() if conversation_limit > 0 else []
                    codebase_results = _search_codebase() if include_codebase else []
                    git_history_results = _search_git_history() if include_git_history else []
                
                logger.info(f"Knowledge search returned {len(knowledge_results)} results")
                if conversation_results:
                    logger.info(f"Conversation search returned {len(conversation_results)} results")
                if codebase_results:
                    logger.info(f"Codebase search returned {len(codebase_results)} results")
                if git_history_results:
                    logger.info(f"Git history search returned {len(git_history_results)} results")
            
            # Tier 3.5: Apply similarity threshold and MMR
            def _distance_to_similarity(distance: float) -> float:
                """Convert ChromaDB distance (0=identical, 1=different) to similarity (0=different, 1=identical)"""
                # ChromaDB uses cosine distance: 0 = identical, 1 = completely different
                # Similarity = 1 - distance
                return max(0.0, min(1.0, 1.0 - distance))
            
            def _apply_mmr(documents: List[Dict[str, Any]], query_embedding: List[float], 
                          limit: int, lambda_param: float) -> List[Dict[str, Any]]:
                """Apply Max Marginal Relevance for diversity
                
                Args:
                    documents: List of documents with 'distance' field
                    query_embedding: Query embedding vector
                    limit: Number of documents to return
                    lambda_param: MMR lambda (0.0-1.0). Higher = more relevance, lower = more diversity
                
                Returns:
                    List of diverse documents
                """
                if len(documents) <= limit:
                    return documents
                
                # Convert distances to similarities
                for doc in documents:
                    doc["similarity"] = _distance_to_similarity(doc.get("distance", 1.0))
                
                # Start with highest similarity document
                selected = []
                remaining = documents.copy()
                
                # Sort by similarity descending
                remaining.sort(key=lambda x: x.get("similarity", 0.0), reverse=True)
                
                # Select first document (highest similarity)
                if remaining:
                    selected.append(remaining.pop(0))
                
                # Select remaining documents using MMR
                while len(selected) < limit and remaining:
                    best_score = -1.0
                    best_idx = -1
                    
                    for i, candidate in enumerate(remaining):
                        # Relevance score (similarity to query)
                        relevance = candidate.get("similarity", 0.0)
                        
                        # Diversity score (max similarity to already selected)
                        max_sim_to_selected = 0.0
                        for selected_doc in selected:
                            # Simple heuristic: if content is similar, assume high similarity
                            # For better diversity, we could compute actual embedding similarity
                            # But that would require additional compute, so we use a simple heuristic
                            selected_content = selected_doc.get("content", "")
                            candidate_content = candidate.get("content", "")
                            
                            # Simple overlap heuristic (can be improved with actual embedding similarity)
                            if selected_content and candidate_content:
                                # Count common words
                                selected_words = set(selected_content.lower().split()[:50])  # First 50 words
                                candidate_words = set(candidate_content.lower().split()[:50])
                                if selected_words and candidate_words:
                                    overlap = len(selected_words & candidate_words) / len(selected_words | candidate_words)
                                    max_sim_to_selected = max(max_sim_to_selected, overlap)
                        
                        # MMR score: λ * relevance - (1-λ) * max_similarity_to_selected
                        mmr_score = lambda_param * relevance - (1.0 - lambda_param) * max_sim_to_selected
                        
                        if mmr_score > best_score:
                            best_score = mmr_score
                            best_idx = i
                    
                    if best_idx >= 0:
                        selected.append(remaining.pop(best_idx))
                    else:
                        break
                
                return selected
            
            # Apply similarity threshold filtering
            original_knowledge_count = len(knowledge_results)
            original_conversation_count = len(conversation_results)
            original_codebase_count = len(codebase_results) if include_codebase else 0
            original_git_history_count = len(git_history_results) if include_git_history else 0
            
            # Filter knowledge results by similarity threshold
            filtered_knowledge = []
            filtered_knowledge_count = 0
            distance_values = []  # Track distance values for debugging
            for doc in knowledge_results:
                distance = doc.get("distance", 1.0)
                distance_values.append(distance)
                similarity = _distance_to_similarity(distance)
                if similarity >= similarity_threshold:
                    doc["similarity"] = similarity  # Add similarity for metrics
                    filtered_knowledge.append(doc)
                else:
                    filtered_knowledge_count += 1
            
            # PROGRESSIVE FALLBACK: If no documents pass threshold, try with lower threshold
            if not filtered_knowledge and knowledge_results:
                logger.warning(f"⚠️ No documents passed threshold {similarity_threshold:.3f}, trying progressive fallback...")
                # Try with progressively lower thresholds
                fallback_thresholds = [0.05, 0.02, 0.01, 0.0]  # Progressive fallback
                for fallback_threshold in fallback_thresholds:
                    if fallback_threshold >= similarity_threshold:
                        continue  # Skip if not lower
                    for doc in knowledge_results:
                        if doc not in filtered_knowledge:
                            distance = doc.get("distance", 1.0)
                            similarity = _distance_to_similarity(distance)
                            if similarity >= fallback_threshold:
                                doc["similarity"] = similarity
                                filtered_knowledge.append(doc)
                                logger.debug(f"✅ Progressive fallback: Added document with similarity {similarity:.3f} (threshold: {fallback_threshold:.3f})")
                    if filtered_knowledge:
                        logger.debug(f"✅ Progressive fallback succeeded: {len(filtered_knowledge)} documents with threshold {fallback_threshold:.3f}")
                        break  # Stop if we found documents
            
            # EMERGENCY: Detect embedding model mismatch
            # If average distance is extremely high (>= 0.95) AND we have documents in database,
            # this strongly indicates embedding model mismatch
            embedding_mismatch_detected = False
            if distance_values:
                avg_distance = sum(distance_values) / len(distance_values)
                min_distance = min(distance_values)
                max_distance = max(distance_values)
                
                # Check database stats to determine if mismatch is likely
                try:
                    stats = self.chroma_client.get_collection_stats()
                    knowledge_docs = stats.get("knowledge_documents", 0)
                    
                    # If we have documents but all have very high distance, it's likely a mismatch
                    if avg_distance >= 0.95 and knowledge_docs > 0 and not filtered_knowledge:
                        embedding_mismatch_detected = True
                        logger.error(f"🚨 CRITICAL: Embedding model mismatch detected!")
                        logger.error(f"   - Average distance: {avg_distance:.3f} (extremely high)")
                        logger.error(f"   - Distance range: [{min_distance:.3f}, {max_distance:.3f}]")
                        logger.error(f"   - Database has {knowledge_docs} knowledge documents but none match")
                        logger.error(f"   - This indicates embeddings were created with a different model")
                        logger.error(f"   - Current model: {self.embedding_service.model_name}")
                        logger.error(f"   - ACTION REQUIRED: Re-embed all documents with current model")
                        
                        # EMERGENCY MODE: Use minimal threshold to allow any matches
                        logger.warning(f"🔧 EMERGENCY MODE: Lowering threshold to 0.01 to allow matches")
                        emergency_threshold = 0.01
                        for doc in knowledge_results:
                            if doc not in filtered_knowledge:
                                distance = doc.get("distance", 1.0)
                                similarity = _distance_to_similarity(distance)
                                if similarity >= emergency_threshold:
                                    doc["similarity"] = similarity
                                    filtered_knowledge.append(doc)
                                    logger.debug(f"✅ Emergency mode: Added document with similarity {similarity:.3f}")
                        
                        if filtered_knowledge:
                            logger.info(f"✅ Emergency mode succeeded: {len(filtered_knowledge)} documents with threshold {emergency_threshold}")
                        else:
                            logger.error(f"❌ Emergency mode failed: No documents match even with threshold {emergency_threshold}")
                            logger.error(f"❌ Database requires complete re-embedding with model: {self.embedding_service.model_name}")
                    elif avg_distance >= 0.95:
                        logger.warning(f"⚠️ High average distance ({avg_distance:.3f}) detected - all documents may be irrelevant. "
                                     f"Distance range: [{min_distance:.3f}, {max_distance:.3f}]. "
                                     f"This may indicate: (1) Database is new/empty, (2) Embedding model mismatch, or (3) Query is unrelated to stored content.")
                except Exception as stats_error:
                    logger.warning(f"Could not check database stats for mismatch detection: {stats_error}")
            
            # Filter conversation results by similarity threshold
            filtered_conversation = []
            filtered_conversation_count = 0
            for doc in conversation_results:
                similarity = _distance_to_similarity(doc.get("distance", 1.0))
                if similarity >= similarity_threshold:
                    doc["similarity"] = similarity
                    filtered_conversation.append(doc)
                else:
                    filtered_conversation_count += 1
            
            # NPR Phase 2.1: Filter codebase and git_history results by similarity threshold
            filtered_codebase = []
            filtered_codebase_count = 0
            for doc in codebase_results:
                similarity = _distance_to_similarity(doc.get("distance", 1.0))
                if similarity >= similarity_threshold:
                    doc["similarity"] = similarity
                    filtered_codebase.append(doc)
                else:
                    filtered_codebase_count += 1
            
            filtered_git_history = []
            filtered_git_history_count = 0
            for doc in git_history_results:
                similarity = _distance_to_similarity(doc.get("distance", 1.0))
                if similarity >= similarity_threshold:
                    doc["similarity"] = similarity
                    filtered_git_history.append(doc)
                else:
                    filtered_git_history_count += 1
            
            if filtered_knowledge_count > 0:
                logger.debug(f"📊 Filtered {filtered_knowledge_count} knowledge docs below similarity threshold {similarity_threshold}")
            if filtered_conversation_count > 0:
                logger.debug(f"📊 Filtered {filtered_conversation_count} conversation docs below similarity threshold {similarity_threshold}")
            if filtered_codebase_count > 0:
                logger.debug(f"📊 Filtered {filtered_codebase_count} codebase docs below similarity threshold {similarity_threshold}")
            if filtered_git_history_count > 0:
                logger.debug(f"📊 Filtered {filtered_git_history_count} git_history docs below similarity threshold {similarity_threshold}")
            
            # Apply MMR if enabled and we have enough documents
            if use_mmr and len(filtered_knowledge) > knowledge_limit:
                # Get more candidates for MMR (2x limit to have diversity to choose from)
                mmr_candidates = filtered_knowledge[:knowledge_limit * 2] if len(filtered_knowledge) > knowledge_limit * 2 else filtered_knowledge
                filtered_knowledge = _apply_mmr(mmr_candidates, query_embedding, knowledge_limit, mmr_lambda)
                logger.info(f"🎯 Applied MMR (λ={mmr_lambda}): Selected {len(filtered_knowledge)} diverse documents from {len(mmr_candidates)} candidates")
            
            # Calculate average similarity for metrics
            avg_similarity = 0.0
            if filtered_knowledge:
                avg_similarity = sum(doc.get("similarity", 0.0) for doc in filtered_knowledge) / len(filtered_knowledge)
                logger.debug(f"📊 RAG retrieval: {len(filtered_knowledge)} docs, avg_similarity={avg_similarity:.3f}, threshold={similarity_threshold}")
            elif knowledge_results:
                # If we have results but all were filtered out, log warning
                logger.warning(f"⚠️ All {len(knowledge_results)} retrieved documents were filtered out (similarity < {similarity_threshold}). "
                             f"This may indicate: (1) Database is new/empty, (2) Embedding model mismatch, or (3) Query is unrelated to stored content.")
            
            # Fix 4: For philosophical questions, skip context if similarity is too low
            # Better to answer from pretrained knowledge than feed low-quality context that distracts the model
            PHILO_MIN_SCORE = 0.4  # Minimum similarity threshold for philosophical questions
            if is_philosophical and filtered_knowledge and avg_similarity < PHILO_MIN_SCORE:
                logger.info(f"⚠️ Philosophical question with low RAG similarity ({avg_similarity:.3f} < {PHILO_MIN_SCORE}). Skipping context - model will answer from pretrained knowledge.")
                # Return empty context - model can answer from pretrained knowledge
                return {
                    "knowledge_docs": [],
                    "conversation_docs": [],
                    "codebase_docs": [],
                    "git_history_docs": [],
                    "total_context_docs": 0,
                    "avg_similarity_score": avg_similarity,
                    "context_quality": "low",
                    "has_reliable_context": False,
                    "filtered_docs_count": 0,
                    "original_knowledge_count": len(knowledge_results) if 'knowledge_results' in locals() else 0,
                    "original_conversation_count": len(conversation_results) if 'conversation_results' in locals() else 0
                }
            
            # Determine context quality
            if avg_similarity >= 0.6:
                context_quality = "high"
            elif avg_similarity >= 0.4:
                context_quality = "medium"
            else:
                context_quality = "low"
            
            # Check if we have reliable context
            has_reliable_context = len(filtered_knowledge) > 0 and avg_similarity >= similarity_threshold
            
            # NPR Phase 2.1: Merge codebase and git_history into knowledge_docs for backward compatibility
            # Or keep them separate for transparency
            all_knowledge_docs = filtered_knowledge[:knowledge_limit].copy()
            if include_codebase:
                # Add codebase results with source tag
                for doc in filtered_codebase[:codebase_limit]:
                    doc["source"] = "codebase"
                    all_knowledge_docs.append(doc)
            if include_git_history:
                # Add git history results with source tag
                for doc in filtered_git_history[:git_history_limit]:
                    doc["source"] = "git_history"
                    all_knowledge_docs.append(doc)
            
            # Build context result with metrics
            context_result = {
                "knowledge_docs": all_knowledge_docs,  # Includes codebase and git_history if enabled
                "conversation_docs": filtered_conversation[:conversation_limit] if conversation_limit > 0 else [],
                # NPR Phase 2.1: Separate fields for codebase and git_history (for transparency)
                "codebase_docs": filtered_codebase[:codebase_limit] if include_codebase else [],
                "git_history_docs": filtered_git_history[:git_history_limit] if include_git_history else [],
                "total_context_docs": len(all_knowledge_docs) + len(filtered_conversation[:conversation_limit] if conversation_limit > 0 else []),
                # Tier 3.5: Context quality metrics
                "avg_similarity_score": avg_similarity,
                "context_quality": context_quality,
                "has_reliable_context": has_reliable_context,
                "filtered_docs_count": filtered_knowledge_count + filtered_conversation_count + filtered_codebase_count + filtered_git_history_count,
                "original_knowledge_count": original_knowledge_count,
                "original_conversation_count": original_conversation_count,
                # NPR Phase 2.1: Track codebase and git_history counts
                "original_codebase_count": original_codebase_count,
                "original_git_history_count": original_git_history_count
            }
            
            if not has_reliable_context:
                logger.warning(f"⚠️ No reliable context found (avg_similarity={avg_similarity:.3f} < threshold={similarity_threshold})")
            
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
                
                # P1.3: Separate foundational knowledge from regular knowledge
                foundational_docs = []
                regular_docs = []
                
                for doc in context["knowledge_docs"]:
                    metadata = doc.get("metadata", {})
                    source = metadata.get("source", "")
                    foundational = metadata.get("foundational", "")
                    doc_type = metadata.get("type", "")
                    tags = str(metadata.get("tags", ""))
                    
                    # Check if this is foundational knowledge
                    is_foundational = (
                        source == "CRITICAL_FOUNDATION" or
                        foundational == "stillme" or
                        doc_type == "foundational" or
                        "CRITICAL_FOUNDATION" in tags or
                        "foundational:stillme" in tags
                    )
                    
                    if is_foundational:
                        foundational_docs.append(doc)
                    else:
                        regular_docs.append(doc)
                
                # P1.3: Add foundational knowledge with marker FIRST (priority)
                if foundational_docs:
                    foundational_header = "\n### [FOUNDATIONAL KNOWLEDGE - CRITICAL INSTRUCTION]"
                    foundational_header_tokens = self._estimate_tokens(foundational_header)
                    remaining_tokens -= foundational_header_tokens
                    context_parts.append(foundational_header)
                    
                    for i, doc in enumerate(foundational_docs, 1):
                        if remaining_tokens <= 100:
                            logger.warning(f"Stopped adding foundational docs at {i}/{len(foundational_docs)} due to token limit")
                            break
                        
                        source = doc.get("metadata", {}).get("source", "Unknown")
                        content = doc.get("content", "")
                        
                        doc_max_tokens = remaining_tokens // max(1, len(foundational_docs) - i + 1)
                        doc_max_tokens = min(doc_max_tokens, 2000)
                        
                        truncated_content = self._truncate_text_by_tokens(content, doc_max_tokens)
                        doc_text = f"{i}. [FOUNDATIONAL] {truncated_content} (Source: {source})"
                        
                        doc_tokens = self._estimate_tokens(doc_text)
                        remaining_tokens -= doc_tokens
                        context_parts.append(doc_text)
                
                # Add regular knowledge
                if regular_docs:
                    if foundational_docs:
                        regular_header = "\n### Regular Knowledge:"
                    else:
                        regular_header = ""
                    
                    for i, doc in enumerate(regular_docs, 1):
                        if remaining_tokens <= 100:
                            logger.warning(f"Stopped adding regular docs at {i}/{len(regular_docs)} due to token limit")
                            break
                        
                        source = doc.get("metadata", {}).get("source", "Unknown")
                        content = doc.get("content", "")
                        
                        doc_max_tokens = remaining_tokens // max(1, len(regular_docs) - i + 1)
                        doc_max_tokens = min(doc_max_tokens, 2000)
                        
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
            
            # P1.3: Verify foundational knowledge markers are present (if foundational docs exist)
            has_foundational_docs = any(
                doc.get("metadata", {}).get("source") == "CRITICAL_FOUNDATION" or
                doc.get("metadata", {}).get("foundational") == "stillme" or
                doc.get("metadata", {}).get("type") == "foundational" or
                "CRITICAL_FOUNDATION" in str(doc.get("metadata", {}).get("tags", ""))
                for doc in (context.get("knowledge_docs", []))
            ) if context else False
            
            if has_foundational_docs:
                has_foundational_markers = (
                    "[FOUNDATIONAL KNOWLEDGE" in result or 
                    "[FOUNDATIONAL]" in result or
                    "CRITICAL_FOUNDATION" in result
                )
                if has_foundational_markers:
                    logger.info("✅ Final context_text contains foundational knowledge markers")
                else:
                    logger.warning("⚠️ Final context_text does NOT contain foundational knowledge markers - may not be formatted correctly (foundational docs present but markers missing)")
            else:
                logger.debug("ℹ️ Final context_text does NOT contain foundational knowledge markers (no foundational docs in context)")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to build prompt context: {e}")
            return "Error building context."
    
    def check_semantic_duplicate(self, content: str, similarity_threshold: float = 0.95) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check for semantic duplicates using embedding similarity (Phase 3.1)
        
        Args:
            content: Content text to check for duplicates
            similarity_threshold: Similarity threshold (0.0-1.0, default 0.95 for very similar)
            
        Returns:
            Tuple of (is_duplicate: bool, most_similar_doc: Optional[Dict])
        """
        if not content or len(content.strip()) < 10:
            return False, None
        
        try:
            # Generate embedding for content
            # Use batch_encode for single item (returns list of embeddings)
            content_embeddings = self.embedding_service.batch_encode([content])
            content_embedding = content_embeddings[0] if content_embeddings else None
            
            if content_embedding is None:
                return False, None
            
            # Search for similar content in knowledge collection
            # Use high limit to find most similar, then filter by threshold
            similar_docs = self.chroma_client.search_knowledge(
                query_embedding=content_embedding,
                limit=5  # Check top 5 most similar
            )
            
            if not similar_docs:
                return False, None
            
            # Check if any document exceeds similarity threshold
            for doc in similar_docs:
                distance = doc.get("distance", 1.0)
                # Convert distance to similarity (cosine distance: 0 = identical, 1 = completely different)
                # For cosine similarity: similarity = 1 - distance
                similarity = 1.0 - distance
                
                if similarity >= similarity_threshold:
                    logger.debug(f"Semantic duplicate detected: similarity={similarity:.3f} >= {similarity_threshold:.3f}")
                    return True, doc
            
            return False, None
        except Exception as e:
            logger.warning(f"Semantic duplicate check failed: {e}")
            return False, None  # Fail open - allow content if check fails
    
    def add_learning_content(self, 
                           content: str, 
                           source: str, 
                           content_type: str = "knowledge",
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Add new learning content to vector database
        
        This method:
        1. Generates embeddings using the embedding service
        2. Inserts documents into ChromaDB
        3. Logs progress for monitoring
        """
        try:
            import uuid
            from datetime import datetime
            import time
            
            start_time = time.time()
            
            # Prepare metadata
            doc_metadata = {
                "source": source,
                "type": content_type,
                "timestamp": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            doc_id = f"{content_type}_{uuid.uuid4().hex[:8]}"
            
            # Generate embedding (ChromaDB will do this automatically, but we log it for visibility)
            # Note: ChromaDB's add() method automatically generates embeddings if not provided
            # We log this step for transparency
            logger.debug(f"🔧 Generating embedding for {content_type} content (ID: {doc_id[:8]}...)")
            embedding_start = time.time()
            
            # Add to appropriate collection (ChromaDB handles embedding generation internally)
            # Knowledge collection: knowledge, style_guide, technical, philosophical (all non-conversation content)
            # Conversation collection: conversation, chat history
            if content_type == "conversation":
                success = self.chroma_client.add_conversation(
                    documents=[content],
                    metadatas=[doc_metadata],
                    ids=[doc_id]
                )
            else:
                # All other content types (knowledge, style_guide, technical, philosophical) go to knowledge collection
                success = self.chroma_client.add_knowledge(
                    documents=[content],
                    metadatas=[doc_metadata],
                    ids=[doc_id]
                )
            
            embedding_time = time.time() - embedding_start
            total_time = time.time() - start_time
            
            if success:
                logger.debug(
                    f"✅ Added {content_type} content from {source} "
                    f"(embedding: {embedding_time:.3f}s, total: {total_time:.3f}s)"
                )
            else:
                logger.warning(f"❌ Failed to add {content_type} content from {source}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to add learning content: {e}", exc_info=True)
            return False
