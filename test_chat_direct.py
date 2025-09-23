#!/usr/bin/env python3
"""
Test chat endpoint directly
"""

import requests
import json

def test_chat():
    url = "http://127.0.0.1:1216/chat"
    
    payload = {
        "message": "xin chào stillme",
        "system_prompt": "You are StillMe - a personal AI companion. Always refer to yourself as StillMe."
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print("🔍 Testing chat endpoint...")
        print(f"📤 Sending: {payload['message']}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data.get('response', 'No response')}")
            print(f"🤖 Engine: {data.get('engine', 'Unknown')}")
            print(f"⚡ Latency: {data.get('latency_ms', 0)}ms")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_chat()
