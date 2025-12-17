"""
Verbosity Validator - Detects overly verbose or defensive responses

This validator measures response length vs question complexity and flags:
- Overly verbose responses (length_ratio > threshold)
- Defensive tone patterns
- Unnecessary repetition

This addresses the issue where StillMe responses can be overly long or self-defensive,
creating cognitive overload or "ideology over clarity".
"""

import re
import logging
from typing import List, Optional
from .base import Validator, ValidationResult

logger = logging.getLogger(__name__)


class VerbosityValidator(Validator):
    """
    Validator that detects overly verbose or defensive responses
    
    Measures:
    - Response length vs question length ratio
    - Defensive tone patterns
    - Unnecessary repetition
    """
    
    def __init__(self, max_length_ratio: float = 3.0, strict_mode: bool = False):
        """
        Initialize verbosity validator
        
        Args:
            max_length_ratio: Maximum response length / question length ratio (default: 3.0)
            strict_mode: If True, fail when verbose. If False, only warn.
        """
        self.max_length_ratio = max_length_ratio
        self.strict_mode = strict_mode
        
        # Defensive tone patterns
        self.defensive_patterns = [
            r"mình (phải|phải|phải) (nhấn mạnh|nhắc lại|giải thích)",
            r"i (must|need to) (emphasize|repeat|explain)",
            r"(như đã nói|as mentioned|as stated) (ở trên|above|earlier)",
            r"(một lần nữa|once again|again)",
            r"(để rõ ràng|to be clear|for clarity)",
            r"(xin lỗi|sorry) (nhưng|but)",
        ]
        
        # Repetition patterns (same phrase repeated)
        self.repetition_patterns = [
            r"(.{10,})\s+\1\s+\1",  # Same phrase 3+ times
        ]
        
        # Compile patterns
        self.defensive_re = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.defensive_patterns
        ]
        self.repetition_re = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.repetition_patterns
        ]
    
    def run(self, answer: str, ctx_docs: List[str], user_question: Optional[str] = None) -> ValidationResult:
        """
        Check if answer is overly verbose or defensive
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents (not used)
            user_question: Optional user question for context
            
        Returns:
            ValidationResult with passed status and warnings
        """
        if not answer or not user_question:
            return ValidationResult(passed=True)
        
        question_length = len(user_question.strip())
        answer_length = len(answer.strip())
        
        if question_length == 0:
            return ValidationResult(passed=True)
        
        # Calculate length ratio
        length_ratio = answer_length / question_length
        
        reasons = []
        
        # Check length ratio
        if length_ratio > self.max_length_ratio:
            reasons.append(f"overly_verbose: length_ratio={length_ratio:.2f} (max={self.max_length_ratio})")
            logger.debug(
                f"VerbosityValidator: Overly verbose response detected "
                f"(ratio={length_ratio:.2f}, question={question_length}, answer={answer_length})"
            )
        
        # Check for defensive tone
        answer_lower = answer.lower()
        has_defensive_tone = any(
            pattern.search(answer_lower) 
            for pattern in self.defensive_re
        )
        
        if has_defensive_tone:
            reasons.append("defensive_tone_detected")
            logger.debug("VerbosityValidator: Defensive tone detected")
        
        # Check for repetition
        has_repetition = any(
            pattern.search(answer) 
            for pattern in self.repetition_re
        )
        
        if has_repetition:
            reasons.append("unnecessary_repetition_detected")
            logger.debug("VerbosityValidator: Unnecessary repetition detected")
        
        # Determine result
        if reasons:
            if self.strict_mode and length_ratio > self.max_length_ratio * 2:
                # Very verbose (2x threshold) → fail
                logger.warning(
                    f"VerbosityValidator: FAILED - Very verbose response "
                    f"(ratio={length_ratio:.2f}, reasons={reasons})"
                )
                return ValidationResult(
                    passed=False,
                    reasons=reasons
                )
            else:
                # Warn but don't fail
                logger.debug(
                    f"VerbosityValidator: WARNINGS - {reasons}"
                )
                return ValidationResult(
                    passed=True,
                    reasons=reasons
                )
        
        # All good
        return ValidationResult(passed=True)

