"""
🔔 StillMe IPC Alerting System
==============================

Simple alerting system for StillMe IPC learning automation.
Provides basic notifications for learning events.

Author: StillMe IPC (Intelligent Personal Companion)
Version: 1.0.0
Date: 2025-09-29
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Import real notifiers
try:
    from .email_notifier import EmailNotifier
    from .telegram_notifier import TelegramNotifier
    REAL_NOTIFIERS_AVAILABLE = True
except ImportError:
    REAL_NOTIFIERS_AVAILABLE = False

class AlertingSystem:
    """Simple alerting system for StillMe IPC"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.artifacts_dir = Path("artifacts/alerts")
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        # Initialize real notifiers
        if REAL_NOTIFIERS_AVAILABLE:
            self.email_notifier = EmailNotifier()
            self.telegram_notifier = TelegramNotifier()
        else:
            self.email_notifier = None
            self.telegram_notifier = None

    def send_alert(self, title: str, message: str, level: str = "info"):
        """Send an alert notification"""
        try:
            alert_data = {
                "title": title,
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat(),
                "source": "stillme_ipc"
            }

            # Log the alert
            self.logger.info(f"🔔 ALERT [{level.upper()}]: {title} - {message}")

            # Save to file
            alert_file = self.artifacts_dir / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(alert_file, 'w', encoding='utf-8') as f:
                json.dump(alert_data, f, indent=2, ensure_ascii=False)

            # Try desktop notification
            try:
                self._send_desktop_notification(title, message, level)
            except Exception as e:
                self.logger.warning(f"Desktop notification failed: {e}")

            # Try real email notification
            if self.email_notifier:
                try:
                    self.email_notifier.send_alert(title, message, level)
                except Exception as e:
                    self.logger.warning(f"Real email notification failed: {e}")
            else:
                self._send_email_notification(title, message, level)

            # Try real Telegram notification
            if self.telegram_notifier:
                try:
                    self.telegram_notifier.send_alert(title, message, level)
                except Exception as e:
                    self.logger.warning(f"Real Telegram notification failed: {e}")

            return True

        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")
            return False

    def _send_desktop_notification(self, title: str, message: str, level: str):
        """Send desktop notification"""
        try:
            import plyer
            plyer.notification.notify(
                title=f"StillMe IPC - {title}",
                message=message,
                timeout=10
            )
        except ImportError:
            pass  # plyer not available
        except Exception as e:
            self.logger.warning(f"Desktop notification error: {e}")

    def _send_email_notification(self, title: str, message: str, level: str):
        """Send email notification (placeholder)"""
        # This would be implemented with actual email sending
        # For now, just log that email would be sent
        self.logger.info(f"📧 Email would be sent: {title}")

    def get_recent_alerts(self, limit: int = 10) -> list:
        """Get recent alerts"""
        try:
            alert_files = list(self.artifacts_dir.glob("alert_*.json"))
            alert_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            alerts = []
            for file_path in alert_files[:limit]:
                try:
                    with open(file_path, encoding='utf-8') as f:
                        alert_data = json.load(f)
                    alerts.append(alert_data)
                except Exception as e:
                    self.logger.warning(f"Error reading alert file {file_path}: {e}")

            return alerts
        except Exception as e:
            self.logger.error(f"Error getting recent alerts: {e}")
            return []

    def clear_old_alerts(self, days: int = 7):
        """Clear alerts older than specified days"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)

            alert_files = list(self.artifacts_dir.glob("alert_*.json"))
            cleared_count = 0

            for file_path in alert_files:
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        cleared_count += 1
                except Exception as e:
                    self.logger.warning(f"Error clearing alert file {file_path}: {e}")

            self.logger.info(f"Cleared {cleared_count} old alerts")
            return cleared_count

        except Exception as e:
            self.logger.error(f"Error clearing old alerts: {e}")
            return 0
