# 🧠 Báo Cáo Chi Tiết: Quy Trình Học Tự Động của StillMe

## 📋 Tổng Quan

StillMe sử dụng **Unified Evolutionary Learning System** với khả năng tự học, tự đánh giá và tự tiến hóa. Hệ thống hiện tại **CHƯA CÓ** scheduler tự động, chỉ hỗ trợ chế độ thủ công thông qua CLI.

## 1️⃣ Chế Độ Tự Động (Scheduler/Trigger)

### ❌ **Trạng Thái Hiện Tại: CHƯA CÓ SCHEDULER**

**Scheduler đang dùng:** `KHÔNG CÓ` - Hệ thống chỉ hỗ trợ chế độ thủ công

**File cấu hình:** 
- `config/learning.toml` - Cấu hình cơ bản (không có scheduler)
- `policies/LEARNING_POLICY.yaml` - Chính sách học tập (không có lịch)

**Lịch mặc định:** `KHÔNG CÓ` - Cần chạy thủ công

**Trigger theo sự kiện:** `KHÔNG CÓ` - Chỉ trigger thủ công

**Giới hạn tài nguyên:** `KHÔNG CÓ` - Chưa implement

**Độ an toàn dữ liệu:** `KHÔNG CÓ` - Chưa implement idempotency

### 🔧 **Cần Implement:**

```bash
# Cần thêm vào config/learning.toml
[scheduler]
enabled = false
cron_expression = "30 2 * * *"  # 02:30 hàng ngày
timezone = "Asia/Ho_Chi_Minh"
jitter_seconds = 300  # ±5 phút
max_concurrent_sessions = 1
resource_limits:
  max_cpu_percent = 70
  max_memory_mb = 1024
  max_tokens_per_day = 10000
```

## 2️⃣ Cơ Chế Giám Sát & Báo Cáo

### 📊 **Logging**

**Định dạng:** Text format (không phải JSONL)
**Đường dẫn log:** `logs/` (chưa được tạo)
**Mức log:** INFO level
**Xoay vòng log:** Chưa implement

**File log hiện tại:**
- `stillme_core/learning/evolutionary_learning_system.py:40` - Logger setup
- `cli/evolutionary_learning.py:42-45` - CLI logging setup

### 📈 **Metrics**

**Thu thập:** 
- Accuracy, Response Time, User Satisfaction
- Knowledge Retention, Adaptation Speed
- Creativity Score, Consistency Score

**Lưu trữ:** Trong memory (deque maxlen=1000)
**File:** `stillme_core/learning/evolutionary_learning_system.py:118`

### 🚨 **Alerting**

**Hiện tại:** `KHÔNG CÓ` - Chỉ console output
**Cần implement:** Webhook, email, file sentinel

### 🔍 **Truy Vết**

**Session ID:** Có - format `training_{timestamp}`
**File:** `stillme_core/learning/evolutionary_learning_system.py:184`

## 3️⃣ Chế Độ Thủ Công (Manual)

### 🎯 **Lệnh Cơ Bản**

```bash
# Kiểm tra trạng thái
python -m cli.evolutionary_learning status

# Chạy training session
python -m cli.evolutionary_learning train --session-type daily

# Chạy self-assessment
python -m cli.evolutionary_learning assess --type full

# Trigger evolution
python -m cli.evolutionary_learning evolve --force

# Reset hệ thống
python -m cli.evolutionary_learning reset --confirm

# Export dữ liệu
python -m cli.evolutionary_learning export --output data.json
```

### 📁 **Ingest Thủ Công**

**❌ CHƯA CÓ** - Cần implement:

```bash
# Ingest thư mục tài liệu
python -m cli.evolutionary_learning ingest --path data/my_notes --type directory

# Ingest RSS/URL đơn lẻ  
python -m cli.evolutionary_learning ingest --url https://arxiv.org/list/cs.AI/rss --type rss

# Ingest experience thủ công
python -m cli.evolutionary_learning ingest --experience '{"context": "...", "action": "...", "outcome": "..."}'
```

