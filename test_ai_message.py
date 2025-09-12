#!/usr/bin/env python3
"""
Test AI Message through Gateway
Test gửi message đến AI qua Gateway
"""

import requests
import json
from datetime import datetime

def test_ai_message():
    """Test AI message through Gateway REST API"""
    
    # Test Gateway health
    print("🔍 Testing Gateway health...")
    try:
        response = requests.get("http://192.168.1.8:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Gateway is healthy")
        else:
            print(f"❌ Gateway health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Gateway connection failed: {e}")
        return
    
    # Test AI message
    print("🤖 Testing AI message...")
    message = {
        "message": "Xin chào StillMe! Bạn có thể giúp tôi không?",
        "language": "vi",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(
            "http://192.168.1.8:8000/api/message",
            json=message,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ AI message sent successfully!")
            print(f"📝 Response: {result}")
        else:
            print(f"❌ AI message failed: {response.status_code}")
            print(f"📝 Error: {response.text}")
            
    except Exception as e:
        print(f"❌ AI message error: {e}")

if __name__ == "__main__":
    print("🧪 Testing AI Message through Gateway")
    print("=" * 50)
    test_ai_message()
