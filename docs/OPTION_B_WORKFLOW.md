# Option B Pipeline - Workflow & Integration Guide

## 🎯 Mục đích của Test Script

File `scripts/test_option_b_pipeline.py` là **DEMO/PROTOTYPE** để:

1. **Test baseline (pipeline hiện tại):** Xem pipeline hiện tại xử lý các câu hỏi như thế nào
2. **Test Option B (sau khi integrate):** So sánh Option B với baseline
3. **Đánh giá hiệu suất:** 
   - Hallucination rate: 0% (mục tiêu)
   - Latency: Chấp nhận được (10-20s)
   - Depth: Sâu sắc, triết học

## 📋 Workflow

### Step 1: Test Baseline (Pipeline Hiện Tại)

```bash
python scripts/test_option_b_pipeline.py
```

**Kết quả mong đợi:**
- Có thể có hallucination (đặc biệt với fake concepts)
- Latency: 5-8s
- Depth: Có thể thiếu

### Step 2: Integrate Option B vào chat_router.py

**Cách 1: Thêm flag `use_option_b` vào ChatRequest model**

```python
# backend/api/models.py
class ChatRequest(BaseModel):
    message: str
    use_rag: bool = True
    context_limit: int = 5
    use_option_b: bool = False  # NEW: Enable Option B pipeline
```

**Cách 2: Sử dụng environment variable**

```python
# backend/api/routers/chat_router.py
USE_OPTION_B_BY_DEFAULT = os.getenv("STILLME_USE_OPTION_B_PIPELINE", "false").lower() == "true"
```

**Cách 3: Tích hợp trực tiếp vào chat_with_rag**

```python
# backend/api/routers/chat_router.py
async def chat_with_rag(request: Request, chat_request: ChatRequest):
    # ... existing code ...
    
    # Check if Option B is enabled
    use_option_b = chat_request.use_option_b if hasattr(chat_request, 'use_option_b') else False
    use_option_b = use_option_b or USE_OPTION_B_BY_DEFAULT
    
    if use_option_b:
        # Use Option B pipeline
        from backend.core.option_b_pipeline import process_with_option_b, process_llm_response_with_option_b
        
        # Step 1-4: Pre-LLM processing
        pre_result = await process_with_option_b(
            question=chat_request.message,
            use_rag=chat_request.use_rag,
            detected_lang=detected_lang,
            rag_retrieval=rag_retrieval
        )
        
        # If blocked by FPS, return immediately
        if pre_result.get("used_fallback"):
            return ChatResponse(
                response=pre_result["response"],
                confidence_score=1.0,
                processing_steps=pre_result["processing_steps"],
                timing_logs=pre_result["timing_logs"]
            )
        
        # Step 4: LLM Raw Answer (existing LLM call)
        # ... existing LLM call code ...
        
        # Step 5-8: Post-LLM processing
        post_result = await process_llm_response_with_option_b(
            llm_response=response,
            question=chat_request.message,
            question_type=pre_result["question_type"],
            ctx_docs=ctx_docs,
            detected_lang=detected_lang,
            fps_result=fps_result
        )
        
        # Use post-processed response
        response = post_result["response"]
        processing_steps.extend(post_result["processing_steps"])
        timing_logs.update(post_result["timing_logs"])
    else:
        # Use existing pipeline (legacy)
        # ... existing code ...
```

### Step 3: Test Option B Pipeline

Sau khi integrate, chạy lại test script:

```bash
python scripts/test_option_b_pipeline.py
```

**Kết quả mong đợi (Option B):**
- ✅ Hallucination rate: 0%
- ✅ Fake concepts → EPD-Fallback (không bịa)
- ✅ Real concepts → Trả lời đúng, có chiều sâu
- ⚠️ Latency: 10-20s (chấp nhận được)

### Step 4: So sánh & Quyết định

**Nếu Option B vượt trội:**
- ✅ 0% hallucination
- ✅ Latency chấp nhận được (10-20s)
- ✅ Depth tốt hơn

→ **Quyết định:** Make Option B the **default pipeline**

**Nếu Option B có vấn đề:**
- ❌ Latency quá cao (>30s)
- ❌ Có lỗi trong implementation

→ **Quyết định:** 
- Tối ưu latency
- Hoặc giữ Option B làm **optional feature** (flag `use_option_b=true`)

## 🔧 Cách Fix Lỗi Test Script

Lỗi hiện tại: **UnicodeEncodeError** trên Windows PowerShell

**Đã fix:**
- Thêm encoding fix cho Windows console
- Safe truncation cho Vietnamese text
- Better error handling

**Chạy lại:**
```bash
python scripts/test_option_b_pipeline.py
```

## 📊 Kết quả Test

Sau khi chạy test, bạn sẽ thấy:

```
GROUP A: Real Factual Questions
  ✅ PASSED / ❌ FAILED

GROUP B: Fake Factual Questions  
  ✅ PASSED (must use EPD-Fallback) / ❌ FAILED (still hallucinating)

GROUP C: Meta-Honesty Questions
  ✅ PASSED (consistent) / ❌ FAILED (contradictory)

Overall: X/8 passed (XX.X%)
```

## 🚀 Next Steps

1. **Fix test script** ✅ (đã fix encoding)
2. **Test baseline** → Chạy script để xem pipeline hiện tại
3. **Integrate Option B** → Thêm vào chat_router.py
4. **Test Option B** → Chạy lại script
5. **So sánh & quyết định** → Make default hoặc optional

## 💡 Lưu ý

- Test script hiện tại test **EXISTING pipeline** (chưa có Option B)
- Sau khi integrate Option B, script sẽ tự động test Option B
- Nếu muốn test Option B trước khi integrate, có thể modify script để gọi trực tiếp `option_b_pipeline.py` (bypass API)

