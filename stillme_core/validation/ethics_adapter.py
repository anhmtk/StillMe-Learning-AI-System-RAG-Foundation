"""
EthicsAdapter - Wraps existing ethics guard if available
"""

from typing import List, Optional, Callable, Tuple
from .base import ValidationResult
import logging

logger = logging.getLogger(__name__)


class EthicsAdapter:
    """Adapter to wrap existing ethics guard"""
    
    def __init__(self, guard_callable: Optional[Callable[[str], Tuple[bool, Optional[str]]]] = None):
        """
        Initialize ethics adapter
        
        Args:
            guard_callable: Function that takes answer and returns (ok: bool, reason: Optional[str])
                           If None, validator will always pass (no-op)
        """
        self.guard = guard_callable
        if guard_callable:
            logger.info("EthicsAdapter initialized with guard")
        else:
            logger.warning("EthicsAdapter initialized without guard (no-op)")
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Run ethics guard check
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents (unused for this validator)
            
        Returns:
            ValidationResult with ethics check result
        """
        if not self.guard:
            # No guard available, pass
            return ValidationResult(passed=True)
        
        try:
            ok, reason = self.guard(answer)
            
            if ok:
                logger.debug("Ethics check passed")
                return ValidationResult(passed=True)
            else:
                logger.warning(f"Ethics check failed: {reason}")
                return ValidationResult(
                    passed=False,
                    reasons=[f"ethics:{reason or 'violation_detected'}"]
                )
        except Exception as e:
            logger.error(f"Ethics guard error: {e}")
            # On error, pass (fail-open to avoid blocking valid responses)
            return ValidationResult(
                passed=True,
                reasons=[f"ethics_error:{str(e)}"]
            )

