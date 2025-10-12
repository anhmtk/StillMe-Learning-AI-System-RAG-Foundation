"""
Notification System for AgentDev Operations
==========================================

Handles email and Telegram notifications for incidents and reports.
"""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

import requests

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Email notification handler"""

    def __init__(self):
        self.config: dict[str, Any] = {
            "enabled": bool(
                os.getenv("SMTP_USERNAME")
                and os.getenv("SMTP_PASSWORD")
                and os.getenv("ALERT_EMAIL")
            ),
            "smtp_server": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "sender_email": os.getenv("SMTP_USERNAME", ""),
            "sender_password": os.getenv("SMTP_PASSWORD", ""),
            "recipient_email": os.getenv("ALERT_EMAIL", ""),
        }

    def send_incident_report(
        self, severity: str, title: str, details: str, remediation: str
    ) -> bool:
        """Send incident report via email"""
        if not self.config["enabled"]:
            logger.warning("Email notifier not configured")
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.config["sender_email"]
            msg["To"] = self.config["recipient_email"]
            msg["Subject"] = f"[{severity}] {title}"

            body = f"""
BÁO CÁO SỰ CỐ KỸ THUẬT - AGENTDEV OPS

Mức độ: {severity}
Tiêu đề: {title}

CHI TIẾT SỰ CỐ:
{details}

PHƯƠNG ÁN XỬ LÝ:
{remediation}

---
Báo cáo tự động từ AgentDev Operations
Thời gian: {self._get_timestamp()}
"""

            msg.attach(MIMEText(body, "plain", "utf-8"))

            with smtplib.SMTP(
                self.config["smtp_server"], self.config["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    self.config["sender_email"], self.config["sender_password"]
                )
                server.send_message(msg)

            logger.info(f"Email incident report sent: {severity} - {title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class TelegramNotifier:
    """Telegram notification handler"""

    def __init__(self):
        self.config: dict[str, Any] = {
            "enabled": bool(
                os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")
            ),
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        }

    def send_incident_report(
        self, severity: str, title: str, details: str, remediation: str
    ) -> bool:
        """Send incident report via Telegram"""
        if not self.config["enabled"]:
            logger.warning("Telegram notifier not configured")
            return False

        try:
            message = f"""
🚨 **{severity}** - {title}

**Chi tiết sự cố:**
{details}

**Phương án xử lý:**
{remediation}

---
🤖 AgentDev Operations
⏰ {self._get_timestamp()}
"""

            url = f"https://api.telegram.org/bot{self.config['bot_token']}/sendMessage"
            data = {
                "chat_id": self.config["chat_id"],
                "text": message,
                "parse_mode": "Markdown",
            }

            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()

            logger.info(f"Telegram incident report sent: {severity} - {title}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
