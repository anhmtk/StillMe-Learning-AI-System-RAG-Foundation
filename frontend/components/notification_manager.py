"""
Notification Manager Component
Handles notifications across multiple channels
"""

import streamlit as st
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationManager:
    """Manages notifications across multiple channels"""
    
    def __init__(self):
        self.notification_history = []
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load notification configuration"""
        
        return {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "admin_emails": ["admin@example.com"]
            },
            "telegram": {
                "enabled": False,
                "bot_token": "",
                "chat_id": ""
            },
            "dashboard": {
                "enabled": True,
                "show_toasts": True
            },
            "triggers": {
                "learning_session_started": True,
                "learning_session_completed": True,
                "evolution_stage_changed": True,
                "system_errors": True,
                "proposals_need_review": True,
                "community_votes_threshold": True
            }
        }
    
    def send_notification(self, title: str, message: str, notification_type: str = "info") -> bool:
        """
        Send notification across configured channels
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification (info, warning, error, success)
            
        Returns:
            bool: True if notification was sent successfully
        """
        
        notification = {
            "title": title,
            "message": message,
            "type": notification_type,
            "timestamp": datetime.now().isoformat(),
            "channels": []
        }
        
        try:
            # Dashboard notifications (always available)
            if self.config["dashboard"]["enabled"]:
                self._send_dashboard_notification(title, message, notification_type)
                notification["channels"].append("dashboard")
            
            # Email notifications
            if self.config["email"]["enabled"]:
                if self._send_email_notification(title, message, notification_type):
                    notification["channels"].append("email")
            
            # Telegram notifications
            if self.config["telegram"]["enabled"]:
                if self._send_telegram_notification(title, message, notification_type):
                    notification["channels"].append("telegram")
            
            # Add to history
            self.notification_history.append(notification)
            
            logger.info(f"Notification sent: {title} via {notification['channels']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False
    
    def _send_dashboard_notification(self, title: str, message: str, notification_type: str):
        """Send notification to Streamlit dashboard"""
        
        # Store in session state for display
        if 'recent_notifications' not in st.session_state:
            st.session_state.recent_notifications = []
        
        notification = {
            "title": title,
            "message": message,
            "type": notification_type,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
        
        st.session_state.recent_notifications.insert(0, notification)
        
        # Keep only last 10 notifications
        if len(st.session_state.recent_notifications) > 10:
            st.session_state.recent_notifications = st.session_state.recent_notifications[:10]
        
        # Show toast notification if enabled
        if self.config["dashboard"]["show_toasts"]:
            # Streamlit doesn't have native toasts, so we'll use success/warning/error messages
            pass
    
    def _send_email_notification(self, title: str, message: str, notification_type: str) -> bool:
        """Send email notification"""
        
        try:
            config = self.config["email"]
            
            if not config["sender_email"] or not config["sender_password"]:
                logger.warning("Email configuration incomplete")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = config["sender_email"]
            msg['To'] = ", ".join(config["admin_emails"])
            msg['Subject'] = f"Evolution AI: {title}"
            
            # Create email body
            body = f"""
            Evolution AI System Notification
            
            Title: {title}
            Message: {message}
            Type: {notification_type}
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            
            ---
            This is an automated notification from the Evolution AI System.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(config["smtp_server"], config["smtp_port"])
            server.starttls()
            server.login(config["sender_email"], config["sender_password"])
            text = msg.as_string()
            server.sendmail(config["sender_email"], config["admin_emails"], text)
            server.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Email notification failed: {str(e)}")
            return False
    
    def _send_telegram_notification(self, title: str, message: str, notification_type: str) -> bool:
        """Send Telegram notification"""
        
        try:
            config = self.config["telegram"]
            
            if not config["bot_token"] or not config["chat_id"]:
                logger.warning("Telegram configuration incomplete")
                return False
            
            # Emoji based on notification type
            emoji = {
                "info": "ℹ️",
                "warning": "⚠️", 
                "error": "❌",
                "success": "✅"
            }.get(notification_type, "📢")
            
            telegram_message = f"{emoji} *{title}*\n\n{message}\n\n_Time: {datetime.now().strftime('%H:%M:%S')}_"
            
            # Send via Telegram Bot API
            import requests
            url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
            payload = {
                "chat_id": config["chat_id"],
                "text": telegram_message,
                "parse_mode": "Markdown"
            }
            
            response = requests.post(url, json=payload)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Telegram notification failed: {str(e)}")
            return False
    
    def get_notification_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get notification history"""
        
        return self.notification_history[:limit]
    
    def get_recent_notifications(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent notifications from specified hours"""
        
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        recent = []
        for notification in self.notification_history:
            notification_time = datetime.fromisoformat(notification["timestamp"]).timestamp()
            if notification_time >= cutoff_time:
                recent.append(notification)
        
        return recent
    
    def clear_notification_history(self):
        """Clear notification history"""
        
        self.notification_history.clear()
        if 'recent_notifications' in st.session_state:
            st.session_state.recent_notifications = []
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update notification configuration"""
        
        self.config.update(new_config)
        logger.info("Notification configuration updated")