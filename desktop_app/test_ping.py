#!/usr/bin/env python3
"""
Test script to ping StillMe VPS server
Usage: python test_ping.py [base_url]
"""

import sys
import json
import time
import requests
from datetime import datetime

def test_health(base_url):
    """Test health endpoint"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Health check failed: {e}")

def test_chat(base_url):
    """Test chat endpoint"""
    try:
        payload = {
            "message": "Hello StillMe! This is a test from desktop app.",
            "session_id": f"test-session-{int(time.time())}",
            "metadata": {
                "persona": "assistant",
                "language": "en",
                "debug": True,
            }
        }
        
        response = requests.post(
            f"{base_url}/chat",
            json=payload,
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Chat request failed: {e}")

def main():
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://160.191.89.99:21568"
    
    print("🔍 Testing StillMe VPS Connection")
    print("=================================")
    print(f"Base URL: {base_url}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Test health endpoint
        print("📡 Testing health endpoint...")
        health_response = test_health(base_url)
        print(f"✅ Health check: {health_response.get('status', 'unknown')}")
        print()
        
        # Test chat endpoint
        print("💬 Testing chat endpoint...")
        chat_response = test_chat(base_url)
        
        # Extract response text
        response_text = chat_response.get('response', chat_response.get('text', 'No response'))
        print(f"✅ Chat response: {response_text[:50]}...")
        print()
        
        # Display response details
        print("📊 Response Details:")
        print(f"  - Model: {chat_response.get('model', 'N/A')}")
        print(f"  - Latency: {chat_response.get('latency_ms', 'N/A')}ms")
        
        usage = chat_response.get('usage', {})
        if usage:
            print(f"  - Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
            print(f"  - Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
            print(f"  - Total Tokens: {usage.get('total_tokens', 'N/A')}")
        
        cost = chat_response.get('cost_estimate_usd')
        if cost is not None:
            print(f"  - Cost: ${cost:.4f}")
        
        routing = chat_response.get('routing', {})
        if routing:
            print(f"  - Selected Model: {routing.get('selected', 'N/A')}")
            candidates = routing.get('candidates', [])
            if candidates:
                print(f"  - Available Models: {', '.join(candidates)}")
        
        safety = chat_response.get('safety', {})
        if safety:
            filtered = safety.get('filtered', False)
            flags = safety.get('flags', [])
            print(f"  - Filtered: {filtered}")
            if flags:
                print(f"  - Safety Flags: {', '.join(flags)}")
        
        print()
        print("🎉 All tests passed! Server is ready for desktop app.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
