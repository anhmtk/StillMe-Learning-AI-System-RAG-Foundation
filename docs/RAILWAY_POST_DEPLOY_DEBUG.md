# Railway Post-Deploy Failure Debug Guide

## Cách Check Railway Logs

### Option 1: Railway Dashboard
1. Vào Railway dashboard: https://railway.app
2. Chọn project "stillme-backend"
3. Click vào tab "Deployments"
4. Click vào deployment bị fail (có thể là deployment mới nhất)
5. Xem logs ở tab "Logs" hoặc "Build Logs"
6. Tìm phần "Post-deploy" stage để xem error message

### Option 2: Railway CLI
```bash
# Install Railway CLI nếu chưa có
npm i -g @railway/cli

# Login
railway login

# View logs
railway logs --service stillme-backend

# View specific deployment logs
railway logs --deployment <deployment-id>
```

### Option 3: Railway API
```bash
# Get deployment logs via API
curl -H "Authorization: Bearer $RAILWAY_TOKEN" \
  https://api.railway.app/v1/deployments/<deployment-id>/logs
```

## Nguyên nhân thường gặp cho Post-Deploy Fail

### 1. Health Check Timeout
**Triệu chứng:**
- Post-deploy stage fail với error "Health check timeout"
- Service start nhưng health endpoint không respond trong thời gian cho phép

**Nguyên nhân:**
- Health check timeout quá ngắn (hiện tại: 1200s = 20 phút)
- Model download mất quá nhiều thời gian
- RAG initialization chậm
- Database connection timeout

**Giải pháp:**
- Đã tăng timeout lên 1200s trong `railway-backend.json`
- Có thể cần tăng thêm nếu vẫn fail
- Check xem health endpoint có respond ngay không

### 2. Health Endpoint Not Responding
**Triệu chứng:**
- Health check fail với "Connection refused" hoặc "Timeout"
- Service start nhưng `/health` endpoint không available

**Nguyên nhân:**
- Port conflict (health check server và FastAPI cùng port)
- Health endpoint chưa ready khi health check chạy
- Network issue trong Railway container

**Giải pháp:**
- Check `start_backend.py` - health check server có start đúng không
- Verify `/health` endpoint trong `main.py` có respond ngay không
- Check logs để xem health endpoint có được register không

### 3. Database/ChromaDB Initialization Fail
**Triệu chứng:**
- Post-deploy fail với database connection error
- Schema mismatch errors
- ChromaDB initialization timeout

**Nguyên nhân:**
- ChromaDB schema mismatch
- Database file corruption
- Volume mount issue

**Giải pháp:**
- Check logs cho ChromaDB errors
- Verify volumes được mount đúng
- Check `FORCE_DB_RESET_ON_STARTUP` setting

### 4. Model Download Timeout
**Triệu chứng:**
- Post-deploy fail sau khi start service
- Logs show "Downloading model..." nhưng không complete

**Nguyên nhân:**
- Model download mất quá nhiều thời gian (> 20 phút)
- Network issue khi download từ HuggingFace
- Persistent volume chưa có model cached

**Giải pháp:**
- Pre-download model trong Dockerfile (MODEL_WARMUP=true)
- Tăng health check timeout thêm
- Check persistent volume có model cached không

### 5. Environment Variables Missing
**Triệu chứng:**
- Post-deploy fail với "Environment variable not set"
- Service start nhưng crash ngay sau đó

**Nguyên nhân:**
- Required env vars không được set trong Railway
- Env vars bị override hoặc reset

**Giải pháp:**
- Check Railway Variables tab
- Verify all required env vars are set
- Check `.env.example` for required vars

## Debug Steps

### Step 1: Check Health Endpoint Manually
```bash
# SSH vào Railway container (nếu có)
railway shell

# Test health endpoint
curl http://localhost:$PORT/health

# Expected response:
# {"status":"healthy","service":"stillme-backend","timestamp":"..."}
```

### Step 2: Check Service Startup Logs
Tìm trong logs:
- "Starting immediate healthcheck server..."
- "Healthcheck server started"
- "FastAPI app imported successfully"
- "RAG components initialization..."

Nếu không thấy các messages này, service chưa start đúng.

### Step 3: Check RAG Initialization
Tìm trong logs:
- "Initializing RAG components..."
- "ChromaDB client initialized"
- "Embedding service initialized"
- "RAG retrieval initialized"

Nếu có errors ở đây, RAG init fail → service có thể start nhưng không ready.

### Step 4: Check Model Download
Tìm trong logs:
- "Pre-downloading embedding model..."
- "Model downloaded and verified"
- "Model cached at: /app/hf_cache"

Nếu model download fail hoặc timeout, có thể gây post-deploy fail.

## Quick Fixes

### Fix 1: Disable Post-Deploy Health Check (Temporary)
Nếu post-deploy không critical, có thể disable:
```json
// railway-backend.json
{
  "deploy": {
    "healthcheckPath": null,  // Disable health check
    "healthcheckTimeout": null
  }
}
```

### Fix 2: Increase Timeout Further
```json
// railway-backend.json
{
  "deploy": {
    "healthcheckTimeout": 1800  // 30 minutes
  }
}
```

### Fix 3: Pre-warm Model in Dockerfile
```dockerfile
# Dockerfile
ARG MODEL_WARMUP=true
RUN if [ "$MODEL_WARMUP" = "true" ]; then \
      python /app/scripts/model_warmup.py || true; \
    fi
```

### Fix 4: Add Health Check Retry Logic
Modify `start_backend.py` to ensure health endpoint is always available:
- Health check server starts immediately
- FastAPI app starts in background
- Health endpoint responds even during RAG init

## Next Steps

1. **Check Railway logs** để xem exact error message
2. **Identify failure point**: Build, Deploy, Network, hoặc Post-deploy?
3. **Check health endpoint** có respond không
4. **Verify model download** có complete không
5. **Check RAG initialization** có errors không

Sau khi có logs, có thể fix chính xác hơn.

