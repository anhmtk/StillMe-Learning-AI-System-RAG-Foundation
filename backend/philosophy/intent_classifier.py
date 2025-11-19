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
    
    # AUTOMATIC HEURISTIC-BASED CLASSIFICATION
    # Instead of hardcoding each pattern, use heuristics to automatically handle edge cases
    
    # Heuristic 1: Position-based priority
    # The keyword that appears LATER in the question is usually the focus
    # Example: "Nếu không có ý thức, bạn làm sao hiểu được?" → "hiểu" is focus
    keyword_positions = {}
    for qtype, keywords_list in [
        (QuestionType.CONSCIOUSNESS, consciousness_keywords),
        (QuestionType.EMOTION, emotion_keywords),
        (QuestionType.UNDERSTANDING, understanding_keywords),
    ]:
        positions = []
        for pattern in keywords_list:
            match = re.search(pattern, text_lower)
            if match:
                positions.append(match.start())
        if positions:
            keyword_positions[qtype] = max(positions)  # Latest position
    
    # Heuristic 2: Proximity to question words
    # Keywords closer to question words (nào, sao, gì, how, what) are more important
    question_word_patterns = [
        r"\bnào\b", r"\bsao\b", r"\bgì\b", r"\bhow\b", r"\bwhat\b",
        r"\btheo\s+nghĩa\s+nào\b", r"\blàm\s+sao\b", r"\bin\s+what\s+sense\b"
    ]
    question_word_positions = [m.start() for pattern in question_word_patterns 
                              for m in re.finditer(pattern, text_lower)]
    
    # Heuristic 3: If multiple types have scores, use heuristics to decide
    if len([s for s in [consciousness_score, emotion_score, understanding_score] if s > 0]) > 1:
        # Multiple types detected - use heuristics
        
        # Priority 1: If understanding keyword appears after consciousness keyword, it's about understanding
        if understanding_score > 0 and consciousness_score > 0:
            if QuestionType.UNDERSTANDING in keyword_positions and QuestionType.CONSCIOUSNESS in keyword_positions:
                if keyword_positions[QuestionType.UNDERSTANDING] > keyword_positions[QuestionType.CONSCIOUSNESS]:
                    return QuestionType.UNDERSTANDING
        
        # Priority 2: If keyword is close to question word, it's the focus
        if question_word_positions:
            min_distance = float('inf')
            closest_type = None
            for qtype, pos in keyword_positions.items():
                for qw_pos in question_word_positions:
                    distance = abs(pos - qw_pos)
                    if distance < min_distance:
                        min_distance = distance
                        closest_type = qtype
            if closest_type and min_distance < 50:  # Within 50 chars
                return closest_type
        
        # Priority 3: If understanding keyword appears, and it's in a question structure, prioritize it
        understanding_keywords_list = [r"\bhiểu\b", r"\bunderstand\b"]
        for pattern in understanding_keywords_list:
            match = re.search(pattern, text_lower)
            if match:
                # Check if it's in a question context (near question words or at end)
                understanding_pos = match.start()
                # If near question word or in second half of sentence
                if any(abs(understanding_pos - qw_pos) < 30 for qw_pos in question_word_positions) or \
                   understanding_pos > len(text_lower) / 2:
                    if understanding_score > 0:
                        return QuestionType.UNDERSTANDING
        
        # Priority 4: If scores are equal, use position (later = more important)
        max_score = max(consciousness_score, emotion_score, understanding_score)
        types_with_max_score = [
            (QuestionType.CONSCIOUSNESS, consciousness_score),
            (QuestionType.EMOTION, emotion_score),
            (QuestionType.UNDERSTANDING, understanding_score),
        ]
        types_with_max_score = [(t, s) for t, s in types_with_max_score if s == max_score]
        
        if len(types_with_max_score) > 1:
            # Multiple types with same score - pick the one with latest position
            latest_type = None
            latest_pos = -1
            for qtype, score in types_with_max_score:
                if qtype in keyword_positions and keyword_positions[qtype] > latest_pos:
                    latest_pos = keyword_positions[qtype]
                    latest_type = qtype
            if latest_type:
                return latest_type
    
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

