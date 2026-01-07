# Stage 2: Meta-Learning - Phase 1: Retention Tracking

## ✅ Status: COMPLETED & TESTED

Phase 1 của Stage 2: Meta-Learning đã được triển khai và test thành công.

## 📋 Tổng quan

Phase 1 tập trung vào **Retention Tracking** - theo dõi documents nào thực sự được sử dụng trong responses để tính retention rate per source.

### Mục tiêu

1. **Track document usage**: Theo dõi documents nào được retrieve và sử dụng trong responses
2. **Calculate retention metrics**: Tính retention rate = (Documents used) / (Total documents learned)
3. **Auto-update source trust**: Tự động điều chỉnh source quality scores dựa trên retention
4. **Recommend sources**: Đề xuất sources tốt nhất dựa trên retention

## 🏗️ Kiến trúc

### Components

1. **DocumentUsageTracker** (`backend/learning/document_usage_tracker.py`)
   - Track document usage trong responses
   - Lưu vào `data/document_usage.jsonl`
   - Tính retention metrics per source

2. **SourceTrustCalculator** (`backend/learning/source_trust_calculator.py`)
   - Tính trust scores dựa trên retention rate
   - Auto-update `ContentCurator.source_quality_scores`
   - Recommend sources

3. **Integration** (`backend/api/routers/chat_router.py`)
   - Tự động track document usage khi generate response
   - Record: query, doc_id, source, similarity, confidence, validation status

4. **API Endpoints** (`backend/api/routers/meta_learning_router.py`)
   - `GET /api/meta-learning/retention` - Xem retention metrics
   - `GET /api/meta-learning/source-trust` - Xem trust scores
   - `POST /api/meta-learning/update-source-trust` - Manually update trust scores
   - `GET /api/meta-learning/recommended-sources` - Get recommended sources

## 📊 Trust Score Calculation

Trust scores được tính dựa trên retention rate:

- **High retention (30%+)** → Trust 0.8-1.0
- **Medium retention (10-30%)** → Trust 0.5-0.8
- **Low retention (<10%)** → Trust 0.2-0.5

### Ví dụ

```
Retention 5%  → Trust 0.35
Retention 15% → Trust 0.57
Retention 25% → Trust 0.73
Retention 35% → Trust 0.81
Retention 50% → Trust 0.86
Retention 75% → Trust 0.93
Retention 90% → Trust 0.97
```

## 🧪 Testing

### Test Script

Chạy test script:

```bash
python scripts/test_meta_learning_phase1.py
```

### Test Results

✅ **All tests passed!**

- DocumentUsageTracker: ✅ PASSED
- SourceTrustCalculator: ✅ PASSED
- Integration: ✅ PASSED

### Test API Endpoints

Khi server đang chạy, test các endpoints:

```bash
# Get retention metrics
curl http://localhost:8000/api/meta-learning/retention?days=30

# Get source trust scores
curl http://localhost:8000/api/meta-learning/source-trust?days=30

# Update source trust scores
curl -X POST http://localhost:8000/api/meta-learning/update-source-trust?days=30

# Get recommended sources
curl http://localhost:8000/api/meta-learning/recommended-sources?days=30&min_retention=0.20
```

## 📈 Data Flow

```
User Query
    ↓
RAG Retrieval → Documents Retrieved
    ↓
LLM Response Generation
    ↓
DocumentUsageTracker.record_batch_usage()
    ↓
data/document_usage.jsonl
    ↓
calculate_retention_metrics()
    ↓
SourceTrustCalculator.calculate_trust_score()
    ↓
ContentCurator.update_source_quality()
    ↓
Future Learning Cycles (prioritize high-trust sources)
```

## 🔄 Auto-Update Mechanism

Source trust scores được tự động update khi:

1. **Manual trigger**: Gọi `POST /api/meta-learning/update-source-trust`
2. **Scheduled task**: (Có thể implement trong tương lai - chạy định kỳ)

## 📝 Files Created/Modified

### New Files

- `backend/learning/document_usage_tracker.py` - Document usage tracking
- `backend/learning/source_trust_calculator.py` - Trust score calculation
- `backend/api/routers/meta_learning_router.py` - API endpoints
- `scripts/test_meta_learning_phase1.py` - Test script
- `docs/META_LEARNING_PHASE1.md` - This document

### Modified Files

- `backend/api/routers/chat_router.py` - Added document usage tracking
- `backend/api/main.py` - Added meta_learning_router

## 🎯 Next Steps

Phase 1 đã hoàn thành. Tiếp theo:

- **Phase 2: Curriculum Learning** (3-4 tháng)
  - LearningPatternAnalyzer
  - CurriculumGenerator
  - Auto-adjust priorities

- **Phase 3: Strategy Optimization** (4-6 tháng)
  - StrategyTracker
  - AutoTuner
  - A/B testing framework

## 📚 References

- [Stage 2: Meta-Learning Overview](../PHILOSOPHY.md#stage-2-meta-learning-v07)
- [ContentCurator Documentation](../stillme_core/learning/curator.py)
- [Learning Scheduler](../backend/services/learning_scheduler.py)

