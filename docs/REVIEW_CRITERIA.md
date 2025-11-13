# StillMe Peer Review Criteria

> **Academic Review Standards for Learning Proposal Evaluation**

This document defines the criteria StillMe uses to evaluate learning proposals and new knowledge, inspired by peer review standards from ICLR, AAAI, and other academic conferences.

---

## Core Evaluation Criteria

### 1. **Novelty (Tính Mới)**
- **High (8-10)**: Introduces genuinely new concepts, methods, or perspectives not commonly found in StillMe's knowledge base
- **Medium (5-7)**: Presents known concepts but with new applications, combinations, or interpretations
- **Low (0-4)**: Purely repetitive of existing knowledge without new insights

**Questions to consider:**
- Does this proposal introduce something StillMe doesn't already know?
- Is this a novel combination of existing concepts?
- Does this provide a new perspective on a known topic?

### 2. **Feasibility (Tính Khả Thi)**
- **High (8-10)**: Clearly implementable, well-defined, with concrete steps
- **Medium (5-7)**: Generally feasible but may require clarification or additional resources
- **Low (0-4)**: Vague, unrealistic, or requires resources beyond StillMe's capabilities

**Questions to consider:**
- Can StillMe actually learn this from available sources?
- Are the learning steps clear and achievable?
- Does this align with StillMe's learning mechanisms (RAG, multi-source learning)?

### 3. **Relevance (Tính Liên Quan)**
- **High (8-10)**: Directly relevant to StillMe's mission (AI transparency, ethics, RAG, learning systems)
- **Medium (5-7)**: Related to AI/tech but not core to StillMe's mission
- **Low (0-4)**: Unrelated to AI, technology, or StillMe's domain

**Questions to consider:**
- Does this relate to AI, machine learning, or StillMe's core mission?
- Will this knowledge help StillMe serve its users better?
- Is this relevant to transparency, ethics, or learning systems?

### 4. **Clarity (Độ Rõ Ràng)**
- **High (8-10)**: Well-structured, clear, unambiguous
- **Medium (5-7)**: Generally clear but may need minor clarification
- **Low (0-4)**: Confusing, ambiguous, or poorly structured

**Questions to consider:**
- Is the proposal clearly stated?
- Are the concepts well-defined?
- Can StillMe understand what to learn from this?

### 5. **Evidence Base (Cơ Sở Bằng Chứng)**
- **High (8-10)**: Well-supported by credible sources, verifiable claims
- **Medium (5-7)**: Some evidence but may need more support
- **Low (0-4)**: Lacks evidence, unverifiable, or from unreliable sources

**Questions to consider:**
- Are claims supported by evidence?
- Can StillMe verify this from trusted sources (arXiv, Wikipedia, etc.)?
- Is this from a credible source?

---

## Scoring Guidelines

### Overall Score Calculation
- **Score Range**: 0.0 to 10.0
- **Threshold for Acceptance**: >= 5.0
- **Threshold for High Quality**: >= 7.0

### Weighted Criteria (for detailed evaluation):
- Novelty: 25%
- Feasibility: 30%
- Relevance: 25%
- Clarity: 10%
- Evidence Base: 10%

### Quick Evaluation (for pre-filtering):
Use a simplified scoring based on:
1. **Relevance check**: Is this related to AI/tech/StillMe's mission? (Yes/No)
2. **Feasibility check**: Can StillMe learn this? (Yes/No)
3. **Quality check**: Is this well-structured and clear? (Yes/No)

If all three are "Yes" → Score >= 5.0 (pass)
If any are "No" → Score < 5.0 (reject)

---

## Examples

### High Quality Proposal (Score: 8.5)
**Proposal**: "StillMe should learn about recent advances in RAG evaluation metrics, specifically focusing on citation accuracy and evidence grounding techniques from recent arXiv papers."

**Evaluation**:
- Novelty: 8 (recent advances, specific focus)
- Feasibility: 9 (can learn from arXiv)
- Relevance: 9 (directly related to RAG)
- Clarity: 8 (clear and specific)
- Evidence Base: 8 (arXiv is credible)
- **Overall: 8.5** ✅ **ACCEPT**

### Medium Quality Proposal (Score: 6.0)
**Proposal**: "StillMe should learn about machine learning in general."

**Evaluation**:
- Novelty: 4 (too broad, likely already known)
- Feasibility: 7 (feasible but vague)
- Relevance: 8 (relevant to AI)
- Clarity: 5 (too vague)
- Evidence Base: 6 (general topic)
- **Overall: 6.0** ✅ **ACCEPT** (but low priority)

### Low Quality Proposal (Score: 2.5)
**Proposal**: "StillMe should learn about cooking recipes."

**Evaluation**:
- Novelty: 3 (not new, but irrelevant)
- Feasibility: 7 (feasible technically)
- Relevance: 1 (not related to AI/tech)
- Clarity: 3 (unclear why StillMe needs this)
- Evidence Base: 4 (recipes exist but not relevant)
- **Overall: 2.5** ❌ **REJECT**

---

## Special Considerations

### StillMe's Mission Alignment
Proposals should align with StillMe's core values:
- **Transparency**: Does this promote transparency in AI?
- **Ethics**: Does this relate to ethical AI development?
- **Open Source**: Does this support open source AI?
- **Community Governance**: Does this enable community control?

### Learning Source Quality
Consider the source of the proposal:
- **High Quality Sources**: arXiv, peer-reviewed papers, Wikipedia, established tech blogs
- **Medium Quality**: General tech news, blog posts
- **Low Quality**: Unverified claims, spam, irrelevant content

### Cost-Benefit Analysis
Even if a proposal passes (score >= 5.0), consider:
- **Learning Cost**: How expensive is it to learn this? (embedding costs, API costs)
- **Value**: How valuable is this knowledge to StillMe's users?
- **Priority**: Should this be learned now or later?

---

## Review Process

1. **Initial Screening**: Quick relevance and feasibility check
2. **Detailed Evaluation**: Full scoring if passes initial screening
3. **Decision**: Accept (>= 5.0) or Reject (< 5.0)
4. **Logging**: Record score, reasons, and decision for transparency

---

## Transparency Commitment

All review decisions are:
- **Logged**: Every evaluation is recorded
- **Explainable**: Reasons for acceptance/rejection are provided
- **Auditable**: Review criteria and process are public
- **Revisable**: Community can suggest improvements to criteria

---

**Last Updated**: 2025-01-27
**Version**: 1.0
**Status**: Active

