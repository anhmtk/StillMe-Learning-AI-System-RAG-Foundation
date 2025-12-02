# StillMe Core Framework Architecture

## Overview

StillMe Core is a modular framework for building transparent, validation-first AI systems. It emphasizes:

- **Transparency**: All decisions are logged and explainable
- **Validation**: Mandatory validation at every step
- **Intellectual Humility**: Honest about limitations and uncertainties
- **Self-Improvement**: Continuous learning from usage patterns

## Core Philosophy

> "We're building a framework, not just an app. Everything we build for StillMe today must be usable by other AI systems tomorrow."

## Architecture Overview

```
stillme_core/
├── validation/          # Validation engine with 27+ validators
├── rag/                 # RAG (Retrieval-Augmented Generation) system
├── external_data/       # External data providers (weather, news, time)
├── learning/            # Continuous learning pipeline
├── postprocessing/      # Post-processing and quality improvement
├── monitoring/          # Unified metrics and monitoring
├── self_improvement/    # Self-improvement mechanisms
└── config/             # Configuration management
```

## Component Architecture

### 1. Validation System (`stillme_core/validation/`)

**Purpose**: Ensure response quality, reduce hallucinations, enforce transparency.

**Key Components**:
- `ValidationEngine`: Orchestrates multiple validators
- `Validator`: Base class for all validators
- 27+ specialized validators (citation, confidence, evidence_overlap, etc.)

**Design Principles**:
- Modular: Each validator is independent
- Parallelizable: Validators can run concurrently
- Extensible: Easy to add new validators
- Observable: All validation decisions are logged

**Flow**:
```
User Query → ValidationEngine → [Validator1, Validator2, ...] → ValidationResult
```

### 2. RAG System (`stillme_core/rag/`)

**Purpose**: Retrieve relevant knowledge from vector database.

**Key Components**:
- `RAGRetrieval`: Main retrieval interface
- `ChromaClient`: Vector database client
- `EmbeddingService`: Embedding generation

**Features**:
- Multi-tier retrieval (L0-L3 knowledge levels)
- Similarity-based filtering
- MMR (Maximal Marginal Relevance) for diversity
- Context quality assessment

### 3. External Data System (`stillme_core/external_data/`)

**Purpose**: Fetch real-time data from external sources.

**Key Components**:
- `ExternalDataOrchestrator`: Coordinates data fetching
- `ExternalDataProvider`: Base class for providers
- Providers: Weather, News, Time, etc.

**Features**:
- Intent detection
- Rate limiting
- Caching
- Retry logic

### 4. Learning System (`stillme_core/learning/`)

**Purpose**: Continuously acquire and integrate new knowledge.

**Key Components**:
- `LearningPipeline`: Abstract learning interface
- `LearningScheduler`: Automated learning cycles
- `ContentCurator`: Content filtering and prioritization
- `LearningFetcher`: Abstract fetcher interface
- Fetchers: RSS, arXiv, CrossRef, Wikipedia

**Flow**:
```
LearningScheduler → Fetch from Sources → ContentCurator → RAG System
```

### 5. Post-Processing System (`stillme_core/postprocessing/`)

**Purpose**: Improve response quality after generation.

**Key Components**:
- `PostProcessor`: Abstract post-processing interface
- `QualityEvaluator`: Assess response quality
- `StyleSanitizer`: Normalize style
- `RewriteLLM`: Conditional rewriting
- `PostProcessingOptimizer`: Smart skip logic

**Flow**:
```
Generated Response → QualityEvaluator → [Rewrite if needed] → Final Response
```

### 6. Monitoring System (`stillme_core/monitoring/`)

**Purpose**: Unified metrics collection and monitoring.

**Key Components**:
- `UnifiedMetricsCollector`: Centralized metrics collection
- `MetricCategory`: Metric categories (VALIDATION, RAG, LEARNING, etc.)
- `MetricRecord`: Individual metric records

**Features**:
- Counters, gauges, histograms
- Persistent storage (JSONL)
- Category-based organization

### 7. Self-Improvement System (`stillme_core/self_improvement/`)

**Purpose**: Analyze patterns and suggest improvements.

