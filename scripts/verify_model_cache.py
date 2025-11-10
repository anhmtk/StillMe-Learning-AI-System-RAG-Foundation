#!/usr/bin/env python3
"""
Script to verify model caching is working correctly
Checks if all-MiniLM-L6-v2 model is cached in persistent volume
"""

import os
import sys
from pathlib import Path

def verify_model_cache():
    """Verify model cache exists and is accessible"""
    print("Verifying Model Cache Setup...")
    print("=" * 60)
    
    # Check environment variables
    print("\n1. Environment Variables:")
    env_vars = [
        "PERSISTENT_CACHE_PATH",
        "SENTENCE_TRANSFORMERS_HOME",
        "TRANSFORMERS_CACHE",
        "HF_HOME"
    ]
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"   [OK] {var} = {value}")
        else:
            print(f"   [WARN] {var} = NOT SET")
    
    # Check cache paths
    print("\n2. Cache Paths:")
    cache_paths = [
        Path("/app/hf_cache"),
        Path("/app/.model_cache"),
        Path.home() / ".cache" / "huggingface",
    ]
    
    for cache_path in cache_paths:
        if cache_path.exists():
            print(f"   [OK] {cache_path} exists")
            # Check if it's writable
            try:
                test_file = cache_path / ".test_write"
                test_file.write_text("test")
                test_file.unlink()
                print(f"      [OK] Writable")
            except Exception as e:
                print(f"      [ERROR] Not writable: {e}")
        else:
            print(f"   [WARN] {cache_path} does not exist")
    
    # Check model files
    print("\n3. Model Files (all-MiniLM-L6-v2):")
    model_name = "all-MiniLM-L6-v2"
    model_name_safe = model_name.replace("/", "_")
    model_name_hf = model_name.replace("/", "--")
    
    possible_locations = [
        Path("/app/hf_cache") / "sentence_transformers" / model_name_safe,
        Path("/app/hf_cache") / "sentence_transformers" / model_name,
        Path("/app/hf_cache") / f"models--{model_name_hf}",
        Path("/app/.model_cache") / "sentence_transformers" / model_name_safe,
        Path.home() / ".cache" / "huggingface" / "hub" / f"models--{model_name_hf}",
    ]
    
    found = False
    for model_path in possible_locations:
        if model_path.exists():
            print(f"   [OK] Model found at: {model_path}")
            # Check size
            if model_path.is_dir():
                total_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
                size_mb = total_size / (1024 * 1024)
                print(f"      Size: {size_mb:.2f} MB")
            found = True
            break
    
    if not found:
        print(f"   [WARN] Model not found in any cache location")
        print(f"      Model will be downloaded on first use")
        print(f"      Expected location: /app/hf_cache/sentence_transformers/{model_name_safe}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    if found:
        print("   [OK] Model is cached - will NOT re-download on deploy")
    else:
        print("   [WARN] Model not cached - will download on first use")
        print("   [INFO] After first download, model will be cached for future deploys")
    
    print("\nTo enable persistent caching:")
    print("   1. Set PERSISTENT_CACHE_PATH=/app/hf_cache in Railway")
    print("   2. Verify persistent volume 'stillme-hf-cache' exists")
    print("   3. After first deploy, model will be cached")

if __name__ == "__main__":
    verify_model_cache()

