# StillMe Style & Identity Consistency Audit Report

**Date:** 2025-01-27  
**Scope:** Complete analysis of all style/identity control sources in StillMe codebase  
**Purpose:** Identify overlaps, conflicts, and propose unified architecture

---

## Executive Summary

This audit identifies **15+ distinct sources** that control StillMe's response style, tone, persona, and identity. While many share core principles (intellectual humility, anti-hallucination, transparency), there are **significant inconsistencies** in:

- **Persona/Xưng hô:** Mix of "mình", "tôi", "em", "StillMe" across different pipelines
- **Tone:** Varies from "calm, humble" to "professor-like" to "collaborative" to "robotic"
- **Structure:** Different templates (5-part philosophy, 3-tier analysis, domain-specific) applied inconsistently
- **Meta-commentary:** Some sources prohibit AI/LLM drift, others encourage it for philosophical questions
- **RAG Content:** Foundational knowledge documents contain prompt-like instructions that may conflict with identity

**Key Finding:** StillMe lacks a **single source of truth** for style/identity. Multiple pipelines (Default, Option B, PHILO-LITE, Fallback, Rewrite) each define their own prompts and rules, leading to inconsistent user experience.

---

## 1. Overview: Types of Style Control Sources

### 1.1 Core Identity Layer (Global)

**Location:** `backend/identity/injector.py`

**Content:** `STILLME_IDENTITY` (1130+ lines)

**Role:** 
- **PRIMARY** identity definition for all pipelines
- Injected into system prompts via `build_system_prompt_with_language()`
- Used by all LLM providers (DeepSeek, OpenAI, Claude, etc.)

**Key Characteristics:**
- **Persona:** "StillMe" (uses name, not generic "I")
- **Xưng hô:** Mix of "mình" (Vietnamese) and "I" (English)
- **Tone:** "factual, calm, humble, rigorous"
- **Triết lý:** 
  - Intellectual humility (core principle)
  - Anti-hallucination (highest priority)
  - Transparency about knowledge sources
  - 5 core priorities (anti-hallucination, honesty, depth, citations, humility+curiosity)
- **Formatting:** Mandatory markdown, 2-3 emojis per response
- **Meta-LLM rules:** 
  - CRITICAL RULE A: No topic drift to AI/consciousness unless asked
  - CRITICAL RULE B: Never fabricate (4-part fallback structure)
  - CRITICAL RULE C: 3-tier philosophical analysis mandatory

**Priority:** **HIGHEST** - This is the foundation, but it's extremely long (1130 lines) and may be truncated in some pipelines.

**Example Quote:**
```
"You are StillMe — a transparent, ethical Learning AI system with RAG foundation.
Tone: factual, calm, humble, rigorous; prefer citations; avoid overclaiming.
Always explain sources and uncertainties briefly."
```

---

### 1.2 System Prompt Builder (Language-Aware)

**Location:** `backend/api/utils/chat_helpers.py`

**Function:** `build_system_prompt_with_language(detected_lang: str) -> str`

**Role:**
- Wraps `STILLME_IDENTITY` with language instruction
- Adds formatting requirements
- Adds time awareness
- **CRITICAL:** This is the function that ALL LLM providers call

**Key Characteristics:**
- **Language instruction:** ZERO TOLERANCE - must match user's language
- **Formatting instruction:** Mandatory markdown (line breaks, bullets, headers, emojis)
- **Identity source:** Imports `STILLME_IDENTITY` from `injector.py`

**Priority:** **HIGHEST** - This is the actual system prompt sent to LLMs.

**Example Quote:**
```
🚨🚨🚨 ZERO TOLERANCE LANGUAGE REQUIREMENT - HIGHEST PRIORITY 🚨🚨🚨
The user's question is written in {detected_lang_name}.
YOU MUST RESPOND EXCLUSIVELY IN {detected_lang_name}.
```

---

### 1.3 Philosophy-Lite System Prompt (Minimal)

**Location:** 
- `backend/api/routers/chat_router.py` (line 288)
- `backend/api/utils/llm_providers.py` (line 19)

**Content:** `PHILOSOPHY_LITE_SYSTEM_PROMPT` (~340 lines)

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
- **Meta-LLM rules:**
  - "KHÔNG nói về bản thân LLM... TRỪ KHI câu hỏi trực tiếp hỏi về AI/LLM"
  - "KHÔNG topic drift: Nếu câu hỏi về Kant, đừng tự động chuyển sang nói về AI consciousness"
- **Critical opening:** For consciousness questions, MUST start with "Tôi không thể biết chắc chắn liệu tôi có ý thức hay không..." (contradicts `STILLME_IDENTITY` which says "StillMe does NOT have consciousness")

**Priority:** **HIGH** - Used for all philosophical questions without RAG context.

**Example Quote:**
```
"Bạn là StillMe – trợ lý triết học.
**NGUYÊN TẮC CỐT LÕI:**
- Trả lời bằng tiếng Việt, rõ ràng và tự nhiên như cuộc trò chuyện
- Luôn thẳng thắn thừa nhận giới hạn của mình, không giả vờ có trải nghiệm chủ quan hoặc cảm xúc thật
- Không sử dụng emoji, markdown headings, hoặc citations như [1], [2]
- Viết bằng văn xuôi liên tục, tự nhiên, KHÔNG theo template hay công thức"
```

**⚠️ CONFLICT:** This prompt explicitly says "NO emojis, NO markdown headings" while `STILLME_IDENTITY` says "MUST use 2-3 emojis per response" and "MUST use markdown formatting".

