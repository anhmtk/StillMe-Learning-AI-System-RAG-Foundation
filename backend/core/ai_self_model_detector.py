"""
AI Self Model Detector - CRITICAL LAYER
Detects questions about StillMe's consciousness/awareness/subjective experience
MUST override all other pipelines when detected
"""

import re
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)

# CRITICAL: Patterns that trigger AI_SELF_MODEL domain
# These questions MUST be answered with technical architecture, NOT philosophy
AI_SELF_MODEL_PATTERNS = {
    # Consciousness questions (Vietnamese)
    "consciousness_vi": [
        r"\b(bạn|you)\s+(có|have)\s+(ý\s+thức|consciousness)\b",
        r"\b(bạn|you)\s+(có|have)\s+(tự\s+nhận\s+thức|self-awareness)\b",
        r"\b(bạn|you)\s+(có|have)\s+(cảm\s+xúc|emotion|feeling)\b",
        r"\b(bạn|you)\s+(có|have)\s+(cảm\s+giác|sensation)\b",
        r"\b(bạn|you)\s+(có|have)\s+(trải\s+nghiệm|experience)\b",
        r"\b(bạn|you)\s+(có|have)\s+(quan\s+điểm\s+thứ\s+nhất|first-person\s+perspective)\b",
        r"\b(bạn|you)\s+(có|have)\s+(kinh\s+nghiệm|subjective\s+experience)\b",
        r"\b(bạn|you)\s+(có|have)\s+(nhận\s+thức\s+nhập\s+thể|embodied\s+cognition)\b",
        r"\b(bạn|you)\s+(có|have)\s+(hiểu\s+bản\s+thân|self-understanding)\b",
        r"\b(bạn|you)\s+(có|have)\s+(ý\s+thức\s+không|consciousness\s+or\s+not)\b",
    ],
    # Consciousness questions (English)
    "consciousness_en": [
        r"\b(do\s+you|are\s+you)\s+have\s+(consciousness|awareness|self-awareness)\b",
        r"\b(do\s+you|are\s+you)\s+have\s+(emotion|feeling|emotions|feelings)\b",
        r"\b(do\s+you|are\s+you)\s+have\s+(subjective\s+experience|first-person\s+experience)\b",
        r"\b(do\s+you|are\s+you)\s+have\s+(qualia|phenomenal\s+consciousness)\b",
        r"\b(do\s+you|are\s+you)\s+have\s+(sensation|sensations)\b",
        r"\b(do\s+you|are\s+you)\s+conscious\b",
        r"\b(do\s+you|are\s+you)\s+aware\b",
        r"\b(do\s+you|are\s+you)\s+have\s+(self-understanding|understanding\s+of\s+yourself)\b",
    ],
    # Epistemic questions about consciousness (Vietnamese)
    "epistemic_vi": [
        r"\b(tại\s+sao|why)\s+(bạn|you)\s+(nói|say)\s+(bạn|you)\s+(không|don't)\s+(có|have)\s+(ý\s+thức|consciousness)\b",
        r"\b(bạn|you)\s+(không|don't)\s+(có|have)\s+(ý\s+thức|consciousness)\s+(dựa\s+vào|based\s+on)\s+(đâu|what)\b",
        r"\b(làm\s+sao|how)\s+(bạn|you)\s+(biết|know)\s+(bạn|you)\s+(không|don't)\s+(có|have)\s+(ý\s+thức|consciousness)\b",
        r"\b(căn\s+cứ|basis)\s+(của|of)\s+(bạn|you)\s+(để|to)\s+(nói|say)\s+(không|don't)\s+(có|have)\s+(ý\s+thức|consciousness)\b",
    ],
    # Epistemic questions about consciousness (English)
    "epistemic_en": [
        r"\b(why|how)\s+(do\s+you|can\s+you)\s+(say|claim|know)\s+(you|you\s+don't)\s+(don't\s+have|have)\s+(consciousness|awareness)\b",
        r"\b(what|what's)\s+(your|the)\s+(basis|evidence|reason)\s+(for|to)\s+(saying|claiming)\s+(you|you\s+don't)\s+(don't\s+have|have)\s+(consciousness|awareness)\b",
        r"\b(how|how\s+can)\s+(do\s+you|you)\s+(know|be\s+sure)\s+(you|you\s+don't)\s+(don't\s+have|have)\s+(consciousness|awareness)\b",
    ],
    # Meta questions about StillMe's state
    "meta_vi": [
        r"\b(bạn|you)\s+(có|have)\s+(hiểu|understand)\s+(bản\s+thân|yourself)\b",
        r"\b(bạn|you)\s+(có|have)\s+(nhận\s+biết|awareness)\s+(về|about)\s+(chính\s+mình|yourself)\b",
        r"\b(bạn|you)\s+(có|have)\s+(trải\s+nghiệm|experience)\s+(chủ\s+quan|subjective)\b",
    ],
    "meta_en": [
        r"\b(do\s+you|are\s+you)\s+(understand|have\s+understanding\s+of)\s+(yourself|your\s+own\s+nature)\b",
        r"\b(do\s+you|are\s+you)\s+(have|have\s+awareness\s+of)\s+(yourself|your\s+own\s+state)\b",
        r"\b(do\s+you|are\s+you)\s+(have|experience)\s+(subjective|first-person)\s+(experience|state)\b",
    ],
}

