"""
Fix Embedding Model Cache Path Mismatch

CRITICAL: This script fixes the cache path mismatch issue where:
- Model is downloaded in HuggingFace format: /app/hf_cache/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2
- But SentenceTransformer looks for: /app/hf_cache/sentence_transformers/paraphrase-multilingual-MiniLM-L12-v2

Solution: Create symlink or copy from HuggingFace format to sentence-transformers format
"""

import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def fix_embedding_model_cache(model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> bool:
    """
    Fix embedding model cache path mismatch.
    
    Args:
        model_name: Name of the model to fix
        
    Returns:
        True if fix was successful or not needed, False if failed
    """
    try:
        cache_base = Path("/app/hf_cache")
        if not cache_base.exists():
            logger.warning(f"⚠️ Cache base directory does not exist: {cache_base}")
            return False
        
        # Model name variations
        model_name_safe = model_name.replace("/", "_")
        model_name_hf = model_name.replace("/", "--")
        
        # HuggingFace format path (where model might be downloaded)
        hf_paths = [
            cache_base / f"models--sentence-transformers--{model_name_hf}",
            cache_base / "hub" / f"models--sentence-transformers--{model_name_hf}",
            cache_base / f"models--{model_name_hf}",
            cache_base / "hub" / f"models--{model_name_hf}",
        ]
        
        # Sentence-transformers format path (where SentenceTransformer looks)
        st_path = cache_base / "sentence_transformers" / model_name_safe
        
        # Find HuggingFace format cache
        hf_source = None
        for hf_path in hf_paths:
            if hf_path.exists():
                # Verify it has model files
                if any(hf_path.rglob("*.json")) or any(hf_path.rglob("*.bin")) or any(hf_path.rglob("*.safetensors")):
                    hf_source = hf_path
                    logger.info(f"✅ Found HuggingFace format cache: {hf_source}")
                    break
        
        if not hf_source:
            logger.info("ℹ️ HuggingFace format cache not found - model may not be downloaded yet")
            return True  # Not an error, just not downloaded yet
        
        # Check if sentence-transformers format already exists
        if st_path.exists():
            logger.info(f"✅ Sentence-transformers format cache already exists: {st_path}")
            return True
        
        # Create sentence_transformers directory
        st_path.parent.mkdir(parents=True, exist_ok=True)
        
        # CRITICAL: For HuggingFace format, we need to extract the actual model files
        # HuggingFace cache structure: models--{name}/snapshots/{hash}/model files
        # Sentence-transformers expects: sentence_transformers/{name}/model files directly
        
        # Check if it's HuggingFace format with snapshots
        snapshots_dir = hf_source / "snapshots"
        if snapshots_dir.exists():
            # Find the latest snapshot
            snapshots = sorted(snapshots_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
            if snapshots:
                latest_snapshot = snapshots[0]
                logger.info(f"📦 Found HuggingFace snapshot: {latest_snapshot}")
                
                # Copy model files from snapshot to sentence-transformers format
                logger.info(f"📦 Copying model files from HuggingFace format to sentence-transformers format...")
                logger.info(f"   Source: {latest_snapshot}")
                logger.info(f"   Destination: {st_path}")
                
                # Copy all files from snapshot
                shutil.copytree(latest_snapshot, st_path, dirs_exist_ok=True)
                logger.info(f"✅ Successfully copied model files to: {st_path}")
                return True
            else:
                logger.warning(f"⚠️ No snapshots found in: {snapshots_dir}")
        else:
            # Direct model files (not HuggingFace snapshot format)
            # Try to copy or symlink
            logger.info(f"📦 Model files are in direct format, creating symlink...")
            logger.info(f"   Source: {hf_source}")
            logger.info(f"   Destination: {st_path}")
            
            try:
                # Try symlink first (more efficient)
                if not st_path.exists():
                    os.symlink(hf_source, st_path)
                    logger.info(f"✅ Created symlink: {st_path} -> {hf_source}")
                    return True
            except OSError as e:
                # Symlink failed (might not be supported on all systems)
                logger.warning(f"⚠️ Symlink failed: {e}, trying copy instead...")
                shutil.copytree(hf_source, st_path, dirs_exist_ok=True)
                logger.info(f"✅ Copied model files to: {st_path}")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Failed to fix embedding cache: {e}")
        return False


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Fix cache
    success = fix_embedding_model_cache()
    if success:
        print("✅ Embedding cache fix completed successfully")
    else:
        print("❌ Embedding cache fix failed - check logs for details")

