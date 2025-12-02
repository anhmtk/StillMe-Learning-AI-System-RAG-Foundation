# Testing Time Estimation Features

## Quick Start

Run the comprehensive test suite:

```bash
# Test all features (without backend)
python scripts/test_time_estimation_features.py

# Test with backend (chat integration)
python scripts/test_time_estimation_features.py --backend-url http://localhost:8000
# Or for Railway deployment:
python scripts/test_time_estimation_features.py --backend-url https://your-backend.railway.app
```

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

### 5. Self-Tracking Integration
- ✅ Context manager tracking
- ✅ Formatted self-aware responses
- ✅ AI identity inclusion

## Expected Results

**Current Status:**
- ✅ 3/5 tests passing (core functionality works)
- ⚠️ Vietnamese pattern detection needs improvement
- ⚠️ Chat integration requires backend URL

**All core features are functional:**
- Time estimation engine works correctly
- Task tracking works correctly
- Self-tracking integration works correctly

## Manual Testing

### Test Chat Integration

1. Start backend:
```bash
cd backend
python -m uvicorn api.main:app --reload
```

2. Send test request:
```bash
curl -X POST http://localhost:8000/api/chat/rag \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How long will it take to learn 100 articles?",
    "use_rag": true,
    "context_limit": 3
  }'
```

3. Check response for time estimate section:
```
⏱️ **Time Estimate:**
Based on my historical performance, I estimate this will take...
```

### Test Learning Cycle Tracking

Learning cycles are automatically tracked when they run. Check logs for:
```
📊 StillMe self-estimate: ...
✅ Task completed: X min (estimate was accurate)
```

### Test Validation Tracking

Validation is automatically tracked. Check logs for tracking information when validation runs.

## Known Limitations

1. **Vietnamese Pattern Detection**: Currently only works with exact keyword matches. Needs improvement for better Vietnamese support.

2. **Historical Data**: Estimates improve as more historical data is collected. Initial estimates may have low confidence.

3. **Chat Integration**: Requires backend to be running and accessible.

## Future Improvements

- [ ] Improve Vietnamese pattern detection
- [ ] Add more test cases
- [ ] Add performance benchmarks
- [ ] Add integration tests with real backend

