#!/usr/bin/env python3
"""
Test Monitoring System
======================

Basic tests for monitoring and anomaly detection.
"""

import pytest
import tempfile
from datetime import datetime, UTC
from pathlib import Path

from agent_dev.anomaly import AnomalyDetector
from agent_dev.self_monitoring import MonitoringSystem
from agent_dev.persistence.models import create_database_engine
from agent_dev.persistence.repo import AgentDevRepo


class TestMonitoringSystem:
    """Test monitoring system"""

    def setup_method(self):
        """Setup test database"""
        self.db_path = tempfile.mktemp(suffix=".db")
        self.engine = create_database_engine(f"sqlite:///{self.db_path}")

        # Create tables
        from agent_dev.persistence.models import Base

        Base.metadata.create_all(self.engine)

        self.repo = AgentDevRepo(self.engine)
        self.monitoring = MonitoringSystem(self.repo)

    def teardown_method(self):
        """Cleanup test database"""
        Path(self.db_path).unlink(missing_ok=True)

    def test_log_run(self):
        """Test logging run to JSONL"""
        metrics = {
            "timestamp": datetime.now(UTC),
            "pass_rate": 85.0,
            "fail_rate": 15.0,
            "coverage_overall": 80.0,
            "coverage_touched": 90.0,
            "lint_errors": 5,
            "pyright_errors": 2,
            "duration": 120.0,
            "total_tests": 100,
        }

        self.monitoring.log_run(metrics)

        # Check if log file was created
        log_file = Path("logs/agentdev_run.jsonl")
        assert log_file.exists()

        # Check log content
        with open(log_file, "r") as f:
            content = f.read()
            assert "pass_rate" in content
            assert "85.0" in content

    def test_record_metrics(self):
        """Test recording metrics to database"""
        metrics_id = self.monitoring.record_metrics(
            {
                "timestamp": datetime.now(UTC),
                "pass_rate": 90.0,
                "fail_rate": 10.0,
                "coverage_overall": 85.0,
                "coverage_touched": 95.0,
                "lint_errors": 3,
                "pyright_errors": 1,
                "duration": 100.0,
            }
        )

        assert metrics_id > 0

    def test_get_recent_metrics(self):
        """Test getting recent metrics"""
        # Record some test metrics
        for i in range(5):
            self.monitoring.record_metrics(
                {
                    "timestamp": datetime.now(UTC),
                    "pass_rate": 80.0 + i,
                    "fail_rate": 20.0 - i,
                    "coverage_overall": 75.0 + i,
                    "coverage_touched": 85.0 + i,
                    "lint_errors": 5 - i,
                    "pyright_errors": 2 - i,
                    "duration": 100.0 + i,
                }
            )

        recent = self.monitoring.get_recent_metrics(days=7)
        assert len(recent) == 5
        assert all("pass_rate" in m for m in recent)


