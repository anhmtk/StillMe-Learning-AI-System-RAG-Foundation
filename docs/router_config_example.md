# AI Router Configuration Guide

## Environment Variables

Copy the following to your `.env` file and customize as needed:

```bash
# =============================================================================
# AI PROVIDER CONFIGURATION
# =============================================================================

# DeepSeek API Key (for complex questions)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# OpenAI API Key (legacy support)
OPENAI_API_KEY=your_openai_api_key_here

# OpenRouter API Key (legacy support)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Preferred AI Provider
PREFERRED_PROVIDER=deepseek

# =============================================================================
# AI ROUTING CONFIGURATION
# =============================================================================

# Complexity Analysis Weights (0.0 - 1.0)
# Higher weights = more influence on complexity score
COMPLEXITY_WEIGHT_LENGTH=0.2
COMPLEXITY_WEIGHT_INDICATORS=0.15
COMPLEXITY_WEIGHT_ACADEMIC=0.2
COMPLEXITY_WEIGHT_ABSTRACT=0.25
COMPLEXITY_WEIGHT_MULTIPART=0.1
COMPLEXITY_WEIGHT_CONDITIONAL=0.15
COMPLEXITY_WEIGHT_DOMAIN=0.3

# Complexity Thresholds for Model Selection
# 0.0 - 0.4: Simple (gemma2:2b)
# 0.4 - 0.7: Medium (deepseek-coder:6.7b)  
# 0.7 - 1.0: Complex (deepseek-chat)
COMPLEXITY_THRESHOLD_SIMPLE=0.4
COMPLEXITY_THRESHOLD_MEDIUM=0.7

# =============================================================================
# TRANSLATION CONFIGURATION
# =============================================================================

# Core language for AI processing (usually English)
TRANSLATION_CORE_LANG=en

# Translation engine priority (comma-separated)
# Options: gemma, nllb
TRANSLATOR_PRIORITY=gemma,nllb

# NLLB Model Name
# Options: facebook/nllb-200-distilled-600M (faster), facebook/nllb-200-distilled-1.3B (better quality)
NLLB_MODEL_NAME=facebook/nllb-200-distilled-600M

# =============================================================================
# SERVER CONFIGURATION
# =============================================================================

# StillMe AI Server Port
AI_SERVER_PORT=1216

# Gateway Port
GATEWAY_PORT=21568

# Chat UI Port
CHAT_UI_PORT=3000

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Log Level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Enable Debug Mode for Complexity Analysis
DEBUG_COMPLEXITY=false

# =============================================================================
# PERFORMANCE CONFIGURATION
# =============================================================================

# Maximum analysis time (milliseconds)
MAX_ANALYSIS_TIME_MS=5

# Fallback log size limit
MAX_FALLBACK_LOG=1000

# Performance log size limit
MAX_PERFORMANCE_LOG=100

# =============================================================================
# SECURITY CONFIGURATION
# =============================================================================

# Enable CORS for Chat UI
ENABLE_CORS=true

# Allowed CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,http://192.168.1.12:3000,http://192.168.1.12:3001

# =============================================================================
# DEVELOPMENT CONFIGURATION
# =============================================================================

# Enable hot reload for development
ENABLE_HOT_RELOAD=true

# Enable detailed logging for development
ENABLE_DEBUG_LOGGING=false

# Test mode (disables external API calls)
TEST_MODE=false
```

## Weight Calibration

### Understanding Weights

The complexity analysis uses weighted heuristics to determine prompt complexity:

- **Length Weight (0.2)**: Influence of prompt length on complexity
- **Indicators Weight (0.15)**: Influence of complex question words
- **Academic Weight (0.2)**: Influence of academic/scientific terms
- **Abstract Weight (0.25)**: Influence of abstract concepts
- **Multipart Weight (0.1)**: Influence of multiple questions
- **Conditional Weight (0.15)**: Influence of conditional statements
- **Domain Weight (0.3)**: Influence of domain-specific terms

### Calibration Process

1. **Run Test Suite**: Use `python tests/test_router.py` to get baseline accuracy
2. **Analyze Results**: Check which prompts are misclassified
3. **Adjust Weights**: Modify weights based on misclassification patterns
4. **Re-test**: Run tests again to verify improvements

### Example Calibration

If academic questions are being classified as simple:

```bash
# Increase academic weight
COMPLEXITY_WEIGHT_ACADEMIC=0.3

# Decrease length weight if it's too dominant
COMPLEXITY_WEIGHT_LENGTH=0.15
```

## Threshold Tuning

