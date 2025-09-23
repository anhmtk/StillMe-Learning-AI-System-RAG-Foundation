#!/usr/bin/env python3
"""
Test Ollama directly
"""

import requests
import json

def test_ollama():
    url = "http://127.0.0.1:11434/api/generate"
    
    payload = {
        "model": "gemma2:2b",
        "messages": [
            {"role": "system", "content": "You are StillMe - a personal AI companion. Always refer to yourself as StillMe."},
            {"role": "user", "content": "xin chào stillme"}
        ],
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }
    
    try:
        print("🔍 Testing Ollama directly...")
        print(f"📤 Sending to: {url}")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, json=payload, timeout=120)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📄 Full Response: {json.dumps(data, indent=2)}")
            
            # Check different response formats
            if "message" in data:
                response_text = data["message"].get("content", "No response")
                print(f"✅ Message Content: {response_text}")
            elif "response" in data:
                response_text = data.get("response", "No response")
                print(f"✅ Response Content: {response_text}")
            else:
                print(f"❌ Unknown response format: {data}")
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_ollama()
