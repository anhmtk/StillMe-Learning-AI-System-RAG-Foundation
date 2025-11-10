"""
Debug endpoints for monitoring cache status, model status, and environment
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/debug", tags=["debug"])


@router.get("/cache-status")
async def get_cache_status() -> Dict[str, Any]:
    """
    Get cache status information.
    
    Returns:
        Cache status including path, size, and verification results
    """
    try:
        from backend.utils.model_cache import ModelManager, verify_model_cache
        
        # Get cache status
        cache_status = verify_model_cache()
        
        # Get ModelManager info if available
        try:
            manager = ModelManager()
            cache_info = manager.get_cache_info()
        except Exception as e:
            logger.warning(f"Could not get ModelManager info: {e}")
            cache_info = None
        
        return {
            "status": "success",
            "cache": {
                "exists": cache_status.exists,
                "path": cache_status.path,
                "size_mb": round(cache_status.size_mb, 2),
                "model_files_found": cache_status.model_files_found,
                "is_persistent": cache_status.is_persistent,
                "is_writable": cache_status.is_writable,
                "error": cache_status.error
            },
            "manager_info": cache_info,
            "message": "✅ CACHE FOUND: Model loaded from persistent cache" if cache_status.model_files_found else "⚠️ CACHE MISS: Model will be downloaded on first use"
        }
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "cache": {
                "exists": False,
                "path": None,
                "size_mb": 0.0,
                "model_files_found": False,
                "is_persistent": False,
                "is_writable": False,
                "error": str(e)
            }
        }


@router.get("/model-status")
async def get_model_status() -> Dict[str, Any]:
    """
    Get model loading status.
    
    Returns:
        Model status including whether it's loaded and cache information
    """
    try:
        # Try to get EmbeddingService instance
        try:
            from backend.api.main import embedding_service
            
            if embedding_service is None:
                return {
                    "status": "not_initialized",
                    "message": "EmbeddingService not initialized yet",
                    "model_loaded": False
                }
            
            model_info = {
                "model_name": embedding_service.model_name,
                "model_loaded": hasattr(embedding_service, 'model') and embedding_service.model is not None,
                "embedding_dimension": embedding_service.get_embedding_dimension() if hasattr(embedding_service, 'get_embedding_dimension') else None
            }
            
            # Get cache info from ModelManager if available
            if hasattr(embedding_service, 'model_manager') and embedding_service.model_manager:
                cache_info = embedding_service.model_manager.get_cache_info()
                model_info["cache"] = cache_info.get("status", {})
            else:
                model_info["cache"] = {
                    "exists": False,
                    "message": "ModelManager not available"
                }
            
            return {
                "status": "success",
                "model": model_info,
                "message": "✅ Model loaded successfully" if model_info["model_loaded"] else "⚠️ Model not loaded"
            }
        except ImportError:
            return {
                "status": "not_available",
                "message": "EmbeddingService not available (RAG not initialized)",
                "model_loaded": False
            }
    except Exception as e:
        logger.error(f"Error getting model status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "model_loaded": False
        }


@router.get("/environment")
async def get_environment() -> Dict[str, Any]:
    """
    Get environment variables related to model caching.
    
    Returns:
        Environment variables and their values
    """
    env_vars = {
        "HF_HOME": os.getenv("HF_HOME"),
        "TRANSFORMERS_CACHE": os.getenv("TRANSFORMERS_CACHE"),
        "SENTENCE_TRANSFORMERS_HOME": os.getenv("SENTENCE_TRANSFORMERS_HOME"),
        "HF_HUB_CACHE": os.getenv("HF_HUB_CACHE"),
        "HF_DATASETS_CACHE": os.getenv("HF_DATASETS_CACHE"),
        "PERSISTENT_CACHE_PATH": os.getenv("PERSISTENT_CACHE_PATH"),
        "HOME": os.getenv("HOME"),
    }
    
    # Check if paths exist
    path_status = {}
    for key, value in env_vars.items():
        if value and key in ["HF_HOME", "TRANSFORMERS_CACHE", "SENTENCE_TRANSFORMERS_HOME", "PERSISTENT_CACHE_PATH"]:
            path = Path(value)
            path_status[key] = {
                "path": value,
                "exists": path.exists(),
                "is_dir": path.is_dir() if path.exists() else False,
                "is_writable": os.access(path, os.W_OK) if path.exists() else False
            }
    
    # Check Railway persistent volume
    railway_cache = Path("/app/hf_cache")
    railway_status = {
        "path": str(railway_cache),
        "exists": railway_cache.exists(),
        "is_dir": railway_cache.is_dir() if railway_cache.exists() else False,
        "is_writable": os.access(railway_cache, os.W_OK) if railway_cache.exists() else False,
        "is_persistent": railway_cache.exists()
    }
    
    # Check Docker image cache
    image_cache = Path("/app/.model_cache")
    image_cache_status = {
        "path": str(image_cache),
        "exists": image_cache.exists(),
        "is_dir": image_cache.is_dir() if image_cache.exists() else False,
        "is_writable": os.access(image_cache, os.W_OK) if image_cache.exists() else False,
        "is_ephemeral": True  # Docker image cache is ephemeral
    }
    
    return {
        "status": "success",
        "environment_variables": env_vars,
        "path_status": path_status,
        "railway_persistent_volume": railway_status,
        "docker_image_cache": image_cache_status,
        "recommendations": _get_recommendations(env_vars, railway_status, image_cache_status)
    }


def _get_recommendations(env_vars: Dict, railway_status: Dict, image_cache_status: Dict) -> list:
    """Get recommendations based on current configuration"""
    recommendations = []
    
    if not railway_status["exists"]:
        recommendations.append({
            "priority": "HIGH",
            "message": "Railway persistent volume not found at /app/hf_cache. Model will be re-downloaded on every deploy.",
            "action": "Ensure persistent volume is mounted at /app/hf_cache in railway-backend.json"
        })
    
    if not env_vars.get("PERSISTENT_CACHE_PATH"):
        recommendations.append({
            "priority": "MEDIUM",
            "message": "PERSISTENT_CACHE_PATH not set. Set to /app/hf_cache for Railway persistent volume.",
            "action": "Set PERSISTENT_CACHE_PATH=/app/hf_cache in Railway environment variables"
        })
    
    if railway_status["exists"] and not railway_status["is_writable"]:
        recommendations.append({
            "priority": "HIGH",
            "message": "Railway persistent volume exists but is not writable.",
            "action": "Check volume permissions in Railway"
        })
    
    if not env_vars.get("HF_HOME") or env_vars.get("HF_HOME") != "/app/hf_cache":
        if railway_status["exists"]:
            recommendations.append({
                "priority": "MEDIUM",
                "message": "HF_HOME not set to Railway persistent volume.",
                "action": "ModelManager should set this automatically, but verify it's set correctly"
            })
    
    if not recommendations:
        recommendations.append({
            "priority": "INFO",
            "message": "✅ Configuration looks good! Model should be cached in persistent volume.",
            "action": "None"
        })
    
    return recommendations

