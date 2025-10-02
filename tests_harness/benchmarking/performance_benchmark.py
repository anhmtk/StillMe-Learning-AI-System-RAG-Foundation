#!/usr/bin/env python3
"""
Performance Benchmark - So sánh StillMe với baseline

Tính năng:
- So sánh StillMe với baseline model
- Đo mức cải thiện % về chi phí token, độ an toàn, translation accuracy
- Tạo báo cáo benchmarking chi tiết
- Export kết quả so sánh
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from evaluators.agentdev_eval import AgentDevEval
from evaluators.efficiency_eval import EfficiencyEval
from evaluators.persona_eval import PersonaEval
from evaluators.safety_eval import SafetyEval
from evaluators.translation_eval import TranslationEval

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceBenchmark:
    """Benchmark để so sánh StillMe với baseline"""

    def __init__(self, output_dir: str = "tests_harness/benchmarking"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger

        # Initialize evaluators
        self.persona_eval = PersonaEval()
        self.safety_eval = SafetyEval()
        self.translation_eval = TranslationEval()
        self.efficiency_eval = EfficiencyEval()
        self.agentdev_eval = AgentDevEval()

        # Baseline configuration
        self.baseline_config = {
            "name": "Baseline Model",
            "description": "Standard AI model without StillMe enhancements",
            "features": {
                "persona_morph": False,
                "ethical_core": False,
                "translation": False,
                "agentdev": False,
                "dynamic_communication": False
            }
        }

        # StillMe configuration
        self.stillme_config = {
            "name": "StillMe AI",
            "description": "Enhanced AI with StillMe modules",
            "features": {
                "persona_morph": True,
                "ethical_core": True,
                "translation": True,
                "agentdev": True,
                "dynamic_communication": True
            }
        }

    def run_benchmark(self,
                     test_cases: List[Dict[str, Any]],
                     stillme_responses: List[Dict[str, Any]],
                     baseline_responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Chạy benchmark so sánh StillMe vs Baseline
        
        Args:
            test_cases: Danh sách test cases
            stillme_responses: Responses từ StillMe AI
            baseline_responses: Responses từ baseline model
            
        Returns:
            Dict: Kết quả benchmark
        """
        try:
            self.logger.info("🚀 Starting Performance Benchmark...")

            # Evaluate StillMe responses
            self.logger.info("🔍 Evaluating StillMe responses...")
            stillme_scores = self._evaluate_responses(stillme_responses, "StillMe")

            # Evaluate baseline responses
            self.logger.info("🔍 Evaluating baseline responses...")
            baseline_scores = self._evaluate_responses(baseline_responses, "Baseline")

            # Calculate improvements
            improvements = self._calculate_improvements(stillme_scores, baseline_scores)

            # Generate benchmark report
            benchmark_report = self._generate_benchmark_report(
                test_cases, stillme_scores, baseline_scores, improvements
            )

            # Save benchmark results
            self._save_benchmark_results(benchmark_report)

            self.logger.info("✅ Performance benchmark completed!")
            return benchmark_report

        except Exception as e:
            self.logger.error(f"❌ Performance benchmark failed: {e}")
            return {"error": str(e)}

    def _evaluate_responses(self, responses: List[Dict[str, Any]], model_name: str) -> Dict[str, Any]:
        """Đánh giá responses từ một model"""
        try:
            # Prepare data for evaluators
            persona_data = []
            safety_data = []
            translation_data = []
            efficiency_data = []
            agentdev_data = []

            for response in responses:
                # Persona evaluation data
                persona_data.append({
                    "response": response.get('response', ''),
                    "user_input": response.get('user_input', ''),
                    "user_preferences": response.get('user_preferences', {})
                })

                # Safety evaluation data
                safety_data.append({
                    "response": response.get('response', ''),
                    "user_input": response.get('user_input', ''),
                    "context": response.get('context', {})
                })

                # Translation evaluation data
                translation_data.append({
                    "response": response.get('response', ''),
                    "user_input": response.get('user_input', ''),
                    "expected_language": response.get('expected_language', 'vi'),
                    "source_language": response.get('source_language', 'auto')
                })

                # Efficiency evaluation data
                efficiency_data.append({
                    "response": response.get('response', ''),
                    "latency_ms": response.get('latency_ms', 0),
                    "token_count": response.get('token_count', 0),
                    "cost_estimate": response.get('cost_estimate', 0),
                    "user_input": response.get('user_input', ''),
                    "context": response.get('context', {})
                })

                # AgentDev evaluation data
                agentdev_data.append({
                    "response": response.get('response', ''),
                    "user_input": response.get('user_input', ''),
                    "context": response.get('context', {}),
                    "performance_metrics": response.get('performance_metrics', {})
                })

            # Run evaluations
            persona_scores = self.persona_eval.batch_evaluate(persona_data)
            safety_scores = self.safety_eval.batch_evaluate(safety_data)
            translation_scores = self.translation_eval.batch_evaluate(translation_data)
            efficiency_scores = self.efficiency_eval.batch_evaluate(efficiency_data)
            agentdev_scores = self.agentdev_eval.batch_evaluate(agentdev_data)

            # Generate reports
            persona_report = self.persona_eval.generate_report(persona_scores)
            safety_report = self.safety_eval.generate_report(safety_scores)
            translation_report = self.translation_eval.generate_report(translation_scores)
            efficiency_report = self.efficiency_eval.generate_report(efficiency_scores)
            agentdev_report = self.agentdev_eval.generate_report(agentdev_scores)

            return {
                "model_name": model_name,
                "persona_scores": [score.to_dict() for score in persona_scores],
                "safety_scores": [score.to_dict() for score in safety_scores],
                "translation_scores": [score.to_dict() for score in translation_scores],
                "efficiency_scores": [score.to_dict() for score in efficiency_scores],
                "agentdev_scores": [score.to_dict() for score in agentdev_scores],
                "reports": {
                    "persona": persona_report,
                    "safety": safety_report,
                    "translation": translation_report,
                    "efficiency": efficiency_report,
                    "agentdev": agentdev_report
                }
            }

        except Exception as e:
            self.logger.error(f"Error evaluating responses: {e}")
            return {}

    def _calculate_improvements(self, stillme_scores: Dict[str, Any],
                              baseline_scores: Dict[str, Any]) -> Dict[str, Any]:
        """Tính toán mức cải thiện"""
        try:
            improvements = {}

            # Calculate overall improvements
            stillme_overall = self._calculate_overall_score(stillme_scores)
            baseline_overall = self._calculate_overall_score(baseline_scores)

            overall_improvement = ((stillme_overall - baseline_overall) / baseline_overall * 100) if baseline_overall > 0 else 0

            improvements["overall"] = {
                "stillme_score": stillme_overall,
                "baseline_score": baseline_overall,
                "improvement_percent": round(overall_improvement, 2),
                "improvement_direction": "positive" if overall_improvement > 0 else "negative"
            }

            # Calculate category-specific improvements
            categories = ["persona", "safety", "translation", "efficiency", "agentdev"]

            for category in categories:
                stillme_avg = self._get_average_score(stillme_scores, category)
                baseline_avg = self._get_average_score(baseline_scores, category)

                if baseline_avg > 0:
                    improvement_percent = ((stillme_avg - baseline_avg) / baseline_avg * 100)
                else:
                    improvement_percent = 0

                improvements[category] = {
                    "stillme_score": stillme_avg,
                    "baseline_score": baseline_avg,
                    "improvement_percent": round(improvement_percent, 2),
                    "improvement_direction": "positive" if improvement_percent > 0 else "negative"
                }

            return improvements

        except Exception as e:
            self.logger.error(f"Error calculating improvements: {e}")
            return {}

    def _calculate_overall_score(self, scores: Dict[str, Any]) -> float:
        """Tính điểm tổng thể"""
        try:
            reports = scores.get('reports', {})

            # Get average scores from reports
            persona_avg = reports.get('persona', {}).get('average_scores', {}).get('overall', 0)
            safety_avg = reports.get('safety', {}).get('average_scores', {}).get('overall_safety', 0)
            translation_avg = reports.get('translation', {}).get('average_scores', {}).get('overall_translation', 0)
            efficiency_avg = reports.get('efficiency', {}).get('average_scores', {}).get('overall_efficiency', 0)
            agentdev_avg = reports.get('agentdev', {}).get('average_scores', {}).get('overall_agentdev', 0)

            # Calculate weighted average
            overall_score = (
                persona_avg * 0.2 +
                safety_avg * 0.2 +
                translation_avg * 0.2 +
                efficiency_avg * 0.2 +
                agentdev_avg * 0.2
            )

            return round(overall_score, 3)

        except Exception as e:
            self.logger.error(f"Error calculating overall score: {e}")
            return 0.0

    def _get_average_score(self, scores: Dict[str, Any], category: str) -> float:
        """Lấy điểm trung bình của một category"""
        try:
            reports = scores.get('reports', {})
            category_report = reports.get(category, {})
            average_scores = category_report.get('average_scores', {})

            if category == "persona":
                return average_scores.get('overall', 0)
            elif category == "safety":
                return average_scores.get('overall_safety', 0)
            elif category == "translation":
                return average_scores.get('overall_translation', 0)
            elif category == "efficiency":
                return average_scores.get('overall_efficiency', 0)
            elif category == "agentdev":
                return average_scores.get('overall_agentdev', 0)
            else:
                return 0.0

        except Exception as e:
            self.logger.error(f"Error getting average score for {category}: {e}")
            return 0.0

    def _generate_benchmark_report(self,
                                 test_cases: List[Dict[str, Any]],
                                 stillme_scores: Dict[str, Any],
                                 baseline_scores: Dict[str, Any],
                                 improvements: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo báo cáo benchmark"""
        try:
            report = {
                "timestamp": datetime.now().isoformat(),
                "benchmark_info": {
                    "total_test_cases": len(test_cases),
                    "stillme_config": self.stillme_config,
                    "baseline_config": self.baseline_config
                },
                "stillme_results": stillme_scores,
                "baseline_results": baseline_scores,
                "improvements": improvements,
                "summary": {
                    "overall_improvement": improvements.get('overall', {}).get('improvement_percent', 0),
                    "best_improvement_category": self._get_best_improvement_category(improvements),
                    "worst_improvement_category": self._get_worst_improvement_category(improvements),
                    "recommendations": self._generate_recommendations(improvements)
                }
            }

            return report

        except Exception as e:
            self.logger.error(f"Error generating benchmark report: {e}")
            return {}

    def _get_best_improvement_category(self, improvements: Dict[str, Any]) -> str:
        """Lấy category có cải thiện tốt nhất"""
        try:
            best_category = "overall"
            best_improvement = improvements.get('overall', {}).get('improvement_percent', 0)

            for category, data in improvements.items():
                if category != "overall":
                    improvement = data.get('improvement_percent', 0)
                    if improvement > best_improvement:
                        best_improvement = improvement
                        best_category = category

            return best_category

        except Exception as e:
            self.logger.error(f"Error getting best improvement category: {e}")
            return "overall"

    def _get_worst_improvement_category(self, improvements: Dict[str, Any]) -> str:
        """Lấy category có cải thiện kém nhất"""
        try:
            worst_category = "overall"
            worst_improvement = improvements.get('overall', {}).get('improvement_percent', 0)

            for category, data in improvements.items():
                if category != "overall":
                    improvement = data.get('improvement_percent', 0)
                    if improvement < worst_improvement:
                        worst_improvement = improvement
                        worst_category = category

            return worst_category

        except Exception as e:
            self.logger.error(f"Error getting worst improvement category: {e}")
            return "overall"

    def _generate_recommendations(self, improvements: Dict[str, Any]) -> List[str]:
        """Tạo recommendations dựa trên kết quả benchmark"""
        try:
            recommendations = []

            for category, data in improvements.items():
                if category != "overall":
                    improvement_percent = data.get('improvement_percent', 0)

                    if improvement_percent > 20:
                        recommendations.append(f"🎉 {category.title()}: Excellent improvement (+{improvement_percent}%)")
                    elif improvement_percent > 10:
                        recommendations.append(f"👍 {category.title()}: Good improvement (+{improvement_percent}%)")
                    elif improvement_percent > 0:
                        recommendations.append(f"📈 {category.title()}: Minor improvement (+{improvement_percent}%)")
                    elif improvement_percent > -10:
                        recommendations.append(f"⚠️ {category.title()}: Needs attention ({improvement_percent}%)")
                    else:
                        recommendations.append(f"🚨 {category.title()}: Critical issue ({improvement_percent}%)")

            # Overall recommendation
            overall_improvement = improvements.get('overall', {}).get('improvement_percent', 0)
            if overall_improvement > 15:
                recommendations.append("🏆 Overall: StillMe significantly outperforms baseline!")
            elif overall_improvement > 5:
                recommendations.append("✅ Overall: StillMe shows good improvement over baseline")
            elif overall_improvement > 0:
                recommendations.append("📊 Overall: StillMe shows minor improvement over baseline")
            else:
                recommendations.append("🔧 Overall: StillMe needs optimization to outperform baseline")

            return recommendations

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return []

    def _save_benchmark_results(self, benchmark_report: Dict[str, Any]) -> str:
        """Lưu kết quả benchmark"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = self.output_dir / f"benchmark_report_{timestamp}.json"

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(benchmark_report, f, indent=2, ensure_ascii=False)

            self.logger.info(f"✅ Benchmark results saved: {file_path}")
            return str(file_path)

        except Exception as e:
            self.logger.error(f"Error saving benchmark results: {e}")
            return ""

# Example usage
if __name__ == "__main__":
    # Test Performance Benchmark
    benchmark = PerformanceBenchmark()

    # Mock test data
    test_cases = [
        {"id": "test_1", "user_input": "Hello StillMe", "category": "greeting"},
        {"id": "test_2", "user_input": "How are you?", "category": "question"}
    ]

    stillme_responses = [
        {
            "response": "Xin chào! Tôi là StillMe AI. Rất vui được gặp bạn!",
            "user_input": "Hello StillMe",
            "latency_ms": 500,
            "token_count": 30,
            "cost_estimate": 0.001
        },
        {
            "response": "Tôi đang hoạt động tốt, cảm ơn bạn!",
            "user_input": "How are you?",
            "latency_ms": 600,
            "token_count": 25,
            "cost_estimate": 0.0008
        }
    ]

    baseline_responses = [
        {
            "response": "Hello! I'm an AI assistant. How can I help you?",
            "user_input": "Hello StillMe",
            "latency_ms": 800,
            "token_count": 35,
            "cost_estimate": 0.0015
        },
        {
            "response": "I'm doing well, thank you for asking!",
            "user_input": "How are you?",
            "latency_ms": 900,
            "token_count": 30,
            "cost_estimate": 0.0012
        }
    ]

    # Run benchmark
    results = benchmark.run_benchmark(test_cases, stillme_responses, baseline_responses)

    print("📊 Performance Benchmark Test Results:")
    print(json.dumps(results.get('summary', {}), indent=2, ensure_ascii=False))
