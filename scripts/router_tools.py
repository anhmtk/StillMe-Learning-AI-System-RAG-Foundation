#!/usr/bin/env python3
"""
AI Router Tools

This script provides various tools for working with the AI router,
including testing, debugging, and utility functions.

Usage:
    python scripts/router_tools.py --test
    python scripts/router_tools.py --debug
    python scripts/router_tools.py --benchmark
    python scripts/router_tools.py --validate
"""

import argparse
import json
import os
import statistics
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stillme_core'))

from modules.api_provider_manager import ComplexityAnalyzer, UnifiedAPIManager


class RouterTools:
    def __init__(self):
        self.manager = UnifiedAPIManager()
        self.analyzer = ComplexityAnalyzer()

    def run_tests(self):
        """Run comprehensive tests"""
        print("🧪 AI Router Comprehensive Tests")
        print("=" * 60)

        test_results = {
            'unit_tests': self._run_unit_tests(),
            'integration_tests': self._run_integration_tests(),
            'performance_tests': self._run_performance_tests(),
            'accuracy_tests': self._run_accuracy_tests()
        }

        # Print summary
        self._print_test_summary(test_results)

        return test_results

    def _run_unit_tests(self):
        """Run unit tests"""
        print("\n🔬 Unit Tests")
        print("-" * 40)

        test_results = {
            'complexity_analysis': self._test_complexity_analysis(),
            'model_selection': self._test_model_selection(),
            'fallback_detection': self._test_fallback_detection(),
            'edge_cases': self._test_edge_cases()
        }

        # Print results
        for test_name, result in test_results.items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {test_name}: {status}")
            if not result['passed']:
                print(f"    Error: {result['error']}")

        return test_results

    def _test_complexity_analysis(self):
        """Test complexity analysis"""
        try:
            # Test simple prompt
            score, _ = self.analyzer.analyze_complexity("chào bạn")
            if score >= 0.4:
                return {'passed': False, 'error': f'Simple prompt got high complexity: {score}'}

            # Test complex prompt
            score, _ = self.analyzer.analyze_complexity("Giải thích định lý bất toàn của Gödel")
            if score < 0.7:
                return {'passed': False, 'error': f'Complex prompt got low complexity: {score}'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _test_model_selection(self):
        """Test model selection"""
        try:
            # Test simple prompt routing
            model = self.manager.choose_model("chào bạn")
            if model != "gemma2:2b":
                return {'passed': False, 'error': f'Simple prompt routed to {model}, expected gemma2:2b'}

            # Test coding prompt routing
            model = self.manager.choose_model("viết code Python")
            if model != "deepseek-coder:6.7b":
                return {'passed': False, 'error': f'Coding prompt routed to {model}, expected deepseek-coder:6.7b'}

            # Test complex prompt routing
            model = self.manager.choose_model("Giải thích định lý bất toàn của Gödel")
            if model != "deepseek-chat":
                return {'passed': False, 'error': f'Complex prompt routed to {model}, expected deepseek-chat'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _test_fallback_detection(self):
        """Test fallback detection"""
        try:
            # Test negative feedback
            should_fallback = self.analyzer.should_trigger_fallback("sai rồi", "original prompt", "gemma2:2b")
            if not should_fallback:
                return {'passed': False, 'error': 'Negative feedback should trigger fallback'}

            # Test positive feedback
            should_fallback = self.analyzer.should_trigger_fallback("đúng rồi", "original prompt", "gemma2:2b")
            if should_fallback:
                return {'passed': False, 'error': 'Positive feedback should not trigger fallback'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _test_edge_cases(self):
        """Test edge cases"""
        try:
            # Test empty prompt
            score, _ = self.analyzer.analyze_complexity("")
            if score != 0.0:
                return {'passed': False, 'error': f'Empty prompt should have complexity 0, got {score}'}

            # Test very long prompt
            long_prompt = "a " * 1000
            score, _ = self.analyzer.analyze_complexity(long_prompt)
            if score <= 0.0:
                return {'passed': False, 'error': f'Very long prompt should have some complexity, got {score}'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _run_integration_tests(self):
        """Run integration tests"""
        print("\n🔗 Integration Tests")
        print("-" * 40)

        test_results = {
            'end_to_end_routing': self._test_end_to_end_routing(),
            'performance_under_load': self._test_performance_under_load(),
            'consistency': self._test_consistency()
        }

        # Print results
        for test_name, result in test_results.items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {test_name}: {status}")
            if not result['passed']:
                print(f"    Error: {result['error']}")

        return test_results

    def _test_end_to_end_routing(self):
        """Test end-to-end routing"""
        try:
            test_cases = [
                ("chào bạn", "gemma2:2b"),
                ("viết code Python", "deepseek-coder:6.7b"),
                ("Giải thích định lý bất toàn của Gödel", "deepseek-chat")
            ]

            for prompt, expected_model in test_cases:
                model = self.manager.choose_model(prompt)
                if model != expected_model:
                    return {'passed': False, 'error': f'Prompt "{prompt}" routed to {model}, expected {expected_model}'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _test_performance_under_load(self):
        """Test performance under load"""
        try:
            test_prompts = [
                "chào bạn",
                "viết code Python",
                "Giải thích định lý bất toàn của Gödel"
            ]

            start_time = time.time()
            for _ in range(100):
                for prompt in test_prompts:
                    self.manager.choose_model(prompt)
            end_time = time.time()

            avg_time = (end_time - start_time) / (100 * len(test_prompts))
            if avg_time > 0.01:  # 10ms
                return {'passed': False, 'error': f'Average routing time {avg_time:.4f}s, expected < 0.01s'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _test_consistency(self):
        """Test consistency"""
        try:
            prompt = "viết code Python tính giai thừa"

            # Test multiple times
            results = []
            for _ in range(10):
                model = self.manager.choose_model(prompt)
                results.append(model)

            # All results should be the same
            if not all(r == results[0] for r in results):
                return {'passed': False, 'error': f'Routing inconsistent: {results}'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _run_performance_tests(self):
        """Run performance tests"""
        print("\n⚡ Performance Tests")
        print("-" * 40)

        test_results = {
            'analysis_speed': self._test_analysis_speed(),
            'memory_usage': self._test_memory_usage(),
            'scalability': self._test_scalability()
        }

        # Print results
        for test_name, result in test_results.items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {test_name}: {status}")
            if not result['passed']:
                print(f"    Error: {result['error']}")

        return test_results

    def _test_analysis_speed(self):
        """Test analysis speed"""
        try:
            start_time = time.time()
            for _ in range(1000):
                self.analyzer.analyze_complexity("Test prompt for speed analysis")
            end_time = time.time()

            avg_time = (end_time - start_time) / 1000
            if avg_time > 0.005:  # 5ms
                return {'passed': False, 'error': f'Average analysis time {avg_time*1000:.2f}ms, expected < 5ms'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _test_memory_usage(self):
        """Test memory usage"""
        try:
            import psutil
            process = psutil.Process()

            # Get initial memory
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Run many analyses
            for _ in range(1000):
                self.analyzer.analyze_complexity("Test prompt for memory analysis")

            # Get final memory
            final_memory = process.memory_info().rss / 1024 / 1024  # MB

            memory_increase = final_memory - initial_memory
            if memory_increase > 100:  # 100MB
                return {'passed': False, 'error': f'Memory increase {memory_increase:.1f}MB, expected < 100MB'}

            return {'passed': True}
        except ImportError:
            return {'passed': True, 'note': 'psutil not available, skipping memory test'}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _test_scalability(self):
        """Test scalability"""
        try:
            # Test with different prompt lengths
            prompt_lengths = [10, 100, 1000, 5000]
            times = []

            for length in prompt_lengths:
                prompt = "a " * length

                start_time = time.time()
                for _ in range(100):
                    self.analyzer.analyze_complexity(prompt)
                end_time = time.time()

                avg_time = (end_time - start_time) / 100
                times.append(avg_time)

            # Check if time increases reasonably with prompt length
            # Time should not increase more than linearly
            for i in range(1, len(times)):
                if times[i] > times[i-1] * 10:  # 10x increase is too much
                    return {'passed': False, 'error': f'Time increase too large: {times[i-1]*1000:.2f}ms -> {times[i]*1000:.2f}ms'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _run_accuracy_tests(self):
        """Run accuracy tests"""
        print("\n🎯 Accuracy Tests")
        print("-" * 40)

        test_results = {
            'simple_prompts': self._test_simple_prompts(),
            'coding_prompts': self._test_coding_prompts(),
            'complex_prompts': self._test_complex_prompts()
        }

        # Print results
        for test_name, result in test_results.items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"  {test_name}: {status}")
            if not result['passed']:
                print(f"    Error: {result['error']}")

        return test_results

    def _test_simple_prompts(self):
        """Test simple prompts"""
        try:
            simple_prompts = [
                "chào bạn",
                "bạn khỏe không?",
                "2+2 bằng mấy?",
                "thủ đô Việt Nam là gì?",
                "hello",
                "how are you?"
            ]

            correct_count = 0
            for prompt in simple_prompts:
                model = self.manager.choose_model(prompt)
                if model == "gemma2:2b":
                    correct_count += 1

            accuracy = correct_count / len(simple_prompts)
            if accuracy < 0.8:  # 80%
                return {'passed': False, 'error': f'Simple prompts accuracy {accuracy:.1%}, expected >= 80%'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _test_coding_prompts(self):
        """Test coding prompts"""
        try:
            coding_prompts = [
                "viết code Python",
                "lập trình JavaScript",
                "debug lỗi",
                "tạo function",
                "viết code",
                "tối ưu thuật toán"
            ]

            correct_count = 0
            for prompt in coding_prompts:
                model = self.manager.choose_model(prompt)
                if model == "deepseek-coder:6.7b":
                    correct_count += 1

            accuracy = correct_count / len(coding_prompts)
            if accuracy < 0.8:  # 80%
                return {'passed': False, 'error': f'Coding prompts accuracy {accuracy:.1%}, expected >= 80%'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _test_complex_prompts(self):
        """Test complex prompts"""
        try:
            complex_prompts = [
                "Giải thích định lý bất toàn của Gödel",
                "Phân tích mối quan hệ giữa triết học và khoa học",
                "So sánh các phương pháp học máy",
                "Tại sao các hệ thống phức tạp lại tự tổ chức?",
                "Ý nghĩa của cuộc sống là gì?",
                "Bản chất của thực tại là gì?"
            ]

            correct_count = 0
            for prompt in complex_prompts:
                model = self.manager.choose_model(prompt)
                if model == "deepseek-chat":
                    correct_count += 1

            accuracy = correct_count / len(complex_prompts)
            if accuracy < 0.8:  # 80%
                return {'passed': False, 'error': f'Complex prompts accuracy {accuracy:.1%}, expected >= 80%'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _print_test_summary(self, test_results: Dict):
        """Print test summary"""
        print("\n📊 Test Summary")
        print("=" * 60)

        total_tests = 0
        passed_tests = 0

        for category, results in test_results.items():
            print(f"\n{category.replace('_', ' ').title()}:")
            for test_name, result in results.items():
                total_tests += 1
                if result['passed']:
                    passed_tests += 1
                    print(f"  ✅ {test_name}")
                else:
                    print(f"  ❌ {test_name}: {result['error']}")

        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        print(f"\n🎯 Overall Success Rate: {success_rate:.1%} ({passed_tests}/{total_tests})")

        if success_rate >= 0.9:
            print("🎉 Excellent! All tests passed.")
        elif success_rate >= 0.8:
            print("✅ Good! Most tests passed.")
        elif success_rate >= 0.7:
            print("⚠️  Warning! Some tests failed.")
        else:
            print("❌ Critical! Many tests failed.")

    def run_debug(self, prompt: str):
        """Run debug analysis on a prompt"""
        print(f"🔍 Debug Analysis: {prompt}")
        print("=" * 60)

        # Analyze complexity
        complexity_score, breakdown = self.analyzer.analyze_complexity(prompt)
        print("🧠 Complexity Analysis:")
        print(f"  Score: {complexity_score:.3f}")
        print(f"  Breakdown: {breakdown}")

        # Select model
        selected_model = self.manager.choose_model(prompt)
        print("\n🎯 Model Selection:")
        print(f"  Selected Model: {selected_model}")

        # Explain routing
        if complexity_score < 0.4:
            routing_reason = "Simple prompt → Local lightweight model (gemma2:2b)"
        elif complexity_score < 0.7:
            routing_reason = "Medium complexity → Local coding model (deepseek-coder:6.7b)"
        else:
            routing_reason = "High complexity → Cloud model (deepseek-chat)"

        print(f"  Routing Logic: {routing_reason}")

        # Check for specific keywords
        prompt_lower = prompt.lower()
        coding_keywords = ["code", "lập trình", "viết", "function", "class", "debug", "tối ưu", "thuật toán"]
        complex_indicators = ["tại sao", "như thế nào", "phân tích", "so sánh", "đánh giá", "giải thích"]

        found_coding = [kw for kw in coding_keywords if kw in prompt_lower]
        found_complex = [ci for ci in complex_indicators if ci in prompt_lower]

        print("\n🔤 Keyword Analysis:")
        if found_coding:
            print(f"  Coding Keywords: {found_coding}")
        if found_complex:
            print(f"  Complex Indicators: {found_complex}")
        if not found_coding and not found_complex:
            print("  No specific keywords found")

        return {
            'prompt': prompt,
            'complexity_score': complexity_score,
            'breakdown': breakdown,
            'selected_model': selected_model,
            'routing_reason': routing_reason,
            'keywords': {
                'coding': found_coding,
                'complex': found_complex
            }
        }

    def run_benchmark(self, num_iterations: int = 1000):
        """Run performance benchmark"""
        print(f"🏃‍♂️ Performance Benchmark ({num_iterations} iterations)")
        print("=" * 60)

        test_prompts = [
            "chào bạn",
            "viết code Python tính giai thừa",
            "Giải thích định lý bất toàn của Gödel"
        ]

        times = []
        scores = []

        print("Running benchmark...")
        for i in range(num_iterations):
            prompt = test_prompts[i % len(test_prompts)]

            start_time = time.time()
            score, _ = self.analyzer.analyze_complexity(prompt)
            end_time = time.time()

            times.append(end_time - start_time)
            scores.append(score)

            if (i + 1) % 100 == 0:
                print(f"  Completed {i + 1}/{num_iterations} iterations...")

        # Calculate statistics
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        std_time = statistics.stdev(times) if len(times) > 1 else 0

        avg_score = statistics.mean(scores)
        min_score = min(scores)
        max_score = max(scores)

        print("\n📊 Benchmark Results:")
        print(f"  Average Analysis Time: {avg_time*1000:.2f}ms")
        print(f"  Min Analysis Time: {min_time*1000:.2f}ms")
        print(f"  Max Analysis Time: {max_time*1000:.2f}ms")
        print(f"  Standard Deviation: {std_time*1000:.2f}ms")
        print(f"  Average Complexity Score: {avg_score:.3f}")
        print(f"  Score Range: {min_score:.3f} - {max_score:.3f}")

        # Performance grade
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

        print(f"  Performance Grade: {grade}")

        return {
            'iterations': num_iterations,
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'std_time': std_time,
            'avg_score': avg_score,
            'min_score': min_score,
            'max_score': max_score,
            'grade': grade
        }

    def run_validation(self):
        """Run validation checks"""
        print("✅ AI Router Validation")
        print("=" * 60)

        validation_results = {
            'configuration': self._validate_configuration(),
            'performance': self._validate_performance(),
            'accuracy': self._validate_accuracy()
        }

        # Print results
        for category, result in validation_results.items():
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"{category.title()}: {status}")
            if not result['passed']:
                print(f"  Error: {result['error']}")

        # Overall status
        all_passed = all(r['passed'] for r in validation_results.values())
        overall_status = "✅ PASS" if all_passed else "❌ FAIL"
        print(f"\n🎯 Overall Validation: {overall_status}")

        return validation_results

    def _validate_configuration(self):
        """Validate configuration"""
        try:
            stats = self.analyzer.get_stats()

            # Check weights
            weights = stats['weights']
            for key, value in weights.items():
                if not (0.0 <= value <= 1.0):
                    return {'passed': False, 'error': f'Invalid weight {key}: {value}'}

            # Check thresholds
            thresholds = stats['thresholds']
            if thresholds['simple'] >= thresholds['medium']:
                return {'passed': False, 'error': f'Invalid threshold order: simple={thresholds["simple"]}, medium={thresholds["medium"]}'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _validate_performance(self):
        """Validate performance"""
        try:
            start_time = time.time()
            for _ in range(100):
                self.analyzer.analyze_complexity("Test prompt for performance validation")
            end_time = time.time()

            avg_time = (end_time - start_time) / 100
            if avg_time > 0.01:  # 10ms
                return {'passed': False, 'error': f'Average analysis time {avg_time*1000:.2f}ms, expected < 10ms'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

    def _validate_accuracy(self):
        """Validate accuracy"""
        try:
            test_cases = [
                ("chào bạn", "gemma2:2b"),
                ("viết code Python", "deepseek-coder:6.7b"),
                ("Giải thích định lý bất toàn của Gödel", "deepseek-chat")
            ]

            correct_count = 0
            for prompt, expected_model in test_cases:
                model = self.manager.choose_model(prompt)
                if model == expected_model:
                    correct_count += 1

            accuracy = correct_count / len(test_cases)
            if accuracy < 0.8:  # 80%
                return {'passed': False, 'error': f'Accuracy {accuracy:.1%}, expected >= 80%'}

            return {'passed': True}
        except Exception as e:
            return {'passed': False, 'error': str(e)}

def main():
    parser = argparse.ArgumentParser(description='AI Router Tools')
    parser.add_argument('--test', action='store_true', help='Run comprehensive tests')
    parser.add_argument('--debug', type=str, help='Debug a specific prompt')
    parser.add_argument('--benchmark', type=int, default=1000, help='Run performance benchmark')
    parser.add_argument('--validate', action='store_true', help='Run validation checks')

    args = parser.parse_args()

    tools = RouterTools()

    if args.test:
        tools.run_tests()
    elif args.debug:
        tools.run_debug(args.debug)
    elif args.benchmark:
        tools.run_benchmark(args.benchmark)
    elif args.validate:
        tools.run_validation()
    else:
        print("Please specify --test, --debug, --benchmark, or --validate")
        print("Use --help for more information")

if __name__ == "__main__":
    main()
