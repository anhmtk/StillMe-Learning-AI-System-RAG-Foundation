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
        import os
        import shutil
        
        self.persist_directory = persist_directory
        self.reset_on_error = reset_on_error
        
        # Check if database exists and needs reset
        if reset_on_error:
            # Delete directory completely
            if os.path.exists(persist_directory):
                logger.info(f"Resetting ChromaDB: deleting {persist_directory} directory...")
                try:
                    # Force delete all files and subdirectories
                    for root, dirs, files in os.walk(persist_directory, topdown=False):
                        for f in files:
                            try:
                                file_path = os.path.join(root, f)
                                os.chmod(file_path, 0o777)  # Make writable
                                os.remove(file_path)
                            except Exception as file_error:
                                logger.warning(f"Could not delete file {f}: {file_error}")
                        for d in dirs:
                            try:
                                dir_path = os.path.join(root, d)
                                os.chmod(dir_path, 0o777)
                                shutil.rmtree(dir_path)
                            except Exception as dir_error:
                                logger.warning(f"Could not delete dir {d}: {dir_error}")
                    # Now remove the directory itself
                    try:
                        os.chmod(persist_directory, 0o777)
                        shutil.rmtree(persist_directory)
                        logger.info(f"✅ Deleted {persist_directory}")
                    except Exception as final_error:
                        logger.error(f"Final deletion failed: {final_error}")
                        raise
                except Exception as dir_error:
                    logger.error(f"Could not delete directory: {dir_error}")
                    raise RuntimeError(f"Failed to delete vector_db directory: {dir_error}. Please manually delete data/vector_db on Railway.")
            
            # Wait a moment to ensure filesystem sync
            import time
            time.sleep(0.5)
            
            # Create fresh directory
            os.makedirs(persist_directory, exist_ok=True)
            logger.info(f"✅ Created fresh directory: {persist_directory}")
        
        try:
            # Create client - if reset_on_error was True, directory is fresh
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # If reset_on_error was True, we deleted the directory, so create new collections directly
            # Otherwise, try to get existing collections or create new ones
            if reset_on_error:
                # Fresh start - create new collections directly (don't try to delete first)
                logger.info("Creating new collections after reset...")
                # Don't try to delete collections - database is fresh, they don't exist
                try:
                    self.knowledge_collection = self.client.create_collection(
                        name="stillme_knowledge",
                        metadata={"description": "Knowledge base for StillMe learning"}
                    )
                    logger.info("✅ Created stillme_knowledge collection")
                except Exception as create_error:
                    # If collection already exists somehow, delete and recreate
                    error_str = str(create_error).lower()
                    if "already exists" in error_str or "duplicate" in error_str:
                        logger.warning(f"Collection exists, deleting first: {create_error}")
                        try:
                            self.client.delete_collection("stillme_knowledge")
                        except Exception:
                            pass
                        self.knowledge_collection = self.client.create_collection(
                            name="stillme_knowledge",
                            metadata={"description": "Knowledge base for StillMe learning"}
                        )
                    else:
                        raise
                
                try:
                    self.conversation_collection = self.client.create_collection(
                        name="stillme_conversations",
                        metadata={"description": "Conversation history for context"}
                    )
                    logger.info("✅ Created stillme_conversations collection")
                except Exception as create_error:
                    # If collection already exists somehow, delete and recreate
                    error_str = str(create_error).lower()
                    if "already exists" in error_str or "duplicate" in error_str:
                        logger.warning(f"Collection exists, deleting first: {create_error}")
                        try:
                            self.client.delete_collection("stillme_conversations")
                        except Exception:
                            pass
                        self.conversation_collection = self.client.create_collection(
                            name="stillme_conversations",
                            metadata={"description": "Conversation history for context"}
                        )
                    else:
                        raise
                
                logger.info("✅ Created new collections after reset")
                logger.info("✅ ChromaDB database fully reset and reinitialized")
            else:
                # Normal initialization - try to get existing or create new
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
                logger.warning(f"⚠️ ChromaDB schema mismatch detected: {e}")
                logger.warning("This usually happens when ChromaDB version changed or database was created with older version")
                
                if self.reset_on_error:
                    logger.info("🔄 Attempting to reset ChromaDB database by deleting directory...")
                    try:
                        # Close existing client if it exists
                        if hasattr(self, 'client'):
                            try:
