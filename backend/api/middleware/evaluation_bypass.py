"""
Evaluation Request Bypass Middleware

Bypasses rate limiting for evaluation requests (user_id="evaluation_bot").
This middleware runs BEFORE slowapi's rate limiter, so it can set a flag
in request.state to bypass rate limiting.
"""

import json
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class EvaluationBypassMiddleware(BaseHTTPMiddleware):
    """
    Middleware to bypass rate limiting for evaluation requests.
    
    Checks request body for user_id="evaluation_bot" and use_server_keys=True,
    then sets a flag in request.state to bypass rate limiting.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only check POST requests to chat endpoints
        if request.method == "POST" and "/api/chat/" in request.url.path:
            try:
                # Read request body
                body = await request.body()
                
                if body:
                    try:
                        body_data = json.loads(body.decode('utf-8'))
                        user_id = body_data.get("user_id", "")
                        use_server_keys = body_data.get("use_server_keys", False)
                        
                        # Check if this is an evaluation request
                        if user_id == "evaluation_bot" and use_server_keys:
                            # Set flag in request state to bypass rate limiting
                            request.state.bypass_rate_limit = True
                            logger.info(f"✅ Evaluation request detected, bypassing rate limit (user_id: {user_id})")
                        else:
                            request.state.bypass_rate_limit = False
                    except (json.JSONDecodeError, UnicodeDecodeError) as e:
                        logger.debug(f"Error parsing request body for evaluation check: {e}")
                        request.state.bypass_rate_limit = False
                else:
                    request.state.bypass_rate_limit = False
            except Exception as e:
                logger.debug(f"Error checking evaluation request: {e}")
                request.state.bypass_rate_limit = False
        else:
            request.state.bypass_rate_limit = False
        
        # Continue with request processing
        response = await call_next(request)
        return response

