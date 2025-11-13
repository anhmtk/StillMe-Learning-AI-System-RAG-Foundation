"""
Tests for ReviewAdapter - Simulated Peer Review for Learning Proposals
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from backend.validators.review_adapter import ReviewAdapter


class TestReviewAdapter:
    """Test ReviewAdapter functionality"""
    
    def test_init_without_api_key(self):
        """Test initialization without API key"""
        adapter = ReviewAdapter(api_key=None, enable_cache=True)
        assert adapter.api_key is None
        assert adapter.enable_cache is True
        assert adapter.review_count == 0
    
    def test_init_with_api_key(self):
        """Test initialization with API key"""
        adapter = ReviewAdapter(api_key="test_key", enable_cache=True)
        assert adapter.api_key == "test_key"
        assert adapter.enable_cache is True
    
    def test_evaluate_proposal_no_api_key(self):
        """Test evaluation when no API key is available"""
        adapter = ReviewAdapter(api_key=None, enable_cache=True)
        result = adapter.evaluate_proposal("Test proposal")
        
        assert result["score"] == 5.0
        assert result["passed"] is True
        assert "review_disabled_no_api_key" in result["reasons"]
        assert result["cached"] is False
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        adapter = ReviewAdapter(api_key="test_key", enable_cache=True)
        
        key1 = adapter._get_cache_key("Test proposal", "learning_content")
        key2 = adapter._get_cache_key("Test proposal", "learning_content")
        key3 = adapter._get_cache_key("Different proposal", "learning_content")
        
        assert key1 == key2  # Same proposal should have same key
        assert key1 != key3  # Different proposals should have different keys
    
    def test_parse_review_response_valid_json(self):
        """Test parsing valid JSON response"""
        adapter = ReviewAdapter(api_key="test_key")
        
        response = '{"score": 7.5, "reasons": ["Good novelty", "Relevant to AI"]}'
        score, reasons = adapter._parse_review_response(response)
        
        assert score == 7.5
        assert len(reasons) == 2
        assert "Good novelty" in reasons
    
    def test_parse_review_response_invalid_json(self):
        """Test parsing invalid JSON response"""
        adapter = ReviewAdapter(api_key="test_key")
        
        response = "This is not JSON"
        score, reasons = adapter._parse_review_response(response)
        
        # Should return neutral score on parse error
        assert score == 5.0
        assert len(reasons) > 0
    
    def test_parse_review_response_score_extraction(self):
        """Test extracting score from text when JSON parsing fails"""
        adapter = ReviewAdapter(api_key="test_key")
        
        response = "The score is 8.5 because it's relevant"
        score, reasons = adapter._parse_review_response(response)
        
        assert score == 8.5
        assert len(reasons) > 0
    
    def test_get_stats(self):
        """Test getting statistics"""
        adapter = ReviewAdapter(api_key="test_key", enable_cache=True)
        
        stats = adapter.get_stats()
        
        assert "reviews_performed" in stats
        assert "cache_hits" in stats
        assert "cache_size" in stats
        assert "cache_hit_rate" in stats
        assert "threshold" in stats
        assert stats["threshold"] == 5.0
    
    def test_clear_cache(self):
        """Test clearing cache"""
        adapter = ReviewAdapter(api_key="test_key", enable_cache=True)
        
        # Add something to cache (simulate)
        adapter._get_cache_key("test", "learning_content")
        
        adapter.clear_cache()
        stats = adapter.get_stats()
        assert stats["cache_size"] == 0
    
    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY not set - skipping real API test"
    )
    def test_evaluate_proposal_real_api(self):
        """Test evaluation with real API (requires DEEPSEEK_API_KEY)"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        adapter = ReviewAdapter(api_key=api_key, enable_cache=True)
        
        # High quality proposal
        result = adapter.evaluate_proposal(
            "StillMe should learn about recent advances in RAG evaluation metrics, "
            "specifically focusing on citation accuracy and evidence grounding techniques from recent arXiv papers.",
            proposal_type="learning_content"
        )
        
        assert "score" in result
        assert "passed" in result
        assert "reasons" in result
        assert 0.0 <= result["score"] <= 10.0
        assert isinstance(result["passed"], bool)
        assert isinstance(result["reasons"], list)
        
        # Low quality proposal
        result2 = adapter.evaluate_proposal(
            "StillMe should learn about cooking recipes.",
            proposal_type="learning_content"
        )
        
        assert "score" in result2
        assert 0.0 <= result2["score"] <= 10.0
        
        # Check that high quality proposal has higher score
        if result["score"] >= 5.0 and result2["score"] < 5.0:
            assert result["score"] > result2["score"]
    
    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY not set - skipping real API test"
    )
    def test_evaluate_proposal_caching(self):
        """Test that caching works correctly"""
        api_key = os.getenv("DEEPSEEK_API_KEY")
        adapter = ReviewAdapter(api_key=api_key, enable_cache=True)
        
        proposal = "StillMe should learn about RAG systems and vector databases."
        
        # First evaluation
        result1 = adapter.evaluate_proposal(proposal, proposal_type="learning_content")
        assert result1["cached"] is False
        
        # Second evaluation (should be cached)
        result2 = adapter.evaluate_proposal(proposal, proposal_type="learning_content")
        assert result2["cached"] is True
        assert result1["score"] == result2["score"]
        
        # Check cache stats
        stats = adapter.get_stats()
        assert stats["cache_hits"] >= 1
        assert stats["cache_size"] >= 1

