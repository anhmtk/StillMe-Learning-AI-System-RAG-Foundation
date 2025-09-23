#!/usr/bin/env python3
"""
Test Core Framework Backend
"""
import requests
import json

BACKEND_URL = "http://127.0.0.1:1216"

def test_core_backend():
    print("🔍 Testing Core Framework Backend...")
    
    # Test 1: Health check
    print("\n1️⃣ Test health endpoint:")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"Status: {result.get('status')}")
            print(f"Framework: {result.get('framework')}")
            if 'modules' in result:
                print(f"Modules: {result.get('modules')}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Root endpoint
    print("\n2️⃣ Test root endpoint:")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"Service: {result.get('service')}")
            print(f"Framework: {result.get('framework')}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Chat with Core Framework
    print("\n3️⃣ Test chat with Core Framework:")
    payload = {
        "message": "bạn là ai?",
        "session_id": "test_user"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print(f"Response: {result.get('response')}")
            print(f"Engine: {result.get('engine')}")
            print(f"Model: {result.get('model')}")
        else:
            print(f"Error: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_core_backend()
