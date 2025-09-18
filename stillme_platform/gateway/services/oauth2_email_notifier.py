
import os
import base64
import requests
import json
from typing import Dict, Any, Optional

class OAuth2EmailNotifier:
    """Gửi email sử dụng Gmail OAuth2"""
    
    def __init__(self):
        self.client_id = os.getenv("GMAIL_OAUTH2_CLIENT_ID")
        self.client_secret = os.getenv("GMAIL_OAUTH2_CLIENT_SECRET")
        self.access_token = os.getenv("GMAIL_OAUTH2_ACCESS_TOKEN")
        self.refresh_token = os.getenv("GMAIL_OAUTH2_REFRESH_TOKEN")
        self.redirect_uri = os.getenv("GMAIL_OAUTH2_REDIRECT_URI")
        self.alert_email = os.getenv("ALERT_EMAIL")
        
        self.is_configured = self._check_config()
        
        if not self.is_configured:
            print("⚠️ OAuth2EmailNotifier chưa được cấu hình đầy đủ")
    
    def _check_config(self) -> bool:
        """Kiểm tra cấu hình OAuth2"""
        required_vars = [
            "GMAIL_OAUTH2_CLIENT_ID", "GMAIL_OAUTH2_CLIENT_SECRET",
            "GMAIL_OAUTH2_ACCESS_TOKEN", "GMAIL_OAUTH2_REFRESH_TOKEN"
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"❌ Missing OAuth2 vars: {', '.join(missing_vars)}")
            return False
        return True
    
    def _refresh_access_token(self) -> bool:
        """Refresh access token nếu cần"""
        try:
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
            response.raise_for_status()
            
            tokens = response.json()
            self.access_token = tokens.get('access_token')
            
            # Update .env file
            self._update_env_token(self.access_token)
            
            return True
        except Exception as e:
            print(f"❌ Lỗi refresh token: {e}")
            return False
    
    def _update_env_token(self, new_token: str):
        """Cập nhật access token trong .env"""
        try:
            with open('.env', 'r') as f:
                lines = f.readlines()
            
            with open('.env', 'w') as f:
                for line in lines:
                    if line.startswith('GMAIL_OAUTH2_ACCESS_TOKEN='):
                        f.write(f'GMAIL_OAUTH2_ACCESS_TOKEN={new_token}\n')
                    else:
                        f.write(line)
        except Exception as e:
            print(f"⚠️ Không thể cập nhật .env: {e}")
    
    async def send_email(
        self,
        subject: str,
        body: str,
        severity: str = "info",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Gửi email sử dụng Gmail OAuth2"""
        if not self.is_configured:
            print("❌ OAuth2EmailNotifier chưa được cấu hình")
            return False
        
        try:
            # Prepare email content
            email_body = f"{body}"
            if metadata:
                email_body += "\n\n--- Metadata ---\n"
                for key, value in metadata.items():
                    email_body += f"{key}: {value}\n"
            
            # Create email message
            email_content = {
                "raw": base64.urlsafe_b64encode(
                    f"To: {self.alert_email}\r\n"
                    f"From: {self.alert_email}\r\n"
                    f"Subject: [{severity.upper()}] StillMe Alert: {subject}\r\n"
                    f"\r\n"
                    f"{email_body}"
                ).decode()
            }
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Send email
            response = requests.post(
                'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
                headers=headers,
                json=email_content
            )
            
            if response.status_code == 401:
                # Token expired, try to refresh
                print("🔄 Access token expired, refreshing...")
                if self._refresh_access_token():
                    headers['Authorization'] = f'Bearer {self.access_token}'
                    response = requests.post(
                        'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
                        headers=headers,
                        json=email_content
                    )
            
            if response.status_code == 200:
                print(f"✅ Email sent: '{subject}' to {self.alert_email}")
                return True
            else:
                print(f"❌ Email failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Lỗi gửi email: {e}")
            return False
