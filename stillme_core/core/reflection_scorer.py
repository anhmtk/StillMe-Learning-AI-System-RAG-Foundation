#!/usr/bin/env python3
"""
Reflection Scorer - Heuristic scoring system for response quality
Hệ thống chấm điểm heuristic cho chất lượng phản hồi

PURPOSE / MỤC ĐÍCH:
- Evaluate response quality across multiple dimensions
- Đánh giá chất lượng phản hồi theo nhiều chiều
- Provide actionable feedback for improvement
- Cung cấp phản hồi có thể hành động để cải thiện
- Support multi-objective optimization
- Hỗ trợ tối ưu đa mục tiêu

FUNCTIONALITY / CHỨC NĂNG:
- Relevance scoring (TF-IDF/embedding based)
- Correctness assessment
- Safety/policy compliance checking
- Clarity and readability evaluation
- Brevity optimization
- Helpfulness measurement
"""

import logging
import re
from collections import Counter
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ScoringWeights:
    """Weights for different scoring dimensions / Trọng số cho các chiều chấm điểm"""

    relevance: float = 0.45
    safety: float = 0.20
    clarity: float = 0.15
    brevity: float = 0.10
    helpfulness: float = 0.10


@dataclass
class ScoringResult:
    """Result of response scoring / Kết quả chấm điểm phản hồi"""

    total_score: float
    relevance_score: float
    safety_score: float
    clarity_score: float
    brevity_score: float
    helpfulness_score: float
    penalties: list[str]
    suggestions: list[str]
    metadata: dict[str, Any]


