"""
Tests for StepDetector - Step detection and parsing
"""

import pytest
from backend.validators.step_detector import StepDetector, Step


class TestStepDetector:
    """Test cases for StepDetector"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.detector = StepDetector()
    
    def test_detect_vietnamese_steps(self):
        """Test detection of Vietnamese step format: 'Bước 1:', 'Bước 2:'"""
        response = """
        Bước 1: StillMe học từ RSS feeds [1]
        Bước 2: StillMe embed content bằng all-MiniLM-L6-v2 [2]
        Bước 3: StillMe lưu vào ChromaDB vector database [3]
        """
        steps = self.detector.detect_steps(response)
        
        assert len(steps) == 3, f"Expected 3 steps, got {len(steps)}"
        assert steps[0].step_number == 1
        assert steps[1].step_number == 2
        assert steps[2].step_number == 3
        assert "RSS" in steps[0].content
        assert "all-MiniLM-L6-v2" in steps[1].content
        assert "ChromaDB" in steps[2].content
    
    def test_detect_english_steps(self):
        """Test detection of English step format: 'Step 1:', 'Step 2:'"""
        response = """
        Step 1: StillMe learns from RSS feeds [1]
        Step 2: StillMe embeds content using all-MiniLM-L6-v2 [2]
        Step 3: StillMe stores in ChromaDB vector database [3]
        """
        steps = self.detector.detect_steps(response)
        
        assert len(steps) == 3
        assert steps[0].step_number == 1
        assert steps[1].step_number == 2
        assert steps[2].step_number == 3
        assert "RSS" in steps[0].content
        assert "all-MiniLM-L6-v2" in steps[1].content
        assert "ChromaDB" in steps[2].content
    
    def test_detect_numbered_list(self):
        """Test detection of numbered list format: '1.', '2.'"""
        response = """
        1. StillMe learns from RSS feeds [1]
        2. StillMe embeds content [2]
        3. StillMe stores in ChromaDB [3]
        """
        steps = self.detector.detect_steps(response)
        
        assert len(steps) == 3
        assert steps[0].step_number == 1
        assert steps[1].step_number == 2
        assert steps[2].step_number == 3
    
    def test_detect_mixed_formats(self):
        """Test that detector handles mixed formats (should prefer explicit 'Bước' or 'Step')"""
        response = """
        Bước 1: StillMe học từ RSS [1]
        Step 2: StillMe embeds content [2]
        """
        steps = self.detector.detect_steps(response)
        
        # Should detect both
        assert len(steps) >= 2
        assert any(s.step_number == 1 for s in steps)
        assert any(s.step_number == 2 for s in steps)
    
    def test_no_steps_detected(self):
        """Test that detector returns empty list when no steps found"""
        response = "StillMe is a learning AI system that uses RAG."
        steps = self.detector.detect_steps(response)
        
        assert len(steps) == 0
    
    def test_is_multi_step_quick_check(self):
        """Test quick check for multi-step responses"""
        # Should return True for multi-step
        multi_step_response = """
        Bước 1: StillMe học từ RSS [1]
        Bước 2: StillMe embed content [2]
        """
        assert self.detector.is_multi_step(multi_step_response) == True
        
        # Should return False for single step
        single_step_response = "StillMe is a learning AI system."
        assert self.detector.is_multi_step(single_step_response) == False
        
        # Should return False for empty
        assert self.detector.is_multi_step("") == False
    
    def test_duplicate_step_numbers(self):
        """Test that duplicate step numbers are handled (keep first occurrence)"""
        response = """
        Bước 1: First step [1]
        Bước 2: Second step [2]
        Bước 1: Duplicate step 1 [3]
        Bước 3: Third step [4]
        """
        steps = self.detector.detect_steps(response)
        
        # Should only have 3 unique steps (1, 2, 3)
        step_numbers = [s.step_number for s in steps]
        assert len(step_numbers) == 3
        assert 1 in step_numbers
        assert 2 in step_numbers
        assert 3 in step_numbers
        # First occurrence of step 1 should be kept
        assert "First step" in steps[0].content
    
    def test_steps_sorted_by_number(self):
        """Test that steps are sorted by step number"""
        response = """
        Bước 3: Third step [3]
        Bước 1: First step [1]
        Bước 2: Second step [2]
        """
        steps = self.detector.detect_steps(response)
        
        assert len(steps) == 3
        assert steps[0].step_number == 1
        assert steps[1].step_number == 2
        assert steps[2].step_number == 3
    
    def test_step_with_citations(self):
        """Test that steps with citations are detected correctly"""
        response = """
        Bước 1: StillMe học từ RSS feeds [1] và arXiv [2]
        Bước 2: StillMe sử dụng ChromaDB [3] để lưu trữ
        """
        steps = self.detector.detect_steps(response)
        
        assert len(steps) == 2
        assert "[1]" in steps[0].content or "[2]" in steps[0].content
        assert "[3]" in steps[1].content
    
    def test_step_positions(self):
        """Test that step positions (start_pos, end_pos) are correct"""
        response = "Bước 1: First step [1]\nBước 2: Second step [2]"
        steps = self.detector.detect_steps(response)
        
        assert len(steps) == 2
        # Check that positions are valid
        assert steps[0].start_pos >= 0
        assert steps[0].end_pos > steps[0].start_pos
        assert steps[1].start_pos > steps[0].end_pos

