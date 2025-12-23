# Railway Auto-Deploy Issue Analysis

## Vấn đề
Khi push code lên repo, Railway tự động deploy nhưng không thành công. Phải redeploy thủ công cả 2 services (backend và dashboard) mới được.

## Nguyên nhân có thể

### 1. **Health Check Timeout Quá Ngắn**
- **Hiện tại**: `healthcheckTimeout: 600` (10 phút) trong `railway-backend.json`
- **Vấn đề**: 
  - Model download lần đầu: 3-5 phút
  - RAG initialization: 30-60s
  - ChromaDB schema check: 10-30s
  - **Tổng cộng có thể > 10 phút** nếu model chưa được cache
- **Giải pháp**: Tăng timeout lên 900s (15 phút) hoặc 1200s (20 phút)

### 2. **Service Dependencies (Dashboard phụ thuộc Backend)**
- Dashboard có thể cần backend URL để khởi động
- Nếu backend chưa ready, dashboard sẽ fail
- **Giải pháp**: Thêm health check cho dashboard, hoặc retry logic

### 3. **Race Condition giữa Auto-Deploy và Manual Redeploy**
- **Auto-deploy**: 
  - Trigger ngay khi push (có thể trước khi code được merge hoàn toàn)
  - Volumes/cache có thể chưa được mount đúng
  - Model chưa được cache → download mất thời gian → timeout
- **Manual redeploy**:
  - Volumes/cache đã có sẵn từ lần deploy trước
  - Model đã được cache → không cần download → nhanh hơn → pass
- **Giải pháp**: Đảm bảo volumes được mount trước khi health check

### 4. **Model Download Blocking Startup**
- `start_backend.py` pre-downloads model TRƯỚC khi start FastAPI
- Nếu model chưa cache, có thể mất 3-5 phút
- Trong thời gian này, health check có thể fail
- **Giải pháp**: Health check server đã được implement, nhưng có thể cần tăng timeout

### 5. **RAG Initialization Errors**
- Nếu ChromaDB schema mismatch, initialization có thể fail
- Service vẫn start nhưng RAG features không available
- Health check có thể pass nhưng service không hoạt động đúng
- **Giải pháp**: Health check endpoint nên check RAG status

## Giải pháp đề xuất

### Giải pháp 1: Tăng Health Check Timeout
```json
// railway-backend.json
{
  "deploy": {
    "healthcheckTimeout": 1200  // 20 phút thay vì 10 phút
  }
}
```

### Giải pháp 2: Thêm Health Check cho Dashboard
```json
// railway-dashboard.json
{
  "deploy": {
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300  // 5 phút
  }
}
```

### Giải pháp 3: Đảm bảo Health Endpoint Luôn Available
- ✅ Đã có: `start_backend.py` có health check server
- ✅ Đã có: `/health` endpoint trong `main.py`
- ⚠️ Cần check: Health endpoint có return đúng status không?

### Giải pháp 4: Pre-warm Model trong Dockerfile
- Hiện tại: Model download ở runtime (trong `start_backend.py`)
- Có thể: Pre-download trong Dockerfile build stage
- Trade-off: Build time tăng nhưng startup time giảm

### Giải pháp 5: Thêm Retry Logic cho Auto-Deploy
- Railway có thể tự động retry nếu health check fail
- Check `restartPolicyMaxRetries` trong config

## Checklist Debug

1. ✅ Check Railway logs khi auto-deploy fail
2. ✅ Check health check response time
3. ✅ Check model download time (first deploy vs redeploy)
4. ✅ Check RAG initialization time
5. ✅ Check service dependencies (dashboard → backend)
6. ✅ Check volumes mount status

## Next Steps

1. Tăng `healthcheckTimeout` trong `railway-backend.json`
2. Thêm health check cho dashboard
3. Monitor logs để xác định exact failure point
4. Consider pre-warming model trong Dockerfile nếu cần

