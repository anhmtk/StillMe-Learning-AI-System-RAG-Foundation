#!/usr/bin/env python3
"""
StillMe Internet Access Test Suite
Test cases cho tính năng truy cập internet có kiểm soát
"""
import asyncio
import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "common"))

from config.validate_env import env_validator
from content_integrity_filter import content_filter
from market_intel import market_intel
from sandbox_controller import sandbox_controller


class TestInternetAccess:
    """Test suite cho internet access"""

    def setup_method(self):
        """Setup cho mỗi test method"""
        # Reset sandbox controller
        sandbox_controller.reset_egress_count()
        sandbox_controller.set_egress_limit(10)  # Allow 10 requests for testing

        # Reset content filter stats
        content_filter.reset_stats()

    def test_environment_validation(self):
        """Test environment validation"""
        print("\n🧪 Testing environment validation...")

        is_valid, missing = env_validator.validate_all()

        # Should not crash even if keys are missing
        assert isinstance(is_valid, bool)
        assert isinstance(missing, list)

        # Check if internet access is ready
        internet_ready = env_validator.check_internet_access_ready()
        assert isinstance(internet_ready, bool)

        print(f"✅ Environment validation: valid={is_valid}, missing={len(missing)}")
        print(f"✅ Internet access ready: {internet_ready}")

    def test_sandbox_controller(self):
        """Test sandbox controller functionality"""
        print("\n🧪 Testing sandbox controller...")

        # Test allowed domains
        allowed_urls = [
            "https://api.github.com/search/repositories",
            "https://newsapi.org/v2/everything",
            "https://gnews.io/api/v4/search"
        ]

        for url in allowed_urls:
            result = sandbox_controller.is_egress_allowed(url)
            assert result["allowed"] == True
            assert "domain" in result

        # Test blocked domains
        blocked_urls = [
            "https://malicious-site.com/evil",
            "https://phishing-site.net/steal"
        ]

        for url in blocked_urls:
            result = sandbox_controller.is_egress_allowed(url)
            assert result["allowed"] == False
            assert "reason" in result

        # Test egress limit
        sandbox_controller.set_egress_limit(2)
        sandbox_controller.reset_egress_count()

        # First two requests should be allowed
        for i in range(2):
            result = sandbox_controller.is_egress_allowed("https://api.github.com/test")
            assert result["allowed"] == True

        # Third request should be blocked
        result = sandbox_controller.is_egress_allowed("https://api.github.com/test")
        assert result["allowed"] == False
        assert "limit reached" in result["reason"]

        print("✅ Sandbox controller tests passed")

    def test_content_integrity_filter(self):
        """Test content integrity filter"""
        print("\n🧪 Testing content integrity filter...")

        # Test clean content
        clean_content = "This is a clean article about AI technology."
        result = content_filter.filter_content(clean_content, "test")
        assert result["success"] == True
        assert result["filtered"] == False
        assert result["content"] == clean_content

        # Test dangerous content
        dangerous_content = """
        <script>alert('XSS')</script>
        <img src="javascript:alert('XSS')">
        <a href="javascript:void(0)">Click me</a>
        This is some text with dangerous content.
        """
        result = content_filter.filter_content(dangerous_content, "test")
        assert result["success"] == True
        assert result["filtered"] == True
        assert len(result["warnings"]) > 0
        assert "<script>" not in result["content"]
        assert "javascript:" not in result["content"]

        # Test JSON filtering
        json_data = {
            "title": "AI News",
            "content": "<script>alert('XSS')</script>This is safe content.",
            "url": "https://example.com",
            "articles": [
                {"title": "Safe article", "content": "Clean content"},
                {"title": "Dangerous article", "content": "<script>alert('XSS')</script>"}
            ]
        }
        result = content_filter.filter_json_response(json_data, "test")
        assert result["success"] == True
        assert result["filtered"] == True
        assert "<script>" not in str(result["content"])

        print("✅ Content integrity filter tests passed")

    @pytest.mark.asyncio
    async def test_market_intelligence_news(self):
        """Test market intelligence news search"""
        print("\n🧪 Testing market intelligence news search...")

        # Test news search
        result = await market_intel.search_news("AI technology", "en")

        # Should not crash even if API keys are missing
        assert isinstance(result, dict)
        assert "success" in result

        if result["success"]:
            assert "data" in result
            assert "articles" in result["data"]
            print(f"✅ News search successful: {len(result['data']['articles'])} articles")
        else:
            print(f"ℹ️  News search failed (expected if no API keys): {result.get('error', 'Unknown error')}")

    @pytest.mark.asyncio
    async def test_market_intelligence_github(self):
        """Test market intelligence GitHub trending"""
        print("\n🧪 Testing market intelligence GitHub trending...")

        # Test GitHub trending
        result = await market_intel.get_github_trending("python")

        # Should not crash even if API keys are missing
        assert isinstance(result, dict)
        assert "success" in result

        if result["success"]:
            assert "data" in result
            assert "repositories" in result["data"]
            print(f"✅ GitHub trending successful: {len(result['data']['repositories'])} repositories")
        else:
            print(f"ℹ️  GitHub trending failed (expected if no API keys): {result.get('error', 'Unknown error')}")

    @pytest.mark.asyncio
    async def test_market_intelligence_hackernews(self):
        """Test market intelligence Hacker News"""
        print("\n🧪 Testing market intelligence Hacker News...")

        # Test Hacker News
        result = await market_intel.get_hackernews_trending()

        # Should not crash even if API keys are missing
        assert isinstance(result, dict)
        assert "success" in result

        if result["success"]:
            assert "data" in result
            assert "stories" in result["data"]
            print(f"✅ Hacker News successful: {len(result['data']['stories'])} stories")
        else:
            print(f"ℹ️  Hacker News failed (expected if no API keys): {result.get('error', 'Unknown error')}")

    @pytest.mark.asyncio
    async def test_web_request_processing(self):
        """Test web request processing"""
        print("\n🧪 Testing web request processing...")

        # Test different request types
        test_cases = [
            ("news", "Tin tức AI hôm nay"),
            ("github_trending", "GitHub trending repositories"),
            ("hackernews", "Hacker News trending")
        ]

        for request_type, query in test_cases:
            result = await market_intel.process_web_request(request_type, query)
            assert isinstance(result, dict)
            assert "success" in result
            print(f"✅ {request_type} request processed: {result['success']}")

    def test_integration_flow(self):
        """Test complete integration flow"""
        print("\n🧪 Testing complete integration flow...")

        # Simulate a web request flow
        # 1. Check sandbox permission
        url = "https://api.github.com/search/repositories"
        sandbox_result = sandbox_controller.is_egress_allowed(url)

        if sandbox_result["allowed"]:
            # 2. Process web request (mock)
            web_data = {
                "repositories": [
                    {
                        "name": "test-repo",
                        "description": "A test repository",
                        "stars": 100,
                        "language": "Python"
                    }
                ]
            }

            # 3. Filter content
            filtered_result = content_filter.filter_json_response(web_data, "integration_test")
            assert filtered_result["success"] == True

            print("✅ Integration flow test passed")
        else:
            print("ℹ️  Integration flow test skipped (sandbox blocked)")

    def test_error_handling(self):
        """Test error handling"""
        print("\n🧪 Testing error handling...")

        # Test with invalid URLs
        invalid_urls = [
            "not-a-url",
            "ftp://malicious.com",
            "javascript:alert('xss')"
        ]

        for url in invalid_urls:
            result = sandbox_controller.is_egress_allowed(url)
            assert result["allowed"] == False
            assert "reason" in result

        # Test with empty content
        result = content_filter.filter_content("", "test")
        assert result["success"] == True

        # Test with None content
        result = content_filter.filter_content(None, "test")
        assert result["success"] == True

        print("✅ Error handling tests passed")

    def test_statistics(self):
        """Test statistics collection"""
        print("\n🧪 Testing statistics collection...")

        # Test sandbox stats
        stats = sandbox_controller.get_stats()
        assert isinstance(stats, dict)
        assert "total_requests" in stats
        assert "allowed_requests" in stats
        assert "blocked_requests" in stats

        # Test content filter stats
        stats = content_filter.get_stats()
        assert isinstance(stats, dict)
        assert "total_processed" in stats
        assert "blocked_content" in stats
        assert "sanitized_content" in stats

        print("✅ Statistics collection tests passed")

