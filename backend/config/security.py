"""
Security Configuration for StillMe API
Handles API key validation, generation, and security warnings
"""

import os
import secrets
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Minimum API key length for security
MIN_API_KEY_LENGTH = 32


def generate_default_api_key() -> str:
    """
    Generate a secure random API key for development/testing.
    
    Returns:
        A secure random hex string (64 characters = 32 bytes)
    """
    return secrets.token_hex(32)


def get_api_key(require_auth: bool = True) -> Optional[str]:
    """
    Get API key from environment variable.
    If not set and require_auth=False, generates a default key.
    
    Args:
        require_auth: If True, returns None if key not set. If False, generates default.
        
    Returns:
        API key string if set or generated, None otherwise
    """
    api_key = os.getenv("STILLME_API_KEY")
    
    if not api_key:
        if require_auth:
            logger.warning("⚠️ STILLME_API_KEY not set in environment")
            logger.warning("⚠️ SECURITY WARNING: Authentication is DISABLED!")
            logger.warning("⚠️ This should ONLY be used in development!")
            logger.warning("⚠️ For production, set STILLME_API_KEY environment variable")
            return None
        else:
            # Generate a default key for development
            default_key = generate_default_api_key()
            logger.warning("⚠️ STILLME_API_KEY not set - generating default key for development")
            logger.warning(f"⚠️ Default API key: {default_key}")
            logger.warning("⚠️ SECURITY WARNING: This is a development key - DO NOT use in production!")
            return default_key
    
    # Validate API key length
    if len(api_key) < MIN_API_KEY_LENGTH:
        logger.error(f"❌ STILLME_API_KEY is too short (minimum {MIN_API_KEY_LENGTH} characters)")
        logger.error("❌ Please set a longer, more secure API key")
        return None
    
    logger.debug("✅ STILLME_API_KEY is set and validated")
    return api_key


def validate_api_key_config() -> dict:
    """
    Validate API key configuration and return status.
    
    Returns:
        Dictionary with validation status and warnings
    """
    api_key = os.getenv("STILLME_API_KEY")
    env = os.getenv("ENV", "development").lower()
    is_production = env == "production"
    
    status = {
        "configured": api_key is not None and len(api_key) >= MIN_API_KEY_LENGTH,
        "is_production": is_production,
        "warnings": [],
        "recommendations": []
    }
    
    if not api_key:
        status["warnings"].append("STILLME_API_KEY is not set - authentication is DISABLED")
        if is_production:
            status["warnings"].append("CRITICAL: Running in PRODUCTION without API key authentication!")
            status["recommendations"].append("Set STILLME_API_KEY environment variable immediately")
        else:
            status["recommendations"].append("Set STILLME_API_KEY for development security")
    elif len(api_key) < MIN_API_KEY_LENGTH:
        status["warnings"].append(f"STILLME_API_KEY is too short (minimum {MIN_API_KEY_LENGTH} characters)")
        status["recommendations"].append("Generate a longer, more secure API key")
    else:
        status["recommendations"].append("API key configuration looks good")
    
    return status

