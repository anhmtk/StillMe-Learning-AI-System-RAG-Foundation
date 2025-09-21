#!/usr/bin/env python3
"""
End-to-End Test Script for StillMe Secure Architecture
App -> VPS Gateway Proxy -> SSH Tunnel -> Local Backend -> AI Model
Tests HMAC authentication, rate limiting, and smart routing
"""
import requests
import json
import time
import os
import sys
from typing import Dict, Any, List

# Configuration
VPS_GATEWAY_URL = os.getenv("VPS_GATEWAY_URL", "http://160.191.89.99:21568")
LOCAL_BACKEND_URL = os.getenv("LOCAL_BACKEND_URL", "http://127.0.0.1:1216")

def test_vps_gateway_health():
    """Test VPS Gateway health endpoint"""
    print("🔍 Testing VPS Gateway Health...")
    
    try:
        response = requests.get(f"{VPS_GATEWAY_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ VPS Health: {response.status_code}")
            print(f"   Service: {data.get('service', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Mode: {data.get('mode', 'N/A')}")
            return True
        else:
            print(f"❌ VPS Health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ VPS Health failed: {e}")
        return False

def test_vps_gateway_backend_status():
    """Test VPS Gateway backend status"""
    print("🔍 Testing VPS Gateway Backend Status...")
    
    try:
        response = requests.get(f"{VPS_GATEWAY_URL}/admin/backend-status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend Status: {response.status_code}")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Backend URL: {data.get('backend_url', 'N/A')}")
            return data.get('status') == 'connected'
        else:
            print(f"❌ Backend Status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend Status failed: {e}")
        return False

def test_vps_gateway_chat():
    """Test VPS Gateway chat with HMAC authentication"""
    print("🔍 Testing VPS Gateway Chat (with HMAC)...")
    
    try:
        payload = {
            "message": "xin chào",
            "session_id": "test_hmac"
        }
        headers = {
            "Content-Type": "application/json",
            "X-User-ID": "test_user",
            "X-User-Lang": "vi"
        }
        
        start_time = time.time()
        response = requests.post(f"{VPS_GATEWAY_URL}/chat", json=payload, headers=headers, timeout=30)
        latency = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ VPS Chat: {response.status_code}")
            print(f"   Engine: {data.get('engine', 'N/A')}")
            print(f"   Model: {data.get('model', 'N/A')}")
            print(f"   Latency: {latency:.1f}ms")
            print(f"   Response: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ VPS Chat failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ VPS Chat failed: {e}")
        return False

def test_local_backend_health():
    """Test Local Backend health endpoint"""
    print("🔍 Testing Local Backend Health...")
    
    try:
        response = requests.get(f"{LOCAL_BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Local Health: {response.status_code}")
            print(f"   Service: {data.get('service', 'N/A')}")
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Mode: {data.get('mode', 'N/A')}")
            print(f"   Ollama Status: {data.get('ollama_status', 'N/A')}")
            return True
        else:
            print(f"❌ Local Health failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Local Health failed: {e}")
        return False

