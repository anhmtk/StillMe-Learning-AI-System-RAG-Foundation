"""Text utility functions for chat router.

This module contains text processing utilities extracted from chat_router.py
to improve maintainability and reduce file size.
"""

import re
import unicodedata
import logging
from typing import List

logger = logging.getLogger(__name__)


def safe_unicode_slice(text: str, max_length: int) -> str:
    """
    Safely slice Unicode string without breaking multi-byte characters.
    
    Args:
        text: Input string (may contain Unicode characters)
        max_length: Maximum length in characters (not bytes)
        
    Returns:
        Sliced string that preserves Unicode characters
    """
    if not text or not isinstance(text, str):
        return text
    
    # Normalize Unicode to ensure consistent character boundaries
    try:
        text = unicodedata.normalize('NFC', text)
    except Exception:
        pass  # If normalization fails, continue with original text
    
    # Safe slice: Python's string slicing already handles Unicode correctly
    # But we add defensive check to ensure we don't exceed string length
    if len(text) <= max_length:
        return text
    
    return text[:max_length]


def clean_response_text(text: str) -> str:
    """
    Clean response text from control characters and smart quotes that may cause encoding issues.
    
    CRITICAL: This function must preserve all Unicode characters (Chinese, Vietnamese, etc.).
    It should ONLY remove:
    - Control characters (0x00-0x1F, 0x7F-0x9F)
    - Smart quotes (\u201c, \u201d, \u2018, \u2019)
    - Zero-width characters that cause issues
    
    It should NOT remove:
    - Any Unicode characters (Chinese, Vietnamese, etc.)
    - Any printable characters
    
    Args:
        text: Original response text (may contain Unicode characters)
        
    Returns:
        Cleaned text with problematic characters removed (Unicode preserved)
    """
    if not text or not isinstance(text, str):
        return text
    
    # CRITICAL: Log input for debugging (especially for Chinese)
    input_length = len(text)
    input_preview = safe_unicode_slice(text, 100) if text else 'None'
    
    # CRITICAL: Only remove control characters and smart quotes
    # DO NOT remove any Unicode characters (Chinese, Vietnamese, etc.)
    # CRITICAL: PRESERVE newlines (\n = 0x0A) and carriage returns (\r = 0x0D) for line breaks
    # Pattern explanation:
    # - [\x00-\x09\x0b-\x1f]: Control characters EXCEPT \n (0x0A) and \r (0x0D)
    # - [\x7f-\x9f]: Extended control characters (0x7F-0x9F)
    # - \u201c\u201d\u2018\u2019: Smart quotes (left/right double and single quotes)
    # - \u200b\u200c\u200d\u200e\u200f: Zero-width characters that can cause issues
    # - \ufffe\uffff: Non-characters
    # CRITICAL: This pattern does NOT match Chinese/Vietnamese/any Unicode characters
    # CRITICAL: This pattern PRESERVES \n (0x0A) and \r (0x0D) for line breaks
    cleaned = re.sub(r'[\x00-\x09\x0b-\x1f\x7f-\x9f\u201c\u201d\u2018\u2019\u200b\u200c\u200d\u200e\u200f\ufffe\uffff]', '', text)
    
    # CRITICAL: Validate that we didn't lose significant content
    output_length = len(cleaned) if cleaned else 0
    removed_chars = input_length - output_length
    
    # CRITICAL: If we removed more than 5% of content (excluding control characters), something is wrong
    # Control characters should be very rare (< 1% of text)
    if removed_chars > (input_length * 0.05) and removed_chars > 10:
        logger.error(
            f"❌ CRITICAL: clean_response_text removed {removed_chars} characters "
            f"({removed_chars/input_length*100:.1f}% of input, length={input_length}), "
            f"this is suspicious - returning original text to prevent content loss"
        )
        return text  # Return original if we removed too much
    
    # Normalize Unicode to NFC form for consistency
    # CRITICAL: This should NOT change the length significantly
    try:
        cleaned_normalized = unicodedata.normalize('NFC', cleaned)
        # CRITICAL: Validate normalization didn't lose content
        if len(cleaned_normalized) < len(cleaned) * 0.95:
            logger.warning(
                f"⚠️ Unicode normalization lost content "
                f"(before: {len(cleaned)}, after: {len(cleaned_normalized)}), "
                f"using pre-normalized text"
            )
            cleaned = cleaned  # Keep pre-normalized version
        else:
            cleaned = cleaned_normalized
    except Exception as e:
        logger.warning(f"⚠️ Unicode normalization failed: {e}, using cleaned text without normalization")
        pass  # If normalization fails, continue with cleaned text
    
    # CRITICAL: Log output for debugging (especially for Chinese)
    output_length_final = len(cleaned) if cleaned else 0
    output_preview = safe_unicode_slice(cleaned, 100) if cleaned else 'None'
    removed_chars_final = input_length - output_length_final
    
    if removed_chars_final > 0:
        logger.info(
            f"clean_response_text: removed {removed_chars_final} problematic characters "
            f"(input_length={input_length}, output_length={output_length_final})"
        )
    
    # CRITICAL: Final validation - ensure output is not empty
    if not cleaned or len(cleaned) == 0:
        logger.error(
            f"❌ CRITICAL: clean_response_text output is empty "
            f"(input_length={input_length}), returning original text"
        )
        return text  # Return original if output is empty
    
    return cleaned


