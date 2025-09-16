#!/usr/bin/env python3
"""
📧 SIMPLE EMAIL NOTIFICATION SYSTEM
📧 HỆ THỐNG THÔNG BÁO EMAIL ĐƠN GIẢN

PURPOSE / MỤC ĐÍCH:
- Simple email notifications for StillMe VPS
- Thông báo email đơn giản cho StillMe VPS
- SMTP integration with Gmail/other providers
- Tích hợp SMTP với Gmail/các nhà cung cấp khác
- Health check alerts
- Cảnh báo kiểm tra sức khỏe

FUNCTIONALITY / CHỨC NĂNG:
- Send email alerts when services are down
- Gửi cảnh báo email khi dịch vụ down
- Simple configuration with environment variables
- Cấu hình đơn giản với biến môi trường
- Error handling and logging
- Xử lý lỗi và ghi log

USAGE / CÁCH SỬ DỤNG:
- Set environment variables: SMTP_USERNAME, SMTP_PASSWORD, ALERT_EMAIL
- Import and use: email_notifier.send_alert("Subject", "Message")
- Use in health check scripts
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleEmailNotification:
    """
    Simple email notification service for StillMe VPS
    """
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.username = os.getenv('SMTP_USERNAME')
        self.password = os.getenv('SMTP_PASSWORD')
        self.to_email = os.getenv('ALERT_EMAIL')
        
        # Check if configuration is complete
        self.configured = all([self.username, self.password, self.to_email])
        
        if not self.configured:
            logger.warning("⚠️ Email notification not fully configured. Set SMTP_USERNAME, SMTP_PASSWORD, ALERT_EMAIL")
        else:
            logger.info(f"✅ Email notification configured for: {self.to_email}")

    def send_alert(self, subject: str, message: str, severity: str = "medium") -> bool:
        """
        Send email alert
        
        Args:
            subject: Email subject
            message: Email message
            severity: Alert severity (low, medium, high, critical)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.configured:
            logger.error("❌ Email notification not configured")
            return False
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = self.to_email
            
            # Add severity to subject
            severity_emoji = {
                "low": "🟢",
                "medium": "🟡", 
                "high": "🟠",
                "critical": "🔴"
            }
            emoji = severity_emoji.get(severity, "🟡")
            
            msg['Subject'] = f"{emoji} [StillMe Alert] {subject}"
            
            # Create email body
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            body = f"""
StillMe VPS Alert

Severity: {severity.upper()}
Time: {timestamp}
Subject: {subject}

Message:
{message}

---
StillMe VPS Monitoring System
Automated Alert
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Email alert sent: {subject} (severity: {severity})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email: {e}")
            return False

    def send_health_alert(self, service: str, status: str, details: str = "") -> bool:
        """
        Send health check alert
        
        Args:
            service: Service name (Gateway, AI Server, etc.)
            status: Service status (down, up, degraded)
            details: Additional details
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if status.lower() == "down":
            severity = "critical"
            subject = f"{service} is DOWN"
            message = f"The {service} service is currently down.\n\nDetails: {details}"
        elif status.lower() == "degraded":
            severity = "high"
            subject = f"{service} is DEGRADED"
            message = f"The {service} service is experiencing issues.\n\nDetails: {details}"
        else:
            severity = "medium"
            subject = f"{service} is UP"
            message = f"The {service} service is back online.\n\nDetails: {details}"
            
        return self.send_alert(subject, message, severity)

    def test_connection(self) -> bool:
        """
        Test SMTP connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        if not self.configured:
            logger.error("❌ Email notification not configured")
            return False
            
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.quit()
            
            logger.info("✅ SMTP connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"❌ SMTP connection test failed: {e}")
            return False


# Global instance
email_notifier = SimpleEmailNotification()


def send_alert(subject: str, message: str, severity: str = "medium") -> bool:
    """
    Convenience function to send email alert
    
    Args:
        subject: Email subject
        message: Email message
        severity: Alert severity
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    return email_notifier.send_alert(subject, message, severity)


def send_health_alert(service: str, status: str, details: str = "") -> bool:
    """
    Convenience function to send health alert
    
    Args:
        service: Service name
        status: Service status
        details: Additional details
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    return email_notifier.send_health_alert(service, status, details)


if __name__ == "__main__":
    # Test the notification system
    print("🧪 Testing StillMe Email Notification System...")
    
    # Test connection
    if email_notifier.test_connection():
        print("✅ SMTP connection test passed")
        
        # Send test alert
        success = send_alert(
            "Test Alert", 
            "This is a test alert from StillMe VPS monitoring system.",
            "medium"
        )
        
        if success:
            print("✅ Test alert sent successfully")
        else:
            print("❌ Failed to send test alert")
    else:
        print("❌ SMTP connection test failed")
        print("💡 Make sure to set environment variables:")
        print("   export SMTP_USERNAME='your-email@gmail.com'")
        print("   export SMTP_PASSWORD='your-app-password'")
        print("   export ALERT_EMAIL='your-email@gmail.com'")
