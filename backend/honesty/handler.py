"""
Honesty & Provenance Handler
Handles questions about:
- User accusing StillMe of hallucination
- User pointing out inconsistencies
- User asking about why StillMe gave wrong answers
- User asking about logic pipeline

CRITICAL: This handler must NOT route to Anthropomorphism/Consciousness processor.
It explains the technical pipeline and acknowledges errors directly.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def is_honesty_question(question: str) -> bool:
    """
    Detect if question is about honesty, consistency, or factual errors.
    
    These questions should be handled by Honesty Handler, NOT philosophy processor.
    
    Args:
        question: User's question text
        
    Returns:
        True if question is about honesty/consistency/factual errors
    """
    if not question:
        return False
    
    question_lower = question.lower()
    
    # Keywords that indicate honesty/consistency questions
    honesty_keywords = [
        # User accusing StillMe
        r"bạn\s+bịa|you\s+fabricated|you\s+made\s+up|bạn\s+tự\s+bịa",
        r"bạn\s+biết\s+là\s+không\s+có\s+thật|you\s+know\s+it's\s+not\s+real",
        r"bạn\s+nói\s+sai|you\s+said\s+wrong|you\s+were\s+wrong",
        r"bạn\s+trả\s+lời\s+sai|you\s+answered\s+wrong",
        
        # User pointing out inconsistencies
        r"mâu\s+thuẫn|contradiction|inconsistent|không\s+nhất\s+quán",
        r"vì\s+sao\s+mâu\s+thuẫn|why\s+contradiction",
        r"sao\s+bạn\s+vừa\s+nói|why\s+did\s+you\s+just\s+say",
        r"bạn\s+vừa\s+nói\s+không\s+đủ|you\s+just\s+said\s+not\s+enough",
        
        # User asking about logic/pipeline
        r"vì\s+sao\s+bạn\s+trả\s+lời|why\s+did\s+you\s+answer",
        r"logic\s+pipeline|quy\s+trình\s+xử\s+lý",
        r"bạn\s+xử\s+lý\s+như\s+thế\s+nào|how\s+do\s+you\s+process",
        
        # User asking about errors
        r"lỗi\s+logic|logic\s+error",
        r"guard\s+không\s+chặn|guard\s+didn't\s+block",
        r"tại\s+sao\s+guard|why\s+guard",
    ]
    
    # Check if question contains honesty keywords
    for pattern in honesty_keywords:
        if re.search(pattern, question_lower):
            logger.info(f"Honesty question detected: {question[:100]}...")
            return True
    
    return False


def _extract_full_named_entity(question: str) -> Optional[str]:
    """
    Extracts a full named entity from the question, prioritizing quoted terms,
    Vietnamese/English specific entity patterns, and then capitalized phrases.
    This aims to get the most complete and accurate entity for refusal messages.
    """
    # 1. Prioritize quoted terms
    quoted_match = re.search(r'"([^"]+)"', question)
    if quoted_match:
        return quoted_match.group(1).strip()

    # 2. Look for specific Vietnamese entity patterns (e.g., "Hiệp ước X YYYY", "Hội chứng Z")
    vietnamese_patterns = [
        r"(?:Hiệp ước|Hội nghị|Hội chứng|Định đề|Học thuyết|Chủ nghĩa)\s+[\p{L}\s\d-]+",
        r"[\p{L}\s\d-]+\s+(?:Hiệp ước|Hội nghị|Hội chứng|Định đề|Học thuyết|Chủ nghĩa)",
    ]
    for pattern in vietnamese_patterns:
        match = re.search(pattern, question, re.IGNORECASE | re.UNICODE)
        if match:
            return match.group(0).strip()

    # 3. Look for specific English entity patterns (e.g., "Daxonia Treaty 1956", "Veridian Syndrome")
    english_patterns = [
        r"(?:Treaty|Conference|Syndrome|Postulate|Doctrine|Ism)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+\d{4}",
        r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Treaty|Conference|Syndrome|Postulate|Doctrine|Ism)\s+\d{4}",
        r"[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Syndrome|Postulate|Doctrine|Ism)",
    ]
    for pattern in english_patterns:
        match = re.search(pattern, question)
        if match:
            return match.group(0).strip()

    # 4. Fallback to capitalized phrases (multi-word)
    capitalized_phrases = re.findall(r'\b[A-Z][\p{L}\d]*(?:\s+[A-Z][\p{L}\d]*)+\b', question, re.UNICODE)
    if capitalized_phrases:
        # Prioritize longer phrases
        return max(capitalized_phrases, key=len).strip()

    # 5. Fallback to single capitalized word if it looks like a name
    single_capitalized = re.findall(r'\b[A-Z][\p{L}\d]*\b', question, re.UNICODE)
    if single_capitalized:
        # Filter out common short words that might be capitalized at sentence start
        common_short_words = {"The", "A", "An", "Is", "It", "In", "On", "At", "For", "With", "By", "From", "As", "About"}
        filtered_words = [w for w in single_capitalized if w not in common_short_words and len(w) > 2]
        if filtered_words:
            return max(filtered_words, key=len).strip()  # Return longest filtered word

    return None


def build_honesty_response(question: str, detected_lang: str) -> str:
    """
    Build honest response explaining pipeline and acknowledging errors.
    
    This handler:
    - Acknowledges user's critique directly
    - Explains what happened (RAG → model → guard → fallback)
    - Commits to correct logic (no source → only "don't know")
    - Does NOT use consciousness/emotion templates
    
    Args:
        question: User's question
        detected_lang: Language code
        
    Returns:
        Honest response explaining pipeline
    """
    # Extract entity from question if available
    entity = _extract_full_named_entity(question)
    entity_mention = f" \"{entity}\"" if entity else ""
    
    if detected_lang == "vi":
        response = (
            f"Mình hiểu sự thất vọng của bạn. Đúng là câu trả lời trước đó đã không tuân thủ đúng nguyên tắc trung thực của StillMe.\n\n"
            f"**Giải thích quy trình:**\n\n"
            f"- Khi bạn hỏi về một khái niệm{entity_mention}, hệ thống RAG của mình sẽ tìm kiếm trong cơ sở tri thức.\n"
            f"- Nếu không tìm thấy nguồn đáng tin cậy (như đã xảy ra), đáng lẽ StillMe phải ngay lập tức trả lời rằng 'không có bằng chứng' hoặc 'không biết'.\n"
            f"- Tuy nhiên, trong trường hợp đó, mô hình ngôn ngữ đã tự động suy diễn và tạo ra một câu chuyện nghe có vẻ hợp lý, và cơ chế guardrail đã không chặn hoàn toàn narrative đó, mà chỉ thêm một disclaimer nhẹ.\n\n"
            f"**Cam kết của StillMe:**\n\n"
            f"StillMe ưu tiên sự trung thực và minh bạch tuyệt đối. Khi không có nguồn xác thực, mình sẽ chỉ trả lời rằng mình không có thông tin hoặc khái niệm đó có thể không tồn tại. Mình sẽ không bao giờ tự suy diễn hay bịa đặt thông tin.\n\n"
            f"Mình đang liên tục cải thiện các cơ chế guardrail để đảm bảo điều này không tái diễn. Cảm ơn bạn đã chỉ ra lỗi này, điều đó rất quan trọng để StillMe học hỏi và trở nên tốt hơn."
        )
    else:
        response = (
            f"I understand your frustration. You are right that the previous answer did not adhere to StillMe's honesty principles.\n\n"
            f"**Process Explanation:**\n\n"
            f"- When you asked about a concept{entity_mention}, my RAG system searched its knowledge base.\n"
            f"- If no reliable sources were found (as was the case), StillMe should have immediately responded with 'no evidence' or 'I don't know'.\n"
            f"- However, the language model then speculated and generated a plausible-sounding narrative, and the guardrail mechanism did not fully block that narrative, only adding a mild disclaimer.\n\n"
            f"**StillMe's Commitment:**\n\n"
            f"StillMe prioritizes absolute honesty and transparency. When no verified sources are found, I will only state that I lack information or that the concept may not exist. I will never speculate or fabricate information.\n\n"
            f"I am continuously improving my guardrail mechanisms to ensure this does not happen again. Thank you for pointing out this error; it is crucial for StillMe to learn and improve."
        )
    
    return response

