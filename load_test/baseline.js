import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

export const options = {
  vus: 50,
  duration: '2m',
  thresholds: {
    http_req_failed: [{threshold: 'rate<0.01', abortOnFail: true}],
    http_req_duration: [
      {threshold: 'p(95)<300', abortOnFail: true},
      {threshold: 'p(99)<500', abortOnFail: true}
    ],
    errors: [{threshold: 'rate<0.01', abortOnFail: true}],
    response_time: [{threshold: 'p(95)<300', abortOnFail: true}]
  },
  tags: {
    test_type: 'baseline',
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
      name: 'health_check',
      url: `${data.baseUrl}/health`,
      method: 'GET'
    },
    {
      name: 'create_job',
      url: `${data.baseUrl}/api/jobs`,
      method: 'POST',
      payload: {
        job_type: 'test',
        config: { test: true },
        variables: { env: 'test' },
        created_by: 'k6_test'
      }
    },
    {
      name: 'list_jobs',
      url: `${data.baseUrl}/api/jobs`,
      method: 'GET'
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
  
  // Record custom metrics
  errorRate.add(response.status >= 400);
  responseTime.add(duration);
  
  // Basic checks
  const checks = check(response, {
    'status is 200 or 201': (r) => r.status === 200 || r.status === 201,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'response has body': (r) => r.body && r.body.length > 0,
  });
  
  // If checks fail, record additional metrics
  if (!checks) {
    console.error(`Test failed: ${testCase.name} - Status: ${response.status}, Duration: ${duration}ms`);
  }
  
  sleep(0.1 + Math.random() * 0.2); // Random sleep between 100-300ms
}

export function teardown(data) {
  // Teardown phase - cleanup if needed
  console.log(`Test completed at ${new Date().toISOString()}`);
  console.log(`Test started at ${data.startTime}`);
}
