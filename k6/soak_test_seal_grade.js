/**
 * SEAL-GRADE SYSTEM TESTS - K6 Soak Testing Script
 * Kịch bản kiểm thử soak K6 cho hệ thống SEAL-GRADE
 * 
 * This script performs extended soak testing to identify:
 * - Memory leaks
 * - Performance degradation over time
 * - Resource exhaustion
 * - Stability issues
 * 
 * Kịch bản này thực hiện kiểm thử soak mở rộng để xác định:
 * - Rò rỉ bộ nhớ
 * - Suy giảm hiệu suất theo thời gian
 * - Cạn kiệt tài nguyên
 * - Vấn đề ổn định
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';

// Custom metrics for soak testing
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time');
const memoryUsage = new Gauge('memory_usage');
const cpuUsage = new Gauge('cpu_usage');
const requestCount = new Counter('request_count');
const successCount = new Counter('success_count');
const degradationRate = new Rate('degradation_rate');

// Test configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const SOAK_DURATION = __ENV.SOAK_DURATION || '4h';
const VIRTUAL_USERS = __ENV.VIRTUAL_USERS || 50;
const CHECK_INTERVAL = __ENV.CHECK_INTERVAL || '5m';

// Test scenarios
export const options = {
  scenarios: {
    // Soak test with constant load
    soak_constant: {
      executor: 'constant-vus',
      vus: VIRTUAL_USERS,
      duration: SOAK_DURATION,
      tags: { test_type: 'soak_constant' },
    },
    
    // Soak test with varying load
    soak_varying: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30m', target: 25 },
        { duration: '1h', target: 50 },
        { duration: '1h', target: 75 },
        { duration: '1h', target: 50 },
        { duration: '30m', target: 25 },
      ],
      tags: { test_type: 'soak_varying' },
    },
    
    // Memory leak detection
    memory_leak_test: {
      executor: 'constant-vus',
      vus: 10,
      duration: '2h',
      tags: { test_type: 'memory_leak' },
    },
  },
  
  thresholds: {
    // Soak test thresholds
    http_req_duration: ['p(95)<1000'], // 95% of requests under 1s
    http_req_failed: ['rate<0.05'],    // Error rate under 5%
    error_rate: ['rate<0.05'],         // Custom error rate under 5%
    response_time: ['p(95)<800'],      // Custom response time under 800ms
    degradation_rate: ['rate<0.02'],   // Performance degradation under 2%
    
    // Memory and resource thresholds
    memory_usage: ['value<1000'],      // Memory usage under 1GB
    cpu_usage: ['value<80'],           // CPU usage under 80%
  },
};

// Test data for extended testing
const testPrompts = [
  "Hello, how are you today?",
  "Can you help me with a coding problem?",
  "What's the weather like?",
  "Explain quantum computing in simple terms",
  "Write a Python function to sort a list",
  "Tell me a joke",
  "What are the benefits of renewable energy?",
  "How do I learn machine learning?",
  "Create a recipe for chocolate cake",
  "What's the history of the internet?",
  "Xin chào, hôm nay thế nào?",
  "Bạn có thể giúp tôi không?",
  "Comment allez-vous aujourd'hui?",
  "¿Cómo estás hoy?",
  "今日はどうですか？",
  "How do neural networks work?",
  "What is machine learning?",
  "Explain deep learning concepts",
  "What are the applications of AI?",
  "How to implement a chatbot?",
  "What is natural language processing?",
  "Explain computer vision",
  "What is reinforcement learning?",
  "How to train a model?",
  "What are the challenges in AI?",
];

// Performance baseline tracking
let baselineResponseTime = null;
let baselineMemoryUsage = null;
let baselineCpuUsage = null;

// Helper functions
function getRandomPrompt() {
  return testPrompts[Math.floor(Math.random() * testPrompts.length)];
}

function makeRequest(prompt, testType = 'soak') {
  const payload = JSON.stringify({
    message: prompt,
    target: "stillme-ai",
    from: `soak-test-user-${__VU}-${__ITER}`,
    test_type: testType,
    timestamp: Date.now()
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'K6-SoakTest/1.0',
    },
    timeout: '60s', // Longer timeout for soak test
  };
  
  const startTime = Date.now();
  const response = http.post(`${BASE_URL}/send-message`, payload, params);
  const endTime = Date.now();
  
  // Record metrics
  requestCount.add(1);
  const responseTimeMs = endTime - startTime;
  responseTime.add(responseTimeMs);
  
  // Check for performance degradation
  if (baselineResponseTime && responseTimeMs > baselineResponseTime * 1.5) {
    degradationRate.add(1);
  } else {
    degradationRate.add(0);
  }
  
  // Check response
  const isSuccess = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 1s': (r) => r.timings.duration < 1000,
    'response has content': (r) => r.body && r.body.length > 0,
    'response is JSON': (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch (e) {
        return false;
      }
    },
    'no memory leak indicators': (r) => {
      // Check for signs of memory issues in response
      return !r.body.includes('memory') || !r.body.includes('leak');
    },
  });
  
  if (isSuccess) {
    successCount.add(1);
    errorRate.add(0);
  } else {
    errorRate.add(1);
  }
  
  return response;
}

function testHealthEndpoint() {
  const response = http.get(`${BASE_URL}/health/ai`);
  
  check(response, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 200ms': (r) => r.timings.duration < 200,
    'health check has status': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.status === 'healthy';
      } catch (e) {
        return false;
      }
    },
  });
  
  return response;
}

function testMemoryEndpoint() {
  const response = http.get(`${BASE_URL}/health/memory`);
  
  if (response.status === 200) {
    try {
      const body = JSON.parse(response.body);
      if (body.memory_usage) {
        memoryUsage.add(body.memory_usage);
      }
      if (body.cpu_usage) {
        cpuUsage.add(body.cpu_usage);
      }
    } catch (e) {
      // Ignore parsing errors
    }
  }
  
  return response;
}

function testGatewayEndpoint() {
  const response = http.get(`${BASE_URL}/`);
  
  check(response, {
    'gateway status is 200': (r) => r.status === 200,
    'gateway response time < 300ms': (r) => r.timings.duration < 300,
  });
  
  return response;
}

// Main test function
export default function() {
  // Test type distribution for soak testing
  const testType = Math.random();
  
  if (testType < 0.8) {
    // 80% normal requests
    const prompt = getRandomPrompt();
    makeRequest(prompt, 'soak_normal');
  } else if (testType < 0.9) {
    // 10% health checks
    testHealthEndpoint();
  } else if (testType < 0.95) {
    // 5% memory checks
    testMemoryEndpoint();
  } else {
    // 5% gateway checks
    testGatewayEndpoint();
  }
  
  // Random sleep between requests (2-5 seconds for soak test)
  sleep(Math.random() * 3 + 2);
}

// Setup function
export function setup() {
  console.log('Starting SEAL-GRADE Soak Test');
  console.log(`Base URL: ${BASE_URL}`);
  console.log(`Soak Duration: ${SOAK_DURATION}`);
  console.log(`Virtual Users: ${VIRTUAL_USERS}`);
  
  // Test connectivity and establish baseline
  const healthResponse = http.get(`${BASE_URL}/health/ai`);
  if (healthResponse.status !== 200) {
    throw new Error(`Health check failed: ${healthResponse.status}`);
  }
  
  // Establish performance baseline
  const baselineResponse = http.post(`${BASE_URL}/send-message`, JSON.stringify({
    message: "Baseline test message",
    target: "stillme-ai",
    from: "baseline-test",
    test_type: "baseline"
  }), {
    headers: { 'Content-Type': 'application/json' },
    timeout: '30s'
  });
  
  if (baselineResponse.status === 200) {
    baselineResponseTime = baselineResponse.timings.duration;
    console.log(`Baseline response time: ${baselineResponseTime}ms`);
  }
  
  console.log('Baseline established, starting soak test...');
  return { 
    startTime: Date.now(),
    baselineResponseTime: baselineResponseTime
  };
}

// Teardown function
export function teardown(data) {
  const endTime = Date.now();
  const duration = (endTime - data.startTime) / 1000;
  
  console.log('SEAL-GRADE Soak Test completed');
  console.log(`Total duration: ${duration} seconds`);
  console.log(`Baseline response time: ${data.baselineResponseTime}ms`);
  console.log('Soak test results will be available in the K6 report');
}

// Handle summary
export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    test_type: 'seal_grade_soak_test',
    duration: data.metrics.iteration_duration?.values?.avg || 0,
    requests: data.metrics.http_reqs?.values?.count || 0,
    requests_per_second: data.metrics.http_reqs?.values?.rate || 0,
    response_time_p95: data.metrics.http_req_duration?.values?.['p(95)'] || 0,
    response_time_p99: data.metrics.http_req_duration?.values?.['p(99)'] || 0,
    error_rate: data.metrics.http_req_failed?.values?.rate || 0,
    success_rate: 1 - (data.metrics.http_req_failed?.values?.rate || 0),
    degradation_rate: data.metrics.degradation_rate?.values?.rate || 0,
    memory_usage_avg: data.metrics.memory_usage?.values?.avg || 0,
    cpu_usage_avg: data.metrics.cpu_usage?.values?.avg || 0,
    thresholds: {
      p95_response_time: data.thresholds['http_req_duration']?.p95 || false,
      error_rate: data.thresholds['http_req_failed']?.rate || false,
      degradation_rate: data.thresholds['degradation_rate']?.rate || false,
      memory_usage: data.thresholds['memory_usage']?.value || false,
      cpu_usage: data.thresholds['cpu_usage']?.value || false,
    },
    passed: Object.values(data.thresholds).every(t => t === true),
    soak_test_analysis: {
      memory_leak_detected: (data.metrics.memory_usage?.values?.avg || 0) > 1000,
      performance_degradation: (data.metrics.degradation_rate?.values?.rate || 0) > 0.02,
      stability_issues: (data.metrics.http_req_failed?.values?.rate || 0) > 0.05,
      resource_exhaustion: (data.metrics.cpu_usage?.values?.avg || 0) > 80,
    }
  };
  
  return {
    'stdout': JSON.stringify(summary, null, 2),
    'reports/seal_grade_soak_test.json': JSON.stringify(summary, null, 2),
  };
}
