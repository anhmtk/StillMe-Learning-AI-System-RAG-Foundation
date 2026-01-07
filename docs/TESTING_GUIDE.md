# Testing Guide - Task 1 & Task 3

Hướng dẫn test sau khi deploy lên Railway.

## Prerequisites

1. **Backend đã deploy xong trên Railway**
   - Kiểm tra: `https://your-railway-app.up.railway.app/health`
   - Response: `{"status": "healthy"}`

2. **Set API_BASE environment variable**
   ```bash
   # Windows PowerShell
   $env:STILLME_API_BASE = "https://your-railway-app.up.railway.app"
   
   # Linux/Mac
   export STILLME_API_BASE="https://your-railway-app.up.railway.app"
   ```

## Task 1: Meta-Learning Dashboard Testing

### Test Script

```bash
# Chạy test script
python scripts/test_meta_learning_dashboard.py
```

### Manual Testing

1. **Access Dashboard UI** (nếu có Streamlit dashboard):
   - URL: `http://localhost:8501` (local) hoặc Railway dashboard URL
   - Navigate to: **Learning** page → **Meta-Learning Dashboard** tab
   - Kiểm tra 3 sub-tabs:
     - Retention Tracking
     - Curriculum Learning
     - Strategy Optimization

2. **Test API Endpoints** (nếu backend chạy):
   ```bash
   # Retention metrics
   curl https://your-railway-app.up.railway.app/api/meta-learning/retention?days=30
   
   # Source trust scores
   curl https://your-railway-app.up.railway.app/api/meta-learning/source-trust?days=30
   
   # Learning effectiveness
   curl https://your-railway-app.up.railway.app/api/meta-learning/learning-effectiveness?days=30
   
   # Curriculum
   curl https://your-railway-app.up.railway.app/api/meta-learning/curriculum?days=30
   
   # Strategy effectiveness
   curl https://your-railway-app.up.railway.app/api/meta-learning/strategy-effectiveness?days=30
   ```

### Expected Results

- ✅ All API endpoints return 200 OK
- ✅ Dashboard UI loads without errors
- ✅ Charts render correctly (Plotly)
- ✅ Data displays in tables/expanders

## Task 3: Request Traceability Testing

### Test Script

```bash
# Chạy test script
python scripts/test_request_traceability.py
```

### Manual Testing

1. **Test Chat with Trace ID**:
   ```bash
   curl -X POST https://your-railway-app.up.railway.app/api/chat/rag \
     -H "Content-Type: application/json" \
     -d '{"message": "What is StillMe?", "user_id": "test_user"}'
   ```
   
   **Expected Response**:
   ```json
   {
     "response": "...",
     "trace_id": "trace_20250107...",
     ...
   }
   ```

2. **Get Trace by ID**:
   ```bash
   # Replace {trace_id} with actual trace_id from step 1
   curl https://your-railway-app.up.railway.app/api/trace/{trace_id}
   ```
   
   **Expected Response**:
   ```json
   {
     "trace_id": "trace_20250107...",
     "timestamp": "2025-01-07T...",
     "query": "What is StillMe?",
     "stages": {
       "rag_retrieval": {...},
       "llm_generation": {...},
       "validation": {...},
       "post_processing": {...},
       "final_response": {
         "response_length": 123,
         "confidence_score": 0.85,
         "validation_passed": true,
         "epistemic_state": "KNOWN"
       }
     },
     "duration_ms": 1234.56
   }
   ```

3. **Test 404 for Non-existent Trace**:
   ```bash
   curl https://your-railway-app.up.railway.app/api/trace/trace_fake_123
   ```
   
   **Expected**: `404 Not Found`

4. **Test Correlation ID Header**:
   ```bash
   curl -X POST https://your-railway-app.up.railway.app/api/chat/rag \
     -H "Content-Type: application/json" \
     -H "X-Correlation-ID: custom-trace-id-123" \
     -d '{"message": "Test", "user_id": "test"}'
   ```
   
   **Expected**: Response body `trace_id` matches `X-Correlation-ID` header

### Expected Results

- ✅ Chat response includes `trace_id`
- ✅ GET `/api/trace/{trace_id}` returns full trace
- ✅ Trace contains all stages (rag_retrieval, llm_generation, validation, etc.)
- ✅ Non-existent trace returns 404
- ✅ Trace ID matches correlation ID header

## Troubleshooting

### Backend Not Running

**Error**: `[SKIP] Backend not running at ...`

**Solution**:
1. Check Railway deployment logs
2. Verify health endpoint: `curl https://your-railway-app.up.railway.app/health`
3. Check environment variables in Railway dashboard

### Trace Not Found (404)

**Error**: `Trace not found (404)`

**Possible Causes**:
1. Trace expired (24h TTL)
2. Trace not stored (check backend logs)
3. Wrong trace_id format

**Solution**:
1. Use trace_id immediately after chat request
2. Check backend logs for trace storage errors
3. Verify trace_id format: `trace_YYYYMMDDHHMMSS_xxxxxxxx`

### Dashboard Not Loading

**Error**: Dashboard UI errors or blank page

**Solution**:
1. Check Streamlit logs
2. Verify Plotly/pandas installed
3. Check browser console for errors
4. Verify API endpoints are accessible

## Quick Test Commands

```bash
# Set API base (replace with your Railway URL)
export STILLME_API_BASE="https://your-railway-app.up.railway.app"

# Run all tests
python scripts/test_meta_learning_dashboard.py
python scripts/test_request_traceability.py

# Or test manually
curl https://your-railway-app.up.railway.app/health
curl https://your-railway-app.up.railway.app/api/meta-learning/retention?days=30
```

## Success Criteria

### Task 1 (Meta-Learning Dashboard)
- ✅ All 8-9 API endpoint tests pass
- ✅ Dashboard UI accessible
- ✅ Charts render without errors

### Task 3 (Request Traceability)
- ✅ Chat response includes trace_id
- ✅ GET trace endpoint works
- ✅ Trace contains expected data
- ✅ 404 handling works correctly

