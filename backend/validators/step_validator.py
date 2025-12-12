"""
StepValidator - Validates individual steps using ValidatorChain
Inspired by SSR (Socratic Self-Refine) for step-level confidence estimation
"""

import re
import logging
from typing import List, Optional
from pydantic import BaseModel
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import ValidationResult
from .chain import ValidatorChain
from .step_detector import Step
from .citation import CitationRequired
from .evidence_overlap import EvidenceOverlap
from .confidence import ConfidenceValidator

logger = logging.getLogger(__name__)


class StepValidationResult(BaseModel):
    """Result of validating a single step"""
    
    step: Step
    validation_result: ValidationResult
    confidence: float  # 0.0-1.0
    passed: bool
    issues: List[str]  # Specific issues found
    
    class Config:
        arbitrary_types_allowed = True  # Allow Step dataclass


class StepValidator:
    """
    Validates individual steps using lightweight ValidatorChain
    
    P1.1 Optimization: Uses lightweight chain (only CitationRequired, EvidenceOverlap, ConfidenceValidator)
    instead of full chain (12 validators) to reduce API calls from 120+ to ~30.
    """
    
    def __init__(self, confidence_threshold: float = 0.5, use_lightweight: bool = True):
        """
        Initialize step validator
        
        Args:
            confidence_threshold: Minimum confidence to consider step reliable (default: 0.5)
            use_lightweight: If True, use lightweight validation chain (default: True)
        """
        self.confidence_threshold = confidence_threshold
        self.use_lightweight = use_lightweight
        logger.info(f"StepValidator initialized (confidence_threshold={confidence_threshold}, use_lightweight={use_lightweight})")
    
    def _create_lightweight_chain(self, ctx_docs: List[str], adaptive_citation_overlap: float = 0.1, adaptive_evidence_threshold: float = 0.01) -> ValidatorChain:
        """
        Create lightweight validation chain for step validation
        
        P1.1 Optimization: Only includes essential validators:
        - CitationRequired: Check if step has citation (critical)
        - EvidenceOverlap: Check if step content overlaps with context (if context available)
        - ConfidenceValidator: Check confidence level (critical)
        
        Skips expensive validators:
        - SourceConsensusValidator (LLM call, timeout-prone)
        - FactualHallucinationValidator (LLM call)
        - PhilosophicalDepthValidator (LLM call)
        - IdentityCheckValidator (LLM call)
        - EgoNeutralityValidator (LLM call)
        - etc.
        
        Args:
            ctx_docs: Context documents from RAG
            adaptive_citation_overlap: Adaptive citation overlap threshold (from main validation)
            adaptive_evidence_threshold: Adaptive evidence threshold (from main validation)
            
        Returns:
            Lightweight ValidatorChain with only essential validators
        """
        validators = [
            CitationRequired(),  # CRITICAL: Always check for citation
        ]
        
        # EvidenceOverlap: Only when has context
        if len(ctx_docs) > 0:
            validators.append(EvidenceOverlap(threshold=adaptive_evidence_threshold))
            logger.debug(f"Lightweight chain: Added EvidenceOverlap (has context, threshold={adaptive_evidence_threshold:.3f})")
        
        # ConfidenceValidator: Always check confidence
        validators.append(
            ConfidenceValidator(require_uncertainty_when_no_context=False)  # Relaxed for steps
        )
        
        chain = ValidatorChain(validators)
        logger.debug(f"Lightweight chain created: {len(validators)} validators (vs 12 in full chain)")
        return chain
    
    def _calculate_step_confidence(
        self,
        step: Step,
        validation_result: ValidationResult,
        ctx_docs: List[str]
    ) -> float:
        """
        Calculate confidence score for a step (0.0-1.0)
        
        Factors:
        - Base confidence: 0.5
        - Has citation: +0.2
        - Evidence overlap > 0.1: +0.2
        - Validation passed: +0.1
        - Missing citation: -0.3
        - Low overlap: -0.2
        
        Args:
            step: The step being validated
            validation_result: Validation result from ValidatorChain
            ctx_docs: Context documents from RAG
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.5
        
        # Check for citation in step content
        has_citation = bool(re.search(r'\[\d+\]', step.content))
        
        # Simple evidence overlap check (check if step content mentions context keywords)
        # This is a simplified check - full overlap would require embedding comparison
        has_overlap = False
        if ctx_docs:
            step_lower = step.content.lower()
            # Check if step mentions common keywords from context
            context_text = " ".join(ctx_docs[:3]).lower()  # Use first 3 docs
            # Simple keyword overlap (at least 2 words match)
            step_words = set(step_lower.split())
            context_words = set(context_text.split())
            common_words = step_words.intersection(context_words)
            # Filter out common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                          'của', 'và', 'hoặc', 'nhưng', 'trong', 'trên', 'với', 'bởi', 'từ', 'đến'}
            meaningful_common = common_words - stop_words
            if len(meaningful_common) >= 2:
                has_overlap = True
        
        # Adjust confidence based on factors
        if has_citation:
            base_confidence += 0.2
        if has_overlap:
            base_confidence += 0.2
        if validation_result.passed:
            base_confidence += 0.1
        else:
            # Check specific failure reasons
            if "missing_citation" in validation_result.reasons:
                base_confidence -= 0.3
            if "low_overlap" in validation_result.reasons:
                base_confidence -= 0.2
            if "missing_uncertainty" in validation_result.reasons:
                base_confidence -= 0.1
        
        # Clamp to [0.0, 1.0]
        confidence = max(0.0, min(1.0, base_confidence))
        
        return confidence
    
    def validate_step(
        self,
        step: Step,
        ctx_docs: List[str],
        chain: Optional[ValidatorChain] = None,
        adaptive_citation_overlap: float = 0.1,
        adaptive_evidence_threshold: float = 0.01
    ) -> StepValidationResult:
        """
        Validate a single step
        
        P1.1 Optimization: Uses lightweight chain by default to reduce API calls.
        If `chain` is provided, uses it (for backward compatibility).
        If `use_lightweight=True` and `chain=None`, creates lightweight chain.
        
        Args:
            step: The step to validate
            ctx_docs: Context documents from RAG
            chain: Optional ValidatorChain to use (if None and use_lightweight=True, creates lightweight chain)
            adaptive_citation_overlap: Adaptive citation overlap threshold (for lightweight chain)
            adaptive_evidence_threshold: Adaptive evidence threshold (for lightweight chain)
            
        Returns:
            StepValidationResult with validation outcome and confidence
        """
        # P1.1: Use lightweight chain if enabled and no chain provided
        if self.use_lightweight and chain is None:
            chain = self._create_lightweight_chain(ctx_docs, adaptive_citation_overlap, adaptive_evidence_threshold)
        elif chain is None:
            raise ValueError("chain must be provided if use_lightweight=False")
        
        # Run validation on step content
        validation_result = chain.run(step.content, ctx_docs)
        
        # Calculate confidence
        confidence = self._calculate_step_confidence(step, validation_result, ctx_docs)
        
        # Extract issues
        issues = []
        if not validation_result.passed:
            issues.extend(validation_result.reasons)
        if confidence < self.confidence_threshold:
            issues.append(f"low_confidence:{confidence:.2f}")
        
        return StepValidationResult(
            step=step,
            validation_result=validation_result,
            confidence=confidence,
            passed=validation_result.passed and confidence >= self.confidence_threshold,
            issues=issues
        )
    
    def validate_all_steps(
        self,
        steps: List[Step],
        ctx_docs: List[str],
        chain: Optional[ValidatorChain] = None,
        parallel: bool = True,
        adaptive_citation_overlap: float = 0.1,
        adaptive_evidence_threshold: float = 0.01
    ) -> List[StepValidationResult]:
        """
        Validate all steps (can run in parallel for speed)
        
        P1.1 Optimization: Uses lightweight chain by default to reduce API calls from 120+ to ~30.
        
        Args:
            steps: List of steps to validate
            ctx_docs: Context documents from RAG
            chain: Optional ValidatorChain to use (if None and use_lightweight=True, creates lightweight chain)
            parallel: If True, run validations in parallel (default: True)
            adaptive_citation_overlap: Adaptive citation overlap threshold (for lightweight chain)
            adaptive_evidence_threshold: Adaptive evidence threshold (for lightweight chain)
            
        Returns:
            List of StepValidationResult, sorted by step number
        """
        if not steps:
            return []
        
        # P1.1: Create lightweight chain once if needed (shared across all steps)
        if self.use_lightweight and chain is None:
            chain = self._create_lightweight_chain(ctx_docs, adaptive_citation_overlap, adaptive_evidence_threshold)
            logger.info(f"P1.1: Using lightweight chain ({len(chain.validators)} validators) for {len(steps)} steps")
        elif chain is None:
            raise ValueError("chain must be provided if use_lightweight=False")
        
        results = []
        
        if parallel and len(steps) > 1:
            # Run validations in parallel for speed
            logger.debug(f"Running {len(steps)} step validations in parallel (lightweight chain)...")
            with ThreadPoolExecutor(max_workers=min(len(steps), 5)) as executor:
                futures = {
                    executor.submit(self.validate_step, step, ctx_docs, chain, adaptive_citation_overlap, adaptive_evidence_threshold): step
                    for step in steps
                }
                
                for future in as_completed(futures):
                    step = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error validating step {step.step_number}: {e}")
                        # Fallback: mark as failed
                        results.append(StepValidationResult(
                            step=step,
                            validation_result=ValidationResult(
                                passed=False,
                                reasons=[f"validation_error: {str(e)}"]
                            ),
                            confidence=0.1,
                            passed=False,
                            issues=[f"Validation error: {str(e)}"]
                        ))
        else:
            # Sequential validation
            for step in steps:
                try:
                    result = self.validate_step(step, ctx_docs, chain, adaptive_citation_overlap, adaptive_evidence_threshold)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error validating step {step.step_number}: {e}")
                    results.append(StepValidationResult(
                        step=step,
                        validation_result=ValidationResult(
                            passed=False,
                            reasons=[f"validation_error: {str(e)}"]
                        ),
                        confidence=0.1,
                        passed=False,
                        issues=[f"Validation error: {str(e)}"]
                    ))
        
        # Sort by step number
        results.sort(key=lambda x: x.step.step_number)
        
        logger.info(f"Validated {len(results)} steps: {sum(1 for r in results if r.passed)} passed, "
                   f"{sum(1 for r in results if not r.passed)} failed")
        
        return results

