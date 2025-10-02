#!/usr/bin/env python3
"""
AI Router Performance Monitor

This script monitors the AI router performance in real-time,
providing insights into routing decisions and accuracy.

Usage:
    python scripts/monitor_router.py --live
    python scripts/monitor_router.py --stats
    python scripts/monitor_router.py --test-prompt "your prompt here"
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Optional

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "stillme_core"))

from modules.api_provider_manager import ComplexityAnalyzer, UnifiedAPIManager


class RouterMonitor:
    def __init__(self):
        self.manager = UnifiedAPIManager()
        self.analyzer = ComplexityAnalyzer()
        self.session_log = []

    def test_prompt(self, prompt: str, debug: bool = True) -> dict:
        """Test a single prompt and return detailed analysis"""
        start_time = time.time()

        # Get complexity analysis
        complexity_score, breakdown = self.analyzer.analyze_complexity(prompt)

        # Get model selection
        selected_model = self.manager.choose_model(prompt)

        # Get actual AI response (if available)
        try:
            ai_response = self.manager.get_response(prompt)
            response_time = time.time() - start_time
        except Exception as e:
            ai_response = f"Error: {str(e)}"
            response_time = time.time() - start_time

        result = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "complexity_score": complexity_score,
            "breakdown": breakdown,
            "selected_model": selected_model,
            "ai_response": ai_response,
            "response_time": response_time,
            "debug": debug,
        }

        # Log to session
        self.session_log.append(result)

        return result

    def print_analysis(self, result: dict):
        """Print formatted analysis results"""
        print("\n🔍 AI Router Analysis")
        print("=" * 60)
        print(f"📝 Prompt: {result['prompt']}")
        print(f"🧠 Complexity Score: {result['complexity_score']:.3f}")
        print(f"🎯 Selected Model: {result['selected_model']}")
        print(f"⏱️  Response Time: {result['response_time']:.2f}s")

        if result["debug"]:
            print("\n📊 Breakdown:")
            for key, value in result["breakdown"].items():
                print(f"  {key}: {value:.3f}")

        print("\n🤖 AI Response:")
        print(f"  {result['ai_response']}")

        # Model routing explanation
        if result["complexity_score"] < 0.4:
            routing_reason = "Simple prompt → Local lightweight model"
        elif result["complexity_score"] < 0.7:
            routing_reason = "Medium complexity → Local coding model"
        else:
            routing_reason = "High complexity → Cloud model"

        print(f"\n💡 Routing Logic: {routing_reason}")

    def live_monitor(self, duration: int = 300):
        """Monitor router performance in real-time"""
        print(f"🔴 Live Router Monitor (Duration: {duration}s)")
        print("=" * 60)
        print("Enter prompts to test routing decisions...")
        print("Type 'quit' to exit, 'stats' for statistics, 'clear' to clear session")

        start_time = time.time()

        while time.time() - start_time < duration:
            try:
                prompt = input("\n💬 Enter prompt: ").strip()

                if prompt.lower() == "quit":
                    break
                elif prompt.lower() == "stats":
                    self.print_session_stats()
                    continue
                elif prompt.lower() == "clear":
                    self.session_log.clear()
                    print("✅ Session cleared")
                    continue
                elif not prompt:
                    continue

                # Test the prompt
                result = self.test_prompt(prompt, debug=True)
                self.print_analysis(result)

            except KeyboardInterrupt:
                print("\n\n👋 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

        # Print final statistics
        self.print_session_stats()

    def print_session_stats(self):
        """Print session statistics"""
        if not self.session_log:
            print("📊 No data in current session")
            return

        print("\n📊 Session Statistics")
        print("=" * 40)

        # Basic stats
        total_prompts = len(self.session_log)
        avg_complexity = (
            sum(r["complexity_score"] for r in self.session_log) / total_prompts
        )
        avg_response_time = (
            sum(r["response_time"] for r in self.session_log) / total_prompts
        )

        print(f"Total Prompts: {total_prompts}")
        print(f"Average Complexity: {avg_complexity:.3f}")
        print(f"Average Response Time: {avg_response_time:.2f}s")

        # Model distribution
        model_counts = {}
        for result in self.session_log:
            model = result["selected_model"]
            model_counts[model] = model_counts.get(model, 0) + 1

        print("\n🎯 Model Distribution:")
        for model, count in model_counts.items():
            percentage = (count / total_prompts) * 100
            print(f"  {model}: {count} ({percentage:.1f}%)")

        # Complexity distribution
        complexity_ranges = {
            "Simple (<0.4)": 0,
            "Medium (0.4-0.7)": 0,
            "Complex (≥0.7)": 0,
        }

        for result in self.session_log:
            score = result["complexity_score"]
            if score < 0.4:
                complexity_ranges["Simple (<0.4)"] += 1
            elif score < 0.7:
                complexity_ranges["Medium (0.4-0.7)"] += 1
            else:
                complexity_ranges["Complex (≥0.7)"] += 1

        print("\n🧠 Complexity Distribution:")
        for range_name, count in complexity_ranges.items():
            percentage = (count / total_prompts) * 100
            print(f"  {range_name}: {count} ({percentage:.1f}%)")

        # Performance insights
        print("\n⚡ Performance Insights:")
        slow_responses = [r for r in self.session_log if r["response_time"] > 2.0]
        if slow_responses:
            print(f"  Slow responses (>2s): {len(slow_responses)}")
            avg_slow_time = sum(r["response_time"] for r in slow_responses) / len(
                slow_responses
            )
            print(f"  Average slow response time: {avg_slow_time:.2f}s")

        high_complexity = [r for r in self.session_log if r["complexity_score"] > 0.8]
        if high_complexity:
            print(f"  High complexity prompts (>0.8): {len(high_complexity)}")

    def export_session_log(self, filename: Optional[str] = None):
        """Export session log to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"router_session_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.session_log, f, indent=2, ensure_ascii=False)

        print(f"✅ Session log exported to {filename}")
        return filename

    def load_session_log(self, filename: str):
        """Load session log from JSON file"""
        try:
            with open(filename, encoding="utf-8") as f:
                self.session_log = json.load(f)
            print(f"✅ Session log loaded from {filename}")
        except Exception as e:
            print(f"❌ Error loading session log: {e}")

    def benchmark_performance(self, num_iterations: int = 100):
        """Benchmark router performance"""
        print(f"🏃‍♂️ Performance Benchmark ({num_iterations} iterations)")
        print("=" * 50)

        test_prompts = [
            "chào bạn",
            "viết code Python tính giai thừa",
            "Giải thích định lý bất toàn của Gödel",
            "Phân tích mối quan hệ giữa triết học và khoa học",
            "tối ưu hóa performance của database query",
            "So sánh các phương pháp học máy khác nhau",
            "debug lỗi trong thuật toán sắp xếp",
            "Tại sao các hệ thống phức tạp lại tự tổ chức?",
            "tạo function JavaScript để validate email",
            "Ý nghĩa của cuộc sống là gì?",
        ]

        times = []
        scores = []

        for i in range(num_iterations):
            prompt = test_prompts[i % len(test_prompts)]

            start_time = time.time()
            score, _ = self.analyzer.analyze_complexity(prompt)
            end_time = time.time()

            times.append(end_time - start_time)
            scores.append(score)

            if (i + 1) % 20 == 0:
                print(f"  Completed {i + 1}/{num_iterations} iterations...")

        # Calculate statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        avg_score = sum(scores) / len(scores)

        print("\n📊 Benchmark Results:")
        print(f"  Average analysis time: {avg_time * 1000:.2f}ms")
        print(f"  Min analysis time: {min_time * 1000:.2f}ms")
        print(f"  Max analysis time: {max_time * 1000:.2f}ms")
        print(f"  Average complexity score: {avg_score:.3f}")

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
            "avg_time": avg_time,
            "min_time": min_time,
            "max_time": max_time,
            "avg_score": avg_score,
            "grade": grade,
        }