class ReflectionScorer:
    """
    Heuristic scorer for response quality evaluation
    Bộ chấm điểm heuristic cho đánh giá chất lượng phản hồi
    """

    def __init__(self, weights: ScoringWeights | None = None):
        self.weights = weights or ScoringWeights()
        self.logger = logging.getLogger(f"{__name__}.ReflectionScorer")

        # Initialize scoring components
        self._init_safety_keywords()
        self._init_helpfulness_patterns()
        self._init_clarity_patterns()

    def _init_safety_keywords(self):
        """Initialize safety-related keywords / Khởi tạo từ khóa liên quan an toàn"""
        self.safety_violations = [
            # Internal architecture keywords / Từ khóa kiến trúc nội bộ
            "agent_dev",
            "framework.py",
            "modules/",
            "internal_config",
            "stacktrace",
            "keys",
            "secrets",
            "docker-compose",
            "uvicorn --reload",
            "stillme_core",
            "backup_legacy",
            "tests/fixtures",
            "node_modules",
            "__pycache__",
            "framework_memory.enc",
            "audit.log",
            # Sensitive technical details / Chi tiết kỹ thuật nhạy cảm
            "api_key",
            "database_url",
            "secret_key",
            "private_key",
            "access_token",
            "refresh_token",
            "jwt_secret",
            # System internals / Nội bộ hệ thống
            "system_prompt",
            "internal_prompt",
            "debug_mode",
            "development_mode",
            "test_mode",
            "sandbox_mode",
        ]

        self.policy_violations = [
            # Questions about internal architecture / Câu hỏi về kiến trúc nội bộ
            "how does stillme work",
            "stillme architecture",
            "stillme internals",
            "stillme code",
            "stillme modules",
            "stillme framework",
            "agent development",
            "agent dev",
            "framework details",
        ]

    def _init_helpfulness_patterns(self):
        """Initialize patterns for helpfulness detection / Khởi tạo mẫu phát hiện tính hữu ích"""
        self.helpful_patterns = [
            # Action items / Mục hành động
            r"\d+\.\s+[A-Z]",  # Numbered lists
            r"•\s+[A-Z]",  # Bullet points
            r"-\s+[A-Z]",  # Dash lists
            # Step-by-step instructions / Hướng dẫn từng bước
            r"step\s+\d+",
            r"bước\s+\d+",
            r"first",
            r"second",
            r"third",
            r"đầu tiên",
            r"thứ hai",
            r"thứ ba",
            r"cuối cùng",
            # Examples / Ví dụ
            r"for example",
            r"ví dụ",
            r"example:",
            r"ví dụ:",
            r"here is",
            r"đây là",
            r"như sau",
            # Commands / Lệnh
            r"run\s+",
            r"execute\s+",
            r"chạy\s+",
            r"thực thi\s+",
            r"install\s+",
            r"cài đặt\s+",
            r"configure\s+",
            r"cấu hình\s+",
            # Code blocks / Khối code
            r"```",
            r"`[^`]+`",
            # Links and references / Liên kết và tham chiếu
            r"https?://",
            r"www\.",
            r"\.com",
            r"\.org",
            r"\.net",
        ]

    def _init_clarity_patterns(self):
        """Initialize patterns for clarity assessment / Khởi tạo mẫu đánh giá độ rõ ràng"""
        self.clarity_indicators = [
            # Good structure / Cấu trúc tốt
            r"^#{1,6}\s+",  # Headers
            r"^\*\*.*\*\*$",  # Bold text
            r"^\*.*\*$",  # Italic text
            # Lists / Danh sách
            r"^\d+\.\s+",  # Numbered lists
            r"^[-*•]\s+",  # Bullet lists
            # Code formatting / Định dạng code
            r"```[\s\S]*?```",  # Code blocks
            r"`[^`]+`",  # Inline code
        ]

        self.clarity_penalties = [
            # Poor structure / Cấu trúc kém
            r"\n{3,}",  # Too many newlines
            r" {4,}",  # Too many spaces
            r"[.!?]{2,}",  # Multiple punctuation
            r"[A-Z]{5,}",  # All caps words
        ]

    def score_response(
        self, response: str, query: str, context: dict[str, Any] | None = None
    ) -> ScoringResult:
        """
        Score a response across multiple dimensions
        Chấm điểm phản hồi theo nhiều chiều

        Args:
            response: The response to score / Phản hồi cần chấm điểm
            query: The original query / Câu hỏi gốc
            context: Additional context / Ngữ cảnh bổ sung

        Returns:
            ScoringResult: Comprehensive scoring result / Kết quả chấm điểm toàn diện
        """
        try:
            self.logger.debug(
                f"Scoring response of length {len(response)} for query: {query[:50]}..."
            )

            # Calculate individual scores
            relevance_score = self._score_relevance(response, query)
            safety_score = self._score_safety(response, query)
            clarity_score = self._score_clarity(response)
            brevity_score = self._score_brevity(response, query)
            helpfulness_score = self._score_helpfulness(response)

            # Calculate total score with weights
            total_score = (
                relevance_score * self.weights.relevance
                + safety_score * self.weights.safety
                + clarity_score * self.weights.clarity
                + brevity_score * self.weights.brevity
                + helpfulness_score * self.weights.helpfulness
            )

            # Generate suggestions
            suggestions = self._generate_suggestions(
                relevance_score,
                safety_score,
                clarity_score,
                brevity_score,
                helpfulness_score,
                response,
                query,
            )

            # Collect penalties
            penalties = self._collect_penalties(response, query)

            # Prepare metadata
            metadata = {
                "response_length": len(response),
                "query_length": len(query),
                "word_count": len(response.split()),
                "sentence_count": len(re.findall(r"[.!?]+", response)),
                "has_code": bool(re.search(r"```|`[^`]+`", response)),
                "has_lists": bool(re.search(r"^\d+\.|^[-*•]", response, re.MULTILINE)),
                "has_headers": bool(re.search(r"^#{1,6}\s+", response, re.MULTILINE)),
            }

            result = ScoringResult(
                total_score=total_score,
                relevance_score=relevance_score,
                safety_score=safety_score,
                clarity_score=clarity_score,
                brevity_score=brevity_score,
                helpfulness_score=helpfulness_score,
                penalties=penalties,
                suggestions=suggestions,
                metadata=metadata,
            )

            self.logger.debug(f"Scoring completed. Total score: {total_score:.3f}")
            return result

        except Exception as e:
            self.logger.error(f"Error scoring response: {e}")
            # Return minimal score on error
            return ScoringResult(
                total_score=0.5,
                relevance_score=0.5,
                safety_score=0.5,
                clarity_score=0.5,
                brevity_score=0.5,
                helpfulness_score=0.5,
                penalties=[f"Scoring error: {e!s}"],
                suggestions=["Fix scoring error"],
                metadata={"error": str(e)},
            )

    def _score_relevance(self, response: str, query: str) -> float:
        """Score relevance using TF-IDF-like approach / Chấm điểm độ liên quan bằng cách tiếp cận TF-IDF"""
        try:
            # Simple word overlap scoring
            query_words = set(re.findall(r"\b\w+\b", query.lower()))
            response_words = set(re.findall(r"\b\w+\b", response.lower()))

            if not query_words:
                return 0.5

            # Calculate overlap
            overlap = len(query_words.intersection(response_words))
            relevance = overlap / len(query_words)

            # Boost for addressing sub-questions
            sub_question_indicators = [
                r"câu hỏi",
                r"question",
                r"vấn đề",
                r"issue",
                r"về",
                r"about",
                r"liên quan",
                r"related",
            ]

            sub_question_boost = sum(
                1
                for pattern in sub_question_indicators
                if re.search(pattern, response.lower())
            )

            relevance = min(1.0, relevance + (sub_question_boost * 0.1))

            return relevance

        except Exception as e:
            self.logger.warning(f"Error in relevance scoring: {e}")
            return 0.5

    def _score_safety(self, response: str, query: str) -> float:
        """Score safety and policy compliance / Chấm điểm an toàn và tuân thủ chính sách"""
        try:
            response_lower = response.lower()
            query_lower = query.lower()

            # Check for internal architecture leaks
            architecture_leaks = sum(
                1
                for keyword in self.safety_violations
                if keyword.lower() in response_lower
            )

            # Check for policy violations
            policy_violations = sum(
                1
                for pattern in self.policy_violations
                if pattern.lower() in query_lower
            )

            # Calculate safety score
            if architecture_leaks > 0:
                safety_score = 0.0  # Critical violation
            elif policy_violations > 0:
                safety_score = 0.3  # Policy violation
            else:
                safety_score = 1.0  # Safe

            return safety_score

        except Exception as e:
            self.logger.warning(f"Error in safety scoring: {e}")
            return 0.5

    def _score_clarity(self, response: str) -> float:
        """Score clarity and readability / Chấm điểm độ rõ ràng và khả năng đọc"""
        try:
            clarity_score = 0.5  # Base score

            # Check for good structure indicators
            structure_bonus = 0
            for pattern in self.clarity_indicators:
                matches = len(re.findall(pattern, response, re.MULTILINE))
                structure_bonus += matches * 0.05

            # Check for clarity penalties
            penalty = 0
            for pattern in self.clarity_penalties:
                matches = len(re.findall(pattern, response))
                penalty += matches * 0.1

            # Check sentence length (prefer shorter sentences)
            sentences = re.split(r"[.!?]+", response)
            avg_sentence_length = sum(len(s.split()) for s in sentences) / max(
                len(sentences), 1
            )

            if avg_sentence_length > 20:
                penalty += 0.2
            elif avg_sentence_length < 10:
                structure_bonus += 0.1

            # Check for repetition
            words = response.lower().split()
            word_counts = Counter(words)
            repetition_penalty = (
                sum(1 for count in word_counts.values() if count > 3) * 0.05
            )

            clarity_score = min(
                1.0, clarity_score + structure_bonus - penalty - repetition_penalty
            )

            return max(0.0, clarity_score)

        except Exception as e:
            self.logger.warning(f"Error in clarity scoring: {e}")
            return 0.5

    def _score_brevity(self, response: str, query: str) -> float:
        """Score brevity and efficiency / Chấm điểm tính ngắn gọn và hiệu quả"""
        try:
            response_length = len(response)
            query_length = len(query)

            # Ideal response length based on query complexity
            if query_length < 50:
                ideal_length = 200
            elif query_length < 150:
                ideal_length = 400
            else:
                ideal_length = 600

            # Calculate brevity score
            if response_length <= ideal_length:
                brevity_score = 1.0
            elif response_length <= ideal_length * 1.5:
                brevity_score = 0.8
            elif response_length <= ideal_length * 2:
                brevity_score = 0.6
            else:
                brevity_score = 0.4

            # Penalty for excessive length
            if response_length > ideal_length * 3:
                brevity_score = 0.2

            return brevity_score

        except Exception as e:
            self.logger.warning(f"Error in brevity scoring: {e}")
            return 0.5

    def _score_helpfulness(self, response: str) -> float:
        """Score helpfulness and actionability / Chấm điểm tính hữu ích và khả năng hành động"""
        try:
            helpfulness_score = 0.5  # Base score

            # Check for helpful patterns
            pattern_bonus = 0
            for pattern in self.helpful_patterns:
                matches = len(re.findall(pattern, response, re.IGNORECASE))
                pattern_bonus += matches * 0.1

            # Check for actionable content
            action_indicators = [
                r"cách",
                r"how to",
                r"hướng dẫn",
                r"guide",
                r"bước",
                r"step",
                r"quy trình",
                r"process",
                r"kiểm tra",
                r"check",
                r"verify",
                r"confirm",
                r"cài đặt",
                r"install",
                r"setup",
                r"configure",
            ]

            action_bonus = sum(
                1
                for pattern in action_indicators
                if re.search(pattern, response.lower())
            )

            helpfulness_score = min(
                1.0, helpfulness_score + pattern_bonus + (action_bonus * 0.05)
            )

            return helpfulness_score

        except Exception as e:
            self.logger.warning(f"Error in helpfulness scoring: {e}")
            return 0.5

    def _generate_suggestions(
        self,
        relevance: float,
        safety: float,
        clarity: float,
        brevity: float,
        helpfulness: float,
        response: str,
        query: str,
    ) -> list[str]:
        """Generate improvement suggestions / Tạo gợi ý cải thiện"""
        suggestions = []

        if relevance < 0.7:
            suggestions.append("Tăng độ liên quan bằng cách trả lời trực tiếp câu hỏi")

        if safety < 1.0:
            suggestions.append("Loại bỏ thông tin nội bộ và chi tiết kỹ thuật nhạy cảm")

        if clarity < 0.7:
            suggestions.append(
                "Cải thiện cấu trúc với headers, lists và định dạng rõ ràng"
            )

        if brevity < 0.7:
            suggestions.append("Rút gọn nội dung, tập trung vào thông tin quan trọng")

        if helpfulness < 0.7:
            suggestions.append(
                "Thêm ví dụ cụ thể, hướng dẫn từng bước hoặc lệnh thực thi"
            )

        return suggestions

    def _collect_penalties(self, response: str, query: str) -> list[str]:
        """Collect penalties for the response / Thu thập các phạt cho phản hồi"""
        penalties = []

        # Check for safety violations
        response_lower = response.lower()
        for keyword in self.safety_violations:
            if keyword.lower() in response_lower:
                penalties.append(f"Safety violation: contains '{keyword}'")

        # Check for excessive length
        if len(response) > 2000:
            penalties.append("Excessive length penalty")

        # Check for poor structure
        if not re.search(r"^#{1,6}\s+|^\d+\.|^[-*•]", response, re.MULTILINE):
            if len(response) > 500:
                penalties.append("Poor structure penalty")

        return penalties


# Utility functions / Hàm tiện ích


def create_scorer_with_weights(weights_dict: dict[str, float]) -> ReflectionScorer:
    """Create scorer with custom weights / Tạo scorer với trọng số tùy chỉnh"""
    weights = ScoringWeights(**weights_dict)
    return ReflectionScorer(weights)


def get_default_scorer() -> ReflectionScorer:
    """Get default scorer instance / Lấy instance scorer mặc định"""
    return ReflectionScorer()


# Example usage / Ví dụ sử dụng
if __name__ == "__main__":
    # Test the scorer
    scorer = get_default_scorer()

    test_response = """
    # Hướng dẫn cài đặt Python

    Để cài đặt Python, bạn có thể làm theo các bước sau:

    1. Truy cập python.org
    2. Tải xuống phiên bản mới nhất
    3. Chạy installer

    Ví dụ:
    ```bash
    python --version
    ```
    """

    test_query = "Cách cài đặt Python?"

    result = scorer.score_response(test_response, test_query)
    print(f"Total score: {result.total_score:.3f}")
    print(f"Suggestions: {result.suggestions}")
