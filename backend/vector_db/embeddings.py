"""
Embedding Service for StillMe
Handles text embedding generation using sentence-transformers
"""

# CRITICAL: Set environment variables BEFORE importing SentenceTransformer
# HuggingFace/transformers resolves cache path on first import
# We must set env vars before any transformers imports
import os
from pathlib import Path

# CRITICAL: Initialize ModelManager FIRST to setup environment and verify cache
# This MUST happen before any SentenceTransformer imports
try:
    from backend.utils.model_cache import ModelManager
    # Initialize ModelManager at module level to setup environment variables
    # This ensures cache is configured before SentenceTransformer is imported
    _global_model_manager = ModelManager(model_name="paraphrase-multilingual-MiniLM-L12-v2")
    # Import logging here to avoid circular import
    import logging as _logging_module
    _temp_logger = _logging_module.getLogger(__name__)
    _temp_logger.info("✅ ModelManager initialized - cache environment configured")
except ImportError as e:
    # Fallback if ModelManager not available
    _global_model_manager = None
    import logging as _logging_module
    _temp_logger = _logging_module.getLogger(__name__)
    _temp_logger.warning(f"⚠️ ModelManager not available, using fallback: {e}")
    # Check for Railway persistent volume FIRST (before any imports)
    _railway_cache = Path("/app/hf_cache")
    if _railway_cache.exists() or _railway_cache.parent.exists():
        # Set env vars immediately to override Dockerfile defaults
        os.environ["TRANSFORMERS_CACHE"] = str(_railway_cache)
        os.environ["HF_HOME"] = str(_railway_cache)
        os.environ["HF_DATASETS_CACHE"] = str(_railway_cache / "datasets")
        os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(_railway_cache)
        # Force HuggingFace to use our cache
        os.environ["HF_HUB_CACHE"] = str(_railway_cache / "hub")
except Exception as e:
    # If ModelManager fails, use fallback
    _global_model_manager = None
    import logging as _logging_module
    _temp_logger = _logging_module.getLogger(__name__)
    _temp_logger.warning(f"⚠️ ModelManager initialization failed, using fallback: {e}")
    # Check for Railway persistent volume
    _railway_cache = Path("/app/hf_cache")
    if _railway_cache.exists() or _railway_cache.parent.exists():
        os.environ["TRANSFORMERS_CACHE"] = str(_railway_cache)
        os.environ["HF_HOME"] = str(_railway_cache)
        os.environ["HF_DATASETS_CACHE"] = str(_railway_cache / "datasets")
        os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(_railway_cache)
        os.environ["HF_HUB_CACHE"] = str(_railway_cache / "hub")

# NOW import SentenceTransformer (after env vars are set)
from sentence_transformers import SentenceTransformer
from typing import List, Union, Dict, Optional
import logging
import hashlib

logger = logging.getLogger(__name__)

# Import Redis cache service (optional - will work without Redis)
try:
    from backend.services.redis_cache import get_cache_service
    REDIS_CACHE_AVAILABLE = True
except ImportError:
    REDIS_CACHE_AVAILABLE = False
    get_cache_service = None

