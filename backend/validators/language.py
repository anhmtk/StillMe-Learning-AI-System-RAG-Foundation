"""
LanguageValidator - Ensures output language matches input language
Prevents "language drift" where AI responds in wrong language
"""

import logging
from typing import List, Optional
from .base import ValidationResult
from backend.api.utils.chat_helpers import detect_language

logger = logging.getLogger(__name__)


class LanguageValidator:
    """Validator that ensures output language matches input language"""
    
    def __init__(self, input_language: str):
        """
        Initialize language validator
        
        Args:
            input_language: The language code of the user's input (e.g., 'en', 'vi', 'es')
        """
        self.input_language = input_language
        logger.debug(f"LanguageValidator initialized for input language: {input_language}")
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Check if answer language matches input language
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents (not used for language validation)
            
        Returns:
            ValidationResult with language match status
        """
        if not answer or len(answer.strip()) == 0:
            return ValidationResult(passed=True)  # Empty answer, skip validation
        
        # Detect language of the answer
        detected_output_lang = detect_language(answer)
        
        # Check if output language matches input language
        if detected_output_lang == self.input_language:
            logger.debug(f"Language match: output={detected_output_lang}, input={self.input_language}")
            return ValidationResult(passed=True)
        else:
            logger.warning(
                f"Language mismatch detected: output={detected_output_lang}, input={self.input_language}. "
                f"Answer starts with: {answer[:100]}"
            )
            
            # Try to generate patched answer (translate to correct language)
            # Note: This is a simple approach - in production, you might want to use a translation API
            patched_answer = self._attempt_translation(answer, self.input_language)
            
            return ValidationResult(
                passed=False,
                reasons=[f"language_mismatch:output={detected_output_lang},expected={self.input_language}"],
                patched_answer=patched_answer if patched_answer else None
            )
    
    def _attempt_translation(self, answer: str, target_lang: str) -> Optional[str]:
        """
        Attempt to translate answer to target language
        This is a placeholder - in production, you might want to use a translation API
        
        For now, we'll return None and let the system handle it through fallback
        or the LLM can be asked to retranslate
        
        Args:
            answer: Answer in wrong language
            target_lang: Target language code
            
        Returns:
            Translated answer or None if translation not available
        """
        # TODO: Implement translation using translation API or LLM
        # For now, return None to trigger fallback or retry
        logger.debug(f"Translation not implemented yet, returning None for language fix")
        return None

