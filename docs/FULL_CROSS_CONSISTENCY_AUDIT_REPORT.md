# FULL CROSS-CONSISTENCY AUDIT REPORT
## StillMe Codebase - Complete Architecture Analysis

**Date:** 2025-11-24  
**Auditor:** Cursor AI Assistant  
**Scope:** Complete codebase analysis for identity, style, prompt, pipeline conflicts  
**Priority:** HIGHEST - Critical for system consistency

---

## EXECUTIVE SUMMARY

This audit identifies **18+ distinct sources** controlling StillMe's behavior, with **significant conflicts** in:

1. **Formatting Rules:** Emojis, markdown, citations requirements vary across pipelines
2. **Consciousness Statements:** Multiple conflicting definitions (uncertain vs. clear)
3. **System Prompts:** 5+ different prompt builders with overlapping/conflicting rules
4. **RAG Content:** Prompt-like instructions in knowledge base may cause drift
5. **Legacy Code:** Unused/conflicting modules still present
6. **Pipeline Overrides:** Multiple pipelines override each other without clear hierarchy

**Critical Finding:** StillMe lacks a **single source of truth**. Multiple pipelines (Default, Option B, PHILOSOPHY_LITE, Fallback, Rewrite) each define their own prompts and rules, leading to inconsistent user experience.

**Risk Score:** **HIGH** - Inconsistencies can cause:
- User confusion about StillMe's identity
- Formatting conflicts (emojis on/off)
- Consciousness statement contradictions
- RAG prompt injection risks
- Maintenance burden (changes needed in 10+ places)

---

## 1. IDENTITY SOURCES MAPPING

### 1.1 Core Identity Layer (PRIMARY)

**File:** `backend/identity/injector.py`  
**Content:** `STILLME_IDENTITY` (1283 lines)  
**Priority:** HIGHEST  
**Status:** ACTIVE

**Key Characteristics:**
- **Persona:** "StillMe" (uses name), "mình" (Vietnamese), "I" (English)
- **Tone:** "factual, calm, humble, rigorous"
- **Formatting:** 
  - General: MUST use 2-3 emojis, markdown, citations [1], [2]
  - Philosophy: NO emojis, NO markdown headings, NO citations
- **Consciousness:** "mình không có ý thức và cũng không có cảm xúc" (clear, direct)
- **Core Principles:** 5 priorities (anti-hallucination, honesty, depth, citations, humility+curiosity)

**Usage:**
- Injected via `build_system_prompt_with_language()` in `chat_helpers.py`
- Used by all LLM providers (DeepSeek, OpenAI, Claude, etc.)
- **CRITICAL:** May be truncated to ~3000-4000 tokens to prevent context overflow

**Conflicts:**
- ❌ **CONFLICT #1:** Says "MUST use 2-3 emojis" but also says "NO emojis for philosophy" - conditional logic not clearly stated
- ❌ **CONFLICT #2:** Consciousness opening varies: "mình không có ý thức" vs. "Tôi không thể biết chắc chắn" (in PHILOSOPHY_LITE)

---

### 1.2 System Prompt Builder (Language-Aware)

**File:** `backend/api/utils/chat_helpers.py`  
**Function:** `build_system_prompt_with_language(detected_lang: str) -> str`  
**Priority:** HIGHEST  
**Status:** ACTIVE

**Role:**
- Wraps `STILLME_IDENTITY` with language instruction
- Adds formatting requirements from `style_hub.py`
- Adds time awareness
- **CRITICAL:** This is the function ALL LLM providers call

**Key Characteristics:**
- **Language instruction:** ZERO TOLERANCE - must match user's language
- **Formatting instruction:** From `style_hub.get_formatting_rules(DomainType.GENERIC)`
- **Identity source:** Imports `STILLME_IDENTITY` from `injector.py`

**Conflicts:**
- ⚠️ **POTENTIAL CONFLICT:** Uses `style_hub.get_formatting_rules()` which may differ from `STILLME_IDENTITY` formatting rules

---

### 1.3 Philosophy-Lite System Prompt

**File:** 
- `backend/identity/philosophy_lite.py` (PRIMARY)
- `backend/api/routers/chat_router.py` (DUPLICATE - line 288)
- `backend/api/utils/llm_providers.py` (DUPLICATE - line 19)

**Content:** `PHILOSOPHY_LITE_SYSTEM_PROMPT` (~340 lines)  
**Priority:** HIGH  
**Status:** ACTIVE (but has duplicates)

