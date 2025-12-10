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
    
    Bypasses rate limit for:
    - Evaluation requests (user_id="evaluation_bot")
    - Admin requests (valid admin API key or admin password)
    
    CRITICAL: Check request.state.bypass_rate_limit flag set by EvaluationBypassMiddleware.
    If flag is True, return special key that will bypass rate limiting.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Rate limit key string
    """
    # CRITICAL: Check if EvaluationBypassMiddleware has set bypass flag
    if hasattr(request.state, 'bypass_rate_limit') and request.state.bypass_rate_limit:
        logger.info(f"✅ Evaluation request detected in key_func, using bypass key")
        return "evaluation:bypass"
    
    # Check for admin bypass (admin API key or admin password)
    api_key = get_api_key_for_limiting(request)
    if api_key:
        # Check if this is admin API key (STILLME_API_KEY)
        try:
            from backend.config.security import get_api_key as get_secure_api_key
            expected_admin_key = get_secure_api_key(require_auth=False)
            if expected_admin_key:
                import hmac
                # Constant-time comparison to prevent timing attacks
                if hmac.compare_digest(api_key.encode(), expected_admin_key.encode()):
                    # This is admin API key - bypass rate limit
                    logger.info(f"✅ Admin API key detected, bypassing rate limit")
                    return "admin:bypass"
        except Exception:
            pass
    
    # Check for admin password in request body (for dashboard/admin panel)
    try:
        import json
        if hasattr(request, '_body'):
            body = request._body
        elif hasattr(request, 'body'):
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
                
                # Check for admin password in request
                admin_password = body_data.get("admin_password", "")
                dashboard_password = os.getenv("DASHBOARD_PASSWORD", "")
                
                if admin_password and dashboard_password:
                    import hmac
                    # Constant-time comparison to prevent timing attacks
                    if hmac.compare_digest(admin_password.encode(), dashboard_password.encode()):
                        logger.info(f"✅ Admin password verified, bypassing rate limit")
                        return "admin:bypass"
            except (json.JSONDecodeError, AttributeError, UnicodeDecodeError):
                pass
    except Exception:
        pass
    
    # Fallback: Check request body manually (if middleware didn't run or flag not set)
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
                    logger.info(f"✅ Evaluation request detected in key_func (from body), using bypass key")
                    return "evaluation:bypass"
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


def get_chat_rate_limit(request: Optional[Request] = None) -> str:
    """
    Get chat endpoint rate limit based on environment and user type.
    For local development/testing, can be disabled or increased via env vars.
    
    CRITICAL: Rate limits by user type:
    - IP-based users (no API key): 15/day (strict limit to prevent abuse)
    - API key users: 1000/day (higher limit for authenticated users)
    - Admin (API key or password): Unlimited (bypass rate limit)
    - Evaluation requests: 10000/day (unlimited for evaluation)
    
    IMPORTANT: This function is called by slowapi's limiter decorator.
    slowapi does NOT support per-key dynamic limits, so we need to check
    the key that will be used and return the appropriate limit.
    
    Args:
        request: Optional FastAPI request object to check for API key
        
    Returns:
        Rate limit string (e.g., "15/day", "1000/day", or "10000/day")
    """
    if DISABLE_RATE_LIMIT:
        # Disable rate limiting by setting a very high limit
        return "10000/day"
    
    # Check if custom rate limit is set via env var (applies to all users)
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
    
    # Railway/Production: 
    # TEMPORARY FIX: Increase default limit to 10000/day for evaluation
    # This is because slowapi doesn't support dynamic per-key limits with callable functions
    # TODO: Find a better solution or switch to a different rate limiting library
    # For now, we'll use a high default limit and rely on EvaluationBypassMiddleware
    # to detect evaluation requests (though it may not work if slowapi caches limits)
    
    # Different limits for API key users vs IP-based users
    if request:
        # CRITICAL: Check the key that will be used by get_rate_limit_key_func
        # This is the only way to support per-key limits with slowapi
        # slowapi calls get_chat_rate_limit(request) for each request,
        # so we can check the key here and return the appropriate limit
        try:
            rate_limit_key = get_rate_limit_key_func(request)
            
            # Admin bypass: unlimited (key starts with "admin:")
            if rate_limit_key.startswith("admin:"):
                logger.info(f"✅ Rate limit for admin request: unlimited (bypass)")
                return "10000/day"  # Effectively unlimited for admin
            
            # Evaluation requests: unlimited (key starts with "evaluation:")
            if rate_limit_key.startswith("evaluation:"):
                logger.info(f"✅ Rate limit for evaluation request: 10000/day (key: {rate_limit_key})")
                return "10000/day"
            
            # API key users: higher limit (key starts with "api_key:")
            if rate_limit_key.startswith("api_key:"):
                limit = os.getenv("RATE_LIMIT_CHAT_API_KEY", "1000/day")
                logger.debug(f"Rate limit for API key user: {limit} (key: {rate_limit_key[:20]}...)")
                return limit
        except Exception as e:
            logger.warning(f"Error getting rate limit key: {e}, falling back to default checks")
        
        # Fallback: Check for evaluation requests in body (if key_func didn't catch it)
        try:
            import json
            body = request._body if hasattr(request, '_body') else None
            if body:
                try:
                    if isinstance(body, bytes):
                        body_str = body.decode('utf-8')
                    else:
                        body_str = str(body)
                    body_data = json.loads(body_str)
                    user_id = body_data.get("user_id", "")
                    use_server_keys = body_data.get("use_server_keys", False)
                    # Evaluation requests: unlimited
                    if user_id == "evaluation_bot" and use_server_keys:
                        logger.info(f"✅ Rate limit for evaluation request (from body): 10000/day")
                        return "10000/day"
                except (json.JSONDecodeError, AttributeError, UnicodeDecodeError) as e:
                    logger.debug(f"Error parsing body: {e}")
        except Exception as e:
            logger.debug(f"Error checking body for evaluation request: {e}")
        
        # Fallback: Check if user has API key (authenticated user)
        api_key = get_api_key_for_limiting(request)
        if api_key:
            # API key users: higher limit (1000/day)
            # This allows authenticated users to use the service freely
            limit = os.getenv("RATE_LIMIT_CHAT_API_KEY", "1000/day")
            logger.debug(f"Rate limit for API key user (from header): {limit}")
            return limit
    
    # IP-based users (no API key): 15/day (strict limit to prevent abuse)
    default_limit = os.getenv("RATE_LIMIT_CHAT_IP", "15/day")
    logger.debug(f"Rate limit for IP-based user: {default_limit}")
    return default_limit

