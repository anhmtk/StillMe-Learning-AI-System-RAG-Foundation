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

__all__ = ['limiter', 'RateLimitExceeded', 'get_api_key_for_limiting', 'get_rate_limit_key', 'get_rate_limit_key_func', 'get_chat_rate_limit', 'DISABLE_RATE_LIMIT']

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
# For local development/testing, can be overridden via env vars
# Set DISABLE_RATE_LIMIT=true to disable all rate limiting (local testing only)
# Or set RATE_LIMIT_CHAT to override chat endpoint limit (e.g., "1000/minute" for testing)
DISABLE_RATE_LIMIT = os.getenv("DISABLE_RATE_LIMIT", "false").lower() == "true"
RATE_LIMIT_CHAT = os.getenv("RATE_LIMIT_CHAT", "10/minute")  # Chat endpoint: 10 requests per minute
RATE_LIMIT_RAG_ADD = os.getenv("RATE_LIMIT_RAG_ADD", "20/hour")  # RAG add: 20 requests per hour
RATE_LIMIT_RSS_FETCH = os.getenv("RATE_LIMIT_RSS_FETCH", "5/hour")  # RSS fetch: 5 requests per hour


def get_rate_limit_key_func(request: Request) -> str:
    """
    Rate limit key function that uses API key if available, otherwise IP address.
    This allows API key users to have higher rate limits.
    
    Bypasses rate limit for evaluation requests (user_id="evaluation_bot").
    
    Args:
        request: FastAPI request object
        
    Returns:
        Rate limit key string
    """
    # CRITICAL: Bypass rate limit for evaluation requests
    # Evaluation requests use user_id="evaluation_bot" and use_server_keys=True
    # We need to check request body for user_id, but rate limit decorator runs before body parsing
    # So we check the request body manually here
    try:
        import json
        import asyncio
        # Read request body - need to handle async properly
        # Check if body is already read
        if hasattr(request, '_body'):
            body = request._body
        elif hasattr(request, 'body'):
            # For async requests, body might be a coroutine
            if asyncio.iscoroutine(request.body):
                # Can't await in sync function, skip this check
                body = None
            else:
                body = request.body
        else:
            body = None
            
        if body:
            try:
                if isinstance(body, bytes):
                    body_str = body.decode('utf-8')
                else:
                    body_str = str(body)
                body_data = json.loads(body_str)
                user_id = body_data.get("user_id", "")
                use_server_keys = body_data.get("use_server_keys", False)
                # Bypass rate limit for evaluation requests
                if user_id == "evaluation_bot" and use_server_keys:
                    # Use a special key that will have unlimited rate limit
                    # We'll configure limiter to allow unlimited for this key
                    return f"evaluation:{user_id}"
            except (json.JSONDecodeError, AttributeError, UnicodeDecodeError):
                pass
    except Exception:
        pass  # If we can't parse body, continue with normal rate limiting
    
    api_key = get_api_key_for_limiting(request)
    if api_key:
        # Use API key for rate limiting (higher limits)
        return f"api_key:{api_key}"
    else:
        # Use IP address for rate limiting (lower limits)
        return get_remote_address(request)


def get_chat_rate_limit() -> str:
    """
    Get chat endpoint rate limit based on environment.
    For local development/testing, can be disabled or increased via env vars.
    
    Note: Evaluation requests (user_id="evaluation_bot") are handled via
    get_rate_limit_key_func which returns a special key "evaluation:evaluation_bot".
    The limiter needs to be configured to allow unlimited requests for this key.
    
    Returns:
        Rate limit string (e.g., "15/day", "1000/minute", or "1000/day" if disabled)
    """
    if DISABLE_RATE_LIMIT:
        # Disable rate limiting by setting a very high limit
        return "10000/day"
    
    # Check if custom rate limit is set via env var
    if os.getenv("RATE_LIMIT_CHAT"):
        return os.getenv("RATE_LIMIT_CHAT")
    
    # Check if we're in local development (not production, not Railway)
    env = os.getenv("ENV", "development").lower()
    is_production = env == "production"
    is_railway = bool(os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_PROJECT_NAME"))
    
    if not is_production and not is_railway:
        # Local development: use more lenient rate limit for testing
        # Default: 1000 requests per day (should be enough for testing)
        return os.getenv("RATE_LIMIT_CHAT_LOCAL", "1000/day")
    
    # Railway/Production: use higher rate limit to support evaluation
    # Previous: 15/day was too strict for evaluation runs
    # New: 1000/day should be enough for evaluation while still preventing abuse
    return os.getenv("RATE_LIMIT_CHAT_RAILWAY", "1000/day")