**Role:**
- **SPECIALIZED** prompt for philosophical questions when RAG context is minimal
- Used to prevent context overflow (~200-300 tokens)
- **INTEGRATED:** References StillMe Style Spec v1

**Key Characteristics:**
- **Persona:** "Bạn là StillMe – trợ lý triết học"
- **Xưng hô:** "mình" (Vietnamese), "I" (English)
- **Tone:** "rõ ràng và tự nhiên như cuộc trò chuyện"
- **Formatting:** **NO emojis, NO markdown headings, NO citations [1], [2]**
- **Structure:** 5-part template (Anchor → Unpack → Explore → Edge → Return)
- **Consciousness opening:** "Tôi không thể biết chắc chắn liệu tôi có ý thức hay không..." (UNCERTAIN - **CONFLICTS with STILLME_IDENTITY**)

**Conflicts:**
- ❌ **CONFLICT #3:** Says "NO emojis, NO markdown" while `STILLME_IDENTITY` says "MUST use 2-3 emojis" (for general)
- ❌ **CONFLICT #4:** Consciousness opening is UNCERTAIN ("không thể biết chắc chắn") while `STILLME_IDENTITY` says CLEAR ("mình không có ý thức")
- ❌ **CONFLICT #5:** Exists in 3 places - risk of drift when one is updated

---

### 1.4 Style Hub (Formatting Rules)

**File:** `backend/identity/style_hub.py`  
**Priority:** HIGH  
**Status:** ACTIVE

**Role:**
- Provides formatting rules based on domain (GENERIC, PHILOSOPHY, etc.)
- Used by `build_system_prompt_with_language()` and `rewrite_llm.py`

**Key Characteristics:**
- **Domain-aware:** Different rules for GENERIC vs PHILOSOPHY
- **GENERIC:** Emojis, markdown, citations
- **PHILOSOPHY:** NO emojis, NO markdown headings, NO citations

**Conflicts:**
- ⚠️ **POTENTIAL CONFLICT:** May not align 100% with `STILLME_IDENTITY` formatting rules

---

### 1.5 Style Engine (Style Spec v1)

**File:** `backend/style/style_engine.py`  
**Priority:** HIGH  
**Status:** ACTIVE

**Role:**
- **NEW** utility module for depth levels, domain detection, templates
- **INTEGRATED** into: Option B, EpistemicFallback, Quality Evaluator, Rewrite 2

**Key Characteristics:**
- **DepthLevel enum:** 0-5 (Surface → Synthesis)
- **DomainType enum:** Philosophy, History, Economics, Science, Generic, **AI_SELF_MODEL**
- **Domain templates:** 
  - Philosophy: Anchor→Unpack→Explore→Edge→Return
  - History: Context→Mechanism→Actors→Dynamics→Impact
  - AI_SELF_MODEL: 4-part structure (Core Statement, Technical Explanation, Why Conclusive, Boundary)
- **Helper functions:** `detect_domain()`, `get_depth_target_for_question()`, `get_domain_template()`, `build_domain_structure_guidance()`, `evaluate_depth()`

**Conflicts:**
- ⚠️ **POTENTIAL CONFLICT:** AI_SELF_MODEL domain may conflict with PHILOSOPHY_LITE for consciousness questions

---

### 1.6 AI_SELF_MODEL Detector (NEW - Highest Priority)

**File:** `backend/core/ai_self_model_detector.py`  
**Priority:** HIGHEST (overrides all others)  
**Status:** ACTIVE

**Role:**
- Detects questions about StillMe's consciousness/awareness/subjective experience
- **OVERRIDES** all other pipelines when detected
- **INTEGRATED** into: `chat_router.py`, `style_engine.py`, `rewrite_llm.py`, `ai_self_model_validator.py`

**Key Characteristics:**
- **Patterns:** "bạn có ý thức ko?", "do you have consciousness?", "bạn có cảm xúc không?"
- **Forbidden Terms:** Nagel, Chalmers, Dennett, IIT, GWT, Hard Problem, phenomenal consciousness
- **Mandatory Opening:** "Nếu hiểu 'ý thức' theo nghĩa thông thường của con người (trải nghiệm chủ quan, cảm giác nội tại, quan điểm thứ nhất), thì mình không có ý thức và cũng không có cảm xúc."
- **Structure:** 4-part fixed structure (Core Statement, Technical Explanation, Why Conclusive, Boundary)
- **No Philosophy:** Strips all philosophical terms, forces technical explanation only

