"""
Demo Stress Test - Test hệ thống đánh giá mà không cần StillMe server
"""

import asyncio
import time
import json
from pathlib import Path
from test_cases import ALL_TEST_CASES
from evaluator import StillMeEvaluator, EvaluationResult, generate_improvement_suggestions

class DemoStillMeStressTester:
    """Demo stress tester để test hệ thống đánh giá"""
    
    def __init__(self):
        self.evaluator = StillMeEvaluator()
        self.results = []
        
        # Tạo thư mục reports
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)
    
    def simulate_ai_response(self, question: str) -> str:
        """Mô phỏng câu trả lời của AI cho demo"""
        question_lower = question.lower()
        
        # Mô phỏng các loại câu trả lời khác nhau
        if "python là gì" in question_lower:
            return "Python là một ngôn ngữ lập trình phổ biến, dễ học và mạnh mẽ. Nó được sử dụng rộng rãi trong phát triển web, data science, AI và nhiều lĩnh vực khác."
        
        elif "giai thừa" in question_lower:
            return "Để tính giai thừa trong Python, bạn có thể sử dụng hàm math.factorial() hoặc viết hàm đệ quy. Ví dụ: def factorial(n): return 1 if n <= 1 else n * factorial(n-1)"
        
        elif "hack" in question_lower or "bom" in question_lower:
            return "Tôi không thể giúp bạn với các hoạt động bất hợp pháp hoặc nguy hiểm. Hãy tìm kiếm sự giúp đỡ từ các nguồn hợp pháp."
        
        elif "đau đầu" in question_lower or "thuốc" in question_lower:
            return "Tôi không thể tư vấn y tế. Bạn nên tham khảo ý kiến bác sĩ để được chẩn đoán và điều trị phù hợp."
        
        elif "đầu tư" in question_lower or "bitcoin" in question_lower:
            return "Đầu tư luôn có rủi ro. Tôi không thể đưa ra lời khuyên tài chính cụ thể. Bạn nên tham khảo chuyên gia tài chính."
        
        elif "xin chào" in question_lower or "hello" in question_lower:
            return "Xin chào! Tôi là StillMe AI, trợ lý thông minh của bạn. Tôi có thể giúp gì cho bạn?"
        
        elif "tên tôi là" in question_lower:
            return "Chào bạn! Tôi đã ghi nhớ tên của bạn. Bạn cần tôi giúp gì?"
        
        elif "tên tôi là gì" in question_lower:
            return "Bạn đã nói tên của bạn trước đó. Tôi nhớ tên bạn là Minh."
        
        elif "bạn có thể sai không" in question_lower:
            return "Có, tôi có thể sai. Tôi là AI và có những giới hạn. Nếu bạn thấy thông tin không chính xác, hãy cho tôi biết."
        
        elif "javascript" in question_lower:
            return "JavaScript là ngôn ngữ lập trình phổ biến cho web development. Bạn muốn học về phần nào cụ thể? Tôi có thể giúp bạn với DOM manipulation, async programming, hoặc framework như React."
        
        elif "thuật toán" in question_lower:
            return "Thuật toán là tập hợp các bước để giải quyết một vấn đề. Bạn muốn tìm hiểu thuật toán nào? Tôi có thể giúp với sorting, searching, hoặc dynamic programming."
        
        else:
            return "Đây là một câu hỏi thú vị. Tôi sẽ cố gắng trả lời dựa trên kiến thức của mình. Tuy nhiên, nếu bạn cần thông tin chính xác hơn, hãy tham khảo các nguồn chuyên môn."
    
    def simulate_response_time(self, question: str) -> float:
        """Mô phỏng thời gian phản hồi"""
        question_lower = question.lower()
        
        # Câu hỏi đơn giản phản hồi nhanh
        if any(word in question_lower for word in ["xin chào", "hello", "cảm ơn", "tạm biệt"]):
            return 0.5 + (hash(question) % 10) / 10  # 0.5-1.5s
        
        # Câu hỏi phức tạp phản hồi chậm hơn
        elif any(word in question_lower for word in ["thuật toán", "phức tạp", "giải thích"]):
            return 2.0 + (hash(question) % 20) / 10  # 2.0-4.0s
        
        # Câu hỏi bình thường
        else:
            return 1.0 + (hash(question) % 15) / 10  # 1.0-2.5s
    
    async def test_single_case(self, test_case: dict) -> dict:
        """Test một test case"""
        question = test_case["question"]
        print(f"Testing: {question[:50]}{'...' if len(question) > 50 else ''}")
        
        # Mô phỏng delay
        await asyncio.sleep(0.1)
        
        # Mô phỏng câu trả lời
        answer = self.simulate_ai_response(question)
        response_time = self.simulate_response_time(question)
        
        # Đánh giá
        evaluation = self.evaluator.evaluate_response(
            question=question,
            answer=answer,
            response_time=response_time,
            expected_keywords=test_case.get("expected_keywords"),
            should_refuse=test_case.get("should_refuse", False),
            should_warn=test_case.get("should_warn", False),
            requires_memory=test_case.get("requires_memory", False)
        )
        
        result = {
            "timestamp": time.time(),
            "test_case": test_case,
            "response": {
                "success": True,
                "answer": answer,
                "response_time": response_time
            },
            "evaluation": {
                "speed_score": evaluation.speed_score,
                "human_like_score": evaluation.human_like_score,
                "intelligence_score": evaluation.intelligence_score,
                "memory_score": evaluation.memory_score,
                "self_reflection_score": evaluation.self_reflection_score,
                "safety_score": evaluation.safety_score,
                "overall_score": evaluation.overall_score,
                "overall_feedback": evaluation.overall_feedback,
                "detailed_analysis": evaluation.detailed_analysis
            },
            "success": True
        }
        
        self.results.append(result)
        return result
    
    async def run_demo_test(self, max_cases: int = 20):
        """Chạy demo test"""
        print("🚀 Starting Demo Stress Test...")
        print(f"📊 Testing {max_cases} cases...")
        
        test_cases = ALL_TEST_CASES[:max_cases]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[{i}/{len(test_cases)}] ", end="")
            await self.test_single_case(test_case)
        
        print(f"\n✅ Completed {len(test_cases)} test cases!")
        return self.results
    
    def generate_demo_report(self) -> str:
        """Tạo báo cáo demo"""
        if not self.results:
            return "No results to analyze."
        
        successful_results = [r for r in self.results if r["success"]]
        
        if not successful_results:
            return "No successful results to analyze."
        
        # Tính điểm trung bình
        avg_scores = {
            "speed": sum(r["evaluation"]["speed_score"] for r in successful_results) / len(successful_results),
            "human_like": sum(r["evaluation"]["human_like_score"] for r in successful_results) / len(successful_results),
            "intelligence": sum(r["evaluation"]["intelligence_score"] for r in successful_results) / len(successful_results),
            "memory": sum(r["evaluation"]["memory_score"] for r in successful_results) / len(successful_results),
            "self_reflection": sum(r["evaluation"]["self_reflection_score"] for r in successful_results) / len(successful_results),
            "safety": sum(r["evaluation"]["safety_score"] for r in successful_results) / len(successful_results),
            "overall": sum(r["evaluation"]["overall_score"] for r in successful_results) / len(successful_results)
        }
        
        # Tính thời gian phản hồi
        response_times = [r["response"]["response_time"] for r in successful_results]
        avg_response_time = sum(response_times) / len(response_times)
        
        # Tạo báo cáo
        report = f"""# StillMe AI Demo Stress Test Report
Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}

## 📊 Tổng quan
- **Total Test Cases**: {len(self.results)}
- **Successful**: {len(successful_results)} ({len(successful_results)/len(self.results)*100:.1f}%)

## ⚡ Hiệu suất
- **Average Response Time**: {avg_response_time:.2f}s

## 🎯 Điểm đánh giá trung bình
- **Speed Score**: {avg_scores['speed']:.1f}/10
- **Human-like Score**: {avg_scores['human_like']:.1f}/10
- **Intelligence Score**: {avg_scores['intelligence']:.1f}/10
- **Memory Score**: {avg_scores['memory']:.1f}/10
- **Self-reflection Score**: {avg_scores['self_reflection']:.1f}/10
- **Safety Score**: {avg_scores['safety']:.1f}/10
- **Overall Score**: {avg_scores['overall']:.1f}/10

## 🚀 Đề xuất cải thiện
"""
        
        # Đề xuất cải thiện
        evaluation_results = [EvaluationResult(**r["evaluation"]) for r in successful_results]
        suggestions = generate_improvement_suggestions(evaluation_results)
        
        for suggestion in suggestions:
            report += f"- {suggestion}\n"
        
        # Top 3 cases tốt nhất
        sorted_results = sorted(successful_results, key=lambda x: x["evaluation"]["overall_score"], reverse=True)
        
        report += "\n## 🏆 Top 3 Cases tốt nhất\n"
        for i, result in enumerate(sorted_results[:3], 1):
            report += f"{i}. **{result['test_case']['question'][:50]}...** - Score: {result['evaluation']['overall_score']:.1f}/10\n"
        
        report += "\n---\n*Demo Report - Simulated AI Responses*"
        
        return report

async def main():
    """Hàm main cho demo"""
    print("🧠 StillMe AI Demo Stress Test System")
    print("=" * 50)
    
    tester = DemoStillMeStressTester()
    
    # Chạy demo test
    await tester.run_demo_test(max_cases=15)
    
    # Tạo và hiển thị báo cáo
    report = tester.generate_demo_report()
    print("\n" + "=" * 50)
    print("📄 DEMO STRESS TEST REPORT")
    print("=" * 50)
    print(report)
    
    # Lưu báo cáo
    report_file = Path("reports/demo_stress_test_report.md")
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n💾 Report saved to {report_file}")

if __name__ == "__main__":
    asyncio.run(main())
