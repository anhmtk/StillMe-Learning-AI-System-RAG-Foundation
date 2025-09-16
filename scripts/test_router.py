#!/usr/bin/env python3
"""
AI Router Test Script

This script provides comprehensive testing for the AI router,
including unit tests, integration tests, and performance tests.

Usage:
    python scripts/test_router.py --unit
    python scripts/test_router.py --integration
    python scripts/test_router.py --performance
    python scripts/test_router.py --all
"""

import os
import sys
import argparse
import time
import unittest
from typing import Dict, List, Tuple, Optional

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stillme_core'))

from modules.api_provider_manager import UnifiedAPIManager, ComplexityAnalyzer

class TestComplexityAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = ComplexityAnalyzer()
    
    def test_simple_prompts(self):
        """Test that simple prompts get low complexity scores"""
        simple_prompts = [
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
        ]
        
        for prompt in simple_prompts:
            with self.subTest(prompt=prompt):
                score, _ = self.analyzer.analyze_complexity(prompt)
                self.assertLess(score, 0.4, f"Simple prompt '{prompt}' got high complexity: {score}")
    
    def test_coding_prompts(self):
        """Test that coding prompts get medium complexity scores"""
        coding_prompts = [
            "viết code Python",
            "lập trình JavaScript",
            "debug lỗi",
            "tạo function",
            "viết code",
            "tối ưu thuật toán",
            "sửa lỗi code",
            "tạo class Python",
            "viết code Python tính giai thừa",
            "nếu tôi muốn học lập trình thì nên bắt đầu từ đâu?",
            "tối ưu hóa performance của database query",
            "sửa lỗi trong thuật toán sắp xếp",
            "tạo function JavaScript để validate email",
            "debug lỗi trong code Python",
            "tối ưu hóa memory usage"
        ]
        
        for prompt in coding_prompts:
            with self.subTest(prompt=prompt):
                score, _ = self.analyzer.analyze_complexity(prompt)
                self.assertGreaterEqual(score, 0.3, f"Coding prompt '{prompt}' got too low complexity: {score}")
                self.assertLess(score, 0.7, f"Coding prompt '{prompt}' got too high complexity: {score}")
    
    def test_complex_prompts(self):
        """Test that complex prompts get high complexity scores"""
        complex_prompts = [
            "Giải thích định lý bất toàn của Gödel",
            "Phân tích mối quan hệ giữa triết học và khoa học",
            "So sánh các phương pháp học máy",
            "Tại sao các hệ thống phức tạp lại tự tổ chức?",
            "Ý nghĩa của cuộc sống là gì?",
            "Bản chất của thực tại là gì?",
            "Tác động của AI đến xã hội",
            "Phân tích xu hướng phát triển công nghệ",
            "giả sử tôi có một bài toán phức tạp, làm thế nào để giải quyết nó?",
            "trong trường hợp nào thì nên sử dụng AI?",
            "Giải thích định lý bất toàn của Gödel và tác động của nó đến toán học hiện đại",
            "Phân tích mối quan hệ giữa triết học và khoa học trong việc hiểu bản chất của thực tại",
            "So sánh và đánh giá các phương pháp học máy khác nhau trong việc xử lý ngôn ngữ tự nhiên",
            "Tại sao các hệ thống phức tạp lại có xu hướng tự tổ chức và phát triển theo quy luật nào?",
            "Phân tích tác động của trí tuệ nhân tạo đến xã hội và tương lai của nhân loại"
        ]
        
        for prompt in complex_prompts:
            with self.subTest(prompt=prompt):
                score, _ = self.analyzer.analyze_complexity(prompt)
                self.assertGreater(score, 0.7, f"Complex prompt '{prompt}' got low complexity: {score}")
    
    def test_fallback_detection(self):
        """Test fallback mechanism detection"""
        # Test cases that should trigger fallback
        fallback_triggers = [
            "sai rồi",
            "không đúng",
            "???",
            "không đúng ý mình",
            "chưa chính xác",
            "thiếu thông tin",
            "không hiểu",
            "??",
            "sai",
            "không đúng ý",
            "chưa đúng",
            "thiếu",
            "không rõ",
            "mơ hồ",
            "không chính xác"
        ]
        
        for feedback in fallback_triggers:
            with self.subTest(feedback=feedback):
                should_fallback = self.analyzer.should_trigger_fallback(feedback, "original prompt", "gemma2:2b")
                self.assertTrue(should_fallback, f"Negative feedback '{feedback}' should trigger fallback")
        
        # Test cases that should NOT trigger fallback
        no_fallback_triggers = [
            "đúng rồi",
            "ok",
            "cảm ơn",
            "tốt lắm",
            "tuyệt vời",
            "cảm ơn bạn",
            "rất hay",
            "chính xác",
            "đúng ý",
            "tốt",
            "hay",
            "được",
            "ổn",
            "tốt rồi",
            "cảm ơn nhiều"
        ]
        
        for feedback in no_fallback_triggers:
            with self.subTest(feedback=feedback):
                should_fallback = self.analyzer.should_trigger_fallback(feedback, "original prompt", "gemma2:2b")
                self.assertFalse(should_fallback, f"Positive feedback '{feedback}' should not trigger fallback")
    
    def test_performance(self):
        """Test that complexity analysis is fast"""
        start_time = time.time()
        for _ in range(100):
            self.analyzer.analyze_complexity("This is a simple test prompt to check performance.")
        end_time = time.time()
        
        elapsed_ms = (end_time - start_time) * 1000 / 100
        self.assertLess(elapsed_ms, 5, f"Average analysis time {elapsed_ms:.2f}ms, expected < 5ms")
    
    def test_edge_cases(self):
        """Test edge cases"""
        # Empty prompt
        score, _ = self.analyzer.analyze_complexity("")
        self.assertEqual(score, 0.0, "Empty prompt should have complexity 0")
        
        # Very long prompt
        long_prompt = "a " * 1000
        score, _ = self.analyzer.analyze_complexity(long_prompt)
        self.assertGreater(score, 0.0, "Very long prompt should have some complexity")
        
        # Single word
        score, _ = self.analyzer.analyze_complexity("hello")
        self.assertLess(score, 0.4, "Single word should be simple")
        
        # Special characters
        score, _ = self.analyzer.analyze_complexity("!@#$%^&*()")
        self.assertLess(score, 0.4, "Special characters should be simple")

