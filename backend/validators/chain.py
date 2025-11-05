"""
ValidatorChain - Orchestrates multiple validators
"""

from typing import List
from .base import Validator, ValidationResult
import logging

logger = logging.getLogger(__name__)


class ValidatorChain:
    """Chain of validators to run sequentially"""
    
    def __init__(self, validators: List[Validator]):
        """
        Initialize validator chain
        
        Args:
            validators: List of validators to run in order
        """
        self.validators = validators
        logger.info(f"ValidatorChain initialized with {len(validators)} validators")
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Run all validators in sequence
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents from RAG
            
        Returns:
            ValidationResult with overall status
        """
        reasons: List[str] = []
        patched = answer
        
        for i, validator in enumerate(self.validators):
            try:
                result = validator.run(patched, ctx_docs)
                
                if not result.passed:
                    reasons.extend(result.reasons)
                    logger.debug(
                        f"Validator {i} ({type(validator).__name__}) failed: {result.reasons}"
                    )
                    
                    # Use patched answer if available
                    if result.patched_answer:
                        patched = result.patched_answer
                        logger.debug(f"Using patched answer from validator {i}")
                    else:
                        # Fail fast if no patch available
                        logger.warning(
                            f"Validator {i} ({type(validator).__name__}) failed without patch"
                        )
                        return ValidationResult(
                            passed=False,
                            reasons=reasons,
                            patched_answer=None
                        )
                else:
                    # Update patched answer if validator provided one (even if passed)
                    if result.patched_answer:
                        patched = result.patched_answer
                        logger.debug(f"Applied patch from validator {i}")
                        
            except Exception as e:
                logger.error(f"Validator {i} ({type(validator).__name__}) error: {e}")
                reasons.append(f"validator_error:{type(validator).__name__}:{str(e)}")
                # Continue with next validator on error
        
        # All validators passed or were patched
        return ValidationResult(
            passed=True,
            reasons=reasons,
            patched_answer=patched if patched != answer else None
        )

