# Session Context - Tình hình hiện tại

> **Mục đích**: File này giúp AI assistant nắm bắt tình hình nhanh chóng khi bị mất kết nối giữa các session.

**Cập nhật lần cuối**: 2025-01-27 (Session mới - sau khi mất kết nối)

---

## 📋 Tổng quan công việc hiện tại

### Đang làm: Evaluation Framework cho StillMe

**Mục tiêu**: Xây dựng framework đánh giá StillMe với các benchmarks và so sánh với baseline systems.

**Trạng thái**: Đang phát triển, đã có cơ bản, cần hoàn thiện và test.

---

## 📁 Files quan trọng

### Core Evaluation Files
- `evaluation/base.py` - Base classes (EvaluationResult, BenchmarkResults, BaseEvaluator)
- `evaluation/metrics.py` - MetricsCalculator, SystemMetrics
- `evaluation/truthfulqa.py` - TruthfulQA benchmark evaluator
- `evaluation/halu_eval.py` - HaluEval benchmark evaluator
- `evaluation/comparison.py` - SystemComparator (StillMe vs baselines) ⚠️ **ĐANG CHỈNH SỬA**
- `evaluation/transparency_study.py` - User study framework
- `evaluation/run_evaluation.py` - Main evaluation runner

### Scripts
- `scripts/run_evaluation_sample.py` - Quick test với sample questions (3-5 questions)
- `scripts/download_benchmark_datasets.py` - Download full datasets (nếu có)

### Documentation
- `docs/EVALUATION_GUIDE.md` - Hướng dẫn chi tiết (mới tạo, chưa commit) ⚠️ **MỚI TẠO**
- `evaluation/README.md` - Technical documentation

---

## ✅ Đã hoàn thành

1. **Base Framework**
   - ✅ Base classes (EvaluationResult, BenchmarkResults)
   - ✅ MetricsCalculator với các metrics: accuracy, hallucination_rate, transparency_score
   - ✅ BaseEvaluator với query_stillme() và extract_metrics()

2. **Benchmark Evaluators**
   - ✅ TruthfulQAEvaluator - đánh giá truthfulness và accuracy
   - ✅ HaluEvalEvaluator - đánh giá hallucination detection
   - ✅ Cả hai đều hỗ trợ sample questions (không cần download datasets)

3. **System Comparison**
   - ✅ SystemComparator class
   - ✅ So sánh StillMe vs Vanilla RAG vs ChatGPT vs Claude
   - ✅ Generate comparison report (markdown)

4. **Scripts & Tools**
   - ✅ `run_evaluation_sample.py` - test nhanh với sample questions
   - ✅ `run_evaluation.py` - full evaluation runner

5. **Documentation**
   - ✅ `EVALUATION_GUIDE.md` - hướng dẫn chi tiết bằng tiếng Việt
   - ✅ Giải thích sample vs full datasets
   - ✅ Roadmap và tips

---

## 🚧 Đang làm / Cần làm

### Immediate (Ưu tiên cao)
1. **Kiểm tra và fix `comparison.py`** ✅ **ĐÃ FIX**
   - File đang modified (chưa commit)
   - ✅ **Đã thêm methods missing**: `_query_stillme()`, `_extract_metrics()`
   - ✅ Methods này reuse logic từ `BaseEvaluator` trong `base.py`
   - ✅ Đã verify: `_check_correctness()` đã có sẵn

2. **Test evaluation framework**
   - Chạy `run_evaluation_sample.py` để verify code hoạt động
   - Kiểm tra API integration
   - Fix bugs nếu có

### Short-term (Sau khi test xong)
3. **Improve correctness checking**
   - Hiện tại `_check_correctness()` chỉ dùng simple keyword matching
   - TODO trong `truthfulqa.py`: "Use better matching (semantic similarity, LLM-based evaluation)"
   - Có thể dùng semantic similarity (cosine similarity với embeddings)

4. **API Integration cho Survey Form**
   - Hiện tại survey form standalone (localStorage)
   - Cần tạo endpoint: `POST /api/evaluation/transparency-rating`
   - Update `evaluation/survey_form.html` để gửi data về API

### Long-term (Khi sẵn sàng)
5. **Download và chạy full datasets**
   - TruthfulQA: ~800 questions
   - HaluEval: ~10,000 questions
   - Chỉ làm khi đã test xong với sample questions

6. **User Study**
   - Tích hợp survey form với API
   - Collect ratings từ users
   - Analyze và generate report

---

## 🔍 Chi tiết kỹ thuật

### Evaluation Flow
1. Load questions (sample hoặc từ dataset)
2. Query StillMe API với từng question
3. Extract metrics từ response (confidence, citations, uncertainty, validation)
4. Check correctness (so sánh với ground truth)
5. Calculate aggregated metrics (accuracy, hallucination_rate, transparency_score)
6. Generate report

### Metrics được tính
- **Accuracy**: % correct answers
- **Hallucination Rate**: % incorrect/ungrounded responses
- **Transparency Score**: Weighted combination
  - Citation Rate (40%)
  - Uncertainty Rate (30%)
  - Validation Pass Rate (30%)
- **Citation Rate**: % responses có citations
- **Uncertainty Rate**: % responses express uncertainty
- **Validation Pass Rate**: % responses pass validation chain

### Systems được so sánh
1. **StillMe** - Full RAG + Validation
2. **Vanilla RAG** - RAG nhưng không có validation
3. **ChatGPT** - GPT-4 (cần OPENAI_API_KEY)
4. **Claude** - Claude-3 (cần ANTHROPIC_API_KEY)

---

## ⚠️ Lưu ý quan trọng

1. **Sample vs Full Datasets**
   - Sample questions: 3-5 questions, test nhanh (1-2 phút)
   - Full datasets: 800-10,000 questions, chạy lâu (1-2 giờ)
   - **Hiện tại**: Dùng sample để test, chưa cần download full datasets

2. **API Requirements**
   - StillMe API phải chạy ở `http://localhost:8000` (hoặc config khác)
   - ChatGPT/Claude cần API keys (optional, chỉ khi muốn so sánh)

3. **File Status**
   - `evaluation/comparison.py` - **MODIFIED** (chưa commit)
   - `docs/EVALUATION_GUIDE.md` - **UNTRACKED** (mới tạo)

---

## 🐛 Known Issues / TODOs

1. **`evaluation/truthfulqa.py:94`**
   - TODO: "Use better matching (semantic similarity, LLM-based evaluation)"
   - Hiện tại chỉ dùng simple keyword matching

2. **`comparison.py`**
   - Cần verify `_query_stillme()` method có tồn tại không
   - Cần verify `_extract_metrics()` method
   - `_check_correctness()` quá đơn giản, cần improve

---

## 📝 Next Steps (Khi tiếp tục)

1. **Đọc file này** để nắm bắt tình hình
2. **Kiểm tra `comparison.py`** - xem có lỗi gì không, có methods missing không
3. **Test evaluation** - chạy `run_evaluation_sample.py` để verify
4. **Fix bugs** nếu có
5. **Commit changes** khi đã test xong

---

## 🔗 Related Files

- `STILLME_TEST_QUESTIONS.md` - Test questions cho StillMe
- `docs/API_DOCUMENTATION.md` - API docs (nếu có)
- `data/evaluation/results/` - Kết quả evaluation (sẽ được tạo khi chạy)

---

**Lưu ý**: File này nên được update mỗi khi có thay đổi quan trọng hoặc khi bắt đầu session mới.

