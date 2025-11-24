"""
Security Utilities for StillMe API
Input sanitization, XSS prevention, and security helpers
"""

import re
import html
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def sanitize_string(value: str, max_length: Optional[int] = None, allow_html: bool = False) -> str:
    """
    Sanitize string input to prevent XSS and injection attacks
    
    Args:
        value: Input string to sanitize
        max_length: Maximum length (truncate if longer)
        allow_html: If True, allow HTML tags (default: False, escape HTML)
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value) if value is not None else ""
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Remove control characters (except newlines and tabs)
    value = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', value)
    
    # Escape HTML if not allowed
    if not allow_html:
        value = html.escape(value)
    
    # Truncate if too long
    if max_length and len(value) > max_length:
        value = value[:max_length]
        logger.warning(f"Input truncated to {max_length} characters")
    
    return value.strip()


def sanitize_url(url: str) -> Optional[str]:
    """
    Sanitize and validate URL
    
    Args:
        url: URL string to sanitize
        
    Returns:
        Sanitized URL or None if invalid
    """
    if not isinstance(url, str):
        return None
    
    url = url.strip()
    
    # Basic URL validation
    if not url:
        return None
    
    # Check for dangerous protocols
    dangerous_protocols = ['javascript:', 'data:', 'vbscript:', 'file:', 'about:']
    url_lower = url.lower()
    if any(url_lower.startswith(proto) for proto in dangerous_protocols):
        logger.warning(f"Blocked dangerous URL protocol: {url}")
        return None
    
    # Only allow http/https
    if not (url.startswith('http://') or url.startswith('https://')):
        logger.warning(f"URL must start with http:// or https://: {url}")
        return None
    
    # Basic length check
    if len(url) > 2048:
        logger.warning(f"URL too long: {len(url)} characters")
        return None
    
    return url


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks
    
    Args:
        filename: Filename to sanitize
        
    Returns:
        Sanitized filename
    """
    if not isinstance(filename, str):
        return "file"
    
    # Remove path separators
    filename = filename.replace('/', '').replace('\\', '')
    
    # Remove dangerous characters
    filename = re.sub(r'[<>:"|?*]', '', filename)
    
    # Remove leading dots (hidden files)
    filename = filename.lstrip('.')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    # Default if empty
    if not filename:
        filename = "file"
    
    return filename


def validate_sql_injection_pattern(value: str) -> bool:
    """
    Check for SQL injection patterns (basic detection)
    
    Args:
        value: String to check
        
    Returns:
        True if suspicious pattern detected, False otherwise
    """
    if not isinstance(value, str):
        return False
    
    # Common SQL injection patterns
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|#|\/\*|\*\/)",  # SQL comments
        r"(\b(UNION|OR|AND)\s+\d+\s*=\s*\d+)",  # UNION/OR/AND injection
        r"('|;|\\)",  # Quote and semicolon patterns
    ]
    
    value_upper = value.upper()
    for pattern in sql_patterns:
        if re.search(pattern, value_upper, re.IGNORECASE):
            logger.warning(f"Potential SQL injection pattern detected: {pattern}")
            return True
    
    return False


def sanitize_for_logging(value: str, max_length: int = 200) -> str:
    """
    Sanitize string for safe logging (prevent log injection)
    
    Args:
        value: String to sanitize for logging
        max_length: Maximum length for log entry
        
    Returns:
        Sanitized string safe for logging
    """
    if not isinstance(value, str):
        return str(value)[:max_length] if value is not None else ""
    
    # Remove newlines and control characters
    value = re.sub(r'[\r\n\t]', ' ', value)
    value = re.sub(r'[\x00-\x1F\x7F]', '', value)
    
    # Truncate
    if len(value) > max_length:
        value = value[:max_length] + "..."
    
    return value

