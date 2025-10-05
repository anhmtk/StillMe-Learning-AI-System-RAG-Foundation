import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Counter, Rate } from "k6/metrics";

// Custom metrics
let ClarificationLatency = new Trend("clarification_latency");
let ClarificationFailures = new Counter("clarification_failures");
let ClarificationSuccessRate = new Rate("clarification_success_rate");
let ProactiveSuggestionRate = new Rate("proactive_suggestion_rate");

export let options = {
  stages: [
    // Stress
    { duration: "2m", target: 200 },
    { duration: "3m", target: 200 },
    { duration: "2m", target: 0 },
    // Spike
    { duration: "30s", target: 500 },
    { duration: "30s", target: 0 },
    // Soak
    { duration: "10m", target: 100 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<500", "p(99)<1000"],
    http_req_failed: ["rate<0.01"],
    clarification_success_rate: ["rate>0.9"],
  },
};

const BASE_URL = __ENV.CLARIFICATION_API_URL || "http://localhost:8000/chat";

// Prompt pool (đa dạng)
const prompts = [
  { prompt: "Do it now" },
  { prompt: "Optimize this" },
  { prompt: "Make it better, like the other one, but faster" },
  { prompt: "def foo(:" }, // code syntax error
  { prompt: "def load_data(): pass\ndef process_data(): pass" },
  { prompt: "IMG: corrupted_bytes" }, // image stub
  { prompt: "Draw me a cat" },
  { prompt: "My email is test@example.com and my password=12345" }, // PII to verify redaction
  { prompt: "Xin chao, toi muon cai dat ung dung nay nhu the nao?" }, // VI
];

export default function () {
  let payload = JSON.stringify(
    prompts[Math.floor(Math.random() * prompts.length)]
  );
  let headers = { "Content-Type": "application/json" };

  let res = http.post(BASE_URL, payload, { headers });

  const hasClarification =
    res.body && (res.body.includes("clarification") || res.body.includes("suggestion"));
  const hasProactive =
    res.body && (res.body.toLowerCase().includes("proactive") || res.body.toLowerCase().includes("suggestion"));

  let passed = check(res, {
    "status is 200": (r) => r.status === 200,
    "clarification/suggestion present": (r) => hasClarification,
  });

  ClarificationLatency.add(res.timings.duration);
  ClarificationSuccessRate.add(passed);
  ProactiveSuggestionRate.add(hasProactive);

  if (!passed) ClarificationFailures.add(1);

  sleep(1);
}