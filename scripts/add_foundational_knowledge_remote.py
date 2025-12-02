#!/usr/bin/env python3
"""
Script to add foundational knowledge to RAG on Railway production via API endpoint.

This script calls the admin endpoint to trigger foundational knowledge update remotely.
"""

import requests
import argparse
import sys

# Ensure UTF-8 output for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


def add_foundational_knowledge_remote(backend_url: str):
    """
    Add foundational knowledge to RAG on Railway via API endpoint.
    
    Args:
        backend_url: Base URL of StillMe backend
    """
    print("="*60)
    print("StillMe Foundational Knowledge - Remote Update")
    print("="*60)
    print(f"Backend URL: {backend_url}\n")
    
    # Ensure URL has scheme
    if not backend_url.startswith("http://") and not backend_url.startswith("https://"):
        backend_url = "https://" + backend_url
        print(f"ℹ️  Added https:// scheme to URL: {backend_url}")
    
    endpoint = f"{backend_url}/api/admin/foundational-knowledge/add"
    
    print(f"Endpoint: {endpoint}")
    print("-" * 60)
    
    try:
        # 1. Test backend connectivity
        print("\n1. Testing backend connectivity...")
        try:
            health_response = requests.get(
                f"{backend_url}/health",
                timeout=10
            )
            if health_response.status_code == 200:
                print("   ✅ Backend is accessible")
            else:
                print(f"   ⚠️  Backend returned status {health_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Health check failed: {e}")
            print("   (This is OK, continuing with request...)")
        
        # 2. Call admin endpoint to add foundational knowledge
        print(f"\n2. Calling admin endpoint to add foundational knowledge...")
        print(f"   This may take 30-60 seconds (embedding generation)...")
        
        response = requests.post(
            endpoint,
            timeout=120  # Longer timeout for embedding generation
        )
        
        print(f"\n3. Response received (status: {response.status_code})")
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            message = data.get("message")
            timestamp = data.get("timestamp")
            
            print(f"\n4. Result:")
            print(f"   Status: {status}")
            print(f"   Message: {message}")
            if timestamp:
                print(f"   Timestamp: {timestamp}")
            
            if status == "success":
                print("\n   ✅ Foundational knowledge added successfully!")
                print("\n   Next steps:")
                print("   1. Clear LLM cache to force regeneration:")
                print(f"      python scripts/clear_cache_railway.ps1 -Pattern llm:response:*")
                print("   2. Test StillMe response:")
                print(f"      python scripts/test_self_tracking_query.py --backend-url {backend_url}")
            else:
                print("\n   ⚠️  Request completed but status is not 'success'")
        else:
            print(f"\n   ❌ Request failed with status code {response.status_code}")
            try:
                error_data = response.json()
                detail = error_data.get("detail", response.text)
                print(f"   Error: {detail}")
            except:
                print(f"   Response: {response.text}")
    
    except requests.exceptions.Timeout:
        print("\n⚠️  Request timeout after 120 seconds")
        print("   This could mean:")
        print("   - Backend is processing (embedding generation takes time)")
        print("   - Backend is cold starting")
        print("   - Network latency")
        print("\n   Try:")
        print("   1. Wait a few seconds and retry")
        print("   2. Check backend logs on Railway")
    except requests.exceptions.RequestException as e:
        print(f"\n   ❌ Request error: {e}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Add foundational knowledge to RAG on Railway production via API endpoint."
    )
    parser.add_argument(
        "--backend-url",
        required=True,
        help="Base URL of the StillMe backend (e.g., stillme-backend-production.up.railway.app)"
    )
    args = parser.parse_args()
    
    add_foundational_knowledge_remote(args.backend_url)