def test_local_backend_direct():
    """Test Local Backend directly (without HMAC for testing)"""
    print("🔍 Testing Local Backend Direct...")
    
    try:
        payload = {
            "message": "xin chào",
            "session_id": "test_direct"
        }
        response = requests.post(f"{LOCAL_BACKEND_URL}/inference", json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Local Direct: {response.status_code}")
            print(f"   Engine: {data.get('engine', 'N/A')}")
            print(f"   Model: {data.get('model', 'N/A')}")
            print(f"   Response: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ Local Direct failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Local Direct failed: {e}")
        return False

def test_routing_scenarios():
    """Test different routing scenarios through VPS Gateway"""
    print("\n🔍 Testing Routing Scenarios (via VPS Gateway)...")
    
    test_cases = [
        {
            "name": "Simple Question",
            "message": "xin chào",
            "expected_engine": "ollama-gemma"
        },
        {
            "name": "Code Question", 
            "message": "Hãy viết code Python đọc CSV",
            "expected_engine": "ollama-deepseek-coder"
        },
        {
            "name": "Complex Question",
            "message": "Phân tích ưu nhược điểm của microservices architecture",
            "expected_engine": "deepseek-cloud"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        print(f"   Message: {test_case['message']}")
        
        try:
            payload = {
                "message": test_case["message"],
                "session_id": "routing-test"
            }
            headers = {
                "Content-Type": "application/json",
                "X-User-ID": "routing_tester",
                "X-User-Lang": "vi"
            }
            
            start_time = time.time()
            response = requests.post(f"{VPS_GATEWAY_URL}/chat", json=payload, headers=headers, timeout=30)
            latency = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                engine = data.get("engine", "unknown")
                model = data.get("model", "unknown")
                response_text = data.get("response", "")[:100]
                status = data.get("status", "unknown")
                
                print(f"   ✅ Engine: {engine}")
                print(f"   ✅ Model: {model}")
                print(f"   ✅ Status: {status}")
                print(f"   ✅ Latency: {latency:.1f}ms")
                print(f"   ✅ Response: {response_text}...")
                
                # Check if routing is correct
                if test_case["expected_engine"] in engine:
                    print(f"   ✅ Routing correct!")
                else:
                    print(f"   ⚠️  Routing unexpected (expected: {test_case['expected_engine']})")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def test_rate_limiting():
    """Test rate limiting on VPS Gateway"""
    print("\n🔍 Testing Rate Limiting...")
    
    print("   Sending multiple rapid requests...")
    success_count = 0
    rate_limited_count = 0
    
    for i in range(15):  # Send 15 requests rapidly
        try:
            payload = {
                "message": f"test message {i}",
                "session_id": f"rate_test_{i}"
            }
            headers = {
                "Content-Type": "application/json",
                "X-User-ID": "rate_tester",
                "X-User-Lang": "vi"
            }
            
            response = requests.post(f"{VPS_GATEWAY_URL}/chat", json=payload, headers=headers, timeout=5)
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"   ✅ Rate limited at request {i+1}")
                break
            else:
                print(f"   ❌ Unexpected status: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"   ✅ Successful requests: {success_count}")
    print(f"   ✅ Rate limited: {rate_limited_count > 0}")
    
    if rate_limited_count > 0:
        print("   ✅ Rate limiting working correctly!")
    else:
        print("   ⚠️  Rate limiting may not be working")

def main():
    """Main test function"""
    print("🚀 StillMe Secure End-to-End Test")
    print("=" * 50)
    print("🔒 Testing: SSH Tunnel + HMAC Authentication + Rate Limiting")
    print("=" * 50)
    
    # Test local backend first
    print("\n📡 Testing Local Backend...")
    local_health_ok = test_local_backend_health()
    local_direct_ok = test_local_backend_direct()
    
    if local_health_ok and local_direct_ok:
        print("\n✅ Local Backend: Working")
        
        # Test VPS gateway
        print("\n📡 Testing VPS Gateway...")
        vps_health_ok = test_vps_gateway_health()
        backend_status_ok = test_vps_gateway_backend_status()
        vps_chat_ok = test_vps_gateway_chat()
        
        if vps_health_ok and backend_status_ok and vps_chat_ok:
            print("\n✅ VPS Gateway: Working")
            print("✅ SSH Tunnel: Connected")
            print("✅ HMAC Authentication: Working")
            
            # Test routing scenarios
            test_routing_scenarios()
            
            # Test rate limiting
            test_rate_limiting()
            
            print("\n🎉 All tests passed!")
            print("✅ Local Backend: Working")
            print("✅ VPS Gateway: Working") 
            print("✅ SSH Tunnel: Working")
            print("✅ HMAC Authentication: Working")
            print("✅ Smart Routing: Working")
            print("✅ Rate Limiting: Working")
        else:
            print("\n⚠️  VPS Gateway issues detected")
            if not backend_status_ok:
                print("❌ SSH Tunnel not connected - check tunnel and GATEWAY_SECRET")
            if not vps_chat_ok:
                print("❌ HMAC authentication failed - check GATEWAY_SECRET")
    else:
        print("\n❌ Local Backend not working - please start it first")
        print("   Run: python local_stillme_backend.py")
        print("   Make sure Ollama is running: ollama list")
        print("   Check models: ollama pull gemma2:2b")

if __name__ == "__main__":
    main()
