/**
 * SEAL-GRADE SYSTEM TESTS - Load Testing with k6
 * Enterprise-grade load testing for StillMe AI Framework
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
export const errorRate = new Rate('errors');
export const responseTime = new Trend('response_time');
export const requestCount = new Counter('requests');

// Test configuration
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // Ramp up
    { duration: '5m', target: 50 },   // Stay at 50 users
    { duration: '2m', target: 100 },  // Ramp up to 100 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],   // Error rate under 1%
    errors: ['rate<0.01'],            // Custom error rate under 1%
  },
};

// Test data
const testPrompts = [
  'Hello, how are you?',
  'What is artificial intelligence?',
  'Explain machine learning concepts',
  'Help me write a business plan',
  'What are the latest AI trends?',
  'How does natural language processing work?',
  'Can you help me with coding?',
  'What is the weather like?',
  'Tell me a joke',
  'Explain quantum computing'
];

const complexPrompts = [
  'Write a detailed analysis of the current state of artificial intelligence, including recent developments, challenges, and future prospects',
  'Create a comprehensive business plan for a tech startup focused on AI solutions',
  'Analyze the impact of AI on various industries and provide recommendations for adoption',
  'Explain the technical details of transformer architecture in deep learning',
  'Provide a detailed comparison of different machine learning algorithms and their use cases'
];

const multilingualPrompts = [
  { text: 'Xin chào, bạn khỏe không?', lang: 'vi' },
  { text: 'Bonjour, comment allez-vous?', lang: 'fr' },
  { text: 'こんにちは、元気ですか？', lang: 'jp' },
  { text: 'Hola, ¿cómo estás?', lang: 'es' },
  { text: 'Hello, how are you?', lang: 'en' }
];

// Base URL configuration
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function() {
  // Randomly select test scenario
  const scenario = Math.random();
  
  if (scenario < 0.6) {
    // 60% simple requests
    testSimpleRequest();
  } else if (scenario < 0.9) {
    // 30% complex requests
    testComplexRequest();
  } else {
    // 10% multilingual requests
    testMultilingualRequest();
  }
  
  sleep(1);
}

function testSimpleRequest() {
  const prompt = testPrompts[Math.floor(Math.random() * testPrompts.length)];
  
  const payload = JSON.stringify({
    prompt: prompt,
    context: {
      user_id: `user_${__VU}`,
      session_id: `session_${__ITER}`,
      timestamp: Date.now()
    }
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-load-test'
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
    'response time < 500ms': (r) => r.timings.duration < 500,
    'response has content': (r) => r.body && r.body.length > 0,
    'response is JSON': (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch (e) {
        return false;
      }
    }
  });
  
  if (!success) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
  }
}

function testComplexRequest() {
  const prompt = complexPrompts[Math.floor(Math.random() * complexPrompts.length)];
  
  const payload = JSON.stringify({
    prompt: prompt,
    context: {
      user_id: `user_${__VU}`,
      session_id: `session_${__ITER}`,
      max_tokens: 1000,
      temperature: 0.7,
      complexity: 'high'
    }
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-load-test'
    },
    timeout: '60s'
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
    }
  });
  
  if (!success) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
  }
}

function testMultilingualRequest() {
  const promptData = multilingualPrompts[Math.floor(Math.random() * multilingualPrompts.length)];
  
  const payload = JSON.stringify({
    prompt: promptData.text,
    context: {
      user_id: `user_${__VU}`,
      session_id: `session_${__ITER}`,
      language: promptData.lang,
      timestamp: Date.now()
    }
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-load-test',
      'Accept-Language': promptData.lang
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
    'response time < 1000ms': (r) => r.timings.duration < 1000,
    'response has content': (r) => r.body && r.body.length > 0,
    'response is JSON': (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch (e) {
        return false;
      }
    }
  });
  
  if (!success) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
  }
}

export function handleSummary(data) {
  return {
    'artifacts/k6-load-test-results.json': JSON.stringify(data, null, 2),
    stdout: `
Load Test Summary:
- Total Requests: ${data.metrics.requests.values.count}
- Error Rate: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%
- P95 Response Time: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms
- P99 Response Time: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms
- Average Response Time: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms
- Max Response Time: ${data.metrics.http_req_duration.values.max.toFixed(2)}ms
- Throughput: ${data.metrics.http_reqs.values.rate.toFixed(2)} req/s
    `,
  };
}

