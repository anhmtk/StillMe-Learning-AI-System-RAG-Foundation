import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    rps200: {
      executor: "constant-arrival-rate",
      rate: 200,         // requests per second
      timeUnit: "1s",
      duration: "5m",
      preAllocatedVUs: 100,
      maxVUs: 500,
    },
    rps300: {
      startTime: "5m10s",
      executor: "constant-arrival-rate",
      rate: 300,
      timeUnit: "1s",
      duration: "3m",
      preAllocatedVUs: 150,
      maxVUs: 600,
    },
    rps400: {
      startTime: "8m20s",
      executor: "constant-arrival-rate",
      rate: 400,
      timeUnit: "1s",
      duration: "2m",
      preAllocatedVUs: 200,
      maxVUs: 800,
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<500", "p(99)<1000"],
    http_req_failed: ["rate<0.01"],
  },
  summaryTrendStats: ["avg","min","med","max","p(90)","p(95)","p(99)"],
};

const BASE_URL = __ENV.CLARIFICATION_API_URL || "http://localhost:8000/chat";

// Diverse prompt pool for realistic testing
const bodies = [
  { prompt: "Do it now" },
  { prompt: "Optimize this" },
  { prompt: "make it better like the other one but faster" },
  { prompt: "def foo(:" },
  { prompt: "def load_data(): pass\ndef process_data(): pass" },
  { prompt: "How can I implement caching in my web application?" },
  { prompt: "What's the difference between microservices and monolithic architecture?" },
  { prompt: "Help me debug this Python code" },
  { prompt: "Xin chào, tôi muốn cài đặt ứng dụng này như thế nào?" },
  { prompt: "My email is test@example.com and my password=12345" },
];

export default function () {
  const payload = JSON.stringify(bodies[Math.floor(Math.random() * bodies.length)]);
  const headers = { "Content-Type": "application/json" };
  
  const res = http.post(BASE_URL, payload, { headers });
  
  check(res, {
    "status is 200": (r) => r.status === 200,
    "clarification/suggestion present": (r) =>
      r.body && (r.body.includes("clarification") || r.body.includes("suggestion")),
    "response time < 1000ms": (r) => r.timings.duration < 1000,
  });
  
  // Minimal sleep to prevent overwhelming the system
  // CAR executor handles the rate, this is just for pacing
  sleep(0.01);
}