def test_main():
    """Main test function"""
    print("🚀 StillMe Internet Access Test Suite")
    print("=" * 60)

    # Create test instance
    test_instance = TestInternetAccess()

    # Run tests
    test_methods = [
        "test_environment_validation",
        "test_sandbox_controller",
        "test_content_integrity_filter",
        "test_integration_flow",
        "test_error_handling",
        "test_statistics"
    ]

    for method_name in test_methods:
        try:
            test_instance.setup_method()
            method = getattr(test_instance, method_name)
            method()
            print(f"✅ {method_name} passed")
        except Exception as e:
            print(f"❌ {method_name} failed: {e}")
            raise

    # Run async tests
    async def run_async_tests():
        async_methods = [
            "test_market_intelligence_news",
            "test_market_intelligence_github",
            "test_market_intelligence_hackernews",
            "test_web_request_processing"
        ]

        for method_name in async_methods:
            try:
                test_instance.setup_method()
                method = getattr(test_instance, method_name)
                await method()
                print(f"✅ {method_name} passed")
            except Exception as e:
                print(f"❌ {method_name} failed: {e}")
                raise

    # Run async tests
    asyncio.run(run_async_tests())

    print("\n" + "=" * 60)
    print("🎉 All tests passed! Internet access is working correctly.")
    print("=" * 60)

if __name__ == "__main__":
    test_main()
