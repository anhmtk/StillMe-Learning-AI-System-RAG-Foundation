"""
ChromaDB Client for StillMe Vector Database
Handles vector storage and retrieval operations
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Import backup manager (avoid circular import)
try:
    from .chroma_backup import ChromaBackupManager
except ImportError:
    ChromaBackupManager = None
    logger.warning("ChromaBackupManager not available")

logger = logging.getLogger(__name__)

class ChromaClient:
    """ChromaDB client for StillMe vector operations"""
    
    def __init__(self, persist_directory: str = None, reset_on_error: bool = False, embedding_service=None):
        """Initialize ChromaDB client
        
        Args:
            persist_directory: Directory to persist vector database (defaults to /app/data/vector_db or env var)
            reset_on_error: If True, reset database on schema errors
            embedding_service: Optional EmbeddingService to generate embeddings (prevents ChromaDB from using default ONNX model)
        """
        self.embedding_service = embedding_service
        import os
        import shutil
        
        # CRITICAL FIX: Use absolute path for Railway persistence
        # Priority 1: Environment variable (for Railway persistent volume)
        # Priority 2: Absolute path /app/data/vector_db (Railway standard)
        # Priority 3: User-provided path (if absolute)
        # Priority 4: Relative path (fallback for local dev)
        if persist_directory is None:
            # Check environment variable first
            persist_directory = os.getenv("CHROMA_DB_PATH")
            if persist_directory:
                logger.info(f"✅ Using CHROMA_DB_PATH from environment: {persist_directory}")
            else:
                # Use absolute path for Railway (persists across deploys)
                persist_directory = "/app/data/vector_db"
                logger.info(f"✅ Using default absolute path for Railway persistence: {persist_directory}")
        else:
            # If user provided path, check if it's relative or absolute
            if not os.path.isabs(persist_directory):
                # Relative path - convert to absolute based on working directory
                # For Railway, we want /app/data/vector_db
                if persist_directory.startswith("data/"):
                    persist_directory = f"/app/{persist_directory}"
                    logger.info(f"✅ Converted relative path to absolute: {persist_directory}")
                else:
                    # Other relative paths - use as-is (local dev)
                    logger.warning(f"⚠️ Using relative path (may not persist on Railway): {persist_directory}")
        
        self.persist_directory = persist_directory
        self.reset_on_error = reset_on_error
        
        # Initialize backup manager (if available)
        if ChromaBackupManager is not None:
            self.backup_manager = ChromaBackupManager(
                persist_directory=persist_directory,
                backup_directory=os.getenv("CHROMA_BACKUP_DIR")
            )
        else:
            self.backup_manager = None
            logger.warning("ChromaDB backup manager not available")
        
        # CRITICAL: Ensure parent directory exists with proper permissions
        # This is essential for Railway persistent volumes
        parent_dir = os.path.dirname(persist_directory)
        if parent_dir and not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir, mode=0o755, exist_ok=True)
                logger.info(f"✅ Created parent directory: {parent_dir}")
            except Exception as parent_error:
                logger.warning(f"⚠️ Could not create parent directory {parent_dir}: {parent_error}")
        
        # Ensure persist_directory exists (if not resetting)
        if not reset_on_error and not os.path.exists(persist_directory):
            try:
                os.makedirs(persist_directory, mode=0o755, exist_ok=True)
                logger.info(f"✅ Created ChromaDB directory: {persist_directory}")
            except Exception as dir_error:
                logger.warning(f"⚠️ Could not create ChromaDB directory {persist_directory}: {dir_error}")
        
        # CRITICAL: Verify directory is writable (essential for persistence)
        if os.path.exists(persist_directory):
            if os.access(persist_directory, os.W_OK):
                logger.info(f"✅ ChromaDB directory is writable: {persist_directory}")
                # Check if directory has existing data
                try:
                    files_in_dir = os.listdir(persist_directory)
                    if files_in_dir:
                        logger.info(f"📊 ChromaDB directory contains {len(files_in_dir)} items (existing data detected)")
                        # Log some file names for debugging (first 5)
                        for item in files_in_dir[:5]:
                            item_path = os.path.join(persist_directory, item)
                            if os.path.isfile(item_path):
                                size = os.path.getsize(item_path)
                                logger.info(f"   - File: {item} ({size} bytes)")
                            elif os.path.isdir(item_path):
                                logger.info(f"   - Directory: {item}")
                    else:
                        logger.info(f"📊 ChromaDB directory is empty (new database)")
                except Exception as list_error:
                    logger.warning(f"⚠️ Could not list directory contents: {list_error}")
            else:
                logger.error(f"❌ ChromaDB directory is NOT writable: {persist_directory}")
                logger.error("💡 This will cause data loss on Railway. Check volume mount permissions.")
        else:
            logger.warning(f"⚠️ ChromaDB directory does not exist yet: {persist_directory}")
        
        # CRITICAL: Add comprehensive persistence debugging
        logger.info(f"🔄 ChromaDB Persistence Debug:")
        logger.info(f"   - Requested path: {persist_directory}")
        logger.info(f"   - Absolute path: {os.path.abspath(persist_directory)}")
        logger.info(f"   - Directory exists: {os.path.exists(persist_directory)}")
        if os.path.exists(persist_directory):
            logger.info(f"   - Directory writable: {os.access(persist_directory, os.W_OK)}")
            try:
                files = os.listdir(persist_directory)
                logger.info(f"   - Files in directory: {len(files)} items")
                if files:
                    logger.info(f"   - Sample files: {files[:3]}")
            except Exception as e:
                logger.warning(f"   - Could not list files: {e}")
        else:
            logger.info(f"   - Directory writable: N/A (does not exist)")
        
        # Check parent directory (CRITICAL for Railway volume mount verification)
        parent_dir = os.path.dirname(persist_directory)
        if parent_dir:
            parent_exists = os.path.exists(parent_dir)
            parent_writable = os.access(parent_dir, os.W_OK) if parent_exists else False
            logger.info(f"   - Parent directory exists: {parent_exists}")
            if parent_exists:
                logger.info(f"   - Parent directory writable: {parent_writable}")
                # Check if parent is likely a Railway volume mount point
                if parent_dir == "/app/data":
                    logger.info(f"   - ✅ Parent directory is /app/data (Railway volume mount point)")
                    if parent_writable:
                        logger.info(f"   - ✅ Volume mount appears to be working correctly")
                    else:
                        logger.error(f"   - ❌ Volume mount exists but is NOT writable - data will NOT persist!")
                else:
                    logger.warning(f"   - ⚠️ Parent directory is {parent_dir} (not /app/data - may not be persistent volume)")
            else:
                logger.error(f"   - ❌ CRITICAL: Parent directory {parent_dir} does NOT exist!")
                logger.error(f"   - ❌ This means Railway volume is NOT mounted - data will be lost on redeploy!")
                logger.error(f"   - 💡 Action: Create volume 'stillme-chromadb-data' in Railway dashboard and mount to /app/data")
        
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
            # CRITICAL: Set ChromaDB ONNX cache to persistent volume
            # ChromaDB caches ONNX models in ~/.cache/chroma/onnx_models/
            # We need to redirect this to Railway persistent volume
            import os
            chroma_cache_dir = "/app/.cache/chroma"
            if os.path.exists(chroma_cache_dir):
                # Persistent volume is mounted at /app/.cache/chroma
                os.environ["CHROMA_CACHE_DIR"] = chroma_cache_dir
                logger.info(f"✅ Using Railway persistent volume for ChromaDB ONNX cache: {chroma_cache_dir}")
            else:
                # Fallback to default cache location
                logger.warning(f"⚠️ ChromaDB persistent cache not found at {chroma_cache_dir}, using default cache")
            
            # Create client - if reset_on_error was True, directory is fresh
            # CRITICAL: Use absolute path to ensure persistence on Railway
            logger.info(f"🔧 Initializing ChromaDB PersistentClient with path: {persist_directory}")
            logger.info(f"🔧 Path is absolute: {os.path.isabs(persist_directory)}")
            logger.info(f"🔧 Path exists: {os.path.exists(persist_directory)}")
            
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # CRITICAL: Verify client is using persistent storage (not in-memory)
            logger.info(f"✅ ChromaDB PersistentClient initialized successfully")
            logger.info(f"✅ Database will persist at: {persist_directory}")
            logger.info(f"✅ This ensures knowledge persists across Railway deploys")
            
            # If reset_on_error was True, we deleted the directory, so create new collections directly
            # Otherwise, try to get existing collections or create new ones
            if reset_on_error:
                # Fresh start - create new collections directly (don't try to delete first)
                logger.info("Creating new collections after reset...")
                # Don't try to delete collections - database is fresh, they don't exist
                try:
                    self.knowledge_collection = self.client.create_collection(
                        name="stillme_knowledge",
                        metadata={"description": "Knowledge base for StillMe learning"},
                        # CRITICAL: Use cosine distance for normalized embeddings
                        # Normalized embeddings work best with cosine similarity
                        distance_metric="cosine"
                    )
                    logger.info("✅ Created stillme_knowledge collection with cosine distance metric")
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
                            metadata={"description": "Knowledge base for StillMe learning"},
                            # CRITICAL: Use cosine distance for normalized embeddings
                            distance_metric="cosine"
                        )
                    else:
                        raise
                
                try:
                    self.conversation_collection = self.client.create_collection(
                        name="stillme_conversations",
                        metadata={"description": "Conversation history for context"},
                        # CRITICAL: Use cosine distance for normalized embeddings
                        distance_metric="cosine"
                    )
                    logger.info("✅ Created stillme_conversations collection with cosine distance metric")
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
                            metadata={"description": "Conversation history for context"},
                            # CRITICAL: Use cosine distance for normalized embeddings
                            distance_metric="cosine"
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
            
            # CRITICAL: Verify persistence after initialization
            # Check if collections exist and have data
            try:
                knowledge_count = self.knowledge_collection.count()
                conversation_count = self.conversation_collection.count()
                logger.info(f"📊 ChromaDB Collections Status:")
                logger.info(f"   - stillme_knowledge: {knowledge_count} documents")
                logger.info(f"   - stillme_conversations: {conversation_count} documents")
                logger.info(f"   - Total: {knowledge_count + conversation_count} documents")
                
                if knowledge_count > 0:
                    logger.info(f"✅ ChromaDB has existing knowledge data - persistence is working!")
                else:
                    logger.info(f"📊 ChromaDB is empty (new database or after reset)")
                
                # Verify directory still exists and is writable
                if os.path.exists(persist_directory):
                    logger.info(f"✅ Persistence directory still exists: {persist_directory}")
                    if os.access(persist_directory, os.W_OK):
                        logger.info(f"✅ Persistence directory is writable")
                    else:
                        logger.error(f"❌ Persistence directory is NOT writable - data loss risk!")
                else:
                    logger.error(f"❌ Persistence directory does NOT exist - data loss risk!")
                    
            except Exception as verify_error:
                logger.warning(f"⚠️ Could not verify ChromaDB persistence status: {verify_error}")
            
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
                                # Try to reset client if method exists
                                if hasattr(self.client, 'reset'):
                                    try:
                                        logger.info("Attempting ChromaDB client.reset()...")
                                        self.client.reset()
                                    except Exception as reset_error:
                                        logger.warning(f"client.reset() failed (may not be available): {reset_error}")
                                del self.client
                            except Exception:
                                pass
                        
                        # Force garbage collection to ensure old client is fully freed
                        import gc
                        gc.collect()
                        logger.info("Garbage collected old client references")
                        
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
                                    
                            except Exception as delete_error:
                                logger.error(f"❌ Failed to delete directory: {delete_error}")
                                logger.error("💡 MANUAL ACTION REQUIRED: Please delete data/vector_db directory on Railway and restart service")
                                raise RuntimeError(
                                    f"ChromaDB schema mismatch and directory deletion failed: {delete_error}. "
                                    "Please manually delete data/vector_db directory on Railway and restart."
                                ) from delete_error
                        
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
                        
                        # Create fresh directory
                        os.makedirs(persist_directory, exist_ok=True)
                        logger.info(f"✅ Created fresh directory: {persist_directory}")
                        
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
                            _ = temp_client.create_collection(
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
                            logger.info(f"🔧 Path is absolute: {os.path.isabs(persist_directory)}")
                            logger.info(f"🔧 Path exists: {os.path.exists(persist_directory)}")
                            
                            self.client = chromadb.PersistentClient(
                                path=persist_directory,
                                settings=Settings(
                                    anonymized_telemetry=False,
                                    allow_reset=True
                                )
                            )
                            
                            logger.info(f"✅ ChromaDB PersistentClient initialized (after reset)")
                            logger.info(f"✅ Database will persist at: {persist_directory}")
                            
                        except Exception as temp_error:
                            logger.warning(f"Temp path approach failed, trying direct path: {temp_error}")
                            # Fallback: Create directly with final path
                            logger.info(f"🔧 Creating ChromaDB client with direct path: {persist_directory}")
                            logger.info(f"🔧 Path is absolute: {os.path.isabs(persist_directory)}")
                            
                            self.client = chromadb.PersistentClient(
                                path=persist_directory,
                                settings=Settings(
                                    anonymized_telemetry=False,
                                    allow_reset=True
                                )
                            )
                            
                            logger.info(f"✅ ChromaDB PersistentClient initialized (fallback)")
                            logger.info(f"✅ Database will persist at: {persist_directory}")
                        
                        # Try to reset if method exists (some ChromaDB versions have this)
                        try:
                            if hasattr(self.client, 'reset'):
                                logger.info("Calling ChromaDB client.reset() to clear any cached metadata...")
                                self.client.reset()
                        except Exception as reset_warning:
                            logger.warning(f"client.reset() not available or failed (this is OK): {reset_warning}")
                        
                        # Create fresh collections
                        self.knowledge_collection = self.client.create_collection(
                            name="stillme_knowledge",
                            metadata={"description": "Knowledge base for StillMe learning"},
                            # CRITICAL: Use cosine distance for normalized embeddings
                            distance_metric="cosine"
                        )
                        self.conversation_collection = self.client.create_collection(
                            name="stillme_conversations",
                            metadata={"description": "Conversation history for context"},
                            # CRITICAL: Use cosine distance for normalized embeddings
                            distance_metric="cosine"
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
            # CRITICAL: Use cosine distance for normalized embeddings
            return self.client.create_collection(
                name=name,
                metadata={"description": description},
                distance_metric="cosine"
            )
    
    def add_knowledge(self, 
                     documents: List[str], 
                     metadatas: List[Dict[str, Any]], 
                     ids: List[str]) -> bool:
        """Add knowledge documents to vector database
        
        This method:
        1. Generates embeddings using EmbeddingService (if available) to use paraphrase-multilingual-MiniLM-L12-v2
        2. Inserts documents with embeddings into ChromaDB collection
        3. Logs progress for monitoring
        
        CRITICAL: If embedding_service is provided, we generate embeddings ourselves to avoid ChromaDB
        using default ONNX model (all-MiniLM-L6-v2). This ensures we use paraphrase-multilingual-MiniLM-L12-v2.
        
        Args:
            documents: List of text documents
            metadatas: List of metadata for each document
            ids: List of unique IDs for each document
            
        Returns:
            bool: Success status
        """
        try:
            import time
            start_time = time.time()
            
            # CRITICAL: Generate embeddings using EmbeddingService if available
            # This prevents ChromaDB from using default ONNX model (all-MiniLM-L6-v2)
            if self.embedding_service:
                logger.debug(f"🔧 Generating embeddings using EmbeddingService (paraphrase-multilingual-MiniLM-L12-v2) for {len(documents)} document(s)...")
                embeddings = [self.embedding_service.encode_text(doc) for doc in documents]
                
                self.knowledge_collection.add(
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            else:
                # Fallback: Let ChromaDB generate embeddings (will use default ONNX model)
                logger.warning("⚠️ EmbeddingService not provided - ChromaDB will use default ONNX model (all-MiniLM-L6-v2)")
                logger.debug(f"🔧 ChromaDB: Generating embeddings for {len(documents)} document(s)...")
                
                self.knowledge_collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            elapsed = time.time() - start_time
            logger.debug(
                f"✅ ChromaDB: Inserted {len(documents)} knowledge document(s) "
                f"(embedding + insertion: {elapsed:.3f}s)"
            )
            return True
        except Exception as e:
            logger.error(f"❌ ChromaDB: Failed to add knowledge: {e}", exc_info=True)
            return False
    
    def add_conversation(self, 
                        documents: List[str], 
                        metadatas: List[Dict[str, Any]], 
                        ids: List[str]) -> bool:
        """Add conversation context to vector database
        
        CRITICAL: If embedding_service is provided, we generate embeddings ourselves to avoid ChromaDB
        using default ONNX model (all-MiniLM-L6-v2). This ensures we use paraphrase-multilingual-MiniLM-L12-v2.
        
        Args:
            documents: List of conversation texts
            metadatas: List of metadata for each conversation
            ids: List of unique IDs for each conversation
            
        Returns:
            bool: Success status
        """
        try:
            # Filter out None values from metadata to prevent ChromaDB TypeError
            cleaned_metadatas = []
            for metadata in metadatas:
                cleaned_metadata = {k: v for k, v in metadata.items() if v is not None}
                cleaned_metadatas.append(cleaned_metadata)
            
            # CRITICAL: Generate embeddings using EmbeddingService if available
            # This prevents ChromaDB from using default ONNX model (all-MiniLM-L6-v2)
            if self.embedding_service:
                logger.debug(f"🔧 Generating embeddings using EmbeddingService (paraphrase-multilingual-MiniLM-L12-v2) for {len(documents)} conversation(s)...")
                embeddings = [self.embedding_service.encode_text(doc) for doc in documents]
                
                self.conversation_collection.add(
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=cleaned_metadatas,
                    ids=ids
                )
            else:
                # Fallback: Let ChromaDB generate embeddings (will use default ONNX model)
                logger.warning("⚠️ EmbeddingService not provided - ChromaDB will use default ONNX model (all-MiniLM-L6-v2)")
                
                self.conversation_collection.add(
                    documents=documents,
                    metadatas=cleaned_metadatas,
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
        # Validate limit parameter - must be > 0
        if limit <= 0:
            logger.warning(f"Invalid knowledge search limit: {limit}. Must be > 0. Returning empty results.")
            return []
        
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
                    # Safely extract metadata - filter out None values to avoid ChromaDB TypeError
                    raw_metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] and i < len(results["metadatas"][0]) else {}
                    # Filter out None values - ChromaDB Rust client can't handle None in metadata
                    clean_metadata = {k: v for k, v in raw_metadata.items() if v is not None} if isinstance(raw_metadata, dict) else {}
                    
                    search_results.append({
                        "content": doc,
                        "metadata": clean_metadata,
                        "distance": results["distances"][0][i] if results["distances"] and results["distances"][0] and i < len(results["distances"][0]) else 0.0,
                        "id": results["ids"][0][i] if results["ids"] and results["ids"][0] and i < len(results["ids"][0]) else f"doc_{i}"
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
            limit: Number of results to return (must be > 0)
            where: Optional metadata filter
            
        Returns:
            List of search results
        """
        # Validate limit parameter - must be > 0
        if limit <= 0:
            logger.warning(f"Invalid conversation search limit: {limit}. Must be > 0. Returning empty results.")
            return []
        
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
                    # Safely extract metadata - filter out None values to avoid ChromaDB TypeError
                    raw_metadata = results["metadatas"][0][i] if results["metadatas"] and results["metadatas"][0] and i < len(results["metadatas"][0]) else {}
                    # Filter out None values - ChromaDB Rust client can't handle None in metadata
                    clean_metadata = {k: v for k, v in raw_metadata.items() if v is not None} if isinstance(raw_metadata, dict) else {}
                    
                    search_results.append({
                        "content": doc,
                        "metadata": clean_metadata,
                        "distance": results["distances"][0][i] if results["distances"] and results["distances"][0] and i < len(results["distances"][0]) else 0.0,
                        "id": results["ids"][0][i] if results["ids"] and results["ids"][0] and i < len(results["ids"][0]) else f"conv_{i}"
                    })
            
            return search_results
        except Exception as e:
            logger.error(f"Failed to search conversations: {e}")
            return []
    
    def check_duplicate_by_link(self, link: str) -> bool:
        """Check if a document with the given link already exists in knowledge collection
        
        This is an optimized duplicate check that queries by metadata filter (no embedding needed)
        Much faster than retrieve_context for duplicate detection during learning cycles.
        
        Args:
            link: URL link to check for duplicates
            
        Returns:
            True if duplicate exists, False otherwise
        """
        if not link:
            return False
        
        try:
            # Query ChromaDB directly by metadata filter (no embedding needed)
            results = self.knowledge_collection.get(
                where={"link": link},
                limit=1
            )
            # If we get any results, it's a duplicate
            return len(results.get("ids", [])) > 0
        except Exception as e:
            # If metadata filter fails (e.g., ChromaDB version compatibility), return False
            # This allows the entry to be added (better than blocking all entries)
            logger.debug(f"Duplicate check by link failed (non-critical): {e}")
            return False
    
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
    
    def create_backup(self, backup_name: Optional[str] = None) -> Optional[str]:
        """Create a backup of ChromaDB data
        
        Args:
            backup_name: Optional backup name (defaults to timestamp)
            
        Returns:
            Path to backup directory, or None if backup manager not available
        """
        if self.backup_manager is None:
            logger.warning("Backup manager not available")
            return None
        return self.backup_manager.create_backup(backup_name)
    
    def restore_backup(self, backup_name: str, verify: bool = True) -> bool:
        """Restore ChromaDB from backup
        
        Args:
            backup_name: Name of backup to restore
            verify: If True, verify backup before restoring
            
        Returns:
            True if successful, False otherwise
        """
        if self.backup_manager is None:
            logger.warning("Backup manager not available")
            return False
        return self.backup_manager.restore_backup(backup_name, verify)
    
    def list_backups(self) -> List[dict]:
        """List all available backups
        
        Returns:
            List of backup metadata dictionaries
        """
        if self.backup_manager is None:
            return []
        return self.backup_manager.list_backups()
    
    def get_backup_stats(self) -> dict:
        """Get statistics about backups
        
        Returns:
            Dictionary with backup statistics
        """
        if self.backup_manager is None:
            return {"error": "Backup manager not available"}
        return self.backup_manager.get_backup_stats()
