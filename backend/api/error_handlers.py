"""
Standardized Error Handling for StillMe API
Provides consistent error response format with error codes
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Error codes for different error types
ERROR_CODES = {
    # 4xx Client Errors
    "VALIDATION_ERROR": "ERR_4001",
    "AUTHENTICATION_REQUIRED": "ERR_4011",
    "AUTHENTICATION_FAILED": "ERR_4012",
    "AUTHORIZATION_FAILED": "ERR_4031",
    "RESOURCE_NOT_FOUND": "ERR_4041",
    "METHOD_NOT_ALLOWED": "ERR_4051",
    "RATE_LIMIT_EXCEEDED": "ERR_4291",
    
    # 5xx Server Errors
    "INTERNAL_SERVER_ERROR": "ERR_5001",
    "SERVICE_UNAVAILABLE": "ERR_5031",
    "DATABASE_ERROR": "ERR_5032",
    "RAG_SYSTEM_ERROR": "ERR_5033",
    "RSS_FETCHER_ERROR": "ERR_5034",
    "SCHEDULER_ERROR": "ERR_5035",
    "VALIDATION_SYSTEM_ERROR": "ERR_5036",
}


class StandardErrorResponse:
    """Standard error response format"""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        timestamp: Optional[str] = None
    ):
        self.error_code = error_code
        self.message = message
        self.details = details or {}
        self.request_id = request_id
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        response = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "timestamp": self.timestamp
        }
        
        if self.details:
            response["details"] = self.details
        
        if self.request_id:
            response["request_id"] = self.request_id
        
        return response


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 500,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None
) -> JSONResponse:
    """
    Create standardized error response
    
    Args:
        error_code: Error code from ERROR_CODES
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        request_id: Optional request ID for tracking
        
    Returns:
        JSONResponse with standardized error format
    """
    error_response = StandardErrorResponse(
        error_code=error_code,
        message=message,
        details=details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.to_dict()
    )


def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    """Handle validation errors"""
    error_details = {}
    if hasattr(exc, 'errors'):
        error_details["field_errors"] = exc.errors()
    
    return create_error_response(
        error_code=ERROR_CODES["VALIDATION_ERROR"],
        message="Input validation failed",
        status_code=422,
        details=error_details
    )


def handle_not_found_error(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle 404 Not Found errors"""
    return create_error_response(
        error_code=ERROR_CODES["RESOURCE_NOT_FOUND"],
        message=exc.detail or "Resource not found",
        status_code=404
    )


def handle_service_unavailable(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle 503 Service Unavailable errors"""
    service_name = "Unknown"
    if "RAG" in str(exc.detail):
        service_name = "RAG"
        error_code = ERROR_CODES["RAG_SYSTEM_ERROR"]
    elif "RSS" in str(exc.detail) or "fetcher" in str(exc.detail):
        service_name = "RSS Fetcher"
        error_code = ERROR_CODES["RSS_FETCHER_ERROR"]
    elif "scheduler" in str(exc.detail):
        service_name = "Scheduler"
        error_code = ERROR_CODES["SCHEDULER_ERROR"]
    elif "database" in str(exc.detail).lower() or "db" in str(exc.detail).lower():
        service_name = "Database"
        error_code = ERROR_CODES["DATABASE_ERROR"]
    else:
        error_code = ERROR_CODES["SERVICE_UNAVAILABLE"]
    
    return create_error_response(
        error_code=error_code,
        message=f"{service_name} service is currently unavailable",
        status_code=503,
        details={"service": service_name, "original_message": str(exc.detail)}
    )


def handle_internal_server_error(request: Request, exc: Exception) -> JSONResponse:
    """Handle 500 Internal Server Error"""
    logger.error(f"Internal server error: {exc}", exc_info=True)
    
    return create_error_response(
        error_code=ERROR_CODES["INTERNAL_SERVER_ERROR"],
        message="An internal server error occurred",
        status_code=500,
        details={"error_type": type(exc).__name__}
    )


def handle_generic_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle generic HTTP exceptions"""
    # Map status codes to error codes
    status_to_code = {
        400: ERROR_CODES["VALIDATION_ERROR"],
        401: ERROR_CODES["AUTHENTICATION_REQUIRED"],
        403: ERROR_CODES["AUTHORIZATION_FAILED"],
        404: ERROR_CODES["RESOURCE_NOT_FOUND"],
        405: ERROR_CODES["METHOD_NOT_ALLOWED"],
        429: ERROR_CODES["RATE_LIMIT_EXCEEDED"],
        500: ERROR_CODES["INTERNAL_SERVER_ERROR"],
        503: ERROR_CODES["SERVICE_UNAVAILABLE"],
    }
    
    error_code = status_to_code.get(exc.status_code, ERROR_CODES["INTERNAL_SERVER_ERROR"])
    
    return create_error_response(
        error_code=error_code,
        message=exc.detail if isinstance(exc.detail, str) else "An error occurred",
        status_code=exc.status_code
    )

