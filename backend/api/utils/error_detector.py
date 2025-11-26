"""
Error Detection Utilities for StillMe
Detects technical error messages that should not be treated as valid LLM responses
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


def is_technical_error(text: str) -> Tuple[bool, str]:
    """
    Detect if text is a technical error message, not a valid LLM response.
    
    Args:
        text: Text to check
        
    Returns:
        Tuple of (is_error, error_type)
        - is_error: True if text is a technical error
        - error_type: Type of error detected (e.g., "context_overflow", "api_error", "generic")
    """
    if not text or len(text.strip()) < 10:
        return False, ""
    
    text_lower = text.lower()
    
    # Context overflow patterns
    context_overflow_patterns = [
        r"i encountered an error.*context overflow",
        r"context overflow",
        r"maximum context length",
        r"context length is",
        r"messages resulted in.*tokens",
        r"requested about.*tokens",
        r"exceeds.*context length",
        r"context.*exceeded",
    ]
    
    # API error patterns
    api_error_patterns = [
        r"openrouter api error",
        r"openai api error",
        r"deepseek api error",
        r"claude api error",
        r"gemini api error",
        r"ollama api error",
        r"api error:",
        r"api returned.*error",  # Catch "API returned unexpected response format" etc.
        r"api returned.*empty",  # Catch "API returned empty or None content" etc.
        r"api returned.*unexpected",  # Catch "API returned unexpected response format" etc.
        r"http/1\.1 \d{3}",
        r"bad request",
        r"internal server error",
        r"service unavailable",
    ]
    
    # Generic error patterns
    generic_error_patterns = [
        r"i encountered an error",  # CRITICAL: Detect "I encountered an error:" from generate_ai_response
        r"error:",
        r"exception:",
        r"failed:",
        r"timeout",
        r"connection.*closed",
        r"peer.*closed",
    ]
    
    # CRITICAL: Technical error messages from get_fallback_message_for_error (these should NOT be detected as errors)
    # These are user-friendly fallback messages, not actual technical errors
    # BUT: If they are the ONLY content (short response), they should be detected as errors for retry logic
    fallback_message_patterns = [
        r"stillme is experiencing a technical issue",
        r"stillme đang gặp sự cố kỹ thuật",
        r"i cannot provide a good answer",
        r"mình không thể trả lời tốt",
        r"i will suggest to the developer",
        r"mình sẽ đề xuất cho developer",
        r"cannot provide a good answer to this question with the current configuration",  # Exact match from test results
    ]
    
    # Check if text is a fallback message first (these are OK, not errors)
    # BUT: If it's a short response (< 300 chars) with ONLY fallback message, treat as error for retry
    text_lower_for_fallback = text_lower
    for pattern in fallback_message_patterns:
        if re.search(pattern, text_lower_for_fallback):
            # This is a fallback message, not a technical error
            # But we still want to detect it as an error if it's the ONLY content (no actual answer)
            # If it's part of a longer response with actual content, it's OK
            if len(text.strip()) < 300:  # Short response = likely just fallback message
                logger.debug(f"Detected fallback message (short): {text[:100]}...")
                return True, "generic"  # Treat as error if it's just the fallback message
            else:
                # Long response with fallback message embedded = OK, not an error
                return False, ""
    
    # Check context overflow first (most specific)
    for pattern in context_overflow_patterns:
        if re.search(pattern, text_lower):
            logger.debug(f"Detected context overflow error: {text[:100]}...")
            return True, "context_overflow"
    
    # Check API errors
    for pattern in api_error_patterns:
        if re.search(pattern, text_lower):
            logger.debug(f"Detected API error: {text[:100]}...")
            return True, "api_error"
    
    # Check generic errors (but be more careful - might be false positive)
    for pattern in generic_error_patterns:
        if re.search(pattern, text_lower):
            # Additional check: if it looks like a technical error message (starts with error, has status codes, etc.)
            if (text_lower.startswith(("i encountered an error", "error", "exception", "failed")) or 
                re.search(r"\d{3}", text) or  # Has HTTP status code
                "api" in text_lower):
                logger.debug(f"Detected generic technical error: {text[:100]}...")
                return True, "generic"
    
    return False, ""


def get_fallback_message_for_error(
    error_type: str, 
    detected_lang: str = "vi",
    user_question: str = "",
    is_philosophical: bool = False,
    ctx_docs: list = None
) -> str:
    """
    Get a user-friendly fallback message in the detected language.
    
    Args:
        error_type: Type of error ("context_overflow", "api_error", "generic")
        detected_lang: User's language code
        user_question: Optional user question (to detect factual questions and add citations)
        is_philosophical: Optional flag indicating if question is philosophical
        ctx_docs: Optional context documents (for citation validation)
        
    Returns:
        User-friendly error message in the detected language (with citation if factual question)
    """
    if error_type == "context_overflow":
        messages = {
            "vi": (
                "Hiện tại hệ thống của StillMe đang gặp giới hạn ngữ cảnh (context) khi xử lý câu hỏi này. "
                "Câu hỏi của bạn có thể quá dài hoặc phức tạp, khiến prompt vượt quá giới hạn của model. "
                "Bạn có thể thử rút ngắn câu hỏi, hoặc chia nhỏ thành nhiều câu hỏi ngắn hơn. "
                "Mình xin lỗi vì không thể trả lời đầy đủ câu hỏi này với giới hạn hiện tại."
            ),
            "en": (
                "StillMe is currently encountering a context limit when processing this question. "
                "Your question may be too long or complex, causing the prompt to exceed the model's limit. "
                "You can try shortening your question or breaking it into smaller parts. "
                "I apologize for not being able to fully answer this question within the current limits."
            ),
        }
    elif error_type == "api_error":
        messages = {
            "vi": (
                "StillMe đang gặp sự cố kỹ thuật khi kết nối với model AI. "
                "Vui lòng thử lại sau một chút, hoặc liên hệ với developer nếu vấn đề vẫn tiếp tục. "
                "Mình xin lỗi vì sự bất tiện này."
            ),
            "en": (
                "StillMe is experiencing a technical issue connecting to the AI model. "
                "Please try again in a moment, or contact the developer if the issue persists. "
                "I apologize for the inconvenience."
            ),
        }
    else:  # generic
        messages = {
            "vi": (
                "StillMe đang gặp sự cố kỹ thuật khi xử lý câu hỏi này. "
                "Mình không thể trả lời tốt câu hỏi này với cấu hình hiện tại. "
                "Bạn có thể thử lại sau, hoặc mình sẽ đề xuất cho developer tinh chỉnh lại hệ thống."
            ),
            "en": (
                "StillMe is experiencing a technical issue processing this question. "
                "I cannot provide a good answer to this question with the current configuration. "
                "You can try again later, or I will suggest to the developer to fine-tune the system."
            ),
        }
    
    fallback_message = messages.get(detected_lang, messages.get("en", "A technical error occurred."))
    
    # CRITICAL: If this is a factual question, add citation for transparency
    if user_question:
        try:
            from backend.validators.citation import CitationRequired
            citation_validator = CitationRequired(required=True)
            citation_result = citation_validator.run(
                fallback_message,
                ctx_docs=ctx_docs or [],
                is_philosophical=is_philosophical,
                user_question=user_question
            )
            if citation_result.patched_answer:
                logger.info(f"✅ Added citation to fallback message for factual question. Reasons: {citation_result.reasons}")
                return citation_result.patched_answer
        except Exception as e:
            logger.warning(f"⚠️ Error adding citation to fallback message: {e}")
            # Return original message if citation addition fails
    
    return fallback_message


def is_fallback_message(text: str) -> bool:
    """
    Detects whether a given text is a user-facing fallback message
    generated by get_fallback_message_for_error, e.g. context limit
    explanations in Vietnamese or other languages.
    
    These messages are terminal - they should not be:
    - Validated by ValidationChain
    - Evaluated by Quality Evaluator
    - Rewritten by DeepSeek
    - Learned by Conversation Learning Extractor
    
    Args:
        text: Text to check
        
    Returns:
        True if text is a fallback meta-answer, False otherwise
    """
    if not text or len(text.strip()) < 50:
        return False
    
    normalized = text.strip()
    text_lower = normalized.lower()
    
    # CRITICAL: Check for exact fallback message patterns (match exact phrases from get_fallback_message_for_error)
    # Vietnamese patterns
    vi_patterns = [
        "hiện tại hệ thống của stillme đang gặp giới hạn ngữ cảnh",
        "prompt vượt quá giới hạn của model",
        "stillme đang gặp sự cố kỹ thuật khi kết nối với model ai",
        "stillme đang gặp sự cố kỹ thuật khi xử lý câu hỏi này",
        "mình không thể trả lời tốt câu hỏi này với cấu hình hiện tại",
        "mình xin lỗi vì không thể trả lời đầy đủ câu hỏi này",
        "mình sẽ đề xuất cho developer",
    ]
    
    # English patterns (exact matches from get_fallback_message_for_error)
    en_patterns = [
        "stillme is currently encountering a context limit",
        "causing the prompt to exceed the model's limit",
        "stillme is experiencing a technical issue connecting to the ai model",
        "stillme is experiencing a technical issue processing this question",
        "i cannot provide a good answer to this question with the current configuration",
        "i apologize for not being able to fully answer this question",
        "i will suggest to the developer",
    ]
    
    # CRITICAL: Check if text is EXACTLY or PREDOMINANTLY a fallback message
    # If the text is short (< 500 chars) and contains a fallback pattern, it's likely a fallback
    # If the text is longer but starts with a fallback pattern, it's also likely a fallback
    all_patterns = vi_patterns + en_patterns
    
    # Check if text starts with or contains a fallback pattern
    for pattern in all_patterns:
        if pattern in text_lower:
            # If text is short, it's definitely a fallback
            if len(normalized) < 500:
                return True
            # If text starts with fallback pattern, it's likely a fallback
            if text_lower.startswith(pattern[:30]):  # Check first 30 chars of pattern
                return True
            # If fallback pattern is in the first 200 chars, it's likely a fallback
            if pattern in text_lower[:200]:
                return True
    
    return False

