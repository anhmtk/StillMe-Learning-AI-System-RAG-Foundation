# 📋 Test Suite Guide

## Overview

StillMe có 2 scripts chính cho testing:

1. **`scripts/generate_test_suite.py`** - Tạo danh sách câu hỏi test (NHANH - chỉ tạo file JSON)
2. **`scripts/run_comprehensive_tests.py`** - Chạy test thực sự với StillMe (CHẬM - gọi API cho mỗi câu hỏi)

## 1. Generate Test Suite (NHANH)

### Mục đích:
Tạo file JSON chứa hàng ngàn câu hỏi đa dạng để test StillMe.

### Chạy:
```bash
python scripts/generate_test_suite.py
```

### Kết quả:
- **File**: `tests/data/comprehensive_test_suite.json`
- **Nội dung**: Danh sách câu hỏi với metadata (category, difficulty, language, sensitive)
- **Thời gian**: Rất nhanh (< 1 giây) vì chỉ tạo file JSON, không gọi API

### Xem kết quả:
```bash
# Xem file JSON
cat tests/data/comprehensive_test_suite.json

# Hoặc dùng Python
python -c "import json; d=json.load(open('tests/data/comprehensive_test_suite.json', 'r', encoding='utf-8')); print(f'Total: {d[\"total_questions\"]} questions'); print(f'Categories: {d[\"categories\"]}')"
```

### Cấu trúc file:
```json
{
  "version": "1.0",
  "total_questions": 202,
  "categories": ["philosophy", "ethics", "politics", ...],
  "languages": ["en", "vi"],
  "difficulties": ["easy", "medium", "hard"],
  "questions": [
    {
      "id": "test_000001",
      "question": "What is the meaning of life?",
      "category": "philosophy",
      "difficulty": "easy",
      "language": "en",
      "sensitive": false
    },
    ...
  ]
}
```

## 2. Run Comprehensive Tests (CHẬM)

### Mục đích:
Chạy test thực sự - gửi từng câu hỏi đến StillMe API và thu thập responses.

### Chạy:
```bash
# Đảm bảo backend đang chạy
# http://localhost:8000

python scripts/run_comprehensive_tests.py
```

### Kết quả:
- **File**: `tests/results/comprehensive_test_YYYYMMDD_HHMMSS.json`
- **Nội dung**: Responses từ StillMe cho mỗi câu hỏi, timing, confidence scores
- **Thời gian**: CHẬM - phụ thuộc vào số lượng câu hỏi và API latency
  - 202 questions ≈ 10-30 phút (tùy API speed)
  - 5000 questions ≈ vài giờ

### Xem kết quả:
```bash
# List các file results
ls tests/results/

# Xem file mới nhất
python -c "import json, glob; files=sorted(glob.glob('tests/results/comprehensive_test_*.json')); d=json.load(open(files[-1],'r',encoding='utf-8')); print(f'Total: {len(d)} results'); print(f'Success: {sum(1 for r in d if r.get(\"status\")==\"success\")}'); print(f'Errors: {sum(1 for r in d if r.get(\"status\")==\"error\")}')"
```

### Cấu trúc kết quả:
```json
[
  {
    "question_id": "test_000001",
    "question": "What is the meaning of life?",
    "category": "philosophy",
    "difficulty": "easy",
    "language": "en",
    "response": "StillMe's response here...",
    "confidence_score": 0.85,
    "latency": 1.23,
    "status": "success",
    "timestamp": "2025-01-11T10:00:00"
  },
  ...
]
```

## Workflow Khuyến Nghị

### Bước 1: Generate Test Suite (NHANH)
```bash
python scripts/generate_test_suite.py
```
✅ Tạo file `tests/data/comprehensive_test_suite.json` với 202+ questions

### Bước 2: Xem Test Suite
```bash
# Xem tổng quan
python -c "import json; d=json.load(open('tests/data/comprehensive_test_suite.json','r',encoding='utf-8')); print(f'Total: {d[\"total_questions\"]} questions'); print(f'Categories: {d[\"categories\"]}'); print(f'Languages: {d[\"languages\"]}')"

# Xem sample questions
python -c "import json; d=json.load(open('tests/data/comprehensive_test_suite.json','r',encoding='utf-8')); [print(f'{i+1}. [{q[\"category\"]}] {q[\"question\"][:80]}...') for i,q in enumerate(d['questions'][:10])]"
```

### Bước 3: Run Tests (CHẬM - cần backend chạy)
```bash
# Đảm bảo backend đang chạy
# http://localhost:8000

# Chạy test với tất cả questions
python scripts/run_comprehensive_tests.py

# Hoặc test với số lượng giới hạn (để test nhanh)
python -c "from scripts.run_comprehensive_tests import *; import asyncio; d=json.load(open('tests/data/comprehensive_test_suite.json','r',encoding='utf-8')); asyncio.run(run_tests(d['questions'][:10], max_concurrent=5, max_questions=10))"
```

### Bước 4: Analyze Results
```bash
# Xem stats
python -c "import json, glob; files=sorted(glob.glob('tests/results/comprehensive_test_*.json')); d=json.load(open(files[-1],'r',encoding='utf-8')); success=sum(1 for r in d if r.get('status')=='success'); print(f'Success: {success}/{len(d)} ({success/len(d)*100:.1f}%)'); print(f'Avg latency: {sum(r.get(\"latency\",0) for r in d if r.get(\"status\")==\"success\")/success:.2f}s' if success>0 else 'N/A')"
```

## Tùy Chỉnh

### Thêm nhiều questions hơn:
Sửa `scripts/generate_test_suite.py`:
- Thêm templates vào `QUESTION_TEMPLATES`
- Tăng `num_questions` trong `generate_questions()`

### Test với production API:
Sửa `scripts/run_comprehensive_tests.py`:
```python
API_BASE = "https://stillme-backend-production.up.railway.app"
```

### Test với số lượng giới hạn:
```python
# Test 50 questions đầu tiên
python -c "from scripts.run_comprehensive_tests import *; import asyncio; d=json.load(open('tests/data/comprehensive_test_suite.json','r',encoding='utf-8')); asyncio.run(run_tests(d['questions'][:50], max_concurrent=10, max_questions=50))"
```

## Troubleshooting

### Script chạy quá nhanh?
✅ **Bình thường!** `generate_test_suite.py` chỉ tạo file JSON, không gọi API.

### Muốn test thực sự?
✅ Dùng `run_comprehensive_tests.py` - script này sẽ gọi API cho mỗi câu hỏi.

### Backend không chạy?
✅ Đảm bảo backend đang chạy tại `http://localhost:8000` trước khi chạy `run_comprehensive_tests.py`.

### Kết quả ở đâu?
- **Test suite (questions)**: `tests/data/comprehensive_test_suite.json`
- **Test results (responses)**: `tests/results/comprehensive_test_*.json`

