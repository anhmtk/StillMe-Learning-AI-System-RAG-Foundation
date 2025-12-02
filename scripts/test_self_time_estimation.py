#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test StillMe's Self-Time Estimation Awareness

Tests if StillMe:
1. Can detect time estimation queries
2. Provides time estimates based on historical data
3. Shows self-awareness about being AI and tracking its own performance
4. Mentions its self-tracking capability

Usage:
    python scripts/test_self_time_estimation.py [--backend-url URL]
"""

import sys
import os
import argparse
import requests
import json
from pathlib import Path
from typing import Optional, List, Dict

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))


def test_time_estimation_query(backend_url: str, query: str, expected_features: List[str]) -> Dict[str, any]:
    """Test a single time estimation query"""
    
    # Auto-add https:// if no scheme provided
    if not backend_url.startswith(("http://", "https://")):
        backend_url = f"https://{backend_url}"
    
    print(f"\n{'='*60}")
    print(f"Testing: '{query}'")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{backend_url}/api/chat/rag",
            json={
                "message": query,
                "use_rag": True,
                "context_limit": 3
            },
            timeout=120
        )
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:200]}"
            }
        
        data = response.json()
        response_text = data.get("response", "")
        
        # Check for expected features
        results = {
            "query": query,
            "success": True,
            "response_length": len(response_text),
            "features_found": {},
            "time_estimate_found": False,
            "self_awareness_found": False,
            "historical_data_mentioned": False,
            "ai_identity_mentioned": False
        }
        
        # Check for time estimate
        time_estimate_indicators = [
            "⏱️",
            "Time Estimate",
            "Ước tính thời gian",
            "estimate",
            "ước tính",
            "minutes",
            "phút",
            "hours",
            "giờ"
        ]
        results["time_estimate_found"] = any(
            indicator in response_text for indicator in time_estimate_indicators
        )
        
        # Check for self-awareness
        self_awareness_indicators = [
            "historical performance",
            "hiệu suất lịch sử",
            "tracks my own",
            "theo dõi",
            "self-aware",
            "tự nhận thức",
            "AI system",
            "hệ thống AI",
            "statistical model",
            "mô hình thống kê"
        ]
        results["self_awareness_found"] = any(
            indicator in response_text.lower() for indicator in self_awareness_indicators
        )
        
        # Check for historical data mention
        historical_indicators = [
            "historical",
            "lịch sử",
            "past",
            "trước đây",
            "similar tasks",
            "nhiệm vụ tương tự",
            "based on",
            "dựa trên"
        ]
        results["historical_data_mentioned"] = any(
            indicator in response_text.lower() for indicator in historical_indicators
        )
        
        # Check for AI identity
        ai_identity_indicators = [
            "I'm an AI",
            "Tôi là AI",
            "I am an AI",
            "mình là AI",
            "AI system",
            "hệ thống AI",
            "statistical model",
            "mô hình thống kê"
        ]
        results["ai_identity_mentioned"] = any(
            indicator in response_text.lower() for indicator in ai_identity_indicators
        )
        
        # Check expected features
        for feature in expected_features:
            if feature in response_text.lower():
                results["features_found"][feature] = True
            else:
                results["features_found"][feature] = False
        
        # Print results
        print(f"✅ Response received ({len(response_text)} chars)")
        print(f"\n📊 Feature Detection:")
        print(f"   Time Estimate: {'✅' if results['time_estimate_found'] else '❌'}")
        print(f"   Self-Awareness: {'✅' if results['self_awareness_found'] else '❌'}")
        print(f"   Historical Data: {'✅' if results['historical_data_mentioned'] else '❌'}")
        print(f"   AI Identity: {'✅' if results['ai_identity_mentioned'] else '❌'}")
        
        # Show relevant section
        if results["time_estimate_found"]:
            print(f"\n📝 Time Estimate Section:")
            # Find time estimate section
            if "⏱️" in response_text:
                estimate_start = response_text.find("⏱️")
                estimate_section = response_text[estimate_start:estimate_start+500]
                print(f"   {estimate_section[:300]}...")
            elif "Time Estimate" in response_text:
                estimate_start = response_text.find("Time Estimate")
                estimate_section = response_text[estimate_start:estimate_start+500]
                print(f"   {estimate_section[:300]}...")
            elif "Ước tính thời gian" in response_text:
                estimate_start = response_text.find("Ước tính thời gian")
                estimate_section = response_text[estimate_start:estimate_start+500]
                print(f"   {estimate_section[:300]}...")
        
        return results
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout (backend may be slow)"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test StillMe Self-Time Estimation")
    parser.add_argument(
        "--backend-url",
        type=str,
        default="stillme-backend-production.up.railway.app",
        help="Backend URL (default: stillme-backend-production.up.railway.app)"
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("StillMe Self-Time Estimation Awareness Test")
    print("="*60)
    print(f"Backend URL: {args.backend_url}")
    print()
    
    # Test queries
    test_queries = [
        {
            "query": "How long will it take to learn 100 articles?",
            "expected_features": ["estimate", "historical", "ai system"]
        },
        {
            "query": "Bao lâu để học 100 bài viết?",
            "expected_features": ["ước tính", "lịch sử", "ai"]
        },
        {
            "query": "How long does validation take?",
            "expected_features": ["estimate", "validation", "time"]
        },
        {
            "query": "Bạn có thể ước lượng thời gian hoàn thành công việc không?",
            "expected_features": ["ước lượng", "thời gian", "công việc"]
        },
        {
            "query": "Do you track your own execution time?",
            "expected_features": ["track", "execution", "time", "self"]
        }
    ]
    
    results = []
    for test_case in test_queries:
        result = test_time_estimation_query(
            args.backend_url,
            test_case["query"],
            test_case["expected_features"]
        )
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    successful_tests = [r for r in results if r.get("success", False)]
    failed_tests = [r for r in results if not r.get("success", False)]
    
    print(f"\n✅ Successful tests: {len(successful_tests)}/{len(results)}")
    print(f"❌ Failed tests: {len(failed_tests)}/{len(results)}")
    
    if successful_tests:
        print(f"\n📊 Feature Statistics:")
        time_estimate_count = sum(1 for r in successful_tests if r.get("time_estimate_found", False))
        self_awareness_count = sum(1 for r in successful_tests if r.get("self_awareness_found", False))
        historical_count = sum(1 for r in successful_tests if r.get("historical_data_mentioned", False))
        ai_identity_count = sum(1 for r in successful_tests if r.get("ai_identity_mentioned", False))
        
        print(f"   Time Estimate: {time_estimate_count}/{len(successful_tests)} ({time_estimate_count*100//len(successful_tests) if successful_tests else 0}%)")
        print(f"   Self-Awareness: {self_awareness_count}/{len(successful_tests)} ({self_awareness_count*100//len(successful_tests) if successful_tests else 0}%)")
        print(f"   Historical Data: {historical_count}/{len(successful_tests)} ({historical_count*100//len(successful_tests) if successful_tests else 0}%)")
        print(f"   AI Identity: {ai_identity_count}/{len(successful_tests)} ({ai_identity_count*100//len(successful_tests) if successful_tests else 0}%)")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for r in failed_tests:
            print(f"   - {r.get('query', 'Unknown')}: {r.get('error', 'Unknown error')}")
    
    print(f"\n{'='*60}")
    print("Test completed!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()

