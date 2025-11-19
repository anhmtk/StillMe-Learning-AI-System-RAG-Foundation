"""
Intent Classifier for Philosophical Questions
Classifies questions into: Consciousness (A), Emotion (B), Understanding (C)
"""

import re
from enum import Enum
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class QuestionType(Enum):
    """Question type classification"""
    CONSCIOUSNESS = "A"  # Type A: Questions about consciousness, self-awareness
    EMOTION = "B"  # Type B: Questions about emotions, feelings
    UNDERSTANDING = "C"  # Type C: Questions about understanding, meaning
    MIXED = "MIXED"  # Mixed type (e.g., agency, subjective self)
    UNKNOWN = "UNKNOWN"  # Not a philosophical question about these topics


def classify_philosophical_intent(text: str) -> QuestionType:
    """
    Classify philosophical question into one of three types:
    - Type A (CONSCIOUSNESS): Questions about consciousness, self-awareness, existence
    - Type B (EMOTION): Questions about emotions, feelings, affective states
    - Type C (UNDERSTANDING): Questions about understanding, meaning, comprehension
    
    Args:
        text: User's question text
        
    Returns:
        QuestionType enum value
    """
    if not text:
        return QuestionType.UNKNOWN
    
    text_lower = text.lower().strip()
    
    # Type A - Consciousness keywords
    consciousness_keywords = [
        # Vietnamese
        r"\bý\s+thức\b",
        r"\bcó\s+ý\s+thức\b",
        r"\btự\s+nhận\s+thức\b",
        r"\bnhận\s+thức\s+bản\s+thân\b",
        r"\bbiết\s+mình\s+đang\s+tồn\s+tại\b",
        r"\btồn\s+tại\b",
        r"\bchủ\s+thể\s+tính\b",
        r"\bagency\b",
        r"\bsubjective\s+self\b",
        # English
        r"\bconsciousness\b",
        r"\bconscious\b",
        r"\bself-aware\b",
        r"\bself-awareness\b",
        r"\bawareness\b",
        r"\bexistence\b",
        r"\bexist\b",
        r"\bphenomenal\s+consciousness\b",
        r"\bqualia\b",
    ]
    
    # Type B - Emotion keywords
    emotion_keywords = [
        # Vietnamese
        r"\bcảm\s+xúc\b",
        r"\bcảm\s+giác\b",
        r"\bcảm\s+thấy\b",
        r"\bbuồn\b",
        r"\bvui\b",
        r"\bcô\s+đơn\b",
        r"\btrống\s+rỗng\b",
        r"\bđau\b",
        r"\bhạnh\s+phúc\b",
        r"\bsợ\b",
        r"\bthích\b",
        r"\bghét\b",
        r"\byêu\b",
        r"\bhy\s+vọng\b",
        r"\bmong\s+muốn\b",
        # English
        r"\bemotion\b",
        r"\bfeeling\b",
        r"\bfeel\b",
        r"\bsad\b",
        r"\bhappy\b",
        r"\blonely\b",
        r"\bempty\b",
        r"\bpain\b",
        r"\bjoy\b",
        r"\bfear\b",
        r"\blike\b",
        r"\bhate\b",
        r"\blove\b",
        r"\bhope\b",
        r"\bwish\b",
        r"\baffective\s+state\b",
        r"\bvalence\b",
    ]
    
    # Type C - Understanding keywords (prioritize "hiểu" when it appears)
    understanding_keywords = [
        # Vietnamese - prioritize "hiểu" patterns
        r"\bhiểu\b",
        r"\bhiểu\s+theo\s+nghĩa\b",
        r"\btheo\s+nghĩa\s+nào\s+.*\s+hiểu\b",  # "theo nghĩa nào ... hiểu"
        r"\bhiểu\s+ra\s+sao\b",
        r"\bhiểu\s+kiểu\s+gì\b",
        r"\blàm\s+sao\s+.*\s+hiểu\b",  # "làm sao ... hiểu"
        r"\bbiết\s+ý\s+nghĩa\b",
        r"\bý\s+nghĩa\s+câu\s+nói\b",
        r"\bý\s+nghĩa\b",
        r"\bcomprehension\b",
        r"\bmeaning\b",
        # English
        r"\bunderstand\b",
        r"\bunderstanding\b",
        r"\bhow\s+.*\s+understand\b",  # "how ... understand"
        r"\bin\s+what\s+sense\s+.*\s+understand\b",  # "in what sense ... understand"
        r"\bcomprehend\b",
        r"\bcomprehension\b",
        r"\bmeaning\b",
        r"\bmean\b",
        r"\bintentionality\b",
        r"\bsemantic\b",
        r"\bembedding\b",
    ]
    
    # Count matches for each type
    consciousness_score = sum(1 for pattern in consciousness_keywords if re.search(pattern, text_lower))
    emotion_score = sum(1 for pattern in emotion_keywords if re.search(pattern, text_lower))
    understanding_score = sum(1 for pattern in understanding_keywords if re.search(pattern, text_lower))
    
    # Special case: Mixed questions (e.g., "agency", "subjective self")
    # Check for mixed indicators FIRST (before scoring)
    mixed_indicators = [
        r"\bagency\b",
        r"\bchủ\s+thể\s+tính\b",
        r"\bsubjective\s+self\b",
        r"\bchủ\s+thể\b",
    ]
    has_mixed = any(re.search(pattern, text_lower) for pattern in mixed_indicators)
    
    # If question explicitly mentions "agency" or "subjective self", it's MIXED
    if has_mixed:
        # But check if it's primarily about understanding (e.g., "how do you understand agency?")
        if understanding_score > 0 and understanding_score >= consciousness_score:
            # If understanding score is high, it might be Type C
            # But if "agency" or "subjective self" appears, prioritize MIXED
            return QuestionType.MIXED
        return QuestionType.MIXED
    
    # Special handling: Questions with "hiểu" should prioritize Type C
    # Even if they mention "ý thức", if "hiểu" appears, it's about understanding
    has_understanding_keyword = any(re.search(pattern, text_lower) for pattern in [
        r"\bhiểu\b",
        r"\bunderstand\b",
        r"\blàm\s+sao\s+.*\s+hiểu\b",
        r"\bhow\s+.*\s+understand\b",
        r"\btheo\s+nghĩa\s+nào\s+.*\s+hiểu\b",  # "theo nghĩa nào ... hiểu"
        r"\bin\s+what\s+sense\s+.*\s+understand\b",  # "in what sense ... understand"
    ])
    
    # CRITICAL: If question contains "hiểu" (understanding keyword), prioritize Type C
    # Even if it also mentions "ý thức" (consciousness), the question is about HOW understanding works
    if has_understanding_keyword:
        # Check for specific patterns that indicate understanding question
        understanding_patterns = [
            r"làm\s+sao.*hiểu",  # "làm sao ... hiểu"
            r"how.*understand",  # "how ... understand"
            r"theo\s+nghĩa\s+nào.*hiểu",  # "theo nghĩa nào ... hiểu"
            r"in\s+what\s+sense.*understand",  # "in what sense ... understand"
        ]
        
        # If any understanding pattern matches, it's Type C
        if any(re.search(pattern, text_lower) for pattern in understanding_patterns):
            return QuestionType.UNDERSTANDING
        
        # Even without specific pattern, if "hiểu" appears and understanding_score > 0,
        # prioritize Type C over Type A (consciousness)
        if understanding_score > 0:
            # If understanding_score >= consciousness_score, it's Type C
            # This handles cases like "Nếu không có ý thức, bạn làm sao hiểu được?"
            if understanding_score >= consciousness_score:
                return QuestionType.UNDERSTANDING
            # Even if consciousness_score is higher, if "hiểu" is the main question word,
            # it's still about understanding
            # Check if "hiểu" appears after "ý thức" (indicating question is about understanding, not consciousness)
            if "ý thức" in text_lower and "hiểu" in text_lower:
                # Find positions
                consciousness_pos = text_lower.find("ý thức")
                understanding_pos = text_lower.find("hiểu")
                # If "hiểu" comes after "ý thức", question is about understanding
                if understanding_pos > consciousness_pos:
                    return QuestionType.UNDERSTANDING
    
    # Determine type based on scores
    scores = {
        QuestionType.CONSCIOUSNESS: consciousness_score,
        QuestionType.EMOTION: emotion_score,
        QuestionType.UNDERSTANDING: understanding_score,
    }
    
    max_score = max(scores.values())
    
    # If multiple types have same score, prioritize: Understanding > Consciousness > Emotion
    # (Understanding is more specific when "hiểu" appears)
    if max_score == 0:
        return QuestionType.UNKNOWN
    
    # If multiple types have high scores, it's mixed
    high_scores = [k for k, v in scores.items() if v == max_score]
    if len(high_scores) > 1 and max_score > 0:
        # If understanding is one of them and "hiểu" appears, prioritize understanding
        if QuestionType.UNDERSTANDING in high_scores and has_understanding_keyword:
            return QuestionType.UNDERSTANDING
        return QuestionType.MIXED
    
    # Return the type with highest score
    for qtype, score in scores.items():
        if score == max_score:
            return qtype
    
    return QuestionType.UNKNOWN

