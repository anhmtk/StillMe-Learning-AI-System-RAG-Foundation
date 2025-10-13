# Attic Wave-01 - Legacy Files Cleanup

## Phạm vi Wave-01
Di chuyển 7 file SAFE_MOVE vào `_attic/legacy/`:
- `api_provider_manager_old.py`
- `backup_legacy/` (thư mục)
- `content_integrity_filter_old.py` 
- `layered_memory_v1_old.py`

## Lý do di chuyển
- **Pattern matching**: Files có pattern `*_old.py`, `backup_*`, `*_legacy`
- **Zero runtime references**: Không được import trong runtime
- **Zero test references**: Không có test nào reference đến
- **Reliability Auditor confirmed**: Được xác nhận là SAFE_MOVE

## Cách khôi phục
```bash
# Khôi phục từng file
git mv _attic/legacy/api_provider_manager_old.py stillme_core/modules/api_provider_manager_old.py
git mv _attic/legacy/backup_legacy stillme_core/modules/backup_legacy
git mv _attic/legacy/content_integrity_filter_old.py stillme_core/modules/content_integrity_filter_old.py
git mv _attic/legacy/layered_memory_v1_old.py stillme_core/modules/layered_memory_v1_old.py

# Hoặc khôi phục toàn bộ wave-01
git checkout cleanup/attic-wave-01~1 -- stillme_core/modules/
```

## Lưu ý
- Files này được di chuyển, KHÔNG xóa vĩnh viễn
- Có thể rollback bất kỳ lúc nào
- AgentDev và core modules không bị ảnh hưởng
- Đã chạy canary test để đảm bảo không phá vỡ chức năng

---
*Created by Cleanup Captain - Wave-01*