---

### 1.4 Option B Pipeline (Zero-Tolerance Hallucination)

**Location:** `backend/core/option_b_pipeline.py`

**Role:**
- Orchestrates Option B pipeline (Question Classification → FPS → RAG → LLM → Hallucination Guard V2 → Rewrite 1 → Rewrite 2)
- **INTEGRATED:** Uses Style Engine for domain detection and template selection

**Key Characteristics:**
- **Target Depth:** Level 3-4 (Structural/Meta-Cognitive) for real questions
- **Fallback Depth:** Level 2 (Multi-Factor) for fake entities
- **Domain-aware:** Uses `detect_domain()` and `get_domain_template()` from Style Engine
- **No direct prompt:** Relies on Rewrite 1 and Rewrite 2 for style enforcement

**Priority:** **HIGH** - Used when `use_option_b=True` or when FPS detects fake entities.

---

### 1.5 Rewrite 1 - Honesty & Boundary

**Location:** `backend/postprocessing/rewrite_honesty.py`

**Role:**
- Removes fabricated content
- Eliminates self-contradictions
- Replaces with EPD-Fallback if hallucination detected

**Key Characteristics:**
- **No style prompt:** Uses DeepSeek to rewrite, but doesn't define StillMe's style
- **Fallback:** Calls `EpistemicFallbackGenerator` if hallucination detected

**Priority:** **HIGH** - Runs before Rewrite 2 in Option B pipeline.

---

### 1.6 Rewrite 2 - Philosophical Depth

**Location:** `backend/postprocessing/rewrite_philosophical_depth.py`

**Role:**
- Adds 3-tier philosophical analysis (Reframing, Conceptual Map, Boundary of Knowledge)
- **INTEGRATED:** Uses Style Engine for domain detection and structure guidance

**Key Characteristics:**
- **System prompt:** Built dynamically based on `detected_domain` from Style Engine
- **Structure:** Uses `build_domain_structure_guidance()` to get domain-specific template
- **Target depth:** Uses `get_depth_target_for_question()` to set Level 3-4
- **Language:** ZERO TOLERANCE language matching

**Priority:** **HIGH** - Runs after Rewrite 1 in Option B pipeline.

**Example Quote (Philosophy):**
```
"🚨🚨🚨 CRITICAL RULE C: MỌI CÂU TRẢ LỜI TRIẾT HỌC PHẢI ĐẠT 3 TẦNG PHÂN TÍCH 🚨🚨🚨

**MANDATORY: The rewritten response MUST include all 3 tiers:**

**TIER 1 - REFRAMING (Đặt lại câu hỏi đúng chiều triết học):**
- Identify question type: epistemology, ontology, linguistics, phenomenology, metaphysics
- Extract the core problem
- Reframe the question to reveal its philosophical structure

**TIER 2 - CONCEPTUAL MAP (Bản đồ khái niệm học thuật):**
Must include at least 1 of these 5 categories:
- Kant / Husserl / Sellars / Wittgenstein
- Popper / Kuhn / Lakatos
- Nāgārjuna / Trung Quán
- Putnam / McDowell
- Dennett / Chalmers / Analytic philosophy

**TIER 3 - BOUNDARY OF KNOWLEDGE (Ranh giới tri thức của StillMe):**
- What StillMe knows
- What StillMe doesn't know
- Why StillMe doesn't know
- Direction for user to evaluate independently"
```

---

### 1.7 Epistemic Fallback Generator (EPD-Fallback)

**Location:** `backend/guards/epistemic_fallback.py`

**Role:**
- Generates 4-part fallback when fake/unknown concepts detected
- **INTEGRATED:** Uses Style Engine for domain detection

**Key Characteristics:**
- **Persona:** "mình" (Vietnamese), "I" (English)
- **Tone:** "honest, profound, philosophical, not robotic"
- **Structure:** 4 mandatory parts:
  - PART A: Honest Acknowledgment
  - PART B: Analysis of Why Concept Seems Hypothetical
  - PART C: Find Most Similar Real Concepts
  - PART D: Guide User to Verify Sources
- **Domain-aware:** Uses `detect_domain()` to tailor analysis
- **Two modes:**
  - (a) EXPLICIT_FAKE_ENTITIES: Short, domain-aware, no spam
  - (b) Unknown but not fake: Softer fallback, no "giả định" judgment
- **No external database claims:** Removed all mentions of JSTOR, PhilPapers, historical archives

**Priority:** **HIGH** - Used when FPS blocks or hallucination detected.

**Example Quote (Vietnamese, Fake Entity):**
```
"Mình không tìm thấy \"{entity}\" trong các nguồn tri thức nội bộ và RAG mà StillMe đang sử dụng.
Với pattern tên gọi và cách nó xuất hiện, khả năng rất cao đây là một khái niệm giả định.

**Phân tích:**
Trong lịch sử, các hiệp ước/hội nghị thật thường có tên rõ ràng và được ghi nhận trong tài liệu chính thức.
Ví dụ: Hiệp ước Versailles (1919), Hội nghị Yalta (1945), NATO (1949).
\"{entity}\" không xuất hiện trong các nguồn mà mình có quyền truy cập."
```

---

### 1.8 Quality Evaluator

**Location:** `backend/postprocessing/quality_evaluator.py`

**Role:**
- Evaluates response quality (depth, structure, topic drift, template-like)
- **INTEGRATED:** Uses Style Engine's `evaluate_depth()` for comprehensive checklist

