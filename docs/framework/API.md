# StillMe Core API Reference

## Overview

This document provides a comprehensive API reference for StillMe Core Framework.

## Core Modules

### Validation (`stillme_core.validation`)

#### `ValidationEngine`

Main validation orchestrator.

```python
from stillme_core.validation import ValidationEngine

engine = ValidationEngine()
result = engine.validate(
    question="What is AI?",
    answer="AI is artificial intelligence...",
    context_docs=[...],
    # ... other parameters
)
```

**Key Methods**:
- `validate()`: Run all validators and return aggregated result
- `add_validator()`: Register a new validator
- `remove_validator()`: Remove a validator

#### `Validator` (Base Class)

Base class for all validators.

```python
from stillme_core.validation import Validator, ValidationResult

class MyValidator(Validator):
    def validate(self, question: str, answer: str, **kwargs) -> ValidationResult:
        # Validation logic
        return ValidationResult(
            passed=True,
            confidence=0.9,
            reasons=["Reason 1", "Reason 2"]
        )
```

**Available Validators**:
- `CitationRequired`: Ensures citations are present
- `CitationRelevance`: Validates citation relevance
- `EvidenceOverlap`: Checks evidence overlap with answer
- `ConfidenceValidator`: Validates confidence scores
- `LanguageValidator`: Validates language consistency
- `IdentityCheckValidator`: Checks StillMe identity
- `EgoNeutralityValidator`: Ensures ego-neutral responses
- `SourceConsensusValidator`: Validates source consensus
- `PhilosophicalDepthValidator`: Validates philosophical depth
- And 18+ more...

### RAG (`stillme_core.rag`)

#### `RAGRetrieval`

Main RAG retrieval interface.

```python
from stillme_core.rag import RAGRetrieval

rag = RAGRetrieval()
context = rag.retrieve_context(
    query="What is machine learning?",
    knowledge_limit=5,
    similarity_threshold=0.6
)
```

**Key Methods**:
- `retrieve_context()`: Retrieve context documents
- `add_learning_content()`: Add new content to knowledge base
- `retrieve_by_tier()`: Retrieve from specific knowledge tier

#### `ChromaClient`

Vector database client.

```python
from stillme_core.rag import ChromaClient

client = ChromaClient()
# Use client for direct database operations
```

#### `EmbeddingService`

Embedding generation service.

```python
from stillme_core.rag import EmbeddingService

service = EmbeddingService()
embeddings = service.embed(["text 1", "text 2"])
```

### External Data (`stillme_core.external_data`)

#### `ExternalDataOrchestrator`

Coordinates external data fetching.

```python
from stillme_core.external_data import ExternalDataOrchestrator

orchestrator = ExternalDataOrchestrator()
result = await orchestrator.fetch_data(
    intent=ExternalDataIntent.WEATHER,
    query="weather in New York"
)
```

**Key Methods**:
- `fetch_data()`: Fetch data for a specific intent
- `register_provider()`: Register a new provider

#### `detect_external_data_intent()`

Detect if query requires external data.

```python
from stillme_core.external_data import detect_external_data_intent

intent = detect_external_data_intent("What's the weather today?")
# Returns: ExternalDataIntent.WEATHER
```

#### `ExternalDataProvider` (Base Class)

Base class for external data providers.

```python
from stillme_core.external_data import ExternalDataProvider, ExternalDataResult

class MyProvider(ExternalDataProvider):
    async def fetch(self, query: str) -> ExternalDataResult:
        # Fetch logic
        return ExternalDataResult(
            success=True,
            data={"key": "value"},
            source="my_provider"
        )
```

### Learning (`stillme_core.learning`)

#### `LearningScheduler`

Automated learning scheduler.

```python
from stillme_core.learning import LearningScheduler
from stillme_core.rag import RAGRetrieval

rag = RAGRetrieval()
scheduler = LearningScheduler(
    rag_retrieval=rag,
    interval_hours=4
)

await scheduler.start()
# Runs learning cycles every 4 hours
```

