#!/usr/bin/env python3
"""
Reflection Controller - Bounded reflection system for response enhancement
Bộ điều khiển phản tư có giới hạn để nâng cao phản hồi

PURPOSE / MỤC ĐÍCH:
- Implement bounded reflection algorithm
- Triển khai thuật toán phản tư có giới hạn
- Optimize responses across multiple objectives
- Tối ưu phản hồi theo nhiều mục tiêu
- Prevent infinite reflection loops
- Ngăn chặn vòng lặp phản tư vô hạn
- Integrate with existing response pipeline
- Tích hợp với pipeline phản hồi hiện có

FUNCTIONALITY / CHỨC NĂNG:
- Multi-objective optimization
- Budget management (tokens, time, steps)
- Early stopping mechanisms
- Context-aware reflection
- Security filtering
- Performance monitoring
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .reflection_scorer import ReflectionScorer, ScoringResult, ScoringWeights
from .secrecy_filter import SecrecyFilter

logger = logging.getLogger(__name__)


class ReflectionMode(Enum):
    """Reflection modes / Chế độ phản tư"""

    FAST = "fast"
    NORMAL = "normal"
    DEEP = "deep"


@dataclass
class ReflectionConfig:
    """Configuration for reflection controller / Cấu hình cho bộ điều khiển phản tư"""

    max_steps: int = 3
    max_latency_s: float = 15.0
    max_tokens: int = 1400
    improvement_epsilon: float = 0.02
    tool_cap: int = 2
    mode: ReflectionMode = ReflectionMode.NORMAL
    weights: ScoringWeights = field(default_factory=ScoringWeights)


@dataclass
class ReflectionContext:
    """Context for reflection process / Ngữ cảnh cho quá trình phản tư"""

    query: str
    intent: str = "general"
    persona: str = "friendly"
    locale: str = "vi"
    user_preferences: dict[str, Any] = field(default_factory=dict)
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReflectionResult:
    """Result of reflection process / Kết quả quá trình phản tư"""

    final_response: str
    original_score: float
    final_score: float
    improvement: float
    steps_taken: int
    time_taken: float
    stop_reason: str
    trace: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ReflectionController:
    """
    Main reflection controller with bounded reflection algorithm
    Bộ điều khiển phản tư chính với thuật toán phản tư có giới hạn
    """

    def __init__(self, config: ReflectionConfig | None = None):
        self.config = config or ReflectionConfig()
        self.logger = logging.getLogger(f"{__name__}.ReflectionController")

        # Initialize components
        self.scorer = ReflectionScorer(self.config.weights)
        self.secrecy_filter = SecrecyFilter()

        # Performance tracking
        self._performance_stats = {
            "total_reflections": 0,
            "successful_reflections": 0,
            "average_improvement": 0.0,
            "average_time": 0.0,
        }

        # Load configuration from file if available
        self._load_config()

    def _load_config(self):
        """Load configuration from file / Tải cấu hình từ file"""
        try:
            config_path = Path("config/reflection.yaml")
            if config_path.exists():
                import yaml

                with open(config_path, encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)

                # Update configuration
                if "modes" in config_data:
                    mode_config = config_data["modes"].get(self.config.mode.value, {})
                    self.config.max_steps = mode_config.get(
                        "max_steps", self.config.max_steps
                    )
                    self.config.max_latency_s = mode_config.get(
                        "max_latency_s", self.config.max_latency_s
                    )
                    self.config.max_tokens = mode_config.get(
                        "tokens", self.config.max_tokens
                    )

                if "weights" in config_data:
                    weights_data = config_data["weights"]
                    self.config.weights = ScoringWeights(**weights_data)

                if "epsilon" in config_data:
                    self.config.improvement_epsilon = config_data["epsilon"]

                if "tool_cap" in config_data:
                    self.config.tool_cap = config_data["tool_cap"]

                self.logger.info(f"Configuration loaded from {config_path}")

        except Exception as e:
            self.logger.warning(f"Could not load configuration: {e}")

    def should_reflect(
        self, query: str, context: ReflectionContext | None = None
    ) -> bool:
        """
        Determine if reflection should be applied
        Xác định xem có nên áp dụng phản tư không

        Args:
            query: The user query / Câu hỏi người dùng
            context: Reflection context / Ngữ cảnh phản tư

        Returns:
            bool: Whether to apply reflection / Có nên áp dụng phản tư không
        """
        try:
            # Check for policy violations first
            should_use_policy, _ = self.secrecy_filter.should_use_policy_response(query)
            if should_use_policy:
                return False  # Use policy response instead

            # Check query characteristics
            query_lower = query.lower()

            # Skip reflection for simple queries
            if len(query) < 20:
                return False

            # Skip reflection for greetings
            greeting_patterns = [
                "hello",
                "hi",
                "hey",
                "xin chào",
                "chào",
                "chào bạn",
                "good morning",
                "good afternoon",
                "good evening",
            ]
            if any(pattern in query_lower for pattern in greeting_patterns):
                return False

            # Apply reflection for complex queries
            complex_indicators = [
                "how to",
                "cách",
                "hướng dẫn",
                "explain",
                "giải thích",
                "help",
                "giúp",
                "problem",
                "vấn đề",
                "error",
                "lỗi",
                "fix",
                "sửa",
                "debug",
                "troubleshoot",
                "khắc phục",
            ]

            if any(indicator in query_lower for indicator in complex_indicators):
                return True

            # Apply reflection for coding questions
            coding_keywords = [
                "code",
                "programming",
                "lập trình",
                "function",
                "hàm",
                "class",
                "lớp",
                "method",
                "phương thức",
                "algorithm",
                "thuật toán",
            ]

            if any(keyword in query_lower for keyword in coding_keywords):
                return True

            # Apply reflection for long queries
            if len(query) > 100:
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error in should_reflect: {e}")
            return False

    async def enhance_response(
        self,
        response: str,
        query: str,
        context: ReflectionContext | None = None,
        mode: ReflectionMode | None = None,
    ) -> ReflectionResult:
        """
        Enhance response through bounded reflection
        Nâng cao phản hồi thông qua phản tư có giới hạn

        Args:
            response: Original response / Phản hồi gốc
            query: User query / Câu hỏi người dùng
            context: Reflection context / Ngữ cảnh phản tư
            mode: Reflection mode / Chế độ phản tư

        Returns:
            ReflectionResult: Enhanced response result / Kết quả phản hồi được nâng cao
        """
        start_time = time.time()

        try:
            self.logger.info(f"Starting reflection for query: {query[:50]}...")

            # Update configuration based on mode
            if mode:
                self._update_config_for_mode(mode)

            # Initialize context
            if not context:
                context = ReflectionContext(query=query)

            # Check if we should use policy response
            should_use_policy, response_type = (
                self.secrecy_filter.should_use_policy_response(query)
            )
            if should_use_policy:
                policy_response = self.secrecy_filter._get_policy_response(
                    response_type, context.locale
                )
                return ReflectionResult(
                    final_response=policy_response,
                    original_score=0.0,
                    final_score=1.0,
                    improvement=1.0,
                    steps_taken=0,
                    time_taken=time.time() - start_time,
                    stop_reason="policy_response",
                    metadata={"policy_type": response_type},
                )

            # Initialize reflection process
            current_response = response
            best_response = response
            best_score = 0.0
            steps_taken = 0
            trace = []

            # Score original response
            original_score_result = self.scorer.score_response(
                current_response, query, context.__dict__
            )
            best_score = original_score_result.total_score

            self.logger.debug(f"Original score: {best_score:.3f}")

            # Reflection loop
            for step in range(self.config.max_steps):
                step_start_time = time.time()

                # Check timeout
                if time.time() - start_time > self.config.max_latency_s:
                    self.logger.warning("Reflection timeout reached")
                    break

                # Generate improvement suggestion
                improvement_suggestion = await self._generate_improvement_suggestion(
                    current_response, query, context, original_score_result
                )

                if not improvement_suggestion:
                    self.logger.debug("No improvement suggestion generated")
                    break

                # Apply improvement
                improved_response = await self._apply_improvement(
                    current_response, improvement_suggestion, context
                )

                # Score improved response
                improved_score_result = self.scorer.score_response(
                    improved_response, query, context.__dict__
                )
                improved_score = improved_score_result.total_score

                # Check if improvement is significant
                improvement_delta = improved_score - best_score

                self.logger.debug(
                    f"Step {step + 1}: Score {improved_score:.3f} (Δ{improvement_delta:+.3f})"
                )

                # Record step in trace
                trace.append(
                    {
                        "step": step + 1,
                        "suggestion": improvement_suggestion,
                        "score": improved_score,
                        "improvement": improvement_delta,
                        "time": time.time() - step_start_time,
                    }
                )

                # Accept improvement if significant
                if improvement_delta >= self.config.improvement_epsilon:
                    current_response = improved_response
                    best_response = improved_response
                    best_score = improved_score
                    steps_taken = step + 1

                    self.logger.debug(f"Improvement accepted: {improvement_delta:.3f}")
                else:
                    self.logger.debug(f"Improvement too small: {improvement_delta:.3f}")
                    break

            # Apply final security filtering
            filter_result = self.secrecy_filter.filter_content(
                best_response, query, context.locale
            )
            final_response = filter_result.filtered_content

            # Calculate final metrics
            time_taken = time.time() - start_time
            improvement = best_score - original_score_result.total_score
            stop_reason = self._determine_stop_reason(
                steps_taken, improvement, time_taken
            )

            # Update performance stats
            self._update_performance_stats(improvement, time_taken)

            result = ReflectionResult(
                final_response=final_response,
                original_score=original_score_result.total_score,
                final_score=best_score,
                improvement=improvement,
                steps_taken=steps_taken,
                time_taken=time_taken,
                stop_reason=stop_reason,
                trace=trace,
                metadata={
                    "config_used": {
                        "mode": self.config.mode.value,
                        "max_steps": self.config.max_steps,
                        "max_latency_s": self.config.max_latency_s,
                        "epsilon": self.config.improvement_epsilon,
                    },
                    "filter_violations": filter_result.violations,
                    "security_level": filter_result.security_level.value,
                },
            )

            self.logger.info(
                f"Reflection completed: {steps_taken} steps, {improvement:+.3f} improvement, {time_taken:.2f}s"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error in reflection process: {e}")
            # Return original response on error
            return ReflectionResult(
                final_response=response,
                original_score=0.5,
                final_score=0.5,
                improvement=0.0,
                steps_taken=0,
                time_taken=time.time() - start_time,
                stop_reason="error",
                metadata={"error": str(e)},
            )

    def _update_config_for_mode(self, mode: ReflectionMode):
        """Update configuration based on mode / Cập nhật cấu hình dựa trên chế độ"""
        mode_configs = {
            ReflectionMode.FAST: {
                "max_steps": 2,
                "max_latency_s": 8.0,
                "max_tokens": 900,
                "improvement_epsilon": 0.03,
            },
            ReflectionMode.NORMAL: {
                "max_steps": 3,
                "max_latency_s": 15.0,
                "max_tokens": 1400,
                "improvement_epsilon": 0.02,
            },
            ReflectionMode.DEEP: {
                "max_steps": 4,
                "max_latency_s": 30.0,
                "max_tokens": 2200,
                "improvement_epsilon": 0.015,
            },
        }

        config_updates = mode_configs.get(mode, {})
        for key, value in config_updates.items():
            setattr(self.config, key, value)

        self.config.mode = mode

    async def _generate_improvement_suggestion(
        self,
        response: str,
        query: str,
        context: ReflectionContext,
        score_result: ScoringResult,
    ) -> str | None:
        """Generate improvement suggestion / Tạo gợi ý cải thiện"""
        try:
            # Analyze score result to identify areas for improvement
            suggestions = []

            if score_result.relevance_score < 0.7:
                suggestions.append(
                    "Tăng độ liên quan bằng cách trả lời trực tiếp câu hỏi"
                )

            if score_result.clarity_score < 0.7:
                suggestions.append(
                    "Cải thiện cấu trúc với headers, lists và định dạng rõ ràng"
                )

            if score_result.brevity_score < 0.7:
                suggestions.append(
                    "Rút gọn nội dung, tập trung vào thông tin quan trọng"
                )

            if score_result.helpfulness_score < 0.7:
                suggestions.append(
                    "Thêm ví dụ cụ thể, hướng dẫn từng bước hoặc lệnh thực thi"
                )

            # Return the most impactful suggestion
            if suggestions:
                return suggestions[0]  # Take the first suggestion for now

            return None

        except Exception as e:
            self.logger.error(f"Error generating improvement suggestion: {e}")
            return None

    async def _apply_improvement(
        self, response: str, suggestion: str, context: ReflectionContext
    ) -> str:
        """Apply improvement suggestion / Áp dụng gợi ý cải thiện"""
        try:
            # This is a simplified improvement application
            # In a real implementation, this would use AI to improve the response

            if "Tăng độ liên quan" in suggestion:
                # Add more direct answer
                return f"{response}\n\n**Tóm tắt:** {suggestion}"

            elif "Cải thiện cấu trúc" in suggestion:
                # Add structure
                if not response.startswith("#"):
                    return f"# Trả lời\n\n{response}"
                return response

            elif "Rút gọn nội dung" in suggestion:
                # Simplify response
                sentences = response.split(". ")
                if len(sentences) > 3:
                    return ". ".join(sentences[:3]) + "."
                return response

            elif "Thêm ví dụ" in suggestion:
                # Add example
                return f"{response}\n\n**Ví dụ:** Đây là một ví dụ cụ thể để minh họa."

            return response

        except Exception as e:
            self.logger.error(f"Error applying improvement: {e}")
            return response

    def _determine_stop_reason(
        self, steps_taken: int, improvement: float, time_taken: float
    ) -> str:
        """Determine why reflection stopped / Xác định lý do dừng phản tư"""
        if steps_taken >= self.config.max_steps:
            return "max_steps_reached"
        elif time_taken >= self.config.max_latency_s:
            return "timeout"
        elif improvement < self.config.improvement_epsilon:
            return "insufficient_improvement"
        else:
            return "completed"

    def _update_performance_stats(self, improvement: float, time_taken: float):
        """Update performance statistics / Cập nhật thống kê hiệu suất"""
        self._performance_stats["total_reflections"] += 1
        if improvement > 0:
            self._performance_stats["successful_reflections"] += 1

        # Update averages
        total = self._performance_stats["total_reflections"]
        self._performance_stats["average_improvement"] = (
            self._performance_stats["average_improvement"] * (total - 1) + improvement
        ) / total
        self._performance_stats["average_time"] = (
            self._performance_stats["average_time"] * (total - 1) + time_taken
        ) / total

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics / Lấy thống kê hiệu suất"""
        return self._performance_stats.copy()

    def reset_performance_stats(self):
        """Reset performance statistics / Đặt lại thống kê hiệu suất"""
        self._performance_stats = {
            "total_reflections": 0,
            "successful_reflections": 0,
            "average_improvement": 0.0,
            "average_time": 0.0,
        }


# Utility functions / Hàm tiện ích


def create_controller(mode: str = "normal") -> ReflectionController:
    """Create reflection controller with specified mode / Tạo bộ điều khiển phản tư với chế độ chỉ định"""
    reflection_mode = ReflectionMode(mode.lower())
    config = ReflectionConfig(mode=reflection_mode)
    return ReflectionController(config)


def get_default_controller() -> ReflectionController:
    """Get default reflection controller / Lấy bộ điều khiển phản tư mặc định"""
    return ReflectionController()


# Example usage / Ví dụ sử dụng
if __name__ == "__main__":
    # Test the controller
    controller = get_default_controller()

    test_response = """
    Để cài đặt Python, bạn có thể tải xuống từ python.org.
    Sau đó chạy installer và làm theo hướng dẫn.
    """

    test_query = "Cách cài đặt Python?"

    # Test should_reflect
    should_reflect = controller.should_reflect(test_query)
    print(f"Should reflect: {should_reflect}")

    if should_reflect:
        # Test enhancement
        import asyncio

        result = asyncio.run(controller.enhance_response(test_response, test_query))
        print(f"Improvement: {result.improvement:.3f}")
        print(f"Steps taken: {result.steps_taken}")
        print(f"Final response: {result.final_response}")
