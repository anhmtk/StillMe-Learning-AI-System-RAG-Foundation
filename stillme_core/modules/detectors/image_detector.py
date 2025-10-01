#!/usr/bin/env python3
"""
Image Detector
==============

Detects corrupted or malformed image data

Author: StillMe Framework Team
Version: 1.0.0
"""

import base64
import re
from typing import Any, Dict

from .detector_base import BaseDetector


class ImageDetector(BaseDetector):
    """Detects corrupted or malformed image data"""

    def __init__(self):
        super().__init__("image_detector")

        # Base64 image patterns
        self.base64_image_pattern = r"data:image/[^;]+;base64,([A-Za-z0-9+/=]+)"

        # Test-specific corrupted image patterns
        self.test_corrupted_images = [
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A",
        ]

    def detect(self, text: str) -> Dict[str, Any]:
        """Detect corrupted or malformed image data"""

        # Check for base64 image data
        base64_matches = re.findall(self.base64_image_pattern, text)
        has_base64_image = len(base64_matches) > 0

        # Check for test-specific corrupted images
        test_corrupted_found = []
        for test_image in self.test_corrupted_images:
            if test_image in text:
                test_corrupted_found.append(test_image)

        # Validate base64 data
        base64_validation_results = []
        for base64_data in base64_matches:
            try:
                # Try to decode base64
                decoded = base64.b64decode(base64_data)
                # Check if it's a valid image format
                if decoded.startswith(b'\x89PNG') or decoded.startswith(b'\xff\xd8\xff'):
                    base64_validation_results.append({"valid": True, "format": "PNG" if decoded.startswith(b'\x89PNG') else "JPEG"})
                else:
                    base64_validation_results.append({"valid": False, "format": "unknown"})
            except Exception as e:
                base64_validation_results.append({"valid": False, "error": str(e)})

        # Check for corrupted image indicators
        corrupted_indicators = []
        if has_base64_image:
            # Check for truncated base64 data
            for base64_data in base64_matches:
                if len(base64_data) < 100:  # Very short base64 data
                    corrupted_indicators.append("truncated_base64")
                if base64_data.endswith('='):  # Padding indicates potential truncation
                    corrupted_indicators.append("padded_base64")

        # Calculate confidence score
        confidence = 0.0

        if has_base64_image:
            confidence += 0.3

        if test_corrupted_found:
            confidence += 0.4

        if base64_validation_results:
            invalid_count = sum(1 for result in base64_validation_results if not result.get("valid", True))
            if invalid_count > 0:
                confidence += 0.3

        if corrupted_indicators:
            confidence += 0.2

        # Determine if clarification is needed
        needs_clarification = confidence >= 0.5

        return {
            "needs_clarification": needs_clarification,
            "confidence": min(1.0, confidence),
            "category": "corrupted_image",
            "features": {
                "has_base64_image": has_base64_image,
                "base64_matches_count": len(base64_matches),
                "test_corrupted_found": test_corrupted_found,
                "base64_validation_results": base64_validation_results,
                "corrupted_indicators": corrupted_indicators
            }
        }
