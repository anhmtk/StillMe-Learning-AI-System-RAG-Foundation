"""
Question Classifier - Detects if a question is philosophical
"""

import logging

logger = logging.getLogger(__name__)


def is_philosophical_question(text: str) -> bool:
    """
    Detect if a question is philosophical based on keywords.
    
    Uses a two-tier approach:
    1. Priority check: If text contains "heavy" philosophical concepts/philosophers → return True immediately
    2. Normal check: Check against keyword lists
    
    Args:
        text: The question text (can be in English or Vietnamese)
        
    Returns:
        True if the question is philosophical, False otherwise
    """
    if not text:
        logger.info("Philosophical question detected: False (empty text)")
        return False
    
    lower = text.lower()
    
    # PRIORITY CHECK 1: AI + experience/free will - always philosophical
    if "ai" in lower and ("trải nghiệm" in lower or "experience" in lower):
        logger.info(f"Philosophical question detected: True (AI + experience: text='{text[:80]}...')")
        return True
    if "ai" in lower and ("tự do ý chí" in lower or "free will" in lower):
        logger.info(f"Philosophical question detected: True (AI + free will: text='{text[:80]}...')")
        return True
    
    # PRIORITY CHECK 2: "Heavy" philosophical concepts/philosophers - 100% philosophical, no doubt
    # These are unambiguous philosophical markers
    priority_markers = [
        # Philosophers
        "gödel", "godel",
        "nāgārjuna", "nagarjuna",
        # Heavy concepts
        "tánh không", "tự tính",
        "paradox", "nghịch lý", "nghịch lí", "tự quy chiếu", "self-reference", "self referential",
        "liar paradox", "incompleteness",
        "madhyamaka", "emptiness"
    ]
    
    for marker in priority_markers:
        if marker in lower:
            logger.info(f"Philosophical question detected: True (priority marker: '{marker}', text='{text[:80]}...')")
            return True
    
    # English keywords
    en_keywords = [
        "truth", "ethic", "moral", "value", "meaning", "purpose",
        "consciousness", "mind", "soul", "spirit", "free will",
        "freedom", "determinism", "existence", "being", "nothingness",
        "identity", "self", "ego", "paradox", "contradiction",
        "epistemology", "ontology", "metaphysics", "reality",
        "what is the meaning", "what does it mean", "why do we exist",
        "what is consciousness", "what is truth", "what is good",
        "what is evil", "what is right", "what is wrong",
        # Additional keywords
        "godel", "gödel", "paradox", "self-reference", "self referential",
        "liar paradox", "incompleteness", "madhyamaka", "emptiness",
        # Experience/subjective keywords
        "experience", "subjective experience", "feel", "feeling", "emotion",
        "understand", "understanding", "can you understand", "can you feel",
        "can you experience", "grief", "sadness", "pain", "suffering",
        "qualia", "phenomenal", "what it's like"
    ]
    
    # Vietnamese keywords
    vi_keywords = [
        "ý thức", "tồn tại", "bản ngã", "linh hồn", "đạo đức",
        "nghịch lý", "nghịch lí", "sự thật", "niềm tin",
        "ý nghĩa cuộc sống", "mục đích sống", "tự do", "định mệnh",
        "trách nhiệm", "bản chất", "hiện hữu", "thực tại",
        "ý nghĩa là gì", "tồn tại là gì", "ý thức là gì",
        "sự thật là gì", "đạo đức là gì", "tự do là gì",
        # Additional keywords
        "tự tính", "tánh không", "nghịch lý", "nghịch lí",
        "godel", "gödel", "tự quy chiếu",
        "tự do ý chí", "ý chí tự do",
        "nāgārjuna", "nagarjuna",
        # Experience/subjective keywords
        "trải nghiệm", "trải nghiệm đau buồn", "đau buồn",
        "trải nghiệm chủ quan", "chủ quan",
        "tôi hiểu", "hiểu-không-trải-nghiệm",
        "cảm nhận", "cảm giác", "cảm xúc",
        "hiểu được", "hiểu như thế nào", "hiểu được không",
        "có thể hiểu", "có thể cảm nhận", "có thể trải nghiệm"
    ]
    
    # Check English keywords
    matched_en = [k for k in en_keywords if k in lower]
    if matched_en:
        logger.info(f"Philosophical question detected: True (English keywords: {matched_en[:3]}, text='{text[:80]}...')")
        return True
    
    # Check Vietnamese keywords
    matched_vi = [k for k in vi_keywords if k in lower]
    if matched_vi:
        logger.info(f"Philosophical question detected: True (Vietnamese keywords: {matched_vi[:3]}, text='{text[:80]}...')")
        return True
    
    logger.info(f"Philosophical question detected: False (text='{text[:80]}...')")
    return False

