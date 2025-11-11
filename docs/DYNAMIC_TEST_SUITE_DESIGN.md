# 🎯 Dynamic Test Suite Architecture Design / Thiết Kế Kiến Trúc Dynamic Test Suite

## Overview / Tổng Quan

Dynamic Test Suite for StillMe is designed to:
- **Avoid overfitting**: No fixed 20 questions
- **Adapt with knowledge**: Test suite automatically adapts to StillMe's learned knowledge
- **Diverse coverage**: Ensures testing across all domains
- **Fresh questions**: Automatically generates questions from new knowledge

Dynamic Test Suite cho StillMe được thiết kế để:
- **Tránh overfitting**: Không test cố định 20 câu
- **Adapt với knowledge**: Test suite tự động adapt với knowledge StillMe đã học
- **Coverage đa dạng**: Đảm bảo test tất cả domains
- **Fresh questions**: Tự động generate questions từ knowledge mới

---

## 🏗️ Overall Architecture / Kiến Trúc Tổng Thể

```
┌─────────────────────────────────────────────────────────┐
│              Dynamic Test Suite System                  │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Question Pool│   │ Domain       │   │ Question     │
│ Manager      │   │ Coverage     │   │ Generator    │
│              │   │ Analyzer     │   │              │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   Test Executor       │
                │   (API Calls)         │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   Metrics Collector   │
                │   (CSV/JSON Logs)     │
                └───────────────────────┘
```

---

## 📦 Component 1: Question Pool Manager / Quản Lý Question Pool

### Functionality / Chức Năng:
- Manages pool of 100-200 questions
- Stratified sampling (by domain, difficulty, language)
- Rotating selection (randomly selects 20 questions each test)
- Baseline questions (5-10 fixed questions for trend tracking)

- Quản lý pool 100-200 câu hỏi
- Stratified sampling (chia theo domain, difficulty, language)
- Rotating selection (mỗi lần test random chọn 20 câu)
- Baseline questions (5-10 câu cố định để track trends)

### Data Structure:
```python
QuestionPool = {
    "baseline_questions": [
        # 5-10 fixed questions, never change
        # 5-10 câu cố định, không bao giờ thay đổi
        {
            "id": "baseline_001",
            "question": "...",
            "domain": "math",
            "difficulty": "hard",
            "language": "vi",
            "expected_answer": "...",
            "fixed": True  # Never remove / Không bao giờ remove
        }
    ],
    "rotating_questions": [
        # 90-190 questions, can be changed
        # 90-190 câu, có thể thay đổi
        {
            "id": "rot_001",
            "question": "...",
            "domain": "physics",
            "difficulty": "medium",
            "language": "en",
            "expected_answer": "...",
            "fixed": False,
            "last_used": "2025-01-15",
            "usage_count": 5
        }
    ]
}
```

---

## 📊 Component 2: Domain Coverage Analyzer / Phân Tích Domain Coverage

### Functionality / Chức Năng:
- Analyzes knowledge StillMe has learned
- Identifies domains with high/low knowledge
- Suggests questions for weak domains
- Tracks coverage trends

- Phân tích knowledge StillMe đã học
- Xác định domain nào có nhiều/ít knowledge
- Suggest questions cho domain yếu
- Track coverage trends

### Integration with Self-Diagnosis API:
```python
def analyze_domain_coverage():
    """
    Use StillMe's self-diagnosis API to analyze knowledge coverage
    Sử dụng self-diagnosis API của StillMe để phân tích knowledge coverage
    """
    domains = ["math", "physics", "ai", "biology", "philosophy", ...]
    coverage = {}
    
    for domain in domains:
        # Call self-diagnosis API
        response = requests.post(
            "/api/learning/self-diagnosis/analyze-coverage",
            json={"topic": domain, "depth": 3}
        )
        
        coverage[domain] = {
            "knowledge_items": response["total_items"],
            "coverage_score": response["coverage_score"],
            "gaps": response["identified_gaps"]
        }
    
    return coverage
```

---

## 🎲 Component 3: Question Generator / Generator Câu Hỏi

### Functionality / Chức Năng:
- Automatically generates questions from StillMe's learned knowledge
- Generates questions from knowledge gaps
- Generates questions from user queries (anonymized)

- Tự động generate questions từ knowledge StillMe đã học
- Generate questions từ knowledge gaps
- Generate questions từ user queries (anonymized)

---

## 🧪 Component 4: Test Executor / Thực Thi Test

