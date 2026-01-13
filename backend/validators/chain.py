"""
ValidatorChain - Orchestrates multiple validators
"""

from typing import List, Dict, Set, Optional, Any
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
        
        NPR-Inspired Optimization:
        - Validators that can run in parallel: Read-only, no dependencies on other validators' results
        - Validators that must run sequentially: Have dependencies or modify shared state
        
        Args:
            validator: Validator instance
            validator_name: Name of validator class
            
        Returns:
            True if validator can run in parallel, False otherwise
        """
        # Validators that MUST run sequentially (have dependencies or modify state)
        sequential_only = {
            "LanguageValidator",      # Must run FIRST (highest priority)
            "CitationRequired",        # Must run before CitationRelevance (provides citations)
            "CitationRelevance",       # DEPENDS on CitationRequired (needs citations to validate)
            "SourceConsensusValidator", # Must run after EvidenceOverlap, before ConfidenceValidator
            "ConfidenceValidator",     # May depend on other validators' results (SourceConsensusValidator, EvidenceOverlap)
            "FactualHallucinationValidator",  # Critical validator, run sequentially for safety
            "ReligiousChoiceValidator", # Critical validator, run sequentially for safety
        }
        
        # Validators that can run in parallel (read-only, no dependencies)
        # These validators only read answer and ctx_docs, don't depend on other validators' results
        parallel_safe = {
            "EvidenceOverlap",         # Reads answer and ctx_docs only
            "NumericUnitsBasic",       # Reads answer only
            "SchemaFormat",            # Reads answer only
            "EgoNeutralityValidator",  # Reads answer and ctx_docs only
            "IdentityCheckValidator",   # Reads answer only
            "PhilosophicalDepthValidator",  # Reads answer only
            "EthicsAdapter",            # Reads answer only (but should run last for safety)
        }
        
        # Check sequential first (higher priority)
        if validator_name in sequential_only:
            return False
        
        # Check parallel safe
        if validator_name in parallel_safe:
            return True
        
        # Default: sequential for safety (unknown validators)
        logger.warning(f"Unknown validator {validator_name}, running sequentially for safety")
        return False
    
    def run(self, answer: str, ctx_docs: List[str], context_quality: Optional[str] = None,
            avg_similarity: Optional[float] = None, is_philosophical: bool = False,
            is_religion_roleplay: bool = False, user_question: Optional[str] = None,
            context: Optional[Dict[str, Any]] = None, is_real_time_question: bool = False) -> ValidationResult:
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
            is_philosophical: If True, relax citation and confidence requirements for philosophical questions
            is_religion_roleplay: If True, skip force template for religion/roleplay questions (they should answer from identity prompt)
            
        Returns:
            ValidationResult with overall status
        """
        import time
        validation_start = time.time()
        
        reasons: List[str] = []
        patched = answer
        has_citation = False
        low_overlap_only = False
        has_critical_failure = False  # Track if any critical validator failed without patch
        
        # Group validators into sequential and parallel groups
        sequential_validators = []
        parallel_validators = []
        
        for i, validator in enumerate(self.validators):
            validator_name = type(validator).__name__
            if self._can_run_parallel(validator, validator_name):
                parallel_validators.append((i, validator, validator_name))
            else:
                sequential_validators.append((i, validator, validator_name))
        
        logger.debug(f"🔍 [NPR] Validator grouping: {len(sequential_validators)} sequential, {len(parallel_validators)} parallel")
        
        # Run sequential validators first (LanguageValidator, CitationRequired, etc.)
        sequential_start = time.time()
        for i, validator, validator_name in sequential_validators:
            try:
                # Tier 3.5: Pass context quality to ConfidenceValidator
                if validator_name == "ConfidenceValidator":
                    # Pass previous reasons and user_question to ConfidenceValidator so it can detect source_contradiction
                    # and use human-readable citations in uncertainty templates
                    # CRITICAL: Pass is_real_time_question to skip disclaimer for real-time questions (time, weather, etc.)
                    result = validator.run(patched, ctx_docs, context_quality=context_quality, avg_similarity=avg_similarity, is_philosophical=is_philosophical, is_religion_roleplay=is_religion_roleplay, previous_reasons=reasons, user_question=user_question, context=context, is_real_time_question=is_real_time_question)
                elif validator_name == "CitationRequired":
                    # Pass is_philosophical, user_question, and context to CitationRequired
                    # user_question is needed to detect real factual questions (even with philosophical elements)
                    # context is needed to detect foundational knowledge for specific citations
                    # Note: context may not be available in all call paths, so it's optional
                    result = validator.run(patched, ctx_docs, is_philosophical=is_philosophical, user_question=user_question, context=context)
                elif validator_name == "FactualHallucinationValidator":
                    # Pass user_question to FactualHallucinationValidator
                    result = validator.run(patched, ctx_docs, user_question=user_question)
                elif validator_name == "SourceConsensusValidator":
                    # Pass user_question to SourceConsensusValidator for context
                    result = validator.run(patched, ctx_docs, user_question=user_question)
                elif validator_name == "IdentityCheckValidator":
                    # Pass is_philosophical to IdentityCheckValidator
                    # Philosophical questions don't require humility when no context (theoretical reasoning)
                    result = validator.run(patched, ctx_docs, is_philosophical=is_philosophical)
                else:
                    result = validator.run(patched, ctx_docs)
                
                # Track citation status
                if "CitationRequired" in type(validator).__name__:
                    has_citation = result.passed
                
                # CRITICAL: Check for patched_answer even when passed=True
                # This allows validators to improve responses (e.g., convert numeric citations to human-readable)
                # even when validation passed
                if result.patched_answer and result.patched_answer != patched:
                    patched = result.patched_answer
                    logger.debug(f"Using patched answer from validator {i} (passed=True, improvement made)")
                
                if not result.passed:
                    reasons.extend(result.reasons)
                    logger.debug(
                        f"Validator {i} ({type(validator).__name__}) failed: {result.reasons}"
                    )
                    
                    # Check if this is only a low_overlap issue
                    if any("low_overlap" in r for r in result.reasons):
                        low_overlap_only = True
                    
                    # Check if this is a source_contradiction (should trigger uncertainty in ConfidenceValidator)
                    if any("source_contradiction" in r for r in result.reasons):
                        logger.info(
                            f"Validator {i} ({type(validator).__name__}) detected source contradiction - "
                            f"ConfidenceValidator will handle uncertainty expression"
                        )
                        # Don't fail fast - let ConfidenceValidator handle it
                        # Mark that we have a source contradiction for ConfidenceValidator
                    
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
                            # CRITICAL FIX: Don't early exit if patched_answer is available
                            # CitationRequired should ALWAYS provide patched_answer when citation is missing
                            # If patched_answer exists, continue with it (don't early exit)
                            if result.patched_answer:
                                logger.info(
                                    f"Validator {i} ({type(validator).__name__}) fixed missing_citation with patched_answer, continuing..."
                                )
                                patched = result.patched_answer
                                # Continue to next validator with patched answer
                            else:
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
                        elif any("future_dates_detected" in r for r in reasons):
                            # CRITICAL: FutureDatesValidator detected future dates - this is a hallucination
                            # Block response immediately - don't allow hallucinated dates
                            logger.warning(
                                f"Validator {i} ({type(validator).__name__}) failed: future_dates_detected (critical) - BLOCKING response to prevent hallucination"
                            )
                            return ValidationResult(
                                passed=False,
                                reasons=reasons,
                                patched_answer=None  # Don't allow patched answer - block the response
                            )
                        else:
                            # Track critical failure (no patch available)
                            has_critical_failure = True
                            logger.warning(
                                f"Validator {i} ({type(validator).__name__}) failed without patch: {result.reasons}"
                            )
                            # Don't fail fast for non-critical errors - continue to collect all failures
                            # But mark that we have a critical failure
                else:
                    # Update patched answer if validator provided one (even if passed)
                    if result.patched_answer:
                        patched = result.patched_answer
                        logger.debug(f"Applied patch from validator {i}")
                        
            except Exception as e:
                logger.error(f"Validator {i} ({type(validator).__name__}) error: {e}")
                reasons.append(f"validator_error:{type(validator).__name__}:{str(e)}")
                # Continue with next validator on error
        
        sequential_time = time.time() - sequential_start
        if sequential_validators:
            logger.debug(f"⏱️ [NPR] Sequential validators completed in {sequential_time:.3f}s ({len(sequential_validators)} validators)")
        
        # NPR-INSPIRED OPTIMIZATION: Run parallel validators concurrently (if any)
        if parallel_validators:
            import time
            parallel_start = time.time()
            logger.debug(f"🚀 [NPR] Running {len(parallel_validators)} validators in parallel...")
            parallel_results: Dict[int, ValidationResult] = {}
            
            def _run_parallel_validator(validator, validator_name, patched_answer, ctx_docs_list, user_q=None):
                """Helper function to run validator with correct parameters"""
                validator_start = time.time()
                try:
                    # Pass user_question to validators that need it
                    if validator_name == "FactualHallucinationValidator":
                        result = validator.run(patched_answer, ctx_docs_list, user_question=user_q)
                    elif validator_name == "SourceConsensusValidator":
                        result = validator.run(patched_answer, ctx_docs_list, user_question=user_q)
                    else:
                        result = validator.run(patched_answer, ctx_docs_list)
                    validator_time = time.time() - validator_start
                    logger.debug(f"⏱️ [NPR] {validator_name} completed in {validator_time:.3f}s")
                    return result
                except Exception as e:
                    logger.error(f"Parallel validator {validator_name} error: {e}")
                    return ValidationResult(
                        passed=False,
                        reasons=[f"validator_error:{validator_name}:{str(e)}"]
                    )
            
            try:
                # NPR: Optimize max_workers based on validator count and CPU cores
                import os
                cpu_count = os.cpu_count() or 4
                optimal_workers = min(len(parallel_validators), cpu_count, 8)  # Cap at 8 for safety
                
                with ThreadPoolExecutor(max_workers=optimal_workers) as executor:
                    # Submit all parallel validators with correct parameters
                    future_to_validator = {
                        executor.submit(
                            _run_parallel_validator,
                            validator,
                            validator_name,
                            patched,
                            ctx_docs,
                            user_question
                        ): (i, validator_name)
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
                
                parallel_time = time.time() - parallel_start
                logger.info(f"✅ [NPR] Parallel validation completed in {parallel_time:.3f}s ({len(parallel_validators)} validators, {optimal_workers} workers)")
                
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
                logger.warning(f"⚠️ [NPR] Parallel validation failed, falling back to sequential: {parallel_error}")
                fallback_start = time.time()
                for i, validator, validator_name in parallel_validators:
                    try:
                        # Pass user_question if available
                        if validator_name == "FactualHallucinationValidator":
                            result = validator.run(patched, ctx_docs, user_question=user_question)
                        else:
                            result = validator.run(patched, ctx_docs)
                        if not result.passed:
                            reasons.extend(result.reasons)
                        if result.patched_answer:
                            patched = result.patched_answer
                    except Exception as e:
                        logger.error(f"Fallback validator {i} ({validator_name}) error: {e}")
                        reasons.append(f"validator_error:{validator_name}:{str(e)}")
                fallback_time = time.time() - fallback_start
                logger.warning(f"⚠️ [NPR] Sequential fallback completed in {fallback_time:.3f}s")
        
        # Determine final validation status
        # If we have critical failures without patches, validation failed
        # Exception: missing_citation with patched_answer is considered fixed
        has_missing_citation_with_patch = any("missing_citation" in r for r in reasons) and (patched != answer)
        has_only_warnings = all(
            r.startswith("citation_relevance_warning:") or 
            r.startswith("low_overlap") or
            r.startswith("identity_warning:")
            for r in reasons
        ) and not has_critical_failure
        
        # CRITICAL FIX: Ensure patched_answer is always set if patched differs from answer
        # OR if we have missing_citation with patch (even if patched == answer due to edge case)
        # This prevents response = None bug
        if patched != answer:
            final_patched_answer = patched
        elif has_missing_citation_with_patch:
            # Even if patched == answer (shouldn't happen, but defensive), use patched
            final_patched_answer = patched
            logger.warning(f"⚠️ [FIX] patched == answer but has_missing_citation_with_patch=True, using patched anyway")
        else:
            final_patched_answer = None
        
        # NPR: Log overall validation performance
        total_validation_time = time.time() - validation_start
        logger.info(f"✅ [NPR] Validation completed in {total_validation_time:.3f}s (sequential: {len(sequential_validators)}, parallel: {len(parallel_validators)})")
        
        # CRITICAL FIX: Log patched_answer status to help debug
        logger.info(f"🔍 [TRACE] ValidatorChain final: patched={patched[:100] if patched else 'None'}..., answer={answer[:100] if answer else 'None'}..., patched_answer={final_patched_answer[:100] if final_patched_answer else 'None'}..., patched != answer={patched != answer}")
        
        # If we have critical failures without patches, validation failed
        if has_critical_failure and not has_missing_citation_with_patch:
            logger.warning(f"Validation failed: {len(reasons)} failure reasons, no patches available")
            return ValidationResult(
                passed=False,
                reasons=reasons,
                patched_answer=final_patched_answer
            )
        
        # If only warnings (not violations), validation passed
        if has_only_warnings:
            logger.info(f"Validation passed with warnings only: {reasons}")
            return ValidationResult(
                passed=True,
                reasons=reasons,
                patched_answer=final_patched_answer
            )
        
        # If missing_citation was fixed with patch, validation passed
        if has_missing_citation_with_patch:
            logger.info(f"Validation passed: missing_citation was auto-fixed with patch")
            return ValidationResult(
                passed=True,
                reasons=[r for r in reasons if r != "missing_citation"],  # Remove missing_citation from reasons since it's fixed
                patched_answer=final_patched_answer
            )
        
        # All validators passed or were patched, or low_overlap was allowed due to citation
        return ValidationResult(
            passed=True,
            reasons=reasons,
            patched_answer=final_patched_answer
        )

