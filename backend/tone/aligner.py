"""
ToneAligner - Normalizes response tone to StillMe style
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
    Align answer tone to StillMe style
    
    Args:
        answer: The answer to align
        
    Returns:
        Aligned answer with normalized tone
    """
    normalized = answer.strip()
    
    # Apply tone normalizations
    for old, new in TONE_NORMALIZATIONS.items():
        normalized = normalized.replace(old, new)
    
    # Ensure polite ending (if not already ending with punctuation)
    if normalized and normalized[-1] not in ".!?":
        normalized += "."
    
    logger.debug("Tone aligned to StillMe style")
    return normalized

