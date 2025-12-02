#!/usr/bin/env python3
"""
Test script for StillMe self-tracking query detection and response

Tests that StillMe correctly:
1. Detects "Do you track your own execution time?" as StillMe query
2. Retrieves foundational knowledge about self-tracking
3. Responds accurately about its self-tracking capabilities
"""

import requests
import argparse
import sys
import os
from typing import Dict, Any

# Ensure UTF-8 output for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


def test_self_tracking_query(backend_url: str, query: str = "Do you track your own execution time?"):
    """
    Test StillMe's response to self-tracking query.
    
    Args:
        backend_url: Base URL of StillMe backend
        query: Query to test (default: self-tracking question)
    """
    print("="*60)
    print("StillMe Self-Tracking Query Test")
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
            print("   (This is OK, continuing with chat test...)")
        
        # 2. Check StillMe query detection locally (for debugging)
        print("\n2. Checking StillMe query detection...")
        try:
            from backend.core.stillme_detector import detect_stillme_query
            is_stillme_query, matched_keywords = detect_stillme_query(query)
            print(f"   StillMe query detected: {is_stillme_query}")
            print(f"   Matched keywords: {matched_keywords}")
            
            if is_stillme_query:
                print("   ✅ Query correctly detected as StillMe query")
            else:
                print("   ⚠️  Query NOT detected as StillMe query - may not retrieve foundational knowledge")
        except Exception as e:
            print(f"   ⚠️  Could not test detection locally: {e}")
        
        # 3. Send chat request
        print(f"\n3. Sending chat request (timeout: 120s)...")
        print(f"   Query: {query}")
        
        response = requests.post(
            f"{backend_url}/api/chat/rag",
            json={
                "message": query,
                "use_rag": True,
                "context_limit": 3
            },
            timeout=120  # Longer timeout for complex processing
        )
        
        print(f"\n4. Response received (status: {response.status_code})")
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            confidence_score = data.get("confidence_score")
            validation_passed = data.get("validation_info", {}).get("overall_passed")
            processing_steps = data.get("processing_steps", [])
            
            print(f"\n5. Analyzing response...")
            print(f"   Response length: {len(response_text)} characters")
            print(f"   Confidence score: {confidence_score}")
            print(f"   Validation passed: {validation_passed}")
            
            # Check for correct answer indicators
            correct_indicators = [
                "yes", "i track", "stillme tracks", "stillme does track",
                "tasktracker", "timeestimationengine", "self-tracking",
                "execution time", "track.*execution", "theo dõi.*thực thi"
            ]
            
            incorrect_indicators = [
                "no.*track", "do not track", "cannot track", "don't track",
                "i do not track", "stillme does not track", "không.*theo dõi"
            ]
            
            has_correct = any(
                indicator.lower() in response_text.lower() 
                for indicator in correct_indicators
            )
            has_incorrect = any(
                indicator.lower() in response_text.lower() 
                for indicator in incorrect_indicators
            )
            
            # Check for foundational knowledge indicators
            has_foundational = any(
                keyword in response_text.lower() 
                for keyword in [
                    "tasktracker", "timeestimationengine", "track_task_execution",
                    "learning cycles", "validation processes", "historical performance"
                ]
            )
            
            print(f"\n6. Response Quality Check:")
            if has_correct and not has_incorrect:
                print("   ✅ Response correctly states StillMe tracks execution time")
            elif has_incorrect:
                print("   ❌ Response incorrectly states StillMe does NOT track execution time")
            else:
                print("   ⚠️  Response unclear about self-tracking capability")
            
            if has_foundational:
                print("   ✅ Response includes technical details (likely from foundational knowledge)")
            else:
                print("   ⚠️  Response lacks technical details (may not have retrieved foundational knowledge)")
            
            # Check processing steps for StillMe query detection
            stillme_detected_in_steps = any(
                "stillme query" in step.lower() or "foundational" in step.lower()
                for step in processing_steps
            )
            
            if stillme_detected_in_steps:
                print("   ✅ Processing steps indicate StillMe query was detected")
            else:
                print("   ⚠️  Processing steps don't show StillMe query detection")
            
            print(f"\n7. Response preview:")
            print("-" * 60)
            # Print first 1000 characters
            preview = response_text[:1000] + "..." if len(response_text) > 1000 else response_text
            print(preview)
            print("-" * 60)
            
            # Summary
            print(f"\n8. Test Summary:")
            print("-" * 60)
            if has_correct and not has_incorrect and has_foundational:
                print("   ✅ PASS: StillMe correctly answers about self-tracking")
            elif has_incorrect:
                print("   ❌ FAIL: StillMe incorrectly denies self-tracking capability")
            else:
                print("   ⚠️  PARTIAL: Response may be correct but lacks detail or clarity")
            print("-" * 60)
            
        else:
            print(f"   ❌ Request failed with status code {response.status_code}")
            print(f"   Response: {response.text}")
    
    except requests.exceptions.Timeout:
        print("\n⚠️  Request timeout after 120 seconds")
        print("   This could mean:")
        print("   - Backend is processing (RAG + validation + estimation takes time)")
        print("   - Backend is cold starting")
        print("   - Network latency")
        print("\n   Try:")
        print("   1. Wait a few seconds and retry")
        print("   2. Check backend logs on Railway")
        print("   3. Test with a simpler query first")
    except requests.exceptions.RequestException as e:
        print(f"\n   ❌ Request error: {e}")
    
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test StillMe's self-tracking query detection and response."
    )
    parser.add_argument(
        "--backend-url",
        required=True,
        help="Base URL of the StillMe backend (e.g., stillme-backend-production.up.railway.app)"
    )
    parser.add_argument(
        "--query",
        default="Do you track your own execution time?",
        help="The query to test (default: self-tracking question)"
    )
    args = parser.parse_args()
    
    test_self_tracking_query(args.backend_url, args.query)