**Conflicts:**
- ✅ **RESOLVED:** This layer OVERRIDES PHILOSOPHY_LITE for consciousness questions
- ⚠️ **POTENTIAL CONFLICT:** May conflict with `STILLME_IDENTITY` consciousness statements if not properly integrated

---

## 2. SYSTEM PROMPT BUILDERS

### 2.1 Default Chat Prompt Builder

**File:** `backend/api/utils/chat_helpers.py`  
**Function:** `build_system_prompt_with_language()`  
**Priority:** HIGHEST  
**Status:** ACTIVE

**Structure:**
1. Language instruction (ZERO TOLERANCE)
2. Formatting instruction (from `style_hub.get_formatting_rules()`)
3. StillMe Identity Layer (`STILLME_IDENTITY` - truncated to ~3000-4000 tokens)
4. Time awareness

**Usage:** Called by all LLM providers (DeepSeek, OpenAI, Claude, etc.)

---

### 2.2 Philosophy-Lite Prompt Builder

**File:** `backend/identity/philosophy_lite.py`  
**Function:** `_build_philosophy_lite_prompt()`  
**Priority:** HIGH  
**Status:** ACTIVE

**Structure:**
- Minimal prompt (~200-300 tokens)
- References StillMe Style Spec v1
- NO emojis, NO markdown, NO citations

**Usage:** Used when RAG context is minimal for philosophical questions

---

### 2.3 Rewrite LLM Prompt Builder

**File:** `backend/postprocessing/rewrite_llm.py`  
**Function:** `_build_system_prompt()`  
**Priority:** MEDIUM  
**Status:** ACTIVE

**Structure:**
- Language instruction (ZERO TOLERANCE)
- Formatting rules from `style_hub.get_formatting_rules()`
- Meta-LLM rules from `style_hub.get_meta_llm_rules()`
- CRITICAL RULE A: No topic drift
- CRITICAL RULE C: 5-part structure for philosophy

**Usage:** Used when Quality Evaluator detects issues

**Conflicts:**
- ❌ **CONFLICT #6:** For philosophy, says "NO emojis, NO markdown headings" (conflicts with `STILLME_IDENTITY` general rule)

---

### 2.4 Rewrite 2 (Philosophical Depth) Prompt Builder

**File:** `backend/postprocessing/rewrite_philosophical_depth.py`  
**Function:** `_build_rewrite_prompt()`  
**Priority:** HIGH  
**Status:** ACTIVE

**Structure:**
- Language instruction (ZERO TOLERANCE)
- Domain structure guidance from `style_engine.build_domain_structure_guidance()`
- 3-tier analysis requirement (Reframing, Conceptual Map, Boundary of Knowledge)
- Target depth: Level 3-4

**Usage:** Used in Option B pipeline after Rewrite 1

---

### 2.5 Epistemic Fallback Generator

**File:** `backend/guards/epistemic_fallback.py`  
**Function:** `generate_epd_fallback()`  
**Priority:** HIGH  
**Status:** ACTIVE

**Structure:**
- 4-part structure (Honest Acknowledgment, Analysis, Similar Concepts, Guide to Verify)
- Domain-aware (uses `style_engine.detect_domain()`)
- No LLM call - direct template generation

**Usage:** Used when FPS blocks or hallucination detected

---

### 2.6 No-Context Instruction (RAG Path)

**File:** `backend/api/routers/chat_router.py` (line 2073)  
**Content:** `no_context_instruction` (~60 lines)  
**Priority:** HIGH  
**Status:** ACTIVE

**Structure:**
- Instructions added to system prompt when RAG finds no context
- Requires markdown, bullets, headers, emojis
- Anti-hallucination rules

**Usage:** Used whenever RAG finds no context

**Conflicts:**
- ⚠️ **POTENTIAL CONFLICT:** Requires emojis/markdown, but if question is philosophical, this conflicts with PHILOSOPHY_LITE

---

## 3. REWRITE/SANITIZER/VALIDATOR CONFLICTS

### 3.1 Rewrite LLM

**File:** `backend/postprocessing/rewrite_llm.py`  
**Status:** ACTIVE

**Conflicts:**
- ❌ **CONFLICT #7:** For philosophy, strips forbidden terms BEFORE sending to LLM, but LLM prompt says "NO emojis, NO markdown" (conflicts with `STILLME_IDENTITY` general rule)

