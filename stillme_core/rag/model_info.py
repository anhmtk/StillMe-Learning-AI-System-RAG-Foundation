"""
Model Information for StillMe

Provides accurate model information that StillMe can use in responses.
This ensures StillMe always mentions the correct model names and versions.
"""

# CRITICAL: This is the SINGLE SOURCE OF TRUTH for embedding model information
# If model changes, update this file and re-run foundational knowledge update

EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_MODEL_DIMENSIONS = 384
EMBEDDING_MODEL_DESCRIPTION = "sentence-transformers model optimized for multilingual Q&A retrieval, supports 50+ languages"

def get_embedding_model_info() -> dict:
    """
    Get current embedding model information.
    
    Returns:
        Dictionary with model information:
        - name: Model name
        - dimensions: Embedding dimensions
        - description: Human-readable description
    """
    return {
        "name": EMBEDDING_MODEL_NAME,
        "dimensions": EMBEDDING_MODEL_DIMENSIONS,
        "description": EMBEDDING_MODEL_DESCRIPTION
    }

def get_embedding_model_display_name() -> str:
    """
    Get formatted model name for display in responses.
    
    Returns:
        Formatted string: "paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions, ...)"
    """
    return f"{EMBEDDING_MODEL_NAME} ({EMBEDDING_MODEL_DIMENSIONS} dimensions, {EMBEDDING_MODEL_DESCRIPTION})"