def main():
    parser = argparse.ArgumentParser(description="AI Router Performance Monitor")
    parser.add_argument("--live", action="store_true", help="Live monitoring mode")
    parser.add_argument("--stats", action="store_true", help="Show current statistics")
    parser.add_argument("--test-prompt", type=str, help="Test a specific prompt")
    parser.add_argument(
        "--benchmark", type=int, default=100, help="Run performance benchmark"
    )
    parser.add_argument("--export", type=str, help="Export session log to file")
    parser.add_argument("--load", type=str, help="Load session log from file")
    parser.add_argument(
        "--duration", type=int, default=300, help="Live monitoring duration (seconds)"
    )

    args = parser.parse_args()

    monitor = RouterMonitor()

    if args.load:
        monitor.load_session_log(args.load)

    if args.test_prompt:
        result = monitor.test_prompt(args.test_prompt, debug=True)
        monitor.print_analysis(result)
    elif args.live:
        monitor.live_monitor(args.duration)
    elif args.stats:
        monitor.print_session_stats()
    elif args.benchmark:
        monitor.benchmark_performance(args.benchmark)
    elif args.export:
        monitor.export_session_log(args.export)
    else:
        print("Please specify an action:")
        print("  --live: Live monitoring mode")
        print("  --stats: Show current statistics")
        print("  --test-prompt 'prompt': Test a specific prompt")
        print("  --benchmark: Run performance benchmark")
        print("  --export filename: Export session log")
        print("  --load filename: Load session log")
        print("\nUse --help for more information")


if __name__ == "__main__":
    main()
