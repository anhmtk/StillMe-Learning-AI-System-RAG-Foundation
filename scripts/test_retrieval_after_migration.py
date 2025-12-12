#!/usr/bin/env python3
"""
Script to test RAG retrieval after migration to cosine distance.

This verifies that foundational knowledge can now be retrieved with low distance.
"""

import requests
import argparse
import sys
import json

# Ensure UTF-8 output for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def test_retrieval_after_migration(backend_url: str, query: str = "Do you track your own execution time?"):
    """
    Test RAG retrieval after migration to verify distance has improved.
    """
    print("="*60)
    print("Testing RAG Retrieval After Migration")
    print("="*60)
    print(f"Backend URL: {backend_url}\n")
    
    # Ensure URL has scheme
    if not backend_url.startswith("http://") and not backend_url.startswith("https://"):
        backend_url = "https://" + backend_url
        print(f"ℹ️  Added https:// scheme to URL: {backend_url}")
    
    print(f"Test Query: '{query}'")
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
            print("   (This is OK, continuing with chat test...)\n")
        
        # 2. Send chat request
        print(f"2. Sending chat request (timeout: 120s)...")
        print(f"   Query: {query}")
        
        response = requests.post(
            f"{backend_url}/api/chat/rag",
            json={
                "message": query,
                "use_rag": True,
                "context_limit": 5
            },
            timeout=120
        )
        
        print(f"\n3. Response received (status: {response.status_code})")
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            confidence_score = data.get("confidence_score")
            validation_result = data.get("validation_result", {})
            processing_steps = data.get("processing_steps", [])
            
            print(f"\n4. Analyzing response...")
            print(f"   Response length: {len(response_text)} characters")
            print(f"   Confidence score: {confidence_score}")
            print(f"   Validation passed: {validation_result.get('overall_passed')}")
            
            # Check processing steps for distance/similarity info
            print(f"\n5. Checking processing steps for distance metrics...")
            distance_found = False
            for step in processing_steps:
                step_lower = step.lower()
                if "distance" in step_lower or "similarity" in step_lower:
                    print(f"   📊 {step}")
                    distance_found = True
                if "high average distance" in step_lower:
                    print(f"   ⚠️  WARNING: {step}")
                if "foundational knowledge" in step_lower:
                    print(f"   ✅ {step}")
            
            if not distance_found:
                print("   ⚠️  No distance metrics found in processing steps")
                print("   💡 Check backend logs for detailed distance information")
            
            # Check for correct self-tracking statement
            correct_statement_found = (
                "StillMe tracks its own execution time" in response_text or
                "StillMe DOES track its own execution time" in response_text or
                "tôi có theo dõi thời gian thực thi của chính mình" in response_text.lower() or
                "TaskTracker" in response_text or
                "TimeEstimationEngine" in response_text
            )
            
            # Check for incorrect statement
            incorrect_statement_found = (
                "does not track" in response_text.lower() or
                "do not track" in response_text.lower() or
                "không theo dõi" in response_text.lower()
            )
            
            print(f"\n6. Response Quality Check:")
            if correct_statement_found:
                print("   ✅ Response correctly states StillMe tracks execution time")
            elif incorrect_statement_found:
                print("   ❌ Response incorrectly states StillMe does NOT track execution time")
            else:
                print("   ⚠️  Response is ambiguous about self-tracking")
            
            # Check for technical details
            technical_details_found = (
                "TaskTracker" in response_text and
                "TimeEstimationEngine" in response_text
            )
            
            if technical_details_found:
                print("   ✅ Response includes technical details (TaskTracker, TimeEstimationEngine)")
            else:
                print("   ⚠️  Response lacks technical details (may not have retrieved foundational knowledge)")
            
            print(f"\n7. Response preview (first 500 chars):")
            print("-" * 60)
            print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
            print("-" * 60)
            
            print("\n8. Test Summary:")
            print("-" * 60)
            if correct_statement_found and technical_details_found:
                print("   ✅ PASS: StillMe correctly identifies and explains self-tracking")
            elif correct_statement_found:
                print("   ⚠️  PARTIAL: Response may be correct but lacks detail")
            else:
                print("   ❌ FAIL: StillMe incorrectly denies self-tracking capability")
                print("   💡 Check backend logs for distance metrics and retrieval details")
            print("-" * 60)
        
        else:
            print(f"   ❌ Request failed with status code {response.status_code}")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.Timeout:
        print("\n⚠️  Request timeout after 120 seconds")
        print("   This could mean:")
        print("   - Backend is processing (RAG + validation takes time)")
        print("   - Backend is cold starting")
        print("   - Network latency")
    except requests.exceptions.RequestException as e:
        print(f"\n   ❌ Request error: {e}")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test RAG retrieval after migration to cosine distance.")
    parser.add_argument("--backend-url", required=True, help="Base URL of the StillMe backend (e.g., stillme-backend-production.up.railway.app)")
    parser.add_argument("--query", default="Do you track your own execution time?", help="The chat query to send.")
    args = parser.parse_args()
    
    test_retrieval_after_migration(args.backend_url, args.query)

