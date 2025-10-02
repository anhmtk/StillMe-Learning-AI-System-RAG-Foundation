#!/usr/bin/env python3
"""
AI Router Dashboard

This script provides a real-time dashboard for monitoring the AI router,
showing performance metrics, routing decisions, and system status.

Usage:
    python scripts/router_dashboard.py --live
    python scripts/router_dashboard.py --stats
    python scripts/router_dashboard.py --monitor
"""

import argparse
import json
import os
import sys
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stillme_core'))

from modules.api_provider_manager import ComplexityAnalyzer, UnifiedAPIManager


class RouterDashboard:
    def __init__(self):
        self.manager = UnifiedAPIManager()
        self.analyzer = ComplexityAnalyzer()
        self.session_data = {
            'prompts': [],
            'routing_decisions': [],
            'performance_metrics': [],
            'start_time': datetime.now()
        }
        self.running = False

    def start_live_dashboard(self, duration: int = 300):
        """Start live dashboard"""
        print("🔴 AI Router Live Dashboard")
        print("=" * 60)
        print("Monitoring router performance in real-time...")
        print("Press Ctrl+C to stop")

        self.running = True
        start_time = time.time()

        try:
            while self.running and (time.time() - start_time) < duration:
                self._update_dashboard()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Dashboard stopped by user")
            self.running = False

        # Print final summary
        self._print_final_summary()

    def _update_dashboard(self):
        """Update dashboard display"""
        # Clear screen (works on most terminals)
        os.system('cls' if os.name == 'nt' else 'clear')

        print("🔴 AI Router Live Dashboard")
        print("=" * 60)
        print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"🕐 Uptime: {self._get_uptime()}")

        # System status
        self._print_system_status()

        # Performance metrics
        self._print_performance_metrics()

        # Recent routing decisions
        self._print_recent_decisions()

        # Statistics
        self._print_statistics()

        print("\n" + "=" * 60)
        print("Press Ctrl+C to stop monitoring")

    def _get_uptime(self) -> str:
        """Get dashboard uptime"""
        uptime = datetime.now() - self.session_data['start_time']
        hours, remainder = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

    def _print_system_status(self):
        """Print system status"""
        print("\n📊 System Status:")

        # Check analyzer status
        try:
            stats = self.analyzer.get_stats()
            print("  🧠 Complexity Analyzer: ✅ Active")
            print(f"  📈 Total Analyses: {stats['performance']['total_analyses']}")
            print(f"  ⚡ Avg Analysis Time: {stats['performance']['avg_time_ms']:.2f}ms")
        except Exception as e:
            print(f"  🧠 Complexity Analyzer: ❌ Error - {e}")

        # Check manager status
        try:
            model_prefs = self.manager.model_preferences
            print("  🎯 Model Manager: ✅ Active")
            print(f"  🤖 Available Models: {len(model_prefs)}")
        except Exception as e:
            print(f"  🎯 Model Manager: ❌ Error - {e}")

    def _print_performance_metrics(self):
        """Print performance metrics"""
        print("\n⚡ Performance Metrics:")

        if self.session_data['performance_metrics']:
            recent_metrics = self.session_data['performance_metrics'][-10:]
            avg_time = sum(m['analysis_time'] for m in recent_metrics) / len(recent_metrics)
            avg_score = sum(m['complexity_score'] for m in recent_metrics) / len(recent_metrics)

            print(f"  📊 Recent Avg Analysis Time: {avg_time*1000:.2f}ms")
            print(f"  🧠 Recent Avg Complexity Score: {avg_score:.3f}")
            print(f"  📈 Total Prompts Processed: {len(self.session_data['prompts'])}")
        else:
            print("  📊 No data available yet")

    def _print_recent_decisions(self):
        """Print recent routing decisions"""
        print("\n🎯 Recent Routing Decisions:")

        if self.session_data['routing_decisions']:
            recent_decisions = self.session_data['routing_decisions'][-5:]
            for decision in recent_decisions:
                timestamp = decision['timestamp'].strftime('%H:%M:%S')
                prompt = decision['prompt'][:30] + "..." if len(decision['prompt']) > 30 else decision['prompt']
                model = decision['selected_model']
                score = decision['complexity_score']

                print(f"  {timestamp} | {prompt} → {model} (score: {score:.3f})")
        else:
            print("  📊 No routing decisions yet")

    def _print_statistics(self):
        """Print statistics"""
        print("\n📈 Statistics:")

        if self.session_data['routing_decisions']:
            # Model distribution
            model_counts = {}
            for decision in self.session_data['routing_decisions']:
                model = decision['selected_model']
                model_counts[model] = model_counts.get(model, 0) + 1

            print("  🤖 Model Distribution:")
            for model, count in model_counts.items():
                percentage = (count / len(self.session_data['routing_decisions'])) * 100
                print(f"    {model}: {count} ({percentage:.1f}%)")

            # Complexity distribution
            complexity_ranges = {
                'Simple (<0.4)': 0,
                'Medium (0.4-0.7)': 0,
                'Complex (≥0.7)': 0
            }

            for decision in self.session_data['routing_decisions']:
                score = decision['complexity_score']
                if score < 0.4:
                    complexity_ranges['Simple (<0.4)'] += 1
                elif score < 0.7:
                    complexity_ranges['Medium (0.4-0.7)'] += 1
                else:
                    complexity_ranges['Complex (≥0.7)'] += 1

            print("  🧠 Complexity Distribution:")
            for range_name, count in complexity_ranges.items():
                percentage = (count / len(self.session_data['routing_decisions'])) * 100
                print(f"    {range_name}: {count} ({percentage:.1f}%)")
        else:
            print("  📊 No statistics available yet")

    def _print_final_summary(self):
        """Print final summary"""
        print("\n📊 Final Summary")
        print("=" * 60)

        if self.session_data['routing_decisions']:
            total_prompts = len(self.session_data['routing_decisions'])
            uptime = datetime.now() - self.session_data['start_time']

            print(f"Total Prompts Processed: {total_prompts}")
            print(f"Total Uptime: {uptime}")
            print(f"Average Prompts/Minute: {total_prompts / (uptime.total_seconds() / 60):.1f}")

            # Model distribution
            model_counts = {}
            for decision in self.session_data['routing_decisions']:
                model = decision['selected_model']
                model_counts[model] = model_counts.get(model, 0) + 1

            print("\nFinal Model Distribution:")
            for model, count in model_counts.items():
                percentage = (count / total_prompts) * 100
                print(f"  {model}: {count} ({percentage:.1f}%)")

            # Performance summary
            if self.session_data['performance_metrics']:
                avg_time = sum(m['analysis_time'] for m in self.session_data['performance_metrics']) / len(self.session_data['performance_metrics'])
                avg_score = sum(m['complexity_score'] for m in self.session_data['performance_metrics']) / len(self.session_data['performance_metrics'])

                print("\nPerformance Summary:")
                print(f"  Average Analysis Time: {avg_time*1000:.2f}ms")
                print(f"  Average Complexity Score: {avg_score:.3f}")
        else:
            print("No data collected during monitoring session")

    def show_statistics(self):
        """Show current statistics"""
        print("📊 AI Router Statistics")
        print("=" * 60)

        # Analyzer statistics
        try:
            stats = self.analyzer.get_stats()
            print("🧠 Complexity Analyzer Stats:")
            print(f"  Total Analyses: {stats['performance']['total_analyses']}")
            print(f"  Average Analysis Time: {stats['performance']['avg_time_ms']:.2f}ms")
            print(f"  Fallback Triggers: {stats['fallback']['total_triggers']}")

            print("\n⚙️  Current Configuration:")
            print(f"  Weights: {stats['weights']}")
            print(f"  Thresholds: {stats['thresholds']}")
        except Exception as e:
            print(f"❌ Error getting analyzer stats: {e}")

        # Model preferences
        try:
            model_prefs = self.manager.model_preferences
            print("\n🤖 Available Models:")
            for i, model in enumerate(model_prefs, 1):
                print(f"  {i}. {model}")
        except Exception as e:
            print(f"❌ Error getting model preferences: {e}")

    def start_monitoring(self, duration: int = 300):
        """Start monitoring mode (collect data without live display)"""
        print(f"📊 AI Router Monitoring Mode (Duration: {duration}s)")
        print("=" * 60)
        print("Collecting data in background...")
        print("Press Ctrl+C to stop")

        self.running = True
        start_time = time.time()

        try:
            while self.running and (time.time() - start_time) < duration:
                # Simulate some activity (in real usage, this would be actual prompts)
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
            self.running = False

        # Print collected data
        self._print_collected_data()

    def _print_collected_data(self):
        """Print collected monitoring data"""
        print("\n📊 Collected Data Summary")
        print("=" * 60)

        if self.session_data['routing_decisions']:
            total_prompts = len(self.session_data['routing_decisions'])
            uptime = datetime.now() - self.session_data['start_time']

            print(f"Total Prompts Processed: {total_prompts}")
            print(f"Total Uptime: {uptime}")
            print(f"Average Prompts/Minute: {total_prompts / (uptime.total_seconds() / 60):.1f}")

            # Model distribution
            model_counts = {}
            for decision in self.session_data['routing_decisions']:
                model = decision['selected_model']
                model_counts[model] = model_counts.get(model, 0) + 1

            print("\nModel Distribution:")
            for model, count in model_counts.items():
                percentage = (count / total_prompts) * 100
                print(f"  {model}: {count} ({percentage:.1f}%)")

            # Complexity distribution
            complexity_ranges = {
                'Simple (<0.4)': 0,
                'Medium (0.4-0.7)': 0,
                'Complex (≥0.7)': 0
            }

            for decision in self.session_data['routing_decisions']:
                score = decision['complexity_score']
                if score < 0.4:
                    complexity_ranges['Simple (<0.4)'] += 1
                elif score < 0.7:
                    complexity_ranges['Medium (0.4-0.7)'] += 1
                else:
                    complexity_ranges['Complex (≥0.7)'] += 1

            print("\nComplexity Distribution:")
            for range_name, count in complexity_ranges.items():
                percentage = (count / total_prompts) * 100
                print(f"  {range_name}: {count} ({percentage:.1f}%)")

            # Performance summary
            if self.session_data['performance_metrics']:
                avg_time = sum(m['analysis_time'] for m in self.session_data['performance_metrics']) / len(self.session_data['performance_metrics'])
                avg_score = sum(m['complexity_score'] for m in self.session_data['performance_metrics']) / len(self.session_data['performance_metrics'])

                print("\nPerformance Summary:")
                print(f"  Average Analysis Time: {avg_time*1000:.2f}ms")
                print(f"  Average Complexity Score: {avg_score:.3f}")
        else:
            print("No data collected during monitoring session")

    def export_data(self, filename: str):
        """Export collected data to JSON file"""
        export_data = {
            'session_info': {
                'start_time': self.session_data['start_time'].isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_prompts': len(self.session_data['routing_decisions'])
            },
            'routing_decisions': [
                {
                    'timestamp': decision['timestamp'].isoformat(),
                    'prompt': decision['prompt'],
                    'complexity_score': decision['complexity_score'],
                    'selected_model': decision['selected_model']
                }
                for decision in self.session_data['routing_decisions']
            ],
            'performance_metrics': self.session_data['performance_metrics']
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Data exported to {filename}")

    def process_prompt(self, prompt: str):
        """Process a prompt and collect data"""
        start_time = time.time()

        # Analyze complexity
        complexity_score, breakdown = self.analyzer.analyze_complexity(prompt)

        # Select model
        selected_model = self.manager.choose_model(prompt)

        end_time = time.time()
        analysis_time = end_time - start_time

        # Store data
        decision = {
            'timestamp': datetime.now(),
            'prompt': prompt,
            'complexity_score': complexity_score,
            'selected_model': selected_model,
            'breakdown': breakdown
        }

        self.session_data['routing_decisions'].append(decision)
        self.session_data['prompts'].append(prompt)

        metric = {
            'timestamp': datetime.now(),
            'analysis_time': analysis_time,
            'complexity_score': complexity_score
        }

        self.session_data['performance_metrics'].append(metric)

        return decision

def main():
    parser = argparse.ArgumentParser(description='AI Router Dashboard')
    parser.add_argument('--live', action='store_true', help='Start live dashboard')
    parser.add_argument('--stats', action='store_true', help='Show current statistics')
    parser.add_argument('--monitor', action='store_true', help='Start monitoring mode')
    parser.add_argument('--duration', type=int, default=300, help='Duration in seconds')
    parser.add_argument('--export', type=str, help='Export data to JSON file')

    args = parser.parse_args()

    dashboard = RouterDashboard()

    if args.live:
        dashboard.start_live_dashboard(args.duration)
    elif args.stats:
        dashboard.show_statistics()
    elif args.monitor:
        dashboard.start_monitoring(args.duration)
    else:
        print("Please specify --live, --stats, or --monitor")
        print("Use --help for more information")
        return

    if args.export:
        dashboard.export_data(args.export)

if __name__ == "__main__":
    main()
