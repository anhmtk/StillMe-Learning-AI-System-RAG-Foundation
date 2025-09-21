#!/usr/bin/env python3
"""
Test VPS Gateway để xem response format thực tế
"""
import requests
import json
import time

def test_vps_gateway():
    base_url = "http://160.191.89.99:21568"
    
    print("🔍 Testing VPS Gateway...")
    
    # Test 1: Health check
    print("\n1️⃣ Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return
    
    # Test 2: Chat endpoint với format đơn giản
    print("\n2️⃣ Testing chat endpoint (simple format)...")
    try:
        payload = {
            "message": "Xin chào StillMe!"
        }
        response = requests.post(
            f"{base_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ❌ Simple chat failed: {e}")
    
    # Test 3: Chat endpoint với format đầy đủ (như mobile app)
    print("\n3️⃣ Testing chat endpoint (full format)...")
    try:
        payload = {
            "message": "Xin chào StillMe!",
            "session_id": f"test_{int(time.time())}",
            "metadata": {
                "persona": "assistant",
                "language": "vi",
                "founder_command": False,
                "debug": True
            }
        }
        response = requests.post(
            f"{base_url}/chat",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Client-Version": "1.0.0",
                "X-Platform": "mobile"
            },
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ❌ Full chat failed: {e}")
    
    # Test 4: Chat endpoint với session headers
    print("\n4️⃣ Testing chat endpoint (with session headers)...")
    try:
        payload = {
            "message": "Xin chào StillMe!"
        }
        response = requests.post(
            f"{base_url}/chat",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "X-Client-Version": "1.0.0",
                "X-Platform": "mobile",
                "X-Session": "test_session_token",
                "X-Nonce": "test_nonce",
                "X-Client": "stillme-mobile/1.0.0"
            },
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"   ❌ Session chat failed: {e}")

if __name__ == "__main__":
    test_vps_gateway()
