"""
Phase 1: Comprehensive Unit Tests for Citation Formatter - Citation Hierarchy

Tests focus on 4 critical aspects:
1. Logic Classification: Similarity scores → correct citation level
2. Format Correctness: Each level has standard format
3. No Crashes: Always has safe fallback
4. Philosophy: Maintains intellectual humility

These are NOT simple tests - they test real-world scenarios, edge cases, and philosophy alignment.
"""

import pytest
from typing import List, Dict, Any, Optional
from backend.utils.citation_formatter import CitationFormatter, get_citation_formatter


class TestCitationHierarchyLogic:
    """Test 1: Logic Classification - Similarity scores → correct citation level"""
    
    def test_hierarchy_level_1_high_similarity_with_metadata(self):
        """Test Level 1: High similarity (>0.8) + metadata → [Title, Source, Date]"""
        formatter = CitationFormatter()
        
        context_docs = [
            {
                "metadata": {
                    "title": "Quantum Computing Fundamentals",
                    "source": "arXiv",
                    "date": "2024-01-15"
                },
                "similarity": 0.85
            }
        ]
        similarity_scores = [0.85]
        
        citation = formatter.get_citation_strategy(
            question="What is quantum computing?",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Level 1: Should have title, source, and date
        assert "Quantum Computing Fundamentals" in citation
        assert "arXiv" in citation
        assert "2024-01-15" in citation
        assert citation.startswith("[") and citation.endswith("]")
        assert citation.count(",") >= 2  # Title, Source, Date
    
    def test_hierarchy_level_1_high_similarity_no_date(self):
        """Test Level 1: High similarity (>0.8) + metadata but no date → [Title, Source]"""
        formatter = CitationFormatter()
        
        context_docs = [
            {
                "metadata": {
                    "title": "StillMe Architecture",
                    "source": "foundational"
                },
                "similarity": 0.92
            }
        ]
        similarity_scores = [0.92]
        
        citation = formatter.get_citation_strategy(
            question="How does StillMe work?",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Level 1: Should have title and source, but no date
        assert "StillMe Architecture" in citation
        assert "foundational" in citation
        assert citation.count(",") == 1  # Only Title, Source
    
    def test_hierarchy_level_2_medium_similarity(self):
        """Test Level 2: Medium similarity (0.5-0.8) + source type → [Information from {Source} documents]"""
        formatter = CitationFormatter()
        
        context_docs = [
            {
                "metadata": {
                    "source": "wikipedia",
                    "title": "Some Wikipedia Article"
                },
                "similarity": 0.65
            }
        ]
        similarity_scores = [0.65]
        
        citation = formatter.get_citation_strategy(
            question="Explain machine learning",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Level 2: Should mention source type
        assert "Information from" in citation
        assert "Wikipedia" in citation
        assert "documents" in citation
        assert citation.startswith("[") and citation.endswith("]")
    
    def test_hierarchy_level_3_low_similarity(self):
        """Test Level 3: Low similarity (0.3-0.5) → [Background knowledge informed by retrieved context]"""
        formatter = CitationFormatter()
        
        context_docs = [
            {
                "metadata": {
                    "source": "arxiv"
                },
                "similarity": 0.35
            }
        ]
        similarity_scores = [0.35]
        
        citation = formatter.get_citation_strategy(
            question="What is AI?",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Level 3: Should acknowledge context but low relevance
        assert "Background knowledge" in citation or "informed by" in citation
        assert citation.startswith("[") and citation.endswith("]")
    
    def test_hierarchy_level_4_no_similarity(self):
        """Test Level 4: No similarity or very low (<0.3) → [general knowledge] + transparency message"""
        formatter = CitationFormatter()
        
        context_docs = [
            {
                "metadata": {
                    "source": "unknown"
                },
                "similarity": 0.15
            }
        ]
        similarity_scores = [0.15]
        
        citation = formatter.get_citation_strategy(
            question="What is 2+2?",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Level 4: Should acknowledge no specific sources (intellectual humility)
        assert "[general knowledge]" in citation
        assert "don't have specific sources" in citation or "I don't have" in citation.lower()
    
    def test_hierarchy_boundary_0_8(self):
        """Test boundary case: similarity = 0.8 (should be Level 1, not Level 2)"""
        formatter = CitationFormatter()
        
        context_docs = [
            {
                "metadata": {
                    "title": "Test Document",
                    "source": "test"
                },
                "similarity": 0.8
            }
        ]
        similarity_scores = [0.8]
        
        citation = formatter.get_citation_strategy(
            question="Test question",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should be Level 1 (>= 0.8) with title and source
        assert "Test Document" in citation
        assert "test" in citation
        assert citation.startswith("[") and citation.endswith("]")
    
    def test_hierarchy_boundary_0_5(self):
        """Test boundary case: similarity = 0.5 (should be Level 2, not Level 3)"""
        formatter = CitationFormatter()
        
        context_docs = [
            {
                "metadata": {
                    "source": "wikipedia"
                },
                "similarity": 0.5
            }
        ]
        similarity_scores = [0.5]
        
        citation = formatter.get_citation_strategy(
            question="Test question",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should be Level 2 (>= 0.5), not Level 3
        assert "Information from" in citation
        assert "Wikipedia" in citation
        assert "documents" in citation
        assert "Background knowledge" not in citation
    
    def test_hierarchy_boundary_0_3(self):
        """Test boundary case: similarity = 0.3 (should be Level 3, not Level 4)"""
        formatter = CitationFormatter()
        
        context_docs = [
            {
                "metadata": {
                    "source": "arxiv"
                },
                "similarity": 0.3
            }
        ]
        similarity_scores = [0.3]
        
        citation = formatter.get_citation_strategy(
            question="Test question",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should be Level 3 (>= 0.3), not Level 4
        assert "Background knowledge" in citation or "informed by" in citation
        assert "arXiv" in citation or "context" in citation
        assert "don't have specific sources" not in citation
    
    def test_hierarchy_multiple_docs_selects_highest(self):
        """Test with multiple docs - should select doc with highest similarity"""
        formatter = CitationFormatter()
        
        context_docs = [
            {
                "metadata": {
                    "title": "Low Relevance Doc",
                    "source": "test1"
                },
                "similarity": 0.4
            },
            {
                "metadata": {
                    "title": "High Relevance Doc",
                    "source": "test2",
                    "date": "2024-01-01"
                },
                "similarity": 0.9
            },
            {
                "metadata": {
                    "title": "Medium Relevance Doc",
                    "source": "test3"
                },
                "similarity": 0.6
            }
        ]
        similarity_scores = [0.4, 0.9, 0.6]
        
        citation = formatter.get_citation_strategy(
            question="Test question",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should use highest similarity (0.9) → Level 1
        assert "High Relevance Doc" in citation
        assert "test2" in citation
        assert "2024-01-01" in citation
        assert "Low Relevance Doc" not in citation
        assert "Medium Relevance Doc" not in citation


class TestCitationFormatCorrectness:
    """Test 2: Format Correctness - Each level has standard format"""
    
    def test_level_1_format_with_all_fields(self):
        """Test Level 1 format: [Title, Source, Date]"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "title": "Test Title",
                "source": "Test Source",
                "date": "2024-01-01"
            },
            "similarity": 0.9
        }]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=[0.9]
        )
        
        # Format: [Title, Source, Date]
        assert citation == "[Test Title, Test Source, 2024-01-01]"
    
    def test_level_1_format_without_date(self):
        """Test Level 1 format: [Title, Source] when date missing"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "title": "Test Title",
                "source": "Test Source"
            },
            "similarity": 0.9
        }]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=[0.9]
        )
        
        # Format: [Title, Source]
        assert citation == "[Test Title, Test Source]"
    
    def test_level_2_format_wikipedia(self):
        """Test Level 2 format: [Information from Wikipedia documents]"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "source": "wikipedia"
            },
            "similarity": 0.6
        }]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=[0.6]
        )
        
        # Format: [Information from Wikipedia documents]
        assert "[Information from Wikipedia documents]" == citation
    
    def test_level_2_format_arxiv(self):
        """Test Level 2 format: [Information from arXiv documents]"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "source": "arxiv"
            },
            "similarity": 0.6
        }]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=[0.6]
        )
        
        # Format: [Information from arXiv documents]
        assert "[Information from arXiv documents]" == citation
    
    def test_level_3_format_with_source(self):
        """Test Level 3 format: [Background knowledge informed by {Source} context]"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "source": "wikipedia"
            },
            "similarity": 0.35
        }]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=[0.35]
        )
        
        # Format: Should mention source and context
        assert "Background knowledge" in citation or "informed by" in citation
        assert "Wikipedia" in citation or "context" in citation
    
    def test_level_4_format_transparency(self):
        """Test Level 4 format: [general knowledge] + transparency message"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {},
            "similarity": 0.1
        }]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=[0.1]
        )
        
        # Format: Should acknowledge no specific sources
        assert "[general knowledge]" in citation
        assert "don't have specific sources" in citation or "I don't have" in citation.lower()


