"""
Validator Configuration

Configuration for validation system components.
"""

from .base import BaseConfig
from typing import Dict, Any

class ValidatorConfig(BaseConfig):
    """
    Configuration for validation system
    
    Environment variables:
    - STILLME_EVIDENCE_THRESHOLD: Minimum overlap threshold (default: 0.08)
    - STILLME_CITATION_REQUIRED: Require citations (default: True)
    - STILLME_ENABLE_VALIDATORS: Enable validators globally (default: True)
    - STILLME_LOW_OVERLAP_THRESHOLD: Low overlap threshold (default: 0.05)
    """
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Get default validator configuration"""
        return {
            "evidence_threshold": 0.08,
            "citation_required": True,
            "enable_validators": True,
            "low_overlap_threshold": 0.05,
            "confidence_threshold": 0.5,
            "parallel_execution": True,
            "max_parallel_workers": 5,
        }
    
    @property
    def evidence_threshold(self) -> float:
        """Minimum evidence overlap threshold"""
        return getattr(self, "_evidence_threshold", 0.08)
    
    @evidence_threshold.setter
    def evidence_threshold(self, value: float):
        self._evidence_threshold = float(value)
    
    @property
    def citation_required(self) -> bool:
        """Whether citations are required"""
        return getattr(self, "_citation_required", True)
    
    @citation_required.setter
    def citation_required(self, value: bool):
        self._citation_required = bool(value)
    
    @property
    def enable_validators(self) -> bool:
        """Whether validators are enabled globally"""
        return getattr(self, "_enable_validators", True)
    
    @enable_validators.setter
    def enable_validators(self, value: bool):
        self._enable_validators = bool(value)

