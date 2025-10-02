#!/usr/bin/env python3
"""
AI Router Command Line Interface

This script provides a command-line interface for interacting with the AI router,
allowing users to test prompts, view statistics, and manage the router.

Usage:
    python scripts/router_cli.py --prompt "your prompt here"
    python scripts/router_cli.py --interactive
    python scripts/router_cli.py --stats
    python scripts/router_cli.py --config
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stillme_core'))

from modules.api_provider_manager import ComplexityAnalyzer, UnifiedAPIManager


class RouterCLI:
    def __init__(self):
        self.manager = UnifiedAPIManager()
        self.analyzer = ComplexityAnalyzer()
        self.session_history = []

    def process_prompt(self, prompt: str, verbose: bool = True) -> dict:
        """Process a single prompt"""
        if verbose:
            print(f"🔍 Processing Prompt: {prompt}")
            print("=" * 60)

        start_time = time.time()

        # Analyze complexity
        complexity_score, breakdown = self.analyzer.analyze_complexity(prompt)

        # Select model
        selected_model = self.manager.choose_model(prompt)

        end_time = time.time()
        analysis_time = end_time - start_time

        # Store in session history
        result = {
            'timestamp': datetime.now(),
            'prompt': prompt,
            'complexity_score': complexity_score,
            'breakdown': breakdown,
            'selected_model': selected_model,
            'analysis_time': analysis_time
        }

        self.session_history.append(result)

        if verbose:
            print("📊 Analysis Results:")
            print(f"  Complexity Score: {complexity_score:.3f}")
            print(f"  Selected Model: {selected_model}")
            print(f"  Analysis Time: {analysis_time*1000:.2f}ms")

            if verbose:
                print("\n🔍 Detailed Breakdown:")
                for key, value in breakdown.items():
                    print(f"  {key}: {value:.3f}")

            # Explain routing decision
            if complexity_score < 0.4:
                routing_reason = "Simple prompt → Local lightweight model (gemma2:2b)"
            elif complexity_score < 0.7:
                routing_reason = "Medium complexity → Local coding model (deepseek-coder:6.7b)"
            else:
                routing_reason = "High complexity → Cloud model (deepseek-chat)"

            print(f"\n💡 Routing Logic: {routing_reason}")

        return result

    def interactive_mode(self):
        """Start interactive mode"""
        print("🔍 AI Router Interactive Mode")
        print("=" * 60)
        print("Enter prompts to test routing decisions...")
        print("Type 'quit' to exit, 'help' for commands")

        while True:
            try:
                prompt = input("\n💬 Enter prompt: ").strip()

                if prompt.lower() == 'quit':
                    break
                elif prompt.lower() == 'help':
                    self._show_help()
                    continue
                elif prompt.lower() == 'stats':
                    self._show_session_stats()
                    continue
                elif prompt.lower() == 'history':
                    self._show_history()
                    continue
                elif prompt.lower() == 'clear':
                    self.session_history.clear()
                    print("✅ Session history cleared")
                    continue
                elif prompt.lower() == 'config':
                    self._show_config()
                    continue
                elif not prompt:
                    continue

                # Process the prompt
                self.process_prompt(prompt, verbose=True)

            except KeyboardInterrupt:
                print("\n\n👋 Interactive mode stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

        # Show final statistics
        self._show_session_stats()

    def _show_help(self):
        """Show help information"""
        print("\n📚 Available Commands:")
        print("  quit     - Exit interactive mode")
        print("  help     - Show this help")
        print("  stats    - Show session statistics")
        print("  history  - Show session history")
        print("  clear    - Clear session history")
        print("  config   - Show current configuration")
        print("\n💡 Tips:")
        print("  - Enter any prompt to test routing")
        print("  - Use 'stats' to see routing patterns")
        print("  - Use 'history' to review past decisions")

    def _show_session_stats(self):
        """Show session statistics"""
        if not self.session_history:
            print("\n📊 No data in current session")
            return

        print("\n📊 Session Statistics")
        print("=" * 40)

        total_prompts = len(self.session_history)
        avg_complexity = sum(r['complexity_score'] for r in self.session_history) / total_prompts
        avg_analysis_time = sum(r['analysis_time'] for r in self.session_history) / total_prompts

        print(f"Total Prompts: {total_prompts}")
        print(f"Average Complexity: {avg_complexity:.3f}")
        print(f"Average Analysis Time: {avg_analysis_time*1000:.2f}ms")

        # Model distribution
        model_counts = {}
        for result in self.session_history:
            model = result['selected_model']
            model_counts[model] = model_counts.get(model, 0) + 1

        print("\n🎯 Model Distribution:")
        for model, count in model_counts.items():
            percentage = (count / total_prompts) * 100
            print(f"  {model}: {count} ({percentage:.1f}%)")

        # Complexity distribution
        complexity_ranges = {
            'Simple (<0.4)': 0,
            'Medium (0.4-0.7)': 0,
            'Complex (≥0.7)': 0
        }

        for result in self.session_history:
            score = result['complexity_score']
            if score < 0.4:
                complexity_ranges['Simple (<0.4)'] += 1
            elif score < 0.7:
                complexity_ranges['Medium (0.4-0.7)'] += 1
            else:
                complexity_ranges['Complex (≥0.7)'] += 1

        print("\n🧠 Complexity Distribution:")
        for range_name, count in complexity_ranges.items():
            percentage = (count / total_prompts) * 100
            print(f"  {range_name}: {count} ({percentage:.1f}%)")

    def _show_history(self):
        """Show session history"""
        if not self.session_history:
            print("\n📊 No history in current session")
            return

        print("\n📊 Session History")
        print("=" * 60)

        for i, result in enumerate(self.session_history, 1):
            timestamp = result['timestamp'].strftime('%H:%M:%S')
            prompt = result['prompt'][:50] + "..." if len(result['prompt']) > 50 else result['prompt']
            model = result['selected_model']
            score = result['complexity_score']

            print(f"{i:2d}. {timestamp} | {prompt} → {model} (score: {score:.3f})")

    def _show_config(self):
        """Show current configuration"""
        print("\n⚙️  Current Configuration")
        print("=" * 40)

        try:
            stats = self.analyzer.get_stats()
            print("🧠 Complexity Analyzer:")
            print(f"  Total Analyses: {stats['performance']['total_analyses']}")
            print(f"  Average Analysis Time: {stats['performance']['avg_time_ms']:.2f}ms")
            print(f"  Fallback Triggers: {stats['fallback']['total_triggers']}")

            print("\n⚙️  Weights:")
            for key, value in stats['weights'].items():
                print(f"  {key}: {value}")

            print("\n🎯 Thresholds:")
            for key, value in stats['thresholds'].items():
                print(f"  {key}: {value}")

            print("\n🤖 Available Models:")
            for i, model in enumerate(self.manager.model_preferences, 1):
                print(f"  {i}. {model}")
        except Exception as e:
            print(f"❌ Error getting configuration: {e}")

    def show_statistics(self):
        """Show current statistics"""
        print("📊 AI Router Statistics")
        print("=" * 60)

        try:
            stats = self.analyzer.get_stats()
            print("🧠 Complexity Analyzer Stats:")
            print(f"  Total Analyses: {stats['performance']['total_analyses']}")
            print(f"  Average Analysis Time: {stats['performance']['avg_time_ms']:.2f}ms")
            print(f"  Fallback Triggers: {stats['fallback']['total_triggers']}")

            print("\n⚙️  Current Configuration:")
            print(f"  Weights: {stats['weights']}")
            print(f"  Thresholds: {stats['thresholds']}")

            print("\n🤖 Available Models:")
            for i, model in enumerate(self.manager.model_preferences, 1):
                print(f"  {i}. {model}")
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")

    def batch_process(self, prompts: list[str]) -> list[dict]:
        """Process multiple prompts in batch"""
        print(f"🔄 Batch Processing {len(prompts)} prompts...")
        print("=" * 60)

        results = []
        for i, prompt in enumerate(prompts, 1):
            print(f"[{i}/{len(prompts)}] Processing: {prompt[:50]}...")
            result = self.process_prompt(prompt, verbose=False)
            results.append(result)

        # Print batch summary
        print("\n📊 Batch Processing Summary")
        print("=" * 40)

        total_prompts = len(results)
        avg_complexity = sum(r['complexity_score'] for r in results) / total_prompts
        avg_analysis_time = sum(r['analysis_time'] for r in results) / total_prompts

        print(f"Total Prompts: {total_prompts}")
        print(f"Average Complexity: {avg_complexity:.3f}")
        print(f"Average Analysis Time: {avg_analysis_time*1000:.2f}ms")

        # Model distribution
        model_counts = {}
        for result in results:
            model = result['selected_model']
            model_counts[model] = model_counts.get(model, 0) + 1

        print("\n🎯 Model Distribution:")
        for model, count in model_counts.items():
            percentage = (count / total_prompts) * 100
            print(f"  {model}: {count} ({percentage:.1f}%)")

        return results

    def export_session(self, filename: str):
        """Export session data to JSON file"""
        export_data = {
            'session_info': {
                'timestamp': datetime.now().isoformat(),
                'total_prompts': len(self.session_history)
            },
            'prompts': [
                {
                    'timestamp': result['timestamp'].isoformat(),
                    'prompt': result['prompt'],
                    'complexity_score': result['complexity_score'],
                    'breakdown': result['breakdown'],
                    'selected_model': result['selected_model'],
                    'analysis_time': result['analysis_time']
                }
                for result in self.session_history
            ]
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Session data exported to {filename}")

    def load_prompts_from_file(self, filename: str) -> list[str]:
        """Load prompts from a text file"""
        try:
            with open(filename, encoding='utf-8') as f:
                prompts = [line.strip() for line in f if line.strip()]

            print(f"✅ Loaded {len(prompts)} prompts from {filename}")
            return prompts
        except Exception as e:
            print(f"❌ Error loading prompts from file: {e}")
            return []

def main():
    parser = argparse.ArgumentParser(description='AI Router Command Line Interface')
    parser.add_argument('--prompt', type=str, help='Process a single prompt')
    parser.add_argument('--interactive', action='store_true', help='Start interactive mode')
    parser.add_argument('--stats', action='store_true', help='Show current statistics')
    parser.add_argument('--config', action='store_true', help='Show current configuration')
    parser.add_argument('--batch', type=str, help='Process prompts from a file')
    parser.add_argument('--export', type=str, help='Export session data to JSON file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    args = parser.parse_args()

    cli = RouterCLI()

    if args.prompt:
        cli.process_prompt(args.prompt, verbose=args.verbose)
    elif args.interactive:
        cli.interactive_mode()
    elif args.stats:
        cli.show_statistics()
    elif args.config:
        cli._show_config()
    elif args.batch:
        prompts = cli.load_prompts_from_file(args.batch)
        if prompts:
            cli.batch_process(prompts)
    else:
        print("Please specify an action:")
        print("  --prompt 'prompt': Process a single prompt")
        print("  --interactive: Start interactive mode")
        print("  --stats: Show current statistics")
        print("  --config: Show current configuration")
        print("  --batch filename: Process prompts from a file")
        print("  --export filename: Export session data")
        print("\nUse --help for more information")
        return

    if args.export:
        cli.export_session(args.export)

if __name__ == "__main__":
    main()
