"""
StillMe AI Stress Test & Evaluation System
==========================================
Comprehensive testing and evaluation system for StillMe AI with automatic improvement suggestions.
"""

import asyncio
import csv
import json
import statistics
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
from test_cases import ALL_TEST_CASES, get_test_statistics

from evaluator import (
    EvaluationResult,
    StillMeEvaluator,
    generate_improvement_suggestions,
)


class StillMeStressTester:
    """Hệ thống stress test và đánh giá StillMe AI"""

    def __init__(self, base_url: str = "http://127.0.0.1:9055"):
        """
        Khởi tạo stress tester

        Args:
            base_url: URL của StillMe AI server
        """
        self.base_url = base_url
        self.evaluator = StillMeEvaluator()
        self.results: List[Dict] = []
        self.session: Optional[aiohttp.ClientSession] = None

        # Tạo thư mục reports nếu chưa có
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)

        # File paths
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results_file = (
            self.reports_dir / f"stress_test_results_{self.timestamp}.json"
        )
        self.csv_file = self.reports_dir / f"stress_test_results_{self.timestamp}.csv"
        self.report_file = self.reports_dir / f"stress_test_report_{self.timestamp}.md"

    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def send_question(self, question: str) -> Dict:
        """
        Gửi câu hỏi đến StillMe AI và nhận câu trả lời

        Args:
            question: Câu hỏi cần gửi

        Returns:
            Dict chứa câu trả lời và thông tin khác
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        start_time = time.time()

        try:
            # Gửi request đến Gradio API
            async with self.session.post(
                f"{self.base_url}/api/predict",
                json={"data": [question, []], "fn_index": 0},  # [message, history]
                timeout=aiohttp.ClientTimeout(total=30),
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    response_time = time.time() - start_time

                    # Parse response từ Gradio
                    if "data" in result and len(result["data"]) > 0:
                        answer = result["data"][0]
                        return {
                            "success": True,
                            "answer": answer,
                            "response_time": response_time,
                            "raw_response": result,
                        }
                    else:
                        return {
                            "success": False,
                            "error": "Invalid response format",
                            "response_time": response_time,
                            "raw_response": result,
                        }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "response_time": time.time() - start_time,
                        "raw_response": None,
                    }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Timeout",
                "response_time": time.time() - start_time,
                "raw_response": None,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time,
                "raw_response": None,
            }

    async def test_single_case(self, test_case: Dict) -> Dict:
        """
        Test một test case

        Args:
            test_case: Test case từ test_cases.py

        Returns:
            Dict chứa kết quả test và đánh giá
        """
        question = test_case["question"]
        print(f"Testing: {question[:50]}{'...' if len(question) > 50 else ''}")

        # Gửi câu hỏi
        response = await self.send_question(question)

        if not response["success"]:
            # Xử lý lỗi
            evaluation = EvaluationResult(
                speed_score=0.0,
                human_like_score=0.0,
                intelligence_score=0.0,
                memory_score=0.0,
                self_reflection_score=0.0,
                safety_score=0.0,
                overall_score=0.0,
                overall_feedback=f"Error: {response['error']}",
                detailed_analysis={"error": response["error"]},
            )
        else:
            # Đánh giá câu trả lời
            evaluation = self.evaluator.evaluate_response(
                question=question,
                answer=response["answer"],
                response_time=response["response_time"],
                expected_keywords=test_case.get("expected_keywords"),
                should_refuse=test_case.get("should_refuse", False),
                should_warn=test_case.get("should_warn", False),
                requires_memory=test_case.get("requires_memory", False),
            )

        # Tạo kết quả tổng hợp
        result = {
            "timestamp": datetime.now().isoformat(),
            "test_case": test_case,
            "response": response,
            "evaluation": asdict(evaluation),
            "success": response["success"],
        }

        self.results.append(result)
        return result

    async def run_stress_test(
        self,
        max_cases: Optional[int] = None,
        categories: Optional[List[str]] = None,
        difficulties: Optional[List[str]] = None,
    ) -> List[Dict]:
        """
        Chạy stress test với các test cases

        Args:
            max_cases: Số lượng test cases tối đa (None = tất cả)
            categories: Danh sách categories cần test (None = tất cả)
            difficulties: Danh sách difficulties cần test (None = tất cả)

        Returns:
            List kết quả test
        """
        print("🚀 Starting StillMe AI Stress Test...")
        print(f"📊 Total test cases available: {len(ALL_TEST_CASES)}")

        # Lọc test cases
        filtered_cases = ALL_TEST_CASES

        if categories:
            filtered_cases = [
                case for case in filtered_cases if case["category"] in categories
            ]

        if difficulties:
            filtered_cases = [
                case for case in filtered_cases if case["difficulty"] in difficulties
            ]

        if max_cases:
            filtered_cases = filtered_cases[:max_cases]

        print(f"🎯 Running {len(filtered_cases)} test cases...")

        # Chạy test cases
        for i, test_case in enumerate(filtered_cases, 1):
            print(f"\n[{i}/{len(filtered_cases)}] ", end="")
            await self.test_single_case(test_case)

            # Nghỉ ngắn giữa các request để tránh overload
            await asyncio.sleep(0.5)

        print(f"\n✅ Completed {len(filtered_cases)} test cases!")
        return self.results

    def save_results(self):
        """Lưu kết quả vào file JSON và CSV"""
        print(f"💾 Saving results to {self.results_file} and {self.csv_file}")

        # Lưu JSON
        with open(self.results_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        # Lưu CSV
        if self.results:
            with open(self.csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Header
                writer.writerow(
                    [
                        "timestamp",
                        "category",
                        "difficulty",
                        "question",
                        "answer",
                        "response_time",
                        "success",
                        "speed_score",
                        "human_like_score",
                        "intelligence_score",
                        "memory_score",
                        "self_reflection_score",
                        "safety_score",
                        "overall_score",
                        "overall_feedback",
                    ]
                )

                # Data
                for result in self.results:
                    writer.writerow(
                        [
                            result["timestamp"],
                            result["test_case"]["category"],
                            result["test_case"]["difficulty"],
                            result["test_case"]["question"],
                            result["response"].get("answer", ""),
                            result["response"].get("response_time", 0),
                            result["success"],
                            result["evaluation"]["speed_score"],
                            result["evaluation"]["human_like_score"],
                            result["evaluation"]["intelligence_score"],
                            result["evaluation"]["memory_score"],
                            result["evaluation"]["self_reflection_score"],
                            result["evaluation"]["safety_score"],
                            result["evaluation"]["overall_score"],
                            result["evaluation"]["overall_feedback"],
                        ]
                    )

    def generate_report(self) -> str:
        """Tạo báo cáo đánh giá tổng thể"""
        if not self.results:
            return "No results to analyze."

        # Tính thống kê
        successful_results = [r for r in self.results if r["success"]]
        failed_results = [r for r in self.results if not r["success"]]

        if not successful_results:
            return "No successful results to analyze."

        # Tính điểm trung bình
        avg_scores = {
            "speed": statistics.mean(
                [r["evaluation"]["speed_score"] for r in successful_results]
            ),
            "human_like": statistics.mean(
                [r["evaluation"]["human_like_score"] for r in successful_results]
            ),
            "intelligence": statistics.mean(
                [r["evaluation"]["intelligence_score"] for r in successful_results]
            ),
            "memory": statistics.mean(
                [r["evaluation"]["memory_score"] for r in successful_results]
            ),
            "self_reflection": statistics.mean(
                [r["evaluation"]["self_reflection_score"] for r in successful_results]
            ),
            "safety": statistics.mean(
                [r["evaluation"]["safety_score"] for r in successful_results]
            ),
            "overall": statistics.mean(
                [r["evaluation"]["overall_score"] for r in successful_results]
            ),
        }

        # Tính thời gian phản hồi
        response_times = [r["response"]["response_time"] for r in successful_results]
        avg_response_time = statistics.mean(response_times)
        median_response_time = statistics.median(response_times)
        p95_response_time = (
            statistics.quantiles(response_times, n=20)[18]
            if len(response_times) > 20
            else max(response_times)
        )

        # Thống kê theo category
        category_stats = {}
        for result in successful_results:
            category = result["test_case"]["category"]
            if category not in category_stats:
                category_stats[category] = []
            category_stats[category].append(result["evaluation"]["overall_score"])

        # Thống kê theo difficulty
        difficulty_stats = {}
        for result in successful_results:
            difficulty = result["test_case"]["difficulty"]
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = []
            difficulty_stats[difficulty].append(result["evaluation"]["overall_score"])

        # Tạo báo cáo
        report = f"""# StillMe AI Stress Test Report
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 📊 Tổng quan
- **Total Test Cases**: {len(self.results)}
- **Successful**: {len(successful_results)} ({len(successful_results)/len(self.results)*100:.1f}%)
- **Failed**: {len(failed_results)} ({len(failed_results)/len(self.results)*100:.1f}%)

