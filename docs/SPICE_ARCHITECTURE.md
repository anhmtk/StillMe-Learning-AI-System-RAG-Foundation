# SPICE Architecture for StillMe v0.5+

## Overview

SPICE (Self-Play In Corpus Environments) is a reinforcement learning framework that enables StillMe to continuously improve its reasoning capabilities through adversarial self-play.

## Architecture Blueprint

### Current Flow (v0.4)
```
RSS Feeds → Filter → Embed → ChromaDB → RAG Query → Response
```

### New SPICE-Enhanced Flow (v0.5+)
```
RSS Feeds → Filter → Embed → ChromaDB (Corpus)
    ↓
SPICE Self-Play Loop:
    ├─ Challenger: Generate questions from corpus
    ├─ Reasoner: Answer questions using RAG
    ├─ Self-Evaluation: Validate answers
    └─ Refinement: Improve failed challenges
    ↓
RAG Query → Enhanced Response (with self-improved reasoning)
```

## Core Components

### 1. Challenger Module
**Purpose**: Generate challenging reasoning questions from corpus

**Responsibilities**:
- Query ChromaDB for knowledge documents
- Generate diverse reasoning questions (ethical, mathematical, logical, factual)
- Create ethical reasoning challenges based on StillMe principles
- Score difficulty and relevance

**Key Methods**:
- `generate_challenges()`: General question generation from corpus
- `generate_ethical_challenges()`: Focus on StillMe ethical principles

**Integration Points**:
- Uses `RAGRetrieval` to access ChromaDB corpus
- Uses `EmbeddingService` for semantic operations
- Will integrate with AI model for question generation

### 2. Reasoner Module
**Purpose**: Attempt to answer Challenger's questions and self-evaluate

**Responsibilities**:
- Receive `ChallengeQuestion` from Challenger
- Use RAG to retrieve relevant context
- Generate answer using AI model
- Self-evaluate answer accuracy against source content
- Detect hallucinations and reasoning gaps

**Key Methods**:
- `answer_challenge()`: Generate answer for a challenge
- `self_evaluate()`: Evaluate answer accuracy and completeness

**Integration Points**:
- Uses `RAGRetrieval` for context retrieval
- Uses AI model for answer generation
- Uses validation chain for quality checks

### 3. SPICE Engine
**Purpose**: Orchestrate self-play learning cycle

**Responsibilities**:
- Coordinate Challenger and Reasoner
- Run self-play cycles
- Track success/failure metrics
- Trigger refinement for failed challenges

**Key Methods**:
- `run_self_play_cycle()`: Execute one complete self-play cycle
- `_handle_failure()`: Process failed challenges

## Integration with Existing Systems

### 1. Learning Scheduler Integration
**Location**: `backend/services/learning_scheduler.py`

**Enhancement**:
```python
async def run_learning_cycle(self):
    # Existing: Fetch RSS and add to RAG
    entries = self.rss_fetcher.fetch_feeds(...)
    # Add to RAG...
    
    # NEW: Run SPICE self-play cycle
    if self.spice_engine:
        spice_result = await self.spice_engine.run_self_play_cycle(
            corpus_query="recent knowledge",
            num_challenges=5,
            focus_ethical=False
        )
```

### 2. Validation Integration
**Location**: `backend/validators/`

**Enhancement**:
- Use Challenger to generate ethical reasoning questions
- Integrate ethical challenges into validation metrics
- Track validation performance on SPICE-generated questions

**Priority Implementation**:
```python
# Initial focus: Ethical reasoning challenges
ethical_challenges = await challenger.generate_ethical_challenges(
    num_questions=3
)
# Use these for validation metrics
```

### 3. RAG Integration
**Location**: `backend/vector_db/rag_retrieval.py`

**No changes required** - SPICE uses existing RAG infrastructure:
- `retrieve_context()`: Reasoner uses this to get context
- `add_learning_content()`: Used for refinement (re-embedding)

## Data Flow

### Self-Play Cycle Flow

