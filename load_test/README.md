# 🧪 K6 SEAL-GRADE Test for Phase 3 Clarification Core

**Comprehensive load testing suite for StillMe AI Framework's Clarification Core with advanced performance monitoring and alerting.**

## 🎯 **OVERVIEW**

This test suite provides **SEAL-GRADE** load testing for the Phase 3 Clarification Core, ensuring the system can handle production workloads with:

- **Performance Testing**: p50/p95/p99 latency measurement
- **Reliability Testing**: Error rate monitoring (<1%)
- **Stability Testing**: Soak test for memory leak detection
- **Spike Testing**: Sudden load increase handling (500 users)
- **Functionality Testing**: Multi-modal prompt processing + proactive suggestions

## 🚀 **QUICK START**

### **Prerequisites**
```bash
# Install k6
# macOS
brew install k6

# Windows
choco install k6

# Ubuntu
sudo apt install k6

# Or download from: https://k6.io/docs/getting-started/installation/
```

### **Start Clarification Core API**
```bash
# Make sure your Clarification Core API is running on localhost:8000
# The API should have a /health endpoint
curl http://localhost:8000/health
```

### **Run Test**
```bash
# Windows
load_test\run_seal_test.bat

# Linux/macOS
./load_test/run_seal_test.sh
```

## 📊 **TEST SCENARIOS**

### **1. Stress Test (5 minutes)**
- **Ramp-up**: 0 → 200 users (2 minutes)
- **Sustain**: 200 users (3 minutes)
- **Ramp-down**: 200 → 0 users (2 minutes)

### **2. Spike Test (1 minute)**
- **Sudden spike**: 0 → 500 users (30 seconds)
- **Ramp-down**: 500 → 0 users (30 seconds)

### **3. Soak Test (10 minutes)**
- **Sustained load**: 100 users for 10 minutes
- **Memory leak detection**: Monitor RAM usage

## 🎯 **ACCEPTANCE CRITERIA**

### **Performance Requirements**
- ✅ **p95 < 500ms**: 95% of requests under 500ms
- ✅ **p99 < 1s**: 99% of requests under 1 second
- ✅ **Throughput ≥ 200 RPS**: Sustained request rate
- ✅ **Error Rate < 1%**: Less than 1% failed requests

### **Functionality Requirements**
- ✅ **Clarification Success > 90%**: Vague prompts trigger clarification
- ✅ **Proactive Suggestion > 70%**: "Optimize" prompts trigger suggestions
- ✅ **Multi-Modal Processing > 80%**: Image + text prompts processed
- ✅ **Code Analysis**: Syntax errors and function selection
- ✅ **Audit Logging**: PII redaction in sensitive prompts

### **Stability Requirements**
- ✅ **No Memory Leaks**: RAM usage stable during soak test
- ✅ **No Crashes**: System handles 500 user spike
- ✅ **Graceful Degradation**: Performance degrades gracefully under load

## 📈 **MONITORING & ALERTING**

### **Prometheus Metrics**
- `http_requests_total`: Total request count
- `http_request_duration_seconds`: Request latency histogram
- `clarification_success_rate`: Clarification accuracy
- `proactive_suggestion_rate`: Proactive suggestion accuracy
- `multimodal_processing_rate`: Multi-modal processing accuracy

### **Grafana Dashboard**
- **Real-time monitoring**: Request rate, latency, error rate
- **Performance trends**: p95/p99 latency over time
- **Success rates**: Clarification, proactive suggestion, multi-modal
- **System metrics**: CPU, memory, disk usage

### **Alert Rules**
- **High Error Rate**: >1% for 1 minute
- **High Latency**: p99 > 1s for 2 minutes
- **Low Success Rate**: <90% for 3 minutes
- **System Resource**: High CPU/memory usage

## 🔧 **CONFIGURATION**

### **Test Configuration**
```javascript
export let options = {
  stages: [
    { duration: "2m", target: 200 },   // Stress test
    { duration: "3m", target: 200 },   // Sustain
    { duration: "2m", target: 0 },     // Ramp down
    { duration: "30s", target: 500 }, // Spike test
    { duration: "30s", target: 0 },    // Spike down
    { duration: "10m", target: 100 },  // Soak test
  ],
  thresholds: {
    http_req_duration: ["p(95)<500", "p(99)<1000"],
    http_req_failed: ["rate<0.01"],
    clarification_success_rate: ["rate>0.9"],
    proactive_suggestion_rate: ["rate>0.7"],
    multimodal_processing_rate: ["rate>0.8"],
  },
};
```