class TestUnifiedAPIManager(unittest.TestCase):
    def setUp(self):
        # Mock the API calls to prevent actual network requests
        self.patcher_ollama = unittest.mock.patch.object(UnifiedAPIManager, 'call_ollama_api', return_value="Mock Ollama Response")
        self.patcher_deepseek = unittest.mock.patch.object(UnifiedAPIManager, 'call_deepseek_api', return_value="Mock DeepSeek Response")
        self.mock_ollama = self.patcher_ollama.start()
        self.mock_deepseek = self.patcher_deepseek.start()
        self.addCleanup(self.patcher_ollama.stop)
        self.addCleanup(self.patcher_deepseek.stop)
        
        self.manager = UnifiedAPIManager()
    
    def test_simple_routing(self):
        """Test that simple prompts route to gemma2:2b"""
        simple_prompts = [
            "chào bạn",
            "bạn tên gì?",
            "2+2 bằng mấy?",
            "thủ đô Việt Nam là gì?",
            "hello",
            "how are you?",
            "tên bạn là gì?",
            "bạn có thể giúp gì?",
            "cảm ơn",
            "tạm biệt"
        ]
        
        for prompt in simple_prompts:
            with self.subTest(prompt=prompt):
                selected_model = self.manager.choose_model(prompt)
                self.assertEqual(selected_model, "gemma2:2b", f"Prompt '{prompt}' should route to gemma2:2b, got {selected_model}")
    
    def test_coding_routing(self):
        """Test that coding prompts route to deepseek-coder:6.7b"""
        coding_prompts = [
            "viết code Python",
            "lập trình JavaScript",
            "debug lỗi",
            "tạo function",
            "viết code",
            "tối ưu thuật toán",
            "sửa lỗi code",
            "tạo class Python",
            "viết code Python tính giai thừa",
            "nếu tôi muốn học lập trình thì nên bắt đầu từ đâu?",
            "tối ưu hóa performance của database query",
            "sửa lỗi trong thuật toán sắp xếp",
            "tạo function JavaScript để validate email",
            "debug lỗi trong code Python",
            "tối ưu hóa memory usage"
        ]
        
        for prompt in coding_prompts:
            with self.subTest(prompt=prompt):
                selected_model = self.manager.choose_model(prompt)
                self.assertEqual(selected_model, "deepseek-coder:6.7b", f"Prompt '{prompt}' should route to deepseek-coder:6.7b, got {selected_model}")
    
    def test_complex_routing(self):
        """Test that complex prompts route to deepseek-chat"""
        complex_prompts = [
            "Giải thích định lý bất toàn của Gödel",
            "Phân tích mối quan hệ giữa triết học và khoa học",
            "So sánh các phương pháp học máy",
            "Tại sao các hệ thống phức tạp lại tự tổ chức?",
            "Ý nghĩa của cuộc sống là gì?",
            "Bản chất của thực tại là gì?",
            "Tác động của AI đến xã hội",
            "Phân tích xu hướng phát triển công nghệ",
            "giả sử tôi có một bài toán phức tạp, làm thế nào để giải quyết nó?",
            "trong trường hợp nào thì nên sử dụng AI?",
            "Giải thích định lý bất toàn của Gödel và tác động của nó đến toán học hiện đại",
            "Phân tích mối quan hệ giữa triết học và khoa học trong việc hiểu bản chất của thực tại",
            "So sánh và đánh giá các phương pháp học máy khác nhau trong việc xử lý ngôn ngữ tự nhiên",
            "Tại sao các hệ thống phức tạp lại có xu hướng tự tổ chức và phát triển theo quy luật nào?",
            "Phân tích tác động của trí tuệ nhân tạo đến xã hội và tương lai của nhân loại"
        ]
        
        for prompt in complex_prompts:
            with self.subTest(prompt=prompt):
                selected_model = self.manager.choose_model(prompt)
                self.assertEqual(selected_model, "deepseek-chat", f"Prompt '{prompt}' should route to deepseek-chat, got {selected_model}")
    
    def test_model_preferences(self):
        """Test that model preferences are respected"""
        # Test that local models are preferred when available
        self.assertIn("gemma2:2b", self.manager.model_preferences)
        self.assertIn("deepseek-coder:6.7b", self.manager.model_preferences)
        self.assertIn("deepseek-chat", self.manager.model_preferences)
    
    def test_fallback_handling(self):
        """Test fallback mechanism"""
        # Test that fallback is triggered for negative feedback
        fallback_triggered = self.manager.handle_fallback("sai rồi", "original prompt", "gemma2:2b")
        self.assertTrue(fallback_triggered, "Fallback should be triggered for negative feedback")
        
        # Test that fallback is not triggered for positive feedback
        fallback_not_triggered = self.manager.handle_fallback("đúng rồi", "original prompt", "gemma2:2b")
        self.assertFalse(fallback_not_triggered, "Fallback should not be triggered for positive feedback")

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.manager = UnifiedAPIManager()
        self.analyzer = ComplexityAnalyzer()
    
    def test_end_to_end_routing(self):
        """Test end-to-end routing flow"""
        test_cases = [
            ("chào bạn", "gemma2:2b"),
            ("viết code Python", "deepseek-coder:6.7b"),
            ("Giải thích định lý bất toàn của Gödel", "deepseek-chat")
        ]
        
        for prompt, expected_model in test_cases:
            with self.subTest(prompt=prompt):
                # Test complexity analysis
                score, _ = self.analyzer.analyze_complexity(prompt)
                
                # Test model selection
                selected_model = self.manager.choose_model(prompt)
                
                # Verify routing
                self.assertEqual(selected_model, expected_model, f"Prompt '{prompt}' should route to {expected_model}, got {selected_model}")
    
    def test_performance_under_load(self):
        """Test performance under load"""
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
        self.assertLess(avg_time, 0.01, f"Average routing time {avg_time:.4f}s, expected < 0.01s")
    
    def test_consistency(self):
        """Test that routing is consistent"""
        prompt = "viết code Python tính giai thừa"
        
        # Test multiple times
        results = []
        for _ in range(10):
            selected_model = self.manager.choose_model(prompt)
            results.append(selected_model)
        
        # All results should be the same
        self.assertTrue(all(r == results[0] for r in results), f"Routing inconsistent: {results}")

