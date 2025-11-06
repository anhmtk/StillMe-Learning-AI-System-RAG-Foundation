"""
Authentication and Authorization for StillMe API
Provides API key-based authentication for sensitive endpoints
"""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

# API Key Header name
API_KEY_HEADER_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


def get_api_key() -> Optional[str]:
    """
    Get API key from environment variable.
    
    Returns:
        API key string if set, None otherwise
    """
    return os.getenv("STILLME_API_KEY")


def constant_time_compare(a: bytes, b: bytes) -> bool:
    """
    Constant-time comparison to prevent timing attacks.
    
    Args:
        a: First byte string
        b: Second byte string
        
    Returns:
        True if strings are equal, False otherwise
    """
    import hmac
    # Use hmac.compare_digest for constant-time comparison
    # It's designed to prevent timing attacks
    return hmac.compare_digest(a, b)


def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key from request header.
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        Verified API key string
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    expected_key = get_api_key()
    
    # If no API key is configured, allow access (for development)
    # In production, this should always be set
    if not expected_key:
        logger.warning("⚠️ STILLME_API_KEY not set in environment. Authentication disabled.")
        logger.warning("⚠️ SECURITY WARNING: This should only be used in development!")
        return "no_auth_configured"
    
    # If API key is provided but doesn't match
    if not api_key:
        logger.warning("API key missing from request header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Please provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Compare API keys (constant-time comparison to prevent timing attacks)
    if not constant_time_compare(api_key.encode(), expected_key.encode()):
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    logger.debug("API key verified successfully")
    return api_key


def require_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Dependency function for FastAPI to require API key authentication.
    Use this in endpoint dependencies.
    
    Example:
        @app.post("/api/sensitive", dependencies=[Depends(require_api_key)])
        async def sensitive_endpoint():
            ...
    
    Args:
        api_key: API key from X-API-Key header
        
    Returns:
        Verified API key string
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    return verify_api_key(api_key)

