# StillMe Gateway - Email Notifier
"""
Professional email notification system với HTML templates và error handling
"""

import asyncio
import logging
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import os
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailTemplate(Enum):
    """Email templates"""
    ALERT = "alert"
    HEALTH = "health"
    SYSTEM = "system"
    SECURITY = "security"
    PERFORMANCE = "performance"


@dataclass
class EmailConfig:
    """Email configuration"""
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    from_name: str = "StillMe AI System"
    from_email: str = ""
    reply_to: str = ""
    use_tls: bool = True
    use_ssl: bool = False
    timeout: int = 30
    max_retries: int = 3


@dataclass
class EmailMessage:
    """Email message structure"""
    to: str
    subject: str
    html_body: str
    text_body: str = ""
    template: EmailTemplate = EmailTemplate.ALERT
    attachments: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []
        if self.metadata is None:
            self.metadata = {}


class EmailNotifier:
    """
    Professional email notification system
    """
    
    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or self._load_config()
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.stats = {
            "total_sent": 0,
            "total_failed": 0,
            "total_retries": 0,
            "last_success": None,
            "last_failure": None
        }
        
        # Connection pool
        self._connection_pool = []
        self._max_connections = 5
        
        self.logger.info("✅ Email Notifier initialized")
    
    def _load_config(self) -> EmailConfig:
        """Load configuration from environment variables"""
        return EmailConfig(
            smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(os.getenv("SMTP_PORT", "587")),
            smtp_username=os.getenv("SMTP_USERNAME", ""),
            smtp_password=os.getenv("SMTP_PASSWORD", ""),
            from_name=os.getenv("EMAIL_FROM_NAME", "StillMe AI System"),
            from_email=os.getenv("EMAIL_FROM_EMAIL", ""),
            reply_to=os.getenv("EMAIL_REPLY_TO", ""),
            use_tls=os.getenv("EMAIL_USE_TLS", "true").lower() == "true",
            use_ssl=os.getenv("EMAIL_USE_SSL", "false").lower() == "true",
            timeout=int(os.getenv("EMAIL_TIMEOUT", "30")),
            max_retries=int(os.getenv("EMAIL_MAX_RETRIES", "3"))
        )
    
    async def send_email(self, message: EmailMessage) -> bool:
        """
        Send email message
        
        Args:
            message: Email message to send
            
        Returns:
            True if successful, False otherwise
        """
        if not self._validate_config():
            return False
        
        for attempt in range(self.config.max_retries):
            try:
                success = await self._send_email_attempt(message)
                if success:
                    self.stats["total_sent"] += 1
                    self.stats["last_success"] = datetime.now()
                    self.logger.info(f"✅ Email sent successfully: {message.subject}")
                    return True
                else:
                    self.stats["total_retries"] += 1
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            except Exception as e:
                self.logger.error(f"❌ Email send attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        self.stats["total_failed"] += 1
        self.stats["last_failure"] = datetime.now()
        self.logger.error(f"❌ Email send failed after {self.config.max_retries} attempts: {message.subject}")
        return False
    
    async def _send_email_attempt(self, message: EmailMessage) -> bool:
        """Single email send attempt"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.config.from_name} <{self.config.from_email or self.config.smtp_username}>"
            msg['To'] = message.to
            msg['Subject'] = message.subject
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            if self.config.reply_to:
                msg['Reply-To'] = self.config.reply_to
            
            # Add text body
            if message.text_body:
                text_part = MIMEText(message.text_body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Add HTML body
            html_part = MIMEText(message.html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Add attachments
            for attachment_path in message.attachments:
                if os.path.exists(attachment_path):
                    with open(attachment_path, 'rb') as f:
                        attachment = MIMEImage(f.read())
                        attachment.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
                        msg.attach(attachment)
            
            # Send email
            await self._send_smtp(msg, message.to)
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Email send attempt failed: {e}")
            return False
    
    async def _send_smtp(self, msg: MIMEMultipart, to: str):
        """Send email via SMTP"""
        try:
            # Create SSL context
            context = ssl.create_default_context()
            if not self.config.use_ssl:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            
            # Connect to SMTP server
            if self.config.use_ssl:
                server = smtplib.SMTP_SSL(self.config.smtp_server, self.config.smtp_port, timeout=self.config.timeout)
            else:
                server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port, timeout=self.config.timeout)
            
            # Start TLS if needed
            if self.config.use_tls and not self.config.use_ssl:
                server.starttls(context=context)
            
            # Login
            server.login(self.config.smtp_username, self.config.smtp_password)
            
            # Send email
            server.send_message(msg, to_addrs=[to])
            server.quit()
            
        except Exception as e:
            self.logger.error(f"❌ SMTP send failed: {e}")
            raise
    
    def _validate_config(self) -> bool:
        """Validate email configuration"""
        if not self.config.smtp_username or not self.config.smtp_password:
            self.logger.error("❌ Email credentials not configured")
            return False
        
        if not self.config.from_email:
            self.config.from_email = self.config.smtp_username
        
        return True
    
    def create_alert_email(
        self,
        to: str,
        title: str,
        message: str,
        severity: str = "medium",
        service: str = "StillMe AI",
        timestamp: Optional[datetime] = None
    ) -> EmailMessage:
        """Create alert email message"""
        if timestamp is None:
            timestamp = datetime.now()
        
        severity_colors = {
            "critical": "#dc3545",
            "high": "#fd7e14",
            "medium": "#ffc107",
            "low": "#28a745",
            "info": "#17a2b8"
        }
        
        color = severity_colors.get(severity.lower(), "#6c757d")
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>StillMe Alert</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: {color};
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 600;
                }}
                .content {{
                    padding: 30px;
                }}
                .alert-info {{
                    background: #f8f9fa;
                    border-left: 4px solid {color};
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .severity {{
                    display: inline-block;
                    background: {color};
                    color: white;
                    padding: 4px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 600;
                    text-transform: uppercase;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .timestamp {{
                    color: #6c757d;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 StillMe Alert</h1>
                </div>
                <div class="content">
                    <h2>{title}</h2>
                    <div class="alert-info">
                        <p><strong>Service:</strong> {service}</p>
                        <p><strong>Severity:</strong> <span class="severity">{severity.upper()}</span></p>
                        <p><strong>Time:</strong> <span class="timestamp">{timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</span></p>
                    </div>
                    <div>
                        <h3>Details:</h3>
                        <p>{message}</p>
                    </div>
                </div>
                <div class="footer">
                    <p>StillMe AI System Notification</p>
                    <p>This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        StillMe Alert - {title}
        
        Service: {service}
        Severity: {severity.upper()}
        Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
        
        Details:
        {message}
        
        ---
        StillMe AI System Notification
        """
        
        return EmailMessage(
            to=to,
            subject=f"[{severity.upper()}] {title}",
            html_body=html_body,
            text_body=text_body,
            template=EmailTemplate.ALERT,
            metadata={
                "severity": severity,
                "service": service,
                "timestamp": timestamp.isoformat()
            }
        )
    
    def create_health_email(
        self,
        to: str,
        service: str,
        status: str,
        details: str,
        timestamp: Optional[datetime] = None
    ) -> EmailMessage:
        """Create health check email"""
        if timestamp is None:
            timestamp = datetime.now()
        
        status_colors = {
            "up": "#28a745",
            "down": "#dc3545",
            "degraded": "#ffc107",
            "maintenance": "#17a2b8"
        }
        
        color = status_colors.get(status.lower(), "#6c757d")
        emoji = "✅" if status.lower() == "up" else "❌" if status.lower() == "down" else "⚠️"
        
        title = f"Health Check: {service} is {status}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>StillMe Health Check</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: {color};
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 600;
                }}
                .content {{
                    padding: 30px;
                }}
                .status {{
                    display: inline-block;
                    background: {color};
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 600;
                    text-transform: uppercase;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #6c757d;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{emoji} StillMe Health Check</h1>
                </div>
                <div class="content">
                    <h2>{title}</h2>
                    <p><strong>Service:</strong> {service}</p>
                    <p><strong>Status:</strong> <span class="status">{status.upper()}</span></p>
                    <p><strong>Time:</strong> {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    <div>
                        <h3>Details:</h3>
                        <p>{details}</p>
                    </div>
                </div>
                <div class="footer">
                    <p>StillMe AI System Health Monitoring</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        StillMe Health Check - {title}
        
        Service: {service}
        Status: {status.upper()}
        Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
        
        Details:
        {details}
        
        ---
        StillMe AI System Health Monitoring
        """
        
        return EmailMessage(
            to=to,
            subject=f"[HEALTH] {title}",
            html_body=html_body,
            text_body=text_body,
            template=EmailTemplate.HEALTH,
            metadata={
                "service": service,
                "status": status,
                "timestamp": timestamp.isoformat()
            }
        )
    
    async def test_email(self, to: str) -> bool:
        """Test email functionality"""
        try:
            test_message = self.create_alert_email(
                to=to,
                title="StillMe Email Test",
                message="This is a test email from StillMe AI System. If you receive this message, the email notification system is working correctly.",
                severity="info",
                service="Email Notifier"
            )
            
            success = await self.send_email(test_message)
            if success:
                self.logger.info(f"🧪 Test email sent successfully to {to}")
            else:
                self.logger.error(f"❌ Test email failed to {to}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Test email error: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get email statistics"""
        return {
            "stats": self.stats,
            "config": {
                "smtp_server": self.config.smtp_server,
                "smtp_port": self.config.smtp_port,
                "from_name": self.config.from_name,
                "from_email": self.config.from_email,
                "use_tls": self.config.use_tls,
                "use_ssl": self.config.use_ssl
            }
        }


# Global email notifier instance
email_notifier = EmailNotifier()


async def send_alert_email(
    to: str,
    title: str,
    message: str,
    severity: str = "medium",
    service: str = "StillMe AI"
) -> bool:
    """Convenience function to send alert email"""
    email_message = email_notifier.create_alert_email(
        to=to,
        title=title,
        message=message,
        severity=severity,
        service=service
    )
    return await email_notifier.send_email(email_message)


async def send_health_email(
    to: str,
    service: str,
    status: str,
    details: str
) -> bool:
    """Convenience function to send health email"""
    email_message = email_notifier.create_health_email(
        to=to,
        service=service,
        status=status,
        details=details
    )
    return await email_notifier.send_email(email_message)
