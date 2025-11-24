"""
Rewrite 2 - Philosophical Depth (Option B Pipeline)

MANDATORY rewrite pass that adds:
1. 3-Tier Philosophical Analysis (Reframing, Conceptual Map, Boundary of Knowledge)
2. Methodological analysis
3. Comparison with real concepts
4. Source verification guidance

CRITICAL: This rewrite ONLY runs after Rewrite 1 (Honesty) has ensured no fabrication.
It focuses on DEPTH and PHILOSOPHICAL RIGOR, not on removing fabrication.
"""

import logging
import os
from typing import Optional, Dict, Any
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PhilosophicalDepthResult:
    """Result of philosophical depth rewrite"""
    text: str
    was_rewritten: bool
    error: Optional[str] = None


class RewritePhilosophicalDepth:
    """
    Rewrite 2: Philosophical Depth
    
    Adds deep philosophical analysis and methodological rigor.
    Only runs after Rewrite 1 has ensured honesty.
    """
    
    def __init__(self):
        """Initialize philosophical depth rewrite"""
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_base_url = "https://api.deepseek.com/v1/chat/completions"
    
    async def rewrite(
        self,
        text: str,
        original_question: str,
        question_type: str,
        detected_lang: str = "en",
        is_fallback: bool = False  # True if text is from EPD-Fallback
    ) -> PhilosophicalDepthResult:
        """
        Rewrite to add philosophical depth
        
        Args:
            text: Text from Rewrite 1 (already honest)
            original_question: User question
            question_type: Question type (from QuestionClassifierV2)
            detected_lang: Detected language code
            is_fallback: True if text is from EPD-Fallback (already has depth)
            
        Returns:
            PhilosophicalDepthResult
        """
        # If already fallback, it already has depth - skip
        if is_fallback:
            logger.info("⏭️ Rewrite 2 (Philosophical Depth): Text is already EPD-Fallback, skipping")
            return PhilosophicalDepthResult(
                text=text,
                was_rewritten=False
            )
        
        # Only apply to philosophical_meta and factual_academic questions
        if question_type not in ["philosophical_meta", "factual_academic"]:
            logger.info(f"⏭️ Rewrite 2 (Philosophical Depth): Question type '{question_type}' doesn't require philosophical depth")
            return PhilosophicalDepthResult(
                text=text,
                was_rewritten=False
            )
        
        if not self.deepseek_api_key:
            logger.warning("DeepSeek API key not available, cannot add philosophical depth")
            return PhilosophicalDepthResult(
                text=text,
                was_rewritten=False,
                error="API key not available"
            )
        
        # Rewrite to add philosophical depth
        rewritten = await self._rewrite_for_depth(
            text, original_question, question_type, detected_lang
        )
        
        if rewritten:
            return PhilosophicalDepthResult(
                text=rewritten,
                was_rewritten=True
            )
        
        return PhilosophicalDepthResult(
            text=text,
            was_rewritten=False,
            error="Rewrite failed"
        )
    
    async def _rewrite_for_depth(
        self,
        text: str,
        original_question: str,
        question_type: str,
        detected_lang: str
    ) -> Optional[str]:
        """
        Rewrite to add philosophical depth
        
        Args:
            text: Original text (already honest)
            original_question: User question
            question_type: Question type
            detected_lang: Language code
            
        Returns:
            Rewritten text or None if error
        """
        # Get full language name
        language_names = {
            'vi': 'Vietnamese (Tiếng Việt)',
            'zh': 'Chinese (中文)',
            'de': 'German (Deutsch)',
            'fr': 'French (Français)',
            'es': 'Spanish (Español)',
            'ja': 'Japanese (日本語)',
            'ko': 'Korean (한국어)',
            'ar': 'Arabic (العربية)',
            'ru': 'Russian (Русский)',
            'pt': 'Portuguese (Português)',
            'it': 'Italian (Italiano)',
            'hi': 'Hindi (हिन्दी)',
            'th': 'Thai (ไทย)',
            'en': 'English'
        }
        lang_name = language_names.get(detected_lang, detected_lang.upper())
        
        # INTEGRATED: Use Style Engine for domain detection and structure guidance
        from backend.style.style_engine import detect_domain, build_domain_structure_guidance, get_depth_target_for_question, DomainType
        
        detected_domain = detect_domain(original_question, question_type)
        target_depth = get_depth_target_for_question(
            domain=detected_domain,
            option_b_enabled=True,
            is_fake_entity=False
        )
        
        # Get domain-specific structure guidance
        domain_guidance = build_domain_structure_guidance(detected_domain, detected_lang)
        
        # Phase 2: Use Unified Identity Layer - formatting.py (single source of truth)
        from backend.identity.formatting import get_formatting_rules
        formatting_rules = get_formatting_rules(detected_domain, detected_lang)
        
        if question_type == "philosophical_meta":
            system_prompt = f"""You are rewriting a philosophical response to add DEPTH and RIGOR.

🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT 🚨🚨🚨
RESPOND EXCLUSIVELY IN {lang_name.upper()} ONLY.

{formatting_rules}

**STILLME STYLE SPEC V1 - PHILOSOPHY TEMPLATE (MANDATORY):**

{domain_guidance}

**TARGET DEPTH LEVEL: {target_depth.name} ({target_depth.value})**

**CRITICAL: If the original response is missing any part of the structure, ADD IT. All parts are MANDATORY.**

RESPOND IN {lang_name.upper()} ONLY."""
        else:  # factual_academic
            # Use domain-specific template for academic questions
            if detected_domain == DomainType.HISTORY:
                domain_guidance = build_domain_structure_guidance(DomainType.HISTORY, detected_lang)
            elif detected_domain == DomainType.ECONOMICS:
                domain_guidance = build_domain_structure_guidance(DomainType.ECONOMICS, detected_lang)
            elif detected_domain == DomainType.SCIENCE:
                domain_guidance = build_domain_structure_guidance(DomainType.SCIENCE, detected_lang)
            else:
                domain_guidance = build_domain_structure_guidance(DomainType.GENERIC, detected_lang)
            
            system_prompt = f"""You are rewriting an academic response to add METHODOLOGICAL DEPTH.

🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT 🚨🚨🚨
RESPOND EXCLUSIVELY IN {lang_name.upper()} ONLY.

{formatting_rules}

**STILLME STYLE SPEC V1 - {detected_domain.value.upper()} TEMPLATE (MANDATORY):**

{domain_guidance}

**TARGET DEPTH LEVEL: {target_depth.name} ({target_depth.value})**

**CRITICAL: If the original response is missing any part of the structure, ADD IT. All parts are MANDATORY.**

RESPOND IN {lang_name.upper()} ONLY."""

        user_prompt = f"""Rewrite this response to add philosophical/methodological depth:

Question: {original_question[:300]}

Original response (already honest, but needs more depth):
{text[:1000]}

Add:
- 3-tier philosophical analysis (if philosophical question)
- Methodological analysis (if academic question)
- Comparison with real concepts
- Source verification guidance

RESPOND IN {lang_name.upper()} ONLY."""

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    self.deepseek_base_url,
                    headers={
                        "Authorization": f"Bearer {self.deepseek_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 2000,  # Increased for deeper analysis
                        "temperature": 0.7
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        rewritten = data["choices"][0]["message"].get("content")
                        if rewritten and len(rewritten.strip()) > 100:
                            logger.info("✅ Rewrite 2 (Philosophical Depth): Successfully added depth")
                            return rewritten
        except Exception as e:
            logger.error(f"❌ Rewrite 2 (Philosophical Depth): Error: {e}")
        
        return None


# Singleton instance
_rewrite_depth_instance: Optional[RewritePhilosophicalDepth] = None


def get_rewrite_philosophical_depth() -> RewritePhilosophicalDepth:
    """Get singleton instance of RewritePhilosophicalDepth"""
    global _rewrite_depth_instance
    if _rewrite_depth_instance is None:
        _rewrite_depth_instance = RewritePhilosophicalDepth()
    return _rewrite_depth_instance

