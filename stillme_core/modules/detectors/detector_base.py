#!/usr/bin/env python3
"""
Base Detector Interface for Multi-Modal Torture Detection
========================================================

Enterprise QA Lead - AI Reliability Division
Base class for all specialized detectors

Author: StillMe Framework Team
Version: 1.0.0
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

class BaseDetector(ABC):
    """Base class for all specialized detectors"""

    def __init__(self, name: str):
        self.name = name
        self.telemetry_file = Path("logs/clarification_torture.jsonl")
        self.telemetry_file.parent.mkdir(exist_ok=True)

        # Loop guard
        self.failure_count = 0
        self.max_failures = 3
        self.last_failure_time = None

    @abstractmethod
    def detect(self, text: str) -> dict[str, Any]:
        """
        Detect specific patterns in text

        Returns:
            Dict with keys:
            - needs_clarification: bool
            - confidence: float (0.0-1.0)
            - category: str
            - features: dict (additional metadata)
        """
        pass

    def analyze(self, text: str) -> dict[str, Any]:
        """
        Analyze text with telemetry and loop guard
        """
        start_time = time.time()

        try:
            result = self.detect(text)
            latency = (time.time() - start_time) * 1000  # Convert to ms

            # Log telemetry
            self._log_telemetry(result, latency, success=True)

            # Reset failure count on success
            self.failure_count = 0

            return result

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            self.failure_count += 1
            self.last_failure_time = time.time()

            logger.error(f"Detector {self.name} failed: {e}")

            # Log failure telemetry
            self._log_telemetry({
                "needs_clarification": False,
                "confidence": 0.0,
                "category": "error",
                "features": {"error": str(e)}
            }, latency, success=False)

            # Check loop guard
            if self.failure_count >= self.max_failures:
                self._generate_rca_report()

            # Return safe fallback
            return {
                "needs_clarification": False,
                "confidence": 0.0,
                "category": "error",
                "features": {"error": str(e), "fallback": True}
            }

    def _log_telemetry(self, result: dict[str, Any], latency: float, success: bool):
        """Log telemetry data"""
        try:
            telemetry_entry = {
                "timestamp": time.time(),
                "detector": self.name,
                "category": result.get("category", "unknown"),
                "confidence": result.get("confidence", 0.0),
                "latency_ms": latency,
                "success": success,
                "features": result.get("features", {})
            }

            with open(self.telemetry_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(telemetry_entry) + "\n")

        except Exception as e:
            logger.warning(f"Failed to log telemetry: {e}")

    def _generate_rca_report(self):
        """Generate Root Cause Analysis report for repeated failures"""
        try:
            rca_file = Path("logs/clarification_torture_rca.md")

            with open(rca_file, "w", encoding="utf-8") as f:
                f.write(f"# RCA Report: {self.name} Detector\n\n")
                f.write(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Detector**: {self.name}\n")
                f.write(f"**Failure Count**: {self.failure_count}\n")
                f.write(f"**Last Failure**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.last_failure_time))}\n\n")
                f.write("## Analysis\n\n")
                f.write("Detector has failed 3+ times consecutively. Manual intervention required.\n\n")
                f.write("## Recommendations\n\n")
                f.write("1. Review detector logic\n")
                f.write("2. Check input validation\n")
                f.write("3. Verify pattern matching\n")
                f.write("4. Test with edge cases\n")

            logger.error(f"RCA report generated: {rca_file}")

        except Exception as e:
            logger.error(f"Failed to generate RCA report: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get detector statistics"""
        return {
            "name": self.name,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "telemetry_file": str(self.telemetry_file)
        }
