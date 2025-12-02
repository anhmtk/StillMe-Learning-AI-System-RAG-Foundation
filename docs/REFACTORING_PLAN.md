# 🏗️ StillMe Framework Refactoring Plan

## 📋 Executive Summary

**Mục tiêu**: Tái cấu trúc StillMe từ một monolithic application thành một **modular framework** có thể:
1. StillMe hiện tại sử dụng như dependency
2. Tách ra thành SDK trong tương lai
3. Tự monitoring và self-improvement
4. Tạo bằng chứng thực tế từ chính usage

**Triết lý cốt lõi**: Transparency-first, Validation-mandatory, Intellectual Humility

---

## 🔍 PHÂN TÍCH CODEBASE HIỆN TẠI

### 1. Components Chính Đã Có

#### ✅ **Validation System** (`backend/validators/`)
- **27 validators** đã được implement
- **ValidatorChain** với parallel execution support
- **ValidationMetrics** tracking (in-memory)
- **ValidationMetricsTracker** với persistent storage (JSONL)
- **SelfImprovementAnalyzer** phân tích patterns và đề xuất improvements

**Điểm mạnh**:
- Modular design với `Validator` protocol
- Có metrics tracking
- Có self-improvement mechanism

**Pain points**:
- Validators nằm trong `backend/validators/` - chưa tách thành core framework
- Metrics tracking rải rác (in-memory + persistent)
- Self-improvement chưa được tích hợp sâu vào workflow

#### ✅ **RAG System** (`backend/vector_db/`)
- **ChromaClient** - vector database client
- **EmbeddingService** - embedding generation
- **RAGRetrieval** - retrieval service với caching

**Điểm mạnh**:
- Tách biệt rõ ràng với application logic
- Có caching mechanism

**Pain points**:
- RAG logic vẫn gắn với StillMe app (hardcoded prompts, thresholds)
- Chưa có abstraction layer cho different RAG strategies

#### ✅ **Learning System** (`backend/learning/`, `backend/services/`)
- **LearningScheduler** - automated learning cycles
- **RSSFetcher** - content fetching
- **ContentCurator** - content filtering
- **AccuracyScorer** - quality assessment

**Điểm mạnh**:
- Tách biệt learning pipeline khỏi chat flow
- Có scheduler với watchdog

**Pain points**:
- Learning logic gắn chặt với StillMe's specific sources (RSS, arXiv)
- Chưa có abstraction cho different learning strategies

#### ✅ **Post-Processing** (`backend/postprocessing/`)
- **QualityEvaluator** - quality assessment
- **RewriteLLM** - response rewriting
- **StyleSanitizer** - style normalization

**Điểm mạnh**:
- Modular post-processing pipeline

**Pain points**:
- Post-processing logic gắn với StillMe's specific requirements
- Chưa có generic post-processing framework

#### ✅ **Identity & Philosophy** (`backend/identity/`, `backend/philosophy/`)
- **IdentityInjector** - StillMe identity injection
- **PhilosophicalProcessor** - specialized philosophical handling

**Điểm mạnh**:
- Tách biệt identity logic

**Pain points**:
- Hardcoded cho StillMe's specific identity
- Chưa có generic identity framework

#### ✅ **External Data** (`backend/external_data/`)
- **ExternalDataOrchestrator** - orchestrates multiple providers
- **Providers** (Weather, News, Time) với base class

**Điểm mạnh**:
- Provider pattern đã được implement
- Có rate limiting và caching

**Pain points**:
- Providers gắn với StillMe's specific use cases
- Chưa có generic provider framework

### 2. Cấu Trúc Thư Mục Hiện Tại

```
backend/
├── validators/          # ✅ 27 validators - có thể tách thành core
├── vector_db/           # ✅ RAG system - có thể tách thành core
├── learning/            # ⚠️ Learning logic - cần abstraction
├── postprocessing/      # ⚠️ Post-processing - cần abstraction
├── identity/            # ⚠️ StillMe-specific - giữ trong app
├── philosophy/          # ⚠️ StillMe-specific - giữ trong app
├── external_data/      # ✅ Provider pattern - có thể tách thành core
├── core/                # ⚠️ Mixed: có generic (model_router) và StillMe-specific
├── services/            # ⚠️ Mixed: có generic (cache_service) và StillMe-specific
└── api/                 # ❌ Application layer - giữ nguyên
```

