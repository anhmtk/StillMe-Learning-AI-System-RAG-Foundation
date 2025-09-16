# desktop_notification.py
import os
import sys
import json
import requests
from datetime import datetime

class DesktopNotification:
    def __init__(self):
        self.desktop_app_url = "http://localhost:3000"  # Desktop app URL
        self.mobile_app_url = "http://localhost:8081"   # Mobile app URL
        
    def send_desktop_alert(self, title, message, severity="info"):
        """Gửi thông báo đến Desktop App"""
        try:
            payload = {
                "type": "system_alert",
                "title": title,
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
                "source": "stillme_vps"
            }
            
            response = requests.post(
                f"{self.desktop_app_url}/api/notifications",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✅ Desktop notification sent: {title}")
                return True
            else:
                print(f"❌ Desktop notification failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Desktop app not reachable: {e}")
            return False
    
    def send_mobile_alert(self, title, message, severity="info"):
        """Gửi thông báo đến Mobile App"""
        try:
            payload = {
                "type": "system_alert",
                "title": title,
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat(),
                "source": "stillme_vps"
            }
            
            response = requests.post(
                f"{self.mobile_app_url}/api/notifications",
                json=payload,
                timeout=5
            )
            
            if response.status_code == 200:
                print(f"✅ Mobile notification sent: {title}")
                return True
            else:
                print(f"❌ Mobile notification failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Mobile app not reachable: {e}")
            return False
    
    def send_sms_alert(self, message, phone_number):
        """Gửi SMS qua API miễn phí"""
        try:
            # Sử dụng SMS API miễn phí
            sms_apis = [
                {
                    "name": "TextBelt",
                    "url": "https://textbelt.com/text",
                    "data": {
                        "phone": phone_number,
                        "message": f"[StillMe Alert] {message}",
                        "key": "textbelt"
                    }
                },
                {
                    "name": "SMS Global",
                    "url": "https://api.smsglobal.com/v1/sms",
                    "headers": {
                        "Authorization": "Basic YOUR_API_KEY"
                    },
                    "data": {
                        "destination": phone_number,
                        "message": f"[StillMe Alert] {message}"
                    }
                }
            ]
            
            for api in sms_apis:
                try:
                    if api["name"] == "TextBelt":
                        response = requests.post(api["url"], data=api["data"], timeout=10)
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("success"):
                                print(f"✅ SMS sent via {api['name']}: {message}")
                                return True
                            else:
                                print(f"❌ SMS failed via {api['name']}: {result.get('error')}")
                    
                except requests.exceptions.RequestException as e:
                    print(f"❌ SMS API {api['name']} failed: {e}")
                    continue
            
            print("❌ All SMS APIs failed")
            return False
            
        except Exception as e:
            print(f"❌ SMS sending error: {e}")
            return False
    
    def send_telegram_alert(self, message, bot_token, chat_id):
        """Gửi thông báo qua Telegram Bot"""
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
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Telegram API failed: {e}")
            return False
    
    def send_all_alerts(self, title, message, severity="info", phone_number=None, telegram_config=None):
        """Gửi thông báo đến tất cả kênh"""
        results = []
        
        # Desktop App
        results.append(self.send_desktop_alert(title, message, severity))
        
        # Mobile App
        results.append(self.send_mobile_alert(title, message, severity))
        
        # SMS (nếu có số điện thoại)
        if phone_number:
            results.append(self.send_sms_alert(message, phone_number))
        
        # Telegram (nếu có config)
        if telegram_config:
            results.append(self.send_telegram_alert(
                message, 
                telegram_config["bot_token"], 
                telegram_config["chat_id"]
            ))
        
        success_count = sum(results)
        total_count = len(results)
        
        print(f"📊 Alert summary: {success_count}/{total_count} channels successful")
        return success_count > 0

# Global instance
desktop_notifier = DesktopNotification()

def send_alert(title, message, severity="info", phone_number=None, telegram_config=None):
    """Hàm gửi thông báo đơn giản"""
    return desktop_notifier.send_all_alerts(title, message, severity, phone_number, telegram_config)

def send_health_alert(service_name, status, details=""):
    """Hàm gửi thông báo sức khỏe hệ thống"""
    title = f"StillMe {service_name} {status.upper()}"
    message = f"Service: {service_name}\nStatus: {status}\nDetails: {details}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return send_alert(title, message, "high" if status == "down" else "info")

if __name__ == "__main__":
    print("🧪 Testing StillMe Desktop Notification System...")
    
    # Test desktop notification
    send_alert("Test Alert", "This is a test from StillMe VPS", "info")
    
    # Test health alert
    send_health_alert("Gateway", "down", "Service is not responding")
    
    print("✅ Desktop notification system test completed!")
