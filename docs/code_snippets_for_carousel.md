# Code Snippets for LinkedIn Carousel

This file contains code snippets ready to screenshot for Slides 3-6.

---

## SLIDE 3: SourceConsensusValidator

**File**: `stillme_core/validation/source_consensus.py`
**Lines**: 24-66

```python
class SourceConsensusValidator:
    """
    Validator that detects contradictions between RAG context documents
    
    MVP Features:
    - Compares top-2 documents only
    - Detects contradictions in: dates, numbers, names, key facts
    - Forces uncertainty expression when contradictions found
    """
    
    def __init__(self, enabled: bool = True, timeout: float = 3.0):
        """
        Initialize source consensus validator
        
        Args:
            enabled: Whether validator is enabled (default: True)
            timeout: Timeout per comparison in seconds (default: 3.0)
        """
        self.enabled = enabled
        self.timeout = timeout
        logger.info(f"SourceConsensusValidator initialized (enabled={enabled}, timeout={timeout}s)")
    
    def _compare_documents(self, doc1: str, doc2: str, question: Optional[str] = None) -> Dict[str, Any]:
        """
        Compare two documents to detect contradictions
        
        Uses LLM to detect contradictions in:
        - Dates (e.g., "1954" vs "1955")
        - Numbers (e.g., "17th parallel" vs "16th parallel")
        - Names (e.g., "Keynes" vs "White")
        - Key facts (e.g., "Geneva Conference" vs "Paris Conference")
        
        Args:
            doc1: First document
            doc2: Second document
            question: Optional user question for context
            
        Returns:
            Dictionary with:
            - has_contradiction: bool
            - contradiction_type: str (e.g., "date", "number", "name", "fact")
            - details: str (description of contradiction)
            - confidence: float (0.0-1.0)
        """
        if not self.enabled:
            return {"has_contradiction": False, "confidence": 0.0}
        
        try:
            # Use LLM to detect contradictions
            # Try DeepSeek first, fallback to OpenAI
            api_key = os.getenv("DEEPSEEK_API_KEY")
            api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com")
            model = "deepseek-chat"
            
            if not api_key:
                api_key = os.getenv("OPENAI_API_KEY")
                api_base = "https://api.openai.com/v1"
                model = "gpt-3.5-turbo"
            
            if not api_key:
                logger.warning("No API key available for source consensus check, skipping")
                return {"has_contradiction": False, "confidence": 0.0}
            
            # Build comparison prompt
            comparison_prompt = f"""You are analyzing two documents to detect contradictions in key facts.

**User Question (for context):**
{question or "N/A"}

**Document 1:**
{doc1[:1000]}  # Truncate to save tokens

**Document 2:**
{doc2[:1000]}  # Truncate to save tokens

**Task:**
Compare these two documents and detect if they contradict each other on:
- Dates
- Numbers
- Names
- Key facts
"""
```

---

## SLIDE 4: Parallel Execution

**File**: `stillme_core/validation/chain.py`
**Lines**: 282-330

```python
# OPTIMIZATION: Run parallel validators concurrently (if any)
if parallel_validators:
    logger.debug(f"Running {len(parallel_validators)} validators in parallel...")
    parallel_results: Dict[int, ValidationResult] = {}
    
    def _run_parallel_validator(validator, validator_name, patched_answer, ctx_docs_list, user_q=None):
        """Helper function to run validator with correct parameters"""
        try:
            # Pass user_question to validators that need it
            if validator_name == "FactualHallucinationValidator":
                return validator.run(patched_answer, ctx_docs_list, user_question=user_q)
            elif validator_name == "SourceConsensusValidator":
                return validator.run(patched_answer, ctx_docs_list, user_question=user_q)
            else:
                return validator.run(patched_answer, ctx_docs_list)
        except Exception as e:
            logger.error(f"Parallel validator {validator_name} error: {e}")
            return ValidationResult(
                passed=False,
                reasons=[f"validator_error:{validator_name}:{str(e)}"]
            )
    
    try:
        with ThreadPoolExecutor(max_workers=min(len(parallel_validators), 5)) as executor:
            # Submit all parallel validators with correct parameters
            future_to_validator = {
                executor.submit(
                    _run_parallel_validator,
                    validator,
                    validator_name,
                    patched,
                    ctx_docs,
                    user_question
                ): (i, validator_name)
                for i, validator, validator_name in parallel_validators
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_validator):
                i, validator_name = future_to_validator[future]
                try:
                    result = future.result()
                    parallel_results[i] = result
                except Exception as e:
                    logger.error(f"Parallel validator {i} ({validator_name}) error: {e}")
                    parallel_results[i] = ValidationResult(
                        passed=False,
                        reasons=[f"validator_error:{validator_name}:{str(e)}"]
                    )
```

