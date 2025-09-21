#!/usr/bin/env python3
"""
Test VPS Gateway directly and check configuration
"""
import requests
import json
import time

def test_vps_direct():
    base_url = "http://160.191.89.99:21568"
    
    print("🔍 Testing VPS Gateway directly...")
    
    # Test 1: Health check
    print("\n1️⃣ Health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Gateway is running")
        else:
            print(f"   ❌ Gateway error: {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Gateway unreachable: {e}")
        return
    
    # Test 2: Chat with probe message
    print("\n2️⃣ Testing chat with probe message...")
    try:
        payload = {
            "message": "probe"
        }
        response = requests.post(
            f"{base_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Model: {data.get('model', 'unknown')}")
            print(f"   Response field: {data.get('response', 'NOT_FOUND')}")
            print(f"   Text field: {data.get('text', 'NOT_FOUND')}")
            print(f"   Output field: {data.get('output', 'NOT_FOUND')}")
            
            # Check if it's placeholder
            model = data.get('model', '')
            if 'placeholder' in model.lower():
                print(f"   🚨 PLACEHOLDER MODE DETECTED: {model}")
                print(f"   📝 Full response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return False
            else:
                print(f"   ✅ REAL LLM MODE: {model}")
                return True
        else:
            print(f"   ❌ Chat failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Chat error: {e}")
        return False

def check_ai_server():
    """Check if AI server is accessible"""
    print("\n3️⃣ Checking AI server...")
    try:
        response = requests.get("http://160.191.89.99:80/health", timeout=10)
        print(f"   AI Server Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ AI Server is running")
            return True
        else:
            print(f"   ❌ AI Server error: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ AI Server unreachable: {e}")
        return False

if __name__ == "__main__":
    print("🚀 VPS Gateway Configuration Check")
    print("=" * 50)
    
    # Test gateway
    gateway_ok = test_vps_direct()
    
    # Test AI server
    ai_server_ok = check_ai_server()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"   Gateway: {'✅ OK' if gateway_ok else '❌ PLACEHOLDER'}")
    print(f"   AI Server: {'✅ OK' if ai_server_ok else '❌ ERROR'}")
    
    if not gateway_ok:
        print("\n🔧 NEXT STEPS:")
        print("   1. SSH to VPS: ssh root@160.191.89.99")
        print("   2. Check gateway config: cat /opt/stillme/real_stillme_gateway.py | grep -E '(ROUTING|PLACEHOLDER|MODEL)'")
        print("   3. Check environment: env | grep -E '(ROUTING|PLACEHOLDER|MODEL|API_KEY)'")
        print("   4. Enable real LLM by setting ROUTING_MODE=live or USE_PLACEHOLDER=false")
        print("   5. Restart services: systemctl restart stillme-gateway stillme-ai-server")
