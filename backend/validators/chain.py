"""
ValidatorChain - Orchestrates multiple validators
"""

from typing import List, Dict, Set, Optional
from .base import Validator, ValidationResult
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

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
    
    def _can_run_parallel(self, validator: Validator, validator_name: str) -> bool:
        """
        Check if a validator can run in parallel with others.
        
        Validators that can run in parallel:
        - CitationRelevance: Only reads answer and ctx_docs, doesn't modify
        - EvidenceOverlap: Only reads answer and ctx_docs, doesn't modify
        - NumericUnitsBasic: Only reads answer, doesn't modify
        - EthicsAdapter: Only reads answer, doesn't modify
        
        Validators that MUST run sequentially:
        - LanguageValidator: Must run first (highest priority)
        - CitationRequired: Must run before CitationRelevance (provides citations)
        - ConfidenceValidator: May depend on other validators' results
        
        Args:
            validator: Validator instance
            validator_name: Name of validator class
            
        Returns:
            True if validator can run in parallel, False otherwise
        """
        # Validators that can run in parallel (read-only, no dependencies)
        parallel_safe = {
            "CitationRelevance",
            "EvidenceOverlap", 
            "NumericUnitsBasic",
            "SchemaFormat",
            "EthicsAdapter",
            "EgoNeutralityValidator"  # Read-only detection, can run in parallel
        }
        
        # Validators that must run sequentially (have dependencies or modify state)
        sequential_only = {
            "LanguageValidator",  # Must run first
            "CitationRequired",   # Must run before CitationRelevance
            "ConfidenceValidator" # May depend on other results
        }
        
        if validator_name in sequential_only:
            return False
        if validator_name in parallel_safe:
            return True
        
        # Default: sequential for safety
        return False
    
    def run(self, answer: str, ctx_docs: List[str], context_quality: Optional[str] = None,
            avg_similarity: Optional[float] = None) -> ValidationResult:
        """
        Run all validators with parallel execution for independent validators
        
        OPTIMIZATION: 
        - Early exit for critical failures (language_mismatch, missing_citation without patch)
        - Parallel execution for independent validators (CitationRelevance, EvidenceOverlap, etc.)
        This reduces latency when validation fails early and speeds up independent validators.
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents from RAG
            context_quality: Context quality from RAG ("high", "medium", "low") - Tier 3.5
            avg_similarity: Average similarity score of retrieved context (0.0-1.0) - Tier 3.5
            
        Returns:
            ValidationResult with overall status
        """
        reasons: List[str] = []
        patched = answer
        has_citation = False
        low_overlap_only = False
        
        # Group validators into sequential and parallel groups
        sequential_validators = []
        parallel_validators = []
        
        for i, validator in enumerate(self.validators):
            validator_name = type(validator).__name__
            if self._can_run_parallel(validator, validator_name):
                parallel_validators.append((i, validator, validator_name))
            else:
                sequential_validators.append((i, validator, validator_name))
        
        # Run sequential validators first (LanguageValidator, CitationRequired, etc.)
        for i, validator, validator_name in sequential_validators:
            try:
                # Tier 3.5: Pass context quality to ConfidenceValidator
                if validator_name == "ConfidenceValidator":
                    result = validator.run(patched, ctx_docs, context_quality=context_quality, avg_similarity=avg_similarity)
                else:
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
        
        # OPTIMIZATION: Run parallel validators concurrently (if any)
        if parallel_validators:
            logger.debug(f"Running {len(parallel_validators)} validators in parallel...")
            parallel_results: Dict[int, ValidationResult] = {}
            
            try:
                with ThreadPoolExecutor(max_workers=len(parallel_validators)) as executor:
                    # Submit all parallel validators
                    future_to_validator = {
                        executor.submit(validator.run, patched, ctx_docs): (i, validator_name)
                        for i, validator, validator_name in parallel_validators
                    }
                    
                    # Collect results as they complete
                    for future in as_completed(future_to_validator):
                        i, validator_name = future_to_validator[future]
                        try:
                            result = future.result()
                            parallel_results[i] = result
                        except Exception as e:
                            logger.error(f"Parallel validator {i} ({validator_name}) error: {e}")
                            parallel_results[i] = ValidationResult(
                                passed=False,
                                reasons=[f"validator_error:{validator_name}:{str(e)}"]
                            )
                
                # Process parallel results
                for i, validator, validator_name in parallel_validators:
                    if i in parallel_results:
                        result = parallel_results[i]
                        
                        if not result.passed:
                            reasons.extend(result.reasons)
                            logger.debug(
                                f"Parallel validator {i} ({validator_name}) failed: {result.reasons}"
                            )
                        else:
                            # Update patched answer if validator provided one
                            if result.patched_answer:
                                patched = result.patched_answer
                                logger.debug(f"Applied patch from parallel validator {i}")
            except Exception as parallel_error:
                # Fallback to sequential if parallel execution fails
                logger.warning(f"Parallel validation failed, falling back to sequential: {parallel_error}")
                for i, validator, validator_name in parallel_validators:
                    try:
                        result = validator.run(patched, ctx_docs)
                        if not result.passed:
                            reasons.extend(result.reasons)
                        if result.patched_answer:
                            patched = result.patched_answer
                    except Exception as e:
                        logger.error(f"Fallback validator {i} ({validator_name}) error: {e}")
                        reasons.append(f"validator_error:{validator_name}:{str(e)}")
        
        # All validators passed or were patched, or low_overlap was allowed due to citation
        return ValidationResult(
            passed=True,
            reasons=reasons,
            patched_answer=patched if patched != answer else None
        )

