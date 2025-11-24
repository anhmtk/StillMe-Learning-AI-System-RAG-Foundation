# Railway Redis Setup Guide

## Tổng quan

StillMe sử dụng Redis để cache embeddings, RAG queries, và LLM responses để giảm latency và cost. Code đã được implement với **graceful fallback**: nếu Redis không available, hệ thống sẽ tự động dùng in-memory cache (không ảnh hưởng chức năng, chỉ mất cache khi restart).

## Setup Redis trên Railway

### Bước 1: Thêm Redis Service

1. Vào Railway Dashboard → Project của bạn
2. Click **"+ New"** → **"Database"** → **"Add Redis"**
3. Railway sẽ tự động tạo Redis service và set `REDIS_URL` environment variable

### Bước 2: Verify Environment Variable

Railway sẽ tự động:
- Tạo `REDIS_URL` environment variable trong backend service
- Format: `redis://default:<password>@<host>:<port>`

**Không cần làm gì thêm!** Code đã tự động đọc `REDIS_URL` từ environment.

### Bước 3: Verify Connection

Sau khi deploy, check logs:
```
✅ Redis cache enabled: redis://...
```

Nếu thấy warning:
```
⚠️ Redis connection failed - caching disabled: ...
```

→ Check:
1. Redis service đã được tạo chưa?
2. `REDIS_URL` có trong environment variables không?
3. Backend service có được link với Redis service không?

## Fallback Behavior

Nếu Redis không available:
- ✅ Hệ thống vẫn hoạt động bình thường
- ✅ Sử dụng in-memory cache (không persistent)
- ⚠️ Cache sẽ mất khi restart service
- ⚠️ Không có distributed caching (mỗi instance có cache riêng)

## Benefits khi có Redis

- ✅ **50-70% latency reduction** cho cached queries
- ✅ **Persistent cache** across restarts
- ✅ **Distributed caching** (nhiều instances share cache)
- ✅ **Reduced embedding costs** (cache embeddings)
- ✅ **Better scalability** cho high-traffic scenarios

## Manual Setup (nếu cần)

Nếu Railway không tự động link Redis:

1. Vào Backend Service → **"Variables"**
2. Add variable:
   - Key: `REDIS_URL`
   - Value: Copy từ Redis service → **"Connect"** → **"REDIS_URL"**

## Testing

Sau khi setup, test bằng cách:
1. Gửi một query (sẽ cache)
2. Gửi lại query tương tự (sẽ hit cache, nhanh hơn)
3. Check logs: `Cache hit` vs `Cache miss`

## Troubleshooting

### Redis connection failed
- Check `REDIS_URL` có đúng format không
- Check Redis service đã start chưa
- Check network connectivity (Railway tự động handle)

### Cache không hoạt động
- Check logs có `✅ Redis cache enabled` không
- Verify `REDIS_URL` trong environment variables
- Check Redis service status trên Railway dashboard

### Performance không cải thiện
- Cache cần thời gian để warm up (sau vài queries)
- Check cache hit rate trong logs
- Verify TTL settings (default: 1h cho queries, 24h cho embeddings)

