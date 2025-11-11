# 🧠 Memory Health & Continuum Memory - Giải Thích

## 📋 Tổng Quan

**Memory Health** là dashboard hiển thị trạng thái của **Continuum Memory System** - hệ thống quản lý bộ nhớ phân tầng (tiered memory) của StillMe.

---

## 🎯 Continuum Memory là gì?

**Continuum Memory** là hệ thống quản lý bộ nhớ phân tầng (L0, L1, L2, L3) giúp StillMe:
- **Tối ưu chi phí embedding**: Chỉ update knowledge ở các tier cần thiết
- **Quản lý vòng đời knowledge**: Tự động promote/demote knowledge dựa trên surprise score
- **Theo dõi forgetting**: Đo lường sự suy giảm recall khi knowledge bị "quên"

### Các Tier (Tầng):

| Tier | Tên | Mô Tả | TTL | Update Frequency |
|------|-----|-------|-----|------------------|
| **L0** | Session/Cache | Knowledge mới fetch, hot | 2 ngày | Mỗi cycle (1) |
| **L1** | Working KB | Knowledge đã validate, có usage tracking | 21 ngày | Mỗi 10 cycles |
| **L2** | Canonical KB | Knowledge chuẩn, confidence cao | 180 ngày | Mỗi 100 cycles |
| **L3** | Core/Policy | Rules và standards bất biến | Vĩnh viễn | Mỗi 1000 cycles |

---

## 🔧 Cách Hoạt Động

### 1. **Surprise Score** (Điểm Bất Ngờ)

Knowledge được route vào tier dựa trên **surprise score**:

```
surprise_score = 0.3 × rarity_score + 
                0.3 × novelty_score + 
                0.2 × retrieval_frequency + 
                0.2 × validator_overlap
```

**Routing Rules:**
- **L3** (Core): `surprise_score >= 0.8` → Knowledge rất quan trọng, cần lưu lâu dài
- **L2** (Canonical): `0.6 <= surprise_score < 0.8` → Knowledge domain quan trọng
- **L1** (Working): `0.4 <= surprise_score < 0.6` → Knowledge in-context learning
- **L0** (Session): `surprise_score < 0.4` → Knowledge ngắn hạn, task-specific

### 2. **Promotion/Demotion**

Knowledge tự động di chuyển giữa các tier:

**Promotion (Nâng cấp):**
- L0 → L1: `surprise_score >= 0.65` AND `retrieval_count_7d` tăng
- L1 → L2: `surprise_score >= 0.65` AND `validator_overlap >= 0.8`

**Demotion (Hạ cấp):**
- L2 → L1: `retrieval_count_7d == 0` OR `validator_overlap < 0.3`
- L0: Expire sau `retention_days` (mặc định: 2 ngày)

### 3. **Nested Learning (Update Frequency)**

Mỗi tier có tần suất update khác nhau để **giảm chi phí embedding**:

- **L0**: Update mỗi cycle (1) → Knowledge mới cần update ngay
- **L1**: Update mỗi 10 cycles → Knowledge ổn định hơn, update ít hơn
- **L2**: Update mỗi 100 cycles → Knowledge chuẩn, update rất ít
- **L3**: Update mỗi 1000 cycles → Knowledge core, update cực ít

**Cost Reduction**: Bằng cách skip update cho L1/L2/L3, StillMe giảm **30-50% chi phí embedding**.

---

## 📊 Memory Health Dashboard Hiển Thị Gì?

### 1. **Tier Distribution**
- Số lượng knowledge items trong mỗi tier (L0, L1, L2, L3)
- Pie chart và bar chart

### 2. **Promotion & Demotion Metrics**
- Số lượng knowledge được promote/demote trong 7 ngày qua
- Trend chart theo thời gian

### 3. **Audit Log**
- Lịch sử tất cả promotion/demotion events
- Bao gồm: `item_id`, `from_tier`, `to_tier`, `reason`, `surprise_score`, `timestamp`

### 4. **Forgetting Trends**
- **Recall@k Degradation**: Đo lường sự suy giảm recall khi knowledge bị "quên"
- **Forgetting Delta**: `Recall Before - Recall After`
- Warning threshold: `Δ > 0.1` → Cần chú ý

