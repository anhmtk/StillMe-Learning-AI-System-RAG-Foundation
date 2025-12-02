#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Chat Integration Test for Time Estimation

Tests if StillMe responds with time estimates when asked about duration.

Usage:
    python scripts/test_chat_time_estimation.py [--backend-url URL] [--query "your query"]
"""

import sys
import os
import argparse
import requests
import json
from pathlib import Path
from typing import Optional

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))


def test_chat_time_estimation(backend_url: str, query: Optional[str] = None):
    """Test chat integration with time estimation"""
    
    # Auto-add https:// if no scheme provided
    if not backend_url.startswith(("http://", "https://")):
        backend_url = f"https://{backend_url}"
    
    print("="*60)
    print("StillMe Chat Time Estimation Test")
    print("="*60)
    print(f"Backend URL: {backend_url}")
    print()
    
    # Default test queries
    test_queries = [
        "How long will it take to learn 100 articles?",
        "Bao lau de hoc 100 bai viet?",
    ]
    
    if query:
        test_queries = [query]
    
    for i, query in enumerate(test_queries, 1):
        print(f"Test {i}/{len(test_queries)}: '{query}'")
        print("-" * 60)
        
        try:
            # First, test if backend is accessible
            print("1. Testing backend connectivity...")
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
            
            # Check intent detection first
            print(f"\n2. Checking intent detection...")
            from backend.core.time_estimation_intent import detect_time_estimation_intent
            is_time_estimation, task_desc = detect_time_estimation_intent(query)
            print(f"   Time estimation intent: {is_time_estimation}")
            if task_desc:
                print(f"   Task description: {task_desc}")
            
            # Send chat request
            print(f"\n3. Sending chat request (timeout: 120s)...")
            print(f"   Query: {query}")
            
            response = requests.post(
                f"{backend_url}/api/chat/rag",
                json={
                    "message": query,
                    "use_rag": True,
                    "context_limit": 3
                },
                timeout=120  # Increased timeout for complex processing
            )
            
            print(f"\n4. Response received (status: {response.status_code})")
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                
                print(f"\n5. Analyzing response...")
                print(f"   Response length: {len(response_text)} characters")
                
                # Check if time estimate is in response
                has_estimate = (
                    "estimate" in response_text.lower() or
                    "ước tính" in response_text.lower() or
                    "Time Estimate" in response_text or
                    "Ước tính thời gian" in response_text or
                    "⏱️" in response_text
                )
                
                if has_estimate:
                    print("   ✅ Time estimate found in response!")
                    print("\n5. Response preview:")
                    print("-" * 60)
                    # Find time estimate section
                    if "⏱️" in response_text:
                        estimate_section = response_text.split("⏱️")[1][:500]
                        print(f"⏱️{estimate_section}...")
                    else:
                        # Show last 500 chars (where estimate usually is)
                        print(response_text[-500:])
                    print("-" * 60)
                else:
                    print("   ⚠️  Time estimate NOT found in response")
                    if is_time_estimation:
                        print("   ⚠️  Intent was detected but estimate not in response - possible backend issue")
                    print("\n6. Full response preview:")
                    print("-" * 60)
                    print(response_text[:500])
                    if len(response_text) > 500:
                        print("...")
                        print(response_text[-200:])
                    print("-" * 60)
                
                # Check for other indicators
                has_ai_identity = (
                    "AI system" in response_text or
                    "hệ thống AI" in response_text or
                    "statistical model" in response_text.lower()
                )
                
                if has_ai_identity:
                    print("\n   ✅ AI identity statement found")
                else:
                    print("\n   ⚠️  AI identity statement not found")
                
                # Show confidence and validation info if available
                confidence = data.get("confidence_score")
                if confidence:
                    print(f"\n   Confidence score: {confidence:.2f}")
                
                validation_info = data.get("validation_info")
                if validation_info:
                    print(f"   Validation: {validation_info.get('passed', 'N/A')}")
                
            else:
                print(f"\n❌ Request failed with status {response.status_code}")
                print(f"Response: {response.text[:500]}")
                
        except requests.exceptions.Timeout as e:
            print(f"\n⚠️  Request timeout after 120 seconds")
            print(f"   This could mean:")
            print(f"   - Backend is processing (RAG + validation + estimation takes time)")
            print(f"   - Backend is cold starting")
            print(f"   - Network latency")
            print(f"\n   Try:")
            print(f"   1. Wait a few seconds and retry")
            print(f"   2. Check backend logs on Railway")
            print(f"   3. Test with a simpler query first")
            
        except requests.exceptions.RequestException as e:
            print(f"\n❌ Request error: {e}")
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*60 + "\n")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Test Chat Time Estimation")
    parser.add_argument(
        "--backend-url",
        type=str,
        default="stillme-backend-production.up.railway.app",
        help="Backend URL (default: stillme-backend-production.up.railway.app)"
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Custom query to test (optional)"
    )
    
    args = parser.parse_args()
    
    test_chat_time_estimation(args.backend_url, args.query)


if __name__ == "__main__":
    main()

