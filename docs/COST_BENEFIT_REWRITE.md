# Cost-Benefit Logic for RewriteLLM

## Overview

StillMe implements a **cost-benefit policy** for the RewriteLLM system to intelligently decide when to rewrite responses for quality improvement. This prevents unnecessary rewrites that waste tokens and increase latency while ensuring critical quality issues are addressed.

## Self-Correction Modes

The system supports three modes (configurable via `SELF_CORRECTION_MODE` environment variable):

- **`off`**: No rewrites (disable self-correction)
- **`light`**: Conservative (max 1 rewrite for medium quality, max 2 for low quality)
- **`aggressive`**: More rewrites (max 2 for medium quality, max 2 for low quality)

**Default**: `light` (balanced cost and quality)

## Quality Thresholds

### High Quality (>= 0.8)
- **Action**: No rewrite
- **Reason**: Quality is already good enough

### Medium Quality (0.5 - 0.8)
- **Light mode**: Max 1 rewrite (only if critical issues present)
- **Aggressive mode**: Max 2 rewrites
- **Condition**: Only rewrite if critical issues or aggressive mode enabled

### Low Quality (< 0.5)
- **Action**: Max 2 rewrites allowed
- **Stop condition**: Stop if quality doesn't improve after rewrite

## Rewrite Decision Logic

### Initial Decision (`should_rewrite()`)

The system decides whether to rewrite based on:

1. **Quality score** from QualityEvaluator
2. **Critical issues** (anthropomorphic language, missing citations, template-like responses, topic drift)
3. **Current rewrite count** (prevents excessive rewrites)
4. **Self-correction mode** (off/light/aggressive)

### Continue Decision (`should_continue_rewrite()`)

After each rewrite, the system decides whether to continue:

- **Continue if**: Quality improved significantly (>= 0.2) but still below threshold
- **Stop if**: 
  - Quality reached threshold (>= 0.8)
  - Max attempts reached
  - Quality not improving (< 0.1 improvement) and still low

## Configuration

### Environment Variable

```bash
SELF_CORRECTION_MODE=light  # Options: off, light, aggressive
```

### Code Configuration

Thresholds can be adjusted in `RewriteDecisionPolicy.__init__()`:

```python
self.high_quality_threshold = 0.8  # No rewrite if >= this
self.medium_quality_threshold = 0.5  # Conditional rewrite if 0.5-0.8
self.max_attempts_light_medium = 1  # Light mode: max 1 for medium
self.max_attempts_aggressive_medium = 2  # Aggressive mode: max 2 for medium
self.max_attempts_low_quality = 2  # Low quality: max 2 attempts
```

## Logging

The system logs detailed metrics for monitoring:

```
🔄 Cost-Benefit: Rewrite decision - {reason}, quality_before={score:.2f}, rewrite_count={count}/{max}, mode={mode}
📊 Rewrite metrics (attempt {n}): quality_before={before:.2f}, quality_after={after:.2f}, improvement={improvement:+.2f}
✅ Rewrite loop complete: initial_quality={init:.2f}, final_quality={final:.2f}, total_rewrites={count}
```

## Benefits

1. **Cost Reduction**: Prevents unnecessary rewrites for already-good responses
2. **Latency Optimization**: Reduces response time by skipping redundant rewrites
3. **Quality Assurance**: Still addresses critical quality issues when needed
4. **Configurable**: Easy to adjust thresholds and modes based on requirements

## Architecture

- **Module**: `backend/postprocessing/rewrite_decision_policy.py`
- **Integration**: Used by `PostProcessingOptimizer.should_rewrite()`
- **Pipeline**: Integrated into `chat_router.py` rewrite loop

## Future Enhancements

- **ML-based Classifier**: Upgrade from rule-based to ML-based for more nuanced decisions
- **Token Cost Tracking**: Track actual token costs for each rewrite
- **Adaptive Thresholds**: Automatically adjust thresholds based on performance metrics

## See Also

- [Epistemic State Classification](EPISTEMIC_STATE.md)
- [Validation Chain Documentation](VALIDATION_CHAIN.md)
- [StillMe Architecture](../README.md)

