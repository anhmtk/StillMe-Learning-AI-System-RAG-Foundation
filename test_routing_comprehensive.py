#!/usr/bin/env python3
"""
Comprehensive routing test - local version
"""
import requests
import json
import time

def test_simple_messages():
    """Test multiple simple messages"""
    print("🔍 Testing simple messages (should use Gemma)...")
    simple_messages = ["xin chào", "2+2=?", "hello", "ping", "chào buổi sáng"]
    results = []
    
    for msg in simple_messages:
        print(f"\n==> SEND: {msg}")
        try:
            response = requests.post(
                'http://160.191.89.99:21568/chat',
                json={'message': msg, 'session_id': 'router-test'},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                model = data.get('model', 'unknown')
                text = data.get('response', '')[:100]
                print(f"Model: {model}")
                print(f"Response: {text}...")
                results.append({'message': msg, 'model': model, 'success': True})
            else:
                print(f"Error: {response.text}")
                results.append({'message': msg, 'model': None, 'success': False})
        except Exception as e:
            print(f"Exception: {e}")
            results.append({'message': msg, 'model': None, 'success': False})
    
    return results

def test_complex_messages():
    """Test complex messages"""
    print("\n🔍 Testing complex messages (should use DeepSeek)...")
    complex_messages = [
        "Hãy viết đoạn code Python đọc CSV, tính trung bình và in kết quả theo cột.",
        "Giải thích thuật toán quicksort và implement bằng Python",
        "Phân tích ưu nhược điểm của microservices architecture"
    ]
    results = []
    
    for msg in complex_messages:
        print(f"\n==> SEND: {msg}")
        try:
            response = requests.post(
                'http://160.191.89.99:21568/chat',
                json={'message': msg, 'session_id': 'router-test'},
                timeout=30
            )
            if response.status_code == 200:
                data = response.json()
                model = data.get('model', 'unknown')
                text = data.get('response', '')[:100]
                print(f"Model: {model}")
                print(f"Response: {text}...")
                results.append({'message': msg, 'model': model, 'success': True})
            else:
                print(f"Error: {response.text}")
                results.append({'message': msg, 'model': None, 'success': False})
        except Exception as e:
            print(f"Exception: {e}")
            results.append({'message': msg, 'model': None, 'success': False})
    
    return results

def analyze_results(simple_results, complex_results):
    """Analyze test results"""
    print("\n📊 ANALYSIS:")
    print("=" * 50)
    
    # Simple messages analysis
    simple_models = [r['model'] for r in simple_results if r['success']]
    simple_success_rate = len([r for r in simple_results if r['success']]) / len(simple_results) * 100
    
    print(f"Simple messages success rate: {simple_success_rate:.1f}%")
    print(f"Simple message models: {set(simple_models)}")
    
    if 'deepseek-chat' in simple_models:
        print("❌ PROBLEM: Simple messages using DeepSeek (expensive)")
    elif any('gemma' in str(m).lower() for m in simple_models):
        print("✅ GOOD: Simple messages using Gemma (local)")
    
    # Complex messages analysis
    complex_models = [r['model'] for r in complex_results if r['success']]
    complex_success_rate = len([r for r in complex_results if r['success']]) / len(complex_results) * 100
    
    print(f"\nComplex messages success rate: {complex_success_rate:.1f}%")
    print(f"Complex message models: {set(complex_models)}")
    
    if 'deepseek-chat' in complex_models:
        print("✅ GOOD: Complex messages using DeepSeek")
    elif complex_success_rate < 50:
        print("❌ PROBLEM: Complex messages failing/timeout")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    if simple_success_rate > 80 and complex_success_rate > 50:
        print("✅ Gateway is working but routing needs optimization")
    elif simple_success_rate < 50:
        print("❌ Gateway has serious issues")
    else:
        print("⚠️ Gateway partially working, needs fixes")

if __name__ == "__main__":
    print("🚀 Comprehensive VPS Gateway Routing Test")
    print("=" * 60)
    
    # Test simple messages
    simple_results = test_simple_messages()
    
    # Test complex messages
    complex_results = test_complex_messages()
    
    # Analyze results
    analyze_results(simple_results, complex_results)
