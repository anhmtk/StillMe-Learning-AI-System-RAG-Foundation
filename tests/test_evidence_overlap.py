"""
Tests for evidence overlap validator
"""

import pytest
from backend.validators.evidence_overlap import EvidenceOverlap, ngram_overlap


class TestNgramOverlap:
    """Test suite for ngram_overlap function"""
    
    def test_ngram_overlap_identical(self):
        """Test overlap with identical texts"""
        text_a = "This is a test sentence"
        text_b = "This is a test sentence"
        
        overlap = ngram_overlap(text_a, text_b, n=3)
        
        assert overlap == 1.0
    
    def test_ngram_overlap_partial(self):
        """Test overlap with partial match"""
        text_a = "This is a test sentence"
        text_b = "This is a different sentence"
        
        overlap = ngram_overlap(text_a, text_b, n=3)
        
        assert 0.0 < overlap < 1.0
    
    def test_ngram_overlap_no_match(self):
        """Test overlap with no match"""
        text_a = "This is a test sentence"
        text_b = "Completely different content here"
        
        overlap = ngram_overlap(text_a, text_b, n=3)
        
        assert overlap == 0.0
    
    def test_ngram_overlap_short_texts(self):
        """Test overlap with texts shorter than n"""
        text_a = "Short"
        text_b = "Text"
        
        overlap = ngram_overlap(text_a, text_b, n=3)
        
        assert overlap == 0.0


class TestEvidenceOverlap:
    """Test suite for EvidenceOverlap validator"""
    
    def test_evidence_overlap_pass(self):
        """Test overlap validator passes with sufficient overlap"""
        validator = EvidenceOverlap(threshold=0.01)
        
        answer = "This is a test answer with some content."
        ctx_docs = ["This is a test answer with some content."]
        
        result = validator.run(answer, ctx_docs)
        
        assert result.passed is True
        assert len(result.reasons) == 0
    
    def test_evidence_overlap_fail(self):
        """Test overlap validator fails with insufficient overlap"""
        validator = EvidenceOverlap(threshold=0.5)
        
        answer = "Completely different content here."
        ctx_docs = ["This is a test answer with some content."]
        
        result = validator.run(answer, ctx_docs)
        
        assert result.passed is False
        assert any("low_overlap" in r for r in result.reasons)
    
    def test_evidence_overlap_no_context(self):
        """Test overlap validator with no context docs"""
        validator = EvidenceOverlap(threshold=0.08)
        
        answer = "This is a test answer."
        ctx_docs = []
        
        result = validator.run(answer, ctx_docs)
        
        assert result.passed is False
        assert "no_context_docs" in result.reasons
    
    def test_evidence_overlap_multiple_docs(self):
        """Test overlap validator with multiple context docs"""
        validator = EvidenceOverlap(threshold=0.01)
        
        answer = "This is a test answer with some content."
        ctx_docs = [
            "Completely different content.",
            "This is a test answer with some content.",
            "Another different sentence."
        ]
        
        result = validator.run(answer, ctx_docs)
        
        # Should pass because second doc has high overlap
        assert result.passed is True
    
    def test_evidence_overlap_threshold(self):
        """Test overlap validator with different thresholds"""
        # Low threshold - should pass
        validator_low = EvidenceOverlap(threshold=0.01)
        answer = "This is a test."
        ctx_docs = ["This is a test."]
        
        result_low = validator_low.run(answer, ctx_docs)
        assert result_low.passed is True
        
        # High threshold - might fail
        validator_high = EvidenceOverlap(threshold=0.9)
        answer2 = "This is a test."
        ctx_docs2 = ["This is a test."]
        
        result_high = validator_high.run(answer2, ctx_docs2)
        # Should still pass for identical texts
        assert result_high.passed is True