**Key Methods**:
- `start()`: Start the scheduler
- `stop()`: Stop the scheduler
- `run_learning_cycle()`: Run a single learning cycle
- `get_status()`: Get scheduler status

#### `LearningPipeline` (Abstract Interface)

Abstract learning pipeline interface.

```python
from stillme_core.learning import LearningPipeline, LearningResult

class MyPipeline(LearningPipeline):
    def run_learning_cycle(self) -> LearningResult:
        # Learning logic
        return LearningResult(
            cycle_number=1,
            entries_fetched=10,
            entries_added=8,
            entries_filtered=2,
            sources={"rss": 5, "arxiv": 5},
            duration_seconds=30.0
        )
```

#### `ContentCurator`

Content filtering and prioritization.

```python
from stillme_core.learning import ContentCurator

curator = ContentCurator()
filtered, rejected = curator.pre_filter_content(content_list)
```

**Key Methods**:
- `pre_filter_content()`: Filter content before embedding
- `prioritize_content()`: Prioritize content by importance

#### `LearningFetcher` (Abstract Interface)

Abstract fetcher interface.

```python
from stillme_core.learning import LearningFetcher

class MyFetcher(LearningFetcher):
    def fetch(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        # Fetch logic
        return [{"title": "...", "content": "...", ...}]
    
    def get_source_name(self) -> str:
        return "my_source"
```

### Post-Processing (`stillme_core.postprocessing`)

#### `PostProcessor` (Abstract Interface)

Abstract post-processing interface.

```python
from stillme_core.postprocessing import PostProcessor, PostProcessingResult

class MyProcessor(PostProcessor):
    def process(self, text: str, context: Optional[Dict] = None) -> PostProcessingResult:
        # Processing logic
        return PostProcessingResult(
            processed_text="...",
            quality_score=0.9,
            rewrite_attempted=False
        )
    
    def evaluate_quality(self, text: str) -> float:
        return 0.9
```

#### `QualityEvaluator`

Assess response quality.

```python
from stillme_core.postprocessing import QualityEvaluator

evaluator = QualityEvaluator()
issues = evaluator.evaluate(
    text="Response text...",
    question="Original question...",
    context_docs=[...]
)
```

#### `StyleSanitizer`

Normalize response style.

```python
from stillme_core.postprocessing import StyleSanitizer

sanitizer = StyleSanitizer()
sanitized = sanitizer.sanitize("Raw response text...")
```

#### `RewriteLLM`

Conditional LLM rewriting.

```python
from stillme_core.postprocessing import RewriteLLM

rewriter = RewriteLLM()
result = await rewriter.rewrite(
    text="Original text...",
    original_question="Question...",
    quality_issues=["issue1", "issue2"]
)
```

#### `PostProcessingOptimizer`

Smart skip logic for post-processing.

```python
from stillme_core.postprocessing import PostProcessingOptimizer

optimizer = PostProcessingOptimizer()
should_process = optimizer.should_process(
    question="Simple question?",
    answer="Simple answer."
)
```

### Monitoring (`stillme_core.monitoring`)

#### `UnifiedMetricsCollector`

Centralized metrics collection.

```python
from stillme_core.monitoring import get_metrics_collector, MetricCategory

metrics = get_metrics_collector()

# Record validation
metrics.record_validation(
    passed=True,
    reasons=["reason1"],
    confidence_score=0.9
)

# Record RAG retrieval
metrics.record_rag_retrieval(
    query="...",
    num_results=5,
    avg_similarity=0.8,
    retrieval_time_ms=100.0
)

# Record learning cycle
metrics.record_learning_cycle(
    cycle_number=1,
    entries_fetched=10,
    entries_added=8,
    duration_seconds=30.0
)

# Get metrics
all_metrics = metrics.get_all_metrics()
validation_metrics = metrics.get_metrics(MetricCategory.VALIDATION)
```

**Key Methods**:
- `record_validation()`: Record validation metrics
- `record_rag_retrieval()`: Record RAG metrics
- `record_learning_cycle()`: Record learning metrics
- `increment_counter()`: Increment a counter
- `set_gauge()`: Set a gauge value
- `record_histogram()`: Record histogram values
- `get_metrics()`: Get metrics for a category
- `get_all_metrics()`: Get all metrics