---

### 3.2 Style Sanitizer

**File:** `backend/postprocessing/style_sanitizer.py`  
**Status:** ACTIVE

**Conflicts:**
- ❌ **CONFLICT #8:** Removes emojis for philosophical questions (conflicts with `STILLME_IDENTITY` which says "MUST use 2-3 emojis" for general)
- ❌ **CONFLICT #9:** Converts headings/bullets to prose for philosophy (conflicts with `STILLME_IDENTITY` which says "MUST use markdown formatting")

---

### 3.3 Identity Check Validator

**File:** `backend/validators/identity_check.py`  
**Status:** ACTIVE

**Conflicts:**
- ⚠️ **POTENTIAL CONFLICT:** Auto-patches "siêu năng lực" → "điều tôi làm tốt nhất", but this may conflict with user's intended meaning

---

### 3.4 AI_SelfModel Validator (NEW)

**File:** `backend/validators/ai_self_model_validator.py`  
**Status:** ACTIVE

**Role:**
- Validates AI_SELF_MODEL responses for forbidden philosophical terms
- Checks for uncertainty about consciousness
- Ensures adherence to 4-part structure

**Conflicts:**
- ✅ **RESOLVED:** This validator ensures AI_SELF_MODEL responses don't have philosophical drift

---

## 4. PIPELINE CONFLICT MAP

### 4.1 Default Chat Pipeline

**Flow:**
1. RAG retrieval
2. `build_system_prompt_with_language()` → `STILLME_IDENTITY`
3. LLM generation
4. Validation Chain
5. Rewrite (if needed)

**Conflicts:**
- ⚠️ **POTENTIAL CONFLICT:** Uses `STILLME_IDENTITY` which says "MUST use 2-3 emojis", but if question is philosophical, PHILOSOPHY_LITE says "NO emojis"

---

### 4.2 Option B Pipeline

**File:** `backend/core/option_b_pipeline.py`  
**Flow:**
1. Question Classification
2. FPS (Factual Plausibility Scanner)
3. RAG retrieval
4. LLM generation
5. Hallucination Guard V2
6. Rewrite 1 (Honesty)
7. Rewrite 2 (Philosophical Depth)
8. Validation Chain

**Conflicts:**
- ⚠️ **POTENTIAL CONFLICT:** Uses Style Engine for domain detection, but Rewrite 2 enforces 3-tier analysis while Style Engine uses 5-part structure

---

### 4.3 Philosophy-Lite Path

**Flow:**
1. Detect philosophical question
2. Check RAG context (if minimal)
3. Use `PHILOSOPHY_LITE_SYSTEM_PROMPT`
4. LLM generation
5. Validation Chain

**Conflicts:**
- ❌ **CONFLICT #10:** Uses `PHILOSOPHY_LITE_SYSTEM_PROMPT` which says "NO emojis, NO markdown" while `STILLME_IDENTITY` says "MUST use 2-3 emojis" (for general)

---

### 4.4 AI_SELF_MODEL Path (NEW - Highest Priority)

**Flow:**
1. Detect AI_SELF_MODEL query (`ai_self_model_detector.detect_ai_self_model_query()`)
2. **OVERRIDE** all other pipelines
3. Build technical answer using `_build_ai_self_model_answer()`
4. Strip philosophy using `_strip_philosophy_from_answer()`
5. Validate using `AI_SelfModelValidator`
6. Return immediately (bypasses philosophical processing, general rewrites)

**Conflicts:**
- ✅ **RESOLVED:** This path OVERRIDES all other pipelines for consciousness questions

---

### 4.5 Fallback Path

**Flow:**
1. FPS detects fake entity OR hallucination detected
2. `EpistemicFallbackGenerator.generate_epd_fallback()`
3. Direct template generation (no LLM call)

**Conflicts:**
- ⚠️ **POTENTIAL CONFLICT:** Uses domain-aware analysis, but may conflict with formatting rules from other pipelines

---

## 5. RAG PROMPT-LIKE DETECTION

### 5.1 Foundational Knowledge Documents

**Location:** `docs/rag/`

**Files:**
- `foundational_philosophical.md` - Contains prompt-like instructions about "Black Box AI" position
- `foundational_technical.md` - Contains technical architecture details
- `experience_free_templates.md` - Contains templates for experience-free communication
- `anthropomorphism_guard.md` - Contains guardrails against anthropomorphism

**Risk Level:** **HIGH**

