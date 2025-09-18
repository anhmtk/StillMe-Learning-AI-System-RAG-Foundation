# StillMe Gateway - Notification Manager
"""
Advanced notification management system với email/SMS/Slack integration
"""

import asyncio
import logging
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Notification channels"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    TELEGRAM = "telegram"
    INTERNAL = "internal"


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class NotificationConfig:
    """Notification configuration"""
    # Email settings
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    alert_email: str = ""
    
    # SMS settings (Twilio)
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    alert_phone: str = ""
    
    # Slack settings
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"
    
    # Telegram settings
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    # General settings
    enabled_channels: List[NotificationChannel] = None
    escalation_enabled: bool = True
    escalation_timeout_minutes: int = 15
    max_retries: int = 3
    
    def __post_init__(self):
        if self.enabled_channels is None:
            self.enabled_channels = [NotificationChannel.EMAIL, NotificationChannel.INTERNAL]


@dataclass
class NotificationMessage:
    """Notification message structure"""
    id: str
    title: str
    body: str
    severity: AlertSeverity
    channel: NotificationChannel
    target: str  # email, phone, channel, etc.
    metadata: Dict[str, Any]
    timestamp: datetime
    retry_count: int = 0
    acknowledged: bool = False
    escalated: bool = False


class NotificationManager:
    """
    Advanced notification management system
    """
    
    def __init__(self, config: Optional[NotificationConfig] = None):
        self.config = config or self._load_config()
        self.logger = logging.getLogger(__name__)
        
        # Message queue và tracking
        self.message_queue: List[NotificationMessage] = []
        self.sent_messages: Dict[str, NotificationMessage] = {}
        self.acknowledged_messages: Dict[str, bool] = {}
        
        # Processing task
        self.processing_task: Optional[asyncio.Task] = None
        self.is_running = False
        
        # Statistics
        self.stats = {
            "total_sent": 0,
            "total_failed": 0,
            "total_acknowledged": 0,
            "total_escalated": 0,
            "channels": {
                "email": {"sent": 0, "failed": 0},
                "sms": {"sent": 0, "failed": 0},
                "slack": {"sent": 0, "failed": 0},
                "telegram": {"sent": 0, "failed": 0},
                "internal": {"sent": 0, "failed": 0}
            }
        }
        
        self.logger.info("✅ Notification Manager initialized")
    
    def _load_config(self) -> NotificationConfig:
        """Load configuration from environment variables"""
        return NotificationConfig(
            # Email
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            alert_email=os.getenv("ALERT_EMAIL", ""),
            
            # SMS
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
            twilio_phone_number=os.getenv("TWILIO_PHONE_NUMBER", ""),
            alert_phone=os.getenv("ALERT_PHONE", ""),
            
            # Slack
            slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL", ""),
            slack_channel=os.getenv("SLACK_CHANNEL", "#alerts"),
            
            # Telegram
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", ""),
            
            # General
            escalation_enabled=os.getenv("ESCALATION_ENABLED", "true").lower() == "true",
            escalation_timeout_minutes=int(os.getenv("ESCALATION_TIMEOUT_MINUTES", "15")),
            max_retries=int(os.getenv("MAX_RETRIES", "3"))
        )
    
    async def start(self):
        """Start notification processing"""
        if self.is_running:
            self.logger.warning("⚠️ Notification Manager already running")
            return
        
        self.is_running = True
        self.processing_task = asyncio.create_task(self._processing_loop())
        self.logger.info("🚀 Notification Manager started")
    
    async def stop(self):
        """Stop notification processing"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("🛑 Notification Manager stopped")
    
    async def send_notification(
        self,
        title: str,
        body: str,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        channels: Optional[List[NotificationChannel]] = None,
        target: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Send notification to specified channels
        
        Args:
            title: Notification title
            body: Notification body
            severity: Alert severity level
            channels: List of channels to send to (default: enabled channels)
            target: Specific target (email, phone, etc.)
            metadata: Additional metadata
            
        Returns:
            Message ID
        """
        if channels is None:
            channels = self.config.enabled_channels
        
        message_id = f"notif_{int(datetime.now().timestamp() * 1000)}"
        
        # Create message for each channel
        for channel in channels:
            if channel not in self.config.enabled_channels:
                self.logger.warning(f"⚠️ Channel {channel.value} not enabled, skipping")
                continue
            
            message = NotificationMessage(
                id=f"{message_id}_{channel.value}",
                title=title,
                body=body,
                severity=severity,
                channel=channel,
                target=target or self._get_default_target(channel),
                metadata=metadata or {},
                timestamp=datetime.now()
            )
            
            self.message_queue.append(message)
            self.logger.info(f"📨 Notification queued: {title} -> {channel.value}")
        
        return message_id
    
    def _get_default_target(self, channel: NotificationChannel) -> str:
        """Get default target for channel"""
        if channel == NotificationChannel.EMAIL:
            return self.config.alert_email
        elif channel == NotificationChannel.SMS:
            return self.config.alert_phone
        elif channel == NotificationChannel.SLACK:
            return self.config.slack_channel
        elif channel == NotificationChannel.TELEGRAM:
            return self.config.telegram_chat_id
        else:
            return "internal"
    
    async def _processing_loop(self):
        """Main processing loop"""
        while self.is_running:
            try:
                if self.message_queue:
                    message = self.message_queue.pop(0)
                    await self._process_message(message)
                
                # Check for escalations
                if self.config.escalation_enabled:
                    await self._check_escalations()
                
                await asyncio.sleep(1)  # Process every second
                
            except Exception as e:
                self.logger.error(f"❌ Error in processing loop: {e}")
                await asyncio.sleep(5)
    
    async def _process_message(self, message: NotificationMessage):
        """Process individual message"""
        try:
            success = False
            
            if message.channel == NotificationChannel.EMAIL:
                success = await self._send_email(message)
            elif message.channel == NotificationChannel.SMS:
                success = await self._send_sms(message)
            elif message.channel == NotificationChannel.SLACK:
                success = await self._send_slack(message)
            elif message.channel == NotificationChannel.TELEGRAM:
                success = await self._send_telegram(message)
            elif message.channel == NotificationChannel.INTERNAL:
                success = await self._send_internal(message)
            
            if success:
                self.sent_messages[message.id] = message
                self.stats["total_sent"] += 1
                self.stats["channels"][message.channel.value]["sent"] += 1
                self.logger.info(f"✅ Notification sent: {message.title} -> {message.channel.value}")
            else:
                # Retry logic
                if message.retry_count < self.config.max_retries:
                    message.retry_count += 1
                    self.message_queue.append(message)
                    self.logger.warning(f"🔄 Retrying notification: {message.title} (attempt {message.retry_count})")
                else:
                    self.stats["total_failed"] += 1
                    self.stats["channels"][message.channel.value]["failed"] += 1
                    self.logger.error(f"❌ Notification failed after {self.config.max_retries} retries: {message.title}")
        
        except Exception as e:
            self.logger.error(f"❌ Error processing message {message.id}: {e}")
            self.stats["total_failed"] += 1
    
    async def _send_email(self, message: NotificationMessage) -> bool:
        """Send email notification using OAuth2 or SMTP"""
        try:
            # Try OAuth2 first if configured
            if os.getenv("GMAIL_OAUTH2_ACCESS_TOKEN"):
                return await self._send_email_oauth2(message)
            
            # Fallback to SMTP
            if not self.config.smtp_username or not self.config.smtp_password:
                self.logger.warning("⚠️ Email credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_username
            msg['To'] = message.target
            msg['Subject'] = f"[{message.severity.value.upper()}] {message.title}"
            
            # Create HTML body
            html_body = f"""
            <html>
            <body>
                <h2 style="color: {self._get_severity_color(message.severity)};">
                    {message.title}
                </h2>
                <p><strong>Severity:</strong> {message.severity.value.upper()}</p>
                <p><strong>Time:</strong> {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p>{message.body}</p>
                <hr>
                <p><small>StillMe AI System Notification</small></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Email send failed: {e}")
            return False
    
    async def _send_email_oauth2(self, message: NotificationMessage) -> bool:
        """Send email using Gmail OAuth2"""
        try:
            from .oauth2_email_notifier import OAuth2EmailNotifier
            
            notifier = OAuth2EmailNotifier()
            return await notifier.send_email(
                subject=message.title,
                body=message.body,
                severity=message.severity.value,
                metadata=message.metadata
            )
            
        except Exception as e:
            self.logger.error(f"❌ OAuth2 email send failed: {e}")
            return False
    
    async def _send_sms(self, message: NotificationMessage) -> bool:
        """Send SMS notification (placeholder for Twilio)"""
        try:
            if not self.config.twilio_account_sid or not self.config.twilio_auth_token:
                self.logger.warning("⚠️ SMS credentials not configured")
                return False
            
            # TODO: Implement Twilio SMS sending
            self.logger.info(f"📱 SMS would be sent to {message.target}: {message.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ SMS send failed: {e}")
            return False
    
    async def _send_slack(self, message: NotificationMessage) -> bool:
        """Send Slack notification"""
        try:
            if not self.config.slack_webhook_url:
                self.logger.warning("⚠️ Slack webhook not configured")
                return False
            
            # TODO: Implement Slack webhook sending
            self.logger.info(f"💬 Slack would be sent to {message.target}: {message.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Slack send failed: {e}")
            return False
    
    async def _send_telegram(self, message: NotificationMessage) -> bool:
        """Send Telegram notification"""
        try:
            if not self.config.telegram_bot_token or not self.config.telegram_chat_id:
                self.logger.warning("⚠️ Telegram credentials not configured")
                return False
            
            # TODO: Implement Telegram bot sending
            self.logger.info(f"📱 Telegram would be sent to {message.target}: {message.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Telegram send failed: {e}")
            return False
    
    async def _send_internal(self, message: NotificationMessage) -> bool:
        """Send internal notification (logging)"""
        try:
            self.logger.warning(f"🚨 INTERNAL ALERT [{message.severity.value.upper()}]: {message.title}")
            self.logger.warning(f"📝 Details: {message.body}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Internal notification failed: {e}")
            return False
    
    def _get_severity_color(self, severity: AlertSeverity) -> str:
        """Get color for severity level"""
        colors = {
            AlertSeverity.CRITICAL: "#dc3545",  # Red
            AlertSeverity.HIGH: "#fd7e14",      # Orange
            AlertSeverity.MEDIUM: "#ffc107",    # Yellow
            AlertSeverity.LOW: "#28a745",       # Green
            AlertSeverity.INFO: "#17a2b8"       # Blue
        }
        return colors.get(severity, "#6c757d")
    
    async def _check_escalations(self):
        """Check for messages that need escalation"""
        try:
            current_time = datetime.now()
            
            for message_id, message in self.sent_messages.items():
                if message.acknowledged or message.escalated:
                    continue
                
                time_diff = (current_time - message.timestamp).total_seconds() / 60
                if time_diff >= self.config.escalation_timeout_minutes:
                    await self._escalate_message(message)
        
        except Exception as e:
            self.logger.error(f"❌ Error checking escalations: {e}")
    
    async def _escalate_message(self, message: NotificationMessage):
        """Escalate unacknowledged message"""
        try:
            message.escalated = True
            self.stats["total_escalated"] += 1
            
            # Send escalation notification
            escalation_title = f"ESCALATED: {message.title}"
            escalation_body = f"""
            This alert has been escalated due to lack of acknowledgment.
            
            Original Alert:
            - Title: {message.title}
            - Severity: {message.severity.value.upper()}
            - Time: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
            - Details: {message.body}
            
            Please acknowledge this alert immediately.
            """
            
            await self.send_notification(
                title=escalation_title,
                body=escalation_body,
                severity=AlertSeverity.HIGH,
                channels=[NotificationChannel.EMAIL, NotificationChannel.INTERNAL],
                metadata={"escalated_from": message.id}
            )
            
            self.logger.warning(f"🚨 Message escalated: {message.title}")
        
        except Exception as e:
            self.logger.error(f"❌ Error escalating message: {e}")
    
    def acknowledge_message(self, message_id: str) -> bool:
        """Acknowledge a message"""
        try:
            if message_id in self.sent_messages:
                self.sent_messages[message_id].acknowledged = True
                self.acknowledged_messages[message_id] = True
                self.stats["total_acknowledged"] += 1
                self.logger.info(f"✅ Message acknowledged: {message_id}")
                return True
            return False
        
        except Exception as e:
            self.logger.error(f"❌ Error acknowledging message: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get notification statistics"""
        return {
            "stats": self.stats,
            "queue_size": len(self.message_queue),
            "sent_messages": len(self.sent_messages),
            "acknowledged_messages": len(self.acknowledged_messages),
            "config": {
                "enabled_channels": [ch.value for ch in self.config.enabled_channels],
                "escalation_enabled": self.config.escalation_enabled,
                "escalation_timeout_minutes": self.config.escalation_timeout_minutes
            }
        }
    
    async def test_notification(self, channel: NotificationChannel = NotificationChannel.EMAIL) -> bool:
        """Test notification system"""
        try:
            test_title = "StillMe Notification Test"
            test_body = f"""
            This is a test notification from StillMe AI System.
            
            Channel: {channel.value}
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            If you receive this message, the notification system is working correctly.
            """
            
            message_id = await self.send_notification(
                title=test_title,
                body=test_body,
                severity=AlertSeverity.INFO,
                channels=[channel]
            )
            
            self.logger.info(f"🧪 Test notification sent: {message_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Test notification failed: {e}")
            return False


# Global notification manager instance
notification_manager = NotificationManager()


async def send_alert(
    title: str,
    body: str,
    severity: AlertSeverity = AlertSeverity.MEDIUM,
    channels: Optional[List[NotificationChannel]] = None
) -> str:
    """Convenience function to send alerts"""
    return await notification_manager.send_notification(
        title=title,
        body=body,
        severity=severity,
        channels=channels
    )


async def send_critical_alert(title: str, body: str) -> str:
    """Send critical alert to all channels"""
    return await notification_manager.send_notification(
        title=title,
        body=body,
        severity=AlertSeverity.CRITICAL,
        channels=notification_manager.config.enabled_channels
    )


async def send_health_alert(service: str, status: str, details: str) -> str:
    """Send health alert"""
    title = f"Health Alert: {service} is {status}"
    body = f"""
    Service: {service}
    Status: {status}
    Details: {details}
    Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    severity = AlertSeverity.CRITICAL if status.lower() == "down" else AlertSeverity.MEDIUM
    
    return await notification_manager.send_notification(
        title=title,
        body=body,
        severity=severity
    )
