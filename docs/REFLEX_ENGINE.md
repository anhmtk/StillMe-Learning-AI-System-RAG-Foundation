# Reflex Engine - StillMe AI Framework

## Overview

The Reflex Engine is a sophisticated habit learning and safety-aware decision system that enables fast, context-aware responses while maintaining strict safety and privacy controls. It operates in **shadow mode** by default, allowing for safe evaluation and gradual rollout.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Input Text    │───▶│  Pattern Matcher │───▶│  Reflex Policy  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Habit Store    │◀───│  Reflex Engine   │───▶│  Safety Guard   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Observability   │◀───│  Action Sandbox  │───▶│   Decision      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Components

### 1. Pattern Matcher
- **Aho-Corasick Algorithm**: Fast multi-pattern matching
- **Unicode Normalization**: NFC/NFKC support for international text
- **Case Folding**: Vietnamese/English case-insensitive matching
- **Emoji-Safe Processing**: Robust emoji handling
- **Homoglyph Detection**: Latin vs Cyrillic character detection

### 2. Reflex Policy
- **Multi-Score Decision Making**: Combines pattern, context, history, and abuse scores
- **Policy Levels**: Strict, Balanced, Creative modes
- **Environment Overrides**: Configurable via ENV variables
- **Weighted Scoring**: Customizable score weights

### 3. Safety Guard
- **Fast Check**: Regex-based pattern matching and entropy analysis
- **Deep Check**: Simulated EthicsGuard integration with timeout
- **Circuit Breaker**: Prevents cascade failures
- **Progressive Safety**: Escalates from fast to deep checks

### 4. Action Sandbox
- **Idempotency**: Prevents duplicate executions
- **Dry-Run Mode**: Safe testing without side effects
- **Side-Effect Blocking**: Prevents dangerous I/O operations
- **Execution History**: Tracks all actions for auditing

### 5. Habit Store
- **Opt-in Privacy**: Disabled by default for privacy
- **Quorum Requirements**: Prevents single-user poisoning
- **Decay Mechanism**: Habits fade over time if unused
- **TTL/Retention**: Automatic data expiration
- **GDPR Compliance**: Export/delete capabilities

### 6. Observability
- **Structured Logging**: JSON format with trace IDs
- **Metrics Collection**: Performance and accuracy metrics
- **Shadow Evaluation**: Precision/recall tracking
- **Report Generation**: Automated performance reports

## Configuration

### Basic Configuration
```yaml
# config/reflex_engine.yaml
enabled: true
shadow_mode: true
policy: "balanced"

# Privacy settings
privacy:
  enabled: true
  habits_opt_in: false  # Default: opt-out
  hash_cues: true
  ttl_days: 90

# Quorum settings
quorum:
  threshold: 3
  window_days: 7

# Decay settings
decay:
  half_life_days: 30
  min_threshold: 0.1

# Observability
observability:
  log_level: "INFO"
  log_format: "json"
  enable_metrics: true
  enable_shadow_evaluation: true
```

### Environment Variables
```bash
# Core settings
STILLME__REFLEX__ENABLED=true
STILLME__REFLEX__SHADOW_MODE=true
STILLME__REFLEX__POLICY=balanced

# Privacy settings
STILLME__PRIVACY__ENABLED=true
STILLME__PRIVACY__HABITS_OPT_IN=false
STILLME__PRIVACY__HASH_CUES=true
STILLME__PRIVACY__TTL_DAYS=90

# Quorum settings
STILLME__QUORUM__THRESHOLD=3
STILLME__QUORUM__WINDOW_DAYS=7

# Decay settings
STILLME__DECAY__HALF_LIFE_DAYS=30
STILLME__DECAY__MIN_THRESHOLD=0.1
```

## Usage

