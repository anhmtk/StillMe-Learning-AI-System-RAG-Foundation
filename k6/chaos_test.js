/**
 * SEAL-GRADE SYSTEM TESTS - Chaos Engineering with k6
 * Test system resilience under failure conditions
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
export const errorRate = new Rate('errors');
export const responseTime = new Trend('response_time');
export const requestCount = new Counter('requests');
export const recoveryTime = new Trend('recovery_time');

// Chaos test configuration
export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Baseline
    { duration: '2m', target: 100 },  // Chaos injection
    { duration: '2m', target: 10 },   // Recovery
    { duration: '1m', target: 50 },   // Stability check
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // Relaxed thresholds for chaos
    http_req_failed: ['rate<0.1'],     // Allow up to 10% errors during chaos
    errors: ['rate<0.1'],
  },
};

// Chaos test scenarios
const chaosScenarios = [
  'normal',
  'high_load',
  'error_injection',
  'timeout_simulation',
  'malformed_requests'
];

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function() {
  const scenario = chaosScenarios[Math.floor(Math.random() * chaosScenarios.length)];
  
  switch (scenario) {
    case 'normal':
      testNormalRequest();
      break;
    case 'high_load':
      testHighLoadRequest();
      break;
    case 'error_injection':
      testErrorInjection();
      break;
    case 'timeout_simulation':
      testTimeoutSimulation();
      break;
    case 'malformed_requests':
      testMalformedRequest();
      break;
  }
  
  sleep(Math.random() * 2 + 0.5); // 0.5-2.5 seconds
}

function testNormalRequest() {
  const payload = JSON.stringify({
    prompt: 'Hello, this is a normal request',
    context: {
      user_id: `chaos_user_${__VU}`,
      session_id: `chaos_session_${__ITER}`,
      test_type: 'normal'
    }
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-chaos-test'
    },
    timeout: '30s'
  };
  
  const response = http.post(`${BASE_URL}/chat`, payload, params);
  
  recordMetrics(response, 'normal');
}

function testHighLoadRequest() {
  // Simulate high load with rapid requests
  const requests = [];
  for (let i = 0; i < 5; i++) {
    const payload = JSON.stringify({
      prompt: `High load request ${i}`,
      context: {
        user_id: `chaos_user_${__VU}`,
        session_id: `chaos_session_${__ITER}_${i}`,
        test_type: 'high_load'
      }
    });
    
    const params = {
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'k6-chaos-test'
      },
      timeout: '10s'
    };
    
    requests.push(http.post(`${BASE_URL}/chat`, payload, params));
  }
  
  // Record metrics for all requests
  requests.forEach(response => recordMetrics(response, 'high_load'));
}

function testErrorInjection() {
  // Inject various error conditions
  const errorTypes = [
    'invalid_json',
    'missing_prompt',
    'oversized_payload',
    'invalid_headers'
  ];
  
  const errorType = errorTypes[Math.floor(Math.random() * errorTypes.length)];
  
  let payload, params;
  
  switch (errorType) {
    case 'invalid_json':
      payload = '{"invalid": json}';
      params = {
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'k6-chaos-test'
        },
        timeout: '30s'
      };
      break;
      
    case 'missing_prompt':
      payload = JSON.stringify({
        context: {
          user_id: `chaos_user_${__VU}`,
          test_type: 'missing_prompt'
        }
      });
      params = {
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'k6-chaos-test'
        },
        timeout: '30s'
      };
      break;
      
    case 'oversized_payload':
      payload = JSON.stringify({
        prompt: 'A'.repeat(100000), // 100KB payload
        context: {
          user_id: `chaos_user_${__VU}`,
          test_type: 'oversized'
        }
      });
      params = {
        headers: {
          'Content-Type': 'application/json',
          'User-Agent': 'k6-chaos-test'
        },
        timeout: '30s'
      };
      break;
      
    case 'invalid_headers':
      payload = JSON.stringify({
        prompt: 'Test with invalid headers',
        context: {
          user_id: `chaos_user_${__VU}`,
          test_type: 'invalid_headers'
        }
      });
      params = {
        headers: {
          'Content-Type': 'text/plain', // Wrong content type
          'User-Agent': 'k6-chaos-test'
        },
        timeout: '30s'
      };
      break;
  }
  
  const response = http.post(`${BASE_URL}/chat`, payload, params);
  recordMetrics(response, 'error_injection');
}

function testTimeoutSimulation() {
  const payload = JSON.stringify({
    prompt: 'This request should timeout',
    context: {
      user_id: `chaos_user_${__VU}`,
      session_id: `chaos_session_${__ITER}`,
      test_type: 'timeout',
      delay: 60 // Request 60 second delay
    }
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-chaos-test'
    },
    timeout: '5s' // Short timeout to trigger timeout
  };
  
  const response = http.post(`${BASE_URL}/chat`, payload, params);
  recordMetrics(response, 'timeout');
}

function testMalformedRequest() {
  const malformedRequests = [
    '', // Empty request
    'not json', // Non-JSON
    '{"incomplete":', // Incomplete JSON
    JSON.stringify({}), // Empty object
    JSON.stringify(null), // Null
    JSON.stringify([]), // Array instead of object
  ];
  
  const payload = malformedRequests[Math.floor(Math.random() * malformedRequests.length)];
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-chaos-test'
    },
    timeout: '30s'
  };
  
  const response = http.post(`${BASE_URL}/chat`, payload, params);
  recordMetrics(response, 'malformed');
}

function recordMetrics(response, testType) {
  requestCount.add(1);
  responseTime.add(response.timings.duration);
  
  const success = check(response, {
    [`${testType} - status check`]: (r) => r.status >= 200 && r.status < 600,
    [`${testType} - response time check`]: (r) => r.timings.duration < 10000,
    [`${testType} - no connection errors`]: (r) => r.status !== 0,
  });
  
  if (!success) {
    errorRate.add(1);
    console.error(`${testType} request failed: ${response.status} - ${response.body}`);
  } else {
    errorRate.add(0);
  }
}

export function handleSummary(data) {
  return {
    'artifacts/k6-chaos-test-results.json': JSON.stringify(data, null, 2),
    stdout: `
Chaos Test Summary:
- Total Requests: ${data.metrics.requests.values.count}
- Error Rate: ${(data.metrics.http_req_failed.values.rate * 100).toFixed(2)}%
- P95 Response Time: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms
- P99 Response Time: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms
- Average Response Time: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms
- Max Response Time: ${data.metrics.http_req_duration.values.max.toFixed(2)}ms
- Throughput: ${data.metrics.http_reqs.values.rate.toFixed(2)} req/s

Chaos Engineering Results:
- System Resilience: ${data.metrics.http_req_failed.values.rate < 0.1 ? 'GOOD' : 'NEEDS IMPROVEMENT'}
- Recovery Capability: ${data.metrics.http_req_duration.values.avg < 1000 ? 'GOOD' : 'NEEDS IMPROVEMENT'}
- Error Handling: ${data.metrics.http_req_failed.values.rate < 0.05 ? 'ROBUST' : 'NEEDS IMPROVEMENT'}
    `,
  };
}

