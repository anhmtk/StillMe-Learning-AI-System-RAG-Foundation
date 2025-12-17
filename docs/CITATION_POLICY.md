# StillMe Citation Policy - Formal Rules

**Date**: 2025-01-27  
**Status**: Official Policy  
**Version**: 1.0

---

## Overview

StillMe's citation policy ensures **transparency** about knowledge sources while maintaining **clarity** and **usability**. This document provides **formal rules** for when citations are required, optional, or not needed.

---

## Core Principle

**"Every factual claim is cited, but the citation format depends on the knowledge type."**

This means:
- **Factual claims** → Require citation `[1]`, `[2]` from RAG context
- **General knowledge** → Optional citation `[general knowledge]` (well-established, pre-2023)
- **Reasoning** → No citation needed (StillMe's logical inference)
- **StillMe self-knowledge** → Uses `[foundational knowledge]` (StillMe's architecture)

---

## 1. Factual Claims (REQUIRES CITATION)

### Definition

Any statement about the external world that can be verified or falsified.

### Examples

- **Dates**: "Bretton Woods Conference 1944"
- **Events**: "World War II ended in 1945"
- **People**: "Keynes proposed the Bretton Woods system"
- **Places**: "Paris is the capital of France"
- **Scientific facts**: "Photosynthesis converts CO2 to glucose"
- **Historical facts**: "The Vietnam War ended in 1975"

### Rule

**MUST cite `[1]`, `[2]` from RAG context.**

If no RAG context is available:
- Use `[general knowledge]` with explanation: "This is general knowledge from base LLM training data, not verified against StillMe's RAG knowledge base."
- StillMe should express uncertainty: "Mình không có thông tin này trong RAG knowledge base, nhưng theo kiến thức tổng quát..."

### Implementation

- `CitationRequired` validator enforces this
- `KnowledgeTypeClassifier` classifies claims as `FACTUAL_CLAIM`
- Auto-patching adds citation if missing

---

## 2. General Knowledge (CITATION OPTIONAL)

### Definition

Well-established facts that are:
- In base LLM training data (pre-2023 cutoff)
- Not disputed in academic literature
- Not time-sensitive

### Examples

- **Scientific facts**: "Water is H2O"
- **Mathematical facts**: "2+2=4"
- **Historical facts**: "Shakespeare wrote Hamlet"
- **Geographical facts**: "Earth orbits the sun"
- **Physical laws**: "Gravity exists"

### Rule

**Can use `[general knowledge]` without RAG citation**, but must acknowledge:

"This is general knowledge from base LLM training data, not verified against StillMe's RAG knowledge base."

### When to Use

- No RAG context available
- Claim is well-established (not disputed)
- Claim is not time-sensitive
- Claim is common knowledge (not specialized)

### Implementation

- `KnowledgeTypeClassifier` classifies as `GENERAL_KNOWLEDGE`
- `CitationRequired` validator allows `[general knowledge]` for this type
- StillMe should still express uncertainty if no RAG verification

---

## 3. Reasoning (NO CITATION NEEDED)

### Definition

Logical inference, philosophical analysis, mathematical proofs, or StillMe's own reasoning.

### Examples

- **Logical inference**: "If A then B, therefore C"
- **Philosophical analysis**: "From a utilitarian perspective, the action is justified because..."
- **Mathematical proof**: "By induction, we can prove that..."
- **StillMe's reasoning**: "Based on the evidence provided, StillMe concludes that..."

### Rule

**No citation needed** - this is StillMe's reasoning, not factual claims.

### When to Use

- Answer involves logical inference
- Answer involves philosophical analysis
- Answer involves mathematical reasoning
- Answer is StillMe's own conclusion based on provided evidence

### Implementation

- `KnowledgeTypeClassifier` classifies as `REASONING`
- `CitationRequired` validator skips citation requirement for this type
- StillMe can reason without citations

---

## 4. StillMe Self-Knowledge (FOUNDATIONAL KNOWLEDGE)

### Definition

Information about StillMe itself (architecture, capabilities, limitations, learning process).

### Examples

- **Architecture**: "StillMe uses RAG with ChromaDB"
- **Capabilities**: "StillMe learns every 4 hours"
- **Limitations**: "StillMe cannot answer questions about events < 4 hours old"
- **Learning process**: "StillMe fetches content from RSS feeds, arXiv, CrossRef, Wikipedia"

### Rule

**Uses `[foundational knowledge]`** - StillMe's self-knowledge, not external sources.

### When to Use

- Question is about StillMe itself
- Answer describes StillMe's architecture, capabilities, or limitations
- Answer explains StillMe's learning process or validation chain

### Implementation

- `KnowledgeTypeClassifier` classifies as `STILLME_SELF_KNOWLEDGE`
- `CitationRequired` validator uses `[foundational knowledge]` for this type
- StillMe should prioritize foundational knowledge from RAG context

---

## Classification Algorithm

The `KnowledgeTypeClassifier` uses this decision tree:

```
1. Is claim about StillMe?
   → YES: STILLME_SELF_KNOWLEDGE
   → NO: Continue

2. Does claim have RAG context?
   → YES: FACTUAL_CLAIM (requires citation)
   → NO: Continue

3. Is claim logical inference/reasoning?
   → YES: REASONING (no citation)
   → NO: Continue

4. Is claim well-established fact (common knowledge, pre-2023)?
   → YES: GENERAL_KNOWLEDGE (citation optional)
   → NO: Continue

5. Does claim have factual indicators (dates, events, people, places)?
   → YES: FACTUAL_CLAIM (requires citation)
   → NO: FACTUAL_CLAIM (default, requires citation)
```

---

## Citation Formats

### RAG-Grounded Citations

- **Format**: `[1]`, `[2]`, `[3]`
- **Meaning**: Information from StillMe's RAG knowledge base
- **Verification**: Validated against retrieved context documents

### General Knowledge Citations

- **Format**: `[general knowledge]`
- **Meaning**: Well-established fact from base LLM training data (pre-2023)
- **Verification**: Not verified against StillMe's RAG knowledge base

### Foundational Knowledge Citations

- **Format**: `[foundational knowledge]`
- **Meaning**: Information about StillMe itself
- **Verification**: From StillMe's foundational knowledge documents

### No Citation

- **Format**: (no citation)
- **Meaning**: StillMe's reasoning, logical inference, or philosophical analysis
- **Verification**: Not applicable (reasoning, not factual claim)

---

## Edge Cases

### 1. Mixed Claims

**Scenario**: Answer contains both factual claims and reasoning.

**Rule**: Cite factual claims, but reasoning doesn't need citation.

**Example**:
> "Bretton Woods Conference 1944 [1] established the IMF. From an economic perspective, this was significant because..."

- "Bretton Woods Conference 1944" → Factual claim → `[1]`
- "From an economic perspective..." → Reasoning → No citation

### 2. Factual Claims Without RAG Context

**Scenario**: User asks about a factual topic, but StillMe has no RAG context.

**Rule**: Use `[general knowledge]` with uncertainty expression.

**Example**:
> "Mình không có thông tin về [topic] trong RAG knowledge base, nhưng theo kiến thức tổng quát, [answer] [general knowledge]"

### 3. StillMe Questions with RAG Context

**Scenario**: User asks about StillMe, and RAG context contains foundational knowledge.

**Rule**: Use `[foundational knowledge]` and prioritize RAG context over base LLM knowledge.

**Example**:
> "StillMe uses RAG with ChromaDB [foundational knowledge]. According to StillMe's foundational knowledge documents [1], StillMe learns every 4 hours."

---

## Validation

### Validators

1. **`CitationRequired`**: Enforces citation requirement based on knowledge type
2. **`KnowledgeTypeClassifier`**: Classifies claims into knowledge types
3. **`CitationRelevance`**: Validates that citations are actually relevant

### Auto-Patching

- If citation is missing for `FACTUAL_CLAIM`, `CitationRequired` auto-adds citation
- If citation format is wrong, validators can patch it
- If knowledge type is misclassified, `KnowledgeTypeClassifier` can correct it

---

## Transparency

StillMe is transparent about:
- **Knowledge source**: RAG-grounded vs general knowledge vs foundational knowledge
- **Verification status**: Verified against RAG vs unverified (general knowledge)
- **Reasoning**: When StillMe is reasoning vs stating facts

---

## Revision History

- **2025-01-27**: Initial formal policy document
- Created to address ambiguity in citation policy
- Based on architectural review findings

---

## References

- `stillme_core/knowledge/type_classifier.py`: Implementation
- `stillme_core/validation/citation.py`: Citation enforcement
- `docs/ANALYSIS_GENERAL_KNOWLEDGE_CITATION.md`: Analysis of general knowledge citations

