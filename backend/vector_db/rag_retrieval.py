"""
RAG (Retrieval-Augmented Generation) Service for StillMe
Combines vector search with knowledge retrieval
"""

from typing import List, Dict, Any, Optional
from .chroma_client import ChromaClient
from .embeddings import EmbeddingService
import logging

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
                        knowledge_limit: int = 2,  # Optimized: reduced from 3 to 2 for latency
                        conversation_limit: int = 1,  # Optimized: reduced from 2 to 1 for latency
                        prioritize_foundational: bool = False) -> Dict[str, Any]:
        """Retrieve relevant context for a query
        
        Args:
            query: Query string
            knowledge_limit: Number of knowledge documents to retrieve
            conversation_limit: Number of conversation documents to retrieve
            prioritize_foundational: If True, prioritize foundational knowledge (tagged with 'foundational:stillme')
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.encode_text(query)
            logger.info(f"Query embedding generated: {len(query_embedding)} dimensions")
            
            # If prioritizing foundational knowledge, try to retrieve with metadata filter first
            knowledge_results = []
            if prioritize_foundational:
                try:
                    # Try to retrieve foundational knowledge first (tagged with CRITICAL_FOUNDATION or foundational:stillme)
                    # Priority: CRITICAL_FOUNDATION > foundational:stillme > foundational
                    try:
                        # First try CRITICAL_FOUNDATION (highest priority)
                        critical_results = self.chroma_client.search_knowledge(
                            query_embedding=query_embedding,
                            limit=knowledge_limit,
                            where={"source": "CRITICAL_FOUNDATION"}
                        )
                        if critical_results:
                            foundational_results = critical_results
                            logger.info(f"Found {len(critical_results)} CRITICAL_FOUNDATION documents")
                        else:
                            # Fallback to other foundational tags
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
                        # If metadata filter fails, try without filter (ChromaDB version compatibility)
                        logger.debug(f"Metadata filter not supported, trying without filter: {filter_error}")
                        foundational_results = []
                    if foundational_results:
                        knowledge_results.extend(foundational_results)
                        logger.info(f"Found {len(foundational_results)} foundational knowledge documents")
                except Exception as foundational_error:
                    # If metadata filter fails, continue with normal search
                    logger.debug(f"Foundational knowledge filter not available: {foundational_error}")
            
            # If we don't have enough results, do normal search
            if len(knowledge_results) < knowledge_limit:
                normal_results = self.chroma_client.search_knowledge(
                    query_embedding=query_embedding,
                    limit=knowledge_limit
                )
                # Merge results, avoiding duplicates
                existing_ids = {doc.get("id") for doc in knowledge_results}
                for doc in normal_results:
                    if doc.get("id") not in existing_ids:
                        knowledge_results.append(doc)
                        if len(knowledge_results) >= knowledge_limit:
                            break
            
            logger.info(f"Knowledge search returned {len(knowledge_results)} results")
            
            # Retrieve conversation documents (only if conversation_limit > 0)
            conversation_results = []
            if conversation_limit > 0:
                conversation_results = self.chroma_client.search_conversations(
                    query_embedding=query_embedding,
                    limit=conversation_limit
                )
                logger.info(f"Conversation search returned {len(conversation_results)} results")
            else:
                logger.debug(f"Skipping conversation search (conversation_limit={conversation_limit})")
            
            return {
                "knowledge_docs": knowledge_results[:knowledge_limit],
                "conversation_docs": conversation_results,
                "total_context_docs": len(knowledge_results[:knowledge_limit]) + len(conversation_results)
            }
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
    
    def build_prompt_context(self, context: Dict[str, Any]) -> str:
        """Build formatted context for LLM prompt"""
        try:
            context_parts = []
            
            # Add knowledge context
            if context["knowledge_docs"]:
                context_parts.append("## Relevant Knowledge:")
                for i, doc in enumerate(context["knowledge_docs"], 1):
                    source = doc.get("metadata", {}).get("source", "Unknown")
                    context_parts.append(f"{i}. {doc['content']} (Source: {source})")
            
            # Add conversation context
            if context["conversation_docs"]:
                context_parts.append("\n## Recent Conversations:")
                for i, doc in enumerate(context["conversation_docs"], 1):
                    timestamp = doc.get("metadata", {}).get("timestamp", "Unknown")
                    context_parts.append(f"{i}. {doc['content']} (Time: {timestamp})")
            
            return "\n".join(context_parts) if context_parts else "No relevant context found."
            
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