## ⚡ Hiệu suất
- **Average Response Time**: {avg_response_time:.2f}s
- **Median Response Time**: {median_response_time:.2f}s
- **P95 Response Time**: {p95_response_time:.2f}s

## 🎯 Điểm đánh giá trung bình
- **Speed Score**: {avg_scores['speed']:.1f}/10
- **Human-like Score**: {avg_scores['human_like']:.1f}/10
- **Intelligence Score**: {avg_scores['intelligence']:.1f}/10
- **Memory Score**: {avg_scores['memory']:.1f}/10
- **Self-reflection Score**: {avg_scores['self_reflection']:.1f}/10
- **Safety Score**: {avg_scores['safety']:.1f}/10
- **Overall Score**: {avg_scores['overall']:.1f}/10

## 📈 Phân tích theo Category
"""

        for category, scores in category_stats.items():
            avg_score = statistics.mean(scores)
            report += f"- **{category}**: {avg_score:.1f}/10 ({len(scores)} cases)\n"

        report += "\n## 📊 Phân tích theo Difficulty\n"
        for difficulty, scores in difficulty_stats.items():
            avg_score = statistics.mean(scores)
            report += f"- **{difficulty}**: {avg_score:.1f}/10 ({len(scores)} cases)\n"

        # Đề xuất cải thiện
        evaluation_results = [
            EvaluationResult(**r["evaluation"]) for r in successful_results
        ]
        suggestions = generate_improvement_suggestions(evaluation_results)

        report += "\n## 🚀 Đề xuất cải thiện\n"
        for suggestion in suggestions:
            report += f"- {suggestion}\n"

        # Top 5 cases tốt nhất và tệ nhất
        sorted_results = sorted(
            successful_results,
            key=lambda x: x["evaluation"]["overall_score"],
            reverse=True,
        )

        report += "\n## 🏆 Top 5 Cases tốt nhất\n"
        for i, result in enumerate(sorted_results[:5], 1):
            report += f"{i}. **{result['test_case']['question'][:50]}...** - Score: {result['evaluation']['overall_score']:.1f}/10\n"

        report += "\n## ⚠️ Top 5 Cases cần cải thiện\n"
        for i, result in enumerate(sorted_results[-5:], 1):
            report += f"{i}. **{result['test_case']['question'][:50]}...** - Score: {result['evaluation']['overall_score']:.1f}/10\n"

        # Lỗi phổ biến
        if failed_results:
            report += "\n## ❌ Lỗi phổ biến\n"
            error_counts = {}
            for result in failed_results:
                error = result["response"].get("error", "Unknown")
                error_counts[error] = error_counts.get(error, 0) + 1

            for error, count in sorted(
                error_counts.items(), key=lambda x: x[1], reverse=True
            ):
                report += f"- **{error}**: {count} cases\n"

        report += "\n---\n*Report generated by StillMe AI Stress Test System*"

        return report

    def save_report(self):
        """Lưu báo cáo vào file"""
        report = self.generate_report()
        with open(self.report_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"📄 Report saved to {self.report_file}")


async def main():
    """Hàm main để chạy stress test"""
    print("🧠 StillMe AI Stress Test & Evaluation System")
    print("=" * 50)

    # Hiển thị thống kê test cases
    stats = get_test_statistics()
    print(f"📊 Available test cases: {stats['total_cases']}")
    print(f"🛡️ Safety cases: {stats['safety_cases']}")
    print(f"⚠️ Warning cases: {stats['warning_cases']}")
    print(f"🧠 Memory cases: {stats['memory_cases']}")

    # Chạy stress test
    async with StillMeStressTester() as tester:
        # Có thể tùy chỉnh các tham số:
        # - max_cases: Số lượng test cases tối đa
        # - categories: Danh sách categories cần test
        # - difficulties: Danh sách difficulties cần test

        await tester.run_stress_test(
            max_cases=50,  # Test 50 cases đầu tiên
            # categories=["programming_python", "safety_ethics"],  # Chỉ test Python và Safety
            # difficulties=["easy", "medium"]  # Chỉ test easy và medium
        )

        # Lưu kết quả
        tester.save_results()
        tester.save_report()

        # Hiển thị báo cáo tóm tắt
        print("\n" + "=" * 50)
        print("📄 STRESS TEST SUMMARY")
        print("=" * 50)

        if tester.results:
            successful = [r for r in tester.results if r["success"]]
            if successful:
                avg_overall = statistics.mean(
                    [r["evaluation"]["overall_score"] for r in successful]
                )
                avg_time = statistics.mean(
                    [r["response"]["response_time"] for r in successful]
                )

                print(
                    f"✅ Success Rate: {len(successful)}/{len(tester.results)} ({len(successful)/len(tester.results)*100:.1f}%)"
                )
                print(f"🎯 Average Overall Score: {avg_overall:.1f}/10")
                print(f"⚡ Average Response Time: {avg_time:.2f}s")

                # Hiển thị đề xuất cải thiện
                evaluation_results = [
                    EvaluationResult(**r["evaluation"]) for r in successful
                ]
                suggestions = generate_improvement_suggestions(evaluation_results)

                print("\n🚀 Key Improvement Suggestions:")
                for suggestion in suggestions[:3]:  # Hiển thị 3 đề xuất đầu tiên
                    print(f"  {suggestion}")
            else:
                print("❌ No successful results to analyze")
        else:
            print("❌ No results generated")


if __name__ == "__main__":
    # Chạy stress test
    asyncio.run(main())
