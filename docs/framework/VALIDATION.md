# StillMe Core Validation System Guide

## Overview

The StillMe Core validation system ensures response quality, reduces hallucinations, and enforces transparency. It consists of a `ValidationEngine` that orchestrates 27+ specialized validators.

## Philosophy

- **Transparency First**: All validation decisions are logged and explainable
- **Mandatory Validation**: Every response must pass validation
- **Intellectual Humility**: Honest about limitations and uncertainties
- **Modular Design**: Each validator is independent and can be enabled/disabled

## Architecture

### ValidationEngine

The `ValidationEngine` orchestrates multiple validators:

```python
from stillme_core.validation import ValidationEngine, CitationRequired, EvidenceOverlap

# Create engine with validators
engine = ValidationEngine([
    CitationRequired(),
    EvidenceOverlap(),
    # ... more validators
])

# Validate a response
result = engine.validate(
    question="What is AI?",
    answer="AI is artificial intelligence...",
    context_docs=["doc1", "doc2"],
    # ... other parameters
)
```

### Validator Base Class

All validators implement the `Validator` protocol:

```python
from stillme_core.validation import Validator, ValidationResult

class MyValidator(Validator):
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        # Validation logic
        if self._check_passes(answer):
            return ValidationResult(
                passed=True,
                reasons=[]
            )
        else:
            return ValidationResult(
                passed=False,
                reasons=["Validation failed: reason"]
            )
```

## Available Validators

### Core Validators

#### `CitationRequired`
Ensures citations are present when required.

**When to use**: Always (critical validator)

**What it checks**:
- Presence of citations in answer
- Citation format correctness

#### `CitationRelevance`
Validates that citations are relevant to the answer.

**When to use**: When citations are present

**What it checks**:
- Citation relevance to answer content
- Citation context matching

#### `EvidenceOverlap`
Checks evidence overlap between answer and context documents.

**When to use**: Always (critical validator)

**What it checks**:
- Overlap score between answer and context
- Evidence coverage

#### `ConfidenceValidator`
Validates confidence scores.

**When to use**: Always (critical validator)

**What it checks**:
- Confidence score appropriateness
- Confidence calibration

### Language Validators

#### `LanguageValidator`
Validates language consistency.

**When to use**: Always (must run first)

**What it checks**:
- Language consistency throughout answer
- Language matching with question

### Identity Validators

#### `IdentityCheckValidator`
Checks StillMe identity consistency.

**When to use**: Always

**What it checks**:
- Identity markers presence
- Identity consistency

#### `EgoNeutralityValidator`
Ensures ego-neutral responses.

**When to use**: Always

**What it checks**:
- Absence of ego markers
- Neutral tone

### Quality Validators

#### `SourceConsensusValidator`
Validates source consensus.

**When to use**: When multiple sources are available

**What it checks**:
- Source agreement
- Consensus strength

#### `ConsistencyChecker`
Checks internal consistency.

**When to use**: Always

**What it checks**:
- Claim consistency
- Logical coherence

#### `PhilosophicalDepthValidator`
Validates philosophical depth.

**When to use**: For philosophical questions

**What it checks**:
- Depth of analysis
- Philosophical rigor

### Specialized Validators

#### `NumericUnitsBasic`
Validates numeric units.

**When to use**: When answer contains numbers

**What it checks**:
- Unit correctness
- Number formatting

#### `SchemaFormat`
Validates schema format.

**When to use**: When structured output is required

**What it checks**:
- Schema compliance
- Format correctness

#### `StepDetector` & `StepValidator`
Detects and validates step-by-step reasoning.

**When to use**: For multi-step questions

**What it checks**:
- Step detection
- Step validation

#### `SelfCriticExperience`
Self-corrects experience claims.

**When to use**: When answer contains experience claims

**What it checks**:
- Experience claim validity
- Auto-correction

#### `EthicsAdapter`
Validates ethical considerations.

**When to use**: Always

**What it checks**:
- Ethical compliance
- Ethical reasoning

#### `ReviewAdapter`
Simulated peer review evaluation.

**When to use**: Optional (can be enabled)

**What it checks**:
- Peer review criteria
- Quality assessment

#### `FallbackHandler`
Handles validation failures gracefully.

**When to use**: Always (last validator)

**What it checks**:
- Fallback generation
- Error handling

## Execution Model

### Sequential vs Parallel

Validators can run in two modes:

1. **Sequential**: Validators that must run in order (dependencies)
2. **Parallel**: Validators that can run concurrently (independent)

**Sequential Validators**:
- `LanguageValidator` (must run first)
- `CitationRequired` (must run before `CitationRelevance`)
- `ConfidenceValidator` (may depend on other results)

**Parallel Validators**:
- `CitationRelevance`
- `EvidenceOverlap`
- `NumericUnitsBasic`
- `EthicsAdapter`
- `EgoNeutralityValidator`
- `SourceConsensusValidator`

### Early Exit

The engine supports early exit for critical failures:

```python
# If a critical validator fails, stop immediately
if result.passed == False and validator.is_critical:
    return result  # Early exit
```

## Validation Result

```python
class ValidationResult:
    passed: bool  # Whether validation passed
    reasons: List[str]  # Failure reasons or warnings
    patched_answer: Optional[str]  # Auto-patched answer
```

## Creating Custom Validators

### Step 1: Implement Validator Protocol

```python
from stillme_core.validation import Validator, ValidationResult

class MyValidator(Validator):
    def run(self, answer: str, ctx_docs: List[str]) -> ValidationResult:
        # Your validation logic
        if self._check(answer):
            return ValidationResult(
                passed=True,
                reasons=[]
            )
        else:
            return ValidationResult(
                passed=False,
                reasons=["My validation failed"]
            )
```

### Step 2: Register Validator

```python
from stillme_core.validation import ValidationEngine

engine = ValidationEngine([...])
engine.add_validator(MyValidator())
```

### Step 3: Configure Execution Order

If your validator has dependencies, ensure it runs after them:

```python
# Validators run in registration order
engine = ValidationEngine([
    LanguageValidator(),  # Runs first
    MyValidator(),  # Runs after LanguageValidator
])
```

## Best Practices

### 1. Keep Validators Focused
Each validator should check one specific aspect.

### 2. Provide Clear Reasons
Always provide clear, actionable failure reasons.

### 3. Support Auto-Patching
If possible, provide `patched_answer` to auto-fix issues.

### 4. Log Validation Decisions
All validation decisions should be logged for transparency.

### 5. Handle Edge Cases
Validators should handle edge cases gracefully (empty answers, no context, etc.).

## Metrics

Validation metrics are automatically recorded to `UnifiedMetricsCollector`:

- Total validations
- Pass/fail counts
- Failure reasons
- Confidence scores
- Overlap scores
- Fallback usage

## Integration

### With RAG System

```python
# Retrieve context
context = rag.retrieve_context(query)

# Validate with context
result = engine.validate(
    question=query,
    answer=response,
    context_docs=context["knowledge_docs"]
)
```

### With Post-Processing

```python
# Validate first
validation_result = engine.validate(...)

# Post-process if validation passed
if validation_result.passed:
    processed = post_processor.process(response)
```

## Related Documentation

- [API Reference](API.md)
- [Architecture Guide](ARCHITECTURE.md)

