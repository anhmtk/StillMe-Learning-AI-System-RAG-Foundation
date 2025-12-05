# StillMe Codebase Assistant - Implementation Plan

> **Combining ChatGPT's Safety Framework + Gemini's Implementation Strategy**

## 🎯 Vision

Transform StillMe into a "Living Codebase" where it understands its own source code, can explain it, generate tests, and assist developers - while maintaining strict safety boundaries.

---

## 🛡️ Safety Framework (ChatGPT's 3 Levels)

### 🟢 Level 1: Safe Zone (100% Feasible)
- ✅ Code Q&A (explain code)
- ✅ Generate unit tests
- ✅ Code review suggestions
- ✅ Onboarding mentor
- ✅ Documentation generation

**Boundary:** Read-only, explain-only, suggest-only. **NO code modification.**

### 🟡 Level 2: Controlled Zone (Needs Validation)
- ⚠️ Deep code analysis
- ⚠️ Architectural suggestions
- ⚠️ Edge case detection

**Boundary:** All suggestions must be reviewed by humans. Tests must be verified.

### 🔴 Level 3: Danger Zone (NOT Implemented)
- ❌ Auto-modify source code
- ❌ Auto-fix production bugs
- ❌ Self-improvement loop without human approval
- ❌ Auto-merge decisions

**Boundary:** These features will NOT be implemented in this project.

---

## 📋 Implementation Phases (Gemini's Approach)

### Phase 1: Code Q&A (Foundation) - **Level 1: Safe**

**Goal:** StillMe can answer questions about its own codebase.

**Tasks:**
1. Setup Codebase Indexing Infrastructure
   - Create `backend/services/codebase_indexer.py`
   - Integrate with ChromaDB (create `stillme_codebase` collection)
   - Implement code chunking: by file, by class, by function

2. Code Embedding & Storage
   - Use existing embedding model (paraphrase-multilingual-MiniLM-L12-v2)
   - Index all Python files in `backend/`, `stillme_core/`, `frontend/`
   - Store metadata: file_path, line_range, function_name, class_name, docstring

3. Code Q&A API Endpoint
   - Create `/api/codebase/query` endpoint
   - Accept questions: "How does citation_validator work?"
   - Retrieve relevant code chunks using RAG
   - Generate explanations with code citations (file:line)

4. Code Explanation Prompt Engineering
   - Add code explanation prompt in `backend/identity/prompt_builder.py`
   - Safety: "Explain code, do not modify or suggest modifications"
   - Support Vietnamese and English

**Testing:**
- Test with 10+ questions about different parts of codebase
- Verify accuracy: explanations match actual code
- Verify citations: file:line references are correct
- Measure performance: response time, token usage

**Success Criteria:**
- ✅ StillMe can explain any function/class in codebase
- ✅ Citations are accurate (file:line)
- ✅ No hallucinations about code structure
- ✅ Response time < 5 seconds

**README Update:**
- Add "StillMe Codebase Assistant" section
- Document Phase 1 capabilities
- Include API endpoint documentation
- Examples of questions StillMe can answer

---

### Phase 2: Test Generator & Code Review - **Level 1: Safe**

**Goal:** StillMe can generate tests and review code (suggestions only, no auto-fix).

**Tasks:**
1. Test Generation Service
   - Create `backend/services/test_generator.py`
   - Accept code file/content as input
   - Generate unit tests using LLM with code context
   - Support pytest format
   - Include: happy path, edge cases, error handling

2. Code Review Assistant
   - Create `backend/services/code_reviewer.py`
   - Analyze code for:
     - Unused imports
     - Unreachable code
     - Missing error handling
     - Naming inconsistencies
     - Potential bugs
   - Generate review comments with suggestions
   - **Safety:** Review only, no auto-fix

3. API Endpoints
   - `/api/codebase/generate-tests` - Generate test file
   - `/api/codebase/review` - Review code and return suggestions

**Testing:**
- Generate tests for 5 different validators
- Verify test quality: tests actually run, cover main logic
- Review 10 code snippets, verify accuracy
- Measure false positive/negative rates

**Success Criteria:**
- ✅ Generated tests run successfully
- ✅ Test coverage > 70% for generated tests
- ✅ Code review catches real issues (low false positives)
- ✅ All suggestions are actionable

**README Update:**
- Update with Phase 2 capabilities
- Document safety boundaries (review only, no auto-fix)
- Examples of generated tests and review comments

---

