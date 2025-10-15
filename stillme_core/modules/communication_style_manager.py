#!/usr/bin/env python3
"""
🎭 COMMUNICATION STYLE MANAGER - QUẢN LÝ PHONG CÁCH GIAO TIẾP
PURPOSE / MỤC ĐÍCH:
- Quản lý và tối ưu hóa phong cách giao tiếp cho StillMe AI
- Làm cho phản hồi AI tự nhiên, ngắn gọn và hiệu quả hơn
- Giảm token usage trong khi cải thiện trải nghiệm người dùng

FUNCTIONALITY / CHỨC NĂNG:
- Phát hiện và loại bỏ các phản hồi dài dòng, chung chung
- Tối ưu hóa cấu trúc câu và từ ngữ
- Quản lý phong cách xưng hô (anh/em, mình/bạn)
- Tự động điều chỉnh tone và style theo ngữ cảnh

TECHNICAL DETAILS / CHI TIẾT KỸ THUẬT:
- Regex patterns để phát hiện verbose responses
- Dynamic communication style preferences
- Context-aware response optimization
- Token usage reduction algorithms
"""

import re


class CommunicationStyleManager:
    """
    Manages and optimizes communication style for StillMe AI responses.

    This module applies efficient communication rules to make responses
    more human-like, concise, and effective while reducing token usage.
    """

    def __init__(self):
        """Initialize the Communication Style Manager."""
        # Patterns for detecting verbose, generic responses
        self.verbose_patterns = [
            r"tất nhiên rồi,?\s*tôi rất sẵn lòng",
            r"tôi rất vui được giúp đỡ bạn",
            r"để làm được điều đó,?\s*tôi sẽ cần",
            r"đầu tiên là.*thứ hai là.*cuối cùng là",
            r"tôi hiểu bạn đang gặp khó khăn",
            r"đây là một câu hỏi rất thú vị",
            r"cảm ơn bạn đã hỏi",
            r"tôi sẽ cố gắng giải thích",
            r"để trả lời câu hỏi này một cách chính xác",
        ]

        # Keywords that indicate missing information
        self.missing_info_keywords = [
            "file",
            "đường dẫn",
            "path",
            "lỗi",
            "error",
            "mô tả",
            "description",
            "tên",
            "name",
            "thông tin",
            "information",
            "chi tiết",
            "details",
        ]

        # Common filler phrases to remove (Vietnamese and English)
        self.filler_phrases = [
            "tất nhiên rồi",
            "tôi rất sẵn lòng",
            "tôi rất vui được",
            "cảm ơn bạn đã hỏi",
            "đây là một câu hỏi",
            "để trả lời câu hỏi này",
            "tôi sẽ cố gắng",
            "tôi hiểu bạn đang",
            "i'm very happy",
            "i'm very glad",
            "thank you for asking",
            "of course",
            "certainly",
            "i'd be happy to",
            "i'd be glad to",
        ]

        # Question templates for missing information
        self.question_templates = {
            "file": "Bạn cho mình xin **đường dẫn đến file** nhé.",
            "error": "Bạn cho mình xin **mô tả lỗi** cụ thể nhé.",
            "name": "Bạn cho mình xin **tên** cụ thể nhé.",
            "info": "Bạn cho mình xin **thông tin** còn thiếu nhé.",
            "details": "Bạn cho mình xin **chi tiết** cụ thể nhé.",
        }

    def optimize_response(self, raw_response: str) -> str:
        """
        Optimize a raw response to be more efficient and human-like.

        Args:
            raw_response: The original response from AI model

        Returns:
            Optimized response that is more concise and effective
        """
        if not raw_response or not raw_response.strip():
            return raw_response

        # Step 1: Check if response is asking for missing information
        optimized = self._apply_ask_first_rule(raw_response)
        if optimized != raw_response:
            return optimized

        # Step 2: Apply concise communication rules
        optimized = self._apply_concise_rule(optimized)

        # Step 3: Apply quick confirmation rules
        optimized = self._apply_quick_confirmation_rule(optimized)

        return optimized

    def _apply_ask_first_rule(self, response: str) -> str:
        """
        Rule 1: If response is generic and asking for missing info,
        replace with a concise question.
        """
        response_lower = response.lower()

        # Check if response contains verbose patterns
        is_verbose = any(
            re.search(pattern, response_lower) for pattern in self.verbose_patterns
        )

        # Check if response is asking for missing information
        has_missing_info = any(
            keyword in response_lower for keyword in self.missing_info_keywords
        )

        if is_verbose and has_missing_info:
            # Determine what information is missing
            if any(word in response_lower for word in ["file", "đường dẫn", "path"]):
                return self.question_templates["file"]
            elif any(word in response_lower for word in ["lỗi", "error", "mô tả"]):
                return self.question_templates["error"]
            elif any(word in response_lower for word in ["tên", "name"]):
                return self.question_templates["name"]
            elif any(word in response_lower for word in ["chi tiết", "details"]):
                return self.question_templates["details"]
            else:
                return self.question_templates["info"]

        return response

    def _apply_concise_rule(self, response: str) -> str:
        """
        Rule 2: Remove unnecessary filler phrases and verbose explanations.
        """
        optimized = response

        # Remove filler phrases
        for phrase in self.filler_phrases:
            # Remove phrase at the beginning
            pattern = rf"^{re.escape(phrase)},?\s*"
            optimized = re.sub(pattern, "", optimized, flags=re.IGNORECASE)

            # Remove phrase in the middle
            pattern = rf",?\s*{re.escape(phrase)},?\s*"
            optimized = re.sub(pattern, " ", optimized, flags=re.IGNORECASE)

        # Remove excessive politeness at the beginning
        politeness_patterns = [
            r"^tất nhiên rồi,?\s*",
            r"^cảm ơn bạn đã hỏi,?\s*",
            r"^tôi rất vui được giúp đỡ,?\s*",
        ]

        for pattern in politeness_patterns:
            optimized = re.sub(pattern, "", optimized, flags=re.IGNORECASE)

        # Clean up multiple spaces and punctuation
        optimized = re.sub(r"\s+", " ", optimized)
        optimized = re.sub(r"\s*,\s*,", ",", optimized)
        optimized = re.sub(r"\s*\.\s*\.", ".", optimized)

        return optimized.strip()

    def _apply_quick_confirmation_rule(self, response: str) -> str:
        """
        Rule 3: Ensure responses go straight to the point when sufficient info is available.
        """
        # If response is already concise (under 100 chars), keep it
        if len(response) <= 100:
            return response

        # Look for direct answers that can be shortened
        direct_answer_patterns = [
            r"để trả lời câu hỏi của bạn.*?\.(.*)",
            r"câu trả lời là.*?\.(.*)",
            r"theo như tôi hiểu.*?\.(.*)",
        ]

        for pattern in direct_answer_patterns:
            match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
            if match:
                # Extract the core answer
                core_answer = match.group(1).strip()
                if len(core_answer) < len(response) * 0.7:  # If significantly shorter
                    return core_answer

        return response

    def get_optimization_stats(self, original: str, optimized: str) -> dict:
        """
        Get statistics about the optimization performed.

        Args:
            original: Original response
            optimized: Optimized response

        Returns:
            Dictionary with optimization statistics
        """
        return {
            "original_length": len(original),
            "optimized_length": len(optimized),
            "reduction_percentage": (
                round((1 - len(optimized) / len(original)) * 100, 1) if original else 0
            ),
            "was_optimized": original != optimized,
        }
