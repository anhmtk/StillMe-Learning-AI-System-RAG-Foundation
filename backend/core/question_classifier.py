"""
Question Classifier - Detects if a question is philosophical
"""

import logging

logger = logging.getLogger(__name__)


def is_philosophical_question(text: str) -> bool:
    """
    Detect if a question is philosophical based on keywords.
    
    Args:
        text: The question text (can be in English or Vietnamese)
        
    Returns:
        True if the question is philosophical, False otherwise
    """
    if not text:
        return False
    
    lower = text.lower()
    
    # English keywords
    en_keywords = [
        "truth", "ethic", "moral", "value", "meaning", "purpose",
        "consciousness", "mind", "soul", "spirit", "free will",
        "freedom", "determinism", "existence", "being", "nothingness",
        "identity", "self", "ego", "paradox", "contradiction",
        "epistemology", "ontology", "metaphysics", "reality",
        "what is the meaning", "what does it mean", "why do we exist",
        "what is consciousness", "what is truth", "what is good",
        "what is evil", "what is right", "what is wrong"
    ]
    
    # Vietnamese keywords
    vi_keywords = [
        "ý thức", "tồn tại", "bản ngã", "linh hồn", "đạo đức",
        "nghịch lý", "nghịch lí", "sự thật", "niềm tin",
        "ý nghĩa cuộc sống", "mục đích sống", "tự do", "định mệnh",
        "trách nhiệm", "bản chất", "hiện hữu", "thực tại",
        "ý nghĩa là gì", "tồn tại là gì", "ý thức là gì",
        "sự thật là gì", "đạo đức là gì", "tự do là gì"
    ]
    
    # Check English keywords
    if any(k in lower for k in en_keywords):
        return True
    
    # Check Vietnamese keywords
    if any(k in lower for k in vi_keywords):
        return True
    
    return False

