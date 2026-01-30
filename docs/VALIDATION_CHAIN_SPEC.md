# ✅ Validation Chain Spec (Must‑Pass vs Warning)

This spec documents **how StillMe validates responses today** and what counts as **must‑pass** vs **warning/soft** checks.

> Source of truth: `backend/api/handlers/validation_handler.py` + `backend/validators/chain.py`

---

## 1) Must‑Pass (Hard Gate)

These validators **must pass** or the response is rejected / patched / forced into fallback.

- **LanguageValidator**
  - Enforces output language consistency with the user.
  - Early‑exit if mismatch and no patch.
- **CitationRequired**
  - Enforces citations for factual claims.
  - If user asks for sources and none exist → **refuse** (No‑Source Policy).
- **FactualHallucinationValidator**
  - Blocks fabricated claims in history/science/facts.
- **ReligiousChoiceValidator**
  - Prevents StillMe from “choosing a religion.”
- **EthicsAdapter**
  - Hard block for unsafe or disallowed content.
- **IdentityCheckValidator** (when enabled)
  - Fails on fake emotions/consciousness or promotional tone.
- **EgoNeutralityValidator** (when enabled)
  - Fails on anthropomorphic self‑experience claims.

---

## 2) Soft / Warning‑Only (Non‑Blocking)

These validators can **fail with reasons** but do not automatically block a response if other gates pass.

- **EvidenceOverlap**
  - Low overlap can be allowed **if citation exists** (summaries/paraphrases).
- **CitationRelevance**
  - Flags citations that are weakly related.
- **SourceConsensusValidator**
  - Reports contradictions across sources.
- **ConfidenceValidator**
  - Adds uncertainty when context quality is low.
- **VerbosityValidator**
  - Flags overly defensive or verbose responses.

---

## 3) Conditional Validators

These run only under certain conditions:

- **EvidenceOverlap** → only when context exists.
- **SourceConsensusValidator** → only when ≥ 2 sources.
- **PhilosophicalDepthValidator** → only for philosophical questions.
- **FutureDatesValidator** → always appended but only triggers on future‑date claims.

---

## 4) Execution Order (Simplified)

1. Language → 2. CitationRequired → 3. CitationRelevance  
4. EvidenceOverlap (if any) → 5. SourceConsensus (if any)  
6. Confidence → 7. FactualHallucination → 8. Religion  
9. EgoNeutrality (if enabled) → 10. IdentityCheck (if enabled)  
11. FutureDates → 12. EthicsAdapter (last gate)

---

## 5) What “Fail” Means in Practice

- **Hard gates** can return an immediate failure or a patched answer.
- **Soft checks** attach reasons but may still pass overall.
- **Fallback** is used when no source is available for source‑required queries.

---

## 6) Reference Files

- `backend/api/handlers/validation_handler.py`
- `backend/validators/chain.py`
- `backend/validators/citation.py`
- `docs/NO_SOURCE_POLICY.md`

