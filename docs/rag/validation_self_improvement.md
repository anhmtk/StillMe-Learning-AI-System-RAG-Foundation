---
content_type: technical
domain: stillme_validation_self_improvement
source: StillMe Internal Documentation
---

# StillMe Validation & Self-Improvement Mechanism

## Overview

StillMe implements a **dual-layer improvement system** that combines:
1. **Manual test-fix cycles**: Developers analyze test results and fix issues at the system level
2. **Automated self-improvement**: StillMe learns from validation results and improves itself

This dual-layer approach accelerates improvement by providing both external guidance and internal learning.

## Validation Metrics Tracking

StillMe tracks validation metrics with persistent storage (`data/validation_metrics.jsonl`):

### Metrics Tracked

- **Validation Results**: Pass/fail status for each question-answer pair
- **Confidence Scores**: AI confidence scores (0.0-1.0) for each response
- **Validation Reasons**: Specific reasons for pass/fail (e.g., "missing_citation", "low_overlap", "missing_uncertainty")
- **Context Quality**: Number of context documents retrieved, overlap scores
- **Citation Status**: Whether answers have citations
- **Question Categories**: Philosophical, factual, technical, religion/roleplay

### Persistent Storage

All validation records are persisted to `data/validation_metrics.jsonl` in JSONL format:
- Each line is a JSON object with timestamp, question, answer, validation results
- Records are never deleted (for historical analysis)
- Enables pattern analysis over time

## Self-Improvement Mechanism

### Pattern Analysis

StillMe analyzes validation patterns to identify:
- **Common failure reasons**: e.g., "missing_citation" appears 10 times in 7 days
- **Category-specific issues**: e.g., "factual" questions have 40% failure rate
- **Knowledge gaps**: Questions with no RAG context indicate missing knowledge

### Learning Suggestions

Based on validation patterns, StillMe automatically suggests:
- **Topics to learn**: e.g., "Citation and source attribution best practices"
- **Sources to prioritize**: e.g., "Wikipedia: Citation, Academic writing"
- **Priority levels**: High/medium based on failure frequency

### Improvement Recommendations

StillMe generates recommendations for:
- **Validator improvements**: e.g., "Strengthen citation detection logic"
- **RAG retrieval optimization**: e.g., "Review overlap threshold"
- **Prompt engineering**: e.g., "Improve citation instruction in prompts"

## Feedback Loop: Validation → Learning

### How It Works

1. **Validation**: Every response is validated and recorded
2. **Pattern Detection**: StillMe analyzes patterns in validation failures
3. **Gap Identification**: Identifies knowledge gaps from failed validations
4. **Learning Suggestions**: Suggests topics and sources to learn
5. **Continuous Improvement**: As StillMe learns, validation pass rate improves

### Example Flow

```
Question: "Hiệp ước Geneva 1954 đã quyết định những gì?"
→ Validation fails: missing_citation, no_context
→ Pattern detected: "missing_citation" appears 5 times for historical questions
→ Learning suggestion: "Learn about Geneva Conference 1954 from Wikipedia"
→ StillMe learns → Next time: Passes validation with citations
```

## API Endpoints

### Validation Metrics

- `GET /api/validators/metrics` - Get validation metrics (pass_rate, confidence_scores)
- `GET /api/validators/metrics/patterns?days=7` - Get validation patterns and suggestions
- `GET /api/validators/metrics/knowledge-gaps?days=7` - Get knowledge gaps from failures

### Self-Improvement

- `GET /api/validators/self-improvement/analyze?days=7` - Get self-improvement analysis
- `GET /api/validators/self-improvement/suggestions` - Get learning suggestions

## Benefits of Dual-Layer Improvement

### Manual Test-Fix Cycle (Layer 1)

- **System-level fixes**: Developers fix root causes, not just symptoms
- **Comprehensive analysis**: Deep investigation of issues
- **Architectural improvements**: Can change system design

### Automated Self-Improvement (Layer 2)

- **Continuous learning**: StillMe learns from every validation
- **Pattern recognition**: Identifies trends across many validations
- **Knowledge gap detection**: Automatically finds missing knowledge
- **Accelerated improvement**: Works 24/7 without human intervention

### Synergy

The two layers work together:
- **Layer 1** fixes systemic issues (e.g., validator logic, prompts)
- **Layer 2** fills knowledge gaps (e.g., learns missing facts)
- **Result**: Faster improvement than either layer alone

## Technical Implementation

### ValidationMetricsTracker

- **Location**: `backend/validators/validation_metrics_tracker.py`
- **Storage**: `data/validation_metrics.jsonl`
- **Features**: Pattern analysis, failure rate by category, knowledge gap extraction

### SelfImprovementAnalyzer

- **Location**: `backend/validators/self_improvement.py`
- **Features**: Pattern analysis, learning suggestions, improvement recommendations

### Integration

- Validation results are automatically recorded via `ValidationMetrics.record_validation()`
- Patterns are analyzed on-demand via API endpoints
- Learning suggestions are generated automatically

## RAG Knowledge Base

This document is stored in StillMe's RAG knowledge base (`stillme_knowledge` collection) so that StillMe can:
- Answer questions about its validation and self-improvement mechanisms
- Explain how it learns from mistakes
- Describe the dual-layer improvement system
- Cite this document when discussing validation metrics

## Citation

When StillMe discusses validation or self-improvement, it should cite this document:
- "According to StillMe's validation and self-improvement documentation [1]..."
- "StillMe's self-improvement mechanism [1] analyzes validation patterns..."

