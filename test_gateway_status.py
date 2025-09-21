#!/usr/bin/env python3
"""
Test VPS Gateway status và routing logic
"""
import requests
import json

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get('http://160.191.89.99:21568/health', timeout=5)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Service: {data.get('service', 'unknown')}")
            print(f"Status: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Exception: {e}")
        return False

def test_simple_message():
    """Test simple message routing"""
    print("\n🔍 Testing simple message routing...")
    try:
        response = requests.post('http://160.191.89.99:21568/chat', 
                               json={'message': 'xin chào', 'session_id': 'test'}, 
                               timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Model: {data.get('model', 'unknown')}")
            print(f"Response: {data.get('response', '')[:100]}...")
            return data.get('model', 'unknown')
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

def test_complex_message():
    """Test complex message routing"""
    print("\n🔍 Testing complex message routing...")
    try:
        response = requests.post('http://160.191.89.99:21568/chat', 
                               json={'message': 'Hãy viết đoạn code Python đọc CSV, tính trung bình và in kết quả theo cột.', 'session_id': 'test'}, 
                               timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Model: {data.get('model', 'unknown')}")
            print(f"Response: {data.get('response', '')[:100]}...")
            return data.get('model', 'unknown')
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Exception: {e}")
        return None

if __name__ == "__main__":
    print("🚀 VPS Gateway Status Check")
    print("=" * 50)
    
    # Test health
    health_ok = test_health()
    
    if health_ok:
        # Test routing
        simple_model = test_simple_message()
        complex_model = test_complex_message()
        
        print("\n📊 SUMMARY:")
        print(f"Health: {'✅ OK' if health_ok else '❌ FAIL'}")
        print(f"Simple message model: {simple_model}")
        print(f"Complex message model: {complex_model}")
        
        if simple_model == "deepseek-chat":
            print("❌ PROBLEM: Simple message using DeepSeek (expensive)")
        elif simple_model and "gemma" in simple_model.lower():
            print("✅ GOOD: Simple message using Gemma (local)")
        
        if complex_model == "deepseek-chat":
            print("✅ GOOD: Complex message using DeepSeek")
        elif complex_model is None:
            print("❌ PROBLEM: Complex message failed/timeout")
    else:
        print("❌ Gateway not healthy, skipping routing tests")
