"""
SchemaFormat validator - Checks if answer matches required format/sections
"""

from typing import List, Optional
from .base import Validator, ValidationResult
import logging

logger = logging.getLogger(__name__)


class SchemaFormat:
    """Validator that checks answer format/sections"""
    
    def __init__(self, require_sections: Optional[List[str]] = None):
        """
        Initialize schema format validator
        
        Args:
            require_sections: List of required section names (e.g., ["Summary", "Details"])
        """
        self.require_sections = require_sections or []
        logger.info(
            f"SchemaFormat initialized with {len(self.require_sections)} required sections"
        )
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Check if answer contains required sections
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents (unused for this validator)
            
        Returns:
            ValidationResult with missing sections
        """
        if not self.require_sections:
            # No requirements, always pass
            return ValidationResult(passed=True)
        
        # Check if each required section exists (case-insensitive)
        answer_lower = answer.lower()
        missing = [
            section for section in self.require_sections
            if section.lower() not in answer_lower
        ]
        
        if missing:
            logger.warning(f"Missing sections: {missing}")
            return ValidationResult(
                passed=False,
                reasons=[f"missing_section:{s}" for s in missing]
            )
        else:
            return ValidationResult(passed=True)