### 3. Pain Points Lớn Nhất

1. **Tight Coupling**: Validation, RAG, Learning logic gắn chặt với StillMe app
2. **Metrics Fragmentation**: Metrics tracking ở nhiều nơi (in-memory, persistent, service)
3. **No Framework Abstraction**: Không có abstraction layer để tách framework khỏi app
4. **Self-Improvement Isolated**: Self-improvement mechanism chưa được tích hợp sâu
5. **Configuration Scattered**: Config rải rác (env vars, hardcoded values)

---

## 🎯 KIẾN TRÚC MỤC TIÊU

### Cấu Trúc Thư Mục Mới

```
stillme-framework/                    # ROOT
├── stillme_core/                     # 🎯 FRAMEWORK CORE (có thể tách thành SDK)
│   ├── __init__.py
│   ├── validation/                   # ✅ Tách từ backend/validators/
│   │   ├── __init__.py
│   │   ├── engine.py                 # ValidatorChain → ValidationEngine
│   │   ├── base.py                   # Validator protocol, ValidationResult
│   │   ├── validators/               # Modular validators
│   │   │   ├── __init__.py
│   │   │   ├── citation.py
│   │   │   ├── evidence.py
│   │   │   ├── confidence.py
│   │   │   └── ... (27 validators)
│   │   └── metrics.py                # ValidationMetrics + ValidationMetricsTracker
│   │
│   ├── rag/                          # ✅ Tách từ backend/vector_db/
│   │   ├── __init__.py
│   │   ├── base.py                   # Abstract RAGRetrieval interface
│   │   ├── chroma_rag.py             # ChromaDB implementation
│   │   ├── embeddings.py             # EmbeddingService
│   │   └── strategies.py             # Different RAG strategies
│   │
│   ├── learning/                     # ⚠️ Tách từ backend/learning/ + services/
│   │   ├── __init__.py
│   │   ├── base.py                   # Abstract LearningPipeline interface
│   │   ├── scheduler.py               # LearningScheduler (generic)
│   │   ├── fetchers/                  # Abstract fetcher interface
│   │   │   ├── base.py
│   │   │   ├── rss_fetcher.py
│   │   │   └── arxiv_fetcher.py
│   │   └── curator.py                 # ContentCurator (generic)
│   │
│   ├── postprocessing/                # ⚠️ Tách từ backend/postprocessing/
│   │   ├── __init__.py
│   │   ├── base.py                   # Abstract PostProcessor interface
│   │   ├── quality_evaluator.py
│   │   ├── rewriter.py
│   │   └── sanitizer.py
│   │
│   ├── external_data/                # ✅ Tách từ backend/external_data/
│   │   ├── __init__.py
│   │   ├── orchestrator.py
│   │   ├── providers/
│   │   │   ├── base.py
│   │   │   └── ... (existing providers)
│   │   └── cache.py
│   │
│   ├── self_improvement/              # 🆕 NEW - Tập trung self-improvement
│   │   ├── __init__.py
│   │   ├── analyzer.py                # SelfImprovementAnalyzer
│   │   ├── metrics_collector.py      # Unified metrics collection
│   │   ├── improvement_engine.py     # Improvement loop
│   │   └── feedback_loop.py          # Feedback từ validation → learning
│   │
│   ├── monitoring/                    # 🆕 NEW - Unified monitoring
│   │   ├── __init__.py
│   │   ├── metrics.py                # Unified metrics interface
│   │   ├── dashboard.py              # Metrics dashboard (optional)
│   │   └── alerts.py                 # Alert system (future)
│   │
│   └── config/                       # 🆕 NEW - Centralized config
│       ├── __init__.py
│       ├── base.py                   # Base config class
│       └── validators.py             # Validator config
│
├── stillme_app/                       # 🎯 STILLME APPLICATION (dùng core)
│   ├── __init__.py
│   ├── main.py                        # FastAPI app entry point
│   │
│   ├── identity/                      # ✅ StillMe-specific identity
│   │   ├── __init__.py
│   │   ├── injector.py
│   │   └── prompt_builder.py
│   │
│   ├── philosophy/                    # ✅ StillMe-specific philosophy
│   │   ├── __init__.py
│   │   └── processor.py
│   │
│   ├── api/                           # ✅ API layer
│   │   ├── main.py
│   │   ├── routers/
│   │   └── middleware/
│   │
│   ├── services/                     # ✅ StillMe-specific services
│   │   ├── learning_scheduler.py     # Wrapper around core scheduler
│   │   └── ... (StillMe-specific services)
│   │
│   └── config/                        # ✅ StillMe-specific config
│       └── stillme_config.py
│
├── tests/                             # Tests cho CẢ framework và app
│   ├── core/
│   │   ├── test_validation/
│   │   ├── test_rag/
│   │   └── test_learning/
│   └── app/
│       └── test_stillme/
│
└── docs/                              # Tài liệu
    ├── framework/                     # Framework docs
    │   ├── ARCHITECTURE.md
    │   ├── VALIDATION.md
    │   └── SELF_IMPROVEMENT.md
    └── app/                            # StillMe app docs
        └── USER_GUIDE.md
```

