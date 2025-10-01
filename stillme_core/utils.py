"""
StillMe Core Utilities
"""

def wrap_content(content: str, content_type: str = "web", source: str = "unknown") -> tuple[str, bool]:
    """
    Wrap content for security analysis
    
    Args:
        content: Content to wrap
        content_type: Type of content (web, news, etc.)
        source: Source of content
        
    Returns:
        tuple: (wrapped_content, injection_detected)
    """
    # Simple implementation for testing
    injection_detected = any(pattern in content.lower() for pattern in [
        "script", "javascript:", "onerror", "onload", "alert("
    ])
    
    if injection_detected:
        wrapped_content = f"[REMOVED_INJECTION] {content[:50]}..."
    else:
        wrapped_content = f"[SAFE] {content}"
    
    return wrapped_content, injection_detected