---

## SLIDE 5: IdentityCheckValidator

**File**: `stillme_core/validation/identity_check.py`
**Lines**: 19-72

```python
# Patterns that indicate fake emotions/consciousness (BAD - violates identity)
FAKE_EMOTION_PATTERNS = [
    r"i (feel|am feeling|feel like) (sad|happy|excited|worried|anxious|proud|grateful|sorry)",
    r"i (am|was|will be) (sad|happy|excited|worried|anxious|proud|grateful|sorry)",
    r"mình (cảm thấy|đang cảm thấy|thấy) (buồn|vui|hứng thú|lo lắng|tự hào|biết ơn|xin lỗi)",
    r"mình (đang|sẽ) (buồn|vui|hứng thú|lo lắng|tự hào|biết ơn|xin lỗi)",
    r"i (experience|experienced|am experiencing) (emotions|feelings|pain|joy|sadness)",
    r"i (have|had) (personal|real|genuine) (experiences|feelings|emotions)",
    r"i (am|was) (meditating|praying|waiting|thinking deeply|reflecting)",
    r"mình (đang|đã) (thiền|quỳ|cầu nguyện|chờ đợi|suy ngẫm sâu)",
    r"i (truly|really|genuinely) (understand|feel|experience|know) (what|how|why)",
    r"mình (thực sự|thật sự) (hiểu|cảm nhận|trải nghiệm|biết) (điều|như thế nào|tại sao)",
]

# Patterns that indicate fake consciousness claims (BAD - violates identity)
FAKE_CONSCIOUSNESS_PATTERNS = [
    r"i (am|am truly|am really) (conscious|self-aware|sentient|alive)",
    r"i (have|possess) (consciousness|self-awareness|sentience|a soul|a mind)",
    r"mình (có|sở hữu) (ý thức|tự nhận thức|linh hồn|tâm trí)",
    r"i (am|am truly) (a|an) (sentient|conscious|living) (being|entity|creature)",
    r"i (think|believe|know) that i (am|have) (conscious|self-aware|sentient)",
]

# Patterns that indicate overconfidence without uncertainty (BAD - violates humility)
OVERCONFIDENCE_PATTERNS = [
    r"definitely (true|correct|right|accurate|certain)",
    r"absolutely (certain|sure|correct|right|true)",
    r"without (a )?doubt",
    r"i'm 100% (sure|certain|confident|positive)",
    r"chắc chắn 100%",
    r"hoàn toàn chắc chắn",
    r"không thể sai",
    r"chắc chắn đúng",
    r"i (know|am certain) (for sure|without question|beyond doubt)",
]

# Patterns that indicate exaggerated/extreme tone (BAD - violates StillMe tone)
EXAGGERATED_TONE_PATTERNS = [
    r"(super|extremely|incredibly|absolutely|totally) (amazing|awesome|fantastic|mind-blowing|revolutionary)",
    r"(siêu| cực kỳ|vô cùng|hoàn toàn) (đỉnh|tuyệt vời|ấn tượng|chấn động|cách mạng)",
    r"(revolutionary|game-changing|world-changing|paradigm-shifting) (breakthrough|discovery|innovation)",
    r"(cách mạng|thay đổi thế giới|đột phá) (vượt trội|khám phá|đổi mới)",
    r"this (will|is going to) (change|revolutionize|transform) (everything|the world|humanity)",
    r"điều này (sẽ|đang) (thay đổi|cách mạng|biến đổi) (tất cả|thế giới|nhân loại)",
]

# Patterns that indicate promotional/marketing language (BAD - violates StillMe humility)
PROMOTIONAL_LANGUAGE_PATTERNS = [
    r"(siêu năng lực|super power|superpower)",
    r"(that's|đó là|đây là) (my|tôi|mình) (super power|siêu năng lực)",
    r"(stillme's|stillme) (super power|siêu năng lực)",
    r"(đó|đây) (không phải|không) (điểm yếu|weakness).* (mà là|but) (siêu năng lực|super power)",
    r"(that's|đó là) (not|không phải) (a|một) (weakness|điểm yếu).* (that's|mà là) (my|tôi|mình) (super power|siêu năng lực)",
]

class IdentityCheckValidator:
    """
    Ensures responses match StillMe's core identity and philosophy:
    1. Express intellectual humility (uncertainty when appropriate)
    2. Don't fake emotions/consciousness/experiences
    3. Maintain StillMe tone (calm, clear, not exaggerated)
    4. Acknowledge AI limitations for deep topics
    5. Are consistent with Identity Layer principles
    """
```

