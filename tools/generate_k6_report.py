import json
import csv
import os
import sys
from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def load_k6_summary(summary_path):
    """Load K6 summary JSON"""
    try:
        with open(summary_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Summary file not found: {summary_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"⚠️ Invalid JSON in summary file: {e}")
        return None

def load_k6_results(results_path):
    """Load K6 results JSON"""
    try:
        with open(results_path, 'r') as f:
            return [json.loads(line) for line in f if line.strip()]
    except FileNotFoundError:
        print(f"⚠️ Results file not found: {results_path}")
        return []
    except json.JSONDecodeError as e:
        print(f"⚠️ Invalid JSON in results file: {e}")
        return []

def load_resource_data(resources_path):
    """Load resource monitoring CSV"""
    try:
        df = pd.read_csv(resources_path)
        return df
    except FileNotFoundError:
        print(f"⚠️ Resource data not found: {resources_path}")
        return None
    except Exception as e:
        print(f"⚠️ Error loading resource data: {e}")
        return None

def analyze_k6_metrics(summary, results):
    """Analyze K6 metrics and extract key performance indicators"""
    metrics = {}

    if summary:
        # Extract metrics from summary
        for metric_name, metric_data in summary.get('metrics', {}).items():
            if 'values' in metric_data:
                values = metric_data['values']
                metrics[metric_name] = {
                    'avg': values.get('avg', 0),
                    'min': values.get('min', 0),
                    'max': values.get('max', 0),
                    'p50': values.get('p(50)', 0),
                    'p95': values.get('p(95)', 0),
                    'p99': values.get('p(99)', 0),
                    'count': values.get('count', 0),
                    'rate': values.get('rate', 0)
                }

    # Calculate additional metrics from results
    if results:
        durations = [r.get('data', {}).get('http_req_duration', 0) for r in results if 'data' in r]
        status_codes = [r.get('data', {}).get('http_req_status', 0) for r in results if 'data' in r]

        if durations:
            metrics['calculated'] = {
                'avg_duration': np.mean(durations),
                'p50_duration': np.percentile(durations, 50),
                'p95_duration': np.percentile(durations, 95),
                'p99_duration': np.percentile(durations, 99),
                'error_rate': sum(1 for s in status_codes if s >= 400) / len(status_codes) if status_codes else 0
            }

    return metrics

def create_latency_chart(results, output_dir):
    """Create latency distribution chart"""
    if not results:
        return None

    durations = [r.get('data', {}).get('http_req_duration', 0) for r in results if 'data' in r]
    if not durations:
        return None

    plt.figure(figsize=(10, 6))
    plt.hist(durations, bins=50, alpha=0.7, color='blue', edgecolor='black')
    plt.axvline(np.percentile(durations, 50), color='green', linestyle='--', label='p50')
    plt.axvline(np.percentile(durations, 95), color='orange', linestyle='--', label='p95')
    plt.axvline(np.percentile(durations, 99), color='red', linestyle='--', label='p99')
    plt.xlabel('Response Time (ms)')
    plt.ylabel('Frequency')
    plt.title('Response Time Distribution')
    plt.legend()
    plt.grid(True, alpha=0.3)

    chart_path = os.path.join(output_dir, 'latency_p50_p95_p99.png')
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()

    return chart_path

def create_rps_chart(results, output_dir):
    """Create RPS over time chart"""
    if not results:
        return None

    # Group results by time windows
    timestamps = [r.get('time', 0) for r in results if 'time' in r]
    if not timestamps:
        return None

    # Create time windows (every 10 seconds)
    start_time = min(timestamps)
    end_time = max(timestamps)
    window_size = 10000000000  # 10 seconds in nanoseconds

    windows = []
    rps_values = []

    current_time = start_time
    while current_time < end_time:
        window_end = current_time + window_size
        window_requests = [r for r in results if current_time <= r.get('time', 0) < window_end]
        rps = len(window_requests) / 10  # 10 second window

        windows.append(datetime.fromtimestamp(current_time / 1000000000))
        rps_values.append(rps)
        current_time = window_end

    plt.figure(figsize=(12, 6))
    plt.plot(windows, rps_values, linewidth=2, color='blue')
    plt.xlabel('Time')
    plt.ylabel('Requests per Second')
    plt.title('Request Rate Over Time')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)

    chart_path = os.path.join(output_dir, 'rps_over_time.png')
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()

    return chart_path

