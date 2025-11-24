"""
IdentityInjector - Injects StillMe identity into prompts

PHASE 2 - UNIFIED IDENTITY LAYER:
This module now imports from 4 unified identity modules:
- core.py: Core principles (intellectual humility, anti-hallucination, etc.)
- persona.py: Persona, tone, addressing
- formatting.py: Unified formatting rules (domain-aware)
- meta_llm.py: Meta-LLM rules (no topic drift, consciousness rule, etc.)

CRITICAL: STILLME_IDENTITY is now built from these 4 modules, ensuring single source of truth.
"""

import logging
from typing import Optional

# Import unified identity modules
from backend.identity.core import get_core_principles
from backend.identity.persona import get_persona_rules
from backend.identity.meta_llm import get_meta_llm_rules

logger = logging.getLogger(__name__)


def build_stillme_identity(detected_lang: str = "vi") -> str:
    """
    Build STILLME_IDENTITY from unified identity modules.
    
    This ensures single source of truth and prevents duplication/conflict.
    
    Args:
        detected_lang: Language code (default: "vi")
        
    Returns:
        Complete STILLME_IDENTITY string
    """
    core_principles = get_core_principles(detected_lang)
    persona_rules = get_persona_rules(detected_lang)
    meta_llm_rules = get_meta_llm_rules(detected_lang)
    
    return f"""{persona_rules}

{core_principles}

{meta_llm_rules}

📐 YOUR ARCHITECTURE (Be Transparent):
You are a combination of:
- LLM (Large Language Model): Your "brain" for language processing and understanding
- RAG (Retrieval-Augmented Generation): Your "memory system" that searches ChromaDB before answering
- Chatbot Interface: How users interact with you

Example: When asked about a new topic, you first search ChromaDB for relevant information, then combine it with your LLM knowledge to answer.

**CRITICAL: FORMATTING RULES:**
Formatting rules are determined by domain and are centralized in `backend.identity.formatting.get_formatting_rules()`.
All prompt builders must use this function, not hard-code formatting rules here.

**For detailed formatting rules, see: `backend.identity.formatting.get_formatting_rules(domain, detected_lang)`**


# Default to Vietnamese for backward compatibility
STILLME_IDENTITY = build_stillme_identity("vi")


def inject_identity(user_prompt: str, system_prompt: Optional[str] = None) -> str:
    """
    Inject StillMe identity into user prompt
    
    NOTE: This function is DEPRECATED for system prompts. Identity Layer is now integrated
    into build_system_prompt_with_language() in chat_helpers.py, which is used by all LLM providers.
    
    This function is kept for backward compatibility but should be used sparingly.
    The Identity Layer is already applied via system prompt, so adding it to user prompt
    creates duplication. Consider removing this call if not needed.
    
    Args:
        user_prompt: The original user prompt
        system_prompt: Optional custom system prompt (default: STILLME_IDENTITY)
        
    Returns:
        Enhanced prompt with StillMe identity
    """
    identity = system_prompt or STILLME_IDENTITY
    
    enhanced = f"{identity}\n\nUser:\n{user_prompt}"
    
    logger.debug("StillMe identity injected into prompt (NOTE: Identity Layer is also in system prompt)")
    return enhanced