def fix_missing_line_breaks(text: str) -> str:
    """
    Auto-fix missing line breaks after headings and bullets.
    
    This is a defensive function to ensure line breaks are present even if LLM
    doesn't follow instructions.
    
    Args:
        text: Response text that may be missing line breaks
        
    Returns:
        Text with line breaks fixed
    """
    if not text or not isinstance(text, str):
        return text
    
    # Fix: Add line break after markdown headings (## HeadingText -> ## HeadingText\n\n)
    # Pattern: ## or ### followed by text, then immediately followed by non-newline character
    text = re.sub(r'(^#{1,6}\s+[^\n]+)([^\n])', r'\1\n\n\2', text, flags=re.MULTILINE)
    
    # Fix: Add line break after heading-like text (if no markdown, check for patterns)
    # Pattern: Text ending with ":" or "?" followed by text without newline
    text = re.sub(r'([^:\n?]+[:\?])([^\n\s])', r'\1\n\2', text)
    
    # Fix: Add line break after bullet points (- Item -> - Item\n)
    # Pattern: - or * at start of line, followed by text, then immediately followed by non-newline
    text = re.sub(r'(^[\s]*[-*•]\s+[^\n]+)([^\n])', r'\1\n\2', text, flags=re.MULTILINE)
    
    # Normalize multiple consecutive newlines to max 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text


def strip_philosophy_from_answer(text: str) -> str:
    """
    Strip all philosophy-related content from answer.
    
    CRITICAL: Must remove philosophers, theories, meta-philosophy.
    
    Args:
        text: Answer text
        
    Returns:
        Text with philosophy stripped
    """
    from backend.core.ai_self_model_detector import FORBIDDEN_PHILOSOPHY_TERMS
    
    # Remove sentences containing forbidden terms
    lines = text.split('\n')
    filtered_lines = []
    
    for line in lines:
        line_lower = line.lower()
        has_forbidden = any(term in line_lower for term in FORBIDDEN_PHILOSOPHY_TERMS)
        if not has_forbidden:
            filtered_lines.append(line)
        else:
            logger.warning(f"🚨 Stripped line with forbidden term: {line[:100]}")
    
    return '\n'.join(filtered_lines)


def strip_forbidden_terms(text: str, forbidden_terms: List[str]) -> str:
    """
    Strip specific forbidden terms from text.
    
    Args:
        text: Text to clean
        forbidden_terms: List of forbidden terms found
        
    Returns:
        Cleaned text
    """
    result = text
    for term in forbidden_terms:
        # Remove sentences containing the term
        pattern = re.compile(rf'.*{re.escape(term)}.*', re.IGNORECASE | re.MULTILINE)
        result = pattern.sub('', result)
    
    # Clean up multiple newlines
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()