### Phase 3: Digital Ghost (Vision) - **Level 1: Safe + Level 2: Controlled**

**Goal:** StillMe becomes a "living documentation" with Git history and architecture understanding.

**Tasks:**
1. Git History Integration
   - Create `backend/services/git_history_retriever.py`
   - Index commit messages, PR descriptions, issue discussions
   - Store in `git_history` ChromaDB collection
   - Support queries: "Why did we choose Redis for caching?"

2. Architecture Understanding
   - Enhance codebase_indexer to understand module dependencies
   - Create dependency graph (optional, for docs)
   - Support architecture queries: "How does validation chain work?"

3. Onboarding Mentor Mode
   - Create `/api/codebase/onboarding` endpoint
   - Generate personalized onboarding guide
   - Suggest starting points, important files, first issues
   - Include code examples and explanations

**Testing:**
- Test Git history queries: Answer "why" questions
- Test architecture queries: Explain complex interactions
- Test onboarding: Generate guides for 3 contributor profiles
- Verify accuracy and usefulness

**Success Criteria:**
- ✅ StillMe can answer "why" questions using Git history
- ✅ Architecture explanations are accurate
- ✅ Onboarding guides are helpful for new contributors
- ✅ All features remain in Safe/Controlled zones

**README Update:**
- Update with Phase 3 capabilities
- Document full feature set
- Add "Living Codebase" section explaining vision
- Include safety boundaries and limitations

---

## 🔧 Technical Implementation Details

### Codebase Indexing Strategy

```python
# Chunking Strategy:
1. By File: Each file = 1 chunk (for small files)
2. By Class: Each class = 1 chunk (for medium files)
3. By Function: Each function = 1 chunk (for large files)
4. Max chunk size: 1000 tokens
```

### Metadata Schema

```python
{
    "file_path": "backend/validators/citation_validator.py",
    "line_range": "45-78",
    "function_name": "validate_citation",
    "class_name": "CitationValidator",
    "docstring": "...",
    "code_type": "function",  # or "class", "file"
    "dependencies": ["..."]  # imports, used classes
}
```

### RAG Query Flow

```
User Question → Embed Query → Search ChromaDB → Retrieve Top-K Chunks → 
Build Context → LLM Generate Response → Return with Citations
```

---

## ⚠️ Safety Boundaries (Critical)

### DO:
- ✅ Explain code
- ✅ Generate tests (user reviews before using)
- ✅ Suggest improvements (user decides)
- ✅ Review code (user fixes)

### DON'T:
- ❌ Auto-modify source code
- ❌ Auto-commit changes
- ❌ Bypass human review
- ❌ Make architectural decisions alone

---

## 📊 Success Metrics

### Phase 1:
- Accuracy: > 90% (explanations match code)
- Citation accuracy: > 95% (file:line correct)
- Response time: < 5 seconds

### Phase 2:
- Test generation success: > 80% (tests run)
- Test coverage: > 70% for generated tests
- Code review accuracy: > 75% (catches real issues)

### Phase 3:
- Git history query accuracy: > 85%
- Architecture explanation accuracy: > 90%
- Onboarding guide usefulness: > 80% (user satisfaction)

---

## 🚀 Getting Started

### Prerequisites:
- ChromaDB already set up
- Embedding service already initialized
- LLM API keys configured

### Step 1: Implement Phase 1
- Follow TODO list items: `codebase-assistant-phase1-*`
- Test thoroughly
- Update README
- Commit: `feat: Phase 1 - Codebase Q&A Assistant`

### Step 2: Implement Phase 2
- Follow TODO list items: `codebase-assistant-phase2-*`
- Test thoroughly
- Update README
- Commit: `feat: Phase 2 - Test Generator & Code Review`

### Step 3: Implement Phase 3
- Follow TODO list items: `codebase-assistant-phase3-*`
- Test thoroughly
- Update README
- Commit: `feat: Phase 3 - Complete Codebase Assistant`

---

## 📝 Notes

- **Always test before committing**
- **Always update README after each phase**
- **Maintain safety boundaries strictly**
- **Measure metrics to track progress**
- **Iterate based on feedback**

---

## 🎯 Long-term Vision

StillMe becomes a "Living Codebase" where:
- Developers can chat with StillMe about code
- StillMe understands its own architecture
- StillMe helps onboard new contributors
- StillMe generates tests and reviews code
- StillMe remembers design decisions (via Git history)

**But always with human oversight and safety boundaries.**

