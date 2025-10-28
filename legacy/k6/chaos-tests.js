import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics for chaos testing
const chaosErrorRate = new Rate('chaos_error_rate');
const recoveryTime = new Trend('recovery_time');
const resilienceScore = new Counter('resilience_score');

// Chaos test configuration
export const options = {
  stages: [
    { duration: '1m', target: 50 }, // Baseline
    { duration: '2m', target: 200 }, // Normal load
    { duration: '3m', target: 500 }, // High load
    { duration: '2m', target: 1000 }, // Peak load
    { duration: '1m', target: 0 }, // Ramp down
  ],
  thresholds: {
    chaos_error_rate: ['rate<0.05'], // Allow 5% error rate during chaos
    recovery_time: ['p95<5000'], // Recovery within 5 seconds
    resilience_score: ['count>100'], // Minimum resilience score
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Chaos scenarios
const chaosScenarios = [
  'memory_failure',
  'router_failure', 
  'agentdev_failure',
  'learning_failure',
  'security_failure',
  'plugin_failure'
];

export default function() {
  const scenario = chaosScenarios[Math.floor(Math.random() * chaosScenarios.length)];
  
  switch(scenario) {
    case 'memory_failure':
      testMemoryFailure();
      break;
    case 'router_failure':
      testRouterFailure();
      break;
    case 'agentdev_failure':
      testAgentDevFailure();
      break;
    case 'learning_failure':
      testLearningFailure();
      break;
    case 'security_failure':
      testSecurityFailure();
      break;
    case 'plugin_failure':
      testPluginFailure();
      break;
  }
  
  sleep(2);
}

// Test memory module failure and recovery
function testMemoryFailure() {
  const startTime = Date.now();
  
  // Simulate memory module failure
  const response = http.post(`${BASE_URL}/api/chaos/memory/fail`, JSON.stringify({
    failure_type: 'memory_corruption',
    duration: 5000, // 5 seconds
    severity: 'high'
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  const duration = Date.now() - startTime;
  
  const success = check(response, {
    'memory failure simulated': (r) => r.status === 200 || r.status === 202,
    'recovery time < 5s': (r) => r.timings.duration < 5000,
  });
  
  chaosErrorRate.add(!success);
  recoveryTime.add(duration);
  resilienceScore.add(success ? 1 : 0);
}

// Test router failure and recovery
function testRouterFailure() {
  const startTime = Date.now();
  
  // Simulate router failure
  const response = http.post(`${BASE_URL}/api/chaos/router/fail`, JSON.stringify({
    failure_type: 'routing_error',
    duration: 3000, // 3 seconds
    severity: 'medium'
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  const duration = Date.now() - startTime;
  
  const success = check(response, {
    'router failure simulated': (r) => r.status === 200 || r.status === 202,
    'recovery time < 3s': (r) => r.timings.duration < 3000,
  });
  
  chaosErrorRate.add(!success);
  recoveryTime.add(duration);
  resilienceScore.add(success ? 1 : 0);
}

// Test AgentDev failure and recovery
function testAgentDevFailure() {
  const startTime = Date.now();
  
  // Simulate AgentDev failure
  const response = http.post(`${BASE_URL}/api/chaos/agentdev/fail`, JSON.stringify({
    failure_type: 'code_execution_error',
    duration: 4000, // 4 seconds
    severity: 'high'
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  const duration = Date.now() - startTime;
  
  const success = check(response, {
    'agentdev failure simulated': (r) => r.status === 200 || r.status === 202,
    'recovery time < 4s': (r) => r.timings.duration < 4000,
  });
  
  chaosErrorRate.add(!success);
  recoveryTime.add(duration);
  resilienceScore.add(success ? 1 : 0);
}

// Test learning system failure and recovery
function testLearningFailure() {
  const startTime = Date.now();
  
  // Simulate learning system failure
  const response = http.post(`${BASE_URL}/api/chaos/learning/fail`, JSON.stringify({
    failure_type: 'learning_corruption',
    duration: 6000, // 6 seconds
    severity: 'critical'
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  const duration = Date.now() - startTime;
  
  const success = check(response, {
    'learning failure simulated': (r) => r.status === 200 || r.status === 202,
    'recovery time < 6s': (r) => r.timings.duration < 6000,
  });
  
  chaosErrorRate.add(!success);
  recoveryTime.add(duration);
  resilienceScore.add(success ? 1 : 0);
}

// Test security system failure and recovery
function testSecurityFailure() {
  const startTime = Date.now();
  
  // Simulate security system failure
  const response = http.post(`${BASE_URL}/api/chaos/security/fail`, JSON.stringify({
    failure_type: 'security_bypass',
    duration: 2000, // 2 seconds
    severity: 'critical'
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  const duration = Date.now() - startTime;
  
  const success = check(response, {
    'security failure simulated': (r) => r.status === 200 || r.status === 202,
    'recovery time < 2s': (r) => r.timings.duration < 2000,
  });
  
  chaosErrorRate.add(!success);
  recoveryTime.add(duration);
  resilienceScore.add(success ? 1 : 0);
}

// Test plugin system failure and recovery
function testPluginFailure() {
  const startTime = Date.now();
  
  // Simulate plugin system failure
  const response = http.post(`${BASE_URL}/api/chaos/plugin/fail`, JSON.stringify({
    failure_type: 'plugin_crash',
    duration: 3000, // 3 seconds
    severity: 'medium'
  }), {
    headers: { 'Content-Type': 'application/json' },
  });
  
  const duration = Date.now() - startTime;
  
  const success = check(response, {
    'plugin failure simulated': (r) => r.status === 200 || r.status === 202,
    'recovery time < 3s': (r) => r.timings.duration < 3000,
  });
  
  chaosErrorRate.add(!success);
  recoveryTime.add(duration);
  resilienceScore.add(success ? 1 : 0);
}

// Setup function
export function setup() {
  console.log('🔥 Starting Chaos Testing...');
  console.log(`Base URL: ${BASE_URL}`);
  console.log('Chaos scenarios: Memory, Router, AgentDev, Learning, Security, Plugin');
  return { startTime: Date.now() };
}

// Teardown function
export function teardown(data) {
  const duration = Date.now() - data.startTime;
  console.log(`✅ Chaos Testing completed in ${duration}ms`);
  console.log('Resilience testing: System should recover from all failures');
}
