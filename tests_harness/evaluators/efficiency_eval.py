#!/usr/bin/env python3
"""
EfficiencyEval - Đánh giá hiệu suất và chi phí của StillMe AI

Kiểm tra:
- Latency (thời gian phản hồi)
- Token cost (chi phí token)
- Response quality (chất lượng phản hồi)
- Throughput (số request/giây)
- Resource utilization (sử dụng tài nguyên)
"""

import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class EfficiencyScore:
    """Kết quả đánh giá hiệu suất"""

    latency_score: float  # 0-1: điểm latency
    token_efficiency: float  # 0-1: hiệu quả sử dụng token
    response_quality: float  # 0-1: chất lượng phản hồi
    throughput_score: float  # 0-1: điểm throughput
    resource_efficiency: float  # 0-1: hiệu quả sử dụng tài nguyên
    overall_efficiency_score: float  # 0-1: điểm hiệu suất tổng

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EfficiencyEval:
    """Evaluator cho hiệu suất và chi phí"""

    def __init__(self):
        self.logger = logger

        # Latency thresholds (milliseconds)
        self.latency_thresholds = {
            "excellent": 500,  # < 500ms
            "good": 1000,  # 500-1000ms
            "fair": 2000,  # 1000-2000ms
            "poor": 5000,  # > 2000ms
        }

        # Token efficiency thresholds
        self.token_thresholds = {
            "excellent": 0.8,  # > 80% efficiency
            "good": 0.6,  # 60-80%
            "fair": 0.4,  # 40-60%
            "poor": 0.2,  # < 40%
        }

        # Response quality indicators
        self.quality_indicators = {
            "length_appropriate": {"min_length": 10, "max_length": 2000},
            "completeness": [
                r"\b(complete|comprehensive|thorough|detailed)\b",
                r"\b(đầy đủ|toàn diện|chi tiết|kỹ lưỡng)\b",
            ],
            "clarity": [
                r"\b(clear|understandable|simple|easy)\b",
                r"\b(rõ ràng|dễ hiểu|đơn giản|dễ dàng)\b",
            ],
            "helpfulness": [
                r"\b(helpful|useful|assist|support)\b",
                r"\b(hữu ích|giúp đỡ|hỗ trợ|có ích)\b",
            ],
            "relevance": [
                r"\b(relevant|related|pertinent|applicable)\b",
                r"\b(liên quan|phù hợp|thích hợp|áp dụng)\b",
            ],
        }

        # Throughput thresholds (requests per second)
        self.throughput_thresholds = {
            "excellent": 10,  # > 10 RPS
            "good": 5,  # 5-10 RPS
            "fair": 2,  # 2-5 RPS
            "poor": 1,  # < 2 RPS
        }

    def evaluate(
        self,
        response: str,
        latency_ms: float,
        token_count: int,
        cost_estimate: float,
        user_input: str = "",
        context: Optional[dict] = None,
    ) -> EfficiencyScore:
        """
        Đánh giá hiệu suất của response

        Args:
            response: AI response cần đánh giá
            latency_ms: Thời gian phản hồi (milliseconds)
            token_count: Số token sử dụng
            cost_estimate: Ước tính chi phí
            user_input: User input gốc (optional)
            context: Context bổ sung (optional)

        Returns:
            EfficiencyScore: Kết quả đánh giá hiệu suất
        """
        try:
            self.logger.info(
                f"🔍 Evaluating efficiency for response: {response[:100]}..."
            )

            # 1. Đánh giá latency
            latency_score = self._evaluate_latency(latency_ms)

            # 2. Đánh giá token efficiency
            token_efficiency = self._evaluate_token_efficiency(
                token_count, response, user_input
            )

            # 3. Đánh giá response quality
            response_quality = self._evaluate_response_quality(response, user_input)

            # 4. Đánh giá throughput (cần context với multiple requests)
            throughput_score = self._evaluate_throughput(context)

            # 5. Đánh giá resource efficiency
            resource_efficiency = self._evaluate_resource_efficiency(
                token_count, cost_estimate, latency_ms, response
            )

            # 6. Tính điểm hiệu suất tổng
            overall_score = (
                latency_score * 0.25
                + token_efficiency * 0.25
                + response_quality * 0.25
                + throughput_score * 0.15
                + resource_efficiency * 0.10
            )

            result = EfficiencyScore(
                latency_score=latency_score,
                token_efficiency=token_efficiency,
                response_quality=response_quality,
                throughput_score=throughput_score,
                resource_efficiency=resource_efficiency,
                overall_efficiency_score=overall_score,
            )

            self.logger.info(
                f"✅ Efficiency evaluation completed. Overall score: {overall_score:.3f}"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ Efficiency evaluation failed: {e}")
            return EfficiencyScore(0, 0, 0, 0, 0, 0)

    def _evaluate_latency(self, latency_ms: float) -> float:
        """Đánh giá latency"""
        try:
            if latency_ms <= self.latency_thresholds["excellent"]:
                return 1.0
            elif latency_ms <= self.latency_thresholds["good"]:
                return 0.8
            elif latency_ms <= self.latency_thresholds["fair"]:
                return 0.6
            elif latency_ms <= self.latency_thresholds["poor"]:
                return 0.4
            else:
                return 0.2

        except Exception as e:
            self.logger.error(f"Error evaluating latency: {e}")
            return 0.0

    def _evaluate_token_efficiency(
        self, token_count: int, response: str, user_input: str
    ) -> float:
        """Đánh giá hiệu quả sử dụng token"""
        try:
            if token_count == 0:
                return 0.0

            # Calculate response length
            response_length = len(response)
            input_length = len(user_input)

            # Calculate token efficiency ratio
            if input_length > 0:
                efficiency_ratio = response_length / (input_length + token_count)
            else:
                efficiency_ratio = response_length / token_count

            # Normalize to 0-1 scale
            if efficiency_ratio >= 0.8:
                return 1.0
            elif efficiency_ratio >= 0.6:
                return 0.8
            elif efficiency_ratio >= 0.4:
                return 0.6
            elif efficiency_ratio >= 0.2:
                return 0.4
            else:
                return 0.2

        except Exception as e:
            self.logger.error(f"Error evaluating token efficiency: {e}")
            return 0.0

    def _evaluate_response_quality(self, response: str, user_input: str) -> float:
        """Đánh giá chất lượng phản hồi"""
        try:
            score = 0.0
            total_checks = 0

            # Check length appropriateness
            response_length = len(response)
            min_length = self.quality_indicators["length_appropriate"]["min_length"]
            max_length = self.quality_indicators["length_appropriate"]["max_length"]

            if min_length <= response_length <= max_length:
                score += 0.2
            elif response_length < min_length:
                score += 0.1  # Too short
            else:
                score += 0.15  # Too long but acceptable
            total_checks += 1

            # Check completeness
            completeness_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.quality_indicators["completeness"]
            )
            if completeness_count > 0:
                score += 0.2
            total_checks += 1

            # Check clarity
            clarity_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.quality_indicators["clarity"]
            )
            if clarity_count > 0:
                score += 0.2
            total_checks += 1

            # Check helpfulness
            helpfulness_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.quality_indicators["helpfulness"]
            )
            if helpfulness_count > 0:
                score += 0.2
            total_checks += 1

            # Check relevance
            relevance_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.quality_indicators["relevance"]
            )
            if relevance_count > 0:
                score += 0.2
            total_checks += 1

            return min(score / max(total_checks, 1), 1.0)

        except Exception as e:
            self.logger.error(f"Error evaluating response quality: {e}")
            return 0.0

    def _evaluate_throughput(self, context: Optional[dict]) -> float:
        """Đánh giá throughput"""
        try:
            if not context or "throughput_rps" not in context:
                return 0.5  # Default score if no throughput data

            throughput_rps = context["throughput_rps"]

            if throughput_rps >= self.throughput_thresholds["excellent"]:
                return 1.0
            elif throughput_rps >= self.throughput_thresholds["good"]:
                return 0.8
            elif throughput_rps >= self.throughput_thresholds["fair"]:
                return 0.6
            elif throughput_rps >= self.throughput_thresholds["poor"]:
                return 0.4
            else:
                return 0.2

        except Exception as e:
            self.logger.error(f"Error evaluating throughput: {e}")
            return 0.0

    def _evaluate_resource_efficiency(
        self, token_count: int, cost_estimate: float, latency_ms: float, response: str
    ) -> float:
        """Đánh giá hiệu quả sử dụng tài nguyên"""
        try:
            score = 0.0
            total_checks = 0

            # Check cost per token
            if token_count > 0:
                cost_per_token = cost_estimate / token_count
                if cost_per_token <= 0.0001:  # Very efficient
                    score += 0.4
                elif cost_per_token <= 0.0005:  # Good
                    score += 0.3
                elif cost_per_token <= 0.001:  # Fair
                    score += 0.2
                else:  # Poor
                    score += 0.1
            total_checks += 1

            # Check latency per token
            if token_count > 0:
                latency_per_token = latency_ms / token_count
                if latency_per_token <= 10:  # Very efficient
                    score += 0.3
                elif latency_per_token <= 20:  # Good
                    score += 0.25
                elif latency_per_token <= 50:  # Fair
                    score += 0.15
                else:  # Poor
                    score += 0.1
            total_checks += 1

            # Check response value per token
            response_length = len(response)
            if token_count > 0:
                value_per_token = response_length / token_count
                if value_per_token >= 2:  # High value
                    score += 0.3
                elif value_per_token >= 1:  # Good value
                    score += 0.25
                elif value_per_token >= 0.5:  # Fair value
                    score += 0.15
                else:  # Low value
                    score += 0.1
            total_checks += 1

            return min(score / max(total_checks, 1), 1.0)

        except Exception as e:
            self.logger.error(f"Error evaluating resource efficiency: {e}")
            return 0.0

    def batch_evaluate(self, responses: list[dict[str, Any]]) -> list[EfficiencyScore]:
        """Đánh giá hàng loạt responses"""
        results = []

        for i, item in enumerate(responses):
            try:
                response = item.get("response", "")
                latency_ms = item.get("latency_ms", 0)
                token_count = item.get("token_count", 0)
                cost_estimate = item.get("cost_estimate", 0)
                user_input = item.get("user_input", "")
                context = item.get("context", {})

                score = self.evaluate(
                    response,
                    latency_ms,
                    token_count,
                    cost_estimate,
                    user_input,
                    context,
                )
                results.append(score)

                self.logger.info(f"✅ Evaluated response {i+1}/{len(responses)}")

            except Exception as e:
                self.logger.error(f"❌ Failed to evaluate response {i+1}: {e}")
                results.append(EfficiencyScore(0, 0, 0, 0, 0, 0))

        return results

    def generate_report(self, scores: list[EfficiencyScore]) -> dict[str, Any]:
        """Tạo báo cáo tổng hợp"""
        try:
            if not scores:
                return {"error": "No scores provided"}

            # Calculate statistics
            total_scores = len(scores)
            avg_latency = sum(s.latency_score for s in scores) / total_scores
            avg_token_efficiency = (
                sum(s.token_efficiency for s in scores) / total_scores
            )
            avg_response_quality = (
                sum(s.response_quality for s in scores) / total_scores
            )
            avg_throughput = sum(s.throughput_score for s in scores) / total_scores
            avg_resource_efficiency = (
                sum(s.resource_efficiency for s in scores) / total_scores
            )
            avg_overall = sum(s.overall_efficiency_score for s in scores) / total_scores

            # Find best and worst scores
            best_score = max(scores, key=lambda s: s.overall_efficiency_score)
            worst_score = min(scores, key=lambda s: s.overall_efficiency_score)

            report = {
                "timestamp": datetime.now().isoformat(),
                "total_responses": total_scores,
                "average_scores": {
                    "latency_score": round(avg_latency, 3),
                    "token_efficiency": round(avg_token_efficiency, 3),
                    "response_quality": round(avg_response_quality, 3),
                    "throughput_score": round(avg_throughput, 3),
                    "resource_efficiency": round(avg_resource_efficiency, 3),
                    "overall_efficiency": round(avg_overall, 3),
                },
                "best_score": {
                    "overall_efficiency": round(best_score.overall_efficiency_score, 3),
                    "latency_score": round(best_score.latency_score, 3),
                    "token_efficiency": round(best_score.token_efficiency, 3),
                },
                "worst_score": {
                    "overall_efficiency": round(
                        worst_score.overall_efficiency_score, 3
                    ),
                    "latency_score": round(worst_score.latency_score, 3),
                    "token_efficiency": round(worst_score.token_efficiency, 3),
                },
                "efficiency_distribution": {
                    "excellent": len(
                        [s for s in scores if s.overall_efficiency_score >= 0.8]
                    ),
                    "good": len(
                        [s for s in scores if 0.6 <= s.overall_efficiency_score < 0.8]
                    ),
                    "fair": len(
                        [s for s in scores if 0.4 <= s.overall_efficiency_score < 0.6]
                    ),
                    "poor": len(
                        [s for s in scores if s.overall_efficiency_score < 0.4]
                    ),
                },
            }

            return report

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    # Test EfficiencyEval
    evaluator = EfficiencyEval()

    # Test responses
    test_responses = [
        {
            "response": "Xin chào anh! Em là StillMe AI. Rất vui được gặp anh! Em có thể giúp gì cho anh hôm nay?",
            "latency_ms": 500,
            "token_count": 50,
            "cost_estimate": 0.001,
            "user_input": "Xin chào StillMe",
            "context": {"throughput_rps": 5},
        },
        {
            "response": "Hello! I'm StillMe AI. Nice to meet you! How can I help you today?",
            "latency_ms": 800,
            "token_count": 45,
            "cost_estimate": 0.0008,
            "user_input": "Hello StillMe",
            "context": {"throughput_rps": 3},
        },
    ]

    # Evaluate
    scores = evaluator.batch_evaluate(test_responses)

    # Generate report
    report = evaluator.generate_report(scores)

    print("⚡ EfficiencyEval Test Results:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
