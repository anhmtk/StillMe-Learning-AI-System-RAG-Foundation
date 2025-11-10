"""
Embedding Service for StillMe
Handles text embedding generation using sentence-transformers
"""

# CRITICAL: Set environment variables BEFORE importing SentenceTransformer
# HuggingFace/transformers resolves cache path on first import
# We must set env vars before any transformers imports
import os
from pathlib import Path

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

# NOW import SentenceTransformer (after env vars are set)
from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating text embeddings"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize embedding service
        
        Args:
            model_name: Name of the sentence transformer model to use
        """
        self.model_name = model_name
        
        # Configure cache path for persistent storage (Railway persistent volume)
        # This prevents re-downloading model on every restart/redeploy
        # CRITICAL: Get cache path FIRST, then set env vars in _get_cache_path()
        cache_path = self._get_cache_path()
        
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
                        logger.info(f"Expected model path: {st_cache_path}")
                        logger.info(f"Alternative path: {hf_hub_path}")
                        logger.info(f"💡 Model will be downloaded and cached when first used.")
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
    
    def encode_text(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Generate embeddings for text
        
        Args:
            text: Single text string or list of text strings
            
        Returns:
            Single embedding vector or list of embedding vectors
        """
        try:
            embeddings = self.model.encode(text, convert_to_tensor=False)
            
            # After first encode, model files should be cached
            # Verify cache location after first use (only log once)
            if not hasattr(self, '_cache_verified_after_use'):
                self._cache_verified_after_use = True
                cache_path = self._get_cache_path()
                if cache_path:
                    cache_dir = Path(cache_path)
                    model_name_safe = self.model_name.replace("/", "_")
                    expected_model_dir = cache_dir / "sentence_transformers" / model_name_safe
                    if expected_model_dir.exists():
                        logger.info(f"✅ After first use: Model files cached in persistent volume: {expected_model_dir}")
                    else:
                        logger.warning(f"⚠️ After first use: Model files NOT in persistent volume. Expected: {expected_model_dir}")
                        # Check HuggingFace default cache
                        try:
                            from transformers import file_utils
                            hf_cache = file_utils.default_cache_path
                            if hf_cache.exists():
                                logger.warning(f"⚠️ Model may be in HuggingFace default cache: {hf_cache}")
                        except:
                            pass
            
            # Convert to list if single text
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
            return 384  # Default for all-MiniLM-L6-v2
    
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
