#!/usr/bin/env python3
"""
Debug script for web search functionality
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append('.')

def test_web_search():
    """Test web search functionality"""
    try:
        print("🔍 Testing web search functionality...")
        
        # Test 1: Import modules
        print("\n1. Testing module imports...")
        from market_intel import market_intel
        from content_integrity_filter import content_filter
        from sandbox_controller import sandbox_controller
        print("✅ All modules imported successfully")
        
        # Test 2: Test news search
        print("\n2. Testing news search...")
        async def test_news():
            result = await market_intel.search_news("AI news", "en")
            print(f"News search result: {result['success']}")
            if result['success']:
                print(f"Data keys: {list(result['data'].keys()) if result['data'] else 'No data'}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
            return result
        
        news_result = asyncio.run(test_news())
        
        # Test 3: Test content filtering
        print("\n3. Testing content filtering...")
        if news_result['success']:
            filtered_result = content_filter.filter_json_response(news_result['data'], "test_news")
            print(f"Content filter result: {filtered_result['success']}")
            if not filtered_result['success']:
                print(f"Filter warnings: {filtered_result.get('warnings', [])}")
        
        # Test 4: Test sandbox controller
        print("\n4. Testing sandbox controller...")
        print(f"Sandbox enabled: {sandbox_controller.is_sandbox_enabled()}")
        print(f"Allowed domains: {sandbox_controller.get_blocked_domains()}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_web_search()
