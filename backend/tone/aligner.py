"""
ToneAligner - Normalizes response tone to StillMe style

CRITICAL: This function must handle Unicode (including Chinese) safely.
It should NOT remove or modify Unicode characters.
"""

import logging
import os
import re

logger = logging.getLogger(__name__)

# Tone style options
STILLME_TONE_STYLE = os.getenv("STILLME_TONE_STYLE", "neutral")

# Phrases to normalize (future: could be expanded)
TONE_NORMALIZATIONS = {
    # Add tone normalization rules here if needed
    # Example: "I'm an AI" → "I'm StillMe"
}


def align_tone(answer: str) -> str:
    """
    Align answer tone to StillMe style.
    
    CRITICAL: This function must preserve all Unicode characters (Chinese, Vietnamese, etc.).
    It should ONLY:
    - Strip leading/trailing whitespace
    - Apply tone normalizations (if any)
    - Add punctuation if missing
    
    It should NOT:
    - Remove any Unicode characters
    - Encode/decode text
    - Use regex that might remove Unicode
    
    Args:
        answer: The answer to align (may contain Unicode characters)
        
    Returns:
        Aligned answer with normalized tone (Unicode preserved)
    """
    # CRITICAL: Log input for debugging (especially for Chinese)
    input_length = len(answer) if answer else 0
    input_preview = answer[:100] if answer and len(answer) > 100 else (answer if answer else 'None')
    
    logger.info(
        f"align_tone INPUT: length={input_length}, "
        f"preview={input_preview}, "
        f"type={type(answer)}"
    )
    
    # CRITICAL: Validate input
    if not answer or not isinstance(answer, str):
        logger.warning(
            f"⚠️ align_tone received invalid input: type={type(answer)}, "
            f"value={answer[:50] if answer else 'None'}"
        )
        return answer if answer else ""
    
    # CRITICAL: Use strip() carefully - only strip whitespace, not content
    # Python's strip() already handles Unicode correctly, but we add defensive check
    normalized = answer.strip()
    
    # CRITICAL: Validate after strip - ensure we didn't lose all content
    if not normalized or len(normalized) == 0:
        logger.warning(
            f"⚠️ align_tone: Input became empty after strip() "
            f"(original_length={input_length}), returning original answer"
        )
        return answer  # Return original if strip() removed everything
    
    # Apply tone normalizations
    for old, new in TONE_NORMALIZATIONS.items():
        if old in normalized:
            normalized = normalized.replace(old, new)
            logger.debug(f"Applied tone normalization: '{old}' → '{new}'")
    
    # CRITICAL: Ensure polite ending (if not already ending with punctuation)
    # Use Unicode-safe check for punctuation
    if normalized and len(normalized) > 0:
        # Check last character safely (Python handles Unicode correctly)
        last_char = normalized[-1]
        # Unicode punctuation includes: . ! ? 。 ！ ？ (Chinese punctuation)
        if last_char not in ".!?。！？":
            normalized += "."
            logger.debug("Added punctuation ending to response")
    
    # CRITICAL: Log output for debugging (especially for Chinese)
    output_length = len(normalized) if normalized else 0
    output_preview = normalized[:100] if normalized and len(normalized) > 100 else (normalized if normalized else 'None')
    removed_chars = input_length - output_length
    
    logger.info(
        f"align_tone OUTPUT: length={output_length}, "
        f"preview={output_preview}, "
        f"removed={removed_chars} chars (should be 0 or negative if punctuation added)"
    )
    
    # CRITICAL: Final validation - ensure output is not empty
    if not normalized or len(normalized) == 0:
        logger.error(
            f"❌ CRITICAL: align_tone output is empty "
            f"(input_length={input_length}), returning original answer"
        )
        return answer  # Return original if output is empty
    
    # CRITICAL: Validate that we didn't lose significant content
    # If we lost more than 10% of content (excluding punctuation addition), something is wrong
    if removed_chars > (input_length * 0.1) and removed_chars > 5:
        logger.error(
            f"❌ CRITICAL: align_tone lost {removed_chars} characters "
            f"({removed_chars/input_length*100:.1f}% of input, length={input_length}), "
            f"returning original answer to prevent content loss"
        )
        return answer  # Return original if we lost significant content
    
    logger.debug("Tone aligned to StillMe style")
    return normalized