### **API Endpoint Configuration**
```javascript
const BASE_URL = "http://localhost:8000/chat";
```

## 📋 **TEST CASES**

### **Vague Prompts (Should Trigger Clarification)**
- "Do it now"
- "Optimize this"
- "Make it better, like the other one, but faster"
- "Fix this"
- "Help me"

### **Code Prompts (Should Trigger Code Analysis)**
- "def foo(:" (syntax error)
- "def load_data(): pass\ndef process_data(): pass" (function selection)
- "import pandas as pd\ndf = pd.DataFrame()" (code analysis)

### **Multi-Modal Prompts**
- "IMG: corrupted_bytes" (image error handling)
- "Draw me a cat" (image generation)
- "Analyze this image and tell me what you see" (image analysis)

### **Security/Audit Prompts**
- "My email is test@example.com and my password=12345" (PII redaction)
- "My API key is sk-1234567890abcdef" (token redaction)

### **Clear Prompts (Should Not Trigger Clarification)**
- "How can I implement a binary search algorithm in Python?"
- "What are the best practices for error handling in JavaScript?"
- "Can you explain the difference between REST and GraphQL APIs?"

### **Vietnamese Prompts**
- "làm sao để fix" (clarification)
- "giúp tôi với cái này" (clarification)
- "cải thiện nó" (proactive suggestion)

## 📊 **REPORTING**

### **JSON Output**
```bash
k6 run --out json=report.json load_test/clarification_seal_test.js
```

### **Prometheus Output**
```bash
k6 run --out prometheus-remote-write load_test/clarification_seal_test.js
```

### **HTML Report**
```bash
k6 run --out json=report.json load_test/clarification_seal_test.js
k6-to-junit report.json > report.html
```

## 🚨 **TROUBLESHOOTING**

### **Common Issues**

1. **API Not Running**
   ```
   ❌ Clarification Core API is not running on localhost:8000
   ```
   **Solution**: Start your Clarification Core API server

2. **High Error Rate**
   ```
   ❌ Error rate > 1%
   ```
   **Solution**: Check API logs, increase server resources

3. **High Latency**
   ```
   ❌ p99 latency > 1s
   ```
   **Solution**: Optimize API performance, check database queries

4. **Low Success Rate**
   ```
   ❌ Clarification success rate < 90%
   ```
   **Solution**: Check clarification logic, review test cases

### **Performance Optimization**

1. **Database Optimization**
   - Add indexes for frequent queries
   - Use connection pooling
   - Optimize query performance

2. **Caching**
   - Implement Redis caching
   - Cache frequent responses
   - Use CDN for static assets

3. **Load Balancing**
   - Deploy multiple API instances
   - Use load balancer (nginx, HAProxy)
   - Implement horizontal scaling

## 📁 **FILE STRUCTURE**

```
load_test/
├── clarification_seal_test.js    # Main K6 test script
├── prometheus.yml                # Prometheus configuration
├── grafana_dashboard.json        # Grafana dashboard
├── alerts.yml                    # Alert rules
├── run_seal_test.sh              # Linux/macOS runner
├── run_seal_test.bat             # Windows runner
└── README.md                     # This documentation
```

## 🎯 **SEAL-GRADE COMPLIANCE**

This test suite ensures **SEAL-GRADE** compliance with:

- ✅ **Comprehensive Testing**: 17-minute test duration
- ✅ **Realistic Scenarios**: Multiple user behavior patterns
- ✅ **Performance Monitoring**: Real-time metrics and alerting
- ✅ **Quality Assurance**: Functionality validation
- ✅ **Production Readiness**: Stress, spike, and soak testing

## 🚀 **NEXT STEPS**

1. **Run the test** to validate current performance
2. **Analyze results** and identify bottlenecks
3. **Optimize system** based on findings
4. **Re-run test** to verify improvements
5. **Deploy to production** with confidence

---

**Generated by**: StillMe AI Framework  
**Quality Assurance**: SEAL-GRADE Testing Standards  
**Status**: ✅ **PRODUCTION READY** - Comprehensive load testing suite
