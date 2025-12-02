# Time Estimation Feature - Implementation Plan

## Overview

Implement AI Self-Aware Time Estimation for StillMe - allowing StillMe to estimate task completion time based on its own historical performance data, not human patterns.

## Goals

1. **Accurate Estimates**: StillMe estimates based on its own capabilities
2. **Calibration**: Estimates include confidence intervals (ranges, not points)
3. **Conservative Bias**: Slightly overestimate (better than underestimate)
4. **Transparency**: Communicate uncertainty clearly
5. **Learning**: Improve estimates over time from actual data

## Implementation Phases

### Phase 1: Data Collection (Foundation) - 30 minutes

**Goal**: Track task execution time and metadata

**Tasks**:
1. Extend `UnifiedMetricsCollector` with task tracking
2. Add `SYSTEM` category for task metrics
3. Create `TaskRecord` dataclass
4. Track: task_type, complexity, size, estimated_time, actual_time

**Files to Create/Modify**:
- `stillme_core/monitoring/metrics.py` - Add task tracking methods
- `stillme_core/monitoring/task_tracker.py` - New file for task tracking

**Code Structure**:
```python
@dataclass
class TaskRecord:
    task_id: str
    task_type: str  # "coding", "review", "migration", "analysis"
    complexity: str  # "simple", "moderate", "complex", "very_complex"
    size: int  # lines_of_code, files_changed, etc.
    estimated_time_minutes: Optional[float]
    actual_time_minutes: float
    accuracy_ratio: float  # actual / estimated
    confidence: float  # 0.0-1.0
    metadata: Dict[str, Any]
```

### Phase 2: Estimation Engine (Core) - 1 hour

**Goal**: Create estimation engine that learns from historical data

**Tasks**:
1. Create `TimeEstimationEngine` class
2. Implement similarity matching for tasks
3. Calculate base estimates from historical data
4. Adjust for complexity and size
5. Add confidence intervals

**Files to Create**:
- `stillme_core/monitoring/time_estimation.py` - New file

**Key Methods**:
```python
class TimeEstimationEngine:
    def estimate(
        self,
        task_description: str,
        task_type: str,
        complexity: str,
        size: int
    ) -> TimeEstimate:
        # 1. Find similar historical tasks
        # 2. Calculate base estimate
        # 3. Adjust for complexity
        # 4. Add confidence interval
        pass
    
    def _find_similar_tasks(self, ...) -> List[TaskRecord]:
        pass
    
    def _calculate_base_estimate(self, ...) -> float:
        pass
    
    def _adjust_for_complexity(self, ...) -> float:
        pass
```

### Phase 3: Integration (Usage) - 30 minutes

**Goal**: Integrate estimation into StillMe workflow

**Tasks**:
1. Add estimation to task start
2. Record actual time at task end
3. Calculate accuracy and learn
4. Expose via API endpoint (optional)

**Integration Points**:
- Task start: `estimate_task_time()`
- Task end: `record_actual_time()`
- User query: "How long will this take?" → Use estimation engine

### Phase 4: Learning Loop (Improvement) - 30 minutes

**Goal**: Improve estimates over time

**Tasks**:
1. Analyze estimation accuracy patterns
2. Adjust estimation parameters
3. Detect systematic biases
4. Update complexity models

**Self-Improvement Integration**:
- Connect to `SelfImprovementAnalyzer`
- Analyze estimation patterns
- Suggest improvements

## Detailed Implementation

### Step 1: Extend Metrics System

**File**: `stillme_core/monitoring/metrics.py`

**Add**:
```python
def record_task_start(
    self,
    task_id: str,
    task_type: str,
    complexity: str,
    size: int,
    estimated_time_minutes: float,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Record task start with estimate"""
    self.record(
        MetricCategory.SYSTEM,
        "task_start",
        {
            "task_id": task_id,
            "task_type": task_type,
            "complexity": complexity,
            "size": size,
            "estimated_time_minutes": estimated_time_minutes
        },
        metadata=metadata
    )

def record_task_end(
    self,
    task_id: str,
    actual_time_minutes: float,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Record task end with actual time"""
    # Get start record
    start_record = self._get_task_start(task_id)
    if start_record:
        estimated = start_record.value.get("estimated_time_minutes", 0)
        accuracy = actual_time_minutes / estimated if estimated > 0 else 0
        
        self.record(
            MetricCategory.SYSTEM,
            "task_end",
            {
                "task_id": task_id,
                "actual_time_minutes": actual_time_minutes,
                "estimated_time_minutes": estimated,
                "accuracy_ratio": accuracy
            },
            metadata=metadata
        )
```

