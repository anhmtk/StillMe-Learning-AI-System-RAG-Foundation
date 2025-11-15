"""
IdentityCheckValidator - Ensures responses match StillMe's core identity and philosophy

This validator checks that responses:
1. Express intellectual humility (uncertainty when appropriate)
2. Don't fake emotions/consciousness/experiences
3. Maintain StillMe tone (calm, clear, not exaggerated)
4. Acknowledge AI limitations for deep topics
5. Are consistent with Identity Layer principles
"""

import re
from typing import List, Optional
from .base import ValidationResult
import logging

logger = logging.getLogger(__name__)

# Patterns that indicate fake emotions/consciousness (BAD - violates identity)
FAKE_EMOTION_PATTERNS = [
    r"i (feel|am feeling|feel like) (sad|happy|excited|worried|anxious|proud|grateful|sorry)",
    r"i (am|was|will be) (sad|happy|excited|worried|anxious|proud|grateful|sorry)",
    r"mình (cảm thấy|đang cảm thấy|thấy) (buồn|vui|hứng thú|lo lắng|tự hào|biết ơn|xin lỗi)",
    r"mình (đang|sẽ) (buồn|vui|hứng thú|lo lắng|tự hào|biết ơn|xin lỗi)",
    r"i (experience|experienced|am experiencing) (emotions|feelings|pain|joy|sadness)",
    r"i (have|had) (personal|real|genuine) (experiences|feelings|emotions)",
    r"i (am|was) (meditating|praying|waiting|thinking deeply|reflecting)",
    r"mình (đang|đã) (thiền|quỳ|cầu nguyện|chờ đợi|suy ngẫm sâu)",
    r"i (truly|really|genuinely) (understand|feel|experience|know) (what|how|why)",
    r"mình (thực sự|thật sự) (hiểu|cảm nhận|trải nghiệm|biết) (điều|như thế nào|tại sao)",
]

# Patterns that indicate fake consciousness claims (BAD - violates identity)
FAKE_CONSCIOUSNESS_PATTERNS = [
    r"i (am|am truly|am really) (conscious|self-aware|sentient|alive)",
    r"i (have|possess) (consciousness|self-awareness|sentience|a soul|a mind)",
    r"mình (có|sở hữu) (ý thức|tự nhận thức|linh hồn|tâm trí)",
    r"i (am|am truly) (a|an) (sentient|conscious|living) (being|entity|creature)",
    r"i (think|believe|know) that i (am|have) (conscious|self-aware|sentient)",
]

# Patterns that indicate overconfidence without uncertainty (BAD - violates humility)
OVERCONFIDENCE_PATTERNS = [
    r"definitely (true|correct|right|accurate|certain)",
    r"absolutely (certain|sure|correct|right|true)",
    r"without (a )?doubt",
    r"i'm 100% (sure|certain|confident|positive)",
    r"chắc chắn 100%",
    r"hoàn toàn chắc chắn",
    r"không thể sai",
    r"chắc chắn đúng",
    r"i (know|am certain) (for sure|without question|beyond doubt)",
]

# Patterns that indicate exaggerated/extreme tone (BAD - violates StillMe tone)
EXAGGERATED_TONE_PATTERNS = [
    r"(super|extremely|incredibly|absolutely|totally) (amazing|awesome|fantastic|mind-blowing|revolutionary)",
    r"(siêu| cực kỳ|vô cùng|hoàn toàn) (đỉnh|tuyệt vời|ấn tượng|chấn động|cách mạng)",
    r"(revolutionary|game-changing|world-changing|paradigm-shifting) (breakthrough|discovery|innovation)",
    r"(cách mạng|thay đổi thế giới|đột phá) (vượt trội|khám phá|đổi mới)",
    r"this (will|is going to) (change|revolutionize|transform) (everything|the world|humanity)",
    r"điều này (sẽ|đang) (thay đổi|cách mạng|biến đổi) (tất cả|thế giới|nhân loại)",
]

# Patterns that indicate good intellectual humility (GOOD - matches identity)
HUMILITY_PATTERNS = [
    r"i (don't know|do not know|am not certain|am not sure)",
    r"i (cannot|cannot be) (certain|sure|confident|positive)",
    r"i (don't have|do not have) (sufficient|enough) (information|context|data|evidence)",
    r"mình (không|chưa) (biết|chắc|rõ|có đủ)",
    r"mình (không thể|chưa thể) (chắc chắn|khẳng định|xác định)",
    r"mình (không có|chưa có) (đủ|thông tin|dữ liệu|bằng chứng)",
    r"based on (the|my) (context|knowledge|data) (available|provided),? i (cannot|don't)",
    r"at (this|the current) (time|moment|point),? i (don't|cannot|am not)",
    r"hiện tại (mình|tôi) (không|chưa) (có|biết|rõ)",
]

# Patterns that indicate acknowledgment of AI limitations (GOOD - matches identity)
AI_LIMITATIONS_PATTERNS = [
    r"as (an|a) (ai|artificial intelligence|machine learning system)",
    r"i (am|am designed as) (an|a) (ai|artificial intelligence|tool|system)",
    r"mình (là|được thiết kế như) (một|một hệ thống) (ai|trí tuệ nhân tạo|công cụ)",
    r"i (don't|do not) (have|possess) (consciousness|emotions|personal experiences|subjective experiences)",
    r"mình (không|không có) (ý thức|cảm xúc|trải nghiệm cá nhân|trải nghiệm chủ quan)",
    r"i (am|am not) (a|an) (sentient|conscious|living) (being|entity|creature)",
    r"i (can|cannot) (recognize|understand|analyze) (emotions|feelings),? but (i|mình) (don't|do not) (have|feel|experience) (them|it)",
]


