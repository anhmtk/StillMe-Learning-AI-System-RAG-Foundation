#!/usr/bin/env python3
"""
Simple test script for StillMe backend
"""
import requests
import json

def test_backend():
    """Test backend endpoints"""
    
    # Test health
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get("http://127.0.0.1:1216/health", timeout=5)
        print(f"Health: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Health error: {e}")
    
    # Test chat
    print("\n🔍 Testing chat endpoint...")
    try:
        payload = {
            "message": "xin chào",
            "session_id": "test"
        }
        response = requests.post(
            "http://127.0.0.1:1216/chat",
            json=payload,
            timeout=30
        )
        print(f"Chat: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Chat error: {e}")

if __name__ == "__main__":
    test_backend()
