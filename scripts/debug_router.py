#!/usr/bin/env python3
"""
AI Router Debug Tool

This script provides detailed debugging information for the AI router,
helping to understand routing decisions and troubleshoot issues.

Usage:
    python scripts/debug_router.py --prompt "your prompt here"
    python scripts/debug_router.py --interactive
    python scripts/debug_router.py --analyze-file input.txt
"""

import argparse
import os
import sys
import time

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "stillme_core"))

from modules.api_provider_manager import ComplexityAnalyzer, UnifiedAPIManager


class RouterDebugger:
    def __init__(self):
        self.manager = UnifiedAPIManager()
        self.analyzer = ComplexityAnalyzer()

    def debug_prompt(self, prompt: str, verbose: bool = True) -> dict:
        """Debug a single prompt with detailed analysis"""
        print(f"🔍 Debugging Prompt: {prompt}")
        print("=" * 80)

        # Step 1: Basic analysis
        print("📊 Step 1: Basic Analysis")
        print("-" * 40)

        word_count = len(prompt.split())
        char_count = len(prompt)
        print(f"  Word count: {word_count}")
        print(f"  Character count: {char_count}")
        print(
            f"  Language: {'Vietnamese' if any(ord(c) > 127 for c in prompt) else 'English'}"
        )

        # Step 2: Complexity analysis
        print("\n🧠 Step 2: Complexity Analysis")
        print("-" * 40)

        complexity_score, breakdown = self.analyzer.analyze_complexity(prompt)
        print(f"  Overall complexity score: {complexity_score:.3f}")

        if verbose:
            print("  Detailed breakdown:")
            for key, value in breakdown.items():
                print(f"    {key}: {value:.3f}")

        # Step 3: Model selection
        print("\n🎯 Step 3: Model Selection")
        print("-" * 40)

        selected_model = self.manager.choose_model(prompt)
        print(f"  Selected model: {selected_model}")

        # Explain routing logic
        if complexity_score < 0.4:
            routing_reason = "Simple prompt → Local lightweight model (gemma2:2b)"
        elif complexity_score < 0.7:
            routing_reason = (
                "Medium complexity → Local coding model (deepseek-coder:6.7b)"
            )
        else:
            routing_reason = "High complexity → Cloud model (deepseek-chat)"

        print(f"  Routing logic: {routing_reason}")

        # Step 4: Keyword analysis
        print("\n🔤 Step 4: Keyword Analysis")
        print("-" * 40)

        prompt_lower = prompt.lower()

        # Check for coding keywords
        coding_keywords = [
            "code",
            "lập trình",
            "viết",
            "function",
            "class",
            "debug",
            "tối ưu",
            "thuật toán",
            "giai thừa",
            "factorial",
        ]
        found_coding = [kw for kw in coding_keywords if kw in prompt_lower]
        if found_coding:
            print(f"  Coding keywords found: {found_coding}")
        else:
            print("  No coding keywords found")

        # Check for complex indicators
        complex_indicators = [
            "tại sao",
            "như thế nào",
            "phân tích",
            "so sánh",
            "đánh giá",
            "giải thích",
            "mối quan hệ",
            "tác động",
            "ảnh hưởng",
        ]
        found_complex = [ci for ci in complex_indicators if ci in prompt_lower]
        if found_complex:
            print(f"  Complex indicators found: {found_complex}")
        else:
            print("  No complex indicators found")

        # Check for academic terms
        academic_terms = [
            "định lý",
            "định luật",
            "nguyên lý",
            "khái niệm",
            "lý thuyết",
            "phương pháp",
            "kỹ thuật",
            "công nghệ",
            "hệ thống",
            "mô hình",
        ]
        found_academic = [at for at in academic_terms if at in prompt_lower]
        if found_academic:
            print(f"  Academic terms found: {found_academic}")
        else:
            print("  No academic terms found")

        # Check for abstract concepts
        abstract_concepts = [
            "ý nghĩa",
            "bản chất",
            "triết lý",
            "tư tưởng",
            "quan điểm",
            "góc độ",
            "khía cạnh",
            "chiều sâu",
            "tầm nhìn",
            "viễn cảnh",
        ]
        found_abstract = [ac for ac in abstract_concepts if ac in prompt_lower]
        if found_abstract:
            print(f"  Abstract concepts found: {found_abstract}")
        else:
            print("  No abstract concepts found")

        # Step 5: Performance analysis
        print("\n⚡ Step 5: Performance Analysis")
        print("-" * 40)

        start_time = time.time()
        for _ in range(100):
            self.analyzer.analyze_complexity(prompt)
        end_time = time.time()

        avg_time = (end_time - start_time) / 100
        print(f"  Average analysis time: {avg_time * 1000:.2f}ms")

        if avg_time < 0.001:
            perf_grade = "A+ (Excellent)"
        elif avg_time < 0.005:
            perf_grade = "A (Very Good)"
        elif avg_time < 0.01:
            perf_grade = "B (Good)"
        elif avg_time < 0.05:
            perf_grade = "C (Acceptable)"
        else:
            perf_grade = "D (Needs Improvement)"

        print(f"  Performance grade: {perf_grade}")

        # Step 6: Recommendations
        print("\n💡 Step 6: Recommendations")
        print("-" * 40)

        recommendations = []

        if complexity_score < 0.2 and selected_model != "gemma2:2b":
            recommendations.append(
                "Consider lowering complexity thresholds for simple prompts"
            )

        if complexity_score > 0.8 and selected_model != "deepseek-chat":
            recommendations.append(
                "Consider raising complexity thresholds for complex prompts"
            )

        if found_coding and selected_model != "deepseek-coder:6.7b":
            recommendations.append("Coding prompts should route to deepseek-coder:6.7b")

        if avg_time > 0.01:
            recommendations.append(
                "Performance could be improved - consider optimizing keyword lookups"
            )

        if not recommendations:
            recommendations.append("No issues detected - routing appears optimal")

        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")

        # Return debug information
        return {
            "prompt": prompt,
            "complexity_score": complexity_score,
            "breakdown": breakdown,
            "selected_model": selected_model,
            "routing_reason": routing_reason,
            "keywords": {
                "coding": found_coding,
                "complex": found_complex,
                "academic": found_academic,
                "abstract": found_abstract,
            },
            "performance": {"avg_time": avg_time, "grade": perf_grade},
            "recommendations": recommendations,
        }

    def interactive_debug(self):
        """Interactive debugging mode"""
        print("🔍 Interactive Router Debugger")
        print("=" * 50)
        print("Enter prompts to debug routing decisions...")
        print("Type 'quit' to exit, 'help' for commands")

        while True:
            try:
                prompt = input("\n💬 Enter prompt to debug: ").strip()

                if prompt.lower() == "quit":
                    break
                elif prompt.lower() == "help":
                    print("\nAvailable commands:")
                    print("  quit - Exit debugger")
                    print("  help - Show this help")
                    print("  stats - Show analyzer statistics")
                    print("  config - Show current configuration")
                    continue
                elif prompt.lower() == "stats":
                    self._show_analyzer_stats()
                    continue
                elif prompt.lower() == "config":
                    self._show_config()
                    continue
                elif not prompt:
                    continue

                # Debug the prompt
                self.debug_prompt(prompt, verbose=True)

            except KeyboardInterrupt:
                print("\n\n👋 Debugger stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def _show_analyzer_stats(self):
        """Show analyzer statistics"""
        stats = self.analyzer.get_stats()

        print("\n📊 Analyzer Statistics")
        print("=" * 40)
        print(f"Total analyses: {stats['performance']['total_analyses']}")
        print(f"Average analysis time: {stats['performance']['avg_time_ms']:.2f}ms")
        print(f"Fallback triggers: {stats['fallback']['total_triggers']}")

        print("\nCurrent weights:")
        for key, value in stats["weights"].items():
            print(f"  {key}: {value}")

        print("\nCurrent thresholds:")
        for key, value in stats["thresholds"].items():
            print(f"  {key}: {value}")

    def _show_config(self):
        """Show current configuration"""
        print("\n⚙️  Current Configuration")
        print("=" * 40)

        # Environment variables
        env_vars = [
            "COMPLEXITY_WEIGHT_LENGTH",
            "COMPLEXITY_WEIGHT_COMPLEX_INDICATORS",
            "COMPLEXITY_WEIGHT_ACADEMIC_TERMS",
            "COMPLEXITY_WEIGHT_ABSTRACT_CONCEPTS",
            "COMPLEXITY_WEIGHT_MULTI_PART",
            "COMPLEXITY_WEIGHT_CONDITIONAL",
            "COMPLEXITY_WEIGHT_DOMAIN_SPECIFIC",
            "COMPLEXITY_THRESHOLD_SIMPLE",
            "COMPLEXITY_THRESHOLD_MEDIUM",
        ]

        for var in env_vars:
            value = os.getenv(var, "Not set")
            print(f"  {var}: {value}")

    def analyze_file(self, filename: str):
        """Analyze prompts from a file"""
        try:
            with open(filename, encoding="utf-8") as f:
                prompts = [line.strip() for line in f if line.strip()]

            print(f"📁 Analyzing {len(prompts)} prompts from {filename}")
            print("=" * 60)

            results = []
            for i, prompt in enumerate(prompts, 1):
                print(f"\n[{i}/{len(prompts)}] Analyzing: {prompt[:50]}...")

                result = self.debug_prompt(prompt, verbose=False)
                results.append(result)

                # Summary
                print(
                    f"  Score: {result['complexity_score']:.3f} → {result['selected_model']}"
                )

            # Overall statistics
            print("\n📊 Overall Analysis Results")
            print("=" * 40)

            avg_complexity = sum(r["complexity_score"] for r in results) / len(results)
            model_counts = {}
            for result in results:
                model = result["selected_model"]
                model_counts[model] = model_counts.get(model, 0) + 1

            print(f"Average complexity: {avg_complexity:.3f}")
            print("Model distribution:")
            for model, count in model_counts.items():
                percentage = (count / len(results)) * 100
                print(f"  {model}: {count} ({percentage:.1f}%)")

            return results

        except Exception as e:
            print(f"❌ Error analyzing file: {e}")
            return []

    def compare_models(self, prompt: str):
        """Compare how different models would handle a prompt"""
        print(f"🔄 Model Comparison for: {prompt}")
        print("=" * 60)

        models = ["gemma2:2b", "deepseek-coder:6.7b", "deepseek-chat"]

        for model in models:
            print(f"\n🤖 Testing {model}:")
            try:
                start_time = time.time()
                response = self.manager.call_ollama_api(prompt, model=model)
                end_time = time.time()

                print(f"  Response time: {end_time - start_time:.2f}s")
                print(f"  Response: {response[:100]}...")

            except Exception as e:
                print(f"  Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="AI Router Debug Tool")
    parser.add_argument("--prompt", type=str, help="Debug a specific prompt")
    parser.add_argument(
        "--interactive", action="store_true", help="Interactive debugging mode"
    )
    parser.add_argument("--analyze-file", type=str, help="Analyze prompts from a file")
    parser.add_argument(
        "--compare-models", type=str, help="Compare models for a specific prompt"
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    debugger = RouterDebugger()

    if args.prompt:
        debugger.debug_prompt(args.prompt, verbose=args.verbose)
    elif args.interactive:
        debugger.interactive_debug()
    elif args.analyze_file:
        debugger.analyze_file(args.analyze_file)
    elif args.compare_models:
        debugger.compare_models(args.compare_models)
    else:
        print("Please specify an action:")
        print("  --prompt 'prompt': Debug a specific prompt")
        print("  --interactive: Interactive debugging mode")
        print("  --analyze-file filename: Analyze prompts from a file")
        print("  --compare-models 'prompt': Compare models for a prompt")
        print("\nUse --help for more information")


if __name__ == "__main__":
    main()
