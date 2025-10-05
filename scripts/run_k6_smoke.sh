#!/bin/bash

# K6 Smoke Test Script for StillMe
# Runs load tests and generates reports

set -e

# Configuration
K6_SCRIPT="tests/load/k6_smoke_test.js"
OUTPUT_DIR="artifacts/k6"
REPORT_FILE="$OUTPUT_DIR/smoke_test_report.json"
SUMMARY_FILE="$OUTPUT_DIR/smoke_test_summary.md"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "🚀 Starting K6 Smoke Tests for StillMe..."

# Check if K6 is installed
if ! command -v k6 &> /dev/null; then
    echo "❌ K6 is not installed. Please install K6 first."
    echo "   Visit: https://k6.io/docs/getting-started/installation/"
    exit 1
fi

# Check if test script exists
if [ ! -f "$K6_SCRIPT" ]; then
    echo "❌ K6 test script not found: $K6_SCRIPT"
    echo "   Creating a basic smoke test script..."
    
    mkdir -p "$(dirname "$K6_SCRIPT")"
    cat > "$K6_SCRIPT" << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');

export let options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 10 },   // Stay at 10 users
    { duration: '30s', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.01'],   // Error rate must be below 1%
    errors: ['rate<0.01'],            // Custom error rate below 1%
  },
};

export default function() {
  // Test health endpoints
  let healthResponse = http.get('http://localhost:8080/healthz');
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 100ms': (r) => r.timings.duration < 100,
  });
  errorRate.add(healthResponse.status !== 200);

  // Test readiness endpoint
  let readyResponse = http.get('http://localhost:8080/readyz');
  check(readyResponse, {
    'readiness check status is 200': (r) => r.status === 200,
    'readiness check response time < 200ms': (r) => r.timings.duration < 200,
  });
  errorRate.add(readyResponse.status !== 200);

  // Test metrics endpoint
  let metricsResponse = http.get('http://localhost:8080/metrics');
  check(metricsResponse, {
    'metrics endpoint status is 200': (r) => r.status === 200,
    'metrics endpoint response time < 300ms': (r) => r.timings.duration < 300,
  });
  errorRate.add(metricsResponse.status !== 200);

  // Test main application endpoint (if available)
  let appResponse = http.get('http://localhost:8080/');
  check(appResponse, {
    'main app status is 200': (r) => r.status === 200,
    'main app response time < 500ms': (r) => r.timings.duration < 500,
  });
  errorRate.add(appResponse.status !== 200);

  sleep(1);
}
EOF
fi

# Run K6 tests
echo "📊 Running K6 smoke tests..."
k6 run \
  --out json="$REPORT_FILE" \
  --summary-export="$OUTPUT_DIR/summary.json" \
  "$K6_SCRIPT"

# Check if K6 run was successful
if [ $? -eq 0 ]; then
    echo "✅ K6 smoke tests completed successfully"
else
    echo "❌ K6 smoke tests failed"
    exit 1
fi

# Generate summary report
echo "📝 Generating summary report..."
cat > "$SUMMARY_FILE" << EOF
# K6 Smoke Test Summary

**Test Date:** $(date)
**Test Duration:** $(jq -r '.root_group.duration // "N/A"' "$OUTPUT_DIR/summary.json")
**Total Requests:** $(jq -r '.metrics.http_reqs.values.count // "N/A"' "$OUTPUT_DIR/summary.json")

## Performance Metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| P95 Latency | $(jq -r '.metrics.http_req_duration.values.p95 // "N/A"' "$OUTPUT_DIR/summary.json")ms | < 500ms | $(if [ $(jq -r '.metrics.http_req_duration.values.p95 // 999' "$OUTPUT_DIR/summary.json") -lt 500 ]; then echo "✅ PASS"; else echo "❌ FAIL"; fi) |
| Error Rate | $(jq -r '.metrics.http_req_failed.values.rate // "N/A"' "$OUTPUT_DIR/summary.json") | < 1% | $(if [ $(echo "$(jq -r '.metrics.http_req_failed.values.rate // 1' "$OUTPUT_DIR/summary.json") < 0.01" | bc -l) ]; then echo "✅ PASS"; else echo "❌ FAIL"; fi) |
| Requests/sec | $(jq -r '.metrics.http_reqs.values.rate // "N/A"' "$OUTPUT_DIR/summary.json") | > 10 | $(if [ $(echo "$(jq -r '.metrics.http_reqs.values.rate // 0' "$OUTPUT_DIR/summary.json") > 10" | bc -l) ]; then echo "✅ PASS"; else echo "❌ FAIL"; fi) |

## Test Results

- **Health Check:** $(jq -r '.root_group.checks["health check status is 200"].passes // 0' "$OUTPUT_DIR/summary.json")/$(jq -r '.root_group.checks["health check status is 200"].passes + .root_group.checks["health check status is 200"].fails' "$OUTPUT_DIR/summary.json") passed
- **Readiness Check:** $(jq -r '.root_group.checks["readiness check status is 200"].passes // 0' "$OUTPUT_DIR/summary.json")/$(jq -r '.root_group.checks["readiness check status is 200"].passes + .root_group.checks["readiness check status is 200"].fails' "$OUTPUT_DIR/summary.json") passed
- **Metrics Endpoint:** $(jq -r '.root_group.checks["metrics endpoint status is 200"].passes // 0' "$OUTPUT_DIR/summary.json")/$(jq -r '.root_group.checks["metrics endpoint status is 200"].passes + .root_group.checks["metrics endpoint status is 200"].fails' "$OUTPUT_DIR/summary.json") passed

## SLO Compliance

- **P95 Latency < 500ms:** $(if [ $(jq -r '.metrics.http_req_duration.values.p95 // 999' "$OUTPUT_DIR/summary.json") -lt 500 ]; then echo "✅ PASS"; else echo "❌ FAIL"; fi)
- **Error Rate < 1%:** $(if [ $(echo "$(jq -r '.metrics.http_req_failed.values.rate // 1' "$OUTPUT_DIR/summary.json") < 0.01" | bc -l) ]; then echo "✅ PASS"; else echo "❌ FAIL"; fi)

## Files Generated

- **Detailed Report:** $REPORT_FILE
- **Summary JSON:** $OUTPUT_DIR/summary.json
- **Summary Markdown:** $SUMMARY_FILE

EOF

echo "📊 K6 smoke test results:"
echo "   - P95 Latency: $(jq -r '.metrics.http_req_duration.values.p95 // "N/A"' "$OUTPUT_DIR/summary.json")ms"
echo "   - Error Rate: $(jq -r '.metrics.http_req_failed.values.rate // "N/A"' "$OUTPUT_DIR/summary.json")"
echo "   - Requests/sec: $(jq -r '.metrics.http_reqs.values.rate // "N/A"' "$OUTPUT_DIR/summary.json")"

echo "✅ K6 smoke tests completed successfully!"
echo "📁 Reports saved to: $OUTPUT_DIR"
