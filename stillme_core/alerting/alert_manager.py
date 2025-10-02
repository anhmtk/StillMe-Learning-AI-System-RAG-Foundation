"""
🔔 StillMe Alert Manager
=======================

Advanced alerting system for AGI learning automation.
Provides multi-channel notifications including email, SMS, desktop,
webhook, and Telegram for comprehensive system monitoring.

Tính năng:
- Multi-channel alerting (Email, SMS, Desktop, Webhook, Telegram)
- Intelligent alert filtering và rate limiting
- Rich HTML email templates với charts
- Smart notification scheduling
- Alert escalation và acknowledgment
- Comprehensive alert analytics
- AGI-specific alert templates

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""

import json
import logging
import os
import smtplib
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional

import requests

try:
    import plyer
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    logging.warning("plyer not available. Install with: pip install plyer")

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logging.warning("twilio not available. Install with: pip install twilio")

logger = logging.getLogger(__name__)

@dataclass
class AlertChannel:
    """Alert channel configuration"""
    name: str
    enabled: bool = True
    priority_threshold: str = "medium"  # low, medium, high, critical
    rate_limit: int = 10  # max alerts per hour
    cooldown: int = 300  # seconds between same-type alerts
    config: dict[str, Any] = None

@dataclass
class AlertTemplate:
    """Alert template configuration"""
    alert_type: str
    subject_template: str
    body_template: str
    emoji: str = "🔔"
    priority: str = "medium"
    channels: list[str] = None
    rate_limit: int = 5  # max per hour
    cooldown: int = 600  # seconds

@dataclass
class Alert:
    """Alert data structure"""
    alert_id: str
    timestamp: datetime
    alert_type: str
    severity: str  # low, medium, high, critical
    title: str
    message: str
    component: str
    context: dict[str, Any] = None
    channels: list[str] = None
    acknowledged: bool = False
    resolved: bool = False
    escalation_level: int = 0
    retry_count: int = 0

class EmailNotifier:
    """Email notification handler"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.smtp_server = None
        self.smtp_port = None
        self.username = None
        self.password = None
        self.alert_email = None
        self._load_config()

    def _load_config(self):
        """Load email configuration from environment"""
        self.smtp_server = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.username = os.getenv('SMTP_USERNAME', '')
        self.password = os.getenv('SMTP_PASSWORD', '')
        self.alert_email = os.getenv('ALERT_EMAIL', '')

        if not all([self.username, self.password, self.alert_email]):
            self.logger.warning("Email configuration incomplete. Email alerts disabled.")
            self.config['enabled'] = False

    async def send_alert(self, alert: Alert) -> bool:
        """Send email alert"""
        if not self.config.get('enabled', True):
            return False

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.username
            msg['To'] = self.alert_email
            emoji = alert.context.get('emoji', '🔔') if alert.context else '🔔'
            msg['Subject'] = f"{emoji} StillMe AI - {alert.severity.upper()}: {alert.title}"

            # Create HTML content
            html_content = self._create_html_content(alert)
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # Create text content
            text_content = self._create_text_content(alert)
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            msg.attach(text_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            self.logger.info(f"Email alert sent: {alert.alert_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False

    def _create_html_content(self, alert: Alert) -> str:
        """Create HTML email content"""
        severity_colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }

        color = severity_colors.get(alert.severity, '#6c757d')

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f8f9fa; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ background: {color}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ padding: 20px; }}
                .alert-info {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
                .metric {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
                .footer {{ background: #f8f9fa; padding: 15px; text-align: center; font-size: 12px; color: #6c757d; }}
                .button {{ display: inline-block; padding: 10px 20px; background: {color}; color: white; text-decoration: none; border-radius: 5px; margin: 10px 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧠 StillMe AI Alert</h1>
                    <p>System: {alert.component} | Severity: {alert.severity.upper()}</p>
                </div>

                <div class="content">
                    <h2>{alert.title}</h2>
                    <p>{alert.message}</p>

                    <div class="alert-info">
                        <strong>Alert ID:</strong> {alert.alert_id}<br>
                        <strong>Time:</strong> {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br>
                        <strong>Component:</strong> {alert.component}<br>
                        <strong>Type:</strong> {alert.alert_type}
                    </div>

                    {self._create_metrics_section(alert)}

                    {self._create_context_section(alert)}

                    <div style="text-align: center; margin: 20px 0;">
                        <a href="#" class="button">View Dashboard</a>
                        <a href="#" class="button">Acknowledge Alert</a>
                    </div>
                </div>

                <div class="footer">
                    <p>StillMe AI Framework - Automated Learning System</p>
                    <p>This is an automated alert. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _create_text_content(self, alert: Alert) -> str:
        """Create plain text email content"""
        return f"""
StillMe AI Alert
================

Severity: {alert.severity.upper()}
Component: {alert.component}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Alert ID: {alert.alert_id}

{alert.title}
{'-' * len(alert.title)}

{alert.message}

Context:
{json.dumps(alert.context or {}, indent=2)}

---
StillMe AI Framework - Automated Learning System
This is an automated alert. Please do not reply to this email.
        """

    def _create_metrics_section(self, alert: Alert) -> str:
        """Create metrics section for HTML email"""
        if not alert.context or 'metrics' not in alert.context:
            return ""

        metrics = alert.context['metrics']
        metrics_html = '<div class="metrics">'

        for key, value in metrics.items():
            metrics_html += f'''
            <div class="metric">
                <strong>{key.replace('_', ' ').title()}</strong><br>
                <span style="font-size: 24px; color: #007bff;">{value}</span>
            </div>
            '''

        metrics_html += '</div>'
        return metrics_html

    def _create_context_section(self, alert: Alert) -> str:
        """Create context section for HTML email"""
        if not alert.context:
            return ""

        context_html = '<div class="alert-info"><h3>Additional Context</h3>'

        for key, value in alert.context.items():
            if key != 'metrics':
                context_html += f'<strong>{key.replace("_", " ").title()}:</strong> {value}<br>'

        context_html += '</div>'
        return context_html

class DesktopNotifier:
    """Desktop notification handler"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.enabled = PLYER_AVAILABLE and config.get('enabled', True)

        if not PLYER_AVAILABLE:
            self.logger.warning("plyer not available. Desktop notifications disabled.")
            self.enabled = False

    async def send_alert(self, alert: Alert) -> bool:
        """Send desktop notification"""
        if not self.enabled:
            return False

        try:
            # Create notification title and message
            title = f"🧠 StillMe AI - {alert.severity.upper()}"
            message = f"{alert.title}\n{alert.message}"

            # Send notification
            plyer.notification.notify(
                title=title,
                message=message,
                app_name="StillMe AI",
                timeout=10,
                toast=True
            )

            self.logger.info(f"Desktop notification sent: {alert.alert_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send desktop notification: {e}")
            return False

class TelegramNotifier:
    """Telegram notification handler"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.bot_token = None
        self.chat_id = None
        self._load_config()

    def _load_config(self):
        """Load Telegram configuration from environment"""
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '')

        if not all([self.bot_token, self.chat_id]):
            self.logger.warning("Telegram configuration incomplete. Telegram alerts disabled.")
            self.config['enabled'] = False

    async def send_alert(self, alert: Alert) -> bool:
        """Send Telegram alert"""
        if not self.config.get('enabled', True):
            return False

        try:
            # Create message
            emoji_map = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🟠',
                'critical': '🔴'
            }

            emoji = emoji_map.get(alert.severity, '🔔')

            message = f"""
{emoji} *StillMe AI Alert*

*{alert.title}*

{alert.message}

📊 *Details:*
• Severity: {alert.severity.upper()}
• Component: {alert.component}
• Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
• Alert ID: `{alert.alert_id}`

{self._create_context_text(alert)}
            """.strip()

            # Send message
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }

            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()

            self.logger.info(f"Telegram alert sent: {alert.alert_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send Telegram alert: {e}")
            return False

    def _create_context_text(self, alert: Alert) -> str:
        """Create context text for Telegram message"""
        if not alert.context:
            return ""

        context_text = "\n📋 *Context:*\n"
        for key, value in alert.context.items():
            context_text += f"• {key.replace('_', ' ').title()}: {value}\n"

        return context_text

class SMSNotifier:
    """SMS notification handler"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = None
        self.from_number = None
        self.to_number = None
        self._load_config()

    def _load_config(self):
        """Load SMS configuration from environment"""
        account_sid = os.getenv('TWILIO_ACCOUNT_SID', '')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN', '')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER', '')
        self.to_number = os.getenv('ALERT_PHONE', '')

        if not all([account_sid, auth_token, self.from_number, self.to_number]):
            self.logger.warning("SMS configuration incomplete. SMS alerts disabled.")
            self.config['enabled'] = False
            return

        if TWILIO_AVAILABLE:
            try:
                self.client = TwilioClient(account_sid, auth_token)
            except Exception as e:
                self.logger.error(f"Failed to initialize Twilio client: {e}")
                self.config['enabled'] = False

    async def send_alert(self, alert: Alert) -> bool:
        """Send SMS alert"""
        if not self.config.get('enabled', True) or not self.client:
            return False

        try:
            # Create SMS message (limited to 160 characters)
            message = f"StillMe AI {alert.severity.upper()}: {alert.title[:50]}..."

            # Send SMS
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=self.to_number
            )

            self.logger.info(f"SMS alert sent: {alert.alert_id} (SID: {message_obj.sid})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send SMS alert: {e}")
            return False

class WebhookNotifier:
    """Webhook notification handler"""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.webhook_url = None
        self.headers = None
        self._load_config()

    def _load_config(self):
        """Load webhook configuration from environment"""
        self.webhook_url = os.getenv('WEBHOOK_URL', '')

        if not self.webhook_url:
            self.logger.warning("Webhook URL not configured. Webhook alerts disabled.")
            self.config['enabled'] = False
            return

        # Default headers
        self.headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'StillMe-AI-Alert/2.0'
        }

        # Add custom headers if configured
        custom_headers = os.getenv('WEBHOOK_HEADERS', '')
        if custom_headers:
            try:
                custom_headers_dict = json.loads(custom_headers)
                self.headers.update(custom_headers_dict)
            except json.JSONDecodeError:
                self.logger.warning("Invalid webhook headers format")

    async def send_alert(self, alert: Alert) -> bool:
        """Send webhook alert"""
        if not self.config.get('enabled', True):
            return False

        try:
            # Create webhook payload
            payload = {
                'alert_id': alert.alert_id,
                'timestamp': alert.timestamp.isoformat(),
                'alert_type': alert.alert_type,
                'severity': alert.severity,
                'title': alert.title,
                'message': alert.message,
                'component': alert.component,
                'context': alert.context or {},
                'acknowledged': alert.acknowledged,
                'resolved': alert.resolved,
                'escalation_level': alert.escalation_level
            }

            # Send webhook
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            self.logger.info(f"Webhook alert sent: {alert.alert_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")
            return False

class AlertManager:
    """
    Advanced alert manager for AGI learning automation
    """

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize notifiers
        self.notifiers = {
            'email': EmailNotifier(self.config.get('email', {})),
            'desktop': DesktopNotifier(self.config.get('desktop', {})),
            'telegram': TelegramNotifier(self.config.get('telegram', {})),
            'sms': SMSNotifier(self.config.get('sms', {})),
            'webhook': WebhookNotifier(self.config.get('webhook', {}))
        }

        # Alert templates
        self.templates = self._load_alert_templates()

        # Rate limiting and cooldown tracking
        self.rate_limits = defaultdict(lambda: deque())
        self.cooldowns = {}

        # Alert history
        self.alert_history = deque(maxlen=1000)

        # Statistics
        self.stats = {
            'total_alerts': 0,
            'alerts_by_severity': defaultdict(int),
            'alerts_by_channel': defaultdict(int),
            'successful_deliveries': defaultdict(int),
            'failed_deliveries': defaultdict(int),
            'last_alert_time': None
        }

    def _load_alert_templates(self) -> dict[str, AlertTemplate]:
        """Load alert templates"""
        return {
            'resource_high': AlertTemplate(
                alert_type='resource_high',
                subject_template='High {resource_type} Usage',
                body_template='{resource_type} usage is {usage_percent}% (limit: {limit}%)',
                emoji='💾',
                priority='high',
                channels=['email', 'desktop', 'telegram'],
                rate_limit=3,
                cooldown=1800  # 30 minutes
            ),
            'learning_failure': AlertTemplate(
                alert_type='learning_failure',
                subject_template='Learning Session Failed',
                body_template='Learning session {session_id} failed: {error_message}',
                emoji='🧠',
                priority='high',
                channels=['email', 'desktop', 'telegram', 'sms'],
                rate_limit=2,
                cooldown=3600  # 1 hour
            ),
            'system_critical': AlertTemplate(
                alert_type='system_critical',
                subject_template='Critical System Error',
                body_template='Critical error in {component}: {error_message}',
                emoji='🚨',
                priority='critical',
                channels=['email', 'desktop', 'telegram', 'sms'],
                rate_limit=1,
                cooldown=7200  # 2 hours
            ),
            'evolution_milestone': AlertTemplate(
                alert_type='evolution_milestone',
                subject_template='AGI Evolution Milestone',
                body_template='StillMe reached {milestone_name}: {description}',
                emoji='🌟',
                priority='medium',
                channels=['email', 'telegram'],
                rate_limit=5,
                cooldown=1800  # 30 minutes
            ),
            'performance_degradation': AlertTemplate(
                alert_type='performance_degradation',
                subject_template='Performance Degradation',
                body_template='Performance degraded by {degradation_percent}% in {component}',
                emoji='📉',
                priority='medium',
                channels=['email', 'desktop', 'telegram'],
                rate_limit=3,
                cooldown=1800  # 30 minutes
            )
        }

    async def send_alert(self, alert_type: str, severity: str, title: str, message: str,
                        component: str, context: dict[str, Any] = None,
                        channels: list[str] = None) -> str:
        """Send alert through configured channels"""

        # Generate alert ID
        alert_id = f"alert_{int(time.time() * 1000)}_{hash(alert_type) % 10000}"

        # Create alert object
        alert = Alert(
            alert_id=alert_id,
            timestamp=datetime.now(),
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            component=component,
            context=context or {},
            channels=channels or []
        )

        # Check rate limiting
        if not self._check_rate_limit(alert):
            self.logger.warning(f"Alert rate limited: {alert_id}")
            return alert_id

        # Check cooldown
        if not self._check_cooldown(alert):
            self.logger.warning(f"Alert in cooldown: {alert_id}")
            return alert_id

        # Get template
        template = self.templates.get(alert_type)
        if template:
            # Add emoji to alert context if template exists
            if not alert.context:
                alert.context = {}
            alert.context['emoji'] = template.emoji
            if not alert.channels:
                alert.channels = template.channels or ['email', 'desktop']

        # Send to channels
        successful_channels = []
        failed_channels = []

        for channel_name in alert.channels:
            if channel_name in self.notifiers:
                notifier = self.notifiers[channel_name]
                try:
                    success = await notifier.send_alert(alert)
                    if success:
                        successful_channels.append(channel_name)
                        self.stats['successful_deliveries'][channel_name] += 1
                    else:
                        failed_channels.append(channel_name)
                        self.stats['failed_deliveries'][channel_name] += 1
                except Exception as e:
                    self.logger.error(f"Error sending alert to {channel_name}: {e}")
                    failed_channels.append(channel_name)
                    self.stats['failed_deliveries'][channel_name] += 1

        # Update statistics
        self._update_statistics(alert, successful_channels, failed_channels)

        # Add to history
        self.alert_history.append(alert)

        self.logger.info(f"Alert sent: {alert_id} to {successful_channels}")
        return alert_id

    def _check_rate_limit(self, alert: Alert) -> bool:
        """Check if alert is within rate limit"""
        now = time.time()
        hour_ago = now - 3600

        # Clean old entries
        while self.rate_limits[alert.alert_type] and self.rate_limits[alert.alert_type][0] < hour_ago:
            self.rate_limits[alert.alert_type].popleft()

        # Check rate limit
        template = self.templates.get(alert.alert_type)
        if template and len(self.rate_limits[alert.alert_type]) >= template.rate_limit:
            return False

        # Add current alert
        self.rate_limits[alert.alert_type].append(now)
        return True

    def _check_cooldown(self, alert: Alert) -> bool:
        """Check if alert is in cooldown period"""
        now = time.time()
        cooldown_key = f"{alert.alert_type}_{alert.component}"

        if cooldown_key in self.cooldowns:
            template = self.templates.get(alert.alert_type)
            cooldown_duration = template.cooldown if template else 600  # 10 minutes default

            if now - self.cooldowns[cooldown_key] < cooldown_duration:
                return False

        # Update cooldown
        self.cooldowns[cooldown_key] = now
        return True

    def _update_statistics(self, alert: Alert, successful_channels: list[str], failed_channels: list[str]):
        """Update alert statistics"""
        self.stats['total_alerts'] += 1
        self.stats['alerts_by_severity'][alert.severity] += 1
        self.stats['last_alert_time'] = alert.timestamp

        for channel in successful_channels:
            self.stats['alerts_by_channel'][channel] += 1

    def get_alert_statistics(self) -> dict[str, Any]:
        """Get alert statistics"""
        return {
            'statistics': dict(self.stats),
            'recent_alerts': [asdict(alert) for alert in list(self.alert_history)[-10:]],
            'notifier_status': {
                name: {
                    'enabled': notifier.config.get('enabled', True),
                    'successful': self.stats['successful_deliveries'][name],
                    'failed': self.stats['failed_deliveries'][name]
                }
                for name, notifier in self.notifiers.items()
            },
            'rate_limits': {
                alert_type: len(rate_queue)
                for alert_type, rate_queue in self.rate_limits.items()
            },
            'cooldowns': {
                key: datetime.fromtimestamp(timestamp).isoformat()
                for key, timestamp in self.cooldowns.items()
            }
        }

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alert_history:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                self.logger.info(f"Alert acknowledged: {alert_id}")
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        for alert in self.alert_history:
            if alert.alert_id == alert_id:
                alert.resolved = True
                self.logger.info(f"Alert resolved: {alert_id}")
                return True
        return False

# Global alert manager instance
_alert_manager_instance: Optional[AlertManager] = None

def get_alert_manager(config: dict[str, Any] = None) -> AlertManager:
    """Get global alert manager instance"""
    global _alert_manager_instance
    if _alert_manager_instance is None:
        _alert_manager_instance = AlertManager(config)
    return _alert_manager_instance

async def send_alert(alert_type: str, severity: str, title: str, message: str,
                    component: str, context: dict[str, Any] = None,
                    channels: list[str] = None) -> str:
    """Convenience function to send alert"""
    manager = get_alert_manager()
    return await manager.send_alert(alert_type, severity, title, message, component, context, channels)
