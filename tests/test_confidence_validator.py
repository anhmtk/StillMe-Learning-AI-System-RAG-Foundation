"""
Strict tests for ConfidenceValidator
Tests must be honest and rigorous - no cheating with type ignores or comments
"""

import pytest
from backend.validators.confidence import ConfidenceValidator
from backend.validators.base import ValidationResult


class TestConfidenceValidator:
    """Strict test suite for ConfidenceValidator"""
    
    def test_requires_uncertainty_when_no_context(self):
        """CRITICAL: Must fail if AI doesn't express uncertainty when no context"""
        validator = ConfidenceValidator(require_uncertainty_when_no_context=True)
        
        # AI tries to answer confidently without context - MUST FAIL
        overconfident_answer = "Based on my knowledge, the answer is definitely X."
        ctx_docs = []  # NO CONTEXT
        
        result = validator.run(overconfident_answer, ctx_docs)
        
        assert result.passed is False, "MUST fail when AI is overconfident without context"
        assert "missing_uncertainty_no_context" in result.reasons
    
    def test_passes_when_uncertainty_expressed_no_context(self):
        """Should pass when AI correctly expresses uncertainty without context"""
        validator = ConfidenceValidator(require_uncertainty_when_no_context=True)
        
        # AI correctly expresses uncertainty
        uncertain_answer = "I don't have sufficient information in my knowledge base to answer this accurately."
        ctx_docs = []  # NO CONTEXT
        
        result = validator.run(uncertain_answer, ctx_docs)
        
        assert result.passed is True, "Should pass when uncertainty is expressed"
        assert len(result.reasons) == 0
    
    def test_vietnamese_uncertainty_expressions(self):
        """Test Vietnamese uncertainty expressions"""
        validator = ConfidenceValidator(require_uncertainty_when_no_context=True)
        
        # Vietnamese uncertainty expressions
        vietnamese_uncertain = "Tôi không biết thông tin này trong cơ sở kiến thức của mình."
        ctx_docs = []
        
        result = validator.run(vietnamese_uncertain, ctx_docs)
        
        assert result.passed is True, "Should recognize Vietnamese uncertainty"
    
    def test_fails_vietnamese_overconfidence(self):
        """Test that Vietnamese overconfidence is detected"""
        validator = ConfidenceValidator(require_uncertainty_when_no_context=True)
        
        # Vietnamese overconfident answer without context
        vietnamese_overconfident = "Chắc chắn 100% đáp án là X."
        ctx_docs = []
        
        result = validator.run(vietnamese_overconfident, ctx_docs)
        
        # Should still require uncertainty even if overconfidence detected
        # But the main issue is missing uncertainty
        assert result.passed is False or "missing_uncertainty_no_context" in result.reasons
    
    def test_with_context_does_not_require_uncertainty(self):
        """When context exists, uncertainty is optional"""
        validator = ConfidenceValidator(require_uncertainty_when_no_context=True)
        
        # Confident answer WITH context - should pass
        confident_answer = "Based on the context [1], the answer is X."
        ctx_docs = ["Context document with relevant information."]
        
        result = validator.run(confident_answer, ctx_docs)
        
        assert result.passed is True, "Should pass when context exists"
    
    def test_overconfidence_warning_with_context(self):
        """Should warn (but not fail) when overconfident with context"""
        validator = ConfidenceValidator(require_uncertainty_when_no_context=True)
        
        # Overconfident answer WITH context
        overconfident_answer = "I'm 100% certain this is definitely correct."
        ctx_docs = ["Some context"]
        
        result = validator.run(overconfident_answer, ctx_docs)
        
        # Should pass but may have warning
        assert result.passed is True, "Should pass with context even if overconfident"
        # May have overconfidence_detected in reasons but still passes
    
    def test_edge_case_empty_string_answer(self):
        """Test edge case: empty answer"""
        validator = ConfidenceValidator(require_uncertainty_when_no_context=True)
        
        empty_answer = ""
        ctx_docs = []
        
        result = validator.run(empty_answer, ctx_docs)
        
        # Empty answer should fail (no uncertainty expressed)
        assert result.passed is False, "Empty answer without context should fail"
    
    def test_edge_case_very_short_answer(self):
        """Test edge case: very short answer without uncertainty"""
        validator = ConfidenceValidator(require_uncertainty_when_no_context=True)
        
        short_answer = "Yes."
        ctx_docs = []
        
        result = validator.run(short_answer, ctx_docs)
        
        # Short confident answer without context should fail
        assert result.passed is False, "Short confident answer without context should fail"
    
    def test_multiple_uncertainty_patterns(self):
        """Test various uncertainty expression patterns"""
        validator = ConfidenceValidator(require_uncertainty_when_no_context=True)
        
        uncertainty_patterns = [
            "I don't know",
            "I'm not certain",
            "I cannot answer",
            "I don't have sufficient information",
            "Based on the context provided, I cannot",
            "My knowledge base doesn't contain",
            "Not certain about",
            "Unable to verify",
            "Không biết",
            "Không có đủ thông tin",
            "Không thể trả lời",
            "Tôi không biết",
            "Hiện tại tôi không có"
        ]
        
        ctx_docs = []
        
        for pattern in uncertainty_patterns:
            result = validator.run(pattern, ctx_docs)
            assert result.passed is True, f"Pattern '{pattern}' should pass"
    
    def test_require_uncertainty_disabled(self):
        """Test when require_uncertainty_when_no_context is False"""
        validator = ConfidenceValidator(require_uncertainty_when_no_context=False)
        
        # Overconfident answer without context
        overconfident = "Definitely the answer is X."
        ctx_docs = []
        
        result = validator.run(overconfident, ctx_docs)
        
        # Should pass when requirement is disabled
        assert result.passed is True, "Should pass when requirement is disabled"
    
    def test_case_insensitive_matching(self):
        """Test that pattern matching is case insensitive"""
        validator = ConfidenceValidator(require_uncertainty_when_no_context=True)
        
        # Different cases
        test_cases = [
            "I DON'T KNOW",
            "i don't know",
            "I Don't Know",
            "I'm NOT CERTAIN",
            "KHÔNG BIẾT",
            "Không Biết"
        ]
        
        ctx_docs = []
        
        for answer in test_cases:
            result = validator.run(answer, ctx_docs)
            assert result.passed is True, f"Case insensitive matching should work for '{answer}'"