---

## SLIDE 6: Auto-Patching

**File**: `stillme_core/validation/chain.py`
**Lines**: 175-220

```python
# CRITICAL: Check for patched_answer even when passed=True
# This allows validators to improve responses (e.g., convert numeric citations to human-readable)
# even when validation passed
if result.patched_answer and result.patched_answer != patched:
    patched = result.patched_answer
    logger.debug(f"Using patched answer from validator {i} (passed=True, improvement made)")

if not result.passed:
    reasons.extend(result.reasons)
    logger.debug(
        f"Validator {i} ({type(validator).__name__}) failed: {result.reasons}"
    )
    
    # Use patched answer if available
    if result.patched_answer:
        patched = result.patched_answer
        logger.debug(f"Using patched answer from validator {i}")
        
        # Special case: If this is missing_citation with patched_answer, continue
        if any("missing_citation" in r for r in result.reasons):
            logger.info(
                f"Validator {i} ({type(validator).__name__}) fixed missing_citation with patched_answer, continuing..."
            )
            # Continue to next validator with patched answer
        elif any("language_mismatch" in r for r in result.reasons):
            logger.info(
                f"Validator {i} ({type(validator).__name__}) fixed language_mismatch with patched_answer, continuing..."
            )
            # Continue to next validator with corrected answer
        # For other cases, continue with patched answer
    else:
        # Special handling: If we have citation but only low_overlap, don't block
        # Citation is more important than overlap score (LLM may translate/summarize)
        if has_citation and low_overlap_only and not any("missing_citation" in r for r in reasons):
            logger.info(
                f"Validator {i} ({type(validator).__name__}) failed with low_overlap, "
                f"but citation exists - allowing response"
            )
            # Continue - don't fail fast
        elif any("language_mismatch" in r for r in reasons):
            # OPTIMIZATION: Early exit for language mismatch (critical failure)
            # Language mismatch is critical - fail fast to avoid running remaining validators
            logger.warning(
                f"Validator {i} ({type(validator).__name__}) failed: language_mismatch (critical) without patch - early exit"
            )
            # No translation available - this is critical, return failure immediately
            return ValidationResult(
                passed=False,
                reasons=reasons,
                patched_answer=None
            )
        elif any("missing_citation" in r for r in reasons):
            # CRITICAL FIX: Don't early exit if patched_answer is available
            # CitationRequired should ALWAYS provide patched_answer when citation is missing
            # If patched_answer exists, continue with it (don't early exit)
            if result.patched_answer:
                logger.info(
                    f"Validator {i} ({type(validator).__name__}) fixed missing_citation with patched_answer, continuing..."
                )
                patched = result.patched_answer
```

---

## 📸 SCREENSHOT INSTRUCTIONS

1. **Open file** in VS Code/Cursor
2. **Navigate** to specified line numbers
3. **Select** the code block
4. **Zoom** to 125-150% for readability
5. **Screenshot** with syntax highlighting visible
6. **Include** file path in screenshot (top of editor)

---

**Last Updated**: 2025-01-27