### Nguyên Tắc Thiết Kế

1. **Separation of Concerns**:
   - `stillme_core/`: Framework logic (generic, reusable)
   - `stillme_app/`: StillMe-specific logic (identity, philosophy, API)

2. **Dependency Direction**:
   - `stillme_app/` → `stillme_core/` (app depends on core, not vice versa)
   - Core không biết về StillMe app

3. **Interface-Based Design**:
   - Core cung cấp abstract interfaces (Protocol/ABC)
   - App implement StillMe-specific logic

4. **Configuration Injection**:
   - Core nhận config từ app (dependency injection)
   - Không hardcode StillMe-specific values

---

## 🚀 LỘ TRÌNH MIGRATION (4 PHASES)

### PHASE 1: TÁI CẤU TRÚC HIỆN CÓ (Tuần 1-2)

#### Step 1.1: Tạo Core Structure
- [ ] Tạo `stillme_core/` directory structure
- [ ] Tạo `stillme_app/` directory structure
- [ ] Setup `__init__.py` files với proper exports

#### Step 1.2: Migrate Validation System
- [ ] Move `backend/validators/` → `stillme_core/validation/`
- [ ] Rename `ValidatorChain` → `ValidationEngine`
- [ ] Consolidate metrics: Merge `ValidationMetrics` + `ValidationMetricsTracker` → `stillme_core/validation/metrics.py`
- [ ] Update imports trong StillMe app
- [ ] Test: Đảm bảo validation vẫn hoạt động

#### Step 1.3: Migrate RAG System
- [ ] Move `backend/vector_db/` → `stillme_core/rag/`
- [ ] Create `RAGRetrieval` abstract interface
- [ ] Refactor `ChromaRAGRetrieval` (rename từ RAGRetrieval)
- [ ] Update imports trong StillMe app
- [ ] Test: Đảm bảo RAG vẫn hoạt động

#### Step 1.4: Migrate External Data
- [ ] Move `backend/external_data/` → `stillme_core/external_data/`
- [ ] Keep provider pattern (đã tốt)
- [ ] Update imports trong StillMe app
- [ ] Test: Đảm bảo external data vẫn hoạt động

**Deliverable**: Core structure với validation, RAG, external_data đã migrate. StillMe app vẫn chạy được.

---

### PHASE 2: SELF-MONITORING & METRICS (Tuần 3)

#### Step 2.1: Unified Metrics System
- [ ] Create `stillme_core/monitoring/metrics.py` - unified metrics interface
- [ ] Migrate tất cả metrics tracking vào unified system:
  - Validation metrics (đã có)
  - RAG metrics (thêm mới)
  - Learning metrics (thêm mới)
  - Post-processing metrics (thêm mới)
- [ ] Create metrics dashboard (optional, có thể dùng Streamlit)

#### Step 2.2: Self-Improvement Integration
- [ ] Move `backend/validators/self_improvement.py` → `stillme_core/self_improvement/analyzer.py`
- [ ] Create `stillme_core/self_improvement/improvement_engine.py` - improvement loop
- [ ] Create `stillme_core/self_improvement/feedback_loop.py` - feedback từ validation → learning
- [ ] Integrate vào StillMe app workflow

#### Step 2.3: Configuration System
- [ ] Create `stillme_core/config/base.py` - base config class
- [ ] Create `stillme_core/config/validators.py` - validator config
- [ ] Refactor: Move env vars → config classes
- [ ] Update StillMe app để sử dụng config system