def create_error_rate_chart(results, output_dir):
    """Create error rate over time chart"""
    if not results:
        return None

    # Group results by time windows
    timestamps = [r.get('time', 0) for r in results if 'time' in r]
    if not timestamps:
        return None

    start_time = min(timestamps)
    end_time = max(timestamps)
    window_size = 10000000000  # 10 seconds in nanoseconds

    windows = []
    error_rates = []

    current_time = start_time
    while current_time < end_time:
        window_end = current_time + window_size
        window_requests = [r for r in results if current_time <= r.get('time', 0) < window_end]

        if window_requests:
            errors = sum(1 for r in window_requests if r.get('data', {}).get('http_req_status', 200) >= 400)
            error_rate = errors / len(window_requests) * 100
        else:
            error_rate = 0

        windows.append(datetime.fromtimestamp(current_time / 1000000000))
        error_rates.append(error_rate)
        current_time = window_end

    plt.figure(figsize=(12, 6))
    plt.plot(windows, error_rates, linewidth=2, color='red')
    plt.axhline(y=1, color='orange', linestyle='--', label='1% threshold')
    plt.xlabel('Time')
    plt.ylabel('Error Rate (%)')
    plt.title('Error Rate Over Time')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.legend()

    chart_path = os.path.join(output_dir, 'error_rate_over_time.png')
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()

    return chart_path

def create_resource_chart(resource_df, output_dir):
    """Create CPU/RAM usage chart"""
    if resource_df is None or resource_df.empty:
        return None

    plt.figure(figsize=(12, 8))

    # Convert timestamp to datetime
    resource_df['datetime'] = pd.to_datetime(resource_df['ts'], unit='s')

    plt.subplot(2, 1, 1)
    plt.plot(resource_df['datetime'], resource_df['cpu_percent'], linewidth=2, color='blue')
    plt.ylabel('CPU Usage (%)')
    plt.title('CPU Usage Over Time')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)

    plt.subplot(2, 1, 2)
    plt.plot(resource_df['datetime'], resource_df['mem_percent'], linewidth=2, color='green')
    plt.ylabel('RAM Usage (%)')
    plt.xlabel('Time')
    plt.title('RAM Usage Over Time')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)

    plt.tight_layout()

    chart_path = os.path.join(output_dir, 'cpu_ram_trend.png')
    plt.savefig(chart_path, dpi=300, bbox_inches='tight')
    plt.close()

    return chart_path

def generate_markdown_report(metrics, charts, output_dir):
    """Generate comprehensive Markdown report"""
    report_path = os.path.join(output_dir, '..', 'clarification_seal_report.md')

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# 🧪 K6 SEAL-GRADE Test Report - Phase 3 Clarification Core\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Summary table
        f.write("## 📊 Executive Summary\n\n")
        f.write("| Metric | Target | Actual | Status |\n")
        f.write("|--------|--------|--------|--------|\n")

        # Extract key metrics
        p95_latency = metrics.get('http_req_duration', {}).get('p95', 0)
        p99_latency = metrics.get('http_req_duration', {}).get('p99', 0)
        error_rate = metrics.get('http_req_failed', {}).get('rate', 0) * 100
        rps = metrics.get('http_reqs', {}).get('rate', 0)

        # Check thresholds
        p95_pass = p95_latency < 500
        p99_pass = p99_latency < 1000
        error_pass = error_rate < 1
        rps_pass = rps >= 200

        f.write(f"| P95 Latency | < 500ms | {p95_latency:.2f}ms | {'✅ PASS' if p95_pass else '❌ FAIL'} |\n")
        f.write(f"| P99 Latency | < 1000ms | {p99_latency:.2f}ms | {'✅ PASS' if p99_pass else '❌ FAIL'} |\n")
        f.write(f"| Error Rate | < 1% | {error_rate:.2f}% | {'✅ PASS' if error_pass else '❌ FAIL'} |\n")
        f.write(f"| Throughput | ≥ 200 RPS | {rps:.2f} RPS | {'✅ PASS' if rps_pass else '❌ FAIL'} |\n")

        # Overall result
        overall_pass = p95_pass and p99_pass and error_pass and rps_pass
        f.write(f"\n**Overall Result**: {'✅ SEAL-GRADE PASSED' if overall_pass else '❌ SEAL-GRADE FAILED'}\n\n")

        # Detailed metrics
        f.write("## 📈 Detailed Metrics\n\n")
        f.write("### Performance Metrics\n")
        f.write(f"- **Total Requests**: {metrics.get('http_reqs', {}).get('count', 0):,}\n")
        f.write(f"- **Average RPS**: {rps:.2f}\n")
        f.write(f"- **P50 Latency**: {metrics.get('http_req_duration', {}).get('p50', 0):.2f}ms\n")
        f.write(f"- **P95 Latency**: {p95_latency:.2f}ms\n")
        f.write(f"- **P99 Latency**: {p99_latency:.2f}ms\n")
        f.write(f"- **Error Rate**: {error_rate:.2f}%\n\n")

        # Charts
        f.write("## 📊 Performance Charts\n\n")
        for chart_name, chart_path in charts.items():
            if chart_path:
                f.write(f"### {chart_name.replace('_', ' ').title()}\n")
                f.write(f"![{chart_name}]({os.path.basename(chart_path)})\n\n")

        # Analysis
        f.write("## 🔍 Analysis\n\n")
        if not overall_pass:
            f.write("### Issues Identified:\n")
            if not p95_pass:
                f.write(f"- **P95 Latency**: {p95_latency:.2f}ms exceeds 500ms threshold\n")
            if not p99_pass:
                f.write(f"- **P99 Latency**: {p99_latency:.2f}ms exceeds 1000ms threshold\n")
            if not error_pass:
                f.write(f"- **Error Rate**: {error_rate:.2f}% exceeds 1% threshold\n")
            if not rps_pass:
                f.write(f"- **Throughput**: {rps:.2f} RPS below 200 RPS threshold\n")

        f.write("\n### Recommendations:\n")
        if not p95_pass or not p99_pass:
            f.write("- Optimize API response time (database queries, caching)\n")
        if not error_pass:
            f.write("- Investigate error causes and improve error handling\n")
        if not rps_pass:
            f.write("- Scale horizontally or optimize server performance\n")

        f.write("\n## 🎯 SEAL-GRADE Compliance\n\n")
        f.write(f"**Status**: {'✅ COMPLIANT' if overall_pass else '❌ NON-COMPLIANT'}\n\n")
        f.write("**Requirements Met**:\n")
        f.write(f"- ✅ Performance: {'PASS' if p95_pass and p99_pass else 'FAIL'}\n")
        f.write(f"- ✅ Reliability: {'PASS' if error_pass else 'FAIL'}\n")
        f.write(f"- ✅ Scalability: {'PASS' if rps_pass else 'FAIL'}\n")

    return report_path

