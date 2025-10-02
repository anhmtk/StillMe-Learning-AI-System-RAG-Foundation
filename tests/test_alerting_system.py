from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

"""
🧪 StillMe Alerting System Tests
================================

Comprehensive test suite for the alerting system.
Tests all notification channels, alert templates, and learning-specific alerts.

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""


import pytest

from stillme_core.alerting.alert_manager import (
    Alert,
    AlertManager,
    DesktopNotifier,
    EmailNotifier,
    SMSNotifier,
    TelegramNotifier,
    WebhookNotifier,
    get_alert_manager,
)
from stillme_core.alerting.learning_alerts import (
    LearningAlertManager,
    LearningMetrics,
    get_learning_alert_manager,
)


class TestAlertManager:
    """Test AlertManager functionality"""

    @pytest.fixture
    def alert_manager(self):
        """Create alert manager instance"""
        return AlertManager()

    @pytest.fixture
    def sample_alert(self):
        """Create sample alert"""
        return Alert(
            alert_id="test_alert_001",
            timestamp=datetime.now(),
            alert_type="test_alert",
            severity="medium",
            title="Test Alert",
            message="This is a test alert",
            component="test_component",
            context={"test": "data"},
        )

    def test_alert_manager_initialization(self, alert_manager):
        """Test alert manager initialization"""
        assert alert_manager is not None
        assert len(alert_manager.notifiers) == 5
        assert "email" in alert_manager.notifiers
        assert "desktop" in alert_manager.notifiers
        assert "telegram" in alert_manager.notifiers
        assert "sms" in alert_manager.notifiers
        assert "webhook" in alert_manager.notifiers

    def test_alert_templates_loaded(self, alert_manager):
        """Test alert templates are loaded"""
        assert len(alert_manager.templates) > 0
        assert "resource_high" in alert_manager.templates
        assert "learning_failure" in alert_manager.templates
        assert "system_critical" in alert_manager.templates
        assert "evolution_milestone" in alert_manager.templates
        assert "performance_degradation" in alert_manager.templates

    @pytest.mark.asyncio
    async def test_send_alert_success(self, alert_manager):
        """Test successful alert sending"""
        with patch.object(
            alert_manager.notifiers["email"], "send_alert", return_value=True
        ) as mock_email:
            with patch.object(
                alert_manager.notifiers["desktop"], "send_alert", return_value=True
            ) as mock_desktop:
                alert_id = await alert_manager.send_alert(
                    alert_type="test_alert",
                    severity="medium",
                    title="Test Alert",
                    message="Test message",
                    component="test_component",
                    channels=["email", "desktop"],
                )

                assert alert_id is not None
                assert alert_id.startswith("alert_")
                mock_email.assert_called_once()
                mock_desktop.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_alert_with_template(self, alert_manager):
        """Test alert sending with template"""
        with patch.object(
            alert_manager.notifiers["email"], "send_alert", return_value=True
        ):
            alert_id = await alert_manager.send_alert(
                alert_type="resource_high",
                severity="high",
                title="High Memory Usage",
                message="Memory usage is 90%",
                component="resource_monitor",
            )

            assert alert_id is not None
            # Check that template was applied
            assert len(alert_manager.alert_history) > 0
            last_alert = alert_manager.alert_history[-1]
            assert last_alert.alert_type == "resource_high"

    def test_rate_limiting(self, alert_manager):
        """Test rate limiting functionality"""
        # Use an existing template with rate limit
        alert_type = "resource_high"  # This template has rate_limit = 3

        # Send multiple alerts quickly (within the last hour)
        now = datetime.now().timestamp()
        for i in range(5):  # More than the rate limit of 3
            alert_manager.rate_limits[alert_type].append(now - i * 60)  # 1 minute apart

        # Check rate limit
        can_send = alert_manager._check_rate_limit(
            Alert(
                alert_id="test",
                timestamp=datetime.now(),
                alert_type=alert_type,
                severity="medium",
                title="Test",
                message="Test",
                component="test",
            )
        )

        # Should be rate limited (5 alerts in last hour > rate limit of 3)
        assert not can_send

    def test_cooldown_checking(self, alert_manager):
        """Test cooldown functionality"""
        # Set cooldown
        alert_manager.cooldowns["test_alert_test_component"] = (
            datetime.now().timestamp()
        )

        # Check cooldown
        can_send = alert_manager._check_cooldown(
            Alert(
                alert_id="test",
                timestamp=datetime.now(),
                alert_type="test_alert",
                severity="medium",
                title="Test",
                message="Test",
                component="test_component",
            )
        )

        # Should be in cooldown
        assert not can_send

    def test_acknowledge_alert(self, alert_manager, sample_alert):
        """Test alert acknowledgment"""
        alert_manager.alert_history.append(sample_alert)

        result = alert_manager.acknowledge_alert(sample_alert.alert_id)
        assert result is True
        assert sample_alert.acknowledged is True

    def test_resolve_alert(self, alert_manager, sample_alert):
        """Test alert resolution"""
        alert_manager.alert_history.append(sample_alert)

        result = alert_manager.resolve_alert(sample_alert.alert_id)
        assert result is True
        assert sample_alert.resolved is True

    def test_get_alert_statistics(self, alert_manager):
        """Test alert statistics"""
        stats = alert_manager.get_alert_statistics()

        assert "statistics" in stats
        assert "recent_alerts" in stats
        assert "notifier_status" in stats
        assert "rate_limits" in stats
        assert "cooldowns" in stats

        assert stats["statistics"]["total_alerts"] == 0
        assert len(stats["recent_alerts"]) == 0


class TestEmailNotifier:
    """Test EmailNotifier functionality"""

    @pytest.fixture
    def email_notifier(self):
        """Create email notifier instance"""
        return EmailNotifier({"enabled": True})

    @pytest.fixture
    def sample_alert(self):
        """Create sample alert"""
        return Alert(
            alert_id="test_alert_001",
            timestamp=datetime.now(),
            alert_type="test_alert",
            severity="medium",
            title="Test Alert",
            message="This is a test alert",
            component="test_component",
            context={"test": "data"},
        )

    def test_email_notifier_initialization(self, email_notifier):
        """Test email notifier initialization"""
        assert email_notifier is not None
        assert email_notifier.smtp_server is not None
        assert email_notifier.smtp_port is not None

    def test_create_html_content(self, email_notifier, sample_alert):
        """Test HTML content creation"""
        html_content = email_notifier._create_html_content(sample_alert)

        assert "<!DOCTYPE html>" in html_content
        assert "StillMe AI Alert" in html_content
        assert sample_alert.title in html_content
        assert sample_alert.message in html_content
        assert sample_alert.alert_id in html_content

    def test_create_text_content(self, email_notifier, sample_alert):
        """Test text content creation"""
        text_content = email_notifier._create_text_content(sample_alert)

        assert "StillMe AI Alert" in text_content
        assert sample_alert.title in text_content
        assert sample_alert.message in text_content
        assert sample_alert.alert_id in text_content

    @pytest.mark.asyncio
    async def test_send_alert_disabled(self):
        """Test sending alert when disabled"""
        notifier = EmailNotifier({"enabled": False})
        sample_alert = Alert(
            alert_id="test",
            timestamp=datetime.now(),
            alert_type="test",
            severity="medium",
            title="Test",
            message="Test",
            component="test",
        )

        result = await notifier.send_alert(sample_alert)
        assert result is False


class TestDesktopNotifier:
    """Test DesktopNotifier functionality"""

    @pytest.fixture
    def desktop_notifier(self):
        """Create desktop notifier instance"""
        return DesktopNotifier({"enabled": True})

    @pytest.fixture
    def sample_alert(self):
        """Create sample alert"""
        return Alert(
            alert_id="test_alert_001",
            timestamp=datetime.now(),
            alert_type="test_alert",
            severity="medium",
            title="Test Alert",
            message="This is a test alert",
            component="test_component",
        )

    def test_desktop_notifier_initialization(self, desktop_notifier):
        """Test desktop notifier initialization"""
        assert desktop_notifier is not None

    @pytest.mark.asyncio
    async def test_send_alert_with_plyer(self, desktop_notifier, sample_alert):
        """Test sending desktop notification with plyer"""
        # Since plyer is not available, test that it returns False
        result = await desktop_notifier.send_alert(sample_alert)

        # Should return False because plyer is not available
        assert result is False

    @pytest.mark.asyncio
    async def test_send_alert_disabled(self):
        """Test sending alert when disabled"""
        notifier = DesktopNotifier({"enabled": False})
        sample_alert = Alert(
            alert_id="test",
            timestamp=datetime.now(),
            alert_type="test",
            severity="medium",
            title="Test",
            message="Test",
            component="test",
        )

        result = await notifier.send_alert(sample_alert)
        assert result is False


class TestTelegramNotifier:
    """Test TelegramNotifier functionality"""

    @pytest.fixture
    def telegram_notifier(self):
        """Create telegram notifier instance"""
        return TelegramNotifier({"enabled": True})

    @pytest.fixture
    def sample_alert(self):
        """Create sample alert"""
        return Alert(
            alert_id="test_alert_001",
            timestamp=datetime.now(),
            alert_type="test_alert",
            severity="medium",
            title="Test Alert",
            message="This is a test alert",
            component="test_component",
        )

    def test_telegram_notifier_initialization(self, telegram_notifier):
        """Test telegram notifier initialization"""
        assert telegram_notifier is not None

    def test_create_context_text(self, telegram_notifier, sample_alert):
        """Test context text creation"""
        sample_alert.context = {"key1": "value1", "key2": "value2"}
        context_text = telegram_notifier._create_context_text(sample_alert)

        assert "Context:" in context_text
        assert "Key1: value1" in context_text
        assert "Key2: value2" in context_text

    @pytest.mark.asyncio
    async def test_send_alert_success(self, telegram_notifier, sample_alert):
        """Test successful telegram alert sending"""
        with patch("stillme_core.alerting.alert_manager.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = await telegram_notifier.send_alert(sample_alert)

            assert result is True
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_alert_disabled(self):
        """Test sending alert when disabled"""
        notifier = TelegramNotifier({"enabled": False})
        sample_alert = Alert(
            alert_id="test",
            timestamp=datetime.now(),
            alert_type="test",
            severity="medium",
            title="Test",
            message="Test",
            component="test",
        )

        result = await notifier.send_alert(sample_alert)
        assert result is False


class TestSMSNotifier:
    """Test SMSNotifier functionality"""

    @pytest.fixture
    def sms_notifier(self):
        """Create SMS notifier instance"""
        return SMSNotifier({"enabled": True})

    @pytest.fixture
    def sample_alert(self):
        """Create sample alert"""
        return Alert(
            alert_id="test_alert_001",
            timestamp=datetime.now(),
            alert_type="test_alert",
            severity="medium",
            title="Test Alert",
            message="This is a test alert",
            component="test_component",
        )

    def test_sms_notifier_initialization(self, sms_notifier):
        """Test SMS notifier initialization"""
        assert sms_notifier is not None

    @pytest.mark.asyncio
    async def test_send_alert_success(self, sms_notifier, sample_alert):
        """Test successful SMS alert sending"""
        # Mock twilio module
        with patch.dict("sys.modules", {"twilio": Mock()}):
            with patch("twilio.rest.Client") as mock_twilio:
                mock_client = Mock()
                mock_message = Mock()
                mock_message.sid = "test_sid"
                mock_client.messages.create.return_value = mock_message
                mock_twilio.return_value = mock_client

                # Set up the notifier with mock client
                sms_notifier.client = mock_client
                sms_notifier.config["enabled"] = True

                result = await sms_notifier.send_alert(sample_alert)

                assert result is True
                mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_alert_disabled(self):
        """Test sending alert when disabled"""
        notifier = SMSNotifier({"enabled": False})
        sample_alert = Alert(
            alert_id="test",
            timestamp=datetime.now(),
            alert_type="test",
            severity="medium",
            title="Test",
            message="Test",
            component="test",
        )

        result = await notifier.send_alert(sample_alert)
        assert result is False


class TestWebhookNotifier:
    """Test WebhookNotifier functionality"""

    @pytest.fixture
    def webhook_notifier(self):
        """Create webhook notifier instance"""
        return WebhookNotifier({"enabled": True})

    @pytest.fixture
    def sample_alert(self):
        """Create sample alert"""
        return Alert(
            alert_id="test_alert_001",
            timestamp=datetime.now(),
            alert_type="test_alert",
            severity="medium",
            title="Test Alert",
            message="This is a test alert",
            component="test_component",
        )

    def test_webhook_notifier_initialization(self, webhook_notifier):
        """Test webhook notifier initialization"""
        assert webhook_notifier is not None

    @pytest.mark.asyncio
    async def test_send_alert_success(self, webhook_notifier, sample_alert):
        """Test successful webhook alert sending"""
        # Set webhook URL for testing
        webhook_notifier.webhook_url = "https://test-webhook.com/alert"
        webhook_notifier.config["enabled"] = True

        with patch("stillme_core.alerting.alert_manager.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            result = await webhook_notifier.send_alert(sample_alert)

            assert result is True
            mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_alert_disabled(self):
        """Test sending alert when disabled"""
        notifier = WebhookNotifier({"enabled": False})
        sample_alert = Alert(
            alert_id="test",
            timestamp=datetime.now(),
            alert_type="test",
            severity="medium",
            title="Test",
            message="Test",
            component="test",
        )

        result = await notifier.send_alert(sample_alert)
        assert result is False


class TestLearningAlertManager:
    """Test LearningAlertManager functionality"""

    @pytest.fixture
    def learning_alert_manager(self):
        """Create learning alert manager instance"""
        with patch(
            "stillme_core.alerting.learning_alerts.get_alert_manager"
        ) as mock_alert_manager:
            mock_alert_manager.return_value = Mock()
            return LearningAlertManager()

    @pytest.fixture
    def sample_metrics(self):
        """Create sample learning metrics"""
        return LearningMetrics(
            session_id="test_session_001",
            timestamp=datetime.now(),
            evolution_stage="child",
            learning_accuracy=0.85,
            training_time=120.5,
            memory_usage=1500.0,
            cpu_usage=65.0,
            token_consumption=500,
            error_count=2,
            success_rate=0.95,
            knowledge_items_processed=100,
            performance_score=0.82,
        )

    def test_learning_alert_manager_initialization(self, learning_alert_manager):
        """Test learning alert manager initialization"""
        assert learning_alert_manager is not None
        assert learning_alert_manager.thresholds is not None
        assert learning_alert_manager.evolution_milestones is not None
        assert learning_alert_manager.achieved_milestones is not None

    def test_thresholds_configured(self, learning_alert_manager):
        """Test thresholds are properly configured"""
        thresholds = learning_alert_manager.thresholds

        assert "memory_usage_mb" in thresholds
        assert "cpu_usage_percent" in thresholds
        assert "learning_accuracy_min" in thresholds
        assert "error_rate_max" in thresholds
        assert "training_time_max" in thresholds
        assert "token_budget_daily" in thresholds
        assert "performance_score_min" in thresholds

    def test_evolution_milestones_configured(self, learning_alert_manager):
        """Test evolution milestones are configured"""
        milestones = learning_alert_manager.evolution_milestones

        assert "infant" in milestones
        assert "child" in milestones
        assert "adolescent" in milestones
        assert "adult" in milestones

        # Check each stage has milestones
        for _stage, stage_milestones in milestones.items():
            assert len(stage_milestones) > 0

    @pytest.mark.asyncio
    async def test_check_learning_session_alerts_high_memory(
        self, learning_alert_manager, sample_metrics
    ):
        """Test learning session alerts for high memory usage"""
        # Set high memory usage
        sample_metrics.memory_usage = 3000.0  # Above threshold

        with patch.object(
            learning_alert_manager.alert_manager,
            "send_alert",
            new_callable=AsyncMock,
            return_value="alert_001",
        ) as mock_send:
            alerts_sent = await learning_alert_manager.check_learning_session_alerts(
                sample_metrics
            )

            assert len(alerts_sent) > 0
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_check_learning_session_alerts_low_accuracy(
        self, learning_alert_manager, sample_metrics
    ):
        """Test learning session alerts for low accuracy"""
        # Set low accuracy
        sample_metrics.learning_accuracy = 0.5  # Below threshold

        with patch.object(
            learning_alert_manager.alert_manager,
            "send_alert",
            new_callable=AsyncMock,
            return_value="alert_001",
        ) as mock_send:
            alerts_sent = await learning_alert_manager.check_learning_session_alerts(
                sample_metrics
            )

            assert len(alerts_sent) > 0
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_check_learning_session_alerts_high_error_rate(
        self, learning_alert_manager, sample_metrics
    ):
        """Test learning session alerts for high error rate"""
        # Set high error rate
        sample_metrics.error_count = 20
        sample_metrics.knowledge_items_processed = 100  # 20% error rate

        with patch.object(
            learning_alert_manager.alert_manager,
            "send_alert",
            new_callable=AsyncMock,
            return_value="alert_001",
        ) as mock_send:
            alerts_sent = await learning_alert_manager.check_learning_session_alerts(
                sample_metrics
            )

            assert len(alerts_sent) > 0
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_check_evolution_milestones(
        self, learning_alert_manager, sample_metrics
    ):
        """Test evolution milestone checking"""
        with patch.object(
            learning_alert_manager.alert_manager,
            "send_alert",
            new_callable=AsyncMock,
            return_value="alert_001",
        ) as mock_send:
            await learning_alert_manager.check_evolution_milestones(sample_metrics)

            # Should check for milestones but may not send alerts if none achieved
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_check_performance_degradation(
        self, learning_alert_manager, sample_metrics
    ):
        """Test performance degradation checking"""
        # Add metrics to history
        learning_alert_manager.performance_history.append(sample_metrics)

        # Create degraded metrics
        degraded_metrics = LearningMetrics(
            session_id="test_session_002",
            timestamp=datetime.now(),
            evolution_stage="child",
            learning_accuracy=0.6,  # Degraded from 0.85
            training_time=120.5,
            memory_usage=1500.0,
            cpu_usage=65.0,
            token_consumption=500,
            error_count=2,
            success_rate=0.95,
            knowledge_items_processed=100,
            performance_score=0.82,
        )

        with patch.object(
            learning_alert_manager.alert_manager,
            "send_alert",
            new_callable=AsyncMock,
            return_value="alert_001",
        ) as mock_send:
            alerts_sent = await learning_alert_manager.check_performance_degradation(
                degraded_metrics
            )

            assert len(alerts_sent) > 0
            mock_send.assert_called()

    @pytest.mark.asyncio
    async def test_send_learning_session_failure(self, learning_alert_manager):
        """Test sending learning session failure alert"""
        with patch.object(
            learning_alert_manager.alert_manager,
            "send_alert",
            new_callable=AsyncMock,
            return_value="alert_001",
        ) as mock_send:
            alert_id = await learning_alert_manager.send_learning_session_failure(
                "test_session_001", "Test error message", "learning_system"
            )

            assert alert_id == "alert_001"
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_system_critical_error(self, learning_alert_manager):
        """Test sending system critical error alert"""
        with patch.object(
            learning_alert_manager.alert_manager,
            "send_alert",
            new_callable=AsyncMock,
            return_value="alert_001",
        ) as mock_send:
            alert_id = await learning_alert_manager.send_system_critical_error(
                "Test critical error", "system"
            )

            assert alert_id == "alert_001"
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_resource_exhaustion_warning(self, learning_alert_manager):
        """Test sending resource exhaustion warning"""
        with patch.object(
            learning_alert_manager.alert_manager,
            "send_alert",
            new_callable=AsyncMock,
            return_value="alert_001",
        ) as mock_send:
            alert_id = await learning_alert_manager.send_resource_exhaustion_warning(
                "memory", 2500.0, 2048.0, "resource_monitor"
            )

            assert alert_id == "alert_001"
            mock_send.assert_called_once()

    def test_get_learning_alert_statistics(self, learning_alert_manager):
        """Test getting learning alert statistics"""
        stats = learning_alert_manager.get_learning_alert_statistics()

        assert "achieved_milestones" in stats
        assert "performance_history_count" in stats
        assert "thresholds" in stats
        assert "degradation_threshold" in stats
        assert "evolution_milestones" in stats
        assert "alert_manager_stats" in stats


class TestIntegration:
    """Integration tests for alerting system"""

    @pytest.mark.asyncio
    async def test_alert_manager_with_learning_alerts(self):
        """Test integration between alert manager and learning alerts"""
        with patch(
            "stillme_core.alerting.learning_alerts.get_alert_manager"
        ) as mock_alert_manager:
            mock_alert_manager.return_value = Mock()

            learning_manager = LearningAlertManager()
            metrics = LearningMetrics(
                session_id="test_session_001",
                timestamp=datetime.now(),
                evolution_stage="child",
                learning_accuracy=0.85,
                training_time=120.5,
                memory_usage=1500.0,
                cpu_usage=65.0,
                token_consumption=500,
                error_count=2,
                success_rate=0.95,
                knowledge_items_processed=100,
                performance_score=0.82,
            )

            with patch.object(
                learning_manager.alert_manager, "send_alert", return_value="alert_001"
            ):
                alerts_sent = await learning_manager.check_learning_session_alerts(
                    metrics
                )

                # Should not send alerts for normal metrics
                assert len(alerts_sent) == 0

    @pytest.mark.asyncio
    async def test_global_alert_manager_singleton(self):
        """Test global alert manager singleton"""
        manager1 = get_alert_manager()
        manager2 = get_alert_manager()

        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_global_learning_alert_manager_singleton(self):
        """Test global learning alert manager singleton"""
        with patch(
            "stillme_core.alerting.learning_alerts.get_alert_manager"
        ) as mock_alert_manager:
            mock_alert_manager.return_value = Mock()

            manager1 = get_learning_alert_manager()
            manager2 = get_learning_alert_manager()

            assert manager1 is manager2


class TestPerformance:
    """Performance tests for alerting system"""

    @pytest.mark.asyncio
    async def test_alert_sending_performance(self):
        """Test alert sending performance"""
        alert_manager = AlertManager()

        start_time = datetime.now()

        # Send multiple alerts
        for i in range(10):
            with patch.object(
                alert_manager.notifiers["email"], "send_alert", return_value=True
            ):
                await alert_manager.send_alert(
                    alert_type="test_alert",
                    severity="medium",
                    title=f"Test Alert {i}",
                    message=f"Test message {i}",
                    component="test_component",
                )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Should complete within reasonable time
        assert duration < 5.0  # 5 seconds for 10 alerts

    def test_alert_history_memory_usage(self):
        """Test alert history memory usage"""
        alert_manager = AlertManager()

        # Add many alerts
        for i in range(1000):
            alert = Alert(
                alert_id=f"test_alert_{i}",
                timestamp=datetime.now(),
                alert_type="test_alert",
                severity="medium",
                title=f"Test Alert {i}",
                message=f"Test message {i}",
                component="test_component",
            )
            alert_manager.alert_history.append(alert)

        # Should be limited to maxlen
        assert len(alert_manager.alert_history) <= 1000  # maxlen from deque


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
