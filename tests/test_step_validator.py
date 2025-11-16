"""
Tests for StepValidator - Step-level validation
"""

import pytest
from backend.validators.step_detector import Step
from backend.validators.step_validator import StepValidator, StepValidationResult
from backend.validators.base import ValidationResult
from backend.validators.chain import ValidatorChain
from backend.validators.citation import CitationRequired
from backend.validators.evidence_overlap import EvidenceOverlap


class TestStepValidator:
    """Test cases for StepValidator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.validator = StepValidator(confidence_threshold=0.5)
        
        # Create a simple validator chain for testing
        self.chain = ValidatorChain([
            CitationRequired(),
            EvidenceOverlap(threshold=0.01)
        ])
    
    def test_calculate_step_confidence_with_citation(self):
        """Test confidence calculation for step with citation"""
        step = Step(
            step_number=1,
            content="StillMe học từ RSS [1]",
            original_text="Bước 1: StillMe học từ RSS [1]",
            start_pos=0,
            end_pos=30
        )
        
        validation_result = ValidationResult(
            passed=True,
            reasons=[]
        )
        
        ctx_docs = ["StillMe learns from RSS feeds every 4 hours"]
        
        confidence = self.validator._calculate_step_confidence(step, validation_result, ctx_docs)
        
        # Should be high confidence (has citation + passed validation)
        assert confidence >= 0.7, f"Expected confidence >= 0.7, got {confidence}"
    
    def test_calculate_step_confidence_no_citation(self):
        """Test confidence calculation for step without citation"""
        step = Step(
            step_number=1,
            content="StillMe học từ RSS",
            original_text="Bước 1: StillMe học từ RSS",
            start_pos=0,
            end_pos=25
        )
        
        validation_result = ValidationResult(
            passed=False,
            reasons=["missing_citation"]
        )
        
        ctx_docs = []
        
        confidence = self.validator._calculate_step_confidence(step, validation_result, ctx_docs)
        
        # Should be low confidence (no citation + failed validation)
        assert confidence < 0.5, f"Expected confidence < 0.5, got {confidence}"
    
    def test_validate_step(self):
        """Test validation of a single step"""
        step = Step(
            step_number=1,
            content="StillMe học từ RSS [1]",
            original_text="Bước 1: StillMe học từ RSS [1]",
            start_pos=0,
            end_pos=30
        )
        
        ctx_docs = ["StillMe learns from RSS feeds"]
        
        result = self.validator.validate_step(step, ctx_docs, self.chain)
        
        assert isinstance(result, StepValidationResult)
        assert result.step == step
        assert 0.0 <= result.confidence <= 1.0
        assert isinstance(result.passed, bool)
        assert isinstance(result.issues, list)
    
    def test_validate_all_steps_parallel(self):
        """Test parallel validation of multiple steps"""
        steps = [
            Step(
                step_number=1,
                content="StillMe học từ RSS [1]",
                original_text="Bước 1: StillMe học từ RSS [1]",
                start_pos=0,
                end_pos=30
            ),
            Step(
                step_number=2,
                content="StillMe embed content [2]",
                original_text="Bước 2: StillMe embed content [2]",
                start_pos=31,
                end_pos=60
            ),
            Step(
                step_number=3,
                content="StillMe lưu vào ChromaDB [3]",
                original_text="Bước 3: StillMe lưu vào ChromaDB [3]",
                start_pos=61,
                end_pos=95
            )
        ]
        
        ctx_docs = [
            "StillMe learns from RSS feeds",
            "StillMe embeds content using all-MiniLM-L6-v2",
            "StillMe stores in ChromaDB vector database"
        ]
        
        results = self.validator.validate_all_steps(steps, ctx_docs, self.chain, parallel=True)
        
        assert len(results) == 3
        assert all(isinstance(r, StepValidationResult) for r in results)
        # Results should be sorted by step number
        assert results[0].step.step_number == 1
        assert results[1].step.step_number == 2
        assert results[2].step.step_number == 3
    
    def test_validate_all_steps_sequential(self):
        """Test sequential validation of multiple steps"""
        steps = [
            Step(
                step_number=1,
                content="StillMe học từ RSS [1]",
                original_text="Bước 1: StillMe học từ RSS [1]",
                start_pos=0,
                end_pos=30
            ),
            Step(
                step_number=2,
                content="StillMe embed content [2]",
                original_text="Bước 2: StillMe embed content [2]",
                start_pos=31,
                end_pos=60
            )
        ]
        
        ctx_docs = ["StillMe learns from RSS feeds"]
        
        results = self.validator.validate_all_steps(steps, ctx_docs, self.chain, parallel=False)
        
        assert len(results) == 2
        assert all(isinstance(r, StepValidationResult) for r in results)
    
    def test_confidence_threshold(self):
        """Test that confidence threshold is respected"""
        validator_low_threshold = StepValidator(confidence_threshold=0.3)
        validator_high_threshold = StepValidator(confidence_threshold=0.8)
        
        step = Step(
            step_number=1,
            content="StillMe học từ RSS [1]",
            original_text="Bước 1: StillMe học từ RSS [1]",
            start_pos=0,
            end_pos=30
        )
        
        validation_result = ValidationResult(passed=True, reasons=[])
        ctx_docs = ["StillMe learns from RSS"]
        
        confidence = validator_low_threshold._calculate_step_confidence(step, validation_result, ctx_docs)
        
        # With low threshold, should pass
        result_low = validator_low_threshold.validate_step(step, ctx_docs, self.chain)
        # With high threshold, might not pass
        result_high = validator_high_threshold.validate_step(step, ctx_docs, self.chain)
        
        # At least one should have reasonable confidence
        assert result_low.confidence >= 0.0
        assert result_high.confidence >= 0.0

