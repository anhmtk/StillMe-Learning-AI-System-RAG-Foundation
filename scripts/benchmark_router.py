#!/usr/bin/env python3
"""
AI Router Benchmark Script

This script benchmarks the AI router performance and accuracy,
providing detailed metrics and comparisons.

Usage:
    python scripts/benchmark_router.py --performance
    python scripts/benchmark_router.py --accuracy
    python scripts/benchmark_router.py --full
    python scripts/benchmark_router.py --compare-configs
"""

import argparse
import json
import os
import statistics
import sys
import time

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stillme_core'))

from modules.api_provider_manager import ComplexityAnalyzer, UnifiedAPIManager


class RouterBenchmark:
    def __init__(self):
        self.manager = UnifiedAPIManager()
        self.analyzer = ComplexityAnalyzer()
        self.benchmark_results = {}

    def benchmark_performance(self, num_iterations: int = 1000) -> dict:
        """Benchmark router performance"""
        print(f"🏃‍♂️ Performance Benchmark ({num_iterations} iterations)")
        print("=" * 60)

        # Test prompts of different complexities
        test_prompts = {
            'simple': [
                "chào bạn",
                "bạn khỏe không?",
                "2+2 bằng mấy?",
                "thủ đô Việt Nam là gì?",
                "hello",
                "how are you?",
                "tên bạn là gì?",
                "bạn có thể giúp gì?",
                "cảm ơn",
                "tạm biệt"
            ],
            'coding': [
                "viết code Python tính giai thừa",
                "lập trình JavaScript",
                "debug lỗi",
                "tạo function",
                "viết code",
                "tối ưu thuật toán",
                "sửa lỗi code",
                "tạo class Python",
                "nếu tôi muốn học lập trình thì nên bắt đầu từ đâu?",
                "tối ưu hóa performance của database query"
            ],
            'complex': [
                "Giải thích định lý bất toàn của Gödel",
                "Phân tích mối quan hệ giữa triết học và khoa học",
                "So sánh các phương pháp học máy",
                "Tại sao các hệ thống phức tạp lại tự tổ chức?",
                "Ý nghĩa của cuộc sống là gì?",
                "Bản chất của thực tại là gì?",
                "Tác động của AI đến xã hội",
                "Phân tích xu hướng phát triển công nghệ",
                "giả sử tôi có một bài toán phức tạp, làm thế nào để giải quyết nó?",
                "trong trường hợp nào thì nên sử dụng AI?"
            ]
        }

        results = {
            'overall': {'times': [], 'scores': []},
            'by_category': {},
            'statistics': {}
        }

        # Benchmark each category
        for category, prompts in test_prompts.items():
            print(f"\n📊 Benchmarking {category} prompts...")

            category_times = []
            category_scores = []

            for i in range(num_iterations):
                prompt = prompts[i % len(prompts)]

                # Measure analysis time
                start_time = time.time()
                score, _ = self.analyzer.analyze_complexity(prompt)
                end_time = time.time()

                analysis_time = end_time - start_time
                category_times.append(analysis_time)
                category_scores.append(score)

                # Add to overall results
                results['overall']['times'].append(analysis_time)
                results['overall']['scores'].append(score)

                if (i + 1) % 100 == 0:
                    print(f"  Completed {i + 1}/{num_iterations} iterations...")

            # Calculate category statistics
            results['by_category'][category] = {
                'times': category_times,
                'scores': category_scores,
                'avg_time': statistics.mean(category_times),
                'min_time': min(category_times),
                'max_time': max(category_times),
                'std_time': statistics.stdev(category_times) if len(category_times) > 1 else 0,
                'avg_score': statistics.mean(category_scores),
                'min_score': min(category_scores),
                'max_score': max(category_scores),
                'std_score': statistics.stdev(category_scores) if len(category_scores) > 1 else 0
            }

        # Calculate overall statistics
        results['statistics'] = {
            'avg_time': statistics.mean(results['overall']['times']),
            'min_time': min(results['overall']['times']),
            'max_time': max(results['overall']['times']),
            'std_time': statistics.stdev(results['overall']['times']),
            'avg_score': statistics.mean(results['overall']['scores']),
            'min_score': min(results['overall']['scores']),
            'max_score': max(results['overall']['scores']),
            'std_score': statistics.stdev(results['overall']['scores']),
            'total_iterations': num_iterations
        }

        # Print results
        print("\n📊 Performance Benchmark Results")
        print("=" * 60)

        print("Overall Statistics:")
        print(f"  Average analysis time: {results['statistics']['avg_time']*1000:.2f}ms")
        print(f"  Min analysis time: {results['statistics']['min_time']*1000:.2f}ms")
        print(f"  Max analysis time: {results['statistics']['max_time']*1000:.2f}ms")
        print(f"  Standard deviation: {results['statistics']['std_time']*1000:.2f}ms")
        print(f"  Average complexity score: {results['statistics']['avg_score']:.3f}")

        print("\nBy Category:")
        for category, stats in results['by_category'].items():
            print(f"  {category.capitalize()}:")
            print(f"    Avg time: {stats['avg_time']*1000:.2f}ms")
            print(f"    Avg score: {stats['avg_score']:.3f}")
            print(f"    Score range: {stats['min_score']:.3f} - {stats['max_score']:.3f}")

        # Performance grade
        avg_time = results['statistics']['avg_time']
        if avg_time < 0.001:  # < 1ms
            grade = "A+ (Excellent)"
        elif avg_time < 0.005:  # < 5ms
            grade = "A (Very Good)"
        elif avg_time < 0.01:  # < 10ms
            grade = "B (Good)"
        elif avg_time < 0.05:  # < 50ms
            grade = "C (Acceptable)"
        else:
            grade = "D (Needs Improvement)"

        print(f"\n🎯 Performance Grade: {grade}")

        return results

    def benchmark_accuracy(self) -> dict:
        """Benchmark router accuracy"""
        print("\n🎯 Accuracy Benchmark")
        print("=" * 60)

        # Test cases with expected routing
        test_cases = [
            # Simple prompts
            ("chào bạn", "gemma2:2b", 0.0),
            ("bạn khỏe không?", "gemma2:2b", 0.0),
            ("2+2 bằng mấy?", "gemma2:2b", 0.0),
            ("thủ đô Việt Nam là gì?", "gemma2:2b", 0.0),
            ("hello", "gemma2:2b", 0.0),
            ("how are you?", "gemma2:2b", 0.0),
            ("tên bạn là gì?", "gemma2:2b", 0.0),
            ("bạn có thể giúp gì?", "gemma2:2b", 0.0),
            ("cảm ơn", "gemma2:2b", 0.0),
            ("tạm biệt", "gemma2:2b", 0.0),

            # Coding prompts
            ("viết code Python", "deepseek-coder:6.7b", 0.3),
            ("lập trình JavaScript", "deepseek-coder:6.7b", 0.3),
            ("debug lỗi", "deepseek-coder:6.7b", 0.3),
            ("tạo function", "deepseek-coder:6.7b", 0.3),
            ("viết code", "deepseek-coder:6.7b", 0.3),
            ("tối ưu thuật toán", "deepseek-coder:6.7b", 0.3),
            ("sửa lỗi code", "deepseek-coder:6.7b", 0.3),
            ("tạo class Python", "deepseek-coder:6.7b", 0.3),
            ("viết code Python tính giai thừa", "deepseek-coder:6.7b", 0.3),
            ("nếu tôi muốn học lập trình thì nên bắt đầu từ đâu?", "deepseek-coder:6.7b", 0.3),
            ("tối ưu hóa performance của database query", "deepseek-coder:6.7b", 0.3),
            ("sửa lỗi trong thuật toán sắp xếp", "deepseek-coder:6.7b", 0.3),
            ("tạo function JavaScript để validate email", "deepseek-coder:6.7b", 0.3),
            ("debug lỗi trong code Python", "deepseek-coder:6.7b", 0.3),
            ("tối ưu hóa memory usage", "deepseek-coder:6.7b", 0.3),

            # Complex prompts
            ("Giải thích định lý bất toàn của Gödel", "deepseek-chat", 0.7),
            ("Phân tích mối quan hệ giữa triết học và khoa học", "deepseek-chat", 0.7),
            ("So sánh các phương pháp học máy", "deepseek-chat", 0.7),
            ("Tại sao các hệ thống phức tạp lại tự tổ chức?", "deepseek-chat", 0.7),
            ("Ý nghĩa của cuộc sống là gì?", "deepseek-chat", 0.7),
            ("Bản chất của thực tại là gì?", "deepseek-chat", 0.7),
            ("Tác động của AI đến xã hội", "deepseek-chat", 0.7),
            ("Phân tích xu hướng phát triển công nghệ", "deepseek-chat", 0.7),
            ("giả sử tôi có một bài toán phức tạp, làm thế nào để giải quyết nó?", "deepseek-chat", 0.7),
            ("trong trường hợp nào thì nên sử dụng AI?", "deepseek-chat", 0.7),
            ("Giải thích định lý bất toàn của Gödel và tác động của nó đến toán học hiện đại", "deepseek-chat", 0.7),
            ("Phân tích mối quan hệ giữa triết học và khoa học trong việc hiểu bản chất của thực tại", "deepseek-chat", 0.7),
            ("So sánh và đánh giá các phương pháp học máy khác nhau trong việc xử lý ngôn ngữ tự nhiên", "deepseek-chat", 0.7),
            ("Tại sao các hệ thống phức tạp lại có xu hướng tự tổ chức và phát triển theo quy luật nào?", "deepseek-chat", 0.7),
            ("Phân tích tác động của trí tuệ nhân tạo đến xã hội và tương lai của nhân loại", "deepseek-chat", 0.7),
        ]

        results = {
            'simple': {'correct': 0, 'total': 0, 'accuracy': 0.0, 'details': []},
            'coding': {'correct': 0, 'total': 0, 'accuracy': 0.0, 'details': []},
            'complex': {'correct': 0, 'total': 0, 'accuracy': 0.0, 'details': []},
            'overall': {'correct': 0, 'total': 0, 'accuracy': 0.0}
        }

        # Categorize test cases
        simple_cases = test_cases[:10]
        coding_cases = test_cases[10:25]
        complex_cases = test_cases[25:]

        # Test each category
        for category, cases in [('simple', simple_cases), ('coding', coding_cases), ('complex', complex_cases)]:
            correct = 0
            total = len(cases)
            details = []

            print(f"\n{category.capitalize()} prompts:")
            for prompt, expected_model, expected_score in cases:
                # Get actual complexity score
                actual_score, _ = self.analyzer.analyze_complexity(prompt)

                # Determine expected model based on score
                if actual_score < 0.4:
                    actual_model = "gemma2:2b"
                elif actual_score < 0.7:
                    actual_model = "deepseek-coder:6.7b"
                else:
                    actual_model = "deepseek-chat"

                # Check if routing is correct
                is_correct = actual_model == expected_model
                if is_correct:
                    correct += 1

                details.append({
                    'prompt': prompt,
                    'expected_model': expected_model,
                    'actual_model': actual_model,
                    'expected_score': expected_score,
                    'actual_score': actual_score,
                    'correct': is_correct
                })

                status = "✅" if is_correct else "❌"
                print(f"  {status} {prompt[:50]}... → {actual_model} (score: {actual_score:.3f})")

                if not is_correct:
                    print(f"    Expected: {expected_model}, Got: {actual_model}")

            accuracy = correct / total
            results[category]['correct'] = correct
            results[category]['total'] = total
            results[category]['accuracy'] = accuracy
            results[category]['details'] = details

            print(f"  📊 {category} accuracy: {accuracy:.1%} ({correct}/{total})")

        # Overall accuracy
        total_correct = sum(results[cat]['correct'] for cat in ['simple', 'coding', 'complex'])
        total_tests = sum(results[cat]['total'] for cat in ['simple', 'coding', 'complex'])
        overall_accuracy = total_correct / total_tests

        results['overall']['correct'] = total_correct
        results['overall']['total'] = total_tests
        results['overall']['accuracy'] = overall_accuracy

        print(f"\n🎯 Overall accuracy: {overall_accuracy:.1%}")

        # Accuracy grade
        if overall_accuracy >= 0.9:
            grade = "A+ (Excellent)"
        elif overall_accuracy >= 0.8:
            grade = "A (Very Good)"
        elif overall_accuracy >= 0.7:
            grade = "B (Good)"
        elif overall_accuracy >= 0.6:
            grade = "C (Acceptable)"
        else:
            grade = "D (Needs Improvement)"

        print(f"🎯 Accuracy Grade: {grade}")

        return results

    def benchmark_fallback(self) -> dict:
        """Benchmark fallback mechanism"""
        print("\n🔄 Fallback Benchmark")
        print("=" * 60)

        # Test cases for fallback detection
        test_cases = [
            # Negative feedback (should trigger fallback)
            ("sai rồi", True),
            ("không đúng", True),
            ("???", True),
            ("không đúng ý mình", True),
            ("chưa chính xác", True),
            ("thiếu thông tin", True),
            ("không hiểu", True),
            ("??", True),
            ("sai", True),
            ("không đúng ý", True),
            ("chưa đúng", True),
            ("thiếu", True),
            ("không rõ", True),
            ("mơ hồ", True),
            ("không chính xác", True),

            # Positive feedback (should NOT trigger fallback)
            ("đúng rồi", False),
            ("ok", False),
            ("cảm ơn", False),
            ("tốt lắm", False),
            ("tuyệt vời", False),
            ("cảm ơn bạn", False),
            ("rất hay", False),
            ("chính xác", False),
            ("đúng ý", False),
            ("tốt", False),
            ("hay", False),
            ("được", False),
            ("ổn", False),
            ("tốt rồi", False),
            ("cảm ơn nhiều", False),
        ]

        results = {
            'negative_feedback': {'correct': 0, 'total': 0, 'accuracy': 0.0},
            'positive_feedback': {'correct': 0, 'total': 0, 'accuracy': 0.0},
            'overall': {'correct': 0, 'total': 0, 'accuracy': 0.0}
        }

        # Test negative feedback
        negative_cases = [case for case in test_cases if case[1]]
        positive_cases = [case for case in test_cases if not case[1]]

        print("Testing negative feedback detection:")
        for feedback, should_trigger in negative_cases:
            actual_trigger = self.analyzer.should_trigger_fallback(feedback, "original prompt", "gemma2:2b")
            is_correct = actual_trigger == should_trigger

            if is_correct:
                results['negative_feedback']['correct'] += 1

            results['negative_feedback']['total'] += 1

            status = "✅" if is_correct else "❌"
            print(f"  {status} '{feedback}' → {actual_trigger} (expected: {should_trigger})")

        print("\nTesting positive feedback detection:")
        for feedback, should_trigger in positive_cases:
            actual_trigger = self.analyzer.should_trigger_fallback(feedback, "original prompt", "gemma2:2b")
            is_correct = actual_trigger == should_trigger

            if is_correct:
                results['positive_feedback']['correct'] += 1

            results['positive_feedback']['total'] += 1

            status = "✅" if is_correct else "❌"
            print(f"  {status} '{feedback}' → {actual_trigger} (expected: {should_trigger})")

        # Calculate accuracies
        results['negative_feedback']['accuracy'] = results['negative_feedback']['correct'] / results['negative_feedback']['total']
        results['positive_feedback']['accuracy'] = results['positive_feedback']['correct'] / results['positive_feedback']['total']

        # Overall accuracy
        total_correct = results['negative_feedback']['correct'] + results['positive_feedback']['correct']
        total_tests = results['negative_feedback']['total'] + results['positive_feedback']['total']
        overall_accuracy = total_correct / total_tests

        results['overall']['correct'] = total_correct
        results['overall']['total'] = total_tests
        results['overall']['accuracy'] = overall_accuracy

        print("\n📊 Fallback Benchmark Results:")
        print(f"  Negative feedback accuracy: {results['negative_feedback']['accuracy']:.1%}")
        print(f"  Positive feedback accuracy: {results['positive_feedback']['accuracy']:.1%}")
        print(f"  Overall accuracy: {overall_accuracy:.1%}")

        # Fallback grade
        if overall_accuracy >= 0.95:
            grade = "A+ (Excellent)"
        elif overall_accuracy >= 0.9:
            grade = "A (Very Good)"
        elif overall_accuracy >= 0.8:
            grade = "B (Good)"
        elif overall_accuracy >= 0.7:
            grade = "C (Acceptable)"
        else:
            grade = "D (Needs Improvement)"

        print(f"🎯 Fallback Grade: {grade}")

        return results

    def run_full_benchmark(self, num_iterations: int = 1000) -> dict:
        """Run full benchmark suite"""
        print("🔍 AI Router Full Benchmark")
        print("=" * 80)

        start_time = time.time()

        # Run all benchmarks
        performance_results = self.benchmark_performance(num_iterations)
        accuracy_results = self.benchmark_accuracy()
        fallback_results = self.benchmark_fallback()

        end_time = time.time()

        # Compile overall results
        overall_results = {
            'performance': performance_results,
            'accuracy': accuracy_results,
            'fallback': fallback_results,
            'total_time': end_time - start_time,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        # Print summary
        print("\n📊 Full Benchmark Summary")
        print("=" * 60)
        print(f"Performance Grade: {self._get_performance_grade(performance_results['statistics']['avg_time'])}")
        print(f"Accuracy Grade: {self._get_accuracy_grade(accuracy_results['overall']['accuracy'])}")
        print(f"Fallback Grade: {self._get_fallback_grade(fallback_results['overall']['accuracy'])}")
        print(f"Total benchmark time: {overall_results['total_time']:.2f}s")

        return overall_results

    def _get_performance_grade(self, avg_time: float) -> str:
        """Get performance grade based on average time"""
        if avg_time < 0.001:  # < 1ms
            return "A+ (Excellent)"
        elif avg_time < 0.005:  # < 5ms
            return "A (Very Good)"
        elif avg_time < 0.01:  # < 10ms
            return "B (Good)"
        elif avg_time < 0.05:  # < 50ms
            return "C (Acceptable)"
        else:
            return "D (Needs Improvement)"

    def _get_accuracy_grade(self, accuracy: float) -> str:
        """Get accuracy grade based on accuracy percentage"""
        if accuracy >= 0.9:
            return "A+ (Excellent)"
        elif accuracy >= 0.8:
            return "A (Very Good)"
        elif accuracy >= 0.7:
            return "B (Good)"
        elif accuracy >= 0.6:
            return "C (Acceptable)"
        else:
            return "D (Needs Improvement)"

    def _get_fallback_grade(self, accuracy: float) -> str:
        """Get fallback grade based on accuracy percentage"""
        if accuracy >= 0.95:
            return "A+ (Excellent)"
        elif accuracy >= 0.9:
            return "A (Very Good)"
        elif accuracy >= 0.8:
            return "B (Good)"
        elif accuracy >= 0.7:
            return "C (Acceptable)"
        else:
            return "D (Needs Improvement)"

    def export_results(self, results: dict, filename: str):
        """Export benchmark results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"✅ Benchmark results exported to {filename}")

def main():
    parser = argparse.ArgumentParser(description='AI Router Benchmark Script')
    parser.add_argument('--performance', action='store_true', help='Run performance benchmark')
    parser.add_argument('--accuracy', action='store_true', help='Run accuracy benchmark')
    parser.add_argument('--fallback', action='store_true', help='Run fallback benchmark')
    parser.add_argument('--full', action='store_true', help='Run full benchmark suite')
    parser.add_argument('--iterations', type=int, default=1000, help='Number of iterations for performance benchmark')
    parser.add_argument('--export', type=str, help='Export results to JSON file')

    args = parser.parse_args()

    benchmark = RouterBenchmark()

    if args.performance:
        results = benchmark.benchmark_performance(args.iterations)
    elif args.accuracy:
        results = benchmark.benchmark_accuracy()
    elif args.fallback:
        results = benchmark.benchmark_fallback()
    elif args.full:
        results = benchmark.run_full_benchmark(args.iterations)
    else:
        print("Please specify --performance, --accuracy, --fallback, or --full")
        print("Use --help for more information")
        return

    if args.export:
        benchmark.export_results(results, args.export)

if __name__ == "__main__":
    main()
