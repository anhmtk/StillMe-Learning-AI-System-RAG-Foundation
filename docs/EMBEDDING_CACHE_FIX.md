# Embedding Cache Path Mismatch - Fix Guide

## Vấn Đề

Model `paraphrase-multilingual-MiniLM-L12-v2` được download ở format HuggingFace:
```
/app/hf_cache/models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2/
```

Nhưng `SentenceTransformer` tìm ở format sentence-transformers:
```
/app/hf_cache/sentence_transformers/paraphrase-multilingual-MiniLM-L12-v2/
```

**Hậu quả:**
- Embeddings không hiệu quả
- Retrieval quality cực thấp: `max_similarity=0.037 < 0.1`
- High average distance: `0.963`

## Giải Pháp

### 1. Auto-Fix trong EmbeddingService

Script `backend/utils/fix_embedding_cache.py` tự động:
- Tìm model trong HuggingFace format
- Copy/symlink sang sentence-transformers format
- Được gọi tự động khi `EmbeddingService` khởi tạo

### 2. Manual Fix (nếu cần)

```python
from backend.utils.fix_embedding_cache import fix_embedding_model_cache

# Fix cache path mismatch
success = fix_embedding_model_cache("paraphrase-multilingual-MiniLM-L12-v2")
```

### 3. Verify Cache

```python
from backend.utils.model_cache import verify_model_cache

status = verify_model_cache("paraphrase-multilingual-MiniLM-L12-v2")
print(f"Model files found: {status.model_files_found}")
print(f"Cache path: {status.path}")
```

## Testing

Sau khi fix, verify:
1. Model được load từ cache (không download lại)
2. Embedding similarity > 0.1 (thay vì 0.037)
3. Average distance < 0.5 (thay vì 0.963)

## Notes

- Fix được gọi tự động trong `EmbeddingService.__init__`
- Nếu fix fail, system vẫn hoạt động bình thường (non-critical)
- Logs sẽ hiển thị status của cache fix

