"""
Ethics Guard for StillMe
Content filtering to prevent malicious or inappropriate content from being added to RAG

This is a basic implementation. For production, consider:
- Integration with external content moderation APIs (e.g., OpenAI Moderation API)
- Machine learning-based toxicity detection
- Community reporting and moderation
"""

from typing import Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)

# Blocked keywords/phrases (basic list - expand as needed)
BLOCKED_KEYWORDS = [
    # Violence
    "kill yourself", "self harm", "suicide",
    # Hate speech (basic examples)
    "hate", "racist", "discrimination",
    # Illegal content
    "illegal drugs", "drug dealing",
    # Spam/scam
    "click here", "free money", "guaranteed profit",
]

# Blocked patterns (regex)
BLOCKED_PATTERNS = [
    r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+",  # URLs (may be legitimate, but flag for review)
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # Email addresses (may be legitimate)
]

# Minimum content length (to prevent spam)
MIN_CONTENT_LENGTH = 50

# Maximum content length (to prevent abuse)
MAX_CONTENT_LENGTH = 100000


def check_content_ethics(content: str) -> Tuple[bool, Optional[str]]:
    """
    Check if content violates ethics guidelines.
    
    This is a basic implementation. For production, consider:
    - Using external moderation APIs (OpenAI Moderation, Perspective API)
    - Machine learning-based toxicity detection
    - Community reporting system
    
    Args:
        content: Content to check
        
    Returns:
        Tuple of (is_valid: bool, reason: Optional[str])
        - is_valid=True: Content passes ethics check
        - is_valid=False: Content fails ethics check, reason explains why
    """
    if not content or not isinstance(content, str):
        return False, "Content is empty or invalid"
    
    content_lower = content.lower()
    
    # Check length
    if len(content) < MIN_CONTENT_LENGTH:
        return False, f"Content too short (minimum {MIN_CONTENT_LENGTH} characters)"
    
    if len(content) > MAX_CONTENT_LENGTH:
        return False, f"Content too long (maximum {MAX_CONTENT_LENGTH} characters)"
    
    # Check for blocked keywords
    for keyword in BLOCKED_KEYWORDS:
        if keyword in content_lower:
            logger.warning(f"Blocked keyword detected: {keyword}")
            return False, f"Content contains blocked keyword: {keyword}"
    
    # Check for blocked patterns
    for pattern in BLOCKED_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            # URLs and emails are flagged but not blocked (may be legitimate)
            # Log for review
            logger.info(f"Pattern detected (flagged for review): {pattern} - {len(matches)} matches")
            # For now, we allow URLs/emails but log them
            # In production, you may want to block or require approval
    
    # Content passes basic ethics check
    return True, None


def check_content_toxicity(content: str) -> Tuple[bool, Optional[str]]:
    """
    Check content for toxicity using external APIs (if available).
    
    This is a placeholder for integration with:
    - OpenAI Moderation API
    - Perspective API (Google)
    - Custom ML models
    
    Args:
        content: Content to check
        
    Returns:
        Tuple of (is_safe: bool, reason: Optional[str])
    """
    # TODO: Implement external API integration
    # For now, use basic keyword check
    return check_content_ethics(content)

