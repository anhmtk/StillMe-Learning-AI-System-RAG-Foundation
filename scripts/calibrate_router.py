#!/usr/bin/env python3
"""
AI Router Calibration Script

This script helps fine-tune the complexity analysis weights and thresholds
to improve routing accuracy.

Usage:
    python scripts/calibrate_router.py --test-suite
    python scripts/calibrate_router.py --interactive
    python scripts/calibrate_router.py --auto-tune
"""

import argparse
import os
import sys
import time

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "stillme_core"))

from modules.api_provider_manager import ComplexityAnalyzer


class RouterCalibrator:
    def __init__(self):
        self.analyzer = ComplexityAnalyzer()
        self.test_cases = self._load_test_cases()

    def _load_test_cases(self) -> dict[str, list[tuple[str, str, float]]]:
        """Load test cases with expected routing"""
        return {
            "simple": [
                ("chào bạn", "gemma2:2b", 0.0),
                ("bạn khỏe không?", "gemma2:2b", 0.0),
                ("2+2 bằng mấy?", "gemma2:2b", 0.0),
                ("thủ đô Việt Nam là gì?", "gemma2:2b", 0.0),
                ("hello", "gemma2:2b", 0.0),
                ("how are you?", "gemma2:2b", 0.0),
            ],
            "coding": [
                ("viết code Python", "deepseek-coder:6.7b", 0.3),
                ("lập trình JavaScript", "deepseek-coder:6.7b", 0.3),
                ("debug lỗi", "deepseek-coder:6.7b", 0.3),
                ("tạo function", "deepseek-coder:6.7b", 0.3),
                ("viết code", "deepseek-coder:6.7b", 0.3),
                ("tối ưu thuật toán", "deepseek-coder:6.7b", 0.3),
                ("sửa lỗi code", "deepseek-coder:6.7b", 0.3),
                ("tạo class Python", "deepseek-coder:6.7b", 0.3),
                ("viết code Python tính giai thừa", "deepseek-coder:6.7b", 0.3),
                (
                    "nếu tôi muốn học lập trình thì nên bắt đầu từ đâu?",
                    "deepseek-coder:6.7b",
                    0.3,
                ),
            ],
            "complex": [
                ("Giải thích định lý bất toàn của Gödel", "deepseek-chat", 0.7),
                (
                    "Phân tích mối quan hệ giữa triết học và khoa học",
                    "deepseek-chat",
                    0.7,
                ),
                ("So sánh các phương pháp học máy", "deepseek-chat", 0.7),
                ("Tại sao các hệ thống phức tạp lại tự tổ chức?", "deepseek-chat", 0.7),
                ("Ý nghĩa của cuộc sống là gì?", "deepseek-chat", 0.7),
                ("Bản chất của thực tại là gì?", "deepseek-chat", 0.7),
                ("Tác động của AI đến xã hội", "deepseek-chat", 0.7),
                ("Phân tích xu hướng phát triển công nghệ", "deepseek-chat", 0.7),
                (
                    "giả sử tôi có một bài toán phức tạp, làm thế nào để giải quyết nó?",
                    "deepseek-chat",
                    0.7,
                ),
                ("trong trường hợp nào thì nên sử dụng AI?", "deepseek-chat", 0.7),
                (
                    "Giải thích định lý bất toàn của Gödel và tác động của nó đến toán học hiện đại",
                    "deepseek-chat",
                    0.7,
                ),
                (
                    "Phân tích mối quan hệ giữa triết học và khoa học trong việc hiểu bản chất của thực tại",
                    "deepseek-chat",
                    0.7,
                ),
                (
                    "So sánh và đánh giá các phương pháp học máy khác nhau trong việc xử lý ngôn ngữ tự nhiên",
                    "deepseek-chat",
                    0.7,
                ),
                (
                    "Tại sao các hệ thống phức tạp lại có xu hướng tự tổ chức và phát triển theo quy luật nào?",
                    "deepseek-chat",
                    0.7,
                ),
            ],
        }

    def test_current_config(self) -> dict[str, float]:
        """Test current configuration and return accuracy scores"""
        results = {}

        for category, test_cases in self.test_cases.items():
            correct = 0
            total = len(test_cases)

            print(f"\n🧪 Testing {category} prompts:")

            for prompt, expected_model, _expected_score in test_cases:
                # Get actual complexity score
                actual_score, breakdown = self.analyzer.analyze_complexity(prompt)

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
                print(
                    f"  {status} {prompt[:50]}... → {actual_model} (score: {actual_score:.3f})"
                )

                if not is_correct:
                    print(f"    Expected: {expected_model}, Got: {actual_model}")

            accuracy = correct / total
            results[category] = accuracy
            print(f"  📊 {category} accuracy: {accuracy:.1%} ({correct}/{total})")

        # Overall accuracy
        total_correct = sum(
            len([tc for tc in test_cases if self._test_single_case(tc)])
            for test_cases in self.test_cases.values()
        )
        total_tests = sum(len(test_cases) for test_cases in self.test_cases.values())
        overall_accuracy = total_correct / total_tests

        results["overall"] = overall_accuracy
        print(f"\n🎯 Overall accuracy: {overall_accuracy:.1%}")

        return results

    def _test_single_case(self, test_case: tuple[str, str, float]) -> bool:
        """Test a single case and return if correct"""
        prompt, expected_model, expected_score = test_case
        actual_score, _ = self.analyzer.analyze_complexity(prompt)

        if actual_score < 0.4:
            actual_model = "gemma2:2b"
        elif actual_score < 0.7:
            actual_model = "deepseek-coder:6.7b"
        else:
            actual_model = "deepseek-chat"

        return actual_model == expected_model

    def interactive_tuning(self):
        """Interactive tuning mode"""
        print("🎛️  Interactive Router Calibration")
        print("=" * 50)

        while True:
            print("\nCurrent configuration:")
            stats = self.analyzer.get_stats()
            print(f"  Weights: {stats['weights']}")
            print(f"  Thresholds: {stats['thresholds']}")

            # Test current config
            results = self.test_current_config()

            print(f"\nCurrent accuracy: {results['overall']:.1%}")

            # Get user input
            print("\nOptions:")
            print("1. Adjust weights")
            print("2. Adjust thresholds")
            print("3. Test specific prompt")
            print("4. Export configuration")
            print("5. Exit")

            choice = input("\nSelect option (1-5): ").strip()

            if choice == "1":
                self._adjust_weights()
            elif choice == "2":
                self._adjust_thresholds()
            elif choice == "3":
                self._test_specific_prompt()
            elif choice == "4":
                self._export_config()
            elif choice == "5":
                break
            else:
                print("Invalid option. Please try again.")

    def _adjust_weights(self):
        """Adjust complexity analysis weights"""
        print("\n🔧 Adjusting weights:")
        print(
            "Available weights: length, complex_indicators, academic_terms, abstract_concepts, multi_part, conditional, domain_specific"
        )

        weight_name = input("Enter weight name: ").strip()
        if weight_name not in [
            "length",
            "complex_indicators",
            "academic_terms",
            "abstract_concepts",
            "multi_part",
            "conditional",
            "domain_specific",
        ]:
            print("Invalid weight name.")
            return

        try:
            new_value = float(
                input(
                    f"Enter new value for {weight_name} (current: {self.analyzer.weights[weight_name]}): "
                )
            )
            os.environ[f"COMPLEXITY_WEIGHT_{weight_name.upper()}"] = str(new_value)

            # Reload analyzer with new weights
            self.analyzer = ComplexityAnalyzer()
            print(f"✅ Updated {weight_name} to {new_value}")
        except ValueError:
            print("Invalid value. Please enter a number.")

    def _adjust_thresholds(self):
        """Adjust complexity thresholds"""
        print("\n🔧 Adjusting thresholds:")

        try:
            simple_threshold = float(
                input(
                    f"Enter simple threshold (current: {self.analyzer.thresholds['simple']}): "
                )
            )
            medium_threshold = float(
                input(
                    f"Enter medium threshold (current: {self.analyzer.thresholds['medium']}): "
                )
            )

            os.environ["COMPLEXITY_THRESHOLD_SIMPLE"] = str(simple_threshold)
            os.environ["COMPLEXITY_THRESHOLD_MEDIUM"] = str(medium_threshold)

            # Reload analyzer with new thresholds
            self.analyzer = ComplexityAnalyzer()
            print(
                f"✅ Updated thresholds: simple={simple_threshold}, medium={medium_threshold}"
            )
        except ValueError:
            print("Invalid value. Please enter a number.")

    def _test_specific_prompt(self):
        """Test a specific prompt"""
        prompt = input("\nEnter prompt to test: ").strip()
        if not prompt:
            return

        score, breakdown = self.analyzer.analyze_complexity(prompt)

        if score < 0.4:
            model = "gemma2:2b"
        elif score < 0.7:
            model = "deepseek-coder:6.7b"
        else:
            model = "deepseek-chat"

        print("\n📊 Analysis results:")
        print(f"  Prompt: {prompt}")
        print(f"  Complexity score: {score:.3f}")
        print(f"  Selected model: {model}")
        print(f"  Breakdown: {breakdown}")

    def _export_config(self):
        """Export current configuration"""
        stats = self.analyzer.get_stats()

        config = f"""# AI Router Configuration
# Generated on {time.strftime('%Y-%m-%d %H:%M:%S')}

# Complexity Analysis Weights
COMPLEXITY_WEIGHT_LENGTH={stats['weights']['length']}
COMPLEXITY_WEIGHT_COMPLEX_INDICATORS={stats['weights']['complex_indicators']}
COMPLEXITY_WEIGHT_ACADEMIC_TERMS={stats['weights']['academic_terms']}
COMPLEXITY_WEIGHT_ABSTRACT_CONCEPTS={stats['weights']['abstract_concepts']}
COMPLEXITY_WEIGHT_MULTI_PART={stats['weights']['multi_part']}
COMPLEXITY_WEIGHT_CONDITIONAL={stats['weights']['conditional']}
COMPLEXITY_WEIGHT_DOMAIN_SPECIFIC={stats['weights']['domain_specific']}

# Complexity Thresholds
COMPLEXITY_THRESHOLD_SIMPLE={stats['thresholds']['simple']}
COMPLEXITY_THRESHOLD_MEDIUM={stats['thresholds']['medium']}

# Performance Stats
# Average analysis time: {stats['performance']['avg_time_ms']:.2f}ms
# Total analyses: {stats['performance']['total_analyses']}
"""

        filename = f"router_config_{int(time.time())}.env"
        with open(filename, "w") as f:
            f.write(config)

        print(f"✅ Configuration exported to {filename}")

    def auto_tune(self, target_accuracy: float = 0.8):
        """Automatically tune weights and thresholds to achieve target accuracy"""
        print(f"🤖 Auto-tuning to achieve {target_accuracy:.1%} accuracy...")

        best_accuracy = 0.0
        best_config = None

        # Test different weight combinations
        weight_ranges = {
            "academic_terms": [0.3, 0.4, 0.5, 0.6],
            "abstract_concepts": [0.4, 0.5, 0.6, 0.7],
            "domain_specific": [0.3, 0.4, 0.5, 0.6],
        }

        threshold_ranges = {
            "simple": [0.2, 0.3, 0.4, 0.5],
            "medium": [0.5, 0.6, 0.7, 0.8],
        }

        total_combinations = (
            len(weight_ranges["academic_terms"])
            * len(weight_ranges["abstract_concepts"])
            * len(weight_ranges["domain_specific"])
            * len(threshold_ranges["simple"])
            * len(threshold_ranges["medium"])
        )
        current_combination = 0

        print(f"Testing {total_combinations} combinations...")

        for academic_weight in weight_ranges["academic_terms"]:
            for abstract_weight in weight_ranges["abstract_concepts"]:
                for domain_weight in weight_ranges["domain_specific"]:
                    for simple_threshold in threshold_ranges["simple"]:
                        for medium_threshold in threshold_ranges["medium"]:
                            current_combination += 1

                            # Set environment variables
                            os.environ["COMPLEXITY_WEIGHT_ACADEMIC_TERMS"] = str(
                                academic_weight
                            )
                            os.environ["COMPLEXITY_WEIGHT_ABSTRACT_CONCEPTS"] = str(
                                abstract_weight
                            )
                            os.environ["COMPLEXITY_WEIGHT_DOMAIN_SPECIFIC"] = str(
                                domain_weight
                            )
                            os.environ["COMPLEXITY_THRESHOLD_SIMPLE"] = str(
                                simple_threshold
                            )
                            os.environ["COMPLEXITY_THRESHOLD_MEDIUM"] = str(
                                medium_threshold
                            )

                            # Reload analyzer
                            self.analyzer = ComplexityAnalyzer()

                            # Test accuracy
                            results = self.test_current_config()
                            accuracy = results["overall"]

                            print(
                                f"  [{current_combination}/{total_combinations}] Accuracy: {accuracy:.1%} (academic={academic_weight}, abstract={abstract_weight}, domain={domain_weight}, simple={simple_threshold}, medium={medium_threshold})"
                            )

                            if accuracy > best_accuracy:
                                best_accuracy = accuracy
                                best_config = {
                                    "academic_terms": academic_weight,
                                    "abstract_concepts": abstract_weight,
                                    "domain_specific": domain_weight,
                                    "simple_threshold": simple_threshold,
                                    "medium_threshold": medium_threshold,
                                    "accuracy": accuracy,
                                }

                            if accuracy >= target_accuracy:
                                print(f"🎯 Target accuracy achieved: {accuracy:.1%}")
                                self._export_best_config(best_config)
                                return best_config

        print(f"🏆 Best configuration found: {best_accuracy:.1%} accuracy")
        self._export_best_config(best_config)
        return best_config

    def _export_best_config(self, config: dict):
        """Export the best configuration found"""
        if not config:
            return

        config_text = f"""# Best AI Router Configuration
# Accuracy: {config['accuracy']:.1%}

COMPLEXITY_WEIGHT_ACADEMIC_TERMS={config['academic_terms']}
COMPLEXITY_WEIGHT_ABSTRACT_CONCEPTS={config['abstract_concepts']}
COMPLEXITY_WEIGHT_DOMAIN_SPECIFIC={config['domain_specific']}
COMPLEXITY_THRESHOLD_SIMPLE={config['simple_threshold']}
COMPLEXITY_THRESHOLD_MEDIUM={config['medium_threshold']}
"""

        filename = f"best_router_config_{int(time.time())}.env"
        with open(filename, "w") as f:
            f.write(config_text)

        print(f"✅ Best configuration exported to {filename}")


def main():
    parser = argparse.ArgumentParser(description="AI Router Calibration Tool")
    parser.add_argument("--test-suite", action="store_true", help="Run test suite")
    parser.add_argument(
        "--interactive", action="store_true", help="Interactive tuning mode"
    )
    parser.add_argument(
        "--auto-tune", action="store_true", help="Auto-tune configuration"
    )
    parser.add_argument(
        "--target-accuracy",
        type=float,
        default=0.8,
        help="Target accuracy for auto-tune",
    )

    args = parser.parse_args()

    calibrator = RouterCalibrator()

    if args.test_suite:
        print("🧪 Running AI Router Test Suite")
        print("=" * 50)
        results = calibrator.test_current_config()
        print("\n📊 Final Results:")
        for category, accuracy in results.items():
            print(f"  {category}: {accuracy:.1%}")
    elif args.interactive:
        calibrator.interactive_tuning()
    elif args.auto_tune:
        calibrator.auto_tune(args.target_accuracy)
    else:
        print("Please specify --test-suite, --interactive, or --auto-tune")
        print("Use --help for more information")


if __name__ == "__main__":
    main()
