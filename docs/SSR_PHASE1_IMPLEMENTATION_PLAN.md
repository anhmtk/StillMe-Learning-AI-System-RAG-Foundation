# SSR Phase 1 Implementation Plan: Step-Level Validation & Self-Consistency Checks

## 📋 Overview

**Goal:** Implement low-cost SSR features (step-level validation + self-consistency checks) with minimal latency increase (8-15%) and zero cost increase.

**Features:**
1. **Step-Level Validation**: Parse multi-step responses and validate each step individually
2. **Self-Consistency Checks**: Detect contradictions within responses and against knowledge base

**Expected Impact:**
- **Latency**: +8-15% (0.15-0.5s)
- **Cost**: 0% (CPU-only, no LLM calls)
- **Accuracy**: Improved error detection for multi-step reasoning

---

## 🏗️ Architecture Design

### Component Structure

```
backend/validators/
├── step_detector.py          # NEW: Detects and parses steps from response
├── step_validator.py         # NEW: Validates individual steps
├── consistency_checker.py    # NEW: Checks consistency between claims
└── ... (existing validators)
```

### Data Flow

```
User Query
    ↓
LLM Response (raw)
    ↓
StepDetector → [Step 1, Step 2, ..., Step N]
    ↓
StepValidator → [Step 1: confidence=0.9, Step 2: confidence=0.2, ...]
    ↓
ConsistencyChecker → [Contradictions detected: Step 2 vs Step 4]
    ↓
Enhanced ValidationResult (with step-level info)
    ↓
Chat Router (decide: use response, flag issues, or suggest refinement)
```

---

## 📁 File Structure

### 1. `backend/validators/step_detector.py`

**Purpose:** Detect and parse multi-step reasoning from responses

**Key Functions:**
- `detect_steps(response: str) -> List[Step]`: Parse response into steps
- `is_multi_step(response: str) -> bool`: Quick check if response has steps

**Step Patterns:**
- Vietnamese: "Bước 1:", "Bước 2:", "1.", "2."
- English: "Step 1:", "Step 2:", "1.", "2."
- Numbered lists: "1.", "2.", "3."

**Step Model:**
```python
@dataclass
class Step:
    step_number: int
    content: str
    original_text: str  # Full text including "Bước 1:" prefix
    start_pos: int      # Position in original response
    end_pos: int
```

---

### 2. `backend/validators/step_validator.py`

**Purpose:** Validate individual steps using existing ValidatorChain

**Key Functions:**
- `validate_step(step: Step, ctx_docs: List[str], chain: ValidatorChain) -> StepValidationResult`
- `validate_all_steps(steps: List[Step], ctx_docs: List[str], chain: ValidatorChain) -> List[StepValidationResult]`

**StepValidationResult Model:**
```python
class StepValidationResult(BaseModel):
    step: Step
    validation_result: ValidationResult
    confidence: float  # 0.0-1.0
    passed: bool
    issues: List[str]  # Specific issues found
```

**Confidence Calculation:**
- Base: 0.5
- Has citation: +0.2
- Evidence overlap > 0.1: +0.2
- Validation passed: +0.1
- Missing citation: -0.3
- Low overlap: -0.2

---

### 3. `backend/validators/consistency_checker.py`

**Purpose:** Check consistency between claims and with knowledge base

**Key Functions:**
- `extract_claims(response: str) -> List[Claim]`: Extract factual claims
- `check_pairwise_consistency(claims: List[Claim]) -> Dict[str, str]`: Check contradictions
- `check_kb_consistency(claim: Claim, ctx_docs: List[str]) -> str`: Check against KB

**Claim Model:**
```python
@dataclass
class Claim:
    text: str
    citation: Optional[str]  # "[1]", "[2]", etc.
    entities: List[str]      # Extracted entities (StillMe, ChromaDB, etc.)
    values: Dict[str, str]   # Extracted values (time: "4 giờ", db: "ChromaDB")
```

**Contradiction Detection:**
- Time contradictions: "4 giờ" vs "6 giờ"
- Database contradictions: "ChromaDB" vs "PostgreSQL"
- Model contradictions: "DeepSeek" vs "GPT-5"
- Frequency contradictions: "mỗi 4 giờ" vs "mỗi ngày"

---

## 🔧 Implementation Details

### Step Detection Algorithm

