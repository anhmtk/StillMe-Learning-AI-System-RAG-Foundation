"""
🔔 StillMe Alerting System
=========================

Advanced alerting system for AGI learning automation.
Provides multi-channel notifications and intelligent alerting.

Tính năng:
- Multi-channel alerting (Email, SMS, Desktop, Webhook, Telegram)
- Learning-specific alert templates
- Intelligent alert filtering và rate limiting
- Rich HTML email templates
- AGI evolution milestone notifications
- Performance degradation alerts
- Resource exhaustion warnings

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""

from .alert_manager import (
    Alert,
    AlertChannel,
    AlertManager,
    AlertTemplate,
    DesktopNotifier,
    EmailNotifier,
    SMSNotifier,
    TelegramNotifier,
    WebhookNotifier,
    get_alert_manager,
    send_alert,
)
from .learning_alerts import (
    LearningAlertManager,
    LearningMetrics,
    check_learning_alerts,
    get_learning_alert_manager,
)

__all__ = [
    # Alert Manager
    "AlertManager",
    "Alert",
    "AlertChannel",
    "AlertTemplate",
    "EmailNotifier",
    "DesktopNotifier",
    "TelegramNotifier",
    "SMSNotifier",
    "WebhookNotifier",
    "get_alert_manager",
    "send_alert",
    # Learning Alerts
    "LearningAlertManager",
    "LearningMetrics",
    "get_learning_alert_manager",
    "check_learning_alerts",
]

__version__ = "2.0.0"
__author__ = "StillMe AI Framework"