refactor/routerization

 refactor/routerization
 main
                                # Try to reset client if method exists
                                if hasattr(self.client, 'reset'):
                                    try:
                                        logger.info("Attempting ChromaDB client.reset()...")
                                        self.client.reset()
                                    except Exception as reset_error:
                                        logger.warning(f"client.reset() failed (may not be available): {reset_error}")
 refactor/routerization


 main
 main
                                del self.client
                            except Exception:
                                pass
                        
 refactor/routerization

 refactor/routerization
 main
                        # Force garbage collection to ensure old client is fully freed
                        import gc
                        gc.collect()
                        logger.info("Garbage collected old client references")
                        
 refactor/routerization

                        # Force delete directory completely (more aggressive approach)
                        if os.path.exists(persist_directory):
                            logger.info(f"🗑️ Deleting {persist_directory} directory and all contents...")
                            try:
                                # First, try to make all files writable and delete
                                max_retries = 3
                                for attempt in range(max_retries):
                                    try:
                                        # Make all files writable first
                                        for root, dirs, files in os.walk(persist_directory, topdown=False):
                                            for f in files:
                                                try:
                                                    file_path = os.path.join(root, f)
                                                    os.chmod(file_path, 0o777)
                                                    os.remove(file_path)
                                                except Exception:
                                                    pass
                                            for d in dirs:
                                                try:
                                                    dir_path = os.path.join(root, d)
                                                    os.chmod(dir_path, 0o777)
                                                    shutil.rmtree(dir_path, ignore_errors=True)
                                                except Exception:
                                                    pass
                                        
                                        # Now delete the directory itself
                                        os.chmod(persist_directory, 0o777)
                                        shutil.rmtree(persist_directory, ignore_errors=True)
                                        
                                        # Verify deletion
                                        if not os.path.exists(persist_directory):
                                            logger.info(f"✅ Deleted {persist_directory} (attempt {attempt + 1})")
                                            break
                                        else:
                                            if attempt < max_retries - 1:
                                                logger.warning(f"Directory still exists, retrying... (attempt {attempt + 1}/{max_retries})")
                                                import time
                                                time.sleep(0.5)
                                    except Exception as delete_error:
                                        if attempt < max_retries - 1:
                                            logger.warning(f"Delete attempt {attempt + 1} failed: {delete_error}, retrying...")
                                            import time
                                            time.sleep(0.5)
                                        else:
                                            raise
                                
                                # Final verification
                                if os.path.exists(persist_directory):
                                    logger.error(f"❌ Directory still exists after {max_retries} attempts")
                                    raise RuntimeError(f"Failed to delete {persist_directory} after {max_retries} attempts")
                                    

 main
                        # Force delete directory completely (more aggressive approach)
                        if os.path.exists(persist_directory):
                            logger.info(f"🗑️ Deleting {persist_directory} directory and all contents...")
                            try:
                                # First, try to make all files writable and delete
                                max_retries = 3
                                for attempt in range(max_retries):
                                    try:
                                        # Make all files writable first
                                        for root, dirs, files in os.walk(persist_directory, topdown=False):
                                            for f in files:
                                                try:
                                                    file_path = os.path.join(root, f)
                                                    os.chmod(file_path, 0o777)
                                                    os.remove(file_path)
                                                except Exception:
                                                    pass
                                            for d in dirs:
                                                try:
                                                    dir_path = os.path.join(root, d)
                                                    os.chmod(dir_path, 0o777)
                                                    shutil.rmtree(dir_path, ignore_errors=True)
                                                except Exception:
                                                    pass
                                        
                                        # Now delete the directory itself
                                        os.chmod(persist_directory, 0o777)
                                        shutil.rmtree(persist_directory, ignore_errors=True)
                                        
                                        # Verify deletion
                                        if not os.path.exists(persist_directory):
                                            logger.info(f"✅ Deleted {persist_directory} (attempt {attempt + 1})")
                                            break
                                        else:
                                            if attempt < max_retries - 1:
                                                logger.warning(f"Directory still exists, retrying... (attempt {attempt + 1}/{max_retries})")
                                                import time
                                                time.sleep(0.5)
                                    except Exception as delete_error:
                                        if attempt < max_retries - 1:
                                            logger.warning(f"Delete attempt {attempt + 1} failed: {delete_error}, retrying...")
                                            import time
                                            time.sleep(0.5)
                                        else:
                                            raise
                                
 refactor/routerization
                                # Final verification
                                if os.path.exists(persist_directory):
                                    logger.error(f"❌ Directory still exists after {max_retries} attempts")
                                    raise RuntimeError(f"Failed to delete {persist_directory} after {max_retries} attempts")
                                    

                                # Now delete everything
                                shutil.rmtree(persist_directory, ignore_errors=True)
                                logger.info(f"✅ Deleted {persist_directory}")
 main
 main
                            except Exception as delete_error:
                                logger.error(f"❌ Failed to delete directory: {delete_error}")
                                logger.error("💡 MANUAL ACTION REQUIRED: Please delete data/vector_db directory on Railway and restart service")
                                raise RuntimeError(
                                    f"ChromaDB schema mismatch and directory deletion failed: {delete_error}. "
                                    "Please manually delete data/vector_db directory on Railway and restart."
                                ) from delete_error
                        
 refactor/routerization
                        # Wait for filesystem sync (longer wait for Railway)
                        import time
                        time.sleep(2.0)  # Increased wait time for Railway filesystem sync
                        
                        # CRITICAL: Also try to delete parent data directory if it exists
                        # This ensures no leftover SQLite files or locks
                        parent_dir = os.path.dirname(persist_directory) if os.path.dirname(persist_directory) else "data"
                        if parent_dir and os.path.exists(parent_dir):
                            # Check if there are other important files in data/ directory
                            try:
                                other_files = [f for f in os.listdir(parent_dir) if f != "vector_db"]
                                if not other_files or all(f.endswith('.db') for f in other_files):
                                    # Only vector_db or only .db files - safe to delete parent
                                    logger.info(f"🗑️ Also deleting parent directory {parent_dir} to ensure clean reset...")
                                    try:
                                        shutil.rmtree(parent_dir, ignore_errors=True)
                                        time.sleep(1.0)
                                        os.makedirs(parent_dir, exist_ok=True)
                                        logger.info(f"✅ Recreated parent directory {parent_dir}")
                                    except Exception as parent_error:
                                        logger.warning(f"Could not delete parent directory (this is OK): {parent_error}")
                            except Exception:
                                pass  # Ignore if can't list directory

 refactor/routerization
                        # Wait for filesystem sync (longer wait for Railway)
                        import time
                        time.sleep(2.0)  # Increased wait time for Railway filesystem sync

                        # Wait for filesystem sync
                        import time
                        time.sleep(1.0)  # Increased wait time for Railway filesystem
 main
 main
                        
                        # Create fresh directory
                        os.makedirs(persist_directory, exist_ok=True)
                        logger.info(f"✅ Created fresh directory: {persist_directory}")
                        
 refactor/routerization
                        # Wait a bit more before creating client
                        time.sleep(1.0)  # Increased wait time
                        
                        # CRITICAL FIX: Create client with a temporary unique path first
                        # This ensures ChromaDB creates completely fresh database
                        import uuid
                        temp_path = os.path.join(persist_directory, f"temp_{uuid.uuid4().hex[:8]}")
                        logger.info(f"🔄 Creating ChromaDB client with temporary path first: {temp_path}")
                        
                        try:
                            # Create client with temp path first
                            temp_client = chromadb.PersistentClient(
                                path=temp_path,
                                settings=Settings(
                                    anonymized_telemetry=False,
                                    allow_reset=True
                                )
                            )
                            
                            # Create a test collection to ensure client works
                            test_collection = temp_client.create_collection(
                                name="test_init",
                                metadata={"test": "true"}
                            )
                            temp_client.delete_collection("test_init")
                            
                            # Now close temp client and move to final path
                            del temp_client
                            import gc
                            gc.collect()
                            time.sleep(0.5)
                            
                            # Remove temp directory
                            if os.path.exists(temp_path):
                                shutil.rmtree(temp_path, ignore_errors=True)
                            
                            # Now create client with final path
                            logger.info(f"🔄 Creating ChromaDB client with final path: {persist_directory}")
                            self.client = chromadb.PersistentClient(
                                path=persist_directory,
                                settings=Settings(
                                    anonymized_telemetry=False,
                                    allow_reset=True
                                )
                            )
                            
                        except Exception as temp_error:
                            logger.warning(f"Temp path approach failed, trying direct path: {temp_error}")
                            # Fallback: Create directly with final path
                            self.client = chromadb.PersistentClient(
                                path=persist_directory,
                                settings=Settings(
                                    anonymized_telemetry=False,
                                    allow_reset=True
                                )
                            )
                        
                        # Try to reset if method exists (some ChromaDB versions have this)
                        try:
                            if hasattr(self.client, 'reset'):
                                logger.info("Calling ChromaDB client.reset() to clear any cached metadata...")
                                self.client.reset()
                        except Exception as reset_warning:
                            logger.warning(f"client.reset() not available or failed (this is OK): {reset_warning}")

 refactor/routerization
                        # Wait a bit more before creating client
                        time.sleep(0.5)
                        
                        # Now create fresh client with explicit reset
                        # Use a temporary path first to avoid any caching issues
                        temp_client = chromadb.PersistentClient(

                        # Now create fresh client
                        self.client = chromadb.PersistentClient(
 main
                            path=persist_directory,
                            settings=Settings(
                                anonymized_telemetry=False,
                                allow_reset=True
                            )
                        )
 refactor/routerization
                        
                        # Try to reset if method exists (some ChromaDB versions have this)
                        try:
                            if hasattr(temp_client, 'reset'):
                                logger.info("Calling ChromaDB client.reset() to clear any cached metadata...")
                                temp_client.reset()
                        except Exception as reset_warning:
                            logger.warning(f"client.reset() not available or failed (this is OK): {reset_warning}")
                        
                        self.client = temp_client
                        

                        
 main
 main
                        # Create fresh collections
                        self.knowledge_collection = self.client.create_collection(
                            name="stillme_knowledge",
                            metadata={"description": "Knowledge base for StillMe learning"}
                        )
                        self.conversation_collection = self.client.create_collection(
                            name="stillme_conversations",
                            metadata={"description": "Conversation history for context"}
                        )
                        logger.info("✅ ChromaDB database reset successfully - fresh collections created")
                    except Exception as reset_error:
                        logger.error(f"❌ CRITICAL: Failed to reset ChromaDB: {reset_error}", exc_info=True)
                        logger.error("💡 MANUAL ACTION REQUIRED: Delete data/vector_db directory on Railway and restart service")
                        raise RuntimeError(
                            f"ChromaDB schema mismatch and reset failed: {reset_error}. "
                            "Please manually delete data/vector_db directory on Railway and restart the service."
                        ) from reset_error
                else:
                    raise RuntimeError(
                        f"ChromaDB schema mismatch: {e}. "
                        "This usually happens when ChromaDB version changed. "
                        "Set FORCE_DB_RESET_ON_STARTUP=true or manually delete the data/vector_db directory and restart."
                    ) from e
            else:
                raise
    
    def _get_or_create_collection(self, name: str, description: str):
        """Get existing collection or create new one"""
        try:
            return self.client.get_collection(name=name)
        except Exception as e:
            error_msg = str(e).lower()
            # Check for schema mismatch - if collection exists but schema is wrong
            if "no such column" in error_msg or "schema" in error_msg or "topic" in error_msg:
                logger.warning(f"Schema mismatch when getting collection {name}: {e}")
                # Try to delete and recreate
                try:
                    self.client.delete_collection(name=name)
                    logger.info(f"Deleted collection {name} due to schema mismatch")
                except Exception as delete_error:
                    logger.warning(f"Could not delete collection {name}: {delete_error}")
            
            # Collection doesn't exist or was deleted, create it
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
