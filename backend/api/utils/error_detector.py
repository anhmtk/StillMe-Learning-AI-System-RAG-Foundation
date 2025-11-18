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
        r"api error:",
        r"http/1\.1 \d{3}",
        r"bad request",
        r"internal server error",
        r"service unavailable",
    ]
    
    # Generic error patterns
    generic_error_patterns = [
        r"error:",
        r"exception:",
        r"failed:",
        r"timeout",
        r"connection.*closed",
        r"peer.*closed",
    ]
    
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
            if (text_lower.startswith(("error", "exception", "failed")) or 
                re.search(r"\d{3}", text) or  # Has HTTP status code
                "api" in text_lower):
                logger.debug(f"Detected generic technical error: {text[:100]}...")
                return True, "generic"
    
    return False, ""


def get_fallback_message_for_error(error_type: str, detected_lang: str = "vi") -> str:
    """
    Get a user-friendly fallback message in the detected language.
    
    Args:
        error_type: Type of error ("context_overflow", "api_error", "generic")
        detected_lang: User's language code
        
    Returns:
        User-friendly error message in the detected language
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
    
    return messages.get(detected_lang, messages.get("en", "A technical error occurred."))