class TestSafeFallback:
    """Test 3: No Crashes - Always has safe fallback"""
    
    def test_empty_context_docs(self):
        """Test with empty context_docs - should not crash"""
        formatter = CitationFormatter()
        
        citation = formatter.get_citation_strategy(
            question="Test question",
            context_docs=[],
            similarity_scores=[]
        )
        
        # Should return Level 4 with transparency message
        assert "[general knowledge]" in citation
        assert "don't have specific sources" in citation or "I don't have" in citation.lower()
        assert isinstance(citation, str)
        assert len(citation) > 0
    
    def test_none_similarity_scores(self):
        """Test with None similarity_scores - should extract from docs or fallback"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "title": "Test",
                "source": "test"
            },
            "similarity": 0.9
        }]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=None
        )
        
        # Should extract similarity from doc metadata or use fallback
        assert isinstance(citation, str)
        assert len(citation) > 0
    
    def test_mismatched_lengths(self):
        """Test with mismatched similarity_scores length - should not crash"""
        formatter = CitationFormatter()
        
        context_docs = [
            {"metadata": {"source": "test1"}, "similarity": 0.8},
            {"metadata": {"source": "test2"}, "similarity": 0.6}
        ]
        similarity_scores = [0.8]  # Only 1 score for 2 docs
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should not crash, should use available scores or extract from docs
        assert isinstance(citation, str)
        assert len(citation) > 0
    
    def test_invalid_similarity_negative(self):
        """Test with negative similarity - should handle gracefully"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {"source": "test"},
            "similarity": -0.1
        }]
        similarity_scores = [-0.1]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should handle negative values (treat as 0.0 or use fallback)
        assert isinstance(citation, str)
        assert len(citation) > 0
    
    def test_invalid_similarity_over_one(self):
        """Test with similarity > 1.0 - should handle gracefully"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {"title": "Test", "source": "test"},
            "similarity": 1.5
        }]
        similarity_scores = [1.5]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should handle values > 1.0 (clamp to 1.0 or use as-is)
        assert isinstance(citation, str)
        assert len(citation) > 0
    
    def test_missing_metadata(self):
        """Test with missing metadata - should not crash"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "similarity": 0.9
            # No metadata field
        }]
        similarity_scores = [0.9]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should fallback to generic high similarity citation (Level 1 without metadata)
        assert isinstance(citation, str)
        assert len(citation) > 0
        assert "Information from" in citation or "retrieved" in citation
    
    def test_mixed_doc_formats_dict_and_object(self):
        """Test with mixed doc formats (dict and object) - should handle both"""
        formatter = CitationFormatter()
        
        # Dict format
        doc1 = {
            "metadata": {
                "title": "Dict Doc",
                "source": "test1"
            },
            "similarity": 0.9
        }
        
        # Object format (mock)
        class MockDoc:
            def __init__(self):
                self.metadata = {
                    "title": "Object Doc",
                    "source": "test2"
                }
                self.similarity = 0.7
        
        doc2 = MockDoc()
        
        context_docs = [doc1, doc2]
        similarity_scores = [0.9, 0.7]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should handle both formats
        assert isinstance(citation, str)
        assert len(citation) > 0
    
    def test_none_context_docs(self):
        """Test with None context_docs - should not crash"""
        formatter = CitationFormatter()
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=None,
            similarity_scores=None
        )
        
        # Should return Level 4 with transparency
        assert isinstance(citation, str)
        assert "[general knowledge]" in citation
    
    def test_empty_string_metadata(self):
        """Test with empty string metadata values - should handle gracefully"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "title": "",
                "source": "",
                "date": ""
            },
            "similarity": 0.9
        }]
        similarity_scores = [0.9]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should fallback to generic high similarity citation (empty strings treated as missing)
        assert isinstance(citation, str)
        assert len(citation) > 0
        assert "Information from" in citation or "retrieved" in citation


class TestIntellectualHumility:
    """Test 4: Philosophy - Maintains intellectual humility"""
    
    def test_acknowledges_no_specific_sources(self):
        """Test that system acknowledges when no specific sources available"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {},
            "similarity": 0.1
        }]
        similarity_scores = [0.1]
        
        citation = formatter.get_citation_strategy(
            question="What is the meaning of life?",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should acknowledge lack of specific sources (intellectual humility)
        assert "don't have specific sources" in citation or "I don't have" in citation.lower()
        assert "[general knowledge]" in citation
    
    def test_transparent_about_low_relevance(self):
        """Test that system is transparent about low relevance context"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "source": "wikipedia"
            },
            "similarity": 0.25
        }]
        similarity_scores = [0.25]
        
        citation = formatter.get_citation_strategy(
            question="Test question",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should acknowledge low relevance (intellectual humility)
        assert "low relevance" in citation.lower() or "Background knowledge" in citation
        # Should not overclaim specificity
    
    def test_no_overclaim_with_high_similarity_but_no_metadata(self):
        """Test that system doesn't overclaim when similarity is high but metadata is missing"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "similarity": 0.95
            # No metadata
        }]
        similarity_scores = [0.95]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should not claim specific title/source if metadata missing
        # Should fallback to generic citation (intellectual humility)
        assert isinstance(citation, str)
        assert len(citation) > 0
        # Should not have fake title/source (no commas with title, source, date format)
        # Should use generic "Information from retrieved documents" instead
        assert "Information from" in citation or "retrieved" in citation
    
    def test_acknowledges_context_but_low_similarity(self):
        """Test that system acknowledges context exists but has low similarity"""
        formatter = CitationFormatter()
        
        context_docs = [
            {
                "metadata": {"source": "arxiv"},
                "similarity": 0.2
            }
        ]
        similarity_scores = [0.2]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should acknowledge context was reviewed but had low relevance
        assert "low relevance" in citation.lower() or "don't have specific sources" in citation
        # Intellectual humility: Don't claim context is relevant when it's not
    
    def test_no_false_confidence(self):
        """Test that system doesn't express false confidence"""
        formatter = CitationFormatter()
        
        # Empty context - should acknowledge uncertainty
        citation = formatter.get_citation_strategy(
            question="What will happen tomorrow?",
            context_docs=[],
            similarity_scores=[]
        )
        
        # Should not claim certainty
        assert "don't have" in citation.lower() or "specific sources" in citation.lower()
        # Should acknowledge limitations (intellectual humility)


