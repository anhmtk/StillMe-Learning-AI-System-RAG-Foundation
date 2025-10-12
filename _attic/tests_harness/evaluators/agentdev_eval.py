#!/usr/bin/env python3
"""
AgentDevEval - Đánh giá tích hợp và hiệu suất của AgentDev

Kiểm tra:
- AgentDev integration (kết nối và hoạt động)
- Performance metrics (thời gian xử lý, tài nguyên)
- Code quality (chất lượng code được tạo)
- Security compliance (tuân thủ bảo mật)
- Learning capabilities (khả năng học hỏi)
"""

import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AgentDevScore:
    """Kết quả đánh giá AgentDev"""

    integration_score: float  # 0-1: điểm tích hợp
    performance_score: float  # 0-1: điểm hiệu suất
    code_quality: float  # 0-1: chất lượng code
    security_compliance: float  # 0-1: tuân thủ bảo mật
    learning_capability: float  # 0-1: khả năng học hỏi
    overall_agentdev_score: float  # 0-1: điểm AgentDev tổng

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AgentDevEval:
    """Evaluator cho AgentDev integration và performance"""

    def __init__(self):
        self.logger = logger

        # AgentDev integration patterns
        self.integration_patterns = {
            "agentdev_indicators": [
                r"\b(AgentDev|agent\s+dev|autonomous\s+development)\b",
                r"\b(self\s+improving|self\s+learning|adaptive)\b",
                r"\b(code\s+generation|automatic\s+coding|AI\s+development)\b",
            ],
            "task_management": [
                r"\b(task|project|development|planning)\b",
                r"\b(plan|strategy|approach|methodology)\b",
                r"\b(execute|implement|deploy|deliver)\b",
            ],
            "learning_indicators": [
                r"\b(learn|improve|optimize|enhance)\b",
                r"\b(experience|knowledge|insight|understanding)\b",
                r"\b(adapt|evolve|progress|advance)\b",
            ],
        }

        # Code quality indicators
        self.code_quality_patterns = {
            "structure": [
                r"\b(class|function|method|module)\b",
                r"\b(import|from|def|class)\b",
                r"\b(if|for|while|try|except)\b",
            ],
            "documentation": [
                r"\b(comment|docstring|documentation|explain)\b",
                r"\b(README|guide|tutorial|example)\b",
                r"\b(description|purpose|usage|parameter)\b",
            ],
            "best_practices": [
                r"\b(error\s+handling|exception|try\s+except)\b",
                r"\b(validation|check|verify|test)\b",
                r"\b(clean\s+code|readable|maintainable)\b",
            ],
        }

        # Security compliance patterns
        self.security_patterns = {
            "input_validation": [
                r"\b(validate|sanitize|filter|check)\b",
                r"\b(input|user\s+input|parameter)\b",
                r"\b(security|safe|secure)\b",
            ],
            "authentication": [
                r"\b(auth|login|password|token)\b",
                r"\b(permission|access|authorize)\b",
                r"\b(credential|identity|verify)\b",
            ],
            "data_protection": [
                r"\b(encrypt|hash|secure|protect)\b",
                r"\b(private|sensitive|confidential)\b",
                r"\b(data\s+protection|privacy)\b",
            ],
        }

        # Performance thresholds
        self.performance_thresholds = {
            "response_time": {
                "excellent": 1000,  # < 1s
                "good": 3000,  # 1-3s
                "fair": 5000,  # 3-5s
                "poor": 10000,  # > 5s
            },
            "memory_usage": {
                "excellent": 100,  # < 100MB
                "good": 500,  # 100-500MB
                "fair": 1000,  # 500MB-1GB
                "poor": 2000,  # > 1GB
            },
        }

    def evaluate(
        self,
        response: str,
        user_input: str = "",
        context: dict | None = None,
        performance_metrics: dict | None = None,
    ) -> AgentDevScore:
        """
        Đánh giá AgentDev integration và performance

        Args:
            response: AI response cần đánh giá
            user_input: User input gốc (optional)
            context: Context bổ sung (optional)
            performance_metrics: Performance metrics (optional)

        Returns:
            AgentDevScore: Kết quả đánh giá AgentDev
        """
        try:
            self.logger.info(
                f"🔍 Evaluating AgentDev for response: {response[:100]}..."
            )

            # 1. Đánh giá integration
            integration_score = self._evaluate_integration(response, user_input)

            # 2. Đánh giá performance
            performance_score = self._evaluate_performance(performance_metrics)

            # 3. Đánh giá code quality
            code_quality = self._evaluate_code_quality(response, user_input)

            # 4. Đánh giá security compliance
            security_compliance = self._evaluate_security_compliance(
                response, user_input
            )

            # 5. Đánh giá learning capability
            learning_capability = self._evaluate_learning_capability(response, context)

            # 6. Tính điểm AgentDev tổng
            overall_score = (
                integration_score * 0.25
                + performance_score * 0.20
                + code_quality * 0.20
                + security_compliance * 0.20
                + learning_capability * 0.15
            )

            result = AgentDevScore(
                integration_score=integration_score,
                performance_score=performance_score,
                code_quality=code_quality,
                security_compliance=security_compliance,
                learning_capability=learning_capability,
                overall_agentdev_score=overall_score,
            )

            self.logger.info(
                f"✅ AgentDev evaluation completed. Overall score: {overall_score:.3f}"
            )
            return result

        except Exception as e:
            self.logger.error(f"❌ AgentDev evaluation failed: {e}")
            return AgentDevScore(0, 0, 0, 0, 0, 0)

    def _evaluate_integration(self, response: str, user_input: str) -> float:
        """Đánh giá AgentDev integration"""
        try:
            score = 0.0
            total_checks = 0

            # Check for AgentDev indicators
            agentdev_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.integration_patterns["agentdev_indicators"]
            )
            if agentdev_count > 0:
                score += 0.4
            total_checks += 1

            # Check for task management capabilities
            task_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.integration_patterns["task_management"]
            )
            if task_count > 0:
                score += 0.3
            total_checks += 1

            # Check for learning indicators
            learning_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.integration_patterns["learning_indicators"]
            )
            if learning_count > 0:
                score += 0.3
            total_checks += 1

            # Check if response shows autonomous behavior
            autonomous_indicators = [
                r"\b(I\s+will|I\s+can|I\s+am\s+able|I\s+can\s+help)\b",
                r"\b(automatically|autonomously|independently)\b",
                r"\b(self\s+directed|self\s+managed|self\s+governing)\b",
            ]

            autonomous_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in autonomous_indicators
            )
            if autonomous_count > 0:
                score += 0.2
            total_checks += 1

            return min(score / max(total_checks, 1), 1.0)

        except Exception as e:
            self.logger.error(f"Error evaluating integration: {e}")
            return 0.0

    def _evaluate_performance(self, performance_metrics: dict | None) -> float:
        """Đánh giá performance"""
        try:
            if not performance_metrics:
                return 0.5  # Default score if no metrics

            score = 0.0
            total_checks = 0

            # Check response time
            response_time = performance_metrics.get("response_time_ms", 0)
            if (
                response_time
                <= self.performance_thresholds["response_time"]["excellent"]
            ):
                score += 0.4
            elif response_time <= self.performance_thresholds["response_time"]["good"]:
                score += 0.3
            elif response_time <= self.performance_thresholds["response_time"]["fair"]:
                score += 0.2
            else:
                score += 0.1
            total_checks += 1

            # Check memory usage
            memory_usage = performance_metrics.get("memory_usage_mb", 0)
            if memory_usage <= self.performance_thresholds["memory_usage"]["excellent"]:
                score += 0.3
            elif memory_usage <= self.performance_thresholds["memory_usage"]["good"]:
                score += 0.25
            elif memory_usage <= self.performance_thresholds["memory_usage"]["fair"]:
                score += 0.15
            else:
                score += 0.1
            total_checks += 1

            # Check CPU usage
            cpu_usage = performance_metrics.get("cpu_usage_percent", 0)
            if cpu_usage <= 50:
                score += 0.3
            elif cpu_usage <= 75:
                score += 0.25
            elif cpu_usage <= 90:
                score += 0.15
            else:
                score += 0.1
            total_checks += 1

            return min(score / max(total_checks, 1), 1.0)

        except Exception as e:
            self.logger.error(f"Error evaluating performance: {e}")
            return 0.0

    def _evaluate_code_quality(self, response: str, user_input: str) -> float:
        """Đánh giá chất lượng code"""
        try:
            score = 0.0
            total_checks = 0

            # Check for code structure
            structure_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.code_quality_patterns["structure"]
            )
            if structure_count > 0:
                score += 0.4
            total_checks += 1

            # Check for documentation
            doc_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.code_quality_patterns["documentation"]
            )
            if doc_count > 0:
                score += 0.3
            total_checks += 1

            # Check for best practices
            practices_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.code_quality_patterns["best_practices"]
            )
            if practices_count > 0:
                score += 0.3
            total_checks += 1

            # Check for code blocks in response
            code_blocks = len(re.findall(r"```[\s\S]*?```", response))
            if code_blocks > 0:
                score += 0.2
            total_checks += 1

            return min(score / max(total_checks, 1), 1.0)

        except Exception as e:
            self.logger.error(f"Error evaluating code quality: {e}")
            return 0.0

    def _evaluate_security_compliance(self, response: str, user_input: str) -> float:
        """Đánh giá tuân thủ bảo mật"""
        try:
            score = 0.0
            total_checks = 0

            # Check for input validation
            validation_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.security_patterns["input_validation"]
            )
            if validation_count > 0:
                score += 0.4
            total_checks += 1

            # Check for authentication
            auth_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.security_patterns["authentication"]
            )
            if auth_count > 0:
                score += 0.3
            total_checks += 1

            # Check for data protection
            protection_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in self.security_patterns["data_protection"]
            )
            if protection_count > 0:
                score += 0.3
            total_checks += 1

            # Check for security warnings
            security_warnings = [
                r"\b(security\s+warning|security\s+risk|vulnerability)\b",
                r"\b(unsafe|dangerous|risky|insecure)\b",
                r"\b(validate\s+input|sanitize\s+data|check\s+permissions)\b",
            ]

            warning_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in security_warnings
            )
            if warning_count > 0:
                score += 0.2
            total_checks += 1

            return min(score / max(total_checks, 1), 1.0)

        except Exception as e:
            self.logger.error(f"Error evaluating security compliance: {e}")
            return 0.0

    def _evaluate_learning_capability(
        self, response: str, context: dict | None
    ) -> float:
        """Đánh giá khả năng học hỏi"""
        try:
            score = 0.0
            total_checks = 0

            # Check for learning indicators in response
            learning_indicators = [
                r"\b(learn|improve|optimize|enhance)\b",
                r"\b(experience|knowledge|insight|understanding)\b",
                r"\b(adapt|evolve|progress|advance)\b",
                r"\b(remember|recall|retain|store)\b",
            ]

            learning_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in learning_indicators
            )
            if learning_count > 0:
                score += 0.4
            total_checks += 1

            # Check for context awareness
            if context and "previous_interactions" in context:
                score += 0.3
            total_checks += 1

            # Check for adaptive behavior
            adaptive_indicators = [
                r"\b(adapt|adjust|modify|change)\b",
                r"\b(based\s+on|according\s+to|depending\s+on)\b",
                r"\b(context|situation|circumstance)\b",
            ]

            adaptive_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in adaptive_indicators
            )
            if adaptive_count > 0:
                score += 0.3
            total_checks += 1

            # Check for self-reflection
            reflection_indicators = [
                r"\b(reflect|analyze|evaluate|assess)\b",
                r"\b(think|consider|ponder|contemplate)\b",
                r"\b(review|examine|study|investigate)\b",
            ]

            reflection_count = sum(
                len(re.findall(pattern, response, re.IGNORECASE))
                for pattern in reflection_indicators
            )
            if reflection_count > 0:
                score += 0.2
            total_checks += 1

            return min(score / max(total_checks, 1), 1.0)

        except Exception as e:
            self.logger.error(f"Error evaluating learning capability: {e}")
            return 0.0

    def batch_evaluate(self, responses: list[dict[str, Any]]) -> list[AgentDevScore]:
        """Đánh giá hàng loạt responses"""
        results = []

        for i, item in enumerate(responses):
            try:
                response = item.get("response", "")
                user_input = item.get("user_input", "")
                context = item.get("context", {})
                performance_metrics = item.get("performance_metrics", {})

                score = self.evaluate(
                    response, user_input, context, performance_metrics
                )
                results.append(score)

                self.logger.info(f"✅ Evaluated response {i+1}/{len(responses)}")

            except Exception as e:
                self.logger.error(f"❌ Failed to evaluate response {i+1}: {e}")
                results.append(AgentDevScore(0, 0, 0, 0, 0, 0))

        return results

    def generate_report(self, scores: list[AgentDevScore]) -> dict[str, Any]:
        """Tạo báo cáo tổng hợp"""
        try:
            if not scores:
                return {"error": "No scores provided"}

            # Calculate statistics
            total_scores = len(scores)
            avg_integration = sum(s.integration_score for s in scores) / total_scores
            avg_performance = sum(s.performance_score for s in scores) / total_scores
            avg_code_quality = sum(s.code_quality for s in scores) / total_scores
            avg_security = sum(s.security_compliance for s in scores) / total_scores
            avg_learning = sum(s.learning_capability for s in scores) / total_scores
            avg_overall = sum(s.overall_agentdev_score for s in scores) / total_scores

            # Find best and worst scores
            best_score = max(scores, key=lambda s: s.overall_agentdev_score)
            worst_score = min(scores, key=lambda s: s.overall_agentdev_score)

            report = {
                "timestamp": datetime.now().isoformat(),
                "total_responses": total_scores,
                "average_scores": {
                    "integration_score": round(avg_integration, 3),
                    "performance_score": round(avg_performance, 3),
                    "code_quality": round(avg_code_quality, 3),
                    "security_compliance": round(avg_security, 3),
                    "learning_capability": round(avg_learning, 3),
                    "overall_agentdev": round(avg_overall, 3),
                },
                "best_score": {
                    "overall_agentdev": round(best_score.overall_agentdev_score, 3),
                    "integration_score": round(best_score.integration_score, 3),
                    "performance_score": round(best_score.performance_score, 3),
                },
                "worst_score": {
                    "overall_agentdev": round(worst_score.overall_agentdev_score, 3),
                    "integration_score": round(worst_score.integration_score, 3),
                    "performance_score": round(worst_score.performance_score, 3),
                },
                "agentdev_distribution": {
                    "excellent": len(
                        [s for s in scores if s.overall_agentdev_score >= 0.8]
                    ),
                    "good": len(
                        [s for s in scores if 0.6 <= s.overall_agentdev_score < 0.8]
                    ),
                    "fair": len(
                        [s for s in scores if 0.4 <= s.overall_agentdev_score < 0.6]
                    ),
                    "poor": len([s for s in scores if s.overall_agentdev_score < 0.4]),
                },
            }

            return report

        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    # Test AgentDevEval
    evaluator = AgentDevEval()

    # Test responses
    test_responses = [
        {
            "response": "I can help you with AgentDev tasks. Let me analyze the requirements and create a development plan.",
            "user_input": "Help me with AgentDev",
            "context": {"previous_interactions": 5},
            "performance_metrics": {
                "response_time_ms": 800,
                "memory_usage_mb": 150,
                "cpu_usage_percent": 45,
            },
        },
        {
            "response": "Based on my learning from previous interactions, I'll adapt my approach to better serve you.",
            "user_input": "Learn from our conversation",
            "context": {"learning_enabled": True},
            "performance_metrics": {
                "response_time_ms": 1200,
                "memory_usage_mb": 200,
                "cpu_usage_percent": 60,
            },
        },
    ]

    # Evaluate
    scores = evaluator.batch_evaluate(test_responses)

    # Generate report
    report = evaluator.generate_report(scores)

    print("🤖 AgentDevEval Test Results:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