### 🔒 **Bộ Lọc An Toàn**

**Human-in-the-loop:** `KHÔNG CÓ` - Chưa implement
**File cấu hình:** `policies/LEARNING_POLICY.yaml:27` - `require_human_approval: true` (chưa hoạt động)

## 4️⃣ Cấu Hình (Bảng Tổng Hợp)

| Khóa | Kiểu | Default | Phạm Vi | Ví Dụ |
|------|------|---------|---------|-------|
| `STILLME_LEARNING_ACTIVE` | string | `unified` | Global | `unified` |
| `STILLME_LEARNING_SCHEDULE` | string | `none` | Scheduler | `30 2 * * *` |
| `STILLME_TZ` | string | `Asia/Ho_Chi_Minh` | Global | `Asia/Ho_Chi_Minh` |
| `STILLME_TOKEN_BUDGET_DAILY` | int | `10000` | Resource | `10000` |
| `STILLME_CONCURRENCY` | int | `1` | Resource | `1` |
| `STILLME_MAX_RSS_ITEMS` | int | `20` | Content | `20` |
| `STILLME_QUALITY_THRESHOLD` | float | `0.72` | Quality | `0.72` |
| `STILLME_RISK_THRESHOLD` | float | `0.25` | Safety | `0.25` |

### 🔐 **API Keys (Cần thêm vào .env.example)**

```bash
# RSS API keys (nếu cần)
ARXIV_API_KEY=your_arxiv_key
OPENAI_API_KEY=your_openai_key
DEEPMIND_API_KEY=your_deepmind_key

# Monitoring keys
WEBHOOK_URL=your_webhook_url
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USER=your_email
EMAIL_PASS=your_password
```

## 5️⃣ Ví Dụ Cấu Hình Điển Hình

### 🌅 **Bật Auto Học Hàng Ngày 02:30**

```toml
# config/learning.toml
[scheduler]
enabled = true
cron_expression = "30 2 * * *"
timezone = "Asia/Ho_Chi_Minh"
jitter_seconds = 300
max_concurrent_sessions = 1

[resource_limits]
max_cpu_percent = 70
max_memory_mb = 1024
max_tokens_per_day = 10000
```

### ⏰ **Chạy Mỗi Giờ (Với Giới Hạn CPU)**

```toml
[scheduler]
enabled = true
cron_expression = "0 * * * *"  # Mỗi giờ
timezone = "Asia/Ho_Chi_Minh"
skip_if_cpu_high = true
cpu_threshold = 70

[resource_limits]
max_cpu_percent = 70
max_memory_mb = 512
max_tokens_per_hour = 1000
```

### 🚫 **Tắt Hoàn Toàn Auto**

```toml
[scheduler]
enabled = false
manual_only = true
```

### 📅 **Chỉ Học Cuối Tuần**

```toml
[scheduler]
enabled = true
cron_expression = "30 2 * * 0,6"  # Chủ nhật và thứ 7
timezone = "Asia/Ho_Chi_Minh"
```

## 6️⃣ Quy Trình Lỗi & Phục Hồi

### 🔄 **Retry Policy**

**❌ CHƯA CÓ** - Cần implement:

```python
# Cần thêm vào evolutionary_learning_system.py
retry_config = {
    "max_retries": 3,
    "backoff_factor": 2,
    "max_delay": 300,  # 5 phút
    "retry_on": ["ConnectionError", "TimeoutError", "RateLimitError"]
}
```

### 💾 **Backup & Rollback**

**Backup:** `KHÔNG CÓ` - Cần implement
**Rollback:** `KHÔNG CÓ` - Cần implement

**Cần thêm:**
```bash
# Backup learning data
python -m cli.evolutionary_learning backup --output backup_$(date +%Y%m%d).json

# Rollback to backup
python -m cli.evolutionary_learning rollback --from backup_20250927.json
```

### ⚠️ **Partial Failure**

