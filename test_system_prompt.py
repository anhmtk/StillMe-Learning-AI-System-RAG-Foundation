#!/usr/bin/env python3
"""
Test system prompt enforcement in backend
"""
import requests
import json

BACKEND_URL = "http://127.0.0.1:1216"

def test_system_prompt():
    print("🔍 Testing system prompt enforcement...")
    
    # Test 1: Without system prompt
    print("\n1️⃣ Test without system prompt:")
    payload1 = {
        "message": "bạn là ai?",
        "session_id": "test_user"
    }
    
    try:
        response1 = requests.post(f"{BACKEND_URL}/chat", json=payload1, timeout=30)
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"Response: {result1.get('response')}")
            print(f"Engine: {result1.get('engine')}")
        else:
            print(f"Error: {response1.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: With system prompt
    print("\n2️⃣ Test with system prompt:")
    payload2 = {
        "message": "bạn là ai?",
        "session_id": "test_user",
        "system_prompt": "You are StillMe — a personal AI companion. Always introduce and refer to yourself as 'StillMe'. Never claim to be Gemma, OpenAI, DeepSeek, or any underlying provider/model."
    }
    
    try:
        response2 = requests.post(f"{BACKEND_URL}/chat", json=payload2, timeout=30)
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"Response: {result2.get('response')}")
            print(f"Engine: {result2.get('engine')}")
        else:
            print(f"Error: {response2.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Code question (should try DeepSeek)
    print("\n3️⃣ Test code question:")
    payload3 = {
        "message": "viết code Python để tính fibonacci",
        "session_id": "test_user",
        "system_prompt": "You are StillMe — a personal AI companion. Always introduce and refer to yourself as 'StillMe'."
    }
    
    try:
        response3 = requests.post(f"{BACKEND_URL}/chat", json=payload3, timeout=30)
        if response3.status_code == 200:
            result3 = response3.json()
            print(f"Response: {result3.get('response')[:100]}...")
            print(f"Engine: {result3.get('engine')}")
            print(f"Model: {result3.get('model')}")
        else:
            print(f"Error: {response3.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_system_prompt()