**Key Components**:
- `ImprovementEngine`: Automated improvement cycles
- `FeedbackLoop`: Connect validation → learning
- `Analyzer`: Pattern analysis and knowledge gap detection

**Flow**:
```
Validation Results → Analyzer → Improvement Suggestions → Learning System
```

### 8. Configuration System (`stillme_core/config/`)

**Purpose**: Centralized, type-safe configuration.

**Key Components**:
- `BaseConfig`: Base configuration class
- `ValidatorConfig`: Validator-specific settings

**Features**:
- Environment variable support
- Type safety
- Easy testing with different configs

## Dependency Graph

```
stillme_app/ (StillMe Application)
    ↓
stillme_core/
    ├── validation/ (independent)
    ├── rag/ (independent)
    ├── external_data/ (independent)
    ├── learning/ → rag/ (uses RAG to store knowledge)
    ├── postprocessing/ (independent)
    ├── monitoring/ (used by all)
    ├── self_improvement/ → validation/, learning/
    └── config/ (used by all)
```

## Design Principles

### 1. Separation of Concerns
- **Core** (`stillme_core/`): Generic, reusable framework logic
- **App** (`stillme_app/` or `backend/`): Application-specific logic

### 2. Dependency Direction
- App depends on Core, not vice versa
- Core doesn't know about StillMe app specifics

### 3. Interface-Based Design
- Core provides abstract interfaces (ABC/Protocol)
- App implements application-specific logic

### 4. Configuration Injection
- Core receives config from app (dependency injection)
- No hardcoded application-specific values

### 5. Backward Compatibility
- During migration, adapters maintain old import paths
- No breaking changes for existing code

## Data Flow

### Request Flow
```
User Query
    ↓
External Data Detection → External Data Providers (if needed)
    ↓
RAG Retrieval → Context Documents
    ↓
LLM Generation → Response
    ↓
Validation Engine → Validation Results
    ↓
Post-Processing → Final Response
    ↓
Metrics Recording → UnifiedMetricsCollector
```

### Learning Flow
```
LearningScheduler (every N hours)
    ↓
Fetch from Sources (RSS, arXiv, etc.)
    ↓
ContentCurator → Filter & Prioritize
    ↓
RAG System → Add to Knowledge Base
    ↓
Metrics Recording → UnifiedMetricsCollector
```

### Self-Improvement Flow
```
Validation Results (accumulated)
    ↓
Analyzer → Pattern Analysis
    ↓
ImprovementEngine → Generate Suggestions
    ↓
FeedbackLoop → Update Learning Priorities
```

## Extension Points

### Adding a New Validator
1. Inherit from `Validator` base class
2. Implement `validate()` method
3. Register in `ValidationEngine`

### Adding a New Learning Fetcher
1. Inherit from `LearningFetcher` interface
2. Implement `fetch()` and `get_source_name()` methods
3. Add to `LearningScheduler`

### Adding a New External Data Provider
1. Inherit from `ExternalDataProvider` base class
2. Implement `fetch()` method
3. Register in `ExternalDataOrchestrator`

### Adding a New Post-Processor
1. Inherit from `PostProcessor` interface
2. Implement `process()` and `evaluate_quality()` methods
3. Integrate into post-processing pipeline

## Performance Considerations

- **Validation**: Parallel execution of independent validators
- **RAG**: Caching of retrieval results
- **Learning**: Pre-filtering to reduce embedding costs
- **Post-Processing**: Smart skip logic to avoid unnecessary rewrites

## Testing Strategy

- **Unit Tests**: Each component tested independently
- **Integration Tests**: Test component interactions
- **End-to-End Tests**: Test full pipeline
- **Backward Compatibility Tests**: Ensure old imports still work

## Future Enhancements

1. **SDK Package**: Package `stillme_core` as installable SDK
2. **Metrics Dashboard**: Visual dashboard for metrics
3. **Plugin System**: Dynamic loading of validators/fetchers
4. **Distributed Mode**: Support for distributed deployment

## Related Documentation

- [API Reference](API.md)
- [Validation System Guide](VALIDATION.md)
- [Self-Improvement Guide](SELF_IMPROVEMENT.md)
- [Migration Guide](../MIGRATION_GUIDE.md)