```
1. Challenger.generate_challenges()
   ├─ Query ChromaDB corpus
   ├─ Generate questions using AI
   └─ Return List[ChallengeQuestion]

2. For each ChallengeQuestion:
   ├─ Reasoner.answer_challenge()
   │  ├─ Retrieve context using RAG
   │  ├─ Generate answer using AI
   │  └─ Self-evaluate answer
   └─ ReasonerResponse
      ├─ If passed: Success count++
      └─ If failed: Trigger refinement

3. SPICE Engine aggregates results
   └─ Return cycle metrics
```

## API Endpoints (Planned)

### New Endpoints

```python
# SPICE Control
POST /api/spice/run-cycle
GET /api/spice/status
GET /api/spice/metrics

# Challenger
POST /api/spice/challenger/generate
POST /api/spice/challenger/ethical

# Reasoner
POST /api/spice/reasoner/answer
POST /api/spice/reasoner/evaluate
```

## Implementation Phases

### Phase 1: Framework (Current)
- ✅ Core classes: `Challenger`, `Reasoner`, `SPICEEngine`
- ✅ Data structures: `ChallengeQuestion`, `ReasonerResponse`
- ✅ Integration points defined
- ⏳ API endpoints (skeleton)

### Phase 2: Challenger Implementation
- AI-powered question generation
- Difficulty scoring
- Ethical reasoning challenge generation
- Corpus query optimization

### Phase 3: Reasoner Implementation
- RAG-based answer generation
- Self-evaluation logic
- Hallucination detection
- Factual accuracy checking

### Phase 4: Self-Play Loop
- Cycle orchestration
- Failure handling and refinement
- Curriculum difficulty adjustment
- Metrics tracking

### Phase 5: Integration
- Learning scheduler integration
- Validation enhancement
- Dashboard metrics
- Performance optimization

## Key Design Decisions

### 1. Corpus-Based Learning
- SPICE learns from real corpus (ChromaDB), not synthetic data
- Maintains context, realism, and semantic depth
- Enables continuous improvement without retraining

### 2. Ethical Reasoning Priority
- Initial focus on ethical reasoning challenges
- Aligns with StillMe's core principles (transparency, open governance)
- Enhances validation metrics

### 3. Self-Evaluation
- Reasoner evaluates its own answers
- Detects hallucinations and reasoning gaps
- Enables autonomous quality control

### 4. Refinement Mechanism
- Failed challenges trigger refinement
- Re-embedding with enhanced metadata
- Validation queue for manual review

## Expected Benefits

### Reasoning Improvement
- +8.9% mathematical reasoning (MATH benchmark)
- +9.8% general reasoning (reasoning benchmarks)
- Based on SPICE research paper results

### Quality Enhancement
- Better hallucination detection
- Improved factual accuracy
- Enhanced ethical reasoning

### Continuous Learning
- No retraining required
- Self-improving system
- Adapts to new corpus content

## Risks and Mitigations

### Risk 1: Bias Amplification
- **Risk**: Self-generated challenges may reproduce biases
- **Mitigation**: 
  - Focus on ethical reasoning challenges
  - Human oversight for validation
  - Bias detection in self-evaluation

### Risk 2: Computational Cost
- **Risk**: Self-play cycles may be expensive
- **Mitigation**:
  - Limit cycle frequency (e.g., once per day)
  - Optimize question generation
  - Cache embeddings and context

### Risk 3: Quality Control
- **Risk**: Generated questions may be low quality
- **Mitigation**:
  - Difficulty scoring
  - Relevance filtering
  - Validation checkpoints

## Next Steps

1. **Complete Phase 1**: Finish API endpoint skeletons
2. **Start Phase 2**: Implement Challenger question generation
3. **Test Integration**: Verify with existing RAG system
4. **Iterate**: Refine based on initial results

## References

- SPICE Paper: https://arxiv.org/abs/2510.24684
- Meta AI Research: Self-Play In Corpus Environments
- StillMe Core Principles: Transparency, Open Governance, Counter-movement to Black Box AI

