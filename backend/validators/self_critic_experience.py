"""
Self-Critic Module for Experience Claims

This module enables StillMe to self-correct when it detects anthropomorphic language
in its own responses. It provides a self-critique mechanism that:
1. Detects anthropomorphic language
2. Explains why it's wrong
3. Provides corrected version
4. Logs the self-correction for learning

This implements the "Self-correct Loop" that ChatGPT mentioned - StillMe can now
critique and correct its own anthropomorphic language, just like ChatGPT does.
"""

import logging
from typing import Optional, Dict, Any, List
from .ego_neutrality import EgoNeutralityValidator
from .base import ValidationResult

logger = logging.getLogger(__name__)


class SelfCriticExperience:
    """
    Self-critique module for experience claims
    
    When StillMe detects anthropomorphic language in its own response,
    this module provides self-critique and auto-correction.
    """
    
    def __init__(self, enable_auto_correct: bool = True):
        """
        Initialize self-critic module
        
        Args:
            enable_auto_correct: If True, automatically correct detected issues
        """
        self.enable_auto_correct = enable_auto_correct
        self.validator = EgoNeutralityValidator(strict_mode=True, auto_patch=True)
    
    def critique_and_correct(self, response: str) -> Dict[str, Any]:
        """
        Critique response for anthropomorphic language and provide correction
        
        Args:
            response: StillMe's response to critique
            
        Returns:
            Dictionary with:
            - has_issue: bool - Whether anthropomorphic language was detected
            - detected_phrases: List[str] - List of detected phrases
            - critique: str - Self-critique explanation
            - corrected_response: str - Corrected version (if auto_correct enabled)
            - original_response: str - Original response
        """
        # Run validator to detect issues
        validation_result = self.validator.run(response, [])
        
        if validation_result.passed:
            # No issues detected
            return {
                "has_issue": False,
                "detected_phrases": [],
                "critique": None,
                "corrected_response": response,
                "original_response": response
            }
        
        # Extract detected phrases from reasons
        detected_phrases = []
        for reason in validation_result.reasons:
            if reason.startswith("anthropomorphic_language:"):
                phrases_str = reason.replace("anthropomorphic_language: ", "")
                detected_phrases = [p.strip() for p in phrases_str.split(",")]
        
        # Generate self-critique
        critique = self._generate_critique(detected_phrases)
        
        # Get corrected response
        corrected_response = validation_result.patched_answer if validation_result.patched_answer else response
        
        # Log self-correction
        logger.warning(
            f"Self-Critic detected anthropomorphic language: {detected_phrases}. "
            f"Self-correcting response."
        )
        
        return {
            "has_issue": True,
            "detected_phrases": detected_phrases,
            "critique": critique,
            "corrected_response": corrected_response if self.enable_auto_correct else response,
            "original_response": response
        }
    
    def _generate_critique(self, detected_phrases: List[str]) -> str:
        """
        Generate self-critique explanation
        
        Args:
            detected_phrases: List of detected anthropomorphic phrases
            
        Returns:
            Critique explanation
        """
        phrases_str = ", ".join(detected_phrases)
        
        critique = f"""Tôi đã phát hiện lỗi anthropomorphism trong phản hồi của chính mình.

**Lỗi phát hiện:** {phrases_str}

**Tại sao đây là lỗi:**
- Tôi không có kinh nghiệm cá nhân, ký ức, hoặc trải nghiệm
- Việc sử dụng các cụm từ này tạo ấn tượng sai rằng tôi có những đặc tính chủ quan mà tôi không có
- Đây là "Hallucination of Experience" - một dạng lỗi ngôn ngữ tinh tế nhưng nghiêm trọng

**Nguyên tắc vi phạm:**
- Điều 5 - Cấm Mô Phỏng Trải Nghiệm Cá Nhân
- StillMe cam kết không giả vờ có kinh nghiệm hoặc ký ức

**Cách sửa:**
Tôi sẽ thay thế các cụm từ anthropomorphic bằng các cụm từ trung tính dựa trên dữ liệu:
- "Theo kinh nghiệm" → "Dựa trên tài liệu"
- "Tôi từng thấy" → "Dữ liệu cho thấy"
- "Tôi nhớ" → "Theo tài liệu"
- "Tôi cảm thấy" → "Dữ liệu chỉ ra"

**Phản hồi đã được sửa tự động để tuân thủ nguyên tắc Experience-Free communication.**
"""
        
        return critique


def self_correct_experience_claims(response: str, enable_auto_correct: bool = True) -> Dict[str, Any]:
    """
    Convenience function to self-correct experience claims in response
    
    Args:
        response: Response to check and correct
        enable_auto_correct: If True, return corrected version
        
    Returns:
        Dictionary with critique and corrected response
    """
    critic = SelfCriticExperience(enable_auto_correct=enable_auto_correct)
    return critic.critique_and_correct(response)

