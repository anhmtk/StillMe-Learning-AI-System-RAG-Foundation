"""
FallbackHandler - Provides safe fallback answers when validation fails
"""

import logging
from typing import List, Optional
from .base import ValidationResult

logger = logging.getLogger(__name__)


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
        detected_lang: str = 'en'
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
        
        # Check for critical failures that require fallback
        if "missing_uncertainty_no_context" in reasons:
            return self._get_no_context_fallback(user_question, detected_lang)
        
        if "missing_citation" in reasons and not ctx_docs:
            return self._get_no_context_fallback(user_question, detected_lang)
        
        if "low_overlap" in reasons and not ctx_docs:
            return self._get_no_context_fallback(user_question, detected_lang)
        
        # If no specific fallback, return original (may be risky, but better than nothing)
        logger.warning(f"No specific fallback for reasons: {reasons}, returning original answer")
        return original_answer
    
    def _get_no_context_fallback(self, user_question: str, detected_lang: str = 'en') -> str:
        """
        Generate fallback answer when no context is available
        
        Args:
            user_question: User's question
            detected_lang: Detected language code
            
        Returns:
            Safe fallback answer in appropriate language
        """
        if detected_lang == 'vi':
            return f"""Tôi xin lỗi. Dựa trên thông tin tôi tìm kiếm, hiện tại StillMe không có dữ liệu đủ tin cậy để trả lời câu hỏi của bạn về "{user_question[:50]}...".

StillMe là hệ thống học tập liên tục, tự động cập nhật kiến thức từ RSS feeds, arXiv, và các nguồn tin cậy khác mỗi 4 giờ (6 lần mỗi ngày). 

Bạn có thể:
- Thử lại sau vài giờ khi StillMe đã học thêm thông tin mới
- Đặt câu hỏi theo cách khác hoặc chia nhỏ câu hỏi
- Yêu cầu tôi giúp tìm kiếm các chủ đề liên quan

Tôi muốn trả lời chính xác dựa trên kiến thức đã được xác minh, thay vì đoán mò. Cảm ơn bạn đã hiểu."""
        
        elif detected_lang == 'zh':
            return f"""抱歉。根据我搜索的信息，目前 StillMe 没有足够可靠的数据来回答您关于"{user_question[:50]}..."的问题。

StillMe 是一个持续学习系统，每 4 小时（每天 6 次）自动从 RSS 源、arXiv 和其他可信来源更新知识。

您可以：
- 几小时后再试，当 StillMe 学习了新信息时
- 以不同方式提问或将问题分解
- 要求我帮助查找相关主题

我希望基于已验证的知识准确回答，而不是猜测。感谢您的理解。"""
        
        else:  # Default to English
            return f"""I apologize. Based on my search, StillMe currently doesn't have sufficiently reliable data to answer your question about "{user_question[:50]}...".

StillMe is a continuous learning system that automatically updates knowledge from RSS feeds, arXiv, and other trusted sources every 4 hours (6 times per day).

You can:
- Try again in a few hours when StillMe has learned new information
- Rephrase your question or break it into smaller parts
- Ask me to help find related topics

I prefer to answer accurately based on verified knowledge rather than guessing. Thank you for understanding."""