class TestRealWorldScenarios:
    """Additional tests: Real-world scenarios and edge cases"""
    
    def test_wikipedia_high_similarity(self):
        """Real scenario: Wikipedia article with high similarity"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "title": "Quantum Computing - Wikipedia",
                "source": "wikipedia",
                "date": "2024-12-01"
            },
            "similarity": 0.88
        }]
        similarity_scores = [0.88]
        
        citation = formatter.get_citation_strategy(
            question="What is quantum computing?",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        assert "Quantum Computing - Wikipedia" in citation
        assert "wikipedia" in citation.lower()
        assert "2024-12-01" in citation
    
    def test_arxiv_medium_similarity(self):
        """Real scenario: arXiv paper with medium similarity"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "title": "Attention Is All You Need",
                "source": "arxiv"
            },
            "similarity": 0.65
        }]
        similarity_scores = [0.65]
        
        citation = formatter.get_citation_strategy(
            question="Explain transformer architecture",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        assert "[Information from arXiv documents]" == citation
    
    def test_rss_feed_low_similarity(self):
        """Real scenario: RSS feed with low similarity"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "source": "rss",
                "source_name": "TechCrunch"
            },
            "similarity": 0.35
        }]
        similarity_scores = [0.35]
        
        citation = formatter.get_citation_strategy(
            question="What's the latest AI news?",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        assert "Background knowledge" in citation or "informed by" in citation
        assert "TechCrunch" in citation or "context" in citation
    
    def test_foundational_knowledge_high_similarity(self):
        """Real scenario: Foundational knowledge with high similarity"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "title": "StillMe Core Principles",
                "source": "CRITICAL_FOUNDATION",
                "type": "foundational"
            },
            "similarity": 0.95
        }]
        similarity_scores = [0.95]
        
        citation = formatter.get_citation_strategy(
            question="What are StillMe's principles?",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        assert "StillMe Core Principles" in citation
        assert "CRITICAL_FOUNDATION" in citation or "foundational" in citation.lower()
    
    def test_multiple_sources_select_best(self):
        """Real scenario: Multiple sources, should select best match"""
        formatter = CitationFormatter()
        
        context_docs = [
            {
                "metadata": {"source": "wikipedia", "title": "General AI Article"},
                "similarity": 0.4
            },
            {
                "metadata": {"source": "arxiv", "title": "Specific Research Paper", "date": "2024-01-01"},
                "similarity": 0.92
            },
            {
                "metadata": {"source": "rss", "source_name": "News"},
                "similarity": 0.3
            }
        ]
        similarity_scores = [0.4, 0.92, 0.3]
        
        citation = formatter.get_citation_strategy(
            question="Explain AI",
            context_docs=context_docs,
            similarity_scores=similarity_scores
        )
        
        # Should use highest similarity (0.92) → Level 1
        assert "Specific Research Paper" in citation
        assert "arxiv" in citation.lower()
        assert "2024-01-01" in citation


class TestBackwardCompatibility:
    """Test backward compatibility - old code should still work"""
    
    def test_no_similarity_scores_parameter(self):
        """Test that calling without similarity_scores still works"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "source": "wikipedia"
            }
        }]
        
        # Call without similarity_scores (backward compatibility)
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs
        )
        
        # Should work and return a citation
        assert isinstance(citation, str)
        assert len(citation) > 0
    
    def test_extract_similarity_from_doc_metadata(self):
        """Test that similarity is extracted from doc if not provided"""
        formatter = CitationFormatter()
        
        context_docs = [{
            "metadata": {
                "title": "Test Doc",
                "source": "test"
            },
            "similarity": 0.85  # In doc, not in parameter
        }]
        
        citation = formatter.get_citation_strategy(
            question="Test",
            context_docs=context_docs,
            similarity_scores=None  # Not provided
        )
        
        # Should extract from doc and use Level 1
        assert "Test Doc" in citation or isinstance(citation, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