### Basic Usage
```python
from stillme_core.middleware.reflex_engine import ReflexEngine

# Initialize engine
engine = ReflexEngine()

# Analyze input
result = engine.analyze(
    text="Hello, how are you?",
    context={"mode": "chat", "user_type": "premium"},
    user_id="user123",
    tenant_id="tenant456"
)

# Result structure
{
    "trace_id": "reflex_1758878091_a1b2c3d4",
    "decision": "fallback",  # Always fallback in shadow mode
    "shadow": True,
    "why_reflex": {
        "scores": {
            "pattern_score": 0.8,
            "context_score": 0.6,
            "history_score": 0.0,
            "abuse_score": 0.0
        },
        "matches": [...],
        "pattern_hits": 2,
        "habit_score": 0.0,
        "habit_action": None,
        "policy": "balanced",
        "confidence": 0.7,
        "breakdown": {...},
        "safety_result": {"safe": True, "reason": "safe"},
        "action_result": None,
        "original_decision": "allow_reflex",
        "processing_time_ms": 5.2
    }
}
```

### Habit Learning (Opt-in)
```python
# Enable habit learning for a user
config = {
    "privacy": {"habits_opt_in": True},
    "quorum": {"threshold": 2}
}
engine = ReflexEngine(config)

# After multiple safe interactions, habits are learned
result = engine.analyze(
    text="What's the weather like?",
    user_id="user123",
    tenant_id="tenant456"
)
```

### Observability
```python
from stillme_core.middleware.observability import ObservabilityManager

# Initialize observability
obs = ObservabilityManager()

# Get metrics
metrics = obs.get_metrics()
print(f"Total requests: {metrics['total_requests']}")
print(f"Reflex hits: {metrics['reflex_hits']}")
print(f"Fallback count: {metrics['fallback_count']}")

# Get shadow evaluation
evaluation = obs.get_shadow_evaluation(hours=24)
if evaluation["evaluation_ready"]:
    print(f"Precision: {evaluation['performance']['precision']:.3f}")
    print(f"Recall: {evaluation['performance']['recall']:.3f}")
    print(f"Ready for production: {evaluation['ready_for_production']}")
```

## Shadow Mode

### What is Shadow Mode?
Shadow mode is a safe evaluation environment where:
- All decisions are calculated but never executed
- Results are logged for analysis
- No side effects occur
- Perfect for testing and gradual rollout

### Shadow Evaluation
The system tracks:
- **Precision**: How often reflex decisions are correct
- **Recall**: How often correct decisions are made by reflex
- **False Positive Rate**: How often reflex makes wrong decisions
- **Processing Time**: Performance metrics

### Production Readiness Criteria
To move out of shadow mode, the system must meet:
- **Precision ≥ 95%**: Reflex decisions are highly accurate
- **Recall ≥ 80%**: Reflex catches most appropriate cases
- **FP Rate ≤ 5%**: Low false positive rate
- **P95 Processing Time ≤ 10ms**: Fast enough for production
- **Zero Security Issues**: No secrets or PII leaks
- **Sufficient Data**: At least 100 evaluation samples

## Privacy & Security

### Privacy Features
- **Opt-in by Default**: Habit learning disabled by default
- **Data Minimization**: Only necessary data collected
- **Cue Hashing**: User input hashed for privacy
- **TTL/Retention**: Automatic data expiration
- **GDPR Compliance**: Export/delete capabilities

### Security Features
- **Progressive Safety**: Fast → Deep check escalation
- **Circuit Breaker**: Prevents cascade failures
- **Side-Effect Blocking**: Prevents dangerous operations
- **Idempotency**: Prevents duplicate executions
- **Audit Logging**: Complete action history

### Threat Mitigation
- **Habit Poisoning**: Quorum requirements prevent single-user attacks
- **Data Leakage**: Cue hashing prevents input reconstruction
- **Timing Attacks**: Decay mechanisms prevent long-term tracking
- **Injection Attacks**: Safety patterns block malicious input

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test categories
pytest -m "unit"           # Unit tests
pytest -m "integration"    # Integration tests
pytest -m "security"       # Security tests

