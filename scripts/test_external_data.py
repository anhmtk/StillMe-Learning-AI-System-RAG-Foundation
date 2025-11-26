"""
Test script for External Data Layer (Phase 1)

Tests weather and news providers to verify implementation.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from backend.external_data import ExternalDataOrchestrator, detect_external_data_intent


async def test_weather():
    """Test weather provider"""
    print("=" * 60)
    print("Testing Weather Provider")
    print("=" * 60)
    
    # Test intent detection
    query = "What is the weather in Hanoi?"
    intent = detect_external_data_intent(query)
    
    if not intent:
        print(f"[FAIL] Intent not detected for: {query}")
        return False
    
    print(f"[OK] Intent detected: type={intent.type}, confidence={intent.confidence}")
    print(f"     Params: {intent.params}")
    
    # Test provider
    orchestrator = ExternalDataOrchestrator()
    result = await orchestrator.route(intent)
    
    if not result:
        print("[FAIL] No result from orchestrator")
        return False
    
    if not result.success:
        print(f"[FAIL] Provider error: {result.error_message}")
        return False
    
    print(f"[OK] Weather data fetched successfully")
    print(f"     Source: {result.source}")
    print(f"     Location: {result.data.get('location')}")
    print(f"     Temperature: {result.data.get('temperature')}°C")
    print(f"     Condition: {result.data.get('weather_description')}")
    print(f"     Cached: {result.cached}")
    
    # Test response formatting
    response_text = orchestrator.format_response(result, query)
    print(f"\n[OK] Formatted response:")
    print("-" * 60)
    print(response_text)
    print("-" * 60)
    
    return True


async def test_news():
    """Test news provider"""
    print("\n" + "=" * 60)
    print("Testing News Provider")
    print("=" * 60)
    
    # Check if API key is configured
    import os
    if not os.getenv("GNEWS_API_KEY"):
        print("[SKIP] GNEWS_API_KEY not configured - skipping news test")
        print("       Set GNEWS_API_KEY in .env to test news provider")
        return None
    
    # Test intent detection
    query = "Latest news about AI"
    intent = detect_external_data_intent(query)
    
    if not intent:
        print(f"[FAIL] Intent not detected for: {query}")
        return False
    
    print(f"[OK] Intent detected: type={intent.type}, confidence={intent.confidence}")
    print(f"     Params: {intent.params}")
    
    # Test provider
    orchestrator = ExternalDataOrchestrator()
    result = await orchestrator.route(intent)
    
    if not result:
        print("[FAIL] No result from orchestrator")
        return False
    
    if not result.success:
        print(f"[FAIL] Provider error: {result.error_message}")
        return False
    
    print(f"[OK] News data fetched successfully")
    print(f"     Source: {result.source}")
    print(f"     Query: {result.data.get('query')}")
    print(f"     Total results: {result.data.get('total_results')}")
    print(f"     Articles returned: {len(result.data.get('articles', []))}")
    print(f"     Cached: {result.cached}")
    
    # Test response formatting
    response_text = orchestrator.format_response(result, query)
    print(f"\n[OK] Formatted response (first 500 chars):")
    print("-" * 60)
    print(response_text[:500] + "..." if len(response_text) > 500 else response_text)
    print("-" * 60)
    
    return True


async def test_caching():
    """Test caching"""
    print("\n" + "=" * 60)
    print("Testing Caching")
    print("=" * 60)
    
    query = "What is the weather in Paris?"
    intent = detect_external_data_intent(query)
    
    if not intent:
        print("[FAIL] Intent not detected")
        return False
    
    orchestrator = ExternalDataOrchestrator()
    
    # First call (should fetch from API)
    print("[1] First call (should fetch from API)...")
    result1 = await orchestrator.route(intent)
    if result1 and result1.success:
        print(f"     Cached: {result1.cached} (should be False)")
    
    # Second call (should use cache)
    print("[2] Second call (should use cache)...")
    result2 = await orchestrator.route(intent)
    if result2 and result2.success:
        print(f"     Cached: {result2.cached} (should be True)")
        if result2.cached:
            print("[OK] Caching works!")
            return True
        else:
            print("[FAIL] Cache not working")
            return False
    
    return False


async def main():
    """Run all tests"""
    print("External Data Layer - Phase 1 Test")
    print("=" * 60)
    print()
    
    results = {}
    
    # Test weather
    results["weather"] = await test_weather()
    
    # Test news
    results["news"] = await test_news()
    
    # Test caching
    results["caching"] = await test_caching()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is None:
            status = "[SKIP]"
        elif result:
            status = "[OK]"
        else:
            status = "[FAIL]"
        print(f"{test_name:20s} {status}")
    
    # Count successes
    passed = sum(1 for r in results.values() if r is True)
    total = sum(1 for r in results.values() if r is not None)
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n[OK] All tests passed!")
        return 0
    else:
        print("\n[WARNING] Some tests failed or were skipped")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