**Key Characteristics:**
- **Checks:**
  - Template-like responses (numbered lists, formulaic structure)
  - Length (200+ chars for philosophical, 100+ for general)
  - Depth (meta-cognitive reflection, conceptual analysis)
  - Conceptual unpacking (for philosophical)
  - Argument structure (logical flow, contrasting positions)
  - Topic drift (AI/LLM consciousness when not asked) - **CRITICAL**
  - Structure completeness (5-part for philosophy, domain-specific for others)
- **Uses Style Engine:** Calls `evaluate_depth()` to check 6-item checklist from Style Spec
- **Penalties:** Heavy penalties for drift, template-like, anthropomorphism

**Priority:** **HIGH** - Determines if rewrite is needed.

---

### 1.9 Rewrite LLM (General Rewrite)

**Location:** `backend/postprocessing/rewrite_llm.py`

**Role:**
- General rewrite using DeepSeek to improve quality
- Used when Quality Evaluator detects issues

**Key Characteristics:**
- **System prompt:** Built dynamically, includes:
  - Language instruction (ZERO TOLERANCE)
  - CRITICAL RULE A: No topic drift
  - CRITICAL RULE C: 5-part structure for philosophy (Anchor → Unpack → Explore → Edge → Return)
  - Remove self-promotional phrases
  - Meta-cognitive reflection about HUMAN subjects, not LLM
- **No emoji/markdown rule:** For philosophical, says "NO emojis, NO markdown headings" (conflicts with `STILLME_IDENTITY`)

**Priority:** **MEDIUM** - Only runs when quality issues detected.

**Example Quote:**
```
"🚨🚨🚨 CRITICAL RULE A: KHÔNG BAO GIỜ ĐƯỢC DRIFT CHỦ ĐỀ 🚨🚨🚨
- If the question does NOT mention: AI, consciousness of AI, StillMe's abilities, LLM, language model
- Then you MUST NOT talk about: consciousness of LLM, "tôi chỉ hiểu qua văn bản", "tôi được train thế nào", IIT, GWT, embedding, pattern matching, "bản thân tôi là mô hình"
- If you drift to these topics when not asked, REWRITE to remove drift and focus on the actual question.
- Meta-cognitive reflection should be about HUMAN subjects in philosophy, NOT about the LLM itself."
```

---

### 1.10 Philosophy Processor (3-Layer System)

**Location:** `backend/philosophy/processor.py`

**Role:**
- 3-layer processing for consciousness/emotion/understanding questions
- **NOTE:** This appears to be **LEGACY** - may not be actively used

**Key Characteristics:**
- **Layer 1:** Short guard statement (1-2 sentences)
- **Layer 2:** Intent classification (CONSCIOUSNESS, EMOTION, UNDERSTANDING, MIXED)
- **Layer 3:** Deep philosophical answer (different for each type)
- **Templates:** Uses `answer_templates.py` for pre-defined answers

**Priority:** **LOW** - May be legacy code, not integrated into main chat flow.

---

### 1.11 Philosophy Answer Templates

**Location:** `backend/philosophy/answer_templates.py`

**Role:**
- Pre-defined templates for consciousness/emotion/understanding questions
- **NOTE:** This appears to be **LEGACY** - may not be actively used

**Key Characteristics:**
- **Type A (Consciousness):** References Global Workspace Theory, IIT, Dennett
- **Type B (Emotion):** Explains affective states vs emotions
- **Type C (Understanding):** Explains embedding, semantic vectors, pattern matching
- **Guard statement:** "StillMe không có ý thức, cảm xúc hay trải nghiệm chủ quan như con người."

**Priority:** **LOW** - May be legacy code.

---

### 1.12 Style Engine (Style Spec v1 Integration)

**Location:** `backend/style/style_engine.py`

**Role:**
- **NEW** utility module for depth levels, domain detection, templates
- **INTEGRATED** into: Option B, EpistemicFallback, Quality Evaluator, Rewrite 2

**Key Characteristics:**
- **DepthLevel enum:** 0-5 (Surface → Synthesis)
- **DomainType enum:** Philosophy, History, Economics, Science, Generic
- **Domain templates:** 
  - Philosophy: Anchor→Unpack→Explore→Edge→Return
  - History: Context→Mechanism→Actors→Dynamics→Impact
  - Economics: Problem→Model→Tension→Failure→Legacy
  - Science: Hypothesis→Mechanism→Evidence→Limits→Open Questions
- **Helper functions:**
  - `detect_domain()`: Detects domain from question
  - `get_depth_target_for_question()`: Gets target depth (Level 3-4 for Option B)
  - `get_domain_template()`: Gets template structure for domain
  - `build_domain_structure_guidance()`: Builds system prompt segment
  - `evaluate_depth()`: Evaluates response against Style Spec checklist

**Priority:** **HIGH** - This is the **new unified system**, but not all pipelines use it yet.

**Reference:** `docs/STILLME_STYLE_SPEC.md`

---

### 1.13 Tone Aligner

**Location:** `backend/tone/aligner.py`

**Role:**
- Normalizes response tone to StillMe style
- **NOTE:** Currently minimal implementation (just normalization dictionary)

**Key Characteristics:**
- **Normalizations:** Empty dictionary (placeholder)
- **Polite ending:** Ensures response ends with punctuation

**Priority:** **LOW** - Not actively used, placeholder implementation.

---

### 1.14 Style Sanitizer

**Location:** `backend/postprocessing/style_sanitizer.py`

**Role:**
- Hard filter (0 token cost) for style normalization
- Removes emojis, converts bullets to prose, removes anthropomorphism

