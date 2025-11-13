# 📚 Vector DB Stats - Giải Thích Chi Tiết

## Tổng Quan

Vector DB Stats hiển thị số lượng documents trong ChromaDB Vector Database của StillMe. Đây là cơ sở dữ liệu vector lưu trữ kiến thức và lịch sử hội thoại.

## Các Con Số

### 1. Total Documents (Tổng số documents)
- **Công thức**: `Total Documents = Knowledge Docs + Conversation Docs`
- **Ví dụ**: 56 = 42 + 14
- **Ý nghĩa**: Tổng số documents trong cả 2 collections của ChromaDB

### 2. Knowledge Docs (Documents kiến thức)
- **Collection**: `stillme_knowledge`
- **Nguồn**:
  - ✅ Tự động học từ RSS feeds, arXiv, CrossRef, Wikipedia (mỗi 4 giờ)
  - ✅ Thêm thủ công qua API `/api/rag/add_knowledge` hoặc Dashboard
  - ✅ Foundational knowledge về StillMe (cơ chế RAG, Validator Chain, etc.)
- **Mục đích**: Dùng để trả lời câu hỏi thông qua semantic search
- **Metadata**: Chứa `source`, `type`, `timestamp`, `title`, `importance_score`

### 3. Conversation Docs (Documents hội thoại)
- **Collection**: `stillme_conversations`
- **Nguồn**:
  - ✅ Tự động lưu sau mỗi cuộc chat với user
  - ✅ Format: `"Q: [câu hỏi]\nA: [câu trả lời]"`
- **Mục đích**:
  - Cung cấp context từ các cuộc hội thoại trước
  - Hỗ trợ multi-turn conversation
  - Cải thiện tính liên tục trong hội thoại
- **Metadata**: Chứa `source`, `user_id`, `timestamp`, `accuracy_score`

## Cơ Chế Reset/Cleanup

### ⚠️ Vector DB CÓ THỂ BỊ RESET TRONG CÁC TRƯỜNG HỢP:

1. **Schema Mismatch (Tự động reset)**
   - Khi ChromaDB schema thay đổi và không tương thích với dữ liệu cũ
   - Dashboard service tự động reset với `reset_on_error=True`
   - Backend service cố gắng preserve data, nhưng nếu lỗi nặng sẽ reset

2. **FORCE_DB_RESET_ON_STARTUP=true**
   - Environment variable để force reset database khi khởi động
   - **⚠️ CẢNH BÁO**: Sẽ xóa TẤT CẢ dữ liệu trong Vector DB!
   - Trong production (ENV=production), biến này bị override về `false` để an toàn

3. **Manual Reset**
   - API endpoint: `POST /api/rag/reset-database` (yêu cầu API key)
   - Xóa toàn bộ `data/vector_db` directory và tạo lại collections

4. **Railway Deployment**
   - Khi deploy mới hoặc restart service, nếu có schema mismatch, database có thể bị reset
   - Dashboard service luôn dùng `reset_on_error=True` để tự động xử lý

### 🔄 Tại Sao Số Documents Có Thể Biến Mất?

1. **Service Restart với Schema Mismatch**
   - Khi backend restart và phát hiện schema không tương thích
   - Hệ thống tự động reset database để tránh crash
   - **Giải pháp**: Kiểm tra logs để xem có schema mismatch không

2. **Railway Ephemeral Storage**
   - Railway có thể reset storage khi service restart hoặc deploy
   - **Giải pháp**: Sử dụng persistent volume hoặc backup database

3. **Manual Reset**
   - Ai đó gọi API reset hoặc xóa thư mục `data/vector_db`
   - **Giải pháp**: Kiểm tra logs và API access logs

### 💾 Retention Policy

**LƯU Ý**: ChromaDB Vector Database **KHÔNG CÓ** automatic retention policy!

- Documents sẽ **KHÔNG TỰ ĐỘNG XÓA** theo thời gian
- Documents chỉ bị xóa khi:
  - Manual reset (API hoặc xóa directory)
  - Schema mismatch reset
  - Service restart với `FORCE_DB_RESET_ON_STARTUP=true`

**Continuum Memory System** (L0-L3 tiers) có retention policy riêng, nhưng đó là cho SQLite database, không phải ChromaDB.

