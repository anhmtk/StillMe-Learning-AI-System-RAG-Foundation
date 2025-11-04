"""
ChromaDB Client for StillMe Vector Database
Handles vector storage and retrieval operations
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ChromaClient:
    """ChromaDB client for StillMe vector operations"""
    
    def __init__(self, persist_directory: str = "data/vector_db", reset_on_error: bool = False):
        """Initialize ChromaDB client
        
        Args:
            persist_directory: Directory to persist vector database
            reset_on_error: If True, reset database on schema errors
        """
        self.persist_directory = persist_directory
        self.reset_on_error = reset_on_error
        
        try:
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Create or get collections
            self.knowledge_collection = self._get_or_create_collection(
                "stillme_knowledge",
                "Knowledge base for StillMe learning"
            )
            
            self.conversation_collection = self._get_or_create_collection(
                "stillme_conversations", 
                "Conversation history for context"
            )
            
            logger.info("ChromaDB client initialized successfully")
            
        except Exception as e:
            error_msg = str(e).lower()
            # Check for schema mismatch errors
            if "no such column" in error_msg or "schema" in error_msg or "topic" in error_msg:
                logger.warning(f"ChromaDB schema mismatch detected: {e}")
                if self.reset_on_error:
                    logger.info("Attempting to reset ChromaDB database...")
                    try:
                        # Reset client
                        self.client = chromadb.PersistentClient(
                            path=persist_directory,
                            settings=Settings(
                                anonymized_telemetry=False,
                                allow_reset=True
                            )
                        )
                        # Delete and recreate collections
                        try:
                            self.client.delete_collection("stillme_knowledge")
                        except:
                            pass
                        try:
                            self.client.delete_collection("stillme_conversations")
                        except:
                            pass
                        
                        # Recreate collections
                        self.knowledge_collection = self.client.create_collection(
                            name="stillme_knowledge",
                            metadata={"description": "Knowledge base for StillMe learning"}
                        )
                        self.conversation_collection = self.client.create_collection(
                            name="stillme_conversations",
                            metadata={"description": "Conversation history for context"}
                        )
                        logger.info("✅ ChromaDB database reset successfully")
                    except Exception as reset_error:
                        logger.error(f"Failed to reset ChromaDB: {reset_error}")
                        raise
                else:
                    raise RuntimeError(
                        f"ChromaDB schema mismatch: {e}. "
                        "This usually happens when ChromaDB version changed. "
                        "You may need to delete the data/vector_db directory and restart."
                    ) from e
            else:
                raise
    
    def _get_or_create_collection(self, name: str, description: str):
        """Get existing collection or create new one"""
        try:
            return self.client.get_collection(name=name)
        except Exception:
            # Collection doesn't exist, create it
            return self.client.create_collection(
                name=name,
                metadata={"description": description}
            )
    
    def add_knowledge(self, 
                     documents: List[str], 
                     metadatas: List[Dict[str, Any]], 
                     ids: List[str]) -> bool:
        """Add knowledge documents to vector database
        
        Args:
            documents: List of text documents
            metadatas: List of metadata for each document
            ids: List of unique IDs for each document
            
        Returns:
            bool: Success status
        """
        try:
            self.knowledge_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} knowledge documents")
            return True
        except Exception as e:
            logger.error(f"Failed to add knowledge: {e}")
            return False
    
    def add_conversation(self, 
                        documents: List[str], 
                        metadatas: List[Dict[str, Any]], 
                        ids: List[str]) -> bool:
        """Add conversation context to vector database
        
        Args:
            documents: List of conversation texts
            metadatas: List of metadata for each conversation
            ids: List of unique IDs for each conversation
            
        Returns:
            bool: Success status
        """
        try:
            self.conversation_collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} conversation documents")
            return True
        except Exception as e:
            logger.error(f"Failed to add conversation: {e}")
            return False
    
    def search_knowledge(self, 
                        query_embedding: List[float], 
                        limit: int = 5,
                        where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search knowledge base using embedding
        
        Args:
            query_embedding: Query embedding vector
            limit: Number of results to return
            where: Optional metadata filter
            
        Returns:
            List of search results
        """
        try:
            results = self.knowledge_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where
            )
            
            # Convert to list of dictionaries
            search_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    search_results.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {},
                        "distance": results["distances"][0][i] if results["distances"] and results["distances"][0] else 0.0,
                        "id": results["ids"][0][i] if results["ids"] and results["ids"][0] else f"doc_{i}"
                    })
            
            return search_results
        except Exception as e:
            logger.error(f"Failed to search knowledge: {e}")
            return []
    
    def search_conversations(self, 
                           query_embedding: List[float], 
                           limit: int = 3,
                           where: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Search conversation history using embedding
        
        Args:
            query_embedding: Query embedding vector
            limit: Number of results to return
            where: Optional metadata filter
            
        Returns:
            List of search results
        """
        try:
            results = self.conversation_collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where
            )
            
            # Convert to list of dictionaries
            search_results = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    search_results.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] else {},
                        "distance": results["distances"][0][i] if results["distances"] and results["distances"][0] else 0.0,
                        "id": results["ids"][0][i] if results["ids"] and results["ids"][0] else f"conv_{i}"
                    })
            
            return search_results
        except Exception as e:
            logger.error(f"Failed to search conversations: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about collections
        
        Returns:
            Dict with collection counts
        """
        try:
            knowledge_count = self.knowledge_collection.count()
            conversation_count = self.conversation_collection.count()
            
            return {
                "knowledge_documents": knowledge_count,
                "conversation_documents": conversation_count,
                "total_documents": knowledge_count + conversation_count
            }
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"knowledge_documents": 0, "conversation_documents": 0, "total_documents": 0}
