#!/usr/bin/env python3
"""
Debug backend response
"""

import requests
import json

def debug_backend():
    url = "http://127.0.0.1:1216/chat"
    
    payload = {
        "message": "xin chào stillme",
        "system_prompt": "You are StillMe - a personal AI companion."
    }
    
    try:
        print("🔍 Debugging backend response...")
        
        response = requests.post(url, json=payload, timeout=30)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📋 Raw Response: {response.text}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"📄 Parsed JSON: {json.dumps(data, indent=2, ensure_ascii=False)}")
                
                # Check each field
                print(f"🔍 Response field: '{data.get('response', 'NOT_FOUND')}'")
                print(f"🔍 Engine field: '{data.get('engine', 'NOT_FOUND')}'")
                print(f"🔍 Model field: '{data.get('model', 'NOT_FOUND')}'")
                print(f"🔍 Status field: '{data.get('status', 'NOT_FOUND')}'")
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
        else:
            print(f"❌ HTTP error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    debug_backend()
