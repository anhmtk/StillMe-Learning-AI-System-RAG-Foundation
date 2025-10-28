"""
Notification Service for StillMe V2
Handles email and Telegram notifications for learning events
"""

import os
import smtplib
import requests
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications via email and Telegram"""
    
    def __init__(self):
        """Initialize notification service with config from .env"""
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.email_from = os.getenv("EMAIL_FROM", self.smtp_username)
        self.email_to = os.getenv("EMAIL_TO", self.smtp_username)
        
        # Telegram config
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        # Notification settings
        self.notify_learning = os.getenv("NOTIFY_ON_LEARNING_SESSION", "1") == "1"
        self.notify_evolution = os.getenv("NOTIFY_ON_EVOLUTION_STAGE", "1") == "1"
        self.notify_errors = os.getenv("NOTIFY_ON_ERRORS", "1") == "1"
        self.notify_sources = os.getenv("NOTIFY_ON_NEW_SOURCES", "1") == "1"
        
        logger.info("📧 Notification service initialized")
    
    def send_email(self, subject: str, body: str) -> bool:
        """Send email notification"""
        if not self.smtp_username or not self.smtp_password:
            logger.warning("⚠️ Email credentials not configured")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = f"🧠 StillMe V2 - {subject}"
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            text = msg.as_string()
            server.sendmail(self.email_from, self.email_to, text)
            server.quit()
            
            logger.info(f"✅ Email sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Email send failed: {e}")
            return False
    
    def send_telegram(self, message: str) -> bool:
        """Send Telegram notification"""
        if not self.telegram_bot_token or not self.telegram_chat_id:
            logger.warning("⚠️ Telegram credentials not configured")
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            data = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
            
            logger.info("✅ Telegram message sent")
            return True
            
        except Exception as e:
            logger.error(f"❌ Telegram send failed: {e}")
            return False
    
    def notify_learning_session(self, session_data: dict):
        """Notify about learning session completion"""
        if not self.notify_learning:
            return
        
        subject = f"Learning Session Completed - {session_data.get('evolution_stage', 'Unknown')}"
        
        body = f"""
        <h2>🧠 StillMe V2 Learning Session Report</h2>
        <p><strong>Session ID:</strong> {session_data.get('session_id', 'N/A')}</p>
        <p><strong>Evolution Stage:</strong> {session_data.get('evolution_stage', 'Unknown')}</p>
        <p><strong>Proposals Learned:</strong> {session_data.get('proposals_learned', 0)}</p>
        <p><strong>Success Rate:</strong> {float(session_data.get('success_rate', 0)):.2%}</p>
        <p><strong>Duration:</strong> {session_data.get('duration_minutes', 0)} minutes</p>
        <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        telegram_msg = f"""
🧠 <b>StillMe V2 Learning Session</b>
📊 Stage: {session_data.get('evolution_stage', 'Unknown')}
📚 Proposals: {session_data.get('proposals_learned', 0)}
✅ Success: {float(session_data.get('success_rate', 0)):.2%}
⏱️ Duration: {session_data.get('duration_minutes', 0)} min
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        self.send_email(subject, body)
        self.send_telegram(telegram_msg)
    
    def notify_evolution_stage(self, old_stage: str, new_stage: str, metrics: dict):
        """Notify about evolution stage change"""
        if not self.notify_evolution:
            return
        
        subject = f"Evolution Stage: {old_stage} → {new_stage}"
        
        body = f"""
        <h2>🧬 StillMe V2 Evolution Update</h2>
        <p><strong>Previous Stage:</strong> {old_stage}</p>
        <p><strong>New Stage:</strong> {new_stage}</p>
        <p><strong>System Age:</strong> {metrics.get('system_age_days', 0)} days</p>
        <p><strong>Total Sessions:</strong> {metrics.get('total_sessions', 0)}</p>
        <p><strong>Accuracy:</strong> {metrics.get('accuracy', 0):.2%}</p>
        <p><strong>Knowledge Retention:</strong> {metrics.get('knowledge_retention', 0):.2%}</p>
        <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        telegram_msg = f"""
🧬 <b>StillMe V2 Evolution!</b>
📈 {old_stage} → {new_stage}
📊 Age: {metrics.get('system_age_days', 0)} days
🎯 Sessions: {metrics.get('total_sessions', 0)}
📈 Accuracy: {metrics.get('accuracy', 0):.2%}
🧠 Retention: {metrics.get('knowledge_retention', 0):.2%}
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        self.send_email(subject, body)
        self.send_telegram(telegram_msg)
    
    def notify_error(self, error_type: str, error_message: str, context: dict = None):
        """Notify about system errors"""
        if not self.notify_errors:
            return
        
        subject = f"System Error: {error_type}"
        
        body = f"""
        <h2>⚠️ StillMe V2 System Error</h2>
        <p><strong>Error Type:</strong> {error_type}</p>
        <p><strong>Error Message:</strong> {error_message}</p>
        <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        if context:
            body += "<h3>Context:</h3><ul>"
            for key, value in context.items():
                body += f"<li><strong>{key}:</strong> {value}</li>"
            body += "</ul>"
        
        telegram_msg = f"""
⚠️ <b>StillMe V2 Error</b>
🔴 Type: {error_type}
📝 Message: {error_message}
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        self.send_email(subject, body)
        self.send_telegram(telegram_msg)
    
    def notify_new_sources(self, sources_data: dict):
        """Notify about new data sources"""
        if not self.notify_sources:
            return
        
        subject = f"New Data Sources: {sources_data.get('total_sources', 0)} active"
        
        body = f"""
        <h2>📡 StillMe V2 Data Sources Update</h2>
        <p><strong>RSS Sources:</strong> {sources_data.get('rss_sources', 0)}</p>
        <p><strong>API Sources:</strong> {sources_data.get('api_sources', 0)}</p>
        <p><strong>Total Sources:</strong> {sources_data.get('total_sources', 0)}</p>
        <p><strong>Content Fetched:</strong> {sources_data.get('content_fetched', 0)}</p>
        <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        telegram_msg = f"""
📡 <b>StillMe V2 Sources Update</b>
🔗 RSS: {sources_data.get('rss_sources', 0)}
🌐 APIs: {sources_data.get('api_sources', 0)}
📊 Total: {sources_data.get('total_sources', 0)}
📦 Content: {sources_data.get('content_fetched', 0)}
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        self.send_email(subject, body)
        self.send_telegram(telegram_msg)

# Global notification service instance
notification_service = NotificationService()
