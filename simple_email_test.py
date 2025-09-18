#!/usr/bin/env python3
"""
Simple email test for StillMe
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from datetime import datetime
from dotenv import load_dotenv

def test_email():
    """Test email sending"""
    print("🚀 StillMe Simple Email Test")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Get email settings
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_username = os.getenv("SMTP_USERNAME")
    smtp_password = os.getenv("SMTP_PASSWORD")
    alert_email = os.getenv("ALERT_EMAIL")
    
    print(f"📧 SMTP Server: {smtp_server}")
    print(f"📧 SMTP Port: {smtp_port}")
    print(f"📧 Username: {smtp_username}")
    print(f"📧 Alert Email: {alert_email}")
    print(f"📧 Password: {'*' * len(smtp_password) if smtp_password else 'NOT SET'}")
    
    if not all([smtp_server, smtp_username, smtp_password, alert_email]):
        print("❌ Missing email configuration!")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = alert_email
        msg['Subject'] = "[TEST] StillMe Email Test"
        
        body = """
        🎉 StillMe Email Test Successful!
        
        This is a test email from StillMe AI System.
        
        If you receive this email, the notification system is working correctly!
        
        Time: """ + str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) + """
        
        Best regards,
        StillMe AI System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        print("📤 Sending test email...")
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        print("✅ Email sent successfully!")
        print(f"📧 Check your inbox: {alert_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False

if __name__ == "__main__":
    success = test_email()
    if success:
        print("\n🎉 Email test completed successfully!")
    else:
        print("\n❌ Email test failed!")
