# Log Selection Guide for Documentation

## 🎯 Purpose

This guide helps select and format backend logs for documentation, showcasing StillMe's technical capabilities and transparency.

## ✅ Logs Worth Capturing

### 1. **RAG Retrieval Process** (Shows Vector Search)

**Example:**
```
[INFO] Query embedding generated: 384 dimensions
[INFO] Found 3 CRITICAL_FOUNDATION documents
[INFO] Retrieved 3 StillMe foundational knowledge documents
[INFO] ⏱️ RAG retrieval took 3.30s
```

**Why**: Shows RAG working, vector search, retrieval time
**Use in**: Architecture docs, RAG explanation

---

### 2. **Validation Chain Execution** (Shows Multi-Layer Validation)

**Example:**
```
[INFO] ValidatorChain initialized with 13 validators
[INFO] Validator 1 (CitationRequired) fixed missing_citation with patched_answer
[WARNING] Ego-Neutrality Validator detected anthropomorphic language: ['trải nghiệm']
[INFO] Ego-Neutrality Validator auto-patched anthropomorphic language
[INFO] ⏱️ Validation took 3.22s
```

**Why**: Shows validation chain, auto-fix mechanisms, transparency
**Use in**: Validation Chain docs, Paper

---

### 3. **Auto-Fix Mechanisms** (Shows Self-Correction)

**Example:**
```
[WARNING] Missing citation in answer (context documents available but no citations found)
[INFO] Auto-added foundational knowledge citation '[foundational knowledge]' to response
[INFO] Validator 1 (CitationRequired) fixed missing_citation with patched_answer
```

**Why**: Shows StillMe can self-correct, not just detect issues
**Use in**: Validation docs, Transparency showcase

---

### 4. **Performance Metrics** (Shows Latency Breakdown)

**Example:**
```
--- LATENCY METRICS ---
RAG_Retrieval_Latency: 3.30 giây
LLM_Inference_Latency: 5.41 giây
Total_Response_Latency: 12.04 giây
------------------------
```

**Why**: Shows performance, transparency about costs
**Use in**: Architecture docs, Performance section

---

### 5. **Context Overflow Handling** (Shows Smart Truncation)

**Example:**
```
[WARNING] ⚠️ Pre-check: Estimated tokens (16654) exceed safe limit (15000)
[INFO] 🔄 Using minimal philosophical prompt (pre-check prevention)
```

**Why**: Shows StillMe handles edge cases intelligently
**Use in**: Architecture docs, Limitations section

---

### 6. **Learning Proposal Generation** (Shows Continuous Learning)

**Example:**
```
[INFO] Detected valuable question from user (score: 0.70)
[INFO] Learning proposal generated (id: e82d41b6-7991-4311-90c0-c05baf30ec08, score: 0.70)
```

**Why**: Shows continuous learning in action
**Use in**: Learning Pipeline docs, Paper

---

### 7. **Epistemic State Classification** (Shows Self-Awareness)

**Example:**
```
[INFO] 📊 EpistemicState: KNOWN (confidence=0.80, ctx_docs=3)
```

**Why**: Shows StillMe knows what it knows
**Use in**: Transparency docs, Paper

---

## ❌ Logs to Avoid

### 1. **Error Logs** (Unless Showing Error Handling)
```
[ERROR] Failed to build prompt context: name 'content_type' is not defined
```
→ Only include if showing how StillMe handles errors gracefully

### 2. **Sensitive Information**
```
[INFO] API key: sk-xxxxx
[INFO] User ID: 12345
```
→ NEVER include API keys, user IDs, or personal data

### 3. **Verbose Debug Logs**
```
[TRACE] Before final_response assignment: response=Tôi không có cảm xúc...
[TRACE] After final_response assignment: response=Tôi không có cảm xúc...
```
→ Too verbose, not useful for documentation

### 4. **Progress Bars**
```
Batches:   0%|          | 0/1 [00:00<?, ?it/s]
Batches: 100%|██████████| 1/1 [00:03<00:00,  3.25s/it]
```
→ Not informative, just noise

---

## 📝 Formatting Guidelines

### 1. **Sanitize First**
- Remove API keys
- Remove user data
- Remove IP addresses (if sensitive)
- Remove timestamps (or use relative time)

### 2. **Annotate**
Add comments explaining what each log shows:
```markdown
## RAG Retrieval Process

```log
[INFO] Query embedding generated: 384 dimensions  ← Vector embedding created
[INFO] Found 3 CRITICAL_FOUNDATION documents      ← Found relevant knowledge
[INFO] ⏱️ RAG retrieval took 3.30s              ← Performance metric
```
```

