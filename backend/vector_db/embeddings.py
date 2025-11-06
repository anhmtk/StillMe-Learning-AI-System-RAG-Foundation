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
        Prioritizes persistent volume path if available.
        
        Returns:
            Cache path string or None to use default
        """
        # Check for Railway persistent volume path (from railway.json: /app/hf_cache)
        persistent_cache = os.getenv("PERSISTENT_CACHE_PATH")
        if persistent_cache:
            # If path ends with /hf_cache, use it directly, otherwise append /huggingface
            if persistent_cache.endswith("/hf_cache") or persistent_cache.endswith("\\hf_cache"):
                cache_dir = Path(persistent_cache)
            else:
                cache_dir = Path(persistent_cache) / "huggingface"
            cache_dir.mkdir(parents=True, exist_ok=True)
            return str(cache_dir)
        
        # Check for custom cache path
        custom_cache = os.getenv("HF_CACHE_PATH")
        if custom_cache:
            cache_dir = Path(custom_cache)
            cache_dir.mkdir(parents=True, exist_ok=True)
            return str(cache_dir)
        
        # Default: use system cache (ephemeral on Railway)
        # This will be /root/.cache/huggingface/ on Railway (ephemeral)
        logger.warning(
            "No persistent cache path configured. Model will be re-downloaded on restart. "
            "Set PERSISTENT_CACHE_PATH=/app/hf_cache or HF_CACHE_PATH environment variable."
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
