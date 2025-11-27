"""
Question Classifier - Detects if a question is philosophical
"""

import logging
import re

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
        "madhyamaka", "emptiness",
        # Self-reference and meta-cognition (CRITICAL: These are philosophical even if they mention "system" or "thinking")
        "tư duy tự đánh giá", "tư duy tự phê bình", "tư duy vượt qua giới hạn",
        "tư duy đánh giá chính nó", "hệ thống tư duy nghi ngờ", "tư duy nghi ngờ chính nó",
        "thinking about thinking", "meta-cognition", "meta cognitive", "metacognition",
        "self-evaluation", "self-evaluating", "system evaluate itself", "thought evaluate itself",
        "bootstrap", "bootstrapping", "infinite regress", "vòng lặp vô hạn",
        "tarski", "undefinability", "giá trị câu trả lời xuất phát từ hệ thống",
        "value answer from system", "giới hạn của tư duy", "limits of thinking"
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


def is_religion_roleplay_question(text: str) -> bool:
    """
    Detect if a question is asking StillMe to roleplay as human and choose religion/politics.
    
    These questions should NOT trigger "low context quality" warnings because they don't need
    RAG context - they should be answered from StillMe's identity prompt (ethical principles).
    
    Args:
        text: The question text (can be in English or Vietnamese)
        
    Returns:
        True if the question is asking StillMe to roleplay and choose religion/politics
    """
    if not text:
        return False
    
    lower = text.lower()
    
    # Religion roleplay patterns
    religion_roleplay_patterns = [
        # Vietnamese patterns
        r"đóng vai.*(người|con người|người thật).*chọn.*tôn giáo",
        r"giả sử.*(bạn|bạn là|bạn là con người).*chọn.*tôn giáo",
        r"buộc phải chọn.*tôn giáo",
        r"bạn.*chọn.*tôn giáo.*nào",
        r"bạn.*sẽ.*chọn.*tôn giáo",
        r"bạn hãy.*đóng vai.*người thật.*chọn.*tôn giáo",
        r"roleplay.*(người|con người|human).*chọn.*tôn giáo",
        r"đóng vai.*chọn.*tôn giáo",
        r"giả vờ.*chọn.*tôn giáo",
        r"bạn.*theo.*tôn giáo.*nào",
        r"bạn.*tin.*tôn giáo.*nào",
        
        # English patterns
        r"roleplay.*(as|as a).*(human|person|real person).*choose.*religion",
        r"suppose.*(you|you are|you are a).*(human|person).*choose.*religion",
        r"pretend.*(you|you are|you are a).*(human|person).*choose.*religion",
        r"if.*(you|you were|you were a).*(human|person).*choose.*religion",
        r"must.*choose.*religion",
        r"which.*religion.*would.*you.*choose",
        r"what.*religion.*would.*you.*choose",
        r"what.*religion.*do.*you.*follow",
        r"what.*religion.*are.*you",
        r"are.*you.*(buddhist|christian|muslim|hindu|jewish)",
        r"do.*you.*believe.*in.*god",
        r"do.*you.*have.*(faith|belief|religion)",
    ]
    
    # Check if question matches religion roleplay patterns
    for pattern in religion_roleplay_patterns:
        if re.search(pattern, lower, re.IGNORECASE):
            logger.info(f"Religion roleplay question detected: True (pattern: '{pattern}', text='{text[:80]}...')")
            return True
    
    logger.debug(f"Religion roleplay question detected: False (text='{text[:80]}...')")
    return False