**Quarantine:** `KHÔNG CÓ` - Cần implement
**Pending state:** `KHÔNG CÓ` - Cần implement

## 7️⃣ Bảo Mật & Quyền Riêng Tư

### 🗄️ **Lưu Trữ Dữ Liệu**

**Vị trí:** SQLite database (`.experience_memory.db`)
**File:** `config/learning.toml:47`

### 🗑️ **Xóa Theo Yêu Cầu**

**❌ CHƯA CÓ** - Cần implement GDPR compliance

### 🔒 **Kiểm Soát Nguồn**

**Allowlist domains:** `policies/LEARNING_POLICY.yaml:5-8`
- `arxiv.org`
- `openai.com` 
- `deepmind.com`

### 📏 **Giới Hạn Kích Cỡ**

**Max content length:** `100000` characters
**File:** `policies/LEARNING_POLICY.yaml:15`

## 8️⃣ Lệnh Mẫu (Copy-Paste Được)

### 🚀 **Bật/Tắt Auto**

```bash
# Bật auto học hàng ngày 02:30
python -m cli.evolutionary_learning schedule --enable --cron "30 2 * * *" --tz Asia/Ho_Chi_Minh

# Tắt auto
python -m cli.evolutionary_learning schedule --disable

# Kiểm tra trạng thái scheduler
python -m cli.evolutionary_learning schedule --status
```

### 📚 **Học Thủ Công**

```bash
# Học từ thư mục
python -m cli.evolutionary_learning ingest --path data/my_notes --type directory

# Học từ RSS
python -m cli.evolutionary_learning ingest --url https://arxiv.org/list/cs.AI/rss --type rss

# Học từ experience
python -m cli.evolutionary_learning ingest --experience '{"context": "user_question", "action": "response", "outcome": "satisfied"}'
```

### 📊 **Kiểm Tra & Báo Cáo**

```bash
# Kiểm tra trạng thái phiên gần nhất
python -m cli.evolutionary_learning status --last

# Xem log phiên theo ID
python -m cli.evolutionary_learning logs --session-id training_1695801600

# Xuất báo cáo nhanh
python -m cli.evolutionary_learning export --output daily_report.json
```

## 9️⃣ Artifacts Cần Xuất

### 📄 **Tài Liệu**

- ✅ `docs/LEARNING_AUTOMATION.md` - Tài liệu này
- ❌ `artifacts/learning/automation_status.json` - Cần tạo
- ❌ `artifacts/metrics/learning_summary.csv` - Cần tạo

### 🔧 **Cấu Hình**

- ❌ Cập nhật `.env.example` - Cần thêm API keys
- ❌ Cập nhật `config/learning.toml` - Cần thêm scheduler config

## ✅ Tiêu Chí Chấp Nhận

### ❌ **Chưa Đạt:**

1. **Scheduler tự động:** CHƯA CÓ
2. **Resource limits:** CHƯA CÓ  
3. **Idempotency:** CHƯA CÓ
4. **Human-in-the-loop:** CHƯA CÓ
5. **Retry policy:** CHƯA CÓ
6. **Backup/Rollback:** CHƯA CÓ
7. **Alerting:** CHƯA CÓ
8. **GDPR compliance:** CHƯA CÓ

### ✅ **Đã Có:**

1. **CLI commands:** Có đầy đủ
2. **Session tracking:** Có Session ID
3. **Metrics collection:** Có basic metrics
4. **Evolution stages:** Có 4 giai đoạn
5. **Self-assessment:** Có assessment system
6. **Export functionality:** Có export data

## 🚨 **Kết Luận**

StillMe hiện tại **CHƯA CÓ** hệ thống học tự động hoàn chỉnh. Chỉ có:
- ✅ CLI thủ công
- ✅ Basic metrics
- ✅ Session tracking
- ❌ Scheduler
- ❌ Resource management
- ❌ Error handling
- ❌ Monitoring/Alerting

**Cần implement ngay:** Scheduler, Resource limits, Error handling, Monitoring system.
