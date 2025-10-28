#!/usr/bin/env python3
"""
Test script để debug chat dashboard
"""
import requests
import json
import time

def test_api_server():
    """Test API server response"""
    print("🔍 Testing API Server...")
    
    try:
        response = requests.post(
            'http://127.0.0.1:8000/dev-agent/bridge',
            json={
                'prompt': 'javascript là gì',
                'mode': 'fast',
                'system_prompt': 'Test',
                'response_format': 'text',
                'force_json': False
            },
            timeout=10
        )
        
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {response.json()}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_dashboard():
    """Test dashboard accessibility"""
    print("\n🔍 Testing Dashboard...")
    
    try:
        response = requests.get('http://localhost:8529', timeout=10)
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Content length: {len(response.text)}")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 StillMe Chat Debug Test")
    print("=" * 50)
    
    # Test API server
    api_ok = test_api_server()
    
    # Test dashboard
    dashboard_ok = test_dashboard()
    
    print("\n📋 SUMMARY:")
    print(f"API Server: {'✅ OK' if api_ok else '❌ FAIL'}")
    print(f"Dashboard: {'✅ OK' if dashboard_ok else '❌ FAIL'}")
    
    if api_ok and dashboard_ok:
        print("\n🎉 All systems working! Try refreshing browser with Ctrl+F5")
    else:
        print("\n❌ Some systems not working. Check logs above.")
