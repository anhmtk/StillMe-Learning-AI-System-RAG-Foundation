#!/bin/bash
# K6 SEAL-GRADE Test Runner for Phase 3 Clarification Core
# ========================================================

set -e

echo "🚀 Starting K6 SEAL-GRADE Test for Phase 3 Clarification Core"
echo "=============================================================="

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
    echo "❌ k6 is not installed. Please install k6 first:"
    echo "   macOS: brew install k6"
    echo "   Windows: choco install k6"
    echo "   Ubuntu: sudo apt install k6"
    exit 1
fi

# Check if Clarification Core API is running
echo "🔍 Checking Clarification Core API availability..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Clarification Core API is not running on localhost:8000"
    echo "   Please start the API server first"
    exit 1
fi

echo "✅ Clarification Core API is running"

# Create reports directory
mkdir -p reports/k6_seal_test

# Run K6 test with multiple outputs
echo "🧪 Running K6 SEAL-GRADE Test..."
echo "   - Duration: ~17 minutes"
echo "   - Max Users: 500 (spike test)"
echo "   - Soak Test: 10 minutes at 100 users"
echo ""

# Run test with JSON output for analysis
k6 run \
  --out json=reports/k6_seal_test/results.json \
  --out prometheus-remote-write \
  load_test/clarification_seal_test.js

echo ""
echo "✅ K6 SEAL-GRADE Test completed!"
echo "📊 Results saved to: reports/k6_seal_test/results.json"
echo "📈 Prometheus metrics exported to: localhost:9090"

# Generate summary report
echo ""
echo "📋 Generating summary report..."
node -e "
const fs = require('fs');
const results = JSON.parse(fs.readFileSync('reports/k6_seal_test/results.json', 'utf8'));

const summary = {
  test_duration: results.metrics.test_duration?.values?.avg || 0,
  total_requests: results.metrics.http_requests?.values?.count || 0,
  request_rate: results.metrics.http_reqs?.values?.rate || 0,
  error_rate: results.metrics.http_req_failed?.values?.rate || 0,
  p95_latency: results.metrics.http_req_duration?.values?.['p(95)'] || 0,
  p99_latency: results.metrics.http_req_duration?.values?.['p(99)'] || 0,
  clarification_success_rate: results.metrics.clarification_success_rate?.values?.rate || 0,
  proactive_suggestion_rate: results.metrics.proactive_suggestion_rate?.values?.rate || 0,
  multimodal_processing_rate: results.metrics.multimodal_processing_rate?.values?.rate || 0
};

console.log('📊 K6 SEAL-GRADE Test Summary:');
console.log('================================');
console.log(\`Test Duration: \${(summary.test_duration / 1000).toFixed(2)}s\`);
console.log(\`Total Requests: \${summary.total_requests}\`);
console.log(\`Request Rate: \${summary.request_rate.toFixed(2)} req/s\`);
console.log(\`Error Rate: \${(summary.error_rate * 100).toFixed(2)}%\`);
console.log(\`P95 Latency: \${summary.p95_latency.toFixed(2)}ms\`);
console.log(\`P99 Latency: \${summary.p99_latency.toFixed(2)}ms\`);
console.log(\`Clarification Success Rate: \${(summary.clarification_success_rate * 100).toFixed(2)}%\`);
console.log(\`Proactive Suggestion Rate: \${(summary.proactive_suggestion_rate * 100).toFixed(2)}%\`);
console.log(\`Multi-Modal Processing Rate: \${(summary.multimodal_processing_rate * 100).toFixed(2)}%\`);

// Check if thresholds are met
const thresholds = {
  error_rate: summary.error_rate < 0.01,
  p95_latency: summary.p95_latency < 500,
  p99_latency: summary.p99_latency < 1000,
  clarification_success: summary.clarification_success_rate > 0.9,
  proactive_suggestion: summary.proactive_suggestion_rate > 0.7,
  multimodal_processing: summary.multimodal_processing_rate > 0.8
};

console.log('');
console.log('🎯 SEAL-GRADE Thresholds:');
console.log('========================');
console.log(\`Error Rate < 1%: \${thresholds.error_rate ? '✅ PASS' : '❌ FAIL'}\`);
console.log(\`P95 Latency < 500ms: \${thresholds.p95_latency ? '✅ PASS' : '❌ FAIL'}\`);
console.log(\`P99 Latency < 1s: \${thresholds.p99_latency ? '✅ PASS' : '❌ FAIL'}\`);
console.log(\`Clarification Success > 90%: \${thresholds.clarification_success ? '✅ PASS' : '❌ FAIL'}\`);
console.log(\`Proactive Suggestion > 70%: \${thresholds.proactive_suggestion ? '✅ PASS' : '❌ FAIL'}\`);
console.log(\`Multi-Modal Processing > 80%: \${thresholds.multimodal_processing ? '✅ PASS' : '❌ FAIL'}\`);

const allPassed = Object.values(thresholds).every(t => t);
console.log('');
console.log(\`🏆 Overall Result: \${allPassed ? '✅ SEAL-GRADE PASSED' : '❌ SEAL-GRADE FAILED'}\`);
"

echo ""
echo "🎉 K6 SEAL-GRADE Test completed successfully!"
echo "📁 Check reports/k6_seal_test/ for detailed results"
