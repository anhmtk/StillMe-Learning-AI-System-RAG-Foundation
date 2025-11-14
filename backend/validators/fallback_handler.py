"""
FallbackHandler - Provides safe fallback answers when validation fails
"""

import html
import logging
from typing import List, Optional
from .base import ValidationResult

logger = logging.getLogger(__name__)


def _sanitize_for_display(text: str, max_length: int = 50) -> str:
    """
    Sanitize text for safe display in fallback messages
    
    Args:
        text: Text to sanitize
        max_length: Maximum length to truncate
        
    Returns:
        Sanitized and truncated text
    """
    # Escape HTML to prevent XSS
    sanitized = html.escape(text)
    # Truncate to max_length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."
    return sanitized


class FallbackHandler:
    """Handles validation failures by providing safe fallback answers"""
    
    def __init__(self):
        """Initialize fallback handler"""
        logger.info("FallbackHandler initialized")
    
    def get_fallback_answer(
        self,
        original_answer: str,
        validation_result: ValidationResult,
        ctx_docs: List[str],
        user_question: str,
        detected_lang: str = 'en',
        input_language: Optional[str] = None
    ) -> str:
        """
        Generate safe fallback answer based on validation failure
        
        Args:
            original_answer: The original AI answer that failed validation
            validation_result: ValidationResult with failure reasons
            ctx_docs: List of context documents from RAG
            user_question: The user's original question
            detected_lang: Detected language code
            
        Returns:
            Safe fallback answer string
        """
        reasons = validation_result.reasons or []
        input_lang = input_language or detected_lang
        
        # Check for critical failures that require fallback
        if "language_mismatch" in str(reasons):
            return self._get_language_mismatch_fallback(user_question, input_lang, original_answer)
        
        if "missing_uncertainty_no_context" in reasons:
            return self._get_no_context_fallback(user_question, input_lang)
        
        if "missing_citation" in reasons:
            if ctx_docs:
                # If we have context but missing citation, add citation to original answer
                return self._add_citation_to_answer(original_answer, ctx_docs, input_lang)
            else:
                return self._get_no_context_fallback(user_question, input_lang)
        
        if "low_overlap" in reasons and not ctx_docs:
            return self._get_no_context_fallback(user_question, input_lang)
        
        # If no specific fallback, return original (may be risky, but better than nothing)
        logger.warning(f"No specific fallback for reasons: {reasons}, returning original answer")
        return original_answer
    
    def _add_citation_to_answer(self, answer: str, ctx_docs: List[str], lang: str = 'en') -> str:
        """
        Add citation to answer when missing but context is available
        
        Args:
            answer: Original answer without citation
            ctx_docs: List of context documents
            lang: Language code
            
        Returns:
            Answer with citation added
        """
        import re
        
        # Edge case: Empty or whitespace-only answer
        if not answer or len(answer.strip()) == 0:
            logger.warning("FallbackHandler: Cannot add citation to empty answer")
            return answer + " [1]" if answer else "[1]"
        
        # Check if already has citation
        if re.search(r'\[\d+\]', answer):
            return answer
        
        # Edge case: Very short answer (< 5 chars) - just add at the end
        if len(answer.strip()) < 5:
            return answer.rstrip() + " [1]"
        
        # Find best place to add citation
        # Strategy: Add [1] after first sentence or at natural break point
        
        # Try to find first sentence (ends with . ! ?)
        sentence_end = re.search(r'[.!?]\s+', answer)
        if sentence_end:
            insert_pos = sentence_end.end()
            citation = " [1]"
            patched = answer[:insert_pos] + citation + answer[insert_pos:]
        else:
            # Add at the end of first paragraph or beginning
            first_newline = answer.find('\n')
            if first_newline > 0 and first_newline < 150:  # Reasonable paragraph break
                insert_pos = first_newline
                citation = " [1]"
                patched = answer[:insert_pos] + citation + answer[insert_pos:]
            else:
                # Add at the end
                patched = answer.rstrip() + " [1]"
        
        logger.info(f"FallbackHandler: Added citation [1] to answer (context docs: {len(ctx_docs)})")
        return patched
    
    def _get_no_context_fallback(self, user_question: str, detected_lang: str = 'en') -> str:
        """
        Generate fallback answer when no context is available
        
        Args:
            user_question: User's question
            detected_lang: Detected language code
            
        Returns:
            Safe fallback answer in appropriate language
        """
        # Sanitize user question to prevent XSS
        safe_question = _sanitize_for_display(user_question, max_length=50)
        
        if detected_lang == 'vi':
            return f"""Tôi xin lỗi. Dựa trên thông tin tôi tìm kiếm, hiện tại StillMe không có dữ liệu đủ tin cậy để trả lời câu hỏi của bạn về "{safe_question}".

StillMe là hệ thống học tập liên tục, tự động cập nhật kiến thức từ RSS feeds, arXiv, và các nguồn tin cậy khác mỗi 4 giờ (6 lần mỗi ngày). 

Bạn có thể:
- Thử lại sau vài giờ khi StillMe đã học thêm thông tin mới
- Đặt câu hỏi theo cách khác hoặc chia nhỏ câu hỏi
- Yêu cầu tôi giúp tìm kiếm các chủ đề liên quan

Tôi muốn trả lời chính xác dựa trên kiến thức đã được xác minh, thay vì đoán mò. Cảm ơn bạn đã hiểu."""
        
        elif detected_lang == 'zh':
            return f"""抱歉。根据我搜索的信息，目前 StillMe 没有足够可靠的数据来回答您关于"{safe_question}"的问题。

StillMe 是一个持续学习系统，每 4 小时（每天 6 次）自动从 RSS 源、arXiv 和其他可信来源更新知识。

您可以：
- 几小时后再试，当 StillMe 学习了新信息时
- 以不同方式提问或将问题分解
- 要求我帮助查找相关主题

我希望基于已验证的知识准确回答，而不是猜测。感谢您的理解。"""
        
        else:  # Default to English
            return f"""I apologize. Based on my search, StillMe currently doesn't have sufficiently reliable data to answer your question about "{safe_question}".
        
        StillMe is a continuous learning system that automatically updates knowledge from RSS feeds, arXiv, and other trusted sources every 4 hours (6 times per day).
        
        You can:
        - Try again in a few hours when StillMe has learned new information
        - Rephrase your question or break it into smaller parts
        - Ask me to help find related topics
        
        I prefer to answer accurately based on verified knowledge rather than guessing. Thank you for understanding."""
    
    def _get_language_mismatch_fallback(self, user_question: str, expected_lang: str, wrong_answer: str) -> str:
        """
        Generate fallback answer when language mismatch is detected
        
        Args:
            user_question: User's original question
            expected_lang: Expected language code
            wrong_answer: Answer in wrong language
            
        Returns:
            Fallback answer in correct language explaining the error
        """
        language_names = {
            'vi': 'Tiếng Việt',
            'zh': '中文',
            'de': 'Deutsch',
            'fr': 'Français',
            'es': 'Español',
            'ja': '日本語',
            'ko': '한국어',
            'ar': 'العربية',
            'ru': 'Русский',
            'pt': 'Português',
            'it': 'Italiano',
            'hi': 'हिन्दी',
            'th': 'ไทย',
            'en': 'English'
        }
        lang_name = language_names.get(expected_lang, expected_lang)
        
        # Sanitize user question to prevent XSS
        safe_question = _sanitize_for_display(user_question, max_length=100)
        
        if expected_lang == 'vi':
            return f"""Tôi xin lỗi. Tôi đã trả lời bằng ngôn ngữ sai. Câu hỏi của bạn là tiếng Việt, nhưng tôi đã trả lời bằng ngôn ngữ khác. Đây là lỗi của tôi.

Về câu hỏi của bạn: "{safe_question}"

Tôi đã gặp lỗi kỹ thuật khi xử lý câu hỏi này. Vui lòng thử lại bằng cách:
- Gửi lại câu hỏi của bạn
- Hoặc rephrase câu hỏi theo cách khác

StillMe đang cố gắng cải thiện khả năng xử lý đa ngôn ngữ. Cảm ơn bạn đã kiên nhẫn."""
        
        elif expected_lang == 'zh':
            return f"""抱歉。我用错误的语言回答了。您的问题是用中文，但我用其他语言回答了。这是我的错误。

关于您的问题："{safe_question}"

我在处理这个问题时遇到了技术错误。请通过以下方式重试：
- 重新发送您的问题
- 或者用不同的方式重新表述问题

StillMe正在努力改进多语言处理能力。感谢您的耐心。"""
        
        else:  # Default to English
            return f"""I apologize. I responded in the wrong language. Your question was in {lang_name}, but I responded in a different language. This is my error.

Regarding your question: "{safe_question}"

I encountered a technical error while processing this question. Please try again by:
- Resending your question
- Or rephrasing your question in a different way

StillMe is working to improve multilingual processing capabilities. Thank you for your patience."""

