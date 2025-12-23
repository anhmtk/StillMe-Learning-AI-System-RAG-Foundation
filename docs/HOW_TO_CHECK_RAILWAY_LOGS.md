# Cách Check Railway Logs để Debug Post-Deploy Failure

## Phương pháp 1: Railway Dashboard (Dễ nhất)

### Bước 1: Vào Railway Dashboard
1. Mở browser, vào: https://railway.app
2. Login vào account của bạn
3. Chọn project "stillme-backend" (hoặc project name của bạn)

### Bước 2: Xem Deployments
1. Click vào tab **"Deployments"** ở menu trên
2. Bạn sẽ thấy list các deployments, deployment mới nhất ở trên cùng
3. Tìm deployment có status **"Failed"** hoặc có icon đỏ

### Bước 3: Xem Logs của Deployment Failed
1. Click vào deployment failed đó
2. Bạn sẽ thấy các stages:
   - ✅ Initialization (thường pass)
   - ✅ Build (thường pass)
   - ✅ Deploy (thường pass)
   - ✅ Network (thường pass)
   - ❌ **Post-deploy** (thường fail ở đây)

3. Click vào stage **"Post-deploy"** để xem logs
4. Tìm các error messages như:
   - "Health check timeout"
   - "Connection refused"
   - "Service unavailable"
   - "Health check failed"

### Bước 4: Xem Service Logs
1. Quay lại tab **"Deployments"**
2. Click vào deployment **"ACTIVE"** (deployment thành công)
3. Click button **"View logs"** (màu xanh)
4. Scroll xuống để xem logs khi service start
5. Tìm các messages:
   - "🚀 Starting immediate healthcheck server..."
   - "✅ Healthcheck server started"
   - "📦 Pre-downloading embedding model..."
   - "✅ Model downloaded and verified"
   - "Importing FastAPI application..."
   - "FastAPI app imported successfully"
   - "🚀 StillMe Backend - FastAPI Startup Event"
   - "📋 /health endpoint is available immediately"

## Phương pháp 2: Railway CLI

### Cài đặt Railway CLI
```bash
npm i -g @railway/cli
```

### Login
```bash
railway login
```

### Xem Logs
```bash
# Xem logs của service backend
railway logs --service stillme-backend

# Xem logs của deployment cụ thể
railway logs --deployment <deployment-id>

# Xem logs real-time
railway logs --service stillme-backend --follow
```

### Lấy Deployment ID
```bash
# List deployments
railway status

# Hoặc vào Railway dashboard, click vào deployment, URL sẽ có deployment-id
```

## Phương pháp 3: Test Health Endpoint Manually

### Nếu có Railway Shell access:
```bash
railway shell

# Test health endpoint
curl http://localhost:$PORT/health

# Expected response:
# {"status":"healthy","service":"stillme-backend","timestamp":"..."}
```

### Nếu không có shell, test từ bên ngoài:
```bash
# Lấy Railway URL từ dashboard
curl https://your-backend-url.railway.app/health
```

## Những gì cần tìm trong Logs

### 1. Health Check Server Start
```
🚀 Starting immediate healthcheck server...
✅ Healthcheck server started - Railway healthcheck will pass immediately
```
**Nếu không thấy**: Health check server không start → service không ready

### 2. Model Download
```
📦 Pre-downloading embedding model...
⏳ Downloading model: paraphrase-multilingual-MiniLM-L12-v2...
✅ Model downloaded and verified (embedding dimension: 384)
✅ Model cached at: /app/hf_cache
```
**Nếu không thấy hoặc timeout**: Model download fail → có thể gây post-deploy fail

### 3. FastAPI App Import
```
Importing FastAPI application...
FastAPI app imported successfully
```
**Nếu có error**: FastAPI app không import được → service không start

### 4. RAG Initialization
```
Initializing RAG components...
✓ ChromaDB client initialized
✓ Embedding service initialized
✓ RAG retrieval initialized
```
**Nếu có errors**: RAG init fail → service có thể start nhưng không ready

### 5. Health Endpoint Available
```
🚀 StillMe Backend - FastAPI Startup Event
📋 /health endpoint is available immediately
```
**Nếu không thấy**: Health endpoint không available → health check sẽ fail

## Common Error Messages và Fixes

### Error 1: "Health check timeout"
**Nguyên nhân**: Health check mất quá nhiều thời gian (> 1200s)
**Fix**: Đã tăng timeout lên 1200s, có thể cần tăng thêm

### Error 2: "Connection refused"
**Nguyên nhân**: Health endpoint không respond
**Fix**: Check xem health check server có start không

### Error 3: "Service unavailable"
**Nguyên nhân**: Service start nhưng crash ngay sau đó
**Fix**: Check logs để xem crash reason

### Error 4: "Model download timeout"
**Nguyên nhân**: Model download mất > 20 phút
**Fix**: Pre-download model trong Dockerfile

## Next Steps Sau Khi Có Logs

1. **Copy error message** từ logs
2. **Identify failure point**: Build, Deploy, Network, hoặc Post-deploy?
3. **Check timing**: Model download mất bao lâu? RAG init mất bao lâu?
4. **Verify health endpoint**: Có respond không? Response time bao nhiêu?
5. **Share logs với tôi** để tôi có thể fix chính xác hơn

