# Railway Persistent Cache Setup Guide

## Vấn đề

SentenceTransformer model (`all-MiniLM-L6-v2`) bị tải lại mỗi khi Container restart/redeploy trên Railway, gây:
- Lãng phí băng thông (download ~80MB mỗi lần)
- Làm chậm quá trình khởi động (30-60 giây)
- Tăng chi phí compute

**Nguyên nhân:** Cache mặc định (`/root/.cache/huggingface/`) là ephemeral storage trên Railway, bị xóa khi container restart.

## Giải pháp: Persistent Volume

### Bước 1: Khai báo Volume trong railway.json (Config-as-Code)

File `railway.json` đã được cấu hình với Persistent Volume:

```json
{
  "volumes": [
    {
      "name": "stillme-hf-cache",
      "mountPath": "/app/hf_cache",
      "sizeGB": 1
    }
  ]
}
```

**Quan trọng:** Sau khi push code lên GitHub, bạn cần:
1. Vào Railway Dashboard → Service → Settings → **Config-as-code**
2. Khai báo đường dẫn file: `/railway.json`
3. Railway sẽ tự động tạo volume và mount vào `/app/hf_cache`

### Bước 2: Cấu hình Environment Variable

Trong Railway Service → Variables, thêm:

```bash
PERSISTENT_CACHE_PATH=/app/hf_cache
```

**Lưu ý:** Path phải khớp với `mountPath` trong `railway.json` (`/app/hf_cache`).

### Bước 3: Redeploy Service

Sau khi set environment variable và Railway tạo volume từ `railway.json`, Railway sẽ tự động redeploy. Lần đầu tiên:
- Model sẽ được download và cache vào `/app/hf_cache/`
- Log sẽ hiển thị: `Using persistent cache path: /app/hf_cache`

Các lần restart/redeploy sau:
- Model sẽ load từ cache (nhanh hơn nhiều)
- Không cần download lại

## Kiểm tra

### Xem log để xác nhận:

```bash
# Log sẽ hiển thị:
✓ Embedding service initialized
Using persistent cache path: /app/hf_cache
Embedding model 'all-MiniLM-L6-v2' loaded successfully
Model cached at: /app/hf_cache
```

### Nếu không thấy persistent cache path:

```bash
# Warning sẽ xuất hiện:
⚠️ No persistent cache path configured. Model will be re-downloaded on restart.
Set PERSISTENT_CACHE_PATH or HF_CACHE_PATH environment variable.
```

## Alternative: Custom Cache Path

Nếu bạn muốn dùng path khác, có thể set:

```bash
HF_CACHE_PATH=/custom/path/to/cache
```

Code sẽ ưu tiên `PERSISTENT_CACHE_PATH` trước, sau đó mới dùng `HF_CACHE_PATH`.

## Troubleshooting

### Volume không mount được

- Kiểm tra mount path trong Railway Volumes tab
- Đảm bảo path bắt đầu bằng `/` (absolute path)
- Restart service sau khi thêm volume

### Permission denied

- Railway tự động set permissions cho volume
- Nếu vẫn lỗi, kiểm tra log để xem exact error

### Cache không persist

- Đảm bảo volume đã được mount đúng path
- Kiểm tra `PERSISTENT_CACHE_PATH` env var đã set
- Xem log để confirm cache path được sử dụng

## Chi phí

- Railway Persistent Volume: ~$0.25/GB/month
- 1GB đủ cho nhiều models, rất rẻ so với chi phí download lại mỗi lần restart

## Kết quả

✅ Model chỉ download **1 lần duy nhất**  
✅ Các lần restart sau load từ cache (nhanh)  
✅ Tiết kiệm băng thông và thời gian khởi động  
✅ Giảm chi phí compute

