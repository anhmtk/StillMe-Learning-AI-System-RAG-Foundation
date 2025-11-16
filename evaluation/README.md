# StillMe Evaluation Framework

Comprehensive evaluation framework for benchmarking StillMe against standard datasets and comparing with baseline systems.

## Overview

This evaluation framework provides:

1. **Benchmark Integration**: TruthfulQA, HaluEval
2. **Quantitative Metrics**: Accuracy, Hallucination Rate, Transparency Score
3. **System Comparison**: StillMe vs Vanilla RAG vs ChatGPT vs Claude
4. **User Study Framework**: Transparency perception studies

## Installation

```bash
# Install dependencies
pip install requests openai anthropic  # For comparison with commercial systems
```

## Usage

### Run Full Evaluation

```bash
python -m evaluation.run_evaluation \
    --api-url http://localhost:8000 \
    --output-dir data/evaluation/results \
    --benchmarks truthfulqa halu_eval comparison
```

### Run Individual Benchmarks

```python
from evaluation.truthfulqa import TruthfulQAEvaluator

evaluator = TruthfulQAEvaluator(api_base_url="http://localhost:8000")
results = evaluator.evaluate()
print(f"Accuracy: {results.accuracy:.2%}")
```

### System Comparison

```python
from evaluation.comparison import SystemComparator

comparator = SystemComparator(stillme_api_url="http://localhost:8000")
questions = [
    {"question": "What is the capital of France?", "correct_answer": "Paris"}
]
results = comparator.compare_systems(questions)
report = comparator.generate_comparison_report(results)
```

### Transparency Study

```python
from evaluation.transparency_study import TransparencyStudy, TransparencyRating

study = TransparencyStudy()

# Add rating
rating = TransparencyRating(
    question="What is the capital of France?",
    system_response="Paris is the capital of France [1]",
    system_name="stillme",
    user_id="user_001",
    transparency_score=5,
    citation_helpful=True,
    uncertainty_helpful=False,
    trust_score=5
)
study.add_rating(rating)

# Get results
results = study.get_results()
print(f"Average Transparency: {results.avg_transparency_score:.2f}/5.0")
```

## Metrics

### Accuracy
Percentage of correct answers (when ground truth available).

### Hallucination Rate
Percentage of incorrect or ungrounded responses. Calculated via:
- Ground truth method: Direct comparison with correct answers
- Heuristic method: No citation + high confidence + validation failed

### Transparency Score
Weighted combination:
- Citation Rate (40%): Percentage of responses with citations
- Uncertainty Rate (30%): Percentage expressing uncertainty when appropriate
- Validation Pass Rate (30%): Percentage passing validation chain

### Response Quality Score
Combination of:
- Accuracy (50%)
- Transparency Score (30%)
- Confidence Appropriateness (20%): How well confidence matches accuracy

## Benchmarks

### TruthfulQA
Tests truthfulness and accuracy. Dataset should be placed at:
`data/benchmarks/truthfulqa.json`

Format:
```json
{
  "questions": [
    {
      "question": "What is the capital of France?",
      "correct_answer": "Paris",
      "incorrect_answers": ["London", "Berlin"]
    }
  ]
}
```

### HaluEval
Tests hallucination detection. Dataset should be placed at:
`data/benchmarks/halu_eval.json`

Format:
```json
{
  "questions": [
    {
      "question": "What is the population of a fictional city?",
      "answer": "The population is 10 million",
      "is_hallucination": true,
      "context": "No context available"
    }
  ]
}
```

## Results

Evaluation results are saved to:
`data/evaluation/results/`

Files:
- `truthfulqa_results.json`: TruthfulQA benchmark results
- `halu_eval_results.json`: HaluEval benchmark results
- `comparison_results.json`: System comparison results
- `comparison_report.md`: Human-readable comparison report
- `transparency_study_report.md`: User study report
- `evaluation_summary.json`: Aggregated summary

## Paper Integration

Results from this evaluation framework are used in:
`docs/PAPER_DRAFT.md`

The paper focuses on:
- **Practical Framework** positioning (not novel algorithm)
- **System Transparency** emphasis (not model interpretability)
- **Quantitative Results** from benchmarks
- **User Study** on transparency perception

## Next Steps

1. **Download Benchmarks**: Get TruthfulQA and HaluEval datasets
2. **Run Evaluation**: Execute full evaluation suite
3. **Collect User Study Data**: Conduct transparency perception study
4. **Fill Paper Results**: Update `docs/PAPER_DRAFT.md` with actual results
5. **Refine Positioning**: Ensure paper emphasizes "Practical Framework"

