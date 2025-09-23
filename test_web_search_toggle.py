#!/usr/bin/env python3
"""
Test script for web search toggle functionality
"""
import requests
import json

def test_web_search_toggle():
    """Test web search toggle functionality"""
    print("🧪 Testing Web Search Toggle Functionality")
    print("=" * 50)
    
    # Test data
    test_message = "Tin tức AI hôm nay"
    api_url = "http://127.0.0.1:1216/chat"
    
    # Test with web search enabled
    print("\n1. Testing with Web Search ENABLED:")
    payload_enabled = {
        "message": test_message,
        "session_id": "test_session",
        "system_prompt": "You are StillMe – Intelligent Personal Companion (IPC).",
        "web_search_enabled": True
    }
    
    try:
        response = requests.post(api_url, json=payload_enabled, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response received")
            print(f"   Model: {result.get('model', 'unknown')}")
            print(f"   Engine: {result.get('engine', 'unknown')}")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Response preview: {result.get('response', '')[:100]}...")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test with web search disabled
    print("\n2. Testing with Web Search DISABLED:")
    payload_disabled = {
        "message": test_message,
        "session_id": "test_session",
        "system_prompt": "You are StillMe – Intelligent Personal Companion (IPC).",
        "web_search_enabled": False
    }
    
    try:
        response = requests.post(api_url, json=payload_disabled, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response received")
            print(f"   Model: {result.get('model', 'unknown')}")
            print(f"   Engine: {result.get('engine', 'unknown')}")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Response preview: {result.get('response', '')[:100]}...")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Test with non-web request (should work the same regardless of toggle)
    print("\n3. Testing with non-web request:")
    payload_normal = {
        "message": "Xin chào, bạn là ai?",
        "session_id": "test_session",
        "system_prompt": "You are StillMe – Intelligent Personal Companion (IPC).",
        "web_search_enabled": False
    }
    
    try:
        response = requests.post(api_url, json=payload_normal, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Response received")
            print(f"   Model: {result.get('model', 'unknown')}")
            print(f"   Engine: {result.get('engine', 'unknown')}")
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Response preview: {result.get('response', '')[:100]}...")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Web search toggle test completed!")

if __name__ == "__main__":
    test_web_search_toggle()
