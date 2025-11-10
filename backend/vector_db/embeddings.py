"""
Embedding Service for StillMe
Handles text embedding generation using sentence-transformers
"""

from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging
import os
from pathlib import Path

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
        cache_path = self._get_cache_path()
        if cache_path:
            os.environ["TRANSFORMERS_CACHE"] = str(cache_path)
            os.environ["HF_HOME"] = str(cache_path)
            logger.info(f"Using persistent cache path: {cache_path}")
        
        try:
            # SentenceTransformer will use TRANSFORMERS_CACHE/HF_HOME env vars
            self.model = SentenceTransformer(model_name, cache_folder=cache_path)
            logger.info(f"Embedding model '{model_name}' loaded successfully")
            if cache_path:
                logger.info(f"Model cached at: {cache_path}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _get_cache_path(self) -> Union[str, None]:
        """
        Get cache path for HuggingFace models.
        Prioritizes model cache from Docker image (SENTENCE_TRANSFORMERS_HOME),
        then persistent volume path, then custom cache path.
        
        Returns:
            Cache path string or None to use default
        """
        # Priority 1: Use cache from Docker image (set in Dockerfile)
        # This ensures model is loaded from image, not re-downloaded
        image_cache = os.getenv("SENTENCE_TRANSFORMERS_HOME")
        if image_cache:
            cache_dir = Path(image_cache)
            if cache_dir.exists():
                logger.info(f"Using model cache from Docker image: {cache_dir}")
                return str(cache_dir)
            else:
                logger.warning(f"Image cache path does not exist: {cache_dir}, falling back to other options")
        
        # Priority 2: Check for Railway persistent volume path (from railway.json: /app/hf_cache)
        # First check env var, then check if persistent volume mount exists
        persistent_cache = os.getenv("PERSISTENT_CACHE_PATH")
        if persistent_cache:
            # If path ends with /hf_cache, use it directly, otherwise append /huggingface
            if persistent_cache.endswith("/hf_cache") or persistent_cache.endswith("\\hf_cache"):
                cache_dir = Path(persistent_cache)
            else:
                cache_dir = Path(persistent_cache) / "huggingface"
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using persistent volume cache: {cache_dir}")
            return str(cache_dir)
        
        # Priority 2b: Check if Railway persistent volume mount exists directly
        # Railway mounts /app/hf_cache as persistent volume
        railway_cache = Path("/app/hf_cache")
        if railway_cache.exists() or railway_cache.parent.exists():
            cache_dir = railway_cache
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Using Railway persistent volume cache: {cache_dir}")
            return str(cache_dir)
        
        # Priority 3: Check for custom cache path
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
