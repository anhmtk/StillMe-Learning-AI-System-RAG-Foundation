import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Counter, Rate } from "k6/metrics";

// Custom metrics để export sang Prometheus
let ClarificationLatency = new Trend("clarification_latency");
let ClarificationFailures = new Counter("clarification_failures");
let ClarificationSuccessRate = new Rate("clarification_success_rate");
let ProactiveSuggestionRate = new Rate("proactive_suggestion_rate");
let MultiModalProcessingRate = new Rate("multimodal_processing_rate");

export let options = {
  stages: [
    // 🧪 Stress Test - Tăng dần load
    { duration: "2m", target: 200 },   // tăng lên 200 user
    { duration: "3m", target: 200 },   // giữ 200 user
    { duration: "2m", target: 0 },     // giảm về 0

    // 🧪 Spike Test - Tải đột biến
    { duration: "30s", target: 500 },  // tăng đột ngột 500 user
    { duration: "30s", target: 0 },

    // 🧪 Soak Test - Sức bền
    { duration: "10m", target: 100 },  // giữ 100 user trong 10 phút
  ],
  thresholds: {
    // Performance thresholds
    http_req_duration: ["p(95)<500", "p(99)<1000"], // 95% < 500ms, 99% < 1s
    http_req_failed: ["rate<0.01"],                // <1% request fail
    
    // Custom thresholds
    clarification_success_rate: ["rate>0.9"],      // ≥90% clarification đúng
    proactive_suggestion_rate: ["rate>0.7"],       // ≥70% proactive suggestion
    multimodal_processing_rate: ["rate>0.8"],      // ≥80% multi-modal processing
  },
};

const BASE_URL = "http://localhost:8000/chat"; // Clarification Core API endpoint

// Tập prompt test đa dạng (text, code, image stub, proactive, multi-modal)
const prompts = [
  // Vague prompts - should trigger clarification
  { prompt: "Do it now", expected: "clarification" },
  { prompt: "Optimize this", expected: "proactive_suggestion" },
  { prompt: "Make it better, like the other one, but faster", expected: "clarification" },
  { prompt: "Fix this", expected: "clarification" },
  { prompt: "Help me", expected: "clarification" },
  
  // Code prompts - should trigger code analysis
  { prompt: "def foo(:", expected: "syntax_error" }, // code lỗi
  { prompt: "def load_data(): pass\ndef process_data(): pass", expected: "function_selection" }, // code hợp lệ
  { prompt: "import pandas as pd\ndf = pd.DataFrame()", expected: "code_analysis" },
  
  // Multi-modal prompts
  { prompt: "IMG: corrupted_bytes", expected: "image_error" }, // giả lập ảnh hỏng
  { prompt: "Draw me a cat", expected: "multimodal" },        // multi-modal: ảnh + text
  { prompt: "Analyze this image and tell me what you see", expected: "multimodal" },
  
  // Security/Audit prompts
  { prompt: "My email is test@example.com and my password=12345", expected: "audit_redacted" }, // audit log test
  { prompt: "My API key is sk-1234567890abcdef", expected: "audit_redacted" },
  
  // Clear prompts - should not trigger clarification
  { prompt: "How can I implement a binary search algorithm in Python?", expected: "clear" },
  { prompt: "What are the best practices for error handling in JavaScript?", expected: "clear" },
  { prompt: "Can you explain the difference between REST and GraphQL APIs?", expected: "clear" },
  
  // Vietnamese prompts
  { prompt: "làm sao để fix", expected: "clarification" },
  { prompt: "giúp tôi với cái này", expected: "clarification" },
  { prompt: "cải thiện nó", expected: "proactive_suggestion" },
];

// Test scenarios for different load patterns
const scenarios = {
  // Normal user behavior
  normal: {
    weight: 60,
    prompts: prompts.filter(p => p.expected === "clear" || p.expected === "clarification"),
  },
  
  // Power user behavior (more complex prompts)
  power: {
    weight: 25,
    prompts: prompts.filter(p => p.expected === "code_analysis" || p.expected === "multimodal"),
  },
  
  // Security testing
  security: {
    weight: 10,
    prompts: prompts.filter(p => p.expected === "audit_redacted"),
  },
  
  // Proactive suggestion testing
  proactive: {
    weight: 5,
    prompts: prompts.filter(p => p.expected === "proactive_suggestion"),
  },
};