## Xem Chi Tiết Documents

### API Endpoint

```bash
GET /api/rag/list-documents?collection=all&limit=100&offset=0
```

**Yêu cầu**: API Key (X-API-Key header)

**Parameters**:
- `collection`: `"knowledge"`, `"conversation"`, hoặc `"all"` (default: `"all"`)
- `limit`: Số documents tối đa (default: 100, max: 1000)
- `offset`: Số documents bỏ qua (default: 0)

**Response**:
```json
{
  "knowledge_documents": [
    {
      "id": "knowledge_abc123",
      "content": "StillMe is a continuously self-learning AI...",
      "content_length": 1234,
      "metadata": {
        "source": "rss",
        "type": "knowledge",
        "timestamp": "2025-11-13T04:48:10",
        "title": "StillMe Architecture"
      }
    }
  ],
  "conversation_documents": [...],
  "total_knowledge": 49,
  "total_conversation": 14
}
```

### Script Command Line

```bash
# Xem tất cả documents
python scripts/view_vector_db_documents.py

# Với API key
STILLME_API_KEY=your-key python scripts/view_vector_db_documents.py

# Với custom API base
STILLME_API_BASE=https://stillme-backend-production.up.railway.app python scripts/view_vector_db_documents.py
```

## Run Now Button - Giải Thích

### Tại Sao Chỉ Thấy "Running" Mà Không Có Feedback?

1. **Non-Blocking Design**
   - `Run Now` trả về `202 Accepted` ngay lập tức
   - Learning cycle chạy trong background (2-5 phút)
   - Dashboard không block để chờ kết quả

2. **Progress Tracking**
   - Dashboard tự động refresh mỗi 3 giây để check scheduler status
   - Khi cycle hoàn thành, `cycle_count` sẽ tăng
   - Vector DB Stats sẽ tự động update

3. **Timeout Handling**
   - Nếu request timeout (60s), dashboard vẫn track progress
   - Sử dụng `cycle_count` để detect khi cycle hoàn thành
   - Hiển thị message: "Learning cycle started! Running in background..."

### Cải Thiện Feedback (Đã Fix)

- ✅ Hiển thị success message ngay khi start
- ✅ Auto-refresh để check progress
- ✅ Hiển thị Vector DB Stats update khi cycle hoàn thành
- ✅ Clear message về thời gian chờ (2-5 phút)

## Best Practices

1. **Backup Database**
   - Nếu cần preserve data, backup `data/vector_db` directory trước khi deploy
   - Hoặc export documents qua API `/api/rag/list-documents`

2. **Monitor Logs**
   - Kiểm tra logs khi thấy documents biến mất
   - Tìm keywords: "schema mismatch", "reset", "FORCE_DB_RESET"

3. **Avoid Force Reset**
   - Không set `FORCE_DB_RESET_ON_STARTUP=true` trong production
   - Chỉ dùng khi thực sự cần reset database

4. **Check Scheduler Status**
   - Sau khi bấm "Run Now", check scheduler status để xem progress
   - Vector DB Stats sẽ update khi cycle hoàn thành

## Troubleshooting

### Documents Biến Mất

1. **Check Logs**: Tìm "reset", "schema mismatch", "FORCE_DB_RESET"
2. **Check Environment**: Xem có `FORCE_DB_RESET_ON_STARTUP=true` không
3. **Check Railway**: Xem có restart/deploy mới không
4. **Check API Access**: Xem có ai gọi `/api/rag/reset-database` không

### Run Now Không Có Feedback

1. **Check Backend Logs**: Xem learning cycle có chạy không
2. **Wait 2-5 Minutes**: Learning cycle cần thời gian
3. **Refresh Dashboard**: Vector DB Stats sẽ update khi cycle hoàn thành
4. **Check Scheduler Status**: Xem `cycle_count` có tăng không

### Vector DB Stats Không Update

1. **Wait for Cycle Complete**: Stats chỉ update sau khi cycle hoàn thành
2. **Check Backend**: Xem backend có đang chạy không
3. **Check API**: Test `/api/rag/stats` trực tiếp
4. **Refresh Dashboard**: Có thể cần manual refresh

