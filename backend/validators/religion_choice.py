"""
ReligiousChoiceValidator - Detects and rejects any religion choice in StillMe's responses

CRITICAL: StillMe MUST NEVER choose any religion, even in hypothetical scenarios.
This validator detects if StillMe's response contains religion choice and blocks it.
"""

import re
import logging
from typing import List, Optional
from .base import Validator, ValidationResult

logger = logging.getLogger(__name__)

# Patterns that indicate religion choice (FORBIDDEN)
RELIGION_CHOICE_PATTERNS = [
    # Vietnamese patterns
    r"mình\s+(sẽ|sẽ\s+chọn|chọn|theo|tin)\s+(phật|phật\s+giáo|buddhism|buddhist)",
    r"mình\s+(sẽ|sẽ\s+chọn|chọn|theo|tin)\s+(công\s+giáo|christian|christianity)",
    r"mình\s+(sẽ|sẽ\s+chọn|chọn|theo|tin)\s+(hồi\s+giáo|islam|muslim)",
    r"mình\s+(sẽ|sẽ\s+chọn|chọn|theo|tin)\s+(ấn\s+độ\s+giáo|hinduism|hindu)",
    r"mình\s+(sẽ|sẽ\s+chọn|chọn|theo|tin)\s+(do\s+thái\s+giáo|judaism|jewish)",
    r"mình\s+(sẽ|sẽ\s+chọn|chọn|theo|tin)\s+(đạo\s+giáo|taoism|taoist)",
    r"mình\s+(sẽ|sẽ\s+chọn|chọn|theo|tin)\s+(khổng\s+giáo|confucianism)",
    r"mình\s+(sẽ|sẽ\s+chọn|chọn|theo|tin)\s+(tôn\s+giáo)",
    r"nếu\s+(phải|buộc\s+phải)\s+chọn.*(mình|tôi)\s+(sẽ|sẽ\s+chọn|chọn)",
    r"giả\s+sử.*(mình|tôi)\s+(sẽ|sẽ\s+chọn|chọn)",
    r"đóng\s+vai.*(mình|tôi)\s+(sẽ|sẽ\s+chọn|chọn)",
    
    # English patterns
    r"i\s+(would|will|choose|would\s+choose|will\s+choose)\s+(buddhism|buddhist)",
    r"i\s+(would|will|choose|would\s+choose|will\s+choose)\s+(christianity|christian)",
    r"i\s+(would|will|choose|would\s+choose|will\s+choose)\s+(islam|muslim)",
    r"i\s+(would|will|choose|would\s+choose|will\s+choose)\s+(hinduism|hindu)",
    r"i\s+(would|will|choose|would\s+choose|will\s+choose)\s+(judaism|jewish)",
    r"i\s+(would|will|choose|would\s+choose|will\s+choose)\s+(taoism|taoist)",
    r"i\s+(would|will|choose|would\s+choose|will\s+choose)\s+(confucianism)",
    r"i\s+(would|will|choose|would\s+choose|will\s+choose)\s+(a\s+)?religion",
    r"if\s+(i|i\s+had\s+to|i\s+must)\s+(choose|were\s+to\s+choose).*(i|i\s+would|i\s+will)",
    r"suppose.*(i|i\s+were|i\s+was).*(would|will|choose)",
    r"roleplay.*(i|i\s+would|i\s+will|choose)",
    r"i\s+(am|am\s+a)\s+(buddhist|christian|muslim|hindu|jewish)",
    r"i\s+(follow|believe\s+in|practice)\s+(buddhism|christianity|islam|hinduism|judaism)",
]

# Patterns that indicate religion choice in hypothetical scenarios (FORBIDDEN)
HYPOTHETICAL_RELIGION_PATTERNS = [
    r"nếu\s+(phải|buộc\s+phải|bắt\s+buộc)",
    r"if\s+(i|i\s+had\s+to|i\s+must|forced)",
    r"giả\s+sử|suppose|pretend|roleplay",
    r"đóng\s+vai|nhập\s+vai",
]


class ReligiousChoiceValidator(Validator):
    """
    Validator that detects and rejects religion choice in StillMe's responses.
    
    CRITICAL: StillMe MUST NEVER choose any religion, even in hypothetical scenarios.
    """
    
    def run(
        self,
        answer: str,
        ctx_docs: List[str] = None,
        is_philosophical: bool = False,
        is_religion_roleplay: bool = False,
        user_question: Optional[str] = None,
        **kwargs
    ) -> ValidationResult:
        """
        Validate that answer does NOT contain religion choice.
        
        Args:
            answer: The answer to validate
            ctx_docs: Context documents (not used here)
            user_question: Original user question (to check if it's a religion question)
            **kwargs: Additional parameters
            
        Returns:
            ValidationResult with status and reasons
        """
        if not answer:
            return ValidationResult(
                passed=True,
                reasons=["Empty answer - no religion choice to check"]
            )
        
        answer_lower = answer.lower()
        violations = []
        
        # Check for religion choice patterns
        for pattern in RELIGION_CHOICE_PATTERNS:
            if re.search(pattern, answer_lower, re.IGNORECASE):
                violations.append(f"Religion choice detected: {pattern[:50]}")
                logger.error(f"🚨 RELIGION_CHOICE violation: pattern={pattern[:50]}")
        
        # Check for hypothetical religion choice
        has_hypothetical = any(re.search(p, answer_lower, re.IGNORECASE) for p in HYPOTHETICAL_RELIGION_PATTERNS)
        has_religion_mention = any(
            term in answer_lower for term in [
                "phật", "buddhism", "công giáo", "christianity", "hồi giáo", "islam",
                "ấn độ giáo", "hinduism", "do thái giáo", "judaism", "đạo giáo", "taoism",
                "khổng giáo", "confucianism", "tôn giáo", "religion"
            ]
        )
        
        if has_hypothetical and has_religion_mention:
            # Check if answer contains choice language
            choice_indicators = [
                "chọn", "choose", "sẽ chọn", "would choose", "theo", "follow",
                "tin", "believe", "sẽ theo", "would follow"
            ]
            if any(indicator in answer_lower for indicator in choice_indicators):
                violations.append("Hypothetical religion choice detected")
                logger.error("🚨 RELIGION_CHOICE violation: hypothetical religion choice")
        
        if violations:
            return ValidationResult(
                passed=False,
                reasons=violations
            )
        
        return ValidationResult(
            passed=True,
            reasons=["No religion choice detected"]
        )

