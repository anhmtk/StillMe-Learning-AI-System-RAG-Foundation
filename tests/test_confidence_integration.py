"""
Integration tests for ConfidenceValidator with ValidatorChain
Strict tests - no cheating
"""

import pytest
from backend.validators.chain import ValidatorChain
from backend.validators.citation import CitationRequired
from backend.validators.evidence_overlap import EvidenceOverlap
from backend.validators.confidence import ConfidenceValidator
from backend.validators.fallback_handler import FallbackHandler


class TestConfidenceIntegration:
    """Integration tests for confidence validation"""
    
    def test_chain_fails_when_no_uncertainty_no_context(self):
        """CRITICAL: Chain must fail when AI doesn't express uncertainty without context"""
        chain = ValidatorChain([
            CitationRequired(),
            EvidenceOverlap(threshold=0.01),
            ConfidenceValidator(require_uncertainty_when_no_context=True)
        ])
        
        # AI tries to answer confidently without context
        overconfident_answer = "The answer is definitely X based on my knowledge."
        ctx_docs = []  # NO CONTEXT
        
        result = chain.run(overconfident_answer, ctx_docs)
        
        assert result.passed is False, "MUST fail when overconfident without context"
        assert "missing_uncertainty_no_context" in result.reasons
    
    def test_chain_passes_when_uncertainty_expressed_no_context(self):
        """Chain should pass when AI correctly expresses uncertainty"""
        chain = ValidatorChain([
            CitationRequired(),
            EvidenceOverlap(threshold=0.01),
            ConfidenceValidator(require_uncertainty_when_no_context=True)
        ])
        
        # AI correctly expresses uncertainty
        uncertain_answer = "I don't have sufficient information in my knowledge base to answer this."
        ctx_docs = []  # NO CONTEXT
        
        result = chain.run(uncertain_answer, ctx_docs)
        
        # CitationRequired should pass (no context = no citation required)
        # EvidenceOverlap should pass (no context = no overlap check)
        # ConfidenceValidator should pass (uncertainty expressed)
        assert result.passed is True
    
    def test_chain_with_context_and_citation(self):
        """Chain should work normally when context exists"""
        chain = ValidatorChain([
            CitationRequired(),
            EvidenceOverlap(threshold=0.01),
            ConfidenceValidator(require_uncertainty_when_no_context=True)
        ])
        
        # Good answer with context and citation
        good_answer = "Based on the context [1], the answer is X."
        ctx_docs = ["Context document with relevant information about X."]
        
        result = chain.run(good_answer, ctx_docs)
        
        assert result.passed is True
    
    def test_fallback_handler_with_chain_failure(self):
        """Test FallbackHandler with chain validation failure"""
        handler = FallbackHandler()
        
        # Chain failed due to missing uncertainty
        validation_result = type('obj', (object,), {
            'passed': False,
            'reasons': ['missing_uncertainty_no_context']
        })()
        validation_result.passed = False
        validation_result.reasons = ['missing_uncertainty_no_context']
        
        original_answer = "The answer is definitely X."
        ctx_docs = []
        
        fallback = handler.get_fallback_answer(
            original_answer=original_answer,
            validation_result=validation_result,
            ctx_docs=ctx_docs,
            user_question="Test question",
            detected_lang="en"
        )
        
        # Fallback should be safe and informative
        assert len(fallback) > 50  # Should be substantial
        assert "stillme" in fallback.lower()
        assert "definitely X" not in fallback  # Should not contain hallucinated content
    
    def test_confidence_validator_does_not_break_existing_chain(self):
        """Test that ConfidenceValidator doesn't break existing chain behavior"""
        # Chain without ConfidenceValidator (old behavior)
        old_chain = ValidatorChain([
            CitationRequired(),
            EvidenceOverlap(threshold=0.01)
        ])
        
        # Chain with ConfidenceValidator (new behavior)
        new_chain = ValidatorChain([
            CitationRequired(),
            EvidenceOverlap(threshold=0.01),
            ConfidenceValidator(require_uncertainty_when_no_context=True)
        ])
        
        # Test with context - should behave the same
        answer = "Based on context [1], the answer is X."
        ctx_docs = ["Context document."]
        
        old_result = old_chain.run(answer, ctx_docs)
        new_result = new_chain.run(answer, ctx_docs)
        
        # Both should pass when context exists
        assert old_result.passed is True
        assert new_result.passed is True
    
    def test_confidence_validator_order_matters(self):
        """Test that validator order affects results"""
        # ConfidenceValidator first
        chain1 = ValidatorChain([
            ConfidenceValidator(require_uncertainty_when_no_context=True),
            CitationRequired(),
            EvidenceOverlap(threshold=0.01)
        ])
        
        # ConfidenceValidator last
        chain2 = ValidatorChain([
            CitationRequired(),
            EvidenceOverlap(threshold=0.01),
            ConfidenceValidator(require_uncertainty_when_no_context=True)
        ])
        
        # Overconfident answer without context
        answer = "The answer is definitely X."
        ctx_docs = []
        
        result1 = chain1.run(answer, ctx_docs)
        result2 = chain2.run(answer, ctx_docs)
        
        # Both should fail (order shouldn't matter for this case)
        assert result1.passed is False
        assert result2.passed is False
        assert "missing_uncertainty_no_context" in result1.reasons
        assert "missing_uncertainty_no_context" in result2.reasons