class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        """Initialize embedding service
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        # OPTIMIZATION: Embedding cache for similar queries (reduces redundant encoding)
        # Cache key: hash of normalized query text, value: embedding vector
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_max_size = 100  # Limit cache size to prevent memory issues
        
        # CRITICAL: Use global ModelManager for cache verification
        # ModelManager was already initialized at module level to setup environment
        if _global_model_manager is not None:
            self.model_manager = _global_model_manager
            
            # Get cache_path FIRST before using it
            cache_path = self.model_manager.cache_path
            cache_status = self.model_manager.cache_status
            
            # CRITICAL: Check if OLD model cache exists and delete it if found
            # This ensures we use the new multilingual model, not the old English-only model
            old_model_paths = [
                cache_path / "sentence_transformers" / "multi-qa-MiniLM-L6-dot-v1",
                cache_path / "hub" / "models--sentence-transformers--multi-qa-MiniLM-L6-dot-v1",
                cache_path / "models--sentence-transformers--multi-qa-MiniLM-L6-dot-v1",
            ]
            for old_path in old_model_paths:
                if old_path.exists():
                    logger.warning(f"⚠️ Found OLD model cache at {old_path} - deleting to force new model download...")
                    try:
                        import shutil
                        shutil.rmtree(old_path)
                        logger.info(f"✅ Deleted old model cache: {old_path}")
                    except Exception as delete_error:
                        logger.warning(f"⚠️ Could not delete old model cache: {delete_error}")
            
            # CRITICAL: Fix cache path mismatch (HuggingFace format -> sentence-transformers format)
            # This fixes the issue where model is downloaded in HuggingFace format but SentenceTransformer looks for sentence-transformers format
            # MUST run BEFORE loading SentenceTransformer model
            try:
                from backend.utils.fix_embedding_cache import fix_embedding_model_cache
                logger.info("🔧 🔧 🔧 EMERGENCY: Attempting to fix embedding cache path mismatch BEFORE model load...")
                fix_success = fix_embedding_model_cache(model_name)
                if fix_success:
                    logger.info("✅ ✅ ✅ Embedding cache path fix completed successfully")
                    # Re-verify cache after fix
                    cache_status = self.model_manager.verify_cache_exists()
                    if cache_status.model_files_found:
                        logger.info(f"✅ Cache verified after fix: {cache_status.path}")
                    else:
                        logger.warning("⚠️ Cache fix reported success but verification failed")
                else:
                    logger.error("❌ ❌ ❌ Embedding cache path fix FAILED - model may load incorrectly")
            except ImportError as import_error:
                logger.error(f"❌ Cannot import fix_embedding_cache: {import_error}")
            except Exception as fix_error:
                logger.error(f"❌ ❌ ❌ CRITICAL: Cache fix error: {fix_error}", exc_info=True)
            
            # Try to copy model from image cache to persistent volume if needed
            if not cache_status.model_files_found:
                logger.info("⚠️ Model not found in persistent cache, attempting to copy from image cache...")
                self.model_manager.copy_model_from_image_cache()
                # Re-verify cache after copy attempt
                cache_status = self.model_manager.cache_status
            
            # Log cache status
            if cache_status.model_files_found:
                logger.info(f"✅ Model cache verified: {cache_status.path}")
                logger.info(f"   Size: {cache_status.size_mb:.2f} MB")
                logger.info(f"   Persistent: {'✅ YES' if cache_status.is_persistent else '❌ NO'}")
            else:
                logger.warning(f"⚠️ Model cache NOT found. Will download on first use.")
                logger.warning(f"   Expected location: {cache_path}")
        else:
            # Fallback to old method
            logger.warning("⚠️ Using fallback cache method (ModelManager not available)")
            cache_path = self._get_cache_path()
            self.model_manager = None
        
        try:
            # CRITICAL: Set environment variables BEFORE loading model
            # This ensures SentenceTransformer uses the persistent cache
            if cache_path:
                os.environ["TRANSFORMERS_CACHE"] = str(cache_path)
                os.environ["HF_HOME"] = str(cache_path)
                os.environ["HF_DATASETS_CACHE"] = str(Path(cache_path) / "datasets")
                os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(cache_path)
                logger.info(f"Set cache environment variables to: {cache_path}")
            
            # SentenceTransformer will use TRANSFORMERS_CACHE/HF_HOME env vars
            # cache_folder parameter is also passed for redundancy
            # CRITICAL: Force cache_folder to ensure model is cached in persistent volume
            # Note: SentenceTransformer may ignore cache_folder if env vars are set
            # So we MUST set env vars BEFORE creating the model
            
            # Suppress tqdm progress bars from sentence-transformers to avoid log spam
            # Set TQDM_DISABLE=1 to prevent "Batches: 100%|..." output in logs
            os.environ.setdefault("TQDM_DISABLE", "1")
            
            self.model = SentenceTransformer(
                model_name, 
                cache_folder=cache_path if cache_path else None
            )
            logger.info(f"Embedding model '{model_name}' loaded successfully")
            
            # CRITICAL: Check where model was actually loaded from
            # SentenceTransformer stores model path in model._modules['0'].auto_model.config._name_or_path
            # But more importantly, check the actual cache location
            try:
                # Check if model has cache_dir attribute
                if hasattr(self.model, 'cache_dir'):
                    logger.info(f"📦 Model cache_dir attribute: {self.model.cache_dir}")
                
                # Check HuggingFace cache location (where model files actually are)
                from transformers import file_utils
                hf_cache_dir = file_utils.default_cache_path
                logger.info(f"📦 HuggingFace default cache path: {hf_cache_dir}")
                
                # Check if model files exist in expected persistent volume location
                if cache_path:
                    expected_model_dir = Path(cache_path) / "sentence_transformers" / model_name.replace("/", "_")
                    if expected_model_dir.exists():
                        logger.info(f"✅ Model files found in persistent volume: {expected_model_dir}")
                    else:
                        logger.warning(f"⚠️ Model files NOT in persistent volume. Expected: {expected_model_dir}")
                        # Check if model is in HuggingFace default cache instead
                        if hf_cache_dir.exists() and hf_cache_dir != Path(cache_path):
                            logger.warning(f"⚠️ Model may be cached in HuggingFace default location: {hf_cache_dir}")
            except Exception as check_error:
                logger.debug(f"Could not check model cache location: {check_error}")
            if cache_path:
                logger.info(f"✅ Model cached at: {cache_path}")
                
                # CRITICAL: Verify where model was actually cached
                # SentenceTransformer may cache in different locations
                import sentence_transformers
                actual_cache_dir = getattr(sentence_transformers.util, 'MODEL_CACHE_DIR', None)
                if actual_cache_dir:
                    logger.info(f"📦 SentenceTransformer cache directory: {actual_cache_dir}")
                
                # Check environment variables to see what SentenceTransformer is using
                logger.info(f"📦 TRANSFORMERS_CACHE: {os.getenv('TRANSFORMERS_CACHE', 'NOT SET')}")
                logger.info(f"📦 HF_HOME: {os.getenv('HF_HOME', 'NOT SET')}")
                logger.info(f"📦 SENTENCE_TRANSFORMERS_HOME: {os.getenv('SENTENCE_TRANSFORMERS_HOME', 'NOT SET')}")
                
                # Verify cache exists
                cache_dir = Path(cache_path)
                if cache_dir.exists():
                    logger.info(f"✅ Cache directory exists: {cache_dir}")
                    # Check if model files exist (sentence-transformers uses different paths)
                    # SentenceTransformer stores models in: {cache_dir}/sentence_transformers/{model_name}/
                    # OR: {HF_HOME}/hub/models--{model_name_hf}/
                    model_name_safe = model_name.replace("/", "_")
                    model_name_hf = model_name.replace("/", "--")
                    
                    # Check sentence-transformers cache location (most common)
                    st_cache_path = cache_dir / "sentence_transformers" / model_name_safe
                    st_cache_path_alt = cache_dir / "sentence_transformers" / model_name
                    
                    # Check HuggingFace hub cache location
                    hf_hub_path = cache_dir / "hub" / f"models--{model_name_hf}"
                    
                    # Also check if cache_dir itself contains model files (direct storage)
                    cache_has_models = (
                        (cache_dir / "sentence_transformers").exists() or
                        (cache_dir / "hub").exists() or
                        any(cache_dir.glob("*.bin")) or  # Model weight files
                        any(cache_dir.glob("*.safetensors"))  # SafeTensor files
                    )
                    
                    possible_paths = [
                        st_cache_path,
                        st_cache_path_alt,
                        hf_hub_path,
                        cache_dir / f"models--{model_name_hf}",
                        cache_dir / f"models--sentence-transformers--{model_name_hf}",  # HuggingFace format for sentence-transformers
                        cache_dir / "hub" / f"models--sentence-transformers--{model_name_hf}",
                    ]
                    
                    model_found = False
                    found_path = None
                    for model_path in possible_paths:
                        if model_path.exists() and (model_path.is_dir() or model_path.is_file()):
                            # Check if it's actually a model directory (has config.json or similar)
                            if model_path.is_dir():
                                if any(model_path.glob("*.json")) or any(model_path.glob("*.bin")) or any(model_path.glob("*.safetensors")):
                                    logger.info(f"✅ Model files found in cache: {model_path}")
                                    model_found = True
                                    found_path = model_path
                                    break
                            else:
                                logger.info(f"✅ Model file found in cache: {model_path}")
                                model_found = True
                                found_path = model_path
                                break
                    
                    # Also check if cache directory has any model-related files
                    if not model_found and cache_has_models:
                        logger.info(f"✅ Model cache directory contains model files: {cache_dir}")
                        model_found = True
                        found_path = cache_dir
                    
                    if not model_found:
                        logger.warning(f"⚠️ Model files not found in cache. Will download on first use.")
                        logger.info(f"Cache directory: {cache_dir}")
                        logger.info(f"Expected model path (sentence-transformers format): {st_cache_path}")
                        logger.info(f"Alternative path (HuggingFace format): {cache_dir / f'models--sentence-transformers--{model_name_hf}'}")
                        logger.info(f"💡 Model will be downloaded and cached when first used.")
                        logger.info(f"💡 After download, model will be cached at: {cache_dir / f'models--sentence-transformers--{model_name_hf}'}")
                    else:
                        logger.info(f"✅ Model cache verified: {found_path}")
                else:
                    logger.error(f"❌ Cache directory does not exist: {cache_dir}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _get_cache_path(self) -> Union[str, None]:
        """
        Get cache path for HuggingFace models.
        CRITICAL: Railway persistent volume has HIGHEST priority to prevent re-downloading on every deploy.
        Priority order:
        1. Railway persistent volume (/app/hf_cache) - PERSISTENT across deploys
        2. PERSISTENT_CACHE_PATH environment variable
        3. Docker image cache (/app/.model_cache) - EPHEMERAL, re-downloads on deploy
        4. Custom cache paths
        
        Returns:
            Cache path string or None to use default
        """
        # Priority 1: Railway persistent volume (HIGHEST PRIORITY - persists across deploys)
        # Check if Railway persistent volume mount exists directly
        railway_cache = Path("/app/hf_cache")
        if railway_cache.exists():
            cache_dir = railway_cache
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Using Railway persistent volume cache: {cache_dir}")
            # Set environment variables immediately
            os.environ["TRANSFORMERS_CACHE"] = str(cache_dir)
            os.environ["HF_HOME"] = str(cache_dir)
            os.environ["HF_DATASETS_CACHE"] = str(cache_dir / "datasets")
            os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(cache_dir)
            return str(cache_dir)
        elif railway_cache.parent.exists():
            # Parent exists but not the cache dir itself - create it
            cache_dir = railway_cache
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created Railway persistent volume cache: {cache_dir}")
            # Set environment variables immediately
            os.environ["TRANSFORMERS_CACHE"] = str(cache_dir)
            os.environ["HF_HOME"] = str(cache_dir)
            os.environ["HF_DATASETS_CACHE"] = str(cache_dir / "datasets")
            os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(cache_dir)
            return str(cache_dir)
        
        # Priority 2: Check PERSISTENT_CACHE_PATH environment variable
        persistent_cache = os.getenv("PERSISTENT_CACHE_PATH")
        if persistent_cache:
            # If path ends with /hf_cache, use it directly, otherwise append /huggingface
            if persistent_cache.endswith("/hf_cache") or persistent_cache.endswith("\\hf_cache"):
                cache_dir = Path(persistent_cache)
            else:
                cache_dir = Path(persistent_cache) / "huggingface"
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Using persistent volume cache: {cache_dir}")
            # Set environment variables immediately
            os.environ["TRANSFORMERS_CACHE"] = str(cache_dir)
            os.environ["HF_HOME"] = str(cache_dir)
            os.environ["HF_DATASETS_CACHE"] = str(cache_dir / "datasets")
            os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(cache_dir)
            return str(cache_dir)
        
        # Priority 3: Use cache from Docker image (set in Dockerfile) - EPHEMERAL
        # This is lower priority because it's ephemeral and re-downloads on every deploy
        # Only use if Railway persistent volume is not available
        image_cache = os.getenv("SENTENCE_TRANSFORMERS_HOME")
        if image_cache:
            cache_dir = Path(image_cache)
            if cache_dir.exists():
                logger.info(f"⚠️ Using model cache from Docker image: {cache_dir} (EPHEMERAL - will re-download on deploy)")
                logger.warning(f"⚠️ To prevent re-downloading, use Railway persistent volume at /app/hf_cache")
                return str(cache_dir)
            else:
                logger.warning(f"Image cache path does not exist: {cache_dir}, falling back to other options")
        
        # Priority 4: Check for custom cache path
        custom_cache = os.getenv("HF_CACHE_PATH")
        if custom_cache:
            cache_dir = Path(custom_cache)
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using custom cache path: {cache_dir}")
            return str(cache_dir)
        
        # Priority 4: Use TRANSFORMERS_CACHE or HF_HOME if set (from Dockerfile ENV)
        transformers_cache = os.getenv("TRANSFORMERS_CACHE")
        if transformers_cache:
            cache_dir = Path(transformers_cache)
            if cache_dir.exists():
                logger.info(f"Using TRANSFORMERS_CACHE: {cache_dir}")
                return str(cache_dir)
        
        hf_home = os.getenv("HF_HOME")
        if hf_home:
            cache_dir = Path(hf_home)
            if cache_dir.exists():
                logger.info(f"Using HF_HOME: {cache_dir}")
                return str(cache_dir)
        
        # Default: use system cache (ephemeral on Railway)
        # This will be /root/.cache/huggingface/ on Railway (ephemeral)
        logger.warning(
            "No persistent cache path configured. Model will be re-downloaded on restart. "
            "Set SENTENCE_TRANSFORMERS_HOME=/app/.model_cache or PERSISTENT_CACHE_PATH=/app/hf_cache environment variable."
        )
        return None
    
    def _normalize_query(self, text: str) -> str:
        """Normalize query text for cache key (lowercase, strip whitespace)"""
        return text.lower().strip()
    
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key from normalized text"""
        normalized = self._normalize_query(text)
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()
    
    def encode_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text
        
        OPTIMIZATION: Uses in-memory cache and Redis cache for single text queries to avoid redundant encoding
        
        Args:
            text: Single text string or list of text strings
            
        Returns:
            Single embedding vector or list of embedding vectors
        """
        try:
            # OPTIMIZATION: Check Redis cache first (for single text queries)
            if isinstance(text, str) and REDIS_CACHE_AVAILABLE:
                cache_service = get_cache_service()
                if cache_service:
                    cached_embedding = cache_service.get_embedding(text)
                    if cached_embedding is not None:
                        logger.debug(f"✅ Redis cache hit for embedding: {text[:50]}...")
                        # Also update in-memory cache
                        cache_key = self._get_cache_key(text)
                        self._embedding_cache[cache_key] = cached_embedding
                        return cached_embedding.copy() if isinstance(cached_embedding, list) else cached_embedding
            
            # OPTIMIZATION: Check in-memory cache for single text queries
            if isinstance(text, str):
                cache_key = self._get_cache_key(text)
                if cache_key in self._embedding_cache:
                    logger.debug(f"✅ In-memory cache hit for query: {text[:50]}...")
                    return self._embedding_cache[cache_key].copy()  # Return copy to prevent mutation
            
            # Generate embeddings
            embeddings = self.model.encode(text, convert_to_tensor=False)
            
            # OPTIMIZATION: Cache single text embeddings (both in-memory and Redis)
            if isinstance(text, str):
                embedding_list = embeddings.tolist() if hasattr(embeddings, 'tolist') else list(embeddings)
                cache_key = self._get_cache_key(text)
                
                # Update in-memory cache
                # Limit cache size (LRU eviction)
                if len(self._embedding_cache) >= self._cache_max_size:
                    # Remove oldest entry (simple FIFO, could use LRU but this is simpler)
                    oldest_key = next(iter(self._embedding_cache))
                    del self._embedding_cache[oldest_key]
                self._embedding_cache[cache_key] = embedding_list
                
                # Update Redis cache (if available)
                if REDIS_CACHE_AVAILABLE:
                    cache_service = get_cache_service()
                    if cache_service:
                        cache_service.cache_embedding(text, embedding_list)
                        logger.debug(f"✅ Cached embedding in Redis: {text[:50]}...")
                
                return embedding_list
            
            # After first encode, model files should be cached
            # Verify cache location after first use (only log once)
            if not hasattr(self, '_cache_verified_after_use'):
                self._cache_verified_after_use = True
                cache_path = self._get_cache_path()
                if cache_path:
                    cache_dir = Path(cache_path)
                    model_name_safe = self.model_name.replace("/", "_")
                    model_name_hf = self.model_name.replace("/", "--")
                    
                    # Check multiple possible cache locations
                    # HuggingFace uses: models--{model_name} format
                    # sentence-transformers uses: sentence_transformers/{model_name} format
                    # Also check for sentence-transformers specific format: models--sentence-transformers--{model_name}
                    possible_locations = [
                        cache_dir / "sentence_transformers" / model_name_safe,
                        cache_dir / "sentence_transformers" / self.model_name,
                        cache_dir / "hub" / f"models--{model_name_hf}",
                        cache_dir / f"models--{model_name_hf}",
                        cache_dir / f"models--sentence-transformers--{model_name_hf}",  # HuggingFace format for sentence-transformers
                        cache_dir / "hub" / f"models--sentence-transformers--{model_name_hf}",
                    ]
                    
                    model_found = False
                    found_location = None
                    logger.debug(f"🔍 Checking {len(possible_locations)} possible cache locations for model: {self.model_name}")
                    for loc in possible_locations:
                        logger.debug(f"  Checking: {loc} (exists: {loc.exists()})")
                        if loc.exists():
                            # Check if it's actually a model directory
                            # HuggingFace cache format: models--sentence-transformers--all-MiniLM-L6-v2/
                            #   contains: snapshots/{hash}/model files
                            if loc.is_dir():
                                # Check for model files directly or in subdirectories (HuggingFace format)
                                has_model_files = (
                                    any(loc.glob("*.json")) or 
                                    any(loc.glob("*.bin")) or 
                                    any(loc.glob("*.safetensors")) or
                                    any(loc.rglob("*.json")) or  # Check subdirectories
                                    any(loc.rglob("*.bin")) or
                                    any(loc.rglob("*.safetensors"))
                                )
                                # Also check if it's a HuggingFace cache directory (has snapshots/ subdirectory)
                                has_hf_structure = (loc / "snapshots").exists() or (loc / "refs").exists()
                                # Check if directory has any subdirectories (HuggingFace cache structure)
                                try:
                                    has_subdirs = any(loc.iterdir()) if loc.exists() else False
                                except Exception as e:
                                    logger.debug(f"  Could not check subdirs for {loc}: {e}")
                                    has_subdirs = False
                                
                                logger.debug(f"    has_model_files: {has_model_files}, has_hf_structure: {has_hf_structure}, has_subdirs: {has_subdirs}")
                                
                                if has_model_files or has_hf_structure or has_subdirs:
                                    # Additional check: if it's a HuggingFace cache, verify it has content
                                    if has_hf_structure:
                                        # Check if snapshots directory has any content
                                        snapshots_dir = loc / "snapshots"
                                        if snapshots_dir.exists():
                                            try:
                                                snapshots = list(snapshots_dir.iterdir())
                                                if snapshots:
                                                    model_found = True
                                                    found_location = loc
                                                    logger.info(f"✅ Found HuggingFace cache structure: {loc} with {len(snapshots)} snapshot(s)")
                                                    break
                                            except Exception as e:
                                                logger.debug(f"  Could not list snapshots for {snapshots_dir}: {e}")
                                    # Or if it's a direct model directory with subdirs or model files
                                    elif has_subdirs or has_model_files:
                                        model_found = True
                                        found_location = loc
                                        logger.info(f"✅ Found model directory: {loc} (has_subdirs: {has_subdirs}, has_model_files: {has_model_files})")
                                        break
                    
                    if model_found:
                        logger.info(f"✅ After first use: Model files cached in persistent volume: {found_location}")
                    else:
                        logger.warning(f"⚠️ After first use: Model files NOT in persistent volume. Expected: {possible_locations[0]}")
                        # Check HuggingFace default cache
                        try:
                            from transformers import file_utils
                            hf_cache = file_utils.default_cache_path
                            logger.info(f"📦 Checking HuggingFace default cache: {hf_cache}")
                            if hf_cache.exists():
                                # Check if model is in HF cache
                                hf_model_path = hf_cache / f"models--{model_name_hf}"
                                if hf_model_path.exists():
                                    logger.warning(f"⚠️ Model is in HuggingFace default cache (NOT persistent): {hf_model_path}")
                                else:
                                    logger.warning(f"⚠️ Model not found in HuggingFace cache either: {hf_cache}")
                        except Exception as e:
                            logger.debug(f"Could not check HuggingFace cache: {e}")
                        
                        # List what's actually in the persistent volume cache directory
                        try:
                            if cache_dir.exists():
                                contents = list(cache_dir.iterdir())
                                logger.info(f"📁 Contents of persistent volume cache: {[str(c.name) for c in contents[:10]]}")
                        except Exception as e:
                            logger.debug(f"Could not list cache directory: {e}")
            
            # Convert to list if single text
            # Note: sentence-transformers may print "Batches: 100%|..." progress bar
            # This is from tqdm and is normal behavior - we suppress it via TQDM_DISABLE env var
            if isinstance(text, str):
                return embeddings.tolist()
            else:
                return embeddings.tolist()
                
        except Exception as e:
            logger.error(f"Failed to encode text: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings
        
        Returns:
            int: Embedding dimension
        """
        try:
            # Get dimension by encoding a single word
            test_embedding = self.encode_text("test")
            return len(test_embedding)
        except Exception as e:
            logger.error(f"Failed to get embedding dimension: {e}")
            return 384  # Default for multi-qa-MiniLM-L6-dot-v1 (384 dimensions)
    
    def batch_encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Encode texts in batches for efficiency
        
        Args:
            texts: List of text strings to encode
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        try:
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = self.encode_text(batch)
                all_embeddings.extend(batch_embeddings)
            
            logger.info(f"Encoded {len(texts)} texts in batches of {batch_size}")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Failed to batch encode texts: {e}")
            raise