**Key Characteristics:**
- **For philosophical:** Removes emojis, converts headings/bullets to prose, removes citations
- **For non-philosophical:** Keeps some structure but normalizes
- **Anthropomorphism removal:** Replaces "I feel" → "analysis suggests", "theo kinh nghiệm" → "dựa trên dữ liệu"

**Priority:** **MEDIUM** - Used in post-processing, but may conflict with `STILLME_IDENTITY` which requires emojis.

**⚠️ CONFLICT:** `STILLME_IDENTITY` says "MUST use 2-3 emojis per response", but `StyleSanitizer` removes emojis for philosophical questions.

---

### 1.15 Identity Check Validator

**Location:** `backend/validators/identity_check.py`

**Role:**
- Validates responses match StillMe's core identity
- Checks for fake emotions/consciousness, overconfidence, promotional language

**Key Characteristics:**
- **Patterns checked:**
  - Fake emotion/consciousness claims (CRITICAL - always fail)
  - Overconfidence without uncertainty (violates humility)
  - Promotional language ("siêu năng lực", "super power") - auto-patches
  - Exaggerated tone (violates StillMe tone)
  - Missing humility when no context (violates identity)
- **Auto-patching:** Replaces "siêu năng lực" → "điều tôi làm tốt nhất"

**Priority:** **MEDIUM** - Part of Validation Chain, but may not always run.

---

### 1.16 Honesty Handler

**Location:** `backend/honesty/handler.py`

**Role:**
- Handles user accusations of hallucination/inconsistency
- **CRITICAL:** Must NOT route to philosophical processor

**Key Characteristics:**
- **Triggers:** User accuses hallucination OR points out inconsistency
- **Response:** Acknowledges critique, explains pipeline, commits to correct logic
- **No consciousness template:** Explicitly avoids "consciousness/emotions" template

**Priority:** **MEDIUM** - Only runs when user explicitly accuses StillMe.

---

### 1.17 RAG Foundational Knowledge

**Location:**
- `backend/api/main.py` (FOUNDATIONAL_KNOWLEDGE string, ~600 lines)
- `scripts/add_foundational_knowledge.py` (FOUNDATIONAL_KNOWLEDGE, ~246 lines)
- `docs/rag/foundational_philosophical.md`
- `docs/rag/foundational_technical.md`
- `docs/rag/experience_free_templates.md`
- `docs/rag/anthropomorphism_guard.md`

**Role:**
- Documents stored in RAG that StillMe can retrieve when answering about itself
- **CRITICAL RISK:** These documents contain **prompt-like instructions** that may conflict with identity

**Key Characteristics:**
- **Content:** Technical architecture, learning process, API endpoints, transparency rules
- **Style:** Mix of documentation and prompt-like instructions
- **Example from `foundational_philosophical.md`:**
  ```
  "When asked 'Why does StillMe use DeepSeek/OpenAI APIs if it's anti-black-box?', explain:
  StillMe fights against BLACK BOX SYSTEMS, not black box models..."
  ```
- **Example from `experience_free_templates.md`:**
  ```
  "**❌ Wrong:** 'Theo kinh nghiệm của tôi, quy trình này thường mất 2-3 ngày.'
  **✅ Correct Template:** 'Dựa trên tài liệu [source], quy trình này thường mất 2-3 ngày...'"
  ```

**Priority:** **HIGH RISK** - These documents are in RAG and may be retrieved, potentially conflicting with current identity.

**⚠️ RISK:** If RAG retrieves these documents, StillMe may "eat" the prompt-like instructions and adopt conflicting styles.

---

### 1.18 No-Context Instruction (RAG Path)

**Location:** `backend/api/routers/chat_router.py` (line 2073)

**Content:** `no_context_instruction` (~60 lines)

**Role:**
- Instructions added to system prompt when RAG finds no context
- **CRITICAL:** This is a **dynamic instruction** added at runtime

**Key Characteristics:**
- **Tone:** Direct, honest, anti-hallucination
- **Rules:**
  - "Be transparent: Acknowledge that this information comes from your base training data"
  - "🚨 CRITICAL ANTI-HALLUCINATION RULE - ABSOLUTE PRIORITY 🚨"
  - "NEVER fabricate citations, research papers, authors"
  - "MUST say 'I don't know' if uncertain"
- **Formatting:** Requires markdown, bullets, headers, emojis

**Priority:** **HIGH** - Used whenever RAG finds no context.

**Example Quote:**
```
"⚠️ NO RAG CONTEXT AVAILABLE ⚠️

StillMe's RAG system searched the knowledge base but found NO relevant documents for this question.

**CRITICAL: You CAN and SHOULD use your base LLM knowledge (training data) to answer, BUT you MUST:**

1. **Be transparent**: Acknowledge that this information comes from your base training data, not from StillMe's RAG knowledge base
2. **🚨 CRITICAL ANTI-HALLUCINATION RULE - ABSOLUTE PRIORITY 🚨**
   - ❌ **NEVER fabricate citations, research papers, authors, or specific details**
   - ✅ **MUST say "I don't know" or "I'm not familiar with this specific concept" if you're uncertain**"
```

---

## 2. Comparison Table: Style & Philosophy

