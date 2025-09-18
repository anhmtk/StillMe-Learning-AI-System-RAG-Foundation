"""
StillMe Core Validation - Core validation system for StillMe AI

This module provides core validation capabilities:
- ValidationFramework: Main validation framework
- FinalValidationSystem: Final validation system
- EnhancedValidation: Enhanced validation features

Author: StillMe AI Team
Version: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "StillMe AI Team"

# Import core validation components
from .validation_framework import ValidationFramework
from .final_validation_system import FinalValidationSystem
from .enhanced_validation import EnhancedValidation

__all__ = [
    "ValidationFramework",
    "FinalValidationSystem",
    "EnhancedValidation"
]
