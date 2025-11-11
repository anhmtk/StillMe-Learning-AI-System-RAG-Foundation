# 🧪 StillMe Chat Test Suite - Hướng Dẫn Sử Dụng

## 📍 Kết Quả Test Ở Đâu?

### ✅ **Terminal (Console)**
- Khi chạy test, kết quả sẽ hiển thị **ngay trong terminal**
- Summary metrics (confidence, validation rate, domain breakdown)
- Progress bar và thông báo từng câu hỏi

### ✅ **CSV File**
- Kết quả chi tiết được lưu vào `tests/results/test_YYYYMMDD_HHMMSS.csv`
- Có thể mở bằng Excel, Google Sheets, hoặc bất kỳ CSV viewer nào
- Chứa đầy đủ thông tin: question, confidence_score, validation_passed, latency, error, etc.

### ❌ **KHÔNG ảnh hưởng đến Dashboard**
- Test suite chạy **hoàn toàn độc lập** với dashboard
- **KHÔNG cần** tắt dashboard hay chat
- **KHÔNG mất** lịch sử chat
- **KHÔNG mất** dữ liệu chat
- Test chỉ gọi API backend, không touch database hay session

---

## 🚀 Cách Chạy Test

### 1. **Basic Test (Phase 1)**
```bash
python tests/stillme_chat_test_suite.py --api-base http://localhost:8000
```

### 2. **Với Domain Coverage Analysis (Phase 2)**
```bash
python tests/stillme_chat_test_suite.py --use-coverage
```

### 3. **Với Question Generation từ Gaps (Phase 3)**
```bash
python tests/stillme_chat_test_suite.py --use-coverage --generate-from-gaps
```

### 4. **Custom Options**
```bash
python tests/stillme_chat_test_suite.py \
  --api-base http://localhost:8000 \
  --questions 30 \
  --use-coverage \
  --generate-from-gaps \
  --max-generated 10 \
  --delay 2.0 \
  --output my_test_run
```

---

## 📊 Xem Kết Quả

### **Option 1: Xem ngay trong Terminal**
Kết quả sẽ hiển thị ngay sau khi test xong:
```
============================================================
TEST SUITE SUMMARY
============================================================
Total Questions: 20
Valid Results: 18
Error Rate: 10.0%

Overall Metrics:
  Average Confidence: 0.75
  Min Confidence: 0.45
  Max Confidence: 0.95
  Validation Pass Rate: 85.0%
  Average Response Length: 1234 chars
  Average Latency: 2.34s

Domain Breakdown:
  math:
    Questions: 3
    Avg Confidence: 0.82
    Validation Pass Rate: 100.0%
  ...
============================================================
```

### **Option 2: Xem bằng Script Helper**
```bash
# Xem test run mới nhất
python tests/view_results.py

# Xem test run cụ thể
python tests/view_results.py --file test_20250111_123456.csv

# Xem chi tiết từng câu hỏi
python tests/view_results.py --detailed

# Liệt kê tất cả test runs
python tests/view_results.py --list
```

### **Option 3: Mở CSV File Trực Tiếp**
```bash
# Windows
start tests/results/test_20250111_123456.csv

# Mac
open tests/results/test_20250111_123456.csv

# Linux
xdg-open tests/results/test_20250111_123456.csv
```

---

## 🔒 Bảo Mật & An Toàn

### ✅ **Test Suite KHÔNG ảnh hưởng:**
- ❌ Dashboard session
- ❌ Chat history
- ❌ Database data
- ❌ User sessions
- ❌ Learning data

### ✅ **Test Suite CHỈ:**
- ✅ Gọi API `/api/chat/smart_router` (read-only từ user perspective)
- ✅ Lưu kết quả vào CSV file
- ✅ Hiển thị metrics trong terminal

### ⚠️ **Lưu Ý:**
- Test suite sẽ tạo **temporary API calls** - có thể thấy trong backend logs
- Nếu backend đang chạy, test sẽ gọi API thật → có thể tốn API credits (nếu dùng paid APIs)
- Để test an toàn hơn, có thể chạy với `--delay` lớn hơn để tránh rate limiting

---

## 📁 Cấu Trúc Files

```
tests/
├── stillme_chat_test_suite.py    # Main test suite script
├── view_results.py               # Helper script để xem kết quả
├── data/
│   ├── question_pool.json       # Question pool (100-200 questions)
│   └── README.md                 # Hướng dẫn question pool
└── results/
    ├── test_20250111_123456.csv # Test results (CSV format)
    ├── test_20250111_140000.csv
    └── ...
```

---

## 🎯 Ví Dụ Output

### **Terminal Output:**
```
Phase 1: Selecting 20 questions from pool...
Selected 20 questions

Executing 20 questions...
[1/20] Testing: baseline_001 (math)
[2/20] Testing: rot_001 (ethics)
...

============================================================
TEST SUITE SUMMARY
============================================================
Total Questions: 20
Valid Results: 18
Error Rate: 10.0%

Overall Metrics:
  Average Confidence: 0.75
  Min Confidence: 0.45
  Max Confidence: 0.95
  Validation Pass Rate: 85.0%
  Average Response Length: 1234 chars
  Average Latency: 2.34s

Domain Breakdown:
  math:
    Questions: 3
    Avg Confidence: 0.82
    Validation Pass Rate: 100.0%
  ethics:
    Questions: 2
    Avg Confidence: 0.68
    Validation Pass Rate: 75.0%
============================================================

Results saved to: tests/results/test_20250111_123456.csv
```

### **CSV File Structure:**
```csv
test_run_id,question_id,question,domain,difficulty,language,confidence_score,validation_passed,response_length,context_docs_count,latency,status_code,error,timestamp
test_20250111_123456,baseline_001,"Nếu một tập hợp có vô hạn phần tử...",math,hard,vi,0.82,True,1234,3,2.34,200,,2025-01-11T12:34:56
...
```

---

## 💡 Tips

1. **Chạy test khi backend đang chạy**: Test cần backend API để hoạt động
2. **Xem kết quả ngay**: Summary hiển thị ngay trong terminal
3. **Lưu trữ lâu dài**: CSV files có thể lưu trữ và so sánh theo thời gian
4. **So sánh kết quả**: Có thể so sánh CSV files từ các test runs khác nhau
5. **CI/CD Integration**: Test suite có thể chạy trong GitHub Actions (xem `.github/workflows/test-suite.yml`)

---

## ❓ FAQ

**Q: Test có làm mất dữ liệu chat không?**  
A: **KHÔNG**. Test chỉ gọi API, không touch database hay session.

**Q: Có cần tắt dashboard không?**  
A: **KHÔNG**. Test chạy độc lập, không ảnh hưởng dashboard.

**Q: Kết quả ở đâu?**  
A: Terminal (summary) + CSV file trong `tests/results/`.

**Q: Có thể xem lại kết quả sau không?**  
A: **CÓ**. Dùng `python tests/view_results.py` hoặc mở CSV file trực tiếp.

**Q: Test có tốn API credits không?**  
A: **CÓ** (nếu dùng paid APIs). Test gọi API thật, nên sẽ tốn credits. Có thể giảm số câu hỏi với `--questions 10`.

---

## 📚 Tham Khảo

- **Architecture Design**: [`docs/DYNAMIC_TEST_SUITE_DESIGN.md`](../docs/DYNAMIC_TEST_SUITE_DESIGN.md)
- **Question Pool**: [`tests/data/question_pool.json`](data/question_pool.json)
- **CI/CD Workflow**: [`.github/workflows/test-suite.yml`](../.github/workflows/test-suite.yml)

