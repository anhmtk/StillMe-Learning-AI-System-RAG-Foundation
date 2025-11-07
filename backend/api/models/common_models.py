"""
Common models for API requests and responses
Includes validation utilities and common patterns
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
import re
import html


class PaginationParams(BaseModel):
    """Pagination parameters with validation"""
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of items to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")
    
    @validator('limit')
    def validate_limit(cls, v):
        if v > 1000:
            raise ValueError("Limit cannot exceed 1000")
        return v


class ValidationErrorResponse(BaseModel):
    """Standard validation error response"""
    error: str = "validation_error"
    message: str
    details: Optional[Dict[str, Any]] = None
    field_errors: Optional[List[Dict[str, str]]] = None


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input to prevent XSS and injection attacks.
    
    Args:
        value: Input string
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        raise ValueError("Input must be a string")
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Trim whitespace
    value = value.strip()
    
    # Limit length
    if max_length and len(value) > max_length:
        value = value[:max_length]
    
    # Escape HTML to prevent XSS
    value = html.escape(value)
    
    return value


def validate_url(url: str) -> str:
    """
    Validate and sanitize URL input.
    
    Args:
        url: URL string
        
    Returns:
        Validated URL string
        
    Raises:
        ValueError: If URL is invalid
    """
    if not isinstance(url, str):
        raise ValueError("URL must be a string")
    
    url = url.strip()
    
    # Basic URL validation pattern
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        raise ValueError("Invalid URL format")
    
    # Sanitize URL
    url = html.escape(url)
    
    return url


def validate_non_empty_string(value: str, field_name: str = "field", min_length: int = 1, max_length: Optional[int] = None) -> str:
    """
    Validate that string is not empty and meets length requirements.
    
    Args:
        value: String value to validate
        field_name: Name of the field (for error messages)
        min_length: Minimum length
        max_length: Maximum length
        
    Returns:
        Validated string
        
    Raises:
        ValueError: If validation fails
    """
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")
    
    value = value.strip()
    
    if len(value) < min_length:
        raise ValueError(f"{field_name} must be at least {min_length} characters long")
    
    if max_length and len(value) > max_length:
        raise ValueError(f"{field_name} must not exceed {max_length} characters")
    
    return value

