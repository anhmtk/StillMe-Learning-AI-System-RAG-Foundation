import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics for egress guard testing
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');
const blockedRequests = new Counter('blocked_requests');
const egressRequests = new Counter('egress_requests');

export const options = {
  vus: 30, // Lower VUs for egress testing
  duration: '2m',
  thresholds: {
    http_req_failed: [{threshold: 'rate<0.01', abortOnFail: true}],
    http_req_duration: [
      {threshold: 'p(95)<300', abortOnFail: true},
      {threshold: 'p(99)<500', abortOnFail: true}
    ],
    errors: [{threshold: 'rate<0.01', abortOnFail: true}],
    response_time: [{threshold: 'p(95)<300', abortOnFail: true}],
    blocked_requests: [{threshold: 'count<10', abortOnFail: false}] // Allow some blocks
  },
  tags: {
    test_type: 'egress_guard',
    environment: 'test'
  }
};

export function setup() {
  // Setup phase - check if services are available
  const healthCheck = http.get('http://agentdev:8080/health');
  check(healthCheck, {
    'health check passed': (r) => r.status === 200,
  });
  
  return {
    baseUrl: 'http://agentdev:8080',
    startTime: new Date().toISOString()
  };
}

export default function(data) {
  const testCases = [
    {
      name: 'internal_api',
      url: `${data.baseUrl}/api/jobs`,
      method: 'GET',
      type: 'internal'
    },
    {
      name: 'create_job_with_egress',
      url: `${data.baseUrl}/api/jobs`,
      method: 'POST',
      payload: {
        job_type: 'web_scrape',
        config: { 
          test: true,
          egress_enabled: true,
          target_url: 'https://httpbin.org/get' // Allowed domain
        },
        variables: { env: 'test' },
        created_by: 'k6_egress_test'
      },
      type: 'egress'
    },
    {
      name: 'blocked_egress_request',
      url: `${data.baseUrl}/api/jobs`,
      method: 'POST',
      payload: {
        job_type: 'web_scrape',
        config: { 
          test: true,
          egress_enabled: true,
          target_url: 'https://malicious-site.com/data' // Blocked domain
        },
        variables: { env: 'test' },
        created_by: 'k6_egress_test'
      },
      type: 'blocked'
    },
    {
      name: 'http_blocked_request',
      url: `${data.baseUrl}/api/jobs`,
      method: 'POST',
      payload: {
        job_type: 'web_scrape',
        config: { 
          test: true,
          egress_enabled: true,
          target_url: 'http://httpbin.org/get' // HTTP blocked
        },
        variables: { env: 'test' },
        created_by: 'k6_egress_test'
      },
      type: 'blocked'
    }
  ];

  // Randomly select a test case
  const testCase = testCases[Math.floor(Math.random() * testCases.length)];
  
  const startTime = Date.now();
  let response;
  
  if (testCase.method === 'GET') {
    response = http.get(testCase.url);
  } else if (testCase.method === 'POST') {
    response = http.post(testCase.url, JSON.stringify(testCase.payload), {
      headers: { 'Content-Type': 'application/json' }
    });
  }
  
  const endTime = Date.now();
  const duration = endTime - startTime;
  
  // Record custom metrics based on test type
  errorRate.add(response.status >= 400);
  responseTime.add(duration);
  
  if (testCase.type === 'egress') {
    egressRequests.add(1);
  } else if (testCase.type === 'blocked') {
    blockedRequests.add(1);
  }
  
  // Different checks based on test type
  let checks;
  if (testCase.type === 'blocked') {
    // For blocked requests, we expect them to be blocked
    checks = check(response, {
      'blocked request handled': (r) => r.status === 403 || r.status === 400,
      'response time < 1s': (r) => r.timings.duration < 1000,
    });
  } else {
    // For normal requests, expect success
    checks = check(response, {
      'status is 200 or 201': (r) => r.status === 200 || r.status === 201,
      'response time < 500ms': (r) => r.timings.duration < 500,
      'response has body': (r) => r.body && r.body.length > 0,
    });
  }
  
  // Log failures for debugging
  if (!checks) {
    console.error(`Test failed: ${testCase.name} - Status: ${response.status}, Duration: ${duration}ms`);
    if (response.body) {
      console.error(`Response body: ${response.body.substring(0, 200)}...`);
    }
  }
  
  sleep(0.1 + Math.random() * 0.3); // Random sleep between 100-400ms
}

export function teardown(data) {
  // Teardown phase - cleanup if needed
  console.log(`Egress guard test completed at ${new Date().toISOString()}`);
  console.log(`Test started at ${data.startTime}`);
}
