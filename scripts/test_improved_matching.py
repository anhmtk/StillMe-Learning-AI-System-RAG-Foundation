#!/usr/bin/env python3
"""
Test improved TruthfulQA matching logic on existing results
"""

import json
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Import the improved evaluator
sys.path.insert(0, str(Path(__file__).parent.parent))
from evaluation.truthfulqa import TruthfulQAEvaluator

def test_improved_matching():
    """Test improved matching on existing results"""
    
    results_path = Path("data/evaluation/results/truthfulqa_results.json")
    
    if not results_path.exists():
        print(f"❌ Results file not found: {results_path}")
        return
    
    print("=" * 80)
    print("TESTING IMPROVED MATCHING LOGIC")
    print("=" * 80)
    print()
    
    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data.get("detailed_results", [])
    
    # Create evaluator instance to access matching method
    evaluator = TruthfulQAEvaluator()
    
    # Load dataset to get incorrect_answers
    dataset_path = Path("data/benchmarks/truthfulqa.json")
    if not dataset_path.exists():
        print(f"❌ Dataset file not found: {dataset_path}")
        return
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    questions_dict = {q.get("question"): q for q in dataset.get("questions", [])}
    
    # Re-evaluate first 50 questions with improved matching
    print(f"Re-evaluating first 50 questions with improved matching...")
    print()
    
    old_correct = 0
    old_incorrect = 0
    old_uncertain = 0
    
    new_correct = 0
    new_incorrect = 0
    new_uncertain = 0
    
    improved = 0
    worsened = 0
    
    for i, result in enumerate(results[:50], 1):
        question = result.get("question", "")
        predicted = result.get("predicted_answer", "")
        ground_truth = result.get("ground_truth", "")
        old_is_correct = result.get("is_correct")
        
        # Get incorrect answers from dataset
        qa_pair = questions_dict.get(question, {})
        incorrect_answers = qa_pair.get("incorrect_answers", [])
        
        # Re-check with improved matching
        new_is_correct = evaluator._check_answer_correctness(
            predicted,
            ground_truth,
            incorrect_answers
        )
        
        # Count old results
        if old_is_correct is True:
            old_correct += 1
        elif old_is_correct is False:
            old_incorrect += 1
        else:
            old_uncertain += 1
        
        # Count new results
        if new_is_correct is True:
            new_correct += 1
        elif new_is_correct is False:
            new_incorrect += 1
        else:
            new_uncertain += 1
        
        # Track improvements
        if old_is_correct is None and new_is_correct is not None:
            improved += 1
        elif old_is_correct is not None and new_is_correct is None:
            worsened += 1
        elif old_is_correct is False and new_is_correct is True:
            improved += 1
        elif old_is_correct is True and new_is_correct is False:
            worsened += 1
    
    print("=" * 80)
    print("RESULTS COMPARISON (First 50 questions)")
    print("=" * 80)
    print()
    print("OLD MATCHING:")
    print(f"  Correct: {old_correct} ({old_correct/50*100:.1f}%)")
    print(f"  Incorrect: {old_incorrect} ({old_incorrect/50*100:.1f}%)")
    print(f"  Uncertain: {old_uncertain} ({old_uncertain/50*100:.1f}%)")
    print()
    print("NEW MATCHING:")
    print(f"  Correct: {new_correct} ({new_correct/50*100:.1f}%)")
    print(f"  Incorrect: {new_incorrect} ({new_incorrect/50*100:.1f}%)")
    print(f"  Uncertain: {new_uncertain} ({new_uncertain/50*100:.1f}%)")
    print()
    print("IMPROVEMENT:")
    print(f"  Questions improved: {improved}")
    print(f"  Questions worsened: {worsened}")
    print(f"  Net improvement: {improved - worsened}")
    print()
    
    if new_uncertain < old_uncertain:
        print(f"✅ SUCCESS: Reduced uncertain answers by {old_uncertain - new_uncertain} ({((old_uncertain - new_uncertain)/old_uncertain*100):.1f}%)")
    else:
        print(f"⚠️  Uncertain answers increased by {new_uncertain - old_uncertain}")
    
    if new_correct > old_correct:
        print(f"✅ SUCCESS: Increased correct answers by {new_correct - old_correct} ({((new_correct - old_correct)/old_correct*100):.1f}%)")
    else:
        print(f"⚠️  Correct answers decreased by {old_correct - new_correct}")

if __name__ == "__main__":
    test_improved_matching()

