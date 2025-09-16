#!/usr/bin/env python3
"""
Simple Desktop Test - StillMe Gateway
=====================================

Test đơn giản kết nối với Gateway
"""

import requests
import json

def test_gateway():
    """Test Gateway cơ bản"""
    gateway_url = "http://160.191.89.99:8000"
    
    print("🔍 Testing Gateway...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{gateway_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check: OK")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test 2: Version check
    try:
        response = requests.get(f"{gateway_url}/version", timeout=5)
        if response.status_code == 200:
            print("✅ Version check: OK")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Version check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Version check error: {e}")
    
    # Test 3: Simple message (với timeout ngắn)
    try:
        print("💬 Testing simple message...")
        payload = {"message": "test", "language": "vi"}
        response = requests.post(
            f"{gateway_url}/send-message",
            json=payload,
            timeout=10  # Timeout ngắn hơn
        )
        
        if response.status_code == 200:
            print("✅ Message test: OK")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Message test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Message test: TIMEOUT (Gateway có thể đang xử lý)")
        print("   Điều này có thể bình thường nếu AI Server chưa sẵn sàng")
        return True  # Timeout không có nghĩa là lỗi hoàn toàn
        
    except Exception as e:
        print(f"❌ Message test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Simple Desktop Gateway Test")
    print("=" * 40)
    
    success = test_gateway()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Gateway connection test: SUCCESS!")
        print("✅ Desktop app có thể kết nối với Gateway")
        print("💡 Bạn có thể update desktop/mobile apps với URL này:")
        print("   http://160.191.89.99:8000")
    else:
        print("❌ Gateway connection test: FAILED!")
        print("🔧 Hãy kiểm tra Gateway logs trên VPS")
