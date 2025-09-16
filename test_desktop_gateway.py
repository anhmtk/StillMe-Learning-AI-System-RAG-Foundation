#!/usr/bin/env python3
"""
Desktop App Test - StillMe Gateway Connection
============================================

Test application để kiểm tra kết nối với StillMe Gateway trên VPS
"""

import requests
import json
import time
from datetime import datetime

class StillMeDesktopClient:
    def __init__(self, gateway_url="http://160.191.89.99:8000"):
        """Khởi tạo desktop client kết nối với Gateway"""
        self.gateway_url = gateway_url
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'StillMe-Desktop-Client/1.0'
        })
    
    def test_connection(self):
        """Test kết nối cơ bản với Gateway"""
        try:
            print("🔍 Testing Gateway connection...")
            response = self.session.get(f"{self.gateway_url}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Gateway Health: {data['status']}")
                print(f"📅 Timestamp: {data['timestamp']}")
                return True
            else:
                print(f"❌ Gateway Health Check Failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Connection Error: {e}")
            return False
    
    def get_version(self):
        """Lấy thông tin version của Gateway"""
        try:
            print("📋 Getting Gateway version...")
            response = self.session.get(f"{self.gateway_url}/version", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Gateway: {data['name']} v{data['version']}")
                print(f"🏗️ Build Time: {data['build_time']}")
                return data
            else:
                print(f"❌ Version Check Failed: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Version Error: {e}")
            return None
    
    def send_message(self, message, language="vi"):
        """Gửi tin nhắn đến StillMe AI qua Gateway"""
        try:
            print(f"💬 Sending message: '{message}'")
            
            payload = {
                "message": message,
                "language": language
            }
            
            response = self.session.post(
                f"{self.gateway_url}/send-message",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ StillMe Response: {data['response']}")
                print(f"📅 Timestamp: {data['timestamp']}")
                print(f"🤖 AI Server: {data['ai_server']}")
                return data
            else:
                print(f"❌ Send Message Failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Send Message Error: {e}")
            return None
    
    def interactive_chat(self):
        """Chế độ chat tương tác"""
        print("\n" + "="*60)
        print("🤖 STILLME DESKTOP CLIENT - INTERACTIVE CHAT")
        print("="*60)
        print("Commands:")
        print("  - Type your message and press Enter")
        print("  - Type 'quit' or 'exit' to stop")
        print("  - Type 'status' to check Gateway health")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n💬 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'status':
                    self.test_connection()
                    continue
                elif not user_input:
                    continue
                
                # Gửi tin nhắn
                response = self.send_message(user_input)
                
                if response:
                    print(f"🤖 StillMe: {response['response']}")
                else:
                    print("❌ Failed to get response from StillMe")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main function"""
    print("🚀 StillMe Desktop Client Starting...")
    print(f"📅 Time: {datetime.now()}")
    print("-" * 50)
    
    # Khởi tạo client
    client = StillMeDesktopClient()
    
    # Test kết nối
    if not client.test_connection():
        print("❌ Cannot connect to Gateway. Please check:")
        print("   1. VPS is running")
        print("   2. Gateway is running on port 8000")
        print("   3. Firewall allows port 8000")
        return
    
    # Lấy version
    client.get_version()
    
    # Test gửi tin nhắn
    print("\n" + "-" * 50)
    print("🧪 Testing message sending...")
    test_response = client.send_message("Xin chào StillMe! Tôi là desktop app.")
    
    if test_response:
        print("\n✅ Gateway connection test SUCCESSFUL!")
        print("🎉 Desktop app can communicate with StillMe AI!")
        
        # Hỏi user có muốn chat không
        choice = input("\n🤔 Do you want to start interactive chat? (y/n): ").strip().lower()
        if choice in ['y', 'yes', 'có']:
            client.interactive_chat()
    else:
        print("\n❌ Gateway connection test FAILED!")
        print("Please check Gateway status and try again.")

if __name__ == "__main__":
    main()
