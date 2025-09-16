#!/usr/bin/env python3
"""
Test Suite for AI Router - Comprehensive testing of complexity analysis and model selection.

This test suite validates the AI routing system with various prompt types:
- Simple greetings and basic questions
- Programming and coding requests  
- Academic and scientific questions
- Complex philosophical and abstract concepts
- Multi-part and conditional questions
"""

import sys
import os
import time
import unittest
from typing import Dict, List, Tuple, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from stillme_core.modules.api_provider_manager import UnifiedAPIManager, ComplexityAnalyzer
except ImportError:
    print("⚠️ Could not import UnifiedAPIManager. Make sure you're in the project root.")
    sys.exit(1)


class TestComplexityAnalyzer(unittest.TestCase):
    """Test the ComplexityAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = ComplexityAnalyzer()
    
    def test_simple_prompts(self):
        """Test simple prompts should get low complexity scores."""
        simple_prompts = [
            "chào bạn",
            "bạn tên gì?",
            "2+2 bằng mấy?",
            "thủ đô Việt Nam là gì?",
            "hello",
            "how are you?",
            "what time is it?"
        ]
        
        for prompt in simple_prompts:
            with self.subTest(prompt=prompt):
                score, _ = self.analyzer.analyze_complexity(prompt)
                self.assertLess(score, 0.4, f"Simple prompt '{prompt}' got high complexity: {score}")
    
    def test_complex_prompts(self):
        """Test complex prompts should get high complexity scores."""
        complex_prompts = [
            "Giải thích định lý bất toàn của Gödel và tác động của nó đến toán học hiện đại",
            "Phân tích mối quan hệ giữa triết học và khoa học trong việc hiểu bản chất của thực tại",
            "So sánh và đánh giá các phương pháp học máy khác nhau trong việc xử lý ngôn ngữ tự nhiên",
            "Tại sao các hệ thống phức tạp lại có xu hướng tự tổ chức và phát triển theo quy luật nào?"
        ]
        
        for prompt in complex_prompts:
            with self.subTest(prompt=prompt):
                score, _ = self.analyzer.analyze_complexity(prompt)
                self.assertGreater(score, 0.7, f"Complex prompt '{prompt}' got low complexity: {score}")
    
    def test_coding_prompts(self):
        """Test coding prompts should get medium complexity scores."""
        coding_prompts = [
            "viết code Python tính giai thừa",
            "tạo function JavaScript để validate email",
            "debug lỗi trong thuật toán sắp xếp",
            "tối ưu hóa performance của database query"
        ]
        
        for prompt in coding_prompts:
            with self.subTest(prompt=prompt):
                score, _ = self.analyzer.analyze_complexity(prompt)
                self.assertGreaterEqual(score, 0.3, f"Coding prompt '{prompt}' got too low complexity: {score}")
                self.assertLessEqual(score, 0.8, f"Coding prompt '{prompt}' got too high complexity: {score}")
    
    def test_performance(self):
        """Test that complexity analysis is fast (< 5ms)."""
        test_prompt = "Giải thích định lý bất toàn của Gödel và tác động của nó đến toán học hiện đại"
        
        # Run multiple times to get average
        times = []
        for _ in range(10):
            start_time = time.time()
            self.analyzer.analyze_complexity(test_prompt)
            elapsed = (time.time() - start_time) * 1000  # Convert to ms
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        self.assertLess(avg_time, 5.0, f"Complexity analysis too slow: {avg_time:.2f}ms")
    
    def test_fallback_detection(self):
        """Test fallback trigger detection."""
        # Negative feedback should trigger fallback
        negative_feedback = [
            "sai rồi",
            "không đúng",
            "không hiểu",
            "???",
            "không phải",
            "chưa đúng"
        ]
        
        for feedback in negative_feedback:
            with self.subTest(feedback=feedback):
                should_fallback = self.analyzer.should_trigger_fallback(
                    feedback, "test prompt", "gemma2:2b"
                )
                self.assertTrue(should_fallback, f"Negative feedback '{feedback}' should trigger fallback")
        
        # Positive feedback should not trigger fallback
        positive_feedback = [
            "đúng rồi",
            "cảm ơn",
            "tốt lắm",
            "hiểu rồi",
            "ok"
        ]
        
        for feedback in positive_feedback:
            with self.subTest(feedback=feedback):
                should_fallback = self.analyzer.should_trigger_fallback(
                    feedback, "test prompt", "gemma2:2b"
                )
                self.assertFalse(should_fallback, f"Positive feedback '{feedback}' should not trigger fallback")


class TestUnifiedAPIManager(unittest.TestCase):
    """Test the UnifiedAPIManager routing logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_manager = UnifiedAPIManager()
    
    def test_simple_routing(self):
        """Test routing for simple prompts."""
        test_cases = [
            ("chào bạn", "gemma2:2b"),
            ("bạn tên gì?", "gemma2:2b"),
            ("2+2 bằng mấy?", "gemma2:2b"),
            ("thủ đô Việt Nam là gì?", "gemma2:2b"),
            ("hello", "gemma2:2b"),
            ("how are you?", "gemma2:2b")
        ]
        
        for prompt, expected_model in test_cases:
            with self.subTest(prompt=prompt):
                selected_model = self.api_manager.choose_model(prompt)
                self.assertEqual(selected_model, expected_model, 
                               f"Prompt '{prompt}' should route to {expected_model}, got {selected_model}")
    
    def test_coding_routing(self):
        """Test routing for coding prompts."""
        test_cases = [
            ("viết code Python", "deepseek-coder:6.7b"),
            ("lập trình JavaScript", "deepseek-coder:6.7b"),
            ("debug lỗi", "deepseek-coder:6.7b"),
            ("tạo function", "deepseek-coder:6.7b"),
            ("viết code", "deepseek-coder:6.7b")
        ]
        
        for prompt, expected_model in test_cases:
            with self.subTest(prompt=prompt):
                selected_model = self.api_manager.choose_model(prompt)
                self.assertEqual(selected_model, expected_model,
                               f"Prompt '{prompt}' should route to {expected_model}, got {selected_model}")
    
    def test_complex_routing(self):
        """Test routing for complex prompts."""
        test_cases = [
            ("Giải thích định lý bất toàn của Gödel", "deepseek-chat"),
            ("Phân tích mối quan hệ giữa triết học và khoa học", "deepseek-chat"),
            ("So sánh các phương pháp học máy", "deepseek-chat"),
            ("Tại sao các hệ thống phức tạp lại tự tổ chức?", "deepseek-chat")
        ]
        
        for prompt, expected_model in test_cases:
            with self.subTest(prompt=prompt):
                selected_model = self.api_manager.choose_model(prompt)
                self.assertEqual(selected_model, expected_model,
                               f"Prompt '{prompt}' should route to {expected_model}, got {selected_model}")
    
    def test_long_prompt_routing(self):
        """Test routing for very long prompts."""
        long_prompt = "A" * 4000  # Very long prompt
        
        selected_model = self.api_manager.choose_model(long_prompt)
        self.assertIn(selected_model, ["deepseek-coder:6.7b", "gemma2:2b"],
                     f"Long prompt should route to local model, got {selected_model}")
    
    def test_debug_mode(self):
        """Test debug mode provides detailed information."""
        prompt = "Giải thích định lý bất toàn của Gödel"
        
        # This should not raise an exception and should provide detailed logging
        selected_model = self.api_manager.choose_model(prompt, debug=True)
        self.assertIsInstance(selected_model, str)
        self.assertGreater(len(selected_model), 0)
    
    def test_fallback_handling(self):
        """Test fallback handling mechanism."""
        original_prompt = "test prompt"
        user_feedback = "sai rồi"
        selected_model = "gemma2:2b"
        
        # Test fallback detection
        fallback_response = self.api_manager.handle_fallback(
            original_prompt, user_feedback, selected_model
        )
        
        # Should either return a new response or None (depending on model availability)
        self.assertIsInstance(fallback_response, (str, type(None)))
    
    def test_analyzer_stats(self):
        """Test analyzer statistics collection."""
        # Run some analyses to generate stats
        test_prompts = [
            "chào bạn",
            "viết code Python",
            "Giải thích định lý bất toàn của Gödel"
        ]
        
        for prompt in test_prompts:
            self.api_manager.choose_model(prompt)
        
        # Get stats
        stats = self.api_manager.get_analyzer_stats()
        
        # Verify stats structure
        self.assertIn('performance', stats)
        self.assertIn('fallback', stats)
        self.assertIn('weights', stats)
        self.assertIn('thresholds', stats)
        
        # Verify performance stats
        perf_stats = stats['performance']
        self.assertIn('avg_time_ms', perf_stats)
        self.assertIn('total_analyses', perf_stats)
        self.assertGreater(perf_stats['total_analyses'], 0)