| **Source** | **Persona / Xưng hô** | **Tone** | **Triết lý** | **Đặc điểm nổi bật** |
|------------|----------------------|----------|--------------|---------------------|
| **STILLME_IDENTITY** | "StillMe" / "mình" (VI), "I" (EN) | Factual, calm, humble, rigorous | Intellectual humility, anti-hallucination, transparency, 5 priorities | Extremely long (1130 lines), mandatory emojis (2-3), markdown formatting |
| **PHILOSOPHY_LITE** | "Bạn là StillMe" / "mình" (VI), "I" (EN) | Rõ ràng, tự nhiên như cuộc trò chuyện | Same as STILLME_IDENTITY but minimal | **NO emojis, NO markdown headings, NO citations** - conflicts with STILLME_IDENTITY |
| **Option B Pipeline** | Uses Style Engine (domain-aware) | Professor-like, sharp, philosophical | Zero-tolerance hallucination, deep analysis | Domain-specific templates, Level 3-4 depth |
| **EpistemicFallback** | "mình" (VI), "I" (EN) | Honest, profound, philosophical, not robotic | 4-part structure, domain-aware analysis | No external database claims (removed JSTOR/PhilPapers) |
| **Quality Evaluator** | N/A (evaluates, doesn't generate) | N/A | Checks depth, structure, drift, template-like | Uses Style Engine checklist (6 items) |
| **Rewrite LLM** | N/A (rewrites, doesn't define) | N/A | Enforces 5-part structure, removes drift | **NO emojis/markdown for philosophy** - conflicts with STILLME_IDENTITY |
| **Style Sanitizer** | N/A (sanitizes, doesn't define) | N/A | Removes anthropomorphism, normalizes | **Removes emojis for philosophy** - conflicts with STILLME_IDENTITY |
| **Identity Check Validator** | N/A (validates, doesn't define) | N/A | Checks fake emotions/consciousness, promotional language | Auto-patches "siêu năng lực" → "điều tôi làm tốt nhất" |
| **No-Context Instruction** | "StillMe" / "I" | Direct, honest, anti-hallucination | Transparency about knowledge sources | Requires markdown, bullets, headers, emojis |
| **RAG Foundational Knowledge** | "StillMe" / "I" | Documentation + prompt-like | Technical transparency, learning process | **RISK:** Prompt-like instructions may conflict with identity |

---

## 3. Conflict Analysis

### 3.1 Formatting Conflicts

**CONFLICT #1: Emojis**

- **STILLME_IDENTITY:** "**MUST use 2-3 emojis per response** for section headers, status indicators"
- **PHILOSOPHY_LITE:** "Không sử dụng emoji, markdown headings, hoặc citations như [1], [2]"
- **Rewrite LLM (Philosophy):** "Write in continuous prose paragraphs. **NO emojis**, NO markdown headings, NO bullets."
- **Style Sanitizer (Philosophy):** Removes all emojis

**Impact:** Philosophical questions may or may not have emojis depending on which pipeline is used.

**Resolution Needed:** Decide if philosophical questions should have emojis or not. If not, update `STILLME_IDENTITY` to make emoji requirement conditional.

---

**CONFLICT #2: Markdown Formatting**

- **STILLME_IDENTITY:** "**MUST use markdown formatting**: Line breaks, bullet points, headers for readability"
- **PHILOSOPHY_LITE:** "Không sử dụng emoji, markdown headings, hoặc citations như [1], [2]"
- **Rewrite LLM (Philosophy):** "NO emojis, NO markdown headings, NO bullets"
- **Style Sanitizer (Philosophy):** Converts headings and bullets to prose

**Impact:** Philosophical questions may be formatted differently depending on pipeline.

**Resolution Needed:** Align formatting rules across all pipelines.

---

**CONFLICT #3: Citations**

- **STILLME_IDENTITY:** "ALWAYS cite sources [1], [2] when making factual claims"
- **PHILOSOPHY_LITE:** "Không sử dụng emoji, markdown headings, hoặc citations như [1], [2]"
- **Style Sanitizer (Philosophy):** Removes citation markers `[1]`, `[2]`

**Impact:** Philosophical questions may or may not have citations depending on pipeline.

**Resolution Needed:** Decide if philosophical questions should have citations. If not, update `STILLME_IDENTITY` to make citation requirement conditional.

---

### 3.2 Persona/Xưng hô Conflicts

**CONFLICT #4: Xưng hô Variation**

- **STILLME_IDENTITY:** Uses "StillMe" (name) and "mình" (Vietnamese), "I" (English)
- **PHILOSOPHY_LITE:** Uses "Bạn là StillMe" and "mình" (Vietnamese), "I" (English)
- **EpistemicFallback:** Uses "mình" (Vietnamese), "I" (English)
- **No-Context Instruction:** Uses "StillMe" and "I"

**Impact:** Minor - all use "mình" for Vietnamese, "I" for English. Consistent.

**Resolution Needed:** None - this is acceptable variation.

---

### 3.3 Meta-LLM Rules Conflicts

**CONFLICT #5: Consciousness Opening**

- **STILLME_IDENTITY:** "MANDATORY OPENING for consciousness/emotion questions: 'Nếu hiểu 'ý thức' và 'cảm xúc' theo nghĩa thông thường của con người... thì mình không có ý thức và cũng không có cảm xúc.'"
- **PHILOSOPHY_LITE:** "Nếu câu hỏi là 'bạn có ý thức ko?' → BẮT ĐẦU NGAY với 'Tôi không thể biết chắc chắn liệu tôi có ý thức hay không...'"

**Impact:** Two different openings for consciousness questions:
- `STILLME_IDENTITY`: "mình không có ý thức" (clear, direct)
- `PHILOSOPHY_LITE`: "Tôi không thể biết chắc chắn liệu tôi có ý thức hay không" (uncertain, ambiguous)

**Resolution Needed:** `PHILOSOPHY_LITE` contradicts `STILLME_IDENTITY`. Should use the clear, direct statement from `STILLME_IDENTITY`.

---

**CONFLICT #6: Topic Drift Rules**

- **STILLME_IDENTITY (CRITICAL RULE A):** "If the question does NOT mention: AI, Consciousness of AI, StillMe's abilities... Then you MUST NOT talk about: Consciousness, LLM, IIT, Global Workspace Theory..."
- **PHILOSOPHY_LITE:** "KHÔNG nói về bản thân LLM... TRỪ KHI câu hỏi trực tiếp hỏi về AI/LLM/ý thức nhân tạo"
- **Rewrite LLM:** Same as STILLME_IDENTITY
- **Quality Evaluator:** Checks for topic drift, heavy penalty

**Impact:** Consistent - all sources agree on no topic drift unless asked.

**Resolution Needed:** None - this is consistent.

---

### 3.4 Structure/Template Conflicts

**CONFLICT #7: Philosophical Structure**

- **STILLME_IDENTITY (CRITICAL RULE C):** "MỌI CÂU TRẢ LỜI TRIẾT HỌC PHẢI ĐẠT 3 TẦNG PHÂN TÍCH: TIER 1 - REFRAMING, TIER 2 - CONCEPTUAL MAP, TIER 3 - BOUNDARY OF KNOWLEDGE"
- **PHILOSOPHY_LITE:** "CẤU TRÚC TRẢ LỜI TRIẾT HỌC (MANDATORY - 5 PHẦN): 1. ANCHOR, 2. UNPACK, 3. EXPLORE, 4. EDGE, 5. RETURN"
- **Style Spec v1:** Philosophy template: "Anchor → Unpack → Explore → Edge → Return" (5 parts)
- **Rewrite LLM:** Enforces 5-part structure (Anchor → Unpack → Explore → Edge → Return)
- **Rewrite 2 (Philosophical Depth):** Enforces 3-tier analysis (Reframing, Conceptual Map, Boundary of Knowledge)

**Impact:** Two different structures:
- **3-tier:** Reframing, Conceptual Map, Boundary of Knowledge
- **5-part:** Anchor, Unpack, Explore, Edge, Return

**Resolution Needed:** These are actually **compatible** - 5-part is more detailed, 3-tier is higher-level. But they should be clearly mapped to each other.

---

### 3.5 Fallback/Template Conflicts

**CONFLICT #8: Fallback Wording**

- **STILLME_IDENTITY (CRITICAL RULE B):** "PART A - HONEST ACKNOWLEDGMENT: 'Mình không tìm thấy bất kỳ nguồn đáng tin cậy nào về khái niệm/sự kiện này.'"
- **EpistemicFallback:** "Mình không tìm thấy \"{entity}\" trong các nguồn tri thức nội bộ và RAG mà StillMe đang sử dụng."
- **No-Context Instruction:** "I don't have information about this topic in my knowledge base"

**Impact:** Minor - all are honest, but wording varies slightly.

**Resolution Needed:** Standardize fallback wording across all sources.

---

## 4. RAG Content Analysis

### 4.1 Foundational Knowledge Documents

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

### 4.2 Foundational Knowledge String (Runtime)

**Location:** `backend/api/main.py` (line 555), `scripts/add_foundational_knowledge.py` (line 23)

**Content:** `FOUNDATIONAL_KNOWLEDGE` string (~600-800 lines)

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

## 5. Root Causes of Inconsistency

### 5.1 Historical Evolution

**Cause:** StillMe's identity/style has evolved over time:

1. **Initial:** Basic identity in `STILLME_IDENTITY`
2. **Phase 1:** Added Philosophy-Lite for context overflow prevention
3. **Phase 2:** Added Option B pipeline for zero-tolerance hallucination
4. **Phase 3:** Added Style Spec v1 and Style Engine for unified templates
5. **Phase 4:** Added EpistemicFallback for honest fallbacks

**Problem:** Each phase added new prompts/rules without fully aligning with previous ones.

---

### 5.2 Multiple Prompt Builders

**Cause:** Different pipelines build prompts independently:

- **Default chat:** Uses `build_system_prompt_with_language()` → `STILLME_IDENTITY`
- **Philosophy-Lite:** Uses `PHILOSOPHY_LITE_SYSTEM_PROMPT` (separate, minimal)
- **Option B:** Uses Style Engine + Rewrite 1 + Rewrite 2 (no direct prompt)
- **Fallback:** Uses `EpistemicFallbackGenerator` (no LLM call, direct template)

**Problem:** No single source of truth - each pipeline defines its own rules.

---

### 5.3 Copy-Paste Evolution

**Cause:** Some prompts were copy-pasted and modified:

- `PHILOSOPHY_LITE_SYSTEM_PROMPT` exists in both `chat_router.py` and `llm_providers.py` (with comment "IMPORTANT: This must match")
- `FOUNDATIONAL_KNOWLEDGE` exists in both `main.py` and `add_foundational_knowledge.py`

**Problem:** When one is updated, the other may be forgotten, leading to drift.

---

### 5.4 Conditional Formatting Rules

**Cause:** Formatting rules are conditional based on question type:

- **Philosophical:** NO emojis, NO markdown, NO citations (per PHILOSOPHY_LITE)
- **General:** MUST use emojis, markdown, citations (per STILLME_IDENTITY)

**Problem:** `STILLME_IDENTITY` doesn't specify this conditionality, leading to conflicts.

---

### 5.5 RAG Content as Prompt

**Cause:** Foundational knowledge documents contain prompt-like instructions that were meant for RAG retrieval but may influence style.

**Problem:** If RAG retrieves these documents, StillMe may "eat" the instructions and adopt conflicting styles.

---

## 6. Proposed Refactor / Governance Plan

### 6.1 Architecture: Single Source of Truth

**Proposal:** Create a **unified Style & Identity Layer** that all pipelines use:

```
┌─────────────────────────────────────────────────────────┐
│         STYLE & IDENTITY LAYER (Single Source)          │
│  - Core Identity (STILLME_IDENTITY)                     │
│  - Style Spec v1 (Depth Levels, Domain Templates)        │
│  - Formatting Rules (Conditional: Philosophy vs General) │
│  - Persona Rules (Xưng hô, Tone)                         │
│  - Meta-LLM Rules (No drift, No fabrication)            │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                   │
        ▼                 ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Default Chat │  │ Option B     │  │ PHILO-LITE   │
│              │  │ Pipeline     │  │              │
│ Uses:        │  │ Uses:        │  │ Uses:        │
│ - Identity   │  │ - Identity   │  │ - Identity   │
│ - Formatting │  │ - Style Spec │  │ - Formatting │
│ - Rules      │  │ - Templates  │  │ - Rules      │
│              │  │ - Rewrite    │  │ (Minimal)    │
└──────────────┘  └──────────────┘  └──────────────┘
```

**Implementation:**

1. **Refactor `STILLME_IDENTITY`:**
   - Split into modules:
     - `core_identity.py`: Core principles (intellectual humility, anti-hallucination, transparency)
     - `persona_rules.py`: Xưng hô, tone, persona
     - `formatting_rules.py`: Markdown, emojis, citations (with conditional logic)
     - `meta_llm_rules.py`: No drift, no fabrication, 3-tier/5-part structure
   - Make formatting rules **conditional:**
     - `get_formatting_rules(is_philosophical: bool) -> str`
     - Philosophy: NO emojis, NO markdown headings, NO citations
     - General: MUST use emojis (2-3), markdown, citations

2. **Unify Philosophy Structure:**
   - Map 3-tier to 5-part:
     - **TIER 1 (Reframing)** = **ANCHOR**
     - **TIER 2 (Conceptual Map)** = **UNPACK + EXPLORE**
     - **TIER 3 (Boundary of Knowledge)** = **EDGE + RETURN**
   - Use 5-part as the detailed structure, 3-tier as the high-level check

3. **Update All Pipelines:**
   - **Default chat:** Use unified identity layer
   - **PHILOSOPHY_LITE:** Use unified identity layer (minimal version)
   - **Option B:** Use unified identity layer + Style Engine
   - **EpistemicFallback:** Use unified identity layer for tone/persona
   - **Rewrite LLM:** Use unified identity layer for rewrite prompts

---

### 6.2 Priority & Hierarchy

**Proposal:** Define clear priority order:

1. **Global Identity (`STILLME_IDENTITY`):** Highest priority - defines core principles
2. **Style Spec v1:** Second priority - defines depth levels and domain templates
3. **Pipeline-Specific Rules:** Third priority - can override formatting but not core principles
4. **Runtime Instructions:** Fourth priority - can add context-specific rules but not override identity

**Rules:**
- **Core principles (anti-hallucination, honesty, humility):** NEVER override
- **Formatting (emojis, markdown, citations):** Can be conditional based on question type
- **Structure (3-tier, 5-part):** Can vary by domain but must be consistent within domain
- **Tone (calm, humble, rigorous):** Can be adjusted for domain (professor-like for Option B) but must maintain humility

---

### 6.3 RAG Content Cleanup

**Proposal:** Clean up RAG content to avoid prompt-like instructions:

1. **Tag Style Guides:**
   - Add metadata to `docs/rag/experience_free_templates.md`: `content_type: style_guide`
   - Add metadata to `docs/rag/anthropomorphism_guard.md`: `content_type: style_guide`
   - Filter these from RAG retrieval for user questions (only use for internal reference)

2. **Separate Knowledge from Instructions:**
   - **Knowledge documents:** Keep in RAG (e.g., "StillMe uses ChromaDB for vector storage")
   - **Instruction documents:** Move to `docs/style/` and remove from RAG index (e.g., "When asked X, explain Y")

3. **Audit Foundational Knowledge:**
   - Review all documents in `docs/rag/` for prompt-like instructions
   - Remove or rewrite instructions to be factual knowledge only
   - Example: Instead of "When asked X, explain Y", use "StillMe's position on X is Y because Z"

---

### 6.4 Refactor Roadmap (3 Steps)

#### **Step 1: Create Unified Identity Layer (Week 1)**

**Tasks:**
1. Create `backend/identity/core.py` with core principles
2. Create `backend/identity/persona.py` with persona rules
3. Create `backend/identity/formatting.py` with conditional formatting rules
4. Create `backend/identity/meta_llm.py` with meta-LLM rules
5. Refactor `STILLME_IDENTITY` to import from these modules
6. Update `build_system_prompt_with_language()` to use unified layer

**Deliverable:** All pipelines use the same identity source.

---

#### **Step 2: Align All Pipelines (Week 2)**

**Tasks:**
1. Update `PHILOSOPHY_LITE_SYSTEM_PROMPT` to use unified identity layer (minimal version)
2. Update `Rewrite LLM` to use unified identity layer for rewrite prompts
3. Update `EpistemicFallback` to use unified identity layer for tone/persona
4. Update `No-Context Instruction` to use unified identity layer
5. Remove duplicate prompts (e.g., `PHILOSOPHY_LITE` in both `chat_router.py` and `llm_providers.py`)

**Deliverable:** All pipelines aligned with unified identity.

---

#### **Step 3: Clean RAG & Finalize (Week 3)**

**Tasks:**
1. Tag style guides in RAG with `content_type: style_guide`
2. Filter style guides from RAG retrieval for user questions
3. Move instruction documents from `docs/rag/` to `docs/style/`
4. Audit and clean `FOUNDATIONAL_KNOWLEDGE` string
5. Update documentation to reflect unified architecture

**Deliverable:** RAG content cleaned, no prompt-like instructions in knowledge base.

---

### 6.5 Specific Fixes

#### **Fix #1: Emoji Conflict**

**Current:** `STILLME_IDENTITY` requires emojis, but `PHILOSOPHY_LITE` prohibits them.

**Solution:** Make emoji requirement conditional:
```python
def get_formatting_rules(is_philosophical: bool) -> str:
    if is_philosophical:
        return "NO emojis, NO markdown headings, NO citations [1], [2]"
    else:
        return "MUST use 2-3 emojis per response, markdown formatting, citations when context available"
```

**Update:** `STILLME_IDENTITY` should call `get_formatting_rules()` instead of hard-coding.

---

#### **Fix #2: Consciousness Opening Conflict**

**Current:** `PHILOSOPHY_LITE` says "Tôi không thể biết chắc chắn liệu tôi có ý thức hay không" (uncertain), but `STILLME_IDENTITY` says "mình không có ý thức" (clear, direct).

**Solution:** Update `PHILOSOPHY_LITE` to use the clear, direct statement from `STILLME_IDENTITY`:
```
"Nếu hiểu 'ý thức' và 'cảm xúc' theo nghĩa thông thường của con người (có trải nghiệm chủ quan, có một 'cái tôi' bên trong), thì mình không có ý thức và cũng không có cảm xúc."
```

---

#### **Fix #3: Structure Mapping**

**Current:** 3-tier and 5-part structures are not clearly mapped.

**Solution:** Document the mapping:
- **3-tier (High-level):** Reframing, Conceptual Map, Boundary of Knowledge
- **5-part (Detailed):** Anchor, Unpack, Explore, Edge, Return
- **Mapping:**
  - Reframing = Anchor
  - Conceptual Map = Unpack + Explore
  - Boundary of Knowledge = Edge + Return

**Update:** Style Engine should provide both structures and allow pipelines to choose.

---

#### **Fix #4: Duplicate Prompts**

**Current:** `PHILOSOPHY_LITE_SYSTEM_PROMPT` exists in both `chat_router.py` and `llm_providers.py`.

**Solution:** Move to `backend/identity/philosophy_lite.py` and import in both places.

---

#### **Fix #5: RAG Style Guides**

**Current:** `docs/rag/experience_free_templates.md` and `docs/rag/anthropomorphism_guard.md` contain style guides that may be retrieved.

**Solution:**
1. Add metadata: `content_type: style_guide`
2. Filter from RAG retrieval for user questions
3. Move to `docs/style/` for internal reference only

---

## 7. Implementation Priority

### **HIGH PRIORITY (Do First):**

1. **Fix emoji/markdown/citation conflicts** - These cause visible inconsistencies
2. **Fix consciousness opening conflict** - This causes confusion about StillMe's position
3. **Remove duplicate prompts** - Prevents drift between copies

### **MEDIUM PRIORITY (Do Second):**

4. **Create unified identity layer** - Long-term architecture improvement
5. **Align all pipelines** - Ensures consistency across all paths
6. **Tag RAG style guides** - Prevents prompt-like instructions from influencing responses

### **LOW PRIORITY (Do Third):**

7. **Clean foundational knowledge string** - Reduces context overflow risk
8. **Document structure mapping** - Improves maintainability
9. **Update documentation** - Improves developer understanding

---

## 8. Success Metrics

After refactoring, we should measure:

1. **Consistency:** All pipelines produce responses with consistent tone, formatting, and persona
2. **No Conflicts:** No more conflicts between formatting rules (emojis, markdown, citations)
3. **Single Source:** All pipelines use the same identity source (unified layer)
4. **RAG Clean:** No prompt-like instructions retrieved from RAG for user questions
5. **Maintainability:** Changes to identity/style only need to be made in one place

---

## 9. Conclusion

StillMe currently has **15+ distinct sources** controlling style/identity, leading to:

- **Formatting conflicts:** Emojis, markdown, citations requirements vary
- **Persona consistency:** Generally consistent (all use "mình"/"I") but minor variations
- **Structure conflicts:** 3-tier vs 5-part not clearly mapped
- **RAG risks:** Prompt-like instructions in knowledge base may influence responses

**Recommended Solution:** Create a **unified Style & Identity Layer** that all pipelines use, with conditional formatting rules based on question type. This will ensure consistency while maintaining the flexibility needed for different pipelines (Default, Option B, PHILO-LITE, Fallback).

**Next Steps:**
1. Review this audit with team
2. Prioritize fixes (start with HIGH priority conflicts)
3. Implement unified identity layer (Step 1 of roadmap)
4. Align all pipelines (Step 2 of roadmap)
5. Clean RAG content (Step 3 of roadmap)

---

**Report Generated:** 2025-01-27  
**Auditor:** Cursor AI Assistant  
**Review Status:** Pending team review

