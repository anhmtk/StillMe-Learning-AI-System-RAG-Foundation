"""
StepValidator - Validates individual steps using ValidatorChain
Inspired by SSR (Socratic Self-Refine) for step-level confidence estimation
"""

import re
import logging
import os
import json
import time
import httpx
from typing import List, Optional, Dict, Any
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
    Validates individual steps using lightweight ValidatorChain or batch LLM validation
    
    P1.1 Optimization: Uses lightweight chain (only CitationRequired, EvidenceOverlap, ConfidenceValidator)
    instead of full chain (12 validators) to reduce API calls from 120+ to ~30.
    
    P1.1.b Optimization: Batch validation - validates all steps in 1 LLM call instead of 30 calls.
    """
    
    def __init__(self, confidence_threshold: float = 0.5, use_lightweight: bool = True, use_batch: bool = True):
        """
        Initialize step validator
        
        Args:
            confidence_threshold: Minimum confidence to consider step reliable (default: 0.5)
            use_lightweight: If True, use lightweight validation chain (default: True)
            use_batch: If True, use batch LLM validation (1 call for all steps) instead of per-step validation (default: True)
        """
        self.confidence_threshold = confidence_threshold
        self.use_lightweight = use_lightweight
        self.use_batch = use_batch
        logger.info(f"StepValidator initialized (confidence_threshold={confidence_threshold}, use_lightweight={use_lightweight}, use_batch={use_batch})")
    
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
    
    def _validate_steps_batch(
        self,
        steps: List[Step],
        ctx_docs: List[str],
        adaptive_citation_overlap: float = 0.1,
        adaptive_evidence_threshold: float = 0.01
    ) -> List[StepValidationResult]:
        """
        P1.1.b: Validate all steps in a single LLM call (batch validation)
        
        This reduces API calls from 30 (10 steps × 3 validators) to 1 LLM call.
        
        Args:
            steps: List of steps to validate
            ctx_docs: Context documents from RAG
            adaptive_citation_overlap: Adaptive citation overlap threshold
            adaptive_evidence_threshold: Adaptive evidence threshold
            
        Returns:
            List of StepValidationResult, sorted by step number
        """
        if not steps:
            return []
        
        try:
            # Get API key and base URL
            api_key = os.getenv("DEEPSEEK_API_KEY")
            api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
            model = "deepseek-chat"
            
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
                api_base = "https://api.openai.com/v1"
                model = "gpt-3.5-turbo"
            
            if not api_key:
                logger.warning("No API key available for batch step validation, falling back to lightweight chain")
                chain = self._create_lightweight_chain(ctx_docs, adaptive_citation_overlap, adaptive_evidence_threshold)
                return [self.validate_step(step, ctx_docs, chain, adaptive_citation_overlap, adaptive_evidence_threshold) for step in steps]
            
            # Build batch validation prompt
            context_summary = " ".join(ctx_docs[:3])[:500] if ctx_docs else "No context available"
            
            steps_text = "\n\n".join([
                f"**Step {step.step_number}:**\n{step.content}"
                for step in steps
            ])
            
            batch_prompt = f"""You are validating {len(steps)} steps from a multi-step response. Validate each step for:

1. **Citation**: Does the step have citations (e.g., [1], [2])? (Required if context is available)
2. **Evidence Overlap**: Does the step content overlap with the provided context? (Threshold: {adaptive_evidence_threshold:.3f})
3. **Confidence**: How confident is the step? (0.0-1.0)

**Context (for reference):**
{context_summary}

**Steps to Validate:**
{steps_text}

**Output Format (JSON only, no other text):**
{{
    "step_1": {{
        "has_citation": true/false,
        "citation_count": 0,
        "evidence_overlap": 0.0-1.0,
        "confidence": 0.0-1.0,
        "passed": true/false,
        "issues": ["issue1", "issue2"]
    }},
    "step_2": {{...}},
    ...
}}

**Validation Rules:**
- If context is available and step has no citation → "missing_citation" issue, passed=false
- If evidence_overlap < {adaptive_evidence_threshold:.3f} → "low_overlap" issue (warning, not failure)
- If confidence < 0.5 → "low_confidence" issue
- passed=true only if: has_citation (when context available) AND confidence >= 0.5

