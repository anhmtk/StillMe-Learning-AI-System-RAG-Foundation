#!/usr/bin/env python3
"""
Test routing logic trên VPS Gateway
"""
import requests
import json

def test_simple_message():
    """Test câu đơn giản - should use Gemma2:2b local"""
    simple_msg = {'message': 'xin chào'}
    print('🔍 Testing simple message (should use Gemma2:2b)...')
    try:
        r = requests.post('http://160.191.89.99:21568/chat', json=simple_msg, timeout=10)
        print(f'Status: {r.status_code}')
        if r.status_code == 200:
            data = r.json()
            print(f'Model: {data.get("model", "unknown")}')
            print(f'Response: {data.get("response", "")[:100]}...')
            return data.get("model", "unknown")
        else:
            print(f'Error: {r.text}')
            return None
    except Exception as e:
        print(f'Exception: {e}')
        return None

def test_complex_message():
    """Test câu phức tạp - should use DeepSeek"""
    complex_msg = {'message': 'hãy giải thích về sự ngẫu nhiên bất khả quy kết'}
    print('\n🔍 Testing complex message (should use DeepSeek)...')
    try:
        r = requests.post('http://160.191.89.99:21568/chat', json=complex_msg, timeout=30)
        print(f'Status: {r.status_code}')
        if r.status_code == 200:
            data = r.json()
            print(f'Model: {data.get("model", "unknown")}')
            print(f'Response: {data.get("response", "")[:100]}...')
            return data.get("model", "unknown")
        else:
            print(f'Error: {r.text}')
            return None
    except Exception as e:
        print(f'Exception: {e}')
        return None

if __name__ == "__main__":
    print("🚀 Testing VPS Gateway Routing Logic")
    print("=" * 50)
    
    simple_model = test_simple_message()
    complex_model = test_complex_message()
    
    print("\n📊 SUMMARY:")
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
