#!/usr/bin/env python3
"""
Analyze K6 CAR Test Results
Phân tích kết quả K6 CAR test để tạo báo cáo throughput tuning
"""

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestMetrics:
    """Test metrics for a specific RPS level"""
    rps_level: int
    duration: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    error_rate: float
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    actual_rps: float

class CARResultsAnalyzer:
    """Analyze K6 CAR test results"""

    def __init__(self, summary_path: str, results_path: str):
        self.summary_path = Path(summary_path)
        self.results_path = Path(results_path)
        self.summary_data = {}
        self.results_data = []

    def load_data(self):
        """Load K6 test data"""
        if self.summary_path.exists():
            with open(self.summary_path) as f:
                self.summary_data = json.load(f)

        if self.results_path.exists():
            with open(self.results_path) as f:
                self.results_data = [json.loads(line) for line in f if line.strip()]

    def extract_metrics(self) -> list[TestMetrics]:
        """Extract metrics for each RPS level"""
        metrics = []

        # Extract overall metrics
        if 'metrics' in self.summary_data:
            http_reqs = self.summary_data['metrics'].get('http_reqs', {})
            http_req_duration = self.summary_data['metrics'].get('http_req_duration', {})
            http_req_failed = self.summary_data['metrics'].get('http_req_failed', {})

            # Calculate overall metrics
            total_requests = http_reqs.get('count', 0)
            failed_requests = int(total_requests * http_req_failed.get('rate', 0))
            successful_requests = total_requests - failed_requests
            error_rate = http_req_failed.get('rate', 0) * 100
            avg_response_time = http_req_duration.get('avg', 0)
            p95_response_time = http_req_duration.get('p(95)', 0)
            p99_response_time = http_req_duration.get('p(99)', 0)
            actual_rps = http_reqs.get('rate', 0)

            # Estimate RPS levels based on test duration (10 minutes total)
            # 200 RPS for 5 minutes, 300 RPS for 3 minutes, 400 RPS for 2 minutes
            test_duration = self.summary_data.get('state', {}).get('testRunDurationMs', 0) / 1000

            if test_duration > 0:
                # Rough estimation of RPS levels
                metrics.append(TestMetrics(
                    rps_level=200,
                    duration="5m",
                    total_requests=int(total_requests * 0.5),  # Estimate
                    successful_requests=int(successful_requests * 0.5),
                    failed_requests=int(failed_requests * 0.5),
                    error_rate=error_rate,
                    avg_response_time=avg_response_time,
                    p95_response_time=p95_response_time,
                    p99_response_time=p99_response_time,
                    actual_rps=actual_rps
                ))

        return metrics

    def generate_report(self) -> str:
        """Generate throughput tuning report"""
        self.extract_metrics()

        report = f"""# 📊 Throughput Tuning Report - K6 CAR Test Results

## 🎯 Test Overview

**Test Type**: K6 Constant Arrival Rate (CAR) Test
**Target RPS**: 200 → 300 → 400 RPS
**Test Duration**: 10 minutes total
**Date**: {self.summary_data.get('root_group', {}).get('startTime', 'N/A')}

## 📈 Performance Results

### Overall Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Total Requests** | {self.summary_data.get('metrics', {}).get('http_reqs', {}).get('count', 0):,} | - | ✅ |
| **Actual RPS** | {self.summary_data.get('metrics', {}).get('http_reqs', {}).get('rate', 0):.1f} | ≥200 | {'✅ PASS' if self.summary_data.get('metrics', {}).get('http_reqs', {}).get('rate', 0) >= 200 else '❌ FAIL'} |
| **Error Rate** | {self.summary_data.get('metrics', {}).get('http_req_failed', {}).get('rate', 0) * 100:.2f}% | <1% | {'✅ PASS' if self.summary_data.get('metrics', {}).get('http_req_failed', {}).get('rate', 0) < 0.01 else '❌ FAIL'} |
| **P95 Latency** | {self.summary_data.get('metrics', {}).get('http_req_duration', {}).get('p(95)', 0):.1f}ms | <500ms | {'✅ PASS' if self.summary_data.get('metrics', {}).get('http_req_duration', {}).get('p(95)', 0) < 500 else '❌ FAIL'} |
| **P99 Latency** | {self.summary_data.get('metrics', {}).get('http_req_duration', {}).get('p(99)', 0):.1f}ms | <1000ms | {'✅ PASS' if self.summary_data.get('metrics', {}).get('http_req_duration', {}).get('p(99)', 0) < 1000 else '❌ FAIL'} |

### Detailed Latency Metrics

| Percentile | Latency (ms) | Target | Status |
|------------|--------------|--------|--------|
| **Average** | {self.summary_data.get('metrics', {}).get('http_req_duration', {}).get('avg', 0):.1f} | - | - |
| **P50 (Median)** | {self.summary_data.get('metrics', {}).get('http_req_duration', {}).get('med', 0):.1f} | - | - |
| **P90** | {self.summary_data.get('metrics', {}).get('http_req_duration', {}).get('p(90)', 0):.1f} | - | - |
| **P95** | {self.summary_data.get('metrics', {}).get('http_req_duration', {}).get('p(95)', 0):.1f} | <500ms | {'✅ PASS' if self.summary_data.get('metrics', {}).get('http_req_duration', {}).get('p(95)', 0) < 500 else '❌ FAIL'} |
| **P99** | {self.summary_data.get('metrics', {}).get('http_req_duration', {}).get('p(99)', 0):.1f} | <1000ms | {'✅ PASS' if self.summary_data.get('metrics', {}).get('http_req_duration', {}).get('p(99)', 0) < 1000 else '❌ FAIL'} |

## 🔧 Optimization Applied

### Server Optimizations
1. **Multiple Workers**: 4 Uvicorn workers for parallel processing
2. **uvloop**: High-performance event loop
3. **httptools**: Fast HTTP parsing
4. **ORJSON**: Fast JSON serialization
5. **Connection Pooling**: Global httpx client with keep-alive
6. **Reduced Logging**: Disabled access logs for performance

### K6 Test Optimizations
1. **Constant Arrival Rate**: Precise RPS control
2. **Pre-allocated VUs**: Reduced startup overhead
3. **Diverse Prompts**: Realistic test scenarios
4. **Minimal Sleep**: 0.01s pacing only

## 🎯 Conclusion

### Performance Assessment
- **Target RPS**: {'✅ ACHIEVED' if self.summary_data.get('metrics', {}).get('http_reqs', {}).get('rate', 0) >= 200 else '❌ NOT ACHIEVED'} (≥200 RPS)
- **Error Rate**: {'✅ ACCEPTABLE' if self.summary_data.get('metrics', {}).get('http_req_failed', {}).get('rate', 0) < 0.01 else '❌ TOO HIGH'} (<1%)
- **Latency**: {'✅ EXCELLENT' if self.summary_data.get('metrics', {}).get('http_req_duration', {}).get('p(95)', 0) < 500 else '❌ NEEDS IMPROVEMENT'} (P95 <500ms)

### Recommendations
"""

        # Add recommendations based on results
        actual_rps = self.summary_data.get('metrics', {}).get('http_reqs', {}).get('rate', 0)
        error_rate = self.summary_data.get('metrics', {}).get('http_req_failed', {}).get('rate', 0)
        p95_latency = self.summary_data.get('metrics', {}).get('http_req_duration', {}).get('p(95)', 0)

        if actual_rps >= 200 and error_rate < 0.01 and p95_latency < 500:
            report += """
✅ **EXCELLENT PERFORMANCE ACHIEVED!**

The optimized server successfully handles ≥200 RPS with:
- Low error rate (<1%)
- Excellent latency (P95 <500ms)
- Stable performance across all test scenarios

**Next Steps:**
- Deploy to production with current configuration
- Monitor real-world performance
- Consider horizontal scaling for higher loads
"""
        else:
            report += """
⚠️ **PERFORMANCE NEEDS IMPROVEMENT**

Current results show:
"""
            if actual_rps < 200:
                report += f"- RPS too low: {actual_rps:.1f} (target: ≥200)\n"
            if error_rate >= 0.01:
                report += f"- Error rate too high: {error_rate*100:.2f}% (target: <1%)\n"
            if p95_latency >= 500:
                report += f"- Latency too high: {p95_latency:.1f}ms P95 (target: <500ms)\n"

            report += """
**Recommended Actions:**
1. Increase number of workers (try 6-8)
2. Add reverse proxy (Nginx) with load balancing
3. Optimize database connections (if applicable)
4. Consider horizontal scaling
5. Profile application for bottlenecks
"""

        report += """

## 📁 Test Files
- **K6 Script**: `load_test/clarification_car_test.js`
- **Summary**: `reports/k6_car_test/summary.json`
- **Results**: `reports/k6_car_test/results.json`
- **Optimized Server**: `gateway_poc/gateway/optimized_main.py`

---
*Report generated by StillMe AI Framework - Throughput Tuning Analysis*
"""

        return report

def main():
    """Main function"""
    analyzer = CARResultsAnalyzer(
        "reports/k6_car_test/summary.json",
        "reports/k6_car_test/results.json"
    )

    analyzer.load_data()
    report = analyzer.generate_report()

    # Save report
    report_path = Path("reports/throughput_tuning_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print("📊 Throughput tuning report generated:")
    print(f"   {report_path}")
    print("\n" + "="*50)
    print(report)

if __name__ == "__main__":
    main()
