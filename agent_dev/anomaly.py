#!/usr/bin/env python3
"""
AgentDev Anomaly Detection
==========================

Anomaly detection for monitoring system performance.
"""

import statistics
from typing import Any, Dict, List, Optional


class AnomalyDetector:
    """Anomaly detection for metrics"""

    def __init__(self, threshold_percent: float = 10.0):
        self.threshold_percent = threshold_percent

    def detect_anomalies(self, metrics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in metrics"""
        if len(metrics) < 2:
            return []

        anomalies = []

        # Check pass rate anomaly
        pass_rates = [m["pass_rate"] for m in metrics]
        if len(pass_rates) >= 3:
            # Sort to get median of all values except current
            historical_rates = sorted(pass_rates[1:])  # All except first (current)
            median_pass_rate = statistics.median(historical_rates)
            current_pass_rate = pass_rates[0]  # Most recent

            drop_percent = (
                ((median_pass_rate - current_pass_rate) / median_pass_rate * 100)
                if median_pass_rate > 0
                else 0
            )

            if drop_percent > self.threshold_percent:
                anomalies.append(
                    {
                        "type": "pass_rate_drop",
                        "severity": "high" if drop_percent > 20 else "medium",
                        "current": current_pass_rate,
                        "median": median_pass_rate,
                        "drop_percent": drop_percent,
                        "message": f"Pass rate dropped {drop_percent:.1f}% from median {median_pass_rate:.1f}% to {current_pass_rate:.1f}%",
                    }
                )

        # Check coverage anomaly
        coverage_rates = [m["coverage_overall"] for m in metrics]
        if len(coverage_rates) >= 3:
            # Sort to get median of all values except current
            historical_coverage = sorted(
                coverage_rates[1:]
            )  # All except first (current)
            median_coverage = statistics.median(historical_coverage)
            current_coverage = coverage_rates[0]

            drop_percent = (
                ((median_coverage - current_coverage) / median_coverage * 100)
                if median_coverage > 0
                else 0
            )

            if drop_percent > self.threshold_percent:
                anomalies.append(
                    {
                        "type": "coverage_drop",
                        "severity": "high" if drop_percent > 20 else "medium",
                        "current": current_coverage,
                        "median": median_coverage,
                        "drop_percent": drop_percent,
                        "message": f"Coverage dropped {drop_percent:.1f}% from median {median_coverage:.1f}% to {current_coverage:.1f}%",
                    }
                )

        # Check error count anomaly
        error_counts = [m["lint_errors"] + m["pyright_errors"] for m in metrics]
        if len(error_counts) >= 3:
            # Sort to get median of all values except current
            historical_errors = sorted(error_counts[1:])  # All except first (current)
            median_errors = statistics.median(historical_errors)
            current_errors = error_counts[0]

            increase_percent = (
                ((current_errors - median_errors) / median_errors * 100)
                if median_errors > 0
                else 0
            )

            if increase_percent > self.threshold_percent:
                anomalies.append(
                    {
                        "type": "error_increase",
                        "severity": "high" if increase_percent > 50 else "medium",
                        "current": current_errors,
                        "median": median_errors,
                        "increase_percent": increase_percent,
                        "message": f"Error count increased {increase_percent:.1f}% from median {median_errors} to {current_errors}",
                    }
                )

        return anomalies

    def calculate_z_score(self, values: List[float]) -> Optional[float]:
        """Calculate z-score for anomaly detection"""
        if len(values) < 3:
            return None

        try:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)

            if stdev == 0:
                return 0.0

            z_score = (values[0] - mean) / stdev
            return z_score
        except (statistics.StatisticsError, ZeroDivisionError):
            return None

    def detect_z_score_anomalies(
        self, metrics: List[Dict[str, Any]], z_threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Detect anomalies using z-score"""
        anomalies = []

        # Pass rate z-score
        pass_rates = [m["pass_rate"] for m in metrics]
        if len(pass_rates) >= 3:
            z_score = self.calculate_z_score(pass_rates)
            if z_score is not None and abs(z_score) > z_threshold:
                anomalies.append(
                    {
                        "type": "pass_rate_z_score",
                        "severity": "high" if abs(z_score) > 3 else "medium",
                        "z_score": z_score,
                        "current": pass_rates[0],
                        "message": f"Pass rate z-score anomaly: {z_score:.2f} (threshold: {z_threshold})",
                    }
                )

        # Coverage z-score
        coverage_rates = [m["coverage_overall"] for m in metrics]
        if len(coverage_rates) >= 3:
            z_score = self.calculate_z_score(coverage_rates)
            if z_score is not None and abs(z_score) > z_threshold:
                anomalies.append(
                    {
                        "type": "coverage_z_score",
                        "severity": "high" if abs(z_score) > 3 else "medium",
                        "z_score": z_score,
                        "current": coverage_rates[0],
                        "message": f"Coverage z-score anomaly: {z_score:.2f} (threshold: {z_threshold})",
                    }
                )

        return anomalies

    def generate_alert(self, anomalies: List[Dict[str, Any]]) -> Optional[str]:
        """Generate alert message from anomalies"""
        if not anomalies:
            return None

        high_severity = [a for a in anomalies if a.get("severity") == "high"]
        medium_severity = [a for a in anomalies if a.get("severity") == "medium"]

        alert_parts = []

        if high_severity:
            alert_parts.append("🚨 HIGH SEVERITY ANOMALIES:")
            for anomaly in high_severity:
                alert_parts.append(f"  - {anomaly['message']}")

        if medium_severity:
            alert_parts.append("⚠️ MEDIUM SEVERITY ANOMALIES:")
            for anomaly in medium_severity:
                alert_parts.append(f"  - {anomaly['message']}")

        return "\n".join(alert_parts)