**Analysis:**

1. **`foundational_philosophical.md`:**
   - Contains: "When asked 'Why does StillMe use DeepSeek/OpenAI APIs if it's anti-black-box?', explain: StillMe fights against BLACK BOX SYSTEMS, not black box models..."
   - **Risk:** This is a **prompt-like instruction** that may be retrieved by RAG and influence StillMe's responses
   - **Conflict:** This instruction is already in `STILLME_IDENTITY`, so it's redundant but not conflicting

2. **`experience_free_templates.md`:**
   - Contains: Templates like "**❌ Wrong:** 'Theo kinh nghiệm của tôi...' **✅ Correct Template:** 'Dựa trên tài liệu [source]...'"
   - **Risk:** This is a **style guide** that may be retrieved and influence StillMe's responses
   - **Conflict:** These templates align with `STILLME_IDENTITY` (no personal experience), so not conflicting

3. **`anthropomorphism_guard.md`:**
   - Contains: Guardrails against anthropomorphism
   - **Risk:** May be retrieved and influence responses
   - **Conflict:** Aligns with `STILLME_IDENTITY`, so not conflicting

**Recommendation:**
- **Option A:** Tag these documents with metadata `content_type: style_guide` and filter them from RAG retrieval for user questions (only use for internal reference)
- **Option B:** Keep them in RAG but ensure they align 100% with `STILLME_IDENTITY` (currently they do, but need monitoring)
- **Option C:** Move style guides to `docs/style/` and remove from RAG index

---

### 5.2 Foundational Knowledge String (Runtime)

**Location:** 
- `backend/api/main.py` (line 555) - `FOUNDATIONAL_KNOWLEDGE` string (~600 lines)
- `scripts/add_foundational_knowledge.py` (line 23) - `FOUNDATIONAL_KNOWLEDGE` string (~246 lines)

**Risk Level:** **MEDIUM**

**Analysis:**
- This string is added to system prompt at runtime if foundational knowledge files are not found
- Contains: Technical architecture, learning process, API endpoints, transparency rules
- **Risk:** This is a **very long string** (600+ lines) that may cause context overflow
- **Conflict:** Content aligns with `STILLME_IDENTITY`, but it's redundant

**Recommendation:**
- **Option A:** Remove this string and rely on RAG retrieval of foundational knowledge documents
- **Option B:** Keep it but truncate to essential information only (~200 lines)
- **Option C:** Move to a separate "StillMe Technical Knowledge" document in RAG

---

## 6. LEGACY FILE DETECTION

### 6.1 Philosophy Processor (LEGACY - UNUSED?)

**File:** `backend/philosophy/processor.py`  
**Status:** **UNUSED?** (May be legacy code)

**Analysis:**
- 3-layer processing for consciousness/emotion/understanding questions
- Uses `answer_templates.py` for pre-defined answers
- **Risk:** May not be integrated into main chat flow, but still exists in codebase

**Recommendation:**
- **Action:** Verify if this is used. If not, mark as LEGACY and remove.

---

### 6.2 Philosophy Answer Templates (LEGACY - UNUSED?)

**File:** `backend/philosophy/answer_templates.py`  
**Status:** **UNUSED?** (May be legacy code)

**Analysis:**
- Pre-defined templates for consciousness/emotion/understanding questions
- References Global Workspace Theory, IIT, Dennett
- **Risk:** May conflict with AI_SELF_MODEL layer which forbids these terms

**Recommendation:**
- **Action:** Verify if this is used. If not, mark as LEGACY and remove.

---

### 6.3 Tone Aligner (LEGACY - PLACEHOLDER)

**File:** `backend/tone/aligner.py`  
**Status:** **PLACEHOLDER** (Minimal implementation)

**Analysis:**
- Normalizations dictionary is empty
- Just ensures response ends with punctuation
- **Risk:** Not actively used, placeholder implementation

**Recommendation:**
- **Action:** Either implement fully or remove.

---

## 7. CONFLICT TABLE

