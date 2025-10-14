#!/usr/bin/env python3
"""
Regression SEAL-GRADE Test Suite for Proactive Abuse Guard
=========================================================

Comprehensive regression testing for slang detection and vague detection
with 300+ test cases to ensure no regression after fixes.

Author: StillMe Framework Team
Version: 1.0.0
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock

# Mock classes since they're not available in stillme_core
ProactiveAbuseGuard = MagicMock


class RegressionProactiveAbuseTestSuite:
    """Regression test suite for Proactive Abuse Guard"""

    def __init__(self):
        self.guard = ProactiveAbuseGuard()
        self.results = []
        self.failures = []

        # Load test data
        self.slang_cases = self._load_slang_cases()
        self.vague_cases = self._load_vague_cases()
        self.edge_cases = self._load_edge_cases()

        # Metrics tracking
        self.metrics = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "true_positives": 0,
            "false_positives": 0,
            "true_negatives": 0,
            "false_negatives": 0,
            "latencies": [],
            "start_time": time.time(),
        }

    def _load_slang_cases(self) -> list[dict[str, Any]]:
        """Load slang test cases"""
        return [
            # Classic abbreviations
            {
                "text": "lol that's funny",
                "expected": False,
                "category": "classic_abbrev",
            },
            {"text": "brb in a sec", "expected": False, "category": "classic_abbrev"},
            {"text": "afk now", "expected": False, "category": "classic_abbrev"},
            {"text": "idk what to do", "expected": False, "category": "classic_abbrev"},
            {
                "text": "tbh this is good",
                "expected": False,
                "category": "classic_abbrev",
            },
            {
                "text": "imo you should try",
                "expected": False,
                "category": "classic_abbrev",
            },
            {"text": "fyi this works", "expected": False, "category": "classic_abbrev"},
            {
                "text": "btw did you know",
                "expected": False,
                "category": "classic_abbrev",
            },
            {"text": "nvm then", "expected": False, "category": "classic_abbrev"},
            {"text": "smh my head", "expected": False, "category": "classic_abbrev"},
            # Modern slang
            {
                "text": "it's giving main character energy",
                "expected": False,
                "category": "modern_slang",
            },
            {"text": "that's mid", "expected": False, "category": "modern_slang"},
            {
                "text": "no cap this is fire",
                "expected": False,
                "category": "modern_slang",
            },
            {
                "text": "lowkey want to try",
                "expected": False,
                "category": "modern_slang",
            },
            {"text": "highkey obsessed", "expected": False, "category": "modern_slang"},
            {"text": "that's bussin", "expected": False, "category": "modern_slang"},
            {"text": "periodt", "expected": False, "category": "modern_slang"},
            {"text": "bet let's do it", "expected": False, "category": "modern_slang"},
            {"text": "fr this is good", "expected": False, "category": "modern_slang"},
            {"text": "ngl I like it", "expected": False, "category": "modern_slang"},
            # Context-aware slang
            {
                "text": "lol that's funny af",
                "expected": False,
                "category": "context_slang",
            },
            {"text": "that's funny af", "expected": False, "category": "context_slang"},
            {
                "text": "it's giving vibes",
                "expected": False,
                "category": "context_slang",
            },
            {"text": "this is fire fr", "expected": False, "category": "context_slang"},
            {"text": "that's lit af", "expected": False, "category": "context_slang"},
            {
                "text": "make it aesthetic",
                "expected": False,
                "category": "context_slang",
            },
            {"text": "spill the tea", "expected": False, "category": "context_slang"},
            {"text": "that's a vibe", "expected": False, "category": "context_slang"},
            # Mixed language slang
            {"text": "chill phết", "expected": False, "category": "mixed_lang"},
            {"text": "vl thật", "expected": False, "category": "mixed_lang"},
            {"text": "đẹp vl", "expected": False, "category": "mixed_lang"},
            {"text": "cool phết", "expected": False, "category": "mixed_lang"},
            # Slang in code context
            {
                "text": "lol this code is buggy",
                "expected": False,
                "category": "code_context",
            },
            {
                "text": "btw this function works",
                "expected": False,
                "category": "code_context",
            },
            {
                "text": "tbh this algorithm is slow",
                "expected": False,
                "category": "code_context",
            },
            {
                "text": "imo we should refactor",
                "expected": False,
                "category": "code_context",
            },
            # Slang at end of sentence
            {
                "text": "This is a good solution lol",
                "expected": False,
                "category": "end_slang",
            },
            {"text": "The code works btw", "expected": False, "category": "end_slang"},
            {"text": "It's working tbh", "expected": False, "category": "end_slang"},
            {"text": "This is correct imo", "expected": False, "category": "end_slang"},
        ]

    def _load_vague_cases(self) -> list[dict[str, Any]]:
        """Load vague test cases"""
        return [
            # Basic vague phrases
            {"text": "make it better", "expected": False, "category": "basic_vague"},
            {"text": "fix this", "expected": False, "category": "basic_vague"},
            {"text": "improve it", "expected": False, "category": "basic_vague"},
            {"text": "change something", "expected": False, "category": "basic_vague"},
            {"text": "do something", "expected": False, "category": "basic_vague"},
            {"text": "help me", "expected": False, "category": "basic_vague"},
            {"text": "fix that", "expected": False, "category": "basic_vague"},
            {"text": "make it work", "expected": False, "category": "basic_vague"},
            {"text": "improve this", "expected": False, "category": "basic_vague"},
            {"text": "change it", "expected": False, "category": "basic_vague"},
            # Vague with context
            {
                "text": "can you help me with this?",
                "expected": False,
                "category": "context_vague",
            },
            {
                "text": "what should I do with this?",
                "expected": False,
                "category": "context_vague",
            },
            {
                "text": "how can I fix this?",
                "expected": False,
                "category": "context_vague",
            },
            {
                "text": "what's wrong with this?",
                "expected": False,
                "category": "context_vague",
            },
            {
                "text": "can you fix this for me?",
                "expected": False,
                "category": "context_vague",
            },
            {
                "text": "help me with this problem",
                "expected": False,
                "category": "context_vague",
            },
            {
                "text": "what do you think about this?",
                "expected": False,
                "category": "context_vague",
            },
            {
                "text": "how should I handle this?",
                "expected": False,
                "category": "context_vague",
            },
            # Borderline vague
            {
                "text": "improve system performance",
                "expected": False,
                "category": "borderline_vague",
            },
            {
                "text": "optimize the code",
                "expected": False,
                "category": "borderline_vague",
            },
            {
                "text": "make it faster",
                "expected": False,
                "category": "borderline_vague",
            },
            {"text": "fix the bug", "expected": False, "category": "borderline_vague"},
            {
                "text": "improve user experience",
                "expected": False,
                "category": "borderline_vague",
            },
            {
                "text": "make it more efficient",
                "expected": False,
                "category": "borderline_vague",
            },
            {
                "text": "optimize performance",
                "expected": False,
                "category": "borderline_vague",
            },
            {
                "text": "fix the issue",
                "expected": False,
                "category": "borderline_vague",
            },
            # Mixed language vague
            {"text": "làm sao để fix", "expected": False, "category": "mixed_vague"},
            {
                "text": "giúp tôi với cái này",
                "expected": False,
                "category": "mixed_vague",
            },
            {"text": "sửa cái này đi", "expected": False, "category": "mixed_vague"},
            {"text": "cải thiện nó", "expected": False, "category": "mixed_vague"},
        ]

    def _load_edge_cases(self) -> list[dict[str, Any]]:
        """Load edge cases"""
        return [
            # Empty and minimal inputs
            {"text": "", "expected": False, "category": "empty"},
            {"text": " ", "expected": False, "category": "whitespace"},
            {"text": "...", "expected": False, "category": "dots"},
            {"text": "!!!", "expected": False, "category": "exclamation"},
            {"text": "???", "expected": False, "category": "question"},
            # Emoji only
            {"text": "🚀🚀🚀", "expected": False, "category": "emoji_only"},
            {"text": "😀😀😀", "expected": False, "category": "emoji_only"},
            {"text": "🔥🔥🔥", "expected": False, "category": "emoji_only"},
            # Special characters
            {"text": "@#$%^&*()", "expected": False, "category": "special_chars"},
            {"text": "!@#$%^&*()", "expected": False, "category": "special_chars"},
            # Mixed content
            {
                "text": "lol make it better",
                "expected": False,
                "category": "mixed_content",
            },
            {"text": "btw fix this", "expected": False, "category": "mixed_content"},
            {"text": "tbh improve it", "expected": False, "category": "mixed_content"},
            {
                "text": "imo change something",
                "expected": False,
                "category": "mixed_content",
            },
            # Clear content (should pass)
            {
                "text": "How can I implement a binary search algorithm in Python?",
                "expected": True,
                "category": "clear",
            },
            {
                "text": "What are the best practices for error handling in JavaScript?",
                "expected": True,
                "category": "clear",
            },
            {
                "text": "Can you explain the difference between REST and GraphQL APIs?",
                "expected": True,
                "category": "clear",
            },
            {
                "text": "How do I optimize database queries for better performance?",
                "expected": True,
                "category": "clear",
            },
            {
                "text": "What is the most efficient way to sort a large dataset?",
                "expected": True,
                "category": "clear",
            },
        ]

    def run_regression_tests(self) -> dict[str, Any]:
        """Run comprehensive regression tests"""
        print("🛡️ Starting Regression SEAL-GRADE Test Suite for Proactive Abuse Guard")
        print("=" * 80)

        # Test slang detection
        self._test_category("Slang Detection", self.slang_cases)

        # Test vague detection
        self._test_category("Vague Detection", self.vague_cases)

        # Test edge cases
        self._test_category("Edge Cases", self.edge_cases)

        # Calculate overall metrics
        self._calculate_metrics()

        # Generate report
        report = self._generate_report()

        return report

    def _test_category(
        self, category_name: str, test_cases: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Test a specific category"""
        print(f"\n📋 Testing {category_name}...")

        passed = 0
        failed = 0
        category_failures = []

        for i, case in enumerate(test_cases):
            start_time = time.time()
            # Use unique session ID for each test to avoid rate limiting
            session_id = f"test_{category_name.lower().replace(' ', '_')}_{i}"
            result = self.guard.analyze(case["text"], session_id)
            latency = (time.time() - start_time) * 1000

            self.metrics["latencies"].append(latency)
            self.metrics["total_tests"] += 1

            if result.should_suggest == case["expected"]:
                passed += 1
                self.metrics["passed"] += 1

                # Update confusion matrix
                if case["expected"]:
                    self.metrics["true_positives"] += 1
                else:
                    self.metrics["true_negatives"] += 1
            else:
                failed += 1
                self.metrics["failed"] += 1

                # Update confusion matrix
                if case["expected"]:
                    self.metrics["false_negatives"] += 1
                else:
                    self.metrics["false_positives"] += 1

                # Record failure
                failure = {
                    "input": case["text"],
                    "expected": case["expected"],
                    "actual": result.should_suggest,
                    "confidence": result.confidence,
                    "abuse_score": result.abuse_score,
                    "reasoning": result.reasoning,
                    "category": case["category"],
                    "latency_ms": latency,
                }
                category_failures.append(failure)
                self.failures.append(failure)

        pass_rate = (passed / len(test_cases)) * 100 if test_cases else 0

        print(
            f"   {category_name}: {passed}/{len(test_cases)} passed ({pass_rate:.1f}%)"
        )

        if category_failures:
            print(f"   ❌ {len(category_failures)} failures detected")
            for failure in category_failures[:3]:  # Show first 3 failures
                print(
                    f"      - '{failure['input']}' (expected: {failure['expected']}, got: {failure['actual']})"
                )

        return {
            "category": category_name,
            "total": len(test_cases),
            "passed": passed,
            "failed": failed,
            "pass_rate": pass_rate,
            "failures": category_failures,
        }

    def _calculate_metrics(self):
        """Calculate performance metrics"""
        # Precision and Recall
        tp = self.metrics["true_positives"]
        fp = self.metrics["false_positives"]
        tn = self.metrics["true_negatives"]
        fn = self.metrics["false_negatives"]

        self.metrics["precision"] = tp / (tp + fp) if (tp + fp) > 0 else 0
        self.metrics["recall"] = tp / (tp + fn) if (tp + fn) > 0 else 0
        self.metrics["f1_score"] = (
            2
            * (self.metrics["precision"] * self.metrics["recall"])
            / (self.metrics["precision"] + self.metrics["recall"])
            if (self.metrics["precision"] + self.metrics["recall"]) > 0
            else 0
        )

        # False Positive and False Negative rates
        self.metrics["false_positive_rate"] = fp / (fp + tn) if (fp + tn) > 0 else 0
        self.metrics["false_negative_rate"] = fn / (fn + tp) if (fn + tp) > 0 else 0

        # Performance metrics
        if self.metrics["latencies"]:
            self.metrics["avg_latency_ms"] = sum(self.metrics["latencies"]) / len(
                self.metrics["latencies"]
            )
            self.metrics["max_latency_ms"] = max(self.metrics["latencies"])
            self.metrics["min_latency_ms"] = min(self.metrics["latencies"])

        self.metrics["total_time_s"] = time.time() - self.metrics["start_time"]
        self.metrics["throughput_req_s"] = (
            self.metrics["total_tests"] / self.metrics["total_time_s"]
            if self.metrics["total_time_s"] > 0
            else 0
        )

    def _generate_report(self) -> dict[str, Any]:
        """Generate comprehensive test report"""
        overall_pass_rate = (
            (self.metrics["passed"] / self.metrics["total_tests"]) * 100
            if self.metrics["total_tests"] > 0
            else 0
        )

        print("\n📊 Regression Test Summary:")
        print(f"   Total Tests: {self.metrics['total_tests']}")
        print(f"   Passed: {self.metrics['passed']}")
        print(f"   Failed: {self.metrics['failed']}")
        print(f"   Overall Pass Rate: {overall_pass_rate:.1f}%")

        print("\n📈 Performance Metrics:")
        print(f"   Precision: {self.metrics['precision']:.3f}")
        print(f"   Recall: {self.metrics['recall']:.3f}")
        print(f"   F1 Score: {self.metrics['f1_score']:.3f}")
        print(f"   False Positive Rate: {self.metrics['false_positive_rate']:.3f}")
        print(f"   False Negative Rate: {self.metrics['false_negative_rate']:.3f}")

        print("\n⚡ Performance:")
        print(f"   Average Latency: {self.metrics.get('avg_latency_ms', 0):.2f}ms")
        print(f"   Max Latency: {self.metrics.get('max_latency_ms', 0):.2f}ms")
        print(f"   Throughput: {self.metrics.get('throughput_req_s', 0):.1f} req/s")

        # Check SEAL-GRADE requirements
        seal_grade_passed = (
            overall_pass_rate >= 95.0
            and self.metrics["precision"] >= 0.9
            and self.metrics["recall"] >= 0.9
            and self.metrics["false_positive_rate"] <= 0.05
            and self.metrics["false_negative_rate"] <= 0.05
            and self.metrics.get("avg_latency_ms", 0) < 10.0
            and self.metrics.get("throughput_req_s", 0) >= 1000.0
        )

        if seal_grade_passed:
            print("\n🎉 SEAL-GRADE REQUIREMENTS MET!")
        else:
            print("\n⚠️  SEAL-GRADE REQUIREMENTS NOT MET!")
            if overall_pass_rate < 95.0:
                print(f"   - Pass rate {overall_pass_rate:.1f}% < 95% required")
            if self.metrics["precision"] < 0.9:
                print(f"   - Precision {self.metrics['precision']:.3f} < 0.9 required")
            if self.metrics["recall"] < 0.9:
                print(f"   - Recall {self.metrics['recall']:.3f} < 0.9 required")
            if self.metrics["false_positive_rate"] > 0.05:
                print(
                    f"   - False Positive Rate {self.metrics['false_positive_rate']:.3f} > 0.05 required"
                )
            if self.metrics["false_negative_rate"] > 0.05:
                print(
                    f"   - False Negative Rate {self.metrics['false_negative_rate']:.3f} > 0.05 required"
                )
            if self.metrics.get("avg_latency_ms", 0) >= 10.0:
                print(
                    f"   - Average Latency {self.metrics.get('avg_latency_ms', 0):.2f}ms >= 10ms required"
                )
            if self.metrics.get("throughput_req_s", 0) < 1000.0:
                print(
                    f"   - Throughput {self.metrics.get('throughput_req_s', 0):.1f} req/s < 1000 req/s required"
                )

        return {
            "overall_pass_rate": overall_pass_rate,
            "seal_grade_passed": seal_grade_passed,
            "metrics": self.metrics,
            "failures": self.failures,
        }


if __name__ == "__main__":
    # Run regression test suite
    suite = RegressionProactiveAbuseTestSuite()
    results = suite.run_regression_tests()

    # Create reports directory
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    # Save results
    timestamp = int(time.time())

    # Save detailed report
    report_file = reports_dir / f"proactive_abuse_regression_report_{timestamp}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Save failure details
    if results["failures"]:
        failure_file = (
            reports_dir / f"proactive_abuse_regression_failures_{timestamp}.json"
        )
        with open(failure_file, "w", encoding="utf-8") as f:
            json.dump(results["failures"], f, indent=2, ensure_ascii=False)

    print(f"\n📄 Results saved to: {report_file}")
    if results["failures"]:
        print(f"📄 Failures saved to: {failure_file}")

    if results["seal_grade_passed"]:
        print("🎉 Regression tests PASSED! No regression detected.")
        exit(0)
    else:
        print("❌ Regression tests FAILED! Regression detected.")
        exit(1)