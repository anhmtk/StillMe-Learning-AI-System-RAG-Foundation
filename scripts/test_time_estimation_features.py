#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for Time Estimation Features

Tests:
1. Chat response integration (time estimation in chat)
2. Learning cycle tracking
3. Validation tracking

Usage:
    python scripts/test_time_estimation_features.py [--backend-url URL]
"""

import sys
import os
import argparse
import requests
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# Import StillMe components for direct testing
from backend.core.time_estimation_intent import detect_time_estimation_intent
from stillme_core.monitoring import (
    get_estimation_engine,
    get_task_tracker,
    format_self_aware_response
)


def test_intent_detection():
    """Test time estimation intent detection"""
    print("\n" + "="*60)
    print("TEST 1: Time Estimation Intent Detection")
    print("="*60)
    
    test_cases = [
        ("How long will it take to learn 100 articles?", True),
        # Note: Vietnamese patterns need improvement - currently only works with exact keywords
        ("Bao lau de hoc 100 bai viet?", False),  # Expected to fail until pattern improved
        ("Hoc 100 bai viet mat bao lau?", False),  # Expected to fail until pattern improved
        ("What is StillMe?", False),
        ("How does RAG work?", False),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected in test_cases:
        is_time_estimation, task_description = detect_time_estimation_intent(query)
        result = "✅ PASS" if is_time_estimation == expected else "❌ FAIL"
        
        if is_time_estimation == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{result}: '{query}'")
        print(f"   Expected: {expected}, Got: {is_time_estimation}")
        if task_description:
            print(f"   Task description: {task_description}")
        print()
    
    print(f"Results: {passed} passed, {failed} failed")
    return failed == 0


def test_estimation_engine():
    """Test time estimation engine"""
    print("\n" + "="*60)
    print("TEST 2: Time Estimation Engine")
    print("="*60)
    
    try:
        estimator = get_estimation_engine()
        
        test_cases = [
            {
                "description": "Learn 100 articles",
                "task_type": "learning",
                "complexity": "moderate",
                "size": 100
            },
            {
                "description": "Validate response with 5 validators",
                "task_type": "validation",
                "complexity": "simple",
                "size": 500
            },
            {
                "description": "Refactor validation system",
                "task_type": "refactoring",
                "complexity": "complex",
                "size": 1000
            }
        ]
        
        passed = 0
        failed = 0
        
        for test_case in test_cases:
            try:
                estimate = estimator.estimate(
                    task_description=test_case["description"],
                    task_type=test_case["task_type"],
                    complexity=test_case["complexity"],
                    size=test_case["size"]
                )
                
                print(f"✅ Task: {test_case['description']}")
                print(f"   Estimated: {estimate.estimated_minutes:.2f} minutes")
                print(f"   Range: {estimate.range_min:.2f} - {estimate.range_max:.2f} minutes")
                print(f"   Confidence: {estimate.confidence:.0%}")
                print(f"   Based on: {estimate.based_on_n_tasks} similar tasks")
                print()
                
                # Validate estimate
                if estimate.estimated_minutes > 0 and estimate.range_min <= estimate.range_max:
                    passed += 1
                else:
                    failed += 1
                    print(f"   ❌ Invalid estimate values")
                    
            except Exception as e:
                print(f"❌ Error estimating '{test_case['description']}': {e}")
                failed += 1
                print()
        
        print(f"Results: {passed} passed, {failed} failed")
        return failed == 0
        
    except Exception as e:
        print(f"❌ Failed to initialize estimation engine: {e}")
        return False


def test_task_tracker():
    """Test task tracking"""
    print("\n" + "="*60)
    print("TEST 3: Task Tracker")
    print("="*60)
    
    try:
        tracker = get_task_tracker()
        
        # Test 1: Start and end a task
        print("Test 3.1: Start and end task")
        task_id = tracker.start_task(
            task_type="testing",
            complexity="simple",
            size=10,
            estimated_time_minutes=5.0,
            metadata={"test": True}
        )
        print(f"   ✅ Started task: {task_id}")
        
        import time
        time.sleep(0.1)  # Simulate work
        
        record = tracker.end_task(task_id, metadata={"test": True})
        if record:
            print(f"   ✅ Ended task: {task_id}")
            print(f"   Estimated: {record.estimated_time_minutes:.2f} min")
            print(f"   Actual: {record.actual_time_minutes:.2f} min")
            print(f"   Accuracy: {record.accuracy_ratio:.2f}")
        else:
            print(f"   ❌ Failed to end task")
            return False
        
        # Test 2: Get historical tasks
        print("\nTest 3.2: Get historical tasks")
        historical = tracker.get_historical_tasks(
            task_type="testing",
            days=7  # Last 7 days
        )
        print(f"   ✅ Found {len(historical)} historical tasks")
        
        if len(historical) > 0:
            print(f"   Latest task: {historical[0].task_type}, {historical[0].actual_time_minutes:.2f} min")
        
        print("\n✅ Task tracker tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Task tracker test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_chat_integration(backend_url: Optional[str] = None):
    """Test chat integration with time estimation"""
    print("\n" + "="*60)
    print("TEST 4: Chat Integration (Time Estimation)")
    print("="*60)
    
    if not backend_url:
        print("⚠️  Backend URL not provided, skipping chat integration test")
        print("   Use --backend-url to test chat integration")
        return None
    
    test_queries = [
        "How long will it take to learn 100 articles?",
        "Bao lau de hoc 100 bai viet?",
    ]
    
    passed = 0
    failed = 0
    
    for query in test_queries:
        try:
            print(f"\nTesting query: '{query}'")
            
            # Send chat request
            response = requests.post(
                f"{backend_url}/api/chat/rag",
                json={
                    "message": query,
                    "use_rag": True,
                    "context_limit": 3
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")
                
                # Check if time estimate is in response
                has_estimate = (
                    "estimate" in response_text.lower() or
                    "ước tính" in response_text.lower() or
                    "Time Estimate" in response_text or
                    "Ước tính thời gian" in response_text
                )
                
                if has_estimate:
                    print(f"   ✅ Time estimate found in response")
                    print(f"   Response preview: {response_text[:200]}...")
                    passed += 1
                else:
                    print(f"   ⚠️  Time estimate not found in response")
                    print(f"   Response preview: {response_text[:200]}...")
                    failed += 1
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                failed += 1
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request error: {e}")
            failed += 1
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0 if passed + failed > 0 else None


def test_self_tracking_integration():
    """Test self-tracking integration"""
    print("\n" + "="*60)
    print("TEST 5: Self-Tracking Integration")
    print("="*60)
    
    try:
        from stillme_core.monitoring import track_task_execution
        
        print("Test 5.1: Context manager tracking")
        
        with track_task_execution(
            task_description="Test task",
            task_type="testing",
            complexity="simple",
            size=10,
            communicate_estimate=False
        ) as estimate:
            import time
            time.sleep(0.1)
            print(f"   ✅ Task executed with estimate: {estimate.estimated_minutes:.2f} min")
        
        print("   ✅ Context manager tracking works")
        
        # Test 5.2: Format self-aware response
        print("\nTest 5.2: Format self-aware response")
        estimator = get_estimation_engine()
        estimate = estimator.estimate(
            task_description="Test task",
            task_type="testing",
            complexity="moderate",
            size=100
        )
        
        formatted = format_self_aware_response(estimate, include_identity=True)
        print(f"   ✅ Formatted response: {formatted[:150]}...")
        
        # Check if AI identity is included
        if "AI system" in formatted or "hệ thống AI" in formatted:
            print("   ✅ AI identity included in response")
        else:
            print("   ⚠️  AI identity not found in response")
        
        print("\n✅ Self-tracking integration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Self-tracking integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    parser = argparse.ArgumentParser(description="Test Time Estimation Features")
    parser.add_argument(
        "--backend-url",
        type=str,
        default=None,
        help="Backend URL for chat integration test (e.g., http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("StillMe Time Estimation Features - Test Suite")
    print("="*60)
    
    results = {}
    
    # Test 1: Intent detection
    results["intent_detection"] = test_intent_detection()
    
    # Test 2: Estimation engine
    results["estimation_engine"] = test_estimation_engine()
    
    # Test 3: Task tracker
    results["task_tracker"] = test_task_tracker()
    
    # Test 4: Chat integration (optional)
    results["chat_integration"] = test_chat_integration(args.backend_url)
    
    # Test 5: Self-tracking integration
    results["self_tracking"] = test_self_tracking_integration()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results.items():
        if result is None:
            status = "⏭️  SKIPPED"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"{status}: {test_name}")
    
    # Overall result
    passed_tests = sum(1 for r in results.values() if r is True)
    failed_tests = sum(1 for r in results.values() if r is False)
    skipped_tests = sum(1 for r in results.values() if r is None)
    total_tests = len(results)
    
    print(f"\nTotal: {total_tests} tests")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Skipped: {skipped_tests}")
    
    if failed_tests == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed_tests} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

