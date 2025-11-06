# Railway Deployment Checklist - Persistent Cache & Validation Fix

## 🚀 Thứ tự triển khai (QUAN TRỌNG)

### Bước 1: Push Code lên GitHub
```bash
git add .
git commit -m "Fix: Add persistent cache config and lower validation threshold"
.\scripts\push_with_token.ps1
```

### Bước 2: Khai báo Config-as-Code trên Railway Dashboard

1. Vào **Railway Dashboard** → **stillme-backend** Service
2. Chọn tab **"Settings"**
3. Tìm section **"Config-as-code"** hoặc **"Railway Config File"**
4. Trong field **"Railway Config File"**, nhập: `/railway.json`
5. Click **"Save"** hoặc **"Update"**

→ Railway sẽ tự động detect và apply config từ `railway.json`, bao gồm:
- Tạo Persistent Volume: `stillme-hf-cache`
- Mount vào: `/app/hf_cache`
- Size: 1GB

### Bước 3: Set Environment Variable

1. Vẫn trong **Settings** → Tab **"Variables"**
2. Thêm biến môi trường mới:
   - **Key:** `PERSISTENT_CACHE_PATH`
   - **Value:** `/app/hf_cache`
3. Click **"Save"**

→ Railway sẽ tự động restart service sau khi thêm env var.

### Bước 4: Kiểm tra Logs

Sau khi deploy xong, kiểm tra logs để xác nhận:

```bash
# Log mong đợi:
✓ Embedding service initialized
Using persistent cache path: /app/hf_cache
Embedding model 'all-MiniLM-L6-v2' loaded successfully
Model cached at: /app/hf_cache
```

### Bước 5: Test Validation Fix

Gửi một câu hỏi về StillMe để test:
- Response không còn bị chặn với `422 - low_overlap`
- Response có citation `[1]`, `[2]` sẽ được chấp nhận dù overlap thấp

## ✅ Checklist

- [ ] Code đã được push lên GitHub
- [ ] Railway Config-as-Code đã khai báo `/railway.json`
- [ ] Environment Variable `PERSISTENT_CACHE_PATH=/app/hf_cache` đã set
- [ ] Service đã restart sau khi set env var
- [ ] Logs hiển thị "Using persistent cache path: /app/hf_cache"
- [ ] Test chat endpoint - không còn 422 low_overlap error
- [ ] Model chỉ download 1 lần, các lần restart sau load từ cache

## 🔍 Troubleshooting

### Volume không được tạo tự động

Nếu Railway không tự động tạo volume từ `railway.json`:
1. Vào **Settings** → **Volumes** tab
2. Click **"New Volume"** thủ công
3. Name: `stillme-hf-cache`
4. Mount path: `/app/hf_cache`
5. Size: 1GB

### Config-as-Code không apply

Nếu Railway không detect `railway.json`:
1. Kiểm tra file đã được push lên GitHub chưa
2. Kiểm tra path trong Config-as-Code: `/railway.json` (phải có dấu `/` đầu)
3. Thử restart service thủ công

### Cache vẫn không persist

1. Kiểm tra env var `PERSISTENT_CACHE_PATH` đã set đúng chưa
2. Kiểm tra volume đã mount vào `/app/hf_cache` chưa
3. Xem logs để confirm cache path được sử dụng

