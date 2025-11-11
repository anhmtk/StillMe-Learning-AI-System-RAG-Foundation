"""
Model Cache Manager - CRITICAL for preventing model re-downloads on Railway
Ensures all-MiniLM-L6-v2 model is cached in persistent volume and verified before loading
"""

import os
import shutil
import logging
from pathlib import Path
from typing import Optional, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheStatus:
    """Cache status information"""
    exists: bool
    path: Optional[str]
    size_mb: float
    model_files_found: bool
    is_persistent: bool
    is_writable: bool
    error: Optional[str] = None


class ModelManager:
    """
    Model Manager with comprehensive cache control and verification.
    
    CRITICAL: This class ensures models are cached in persistent volumes
    to prevent re-downloading on every Railway deploy.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize ModelManager
        
        Args:
            model_name: Name of the model to manage
        """
        self.model_name = model_name
        self.model_name_safe = model_name.replace("/", "_")
        self.model_name_hf = model_name.replace("/", "--")
        
        # Setup environment FIRST (before any imports)
        self.setup_cache_environment()
        
        # Verify cache exists
        self.cache_status = self.verify_cache_exists()
        
        # Log cache status
        self._log_cache_status()
    
    def setup_cache_environment(self) -> None:
        """
        SET CRITICAL ENVIRONMENT VARIABLES BEFORE ANY MODEL IMPORTS.
        
        HuggingFace/transformers resolves cache path on first import,
        so we MUST set env vars before importing SentenceTransformer.
        """
        # Priority 1: Railway persistent volume (HIGHEST PRIORITY)
        railway_cache = Path("/app/hf_cache")
        if railway_cache.exists() or railway_cache.parent.exists():
            cache_path = railway_cache
            cache_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Railway persistent volume found: {cache_path}")
        else:
            # Priority 2: Check PERSISTENT_CACHE_PATH env var
            persistent_cache = os.getenv("PERSISTENT_CACHE_PATH")
            if persistent_cache:
                cache_path = Path(persistent_cache)
                cache_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Using PERSISTENT_CACHE_PATH: {cache_path}")
            else:
                # Priority 3: Docker image cache (ephemeral)
                cache_path = Path("/app/.model_cache")
                cache_path.mkdir(parents=True, exist_ok=True)
                logger.warning(f"⚠️ Using Docker image cache (EPHEMERAL): {cache_path}")
                logger.warning(f"⚠️ Model will be re-downloaded on deploy. Set Railway persistent volume at /app/hf_cache")
        
        # CRITICAL: Set ALL environment variables
        os.environ["HF_HOME"] = str(cache_path)
        os.environ["TRANSFORMERS_CACHE"] = str(cache_path)
        os.environ["HF_DATASETS_CACHE"] = str(cache_path / "datasets")
        os.environ["SENTENCE_TRANSFORMERS_HOME"] = str(cache_path)
        os.environ["HF_HUB_CACHE"] = str(cache_path / "hub")
        
        logger.info(f"✅ Environment variables set:")
        logger.info(f"   HF_HOME={cache_path}")
        logger.info(f"   TRANSFORMERS_CACHE={cache_path}")
        logger.info(f"   SENTENCE_TRANSFORMERS_HOME={cache_path}")
        
        self.cache_path = cache_path
    
    def verify_cache_exists(self) -> CacheStatus:
        """
        Verify model cache exists and is accessible.
        
        Returns:
            CacheStatus with detailed information
        """
        try:
            cache_dir = Path(self.cache_path)
            
            # Check if cache directory exists
            if not cache_dir.exists():
                return CacheStatus(
                    exists=False,
                    path=str(cache_dir),
                    size_mb=0.0,
                    model_files_found=False,
                    is_persistent=False,
                    is_writable=False,
                    error=f"Cache directory does not exist: {cache_dir}"
                )
            
            # Check if writable
            is_writable = os.access(cache_dir, os.W_OK)
            if not is_writable:
                logger.warning(f"⚠️ Cache directory is not writable: {cache_dir}")
            
            # Check if persistent (Railway volume)
            is_persistent = str(cache_dir) == "/app/hf_cache" and cache_dir.exists()
            
            # Check for model files in multiple possible locations
            possible_paths = [
                # Sentence-transformers format
                cache_dir / "sentence_transformers" / self.model_name_safe,
                cache_dir / "sentence_transformers" / self.model_name,
                # HuggingFace hub format
                cache_dir / "hub" / f"models--{self.model_name_hf}",
                cache_dir / f"models--{self.model_name_hf}",
                cache_dir / f"models--sentence-transformers--{self.model_name_hf}",
                cache_dir / "hub" / f"models--sentence-transformers--{self.model_name_hf}",
            ]
            
            model_files_found = False
            found_path = None
            total_size = 0.0
            
            for model_path in possible_paths:
                if model_path.exists():
                    # Check if it's actually a model directory
                    if model_path.is_dir():
                        # Check for model files
                        has_model_files = (
                            any(model_path.glob("*.json")) or
                            any(model_path.glob("*.bin")) or
                            any(model_path.glob("*.safetensors")) or
                            any(model_path.rglob("*.json")) or
                            any(model_path.rglob("*.bin")) or
                            any(model_path.rglob("*.safetensors"))
                        )
                        
                        # Check for HuggingFace cache structure
                        has_hf_structure = (model_path / "snapshots").exists()
                        
                        if has_model_files or has_hf_structure:
                            model_files_found = True
                            found_path = model_path
                            
                            # Calculate size
                            try:
                                for file in model_path.rglob("*"):
                                    if file.is_file():
                                        total_size += file.stat().st_size
                            except Exception as e:
                                logger.debug(f"Could not calculate size for {model_path}: {e}")
                            
                            break
            
            # If not found in expected locations, check if cache_dir has any model-related content
            if not model_files_found:
                try:
                    cache_contents = list(cache_dir.iterdir())
                    has_model_content = any(
                        (cache_dir / item).is_dir() and (
                            "sentence_transformers" in str(item) or
                            "hub" in str(item) or
                            "models--" in str(item)
                        )
                        for item in cache_contents
                    )
                    if has_model_content:
                        # Calculate total cache size
                        try:
                            for item in cache_contents:
                                item_path = cache_dir / item
                                if item_path.is_dir():
                                    for file in item_path.rglob("*"):
                                        if file.is_file():
                                            total_size += file.stat().st_size
                        except Exception:
                            pass
                except Exception:
                    pass
            
            size_mb = total_size / (1024 * 1024)
            
            return CacheStatus(
                exists=True,
                path=str(found_path) if found_path else str(cache_dir),
                size_mb=size_mb,
                model_files_found=model_files_found,
                is_persistent=is_persistent,
                is_writable=is_writable,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Error verifying cache: {e}")
            return CacheStatus(
                exists=False,
                path=str(self.cache_path) if hasattr(self, 'cache_path') else None,
                size_mb=0.0,
                model_files_found=False,
                is_persistent=False,
                is_writable=False,
                error=str(e)
            )
    
    def copy_model_from_image_cache(self) -> bool:
        """
        Copy model from Docker image cache to persistent volume if needed.
        
        This is useful when:
        - Model is pre-downloaded in Docker image at /app/.model_cache
        - Persistent volume at /app/hf_cache is empty
        - We want to copy model to persistent volume to avoid re-download
        
        Returns:
            True if copy was successful or not needed, False if failed
        """
        # Only copy if persistent volume exists but is empty
        persistent_volume = Path("/app/hf_cache")
        image_cache = Path("/app/.model_cache")
        
        if not persistent_volume.exists():
            logger.debug("Persistent volume does not exist, skipping copy")
            return True
        
        if not image_cache.exists():
            logger.debug("Image cache does not exist, skipping copy")
            return True
        
        # Check if persistent volume already has model
        if self.cache_status.model_files_found and self.cache_status.is_persistent:
            logger.info("✅ Persistent volume already has model, skipping copy")
            return True
        
        # Check if image cache has model
        # Model can be cached in multiple formats by HuggingFace/sentence-transformers
        image_model_paths = [
            # Sentence-transformers format
            image_cache / "sentence_transformers" / self.model_name_safe,
            image_cache / "sentence_transformers" / self.model_name,
            # HuggingFace hub format (full format)
            image_cache / "hub" / f"models--sentence-transformers--{self.model_name_hf}",
            image_cache / "hub" / f"models--{self.model_name_hf}",
            image_cache / f"models--sentence-transformers--{self.model_name_hf}",
            image_cache / f"models--{self.model_name_hf}",
        ]
        
        source_path = None
        for path in image_model_paths:
            if path.exists():
                # Verify it has model files
                if any(path.rglob("*.json")) or any(path.rglob("*.bin")) or any(path.rglob("*.safetensors")):
                    source_path = path
                    break
        
        if not source_path:
            logger.debug("Image cache does not have model, skipping copy")
            return True
        
        # Copy to persistent volume
        try:
            logger.info(f"📦 Copying model from image cache to persistent volume...")
            logger.info(f"   Source: {source_path}")
            logger.info(f"   Destination: {persistent_volume}")
            
            # Determine destination path based on source structure
            # Preserve the same structure as source (hub/ or sentence_transformers/)
            if "hub" in str(source_path):
                # HuggingFace hub format - preserve full path structure
                if "models--sentence-transformers--" in str(source_path):
                    dest_path = persistent_volume / "hub" / f"models--sentence-transformers--{self.model_name_hf}"
                else:
                    dest_path = persistent_volume / "hub" / f"models--{self.model_name_hf}"
            elif "sentence_transformers" in str(source_path):
                dest_path = persistent_volume / "sentence_transformers" / self.model_name_safe
            else:
                # Fallback: use source name
                dest_path = persistent_volume / source_path.name
            
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy directory
            if dest_path.exists():
                logger.info(f"   Destination already exists, skipping: {dest_path}")
                return True
            
            shutil.copytree(source_path, dest_path)
            logger.info(f"✅ Model copied successfully to: {dest_path}")
            
            # Re-verify cache
            self.cache_status = self.verify_cache_exists()
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to copy model from image cache: {e}")
            return False
    
    def _log_cache_status(self) -> None:
        """Log cache status for debugging"""
        status = self.cache_status
        
        if status.exists:
            logger.info("=" * 60)
            logger.info("📦 MODEL CACHE STATUS")
            logger.info("=" * 60)
            logger.info(f"Cache Path: {status.path}")
            logger.info(f"Size: {status.size_mb:.2f} MB")
            logger.info(f"Model Files Found: {'✅ YES' if status.model_files_found else '❌ NO'}")
            logger.info(f"Persistent Volume: {'✅ YES' if status.is_persistent else '❌ NO (EPHEMERAL)'}")
            logger.info(f"Writable: {'✅ YES' if status.is_writable else '❌ NO'}")
            
            if status.model_files_found:
                logger.info("✅ CACHE FOUND: Model loaded from persistent cache")
                logger.info("⏱️  Load time: ~1-2 seconds (no download needed)")
            else:
                logger.warning("⚠️ CACHE MISS: Model will be downloaded on first use")
                logger.warning("⏱️  Download time: ~10-15 minutes")
            
            if status.error:
                logger.error(f"Error: {status.error}")
            
            logger.info("=" * 60)
        else:
            logger.error("❌ CACHE VERIFICATION FAILED")
            logger.error(f"Error: {status.error}")
    
    def get_cache_info(self) -> Dict:
        """Get cache information as dictionary"""
        return {
            "cache_path": str(self.cache_path),
            "model_name": self.model_name,
            "status": {
                "exists": self.cache_status.exists,
                "path": self.cache_status.path,
                "size_mb": round(self.cache_status.size_mb, 2),
                "model_files_found": self.cache_status.model_files_found,
                "is_persistent": self.cache_status.is_persistent,
                "is_writable": self.cache_status.is_writable,
                "error": self.cache_status.error
            },
            "environment": {
                "HF_HOME": os.getenv("HF_HOME"),
                "TRANSFORMERS_CACHE": os.getenv("TRANSFORMERS_CACHE"),
                "SENTENCE_TRANSFORMERS_HOME": os.getenv("SENTENCE_TRANSFORMERS_HOME"),
                "HF_HUB_CACHE": os.getenv("HF_HUB_CACHE"),
            }
        }


def verify_model_cache(model_name: str = "all-MiniLM-L6-v2") -> CacheStatus:
    """
    Standalone function to verify model cache.
    
    Args:
        model_name: Name of the model to verify
        
    Returns:
        CacheStatus with detailed information
    """
    manager = ModelManager(model_name=model_name)
    return manager.cache_status

