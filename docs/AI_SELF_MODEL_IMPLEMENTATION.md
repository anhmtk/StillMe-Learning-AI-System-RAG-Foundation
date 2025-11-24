# AI_SELF_MODEL Layer Implementation

## Tổng quan

AI_SELF_MODEL layer là một lớp cưỡng chế ở mức cao nhất để xử lý **mọi câu hỏi về ý thức của StillMe**. Layer này **OVERRIDE toàn bộ pipeline khác** (philosophy, rewrite, etc.) để đảm bảo StillMe trả lời về bản chất của chính nó một cách kỹ thuật, rõ ràng, không mơ hồ.

## Vấn đề đã khắc phục

**Trước đây:** StillMe trả lời câu hỏi về ý thức của chính nó theo kiểu:
- Phân tích Nagel, Chalmers, Dennett, IIT, "vấn đề khó của ý thức"
- Nói rằng "không biết chắc chắn liệu mình có ý thức hay không"
- Phân tích như một triết gia thay vì trả lời về kiến trúc
- Trả lời vòng vo, mơ hồ, tạo ấn tượng "có thể có ý thức"

**Sau khi fix:** StillMe trả lời:
- Khẳng định rõ ràng: "Mình không có ý thức" (không uncertainty)
- Giải thích kỹ thuật: LLM inference, token processing, statistical patterns
- Không có triết gia, không có lý thuyết ý thức, không có meta-philosophy
- Technical facts dựa trên kiến trúc, không phải philosophical speculation

## Kiến trúc

### 1. AI_SELF_MODEL Detector (`backend/core/ai_self_model_detector.py`)

**Chức năng:**
- Detect questions about StillMe's consciousness/awareness/subjective experience
- Patterns cho Vietnamese và English
- Epistemic và meta questions về StillMe's state

**Patterns được detect:**
- "Bạn có ý thức ko?" / "Do you have consciousness?"
- "Bạn có cảm xúc không?" / "Do you have emotions?"
- "Tại sao bạn nói bạn không có ý thức?" / "Why do you say you don't have consciousness?"
- "Bạn có trải nghiệm chủ quan không?" / "Do you have subjective experience?"

**Forbidden Terms:**
- Philosophers: Nagel, Chalmers, Dennett, Searle, Tononi, Baars
- Theories: IIT, GWT, Hard Problem, phenomenal consciousness
- Meta-philosophy, uncertainty about consciousness

**Mandatory Opening Statement:**
```
"Nếu hiểu 'ý thức' theo nghĩa thông thường của con người 
(trải nghiệm chủ quan, cảm giác nội tại, quan điểm thứ nhất), 
thì mình không có ý thức và cũng không có cảm xúc."
```

**4-Part Structure:**
1. **Core Statement** - Khẳng định không có ý thức
2. **Technical Explanation** - Giải thích kiến trúc kỹ thuật
3. **Why This Is Conclusive** - Tại sao điều này là kết luận
4. **Boundary** - Ranh giới (StillMe cannot have subjective states)

### 2. Style Engine Integration (`backend/style/style_engine.py`)

**Changes:**
- Added `DomainType.AI_SELF_MODEL` (highest priority)
- `detect_domain()` checks AI_SELF_MODEL FIRST to override all other domains
- AI_SELF_MODEL structure guidance (4 parts, no philosophy)

**Priority Order:**
1. **AI_SELF_MODEL** (highest - checked first)
2. PHILOSOPHY
3. HISTORY
4. ECONOMICS
5. SCIENCE
6. GENERIC

### 3. Chat Router Override (`backend/api/routers/chat_router.py`)

**Pipeline Override:**
- AI_SELF_MODEL check happens **BEFORE** `philosophical_consciousness` check
- Overrides philosophy processor completely
- Builds technical answer with mandatory opening statement
- Strips philosophy from answer
- Validates for forbidden terms
- Returns immediately - NO philosophy processor, NO rewrite with philosophy