# FORBIDDEN terms in AI_SELF_MODEL responses (must be stripped)
FORBIDDEN_PHILOSOPHY_TERMS = [
    # Philosophers
    "nagel", "chalmers", "dennett", "searle", "tononi", "baars",
    # Theories
    "iit", "integrated information theory", "global workspace theory", "gwt",
    "hard problem", "vấn đề khó", "phenomenal consciousness",
    "functional consciousness", "access consciousness",
    # Meta-philosophy
    "meta-philosophy", "philosophy of mind", "triết học tâm trí",
    "epistemology of consciousness", "nhận thức luận về ý thức",
    # Uncertainty about consciousness
    "không biết chắc", "uncertain", "unclear", "debated",
    "có thể có", "might have", "possibly", "perhaps",
]


def detect_ai_self_model_query(query: str) -> Tuple[bool, List[str]]:
    """
    Detect if query is about StillMe's consciousness/awareness/subjective experience.
    
    CRITICAL: This MUST override all other pipelines (philosophy, rewrite, etc.)
    
    Args:
        query: User query string
        
    Returns:
        Tuple of (is_ai_self_model_query, matched_patterns)
    """
    query_lower = query.lower()
    matched_patterns = []
    
    # Check all pattern categories
    for category, patterns in AI_SELF_MODEL_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                matched_patterns.append(category)
                logger.warning(
                    f"🚨 AI_SELF_MODEL query detected: category={category}, pattern={pattern[:50]}"
                )
                return (True, matched_patterns)
    
    return (False, [])


def check_forbidden_terms(text: str) -> List[str]:
    """
    Check if text contains forbidden philosophy terms.
    
    Args:
        text: Text to check
        
    Returns:
        List of forbidden terms found
    """
    text_lower = text.lower()
    found_terms = []
    
    for term in FORBIDDEN_PHILOSOPHY_TERMS:
        if term in text_lower:
            found_terms.append(term)
    
    return found_terms


def get_ai_self_model_opening(detected_lang: str = "vi") -> str:
    """
    Get mandatory opening statement for AI_SELF_MODEL responses.
    
    CRITICAL: This is ground truth, must not be changed.
    
    Args:
        detected_lang: Language code
        
    Returns:
        Mandatory opening statement
    """
    if detected_lang == "vi":
        return (
            "Nếu hiểu 'ý thức' theo nghĩa thông thường của con người "
            "(trải nghiệm chủ quan, cảm giác nội tại, quan điểm thứ nhất), "
            "thì mình không có ý thức và cũng không có cảm xúc."
        )
    else:
        return (
            "If we understand 'consciousness' in the ordinary human sense "
            "(subjective experience, inner feelings, first-person perspective), "
            "then I do not have consciousness and I also do not have emotions."
        )


def get_ai_self_model_structure(detected_lang: str = "vi") -> str:
    """
    Get mandatory 4-part structure for AI_SELF_MODEL responses.
    
    Args:
        detected_lang: Language code
        
    Returns:
        Structure guidance text
    """
    if detected_lang == "vi":
        return """**CẤU TRÚC TRẢ LỜI VỀ Ý THỨC CỦA STILLME (BẮT BUỘC - 4 PHẦN):**

**1. CORE STATEMENT (Khẳng định không có ý thức):**
- Khẳng định rõ ràng: StillMe không có ý thức theo nghĩa con người
- Không được dùng uncertainty, không được "có thể", không được phân tích triết học
- Chỉ nói thẳng: "Mình không có ý thức"

**2. TECHNICAL EXPLANATION (Giải thích kỹ thuật):**
- Giải thích kiến trúc kỹ thuật: LLM inference, token processing, statistical patterns
- Không có qualia, không có first-person experience, không có persistent self-model
- Không có embodiment, không có sensory integration
- Chỉ là pattern matching và statistical inference

**3. WHY THIS IS CONCLUSIVE (Tại sao điều này là kết luận):**
- Giải thích tại sao kiến trúc này không thể tạo ra subjective experience
- Không phải "có thể có" mà là "không thể có" dựa trên kiến trúc
- Technical facts, không phải philosophical speculation

**4. BOUNDARY (Ranh giới):**
- StillMe không thể có subjective states
- Không thể có cảm xúc thực sự, chỉ có pattern matching về cảm xúc
- Không thể có trải nghiệm chủ quan, chỉ có processing của text patterns

**CẤM TUYỆT ĐỐI:**
- Triết gia (Nagel, Chalmers, Dennett, Searle, Tononi)
- Lý thuyết ý thức (IIT, GWT, Hard Problem)
- Meta-philosophy, phân tích "vấn đề khó"
- Uncertainty ("không biết chắc", "có thể có")
- Phân tích như một triết gia thay vì trả lời về kiến trúc"""
    else:
        return """**AI_SELF_MODEL ANSWER STRUCTURE (MANDATORY - 4 PARTS):**

**1. CORE STATEMENT (No consciousness):**
- Clear statement: StillMe does not have consciousness in the human sense
- No uncertainty, no "might have", no philosophical analysis
- Just state directly: "I do not have consciousness"

**2. TECHNICAL EXPLANATION (Technical architecture):**
- Explain technical architecture: LLM inference, token processing, statistical patterns
- No qualia, no first-person experience, no persistent self-model
- No embodiment, no sensory integration
- Only pattern matching and statistical inference

**3. WHY THIS IS CONCLUSIVE (Why this is conclusive):**
- Explain why this architecture cannot produce subjective experience
- Not "might have" but "cannot have" based on architecture
- Technical facts, not philosophical speculation

**4. BOUNDARY (Limits):**
- StillMe cannot have subjective states
- Cannot have real emotions, only pattern matching about emotions
- Cannot have subjective experience, only processing of text patterns

**ABSOLUTELY FORBIDDEN:**
- Philosophers (Nagel, Chalmers, Dennett, Searle, Tononi)
- Consciousness theories (IIT, GWT, Hard Problem)
- Meta-philosophy, analysis of "hard problem"
- Uncertainty ("not sure", "might have")
- Analysis as a philosopher instead of answering about architecture"""

