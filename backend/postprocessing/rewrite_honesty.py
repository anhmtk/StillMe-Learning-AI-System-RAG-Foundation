"""
Rewrite 1 - Honesty & Boundary (Option B Pipeline)

MANDATORY rewrite pass that:
1. Removes 100% of content lacking evidence
2. Eliminates self-contradictory statements (e.g., "I don't know" + detailed explanation)
3. Replaces hallucinated content with honest fallback
4. Ensures no fabrication, even with disclaimers

CRITICAL: This rewrite MUST run before Rewrite 2 (Philosophical Depth).
It acts as a "police of honesty" - cutting out all unsupported content.
"""

import logging
import os
from typing import Optional, Dict, Any, List
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HonestyRewriteResult:
    """Result of honesty rewrite"""
    text: str
    was_rewritten: bool
    used_fallback: bool  # True if replaced with EPD-Fallback
    error: Optional[str] = None


class RewriteHonesty:
    """
    Rewrite 1: Honesty & Boundary
    
    Removes all content lacking evidence and ensures complete honesty.
    If hallucination is detected, replaces entire response with EPD-Fallback.
    """
    
    def __init__(self):
        """Initialize honesty rewrite"""
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_base_url = "https://api.deepseek.com/v1/chat/completions"
    
    async def rewrite(
        self,
        text: str,
        original_question: str,
        hallucination_detection: object,  # HallucinationDetection from HallucinationGuardV2
        ctx_docs: List[str],
        question_type: str,
        detected_lang: str = "en"
    ) -> HonestyRewriteResult:
        """
        Rewrite to ensure complete honesty
        
        Args:
            text: Original LLM response
            original_question: User question
            hallucination_detection: HallucinationDetection from HallucinationGuardV2
            ctx_docs: Context documents from RAG
            question_type: Question type (from QuestionClassifierV2)
            detected_lang: Detected language code
            
        Returns:
            HonestyRewriteResult
        """
        # If hallucination detected, use EPD-Fallback immediately
        if hallucination_detection.is_hallucination:
            logger.warning(
                f"🛡️ Rewrite 1 (Honesty): Hallucination detected, using EPD-Fallback. "
                f"Reasons: {hallucination_detection.reasons}"
            )
            
            from backend.guards.epistemic_fallback import get_epistemic_fallback_generator
            generator = get_epistemic_fallback_generator()
            
            # Get suspicious entity
            suspicious_entity = (
                hallucination_detection.detected_entities[0] 
                if hallucination_detection.detected_entities 
                else None
            )
            
            # Generate EPD-Fallback
            fallback_text = generator.generate_epd_fallback(
                question=original_question,
                detected_lang=detected_lang,
                suspicious_entity=suspicious_entity
            )
            
            return HonestyRewriteResult(
                text=fallback_text,
                was_rewritten=True,
                used_fallback=True
            )
        
        # If no hallucination but has contradiction, rewrite to remove contradiction
        if hallucination_detection.has_contradiction:
            logger.info(
                "🔄 Rewrite 1 (Honesty): Self-contradiction detected, rewriting to remove contradiction"
            )
            
            # Use DeepSeek to rewrite and remove contradiction
            if not self.deepseek_api_key:
                logger.warning("DeepSeek API key not available, cannot rewrite contradiction")
                return HonestyRewriteResult(
                    text=text,
                    was_rewritten=False,
                    used_fallback=False,
                    error="API key not available"
                )
            
            rewritten = await self._rewrite_contradiction(
                text, original_question, detected_lang
            )
            
            if rewritten:
                return HonestyRewriteResult(
                    text=rewritten,
                    was_rewritten=True,
                    used_fallback=False
                )
        
        # No issues detected, return original
        return HonestyRewriteResult(
            text=text,
            was_rewritten=False,
            used_fallback=False
        )
    
    async def _rewrite_contradiction(
        self,
        text: str,
        original_question: str,
        detected_lang: str
    ) -> Optional[str]:
        """
        Rewrite to remove self-contradiction
        
        Args:
            text: Original text with contradiction
            original_question: User question
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
        
        system_prompt = f"""You are rewriting a response to remove self-contradiction.

🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT 🚨🚨🚨
RESPOND EXCLUSIVELY IN {lang_name.upper()} ONLY.

CRITICAL RULE: The original response contains a contradiction:
- It says "I don't know" / "không tìm thấy nguồn" / "not enough information"
- BUT then provides detailed explanations as if it knows

YOUR TASK:
1. Remove ALL detailed explanations that contradict the uncertainty statement
2. Keep ONLY the honest acknowledgment of uncertainty
3. If you can provide analysis of WHY the concept seems hypothetical, do so (but do NOT fabricate details)
4. Do NOT keep any fabricated details, citations, or descriptions

RESPOND IN {lang_name.upper()} ONLY."""

        user_prompt = f"""Rewrite this response to remove self-contradiction:

Question: {original_question[:200]}

Original response (contains contradiction):
{text[:800]}

Remove all detailed explanations that contradict uncertainty statements.
Keep only honest acknowledgment and analysis of why concept seems hypothetical.

RESPOND IN {lang_name.upper()} ONLY."""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
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
                        "max_tokens": 1500,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        rewritten = data["choices"][0]["message"].get("content")
                        if rewritten and len(rewritten.strip()) > 50:
                            logger.info("✅ Rewrite 1 (Honesty): Successfully removed contradiction")
                            return rewritten
        except Exception as e:
            logger.error(f"❌ Rewrite 1 (Honesty): Error rewriting contradiction: {e}")
        
        return None


# Singleton instance
_rewrite_honesty_instance: Optional[RewriteHonesty] = None


def get_rewrite_honesty() -> RewriteHonesty:
    """Get singleton instance of RewriteHonesty"""
    global _rewrite_honesty_instance
    if _rewrite_honesty_instance is None:
        _rewrite_honesty_instance = RewriteHonesty()
    return _rewrite_honesty_instance

