# sms_notification.py
import requests
import os
from datetime import datetime

class SMSNotification:
    def __init__(self):
        self.phone_number = os.getenv('ALERT_PHONE', '+84901234567')  # Số điện thoại nhận SMS
        
    def send_sms_via_textbelt(self, message, phone_number=None):
        """Gửi SMS qua TextBelt (miễn phí)"""
        if not phone_number:
            phone_number = self.phone_number
            
        try:
            url = "https://textbelt.com/text"
            data = {
                "phone": phone_number,
                "message": f"[StillMe Alert] {message}",
                "key": "textbelt"  # Free key
            }
            
            response = requests.post(url, data=data, timeout=10)
            result = response.json()
            
            if result.get("success"):
                print(f"✅ SMS sent via TextBelt: {message}")
                return True
            else:
                print(f"❌ SMS failed via TextBelt: {result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ TextBelt SMS error: {e}")
            return False
    
    def send_sms_via_smsglobal(self, message, phone_number=None):
        """Gửi SMS qua SMS Global (miễn phí)"""
        if not phone_number:
            phone_number = self.phone_number
            
        try:
            url = "https://api.smsglobal.com/v1/sms"
            headers = {
                "Authorization": "Basic YOUR_API_KEY"  # Cần đăng ký
            }
            data = {
                "destination": phone_number,
                "message": f"[StillMe Alert] {message}"
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ SMS sent via SMS Global: {message}")
                return True
            else:
                print(f"❌ SMS failed via SMS Global: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ SMS Global error: {e}")
            return False
    
    def send_sms_via_twilio(self, message, phone_number=None):
        """Gửi SMS qua Twilio (có phí)"""
        if not phone_number:
            phone_number = self.phone_number
            
        try:
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
            
            if not all([account_sid, auth_token, twilio_phone]):
                print("❌ Twilio credentials not configured")
                return False
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
            data = {
                "From": twilio_phone,
                "To": phone_number,
                "Body": f"[StillMe Alert] {message}"
            }
            
            response = requests.post(url, data=data, auth=(account_sid, auth_token), timeout=10)
            
            if response.status_code == 201:
                print(f"✅ SMS sent via Twilio: {message}")
                return True
            else:
                print(f"❌ SMS failed via Twilio: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Twilio SMS error: {e}")
            return False
    
    def send_sms_via_telegram(self, message, bot_token, chat_id):
        """Gửi thông báo qua Telegram Bot (miễn phí)"""
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": f"🚨 [StillMe Alert]\n{message}",
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Telegram notification sent: {message}")
                return True
            else:
                print(f"❌ Telegram notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Telegram API error: {e}")
            return False
    
    def send_sms_via_discord(self, message, webhook_url):
        """Gửi thông báo qua Discord Webhook (miễn phí)"""
        try:
            payload = {
                "content": f"🚨 **StillMe Alert**\n{message}",
                "username": "StillMe VPS",
                "avatar_url": "https://example.com/stillme-avatar.png"
            }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code == 204:
                print(f"✅ Discord notification sent: {message}")
                return True
            else:
                print(f"❌ Discord notification failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Discord webhook error: {e}")
            return False
    
    def send_all_sms(self, message, phone_number=None):
        """Thử gửi SMS qua tất cả kênh miễn phí"""
        results = []
        
        # TextBelt (miễn phí)
        results.append(self.send_sms_via_textbelt(message, phone_number))
        
        # Telegram (nếu có config)
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if bot_token and chat_id:
            results.append(self.send_sms_via_telegram(message, bot_token, chat_id))
        
        # Discord (nếu có webhook)
        discord_webhook = os.getenv('DISCORD_WEBHOOK_URL')
        if discord_webhook:
            results.append(self.send_sms_via_discord(message, discord_webhook))
        
        success_count = sum(results)
        total_count = len(results)
        
        print(f"📊 SMS summary: {success_count}/{total_count} channels successful")
        return success_count > 0

# Global instance
sms_notifier = SMSNotification()

def send_sms_alert(message, phone_number=None):
    """Hàm gửi SMS đơn giản"""
    return sms_notifier.send_all_sms(message, phone_number)

def send_health_sms(service_name, status, details=""):
    """Hàm gửi SMS thông báo sức khỏe hệ thống"""
    message = f"StillMe {service_name} {status.upper()}\nDetails: {details}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    return send_sms_alert(message)

if __name__ == "__main__":
    print("🧪 Testing StillMe SMS Notification System...")
    
    # Test SMS
    send_sms_alert("This is a test from StillMe VPS")
    
    # Test health SMS
    send_health_sms("Gateway", "down", "Service is not responding")
    
    print("✅ SMS notification system test completed!")
