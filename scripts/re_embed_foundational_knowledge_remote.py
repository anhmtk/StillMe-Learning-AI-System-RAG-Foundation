#!/usr/bin/env python3
"""
Script to remotely re-embed foundational knowledge via API endpoint.

This calls the /api/admin/foundational-knowledge/re-embed endpoint
to re-embed all CRITICAL_FOUNDATION documents with the current model.
"""

import requests
import argparse
import sys
import os
import time

# Ensure UTF-8 output for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


def re_embed_foundational_knowledge_remote(backend_url: str, api_key: str = None):
    """
    Re-embed foundational knowledge remotely via API endpoint.
    
    Args:
        backend_url: Base URL of the StillMe backend (e.g., stillme-backend-production.up.railway.app)
        api_key: API key for authentication (optional, can be set via STILLME_API_KEY env var)
    """
    print("="*60)
    print("StillMe Foundational Knowledge - Remote Re-embedding")
    print("="*60)
    print(f"Backend URL: {backend_url}\n")
    
    # Ensure URL has scheme
    if not backend_url.startswith("http://") and not backend_url.startswith("https://"):
        backend_url = "https://" + backend_url
        print(f"ℹ️  Added https:// scheme to URL: {backend_url}")
    
    endpoint = f"{backend_url}/api/admin/foundational-knowledge/re-embed"
    
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
    
    # 2. Get API key from environment or prompt
    if not api_key:
        api_key = os.getenv("STILLME_API_KEY")
        if not api_key:
            print("\n   ⚠️  STILLME_API_KEY not found in environment variables")
            print("   This endpoint requires API key authentication.")
            print("   Please set STILLME_API_KEY environment variable or provide it via --api-key")
            api_key = input("   Enter API key (or press Enter to skip authentication): ").strip()
            if not api_key:
                print("   ⚠️  No API key provided - request may fail if authentication is required")
    
    # 3. Call admin endpoint to re-embed foundational knowledge
    print(f"\n2. Calling admin endpoint to re-embed foundational knowledge...")
    print(f"   This may take 30-60 seconds (re-embedding all CRITICAL_FOUNDATION documents)...")
    
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
        print(f"   Using API key authentication")
    
    try:
        response = requests.post(
            endpoint,
            headers=headers,
            timeout=180  # Longer timeout for re-embedding (may take time)
        )
        
        print(f"\n3. Response received (status: {response.status_code})")
        
        if response.status_code == 200:
            data = response.json()
            status = data.get("status")
            message = data.get("message")
            documents_found = data.get("documents_found", 0)
            documents_re_embedded = data.get("documents_re_embedded", 0)
            model_used = data.get("model_used", "unknown")
            test_results = data.get("test_results", {})
            
            print(f"\n4. Result:")
            print(f"   Status: {status}")
            print(f"   Message: {message}")
            print(f"   Documents found: {documents_found}")
            print(f"   Documents re-embedded: {documents_re_embedded}")
            print(f"   Model used: {model_used}")
            
            if test_results:
                print(f"\n5. Test Retrieval Results:")
                test_status = test_results.get("status", "unknown")
                print(f"   Status: {test_status}")
                
                if "distance_range" in test_results:
                    dist_range = test_results["distance_range"]
                    print(f"   Distance range: {dist_range.get('min', 'N/A')} - {dist_range.get('max', 'N/A')}")
                    print(f"   Average distance: {dist_range.get('average', 'N/A')}")
                
                if "estimated_similarity" in test_results:
                    print(f"   Estimated similarity: {test_results['estimated_similarity']}")
                
                if "documents_retrieved" in test_results:
                    print(f"   Documents retrieved: {test_results['documents_retrieved']}")
                
                if test_status == "good":
                    print("   ✅ Distance looks good! Documents should be retrievable")
                elif test_status == "moderate":
                    print("   ⚠️  Distance is moderate - may need lower threshold")
                elif test_status == "high":
                    print("   ⚠️  Distance is still high - may need to check embedding model")
            
            if data.get("errors"):
                print(f"\n6. Errors:")
                for error in data["errors"]:
                    print(f"   ⚠️  {error}")
            
            print("\n" + "="*60)
            if status == "success":
                print("✅ Foundational knowledge re-embedded successfully!")
            elif status == "partial":
                print("⚠️  Foundational knowledge partially re-embedded (some errors occurred)")
            else:
                print("❌ Foundational knowledge re-embedding failed")
            
            print("\nNext steps:")
            print("1. Clear LLM cache to force regeneration:")
            print("   python scripts/clear_cache_railway.ps1 -Pattern llm:response:*")
            print("2. Test StillMe response:")
            print("   python scripts/test_self_tracking_query.py --backend-url " + backend_url)
            print("="*60)
        else:
            print(f"   ❌ Request failed with status code {response.status_code}")
            print(f"   Response: {response.text}")
            print("\n" + "="*60)
            print("❌ Foundational knowledge re-embedding FAILED.")
            print("Please check backend logs for errors and ensure API key is correct.")
            print("="*60)
    except requests.exceptions.Timeout:
        print("\n⚠️  Request timeout after 180 seconds")
        print("   This could mean:")
        print("   - Backend is processing (re-embedding takes time)")
        print("   - Backend is cold starting")
        print("   - Network latency")
        print("\n   Try:")
        print("   1. Wait a few seconds and retry")
        print("   2. Check backend logs on Railway")
        print("   3. Ensure STILLME_API_KEY is set correctly")
    except requests.exceptions.RequestException as e:
        print(f"\n   ❌ Request error: {e}")
        print("\n" + "="*60)
        print("❌ Foundational knowledge re-embedding FAILED.")
        print("Please check network connectivity and backend status.")
        print("="*60)
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remotely re-embed StillMe foundational knowledge in RAG.")
    parser.add_argument("--backend-url", required=True, help="Base URL of the StillMe backend (e.g., stillme-backend-production.up.railway.app)")
    parser.add_argument("--api-key", help="API key for authentication (e.g., X-API-Key header)")
    args = parser.parse_args()
    
    re_embed_foundational_knowledge_remote(args.backend_url, args.api_key)

