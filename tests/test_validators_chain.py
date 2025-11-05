"""
Tests for validator chain
"""

import pytest
from backend.validators.chain import ValidatorChain
from backend.validators.citation import CitationRequired
from backend.validators.evidence_overlap import EvidenceOverlap
from backend.validators.numeric import NumericUnitsBasic
from backend.validators.base import ValidationResult


class TestValidatorChain:
    """Test suite for ValidatorChain"""
    
    def test_chain_pass_all(self):
        """Test chain passes when all validators pass"""
        chain = ValidatorChain([
            CitationRequired(),
            EvidenceOverlap(threshold=0.01),  # Low threshold for test
            NumericUnitsBasic()
        ])
        
        answer = "This is a test answer [1] with some content."
        ctx_docs = ["This is a test answer with some content."]
        
        result = chain.run(answer, ctx_docs)
        
        assert result.passed is True
        assert len(result.reasons) == 0
    
    def test_chain_fail_citation(self):
        """Test chain fails when citation validator fails"""
        chain = ValidatorChain([
            CitationRequired(),
            EvidenceOverlap(threshold=0.01),
            NumericUnitsBasic()
        ])
        
        answer = "This is a test answer without citation."
        ctx_docs = ["This is a test answer with some content."]
        
        result = chain.run(answer, ctx_docs)
        
        assert result.passed is False
        assert "missing_citation" in result.reasons
    
    def test_chain_fail_overlap(self):
        """Test chain fails when overlap validator fails"""
        chain = ValidatorChain([
            CitationRequired(required=False),  # Disable citation for this test
            EvidenceOverlap(threshold=0.5),  # High threshold
            NumericUnitsBasic()
        ])
        
        answer = "Completely different content here."
        ctx_docs = ["This is a test answer with some content."]
        
        result = chain.run(answer, ctx_docs)
        
        assert result.passed is False
        assert any("low_overlap" in r for r in result.reasons)
    
    def test_chain_with_patched_answer(self):
        """Test chain handles patched answers"""
        # Create a validator that provides patched answer
        class MockValidator:
            def run(self, answer, ctx_docs):
                return ValidationResult(
                    passed=False,
                    reasons=["test_reason"],
                    patched_answer=answer + " [PATCHED]"
                )
        
        chain = ValidatorChain([
            CitationRequired(required=False),
            MockValidator(),
            NumericUnitsBasic()
        ])
        
        answer = "Test answer"
        ctx_docs = ["Test context"]
        
        result = chain.run(answer, ctx_docs)
        
        # Should use patched answer and continue
        assert result.passed is True  # Chain continues with patched answer
        assert "[PATCHED]" in (result.patched_answer or answer)
    
    def test_chain_empty_validators(self):
        """Test chain with empty validators list"""
        chain = ValidatorChain([])
        
        answer = "Test answer"
        ctx_docs = ["Test context"]
        
        result = chain.run(answer, ctx_docs)
        
        assert result.passed is True
        assert len(result.reasons) == 0

