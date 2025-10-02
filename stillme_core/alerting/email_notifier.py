"""
📧 StillMe IPC Email Notifier
=============================

Real email notifications for StillMe IPC learning events.
Sends alerts to founder via Gmail SMTP.

Author: StillMe IPC (Intelligent Personal Companion)
Version: 1.0.0
Date: 2025-09-29
"""

import json
import logging
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Real email notifier for StillMe IPC"""

    def __init__(self):
        self.config_file = Path("artifacts/email_config.json")
        self.load_config()

    def load_config(self):
        """Load email configuration from .env first, then config file"""
        # Load from .env first
        env_config = {
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
            "use_app_password": True,
        }

        # Load from config file if exists
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    file_config = json.load(f)
                # Merge with env config (env takes priority)
                env_config.update(file_config)
            except:
                pass

        self.config = env_config
        self.save_config()

    def save_config(self):
        """Save email configuration"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w") as f:
            json.dump(self.config, f, indent=2)

    def setup_email(
        self, sender_email: str, sender_password: str, recipient_email: str
    ):
        """Setup email configuration"""
        self.config.update(
            {
                "enabled": True,
                "sender_email": sender_email,
                "sender_password": sender_password,
                "recipient_email": recipient_email,
            }
        )
        self.save_config()
        logger.info("📧 Email configuration saved")

    def send_alert(self, title: str, message: str, level: str = "info"):
        """Send real email alert"""
        if not self.config["enabled"]:
            logger.warning("📧 Email notifications disabled")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.config["sender_email"]
            msg["To"] = self.config["recipient_email"]
            msg["Subject"] = f"🧠 StillMe IPC Alert: {title}"

            # Create HTML body
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px 10px 0 0;">
                        <h1 style="margin: 0; font-size: 24px;">🧠 StillMe IPC Alert</h1>
                        <p style="margin: 5px 0 0 0; opacity: 0.9;">Intelligent Personal Companion</p>
                    </div>

                    <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 10px 10px;">
                        <h2 style="color: #2c3e50; margin-top: 0;">{title}</h2>
                        <div style="background: white; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db;">
                            <p style="margin: 0; white-space: pre-line;">{message}</p>
                        </div>

                        <div style="margin-top: 20px; padding: 15px; background: #e8f4fd; border-radius: 8px;">
                            <h3 style="color: #2c3e50; margin-top: 0;">📊 System Status</h3>
                            <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            <p><strong>Level:</strong> {level.upper()}</p>
                            <p><strong>Source:</strong> StillMe IPC Learning System</p>
                        </div>

                        <div style="margin-top: 20px; text-align: center;">
                            <a href="http://localhost:8507" style="background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                                🚀 Open Dashboard
                            </a>
                        </div>

                        <div style="margin-top: 20px; padding: 15px; background: #f1f2f6; border-radius: 8px; font-size: 12px; color: #666;">
                            <p style="margin: 0;">This is an automated message from StillMe IPC Learning System.</p>
                            <p style="margin: 5px 0 0 0;">To configure notifications, check the dashboard settings.</p>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_body, "html"))

            # Send email
            server = smtplib.SMTP(self.config["smtp_server"], self.config["smtp_port"])
            server.starttls()
            server.login(self.config["sender_email"], self.config["sender_password"])

            text = msg.as_string()
            server.sendmail(
                self.config["sender_email"], self.config["recipient_email"], text
            )
            server.quit()

            logger.info(f"📧 Email sent successfully: {title}")
            return True

        except Exception as e:
            logger.error(f"📧 Failed to send email: {e}")
            return False

    def test_email(self):
        """Test email configuration"""
        if not self.config["enabled"]:
            return False

        return self.send_alert(
            "Test Email",
            "This is a test email from StillMe IPC Learning System.\n\nIf you receive this, email notifications are working correctly!",
            "info",
        )
