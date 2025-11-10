#!/usr/bin/env python3
"""
Model warmup script for Docker build.
Pre-downloads all-MiniLM-L6-v2 model during build to avoid downloading on first query.

This script is safe to fail - it will not break the Docker build.
"""
import os
import sys
from pathlib import Path

try:
    # CRITICAL: Set environment variables FIRST before importing SentenceTransformer
    # HuggingFace/transformers resolves cache path on first import
    cache_dir = '/app/.model_cache'
    
    os.environ['HF_HOME'] = cache_dir
    os.environ['TRANSFORMERS_CACHE'] = cache_dir
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = cache_dir
    os.environ['HF_HUB_CACHE'] = os.path.join(cache_dir, 'hub')
    
    # Ensure cache directory exists
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    print(f'Created model cache directory: {cache_dir}')
    
    print('🏗️ Pre-downloading model all-MiniLM-L6-v2...')
    from sentence_transformers import SentenceTransformer
    
    model = SentenceTransformer('all-MiniLM-L6-v2', cache_folder=cache_dir)
    print('✅ Model pre-downloaded to /app/.model_cache')
    
    # Verify cache size
    cache_path = Path(cache_dir)
    if cache_path.exists():
        total_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        print(f'📦 Cache size: {size_mb:.2f} MB')
        
        # List cache contents for debugging
        print(f'📁 Cache directory contents:')
        for item in sorted(cache_path.iterdir()):
            if item.is_dir():
                print(f'   📂 {item.name}/')
            else:
                size_kb = item.stat().st_size / 1024
                print(f'   📄 {item.name} ({size_kb:.2f} KB)')
    
    print('✅ Model warmup completed successfully')
    
except Exception as e:
    print(f'⚠️ Model warmup failed (non-critical): {e}')
    import traceback
    traceback.print_exc()
    # Don't fail the build - this is non-critical
    sys.exit(0)  # Exit with 0 to not fail Docker build