def main():
    """Main function to generate K6 report"""
    print("🔍 Generating K6 SEAL-GRADE Test Report...")

    # File paths
    summary_path = "reports/k6_seal_test/summary.json"
    results_path = "reports/k6_seal_test/results.json"
    resources_path = "reports/k6_seal_test/resources.csv"
    output_dir = "reports/k6_seal_test"

    # Load data
    summary = load_k6_summary(summary_path)
    results = load_k6_results(results_path)
    resource_df = load_resource_data(resources_path)

    # Analyze metrics
    metrics = analyze_k6_metrics(summary, results)

    # Create charts
    charts = {}
    charts['latency_distribution'] = create_latency_chart(results, output_dir)
    charts['rps_over_time'] = create_rps_chart(results, output_dir)
    charts['error_rate_over_time'] = create_error_rate_chart(results, output_dir)
    charts['resource_usage'] = create_resource_chart(resource_df, output_dir)

    # Generate report
    report_path = generate_markdown_report(metrics, charts, output_dir)

    # Save raw metrics
    results_path = os.path.join(output_dir, '..', 'clarification_seal_results.json')
    with open(results_path, 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f"✅ Report generated: {report_path}")
    print(f"✅ Raw metrics saved: {results_path}")

    # Print summary
    if metrics:
        p95 = metrics.get('http_req_duration', {}).get('p95', 0)
        p99 = metrics.get('http_req_duration', {}).get('p99', 0)
        error_rate = metrics.get('http_req_failed', {}).get('rate', 0) * 100
        rps = metrics.get('http_reqs', {}).get('rate', 0)

        overall_pass = p95 < 500 and p99 < 1000 and error_rate < 1 and rps >= 200

        print(f"\n📊 K6 SEAL-GRADE Test Summary:")
        print(f"   P95 Latency: {p95:.2f}ms {'✅' if p95 < 500 else '❌'}")
        print(f"   P99 Latency: {p99:.2f}ms {'✅' if p99 < 1000 else '❌'}")
        print(f"   Error Rate: {error_rate:.2f}% {'✅' if error_rate < 1 else '❌'}")
        print(f"   Throughput: {rps:.2f} RPS {'✅' if rps >= 200 else '❌'}")
        print(f"   Overall: {'✅ SEAL-GRADE PASSED' if overall_pass else '❌ SEAL-GRADE FAILED'}")

    return report_path, results_path

if __name__ == "__main__":
    main()
