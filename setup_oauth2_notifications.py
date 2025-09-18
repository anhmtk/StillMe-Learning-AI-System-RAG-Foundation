#!/usr/bin/env python3
"""
StillMe OAuth2 Email Notification Setup
Thiết lập email notifications sử dụng OAuth2 thay vì App Password
"""

import os
import json
import webbrowser
from urllib.parse import urlencode, parse_qs
import requests
import base64
import hashlib
import secrets

def generate_oauth2_credentials():
    """Tạo OAuth2 credentials cho Gmail API"""
    print("🔐 StillMe OAuth2 Email Setup")
    print("=" * 50)
    
    # OAuth2 configuration
    client_id = "your_client_id_here"  # Sẽ được thay thế
    client_secret = "your_client_secret_here"  # Sẽ được thay thế
    redirect_uri = "http://localhost:8080/callback"
    
    # Generate state và code_verifier cho PKCE
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(32)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    # OAuth2 authorization URL
    auth_params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'https://www.googleapis.com/auth/gmail.send',
        'response_type': 'code',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
        'access_type': 'offline',
        'prompt': 'consent'
    }
    
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(auth_params)}"
    
    print("📋 Hướng dẫn OAuth2 Setup:")
    print("1. Vào Google Cloud Console: https://console.cloud.google.com/")
    print("2. Tạo project mới hoặc chọn project hiện có")
    print("3. Enable Gmail API")
    print("4. Tạo OAuth2 credentials")
    print("5. Thêm redirect URI: http://localhost:8080/callback")
    print("6. Copy Client ID và Client Secret")
    print()
    
    # Get credentials from user
    client_id = input("Nhập Client ID: ").strip()
    client_secret = input("Nhập Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Client ID và Client Secret không được để trống!")
        return False
    
    # Update auth URL with real credentials
    auth_params['client_id'] = client_id
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(auth_params)}"
    
    print(f"\n🌐 Mở trình duyệt để authorize...")
    print(f"URL: {auth_url}")
    
    # Open browser
    webbrowser.open(auth_url)
    
    print("\n📝 Sau khi authorize:")
    print("1. Copy toàn bộ URL từ address bar")
    print("2. Paste vào đây")
    
    callback_url = input("\nPaste callback URL: ").strip()
    
    if not callback_url:
        print("❌ Callback URL không được để trống!")
        return False
    
    # Parse callback URL
    try:
        parsed = parse_qs(callback_url.split('?')[1])
        auth_code = parsed.get('code', [None])[0]
        returned_state = parsed.get('state', [None])[0]
        
        if not auth_code:
            print("❌ Không tìm thấy authorization code!")
            return False
            
        if returned_state != state:
            print("❌ State mismatch - có thể bị tấn công!")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi parse callback URL: {e}")
        return False
    
    # Exchange code for tokens
    print("\n🔄 Đang lấy access token...")
    
    token_data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
        'code_verifier': code_verifier
    }
    
    try:
        response = requests.post('https://oauth2.googleapis.com/token', data=token_data)
        response.raise_for_status()
        
        tokens = response.json()
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        
        if not access_token:
            print("❌ Không nhận được access token!")
            return False
            
        print("✅ OAuth2 setup thành công!")
        
        # Save to .env
        env_content = f"""
# OAuth2 Gmail Configuration
GMAIL_OAUTH2_CLIENT_ID={client_id}
GMAIL_OAUTH2_CLIENT_SECRET={client_secret}
GMAIL_OAUTH2_ACCESS_TOKEN={access_token}
GMAIL_OAUTH2_REFRESH_TOKEN={refresh_token}
GMAIL_OAUTH2_REDIRECT_URI={redirect_uri}

# Alert Configuration
ALERT_EMAIL=anhnguyen.nk86@gmail.com
"""
        
        with open('.env', 'a') as f:
            f.write(env_content)
            
        print("💾 Đã lưu OAuth2 credentials vào .env")
        print("🧪 Đang test email...")
        
        # Test email
        return test_oauth2_email(access_token, client_id, client_secret, refresh_token)
        
    except Exception as e:
        print(f"❌ Lỗi lấy token: {e}")
        return False

def test_oauth2_email(access_token, client_id, client_secret, refresh_token):
    """Test gửi email với OAuth2"""
    try:
        # Create test email
        email_content = {
            "raw": base64.urlsafe_b64encode(
                f"To: anhnguyen.nk86@gmail.com\r\n"
                f"From: anhnguyen.nk86@gmail.com\r\n"
                f"Subject: [TEST] StillMe OAuth2 Email Test\r\n"
                f"\r\n"
                f"Đây là email test từ StillMe OAuth2 system!\r\n"
                f"Timestamp: {os.popen('date').read().strip()}\r\n"
                f"Status: ✅ OAuth2 working correctly!"
            ).decode()
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
            headers=headers,
            json=email_content
        )
        
        if response.status_code == 200:
            print("✅ Email test thành công!")
            print("📧 Check inbox: anhnguyen.nk86@gmail.com")
            return True
        else:
            print(f"❌ Email test thất bại: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi test email: {e}")
        return False

def create_oauth2_notifier():
    """Tạo OAuth2 Email Notifier"""
    notifier_code = '''
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
                        f.write(f'GMAIL_OAUTH2_ACCESS_TOKEN={new_token}\\n')
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
                email_body += "\\n\\n--- Metadata ---\\n"
                for key, value in metadata.items():
                    email_body += f"{key}: {value}\\n"
            
            # Create email message
            email_content = {
                "raw": base64.urlsafe_b64encode(
                    f"To: {self.alert_email}\\r\\n"
                    f"From: {self.alert_email}\\r\\n"
                    f"Subject: [{severity.upper()}] StillMe Alert: {subject}\\r\\n"
                    f"\\r\\n"
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
'''
    
    with open('stillme_platform/gateway/services/oauth2_email_notifier.py', 'w', encoding='utf-8') as f:
        f.write(notifier_code)
    
    print("📁 Đã tạo OAuth2EmailNotifier")

if __name__ == "__main__":
    print("🚀 StillMe OAuth2 Email Notification Setup")
    print("=" * 50)
    
    # Create OAuth2 notifier
    create_oauth2_notifier()
    
    # Setup OAuth2 credentials
    success = generate_oauth2_credentials()
    
    if success:
        print("\\n🎉 OAuth2 Email Setup hoàn thành!")
        print("📧 Bạn có thể sử dụng OAuth2EmailNotifier thay vì EmailNotifier")
        print("🔧 Cập nhật NotificationManager để sử dụng OAuth2EmailNotifier")
    else:
        print("\\n❌ OAuth2 setup thất bại")
        print("💡 Bạn có thể thử lại hoặc sử dụng App Password method")
