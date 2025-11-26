"""
Unit tests for External Data Layer

Tests for providers, orchestrator, caching, retry, and rate limiting.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from backend.external_data import (
    ExternalDataOrchestrator,
    detect_external_data_intent,
    ExternalDataIntent
)
from backend.external_data.providers.base import ExternalDataResult
from backend.external_data.retry import retry_with_backoff
from backend.external_data.rate_limit_tracker import RateLimitTracker


class TestIntentDetection:
    """Test intent detection"""
    
    def test_weather_intent_detection(self):
        """Test weather intent detection"""
        queries = [
            "What is the weather in Hanoi?",
            "Thời tiết ở Hà Nội như thế nào?",
            "Weather in Paris today",
        ]
        
        for query in queries:
            intent = detect_external_data_intent(query)
            assert intent is not None, f"Should detect weather intent for: {query}"
            assert intent.type == "weather", f"Intent type should be 'weather' for: {query}"
            assert intent.confidence >= 0.7, f"Confidence should be >= 0.7 for: {query}"
    
    def test_news_intent_detection(self):
        """Test news intent detection"""
        queries = [
            "Latest news about AI",
            "Tin tức mới nhất về AI",
            "bạn có biết thông tin mới nhất về AI ngày hôm nay ko?",
        ]
        
        for query in queries:
            intent = detect_external_data_intent(query)
            assert intent is not None, f"Should detect news intent for: {query}"
            assert intent.type == "news", f"Intent type should be 'news' for: {query}"
            assert intent.confidence >= 0.7, f"Confidence should be >= 0.7 for: {query}"


class TestRetryLogic:
    """Test retry logic with exponential backoff"""
    
    @pytest.mark.asyncio
    async def test_retry_success_on_first_attempt(self):
        """Test that successful call doesn't retry"""
        call_count = 0
        
        async def mock_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await retry_with_backoff(mock_func, max_retries=3)
        
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_success_after_failures(self):
        """Test retry succeeds after initial failures"""
        call_count = 0
        
        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            return "success"
        
        result = await retry_with_backoff(mock_func, max_retries=3)
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_fails_after_max_retries(self):
        """Test retry fails after max retries"""
        call_count = 0
        
        async def mock_func():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent error")
        
        with pytest.raises(Exception, match="Persistent error"):
            await retry_with_backoff(mock_func, max_retries=2)
        
        assert call_count == 3  # Initial + 2 retries


class TestRateLimitTracker:
    """Test rate limit tracking"""
    
    def test_rate_limit_allows_requests(self):
        """Test that rate limit allows requests within limit"""
        tracker = RateLimitTracker()
        
        # Configure low limit for testing
        tracker.configure_rate_limit("test_provider", max_calls=5, window_seconds=60)
        
        # Make requests within limit
        for i in range(5):
            can_make, error = tracker.can_make_request("test_provider")
            assert can_make, f"Request {i+1} should be allowed"
            tracker.record_call("test_provider")
    
    def test_rate_limit_blocks_excess_requests(self):
        """Test that rate limit blocks requests exceeding limit"""
        tracker = RateLimitTracker()
        
        # Configure low limit for testing
        tracker.configure_rate_limit("test_provider", max_calls=2, window_seconds=60)
        
        # Make requests up to limit
        for i in range(2):
            can_make, error = tracker.can_make_request("test_provider")
            assert can_make, f"Request {i+1} should be allowed"
            tracker.record_call("test_provider")
        
        # Next request should be blocked
        can_make, error = tracker.can_make_request("test_provider")
        assert not can_make, "Request should be blocked"
        assert "Rate limit exceeded" in error
    
    def test_rate_limit_stats(self):
        """Test rate limit statistics"""
        tracker = RateLimitTracker()
        
        tracker.configure_rate_limit("test_provider", max_calls=10, window_seconds=60)
        
        # Make some calls
        for i in range(3):
            tracker.record_call("test_provider")
        
        stats = tracker.get_stats("test_provider")
        
        assert stats["provider"] == "test_provider"
        assert stats["calls_in_window"] == 3
        assert stats["max_calls"] == 10
        assert stats["window_seconds"] == 60


class TestOrchestrator:
    """Test ExternalDataOrchestrator"""
    
    @pytest.mark.asyncio
    async def test_orchestrator_caching(self):
        """Test that orchestrator uses cache"""
        orchestrator = ExternalDataOrchestrator()
        
        # Create mock intent
        intent = ExternalDataIntent(
            type="weather",
            params={"location": "Hanoi"},
            confidence=0.9
        )
        
        # First call - should fetch from API (mocked)
        with patch.object(orchestrator, '_find_provider') as mock_find:
            mock_provider = Mock()
            mock_provider.get_provider_name.return_value = "Open-Meteo"
            mock_provider.supports.return_value = True
            mock_provider.get_cache_ttl.return_value = 60
            
            result = ExternalDataResult(
                data={"location": "Hanoi", "temperature": 25},
                source="Open-Meteo",
                timestamp=datetime.utcnow(),
                cached=False,
                success=True
            )
            mock_provider.fetch = AsyncMock(return_value=result)
            mock_find.return_value = mock_provider
            
            # First call
            result1 = await orchestrator.route(intent)
            assert result1 is not None
            assert not result1.cached
            
            # Second call - should use cache
            result2 = await orchestrator.route(intent)
            assert result2 is not None
            assert result2.cached


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

