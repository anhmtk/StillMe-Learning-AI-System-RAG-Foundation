#!/usr/bin/env python3
"""
Debug script for app.py full web request flow
"""
import asyncio
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append('.')

def test_app_full_flow():
    """Test app.py full web request flow"""
    try:
        print("🔍 Testing app.py full web request flow...")
        
        # Import modules
        from market_intel import market_intel
        from content_integrity_filter import content_filter
        from sandbox_controller import sandbox_controller
        
        # Test 1: Check web request detection
        print("\n1. Testing web request detection...")
        message = "tin tức AI hôm nay"
        message_lower = message.lower()
        news_keywords = ["tin tức", "news", "báo", "thời sự", "xu hướng", "trend", "cập nhật", "mới nhất"]
        
        is_news_request = any(keyword in message_lower for keyword in news_keywords)
        print(f"Is news request: {is_news_request}")
        
        if not is_news_request:
            print("❌ Not a news request")
            return
        
        # Test 2: Test sandbox permission
        print("\n2. Testing sandbox permission...")
        sandbox_enabled = sandbox_controller.is_sandbox_enabled()
        print(f"Sandbox enabled: {sandbox_enabled}")
        
        if not sandbox_enabled:
            print("❌ Sandbox is disabled, web search will be blocked")
            return
        
        # Test 3: Test news search
        print("\n3. Testing news search...")
        async def test_news():
            result = await market_intel.search_news(message, "vi")
            print(f"News search result: {result['success']}")
            if result['success']:
                print(f"Data keys: {list(result['data'].keys()) if result['data'] else 'No data'}")
                return result
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                return None
        
        news_result = asyncio.run(test_news())
        
        if not news_result:
            print("❌ News search failed")
            return
        
        # Test 4: Test content filtering
        print("\n4. Testing content filtering...")
        filtered_result = content_filter.filter_json_response(news_result['data'], "test_news")
        print(f"Content filter result: {filtered_result['success']}")
        
        if not filtered_result['success']:
            print(f"Filter warnings: {filtered_result.get('warnings', [])}")
            print("❌ Content filtering failed")
            return
        
        # Test 5: Test response formatting
        print("\n5. Testing response formatting...")
        try:
            articles = filtered_result['content'].get("articles", [])
            if not articles:
                print("❌ No articles found")
                return
            
            response = "📰 Tin tức mới nhất:\n\n"
            for i, article in enumerate(articles[:5], 1):
                title = article.get("title", "Không có tiêu đề")
                description = article.get("description", "Không có mô tả")
                source = article.get("source", "Nguồn không xác định")
                response += f"{i}. **{title}**\n"
                response += f"   {description}\n"
                response += f"   Nguồn: {source}\n\n"
            
            print("✅ Response formatting successful")
            print(f"Formatted response length: {len(response)} characters")
            print(f"First 200 chars: {response[:200]}...")
            
        except Exception as e:
            print(f"❌ Response formatting failed: {e}")
            return
        
        # Test 6: Test final response format
        print("\n6. Testing final response format...")
        final_response = {
            "is_web_request": True,
            "model": "web_news",
            "response": response,
            "engine": "web",
            "status": "success"
        }
        
        print("✅ Final response format successful")
        print(f"Final response keys: {list(final_response.keys())}")
        
        print("\n✅ Full flow test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_app_full_flow()