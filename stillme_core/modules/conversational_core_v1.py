#!/usr/bin/env python3
"""
ConversationalCore_v1 - Bộ xử lý hội thoại chính cho hệ thống AI StillMe

Chức năng:
- Quản lý lịch sử hội thoại với giới hạn tùy chỉnh
- Tích hợp PersonaMorph_v1 để điều chỉnh phong cách
- Hỗ trợ câu trả lời tạm thời khi xử lý
- Đảm bảo phản hồi tự nhiên, nhân văn
"""

import logging
import random
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationalCore:
    """Core xử lý hội thoại với khả năng duy trì ngữ cảnh và phong cách"""

    DEFAULT_DELAY_MESSAGES = [
        "Đợi e xíu nhé, e đang kiểm tra...",
        "E đang tìm hiểu thông tin, chờ xíu ạ...",
        "Một chút thôi, e đang xử lý...",
        "Để e suy nghĩ xíu nhé...",
        "E đang tra cứu thông tin cho bạn...",
        "Chờ e tí, e đang nghĩ cách trả lời...",
        "E cần xem lại một chút, đợi e nhé...",
        "Để e tìm câu trả lời tốt nhất...",
        "E đang phân tích câu hỏi của bạn...",
        "Một lát thôi, e sắp có câu trả lời...",
    ]

    def __init__(
        self,
        persona_engine: Any,  # Type hint linh hoạt cho persona engine
        delay_messages: list[str] | None = None,
        max_history: int = 10,
    ):
        """
        Khởi tạo conversational core

        Args:
            persona_engine: Engine điều chỉnh phong cách trả lời
            delay_messages: Danh sách câu che delay (mặc định có sẵn)
            max_history: Số lượng tin nhắn tối đa (tính theo cặp user-agent)
        """
        self.persona_engine = persona_engine
        self.max_history = max(5, min(max_history, 20))  # Giới hạn 5-20
        self.history: list[dict[str, str]] = []
        self.delay_messages = delay_messages or self.DEFAULT_DELAY_MESSAGES.copy()

        # Initialize IdentityHandler
        try:
            from .identity_handler import IdentityHandler

            self.identity_handler = IdentityHandler()
            logger.info("✅ IdentityHandler integrated into ConversationalCore")
        except ImportError as e:
            logger.warning(f"IdentityHandler not available: {e}")
            self.identity_handler = None

        logger.info(
            f"Initialized ConversationalCore with max_history={self.max_history}"
        )

    def respond(self, user_input: str) -> str:
        """
        Xử lý câu nhập từ user và trả về phản hồi phù hợp

        Args:
            user_input: Câu nhập từ người dùng

        Returns:
            Phản hồi được tạo bởi persona engine hoặc câu delay
        """
        if not user_input.strip():
            logger.warning("Received empty input")
            return random.choice(
                [
                    "E chưa nghe rõ a nói gì ạ",
                    "A có thể nhắc lại được không ạ?",
                    "Dạ? E chưa hiểu ý a lắm",
                ]
            )

        try:
            # Thêm input vào lịch sử
            self._add_to_history("user", user_input)

            # Check for secure responses first (identity + architecture)
            if self.identity_handler:
                secure_response = self.identity_handler.generate_secure_response(
                    user_input
                )
                if secure_response:
                    self._add_to_history("agent", secure_response)
                    logger.info(f"Secure response generated: {secure_response[:50]}...")
                    return secure_response

            # Tạo phản hồi từ persona engine
            response = self.persona_engine.generate_response(
                user_input=user_input, history=self.history
            )

            # Validate response
            if not response.strip():
                logger.warning("Empty response from persona engine")
                response = self._get_fallback_response(user_input)

            # Thêm phản hồi vào lịch sử
            self._add_to_history("agent", response)
            logger.info(f"Generated response: {response[:50]}...")

            return response

        except Exception as e:
            logger.error(f"Error generating response: {e!s}")
            return self.get_random_delay_message()

    def _add_to_history(self, role: str, content: str):
        """Quản lý lịch sử hội thoại với giới hạn max_history"""
        self.history.append({"role": role, "content": content})

        # Giữ lại tối đa max_history cặp Q-A
        if len(self.history) > self.max_history * 2:
            self.history = self.history[-(self.max_history * 2) :]

    def _get_fallback_response(self, user_input: str) -> str:
        """Xử lý khi persona engine trả về rỗng"""
        fallbacks = [
            f"E chưa hiểu rõ ý '{user_input}' lắm, a giải thích thêm được không?",
            "E cần thêm thông tin để trả lời chính xác ạ",
            "Hiện e chưa có câu trả lời tốt nhất, a đợi e xíu nhé",
        ]
        return random.choice(fallbacks)

    def add_delay_message(self, msg: str) -> None:
        """Thêm câu che delay mới vào danh sách"""
        if msg and msg.strip() and msg not in self.delay_messages:
            self.delay_messages.append(msg.strip())
            logger.info(f"Added new delay message: {msg[:20]}...")

    def get_random_delay_message(self) -> str:
        """Lấy ngẫu nhiên một câu che delay"""
        return (
            random.choice(self.delay_messages)
            if self.delay_messages
            else "Vui lòng đợi..."
        )

    def reset_history(self) -> None:
        """Xóa toàn bộ lịch sử hội thoại"""
        self.history.clear()
        logger.info("Conversation history reset")

    def get_conversation_state(self) -> dict[str, int | list[dict]]:
        """Lấy trạng thái hiện tại của hội thoại"""
        return {
            "history_length": len(self.history),
            "recent_messages": self.history[-3:] if self.history else [],
        }
