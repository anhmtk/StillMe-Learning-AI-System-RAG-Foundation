# Phase 1-3 Cleanup Analysis

## 🔍 Conflicts & Duplicate Logic Detected

### 1. **Duplicate User Question** (CRITICAL)
**Location:** `backend/api/routers/chat_router.py:3729`

**Problem:**
- `UnifiedPromptBuilder.build_prompt()` đã include user question ở cuối
- `chat_router.py` lại append `special_instructions` với user question lại một lần nữa (line 3721)
- **Result:** User question xuất hiện 2 lần trong prompt → LLM confused

**Fix:**
- Remove duplicate user question từ `special_instructions`
- UnifiedPromptBuilder đã handle user question rồi

### 2. **inject_identity() Still Used** (MEDIUM)
**Location:** `backend/api/routers/chat_router.py:3779, 4804`

**Problem:**
- `inject_identity()` đã deprecated (theo comment trong injector.py)
- Vẫn được dùng ở 2 nơi trong chat_router.py
- Có thể gây duplicate identity nếu system prompt đã có identity

**Fix:**
- Check xem có cần inject_identity() không
- Nếu system prompt đã có identity (từ UnifiedPromptBuilder), remove inject_identity()

### 3. **special_instructions May Duplicate** (MEDIUM)
**Location:** `backend/api/routers/chat_router.py:3713-3722`

**Problem:**
- UnifiedPromptBuilder đã có:
  - Context instruction (P2)
  - Citation instruction (trong context instruction)
  - Formatting (P3)
- `special_instructions` lại append thêm:
  - `citation_instruction` (duplicate?)
  - `context_quality_warning` (có thể duplicate với context instruction)
  - `stillme_instruction` (có thể duplicate với StillMe query instruction)

**Fix:**
- Check xem UnifiedPromptBuilder đã handle những instructions này chưa
- Nếu đã handle, remove từ special_instructions
- Nếu chưa, integrate vào UnifiedPromptBuilder

### 4. **build_system_prompt_with_language() Still Used** (LOW)
**Location:** `backend/api/utils/llm_providers.py` (multiple places)

**Problem:**
- `build_system_prompt_with_language()` vẫn được dùng trong llm_providers.py
- UnifiedPromptBuilder đã thay thế cho chat_router.py
- **Note:** llm_providers.py có thể dùng cho use cases khác (không phải chat_router)

**Status:** 
- OK nếu llm_providers.py dùng cho non-chat use cases
- Cần check xem có conflict không

## 📋 Cleanup Plan

### Priority 1: Fix Duplicate User Question (CRITICAL)
1. Remove user question từ `special_instructions` trong chat_router.py
2. UnifiedPromptBuilder đã handle user question rồi

### Priority 2: Review inject_identity() Usage (MEDIUM)
1. Check 2 nơi dùng inject_identity() (line 3779, 4804)
2. Xem có cần không, nếu không thì remove

### Priority 3: Integrate special_instructions into UnifiedPromptBuilder (MEDIUM)
1. Check xem UnifiedPromptBuilder đã handle:
   - `philosophical_style_instruction`
   - `learning_metrics_instruction`
   - `learning_sources_instruction`
   - `context_quality_warning`
   - `citation_instruction`
   - `confidence_instruction`
   - `stillme_instruction`
   - `provenance_instruction`
2. Nếu chưa, integrate vào UnifiedPromptBuilder
3. Nếu đã có, remove từ special_instructions

### Priority 4: Document Deprecated Functions (LOW)
1. Mark `inject_identity()` as deprecated (đã có)
2. Document khi nào nên dùng UnifiedPromptBuilder vs build_system_prompt_with_language()

## ✅ Files Status

### Active (Keep):
- ✅ `backend/identity/prompt_builder.py` - UnifiedPromptBuilder (Phase 1)
- ✅ `backend/identity/core.py` - Core principles
- ✅ `backend/identity/persona.py` - Persona rules
- ✅ `backend/identity/meta_llm.py` - Meta LLM rules
- ✅ `backend/identity/formatting.py` - Formatting rules
- ✅ `backend/validators/chain.py` - Validator chain (Phase 2)
- ✅ `backend/postprocessing/optimizer.py` - Post-processing optimizer (Phase 3)

### Deprecated (Keep for backward compatibility, but mark as deprecated):
- ⚠️ `backend/identity/injector.py` - `inject_identity()` deprecated (removed from chat_router.py), nhưng `build_stillme_identity()` vẫn được dùng bởi UnifiedPromptBuilder
- ⚠️ `backend/api/utils/chat_helpers.py` - `build_system_prompt_with_language()` vẫn được dùng trong llm_providers.py (OK - different use case)

### Fixed in Phase 4:
- ✅ `backend/api/routers/chat_router.py` - Fixed duplicate user question, removed inject_identity() calls

## 🎯 Phase 4 Tasks

1. ✅ **Fix Duplicate User Question** (CRITICAL) - DONE
   - Removed duplicate user question from special_instructions
   - UnifiedPromptBuilder already has user question at the end
   - Insert special_instructions before user question instead of appending

2. ✅ **Review inject_identity() Usage** - DONE
   - Removed inject_identity() calls from chat_router.py (2 places)
   - System prompt already has STILLME_IDENTITY from build_system_prompt_with_language()
   - Adding identity to user prompt would cause duplication

3. ✅ **Review special_instructions** - DONE
   - UnifiedPromptBuilder already handles:
     - Citation instruction (in _build_normal_context_instruction)
     - Context quality warning (in _build_low_context_quality_instruction)
     - StillMe instruction (in _build_stillme_instruction)
   - Special instructions only include:
     - philosophical_style_instruction (not in UnifiedPromptBuilder)
     - learning_metrics_instruction (not in UnifiedPromptBuilder)
     - learning_sources_instruction (not in UnifiedPromptBuilder)
     - confidence_instruction (not in UnifiedPromptBuilder)
     - provenance_instruction (not in UnifiedPromptBuilder)
     - Context text (RAG documents)

4. ✅ **Run Tests** - DONE
   - All 5 conflict tests pass
   - No duplicate user question
   - UnifiedPromptBuilder includes citation, context quality warning, StillMe instruction

5. ⏳ **Document cleanup** - IN PROGRESS