class TestAnomalyDetector:
    """Test anomaly detection"""

    def test_detect_anomalies_pass_rate_drop(self):
        """Test detecting pass rate drop anomaly"""
        detector = AnomalyDetector(threshold_percent=10.0)

        # Create metrics with pass rate drop (current first, then historical)
        metrics = [
            {
                "pass_rate": 75.0,
                "coverage_overall": 80.0,
                "lint_errors": 6,
                "pyright_errors": 3,
            },  # Current (anomaly)
            {
                "pass_rate": 80.0,
                "coverage_overall": 82.0,
                "lint_errors": 5,
                "pyright_errors": 2,
            },
            {
                "pass_rate": 85.0,
                "coverage_overall": 85.0,
                "lint_errors": 4,
                "pyright_errors": 2,
            },
            {
                "pass_rate": 90.0,
                "coverage_overall": 88.0,
                "lint_errors": 3,
                "pyright_errors": 1,
            },
            {
                "pass_rate": 95.0,
                "coverage_overall": 90.0,
                "lint_errors": 2,
                "pyright_errors": 1,
            },
        ]

        anomalies = detector.detect_anomalies(metrics)

        assert len(anomalies) > 0
        assert any(a["type"] == "pass_rate_drop" for a in anomalies)

    def test_detect_anomalies_coverage_drop(self):
        """Test detecting coverage drop anomaly"""
        detector = AnomalyDetector(threshold_percent=10.0)

        # Create metrics with coverage drop (current first, then historical)
        metrics = [
            {
                "pass_rate": 80.0,
                "coverage_overall": 75.0,
                "lint_errors": 6,
                "pyright_errors": 3,
            },  # Current (anomaly)
            {
                "pass_rate": 82.0,
                "coverage_overall": 88.0,
                "lint_errors": 5,
                "pyright_errors": 2,
            },
            {
                "pass_rate": 85.0,
                "coverage_overall": 90.0,
                "lint_errors": 4,
                "pyright_errors": 2,
            },
            {
                "pass_rate": 88.0,
                "coverage_overall": 92.0,
                "lint_errors": 3,
                "pyright_errors": 1,
            },
            {
                "pass_rate": 90.0,
                "coverage_overall": 95.0,
                "lint_errors": 2,
                "pyright_errors": 1,
            },
        ]

        anomalies = detector.detect_anomalies(metrics)

        assert len(anomalies) > 0
        assert any(a["type"] == "coverage_drop" for a in anomalies)

    def test_detect_anomalies_error_increase(self):
        """Test detecting error count increase anomaly"""
        detector = AnomalyDetector(threshold_percent=10.0)

        # Create metrics with error increase (current first, then historical)
        metrics = [
            {
                "pass_rate": 80.0,
                "coverage_overall": 75.0,
                "lint_errors": 15,
                "pyright_errors": 8,
            },  # Current (anomaly)
            {
                "pass_rate": 82.0,
                "coverage_overall": 78.0,
                "lint_errors": 5,
                "pyright_errors": 2,
            },
            {
                "pass_rate": 85.0,
                "coverage_overall": 80.0,
                "lint_errors": 4,
                "pyright_errors": 2,
            },
            {
                "pass_rate": 88.0,
                "coverage_overall": 83.0,
                "lint_errors": 3,
                "pyright_errors": 1,
            },
            {
                "pass_rate": 90.0,
                "coverage_overall": 85.0,
                "lint_errors": 2,
                "pyright_errors": 1,
            },
        ]

        anomalies = detector.detect_anomalies(metrics)

        assert len(anomalies) > 0
        assert any(a["type"] == "error_increase" for a in anomalies)

    def test_calculate_z_score(self):
        """Test z-score calculation"""
        detector = AnomalyDetector()

        # Normal distribution
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        z_score = detector.calculate_z_score(values)

        assert z_score is not None
        assert abs(z_score) < 2.0  # Should be within normal range

        # Anomalous value
        values = [1.0, 2.0, 3.0, 4.0, 20.0]  # Last value is extreme outlier
        z_score = detector.calculate_z_score(values)

        assert z_score is not None
        assert abs(z_score) > 0.5  # Should be anomalous

    def test_generate_alert(self):
        """Test alert generation"""
        detector = AnomalyDetector()

        anomalies = [
            {
                "type": "pass_rate_drop",
                "severity": "high",
                "message": "Pass rate dropped 20% from median 90% to 70%",
            },
            {
                "type": "coverage_drop",
                "severity": "medium",
                "message": "Coverage dropped 15% from median 85% to 70%",
            },
        ]

        alert = detector.generate_alert(anomalies)

        assert alert is not None
        assert "HIGH SEVERITY ANOMALIES" in alert
        assert "MEDIUM SEVERITY ANOMALIES" in alert
        assert "Pass rate dropped" in alert
        assert "Coverage dropped" in alert


if __name__ == "__main__":
    pytest.main([__file__])