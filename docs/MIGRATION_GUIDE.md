# Migration Guide: From Old Structure to StillMe Core

This guide helps you migrate from the old `backend/` structure to the new `stillme_core/` framework structure.

## Overview

The StillMe codebase has been refactored into a modular framework:

- **Old**: Components in `backend/validators/`, `backend/vector_db/`, etc.
- **New**: Core framework in `stillme_core/`, app-specific code in `backend/`

## Migration Status

✅ **Backward Compatibility Maintained**: All old imports continue to work via adapters.

You can migrate gradually or continue using old imports. Both work!

## Import Changes

### Validation System

**Old**:
```python
from backend.validators import ValidatorChain
from backend.validators.citation import CitationRequired
```

**New** (Recommended):
```python
from stillme_core.validation import ValidationEngine
from stillme_core.validation import CitationRequired
```

**Old Still Works** (via adapter):
```python
from backend.validators import ValidatorChain  # Still works!
```

### RAG System

**Old**:
```python
from backend.vector_db.rag_retrieval import RAGRetrieval
from backend.vector_db.chroma_client import ChromaClient
```

**New** (Recommended):
```python
from stillme_core.rag import RAGRetrieval
from stillme_core.rag import ChromaClient
```

**Old Still Works** (via adapter):
```python
from backend.vector_db.rag_retrieval import RAGRetrieval  # Still works!
```

### External Data

**Old**:
```python
from backend.external_data import ExternalDataOrchestrator
from backend.external_data.providers.weather import WeatherProvider
```

**New** (Recommended):
```python
from stillme_core.external_data import ExternalDataOrchestrator
from stillme_core.external_data.providers.weather import WeatherProvider
```

**Old Still Works** (via adapter):
```python
from backend.external_data import ExternalDataOrchestrator  # Still works!
```

### Learning System

**Old**:
```python
from backend.services.learning_scheduler import LearningScheduler
from backend.services.content_curator import ContentCurator
```

**New** (Recommended):
```python
from stillme_core.learning import LearningScheduler
from stillme_core.learning import ContentCurator
```

**Old Still Works** (via adapter):
```python
from backend.services.learning_scheduler import LearningScheduler  # Still works!
```

### Post-Processing

**Old**:
```python
from backend.postprocessing import QualityEvaluator
from backend.postprocessing.rewrite_llm import RewriteLLM
```

**New** (Recommended):
```python
from stillme_core.postprocessing import QualityEvaluator
from stillme_core.postprocessing import RewriteLLM
```

**Old Still Works** (via adapter):
```python
from backend.postprocessing import QualityEvaluator  # Still works!
```

## Class Name Changes

### ValidatorChain → ValidationEngine

**Old**:
```python
from backend.validators import ValidatorChain
chain = ValidatorChain([...])
```

**New**:
```python
from stillme_core.validation import ValidationEngine
engine = ValidationEngine([...])
```

**Backward Compatibility**:
```python
from stillme_core.validation import ValidatorChain  # Alias for ValidationEngine
# Or
from backend.validators import ValidatorChain  # Still works via adapter
```

## Step-by-Step Migration

### Step 1: Update Imports (Optional)

You can update imports gradually. Start with new code:

```python
# New code uses new imports
from stillme_core.validation import ValidationEngine

# Old code continues to work
from backend.validators import ValidatorChain  # Still works!
```

### Step 2: Update Class Names (Optional)

If you want to use new class names:

```python
# Old
from backend.validators import ValidatorChain
chain = ValidatorChain([...])

# New
from stillme_core.validation import ValidationEngine
engine = ValidationEngine([...])
```

### Step 3: Use New APIs (Optional)

New APIs may have additional features:

```python
# Unified metrics (new)
from stillme_core.monitoring import get_metrics_collector
metrics = get_metrics_collector()
metrics.record_validation(...)
```

## Migration Checklist

- [ ] Review your codebase for old imports
- [ ] Decide: gradual migration or keep old imports
- [ ] Update new code to use `stillme_core/` imports
- [ ] Test thoroughly after changes
- [ ] Update documentation if needed

## Common Issues

### Issue 1: Import Errors

**Problem**: `ImportError: cannot import name 'X' from 'backend.Y'`

**Solution**: Use new import path:
```python
# Old (may break)
from backend.validators import X

# New (works)
from stillme_core.validation import X
```

### Issue 2: Class Not Found

**Problem**: `ValidatorChain` not found

**Solution**: Use `ValidationEngine` or import alias:
```python
# Option 1: Use new name
from stillme_core.validation import ValidationEngine

# Option 2: Use alias
from stillme_core.validation import ValidatorChain  # Alias for ValidationEngine
```

### Issue 3: Missing Methods

**Problem**: Method doesn't exist on new class

**Solution**: Check API documentation. Some methods may have been renamed or moved.

## Testing After Migration

After migrating, test thoroughly:

1. **Unit Tests**: Run all unit tests
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test full pipeline
4. **Manual Testing**: Test critical user flows

## Rollback Plan

If you encounter issues:

1. **Keep Old Imports**: Old imports still work via adapters
2. **Gradual Migration**: Migrate one module at a time
3. **Revert Changes**: Git allows easy rollback

## Benefits of Migration

### 1. Clear Separation
- Core framework (`stillme_core/`) is reusable
- App-specific code (`backend/`) is separate

### 2. Better Organization
- Components grouped by functionality
- Clear dependency direction

### 3. Future SDK
- Framework can be packaged as SDK
- Easier to share with community

### 4. New Features
- Unified metrics system
- Self-improvement mechanisms
- Configuration system

## Questions?

- Check [API Reference](framework/API.md)
- Check [Architecture Guide](framework/ARCHITECTURE.md)
- Review existing code in `stillme_core/`

## Related Documentation

- [Architecture Guide](framework/ARCHITECTURE.md)
- [API Reference](framework/API.md)