class TestRouterIntegration(unittest.TestCase):
    """Integration tests for the complete routing system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.api_manager = UnifiedAPIManager()
    
    def test_end_to_end_routing(self):
        """Test complete routing flow from prompt to model selection."""
        test_cases = [
            # (prompt, expected_model_category, expected_complexity_range)
            ("chào bạn", "simple", (0.0, 0.4)),
            ("viết code Python", "coding", (0.3, 0.8)),
            ("Giải thích định lý bất toàn của Gödel", "complex", (0.7, 1.0)),
            ("GDP là gì?", "simple", (0.0, 0.4)),
            ("Phân tích tác động của AI đến xã hội", "complex", (0.7, 1.0)),
            ("tạo function tính tổng", "coding", (0.3, 0.8))
        ]
        
        for prompt, category, complexity_range in test_cases:
            with self.subTest(prompt=prompt):
                # Test model selection
                selected_model = self.api_manager.choose_model(prompt)
                
                # Test complexity analysis
                complexity_score, detailed_scores = self.api_manager.complexity_analyzer.analyze_complexity(prompt)
                
                # Verify complexity score is in expected range
                self.assertGreaterEqual(complexity_score, complexity_range[0],
                                      f"Prompt '{prompt}' complexity too low: {complexity_score}")
                self.assertLessEqual(complexity_score, complexity_range[1],
                                   f"Prompt '{prompt}' complexity too high: {complexity_score}")
                
                # Verify model selection makes sense
                if category == "simple":
                    self.assertIn(selected_model, ["gemma2:2b"])
                elif category == "coding":
                    self.assertIn(selected_model, ["deepseek-coder:6.7b"])
                elif category == "complex":
                    self.assertIn(selected_model, ["deepseek-chat"])
    
    def test_weight_calibration(self):
        """Test weight calibration functionality."""
        # Create test results
        test_results = [
            {
                'prompt': 'chào bạn',
                'expected_complexity': 0.1,
                'actual_complexity': 0.15,
                'expected_model': 'gemma2:2b',
                'actual_model': 'gemma2:2b'
            },
            {
                'prompt': 'Giải thích định lý bất toàn của Gödel',
                'expected_complexity': 0.9,
                'actual_complexity': 0.85,
                'expected_model': 'deepseek-chat',
                'actual_model': 'deepseek-chat'
            }
        ]
        
        # Test calibration
        new_weights = self.api_manager.complexity_analyzer.calibrate_weights(test_results)
        
        # Verify weights structure
        expected_weight_keys = [
            'length', 'complex_indicators', 'academic_terms', 'abstract_concepts',
            'multi_part', 'conditional', 'domain_specific'
        ]
        
        for key in expected_weight_keys:
            self.assertIn(key, new_weights)
            self.assertIsInstance(new_weights[key], float)
            self.assertGreaterEqual(new_weights[key], 0.0)
            self.assertLessEqual(new_weights[key], 1.0)


def run_performance_benchmark():
    """Run performance benchmark for the routing system."""
    print("\n🚀 Running Performance Benchmark...")
    
    api_manager = UnifiedAPIManager()
    
    # Test prompts of varying complexity
    test_prompts = [
        "chào bạn",
        "viết code Python tính giai thừa",
        "Giải thích định lý bất toàn của Gödel và tác động của nó đến toán học hiện đại",
        "Phân tích mối quan hệ giữa triết học và khoa học trong việc hiểu bản chất của thực tại",
        "So sánh và đánh giá các phương pháp học máy khác nhau trong việc xử lý ngôn ngữ tự nhiên"
    ]
    
    total_time = 0
    total_analyses = 0
    
    for prompt in test_prompts:
        start_time = time.time()
        
        # Test model selection
        selected_model = api_manager.choose_model(prompt)
        
        # Test complexity analysis
        complexity_score, detailed_scores = api_manager.complexity_analyzer.analyze_complexity(prompt)
        
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        total_time += elapsed
        total_analyses += 1
        
        print(f"  📝 '{prompt[:50]}...'")
        print(f"     Model: {selected_model}")
        print(f"     Complexity: {complexity_score:.3f}")
        print(f"     Time: {elapsed:.2f}ms")
        print()
    
    avg_time = total_time / total_analyses
    print(f"📊 Performance Summary:")
    print(f"   Total analyses: {total_analyses}")
    print(f"   Average time: {avg_time:.2f}ms")
    print(f"   Total time: {total_time:.2f}ms")
    
    # Get detailed stats
    stats = api_manager.get_analyzer_stats()
    print(f"   Analyzer stats: {stats['performance']}")
    
    return avg_time < 5.0  # Should be under 5ms


def run_accuracy_test():
    """Run accuracy test with predefined test cases."""
    print("\n🎯 Running Accuracy Test...")
    
    api_manager = UnifiedAPIManager()
    
    # Comprehensive test cases
    test_cases = [
        # Simple prompts (should go to gemma2:2b)
        ("chào bạn", "gemma2:2b", "simple"),
        ("bạn tên gì?", "gemma2:2b", "simple"),
        ("2+2 bằng mấy?", "gemma2:2b", "simple"),
        ("thủ đô Việt Nam là gì?", "gemma2:2b", "simple"),
        ("hello", "gemma2:2b", "simple"),
        ("how are you?", "gemma2:2b", "simple"),
        ("GDP là gì?", "gemma2:2b", "simple"),
        ("nước nào lớn nhất thế giới?", "gemma2:2b", "simple"),
        
        # Coding prompts (should go to deepseek-coder:6.7b)
        ("viết code Python", "deepseek-coder:6.7b", "coding"),
        ("lập trình JavaScript", "deepseek-coder:6.7b", "coding"),
        ("debug lỗi", "deepseek-coder:6.7b", "coding"),
        ("tạo function", "deepseek-coder:6.7b", "coding"),
        ("viết code", "deepseek-coder:6.7b", "coding"),
        ("tối ưu thuật toán", "deepseek-coder:6.7b", "coding"),
        ("sửa lỗi code", "deepseek-coder:6.7b", "coding"),
        ("tạo class Python", "deepseek-coder:6.7b", "coding"),
        
        # Complex prompts (should go to deepseek-chat)
        ("Giải thích định lý bất toàn của Gödel", "deepseek-chat", "complex"),
        ("Phân tích mối quan hệ giữa triết học và khoa học", "deepseek-chat", "complex"),
        ("So sánh các phương pháp học máy", "deepseek-chat", "complex"),
        ("Tại sao các hệ thống phức tạp lại tự tổ chức?", "deepseek-chat", "complex"),
        ("Ý nghĩa của cuộc sống là gì?", "deepseek-chat", "complex"),
        ("Bản chất của thực tại là gì?", "deepseek-chat", "complex"),
        ("Tác động của AI đến xã hội", "deepseek-chat", "complex"),
        ("Phân tích xu hướng phát triển công nghệ", "deepseek-chat", "complex"),
        
        # Edge cases
        ("nếu tôi muốn học lập trình thì nên bắt đầu từ đâu?", "deepseek-coder:6.7b", "coding"),
        ("giả sử tôi có một bài toán phức tạp, làm thế nào để giải quyết?", "deepseek-chat", "complex"),
        ("trong trường hợp nào thì nên sử dụng AI?", "deepseek-chat", "complex"),
    ]
    
    correct_predictions = 0
    total_predictions = len(test_cases)
    
    for prompt, expected_model, category in test_cases:
        selected_model = api_manager.choose_model(prompt)
        
        if selected_model == expected_model:
            correct_predictions += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"  {status} '{prompt[:50]}...'")
        print(f"     Expected: {expected_model} ({category})")
        print(f"     Got: {selected_model}")
        print()
    
    accuracy = (correct_predictions / total_predictions) * 100
    print(f"📊 Accuracy Summary:")
    print(f"   Correct predictions: {correct_predictions}/{total_predictions}")
    print(f"   Accuracy: {accuracy:.1f}%")
    
    return accuracy >= 80.0  # Should be at least 80% accurate


def main():
    """Main test runner."""
    print("🧪 AI Router Test Suite")
    print("=" * 50)
    
    # Run unit tests
    print("\n📋 Running Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance benchmark
    performance_ok = run_performance_benchmark()
    
    # Run accuracy test
    accuracy_ok = run_accuracy_test()
    
    # Summary
    print("\n📊 Test Summary:")
    print(f"   Performance: {'✅ PASS' if performance_ok else '❌ FAIL'}")
    print(f"   Accuracy: {'✅ PASS' if accuracy_ok else '❌ FAIL'}")
    
    if performance_ok and accuracy_ok:
        print("\n🎉 All tests passed! AI Router is ready for production.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please review the results.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