### Step 2: Create Estimation Engine

**File**: `stillme_core/monitoring/time_estimation.py` (NEW)

**Structure**:
```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from stillme_core.monitoring import get_metrics_collector, MetricCategory

@dataclass
class TimeEstimate:
    estimated_minutes: float
    confidence: float  # 0.0-1.0
    range_min: float
    range_max: float
    based_on_n_tasks: int

class TimeEstimationEngine:
    def __init__(self):
        self.metrics = get_metrics_collector()
    
    def estimate(
        self,
        task_description: str,
        task_type: str,
        complexity: str,
        size: int
    ) -> TimeEstimate:
        # Implementation
        pass
    
    def _find_similar_tasks(
        self,
        task_type: str,
        complexity: str,
        size: int
    ) -> List[Dict[str, Any]]:
        # Find similar tasks from metrics
        pass
    
    def _calculate_base_estimate(
        self,
        similar_tasks: List[Dict[str, Any]]
    ) -> float:
        # Calculate median/mean from similar tasks
        pass
    
    def _adjust_for_complexity(
        self,
        base_estimate: float,
        complexity: str
    ) -> float:
        # Adjust based on complexity
        complexity_multipliers = {
            "simple": 0.7,
            "moderate": 1.0,
            "complex": 1.5,
            "very_complex": 2.5
        }
        return base_estimate * complexity_multipliers.get(complexity, 1.0)
    
    def _calculate_confidence(
        self,
        similar_tasks: List[Dict[str, Any]]
    ) -> float:
        # More similar tasks = higher confidence
        n = len(similar_tasks)
        if n >= 10:
            return 0.9
        elif n >= 5:
            return 0.7
        elif n >= 2:
            return 0.5
        else:
            return 0.3
```

### Step 3: Integration Points

**Where to Add**:

1. **Task Start** (when StillMe starts a task):
```python
from stillme_core.monitoring import get_metrics_collector, TimeEstimationEngine

metrics = get_metrics_collector()
estimator = TimeEstimationEngine()

# When starting a task
task_id = generate_task_id()
estimate = estimator.estimate(
    task_description="Migrate validation system",
    task_type="migration",
    complexity="moderate",
    size=500  # lines of code
)

metrics.record_task_start(
    task_id=task_id,
    task_type="migration",
    complexity="moderate",
    size=500,
    estimated_time_minutes=estimate.estimated_minutes
)

# Communicate to user
print(f"I estimate this will take {estimate.range_min:.0f}-{estimate.range_max:.0f} minutes (confidence: {estimate.confidence:.0%})")
```

2. **Task End** (when StillMe completes a task):
```python
import time

start_time = time.time()
# ... do work ...
actual_time_minutes = (time.time() - start_time) / 60

metrics.record_task_end(
    task_id=task_id,
    actual_time_minutes=actual_time_minutes
)
```

3. **User Query** (when user asks "How long?"):
```python
# In chat endpoint
if "how long" in question.lower() or "estimate" in question.lower():
    estimate = estimator.estimate(...)
    response = f"Based on my historical performance, I estimate this will take {estimate.range_min:.0f}-{estimate.range_max:.0f} minutes (confidence: {estimate.confidence:.0%})."
```

## Testing Strategy

### Unit Tests
- Test estimation engine with mock data
- Test similarity matching
- Test complexity adjustment
- Test confidence calculation

### Integration Tests
- Test full workflow: estimate → execute → record
- Test learning loop: improve estimates over time
- Test edge cases: no historical data, novel tasks

### Validation
- Ensure estimates are reasonable (not too conservative, not too aggressive)
- Ensure confidence intervals are calibrated (actual time in range)
- Ensure learning improves estimates over time

## Success Criteria

1. ✅ Estimates are more accurate than human-pattern-based estimates
2. ✅ Confidence intervals are calibrated (actual time in range 70%+ of time)
3. ✅ Estimates improve over time (learning loop works)
4. ✅ User perceives StillMe as "self-aware" and "reliable"

## Timeline

- **Phase 1**: 30 minutes (Data Collection)
- **Phase 2**: 1 hour (Estimation Engine)
- **Phase 3**: 30 minutes (Integration)
- **Phase 4**: 30 minutes (Learning Loop)

**Total**: ~2.5 hours for basic implementation

## Future Enhancements

1. **Dependency Detection**: Detect external dependencies that affect time
2. **Context Awareness**: Adjust estimates based on current context
3. **Multi-step Tasks**: Break down large tasks, estimate each step
4. **Real-time Updates**: Re-estimate if context changes during task
5. **Visualization**: Dashboard showing estimation accuracy over time