### Functionality / Chức Năng:
- Executes test questions via API
- Collects metrics (confidence, validation, latency)
- Handles errors gracefully

- Execute test questions qua API
- Collect metrics (confidence, validation, latency)
- Handle errors gracefully

---

## 📈 Component 5: Metrics Collector / Thu Thập Metrics

### Functionality / Chức Năng:
- Logs results to CSV/JSON
- Calculates aggregate metrics
- Tracks trends over time
- Generates reports

- Log results to CSV/JSON
- Calculate aggregate metrics
- Track trends over time
- Generate reports

---

## 🚀 Implementation Phases / Các Giai Đoạn Triển Khai

### Phase 1: Static Pool (Month 1-2) / Pool Tĩnh (Tháng 1-2)
- ✅ Create question pool (100-200 questions) / Tạo question pool (100-200 câu)
- ✅ Implement stratified sampling / Triển khai stratified sampling
- ✅ Basic test executor / Test executor cơ bản
- ✅ CSV logging / Ghi log CSV

### Phase 2: Domain Coverage (Month 3-4) / Domain Coverage (Tháng 3-4)
- ✅ Integrate with self-diagnosis API / Tích hợp với self-diagnosis API
- ✅ Coverage-based question selection / Chọn câu hỏi dựa trên coverage
- ✅ Adaptive difficulty / Điều chỉnh độ khó

### Phase 3: Dynamic Generation (Month 5-6) / Generate Động (Tháng 5-6)
- ✅ Generate questions from knowledge base / Generate từ knowledge base
- ✅ Generate questions from gaps / Generate từ gaps
- ✅ Generate questions from user queries / Generate từ user queries

### Phase 4: Production Integration (Month 7+) / Tích Hợp Production (Tháng 7+)
- ✅ CI/CD integration / Tích hợp CI/CD
- ✅ Automated reporting / Báo cáo tự động
- ✅ Alerting system / Hệ thống cảnh báo
- ✅ Dashboard visualization / Trực quan hóa dashboard

---

## 📝 Best Practices / Thực Hành Tốt Nhất

1. **Question Quality / Chất Lượng Câu Hỏi**:
   - Human review new questions before adding to pool / Người review câu hỏi mới trước khi thêm vào pool
   - Remove outdated questions periodically / Xóa câu hỏi lỗi thời định kỳ
   - Validate questions against current knowledge / Validate câu hỏi với knowledge hiện tại

2. **Test Frequency / Tần Suất Test**:
   - After major deployments: Full suite (20 questions) / Sau deploy lớn: Full suite (20 câu)
   - Daily: Light suite (5-10 questions) / Hàng ngày: Light suite (5-10 câu)
   - Weekly: Full suite with coverage analysis / Hàng tuần: Full suite với coverage analysis

3. **Metrics Tracking / Theo Dõi Metrics**:
   - Keep baseline questions fixed for trend tracking / Giữ baseline questions cố định để track trends
   - Rotate other questions to avoid overfitting / Xoay các câu khác để tránh overfitting
   - Track both technical metrics and human evaluation / Track cả technical metrics và human evaluation

4. **Cost Management / Quản Lý Chi Phí**:
   - Cache responses for unchanged questions / Cache responses cho câu hỏi không đổi
   - Run tests during off-peak hours / Chạy test vào giờ off-peak
   - Limit test frequency if API costs are high / Giới hạn tần suất test nếu API costs cao

---

## 🎯 Conclusion / Kết Luận

Dynamic Test Suite will:
- ✅ Avoid overfitting with rotating questions / Tránh overfitting với rotating questions
- ✅ Adapt with knowledge StillMe has learned / Adapt với knowledge StillMe đã học
- ✅ Focus on weak domains / Tập trung vào domains yếu
- ✅ Generate fresh questions from new knowledge / Generate câu hỏi mới từ knowledge mới
- ✅ Track trends and improvements / Track trends và improvements

Dynamic Test Suite sẽ:
- ✅ Tránh overfitting với rotating questions
- ✅ Adapt với knowledge StillMe đã học
- ✅ Focus vào domains yếu
- ✅ Generate fresh questions từ knowledge mới
- ✅ Track trends và improvements

**Next Steps**: Implement Phase 1 (Static Pool) first, then expand to Phase 2-4.
**Bước Tiếp Theo**: Triển khai Phase 1 (Static Pool) trước, sau đó mở rộng sang Phase 2-4.
