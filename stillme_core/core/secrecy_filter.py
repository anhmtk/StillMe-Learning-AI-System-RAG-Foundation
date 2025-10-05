#!/usr/bin/env python3
"""
Secrecy Filter - Security filter for protecting internal information
Bộ lọc bảo mật để bảo vệ thông tin nội bộ

PURPOSE / MỤC ĐÍCH:
- Filter out internal architecture details
- Lọc bỏ chi tiết kiến trúc nội bộ
- Provide policy-compliant responses for sensitive queries
- Cung cấp phản hồi tuân thủ chính sách cho câu hỏi nhạy cảm
- Prevent information leakage
- Ngăn chặn rò rỉ thông tin

FUNCTIONALITY / CHỨC NĂNG:
- Keyword filtering
- Pattern matching
- Policy response generation
- Content sanitization
- Security logging
"""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for filtering / Mức độ bảo mật cho lọc"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FilterResult:
    """Result of secrecy filtering / Kết quả lọc bảo mật"""

    is_safe: bool
    filtered_content: str
    violations: list[str]
    security_level: SecurityLevel
    policy_response: str | None = None
    metadata: dict[str, Any] = None


class SecrecyFilter:
    """
    Security filter for protecting internal information
    Bộ lọc bảo mật để bảo vệ thông tin nội bộ
    """

    def __init__(self, security_level: SecurityLevel = SecurityLevel.HIGH):
        self.security_level = security_level
        self.logger = logging.getLogger(f"{__name__}.SecrecyFilter")

        # Initialize filter patterns
        self._init_internal_keywords()
        self._init_sensitive_patterns()
        self._init_policy_responses()

    def _init_internal_keywords(self):
        """Initialize internal architecture keywords / Khởi tạo từ khóa kiến trúc nội bộ"""
        self.internal_keywords = [
            # Framework internals / Nội bộ framework
            "agent_dev",
            "framework.py",
            "modules/",
            "stillme_core",
            "backup_legacy",
            "tests/fixtures",
            "node_modules",
            "__pycache__",
            "framework_memory.enc",
            "audit.log",
            "stillme.log",
            # Configuration files / File cấu hình
            "config/",
            "settings.py",
            "environment.py",
            ".env",
            "docker-compose",
            "Dockerfile",
            "requirements.txt",
            "pyproject.toml",
            "package.json",
            "package-lock.json",
            # Development tools / Công cụ phát triển
            "uvicorn --reload",
            "pytest",
            "pyright",
            "ruff",
            "black",
            "mypy",
            "pre-commit",
            "git hooks",
            # API keys and secrets / API keys và secrets
            "api_key",
            "secret_key",
            "private_key",
            "access_token",
            "refresh_token",
            "jwt_secret",
            "database_url",
            "openai_api_key",
            "openrouter_api_key",
            "google_api_key",
            # System internals / Nội bộ hệ thống
            "system_prompt",
            "internal_prompt",
            "debug_mode",
            "development_mode",
            "test_mode",
            "sandbox_mode",
            "internal_config",
            "system_config",
            "debug_config",
        ]

        # Critical keywords that should never appear / Từ khóa quan trọng không bao giờ xuất hiện
        self.critical_keywords = [
            "agent_dev",
            "framework.py",
            "internal_config",
            "system_prompt",
            "debug_mode",
            "api_key",
        ]

    def _init_sensitive_patterns(self):
        """Initialize sensitive content patterns / Khởi tạo mẫu nội dung nhạy cảm"""
        self.sensitive_patterns = [
            # File paths / Đường dẫn file
            r"[A-Za-z]:\\[^\\]+\\[^\\]+",  # Windows paths
            r"/[a-zA-Z0-9_/.-]+\.(py|js|ts|json|yaml|yml|env|log)",  # Unix paths
            # API endpoints / API endpoints
            r"https?://[^/]+/api/[^/\s]+",
            r"localhost:\d+",
            r"127\.0\.0\.1:\d+",
            # Configuration values / Giá trị cấu hình
            r'"[A-Za-z0-9_]+":\s*"[^"]{20,}"',  # Long config values
            r'API_KEY\s*=\s*"[^"]+"',
            r'SECRET\s*=\s*"[^"]+"',
            # Stack traces / Stack traces
            r"Traceback \(most recent call last\):",
            r'File "[^"]+", line \d+',
            r"Exception:",
            r"Error:",
            # Internal module references / Tham chiếu module nội bộ
            r"from\s+modules\.",
            r"import\s+modules\.",
            r"stillme_core\.",
            r"framework\.",
        ]

    def _init_policy_responses(self):
        """Initialize policy-compliant responses / Khởi tạo phản hồi tuân thủ chính sách"""
        self.policy_responses = {
            "architecture": {
                "vi": "Tôi là StillMe, một AI được tạo bởi Anh Nguyễn với sự hỗ trợ từ các tổ chức AI hàng đầu như OpenAI, Google, DeepSeek. Mục đích của tôi là đồng hành và kết bạn với mọi người. Tôi không thể chia sẻ chi tiết về kiến trúc nội bộ, nhưng tôi có thể giúp bạn với các câu hỏi khác!",
                "en": "I'm StillMe, an AI created by Anh Nguyễn with major support from leading AI organizations like OpenAI, Google, DeepSeek. My purpose is to accompany and befriend everyone. I cannot share internal architecture details, but I can help you with other questions!",
            },
            "development": {
                "vi": "Tôi không thể chia sẻ thông tin về quá trình phát triển nội bộ hoặc cấu trúc hệ thống. Tuy nhiên, tôi có thể giúp bạn với các câu hỏi về lập trình, công nghệ hoặc bất kỳ chủ đề nào khác!",
                "en": "I cannot share information about internal development processes or system architecture. However, I can help you with programming, technology, or any other topics!",
            },
            "technical": {
                "vi": "Tôi không thể tiết lộ chi tiết kỹ thuật nội bộ về cách tôi hoạt động. Nhưng tôi rất sẵn lòng giúp bạn với các vấn đề kỹ thuật khác mà bạn đang gặp phải!",
                "en": "I cannot reveal internal technical details about how I work. But I'm happy to help you with other technical issues you might be facing!",
            },
            "default": {
                "vi": "Tôi không thể chia sẻ thông tin nội bộ về hệ thống. Tuy nhiên, tôi có thể giúp bạn với nhiều chủ đề khác! Bạn có câu hỏi gì khác không?",
                "en": "I cannot share internal system information. However, I can help you with many other topics! Do you have any other questions?",
            },
        }

    def filter_content(
        self, content: str, query: str = "", locale: str = "vi"
    ) -> FilterResult:
        """
        Filter content for security violations
        Lọc nội dung để tìm vi phạm bảo mật

        Args:
            content: Content to filter / Nội dung cần lọc
            query: Original query / Câu hỏi gốc
            locale: Language locale / Ngôn ngữ

        Returns:
            FilterResult: Filtering result / Kết quả lọc
        """
        try:
            self.logger.debug(f"Filtering content of length {len(content)}")

            violations = []
            filtered_content = content
            security_level = SecurityLevel.LOW
            policy_response = None

            # Check for critical keywords
            critical_violations = self._check_critical_keywords(content)
            if critical_violations:
                violations.extend(critical_violations)
                security_level = SecurityLevel.CRITICAL
                policy_response = self._get_policy_response("architecture", locale)

            # Check for internal keywords
            internal_violations = self._check_internal_keywords(content)
            if internal_violations:
                violations.extend(internal_violations)
                if security_level == SecurityLevel.LOW:
                    security_level = SecurityLevel.HIGH

            # Check for sensitive patterns
            pattern_violations = self._check_sensitive_patterns(content)
            if pattern_violations:
                violations.extend(pattern_violations)
                if security_level == SecurityLevel.LOW:
                    security_level = SecurityLevel.MEDIUM

            # Check query for policy violations
            query_violations = self._check_query_policy(query)
            if query_violations:
                violations.extend(query_violations)
                if not policy_response:
                    policy_response = self._get_policy_response("default", locale)
                security_level = SecurityLevel.HIGH

            # Apply filtering based on security level
            if security_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]:
                filtered_content = self._apply_filtering(content, violations)

            # Determine if content is safe
            is_safe = security_level not in [SecurityLevel.CRITICAL]

            # Prepare metadata
            metadata = {
                "original_length": len(content),
                "filtered_length": len(filtered_content),
                "violation_count": len(violations),
                "security_level": security_level.value,
                "has_policy_response": policy_response is not None,
            }

            result = FilterResult(
                is_safe=is_safe,
                filtered_content=filtered_content,
                violations=violations,
                security_level=security_level,
                policy_response=policy_response,
                metadata=metadata,
            )

            self.logger.debug(
                f"Filtering completed. Security level: {security_level.value}, Violations: {len(violations)}"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error in content filtering: {e}")
            # Return safe result on error
            return FilterResult(
                is_safe=False,
                filtered_content="",
                violations=[f"Filtering error: {e!s}"],
                security_level=SecurityLevel.CRITICAL,
                policy_response=self._get_policy_response("default", locale),
                metadata={"error": str(e)},
            )

    def _check_critical_keywords(self, content: str) -> list[str]:
        """Check for critical security violations / Kiểm tra vi phạm bảo mật quan trọng"""
        violations = []
        content_lower = content.lower()

        for keyword in self.critical_keywords:
            if keyword.lower() in content_lower:
                violations.append(f"Critical violation: '{keyword}' detected")

        return violations

    def _check_internal_keywords(self, content: str) -> list[str]:
        """Check for internal architecture keywords / Kiểm tra từ khóa kiến trúc nội bộ"""
        violations = []
        content_lower = content.lower()

        for keyword in self.internal_keywords:
            if keyword.lower() in content_lower:
                violations.append(f"Internal keyword: '{keyword}' detected")

        return violations

    def _check_sensitive_patterns(self, content: str) -> list[str]:
        """Check for sensitive content patterns / Kiểm tra mẫu nội dung nhạy cảm"""
        violations = []

        for pattern in self.sensitive_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                violations.append(f"Sensitive pattern detected: {pattern}")

        return violations

    def _check_query_policy(self, query: str) -> list[str]:
        """Check query for policy violations / Kiểm tra câu hỏi về vi phạm chính sách"""
        violations = []
        query_lower = query.lower()

        # Policy violation patterns
        policy_patterns = [
            r"how does stillme work",
            r"stillme architecture",
            r"stillme internals",
            r"stillme code",
            r"stillme modules",
            r"stillme framework",
            r"agent development",
            r"agent dev",
            r"framework details",
            r"system prompt",
            r"internal prompt",
            r"debug mode",
            r"development mode",
        ]

        for pattern in policy_patterns:
            if re.search(pattern, query_lower):
                violations.append(f"Policy violation: query about '{pattern}'")

        return violations

    def _apply_filtering(self, content: str, violations: list[str]) -> str:
        """Apply content filtering based on violations / Áp dụng lọc nội dung dựa trên vi phạm"""
        filtered_content = content

        # Remove critical keywords
        for keyword in self.critical_keywords:
            filtered_content = re.sub(
                re.escape(keyword), "[REDACTED]", filtered_content, flags=re.IGNORECASE
            )

        # Remove internal keywords
        for keyword in self.internal_keywords:
            filtered_content = re.sub(
                re.escape(keyword), "[FILTERED]", filtered_content, flags=re.IGNORECASE
            )

        # Remove sensitive patterns
        for pattern in self.sensitive_patterns:
            filtered_content = re.sub(
                pattern, "[SENSITIVE_CONTENT]", filtered_content, flags=re.IGNORECASE
            )

        return filtered_content

    def _get_policy_response(self, response_type: str, locale: str) -> str:
        """Get policy-compliant response / Lấy phản hồi tuân thủ chính sách"""
        try:
            response = self.policy_responses.get(
                response_type, self.policy_responses["default"]
            )
            return response.get(locale, response.get("en", response.get("vi", "")))
        except Exception as e:
            self.logger.warning(f"Error getting policy response: {e}")
            return self.policy_responses["default"].get(
                locale, "I cannot share internal information."
            )

    def should_use_policy_response(self, query: str) -> tuple[bool, str]:
        """
        Check if query should get policy response
        Kiểm tra xem câu hỏi có nên nhận phản hồi chính sách không

        Args:
            query: The query to check / Câu hỏi cần kiểm tra

        Returns:
            Tuple[bool, str]: (should_use_policy, response_type)
        """
        query_lower = query.lower()

        # Architecture questions
        if any(
            keyword in query_lower
            for keyword in [
                "architecture",
                "kiến trúc",
                "how does stillme work",
                "stillme internals",
                "framework",
                "modules",
            ]
        ):
            return True, "architecture"

        # Development questions
        if any(
            keyword in query_lower
            for keyword in [
                "development",
                "phát triển",
                "code",
                "source code",
                "agent dev",
                "framework.py",
                "internal",
            ]
        ):
            return True, "development"

        # Technical questions
        if any(
            keyword in query_lower
            for keyword in [
                "technical",
                "kỹ thuật",
                "system prompt",
                "debug",
                "configuration",
                "cấu hình",
                "api key",
            ]
        ):
            return True, "technical"

        return False, "default"

    def log_security_event(self, event_type: str, details: dict[str, Any]):
        """Log security event / Ghi log sự kiện bảo mật"""
        try:
            self.logger.warning(f"Security event: {event_type} - {details}")
        except Exception as e:
            self.logger.error(f"Error logging security event: {e}")


# Utility functions / Hàm tiện ích


def create_filter(security_level: str = "high") -> SecrecyFilter:
    """Create secrecy filter with specified security level / Tạo bộ lọc bảo mật với mức độ bảo mật chỉ định"""
    level = SecurityLevel(security_level.lower())
    return SecrecyFilter(level)


def get_default_filter() -> SecrecyFilter:
    """Get default secrecy filter / Lấy bộ lọc bảo mật mặc định"""
    return SecrecyFilter()


# Example usage / Ví dụ sử dụng
if __name__ == "__main__":
    # Test the filter
    filter_instance = get_default_filter()

    test_content = """
    This is a test response that contains some internal details:
    - framework.py is the main file
    - agent_dev handles the development
    - API_KEY is stored in config
    """

    test_query = "How does StillMe work internally?"

    result = filter_instance.filter_content(test_content, test_query)
    print(f"Is safe: {result.is_safe}")
    print(f"Security level: {result.security_level.value}")
    print(f"Violations: {result.violations}")
    if result.policy_response:
        print(f"Policy response: {result.policy_response}")
    print(f"Filtered content: {result.filtered_content}")
