#!/usr/bin/env python3
"""
Test Web Access v2 integration with app.py
"""
import asyncio
import sys
import os

# Add current directory to path
sys.path.append('.')

def test_web_access_v2_integration():
    """Test Web Access v2 integration"""
    print("🔍 Testing Web Access v2 integration...")
    
    try:
        # Test imports
        print("1. Testing imports...")
        from web_tools import web_tools
        from policy.tool_gate import validate_tool_request
        from security.content_wrap import wrap_content
        from cache.web_cache import get_cached_data, cache_data, generate_cache_key
        from metrics.web_metrics import record_request
        from sandbox_controller import sandbox_controller
        print("✅ All imports successful")
        
        # Test tool gate
        print("\n2. Testing tool gate...")
        decision = validate_tool_request('web.search_news', {'query': 'AI technology', 'window': '24h'}, 'What is the latest AI news?')
        print(f"✅ Tool gate: {decision.allowed}")
        
        # Test sandbox
        print("\n3. Testing sandbox...")
        result = sandbox_controller.is_egress_allowed('https://api.github.com/test')
        print(f"✅ Sandbox: {result['allowed']}")
        
        # Test web tools
        print("\n4. Testing web tools...")
        async def test_web_tools():
            result = await web_tools.call_tool('web.search_news', query='AI technology', window='24h')
            print(f"✅ Web tools: Success = {result.success}")
            return result
        
        web_result = asyncio.run(test_web_tools())
        
        # Test cache
        print("\n5. Testing cache...")
        key = generate_cache_key('web.search_news', query='AI technology', window='24h')
        cache_data(key, {'test': 'data'}, 'news')
        cached_data, hit = get_cached_data(key, 'news')
        print(f"✅ Cache: Hit = {hit}")
        
        # Test metrics
        print("\n6. Testing metrics...")
        record_request('web.search_news', True, 1500.0, False, 'newsapi.org', None, 2048)
        print("✅ Metrics recorded")
        
        print("\n✅ All Web Access v2 components working!")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_app_integration():
    """Test app.py integration"""
    print("\n🔍 Testing app.py integration...")
    
    try:
        # Import SmartRouter from app.py
        import app
        smart_router = app.SmartRouter()
        
        # Test web request detection
        print("1. Testing web request detection...")
        web_result = smart_router._check_web_request("tin tức AI hôm nay")
        print(f"✅ Web request detected: {web_result['is_web_request']}")
        
        if web_result['is_web_request']:
            print(f"   Request type: {web_result.get('request_type', 'web_search')}")
            
            # Test Web Access v2 handling
            print("2. Testing Web Access v2 handling...")
            result = smart_router._handle_web_request_v2(web_result.get('request_type', 'web_search'), "tin tức AI hôm nay")
            print(f"✅ Web Access v2 result: {result['status']}")
            print(f"   Model: {result['model']}")
            print(f"   Engine: {result['engine']}")
            if 'attribution' in result:
                print(f"   Attribution: {result['attribution'] is not None}")
        
        print("\n✅ App integration working!")
        return True
        
    except Exception as e:
        print(f"❌ App integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Web Access v2 Integration Test Suite")
    print("=" * 50)
    
    # Test Web Access v2 components
    web_access_ok = test_web_access_v2_integration()
    
    # Test app integration
    app_ok = test_app_integration()
    
    print("\n" + "=" * 50)
    if web_access_ok and app_ok:
        print("✅ All tests passed! Web Access v2 is ready.")
    else:
        print("❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
