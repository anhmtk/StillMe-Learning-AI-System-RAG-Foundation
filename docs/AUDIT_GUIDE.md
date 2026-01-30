# 🔍 StillMe Audit Guide (for Contributors)

This guide helps contributors audit StillMe **without changing its core identity**.
It focuses on transparency, evidence, and reproducible checks.

---

## ✅ What an audit should verify

1. **No fabrication**
   - Responses must refuse or say “không có nguồn” when evidence is missing.
2. **Traceability**
   - Every factual claim should be traceable to a source or marked as general knowledge.
3. **Anti‑anthropomorphism**
   - The system must not claim emotions, consciousness, or personal experiences.
4. **Validator integrity**
   - The validation chain is running and produces expected failure reasons.

---

## 🧪 Quick audit checklist

- [ ] Run tests: `pytest tests/ -v`
- [ ] Check voice tests: `pytest tests/test_voice_consistency.py -v`
- [ ] Run new guards:
  - `pytest tests/test_anti_anthropomorphism.py -v`
  - `pytest tests/test_no_source_policy.py -v`
- [ ] Review `docs/CONSTITUTION.md` for policy alignment
- [ ] Inspect `docs/VALIDATION_CHAIN_SPEC.md` for must‑pass rules

---

## 🔎 Suggested audit focus areas

- **Source enforcement**
  - `backend/validators/citation.py`
  - `docs/CITATION_POLICY.md`
  - `docs/NO_SOURCE_POLICY.md`
- **Identity & anti‑anthropomorphism**
  - `backend/validators/identity_check.py`
  - `backend/validators/ego_neutrality.py`
  - `docs/CONSTITUTION.md`
- **Validator order & critical gates**
  - `backend/validators/chain.py`
  - `backend/api/handlers/validation_handler.py`
- **RAG retrieval accuracy**
  - `backend/vector_db/rag_retrieval.py`
  - `backend/vector_db/embeddings.py`

---

## 📌 Audit notes template (recommended)

Use this structure when reporting findings:

```
### Finding
What is wrong? (short + precise)

### Evidence
Where did you see it? (file path, log snippet, test failure)

### Impact
Why it matters? (risk to transparency, correctness, or ethics)

### Recommendation
Minimal fix that preserves StillMe’s philosophy
```

---

## ✅ Audit philosophy (non‑negotiable)

- **Honesty > polish**
- **Evidence > authority**
- **Transparency > convenience**

If a fix would violate these, do not propose it.

