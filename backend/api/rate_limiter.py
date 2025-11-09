"""
Rate Limiting Middleware for StillMe API
Provides per-IP and per-API-key rate limiting to prevent abuse
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,  # Default: use IP address
    default_limits=["100/minute"],  # Default rate limit
    storage_uri="memory://"  # In-memory storage (can be upgraded to Redis)
)


def get_api_key_for_limiting(request: Request) -> Optional[str]:
    """
    Get API key from request header for rate limiting.
    If API key is present, use it for rate limiting (higher limits).
    Otherwise, use IP address (lower limits).
    
    Args:
        request: FastAPI request object
        
    Returns:
        API key string if present, None otherwise
    """
    api_key = request.headers.get("X-API-Key")
    return api_key if api_key else None


def get_rate_limit_key(request: Request) -> str:
    """
    Get rate limit key based on API key or IP address.
    API key users get higher limits, IP-based users get lower limits.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Rate limit key string
    """
    api_key = get_api_key_for_limiting(request)
    if api_key:
        # Use API key for rate limiting (higher limits)
        return f"api_key:{api_key}"
    else:
        # Use IP address for rate limiting (lower limits)
        return get_remote_address(request)


# Rate limit configurations (configurable via environment variables)
RATE_LIMIT_PER_IP = os.getenv("RATE_LIMIT_PER_IP", "100/minute")  # Per IP: 100 requests per minute
RATE_LIMIT_PER_API_KEY = os.getenv("RATE_LIMIT_PER_API_KEY", "1000/hour")  # Per API key: 1000 requests per hour

# Rate limits for specific endpoints
RATE_LIMIT_CHAT = os.getenv("RATE_LIMIT_CHAT", "10/minute")  # Chat endpoint: 10 requests per minute
RATE_LIMIT_RAG_ADD = os.getenv("RATE_LIMIT_RAG_ADD", "20/hour")  # RAG add: 20 requests per hour
RATE_LIMIT_RSS_FETCH = os.getenv("RATE_LIMIT_RSS_FETCH", "5/hour")  # RSS fetch: 5 requests per hour


def get_rate_limit_key_func(request: Request) -> str:
    """
    Rate limit key function that uses API key if available, otherwise IP address.
    This allows API key users to have higher rate limits.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Rate limit key string
    """
    api_key = get_api_key_for_limiting(request)
    if api_key:
        # Use API key for rate limiting (higher limits)
        return f"api_key:{api_key}"
    else:
        # Use IP address for rate limiting (lower limits)
        return get_remote_address(request)

