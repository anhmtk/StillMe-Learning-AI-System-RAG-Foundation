# StillMe Evaluation Guide - Hướng dẫn chi tiết

## 📚 Hiểu về Evaluation Framework

### 1. Sample Questions vs Full Datasets

#### Sample Questions (Hiện tại - Đã có sẵn)
- **Mục đích**: Test nhanh framework, verify code hoạt động
- **Số lượng**: 3-5 questions (sample trong code)
- **Khi nào dùng**: 
  - ✅ Test code mới viết
  - ✅ Verify API hoạt động
  - ✅ Quick check trước khi chạy full evaluation
- **Ưu điểm**: Nhanh (1-2 phút), không cần download gì
- **Nhược điểm**: Không đủ để publish paper (quá ít questions)

#### Full Datasets (Cần download)
- **Mục đích**: Evaluation đầy đủ cho paper
- **Số lượng**: 
  - TruthfulQA: ~800 questions
  - HaluEval: ~10,000 questions
- **Khi nào cần**:
  - ✅ Khi muốn có results đầy đủ cho paper
  - ✅ Khi cần so sánh với baseline systems
  - ✅ Khi cần statistical significance
- **Ưu điểm**: Results đáng tin cậy, có thể publish
- **Nhược điểm**: Mất thời gian (1-2 giờ để chạy), cần download datasets

### 2. Khi nào "sẵn sàng" download full datasets?

**Sẵn sàng khi:**
1. ✅ Sample evaluation đã chạy thành công (code hoạt động)
2. ✅ Bạn muốn có results đầy đủ cho paper
3. ✅ Có thời gian chạy evaluation (1-2 giờ)
4. ✅ Backend đã stable, không có lỗi

**Chưa sẵn sàng khi:**
- ❌ Code mới viết, chưa test
- ❌ Backend còn lỗi
- ❌ Chỉ muốn test nhanh framework

**Lời khuyên:**
- **Bây giờ**: Dùng sample questions để test
- **Sau khi test xong**: Download full datasets và chạy full evaluation
- **Trước khi submit paper**: Chạy full evaluation với full datasets

---

## 📋 Survey Form Integration với API

### Hiện tại (Survey Form Standalone)

**File**: `evaluation/survey_form.html`

**Cách hoạt động hiện tại:**
- Mở file HTML trong browser
- User điền survey
- Data lưu vào **localStorage** (chỉ trong browser)
- Phải export thủ công để lấy data

**Vấn đề:**
- ❌ Data không tự động gửi về server
- ❌ Phải export thủ công
- ❌ Khó collect data từ nhiều users

### Sau khi tích hợp API (Recommended)

**Cách hoạt động:**
- Survey form gửi data trực tiếp về StillMe API
- API lưu vào database
- Tự động analyze và generate report
- Dễ collect từ nhiều users

**Lợi ích:**
- ✅ Tự động collect data
- ✅ Centralized storage
- ✅ Dễ analyze và report
- ✅ Có thể share link survey cho nhiều users

**Cần làm:**
1. Tạo API endpoint: `POST /api/evaluation/transparency-rating`
2. Update survey form để gửi data về API
3. Tự động analyze và generate report

---

## 🚀 Quick Start Guide

### Bước 1: Test với Sample Questions (Bây giờ)

```bash
# Start backend (nếu chưa chạy)
python start_backend.py

# Chạy evaluation với sample questions
python scripts/run_evaluation_sample.py --api-url http://localhost:8000
```

**Kết quả mong đợi:**
- ✅ Evaluation chạy thành công
- ✅ Hiển thị accuracy, hallucination rate, transparency score
- ✅ So sánh StillMe vs Vanilla RAG
- ⏱️ Thời gian: 1-2 phút

### Bước 2: Download Full Datasets (Khi sẵn sàng)

```bash
# Download TruthfulQA và HaluEval
python scripts/download_benchmark_datasets.py --datasets all
```

**Kết quả:**
- ✅ Datasets saved to `data/benchmarks/truthfulqa.json`
- ✅ Datasets saved to `data/benchmarks/halu_eval.json`

**Lưu ý:**
- Script sẽ tự động tạo sample nếu không download được
- Có thể download thủ công từ official sources

### Bước 3: Chạy Full Evaluation (Khi có datasets)

```bash
# Chạy full evaluation
python -m evaluation.run_evaluation \
    --api-url http://localhost:8000 \
    --output-dir data/evaluation/results \
    --benchmarks truthfulqa halu_eval comparison
```

**Kết quả:**
- ✅ Results saved to `data/evaluation/results/`
- ✅ Comparison report generated
- ⏱️ Thời gian: 1-2 giờ (tùy số lượng questions)

### Bước 4: User Study (Optional)

**Cách 1: Standalone (Hiện tại)**
- Mở `evaluation/survey_form.html` trong browser
- Share với participants
- Export data thủ công

**Cách 2: Integrated (Sau khi có API)**
- Survey form gửi data về API
- Tự động analyze
- Generate report

---

## 📊 Evaluation Results Structure

```
data/evaluation/results/
├── truthfulqa_results.json          # TruthfulQA benchmark results
├── halu_eval_results.json           # HaluEval benchmark results
├── comparison_results.json          # System comparison results
├── comparison_report.md             # Human-readable comparison report
├── summary_report.md                # Summary report
└── evaluation_summary.json          # Aggregated summary
```

---

## 🎯 Roadmap

### Phase 1: Test Framework (Bây giờ) ✅
- [x] Test với sample questions
- [x] Verify code hoạt động
- [x] Check API integration

### Phase 2: Full Evaluation (Khi sẵn sàng)
- [ ] Download full datasets
- [ ] Chạy full evaluation
- [ ] Collect results

### Phase 3: User Study (Optional)
- [ ] Tích hợp survey form với API
- [ ] Collect ratings từ users
- [ ] Analyze và report

---

## 💡 Tips

1. **Bắt đầu với sample**: Luôn test với sample questions trước
2. **Full datasets khi cần**: Chỉ download khi thực sự cần results đầy đủ
3. **Survey form**: Có thể dùng standalone hoặc tích hợp API sau
4. **Results cho paper**: Cần full evaluation với full datasets

---

## ❓ FAQ

**Q: Khi nào cần download full datasets?**
A: Khi bạn muốn có results đầy đủ cho paper, sau khi đã test thành công với sample.

**Q: Survey form có cần tích hợp API ngay không?**
A: Không. Có thể dùng standalone trước, tích hợp API sau khi cần.

**Q: Sample questions đủ để publish paper không?**
A: Không. Cần full datasets để có statistical significance.

**Q: Mất bao lâu để chạy full evaluation?**
A: 1-2 giờ tùy số lượng questions và API response time.

