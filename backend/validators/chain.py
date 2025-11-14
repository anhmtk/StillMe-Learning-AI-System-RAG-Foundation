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
        
        OPTIMIZATION: Early exit for critical failures (language_mismatch, missing_citation without patch)
        This reduces latency when validation fails early, avoiding unnecessary validator runs.
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents from RAG
            
        Returns:
            ValidationResult with overall status
        """
        reasons: List[str] = []
        patched = answer
        has_citation = False
        low_overlap_only = False
        
        for i, validator in enumerate(self.validators):
            try:
                result = validator.run(patched, ctx_docs)
                
                # Track citation status
                if "CitationRequired" in type(validator).__name__:
                    has_citation = result.passed
                
                if not result.passed:
                    reasons.extend(result.reasons)
                    logger.debug(
                        f"Validator {i} ({type(validator).__name__}) failed: {result.reasons}"
                    )
                    
                    # Check if this is only a low_overlap issue
                    if any("low_overlap" in r for r in result.reasons):
                        low_overlap_only = True
                    
                    # Use patched answer if available
                    if result.patched_answer:
                        patched = result.patched_answer
                        logger.debug(f"Using patched answer from validator {i}")
                        
                        # If validator provided patched_answer, continue with patched version
                        # This allows subsequent validators to validate the patched answer
                        # Special case: If this is missing_citation with patched_answer, continue
                        if any("missing_citation" in r for r in result.reasons):
                            logger.info(
                                f"Validator {i} ({type(validator).__name__}) fixed missing_citation with patched_answer, continuing..."
                            )
                            # Continue to next validator with patched answer
                        elif any("language_mismatch" in r for r in result.reasons):
                            logger.info(
                                f"Validator {i} ({type(validator).__name__}) fixed language_mismatch with patched_answer, continuing..."
                            )
                            # Continue to next validator with corrected answer
                        # For other cases, continue with patched answer
                    else:
                        # Special handling: If we have citation but only low_overlap, don't block
                        # Citation is more important than overlap score (LLM may translate/summarize)
                        if has_citation and low_overlap_only and not any("missing_citation" in r for r in reasons):
                            logger.info(
                                f"Validator {i} ({type(validator).__name__}) failed with low_overlap, "
                                f"but citation exists - allowing response"
                            )
                            # Continue - don't fail fast
                        elif any("language_mismatch" in r for r in reasons):
                            # OPTIMIZATION: Early exit for language mismatch (critical failure)
                            # Language mismatch is critical - fail fast to avoid running remaining validators
                            logger.warning(
                                f"Validator {i} ({type(validator).__name__}) failed: language_mismatch (critical) without patch - early exit"
                            )
                            # No translation available - this is critical, return failure immediately
                            return ValidationResult(
                                passed=False,
                                reasons=reasons,
                                patched_answer=None
                            )
                        elif any("missing_citation" in r for r in reasons):
                            # OPTIMIZATION: Early exit for missing citation without patch (critical failure)
                            # Missing citation is critical but no patched_answer available
                            # This should not happen if CitationRequired is working correctly
                            logger.warning(
                                f"Validator {i} ({type(validator).__name__}) failed: missing_citation (critical) without patch - early exit"
                            )
                            return ValidationResult(
                                passed=False,
                                reasons=reasons,
                                patched_answer=None
                            )
                        else:
                            # Fail fast for other critical errors
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
        
        # All validators passed or were patched, or low_overlap was allowed due to citation
        return ValidationResult(
            passed=True,
            reasons=reasons,
            patched_answer=patched if patched != answer else None
        )