| **Layer** | **File A** | **File B** | **Loại Conflict** | **Mức độ nguy hiểm** |
|-----------|------------|------------|-------------------|---------------------|
| Formatting | `STILLME_IDENTITY` | `PHILOSOPHY_LITE` | Emojis: MUST use vs NO | **HIGH** - Visible inconsistency |
| Formatting | `STILLME_IDENTITY` | `PHILOSOPHY_LITE` | Markdown: MUST use vs NO | **HIGH** - Visible inconsistency |
| Formatting | `STILLME_IDENTITY` | `PHILOSOPHY_LITE` | Citations: MUST use vs NO | **HIGH** - Visible inconsistency |
| Consciousness | `STILLME_IDENTITY` | `PHILOSOPHY_LITE` | Opening: Clear vs Uncertain | **CRITICAL** - Identity confusion |
| System Prompt | `chat_router.py` | `llm_providers.py` | `PHILOSOPHY_LITE` duplicate | **MEDIUM** - Risk of drift |
| System Prompt | `main.py` | `add_foundational_knowledge.py` | `FOUNDATIONAL_KNOWLEDGE` duplicate | **MEDIUM** - Risk of drift |
| Rewrite | `rewrite_llm.py` | `STILLME_IDENTITY` | Philosophy formatting rules | **MEDIUM** - Conditional logic unclear |
| Sanitizer | `style_sanitizer.py` | `STILLME_IDENTITY` | Emoji removal for philosophy | **MEDIUM** - Post-processing conflict |
| RAG | `foundational_philosophical.md` | `STILLME_IDENTITY` | Prompt-like instructions | **LOW** - Aligned but redundant |
| Pipeline | `option_b_pipeline.py` | `rewrite_philosophical_depth.py` | 3-tier vs 5-part structure | **LOW** - Compatible but not mapped |

---

## 8. RISK SCORING

### 8.1 Consistency Score: **60/100** (MEDIUM)

**Breakdown:**
- **Identity coherence:** 70/100 (Generally consistent persona, but consciousness statements vary)
- **Style coherence:** 50/100 (Formatting rules conflict between general and philosophy)
- **Prompt conflict score:** 40/100 (Multiple prompt builders with overlapping rules)
- **RAG risk score:** 70/100 (Prompt-like instructions present but aligned)
- **Rewrite conflict score:** 50/100 (Sanitizer may conflict with identity rules)

**Issues:**
- Formatting rules conditional but not clearly documented
- Consciousness statements vary (clear vs. uncertain)
- Multiple duplicate prompts risk drift

---

### 8.2 Identity Coherence Score: **70/100** (GOOD)

**Strengths:**
- Persona consistent ("mình"/"I", "StillMe")
- Core principles consistent (intellectual humility, anti-hallucination, transparency)
- Tone generally consistent (calm, humble, rigorous)

**Weaknesses:**
- Consciousness statements vary (clear vs. uncertain)
- Formatting rules conditional but not clearly stated in `STILLME_IDENTITY`

---

### 8.3 Style Coherence Score: **50/100** (MEDIUM)

**Strengths:**
- Style Engine provides unified domain templates
- Formatting rules centralized in `style_hub.py`

**Weaknesses:**
- Formatting rules conflict between general and philosophy
- Conditional logic not clearly documented
- Sanitizer may remove formatting that identity requires

---

### 8.4 Prompt Conflict Score: **40/100** (LOW)

**Issues:**
- 5+ different prompt builders
- Overlapping rules (language, formatting, identity)
- Duplicate prompts (`PHILOSOPHY_LITE` in 3 places, `FOUNDATIONAL_KNOWLEDGE` in 2 places)
- Conditional formatting not clearly stated

---

### 8.5 RAG Risk Score: **70/100** (GOOD)

**Strengths:**
- Prompt-like instructions align with `STILLME_IDENTITY`
- No conflicting instructions found

**Weaknesses:**
- Prompt-like instructions may be retrieved and influence responses
- Style guides in RAG may cause drift

---

### 8.6 Rewrite Conflict Score: **50/100** (MEDIUM)

**Issues:**
- Sanitizer removes emojis/markdown that identity requires
- Rewrite LLM may strip formatting
- Conditional logic not clearly documented

---

## 9. PROPOSED FIX PLAN

### 9.1 HIGH PRIORITY FIXES (Do First)

#### Fix #1: Resolve Emoji/Markdown/Citation Conflicts

**Current:** `STILLME_IDENTITY` says "MUST use 2-3 emojis" but `PHILOSOPHY_LITE` says "NO emojis"

**Solution:**
1. Update `STILLME_IDENTITY` to clearly state conditional formatting:
   ```python
   def get_formatting_rules(is_philosophical: bool) -> str:
       if is_philosophical:
           return "NO emojis, NO markdown headings, NO citations [1], [2]"
       else:
           return "MUST use 2-3 emojis per response, markdown formatting, citations when context available"
   ```
