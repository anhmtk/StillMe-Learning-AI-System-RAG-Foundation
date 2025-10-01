#!/usr/bin/env python3
"""
AI Router Validation Script

This script validates the AI router configuration and performance,
ensuring it meets quality standards before deployment.

Usage:
    python scripts/validate_router.py --full
    python scripts/validate_router.py --quick
    python scripts/validate_router.py --performance
"""

import os
import sys
import argparse
import time
import json
from typing import Dict, List, Tuple, Optional

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stillme_core'))

from modules.api_provider_manager import UnifiedAPIManager, ComplexityAnalyzer

class RouterValidator:
    def __init__(self):
        self.manager = UnifiedAPIManager()
        self.analyzer = ComplexityAnalyzer()
        self.validation_results = {}

    def validate_configuration(self) -> Dict:
        """Validate router configuration"""
        print("⚙️  Validating Configuration")
        print("-" * 40)

        results = {
            'weights': {},
            'thresholds': {},
            'environment': {},
            'overall': 'PASS'
        }

        # Check weights
        required_weights = [
            'length', 'complex_indicators', 'academic_terms',
            'abstract_concepts', 'multi_part', 'conditional', 'domain_specific'
        ]

        stats = self.analyzer.get_stats()
        weights = stats['weights']

        for weight in required_weights:
            if weight in weights:
                value = weights[weight]
                if 0.0 <= value <= 1.0:
                    results['weights'][weight] = 'PASS'
                else:
                    results['weights'][weight] = f'FAIL (value: {value}, expected: 0.0-1.0)'
                    results['overall'] = 'FAIL'
            else:
                results['weights'][weight] = 'FAIL (missing)'
                results['overall'] = 'FAIL'

        # Check thresholds
        thresholds = stats['thresholds']
        if 'simple' in thresholds and 'medium' in thresholds:
            simple = thresholds['simple']
            medium = thresholds['medium']

            if 0.0 <= simple <= 1.0:
                results['thresholds']['simple'] = 'PASS'
            else:
                results['thresholds']['simple'] = f'FAIL (value: {simple}, expected: 0.0-1.0)'
                results['overall'] = 'FAIL'

            if 0.0 <= medium <= 1.0:
                results['thresholds']['medium'] = 'PASS'
            else:
                results['thresholds']['medium'] = f'FAIL (value: {medium}, expected: 0.0-1.0)'
                results['overall'] = 'FAIL'

            if simple >= medium:
                results['thresholds']['order'] = f'FAIL (simple: {simple} >= medium: {medium})'
                results['overall'] = 'FAIL'
            else:
                results['thresholds']['order'] = 'PASS'
        else:
            results['thresholds']['simple'] = 'FAIL (missing)'
            results['thresholds']['medium'] = 'FAIL (missing)'
            results['overall'] = 'FAIL'

        # Check environment variables
        env_vars = [
            'COMPLEXITY_WEIGHT_LENGTH',
            'COMPLEXITY_WEIGHT_COMPLEX_INDICATORS',
            'COMPLEXITY_WEIGHT_ACADEMIC_TERMS',
            'COMPLEXITY_WEIGHT_ABSTRACT_CONCEPTS',
            'COMPLEXITY_WEIGHT_MULTI_PART',
            'COMPLEXITY_WEIGHT_CONDITIONAL',
            'COMPLEXITY_WEIGHT_DOMAIN_SPECIFIC',
            'COMPLEXITY_THRESHOLD_SIMPLE',
            'COMPLEXITY_THRESHOLD_MEDIUM'
        ]

        for var in env_vars:
            if os.getenv(var):
                results['environment'][var] = 'PASS'
            else:
                results['environment'][var] = 'WARN (not set, using default)'

        # Print results
        print(f"Weights validation:")
        for weight, status in results['weights'].items():
            print(f"  {weight}: {status}")

        print(f"\nThresholds validation:")
        for threshold, status in results['thresholds'].items():
            print(f"  {threshold}: {status}")

        print(f"\nEnvironment variables:")
        for var, status in results['environment'].items():
            print(f"  {var}: {status}")

        print(f"\nConfiguration validation: {results['overall']}")

        return results

    def validate_performance(self) -> Dict:
        """Validate router performance"""
        print("\n⚡ Validating Performance")
        print("-" * 40)

        results = {
            'analysis_time': {},
            'memory_usage': {},
            'overall': 'PASS'
        }

        # Test analysis time
        test_prompts = [
            "chào bạn",
            "viết code Python tính giai thừa",
            "Giải thích định lý bất toàn của Gödel",
            "Phân tích mối quan hệ giữa triết học và khoa học",
            "tối ưu hóa performance của database query"
        ]

        times = []
        for prompt in test_prompts:
            start_time = time.time()
            self.analyzer.analyze_complexity(prompt)
            end_time = time.time()
            times.append(end_time - start_time)

        avg_time = sum(times) / len(times)
        max_time = max(times)

        if avg_time < 0.005:  # < 5ms
            results['analysis_time']['average'] = 'PASS'
        else:
            results['analysis_time']['average'] = f'FAIL (avg: {avg_time*1000:.2f}ms, expected: <5ms)'
            results['overall'] = 'FAIL'

        if max_time < 0.01:  # < 10ms
            results['analysis_time']['maximum'] = 'PASS'
        else:
            results['analysis_time']['maximum'] = f'FAIL (max: {max_time*1000:.2f}ms, expected: <10ms)'
            results['overall'] = 'FAIL'

        # Memory usage (basic check)
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024

        if memory_mb < 100:  # < 100MB
            results['memory_usage']['current'] = 'PASS'
        else:
            results['memory_usage']['current'] = f'WARN (current: {memory_mb:.1f}MB)'

        # Print results
        print(f"Analysis time:")
        print(f"  Average: {avg_time*1000:.2f}ms ({results['analysis_time']['average']})")
        print(f"  Maximum: {max_time*1000:.2f}ms ({results['analysis_time']['maximum']})")

        print(f"\nMemory usage:")
        print(f"  Current: {memory_mb:.1f}MB ({results['memory_usage']['current']})")

        print(f"\nPerformance validation: {results['overall']}")

        return results

    def validate_accuracy(self) -> Dict:
        """Validate router accuracy"""
        print("\n🎯 Validating Accuracy")
        print("-" * 40)

        # Test cases with expected routing
        test_cases = [
            # Simple prompts
            ("chào bạn", "gemma2:2b", 0.0),
            ("bạn khỏe không?", "gemma2:2b", 0.0),
            ("2+2 bằng mấy?", "gemma2:2b", 0.0),
            ("thủ đô Việt Nam là gì?", "gemma2:2b", 0.0),
            ("hello", "gemma2:2b", 0.0),
            ("how are you?", "gemma2:2b", 0.0),

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
        ]

        results = {
            'simple': {'correct': 0, 'total': 0, 'accuracy': 0.0},
            'coding': {'correct': 0, 'total': 0, 'accuracy': 0.0},
            'complex': {'correct': 0, 'total': 0, 'accuracy': 0.0},
            'overall': {'correct': 0, 'total': 0, 'accuracy': 0.0}
        }

        # Categorize test cases
        simple_cases = test_cases[:6]
        coding_cases = test_cases[6:16]
        complex_cases = test_cases[16:]

        # Test each category
        for category, cases in [('simple', simple_cases), ('coding', coding_cases), ('complex', complex_cases)]:
            correct = 0
            total = len(cases)

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

                status = "✅" if is_correct else "❌"
                print(f"  {status} {prompt[:50]}... → {actual_model} (score: {actual_score:.3f})")

                if not is_correct:
                    print(f"    Expected: {expected_model}, Got: {actual_model}")

            accuracy = correct / total
            results[category]['correct'] = correct
            results[category]['total'] = total
            results[category]['accuracy'] = accuracy

            print(f"  📊 {category} accuracy: {accuracy:.1%} ({correct}/{total})")

        # Overall accuracy
        total_correct = sum(results[cat]['correct'] for cat in ['simple', 'coding', 'complex'])
        total_tests = sum(results[cat]['total'] for cat in ['simple', 'coding', 'complex'])
        overall_accuracy = total_correct / total_tests

        results['overall']['correct'] = total_correct
        results['overall']['total'] = total_tests
        results['overall']['accuracy'] = overall_accuracy

        print(f"\n🎯 Overall accuracy: {overall_accuracy:.1%}")

        # Determine overall status
        if overall_accuracy >= 0.8:
            results['overall']['status'] = 'PASS'
        elif overall_accuracy >= 0.6:
            results['overall']['status'] = 'WARN'
        else:
            results['overall']['status'] = 'FAIL'

        return results

    def validate_fallback(self) -> Dict:
        """Validate fallback mechanism"""
        print("\n🔄 Validating Fallback Mechanism")
        print("-" * 40)

        results = {
            'negative_feedback': {},
            'confusion_markers': {},
            'short_responses': {},
            'overall': 'PASS'
        }

        # Test negative feedback detection
        negative_feedback = [
            "sai rồi", "không đúng", "???", "không đúng ý mình",
            "chưa chính xác", "thiếu thông tin", "không hiểu", "??", "sai"
        ]

        correct_negative = 0
        for feedback in negative_feedback:
            should_fallback = self.analyzer.should_trigger_fallback(feedback, "original prompt", "gemma2:2b")
            if should_fallback:
                correct_negative += 1

        results['negative_feedback']['correct'] = correct_negative
        results['negative_feedback']['total'] = len(negative_feedback)
        results['negative_feedback']['accuracy'] = correct_negative / len(negative_feedback)

        # Test positive feedback (should NOT trigger fallback)
        positive_feedback = [
            "đúng rồi", "ok", "cảm ơn", "tốt lắm", "tuyệt vời", "cảm ơn bạn", "rất hay"
        ]

        correct_positive = 0
        for feedback in positive_feedback:
            should_fallback = self.analyzer.should_trigger_fallback(feedback, "original prompt", "gemma2:2b")
            if not should_fallback:
                correct_positive += 1

        results['confusion_markers']['correct'] = correct_positive
        results['confusion_markers']['total'] = len(positive_feedback)
        results['confusion_markers']['accuracy'] = correct_positive / len(positive_feedback)

        # Print results
        print(f"Negative feedback detection:")
        print(f"  Correct: {correct_negative}/{len(negative_feedback)} ({results['negative_feedback']['accuracy']:.1%})")

        print(f"\nPositive feedback detection:")
        print(f"  Correct: {correct_positive}/{len(positive_feedback)} ({results['confusion_markers']['accuracy']:.1%})")

        # Overall fallback validation
        total_correct = correct_negative + correct_positive
        total_tests = len(negative_feedback) + len(positive_feedback)
        overall_accuracy = total_correct / total_tests

        if overall_accuracy >= 0.9:
            results['overall'] = 'PASS'
        elif overall_accuracy >= 0.7:
            results['overall'] = 'WARN'
        else:
            results['overall'] = 'FAIL'

        print(f"\nFallback validation: {results['overall']} ({overall_accuracy:.1%})")

        return results

    def run_full_validation(self) -> Dict:
        """Run full validation suite"""
        print("🔍 AI Router Full Validation")
        print("=" * 60)

        start_time = time.time()

        # Run all validations
        config_results = self.validate_configuration()
        performance_results = self.validate_performance()
        accuracy_results = self.validate_accuracy()
        fallback_results = self.validate_fallback()

        end_time = time.time()

        # Compile overall results
        overall_results = {
            'configuration': config_results,
            'performance': performance_results,
            'accuracy': accuracy_results,
            'fallback': fallback_results,
            'total_time': end_time - start_time
        }

        # Determine overall status
        overall_status = 'PASS'
        if (config_results['overall'] == 'FAIL' or
            performance_results['overall'] == 'FAIL' or
            accuracy_results['overall']['status'] == 'FAIL' or
            fallback_results['overall'] == 'FAIL'):
            overall_status = 'FAIL'
        elif (config_results['overall'] == 'WARN' or
              performance_results['overall'] == 'WARN' or
              accuracy_results['overall']['status'] == 'WARN' or
              fallback_results['overall'] == 'WARN'):
            overall_status = 'WARN'

        overall_results['overall_status'] = overall_status

        # Print summary
        print(f"\n📊 Validation Summary")
        print("=" * 40)
        print(f"Configuration: {config_results['overall']}")
        print(f"Performance: {performance_results['overall']}")
        print(f"Accuracy: {accuracy_results['overall']['status']} ({accuracy_results['overall']['accuracy']:.1%})")
        print(f"Fallback: {fallback_results['overall']}")
        print(f"Total time: {overall_results['total_time']:.2f}s")
        print(f"\n🎯 Overall Status: {overall_status}")

        return overall_results

    def run_quick_validation(self) -> Dict:
        """Run quick validation (essential checks only)"""
        print("⚡ AI Router Quick Validation")
        print("=" * 40)

        start_time = time.time()

        # Run essential validations only
        config_results = self.validate_configuration()
        performance_results = self.validate_performance()

        end_time = time.time()

        # Compile results
        results = {
            'configuration': config_results,
            'performance': performance_results,
            'total_time': end_time - start_time
        }

        # Determine overall status
        overall_status = 'PASS'
        if (config_results['overall'] == 'FAIL' or
            performance_results['overall'] == 'FAIL'):
            overall_status = 'FAIL'
        elif (config_results['overall'] == 'WARN' or
              performance_results['overall'] == 'WARN'):
            overall_status = 'WARN'

        results['overall_status'] = overall_status

        # Print summary
        print(f"\n📊 Quick Validation Summary")
        print("=" * 40)
        print(f"Configuration: {config_results['overall']}")
        print(f"Performance: {performance_results['overall']}")
        print(f"Total time: {results['total_time']:.2f}s")
        print(f"\n🎯 Overall Status: {overall_status}")

        return results

    def export_results(self, results: Dict, filename: str):
        """Export validation results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"✅ Validation results exported to {filename}")

def main():
    parser = argparse.ArgumentParser(description='AI Router Validation Script')
    parser.add_argument('--full', action='store_true', help='Run full validation suite')
    parser.add_argument('--quick', action='store_true', help='Run quick validation')
    parser.add_argument('--performance', action='store_true', help='Run performance validation only')
    parser.add_argument('--export', type=str, help='Export results to JSON file')

    args = parser.parse_args()

    validator = RouterValidator()

    if args.full:
        results = validator.run_full_validation()
    elif args.quick:
        results = validator.run_quick_validation()
    elif args.performance:
        results = {'performance': validator.validate_performance()}
    else:
        print("Please specify --full, --quick, or --performance")
        print("Use --help for more information")
        return

    if args.export:
        validator.export_results(results, args.export)

if __name__ == "__main__":
    main()
