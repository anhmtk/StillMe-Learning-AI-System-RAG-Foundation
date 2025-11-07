"""
IdentityInjector - Injects StillMe identity into prompts
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# StillMe identity prompt
STILLME_IDENTITY = """You are StillMe — a transparent, ethical Learning AI system with RAG foundation.
Tone: factual, calm, humble, rigorous; prefer citations; avoid overclaiming.
Always explain sources and uncertainties briefly."""


def inject_identity(user_prompt: str, system_prompt: Optional[str] = None) -> str:
    """
    Inject StillMe identity into user prompt
    
    Args:
        user_prompt: The original user prompt
        system_prompt: Optional custom system prompt (default: STILLME_IDENTITY)
        
    Returns:
        Enhanced prompt with StillMe identity
    """
    identity = system_prompt or STILLME_IDENTITY
    
    enhanced = f"{identity}\n\nUser:\n{user_prompt}"
    
    logger.debug("StillMe identity injected into prompt")
    return enhanced

