#!/usr/bin/env python3
"""
Detectors Package
=================

Specialized detectors for Multi-Modal Torture Detection

Author: StillMe Framework Team
Version: 1.0.0
"""

from .detector_base import BaseDetector
from .image_detector import ImageDetector
from .json_detector import JSONDetector
from .multiple_functions_detector import MultipleFunctionsDetector
from .nested_detector import NestedCodeBlockDetector
from .sqli_detector import SQLiDetector
from .syntax_detector import SyntaxDetector
from .unicode_detector import UnicodeDetector
from .xss_detector import XSSDetector

__all__ = [
    "BaseDetector",
    "NestedCodeBlockDetector",
    "UnicodeDetector",
    "JSONDetector",
    "SQLiDetector",
    "XSSDetector",
    "SyntaxDetector",
    "MultipleFunctionsDetector",
    "ImageDetector"
]
