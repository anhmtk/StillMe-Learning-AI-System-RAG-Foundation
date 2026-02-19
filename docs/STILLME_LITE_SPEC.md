# StillMe Lite v0.1 Spec

This document defines a minimal integration profile for teams that want a fast, low-overhead verification layer in front of or after LLM responses.

---

## 1) Product Intent

StillMe Lite is a **verification-first framework module** for reducing factual hallucination risk with explicit, auditable decisions.

Design goals:
- Easy to install
- Easy to integrate in existing RAG/chat pipelines
- Clear refusal behavior when evidence is missing
- Structured output for logging and downstream policy actions

---

## 2) Scope and Non-Goals

### In Scope
- Factual claim checking with source-aware behavior
- Source-required detection and no-source refusal behavior
- Lightweight validator decision output (`answer`, `refuse`, `ask_clarify`)
- Monitor-first rollout (`monitor`, `warn`, `enforce`)

### Out of Scope (v0.1)
- Full enterprise compliance certification
- Vertical-specific legal advice
- Perfect hallucination elimination
- Autonomous model retraining

---

## 3) Integration Contract

### 3.1 Input Schema

```json
{
  "request_id": "optional string",
  "query": "user question",
  "draft_answer": "optional model answer before verification",
  "retrieved_context": [
    {
      "source_id": "doc-123",
      "title": "optional",
      "url": "optional",
      "timestamp": "optional",
      "text": "retrieved chunk text",
      "similarity": 0.71
    }
  ],
  "metadata": {
    "language": "vi|en|auto",
    "domain": "optional",
    "session_id": "optional"
  }
}
```

### 3.2 Output Schema

```json
{
  "request_id": "echoed or generated",
  "decision": "answer|refuse|ask_clarify",
  "mode": "monitor|warn|enforce",
  "source_required": true,
  "confidence_band": "low|medium|high",
  "reasons": [
    "source_required_no_context",
    "low_context_similarity"
  ],
  "validator_trace_id": "trace-uuid",
  "citations": [
    {
      "source_id": "doc-123",
      "url": "https://...",
      "timestamp": "2026-02-18T10:30:00Z"
    }
  ],
  "safe_response": "optional rewritten answer/refusal",
  "metrics": {
    "max_similarity": 0.39,
    "context_count": 6
  }
}
```

### 3.3 Decision Semantics

- `answer`: evidence is sufficient and policy conditions pass.
- `refuse`: evidence is missing/insufficient for factual claim or policy blocks answer.
- `ask_clarify`: user intent is ambiguous, scope too broad, or question requires narrowing before trustworthy response.

---

## 4) Runtime Modes

### `monitor`
- Does not block model output.
- Emits full decision and reason codes for evaluation only.
- Recommended default for first deployment.

### `warn`
- Allows answer but attaches warning metadata and optional user-facing disclaimer.
- Use after baseline is stable.

### `enforce`
- Applies strict policy actions (`refuse`/`ask_clarify`) from validator decisions.
- Use only after monitor/warn evaluation passes thresholds.

---

## 5) Required Reason Codes (v0.1)

Minimum standard codes:
- `source_required_no_context`
- `source_required_low_similarity`
- `citation_missing_for_factual_claim`
- `ambiguous_query_needs_clarification`
- `policy_block_anthropomorphic_roleplay`
- `policy_block_unsafe_content`
- `context_conflict_low_consensus`
- `passed_with_warnings`

Reason codes are for humans and machines: they power logs, dashboards, and incident review.

---

## 6) Policy Config (Single File)

Path: `policy.yaml`

Example:

```yaml
mode: monitor

thresholds:
  min_similarity_for_factual: 0.45
  min_similarity_for_source_required: 0.50

behavior:
  enforce_no_source_refusal: true
  enforce_anti_anthropomorphism: true
  allow_soft_answer_with_warning: false

output:
  include_validator_trace: true
  include_reason_codes: true
```

---

## 7) Minimal Integration Patterns

### Pattern A: Post-Generation Guard (fastest)
1. LLM generates draft answer.
2. StillMe Lite validates draft against retrieved context.
3. Router returns safe response or refusal based on decision.

Best when the existing app already has retrieval and generation.

### Pattern B: Middleware Guard
1. Query + context pass through StillMe Lite first.
2. If high risk, trigger `refuse` or `ask_clarify` before final answer generation.
3. Otherwise continue normal generation path.

Best when teams want early policy enforcement.

---

## 8) Rollout Checklist

- [ ] Start in `monitor` mode for 7-14 days
- [ ] Log `decision`, `reasons`, `confidence_band`, `trace_id` for every request
- [ ] Measure baseline metrics (escape rate, refusal precision, source coverage)
- [ ] Review false refusals and missing refusals weekly
- [ ] Move to `warn` mode only after metric improvement is stable
- [ ] Move to `enforce` mode only after agreed thresholds are met

---

## 9) Mandatory Evaluation Metrics

- `hallucination_escape_rate`: fraction of unsupported factual claims that still pass as answer.
- `refusal_precision`: among refused cases, fraction where refusal is actually correct.
- `source_coverage`: fraction of factual answers with valid source attribution.

See `docs/CASE_STUDY_TEMPLATE.md` for dataset protocol and reporting format.

---

## 10) Known Limitations (Must Disclose)

- StillMe Lite reduces risk; it does not guarantee perfect factual correctness.
- Retrieval quality strongly affects verification outcomes.
- Domain-specific policy tuning may be required.
- Strict refusal policies can reduce answer rate in low-context environments.

---

## 11) Positioning Statement (Public Interest)

StillMe Lite is designed as a **practical, open framework** for teams that prioritize auditability and factual integrity over fluent but unverifiable output.

