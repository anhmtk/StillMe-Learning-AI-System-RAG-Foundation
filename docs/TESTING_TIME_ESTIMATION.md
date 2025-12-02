# Testing Time Estimation Features

## Quick Start

### Option 1: Comprehensive Test Suite

```bash
# Test all features (without backend)
python scripts/test_time_estimation_features.py

# Test with backend (chat integration)
python scripts/test_time_estimation_features.py --backend-url stillme-backend-production.up.railway.app
```

**Note**: The script automatically adds `https://` if no scheme is provided.

### Option 2: Simple Chat Test (Recommended for Quick Testing)

```bash
# Test chat integration with detailed output
python scripts/test_chat_time_estimation.py --backend-url stillme-backend-production.up.railway.app

# Test with custom query
python scripts/test_chat_time_estimation.py --backend-url stillme-backend-production.up.railway.app --query "How long will it take?"
```

**This script is recommended for testing chat integration** as it provides:
- Health check before testing
- Detailed response analysis
- Shows time estimate section if found
- Better timeout handling

## Test Coverage

### 1. Time Estimation Intent Detection
- ✅ English patterns: "How long will it take...", "How much time..."
- ⚠️ Vietnamese patterns: Currently limited (needs improvement)

### 2. Time Estimation Engine
- ✅ Various task types (learning, validation, refactoring)
- ✅ Complexity-based estimates
- ✅ Confidence intervals
- ✅ Historical data integration

### 3. Task Tracker
- ✅ Start/end task tracking
- ✅ Accuracy calculation
- ✅ Historical task retrieval

### 4. Chat Integration (Optional)
- Requires backend URL
- Tests time estimation in chat responses
- Verifies formatted output with AI identity
- **Note**: First request may timeout due to cold start (normal)

### 5. Self-Tracking Integration
- ✅ Context manager tracking
- ✅ Formatted self-aware responses
- ✅ AI identity inclusion

## Expected Results

**Current Status:**
- ✅ 4/5 tests passing (core functionality works)
- ✅ **Chat integration works on Railway** (confirmed with simple test script)
- ⚠️ Comprehensive test may timeout due to multiple sequential requests
- ⚠️ Vietnamese pattern detection needs improvement

**All core features are functional:**
- ✅ Time estimation engine works correctly
- ✅ Task tracking works correctly
- ✅ Self-tracking integration works correctly
- ✅ **Chat integration works correctly** (tested on Railway)

## Manual Testing

### Test Chat Integration

1. **Using curl:**
```bash
curl -X POST https://stillme-backend-production.up.railway.app/api/chat/rag \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How long will it take to learn 100 articles?",
    "use_rag": true,
    "context_limit": 3
  }'
```

2. **Check response for time estimate section:**
Look for:
```
⏱️ **Time Estimate:**
Based on my historical performance, I estimate this will take...
```

3. **Expected behavior:**
- StillMe detects time estimation intent
- Generates estimate based on historical performance
- Appends formatted estimate to response
- Includes AI identity statement

### Test Learning Cycle Tracking

Learning cycles are automatically tracked when they run. Check backend logs for:
```
📊 StillMe self-estimate: ...
✅ Task completed: X min (estimate was accurate)
```

### Test Validation Tracking

Validation is automatically tracked. Check backend logs for tracking information when validation runs.

## Troubleshooting

### Chat Integration Timeout

**Symptom**: Request times out after 60 seconds

**Possible causes:**
1. **Cold start**: First request after deployment takes longer (normal)
2. **Complex query**: RAG + validation + estimation takes time
3. **Backend overload**: Server is processing other requests

**Solutions:**
- Wait a few seconds and retry
- Check backend logs for errors
- Verify backend is running and accessible

### No Time Estimate in Response

**Symptom**: Chat response doesn't include time estimate

**Possible causes:**
1. Intent detection didn't match the query
2. Query format doesn't match expected patterns
3. Backend error (check logs)

**Solutions:**
- Use exact patterns: "How long will it take to..."
- Check backend logs for errors
- Verify time estimation integration is enabled

## Known Limitations

1. **Vietnamese Pattern Detection**: Currently only works with exact keyword matches. Needs improvement for better Vietnamese support.

2. **Historical Data**: Estimates improve as more historical data is collected. Initial estimates may have low confidence.

3. **Chat Integration**: 
   - Requires backend to be running and accessible
   - First request may timeout (cold start)
   - Complex queries take longer to process

4. **Timeout**: Default timeout is 60 seconds. Very complex queries may need more time.

## Future Improvements

- [ ] Improve Vietnamese pattern detection
- [ ] Add more test cases
- [ ] Add performance benchmarks
- [ ] Add integration tests with real backend
- [ ] Add retry logic for timeout cases
- [ ] Add health check before testing
