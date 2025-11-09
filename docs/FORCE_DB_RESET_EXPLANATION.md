# Giải thích về FORCE_DB_RESET_ON_STARTUP

## 🔍 FORCE_DB_RESET_ON_STARTUP làm gì?

`FORCE_DB_RESET_ON_STARTUP=true` **CHỈ reset ChromaDB** (vector database), **KHÔNG xóa toàn bộ dữ liệu đã học**.

## 📊 Dữ liệu được lưu ở đâu?

### 1. **ChromaDB** (`data/vector_db/`) - Vector Embeddings
- **Mục đích**: Lưu vector embeddings cho semantic search
- **Bị reset khi**: `FORCE_DB_RESET_ON_STARTUP=true`
- **Ảnh hưởng**: Mất vector embeddings, cần re-embed lại

### 2. **SQLite Databases** - Dữ liệu đã học (KHÔNG bị reset)
- `data/knowledge_retention.db` - Knowledge items, learning sessions
- `data/continuum_memory.db` - Continuum Memory tiers
- `data/rss_fetch_history.db` - RSS fetch history
- `data/accuracy_scores.db` - Accuracy scores
- **KHÔNG bị ảnh hưởng** bởi `FORCE_DB_RESET_ON_STARTUP`

### 3. **JSON Files** - Knowledge Base (KHÔNG bị reset)
- `data/consolidated_knowledge.json`
- `data/knowledge_base.json`
- `data/knowledge_index.json`
- **KHÔNG bị ảnh hưởng** bởi `FORCE_DB_RESET_ON_STARTUP`

## ⚠️ Khi nào cần reset?

**Chỉ reset khi:**
- ChromaDB schema mismatch (lỗi `no such column: collections.topic`)
- ChromaDB version upgrade gây incompatibility
- Database corruption

## ✅ Sau khi reset, dữ liệu sẽ như thế nào?

1. **Vector embeddings bị mất** → Cần re-embed lại
2. **Knowledge items vẫn còn** trong SQLite databases
3. **Knowledge base JSON vẫn còn**
4. **Hệ thống sẽ tự động re-embed** khi:
   - Learning cycle chạy (mỗi 4 giờ)
   - User thêm knowledge mới
   - System rebuild từ knowledge base

## 💡 Kết luận

**FORCE_DB_RESET_ON_STARTUP=true KHÔNG xóa toàn bộ dữ liệu đã học!**

- ✅ Knowledge items vẫn còn trong SQLite
- ✅ Knowledge base JSON vẫn còn
- ✅ Chỉ mất vector embeddings (có thể rebuild)
- ✅ Hệ thống sẽ tự động re-embed khi cần

**Tuy nhiên**, nếu `ENV=production`, code sẽ **force disable** `FORCE_DB_RESET_ON_STARTUP` để an toàn.