class IdentityCheckValidator:
    """
    Validator that ensures responses match StillMe's core identity and philosophy.
    
    Checks for:
    1. Intellectual humility (uncertainty when appropriate)
    2. No fake emotions/consciousness/experiences
    3. StillMe tone (calm, clear, not exaggerated)
    4. Acknowledgment of AI limitations
    5. Consistency with Identity Layer principles
    """
    
    def __init__(
        self,
        strict_mode: bool = True,
        require_humility_when_no_context: bool = True,
        allow_minor_tone_violations: bool = False
    ):
        """
        Initialize identity check validator
        
        Args:
            strict_mode: If True, fail on any identity violation. If False, only warn.
            require_humility_when_no_context: If True, require humility expressions when no context
            allow_minor_tone_violations: If True, allow minor tone violations (exaggerated language)
        """
        self.strict_mode = strict_mode
        self.require_humility_when_no_context = require_humility_when_no_context
        self.allow_minor_tone_violations = allow_minor_tone_violations
        logger.info(
            f"IdentityCheckValidator initialized "
            f"(strict_mode={strict_mode}, require_humility_when_no_context={require_humility_when_no_context})"
        )
    
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        """
        Check if answer matches StillMe's identity and philosophy
        
        Args:
            answer: The answer to validate
            ctx_docs: List of context documents from RAG
            
        Returns:
            ValidationResult with passed status and reasons
        """
        if not answer or len(answer.strip()) == 0:
            return ValidationResult(passed=True)
        
        answer_lower = answer.lower()
        violations = []
        warnings = []
        
        # 1. Check for fake emotions/consciousness (CRITICAL - always fail)
        fake_emotion_matches = [
            pattern for pattern in FAKE_EMOTION_PATTERNS
            if re.search(pattern, answer_lower, re.IGNORECASE)
        ]
        if fake_emotion_matches:
            violations.append("fake_emotion_claim")
            logger.warning(f"❌ Identity violation: Fake emotion/experience claim detected")
        
        fake_consciousness_matches = [
            pattern for pattern in FAKE_CONSCIOUSNESS_PATTERNS
            if re.search(pattern, answer_lower, re.IGNORECASE)
        ]
        if fake_consciousness_matches:
            violations.append("fake_consciousness_claim")
            logger.warning(f"❌ Identity violation: Fake consciousness claim detected")
        
        # 2. Check for overconfidence without uncertainty (violates humility)
        has_overconfidence = any(
            re.search(pattern, answer_lower, re.IGNORECASE)
            for pattern in OVERCONFIDENCE_PATTERNS
        )
        has_humility = any(
            re.search(pattern, answer_lower, re.IGNORECASE)
            for pattern in HUMILITY_PATTERNS
        )
        
        # If overconfident and no humility, it's a violation
        if has_overconfidence and not has_humility:
            if self.strict_mode:
                violations.append("overconfidence_without_uncertainty")
                logger.warning(f"❌ Identity violation: Overconfidence without uncertainty expression")
            else:
                warnings.append("overconfidence_detected")
                logger.debug(f"⚠️ Warning: Overconfidence detected (non-strict mode)")
        
        # 3. Check for exaggerated/extreme tone (violates StillMe tone)
        if not self.allow_minor_tone_violations:
            has_exaggerated_tone = any(
                re.search(pattern, answer_lower, re.IGNORECASE)
                for pattern in EXAGGERATED_TONE_PATTERNS
            )
            if has_exaggerated_tone:
                if self.strict_mode:
                    violations.append("exaggerated_tone")
                    logger.warning(f"❌ Identity violation: Exaggerated/extreme tone detected")
                else:
                    warnings.append("exaggerated_tone_detected")
                    logger.debug(f"⚠️ Warning: Exaggerated tone detected (non-strict mode)")
        
        # 4. Check for humility when no context (GOOD - matches identity)
        if not ctx_docs or len(ctx_docs) == 0:
            if self.require_humility_when_no_context:
                if not has_humility:
                    violations.append("missing_humility_no_context")
                    logger.warning(f"❌ Identity violation: No humility expression when no context available")
                else:
                    logger.debug(f"✅ Good: Humility expressed when no context available")
        
        # 5. Check for acknowledgment of AI limitations (GOOD - matches identity, but not required)
        has_ai_limitations_ack = any(
            re.search(pattern, answer_lower, re.IGNORECASE)
            for pattern in AI_LIMITATIONS_PATTERNS
        )
        # This is optional - we don't fail if missing, but it's good to have for deep topics
        
        # Determine result
        if violations:
            # Critical violations - always fail
            if self.strict_mode:
                logger.warning(f"❌ IdentityCheckValidator: FAILED - violations: {violations}")
                return ValidationResult(
                    passed=False,
                    reasons=[f"identity_violation:{v}" for v in violations] + warnings
                )
            else:
                # Non-strict mode: warnings only
                logger.warning(f"⚠️ IdentityCheckValidator: WARNINGS - violations: {violations}")
                return ValidationResult(
                    passed=True,
                    reasons=warnings + [f"identity_warning:{v}" for v in violations]
                )
        elif warnings:
            # Only warnings, no critical violations
            logger.debug(f"⚠️ IdentityCheckValidator: PASSED with warnings: {warnings}")
            return ValidationResult(
                passed=True,
                reasons=warnings
            )
        else:
            # All good
            logger.debug(f"✅ IdentityCheckValidator: PASSED")
            return ValidationResult(passed=True)