### Self-Improvement (`stillme_core.self_improvement`)

#### `ImprovementEngine`

Automated improvement engine.

```python
from stillme_core.self_improvement import get_improvement_engine

engine = get_improvement_engine()
suggestions = engine.generate_improvements(days=7)
```

**Key Methods**:
- `generate_improvements()`: Generate improvement suggestions
- `apply_improvements()`: Apply improvements automatically

#### `FeedbackLoop`

Feedback loop from validation to learning.

```python
from stillme_core.self_improvement import get_feedback_loop

loop = get_feedback_loop()
loop.process_validation_results(validation_results)
```

**Key Methods**:
- `process_validation_results()`: Process validation results
- `update_learning_priorities()`: Update learning priorities

#### `SelfImprovementAnalyzer`

Pattern analysis and knowledge gap detection.

```python
from stillme_core.self_improvement import get_self_improvement_analyzer

analyzer = get_self_improvement_analyzer()
patterns = analyzer.analyze_patterns(days=7)
gaps = analyzer.detect_knowledge_gaps()
```

**Key Methods**:
- `analyze_patterns()`: Analyze validation patterns
- `detect_knowledge_gaps()`: Detect knowledge gaps
- `suggest_learning_content()`: Suggest learning content

### Configuration (`stillme_core.config`)

#### `BaseConfig`

Base configuration class.

```python
from stillme_core.config import BaseConfig

class MyConfig(BaseConfig):
    def __init__(self):
        super().__init__()
        self.my_setting = self.get_env("MY_SETTING", default="default_value")
```

#### `ValidatorConfig`

Validator-specific configuration.

```python
from stillme_core.config import ValidatorConfig

config = ValidatorConfig()
threshold = config.get_threshold("confidence", default=0.8)
```

## Common Patterns

### Creating a Custom Validator

```python
from stillme_core.validation import Validator, ValidationResult

class CustomValidator(Validator):
    def validate(self, question: str, answer: str, **kwargs) -> ValidationResult:
        # Your validation logic
        passed = self._check_something(answer)
        return ValidationResult(
            passed=passed,
            confidence=0.9 if passed else 0.3,
            reasons=["Custom validation reason"]
        )

# Register it
engine = ValidationEngine()
engine.add_validator(CustomValidator())
```

### Creating a Custom Learning Fetcher

```python
from stillme_core.learning import LearningFetcher

class CustomFetcher(LearningFetcher):
    def fetch(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        # Fetch logic
        return [
            {
                "title": "Title",
                "summary": "Summary",
                "source": "custom_source",
                "link": "https://..."
            }
        ]
    
    def get_source_name(self) -> str:
        return "custom_source"
```

### Using Unified Metrics

```python
from stillme_core.monitoring import get_metrics_collector, MetricCategory

metrics = get_metrics_collector()

# Record custom metric
metrics.increment_counter(
    MetricCategory.VALIDATION,
    "custom_metric",
    metadata={"key": "value"}
)

# Get metrics
all_metrics = metrics.get_all_metrics()
print(all_metrics)
```

## Error Handling

All components follow consistent error handling:

- **Validation errors**: Return `ValidationResult` with `passed=False`
- **RAG errors**: Return empty context or raise exceptions
- **External data errors**: Return `ExternalDataResult` with `success=False`
- **Learning errors**: Log errors and continue with next cycle
- **Post-processing errors**: Return original text if processing fails

## Type Hints

All APIs use Python type hints for better IDE support and type checking.

```python
from typing import List, Dict, Any, Optional
from stillme_core.validation import ValidationResult

def my_function(text: str, count: int = 0) -> Optional[ValidationResult]:
    # ...
```

## Related Documentation

- [Architecture Guide](ARCHITECTURE.md)
- [Validation System Guide](VALIDATION.md)
- [Self-Improvement Guide](SELF_IMPROVEMENT.md)

