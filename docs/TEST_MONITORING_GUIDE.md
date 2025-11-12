# 📊 Test Monitoring Guide

## Where to See Test Progress

Khi chạy `run_comprehensive_tests.py`, bạn có thể xem progress ở 3 nơi:

### 1. Terminal (Nơi chạy test script) ✅

**Đây là nơi chính để xem progress!**

Script sẽ hiển thị:
```
Testing batch 1/21 (1-10/202)
Testing batch 2/21 (11-20/202)
...
INFO:__main__:Saved 100 results to D:\...\comprehensive_test_20251112_230243.json
Testing batch 11/21 (101-110/202)
...
```

**Progress indicators:**
- `Testing batch X/21` - Đang test batch thứ X
- `(Y-Z/202)` - Đang test câu hỏi Y đến Z trong tổng 202 câu
- `Saved N results` - Đã lưu N kết quả vào file JSON

### 2. Backend Logs (Terminal/Console nơi backend chạy) ✅

**Nếu backend chạy local:**
- Xem terminal nơi bạn chạy `uvicorn` hoặc `python -m backend.api.main`
- Logs sẽ hiển thị mỗi request từ test script

**Nếu backend deploy trên Railway:**
- Vào Railway Dashboard → Chọn service → Tab "Logs"
- Hoặc dùng Railway CLI: `railway logs`

**Logs bạn sẽ thấy:**
```
INFO:backend.api.routers.chat_router:⏱️ RAG retrieval took 0.234s
INFO:backend.api.routers.chat_router:🌐 Detected language: en (took 0.001s) for question: 'What is the meaning of life?...'
INFO:backend.api.routers.chat_router:⏱️ LLM inference took 1.456s
INFO:backend.api.routers.chat_router:⏱️ Validation took 0.123s
```

**Mỗi câu hỏi test sẽ tạo ra:**
- 1 log line cho RAG retrieval
- 1 log line cho language detection
- 1 log line cho LLM inference
- 1 log line cho validation
- = **~4-5 log lines per question**

Với 202 questions, bạn sẽ thấy **~800-1000 log lines** trong backend logs!

### 3. Dashboard (Limited) ⚠️

**Hiện tại dashboard KHÔNG có test progress viewer.**

Tuy nhiên, bạn có thể xem:
- **Validation Page**: Validation metrics sẽ tăng khi test chạy
- **Overview Page**: System metrics (nhưng không phải test-specific)

**💡 Tip:** Mở Validation page trong dashboard và refresh để xem validation count tăng dần.

### 4. Test Progress Viewer (Script mới) ✅

**Real-time progress monitor:**

```bash
# Mở terminal mới và chạy:
python scripts/view_test_progress.py
```

Script này sẽ:
- Monitor file results JSON real-time
- Hiển thị progress: `✅ Progress: 150 completed | Success: 145 | Errors: 3 | Timeouts: 2`
- Update mỗi giây
- Show final summary khi bạn Ctrl+C

**Output example:**
```
============================================================
TEST PROGRESS MONITOR
============================================================
Watching for test results...
Press Ctrl+C to stop

📁 Found results file: comprehensive_test_20251112_230243.json
✅ Progress: 150 completed | Success: 145 | Errors: 3 | Timeouts: 2 | Avg Latency: 1.23s | Avg Confidence: 0.85
```

## Recommended Setup

### Terminal 1: Run Tests
```bash
python scripts/run_comprehensive_tests.py
```

### Terminal 2: Monitor Progress (Optional)
```bash
python scripts/view_test_progress.py
```

### Browser: View Backend Logs (Railway)
- Railway Dashboard → Logs tab
- Hoặc local terminal nơi backend chạy

### Browser: View Dashboard (Optional)
- Open dashboard → Validation page
- Refresh để xem validation metrics tăng

## Understanding the Output

### Test Script Output:
```
Testing batch 10/21 (91-100/202)
INFO:__main__:Saved 100 results to ...comprehensive_test_20251112_230243.json
```

**Nghĩa là:**
- Đang test batch 10 trong tổng 21 batches
- Đang test câu hỏi 91-100 trong tổng 202 câu
- Đã lưu 100 kết quả vào file JSON (checkpoint)

### Backend Logs:
```
INFO:backend.api.routers.chat_router:⏱️ RAG retrieval took 0.234s
INFO:backend.api.routers.chat_router:⏱️ LLM inference took 1.456s
```

**Nghĩa là:**
- Mỗi câu hỏi đang được xử lý
- RAG retrieval: 0.234s
- LLM inference: 1.456s
- Total: ~1.7s per question

### Results File:
```json
{
  "question_id": "test_000001",
  "question": "What is the meaning of life?",
  "response": "StillMe's response...",
  "confidence_score": 0.85,
  "latency": 1.23,
  "status": "success"
}
```

**File location:** `tests/results/comprehensive_test_YYYYMMDD_HHMMSS.json`

## Troubleshooting

### Không thấy logs trong backend?
- ✅ Check backend đang chạy: `curl http://localhost:8000/api/status`
- ✅ Check log level: Backend logs ở INFO level
- ✅ Check Railway logs nếu deploy: Railway Dashboard → Logs

### Test script chạy nhưng không có output?
- ✅ Check API_BASE trong `run_comprehensive_tests.py` đúng chưa
- ✅ Check backend đang chạy và accessible
- ✅ Check network/firewall không block requests

### Muốn xem progress trong dashboard?
- ⚠️ Hiện tại chưa có test progress page trong dashboard
- 💡 Có thể xem Validation metrics tăng dần
- 💡 Hoặc dùng `view_test_progress.py` script

## Next Steps

Sau khi test xong:
1. Xem results file: `tests/results/comprehensive_test_*.json`
2. Analyze results: `python scripts/view_test_suite.py` (xem summary)
3. Check feedback: `curl http://localhost:8000/api/feedback/stats`

