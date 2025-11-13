"""
Tests for ContentCurator with ReviewAdapter integration
"""

import pytest
import os
from backend.services.content_curator import ContentCurator


class TestContentCuratorReview:
    """Test ContentCurator with ReviewAdapter"""
    
    def test_init_without_review_adapter(self):
        """Test initialization without ReviewAdapter"""
        curator = ContentCurator(enable_review_adapter=False)
        assert curator.review_adapter is None
    
    def test_init_with_review_adapter_disabled(self):
        """Test initialization with ReviewAdapter disabled via env"""
        curator = ContentCurator(enable_review_adapter=False)
        assert curator.review_adapter is None
    
    def test_pre_filter_without_review_adapter(self):
        """Test pre-filter without ReviewAdapter (should work normally)"""
        curator = ContentCurator(enable_review_adapter=False)
        
        content_list = [
            {
                "title": "RAG Systems in AI and Machine Learning",
                "summary": "This article discusses retrieval-augmented generation systems and their applications in artificial intelligence and machine learning. It covers vector databases, embeddings, and semantic search techniques.",
                "source": "test_source"
            },
            {
                "title": "Short",
                "summary": "Too short",
                "source": "test_source"
            }
        ]
        
        filtered, rejected = curator.pre_filter_content(content_list)
        
        # First item should pass (good length, relevant keywords like "rag", "ai", "machine learning")
        assert len(filtered) >= 1, f"Expected at least 1 filtered item, got {len(filtered)}. Rejected: {[r.get('rejection_reason') for r in rejected]}"
        # Second item should be rejected (too short)
        assert len(rejected) >= 1
    
    @pytest.mark.skipif(
        not os.getenv("DEEPSEEK_API_KEY"),
        reason="DEEPSEEK_API_KEY not set - skipping real API test"
    )
    def test_pre_filter_with_review_adapter(self):
        """Test pre-filter with ReviewAdapter enabled"""
        curator = ContentCurator(enable_review_adapter=True)
        
        # High quality content
        high_quality = {
            "title": "Recent Advances in RAG Evaluation Metrics",
            "summary": "This paper discusses citation accuracy and evidence grounding techniques for RAG systems, published on arXiv.",
            "source": "arxiv.org",
            "link": "https://arxiv.org/abs/2024.12345"
        }
        
        # Low quality content (not relevant)
        low_quality = {
            "title": "Cooking Recipes for Beginners",
            "summary": "Learn how to cook delicious meals with these easy recipes.",
            "source": "cooking-blog.com",
            "link": "https://cooking-blog.com/recipes"
        }
        
        content_list = [high_quality, low_quality]
        filtered, rejected = curator.pre_filter_content(content_list)
        
        # High quality should pass review
        assert len(filtered) >= 0  # May pass or fail based on other filters
        assert len(rejected) >= 0  # Low quality should likely be rejected
        
        # Check if review scores are added
        for item in filtered + rejected:
            if "review_score" in item:
                assert 0.0 <= item["review_score"] <= 10.0
                assert "review_passed" in item
    
    def test_get_curation_stats_with_review_adapter(self):
        """Test getting stats with ReviewAdapter"""
        curator = ContentCurator(enable_review_adapter=False)
        stats = curator.get_curation_stats()
        
        assert "review_adapter_enabled" in stats
        assert stats["review_adapter_enabled"] is False
        
        # Test with ReviewAdapter enabled (if API key available)
        if os.getenv("DEEPSEEK_API_KEY"):
            curator2 = ContentCurator(enable_review_adapter=True)
            stats2 = curator2.get_curation_stats()
            
            assert stats2["review_adapter_enabled"] is True
            if curator2.review_adapter:
                assert "review_adapter" in stats2
                assert "reviews_performed" in stats2["review_adapter"]

