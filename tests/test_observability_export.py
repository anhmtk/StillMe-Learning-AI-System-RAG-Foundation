"""
Test Suite for Observability Export
===================================

Tests Prometheus metrics export, Grafana dashboard, and alert rules.
Validates observability infrastructure and monitoring capabilities.

Author: StillMe AI Framework
Created: 2025-01-08
"""

import json
import time
import os
import sys
import threading
import requests
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Import metrics server
sys.path.append(str(Path(__file__).parent.parent))
from observability.metrics_server import metrics_collector, start_metrics_server


@dataclass
class ObservabilityTestResult:
    """Result of an observability test"""
    test_name: str
    metric_name: str
    expected_value: Any
    actual_value: Any
    success: bool
    details: Dict[str, Any]


class ObservabilityExportTestSuite:
    """
    Comprehensive observability export test suite
    
    Tests:
    - Prometheus metrics export
    - Grafana dashboard validation
    - Alert rules validation
    - Metrics collection and aggregation
    - Health check endpoints
    """
    
    def __init__(self):
        """Initialize test suite"""
        self.test_results = []
        self.passed_tests = 0
        self.total_tests = 0
        self.metrics_server_process = None
        self.base_url = "http://localhost:9090"
        
    def test_metrics_endpoint(self) -> bool:
        """Test /metrics endpoint availability and format"""
        print("\n=== Testing Metrics Endpoint ===")
        
        passed = 0
        total = 0
        
        # Test metrics endpoint
        total += 1
        try:
            response = requests.get(f"{self.base_url}/metrics", timeout=5)
            
            if response.status_code == 200:
                metrics_text = response.text
                
                # Check for required metrics
                required_metrics = [
                    "requests_total",
                    "requests_duration_seconds",
                    "clarify_trigger_total",
                    "errors_total",
                    "detector_hits_total",
                    "system_uptime_seconds",
                    "system_memory_usage_bytes",
                    "system_cpu_usage_percent"
                ]
                
                missing_metrics = []
                for metric in required_metrics:
                    if metric not in metrics_text:
                        missing_metrics.append(metric)
                
                if not missing_metrics:
                    passed += 1
                    print(f"PASSED: All required metrics present")
                else:
                    print(f"FAILED: Missing metrics: {missing_metrics}")
                    
            else:
                print(f"FAILED: Metrics endpoint returned status {response.status_code}")
                
        except Exception as e:
            print(f"ERROR: Metrics endpoint test failed - {e}")
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Metrics Endpoint: {passed}/{total} ({pass_rate:.1f}%)")
        
        self.test_results.append({
            'test': 'metrics_endpoint',
            'passed': passed,
            'total': total,
            'pass_rate': pass_rate
        })
        
        return pass_rate >= 90.0
    
    def test_health_endpoint(self) -> bool:
        """Test /health endpoint availability and format"""
        print("\n=== Testing Health Endpoint ===")
        
        passed = 0
        total = 0
        
        # Test health endpoint
        total += 1
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            
            if response.status_code == 200:
                health_data = response.json()
                
                # Check for required fields
                required_fields = ["status", "timestamp", "uptime"]
                missing_fields = []
                
                for field in required_fields:
                    if field not in health_data:
                        missing_fields.append(field)
                
                if not missing_fields and health_data["status"] == "healthy":
                    passed += 1
                    print(f"PASSED: Health endpoint returns valid data")
                else:
                    print(f"FAILED: Missing fields or invalid status: {missing_fields}")
                    
            else:
                print(f"FAILED: Health endpoint returned status {response.status_code}")
                
        except Exception as e:
            print(f"ERROR: Health endpoint test failed - {e}")
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Health Endpoint: {passed}/{total} ({pass_rate:.1f}%)")
        
        self.test_results.append({
            'test': 'health_endpoint',
            'passed': passed,
            'total': total,
            'pass_rate': pass_rate
        })
        
        return pass_rate >= 90.0
    
    def test_metrics_collection(self) -> bool:
        """Test metrics collection and aggregation"""
        print("\n=== Testing Metrics Collection ===")
        
        passed = 0
        total = 0
        
        # Test different metric types
        metric_tests = [
            {"name": "requests", "function": lambda: metrics_collector.increment_requests(0.1)},
            {"name": "clarify_trigger", "function": lambda: metrics_collector.increment_clarify_trigger("test")},
            {"name": "errors", "function": lambda: metrics_collector.increment_errors("test_error")},
            {"name": "detector_hits", "function": lambda: metrics_collector.increment_detector_hits("test_detector")},
        ]
        
        for test_config in metric_tests:
            total += 1
            try:
                # Record initial value
                initial_metrics = metrics_collector.get_metrics()
                
                # Increment metric
                test_config["function"]()
                
                # Check if metric was updated
                updated_metrics = metrics_collector.get_metrics()
                
                if updated_metrics != initial_metrics:
                    passed += 1
                    print(f"PASSED: {test_config['name']} metric collection")
                else:
                    print(f"FAILED: {test_config['name']} metric not updated")
                    
            except Exception as e:
                print(f"ERROR: {test_config['name']} metric test failed - {e}")
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Metrics Collection: {passed}/{total} ({pass_rate:.1f}%)")
        
        self.test_results.append({
            'test': 'metrics_collection',
            'passed': passed,
            'total': total,
            'pass_rate': pass_rate
        })
        
        return pass_rate >= 90.0
    
    def test_grafana_dashboard(self) -> bool:
        """Test Grafana dashboard configuration"""
        print("\n=== Testing Grafana Dashboard ===")
        
        passed = 0
        total = 0
        
        # Test dashboard file exists and is valid JSON
        total += 1
        try:
            dashboard_path = Path(__file__).parent.parent / "observability" / "grafana_dashboard.json"
            
            if dashboard_path.exists():
                with open(dashboard_path, 'r') as f:
                    dashboard_data = json.load(f)
                
                # Check for required dashboard fields
                required_fields = ["dashboard"]
                dashboard = dashboard_data.get("dashboard", {})
                dashboard_required_fields = ["title", "panels"]
                
                missing_fields = []
                for field in required_fields:
                    if field not in dashboard_data:
                        missing_fields.append(field)
                
                for field in dashboard_required_fields:
                    if field not in dashboard:
                        missing_fields.append(f"dashboard.{field}")
                
                if not missing_fields and len(dashboard.get("panels", [])) > 0:
                    passed += 1
                    print(f"PASSED: Grafana dashboard configuration valid")
                else:
                    print(f"FAILED: Missing fields or no panels: {missing_fields}")
                    
            else:
                print(f"FAILED: Grafana dashboard file not found")
                
        except Exception as e:
            print(f"ERROR: Grafana dashboard test failed - {e}")
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Grafana Dashboard: {passed}/{total} ({pass_rate:.1f}%)")
        
        self.test_results.append({
            'test': 'grafana_dashboard',
            'passed': passed,
            'total': total,
            'pass_rate': pass_rate
        })
        
        return pass_rate >= 90.0
    
    def test_alert_rules(self) -> bool:
        """Test alert rules configuration"""
        print("\n=== Testing Alert Rules ===")
        
        passed = 0
        total = 0
        
        # Test alert rules file exists and is valid YAML
        total += 1
        try:
            alerts_path = Path(__file__).parent.parent / "observability" / "alerts.yml"
            
            if alerts_path.exists():
                with open(alerts_path, 'r') as f:
                    alerts_content = f.read()
                
                # Check for required alert rules
                required_alerts = [
                    "HighErrorRate",
                    "HighP99Latency",
                    "HighP95Latency",
                    "ServiceDown",
                    "HighMemoryUsage",
                    "HighCPUUsage"
                ]
                
                missing_alerts = []
                for alert in required_alerts:
                    if alert not in alerts_content:
                        missing_alerts.append(alert)
                
                if not missing_alerts:
                    passed += 1
                    print(f"PASSED: All required alert rules present")
                else:
                    print(f"FAILED: Missing alert rules: {missing_alerts}")
                    
            else:
                print(f"FAILED: Alert rules file not found")
                
        except Exception as e:
            print(f"ERROR: Alert rules test failed - {e}")
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Alert Rules: {passed}/{total} ({pass_rate:.1f}%)")
        
        self.test_results.append({
            'test': 'alert_rules',
            'passed': passed,
            'total': total,
            'pass_rate': pass_rate
        })
        
        return pass_rate >= 90.0
    
    def test_metrics_format(self) -> bool:
        """Test Prometheus metrics format compliance"""
        print("\n=== Testing Metrics Format ===")
        
        passed = 0
        total = 0
        
        # Test metrics format
        total += 1
        try:
            metrics_text = metrics_collector.get_metrics()
            
            # Check for Prometheus format compliance
            lines = metrics_text.split('\n')
            format_issues = []
            
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    # Check metric format: name{labels} value
                    if ' ' not in line:
                        format_issues.append(f"Missing value: {line}")
                    else:
                        # Extract metric name (before first space)
                        metric_part = line.split()[0]
                        # Remove labels and check if metric name is valid
                        metric_name = metric_part.split('{')[0]
                        if not metric_name.replace('_', '').isalnum():
                            format_issues.append(f"Invalid metric name: {line}")
            
            if not format_issues:
                passed += 1
                print(f"PASSED: Metrics format is Prometheus compliant")
            else:
                print(f"FAILED: Format issues: {format_issues[:3]}...")  # Show first 3 issues
                
        except Exception as e:
            print(f"ERROR: Metrics format test failed - {e}")
        
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"Metrics Format: {passed}/{total} ({pass_rate:.1f}%)")
        
        self.test_results.append({
            'test': 'metrics_format',
            'passed': passed,
            'total': total,
            'pass_rate': pass_rate
        })
        
        return pass_rate >= 90.0
    
    def _start_metrics_server(self):
        """Start metrics server in background thread"""
        def run_server():
            try:
                start_metrics_server(port=9090)
            except Exception as e:
                print(f"Metrics server error: {e}")
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        time.sleep(2)
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all observability export tests"""
        print("📊 Starting Observability Export Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Start metrics server
        self._start_metrics_server()
        
        # Run all tests
        tests = [
            self.test_metrics_endpoint,
            self.test_health_endpoint,
            self.test_metrics_collection,
            self.test_grafana_dashboard,
            self.test_alert_rules,
            self.test_metrics_format,
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                print(f"ERROR: Test {test.__name__} failed with exception: {e}")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate overall pass rate
        overall_pass_rate = (passed_tests / total_tests) * 100
        
        # Calculate detailed pass rate
        total_passed = sum(result['passed'] for result in self.test_results)
        total_cases = sum(result['total'] for result in self.test_results)
        detailed_pass_rate = (total_passed / total_cases) * 100 if total_cases > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 OBSERVABILITY EXPORT TEST RESULTS")
        print("=" * 60)
        print(f"Overall Pass Rate: {passed_tests}/{total_tests} ({overall_pass_rate:.1f}%)")
        print(f"Detailed Pass Rate: {total_passed}/{total_cases} ({detailed_pass_rate:.1f}%)")
        print(f"Total Duration: {total_duration:.2f}s")
        
        print("\n📋 Test Breakdown:")
        for result in self.test_results:
            print(f"  {result['test']}: {result['passed']}/{result['total']} ({result['pass_rate']:.1f}%)")
        
        # Determine success
        success = overall_pass_rate >= 90.0 and detailed_pass_rate >= 90.0
        
        print(f"\n🎯 Target: 90%+ pass rate")
        print(f"✅ Result: {'PASSED' if success else 'FAILED'}")
        
        return {
            'overall_pass_rate': overall_pass_rate,
            'detailed_pass_rate': detailed_pass_rate,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_cases': total_cases,
            'duration': total_duration,
            'success': success,
            'test_results': self.test_results
        }


if __name__ == "__main__":
    # Run test suite
    test_suite = ObservabilityExportTestSuite()
    results = test_suite.run_all_tests()
    
    # Exit with appropriate code
    exit(0 if results['success'] else 1)