---

## ❓ Tại Sao Hiển Thị "Disabled"?

**Vấn đề**: Dashboard hiển thị "Continuum Memory is disabled" mặc dù `ENABLE_CONTINUUM_MEMORY=true` trong backend.

**Nguyên nhân**: 
- Dashboard `dashboard_memory_health.py` trước đây check một **checkbox local** trong sidebar (không liên quan đến backend)
- Đã fix: Dashboard giờ check backend status qua API `/api/learning/nested-learning/metrics`

**Cách kiểm tra**:
1. Backend environment variable: `ENABLE_CONTINUUM_MEMORY=true`
2. Restart backend service
3. Check API: `GET /api/learning/nested-learning/metrics` → `enabled: true`
4. Dashboard sẽ tự động hiển thị metrics

---

## 💬 StillMe Có Học Từ Chat Không?

### **Câu Trả Lời Ngắn**: **KHÔNG trực tiếp**, nhưng **CÓ gián tiếp**.

### **Chi Tiết**:

#### ❌ **KHÔNG Học Trực Từ Chat Messages**

StillMe **KHÔNG** tự động lưu chat messages vào ChromaDB để học. Lý do:
- Chat messages có thể chứa thông tin không chính xác
- Cần validation và curation trước khi học
- Tránh "hallucination loop" (học từ câu trả lời sai)

#### ✅ **CÓ Học Gián Tiếp Qua Learning Cycles**

StillMe học từ:
1. **RSS Feeds**: Tự động fetch mỗi 4 giờ
2. **arXiv**: Research papers
3. **CrossRef**: Academic publications
4. **Wikipedia**: General knowledge

**Quy trình học:**
```
Learning Cycle (mỗi 4 giờ)
  ↓
Fetch RSS/arXiv/CrossRef/Wikipedia
  ↓
Pre-filter (quality check)
  ↓
Embedding (all-MiniLM-L6-v2)
  ↓
Store vào ChromaDB
  ↓
Continuum Memory routing (L0/L1/L2/L3)
```

#### 🔄 **Chat → Learning (Gián Tiếp)**

Khi bạn chat với StillMe:
1. StillMe **retrieve** knowledge từ ChromaDB (đã học từ learning cycles)
2. StillMe **generate** response dựa trên retrieved context
3. StillMe **KHÔNG** lưu chat message vào ChromaDB

**Nhưng:**
- Chat history được lưu vào **SQLite** (`chat_history.db`) - chỉ để hiển thị, không để học
- Learning suggestions có thể được generate từ chat (ví dụ: "StillMe should learn about X")
- Self-diagnosis có thể identify knowledge gaps từ chat patterns

---

## 🎯 Tóm Tắt

### **Memory Health**:
- Dashboard hiển thị trạng thái Continuum Memory System
- Hiển thị tier distribution, promotion/demotion, forgetting trends
- Giúp monitor và optimize memory management

### **Continuum Memory**:
- Hệ thống quản lý bộ nhớ phân tầng (L0-L3)
- Tối ưu chi phí embedding (30-50% reduction)
- Tự động promote/demote knowledge dựa trên surprise score

### **Learning từ Chat**:
- **KHÔNG** học trực tiếp từ chat messages
- **CÓ** học từ learning cycles (RSS, arXiv, CrossRef, Wikipedia)
- Chat chỉ để retrieve và generate responses

---

## 🔧 Troubleshooting

**Nếu Memory Health hiển thị "disabled":**

1. Check backend environment variable:
   ```bash
   ENABLE_CONTINUUM_MEMORY=true
   ```

2. Restart backend service

3. Check API:
   ```bash
   curl https://your-backend-url/api/learning/nested-learning/metrics
   ```
   Response phải có `"enabled": true`

4. Refresh dashboard

5. Nếu vẫn disabled, check backend logs:
   ```
   Continuum Memory is disabled (ENABLE_CONTINUUM_MEMORY=false)
   ```

---

## 📚 Tài Liệu Tham Khảo

- `backend/learning/continuum_memory.py` - Continuum Memory implementation
- `backend/api/routers/learning_router.py` - Nested Learning API endpoints
- `dashboard_memory_health.py` - Memory Health dashboard page

