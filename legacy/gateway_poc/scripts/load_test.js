// Load testing script for StillMe Gateway POC
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
export const errorRate = new Rate('errors');
export const responseTime = new Trend('response_time');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 }, // Ramp up to 10 users
    { duration: '5m', target: 10 }, // Stay at 10 users
    { duration: '2m', target: 20 }, // Ramp up to 20 users
    { duration: '5m', target: 20 }, // Stay at 20 users
    { duration: '2m', target: 0 },  // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
    http_req_failed: ['rate<0.1'],    // Error rate must be below 10%
    errors: ['rate<0.1'],             // Custom error rate below 10%
  },
};

// Base URL
const BASE_URL = 'http://gateway:8000';

// Test data
const testUsers = [
  { id: 'user1', token: 'test-token-1' },
  { id: 'user2', token: 'test-token-2' },
  { id: 'user3', token: 'test-token-3' },
];

export default function () {
  const user = testUsers[Math.floor(Math.random() * testUsers.length)];
  
  // Test 1: Health check
  const healthResponse = http.get(`${BASE_URL}/health`);
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
    'health check response time < 100ms': (r) => r.timings.duration < 100,
  });
  errorRate.add(healthResponse.status !== 200);
  responseTime.add(healthResponse.timings.duration);
  
  sleep(1);
  
  // Test 2: Root endpoint
  const rootResponse = http.get(`${BASE_URL}/`);
  check(rootResponse, {
    'root endpoint status is 200': (r) => r.status === 200,
    'root endpoint has version': (r) => r.json('version') !== undefined,
  });
  errorRate.add(rootResponse.status !== 200);
  responseTime.add(rootResponse.timings.duration);
  
  sleep(1);
  
  // Test 3: API endpoint
  const apiResponse = http.get(`${BASE_URL}/api/health`, {
    headers: {
      'Authorization': `Bearer ${user.token}`,
      'Content-Type': 'application/json',
    },
  });
  check(apiResponse, {
    'API endpoint status is 200': (r) => r.status === 200,
    'API endpoint response time < 200ms': (r) => r.timings.duration < 200,
  });
  errorRate.add(apiResponse.status !== 200);
  responseTime.add(apiResponse.timings.duration);
  
  sleep(1);
  
  // Test 4: Metrics endpoint
  const metricsResponse = http.get(`${BASE_URL}/metrics`);
  check(metricsResponse, {
    'metrics endpoint status is 200': (r) => r.status === 200,
    'metrics endpoint returns prometheus format': (r) => r.body.includes('prometheus'),
  });
  errorRate.add(metricsResponse.status !== 200);
  responseTime.add(metricsResponse.timings.duration);
  
  sleep(1);
  
  // Test 5: WebSocket connection (simulated with HTTP)
  const wsResponse = http.get(`${BASE_URL}/ws/${user.id}`, {
    headers: {
      'Upgrade': 'websocket',
      'Connection': 'Upgrade',
      'Sec-WebSocket-Key': 'test-key',
      'Sec-WebSocket-Version': '13',
    },
  });
  check(wsResponse, {
    'WebSocket endpoint responds': (r) => r.status === 101 || r.status === 400,
  });
  errorRate.add(wsResponse.status >= 500);
  responseTime.add(wsResponse.timings.duration);
  
  sleep(2);
}

export function handleSummary(data) {
  return {
    'load_test_results.json': JSON.stringify(data, null, 2),
    stdout: `
Load Test Summary:
==================
Total Requests: ${data.metrics.http_reqs.values.count}
Failed Requests: ${data.metrics.http_req_failed.values.count}
Error Rate: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%
Average Response Time: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms
95th Percentile: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms
99th Percentile: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms
    `,
  };
}
