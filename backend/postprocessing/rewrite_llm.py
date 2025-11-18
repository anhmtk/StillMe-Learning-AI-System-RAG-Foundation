"""
Rewrite LLM - Conditional DeepSeek rewrite for quality improvement

Only rewrites when quality evaluator determines output needs improvement.
Uses DeepSeek (cost-effective) with minimal prompt to rewrite output
while preserving factual content.
"""

import logging
import os
from typing import Optional, Dict, Any, Tuple
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RewriteResult:
    """Result of rewrite operation"""
    text: str
    was_rewritten: bool
    error: Optional[str] = None


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
    ) -> RewriteResult:
        """
        Rewrite text to improve quality while preserving factual content
        
        Args:
            text: Original output text (already sanitized)
            original_question: Original user question
            quality_issues: List of quality issues from evaluator
            is_philosophical: Whether this is a philosophical question
            detected_lang: Detected language code
            
        Returns:
            RewriteResult with rewritten text and success flag
        """
        if not self.deepseek_api_key:
            logger.warning("DeepSeek API key not available, skipping rewrite")
            return RewriteResult(text=text, was_rewritten=False, error="API key not available")
        
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
                    try:
                        data = response.json()
                        if "choices" in data and len(data["choices"]) > 0:
                            rewritten = data["choices"][0]["message"].get("content")
                            
                            # CRITICAL: Check if content is None or empty
                            if not rewritten or not isinstance(rewritten, str):
                                logger.warning(f"DeepSeek rewrite returned None or invalid content (type: {type(rewritten)})")
                                return RewriteResult(
                                    text=text,
                                    was_rewritten=False,
                                    error="Rewrite returned None or invalid content"
                                )
                            
                            # Validate rewritten output length
                            if len(rewritten.strip()) < 50:
                                logger.warning(f"DeepSeek rewrite returned too short output ({len(rewritten)} chars)")
                                return RewriteResult(
                                    text=text,
                                    was_rewritten=False,
                                    error="Rewrite output too short"
                                )
                            
                            logger.info(
                                "✅ Successfully rewrote output (original: %d chars, rewritten: %d chars)",
                                len(text),
                                len(rewritten)
                            )
                            return RewriteResult(text=rewritten, was_rewritten=True)
                        else:
                            logger.warning("DeepSeek rewrite returned unexpected format: no choices in response")
                            return RewriteResult(
                                text=text,
                                was_rewritten=False,
                                error="Unexpected response format: no choices"
                            )
                    except (ValueError, KeyError) as parse_error:
                        logger.error(f"Failed to parse DeepSeek response JSON: {parse_error}")
                        return RewriteResult(
                            text=text,
                            was_rewritten=False,
                            error=f"JSON parse error: {str(parse_error)}"
                        )
                else:
                    error_text = response.text[:500] if response.text else "No error message"
                    error_msg = f"HTTP {response.status_code}: {error_text}"
                    logger.warning(f"⚠️ DeepSeek rewrite failed: {error_msg}")
                    return RewriteResult(
                        text=text,
                        was_rewritten=False,
                        error=error_msg
                    )
        except httpx.TimeoutException as timeout_error:
            logger.warning(f"⚠️ DeepSeek rewrite timeout after 30s: {timeout_error}")
            return RewriteResult(
                text=text,
                was_rewritten=False,
                error=f"Timeout after 30s: {str(timeout_error)}"
            )
        except httpx.RequestError as request_error:
            logger.error(f"DeepSeek rewrite request error: {request_error}")
            return RewriteResult(
                text=text,
                was_rewritten=False,
                error=f"Request error: {str(request_error)}"
            )
        except Exception as e:
            logger.error(f"Error during DeepSeek rewrite: {e}", exc_info=True)
            return RewriteResult(
                text=text,
                was_rewritten=False,
                error=f"Unexpected error: {str(e)}"
            )
    
    def _build_system_prompt(self, is_philosophical: bool, detected_lang: str) -> str:
        """Build minimal system prompt for rewrite"""
        # Get full language name for better clarity
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
        
        if is_philosophical:
            return f"""You are rewriting a philosophical response to improve quality.

🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - HIGHEST PRIORITY 🚨🚨🚨
THE USER'S QUESTION IS IN {lang_name.upper()}.
YOU MUST RESPOND EXCLUSIVELY IN {lang_name.upper()} ONLY.
DO NOT RESPOND IN ENGLISH, VIETNAMESE, OR ANY OTHER LANGUAGE.
EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN {lang_name.upper()}.
IF YOUR BASE MODEL WANTS TO RESPOND IN ANOTHER LANGUAGE, YOU MUST TRANSLATE IT TO {lang_name.upper()} BEFORE RETURNING.
UNDER NO CIRCUMSTANCES return a response in any language other than {lang_name.upper()}.
⚠️ REMINDER: RESPOND IN {lang_name.upper()} ONLY. TRANSLATE IF NECESSARY. ⚠️

CRITICAL RULES:
- Write in continuous prose paragraphs. NO emojis, NO markdown headings, NO bullets.
- Preserve ALL factual content from the original.
- Improve depth, structure, and philosophical rigor.
- Follow structure: Anchor → Unpack → Explore → Edge → Return.
- RESPOND IN {lang_name.upper()} ONLY."""
        else:
            return f"""You are rewriting a response to improve quality.

🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - HIGHEST PRIORITY 🚨🚨🚨
THE USER'S QUESTION IS IN {lang_name.upper()}.
YOU MUST RESPOND EXCLUSIVELY IN {lang_name.upper()} ONLY.
DO NOT RESPOND IN ENGLISH, VIETNAMESE, OR ANY OTHER LANGUAGE.
EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN {lang_name.upper()}.
IF YOUR BASE MODEL WANTS TO RESPOND IN ANOTHER LANGUAGE, YOU MUST TRANSLATE IT TO {lang_name.upper()} BEFORE RETURNING.
UNDER NO CIRCUMSTANCES return a response in any language other than {lang_name.upper()}.
⚠️ REMINDER: RESPOND IN {lang_name.upper()} ONLY. TRANSLATE IF NECESSARY. ⚠️

CRITICAL RULES:
- Preserve ALL factual content from the original.
- Improve clarity, structure, and depth.
- RESPOND IN {lang_name.upper()} ONLY."""
    
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
        
        # Get full language name for better clarity
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
        
        # Truncate text to keep prompt small (max 600 chars for original response)
        truncated_text = text[:600] + "..." if len(text) > 600 else text
        truncated_question = original_question[:100] + "..." if len(original_question) > 100 else original_question
        
        if is_philosophical:
            prompt = f"""Rewrite this philosophical response to fix: {issues_text}

Q (in {lang_name}): {truncated_question}

Original response:
{truncated_text}

🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT 🚨🚨🚨
THE USER'S QUESTION IS IN {lang_name.upper()}.
YOU MUST RESPOND EXCLUSIVELY IN {lang_name.upper()} ONLY.
DO NOT RESPOND IN ENGLISH OR ANY OTHER LANGUAGE.
EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN {lang_name.upper()}.
IF THE ORIGINAL RESPONSE IS IN ANOTHER LANGUAGE, YOU MUST TRANSLATE IT TO {lang_name.upper()}.
⚠️ RESPOND IN {lang_name.upper()} ONLY. TRANSLATE IF NECESSARY. ⚠️

REQUIREMENTS:
- Keep ALL factual content
- Improve depth and structure
- Use prose (no emojis, no bullets, no headings)
- Follow: Anchor → Unpack → Explore → Edge → Return
- RESPOND IN {lang_name.upper()} ONLY"""
        else:
            prompt = f"""Rewrite this response to fix: {issues_text}

Q (in {lang_name}): {truncated_question}

Original response:
{truncated_text}

🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT 🚨🚨🚨
THE USER'S QUESTION IS IN {lang_name.upper()}.
YOU MUST RESPOND EXCLUSIVELY IN {lang_name.upper()} ONLY.
DO NOT RESPOND IN ENGLISH OR ANY OTHER LANGUAGE.
EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN {lang_name.upper()}.
IF THE ORIGINAL RESPONSE IS IN ANOTHER LANGUAGE, YOU MUST TRANSLATE IT TO {lang_name.upper()}.
⚠️ RESPOND IN {lang_name.upper()} ONLY. TRANSLATE IF NECESSARY. ⚠️

REQUIREMENTS:
- Keep ALL factual content
- Improve clarity and structure
- RESPOND IN {lang_name.upper()} ONLY"""
        
        return prompt


def get_rewrite_llm() -> RewriteLLM:
    """Get singleton instance of RewriteLLM"""
    if not hasattr(get_rewrite_llm, '_instance'):
        get_rewrite_llm._instance = RewriteLLM()
    return get_rewrite_llm._instance

