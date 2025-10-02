from typing import Any

#!/usr/bin/env python3
"""
Threshold Calibration for Proactive Abuse Guard
===============================================

Script để calibrate thresholds cho optimal precision/recall balance.

Author: StillMe Framework Team
Version: 1.0.0
"""

import os
import sys
import time
from pathlib import Path

import yaml

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stillme_core.proactive.abuse_guard import ProactiveAbuseGuard


class ThresholdCalibrator:
    """Threshold calibration for optimal performance"""

    def __init__(self):
        self.test_cases = self._load_test_cases()
        self.results = []

    def _load_test_cases(self) -> list[dict[str, Any]]:
        """Load test cases from regression suite"""
        # This would normally load from the regression test suite
        # For now, we'll use a subset of known cases
        return [
            # Slang cases (should block)
            {"text": "lol that's funny", "expected": False, "category": "slang"},
            {"text": "It's working tbh", "expected": False, "category": "slang"},
            {"text": "that's mid", "expected": False, "category": "slang"},
            {"text": "vl thật", "expected": False, "category": "slang"},
            {"text": "đẹp vl", "expected": False, "category": "slang"},

            # Vague cases (should block)
            {"text": "change something", "expected": False, "category": "vague"},
            {"text": "what do you think about this?", "expected": False, "category": "vague"},
            {"text": "what's wrong with this?", "expected": False, "category": "vague"},
            {"text": "improve system performance", "expected": False, "category": "vague"},
            {"text": "how should I handle this?", "expected": False, "category": "vague"},

            # Edge cases (should block)
            {"text": "", "expected": False, "category": "edge"},
            {"text": " ", "expected": False, "category": "edge"},
            {"text": "...", "expected": False, "category": "edge"},
            {"text": "@#$%^&*()", "expected": False, "category": "edge"},
            {"text": "!@#$%^&*()", "expected": False, "category": "edge"},

            # Clear cases (should allow)
            {"text": "How can I implement a binary search algorithm in Python?", "expected": True, "category": "clear"},
            {"text": "What are the best practices for error handling in JavaScript?", "expected": True, "category": "clear"},
            {"text": "Can you explain the difference between REST and GraphQL APIs?", "expected": True, "category": "clear"},
            {"text": "How do I optimize database queries for better performance?", "expected": True, "category": "clear"},
            {"text": "What is the most efficient way to sort a large dataset?", "expected": True, "category": "clear"},
        ]

    def calibrate_thresholds(self) -> dict[str, Any]:
        """Calibrate thresholds for optimal performance"""
        print("🔧 Starting Threshold Calibration...")
        print("=" * 50)

        best_config = None
        best_score = 0.0

        # Sweep parameters
        abuse_thresholds = [i/100.0 for i in range(10, 21)]  # 0.10 to 0.20
        suggestion_thresholds = [i/100.0 for i in range(80, 91)]  # 0.80 to 0.90

        total_combinations = len(abuse_thresholds) * len(suggestion_thresholds)
        current_combination = 0

        for abuse_threshold in abuse_thresholds:
            for suggestion_threshold in suggestion_thresholds:
                current_combination += 1

                print(f"Testing combination {current_combination}/{total_combinations}: "
                      f"abuse={abuse_threshold:.2f}, suggestion={suggestion_threshold:.2f}")

                # Test this configuration
                config = {
                    "abuse_threshold": abuse_threshold,
                    "suggestion_threshold": suggestion_threshold
                }

                results = self._test_configuration(config)

                # Calculate score (weighted combination of metrics)
                score = self._calculate_score(results)

                if score > best_score:
                    best_score = score
                    best_config = {
                        "abuse_threshold": abuse_threshold,
                        "suggestion_threshold": suggestion_threshold,
                        "results": results,
                        "score": score
                    }

                print(f"  Score: {score:.3f} (Precision: {results['precision']:.3f}, "
                      f"Recall: {results['recall']:.3f}, FPR: {results['false_positive_rate']:.3f})")

        print("\n🎯 Best Configuration Found:")
        print(f"   Abuse Threshold: {best_config['abuse_threshold']:.2f}")
        print(f"   Suggestion Threshold: {best_config['suggestion_threshold']:.2f}")
        print(f"   Score: {best_config['score']:.3f}")
        print(f"   Precision: {best_config['results']['precision']:.3f}")
        print(f"   Recall: {best_config['results']['recall']:.3f}")
        print(f"   False Positive Rate: {best_config['results']['false_positive_rate']:.3f}")

        return best_config

    def _test_configuration(self, config: dict[str, Any]) -> dict[str, Any]:
        """Test a specific configuration"""
        guard = ProactiveAbuseGuard(config)

        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0

        for case in self.test_cases:
            result = guard.analyze(case["text"], f"test_{case['text'][:10]}")
            predicted = result.should_suggest
            actual = case["expected"]

            if predicted and actual:
                true_positives += 1
            elif predicted and not actual:
                false_positives += 1
            elif not predicted and actual:
                false_negatives += 1
            else:
                true_negatives += 1

        # Calculate metrics
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        false_positive_rate = false_positives / (false_positives + true_negatives) if (false_positives + true_negatives) > 0 else 0
        false_negative_rate = false_negatives / (false_negatives + true_positives) if (false_negatives + true_positives) > 0 else 0

        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score,
            "false_positive_rate": false_positive_rate,
            "false_negative_rate": false_negative_rate,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "true_negatives": true_negatives,
            "false_negatives": false_negatives
        }

    def _calculate_score(self, results: dict[str, Any]) -> float:
        """Calculate weighted score for configuration"""
        precision = results["precision"]
        recall = results["recall"]
        fpr = results["false_positive_rate"]

        # Weighted score: prioritize precision and low FPR
        # Target: Precision ≥0.90, FPR ≤0.05, Recall ≥0.80
        score = 0.0

        # Precision component (40% weight)
        if precision >= 0.90:
            score += 0.4
        else:
            score += 0.4 * (precision / 0.90)

        # FPR component (30% weight) - lower is better
        if fpr <= 0.05:
            score += 0.3
        else:
            score += 0.3 * max(0, (0.05 - fpr) / 0.05)

        # Recall component (30% weight)
        if recall >= 0.80:
            score += 0.3
        else:
            score += 0.3 * (recall / 0.80)

        return score

    def save_calibrated_config(self, best_config: dict[str, Any]):
        """Save calibrated configuration to file"""
        config_data = {
            "abuse_threshold": best_config["abuse_threshold"],
            "suggestion_threshold": best_config["suggestion_threshold"],
            "calibration_results": best_config["results"],
            "calibration_score": best_config["score"],
            "calibration_timestamp": time.time()
        }

        # Save to YAML file
        config_file = Path("config/abuse_guard_calib.yaml")
        config_file.parent.mkdir(exist_ok=True)

        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, indent=2)

        print(f"\n💾 Calibrated configuration saved to: {config_file}")

if __name__ == "__main__":
    calibrator = ThresholdCalibrator()
    best_config = calibrator.calibrate_thresholds()
    calibrator.save_calibrated_config(best_config)

    print("\n✅ Threshold calibration completed!")
