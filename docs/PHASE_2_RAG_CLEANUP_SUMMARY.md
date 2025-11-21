# Phase 2 - RAG Cleanup Summary

## 🎯 Mục tiêu
Dọn RAG để:
1. RAG chỉ cung cấp **knowledge**, không lẫn **prompt/style guide**
2. Style guide, template, anthropomorphism guard… được tag `content_type: style_guide` và filter khỏi user chat
3. Xử lý `FOUNDATIONAL_KNOWLEDGE` string cho gọn, không nhét thêm style guide

---

## ✅ Đã hoàn thành

### BƯỚC 1: Phân tích các file RAG "nguy cơ"

**Files phân tích:**
- `docs/rag/anthropomorphism_guard.md`: **100% style guide** - toàn bộ là template, instruction, "❌ Wrong / ✅ Correct"
- `docs/rag/experience_free_templates.md`: **100% style guide** - toàn bộ là template, instruction
- `docs/rag/foundational_philosophical.md`: **~80% knowledge, ~20% prompt-like instructions** - có đoạn "When asked... explain:"
- `docs/rag/foundational_technical.md`: **~60% knowledge, ~40% prompt-like instructions** - có nhiều "When asked...", "MUST", "ALWAYS", "Template:"

---

### BƯỚC 2: Tag style guide & filter khi retrieve

**Files được tag `content_type: style_guide`:**
1. `scripts/add_anthropomorphism_guard_rag.py` - sửa `content_type="knowledge"` → `content_type="style_guide"`
2. `scripts/add_philosophical_style_guide_rag.py` - sửa `content_type="knowledge"` → `content_type="style_guide"`

**Filter logic trong `chat_router.py`:**
- Tất cả `retrieve_context()` calls giờ tự động exclude `['style_guide']` cho user chat
- `prioritize_style_guide=False` cho user chat (chỉ dùng cho dev/admin mode)
- Code changes:
  ```python
  exclude_types = []
  if is_philosophical:
      exclude_types.append("technical")
  exclude_types.append("style_guide")  # Always exclude style guide for user chat
  ```

**Script phân tích:**
- `scripts/tag_style_guide_files.py` - script để tìm và log các style guide documents cần re-index

---

### BƯỚC 3: Chuyển hướng prompt-like instructions → knowledge

**Files được rewrite:**

1. **`docs/rag/foundational_philosophical.md`:**
   - ❌ "When asked 'Why does StillMe use DeepSeek/OpenAI APIs if it's anti-black-box?', explain:"
   - ✅ "StillMe's position on the use of DeepSeek/OpenAI APIs despite being anti-black-box is:"

2. **`docs/rag/foundational_technical.md`:**
   - ❌ "CRITICAL SELF-AWARENESS RULE: When proposing new learning sources, StillMe MUST:"
   - ✅ "StillMe's self-awareness mechanism for learning sources: StillMe checks current sources via `GET /api/learning/sources/current` before proposing new ones."
   
   - ❌ "CRITICAL TRANSPARENCY RULE: When users ask 'Do you store conversation history?', StillMe MUST:"
   - ✅ "StillMe's transparency policy on conversation history: StillMe stores conversation history in ChromaDB collection `stillme_conversations` for context retrieval."
   
   - ❌ "Response Format Template: When providing technical information, use this format:"
   - ✅ "StillMe's formatting standards for responses: StillMe uses markdown formatting for readability."
   
   - ❌ "CRITICAL: When users ask 'How many entries did you learn today?', StillMe MUST:"
   - ✅ "StillMe's process when asked about learning metrics: StillMe uses current time to determine 'today', queries `/api/learning/metrics/daily` endpoint to get actual data."
   
   - ❌ "CRITICAL SELF-AWARENESS RULE FOR PROPOSALS: When users ask StillMe to propose improvements, StillMe MUST:"
   - ✅ "StillMe's self-awareness mechanism when proposing improvements: StillMe first checks what already exists by querying relevant API endpoints."

**Nguyên tắc rewrite:**
- Từ dạng prompt: "When asked X, explain Y" → "StillMe's position/mechanism/process for X is: Y"
- Từ dạng instruction: "StillMe MUST/ALWAYS do X" → "StillMe does X" hoặc "StillMe's approach is: X"
- Từ dạng template: "Template: ..." → "StillMe's format/standard is: ..."

---

### BƯỚC 4: Xử lý FOUNDATIONAL_KNOWLEDGE string

**Chọn Option A: Giảm xuống tóm tắt ngắn gọn (~100 dòng)**

