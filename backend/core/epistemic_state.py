"""
Epistemic State - Simple knowledge state classification

Classifies each response into one of three epistemic states:
- KNOWN: Clear evidence, good citations, validators pass
- UNCERTAIN: Some information but thin, or validators warn
- UNKNOWN: System truly doesn't know / insufficient data

This is a rule-based classifier that can be upgraded to ML-based in the future.
"""

import logging
from enum import Enum
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class EpistemicState(str, Enum):
    """Epistemic state of a response"""
    KNOWN = "KNOWN"  # Clear evidence, good citations, validators pass
    UNCERTAIN = "UNCERTAIN"  # Some information but thin, or validators warn
    UNKNOWN = "UNKNOWN"  # System truly doesn't know / insufficient data


def calculate_epistemic_state(
    validation_info: Optional[Dict[str, Any]] = None,
    confidence_score: Optional[float] = None,
    response_text: Optional[str] = None,
    context_docs_count: int = 0
) -> EpistemicState:
    """
    Calculate epistemic state based on validation results, confidence, and context
    
    Rules:
    - KNOWN if:
      - Has at least 1 valid citation
      - EvidenceOverlap/CitationRelevance don't flag critical errors
      - ConfidenceValidator score >= 0.7
      - Validation passed (or only warnings)
    
    - UNCERTAIN if:
      - Has some citation/context but:
        - Confidence low (0.4-0.7), or
        - Has warnings from validators but not critical failures
    
    - UNKNOWN if:
      - No citation / no relevant context, or
      - Fallback "I don't know / not enough data" triggered, or
      - Validators fail at critical level
    
    Args:
        validation_info: Validation results dict with:
            - passed: bool
            - reasons: List[str]
            - used_fallback: bool
            - context_docs_count: int
        confidence_score: Confidence score (0.0-1.0)
        response_text: Response text (to check for citations and fallback messages)
        context_docs_count: Number of context documents (fallback if not in validation_info)
        
    Returns:
        EpistemicState enum value
    """
    # Default to UNKNOWN if no information
    if validation_info is None and confidence_score is None:
        logger.debug("EpistemicState: UNKNOWN (no validation_info or confidence_score)")
        return EpistemicState.UNKNOWN
    
    # Extract values from validation_info
    validation_passed = validation_info.get("passed", False) if validation_info else True
    validation_reasons = validation_info.get("reasons", []) if validation_info else []
    used_fallback = validation_info.get("used_fallback", False) if validation_info else False
    ctx_docs_count = validation_info.get("context_docs_count", context_docs_count) if validation_info else context_docs_count
    
    # Use confidence_score from validation_info if available, otherwise use parameter
    conf_score = validation_info.get("confidence_score", confidence_score) if validation_info else confidence_score
    
    # Check for fallback messages in response text
    is_fallback_message = False
    if response_text:
        fallback_indicators = [
            "i don't have sufficient information",
            "mình không có đủ thông tin",
            "i don't know",
            "mình không biết",
            "not enough data",
            "không đủ dữ liệu",
            "cannot find",
            "không tìm thấy"
        ]
        response_lower = response_text.lower()
        is_fallback_message = any(indicator in response_lower for indicator in fallback_indicators)
    
    # UNKNOWN: Fallback triggered or no context
    if used_fallback or is_fallback_message:
        logger.debug(f"EpistemicState: UNKNOWN (used_fallback={used_fallback}, is_fallback_message={is_fallback_message})")
        return EpistemicState.UNKNOWN
    
    if ctx_docs_count == 0:
        # No context - check if response explicitly says "I don't know"
        if is_fallback_message:
            logger.debug("EpistemicState: UNKNOWN (no context and fallback message)")
            return EpistemicState.UNKNOWN
        # If no context but response doesn't say "I don't know", might be general knowledge
        # But we'll be conservative and mark as UNCERTAIN
        if conf_score is not None and conf_score < 0.5:
            logger.debug(f"EpistemicState: UNKNOWN (no context, low confidence={conf_score:.2f})")
            return EpistemicState.UNKNOWN
    
    # Check for citations in response text
    has_citations = False
    if response_text:
        import re
        # Check for citation patterns: [1], [2], [general knowledge], [foundational knowledge]
        citation_patterns = [
            r'\[\d+\]',  # [1], [2], etc.
            r'\[general knowledge\]',
            r'\[foundational knowledge\]',
            r'\[kiến thức tổng quát\]',
            r'\[kiến thức nền tảng\]'
        ]
        for pattern in citation_patterns:
            if re.search(pattern, response_text, re.IGNORECASE):
                has_citations = True
                break
    
    # Check for critical validation failures
    critical_failures = [
        "missing_citation",
        "language_mismatch",
        "factual_hallucination",
        "explicit_fake_entity",
        "anthropomorphic"
    ]
    has_critical_failure = any(
        any(critical in reason.lower() for critical in critical_failures)
        for reason in validation_reasons
    )
    
    # Check for warnings (non-critical issues)
    warning_patterns = [
        "citation_relevance_warning",
        "low_overlap",
        "identity_warning"
    ]
    has_warnings = any(
        any(warning in reason.lower() for warning in warning_patterns)
        for reason in validation_reasons
    )
    
    # UNKNOWN: Critical validation failures
    if has_critical_failure and not validation_passed:
        logger.debug(f"EpistemicState: UNKNOWN (critical validation failure: {validation_reasons})")
        return EpistemicState.UNKNOWN
    
    # KNOWN: High confidence, good citations, validation passed
    if (
        validation_passed and
        has_citations and
        ctx_docs_count > 0 and
        (conf_score is None or conf_score >= 0.7) and
        not has_warnings
    ):
        conf_display = f"{conf_score:.2f}" if conf_score is not None else "N/A"
        logger.debug(
            f"EpistemicState: KNOWN "
            f"(passed={validation_passed}, citations={has_citations}, "
            f"ctx_docs={ctx_docs_count}, confidence={conf_display})"
        )
        return EpistemicState.KNOWN
    
    # KNOWN: Even with warnings, if confidence is high and has citations
    if (
        validation_passed and
        has_citations and
        ctx_docs_count > 0 and
        conf_score is not None and conf_score >= 0.8
    ):
        logger.debug(
            f"EpistemicState: KNOWN "
            f"(high confidence={conf_score:.2f} with citations, despite warnings)"
        )
        return EpistemicState.KNOWN
    
    # UNCERTAIN: Has some information but not fully confident
    if (
        (has_citations or ctx_docs_count > 0) and
        (conf_score is None or (0.4 <= conf_score < 0.7)) or
        (validation_passed and has_warnings) or
        (has_citations and ctx_docs_count == 0)  # Citations but no context (general knowledge)
    ):
        conf_display = f"{conf_score:.2f}" if conf_score is not None else "N/A"
        logger.debug(
            f"EpistemicState: UNCERTAIN "
            f"(citations={has_citations}, ctx_docs={ctx_docs_count}, "
            f"confidence={conf_display}, warnings={has_warnings})"
        )
        return EpistemicState.UNCERTAIN
    
    # UNCERTAIN: Low confidence even with context
    if ctx_docs_count > 0 and conf_score is not None and conf_score < 0.4:
        logger.debug(f"EpistemicState: UNCERTAIN (low confidence={conf_score:.2f} despite context)")
        return EpistemicState.UNCERTAIN
    
    # Default: UNKNOWN if we can't determine
    logger.debug(f"EpistemicState: UNKNOWN (default - couldn't determine from available info)")
    return EpistemicState.UNKNOWN

