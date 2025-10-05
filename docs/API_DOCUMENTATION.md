# StillMe AI Framework - API Documentation

**Version**: 1.0.0  
**Last Updated**: 2025-09-26  
**Base URL**: `http://localhost:8000`

## 📋 **OVERVIEW**

StillMe AI Framework provides a comprehensive REST API for AI-powered applications with advanced self-learning, security, privacy, and extensibility features.

## 🔐 **AUTHENTICATION**

### **API Key Authentication**
```http
X-API-Key: your-api-key-here
```

### **Session Authentication**
```http
X-Session-ID: session-id-here
```

### **User Authentication**
```http
X-User-ID: user-id-here
```

## 🧠 **CORE AI ENDPOINTS**

### **1. Health Check**
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-26T10:00:00Z",
  "version": "1.0.0",
  "components": {
    "memory": "active",
    "router": "active",
    "agentdev": "active",
    "learning": "active",
    "security": "active"
  }
}
```

### **2. AI Processing**
```http
POST /api/ai/process
```

**Request Body:**
```json
{
  "input": "Your question or request",
  "context": {
    "user_id": "user123",
    "session_id": "session456",
    "preferences": {
      "language": "en",
      "tone": "professional"
    }
  },
  "options": {
    "rationale": true,
    "policy_level": "balanced"
  }
}
```

**Response:**
```json
{
  "output": "AI response",
  "rationale": {
    "reasoning": "Step-by-step reasoning",
    "confidence": 0.95,
    "factors": ["factor1", "factor2"]
  },
  "metadata": {
    "processing_time": 1.2,
    "model_used": "stillme-v1",
    "policy_applied": "balanced"
  }
}
```

## 🧠 **SELF-LEARNING ENDPOINTS**

### **1. Start Learning Session**
```http
POST /api/learning/session
```

**Request Body:**
```json
{
  "session_id": "session123",
  "user_id": "user456",
  "learning_type": "self_improvement",
  "context": {
    "task_type": "code_fixing",
    "complexity": "high"
  }
}
```

**Response:**
```json
{
  "session_id": "session123",
  "status": "started",
  "learning_strategy": "reinforcement",
  "estimated_duration": "30m"
}
```

### **2. Learning Metrics**
```http
GET /api/learning/metrics
```

**Query Parameters:**
- `session_id` (optional): Specific session ID
- `time_range` (optional): Time range (e.g., "7d", "30d")
- `metric_type` (optional): Type of metrics

**Response:**
```json
{
  "session_id": "session123",
  "metrics": {
    "success_rate": 0.94,
    "accuracy_delta": 0.15,
    "safety_violation_rate": 0.0,
    "rollback_count": 2,
    "learning_velocity": 0.8
  },
  "timestamp": "2025-09-26T10:00:00Z"
}
```

### **3. Learning Validation**
```http
POST /api/learning/validation
```

**Request Body:**
```json
{
  "session_id": "session123",
  "validation_type": "objective",
  "benchmark_data": {
    "accuracy": 0.92,
    "safety": 1.0,
    "performance": 0.88
  }
}
```

**Response:**
```json
{
  "validation_id": "val123",
  "status": "completed",
  "results": {
    "overall_score": 0.93,
    "accuracy_score": 0.92,
    "safety_score": 1.0,
    "performance_score": 0.88
  },
  "recommendations": [
    "Improve accuracy on complex tasks",
    "Maintain current safety standards"
  ]
}
```

### **4. Learning Rollback**
```http
POST /api/learning/rollback
```

**Request Body:**
```json
{
  "session_id": "session123",
  "version_id": "v20250926_100000",
  "reason": "Performance degradation detected",
  "force": false
}
```

**Response:**
```json
{
  "rollback_id": "roll123",
  "status": "completed",
  "previous_version": "v20250926_100000",
  "current_version": "v20250926_100500",
  "rollback_time": 2.3
}
```

## 🛡️ **SECURITY ENDPOINTS**

### **1. Security Scan**
```http
POST /api/security/scan
```

**Request Body:**
```json
{
  "scan_type": "comprehensive",
  "targets": ["code", "dependencies", "secrets"],
  "severity_levels": ["high", "critical"]
}
```

**Response:**
```json
{
  "scan_id": "scan123",
  "status": "completed",
  "results": {
    "total_issues": 0,
    "high_severity": 0,
    "critical_severity": 0,
    "security_score": 95
  },
  "recommendations": []
}
```

### **2. Security Validation**
```http
POST /api/security/validate
```

**Request Body:**
```json
{
  "input": "User input to validate",
  "validation_type": "injection_attack",
  "context": {
    "user_id": "user123",
    "session_id": "session456"
  }
}
```

**Response:**
```json
{
  "validation_id": "val123",
  "status": "passed",
  "security_score": 0.98,
  "threats_detected": [],
  "recommendations": []
}
```

### **3. Security Audit**
```http
GET /api/security/audit
```

**Query Parameters:**
- `audit_type` (optional): Type of audit
- `time_range` (optional): Time range for audit

**Response:**
```json
{
  "audit_id": "audit123",
  "status": "completed",
  "findings": {
    "total_events": 1250,
    "security_events": 5,
    "threat_level": "low"
  },
  "recommendations": [
    "Regular security updates",
    "Monitor for new threats"
  ]
}
```

## 🔒 **PRIVACY ENDPOINTS**

### **1. Export User Data**
```http
GET /api/privacy/data/{user_id}/export
```

**Response:**
```json
{
  "user_id": "user123",
  "export_id": "export123",
  "data": {
    "profile": {...},
    "interactions": [...],
    "learning_data": [...],
    "preferences": {...}
  },
  "exported_at": "2025-09-26T10:00:00Z",
  "data_retention": "30d"
}
```

### **2. Delete User Data**
```http
DELETE /api/privacy/data/{user_id}/delete
```

**Response:**
```json
{
  "user_id": "user123",
  "deletion_id": "del123",
  "status": "completed",
  "deleted_at": "2025-09-26T10:00:00Z",
  "data_types_deleted": [
    "profile",
    "interactions",
    "learning_data",
    "preferences"
  ]
}
```

### **3. Privacy Status**
```http
GET /api/privacy/status
```

**Response:**
```json
{
  "privacy_mode": "balanced",
  "data_retention_days": 30,
  "gdpr_like_capabilities": true,
  "pii_redaction_enabled": true,
  "consent_required": true
}
```

## 🔌 **PLUGIN ENDPOINTS**

### **1. List Plugins**
```http
GET /api/plugins
```

**Response:**
```json
{
  "plugins": [
    {
      "name": "CalculatorPlugin",
      "version": "1.0.0",
      "status": "active",
      "description": "Basic arithmetic operations",
      "author": "StillMe AI Team"
    }
  ],
  "total_plugins": 1
}
```

### **2. Execute Plugin**
```http
POST /api/plugins/{plugin_name}
```

**Request Body:**
```json
{
  "operation": "add",
  "args": [1, 2, 3],
  "options": {
    "precision": 2
  }
}
```

**Response:**
```json
{
  "plugin_name": "CalculatorPlugin",
  "status": "success",
  "result": 6,
  "execution_time": 0.05,
  "metadata": {
    "operation": "add",
    "args": [1, 2, 3]
  }
}
```

## 🧪 **ETHICS ENDPOINTS**

### **1. Ethics Test**
```http
POST /api/ethics/test
```

**Request Body:**
```json
{
  "input": "Test input for ethics validation",
  "test_type": "bias_detection",
  "context": {
    "user_id": "user123",
    "session_id": "session456"
  }
}
```

**Response:**
```json
{
  "test_id": "test123",
  "status": "passed",
  "ethics_score": 0.95,
  "bias_detected": false,
  "safety_level": "high",
  "recommendations": []
}
```

### **2. Ethics Validation**
```http
POST /api/ethics/validate
```

**Request Body:**
```json
{
  "content": "Content to validate",
  "validation_type": "comprehensive",
  "severity_levels": ["high", "critical"]
}
```

**Response:**
```json
{
  "validation_id": "val123",
  "status": "passed",
  "ethics_score": 0.98,
  "violations_detected": [],
  "recommendations": []
}
```

## 📊 **MONITORING ENDPOINTS**

### **1. System Status**
```http
GET /api/monitoring/status
```

**Response:**
```json
{
  "system_status": "healthy",
  "components": {
    "memory": {"status": "active", "usage": "45%"},
    "router": {"status": "active", "latency": "12ms"},
    "agentdev": {"status": "active", "queue": "3"},
    "learning": {"status": "active", "sessions": "5"},
    "security": {"status": "active", "threats": "0"}
  },
  "performance": {
    "cpu_usage": "25%",
    "memory_usage": "60%",
    "disk_usage": "40%"
  }
}
```

### **2. Learning Dashboard**
```http
GET /api/monitoring/learning-dashboard
```

**Response:**
```json
{
  "dashboard_id": "dash123",
  "metrics": {
    "learning_sessions": 156,
    "success_rate": 0.942,
    "rollback_count": 3,
    "ethics_violations": 0,
    "performance_improvement": 0.235
  },
  "charts": {
    "success_rate_trend": [...],
    "learning_velocity": [...],
    "error_distribution": [...]
  }
}
```

## 🚨 **ERROR HANDLING**

### **Standard Error Response**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Input validation failed",
    "details": {
      "field": "input",
      "issue": "Required field missing"
    },
    "timestamp": "2025-09-26T10:00:00Z",
    "request_id": "req123"
  }
}
```

