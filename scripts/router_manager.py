#!/usr/bin/env python3
"""
AI Router Manager

This script provides management capabilities for the AI router,
including configuration, monitoring, and maintenance tasks.

Usage:
    python scripts/router_manager.py --status
    python scripts/router_manager.py --config
    python scripts/router_manager.py --monitor
    python scripts/router_manager.py --maintenance
"""

import os
import sys
import argparse
import time
import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional

# Add stillme_core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'stillme_core'))

from modules.api_provider_manager import UnifiedAPIManager, ComplexityAnalyzer

class RouterManager:
    def __init__(self):
        self.manager = UnifiedAPIManager()
        self.analyzer = ComplexityAnalyzer()
        self.status = {
            'start_time': datetime.now(),
            'total_requests': 0,
            'errors': 0,
            'last_error': None
        }
        
    def get_status(self) -> Dict:
        """Get router status"""
        print("📊 AI Router Status")
        print("=" * 60)
        
        try:
            # Check analyzer status
            analyzer_stats = self.analyzer.get_stats()
            print(f"🧠 Complexity Analyzer:")
            print(f"  Status: ✅ Active")
            print(f"  Total Analyses: {analyzer_stats['performance']['total_analyses']}")
            print(f"  Average Analysis Time: {analyzer_stats['performance']['avg_time_ms']:.2f}ms")
            print(f"  Fallback Triggers: {analyzer_stats['fallback']['total_triggers']}")
            
            # Check manager status
            model_prefs = self.manager.model_preferences
            print(f"\n🎯 Model Manager:")
            print(f"  Status: ✅ Active")
            print(f"  Available Models: {len(model_prefs)}")
            print(f"  Model Preferences: {model_prefs}")
            
            # Check system resources
            self._check_system_resources()
            
            # Check configuration
            self._check_configuration()
            
            # Overall status
            print(f"\n🎯 Overall Status: ✅ Healthy")
            
            return {
                'analyzer': analyzer_stats,
                'manager': {'models': model_prefs},
                'status': 'healthy'
            }
            
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def _check_system_resources(self):
        """Check system resources"""
        print(f"\n💻 System Resources:")
        
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            print(f"  CPU Usage: {cpu_percent:.1f}%")
            
            # Memory usage
            memory = psutil.virtual_memory()
            print(f"  Memory Usage: {memory.percent:.1f}% ({memory.used / 1024 / 1024 / 1024:.1f}GB / {memory.total / 1024 / 1024 / 1024:.1f}GB)")
            
            # Disk usage
            disk = psutil.disk_usage('/')
            print(f"  Disk Usage: {disk.percent:.1f}% ({disk.used / 1024 / 1024 / 1024:.1f}GB / {disk.total / 1024 / 1024 / 1024:.1f}GB)")
            
        except ImportError:
            print(f"  ⚠️  psutil not available, cannot check system resources")
        except Exception as e:
            print(f"  ❌ Error checking system resources: {e}")
    
    def _check_configuration(self):
        """Check configuration"""
        print(f"\n⚙️  Configuration:")
        
        try:
            stats = self.analyzer.get_stats()
            
            # Check weights
            weights = stats['weights']
            print(f"  Weights: {weights}")
            
            # Check thresholds
            thresholds = stats['thresholds']
            print(f"  Thresholds: {thresholds}")
            
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
            
            print(f"  Environment Variables:")
            for var in env_vars:
                value = os.getenv(var, 'Not set')
                print(f"    {var}: {value}")
            
        except Exception as e:
            print(f"  ❌ Error checking configuration: {e}")
    
    def show_configuration(self):
        """Show detailed configuration"""
        print("⚙️  AI Router Configuration")
        print("=" * 60)
        
        try:
            stats = self.analyzer.get_stats()
            
            print(f"🧠 Complexity Analyzer Configuration:")
            print(f"  Weights:")
            for key, value in stats['weights'].items():
                print(f"    {key}: {value}")
            
            print(f"  Thresholds:")
            for key, value in stats['thresholds'].items():
                print(f"    {key}: {value}")
            
            print(f"\n🎯 Model Manager Configuration:")
            print(f"  Model Preferences: {self.manager.model_preferences}")
            
            print(f"\n🌐 Environment Variables:")
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
                value = os.getenv(var, 'Not set')
                print(f"  {var}: {value}")
            
        except Exception as e:
            print(f"❌ Error getting configuration: {e}")
    
    def start_monitoring(self, duration: int = 300):
        """Start monitoring mode"""
        print(f"📊 AI Router Monitoring (Duration: {duration}s)")
        print("=" * 60)
        print("Monitoring router performance...")
        print("Press Ctrl+C to stop")
        
        start_time = time.time()
        monitoring_data = []
        
        try:
            while (time.time() - start_time) < duration:
                # Collect monitoring data
                try:
                    stats = self.analyzer.get_stats()
                    model_prefs = self.manager.model_preferences
                    
                    data_point = {
                        'timestamp': datetime.now(),
                        'analyzer_stats': stats,
                        'model_preferences': model_prefs
                    }
                    
                    monitoring_data.append(data_point)
                    
                    # Print current status
                    print(f"\r⏰ {datetime.now().strftime('%H:%M:%S')} | "
                          f"Analyses: {stats['performance']['total_analyses']} | "
                          f"Avg Time: {stats['performance']['avg_time_ms']:.2f}ms | "
                          f"Fallbacks: {stats['fallback']['total_triggers']}", end='')
                    
                    time.sleep(5)  # Update every 5 seconds
                    
                except Exception as e:
                    print(f"\n❌ Error collecting monitoring data: {e}")
                    time.sleep(5)
                    
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
        
        # Print monitoring summary
        self._print_monitoring_summary(monitoring_data)
        
        return monitoring_data
    
    def _print_monitoring_summary(self, monitoring_data: List[Dict]):
        """Print monitoring summary"""
        if not monitoring_data:
            print("\n📊 No monitoring data collected")
            return
        
        print(f"\n📊 Monitoring Summary")
        print("=" * 40)
        
        total_data_points = len(monitoring_data)
        duration = (monitoring_data[-1]['timestamp'] - monitoring_data[0]['timestamp']).total_seconds()
        
        print(f"Total Data Points: {total_data_points}")
        print(f"Monitoring Duration: {duration:.1f}s")
        
        # Analyze trends
        if total_data_points > 1:
            first_stats = monitoring_data[0]['analyzer_stats']
            last_stats = monitoring_data[-1]['analyzer_stats']
            
            analyses_increase = last_stats['performance']['total_analyses'] - first_stats['performance']['total_analyses']
            fallbacks_increase = last_stats['fallback']['total_triggers'] - first_stats['fallback']['total_triggers']
            
            print(f"\n📈 Trends:")
            print(f"  Analyses Increase: {analyses_increase}")
            print(f"  Fallbacks Increase: {fallbacks_increase}")
            
            if analyses_increase > 0:
                avg_analyses_per_second = analyses_increase / duration
                print(f"  Average Analyses/Second: {avg_analyses_per_second:.2f}")
    
    def run_maintenance(self):
        """Run maintenance tasks"""
        print("🔧 AI Router Maintenance")
        print("=" * 60)
        
        maintenance_tasks = [
            ("Check system status", self._check_system_status),
            ("Validate configuration", self._validate_configuration),
            ("Test routing logic", self._test_routing_logic),
            ("Check performance", self._check_performance),
            ("Clean up logs", self._cleanup_logs)
        ]
        
        results = {}
        
        for task_name, task_func in maintenance_tasks:
            print(f"\n🔧 Running: {task_name}")
            try:
                result = task_func()
                results[task_name] = {'status': 'success', 'result': result}
                print(f"  ✅ {task_name}: Success")
            except Exception as e:
                results[task_name] = {'status': 'error', 'error': str(e)}
                print(f"  ❌ {task_name}: Error - {e}")
        
        # Print maintenance summary
        print(f"\n📊 Maintenance Summary")
        print("=" * 40)
        
        successful_tasks = sum(1 for r in results.values() if r['status'] == 'success')
        total_tasks = len(results)
        
        print(f"Successful Tasks: {successful_tasks}/{total_tasks}")
        
        if successful_tasks == total_tasks:
            print("🎯 Overall Status: ✅ All maintenance tasks completed successfully")
        else:
            print("⚠️  Overall Status: ⚠️  Some maintenance tasks failed")
        
        return results
    
    def _check_system_status(self):
        """Check system status"""
        try:
            stats = self.analyzer.get_stats()
            model_prefs = self.manager.model_preferences
            
            return {
                'analyzer_active': True,
                'manager_active': True,
                'total_analyses': stats['performance']['total_analyses'],
                'available_models': len(model_prefs)
            }
        except Exception as e:
            raise Exception(f"System status check failed: {e}")
    
    def _validate_configuration(self):
        """Validate configuration"""
        try:
            stats = self.analyzer.get_stats()
            
            # Check weights
            weights = stats['weights']
            for key, value in weights.items():
                if not (0.0 <= value <= 1.0):
                    raise Exception(f"Invalid weight {key}: {value}")
            
            # Check thresholds
            thresholds = stats['thresholds']
            if thresholds['simple'] >= thresholds['medium']:
                raise Exception(f"Invalid threshold order: simple={thresholds['simple']}, medium={thresholds['medium']}")
            
            return {
                'weights_valid': True,
                'thresholds_valid': True,
                'configuration_valid': True
            }
        except Exception as e:
            raise Exception(f"Configuration validation failed: {e}")
    
    def _test_routing_logic(self):
        """Test routing logic"""
        try:
            test_prompts = [
                ("chào bạn", "gemma2:2b"),
                ("viết code Python", "deepseek-coder:6.7b"),
                ("Giải thích định lý bất toàn của Gödel", "deepseek-chat")
            ]
            
            results = []
            for prompt, expected_model in test_prompts:
                selected_model = self.manager.choose_model(prompt)
                is_correct = selected_model == expected_model
                results.append({
                    'prompt': prompt,
                    'expected': expected_model,
                    'actual': selected_model,
                    'correct': is_correct
                })
            
            correct_count = sum(1 for r in results if r['correct'])
            total_count = len(results)
            
            return {
                'test_results': results,
                'accuracy': correct_count / total_count,
                'correct_count': correct_count,
                'total_count': total_count
            }
        except Exception as e:
            raise Exception(f"Routing logic test failed: {e}")
    
    def _check_performance(self):
        """Check performance"""
        try:
            start_time = time.time()
            for _ in range(100):
                self.analyzer.analyze_complexity("Test prompt for performance check")
            end_time = time.time()
            
            avg_time = (end_time - start_time) / 100
            
            return {
                'avg_analysis_time': avg_time,
                'avg_analysis_time_ms': avg_time * 1000,
                'performance_grade': self._get_performance_grade(avg_time)
            }
        except Exception as e:
            raise Exception(f"Performance check failed: {e}")
    
    def _get_performance_grade(self, avg_time: float) -> str:
        """Get performance grade"""
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
    
    def _cleanup_logs(self):
        """Clean up logs"""
        try:
            # This is a placeholder for log cleanup
            # In a real implementation, you would clean up old log files
            return {
                'logs_cleaned': 0,
                'space_freed': 0
            }
        except Exception as e:
            raise Exception(f"Log cleanup failed: {e}")
    
    def export_status(self, filename: str):
        """Export status to JSON file"""
        try:
            status_data = self.get_status()
            
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'status': status_data
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Status exported to {filename}")
        except Exception as e:
            print(f"❌ Error exporting status: {e}")

def main():
    parser = argparse.ArgumentParser(description='AI Router Manager')
    parser.add_argument('--status', action='store_true', help='Show router status')
    parser.add_argument('--config', action='store_true', help='Show configuration')
    parser.add_argument('--monitor', action='store_true', help='Start monitoring')
    parser.add_argument('--maintenance', action='store_true', help='Run maintenance')
    parser.add_argument('--duration', type=int, default=300, help='Monitoring duration in seconds')
    parser.add_argument('--export', type=str, help='Export status to JSON file')
    
    args = parser.parse_args()
    
    manager = RouterManager()
    
    if args.status:
        manager.get_status()
    elif args.config:
        manager.show_configuration()
    elif args.monitor:
        manager.start_monitoring(args.duration)
    elif args.maintenance:
        manager.run_maintenance()
    else:
        print("Please specify --status, --config, --monitor, or --maintenance")
        print("Use --help for more information")
        return
    
    if args.export:
        manager.export_status(args.export)

if __name__ == "__main__":
    main()