### Model Selection Thresholds

- **Simple Threshold (0.4)**: Below this → gemma2:2b
- **Medium Threshold (0.7)**: Above this → deepseek-chat
- **Between thresholds**: deepseek-coder:6.7b

### Tuning Process

1. **Monitor Performance**: Check which models are being selected
2. **Analyze Quality**: Review response quality for each model
3. **Adjust Thresholds**: Fine-tune based on performance data

### Example Tuning

If too many simple questions go to complex models:

```bash
# Lower the medium threshold
COMPLEXITY_THRESHOLD_MEDIUM=0.6

# Or raise the simple threshold
COMPLEXITY_THRESHOLD_SIMPLE=0.5
```

## Performance Optimization

### Analysis Speed

The complexity analyzer should complete in < 5ms:

```bash
# Monitor performance
python -c "
from stillme_core.modules.api_provider_manager import UnifiedAPIManager
import time

manager = UnifiedAPIManager()
start = time.time()
manager.choose_model('test prompt')
print(f'Analysis time: {(time.time() - start) * 1000:.2f}ms')
"
```

### Memory Usage

- **Keyword Sets**: Pre-compiled for O(1) lookup
- **Fallback Log**: Limited to 1000 entries
- **Performance Log**: Limited to 100 entries

## Fallback Configuration

### Trigger Conditions

Fallback is triggered when user feedback contains:

- Negative indicators: "sai", "không đúng", "không hiểu"
- Confusion markers: "???", "??"
- Very short responses: < 10 characters

### Fallback Chain

1. **Cloud Model**: deepseek-chat (highest quality)
2. **Local Coder**: deepseek-coder:6.7b (good for coding)
3. **Simple Model**: gemma2:2b (fastest)

## Monitoring and Debugging

### Enable Debug Mode

```bash
DEBUG_COMPLEXITY=true
```

This will log detailed complexity breakdowns:

```
🧠 Complexity Analysis (DEBUG): 0.750
   length: 0.500
   complex_indicators: 0.200
   academic_terms: 0.250
   abstract_concepts: 0.300
   multi_part: 0.000
   conditional: 0.000
   domain_specific: 0.500
```

### Get Statistics

```python
from stillme_core.modules.api_provider_manager import UnifiedAPIManager

manager = UnifiedAPIManager()
stats = manager.get_analyzer_stats()

print("Performance:", stats['performance'])
print("Fallback:", stats['fallback'])
print("Weights:", stats['weights'])
print("Thresholds:", stats['thresholds'])
```

### Test Suite

Run comprehensive tests:

```bash
# Full test suite
python tests/test_router.py

# Performance benchmark only
python -c "
from tests.test_router import run_performance_benchmark
run_performance_benchmark()
"

# Accuracy test only
python -c "
from tests.test_router import run_accuracy_test
run_accuracy_test()
"
```

## Best Practices

### 1. Start with Defaults

Use the default weights and thresholds first, then tune based on your specific use case.

### 2. Monitor Continuously

Regularly check performance and accuracy metrics to ensure optimal routing.

### 3. Test Thoroughly

Run the test suite after any configuration changes to ensure no regressions.

### 4. Document Changes

Keep track of configuration changes and their impact on performance.

### 5. Gradual Tuning

Make small adjustments to weights and thresholds rather than large changes.

## Troubleshooting

### Common Issues

1. **Slow Analysis**: Check if keyword sets are properly pre-compiled
2. **Poor Accuracy**: Review weight calibration and threshold tuning
3. **Too Many Fallbacks**: Check fallback trigger conditions
4. **Memory Issues**: Verify log size limits are appropriate

### Debug Commands

```bash
# Check complexity analysis
python -c "
from stillme_core.modules.api_provider_manager import UnifiedAPIManager
manager = UnifiedAPIManager()
score, details = manager.complexity_analyzer.analyze_complexity('your prompt here', debug=True)
print(f'Score: {score}')
print(f'Details: {details}')
"

# Check model selection
python -c "
from stillme_core.modules.api_provider_manager import UnifiedAPIManager
manager = UnifiedAPIManager()
model = manager.choose_model('your prompt here', debug=True)
print(f'Selected model: {model}')
"

# Check fallback detection
python -c "
from stillme_core.modules.api_provider_manager import UnifiedAPIManager
manager = UnifiedAPIManager()
should_fallback = manager.complexity_analyzer.should_trigger_fallback('sai rồi', 'test prompt', 'gemma2:2b')
print(f'Should fallback: {should_fallback}')
"
```
