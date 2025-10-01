"""
Kill Switch Integration Tests
Tests for security monitoring and kill switch functionality
"""

from datetime import datetime, timedelta

import pytest

from stillme_core.security import (
    SecurityAuditLogger,
    SecurityEvent,
    SecurityLevel,
    SecurityMonitor,
)


class TestKillSwitch:
    """Test kill switch functionality"""

    @pytest.fixture
    def security_monitor(self):
        """Create security monitor instance"""
        return SecurityMonitor()

    @pytest.fixture
    def audit_logger(self):
        """Create audit logger instance"""
        return SecurityAuditLogger()

    def test_kill_switch_activation(self, security_monitor, audit_logger):
        """Test kill switch activation when thresholds are exceeded"""
        # Generate high-risk events to trigger kill switch
        for i in range(15):  # Exceed threshold of 10
            event = SecurityEvent(
                event_id=f"event_{i}",
                timestamp=datetime.now(),
                event_type="suspicious_activity",
                severity=SecurityLevel.HIGH,
                source_ip="192.168.1.100",
                user_agent="malicious-bot",
                request_path="/api/sensitive",
                details={"risk_score": 0.8, "activity": "data_exfiltration"},
                risk_score=0.8
            )
            audit_logger.log_security_event(event)

        # Check for alerts
        alerts = security_monitor.check_security_alerts()

        # Should have high-risk events alert
        high_risk_alerts = [alert for alert in alerts if alert["type"] == "high_risk_events"]
        assert len(high_risk_alerts) > 0
        assert high_risk_alerts[0]["severity"] == "HIGH"
        assert high_risk_alerts[0]["count"] >= 10

    def test_rate_limit_violation_alert(self, security_monitor, audit_logger):
        """Test rate limit violation alerting"""
        # Generate rate limit violation events
        for i in range(150):  # Exceed threshold of 100
            event = SecurityEvent(
                event_id=f"rate_limit_{i}",
                timestamp=datetime.now(),
                event_type="rate_limit_violation",
                severity=SecurityLevel.MEDIUM,
                source_ip="192.168.1.200",
                user_agent="aggressive-scanner",
                request_path="/api/endpoint",
                details={"rate_limit_result": {"limit": 100, "window": 60}},
                risk_score=0.5
            )
            audit_logger.log_security_event(event)

        # Check for alerts
        alerts = security_monitor.check_security_alerts()

        # Should have rate limit violation alert
        rate_limit_alerts = [alert for alert in alerts if alert["type"] == "rate_limit_violations"]
        assert len(rate_limit_alerts) > 0
        assert rate_limit_alerts[0]["severity"] == "MEDIUM"
        assert rate_limit_alerts[0]["count"] >= 100

    def test_security_dashboard_data(self, security_monitor, audit_logger):
        """Test security dashboard data generation"""
        # Generate some test events
        for i in range(5):
            event = SecurityEvent(
                event_id=f"test_event_{i}",
                timestamp=datetime.now(),
                event_type="test_event",
                severity=SecurityLevel.MEDIUM,
                source_ip="192.168.1.1",
                user_agent="test-agent",
                request_path="/test",
                details={"test": True},
                risk_score=0.5
            )
            audit_logger.log_security_event(event)

        # Get dashboard data
        dashboard_data = security_monitor.get_security_dashboard_data()

        # Verify dashboard data structure
        assert "risk_summary" in dashboard_data
        assert "active_alerts" in dashboard_data
        assert "security_status" in dashboard_data
        assert "last_updated" in dashboard_data

        # Verify risk summary
        risk_summary = dashboard_data["risk_summary"]
        assert "total_events" in risk_summary
        assert "risk_levels" in risk_summary
        assert "avg_risk_score" in risk_summary
        assert "high_risk_events" in risk_summary

        assert risk_summary["total_events"] >= 5
        assert risk_summary["avg_risk_score"] > 0

    def test_kill_switch_thresholds(self, security_monitor):
        """Test kill switch threshold configuration"""
        # Test default thresholds
        assert security_monitor.alert_thresholds["high_risk_events_per_hour"] == 10
        assert security_monitor.alert_thresholds["rate_limit_violations_per_hour"] == 100
        assert security_monitor.alert_thresholds["failed_authentication_per_hour"] == 50

        # Test threshold modification
        security_monitor.alert_thresholds["high_risk_events_per_hour"] = 5

        assert security_monitor.alert_thresholds["high_risk_events_per_hour"] == 5

    def test_security_event_risk_scoring(self, audit_logger):
        """Test security event risk scoring"""
        # Test different risk levels
        low_risk_event = SecurityEvent(
            event_id="low_risk",
            timestamp=datetime.now(),
            event_type="normal_activity",
            severity=SecurityLevel.LOW,
            source_ip="192.168.1.1",
            user_agent="normal-browser",
            request_path="/api/normal",
            details={"activity": "normal"},
            risk_score=0.2
        )

        high_risk_event = SecurityEvent(
            event_id="high_risk",
            timestamp=datetime.now(),
            event_type="suspicious_activity",
            severity=SecurityLevel.HIGH,
            source_ip="192.168.1.100",
            user_agent="malicious-bot",
            request_path="/api/sensitive",
            details={"activity": "data_exfiltration"},
            risk_score=0.8
        )

        # Log events
        audit_logger.log_security_event(low_risk_event)
        audit_logger.log_security_event(high_risk_event)

        # Check risk summary
        risk_summary = audit_logger.get_risk_summary()

        assert risk_summary["total_events"] == 2
        assert risk_summary["risk_levels"]["low"] == 1
        assert risk_summary["risk_levels"]["high"] == 1
        assert risk_summary["high_risk_events"] == 1
        assert risk_summary["avg_risk_score"] == 0.5

    def test_security_event_filtering(self, audit_logger):
        """Test security event filtering by time"""
        # Create events at different times
        now = datetime.now()
        old_event = SecurityEvent(
            event_id="old_event",
            timestamp=now - timedelta(hours=2),
            event_type="old_activity",
            severity=SecurityLevel.MEDIUM,
            source_ip="192.168.1.1",
            user_agent="old-agent",
            request_path="/old",
            details={"old": True},
            risk_score=0.5
        )

        recent_event = SecurityEvent(
            event_id="recent_event",
            timestamp=now,
            event_type="recent_activity",
            severity=SecurityLevel.MEDIUM,
            source_ip="192.168.1.1",
            user_agent="recent-agent",
            request_path="/recent",
            details={"recent": True},
            risk_score=0.5
        )

        # Log events
        audit_logger.log_security_event(old_event)
        audit_logger.log_security_event(recent_event)

        # Get events from last hour (should only include recent event)
        recent_events = audit_logger.get_security_events(hours=1)

        assert len(recent_events) == 1
        assert recent_events[0].event_id == "recent_event"

        # Get events from last 3 hours (should include both events)
        all_events = audit_logger.get_security_events(hours=3)

        assert len(all_events) == 2

    def test_kill_switch_integration_workflow(self, security_monitor, audit_logger):
        """Test complete kill switch integration workflow"""
        # Step 1: Normal operation - no alerts
        alerts = security_monitor.check_security_alerts()
        assert len(alerts) == 0

        # Step 2: Generate suspicious activity
        for i in range(12):  # Exceed high-risk threshold
            event = SecurityEvent(
                event_id=f"suspicious_{i}",
                timestamp=datetime.now(),
                event_type="suspicious_activity",
                severity=SecurityLevel.HIGH,
                source_ip="192.168.1.100",
                user_agent="malicious-bot",
                request_path="/api/sensitive",
                details={"risk_score": 0.8, "activity": "data_exfiltration"},
                risk_score=0.8
            )
            audit_logger.log_security_event(event)

        # Step 3: Check for alerts
        alerts = security_monitor.check_security_alerts()
        assert len(alerts) > 0

        # Step 4: Verify alert details
        high_risk_alert = alerts[0]
        assert high_risk_alert["type"] == "high_risk_events"
        assert high_risk_alert["severity"] == "HIGH"
        assert high_risk_alert["count"] >= 10

        # Step 5: Get dashboard data
        dashboard_data = security_monitor.get_security_dashboard_data()
        assert dashboard_data["security_status"] == "WARNING"
        assert len(dashboard_data["active_alerts"]) > 0

        # Step 6: Verify risk summary
        risk_summary = dashboard_data["risk_summary"]
        assert risk_summary["high_risk_events"] >= 10
        assert risk_summary["avg_risk_score"] > 0.7

    def test_kill_switch_alert_types(self, security_monitor, audit_logger):
        """Test different types of kill switch alerts"""
        # Test high-risk events alert
        for i in range(15):
            event = SecurityEvent(
                event_id=f"high_risk_{i}",
                timestamp=datetime.now(),
                event_type="suspicious_activity",
                severity=SecurityLevel.HIGH,
                source_ip="192.168.1.100",
                user_agent="malicious-bot",
                request_path="/api/sensitive",
                details={"risk_score": 0.8},
                risk_score=0.8
            )
            audit_logger.log_security_event(event)

        # Test rate limit violations alert
        for i in range(150):
            event = SecurityEvent(
                event_id=f"rate_limit_{i}",
                timestamp=datetime.now(),
                event_type="rate_limit_violation",
                severity=SecurityLevel.MEDIUM,
                source_ip="192.168.1.200",
                user_agent="aggressive-scanner",
                request_path="/api/endpoint",
                details={"rate_limit_result": {"limit": 100}},
                risk_score=0.5
            )
            audit_logger.log_security_event(event)

        # Check for multiple alerts
        alerts = security_monitor.check_security_alerts()

        alert_types = [alert["type"] for alert in alerts]
        assert "high_risk_events" in alert_types
        assert "rate_limit_violations" in alert_types

        # Verify alert counts
        high_risk_alert = next(alert for alert in alerts if alert["type"] == "high_risk_events")
        rate_limit_alert = next(alert for alert in alerts if alert["type"] == "rate_limit_violations")

        assert high_risk_alert["count"] >= 10
        assert rate_limit_alert["count"] >= 100

    def test_kill_switch_alert_severity(self, security_monitor, audit_logger):
        """Test kill switch alert severity levels"""
        # Generate critical events
        for i in range(5):
            event = SecurityEvent(
                event_id=f"critical_{i}",
                timestamp=datetime.now(),
                event_type="critical_attack",
                severity=SecurityLevel.CRITICAL,
                source_ip="192.168.1.100",
                user_agent="attack-bot",
                request_path="/api/critical",
                details={"risk_score": 0.9, "attack_type": "rce"},
                risk_score=0.9
            )
            audit_logger.log_security_event(event)

        # Check for alerts
        alerts = security_monitor.check_security_alerts()

        # Should have high-risk events alert due to critical events
        high_risk_alerts = [alert for alert in alerts if alert["type"] == "high_risk_events"]
        assert len(high_risk_alerts) > 0
        assert high_risk_alerts[0]["severity"] == "HIGH"
        assert high_risk_alerts[0]["count"] >= 5