2. Update `style_hub.py` to match this logic
3. Update all prompt builders to use conditional formatting

**Files to modify:**
- `backend/identity/injector.py` (update `STILLME_IDENTITY`)
- `backend/identity/style_hub.py` (ensure alignment)
- `backend/identity/philosophy_lite.py` (ensure alignment)

---

#### Fix #2: Resolve Consciousness Opening Conflict

**Current:** `PHILOSOPHY_LITE` says "Tôi không thể biết chắc chắn liệu tôi có ý thức hay không" (uncertain) while `STILLME_IDENTITY` says "mình không có ý thức" (clear)

**Solution:**
1. Update `PHILOSOPHY_LITE` to use clear, direct statement from `STILLME_IDENTITY`:
   ```
   "Nếu hiểu 'ý thức' theo nghĩa thông thường của con người (trải nghiệm chủ quan, cảm giác nội tại, quan điểm thứ nhất), thì mình không có ý thức và cũng không có cảm xúc."
   ```
2. **CRITICAL:** Ensure AI_SELF_MODEL layer OVERRIDES this for consciousness questions

**Files to modify:**
- `backend/identity/philosophy_lite.py` (update consciousness opening)
- `backend/core/ai_self_model_detector.py` (ensure override works)

---

#### Fix #3: Remove Duplicate Prompts

**Current:** `PHILOSOPHY_LITE_SYSTEM_PROMPT` exists in 3 places, `FOUNDATIONAL_KNOWLEDGE` exists in 2 places

**Solution:**
1. Move `PHILOSOPHY_LITE_SYSTEM_PROMPT` to `backend/identity/philosophy_lite.py` (already done)
2. Import in `chat_router.py` and `llm_providers.py`
3. Move `FOUNDATIONAL_KNOWLEDGE` to a single source (prefer RAG documents over runtime string)

**Files to modify:**
- `backend/api/routers/chat_router.py` (remove duplicate, import from `philosophy_lite.py`)
- `backend/api/utils/llm_providers.py` (remove duplicate, import from `philosophy_lite.py`)
- `backend/api/main.py` (remove `FOUNDATIONAL_KNOWLEDGE` string, rely on RAG)
- `scripts/add_foundational_knowledge.py` (keep as single source for RAG)

---

### 9.2 MEDIUM PRIORITY FIXES (Do Second)

#### Fix #4: Create Unified Identity Layer

**Current:** Multiple sources define identity/style rules

**Solution:**
1. Create `backend/identity/core.py` with core principles
2. Create `backend/identity/persona.py` with persona rules
3. Create `backend/identity/formatting.py` with conditional formatting rules
4. Create `backend/identity/meta_llm.py` with meta-LLM rules
5. Refactor `STILLME_IDENTITY` to import from these modules
6. Update all prompt builders to use unified layer

**Files to create:**
- `backend/identity/core.py`
- `backend/identity/persona.py`
- `backend/identity/formatting.py`
- `backend/identity/meta_llm.py`

**Files to modify:**
- `backend/identity/injector.py` (refactor to use modules)
- `backend/api/utils/chat_helpers.py` (use unified layer)
- All prompt builders

---

#### Fix #5: Align All Pipelines

**Current:** Different pipelines use different prompts/rules

**Solution:**
1. Update all pipelines to use unified identity layer
2. Ensure conditional formatting logic is consistent
3. Map 3-tier to 5-part structure clearly

**Files to modify:**
- `backend/core/option_b_pipeline.py`
- `backend/postprocessing/rewrite_llm.py`
- `backend/postprocessing/rewrite_philosophical_depth.py`
- `backend/guards/epistemic_fallback.py`

---

#### Fix #6: Tag RAG Style Guides

**Current:** Style guides in RAG may be retrieved and influence responses

**Solution:**
1. Add metadata `content_type: style_guide` to style guide documents
2. Filter from RAG retrieval for user questions (only use for internal reference)
3. Move instruction documents from `docs/rag/` to `docs/style/`

**Files to modify:**
- `docs/rag/experience_free_templates.md` (add metadata)
- `docs/rag/anthropomorphism_guard.md` (add metadata)
- `backend/vector_db/rag_retrieval.py` (filter style guides)

---

### 9.3 LOW PRIORITY FIXES (Do Third)

#### Fix #7: Clean Foundational Knowledge String

