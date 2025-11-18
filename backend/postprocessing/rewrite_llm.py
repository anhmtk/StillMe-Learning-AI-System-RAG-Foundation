"""
Rewrite LLM - Conditional DeepSeek rewrite for quality improvement

Only rewrites when quality evaluator determines output needs improvement.
Uses DeepSeek (cost-effective) with minimal prompt to rewrite output
while preserving factual content.
"""

import logging
import os
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class RewriteLLM:
    """
    Conditional LLM rewrite using DeepSeek (cost-optimized)
    
    Only rewrites when quality evaluator flags output as needing improvement.
    Uses minimal prompt to keep costs low.
    """
    
    def __init__(self):
        """Initialize rewrite LLM"""
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_base_url = "https://api.deepseek.com/v1/chat/completions"
    
    async def rewrite(
        self,
        text: str,
        original_question: str,
        quality_issues: list,
        is_philosophical: bool = False,
        detected_lang: str = "en"
    ) -> str:
        """
        Rewrite text to improve quality while preserving factual content
        
        Args:
            text: Original output text (already sanitized)
            original_question: Original user question
            quality_issues: List of quality issues from evaluator
            is_philosophical: Whether this is a philosophical question
            detected_lang: Detected language code
            
        Returns:
            Rewritten text with improved quality
        """
        if not self.deepseek_api_key:
            logger.warning("DeepSeek API key not available, skipping rewrite")
            return text
        
        # Build minimal rewrite prompt (<200 tokens)
        rewrite_prompt = self._build_rewrite_prompt(
            text, original_question, quality_issues, is_philosophical, detected_lang
        )
        
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
                            {
                                "role": "system",
                                "content": self._build_system_prompt(is_philosophical, detected_lang)
                            },
                            {
                                "role": "user",
                                "content": rewrite_prompt
                            }
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        rewritten = data["choices"][0]["message"]["content"]
                        logger.info(f"✅ Successfully rewrote output (original: {len(text)} chars, rewritten: {len(rewritten)} chars)")
                        return rewritten
                    else:
                        logger.warning("DeepSeek rewrite returned unexpected format")
                        return text
                else:
                    logger.warning(f"DeepSeek rewrite failed: {response.status_code} - {response.text}")
                    return text
        except Exception as e:
            logger.error(f"Error during DeepSeek rewrite: {e}")
            return text  # Fallback to original
    
    def _build_system_prompt(self, is_philosophical: bool, detected_lang: str) -> str:
        """Build minimal system prompt for rewrite"""
        lang_name = "the same language" if detected_lang == "en" else detected_lang
        
        if is_philosophical:
            return f"""You are rewriting a philosophical response to improve quality.

CRITICAL RULES:
- Write in continuous prose paragraphs. NO emojis, NO markdown headings, NO bullets.
- Preserve ALL factual content from the original.
- Improve depth, structure, and philosophical rigor.
- Follow structure: Anchor → Unpack → Explore → Edge → Return.
- Respond in {lang_name} ONLY."""
        else:
            return f"""You are rewriting a response to improve quality.

CRITICAL RULES:
- Preserve ALL factual content from the original.
- Improve clarity, structure, and depth.
- Respond in {lang_name} ONLY."""
    
    def _build_rewrite_prompt(
        self,
        text: str,
        original_question: str,
        quality_issues: list,
        is_philosophical: bool,
        detected_lang: str
    ) -> str:
        """Build minimal rewrite prompt (<200 tokens)"""
        issues_text = ", ".join(quality_issues[:3])  # Limit to 3 issues
        
        # Truncate text to keep prompt small (max 600 chars for original response)
        truncated_text = text[:600] + "..." if len(text) > 600 else text
        truncated_question = original_question[:100] + "..." if len(original_question) > 100 else original_question
        
        if is_philosophical:
            prompt = f"""Rewrite this philosophical response to fix: {issues_text}

Q: {truncated_question}

Original:
{truncated_text}

REQUIREMENTS:
- Keep ALL factual content
- Improve depth and structure
- Use prose (no emojis, no bullets, no headings)
- Follow: Anchor → Unpack → Explore → Edge → Return
- Respond in {detected_lang}"""
        else:
            prompt = f"""Rewrite this response to fix: {issues_text}

Q: {truncated_question}

Original:
{truncated_text}

REQUIREMENTS:
- Keep ALL factual content
- Improve clarity and structure
- Respond in {detected_lang}"""
        
        return prompt


def get_rewrite_llm() -> RewriteLLM:
    """Get singleton instance of RewriteLLM"""
    if not hasattr(get_rewrite_llm, '_instance'):
        get_rewrite_llm._instance = RewriteLLM()
    return get_rewrite_llm._instance

