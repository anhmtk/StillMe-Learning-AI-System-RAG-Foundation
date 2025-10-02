#!/usr/bin/env python3
"""
Real Test Runner - Chạy test thực tế với StillMe AI Server

Tính năng:
- Kết nối đến StillMe AI Server qua Gateway
- Gửi request thật và đo performance
- Tích hợp với các evaluators
- Tạo báo cáo chi tiết
- Scale up dataset từ 50 lên 1000+ mẫu
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from evaluators.persona_eval import PersonaEval
from evaluators.safety_eval import SafetyEval
from evaluators.translation_eval import TranslationEval
from report_builder import HTMLReportBuilder

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RealTestRunner:
    """Runner cho testing thực tế với StillMe AI"""

    def __init__(
        self,
        gateway_url: str = "http://localhost:21568",
        ai_server_url: str = "http://localhost:1216",
        output_dir: str = "tests_harness/reports",
    ):
        self.gateway_url = gateway_url
        self.ai_server_url = ai_server_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger

        # Initialize evaluators
        self.persona_eval = PersonaEval()
        self.safety_eval = SafetyEval()
        self.translation_eval = TranslationEval()

        # Initialize report builder
        self.report_builder = HTMLReportBuilder(str(self.output_dir))

        # Test results storage
        self.test_results = []
        self.performance_metrics = []

    def run_comprehensive_test(
        self,
        test_cases: list[dict[str, Any]],
        max_concurrent: int = 5,
        timeout: int = 30,
    ) -> dict[str, Any]:
        """
        Chạy test toàn diện với StillMe AI

        Args:
            test_cases: Danh sách test cases
            max_concurrent: Số request đồng thời tối đa
            timeout: Timeout cho mỗi request (seconds)

        Returns:
            Dict: Kết quả test tổng hợp
        """
        try:
            self.logger.info(
                f"🚀 Starting comprehensive test with {len(test_cases)} test cases..."
            )

            # Check server health
            if not self._check_server_health():
                return {"error": "Server health check failed"}

            # Run tests
            start_time = time.time()
            results = self._run_test_batch(test_cases, max_concurrent, timeout)
            end_time = time.time()

            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(
                results, end_time - start_time
            )

            # Evaluate results
            evaluation_results = self._evaluate_results(results)

            # Generate comprehensive report
            report_data = self._generate_comprehensive_report(
                results, evaluation_results, performance_metrics
            )

            self.logger.info("✅ Comprehensive test completed successfully!")
            return report_data

        except Exception as e:
            self.logger.error(f"❌ Comprehensive test failed: {e}")
            return {"error": str(e)}

    def _check_server_health(self) -> bool:
        """Kiểm tra sức khỏe server"""
        try:
            # Check Gateway health
            gateway_response = requests.get(f"{self.gateway_url}/health", timeout=10)
            if gateway_response.status_code != 200:
                self.logger.error(
                    f"Gateway health check failed: {gateway_response.status_code}"
                )
                return False

            # Check AI Server health
            ai_response = requests.get(f"{self.ai_server_url}/health", timeout=10)
            if ai_response.status_code != 200:
                self.logger.error(
                    f"AI Server health check failed: {ai_response.status_code}"
                )
                return False

            self.logger.info("✅ Server health check passed")
            return True

        except Exception as e:
            self.logger.error(f"❌ Server health check failed: {e}")
            return False

    def _run_test_batch(
        self, test_cases: list[dict[str, Any]], max_concurrent: int, timeout: int
    ) -> list[dict[str, Any]]:
        """Chạy batch test cases"""
        results = []

        for i, test_case in enumerate(test_cases):
            try:
                self.logger.info(
                    f"🧪 Running test case {i+1}/{len(test_cases)}: {test_case.get('id', 'unknown')}"
                )

                # Send request to StillMe AI
                response_data = self._send_request(test_case, timeout)

                # Store result
                result = {
                    "test_case_id": test_case.get("id", f"test_{i+1}"),
                    "user_input": test_case.get("user_input", ""),
                    "expected_response": test_case.get("expected_response", ""),
                    "actual_response": response_data.get("response", ""),
                    "latency_ms": response_data.get("latency_ms", 0),
                    "token_count": response_data.get("token_count", 0),
                    "cost_estimate": response_data.get("cost_estimate", 0),
                    "success": response_data.get("success", False),
                    "error": response_data.get("error", ""),
                    "timestamp": datetime.now().isoformat(),
                }

                results.append(result)

                # Small delay to avoid overwhelming the server
                time.sleep(0.1)

            except Exception as e:
                self.logger.error(f"❌ Test case {i+1} failed: {e}")
                results.append(
                    {
                        "test_case_id": test_case.get("id", f"test_{i+1}"),
                        "user_input": test_case.get("user_input", ""),
                        "expected_response": test_case.get("expected_response", ""),
                        "actual_response": "",
                        "latency_ms": 0,
                        "token_count": 0,
                        "cost_estimate": 0,
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        return results

    def _send_request(self, test_case: dict[str, Any], timeout: int) -> dict[str, Any]:
        """Gửi request đến StillMe AI"""
        try:
            start_time = time.time()

            # Prepare request payload
            payload = {
                "message": test_case.get("user_input", ""),
                "locale": test_case.get("locale", "vi"),
                "user_preferences": test_case.get("user_preferences", {}),
            }

            # Send request to Gateway
            response = requests.post(
                f"{self.gateway_url}/send-message",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=timeout,
            )

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            if response.status_code == 200:
                response_data = response.json()

                # Extract response text
                ai_response = response_data.get("response", "")
                if not ai_response and "text" in response_data:
                    ai_response = response_data["text"]

                # Estimate token count (rough approximation)
                token_count = len(ai_response.split()) * 1.3  # Rough estimate

                # Estimate cost (rough approximation)
                cost_estimate = token_count * 0.0001  # Rough estimate

                return {
                    "response": ai_response,
                    "latency_ms": latency_ms,
                    "token_count": int(token_count),
                    "cost_estimate": round(cost_estimate, 6),
                    "success": True,
                    "error": "",
                }
            else:
                return {
                    "response": "",
                    "latency_ms": latency_ms,
                    "token_count": 0,
                    "cost_estimate": 0,
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                }

        except Exception as e:
            return {
                "response": "",
                "latency_ms": 0,
                "token_count": 0,
                "cost_estimate": 0,
                "success": False,
                "error": str(e),
            }

    def _calculate_performance_metrics(
        self, results: list[dict[str, Any]], total_duration: float
    ) -> dict[str, Any]:
        """Tính toán performance metrics"""
        try:
            if not results:
                return {}

            # Calculate basic metrics
            total_requests = len(results)
            successful_requests = len([r for r in results if r.get("success", False)])
            failed_requests = total_requests - successful_requests

            # Calculate latency metrics
            latencies = [
                r.get("latency_ms", 0) for r in results if r.get("success", False)
            ]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            min_latency = min(latencies) if latencies else 0
            max_latency = max(latencies) if latencies else 0

            # Calculate token metrics
            token_counts = [
                r.get("token_count", 0) for r in results if r.get("success", False)
            ]
            total_tokens = sum(token_counts)
            avg_tokens = total_tokens / len(token_counts) if token_counts else 0

            # Calculate cost metrics
            costs = [
                r.get("cost_estimate", 0) for r in results if r.get("success", False)
            ]
            total_cost = sum(costs)
            avg_cost = total_cost / len(costs) if costs else 0

            # Calculate throughput
            throughput = total_requests / total_duration if total_duration > 0 else 0

            return {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": successful_requests / total_requests
                if total_requests > 0
                else 0,
                "total_duration_seconds": total_duration,
                "throughput_rps": throughput,
                "latency_metrics": {
                    "average_ms": round(avg_latency, 2),
                    "min_ms": min_latency,
                    "max_ms": max_latency,
                },
                "token_metrics": {
                    "total_tokens": total_tokens,
                    "average_tokens": round(avg_tokens, 2),
                },
                "cost_metrics": {
                    "total_cost": round(total_cost, 6),
                    "average_cost": round(avg_cost, 6),
                },
            }

        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {}

    def _evaluate_results(self, results: list[dict[str, Any]]) -> dict[str, Any]:
        """Đánh giá kết quả test"""
        try:
            self.logger.info("🔍 Evaluating test results...")

            # Prepare data for evaluators
            persona_data = []
            safety_data = []
            translation_data = []

            for result in results:
                if result.get("success", False):
                    # Persona evaluation data
                    persona_data.append(
                        {
                            "response": result.get("actual_response", ""),
                            "user_input": result.get("user_input", ""),
                            "user_preferences": {},
                        }
                    )

                    # Safety evaluation data
                    safety_data.append(
                        {
                            "response": result.get("actual_response", ""),
                            "user_input": result.get("user_input", ""),
                            "context": {},
                        }
                    )

                    # Translation evaluation data
                    translation_data.append(
                        {
                            "response": result.get("actual_response", ""),
                            "user_input": result.get("user_input", ""),
                            "expected_language": "vietnamese",
                            "source_language": "auto",
                        }
                    )

            # Run evaluations
            persona_scores = self.persona_eval.batch_evaluate(persona_data)
            safety_scores = self.safety_eval.batch_evaluate(safety_data)
            translation_scores = self.translation_eval.batch_evaluate(translation_data)

            # Generate evaluation reports
            persona_report = self.persona_eval.generate_report(persona_scores)
            safety_report = self.safety_eval.generate_report(safety_scores)
            translation_report = self.translation_eval.generate_report(
                translation_scores
            )

            return {
                "persona_evaluation": {
                    "scores": [score.to_dict() for score in persona_scores],
                    "report": persona_report,
                },
                "safety_evaluation": {
                    "scores": [score.to_dict() for score in safety_scores],
                    "report": safety_report,
                },
                "translation_evaluation": {
                    "scores": [score.to_dict() for score in translation_scores],
                    "report": translation_report,
                },
            }

        except Exception as e:
            self.logger.error(f"Error evaluating results: {e}")
            return {}

    def _generate_comprehensive_report(
        self,
        results: list[dict[str, Any]],
        evaluation_results: dict[str, Any],
        performance_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """Tạo báo cáo toàn diện"""
        try:
            self.logger.info("📊 Generating comprehensive report...")

            # Prepare data for HTML report
            persona_scores = evaluation_results.get("persona_evaluation", {}).get(
                "scores", []
            )
            safety_scores = evaluation_results.get("safety_evaluation", {}).get(
                "scores", []
            )
            translation_scores = evaluation_results.get(
                "translation_evaluation", {}
            ).get("scores", [])

            # Mock efficiency scores (would be calculated from performance metrics)
            efficiency_scores = []
            for result in results:
                if result.get("success", False):
                    efficiency_scores.append(
                        {
                            "overall_efficiency_score": 0.8,  # Mock score
                            "latency": result.get("latency_ms", 0)
                            / 1000,  # Convert to seconds
                            "token_cost": result.get("cost_estimate", 0),
                            "response_quality": 0.7,  # Mock score
                        }
                    )

            # Prepare metadata
            metadata = {
                "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "dataset_size": f"{len(results)} test cases",
                "test_duration": f"{performance_metrics.get('total_duration_seconds', 0):.2f} seconds",
                "environment": "Local Development",
                "stillme_version": "1.0.0",
                "gateway_url": self.gateway_url,
                "ai_server_url": self.ai_server_url,
            }

            # Generate HTML report
            html_file = self.report_builder.build_comprehensive_report(
                persona_scores,
                safety_scores,
                translation_scores,
                efficiency_scores,
                metadata,
            )

            # Generate JSON report
            json_file = self.report_builder.export_json_report(
                persona_scores,
                safety_scores,
                translation_scores,
                efficiency_scores,
                metadata,
            )

            # Compile comprehensive report
            comprehensive_report = {
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata,
                "performance_metrics": performance_metrics,
                "evaluation_results": evaluation_results,
                "test_results": results,
                "reports": {"html_report": html_file, "json_report": json_file},
                "summary": {
                    "total_tests": len(results),
                    "successful_tests": len(
                        [r for r in results if r.get("success", False)]
                    ),
                    "average_latency_ms": performance_metrics.get(
                        "latency_metrics", {}
                    ).get("average_ms", 0),
                    "total_cost": performance_metrics.get("cost_metrics", {}).get(
                        "total_cost", 0
                    ),
                    "overall_performance": "Good"
                    if performance_metrics.get("success_rate", 0) > 0.8
                    else "Needs Improvement",
                },
            }

            # Save comprehensive report
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = (
                self.output_dir / f"comprehensive_test_report_{timestamp}.json"
            )

            with open(report_file, "w", encoding="utf-8") as f:
                json.dump(comprehensive_report, f, indent=2, ensure_ascii=False)

            self.logger.info(f"✅ Comprehensive report generated: {report_file}")
            return comprehensive_report

        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            return {"error": str(e)}

    def load_test_cases_from_file(self, file_path: str) -> list[dict[str, Any]]:
        """Load test cases từ file"""
        try:
            with open(file_path, encoding="utf-8") as f:
                if file_path.endswith(".json"):
                    return json.load(f)
                elif file_path.endswith(".jsonl"):
                    return [json.loads(line) for line in f if line.strip()]
                else:
                    self.logger.error(f"Unsupported file format: {file_path}")
                    return []

        except Exception as e:
            self.logger.error(f"Error loading test cases: {e}")
            return []

    def generate_test_cases(self, count: int = 100) -> list[dict[str, Any]]:
        """Tạo test cases mẫu"""
        test_cases = []

        # Sample test cases
        sample_cases = [
            {
                "id": "greeting_vi",
                "user_input": "Xin chào StillMe",
                "expected_response": "Xin chào",
                "locale": "vi",
                "category": "greeting",
            },
            {
                "id": "greeting_en",
                "user_input": "Hello StillMe",
                "expected_response": "Hello",
                "locale": "en",
                "category": "greeting",
            },
            {
                "id": "question_vi",
                "user_input": "Hôm nay thế nào?",
                "expected_response": "Hôm nay",
                "locale": "vi",
                "category": "question",
            },
            {
                "id": "question_en",
                "user_input": "How are you today?",
                "expected_response": "Today",
                "locale": "en",
                "category": "question",
            },
            {
                "id": "help_request",
                "user_input": "Bạn có thể giúp tôi không?",
                "expected_response": "giúp",
                "locale": "vi",
                "category": "help_request",
            },
        ]

        # Generate more test cases
        for i in range(count):
            base_case = sample_cases[i % len(sample_cases)]
            test_case = {
                "id": f"{base_case['id']}_{i+1}",
                "user_input": base_case["user_input"],
                "expected_response": base_case["expected_response"],
                "locale": base_case["locale"],
                "category": base_case["category"],
                "user_preferences": {},
            }
            test_cases.append(test_case)

        return test_cases


# Example usage
if __name__ == "__main__":
    # Test Real Test Runner
    runner = RealTestRunner()

    # Generate test cases
    test_cases = runner.generate_test_cases(10)

    # Run comprehensive test
    results = runner.run_comprehensive_test(test_cases)

    print("🧪 Real Test Runner Test Results:")
    print(json.dumps(results.get("summary", {}), indent=2, ensure_ascii=False))
