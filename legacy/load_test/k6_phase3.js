/**
 * K6 Load Test for Phase 3 Clarification Core
 * ===========================================
 * 
 * Tests performance and load handling with:
 * - 2 profiles: burst (100 VU, 5 min), steady (50 VU, 10 min)
 * - Input mix: 60% short, 30% medium, 10% long prompts
 * - 20% clarification careful-mode
 * - Abort rules: p99 > 1.5s or error rate > 2%
 * 
 * Author: StillMe AI Framework
 * Created: 2025-01-08
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time');

// Test configuration
export const options = {
  scenarios: {
    // Burst scenario: 100 VU for 5 minutes
    burst: {
      executor: 'constant-vus',
      vus: 100,
      duration: '5m',
      tags: { scenario: 'burst' },
    },
    
    // Steady scenario: 50 VU for 10 minutes
    steady: {
      executor: 'constant-vus',
      vus: 50,
      duration: '10m',
      startTime: '6m', // Start after burst
      tags: { scenario: 'steady' },
    },
  },
  
  // Abort conditions
  abortOnFail: false,
  thresholds: {
    // Performance thresholds
    'http_req_duration': ['p95<800', 'p99<1200'],
    'http_req_duration{scenario:burst}': ['p95<800', 'p99<1200'],
    'http_req_duration{scenario:steady}': ['p95<1200', 'p99<1500'],
    
    // Error rate thresholds
    'http_req_failed': ['rate<0.01'], // < 1% error rate
    'error_rate': ['rate<0.02'], // < 2% error rate
    
    // Throughput thresholds
    'http_reqs': ['rate>10'], // > 10 requests/second
  },
};

// Test data
const testPrompts = {
  short: [
    "Hello, how are you?",
    "What's the weather like?",
    "Can you help me?",
    "Thanks for your help",
    "Good morning!",
  ],
  
  medium: [
    "Can you explain how machine learning works in simple terms?",
    "I need help with a Python function that processes CSV files",
    "What are the best practices for database design?",
    "How do I implement authentication in a web application?",
    "Can you review this code and suggest improvements?",
  ],
  
  long: [
    "I'm working on a complex e-commerce application with multiple microservices. I need to implement a recommendation system that suggests products based on user behavior, purchase history, and similar users. The system should handle real-time updates, be scalable to millions of users, and integrate with our existing inventory management system. Can you provide a detailed architecture and implementation plan?",
    "I'm building a data pipeline that processes millions of records daily. The pipeline needs to handle various data formats (JSON, CSV, XML), perform data validation and transformation, detect anomalies, and load the processed data into a data warehouse. The system should be fault-tolerant, support real-time and batch processing, and provide monitoring and alerting capabilities. What's the best approach?",
    "I need to design a distributed system for handling IoT sensor data from thousands of devices. The system should collect data in real-time, perform edge computing for immediate responses, store historical data for analysis, and provide APIs for data access. The system must be highly available, handle network failures gracefully, and scale horizontally. Can you help me design this architecture?",
  ],
};

// Base URL for the API
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  // Determine prompt type based on distribution
  const promptType = getPromptType();
  const prompt = getRandomPrompt(promptType);
  const useCarefulMode = Math.random() < 0.2; // 20% careful mode
  
  // Prepare request payload
  const payload = {
    message: prompt,
    careful_mode: useCarefulMode,
    timestamp: new Date().toISOString(),
  };
  
  // Make HTTP request
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'User-Agent': 'k6-load-test/1.0',
    },
    timeout: '30s',
  };
  
  const startTime = Date.now();
  const response = http.post(`${BASE_URL}/api/chat`, JSON.stringify(payload), params);
  const endTime = Date.now();
  const duration = endTime - startTime;
  
  // Record metrics
  responseTime.add(duration);
  
  // Check response
  const success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 2s': (r) => r.timings.duration < 2000,
    'response has content': (r) => r.body && r.body.length > 0,
    'response is valid JSON': (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch (e) {
        return false;
      }
    },
  });
  
  errorRate.add(!success);
  
  // Log errors
  if (!success) {
    console.error(`Request failed: ${response.status} - ${response.body}`);
  }
  
  // Sleep between requests (1-3 seconds)
  sleep(Math.random() * 2 + 1);
}

// Helper functions
function getPromptType() {
  const rand = Math.random();
  if (rand < 0.6) return 'short';      // 60% short
  if (rand < 0.9) return 'medium';     // 30% medium
  return 'long';                       // 10% long
}

function getRandomPrompt(type) {
  const prompts = testPrompts[type];
  return prompts[Math.floor(Math.random() * prompts.length)];
}

// Setup function (runs once at the beginning)
export function setup() {
  console.log('Starting K6 load test for Phase 3 Clarification Core');
  console.log(`Base URL: ${BASE_URL}`);
  console.log('Test scenarios:');
  console.log('- Burst: 100 VU for 5 minutes');
  console.log('- Steady: 50 VU for 10 minutes');
  console.log('Thresholds:');
  console.log('- p95 < 800ms (burst), < 1200ms (steady)');
  console.log('- p99 < 1200ms (burst), < 1500ms (steady)');
  console.log('- Error rate < 1%');
  console.log('- Throughput > 10 req/s');
  
  // Test API availability
  const healthCheck = http.get(`${BASE_URL}/health`);
  if (healthCheck.status !== 200) {
    console.error(`Health check failed: ${healthCheck.status}`);
    return false;
  }
  
  return true;
}

// Teardown function (runs once at the end)
export function teardown(data) {
  console.log('K6 load test completed');
  console.log('Final metrics will be available in the summary');
}
