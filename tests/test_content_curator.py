"""
Tests for Content Curator Service
Tests pre-filtering, prioritization, keyword scoring, and source quality tracking
"""

import pytest
from backend.services.content_curator import ContentCurator, MINIMUM_CONTENT_LENGTH


class TestContentCurator:
    """Test suite for ContentCurator"""
    
    @pytest.fixture
    def curator(self):
        """Create ContentCurator instance"""
        return ContentCurator()
    
    def test_pre_filter_content_passes_length_and_keyword(self, curator):
        """Test pre-filter passes content with sufficient length and keywords"""
        # Create summary that is definitely long enough and has keywords
        summary = (
            "This article discusses the importance of ethical AI systems with complete transparency. "
            "It covers AI governance, RAG systems, and the need for open-source solutions. "
            "StillMe is an example of a transparent AI system that uses retrieval-augmented generation to learn continuously. "
            "The system emphasizes ethics, transparency, and governance in artificial intelligence. "
            "Machine learning and deep learning are important components of modern AI systems."
        ) * 3  # Repeat to ensure it's long enough
        
        content_list = [
            {
                "title": "Ethics in AI: Transparency and Governance",
                "summary": summary,
                "link": "https://example.com/article1"
            }
        ]
        
        filtered, rejected = curator.pre_filter_content(content_list)
        
        assert len(filtered) == 1
        assert len(rejected) == 0
        assert filtered[0]["title"] == content_list[0]["title"]
        assert "keyword_score" in filtered[0]
        assert "content_length" in filtered[0]
    
    def test_pre_filter_content_rejects_short_content(self, curator):
        """Test pre-filter rejects content that is too short"""
        content_list = [
            {
                "title": "Short",
                "summary": "Too short",
                "link": "https://example.com/short"
            }
        ]
        
        filtered, rejected = curator.pre_filter_content(content_list)
        
        assert len(filtered) == 0
        assert len(rejected) == 1
        assert "rejection_reason" in rejected[0]
        assert "too short" in rejected[0]["rejection_reason"].lower()
    
    def test_pre_filter_content_rejects_low_keyword_score(self, curator):
        """Test pre-filter rejects content with low keyword score"""
        # Create content that is long enough but has no relevant keywords
        long_text = "A" * MINIMUM_CONTENT_LENGTH
        content_list = [
            {
                "title": "Random Article",
                "summary": long_text,
                "link": "https://example.com/random"
            }
        ]
        
        filtered, rejected = curator.pre_filter_content(content_list)
        
        assert len(filtered) == 0
        assert len(rejected) == 1
        assert "rejection_reason" in rejected[0]
        assert "low keyword" in rejected[0]["rejection_reason"].lower()
        assert "keyword_score" in rejected[0]
    
    def test_pre_filter_content_mixed_results(self, curator):
        """Test pre-filter with mixed content (some pass, some fail)"""
        content_list = [
            {
                "title": "Ethics in AI",
                "summary": "This article discusses ethical AI systems with transparency and governance. " * 20,  # Long enough
                "link": "https://example.com/ethics"
            },
            {
                "title": "Short",
                "summary": "Too short",
                "link": "https://example.com/short"
            },
            {
                "title": "Random",
                "summary": "A" * MINIMUM_CONTENT_LENGTH,  # Long but no keywords
                "link": "https://example.com/random"
            }
        ]
        
        filtered, rejected = curator.pre_filter_content(content_list)
        
        assert len(filtered) == 1
        assert len(rejected) == 2
        assert filtered[0]["title"] == "Ethics in AI"
    
    def test_pre_filter_content_empty_list(self, curator):
        """Test pre-filter with empty content list"""
        filtered, rejected = curator.pre_filter_content([])
        
        assert len(filtered) == 0
        assert len(rejected) == 0
    
    def test_pre_filter_content_none(self, curator):
        """Test pre-filter handles None gracefully"""
        filtered, rejected = curator.pre_filter_content(None)
        
        # Should return empty lists
        assert isinstance(filtered, list)
        assert isinstance(rejected, list)
    
    def test_calculate_keyword_score_high_priority_keywords(self, curator):
        """Test keyword scoring with high priority keywords"""
        text = "Ethics and transparency in AI governance with RAG systems and StillMe"
        
        score = curator._calculate_keyword_score(text)
        
        assert score > 0.5  # Should have high score
        assert score <= 1.0
    
    def test_calculate_keyword_score_medium_priority_keywords(self, curator):
        """Test keyword scoring with medium priority keywords"""
        text = "Machine learning and deep learning with neural networks and vector databases"
        
        score = curator._calculate_keyword_score(text)
        
        assert score > 0.0
        assert score <= 1.0
    
    def test_calculate_keyword_score_no_keywords(self, curator):
        """Test keyword scoring with no relevant keywords"""
        text = "This is a random article about cooking recipes and gardening tips"
        
        score = curator._calculate_keyword_score(text)
        
        assert score == 0.0
    
    def test_calculate_keyword_score_multiple_matches(self, curator):
        """Test keyword scoring with multiple keyword matches"""
        text = "Ethics transparency governance RAG StillMe machine learning"
        
        score = curator._calculate_keyword_score(text)
        
        assert score > 0.0
        assert score <= 1.0
    
    def test_calculate_keyword_score_case_insensitive(self, curator):
        """Test keyword scoring is case insensitive"""
        text1 = "ETHICS TRANSPARENCY"
        text2 = "ethics transparency"
        text3 = "Ethics Transparency"
        
        score1 = curator._calculate_keyword_score(text1)
        score2 = curator._calculate_keyword_score(text2)
        score3 = curator._calculate_keyword_score(text3)
        
        assert score1 == score2 == score3
    
    def test_prioritize_learning_content_basic(self, curator):
        """Test basic content prioritization"""
        content_list = [
            {
                "title": "Article 1",
                "summary": "Ethics in AI" * 50,
                "link": "https://example.com/1",
                "keyword_score": 0.8
            },
            {
                "title": "Article 2",
                "summary": "Machine learning" * 50,
                "link": "https://example.com/2",
                "keyword_score": 0.6
            }
        ]
        
        prioritized = curator.prioritize_learning_content(content_list)
        
        assert len(prioritized) == 2
        # Higher keyword score should be first
        assert prioritized[0]["keyword_score"] >= prioritized[1]["keyword_score"]
    
    def test_prioritize_learning_content_with_knowledge_gaps(self, curator):
        """Test prioritization with knowledge gaps"""
        content_list = [
            {
                "title": "Article 1",
                "summary": "Machine learning algorithms",
                "link": "https://example.com/1",
                "keyword_score": 0.6
            },
            {
                "title": "Article 2",
                "summary": "Ethics and transparency",
                "link": "https://example.com/2",
                "keyword_score": 0.8
            }
        ]
        
        knowledge_gaps = ["machine learning"]
        
        prioritized = curator.prioritize_learning_content(content_list, knowledge_gaps)
        
        assert len(prioritized) == 2
        # Article matching knowledge gap should be prioritized
        assert "machine learning" in prioritized[0]["summary"].lower()
    
    def test_prioritize_learning_content_empty_list(self, curator):
        """Test prioritization with empty list"""
        prioritized = curator.prioritize_learning_content([])
        
        assert len(prioritized) == 0
    
    def test_prioritize_learning_content_single_item(self, curator):
        """Test prioritization with single item"""
        content_list = [
            {
                "title": "Single Article",
                "summary": "Ethics in AI" * 50,
                "link": "https://example.com/single",
                "keyword_score": 0.8
            }
        ]
        
        prioritized = curator.prioritize_learning_content(content_list)
        
        assert len(prioritized) == 1
        assert prioritized[0]["title"] == "Single Article"
    
    def test_source_quality_tracking(self, curator):
        """Test source quality score tracking"""
        source = "https://example.com/source"
        
        # Update source quality
        curator.source_quality_scores[source] = 0.85
        
        # Check it's tracked
        assert source in curator.source_quality_scores
        assert curator.source_quality_scores[source] == 0.85
    
    def test_content_priorities_tracking(self, curator):
        """Test content priority tracking"""
        content_id = "content_123"
        
        # Update priority
        curator.content_priorities[content_id] = 0.9
        
        # Check it's tracked
        assert content_id in curator.content_priorities
        assert curator.content_priorities[content_id] == 0.9
    
    def test_pre_filter_content_missing_fields(self, curator):
        """Test pre-filter handles content with missing fields"""
        content_list = [
            {
                "title": "Article with missing summary",
                # Missing summary
                "link": "https://example.com/missing"
            }
        ]
        
        filtered, rejected = curator.pre_filter_content(content_list)
        
        # Should handle gracefully (likely rejected due to short length)
        assert isinstance(filtered, list)
        assert isinstance(rejected, list)
    
    def test_pre_filter_content_exact_length_threshold(self, curator):
        """Test pre-filter with content at exact length threshold"""
        # Create content exactly at minimum length
        title = "Test"
        summary = "A" * (MINIMUM_CONTENT_LENGTH - len(title) - 1)  # -1 for space
        content_list = [
            {
                "title": title,
                "summary": summary,
                "link": "https://example.com/exact"
            }
        ]
        
        filtered, rejected = curator.pre_filter_content(content_list)
        
        # Should pass length check (>= MINIMUM_CONTENT_LENGTH)
        # May still be rejected if keyword score is too low
        assert isinstance(filtered, list)
        assert isinstance(rejected, list)