class RouterTestSuite:
    def __init__(self):
        self.test_results = {}
    
    def run_unit_tests(self) -> Dict:
        """Run unit tests"""
        print("🧪 Running Unit Tests")
        print("=" * 40)
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add test cases
        suite.addTests(loader.loadTestsFromTestCase(TestComplexityAnalyzer))
        suite.addTests(loader.loadTestsFromTestCase(TestUnifiedAPIManager))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Compile results
        test_results = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
            'details': {
                'failures': [str(f[1]) for f in result.failures],
                'errors': [str(e[1]) for e in result.errors]
            }
        }
        
        print(f"\n📊 Unit Test Results:")
        print(f"  Tests run: {test_results['tests_run']}")
        print(f"  Failures: {test_results['failures']}")
        print(f"  Errors: {test_results['errors']}")
        print(f"  Success rate: {test_results['success_rate']:.1%}")
        
        return test_results
    
    def run_integration_tests(self) -> Dict:
        """Run integration tests"""
        print("\n🔗 Running Integration Tests")
        print("=" * 40)
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Add test cases
        suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
        
        # Run tests
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Compile results
        test_results = {
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
            'details': {
                'failures': [str(f[1]) for f in result.failures],
                'errors': [str(e[1]) for e in result.errors]
            }
        }
        
        print(f"\n📊 Integration Test Results:")
        print(f"  Tests run: {test_results['tests_run']}")
        print(f"  Failures: {test_results['failures']}")
        print(f"  Errors: {test_results['errors']}")
        print(f"  Success rate: {test_results['success_rate']:.1%}")
        
        return test_results
    
    def run_performance_tests(self) -> Dict:
        """Run performance tests"""
        print("\n⚡ Running Performance Tests")
        print("=" * 40)
        
        analyzer = ComplexityAnalyzer()
        manager = UnifiedAPIManager()
        
        # Test prompts
        test_prompts = [
            "chào bạn",
            "viết code Python tính giai thừa",
            "Giải thích định lý bất toàn của Gödel"
        ]
        
        # Test complexity analysis performance
        print("Testing complexity analysis performance...")
        start_time = time.time()
        for _ in range(1000):
            for prompt in test_prompts:
                analyzer.analyze_complexity(prompt)
        end_time = time.time()
        
        analysis_time = (end_time - start_time) / (1000 * len(test_prompts))
        
        # Test model selection performance
        print("Testing model selection performance...")
        start_time = time.time()
        for _ in range(1000):
            for prompt in test_prompts:
                manager.choose_model(prompt)
        end_time = time.time()
        
        selection_time = (end_time - start_time) / (1000 * len(test_prompts))
        
        # Compile results
        test_results = {
            'complexity_analysis_time': analysis_time,
            'model_selection_time': selection_time,
            'total_time': analysis_time + selection_time,
            'performance_grade': self._get_performance_grade(analysis_time + selection_time)
        }
        
        print(f"\n📊 Performance Test Results:")
        print(f"  Complexity analysis time: {analysis_time*1000:.2f}ms")
        print(f"  Model selection time: {selection_time*1000:.2f}ms")
        print(f"  Total time: {test_results['total_time']*1000:.2f}ms")
        print(f"  Performance grade: {test_results['performance_grade']}")
        
        return test_results
    
    def _get_performance_grade(self, total_time: float) -> str:
        """Get performance grade based on total time"""
        if total_time < 0.001:  # < 1ms
            return "A+ (Excellent)"
        elif total_time < 0.005:  # < 5ms
            return "A (Very Good)"
        elif total_time < 0.01:  # < 10ms
            return "B (Good)"
        elif total_time < 0.05:  # < 50ms
            return "C (Acceptable)"
        else:
            return "D (Needs Improvement)"
    
    def run_all_tests(self) -> Dict:
        """Run all tests"""
        print("🔍 AI Router Full Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all test suites
        unit_results = self.run_unit_tests()
        integration_results = self.run_integration_tests()
        performance_results = self.run_performance_tests()
        
        end_time = time.time()
        
        # Compile overall results
        overall_results = {
            'unit_tests': unit_results,
            'integration_tests': integration_results,
            'performance_tests': performance_results,
            'total_time': end_time - start_time,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Print summary
        print(f"\n📊 Full Test Suite Summary")
        print("=" * 60)
        print(f"Unit tests: {unit_results['success_rate']:.1%} success rate")
        print(f"Integration tests: {integration_results['success_rate']:.1%} success rate")
        print(f"Performance: {performance_results['performance_grade']}")
        print(f"Total test time: {overall_results['total_time']:.2f}s")
        
        # Overall status
        if (unit_results['success_rate'] >= 0.9 and 
            integration_results['success_rate'] >= 0.9 and 
            performance_results['performance_grade'].startswith('A')):
            overall_status = "PASS"
        elif (unit_results['success_rate'] >= 0.8 and 
              integration_results['success_rate'] >= 0.8 and 
              performance_results['performance_grade'].startswith('B')):
            overall_status = "WARN"
        else:
            overall_status = "FAIL"
        
        print(f"\n🎯 Overall Status: {overall_status}")
        
        return overall_results

def main():
    parser = argparse.ArgumentParser(description='AI Router Test Script')
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    test_suite = RouterTestSuite()
    
    if args.unit:
        results = test_suite.run_unit_tests()
    elif args.integration:
        results = test_suite.run_integration_tests()
    elif args.performance:
        results = test_suite.run_performance_tests()
    elif args.all:
        results = test_suite.run_all_tests()
    else:
        print("Please specify --unit, --integration, --performance, or --all")
        print("Use --help for more information")
        return
    
    # Exit with appropriate code
    if 'success_rate' in results:
        if results['success_rate'] >= 0.9:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
    elif 'performance_grade' in results:
        if results['performance_grade'].startswith('A'):
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure
    else:
        sys.exit(0)  # Success

if __name__ == "__main__":
    main()
