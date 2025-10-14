#!/usr/bin/env python3
"""
Clarification Engine
====================

Integration layer for all specialized detectors

Author: StillMe Framework Team
Version: 1.0.0
"""

import logging
import time
from typing import Any

from .detectors.image_detector import ImageDetector
from .detectors.json_detector import JSONDetector
from .detectors.multiple_functions_detector import MultipleFunctionsDetector

# Import detectors
from .detectors.nested_detector import NestedCodeBlockDetector
from .detectors.sqli_detector import SQLiDetector
from .detectors.syntax_detector import SyntaxDetector
from .detectors.unicode_detector import UnicodeDetector
from .detectors.xss_detector import XSSDetector

logger = logging.getLogger(__name__)


class ClarificationEngine:
    """Main engine that coordinates all detectors"""

    def __init__(self):
        self.detectors = [
            NestedCodeBlockDetector(),
            UnicodeDetector(),
            JSONDetector(),
            SQLiDetector(),
            XSSDetector(),
            SyntaxDetector(),
            MultipleFunctionsDetector(),
            ImageDetector(),
        ]

        # Performance tracking
        self.performance_stats = {
            "total_requests": 0,
            "total_latency_ms": 0.0,
            "detector_stats": {},
        }

        # Initialize detector stats
        for detector in self.detectors:
            self.performance_stats["detector_stats"][detector.name] = {
                "requests": 0,
                "total_latency_ms": 0.0,
                "successes": 0,
                "failures": 0,
            }

    def analyze(self, text: str, mode: str = "quick") -> dict[str, Any]:
        """
        Analyze text using all detectors

        Args:
            text: Input text to analyze
            mode: "quick" (≤50ms) or "careful" (≤200ms)

        Returns:
            Dict with analysis results
        """
        start_time = time.time()

        # Run all detectors
        results = []
        for detector in self.detectors:
            try:
                result = detector.analyze(text)
                results.append(result)

                # Update stats
                detector_stats = self.performance_stats["detector_stats"][detector.name]
                detector_stats["requests"] += 1
                detector_stats["successes"] += 1

            except Exception as e:
                logger.error(f"Detector {detector.name} failed: {e}")

                # Update failure stats
                detector_stats = self.performance_stats["detector_stats"][detector.name]
                detector_stats["requests"] += 1
                detector_stats["failures"] += 1

                # Add error result
                results.append(
                    {
                        "needs_clarification": False,
                        "confidence": 0.0,
                        "category": "error",
                        "features": {"error": str(e), "detector": detector.name},
                    }
                )

        # Choose best result (highest confidence)
        best_result = max(results, key=lambda r: r.get("confidence", 0.0))

        # Calculate total latency
        total_latency = (time.time() - start_time) * 1000

        # Update performance stats
        self.performance_stats["total_requests"] += 1
        self.performance_stats["total_latency_ms"] += total_latency

        # Check performance requirements
        max_latency = 50 if mode == "quick" else 200
        performance_ok = total_latency <= max_latency

        # Prepare final result
        final_result = {
            "needs_clarification": best_result.get("needs_clarification", False),
            "confidence": best_result.get("confidence", 0.0),
            "category": best_result.get("category", "unknown"),
            "features": best_result.get("features", {}),
            "performance": {
                "total_latency_ms": total_latency,
                "mode": mode,
                "performance_ok": performance_ok,
                "max_latency_ms": max_latency,
            },
            "detector_results": results,
            "best_detector": best_result.get("category", "unknown"),
        }

        # Log performance warning if needed
        if not performance_ok:
            logger.warning(
                f"Performance threshold exceeded: {total_latency:.2f}ms > {max_latency}ms"
            )

        return final_result

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics"""
        total_requests = self.performance_stats["total_requests"]
        avg_latency = (
            self.performance_stats["total_latency_ms"] / total_requests
            if total_requests > 0
            else 0.0
        )

        return {
            "total_requests": total_requests,
            "average_latency_ms": avg_latency,
            "detector_stats": self.performance_stats["detector_stats"],
        }

    def reset_stats(self):
        """Reset performance statistics"""
        self.performance_stats = {
            "total_requests": 0,
            "total_latency_ms": 0.0,
            "detector_stats": {},
        }

        for detector in self.detectors:
            self.performance_stats["detector_stats"][detector.name] = {
                "requests": 0,
                "total_latency_ms": 0.0,
                "successes": 0,
                "failures": 0,
            }

    def get_detector_status(self) -> dict[str, Any]:
        """Get status of all detectors"""
        status = {}
        for detector in self.detectors:
            status[detector.name] = detector.get_stats()
        return status