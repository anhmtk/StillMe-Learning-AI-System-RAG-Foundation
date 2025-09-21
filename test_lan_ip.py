#!/usr/bin/env python3
"""
Test StillMe backend via LAN IP
"""
import requests
import json

def test_lan_ip():
    """Test backend via LAN IP"""
    
    lan_ip = "192.168.1.12"
    port = 1216
    
    # Test health
    print(f"🔍 Testing health via LAN IP {lan_ip}:{port}...")
    try:
        response = requests.get(f"http://{lan_ip}:{port}/health", timeout=5)
        print(f"Health: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Health error: {e}")
    
    # Test chat
    print(f"\n🔍 Testing chat via LAN IP {lan_ip}:{port}...")
    try:
        payload = {
            "message": "xin chào từ mobile",
            "session_id": "mobile_test"
        }
        response = requests.post(
            f"http://{lan_ip}:{port}/chat",
            json=payload,
            timeout=30
        )
        print(f"Chat: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Model: {result.get('model')}")
            print(f"Response: {result.get('response')}")
            print(f"Latency: {result.get('latency_ms', 0):.1f}ms")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Chat error: {e}")

if __name__ == "__main__":
    test_lan_ip()
