#!/usr/bin/env python3
"""
ChromaDB ONNX warmup script for Docker build.
Pre-downloads ONNX models during build to avoid downloading on first query.

This script is safe to fail - it will not break the Docker build.
"""
import os
import sys

try:
    import chromadb
    from chromadb.config import Settings
    
    # CRITICAL: Set HOME to /app so ChromaDB uses /app/.cache/chroma/onnx_models/
    # This ensures ONNX models are cached in the image
    os.environ['HOME'] = '/app'
    
    # Ensure cache directory exists
    chroma_cache_dir = '/app/.cache/chroma'
    os.makedirs(chroma_cache_dir, exist_ok=True)
    print(f'Created ChromaDB cache directory: {chroma_cache_dir}')
    
    # CRITICAL: Use PersistentClient (not Client) to trigger ONNX model download
    # PersistentClient will download ONNX models when needed
    # Client (in-memory) does NOT trigger ONNX download
    client = chromadb.PersistentClient(
        path=chroma_cache_dir,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    print('Created ChromaDB PersistentClient')
    
    # Create temporary collection for warmup
    collection = client.create_collection('_preload_onnx')
    print('Created temporary collection for warmup')
    
    # Add dummy document WITHOUT embeddings (let ChromaDB generate embeddings using ONNX)
    # This will trigger ONNX model download if not already cached
    collection.add(
        ids=['warmup_doc'],
        documents=['This is a warmup document to trigger ONNX model download for all-MiniLM-L6-v2']
    )
    print('Added warmup document (will trigger ONNX model download)')
    
    # Query WITHOUT embeddings (let ChromaDB generate query embedding using ONNX)
    # This ensures ONNX model is actually used and cached
    try:
        results = collection.query(
            query_texts=['warmup query to trigger ONNX model'],
            n_results=1
        )
        print('✅ ChromaDB query executed - ONNX model should be cached')
        print(f'   Query returned {len(results["ids"][0]) if results.get("ids") else 0} results')
    except Exception as e:
        print(f'⚠️ Query executed but may not have triggered ONNX download: {e}')
    
    # Clean up
    client.delete_collection('_preload_onnx')
    print('✅ ChromaDB ONNX warmup done')
    
    # Verify ONNX model was downloaded
    onnx_model_path = os.path.join(chroma_cache_dir, 'onnx_models', 'all-MiniLM-L6-v2')
    if os.path.exists(onnx_model_path):
        print(f'✅ ONNX model verified at: {onnx_model_path}')
    else:
        print(f'⚠️ ONNX model not found at: {onnx_model_path} (may download on first real use)')
    
except Exception as e:
    # Never fail the build - just log and continue
    print(f'⚠️ Chroma warmup skipped: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(0)  # Exit with 0 to not fail build