**Deliverable**: Unified metrics system, self-improvement tích hợp, config system centralized.

---

### PHASE 3: LEARNING & POST-PROCESSING (Tuần 4)

#### Step 3.1: Abstract Learning Pipeline
- [ ] Create `stillme_core/learning/base.py` - abstract LearningPipeline interface
- [ ] Move `backend/services/learning_scheduler.py` → `stillme_core/learning/scheduler.py` (generic)
- [ ] Create abstract fetcher interface
- [ ] Move RSS/arXiv fetchers → `stillme_core/learning/fetchers/`
- [ ] Create StillMe-specific learning pipeline wrapper trong `stillme_app/`

#### Step 3.2: Abstract Post-Processing
- [ ] Create `stillme_core/postprocessing/base.py` - abstract PostProcessor interface
- [ ] Move post-processing components → `stillme_core/postprocessing/`
- [ ] Create StillMe-specific post-processor wrapper trong `stillme_app/`

#### Step 3.3: Integration Testing
- [ ] Test toàn bộ pipeline: Learning → RAG → Validation → Post-processing
- [ ] Test self-improvement loop
- [ ] Performance testing

**Deliverable**: Learning và post-processing đã abstract, StillMe app sử dụng core framework.

---

### PHASE 4: DOCUMENTATION & PROOF (Tuần 5)

#### Step 4.1: Framework Documentation
- [ ] Write `docs/framework/ARCHITECTURE.md` - framework architecture
- [ ] Write `docs/framework/VALIDATION.md` - validation system guide
- [ ] Write `docs/framework/SELF_IMPROVEMENT.md` - self-improvement guide
- [ ] Write `docs/framework/API.md` - core API reference

#### Step 4.2: Migration Guide
- [ ] Write `docs/MIGRATION_GUIDE.md` - hướng dẫn migrate từ old structure
- [ ] Write `docs/CONTRIBUTING.md` - hướng dẫn contribute to framework

#### Step 4.3: Proof Package
- [ ] Collect real usage data từ StillMe app
- [ ] Create "proof package" với:
  - Validation metrics (pass rate, hallucination reduction)
  - Self-improvement evidence (improvements suggested & implemented)
  - Performance metrics (latency, throughput)
- [ ] Create `docs/framework/PROOF.md` - bằng chứng framework hoạt động

**Deliverable**: Documentation đầy đủ, proof package với real data.

---

## ⚠️ LƯU Ý QUAN TRỌNG

### ĐỪNG LÀM:
- ❌ Phá vỡ chức năng hiện tại của StillMe
- ❌ Tạo duplicate code khi đã có sẵn
- ❌ Thay đổi triết lý core (transparency-first)
- ❌ Tối ưu premature - ưu tiên modularity trước performance

### NÊN LÀM:
- ✅ Hiểu codebase hiện tại TRƯỚC khi refactor
- ✅ Tái cấu trúc GRADUAL, có testing sau mỗi step
- ✅ Giữ backward compatibility (có thể dùng adapter pattern)
- ✅ Document mọi architectural decision
- ✅ Hỏi nếu không rõ về triết lý/tinh thần

---

## 🎯 SUCCESS CRITERIA

### Phase 1 Success:
- ✅ StillMe app vẫn chạy được sau migration
- ✅ Validation, RAG, external_data đã migrate vào core
- ✅ Tests pass

### Phase 2 Success:
- ✅ Unified metrics system hoạt động
- ✅ Self-improvement tích hợp vào workflow
- ✅ Config system centralized

### Phase 3 Success:
- ✅ Learning và post-processing đã abstract
- ✅ StillMe app sử dụng core framework
- ✅ Performance không degrade

### Phase 4 Success:
- ✅ Documentation đầy đủ
- ✅ Proof package với real data
- ✅ Framework sẵn sàng cho community launch

---

## 📞 NEXT STEPS

1. **Review plan này với team/user**
2. **Bắt đầu Phase 1**: Tạo core structure và migrate validation system
3. **Iterate**: Sau mỗi phase, review và adjust nếu cần

---

**Tinh thần cuối cùng**: 
> "Chúng ta đang xây một framework, không chỉ một app. Mọi thứ chúng ta làm cho StillMe hôm nay, phải là thứ các AI khác có thể dùng ngày mai."