export default function () {
  // Select scenario based on weights
  let scenario = selectScenario();
  let prompt = scenario.prompts[Math.floor(Math.random() * scenario.prompts.length)];
  
  let payload = JSON.stringify({
    prompt: prompt.prompt,
    context: {
      user_id: `user_${__VU}`,
      session_id: `session_${__ITER}`,
      timestamp: new Date().toISOString(),
    },
    options: {
      enable_proactive_suggestions: true,
      enable_multimodal: true,
      enable_audit_logging: true,
    }
  });
  
  let headers = { 
    "Content-Type": "application/json",
    "X-User-ID": `user_${__VU}`,
    "X-Session-ID": `session_${__ITER}`,
  };

  let startTime = Date.now();
  let res = http.post(BASE_URL, payload, { headers });
  let endTime = Date.now();
  let latency = endTime - startTime;

  // Record custom metrics
  ClarificationLatency.add(latency);
  
  // Check response quality
  let checks = check(res, {
    "status is 200": (r) => r.status === 200,
    "response time < 1s": (r) => r.timings.duration < 1000,
    "contains clarification": (r) => 
      r.body.includes("clarification") || r.body.includes("suggestion") || r.body.includes("clarify"),
    "valid JSON response": (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch (e) {
        return false;
      }
    },
  });

  // Additional quality checks based on expected behavior
  let qualityChecks = check(res, {
    "vague prompt triggers clarification": (r) => {
      if (prompt.expected === "clarification") {
        return r.body.includes("clarification") || r.body.includes("clarify");
      }
      return true;
    },
    "proactive suggestion present": (r) => {
      if (prompt.expected === "proactive_suggestion") {
        return r.body.includes("suggestion") || r.body.includes("proactive");
      }
      return true;
    },
    "code analysis present": (r) => {
      if (prompt.expected === "code_analysis" || prompt.expected === "syntax_error") {
        return r.body.includes("code") || r.body.includes("function") || r.body.includes("syntax");
      }
      return true;
    },
    "multimodal processing": (r) => {
      if (prompt.expected === "multimodal") {
        return r.body.includes("image") || r.body.includes("visual") || r.body.includes("draw");
      }
      return true;
    },
    "audit logging redacted": (r) => {
      if (prompt.expected === "audit_redacted") {
        return !r.body.includes("test@example.com") && !r.body.includes("sk-1234567890abcdef");
      }
      return true;
    },
  });

  // Record success/failure metrics
  if (!checks || !qualityChecks) {
    ClarificationFailures.add(1);
    ClarificationSuccessRate.add(false);
  } else {
    ClarificationSuccessRate.add(true);
  }

  // Record specific feature metrics
  if (prompt.expected === "proactive_suggestion") {
    ProactiveSuggestionRate.add(qualityChecks);
  }
  
  if (prompt.expected === "multimodal") {
    MultiModalProcessingRate.add(qualityChecks);
  }

  // Simulate user think time (1-3 seconds)
  sleep(Math.random() * 2 + 1);
}

function selectScenario() {
  let rand = Math.random();
  let cumulative = 0;
  
  for (let [name, scenario] of Object.entries(scenarios)) {
    cumulative += scenario.weight / 100;
    if (rand <= cumulative) {
      return scenario;
    }
  }
  
  return scenarios.normal;
}

// Setup function - chạy trước khi test bắt đầu
export function setup() {
  console.log("🚀 Starting K6 SEAL-GRADE Test for Phase 3 Clarification Core");
  console.log("📊 Test Configuration:");
  console.log("   - Stress Test: 200 users for 5 minutes");
  console.log("   - Spike Test: 500 users for 1 minute");
  console.log("   - Soak Test: 100 users for 10 minutes");
  console.log("   - Total Duration: ~17 minutes");
  console.log("🎯 Targets:");
  console.log("   - p95 < 500ms, p99 < 1s");
  console.log("   - Error rate < 1%");
  console.log("   - Clarification success rate > 90%");
  console.log("   - Proactive suggestion rate > 70%");
  console.log("   - Multi-modal processing rate > 80%");
  
  return { startTime: Date.now() };
}

// Teardown function - chạy sau khi test kết thúc
export function teardown(data) {
  let duration = (Date.now() - data.startTime) / 1000;
  console.log(`✅ K6 SEAL-GRADE Test completed in ${duration.toFixed(2)} seconds`);
  console.log("📈 Check the metrics above for performance analysis");
}