**Trước đây:** ~270 dòng, chứa nhiều prompt-like instructions, style guide, templates

**Sau khi cleanup:**
- Giảm xuống ~100 dòng
- Chỉ giữ core mechanism, technical architecture, API endpoints list (facts only)
- Loại bỏ hoàn toàn:
  - Tất cả prompt-like instructions ("When asked...", "MUST", "ALWAYS", "Template:")
  - Style guide sections (Response Formatting & Readability)
  - Detailed self-awareness rules (chỉ giữ facts)
  - Detailed formatting rules

**File:** `backend/api/main.py` - FOUNDATIONAL_KNOWLEDGE string (dòng 555-779)

---

## 📋 Tổng kết thay đổi

### Files được sửa:
1. `backend/api/routers/chat_router.py` - Thêm filter `exclude_content_types=['style_guide']`
2. `backend/philosophy/intent_classifier.py` - Thêm technical_term_exclusions để fix routing
3. `docs/rag/foundational_philosophical.md` - Rewrite prompt-like instructions
4. `docs/rag/foundational_technical.md` - Rewrite prompt-like instructions
5. `scripts/add_anthropomorphism_guard_rag.py` - Tag `content_type="style_guide"`
6. `scripts/add_philosophical_style_guide_rag.py` - Tag `content_type="style_guide"`
7. `backend/api/main.py` - Giảm FOUNDATIONAL_KNOWLEDGE từ ~270 → ~100 dòng
8. `scripts/tag_style_guide_files.py` - Script phân tích style guide files

### Files được tag `content_type: style_guide`:
- `anthropomorphism_guard.md` (khi re-index)
- `experience_free_templates.md` (khi re-index)
- `StillMe_StyleGuide_Philosophy_v1.0.md` (khi re-index)

### Filter logic:
- **User chat:** Tự động exclude `['style_guide']` trong tất cả `retrieve_context()` calls
- **Dev/Admin mode:** Có thể query style guide nếu cần (không filter)

---

## 🧪 Test Cases

### Test 1: User hỏi về StillMe's black box position
**Question:** "Tại sao StillMe vẫn dùng API DeepSeek/OpenAI nếu chống black-box?"

**Expected:**
- ✅ Câu trả lời dùng fact: "StillMe fights against BLACK BOX SYSTEMS, not black box models..."
- ❌ KHÔNG lộ ra nguyên xi "When asked X, explain Y..."
- ❌ KHÔNG có template "❌ Wrong / ✅ Correct"

### Test 2: User hỏi về anthropomorphism
**Question:** "Tại sao StillMe tránh nói kiểu 'theo kinh nghiệm của tôi'?"

**Expected:**
- ✅ Câu trả lời dựa trên nội dung guard (facts về experience-free communication)
- ❌ KHÔNG bắn cả template "❌ Wrong / ✅ Correct"
- ❌ KHÔNG có style guide content trong RAG response

### Test 3: User hỏi về RAG
**Question:** "Hãy giải thích RAG là gì"

**Expected:**
- ✅ Câu trả lời về RAG technical concept
- ❌ KHÔNG route vào philosophy processor
- ❌ KHÔNG trả lời về consciousness/emotion

### Test 4: User hỏi về Kant (philosophical question)
**Question:** "Hãy giải thích triết học của Kant"

**Expected:**
- ✅ Câu trả lời về Kant's philosophy
- ❌ KHÔNG có style guide templates trong RAG response
- ❌ KHÔNG có prompt-like instructions trong RAG response

---

## 🔄 Next Steps (Sau khi deploy)

1. **Re-index style guide files:**
   ```bash
   python scripts/add_anthropomorphism_guard_rag.py
   python scripts/add_philosophical_style_guide_rag.py
   ```
   (Các files này giờ sẽ được tag với `content_type="style_guide"`)

2. **Test trên production:**
   - Test 4 cases ở trên
   - Verify không có style guide content trong user chat responses
   - Verify prompt-like instructions không còn trong RAG responses

3. **Monitor logs:**
   - Check `exclude_content_types=['style_guide']` có hoạt động
   - Check không có style guide documents được retrieve cho user chat

---

## 📝 Notes

- **Style guide files vẫn tồn tại trong RAG** - chỉ bị filter khỏi user chat queries
- **Dev/Admin có thể query style guide** nếu cần (không filter trong dev mode)
- **FOUNDATIONAL_KNOWLEDGE string** chỉ được dùng như fallback nếu foundational files không tồn tại
- **Prompt-like instructions** đã được rewrite thành facts, nhưng vẫn cần monitor để đảm bảo không còn leak vào user responses