```python
def detect_steps(response: str) -> List[Step]:
    """
    Detect steps using multiple patterns
    """
    patterns = [
        # Vietnamese: "Bước 1:", "Bước 2:"
        (r"Bước\s+(\d+)[:\.]\s*(.+?)(?=Bước\s+\d+|$)", "vi"),
        # English: "Step 1:", "Step 2:"
        (r"Step\s+(\d+)[:\.]\s*(.+?)(?=Step\s+\d+|$)", "en"),
        # Numbered: "1.", "2."
        (r"^(\d+)\.\s*(.+?)(?=^\d+\.|$)", "numbered"),
    ]
    
    steps = []
    for pattern, lang in patterns:
        matches = re.finditer(pattern, response, re.MULTILINE | re.DOTALL)
        for match in matches:
            step_num = int(match.group(1))
            content = match.group(2).strip()
            steps.append(Step(
                step_number=step_num,
                content=content,
                original_text=match.group(0),
                start_pos=match.start(),
                end_pos=match.end()
            ))
    
    # Sort by step number
    steps.sort(key=lambda x: x.step_number)
    return steps
```

---

### Step Validation Algorithm

```python
def validate_all_steps(
    steps: List[Step],
    ctx_docs: List[str],
    chain: ValidatorChain
) -> List[StepValidationResult]:
    """
    Validate all steps in parallel (CPU-only, fast)
    """
    results = []
    
    # Run validations in parallel for speed
    with ThreadPoolExecutor(max_workers=len(steps)) as executor:
        futures = {
            executor.submit(validate_step, step, ctx_docs, chain): step
            for step in steps
        }
        
        for future in as_completed(futures):
            step = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"Error validating step {step.step_number}: {e}")
                # Fallback: mark as failed
                results.append(StepValidationResult(
                    step=step,
                    validation_result=ValidationResult(
                        passed=False,
                        reasons=[f"validation_error: {str(e)}"]
                    ),
                    confidence=0.1,
                    passed=False,
                    issues=[f"Validation error: {str(e)}"]
                ))
    
    # Sort by step number
    results.sort(key=lambda x: x.step.step_number)
    return results
```

---

### Consistency Check Algorithm

```python
def check_pairwise_consistency(claims: List[Claim]) -> Dict[str, str]:
    """
    Check consistency between all pairs of claims
    """
    consistency_results = {}
    
    for i, claim1 in enumerate(claims):
        for j, claim2 in enumerate(claims[i+1:], start=i+1):
            # Check for contradictions
            if are_contradictory(claim1, claim2):
                consistency_results[f"claim_{i}_vs_claim_{j}"] = "CONTRADICTION"
            elif are_redundant(claim1, claim2):
                consistency_results[f"claim_{i}_vs_claim_{j}"] = "REDUNDANT"
            else:
                consistency_results[f"claim_{i}_vs_claim_{j}"] = "CONSISTENT"
    
    return consistency_results

def are_contradictory(claim1: Claim, claim2: Claim) -> bool:
    """
    Check if two claims contradict each other
    """
    # Time contradictions
    time_patterns = [
        (r"(\d+)\s*giờ", r"(\d+)\s*giờ"),  # "4 giờ" vs "6 giờ"
        (r"mỗi\s+(\w+)", r"mỗi\s+(\w+)"),  # "mỗi 4 giờ" vs "mỗi ngày"
    ]
    
    # Database contradictions
    db_contradictions = [
        ("ChromaDB", "PostgreSQL"),
        ("ChromaDB", "MySQL"),
        ("vector database", "SQL database"),
    ]
    
    # Model contradictions
    model_contradictions = [
        ("DeepSeek", "GPT-5"),
        ("OpenAI", "GPT-5"),
    ]
    
    # Check time contradictions
    for pattern1, pattern2 in time_patterns:
        match1 = re.search(pattern1, claim1.text, re.IGNORECASE)
        match2 = re.search(pattern2, claim2.text, re.IGNORECASE)
        if match1 and match2:
            val1 = match1.group(1) if match1.lastindex else None
            val2 = match2.group(1) if match2.lastindex else None
            if val1 and val2 and val1 != val2:
                return True
    
    # Check database contradictions
    for db1, db2 in db_contradictions:
        if (db1 in claim1.text and db2 in claim2.text) or \
           (db2 in claim1.text and db1 in claim2.text):
            return True
    
    # Check model contradictions
    for model1, model2 in model_contradictions:
        if (model1 in claim1.text and model2 in claim2.text) or \
           (model2 in claim1.text and model1 in claim2.text):
            return True
    
    return False
```

---

## 🔌 Integration Points

### 1. Update `chat_router.py`

**Location:** `backend/api/routers/chat_router.py`

**Changes:**
- Add step-level validation after regular validation
- Add consistency checks after step validation
- Include step-level info in response metadata