Return ONLY valid JSON, no markdown code blocks."""

            # Call LLM API
            start_time = time.time()
            # P1: Reduce timeout from 10s to 3s for faster fallback
            with httpx.Client(timeout=3.0) as client:
                response = client.post(
                    f"{api_base}/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": "You are a step validation assistant. Analyze steps and return JSON only."},
                            {"role": "user", "content": batch_prompt}
                        ],
                        "temperature": 0.0,  # Deterministic
                        "max_tokens": 2000
                    }
                )
                
                if response.status_code != 200:
                    logger.warning(f"Batch validation LLM API error: {response.status_code}, falling back to lightweight chain")
                    chain = self._create_lightweight_chain(ctx_docs, adaptive_citation_overlap, adaptive_evidence_threshold)
                    return [self.validate_step(step, ctx_docs, chain, adaptive_citation_overlap, adaptive_evidence_threshold) for step in steps]
                
                data = response.json()
                if "choices" not in data or len(data["choices"]) == 0:
                    logger.warning("Batch validation LLM API returned unexpected format, falling back to lightweight chain")
                    chain = self._create_lightweight_chain(ctx_docs, adaptive_citation_overlap, adaptive_evidence_threshold)
                    return [self.validate_step(step, ctx_docs, chain, adaptive_citation_overlap, adaptive_evidence_threshold) for step in steps]
                
                result_text = data["choices"][0]["message"]["content"].strip()
                elapsed = time.time() - start_time
                
                # Parse JSON response
                try:
                    # Remove markdown code blocks if present
                    if result_text.startswith("```"):
                        result_text = result_text.split("```")[1]
                        if result_text.startswith("json"):
                            result_text = result_text[4:]
                    result_text = result_text.strip()
                    
                    batch_results = json.loads(result_text)
                    
                    logger.info(f"P1.1.b: Batch validation completed in {elapsed:.2f}s for {len(steps)} steps (1 LLM call)")
                    
                    # Convert batch results to StepValidationResult list
                    results = []
                    for step in steps:
                        step_key = f"step_{step.step_number}"
                        if step_key not in batch_results:
                            logger.warning(f"Missing result for {step_key}, using fallback")
                            # Fallback: create result with low confidence
                            results.append(StepValidationResult(
                                step=step,
                                validation_result=ValidationResult(
                                    passed=False,
                                    reasons=["batch_validation:missing_result"]
                                ),
                                confidence=0.3,
                                passed=False,
                                issues=["Missing validation result"]
                            ))
                            continue
                        
                        step_result = batch_results[step_key]
                        has_citation = step_result.get("has_citation", False)
                        evidence_overlap = step_result.get("evidence_overlap", 0.0)
                        confidence = step_result.get("confidence", 0.5)
                        passed = step_result.get("passed", False)
                        issues = step_result.get("issues", [])
                        
                        # Build ValidationResult
                        reasons = []
                        if not has_citation and ctx_docs:
                            reasons.append("missing_citation")
                        if evidence_overlap < adaptive_evidence_threshold:
                            reasons.append(f"low_overlap:{evidence_overlap:.3f}")
                        if confidence < self.confidence_threshold:
                            reasons.append(f"low_confidence:{confidence:.2f}")
                        reasons.extend(issues)
                        
                        validation_result = ValidationResult(
                            passed=passed,
                            reasons=reasons if reasons else []
                        )
                        
                        results.append(StepValidationResult(
                            step=step,
                            validation_result=validation_result,
                            confidence=confidence,
                            passed=passed,
                            issues=issues
                        ))
                    
                    # Sort by step number
                    results.sort(key=lambda x: x.step.step_number)
                    return results
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse batch validation JSON: {result_text[:200]}, error: {e}, falling back to lightweight chain")
                    chain = self._create_lightweight_chain(ctx_docs, adaptive_citation_overlap, adaptive_evidence_threshold)
                    return [self.validate_step(step, ctx_docs, chain, adaptive_citation_overlap, adaptive_evidence_threshold) for step in steps]
        
        except Exception as e:
            logger.warning(f"Batch validation failed: {e}, falling back to lightweight chain")
            chain = self._create_lightweight_chain(ctx_docs, adaptive_citation_overlap, adaptive_evidence_threshold)
            return [self.validate_step(step, ctx_docs, chain, adaptive_citation_overlap, adaptive_evidence_threshold) for step in steps]
    
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
        Validate all steps (can run in parallel for speed or use batch validation)
        
        P1.1 Optimization: Uses lightweight chain by default to reduce API calls from 120+ to ~30.
        P1.1.b Optimization: Uses batch validation (1 LLM call) to reduce from ~30 to 1 call.
        
        Args:
            steps: List of steps to validate
            ctx_docs: Context documents from RAG
            chain: Optional ValidatorChain to use (if None and use_lightweight=True, creates lightweight chain)
            parallel: If True, run validations in parallel (default: True, ignored if use_batch=True)
            adaptive_citation_overlap: Adaptive citation overlap threshold (for lightweight chain)
            adaptive_evidence_threshold: Adaptive evidence threshold (for lightweight chain)
            
        Returns:
            List of StepValidationResult, sorted by step number
        """
        if not steps:
            return []
        
        # P1.1.b: Use batch validation if enabled (1 LLM call for all steps)
        if self.use_batch:
            logger.info(f"P1.1.b: Using batch validation (1 LLM call) for {len(steps)} steps")
            return self._validate_steps_batch(steps, ctx_docs, adaptive_citation_overlap, adaptive_evidence_threshold)
        
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

