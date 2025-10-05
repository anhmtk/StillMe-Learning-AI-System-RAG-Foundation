/**
 * SEAL-GRADE SYSTEM TESTS - Soak Testing with k6
 * Extended duration testing for system stability
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';

// Custom metrics
export const errorRate = new Rate('errors');
export const responseTime = new Trend('response_time');
export const requestCount = new Counter('requests');
export const memoryUsage = new Gauge('memory_usage');
export const cpuUsage = new Gauge('cpu_usage');

// Soak test configuration
export const options = {
  stages: [
    { duration: '5m', target: 10 },   // Ramp up slowly
    { duration: '4h', target: 50 },   // Soak for 4 hours
    { duration: '5m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95% of requests under 1s
    http_req_failed: ['rate<0.02'],    // Error rate under 2%
    errors: ['rate<0.02'],             // Custom error rate under 2%
  },
};

// Test data for soak testing
const soakTestPrompts = [
  'Hello, how are you today?',
  'What is the current time?',
  'Can you help me with a simple question?',
  'Tell me about artificial intelligence',
  'What are the benefits of machine learning?',
  'Explain the concept of neural networks',
  'How does natural language processing work?',
  'What is deep learning?',
  'Can you provide some coding examples?',
  'What are the latest technology trends?'
];

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function() {
  // Simulate realistic user behavior with longer pauses
  const pauseTime = Math.random() * 5 + 2; // 2-7 seconds between requests
  
  // Randomly select prompt
  const prompt = soakTestPrompts[Math.floor(Math.random() * soakTestPrompts.length)];
  
  const payload = JSON.stringify({
    prompt: prompt,
    context: {
      user_id: `soak_user_${__VU}`,
      session_id: `soak_session_${__ITER}`,
      timestamp: Date.now(),
      test_type: 'soak'
    }
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-soak-test'
    },
    timeout: '30s'
  };
  
  const response = http.post(`${BASE_URL}/chat`, payload, params);
  
  // Record metrics
  requestCount.add(1);
  responseTime.add(response.timings.duration);
  
  // Validate response
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 2000ms': (r) => r.timings.duration < 2000,
    'response has content': (r) => r.body && r.body.length > 0,
    'response is JSON': (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch (e) {
        return false;
      }
    },
    'no server errors': (r) => r.status < 500
  });
  
  if (!success) {
    errorRate.add(1);
    console.error(`Request failed: ${response.status} - ${response.body}`);
  } else {
    errorRate.add(0);
  }
  
  // Simulate realistic user behavior
  sleep(pauseTime);
}

export function handleSummary(data) {
  const duration = data.state.testRunDurationMs / 1000 / 60; // minutes
  
  return {
    'artifacts/k6-soak-test-results.json': JSON.stringify(data, null, 2),
    stdout: `
Soak Test Summary (${duration.toFixed(1)} minutes):
- Total Requests: ${data.metrics.requests.values.count}
- Error Rate: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%
- P95 Response Time: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms
- P99 Response Time: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms
- Average Response Time: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms
- Max Response Time: ${data.metrics.http_req_duration.values.max.toFixed(2)}ms
- Min Response Time: ${data.metrics.http_req_duration.values.min.toFixed(2)}ms
- Throughput: ${data.metrics.http_reqs.values.rate.toFixed(2)} req/s
- Total Data Transferred: ${(data.metrics.data_sent.values.count + data.metrics.data_received.values.count) / 1024 / 1024} MB

Stability Analysis:
- Error rate trend: ${data.metrics.http_req_failed.values.rate < 0.01 ? 'STABLE' : 'DEGRADING'}
- Response time trend: ${data.metrics.http_req_duration.values.avg < 500 ? 'STABLE' : 'DEGRADING'}
- System health: ${data.metrics.http_req_failed.values.rate < 0.02 && data.metrics.http_req_duration.values['p(95)'] < 1000 ? 'HEALTHY' : 'NEEDS ATTENTION'}
    `,
  };
}