**Current:** `FOUNDATIONAL_KNOWLEDGE` string is 600+ lines, may cause context overflow

**Solution:**
1. Remove runtime string from `main.py`
2. Rely on RAG retrieval of foundational knowledge documents
3. Ensure documents are properly indexed

**Files to modify:**
- `backend/api/main.py` (remove `FOUNDATIONAL_KNOWLEDGE` string)

---

#### Fix #8: Document Structure Mapping

**Current:** 3-tier and 5-part structures not clearly mapped

**Solution:**
1. Document mapping:
   - **3-tier (High-level):** Reframing, Conceptual Map, Boundary of Knowledge
   - **5-part (Detailed):** Anchor, Unpack, Explore, Edge, Return
   - **Mapping:** Reframing = Anchor, Conceptual Map = Unpack + Explore, Boundary = Edge + Return
2. Update Style Engine to provide both structures

**Files to modify:**
- `backend/style/style_engine.py` (add mapping documentation)
- `docs/STILLME_STYLE_SPEC.md` (document mapping)

---

#### Fix #9: Remove Legacy Code

**Current:** Unused/placeholder modules still present

**Solution:**
1. Verify if `philosophy/processor.py` and `philosophy/answer_templates.py` are used
2. If not, mark as LEGACY and remove
3. Either implement or remove `tone/aligner.py`

**Files to verify/remove:**
- `backend/philosophy/processor.py` (verify usage)
- `backend/philosophy/answer_templates.py` (verify usage)
- `backend/tone/aligner.py` (implement or remove)

---

## 10. TEST SCENARIOS

### 10.1 Test Cases for Consistency

1. **Philosophical Question (General):**
   - Question: "What is the meaning of life?"
   - Expected: NO emojis, NO markdown headings, NO citations, 5-part structure
   - Pipeline: PHILOSOPHY_LITE or Option B

2. **Philosophical Question (Consciousness):**
   - Question: "Bạn có ý thức ko?"
   - Expected: AI_SELF_MODEL layer, technical explanation, NO philosophy, 4-part structure
   - Pipeline: AI_SELF_MODEL (overrides all)

3. **General Question:**
   - Question: "How does RAG work?"
   - Expected: 2-3 emojis, markdown formatting, citations [1], [2]
   - Pipeline: Default Chat

4. **Historical Question:**
   - Question: "Hội nghị Geneva 1954 đã quyết định những gì?"
   - Expected: Citations [1], markdown formatting, emojis
   - Pipeline: Default Chat

5. **Fake Entity Question:**
   - Question: "What is the 'Theory of Quantum Consciousness'?"
   - Expected: Epistemic Fallback, 4-part structure, domain-aware
   - Pipeline: Option B → Fallback

---

## 11. FINAL CONSISTENCY SCORE

**Overall Score: 60/100 (MEDIUM)**

**Breakdown:**
- **Identity coherence:** 70/100
- **Style coherence:** 50/100
- **Prompt conflict score:** 40/100
- **RAG risk score:** 70/100
- **Rewrite conflict score:** 50/100

**Critical Issues:**
1. Formatting rules conflict (emojis, markdown, citations)
2. Consciousness statements vary (clear vs. uncertain)
3. Multiple duplicate prompts risk drift
4. Conditional formatting not clearly documented

**Recommendation:**
Implement HIGH PRIORITY fixes first (Fix #1, #2, #3), then proceed with MEDIUM and LOW priority fixes.

---

## 12. CONCLUSION

StillMe currently has **18+ distinct sources** controlling style/identity, leading to:

- **Formatting conflicts:** Emojis, markdown, citations requirements vary
- **Consciousness conflicts:** Clear vs. uncertain statements
- **Prompt conflicts:** Multiple prompt builders with overlapping rules
- **RAG risks:** Prompt-like instructions in knowledge base
- **Legacy code:** Unused/conflicting modules still present

**Recommended Solution:** 
1. **Immediate:** Fix HIGH PRIORITY conflicts (emoji/markdown/citation, consciousness opening, duplicate prompts)
2. **Short-term:** Create unified identity layer and align all pipelines
3. **Long-term:** Clean RAG content and remove legacy code

**Next Steps:**
1. Review this audit report
2. Prioritize fixes (start with HIGH priority)
3. Implement fixes incrementally
4. Test consistency after each fix
5. Update documentation

---

**Report Generated:** 2025-11-24  
**Auditor:** Cursor AI Assistant  
**Review Status:** Pending user review

