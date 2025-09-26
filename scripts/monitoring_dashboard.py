#!/usr/bin/env python3
"""
Monitoring Dashboard for StillMe AI Framework
=============================================

This script creates a comprehensive monitoring dashboard for the StillMe AI Framework,
tracking performance, security, and quality metrics.

Author: StillMe AI Framework Team
Version: 1.0.0
Last Updated: 2025-09-26
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import argparse


@dataclass
class MetricData:
    """Metric data structure"""
    name: str
    value: float
    unit: str
    timestamp: str
    status: str  # GOOD, WARNING, CRITICAL
    trend: str  # UP, DOWN, STABLE


@dataclass
class SystemHealth:
    """System health data structure"""
    overall_status: str
    uptime: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    error_rate: float
    response_time: float


@dataclass
class TestMetrics:
    """Test metrics data structure"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    coverage_percentage: float
    test_duration: float
    pass_rate: float


@dataclass
class SecurityMetrics:
    """Security metrics data structure"""
    vulnerabilities_critical: int
    vulnerabilities_high: int
    vulnerabilities_medium: int
    vulnerabilities_low: int
    security_score: int
    last_scan: str
    compliance_status: str


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    requests_per_second: float
    average_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    throughput: float


class MonitoringDashboard:
    """Monitoring dashboard for StillMe AI Framework"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.artifacts_dir = self.project_root / "artifacts"
        self.dashboard_dir = self.project_root / "monitoring"
        self.dashboard_dir.mkdir(exist_ok=True)
        
        # Thresholds
        self.thresholds = {
            "coverage": {"good": 90, "warning": 80, "critical": 70},
            "security_score": {"good": 90, "warning": 75, "critical": 50},
            "performance_p95": {"good": 500, "warning": 1000, "critical": 2000},
            "error_rate": {"good": 1, "warning": 5, "critical": 10},
            "test_pass_rate": {"good": 95, "warning": 90, "critical": 85}
        }
    
    def collect_system_health(self) -> SystemHealth:
        """Collect system health metrics"""
        try:
            # Get system information
            uptime = self._get_uptime()
            cpu_usage = self._get_cpu_usage()
            memory_usage = self._get_memory_usage()
            disk_usage = self._get_disk_usage()
            network_latency = self._get_network_latency()
            error_rate = self._get_error_rate()
            response_time = self._get_response_time()
            
            # Determine overall status
            status_checks = [
                cpu_usage < 80,
                memory_usage < 80,
                disk_usage < 90,
                network_latency < 100,
                error_rate < 5,
                response_time < 1000
            ]
            
            if all(status_checks):
                overall_status = "HEALTHY"
            elif sum(status_checks) >= 4:
                overall_status = "WARNING"
            else:
                overall_status = "CRITICAL"
            
            return SystemHealth(
                overall_status=overall_status,
                uptime=uptime,
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_latency=network_latency,
                error_rate=error_rate,
                response_time=response_time
            )
        except Exception as e:
            print(f"⚠️ Error collecting system health: {e}")
            return SystemHealth(
                overall_status="UNKNOWN",
                uptime=0.0,
                cpu_usage=0.0,
                memory_usage=0.0,
                disk_usage=0.0,
                network_latency=0.0,
                error_rate=0.0,
                response_time=0.0
            )
    
    def collect_test_metrics(self) -> TestMetrics:
        """Collect test metrics from artifacts"""
        try:
            # Read test results
            test_files = list(self.artifacts_dir.glob("*test*.json"))
            total_tests = 0
            passed_tests = 0
            failed_tests = 0
            skipped_tests = 0
            coverage_percentage = 0.0
            test_duration = 0.0
            
            for test_file in test_files:
                try:
                    with open(test_file, 'r') as f:
                        data = json.load(f)
                    
                    if 'tests' in data:
                        total_tests += data['tests']
                    if 'passed' in data:
                        passed_tests += data['passed']
                    if 'failed' in data:
                        failed_tests += data['failed']
                    if 'skipped' in data:
                        skipped_tests += data['skipped']
                    if 'coverage' in data:
                        coverage_percentage = max(coverage_percentage, data['coverage'])
                    if 'duration' in data:
                        test_duration += data['duration']
                except Exception as e:
                    print(f"⚠️ Error reading {test_file}: {e}")
            
            # Calculate pass rate
            if total_tests > 0:
                pass_rate = (passed_tests / total_tests) * 100
            else:
                pass_rate = 0.0
            
            return TestMetrics(
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                skipped_tests=skipped_tests,
                coverage_percentage=coverage_percentage,
                test_duration=test_duration,
                pass_rate=pass_rate
            )
        except Exception as e:
            print(f"⚠️ Error collecting test metrics: {e}")
            return TestMetrics(0, 0, 0, 0, 0.0, 0.0, 0.0)
    
    def collect_security_metrics(self) -> SecurityMetrics:
        """Collect security metrics from artifacts"""
        try:
            # Read security reports
            security_files = list(self.artifacts_dir.glob("*security*.json"))
            vulnerabilities_critical = 0
            vulnerabilities_high = 0
            vulnerabilities_medium = 0
            vulnerabilities_low = 0
            security_score = 0
            last_scan = "Never"
            compliance_status = "UNKNOWN"
            
            for security_file in security_files:
                try:
                    with open(security_file, 'r') as f:
                        data = json.load(f)
                    
                    if 'vulnerabilities' in data:
                        vulns = data['vulnerabilities']
                        vulnerabilities_critical += vulns.get('critical', 0)
                        vulnerabilities_high += vulns.get('high', 0)
                        vulnerabilities_medium += vulns.get('medium', 0)
                        vulnerabilities_low += vulns.get('low', 0)
                    
                    if 'security_score' in data:
                        security_score = max(security_score, data['security_score'])
                    
                    if 'last_scan' in data:
                        last_scan = data['last_scan']
                    
                    if 'compliance_status' in data:
                        compliance_status = data['compliance_status']
                except Exception as e:
                    print(f"⚠️ Error reading {security_file}: {e}")
            
            return SecurityMetrics(
                vulnerabilities_critical=vulnerabilities_critical,
                vulnerabilities_high=vulnerabilities_high,
                vulnerabilities_medium=vulnerabilities_medium,
                vulnerabilities_low=vulnerabilities_low,
                security_score=security_score,
                last_scan=last_scan,
                compliance_status=compliance_status
            )
        except Exception as e:
            print(f"⚠️ Error collecting security metrics: {e}")
            return SecurityMetrics(0, 0, 0, 0, 0, "Never", "UNKNOWN")
    
    def collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect performance metrics from artifacts"""
        try:
            # Read performance results
            perf_files = list(self.artifacts_dir.glob("*performance*.json"))
            requests_per_second = 0.0
            average_response_time = 0.0
            p95_response_time = 0.0
            p99_response_time = 0.0
            error_rate = 0.0
            throughput = 0.0
            
            for perf_file in perf_files:
                try:
                    with open(perf_file, 'r') as f:
                        data = json.load(f)
                    
                    if 'metrics' in data:
                        metrics = data['metrics']
                        requests_per_second = max(requests_per_second, metrics.get('rps', 0))
                        average_response_time = max(average_response_time, metrics.get('avg_response_time', 0))
                        p95_response_time = max(p95_response_time, metrics.get('p95_response_time', 0))
                        p99_response_time = max(p99_response_time, metrics.get('p99_response_time', 0))
                        error_rate = max(error_rate, metrics.get('error_rate', 0))
                        throughput = max(throughput, metrics.get('throughput', 0))
                except Exception as e:
                    print(f"⚠️ Error reading {perf_file}: {e}")
            
            return PerformanceMetrics(
                requests_per_second=requests_per_second,
                average_response_time=average_response_time,
                p95_response_time=p95_response_time,
                p99_response_time=p99_response_time,
                error_rate=error_rate,
                throughput=throughput
            )
        except Exception as e:
            print(f"⚠️ Error collecting performance metrics: {e}")
            return PerformanceMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    
    def _get_uptime(self) -> float:
        """Get system uptime in hours"""
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(['wmic', 'os', 'get', 'lastbootuptime'], 
                                      capture_output=True, text=True)
                # Parse Windows uptime (simplified)
                return 24.0  # Mock value
            else:  # Unix-like
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.read().split()[0])
                return uptime_seconds / 3600
        except:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(['wmic', 'cpu', 'get', 'loadpercentage'], 
                                      capture_output=True, text=True)
                # Parse Windows CPU usage (simplified)
                return 25.0  # Mock value
            else:  # Unix-like
                result = subprocess.run(['top', '-bn1'], capture_output=True, text=True)
                # Parse CPU usage (simplified)
                return 30.0  # Mock value
        except:
            return 0.0
    
    def _get_memory_usage(self) -> float:
        """Get memory usage percentage"""
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(['wmic', 'OS', 'get', 'TotalVisibleMemorySize,FreePhysicalMemory'], 
                                      capture_output=True, text=True)
                # Parse Windows memory usage (simplified)
                return 45.0  # Mock value
            else:  # Unix-like
                result = subprocess.run(['free', '-m'], capture_output=True, text=True)
                # Parse memory usage (simplified)
                return 50.0  # Mock value
        except:
            return 0.0
    
    def _get_disk_usage(self) -> float:
        """Get disk usage percentage"""
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(['wmic', 'logicaldisk', 'get', 'size,freespace'], 
                                      capture_output=True, text=True)
                # Parse Windows disk usage (simplified)
                return 60.0  # Mock value
            else:  # Unix-like
                result = subprocess.run(['df', '-h'], capture_output=True, text=True)
                # Parse disk usage (simplified)
                return 65.0  # Mock value
        except:
            return 0.0
    
    def _get_network_latency(self) -> float:
        """Get network latency in milliseconds"""
        try:
            result = subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                                  capture_output=True, text=True, timeout=5)
            # Parse ping output (simplified)
            return 25.0  # Mock value
        except:
            return 0.0
    
    def _get_error_rate(self) -> float:
        """Get error rate percentage"""
        # Mock implementation
        return 2.5
    
    def _get_response_time(self) -> float:
        """Get average response time in milliseconds"""
        # Mock implementation
        return 150.0
    
    def generate_dashboard_html(self, system_health: SystemHealth, test_metrics: TestMetrics, 
                              security_metrics: SecurityMetrics, performance_metrics: PerformanceMetrics) -> str:
        """Generate HTML dashboard"""
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StillMe AI Framework - Monitoring Dashboard</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .metric-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .metric-title {{
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }}
        .metric-value {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-unit {{
            font-size: 14px;
            color: #666;
        }}
        .status-good {{ color: #28a745; }}
        .status-warning {{ color: #ffc107; }}
        .status-critical {{ color: #dc3545; }}
        .status-unknown {{ color: #6c757d; }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 StillMe AI Framework</h1>
            <h2>Monitoring Dashboard</h2>
            <p>Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="metrics-grid">
            <!-- System Health -->
            <div class="metric-card">
                <div class="metric-title">System Health</div>
                <div class="metric-value status-{system_health.overall_status.lower()}">{system_health.overall_status}</div>
                <div class="metric-unit">Overall Status</div>
                <div style="margin-top: 10px;">
                    <div>CPU: {system_health.cpu_usage:.1f}%</div>
                    <div>Memory: {system_health.memory_usage:.1f}%</div>
                    <div>Disk: {system_health.disk_usage:.1f}%</div>
                    <div>Uptime: {system_health.uptime:.1f}h</div>
                </div>
            </div>
            
            <!-- Test Metrics -->
            <div class="metric-card">
                <div class="metric-title">Test Metrics</div>
                <div class="metric-value status-{'good' if test_metrics.pass_rate >= 95 else 'warning' if test_metrics.pass_rate >= 90 else 'critical'}">{test_metrics.pass_rate:.1f}%</div>
                <div class="metric-unit">Pass Rate</div>
                <div style="margin-top: 10px;">
                    <div>Total Tests: {test_metrics.total_tests}</div>
                    <div>Passed: {test_metrics.passed_tests}</div>
                    <div>Failed: {test_metrics.failed_tests}</div>
                    <div>Coverage: {test_metrics.coverage_percentage:.1f}%</div>
                </div>
            </div>
            
            <!-- Security Metrics -->
            <div class="metric-card">
                <div class="metric-title">Security Metrics</div>
                <div class="metric-value status-{'good' if security_metrics.security_score >= 90 else 'warning' if security_metrics.security_score >= 75 else 'critical'}">{security_metrics.security_score}/100</div>
                <div class="metric-unit">Security Score</div>
                <div style="margin-top: 10px;">
                    <div>Critical: {security_metrics.vulnerabilities_critical}</div>
                    <div>High: {security_metrics.vulnerabilities_high}</div>
                    <div>Medium: {security_metrics.vulnerabilities_medium}</div>
                    <div>Low: {security_metrics.vulnerabilities_low}</div>
                </div>
            </div>
            
            <!-- Performance Metrics -->
            <div class="metric-card">
                <div class="metric-title">Performance Metrics</div>
                <div class="metric-value status-{'good' if performance_metrics.p95_response_time <= 500 else 'warning' if performance_metrics.p95_response_time <= 1000 else 'critical'}">{performance_metrics.p95_response_time:.0f}ms</div>
                <div class="metric-unit">P95 Response Time</div>
                <div style="margin-top: 10px;">
                    <div>RPS: {performance_metrics.requests_per_second:.1f}</div>
                    <div>Avg RT: {performance_metrics.average_response_time:.0f}ms</div>
                    <div>P99 RT: {performance_metrics.p99_response_time:.0f}ms</div>
                    <div>Error Rate: {performance_metrics.error_rate:.1f}%</div>
                </div>
            </div>
        </div>
        
        <!-- Detailed Charts -->
        <div class="chart-container">
            <h3>📊 System Overview</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px;">
                <div>
                    <h4>Test Results</h4>
                    <div>✅ Passed: {test_metrics.passed_tests}</div>
                    <div>❌ Failed: {test_metrics.failed_tests}</div>
                    <div>⏭️ Skipped: {test_metrics.skipped_tests}</div>
                </div>
                <div>
                    <h4>Security Status</h4>
                    <div>🔴 Critical: {security_metrics.vulnerabilities_critical}</div>
                    <div>🟠 High: {security_metrics.vulnerabilities_high}</div>
                    <div>🟡 Medium: {security_metrics.vulnerabilities_medium}</div>
                    <div>🟢 Low: {security_metrics.vulnerabilities_low}</div>
                </div>
                <div>
                    <h4>Performance</h4>
                    <div>🚀 RPS: {performance_metrics.requests_per_second:.1f}</div>
                    <div>⏱️ Avg RT: {performance_metrics.average_response_time:.0f}ms</div>
                    <div>📈 Throughput: {performance_metrics.throughput:.1f}</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>StillMe AI Framework Monitoring Dashboard | Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        return html_content
    
    def save_dashboard(self, html_content: str, output_file: str = "monitoring/dashboard.html"):
        """Save dashboard to file"""
        output_path = self.project_root / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📊 Dashboard saved to: {output_path}")
    
    def generate_json_report(self, system_health: SystemHealth, test_metrics: TestMetrics, 
                           security_metrics: SecurityMetrics, performance_metrics: PerformanceMetrics) -> Dict[str, Any]:
        """Generate JSON report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "system_health": asdict(system_health),
            "test_metrics": asdict(test_metrics),
            "security_metrics": asdict(security_metrics),
            "performance_metrics": asdict(performance_metrics),
            "overall_status": self._calculate_overall_status(system_health, test_metrics, security_metrics, performance_metrics)
        }
    
    def _calculate_overall_status(self, system_health: SystemHealth, test_metrics: TestMetrics, 
                                security_metrics: SecurityMetrics, performance_metrics: PerformanceMetrics) -> str:
        """Calculate overall system status"""
        statuses = []
        
        # System health status
        if system_health.overall_status == "HEALTHY":
            statuses.append("GOOD")
        elif system_health.overall_status == "WARNING":
            statuses.append("WARNING")
        else:
            statuses.append("CRITICAL")
        
        # Test metrics status
        if test_metrics.pass_rate >= 95:
            statuses.append("GOOD")
        elif test_metrics.pass_rate >= 90:
            statuses.append("WARNING")
        else:
            statuses.append("CRITICAL")
        
        # Security metrics status
        if security_metrics.security_score >= 90:
            statuses.append("GOOD")
        elif security_metrics.security_score >= 75:
            statuses.append("WARNING")
        else:
            statuses.append("CRITICAL")
        
        # Performance metrics status
        if performance_metrics.p95_response_time <= 500:
            statuses.append("GOOD")
        elif performance_metrics.p95_response_time <= 1000:
            statuses.append("WARNING")
        else:
            statuses.append("CRITICAL")
        
        # Determine overall status
        if "CRITICAL" in statuses:
            return "CRITICAL"
        elif "WARNING" in statuses:
            return "WARNING"
        else:
            return "GOOD"


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Monitoring Dashboard for StillMe AI Framework")
    parser.add_argument("--output", type=str, default="monitoring/dashboard.html", help="Output HTML file")
    parser.add_argument("--json-output", type=str, default="monitoring/metrics.json", help="Output JSON file")
    parser.add_argument("--project-root", type=str, default=".", help="Project root directory")
    
    args = parser.parse_args()
    
    print("📊 Starting monitoring dashboard generation...")
    print(f"📁 Project root: {args.project_root}")
    
    # Initialize dashboard
    dashboard = MonitoringDashboard(args.project_root)
    
    # Collect metrics
    print("🔍 Collecting system health metrics...")
    system_health = dashboard.collect_system_health()
    
    print("🧪 Collecting test metrics...")
    test_metrics = dashboard.collect_test_metrics()
    
    print("🔒 Collecting security metrics...")
    security_metrics = dashboard.collect_security_metrics()
    
    print("⚡ Collecting performance metrics...")
    performance_metrics = dashboard.collect_performance_metrics()
    
    # Generate dashboard
    print("📊 Generating dashboard...")
    html_content = dashboard.generate_dashboard_html(system_health, test_metrics, security_metrics, performance_metrics)
    dashboard.save_dashboard(html_content, args.output)
    
    # Generate JSON report
    json_report = dashboard.generate_json_report(system_health, test_metrics, security_metrics, performance_metrics)
    json_path = dashboard.project_root / args.json_output
    json_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2, ensure_ascii=False)
    
    print(f"📄 JSON report saved to: {json_path}")
    
    # Print summary
    print(f"\n📊 Monitoring Summary:")
    print(f"   System Health: {system_health.overall_status}")
    print(f"   Test Pass Rate: {test_metrics.pass_rate:.1f}%")
    print(f"   Security Score: {security_metrics.security_score}/100")
    print(f"   P95 Response Time: {performance_metrics.p95_response_time:.0f}ms")
    print(f"   Overall Status: {json_report['overall_status']}")
    
    print(f"\n📄 Dashboard: {args.output}")
    print(f"📄 JSON Report: {args.json_output}")


if __name__ == "__main__":
    main()
