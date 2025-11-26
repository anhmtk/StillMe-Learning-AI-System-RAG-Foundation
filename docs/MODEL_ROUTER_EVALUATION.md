# Đánh giá Model Router: DeepSeek Chat vs Reasoner

## 📊 Tổng quan

Đánh giá đề xuất implement model router để chọn giữa `deepseek-chat` và `deepseek-reasoner` dựa trên loại câu hỏi.

## ✅ Kết luận: **NÊN ÁP DỤNG** (Conservative Approach)

### Lợi ích > Rủi ro với approach conservative

---

## 🔍 Phân tích chi tiết

### 1. Kiến trúc hiện tại

**DeepSeek được dùng cho:**
- Main chat responses: `DeepSeekProvider.generate()` → hardcoded `deepseek-chat`
- Rewrite tasks: `RewriteLLM.rewrite()` → hardcoded `deepseek-chat`
- Timeout: 60s (chat), 45s (rewrite)
- Max tokens: 1500 cho cả hai

**Philosophical detection:**
- Có `is_philosophical_question()` function
- Được dùng trong chat router để quyết định prompt và xử lý

**Latency hiện tại:**
- LLM Inference: 2.5s average (1.8s - 4.2s)
- Total: 3.22s average
- Philosophical: 8-12s (legacy), 12-20s (Option B)

---

### 2. Ưu điểm của Model Router

#### ✅ Quality Improvement
- **Reasoner có thinking mode tốt hơn** cho philosophical questions
- Có thể cải thiện depth và reasoning cho philosophical answers
- Better handling of paradoxes, abstract concepts

#### ✅ Cost Optimization
- Chat model vẫn dùng cho factual (nhanh, rẻ)
- Reasoner chỉ dùng khi thực sự cần (philosophical questions)
- Có thể tối ưu cost nếu routing đúng

#### ✅ Flexibility
- Dễ dàng điều chỉnh routing logic
- Có thể A/B test để so sánh quality

---

### 3. Nhược điểm và Rủi ro

#### ⚠️ Complexity
- Thêm complexity vào codebase
- Cần maintain routing logic
- Có thể có edge cases routing sai

#### ⚠️ Latency
- Reasoner có thể chậm hơn (thinking mode)
- Có thể tăng latency cho philosophical questions
- **Impact:** +2-5s cho philosophical questions (có thể chấp nhận được)

#### ⚠️ Cost
- Reasoner có thể đắt hơn chat model
- Cần monitor cost khi dùng reasoner
- **Mitigation:** Chỉ dùng cho pure philosophical questions

#### ⚠️ Testing
- Cần test kỹ routing logic
- Cần validate quality improvement
- Cần monitor performance metrics

---

### 4. Khuyến nghị Implementation

#### 🎯 Conservative Approach (Recommended)

**Strategy:**
1. **Main Chat:**
   - Pure philosophical questions → `deepseek-reasoner` (thinking mode)
   - Philosophical factual questions → `deepseek-chat` (speed + cost)
   - Factual questions → `deepseek-chat` (speed + cost)

2. **Rewrite:**
   - **LUÔN dùng `deepseek-chat`** (đã có quality evaluator, không cần reasoner)

3. **Validation:**
   - **LUÔN dùng `deepseek-chat`** (cần function calling)

**Rationale:**
- Conservative = ít rủi ro
- Chỉ dùng reasoner khi chắc chắn sẽ giúp (pure philosophical)
- Rewrite và validation không cần reasoner (đã có quality checks)

---

### 5. Implementation Plan

#### Phase 1: Core Router (✅ Done)
- [x] Tạo `backend/core/model_router.py`
- [x] Implement `DeepSeekModelRouter` class
- [x] Conservative routing logic

#### Phase 2: Integration
- [ ] Integrate vào `DeepSeekProvider.generate()`
- [ ] Pass `question` và `task_type` từ chat router
- [ ] Update `RewriteLLM` để pass `task_type="rewrite"`

#### Phase 3: Testing
- [ ] Test với philosophical questions
- [ ] Test với factual questions
- [ ] Monitor latency và cost
- [ ] Compare quality (reasoner vs chat)

#### Phase 4: Monitoring
- [ ] Log model selection decisions
- [ ] Track latency by model type
- [ ] Track cost by model type
- [ ] A/B test quality improvement

---

### 6. Expected Impact

#### Quality
- **Philosophical questions:** +10-20% quality improvement (expected)
- **Factual questions:** No change (still use chat)

#### Latency
- **Philosophical questions:** +2-5s (reasoner thinking mode)
- **Factual questions:** No change (still use chat)
- **Total impact:** Minimal (only affects ~10-20% of questions)

#### Cost
- **Philosophical questions:** +20-50% cost (reasoner more expensive)
- **Factual questions:** No change (still use chat)
- **Total impact:** +5-10% overall cost (if 20% questions are philosophical)

---

### 7. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| Routing sai | Low | Medium | Conservative approach, extensive testing |
| Latency tăng | Medium | Low | Only for philosophical questions, acceptable |
| Cost tăng | Medium | Low | Monitor and adjust routing if needed |
| Quality không cải thiện | Low | Low | Can revert to chat-only easily |

**Overall Risk: LOW** (với conservative approach)

---

### 8. Success Metrics

#### Quality Metrics
- [ ] Philosophical question quality score (human evaluation)
- [ ] Citation rate (should maintain)
- [ ] Hallucination rate (should maintain or improve)

#### Performance Metrics
- [ ] Latency by question type
- [ ] Cost per question by model type
- [ ] Model selection distribution

#### User Experience
- [ ] User satisfaction with philosophical answers
- [ ] Response time perception
- [ ] Overall system quality

---

## 🎯 Final Recommendation

### ✅ **NÊN ÁP DỤNG** với Conservative Approach

**Lý do:**
1. **Lợi ích > Rủi ro:** Quality improvement cho philosophical questions quan trọng hơn cost/latency increase nhỏ
2. **Conservative approach:** Chỉ dùng reasoner khi chắc chắn sẽ giúp (pure philosophical)
3. **Reversible:** Dễ dàng revert nếu không hiệu quả
4. **Aligned với StillMe values:** Quality > Speed cho philosophical questions

**Next Steps:**
1. Complete Phase 2 integration
2. Test với small batch
3. Monitor metrics
4. Adjust routing logic based on results

---

## 📝 Notes

- **Reasoner thinking mode:** Có thể tốt hơn cho philosophical questions nhưng cần test
- **Cost monitoring:** Cần track cost để đảm bảo không vượt budget
- **Quality validation:** Cần human evaluation để confirm quality improvement
- **Fallback:** Luôn có fallback về chat model nếu reasoner fails