### 3. **Group Related Logs**
Group logs by feature/process:
```markdown
### Validation Chain Execution

```log
[INFO] ValidatorChain initialized with 13 validators
[INFO] Validator 1 (CitationRequired) fixed missing_citation
[INFO] ⏱️ Validation took 3.22s
```
```

### 4. **Highlight Key Points**
Use bold or annotations:
```markdown
**Key Points:**
- ✅ 13 validators run sequentially
- ✅ Auto-fix mechanisms work
- ✅ Validation takes ~3s
```

---

## 🎨 Presentation Styles

### Style 1: **Minimal** (For README)
```markdown
StillMe's validation chain runs 13 validators in 3.22s:

```log
[INFO] ValidatorChain initialized with 13 validators
[INFO] ⏱️ Validation took 3.22s
```
```

### Style 2: **Annotated** (For Technical Docs)
```markdown
## Validation Chain Execution

StillMe runs 13 validators sequentially:

```log
[INFO] ValidatorChain initialized with 13 validators  ← All validators loaded
[INFO] Validator 1 (CitationRequired) fixed missing_citation  ← Auto-fix works
[INFO] ⏱️ Validation took 3.22s  ← Performance metric
```

**What this shows:**
- Multi-layer validation
- Auto-correction capabilities
- Performance transparency
```

### Style 3: **Visual** (For Paper/Blog)
Create a diagram showing log flow:
```
User Query
    ↓
RAG Retrieval (3.30s)
    ↓
LLM Inference (5.41s)
    ↓
Validation Chain (3.22s)
    ↓
Response (12.04s total)
```

---

## 📍 Where to Use Logs

### ✅ Good Places:
1. `docs/ARCHITECTURE.md` - Show system flow
2. `docs/VALIDATION_CHAIN.md` - Show validation process
3. `docs/PAPER.md` - Show technical depth
4. `README.md` (Architecture section) - Brief examples
5. Blog posts - Transparency showcase

### ❌ Avoid:
1. Main README intro - Too technical
2. User guides - Users don't need this
3. Marketing materials - Too detailed

---

## 🔍 Example: Complete Log Selection

### Original Log (Too Verbose):
```
2025-12-06T06:01:04.176581950Z [inf]  2025-12-06 06:01:03,063 [INFO] 📥 Received chat request
2025-12-06T06:01:04.176593284Z [inf]  2025-12-06 06:01:03,064 [INFO] Philosophical question detected
2025-12-06T06:01:07.033589591Z [inf]  2025-12-06 06:01:06,374 [INFO] Query embedding generated: 384 dimensions
2025-12-06T06:01:07.179850141Z [inf]  2025-12-06 06:01:06,396 [INFO] Found 3 CRITICAL_FOUNDATION documents
2025-12-06T06:01:07.179920095Z [inf]  2025-12-06 06:01:06,409 [INFO] Retrieved 3 StillMe foundational knowledge documents
2025-12-06T06:01:07.179939398Z [inf]  2025-12-06 06:01:06,409 [INFO] ⏱️ RAG retrieval took 3.30s
```

### Selected & Formatted (Documentation-Ready):
```markdown
## RAG Retrieval Process

StillMe retrieves relevant knowledge from its vector database:

```log
[INFO] Query embedding generated: 384 dimensions
[INFO] Found 3 CRITICAL_FOUNDATION documents
[INFO] Retrieved 3 StillMe foundational knowledge documents
[INFO] ⏱️ RAG retrieval took 3.30s
```

**What this shows:**
- Vector search using 384-dimensional embeddings
- Foundational knowledge retrieval
- Performance: 3.30s retrieval time
```

---

## ✅ Checklist Before Publishing

- [ ] Removed API keys
- [ ] Removed user data
- [ ] Removed sensitive information
- [ ] Added annotations/explanations
- [ ] Grouped related logs
- [ ] Highlighted key points
- [ ] Used appropriate style for audience
- [ ] Added context (what this shows)

---

## 🎯 Quick Reference

| Log Type | Use In | Style |
|----------|--------|-------|
| RAG Retrieval | Architecture, RAG docs | Annotated |
| Validation Chain | Validation docs, Paper | Visual + Annotated |
| Auto-Fix | Transparency showcase | Minimal + Highlight |
| Performance | Architecture, Paper | Minimal |
| Learning | Learning Pipeline docs | Annotated |
| Epistemic State | Transparency docs | Minimal |

---

**Last Updated**: 2025-12-06