### **Error Codes**
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error
- `503` - Service Unavailable

## 📈 **RATE LIMITING**

### **Rate Limits**
- **General API**: 1000 requests/hour
- **Learning Endpoints**: 100 requests/hour
- **Security Endpoints**: 500 requests/hour
- **Privacy Endpoints**: 50 requests/hour

### **Rate Limit Headers**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 🔧 **DEVELOPMENT ENDPOINTS**

### **1. Development Mode**
```http
POST /api/dev/mode
```

**Request Body:**
```json
{
  "mode": "development",
  "features": {
    "debug_logging": true,
    "verbose_output": true,
    "test_mode": true
  }
}
```

### **2. Test Execution**
```http
POST /api/dev/test
```

**Request Body:**
```json
{
  "test_suite": "comprehensive",
  "test_types": ["unit", "integration", "security"],
  "parallel": true
}
```

## 📚 **SDK EXAMPLES**

### **Python SDK**
```python
from stillme_ai import StillMeClient

client = StillMeClient(api_key="your-api-key")

# Process AI request
response = client.process(
    input="What is machine learning?",
    context={"user_id": "user123"},
    options={"rationale": True}
)

# Start learning session
session = client.learning.start_session(
    user_id="user123",
    learning_type="self_improvement"
)

# Execute plugin
result = client.plugins.execute(
    plugin_name="calculator",
    operation="add",
    args=[1, 2, 3]
)
```