**Code Snippet:**
```python
# After regular validation
if enable_validators:
    validation_result = chain.run(raw_response, ctx_docs)
    
    # NEW: Step-level validation (if enabled)
    step_validation_info = None
    if os.getenv("ENABLE_STEP_LEVEL_VALIDATION", "true").lower() == "true":
        from backend.validators.step_detector import StepDetector
        from backend.validators.step_validator import StepValidator
        
        step_detector = StepDetector()
        steps = step_detector.detect_steps(raw_response)
        
        if len(steps) > 1:  # Multi-step detected
            step_validator = StepValidator()
            step_results = step_validator.validate_all_steps(steps, ctx_docs, chain)
            
            step_validation_info = {
                "is_multi_step": True,
                "total_steps": len(steps),
                "steps": [
                    {
                        "step_number": r.step.step_number,
                        "confidence": r.confidence,
                        "passed": r.passed,
                        "issues": r.issues
                    }
                    for r in step_results
                ],
                "low_confidence_steps": [
                    r.step.step_number
                    for r in step_results
                    if r.confidence < 0.5
                ]
            }
    
    # NEW: Consistency checks (if enabled)
    consistency_info = None
    if os.getenv("ENABLE_CONSISTENCY_CHECKS", "true").lower() == "true":
        from backend.validators.consistency_checker import ConsistencyChecker
        
        checker = ConsistencyChecker()
        claims = checker.extract_claims(raw_response)
        
        if len(claims) > 1:
            consistency_results = checker.check_pairwise_consistency(claims)
            kb_results = checker.check_kb_consistency(claims, ctx_docs)
            
            contradictions = [
                key for key, value in consistency_results.items()
                if value == "CONTRADICTION"
            ]
            
            consistency_info = {
                "total_claims": len(claims),
                "contradictions": contradictions,
                "kb_inconsistencies": [
                    key for key, value in kb_results.items()
                    if "INCONSISTENT" in value
                ]
            }
    
    # Add to validation_info
    validation_info = {
        "passed": validation_result.passed,
        "reasons": validation_result.reasons,
        "step_validation": step_validation_info,  # NEW
        "consistency": consistency_info,  # NEW
        "confidence_score": confidence_score
    }
```

---

### 2. Update `validators/__init__.py`

**Add exports:**
```python
from .step_detector import StepDetector, Step
from .step_validator import StepValidator, StepValidationResult
from .consistency_checker import ConsistencyChecker, Claim

__all__ = [
    # ... existing exports ...
    "StepDetector",
    "Step",
    "StepValidator",
    "StepValidationResult",
    "ConsistencyChecker",
    "Claim",
]
```

---

### 3. Update `env.example`

**Add configuration:**
```bash
# =============================================================================
# Step-Level Validation & Consistency Checks (Phase 1 - SSR)
# =============================================================================
# Enable step-level validation for multi-step reasoning
# Default: true (enabled)
ENABLE_STEP_LEVEL_VALIDATION=true

# Enable self-consistency checks
# Default: true (enabled)
ENABLE_CONSISTENCY_CHECKS=true

# Minimum number of steps to trigger step-level validation
# Default: 2 (only validate if 2+ steps detected)
STEP_VALIDATION_MIN_STEPS=2

# Confidence threshold for flagging unreliable steps
# Steps with confidence below this will be flagged
# Default: 0.5
STEP_CONFIDENCE_THRESHOLD=0.5
```

---

## 📊 Metrics & Monitoring

### Update `validators/metrics.py`

**Add step-level metrics:**
```python
class ValidationMetrics:
    # ... existing fields ...
    
    # NEW: Step-level metrics
    step_validations_total: int = 0
    step_validations_passed: int = 0
    step_validations_failed: int = 0
    average_steps_per_response: float = 0.0
    low_confidence_steps_count: int = 0
    
    # NEW: Consistency metrics
    consistency_checks_total: int = 0
    contradictions_detected: int = 0
    kb_inconsistencies_detected: int = 0
```

---

## 🧪 Testing Strategy

### Unit Tests

**File:** `tests/test_step_detector.py`
```python
def test_detect_vietnamese_steps():
    response = """
    Bước 1: StillMe học từ RSS [1]
    Bước 2: StillMe embed content [2]
    Bước 3: StillMe lưu vào ChromaDB [3]
    """
    detector = StepDetector()
    steps = detector.detect_steps(response)
    assert len(steps) == 3
    assert steps[0].step_number == 1
    assert "RSS" in steps[0].content

def test_detect_english_steps():
    response = """
    Step 1: StillMe learns from RSS [1]
    Step 2: StillMe embeds content [2]
    """
    detector = StepDetector()
    steps = detector.detect_steps(response)
    assert len(steps) == 2

def test_detect_numbered_list():
    response = """
    1. StillMe learns from RSS [1]
    2. StillMe embeds content [2]
    3. StillMe stores in ChromaDB [3]
    """
    detector = StepDetector()
    steps = detector.detect_steps(response)
    assert len(steps) == 3
```