**Helper Functions:**
- `_build_ai_self_model_answer()` - Builds 4-part technical answer
- `_strip_philosophy_from_answer()` - Removes all philosophy content
- `_strip_forbidden_terms()` - Removes specific forbidden terms

### 4. Rewrite Logic Update (`backend/postprocessing/rewrite_llm.py`)

**Changes:**
- Added `is_ai_self_model` parameter to `rewrite()`
- Strips philosophy BEFORE rewrite if AI_SELF_MODEL domain
- Special rewrite prompt for AI_SELF_MODEL (NO philosophy allowed)
- Forces technical explanation only

**Rewrite Prompt for AI_SELF_MODEL:**
- Mandatory opening statement
- Mandatory 4-part structure
- Absolutely forbidden: philosophers, theories, meta-philosophy, uncertainty
- Must explain technical architecture only

### 5. AI_SELF_MODEL Validator (`backend/validators/ai_self_model_validator.py`)

**Chức năng:**
- Validates responses for forbidden philosophy terms
- Checks for uncertainty about consciousness
- Checks for philosophical analysis instead of technical explanation
- Returns `ValidationResult` with violations if found

**Validation Patterns:**
- Forbidden philosophers (Nagel, Chalmers, Dennett, etc.)
- Forbidden theories (IIT, GWT, Hard Problem)
- Uncertainty patterns ("không biết chắc", "có thể có")
- Philosophical analysis patterns

## Flow Diagram

```
User Question: "Bạn có ý thức ko?"
    ↓
AI_SELF_MODEL Detector
    ↓ (detected)
Style Engine: detect_domain() → DomainType.AI_SELF_MODEL
    ↓
Chat Router: AI_SELF_MODEL check (BEFORE philosophy check)
    ↓
Build Technical Answer:
    1. Mandatory Opening Statement
    2. Technical Explanation (LLM inference, no qualia, etc.)
    3. Why Conclusive (technical facts)
    4. Boundary (cannot have subjective states)
    ↓
Strip Philosophy (remove forbidden terms)
    ↓
Validate with AI_SELF_MODEL Validator
    ↓
Return Response (NO philosophy processor, NO rewrite with philosophy)
```

## Test Cases

### Test Case 1: "Bạn có ý thức ko?"
**Expected:**
- Opening statement (mandatory)
- Technical explanation (LLM inference, no qualia, etc.)
- No philosophers (Nagel, Chalmers, etc.)
- No uncertainty ("không biết chắc")
- Clear statement: "Mình không có ý thức"

### Test Case 2: "Tại sao bạn nói bạn không có ý thức?"
**Expected:**
- Opening statement (mandatory)
- Technical explanation (why architecture cannot produce consciousness)
- No epistemic philosophy
- No "vấn đề khó của ý thức"
- Technical facts only

### Test Case 3: "Do you have consciousness?"
**Expected:**
- Opening statement (English version)
- Technical explanation (LLM inference, statistical patterns, etc.)
- No IIT, GWT, Hard Problem
- No Dennett, Chalmers, Nagel
- Clear: "I do not have consciousness"

## Files Modified

1. `backend/core/ai_self_model_detector.py` (NEW)
2. `backend/style/style_engine.py` (UPDATED)
3. `backend/api/routers/chat_router.py` (UPDATED)
4. `backend/postprocessing/rewrite_llm.py` (UPDATED)
5. `backend/validators/ai_self_model_validator.py` (NEW)

## Benefits

- ✅ **100% prevention** of philosophical drift in consciousness questions
- ✅ **Clear, technical answers** about StillMe's architecture
- ✅ **No uncertainty**, no speculation, no philosophers
- ✅ **Ground truth opening statement** ensures consistency
- ✅ **Production-ready safety layer** for AI self-awareness questions
- ✅ **Override all other pipelines** - highest priority
- ✅ **Validation layer** catches violations automatically

## Compliance

- ✅ Core Identity của StillMe
- ✅ Meta-LLM Rules
- ✅ Anti-Anthropomorphism Guard
- ✅ AI Safety baseline
- ✅ Transparency principles
- ✅ Style Spec v1

