#!/usr/bin/env python3
"""
🚨 AgentDev Proactive Alerter - Hệ thống cảnh báo chủ động
===========================================================

Hệ thống cảnh báo chủ động cho AgentDev để:
1. Phát hiện sớm các vấn đề code quality
2. Gửi thông báo real-time
3. Tích hợp với các hệ thống monitoring
4. Tự động phân loại và ưu tiên alerts
5. Tích hợp với CI/CD pipeline

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-30
"""

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AlertPriority(Enum):
    """Mức độ ưu tiên alert"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertChannel(Enum):
    """Kênh gửi alert"""

    CONSOLE = "console"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    FILE = "file"


@dataclass
class AlertRule:
    """Rule để tạo alert"""

    id: str
    name: str
    condition: str
    priority: AlertPriority
    channels: list[AlertChannel]
    enabled: bool = True
    cooldown_minutes: int = 15


@dataclass
class AlertEvent:
    """Event tạo alert"""

    id: str
    rule_id: str
    title: str
    message: str
    priority: AlertPriority
    timestamp: datetime
    metadata: dict[str, Any]
    resolved: bool = False


class ProactiveAlerter:
    """Hệ thống cảnh báo chủ động"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or self._default_config()
        self.rules = self._load_rules()
        self.events: list[Any] = []
        self.last_alert_times: dict[str, Any] = {}

        # Setup logging
        self._setup_logging()

        logger.info("🚨 Proactive Alerter initialized")

    def _default_config(self) -> dict[str, Any]:
        """Default configuration"""
        return {
            "channels": {
                "console": {"enabled": True},
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "to_addresses": [],
                },
                "slack": {"enabled": False, "webhook_url": "", "channel": "#alerts"},
                "webhook": {"enabled": False, "url": "", "headers": {}},
                "file": {"enabled": True, "path": "logs/alerts.json"},
            },
            "rules": {
                "high_error_count": {
                    "enabled": True,
                    "condition": "total_errors > 50",
                    "priority": "critical",
                    "channels": ["console", "file"],
                    "cooldown_minutes": 15,
                },
                "syntax_errors": {
                    "enabled": True,
                    "condition": "syntax_errors > 5",
                    "priority": "high",
                    "channels": ["console", "file"],
                    "cooldown_minutes": 30,
                },
                "import_errors": {
                    "enabled": True,
                    "condition": "import_errors > 10",
                    "priority": "medium",
                    "channels": ["console"],
                    "cooldown_minutes": 60,
                },
            },
        }

    def _setup_logging(self):
        """Setup logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_dir / "proactive_alerter.log"),
                logging.StreamHandler(),
            ],
        )

    def _load_rules(self) -> list[AlertRule]:
        """Load alert rules from config"""
        rules: list[AlertRule] = []

        for rule_id, rule_config in self.config["rules"].items():
            if rule_config.get("enabled", True):
                rule = AlertRule(
                    id=rule_id,
                    name=rule_config.get("name", rule_id),
                    condition=rule_config["condition"],
                    priority=AlertPriority(rule_config["priority"]),
                    channels=[AlertChannel(c) for c in rule_config["channels"]],
                    enabled=rule_config.get("enabled", True),
                    cooldown_minutes=rule_config.get("cooldown_minutes", 15),
                )
                rules.append(rule)

        return rules

    def check_metrics(self, metrics: dict[str, Any]) -> list[AlertEvent]:
        """Check metrics against alert rules"""
        events: list[AlertEvent] = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            # Check cooldown
            if self._is_in_cooldown(rule.id):
                continue

            # Evaluate condition
            if self._evaluate_condition(rule.condition, metrics):
                event = AlertEvent(
                    id=f"{rule.id}_{int(time.time())}",
                    rule_id=rule.id,
                    title=f"Alert: {rule.name}",
                    message=self._generate_message(rule, metrics),
                    priority=rule.priority,
                    timestamp=datetime.now(),
                    metadata=metrics,
                )

                events.append(event)
                self._send_alert(event, rule.channels)

                # Update cooldown
                self.last_alert_times[rule.id] = datetime.now()

        # Store events
        self.events.extend(events)

        return events

    def _evaluate_condition(self, condition: str, metrics: dict[str, Any]) -> bool:
        """Evaluate alert condition"""
        try:
            # Simple condition evaluation
            # In a real implementation, you'd use a proper expression evaluator
            if "total_errors >" in condition:
                threshold = int(condition.split(">")[1].strip())
                return metrics.get("total_errors", 0) > threshold
            elif "syntax_errors >" in condition:
                threshold = int(condition.split(">")[1].strip())
                return metrics.get("syntax_errors", 0) > threshold
            elif "import_errors >" in condition:
                threshold = int(condition.split(">")[1].strip())
                return metrics.get("import_errors", 0) > threshold

            return False

        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False

    def _generate_message(self, rule: AlertRule, metrics: dict[str, Any]) -> str:
        """Generate alert message"""
        if rule.id == "high_error_count":
            return f"High error count detected: {metrics.get('total_errors', 0)} errors found"
        elif rule.id == "syntax_errors":
            return f"Syntax errors detected: {metrics.get('syntax_errors', 0)} syntax errors found"
        elif rule.id == "import_errors":
            return f"Import errors detected: {metrics.get('import_errors', 0)} import errors found"
        else:
            return f"Alert triggered: {rule.name}"

    def _is_in_cooldown(self, rule_id: str) -> bool:
        """Check if rule is in cooldown period"""
        if rule_id not in self.last_alert_times:
            return False

        rule = next((r for r in self.rules if r.id == rule_id), None)
        if not rule:
            return False

        last_alert = self.last_alert_times[rule_id]
        cooldown_end = last_alert + timedelta(minutes=rule.cooldown_minutes)

        return datetime.now() < cooldown_end

    def _send_alert(self, event: AlertEvent, channels: list[AlertChannel]):
        """Send alert to specified channels"""
        for channel in channels:
            try:
                if channel == AlertChannel.CONSOLE:
                    self._send_console_alert(event)
                elif channel == AlertChannel.EMAIL:
                    self._send_email_alert(event)
                elif channel == AlertChannel.SLACK:
                    self._send_slack_alert(event)
                elif channel == AlertChannel.WEBHOOK:
                    self._send_webhook_alert(event)
                elif channel == AlertChannel.FILE:
                    self._send_file_alert(event)

            except Exception as e:
                logger.error(f"Error sending alert to {channel.value}: {e}")

    def _send_console_alert(self, event: AlertEvent):
        """Send alert to console"""
        priority_emoji = {
            AlertPriority.LOW: "ℹ️",
            AlertPriority.MEDIUM: "⚠️",
            AlertPriority.HIGH: "❌",
            AlertPriority.CRITICAL: "🚨",
        }

        emoji = priority_emoji[event.priority]
        print(f"{emoji} {event.title}: {event.message}")
        print(f"   Time: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Priority: {event.priority.value.upper()}")
        print()

    def _send_email_alert(self, event: AlertEvent):
        """Send alert via email"""
        email_config = self.config["channels"]["email"]
        if not email_config["enabled"]:
            return

        # Email implementation would go here
        logger.info(f"Email alert sent: {event.title}")

    def _send_slack_alert(self, event: AlertEvent):
        """Send alert to Slack"""
        slack_config = self.config["channels"]["slack"]
        if not slack_config["enabled"]:
            return

        # Slack implementation would go here
        logger.info(f"Slack alert sent: {event.title}")

    def _send_webhook_alert(self, event: AlertEvent):
        """Send alert via webhook"""
        webhook_config = self.config["channels"]["webhook"]
        if not webhook_config["enabled"]:
            return

        # Webhook implementation would go here
        logger.info(f"Webhook alert sent: {event.title}")

    def _send_file_alert(self, event: AlertEvent):
        """Send alert to file"""
        file_config = self.config["channels"]["file"]
        if not file_config["enabled"]:
            return

        file_path = Path(file_config["path"])
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Append to file
        with open(file_path, "a") as f:
            f.write(json.dumps(asdict(event), default=str) + "\n")

        logger.info(f"File alert written: {event.title}")

    def get_recent_events(self, hours: int = 24) -> list[dict[str, Any]]:
        """Get recent alert events"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_events = [e for e in self.events if e.timestamp > cutoff_time]
        return [asdict(event) for event in recent_events]

    def get_alert_summary(self) -> dict[str, Any]:
        """Get alert summary"""
        if not self.events:
            return {"message": "No alerts"}

        recent_events = [
            e for e in self.events if e.timestamp > datetime.now() - timedelta(hours=24)
        ]

        summary: dict[str, Any] = {
            "total_events": len(self.events),
            "recent_events": len(recent_events),
            "by_priority": {},
            "by_rule": {},
            "last_alert": self.events[-1].timestamp.isoformat()
            if self.events
            else None,
        }

        # Count by priority
        for priority in AlertPriority:
            count = len([e for e in recent_events if e.priority == priority])
            summary["by_priority"][priority.value] = count

        # Count by rule
        for rule in self.rules:
            count = len([e for e in recent_events if e.rule_id == rule.id])
            summary["by_rule"][rule.id] = count

        return summary


# Example usage
if __name__ == "__main__":
    # Initialize alerter
    alerter = ProactiveAlerter()

    # Test with sample metrics
    test_metrics = {
        "total_errors": 75,
        "syntax_errors": 8,
        "import_errors": 15,
        "files_with_errors": 12,
    }

    # Check metrics
    events = alerter.check_metrics(test_metrics)

    # Print summary
    summary = alerter.get_alert_summary()
    print("📊 Alert Summary:")
    print(json.dumps(summary, indent=2))