**File:** `tests/test_consistency_checker.py`
```python
def test_detect_time_contradiction():
    response = """
    StillMe học từ RSS mỗi 4 giờ [1].
    StillMe học từ arXiv mỗi 6 giờ [2].
    """
    checker = ConsistencyChecker()
    claims = checker.extract_claims(response)
    consistency = checker.check_pairwise_consistency(claims)
    assert "CONTRADICTION" in consistency.values()

def test_detect_database_contradiction():
    response = """
    StillMe lưu vào ChromaDB [1].
    StillMe lưu vào PostgreSQL [2].
    """
    checker = ConsistencyChecker()
    claims = checker.extract_claims(response)
    consistency = checker.check_pairwise_consistency(claims)
    assert "CONTRADICTION" in consistency.values()
```

### Integration Tests

**File:** `tests/test_step_validation_integration.py`
```python
async def test_step_validation_in_chat_flow():
    """Test step validation in actual chat flow"""
    # Send multi-step question
    response = await chat_with_rag(
        ChatRequest(message="Giải thích cách StillMe hoạt động từ đầu đến cuối")
    )
    
    # Check if step validation info is present
    assert "step_validation" in response.validation_info
    assert response.validation_info["step_validation"]["is_multi_step"] == True
    assert response.validation_info["step_validation"]["total_steps"] > 1
```

---

## 🚀 Deployment Plan

### Phase 1.1: Step Detection (Week 1)
- ✅ Implement `StepDetector`
- ✅ Unit tests
- ✅ Integration with chat_router (detection only, no validation yet)

### Phase 1.2: Step Validation (Week 1-2)
- ✅ Implement `StepValidator`
- ✅ Unit tests
- ✅ Integration with chat_router (full step validation)

### Phase 1.3: Consistency Checks (Week 2)
- ✅ Implement `ConsistencyChecker`
- ✅ Unit tests
- ✅ Integration with chat_router (full consistency checking)

### Phase 1.4: Metrics & Monitoring (Week 2-3)
- ✅ Update metrics collection
- ✅ Dashboard integration (optional)
- ✅ Logging and monitoring

### Phase 1.5: Testing & Optimization (Week 3)
- ✅ End-to-end testing
- ✅ Performance optimization
- ✅ Documentation

---

## ⚙️ Configuration Options

### Environment Variables

```bash
# Enable/disable features
ENABLE_STEP_LEVEL_VALIDATION=true
ENABLE_CONSISTENCY_CHECKS=true

# Thresholds
STEP_VALIDATION_MIN_STEPS=2
STEP_CONFIDENCE_THRESHOLD=0.5

# Performance tuning
STEP_VALIDATION_PARALLEL=true  # Run step validations in parallel
CONSISTENCY_CHECK_PARALLEL=true  # Run consistency checks in parallel
```

---

## 📈 Expected Results

### Before (Baseline)
- Response-level validation only
- No step-level error detection
- No consistency checking
- Latency: 1.7-3.6s
- Cost: $0.0004-0.0006 per request

### After (Phase 1)
- Step-level validation for multi-step responses
- Consistency checking for contradictions
- Enhanced error detection
- Latency: 1.85-3.75s (+8-15%)
- Cost: $0.0004-0.0006 per request (0% increase)

### Metrics to Track
- Step detection rate: % of responses with detected steps
- Step validation pass rate: % of steps that pass validation
- Contradiction detection rate: % of responses with contradictions
- Average steps per multi-step response
- Low confidence steps rate: % of steps with confidence < 0.5

---

## 🔄 Backward Compatibility

**Critical:** All features are **opt-in** via environment variables:
- Default: `ENABLE_STEP_LEVEL_VALIDATION=true` (enabled by default)
- Default: `ENABLE_CONSISTENCY_CHECKS=true` (enabled by default)
- Can be disabled: Set to `false` to revert to current behavior

**No breaking changes:**
- Existing validation flow unchanged
- Step-level validation is **additive** (runs after regular validation)
- Consistency checks are **additive** (runs after step validation)
- Response format unchanged (just more metadata)

---

## 📝 Next Steps

1. **Review this plan** - Get approval before implementation
2. **Create feature branch** - `feature/ssr-phase1-step-validation`
3. **Implement StepDetector** - Start with detection only
4. **Implement StepValidator** - Add validation logic
5. **Implement ConsistencyChecker** - Add consistency logic
6. **Integration** - Wire into chat_router
7. **Testing** - Unit + integration tests
8. **Documentation** - Update docs with new features
9. **Deploy** - Gradual rollout with monitoring

---

## 🎯 Success Criteria

- ✅ Step detection works for Vietnamese, English, numbered lists
- ✅ Step validation identifies low-confidence steps
- ✅ Consistency checks detect contradictions
- ✅ Latency increase < 15%
- ✅ Cost increase = 0%
- ✅ No breaking changes
- ✅ All tests pass
- ✅ Backward compatible

---

**Ready to implement?** Let's start with StepDetector! 🚀