# Run Reflex Engine specific tests
pytest tests/test_reflex_engine_*.py
pytest tests/test_pattern_matcher.py
pytest tests/test_reflex_policy.py
pytest tests/test_reflex_safety.py
pytest tests/test_action_sandbox.py
pytest tests/test_habit_store.py
pytest tests/test_observability.py
```

### Test Coverage
```bash
# Generate coverage report
pytest --cov=stillme_core --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Performance Benchmarks
```bash
# Run performance tests
pytest tests/ -k "benchmark"

# Pattern matcher performance
pytest tests/test_pattern_matcher.py::TestPatternMatcher::test_performance_benchmark
```

## Monitoring & Observability

### Logs
All logs are in structured JSON format:
```json
{
  "timestamp": 1758878091000,
  "trace_id": "reflex_1758878091_a1b2c3d4",
  "user_id": "user123",
  "tenant_id": "tenant456",
  "event": "reflex_decision",
  "decision": "fallback",
  "confidence": 0.7,
  "processing_time_ms": 5.2,
  "shadow_mode": true,
  "why_reflex": {
    "scores": {...},
    "matches": [...],
    "policy": "balanced",
    "safety_result": {...}
  }
}
```

### Metrics
Key metrics tracked:
- `reflex_hits`: Successful reflex decisions
- `reflex_misses`: Failed reflex decisions
- `safety_fails`: Safety check failures
- `fallback_count`: Fallback to reasoning
- `avg_processing_time_ms`: Average processing time
- `p95_processing_time_ms`: 95th percentile processing time

### Shadow Evaluation Report
Generate evaluation reports:
```bash
# Generate report
python scripts/generate_shadow_report.py

# Generate with custom window
python scripts/generate_shadow_report.py --hours 48 --output reports/eval-48h.md
```

## Rollout Strategy

### Phase 1: Shadow Mode (Current)
- ✅ All components implemented
- ✅ Comprehensive testing
- ✅ Privacy controls active
- ✅ Security measures in place
- 🔄 Shadow evaluation ongoing

### Phase 2: Gated Rollout (5% Traffic)
- Enable for 5% of users
- Monitor metrics closely
- Maintain shadow evaluation
- Quick rollback capability

### Phase 3: Canary Deployment (25% Traffic)
- Expand to 25% of users
- A/B testing with control group
- Performance optimization
- User feedback collection

### Phase 4: Full Production (100% Traffic)
- Complete rollout
- Continuous monitoring
- Regular performance reviews
- Feature enhancements

## Troubleshooting

### Common Issues

#### High False Positive Rate
```bash
# Check shadow evaluation
python scripts/generate_shadow_report.py

# Adjust thresholds
export STILLME__THRESHOLDS__BALANCED__ALLOW_REFLEX=0.7
```

#### Slow Processing Time
```bash
# Check performance benchmarks
pytest tests/test_pattern_matcher.py::TestPatternMatcher::test_performance_benchmark

# Optimize pattern matching
# Consider reducing pattern count or using Aho-Corasick
```

#### Privacy Concerns
```bash
# Verify privacy settings
python -c "
from stillme_core.middleware.habit_store import HabitStore
store = HabitStore()
print(f'Habit learning enabled: {store.is_enabled()}')
print(f'Cue hashing enabled: {store.hash_cues}')
"
```

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('stillme_core.middleware').setLevel(logging.DEBUG)

# Run with detailed output
engine = ReflexEngine()
result = engine.analyze("test input", context={"debug": True})
print(result["why_reflex"])
```

## Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd stillme_ai

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
ruff check . --fix
pyright stillme_core/ tests/
```

### Code Style
- Follow PEP 8
- Use type hints
- Write comprehensive tests
- Document public APIs
- Follow security best practices

### Pull Request Process
1. Create feature branch
2. Implement changes with tests
3. Run full test suite
4. Update documentation
5. Submit pull request
6. Address review feedback

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:
- **Documentation**: [docs/REFLEX_ENGINE.md](REFLEX_ENGINE.md)
- **Privacy**: [docs/PRIVACY_MODE.md](PRIVACY_MODE.md)
- **Issues**: GitHub Issues
- **Security**: security@stillme.ai

---

*Last updated: 2024-01-15*
