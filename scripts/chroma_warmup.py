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
    
    # Ensure cache directory exists
    os.makedirs('/app/.cache/chroma', exist_ok=True)
    
    # Create ChromaDB client
    client = chromadb.Client()
    
    # Create temporary collection for warmup
    collection = client.create_collection('_preload_onnx')
    
    # Add dummy document with embeddings
    collection.add(ids=['d'], documents=['d'], embeddings=[[0.1]*384])
    
    # Query to potentially trigger ONNX model loading
    try:
        results = collection.query(query_embeddings=[[0.1]*384], n_results=1)
        print('ChromaDB query executed - ONNX model may be cached')
    except Exception as e:
        print(f'Query executed (ONNX may download on first real use): {e}')
    
    # Clean up
    client.delete_collection('_preload_onnx')
    print('ChromaDB ONNX warmup done')
    
except Exception as e:
    # Never fail the build - just log and continue
    print(f'Chroma warmup skipped: {e}')
    sys.exit(0)  # Exit with 0 to not fail build

