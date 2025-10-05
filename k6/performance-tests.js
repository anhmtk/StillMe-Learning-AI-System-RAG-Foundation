import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time');
const requestCount = new Counter('request_count');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up
    { duration: '5m', target: 500 }, // Stay at 500 users
    { duration: '2m', target: 1000 }, // Ramp up to 1000 users
    { duration: '5m', target: 1000 }, // Stay at 1000 users
    { duration: '2m', target: 0 }, // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p95<500', 'p99<1000'],
    http_req_failed: ['rate<0.01'],
    error_rate: ['rate<0.01'],
    response_time: ['p95<500'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Test scenarios
export default function() {
  const scenarios = [
    testBasicAPI,
    testLearningEndpoints,
    testSecurityEndpoints,
    testPrivacyEndpoints,
    testPluginSystem,
    testSelfLearning,
  ];

  const scenario = scenarios[Math.floor(Math.random() * scenarios.length)];
  scenario();
  
  sleep(1);
}

// Basic API performance test
function testBasicAPI() {
  const startTime = Date.now();
  
  const response = http.get(`${BASE_URL}/health`, {
    headers: { 'Content-Type': 'application/json' },
  });
  
  const duration = Date.now() - startTime;
  
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'response has body': (r) => r.body.length > 0,
  });
  
  errorRate.add(!success);
  responseTime.add(duration);
  requestCount.add(1);
}

// Learning endpoints performance test
function testLearningEndpoints() {
  const endpoints = [
    '/api/learning/session',
    '/api/learning/metrics',
    '/api/learning/validation',
    '/api/learning/rollback',
  ];
  
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const startTime = Date.now();
  
  const response = http.get(`${BASE_URL}${endpoint}`, {
    headers: { 
      'Content-Type': 'application/json',
      'X-Session-ID': 'perf-test-' + Math.random().toString(36).substr(2, 9)
    },
  });
  
  const duration = Date.now() - startTime;
  
  const success = check(response, {
    'status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'response time < 1000ms': (r) => r.timings.duration < 1000,
  });
  
  errorRate.add(!success);
  responseTime.add(duration);
  requestCount.add(1);
}

// Security endpoints performance test
function testSecurityEndpoints() {
  const endpoints = [
    '/api/security/scan',
    '/api/security/validate',
    '/api/security/audit',
  ];
  
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const startTime = Date.now();
  
  const response = http.post(`${BASE_URL}${endpoint}`, JSON.stringify({
    test_data: 'performance_test',
    timestamp: new Date().toISOString(),
  }), {
    headers: { 
      'Content-Type': 'application/json',
      'X-API-Key': 'test-key'
    },
  });
  
  const duration = Date.now() - startTime;
  
  const success = check(response, {
    'status is 200 or 401': (r) => r.status === 200 || r.status === 401,
    'response time < 2000ms': (r) => r.timings.duration < 2000,
  });
  
  errorRate.add(!success);
  responseTime.add(duration);
  requestCount.add(1);
}

// Privacy endpoints performance test
function testPrivacyEndpoints() {
  const userId = 'test-user-' + Math.random().toString(36).substr(2, 9);
  const endpoints = [
    `/api/privacy/data/${userId}/export`,
    `/api/privacy/data/${userId}/delete`,
    '/api/privacy/status',
  ];
  
  const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
  const startTime = Date.now();
  
  const response = http.get(`${BASE_URL}${endpoint}`, {
    headers: { 
      'Content-Type': 'application/json',
      'X-User-ID': userId
    },
  });
  
  const duration = Date.now() - startTime;
  
  const success = check(response, {
    'status is 200 or 404': (r) => r.status === 200 || r.status === 404,
    'response time < 1500ms': (r) => r.timings.duration < 1500,
  });
  
  errorRate.add(!success);
  responseTime.add(duration);
  requestCount.add(1);
}

// Plugin system performance test
function testPluginSystem() {
  const startTime = Date.now();
  
  const response = http.post(`${BASE_URL}/api/plugins/calculator`, JSON.stringify({
    operation: 'add',
    args: [Math.random() * 100, Math.random() * 100]
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  const duration = Date.now() - startTime;
  
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 300ms': (r) => r.timings.duration < 300,
    'response has result': (r) => {
      try {
        const body = JSON.parse(r.body);
        return body.status === 'success' && typeof body.result === 'number';
      } catch {
        return false;
      }
    },
  });
  
  errorRate.add(!success);
  responseTime.add(duration);
  requestCount.add(1);
}

// Self-learning performance test
function testSelfLearning() {
  const startTime = Date.now();
  
  const response = http.post(`${BASE_URL}/api/learning/self-improvement`, JSON.stringify({
    session_id: 'perf-test-' + Math.random().toString(36).substr(2, 9),
    user_id: 'test-user-' + Math.random().toString(36).substr(2, 9),
    learning_type: 'performance_test',
    context: {
      test_scenario: 'load_testing',
      timestamp: new Date().toISOString()
    }
  }), {
    headers: { 
      'Content-Type': 'application/json',
      'X-Learning-Session': 'perf-test-session'
    },
  });
  
  const duration = Date.now() - startTime;
  
  const success = check(response, {
    'status is 200 or 202': (r) => r.status === 200 || r.status === 202,
    'response time < 2000ms': (r) => r.timings.duration < 2000,
  });
  
  errorRate.add(!success);
  responseTime.add(duration);
  requestCount.add(1);
}

// Setup function
export function setup() {
  console.log('🚀 Starting Performance Testing...');
  console.log(`Base URL: ${BASE_URL}`);
  console.log('Test scenarios: Basic API, Learning, Security, Privacy, Plugins, Self-Learning');
  return { startTime: Date.now() };
}

// Teardown function
export function teardown(data) {
  const duration = Date.now() - data.startTime;
  console.log(`✅ Performance Testing completed in ${duration}ms`);
}
