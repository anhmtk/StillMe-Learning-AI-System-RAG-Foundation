"""
Fix Embedding Model Cache Path Mismatch - EMERGENCY FIX WITH DETAILED DEBUG

CRITICAL: This script fixes the cache path mismatch issue where:
- Model is downloaded in HuggingFace format: /app/hf_cache/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2
- But SentenceTransformer looks for: /app/hf_cache/sentence_transformers/paraphrase-multilingual-MiniLM-L12-v2

Solution: Multiple fallback strategies with detailed logging
"""

import os
import shutil
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def fix_embedding_model_cache(model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> bool:
    """
    Fix embedding model cache path mismatch with detailed debug and multiple fallback strategies.
    
    Args:
        model_name: Name of the model to fix
        
    Returns:
        True if fix was successful or not needed, False if failed
    """
    logger.info("🚨 ===== EMERGENCY CACHE FIX WITH DEBUG =====")
    
    try:
        cache_base = Path("/app/hf_cache")
        
        # DEBUG: Log cache base
        logger.info(f"🔍 Cache base: {cache_base}")
        logger.info(f"📁 Cache base exists: {cache_base.exists()}")
        
        if not cache_base.exists():
            logger.warning(f"⚠️ Cache base directory does not exist: {cache_base}")
            # Try to create it
            try:
                cache_base.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created cache base directory: {cache_base}")
            except Exception as e:
                logger.error(f"❌ Cannot create cache base: {e}")
                return False
        
        # Model name variations
        model_name_safe = model_name.replace("/", "_")
        model_name_hf = model_name.replace("/", "--")
        
        logger.info(f"🔍 Model name: {model_name}")
        logger.info(f"🔍 Model name safe: {model_name_safe}")
        logger.info(f"🔍 Model name HF: {model_name_hf}")
        
        # HuggingFace format paths (where model might be downloaded)
        hf_paths = [
            cache_base / f"models--sentence-transformers--{model_name_hf}",
            cache_base / "hub" / f"models--sentence-transformers--{model_name_hf}",
            cache_base / f"models--{model_name_hf}",
            cache_base / "hub" / f"models--{model_name_hf}",
        ]
        
        # Sentence-transformers format path (where SentenceTransformer looks)
        st_path = cache_base / "sentence_transformers" / model_name_safe
        
        logger.info(f"🔍 ST Path: {st_path}")
        logger.info(f"📁 ST Path exists: {st_path.exists()}")
        
        # DEBUG: Check all HF paths
        hf_source = None
        for hf_path in hf_paths:
            logger.info(f"🔍 Checking HF path: {hf_path}")
            logger.info(f"   Exists: {hf_path.exists()}")
            if hf_path.exists():
                logger.info(f"   Is directory: {hf_path.is_dir()}")
                # Verify it has model files
                try:
                    has_json = any(hf_path.rglob("*.json"))
                    has_bin = any(hf_path.rglob("*.bin"))
                    has_safetensors = any(hf_path.rglob("*.safetensors"))
                    logger.info(f"   Has JSON: {has_json}, Has BIN: {has_bin}, Has SafeTensors: {has_safetensors}")
                    
                    if has_json or has_bin or has_safetensors:
                        hf_source = hf_path
                        logger.info(f"✅ Found HuggingFace format cache: {hf_source}")
                        
                        # List first few files for debug
                        try:
                            all_files = list(hf_path.rglob("*"))[:10]
                            logger.info(f"   Sample files ({len(all_files)}):")
                            for f in all_files[:5]:
                                logger.info(f"      {f.name} ({f.stat().st_size if f.is_file() else 'DIR'})")
                        except Exception as e:
                            logger.debug(f"   Cannot list files: {e}")
                        break
                except Exception as e:
                    logger.warning(f"   Error checking files: {e}")
        
        if not hf_source:
            logger.info("ℹ️ HuggingFace format cache not found - model may not be downloaded yet")
            logger.info("   This is OK - model will be downloaded on first use")
            return True  # Not an error, just not downloaded yet
        
        # Check if sentence-transformers format already exists
        if st_path.exists():
            logger.info(f"✅ Sentence-transformers format cache already exists: {st_path}")
            # Verify it has model files
            try:
                has_files = any(st_path.rglob("*.json")) or any(st_path.rglob("*.bin")) or any(st_path.rglob("*.safetensors"))
                if has_files:
                    logger.info(f"✅ ST cache verified - has model files")
                    return True
                else:
                    logger.warning(f"⚠️ ST cache exists but no model files - will recreate")
                    # Remove empty directory
                    try:
                        st_path.rmdir()
                        logger.info(f"✅ Removed empty ST cache directory")
                    except:
                        pass
            except Exception as e:
                logger.warning(f"⚠️ Error verifying ST cache: {e}")
        
        # Create sentence_transformers directory
        try:
            st_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ Created parent directory: {st_path.parent}")
        except Exception as e:
            logger.error(f"❌ Cannot create parent directory: {e}")
            return False
        
        # FIX STRATEGY 1: Check if it's HuggingFace format with snapshots
        snapshots_dir = hf_source / "snapshots"
        logger.info(f"🔍 Checking for snapshots: {snapshots_dir}")
        logger.info(f"   Snapshots dir exists: {snapshots_dir.exists()}")
        
        if snapshots_dir.exists():
            try:
                snapshots = sorted(snapshots_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
                logger.info(f"   Found {len(snapshots)} snapshot(s)")
                if snapshots:
                    latest_snapshot = snapshots[0]
                    logger.info(f"📦 Using latest snapshot: {latest_snapshot}")
                    
                    # Copy model files from snapshot to sentence-transformers format
                    logger.info(f"📦 STRATEGY 1: Copying from snapshot...")
                    logger.info(f"   Source: {latest_snapshot}")
                    logger.info(f"   Destination: {st_path}")
                    
                    try:
                        shutil.copytree(latest_snapshot, st_path, dirs_exist_ok=True)
                        logger.info(f"✅ ✅ ✅ STRATEGY 1 SUCCESS: Copied model files to: {st_path}")
                        
                        # Verify copy
                        if st_path.exists():
                            st_files = list(st_path.rglob("*"))
                            logger.info(f"✅ Verification: {len(st_files)} files in ST path")
                            return True
                    except Exception as e:
                        logger.error(f"❌ Strategy 1 failed: {e}")
            except Exception as e:
                logger.warning(f"⚠️ Error checking snapshots: {e}")
        
        # FIX STRATEGY 2: Try symlink (more efficient)
        logger.info(f"📦 STRATEGY 2: Creating symlink...")
        logger.info(f"   Source: {hf_source}")
        logger.info(f"   Destination: {st_path}")
        
        try:
            if not st_path.exists():
                os.symlink(hf_source, st_path)
                logger.info(f"✅ ✅ ✅ STRATEGY 2 SUCCESS: Created symlink: {st_path} -> {hf_source}")
                
                # Verify symlink
                if st_path.exists():
                    logger.info(f"✅ Symlink exists: {st_path.exists()}")
                    logger.info(f"✅ Is symlink: {os.path.islink(st_path)}")
                    if os.path.islink(st_path):
                        logger.info(f"✅ Symlink target: {os.readlink(st_path)}")
                    return True
                else:
                    logger.error("❌ Symlink creation failed - path still doesn't exist")
        except OSError as e:
            logger.warning(f"⚠️ Strategy 2 (symlink) failed: {e}")
            logger.info("   Trying copy instead...")
        
        # FIX STRATEGY 3: Copy entire directory
        logger.info(f"📦 STRATEGY 3: Copying entire directory...")
        logger.info(f"   Source: {hf_source}")
        logger.info(f"   Destination: {st_path}")
        
        try:
            shutil.copytree(hf_source, st_path, dirs_exist_ok=True)
            logger.info(f"✅ ✅ ✅ STRATEGY 3 SUCCESS: Copied model files to: {st_path}")
            
            # Verify copy
            if st_path.exists():
                st_files = list(st_path.rglob("*"))
                logger.info(f"✅ Verification: {len(st_files)} files in ST path")
                return True
        except Exception as e:
            logger.error(f"❌ Strategy 3 failed: {e}")
        
        # FIX STRATEGY 4: Manual copy of essential files
        logger.info(f"📦 STRATEGY 4: Manual copy of essential files...")
        essential_files = ['pytorch_model.bin', 'config.json', 'tokenizer.json', 'vocab.txt', 'tokenizer_config.json']
        
        try:
            st_path.mkdir(parents=True, exist_ok=True)
            copied_count = 0
            
            # Search for essential files in HF source
            for file_pattern in essential_files:
                found_files = list(hf_source.rglob(file_pattern))
                for src_file in found_files:
                    # Preserve relative path structure
                    rel_path = src_file.relative_to(hf_source)
                    dst_file = st_path / rel_path
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        shutil.copy2(src_file, dst_file)
                        logger.info(f"✅ Copied: {rel_path}")
                        copied_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ Cannot copy {rel_path}: {e}")
            
            if copied_count > 0:
                logger.info(f"✅ ✅ ✅ STRATEGY 4 SUCCESS: Copied {copied_count} essential files")
                return True
            else:
                logger.error("❌ Strategy 4 failed: No essential files found or copied")
        except Exception as e:
            logger.error(f"❌ Strategy 4 failed: {e}")
        
        # FIX STRATEGY 5: Set environment variables FORCEFULLY
        logger.info(f"📦 STRATEGY 5: Setting environment variables...")
        os.environ['SENTENCE_TRANSFORMERS_HOME'] = '/app/hf_cache'
        os.environ['HF_HOME'] = '/app/hf_cache'
        os.environ['TRANSFORMERS_CACHE'] = '/app/hf_cache'
        os.environ['HF_DATASETS_CACHE'] = '/app/hf_cache/datasets'
        os.environ['HF_HUB_CACHE'] = '/app/hf_cache/hub'
        
        logger.info("🌍 Environment variables set:")
        logger.info(f"   SENTENCE_TRANSFORMERS_HOME={os.environ.get('SENTENCE_TRANSFORMERS_HOME')}")
        logger.info(f"   HF_HOME={os.environ.get('HF_HOME')}")
        logger.info(f"   TRANSFORMERS_CACHE={os.environ.get('TRANSFORMERS_CACHE')}")
        
        # FIX STRATEGY 6: Create .sentence_transformers folder
        st_cache_dir = Path("/app/hf_cache/.sentence_transformers")
        if not st_cache_dir.exists():
            try:
                st_cache_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created .sentence_transformers cache dir: {st_cache_dir}")
            except Exception as e:
                logger.warning(f"⚠️ Cannot create .sentence_transformers dir: {e}")
        
        logger.info("🚨 ===== END EMERGENCY FIX =====")
        
        # Final check
        if st_path.exists():
            logger.info(f"✅ Final check: ST path exists: {st_path.exists()}")
            return True
        else:
            logger.error(f"❌ ❌ ❌ ALL STRATEGIES FAILED - ST path still doesn't exist: {st_path}")
            return False
        
    except Exception as e:
        logger.error(f"❌ ❌ ❌ CRITICAL ERROR in fix_embedding_model_cache: {e}", exc_info=True)
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

