"""
Security Middleware for StillMe API
Includes HTTPS enforcement, HSTS headers, and other security headers
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
import logging
import os

logger = logging.getLogger(__name__)

# Security configuration from environment variables
ENFORCE_HTTPS = os.getenv("ENFORCE_HTTPS", "false").lower() == "true"
HSTS_MAX_AGE = int(os.getenv("HSTS_MAX_AGE", "31536000"))  # 1 year default
ALLOW_INSECURE_IN_DEV = os.getenv("ALLOW_INSECURE_IN_DEV", "false").lower() == "true"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        response = await call_next(request)
        
        # Add HSTS header (HTTP Strict Transport Security)
        # Only add if HTTPS is enforced or we're in production
        if ENFORCE_HTTPS or not ALLOW_INSECURE_IN_DEV:
            response.headers["Strict-Transport-Security"] = f"max-age={HSTS_MAX_AGE}; includeSubDomains; preload"
        
        # Add X-Content-Type-Options header
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Add X-Frame-Options header (prevent clickjacking)
        response.headers["X-Frame-Options"] = "DENY"
        
        # Add X-XSS-Protection header (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Add Referrer-Policy header
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Add Content-Security-Policy header (basic)
        # Note: This is a basic CSP. Adjust based on your needs
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Allow inline scripts for Streamlit
            "style-src 'self' 'unsafe-inline'; "  # Allow inline styles
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Add Permissions-Policy header (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=()"
        )
        
        return response


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """Middleware to redirect HTTP to HTTPS"""
    
    async def dispatch(self, request: Request, call_next):
        """Redirect HTTP requests to HTTPS if enforcement is enabled"""
        
        # Skip HTTPS enforcement in development if allowed
        if ALLOW_INSECURE_IN_DEV and not ENFORCE_HTTPS:
            return await call_next(request)
        
        # Check if HTTPS enforcement is enabled
        if not ENFORCE_HTTPS:
            return await call_next(request)
        
        # Check if request is HTTP (not HTTPS)
        url = request.url
        if url.scheme == "http":
            # Get the HTTPS URL
            https_url = url.replace(scheme="https", port=443 if url.port == 80 else url.port)
            
            logger.warning(f"Redirecting HTTP request to HTTPS: {url} -> {https_url}")
            
            # Return redirect response
            return RedirectResponse(
                url=str(https_url),
                status_code=301  # Permanent redirect
            )
        
        # Request is already HTTPS, continue
        return await call_next(request)


def get_security_middleware():
    """
    Get list of security middleware to add to FastAPI app.
    
    Returns:
        List of middleware classes
    """
    middleware = []
    
    # Always add security headers middleware
    middleware.append(SecurityHeadersMiddleware)
    
    # Add HTTPS redirect middleware if enforcement is enabled
    if ENFORCE_HTTPS:
        middleware.append(HTTPSRedirectMiddleware)
        logger.info("✅ HTTPS enforcement enabled - HTTP requests will be redirected to HTTPS")
    else:
        logger.info("⚠️ HTTPS enforcement disabled - set ENFORCE_HTTPS=true to enable")
    
    return middleware

