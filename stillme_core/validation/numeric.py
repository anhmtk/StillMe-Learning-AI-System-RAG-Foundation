"""
NumericUnitsBasic validator - Detects numbers and suggests citations
"""

import re
from typing import List
from .base import ValidationResult
import logging

logger = logging.getLogger(__name__)

# Pattern to match numbers (integers and decimals)
NUM_RE = re.compile(r"\b\d+[.,]?\d*\b")


class NumericUnitsBasic:
    """Validator that detects numbers in answers"""
    
    def __init__(self, warn_only: bool = True):
        """
        Initialize numeric validator
        
        Args:
            warn_only: If True, only warn (don't fail) on numbers (default: True)
        """
        self.warn_only = warn_only
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Check if answer contains numbers
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents (unused for this validator)
            
        Returns:
            ValidationResult (always passes if warn_only=True)
        """
        has_number = bool(NUM_RE.search(answer))
        
        if has_number:
            logger.debug("Numbers detected in answer")
            # For MVP: only warn, don't fail
            # Future: could check if numbers are cited
            if self.warn_only:
                return ValidationResult(
                    passed=True,
                    reasons=["has_numbers:consider_citation"]
                )
            else:
                return ValidationResult(
                    passed=False,
                    reasons=["has_numbers:citation_required"]
                )
        else:
            return ValidationResult(passed=True)