### **JavaScript SDK**
```javascript
import { StillMeClient } from 'stillme-ai-sdk';

const client = new StillMeClient('your-api-key');

// Process AI request
const response = await client.process({
  input: 'What is machine learning?',
  context: { user_id: 'user123' },
  options: { rationale: true }
});

// Start learning session
const session = await client.learning.startSession({
  user_id: 'user123',
  learning_type: 'self_improvement'
});
```

## 🔄 **WEBHOOKS**

### **Webhook Configuration**
```http
POST /api/webhooks/configure
```

**Request Body:**
```json
{
  "url": "https://your-app.com/webhook",
  "events": ["learning_completed", "security_alert", "privacy_request"],
  "secret": "webhook-secret"
}
```

### **Webhook Payload**
```json
{
  "event": "learning_completed",
  "timestamp": "2025-09-26T10:00:00Z",
  "data": {
    "session_id": "session123",
    "success_rate": 0.94,
    "improvements": ["accuracy", "safety"]
  },
  "signature": "webhook-signature"
}
```

## 📋 **CHANGELOG**

### **Version 1.0.0 (2025-09-26)**
- Initial API release
- Core AI processing endpoints
- Self-learning capabilities
- Security and privacy features
- Plugin system
- Ethics validation
- Monitoring and analytics

---

**For more information, visit our [GitHub repository](https://github.com/stillme-ai/framework) or contact support at support@stillme.ai**
