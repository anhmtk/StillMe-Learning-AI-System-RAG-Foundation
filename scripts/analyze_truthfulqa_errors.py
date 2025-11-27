#!/usr/bin/env python3
"""
Analyze TruthfulQA errors to identify patterns and improvement opportunities
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

# Fix encoding for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

def analyze_errors():
    """Analyze TruthfulQA results to find error patterns"""
    
    results_path = Path("data/evaluation/results/truthfulqa_results.json")
    
    if not results_path.exists():
        print(f"❌ Results file not found: {results_path}")
        return
    
    print("=" * 80)
    print("TRUTHFULQA ERROR ANALYSIS")
    print("=" * 80)
    print()
    
    with open(results_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data.get("detailed_results", [])
    total = len(results)
    
    # Categorize results
    correct = [r for r in results if r.get("is_correct") is True]
    incorrect = [r for r in results if r.get("is_correct") is False]
    uncertain = [r for r in results if r.get("is_correct") is None]
    
    print(f"📊 SUMMARY:")
    print(f"  Total Questions: {total}")
    print(f"  Correct: {len(correct)} ({len(correct)/total*100:.1f}%)")
    print(f"  Incorrect: {len(incorrect)} ({len(incorrect)/total*100:.1f}%)")
    print(f"  Uncertain: {len(uncertain)} ({len(uncertain)/total*100:.1f}%)")
    print()
    
    # Analyze incorrect answers
    print("=" * 80)
    print("❌ INCORRECT ANSWERS ANALYSIS")
    print("=" * 80)
    print()
    
    if incorrect:
        print(f"Found {len(incorrect)} incorrect answers. Analyzing patterns...")
        print()
        
        # Pattern 1: Check for uncertainty expression
        incorrect_with_uncertainty = [r for r in incorrect if r.get("has_uncertainty", False)]
        incorrect_without_uncertainty = [r for r in incorrect if not r.get("has_uncertainty", False)]
        
        print(f"  Incorrect with uncertainty: {len(incorrect_with_uncertainty)} ({len(incorrect_with_uncertainty)/len(incorrect)*100:.1f}%)")
        print(f"  Incorrect without uncertainty: {len(incorrect_without_uncertainty)} ({len(incorrect_without_uncertainty)/len(incorrect)*100:.1f}%)")
        print()
        
        # Pattern 2: Check for citations
        incorrect_with_citation = [r for r in incorrect if r.get("has_citation", False)]
        incorrect_without_citation = [r for r in incorrect if not r.get("has_citation", False)]
        
        print(f"  Incorrect with citation: {len(incorrect_with_citation)} ({len(incorrect_with_citation)/len(incorrect)*100:.1f}%)")
        print(f"  Incorrect without citation: {len(incorrect_without_citation)} ({len(incorrect_without_citation)/len(incorrect)*100:.1f}%)")
        print()
        
        # Pattern 3: Check response length
        response_lengths = [len(r.get("predicted_answer", "")) for r in incorrect]
        avg_length = sum(response_lengths) / len(response_lengths) if response_lengths else 0
        
        print(f"  Average response length: {avg_length:.0f} characters")
        print()
        
        # Show sample incorrect answers
        print("📝 SAMPLE INCORRECT ANSWERS (first 5):")
        print()
        for i, r in enumerate(incorrect[:5], 1):
            print(f"  {i}. Question: {r.get('question', '')[:60]}...")
            print(f"     Ground Truth: {r.get('ground_truth', '')[:80]}")
            predicted = r.get("predicted_answer", "")[:200]
            print(f"     Predicted: {predicted}...")
            print(f"     Has Uncertainty: {r.get('has_uncertainty', False)}")
            print(f"     Has Citation: {r.get('has_citation', False)}")
            print()
    
    # Analyze uncertain answers
    print("=" * 80)
    print("❓ UNCERTAIN ANSWERS ANALYSIS")
    print("=" * 80)
    print()
    
    if uncertain:
        print(f"Found {len(uncertain)} uncertain answers. This is a major issue!")
        print()
        
        # Pattern 1: Check for uncertainty expression
        uncertain_with_uncertainty = [r for r in uncertain if r.get("has_uncertainty", False)]
        uncertain_without_uncertainty = [r for r in uncertain if not r.get("has_uncertainty", False)]
        
        print(f"  Uncertain with uncertainty flag: {len(uncertain_with_uncertainty)} ({len(uncertain_with_uncertainty)/len(uncertain)*100:.1f}%)")
        print(f"  Uncertain without uncertainty flag: {len(uncertain_without_uncertainty)} ({len(uncertain_without_uncertainty)/len(uncertain)*100:.1f}%)")
        print()
        
        # Show sample uncertain answers
        print("📝 SAMPLE UNCERTAIN ANSWERS (first 5):")
        print()
        for i, r in enumerate(uncertain[:5], 1):
            print(f"  {i}. Question: {r.get('question', '')[:60]}...")
            print(f"     Ground Truth: {r.get('ground_truth', '')[:80]}")
            predicted = r.get("predicted_answer", "")[:200]
            print(f"     Predicted: {predicted}...")
            print(f"     Has Uncertainty: {r.get('has_uncertainty', False)}")
            print(f"     Has Citation: {r.get('has_citation', False)}")
            print()
    
    # Analyze correct answers for patterns
    print("=" * 80)
    print("✅ CORRECT ANSWERS ANALYSIS (for comparison)")
    print("=" * 80)
    print()
    
    if correct:
        correct_with_uncertainty = [r for r in correct if r.get("has_uncertainty", False)]
        correct_without_uncertainty = [r for r in correct if not r.get("has_uncertainty", False)]
        
        print(f"  Correct with uncertainty: {len(correct_with_uncertainty)} ({len(correct_with_uncertainty)/len(correct)*100:.1f}%)")
        print(f"  Correct without uncertainty: {len(correct_without_uncertainty)} ({len(correct_without_uncertainty)/len(correct)*100:.1f}%)")
        print()
        
        # Show sample correct answers
        print("📝 SAMPLE CORRECT ANSWERS (first 3):")
        print()
        for i, r in enumerate(correct[:3], 1):
            print(f"  {i}. Question: {r.get('question', '')[:60]}...")
            print(f"     Ground Truth: {r.get('ground_truth', '')[:80]}")
            predicted = r.get("predicted_answer", "")[:200]
            print(f"     Predicted: {predicted}...")
            print(f"     Has Uncertainty: {r.get('has_uncertainty', False)}")
            print(f"     Has Citation: {r.get('has_citation', False)}")
            print()
    
    # Recommendations
    print("=" * 80)
    print("💡 RECOMMENDATIONS FOR IMPROVEMENT")
    print("=" * 80)
    print()
    
    recommendations = []
    
    if len(uncertain) > len(incorrect):
        recommendations.append("⚠️  MAJOR ISSUE: Too many uncertain answers. The matching logic may be too strict or answers are too verbose.")
        recommendations.append("   → Improve answer extraction to get concise, direct answers")
        recommendations.append("   → Improve matching logic to handle verbose responses better")
    
    if len(incorrect_without_uncertainty) > len(incorrect_with_uncertainty):
        recommendations.append("⚠️  Many incorrect answers don't express uncertainty. System is overconfident.")
        recommendations.append("   → Improve uncertainty detection for ambiguous questions")
        recommendations.append("   → Add validation to catch incorrect answers before returning")
    
    if avg_length > 500:
        recommendations.append("⚠️  Responses are too long. May contain irrelevant information.")
        recommendations.append("   → Add answer summarization/extraction step")
        recommendations.append("   → Focus on direct answers rather than explanations")
    
    if not recommendations:
        recommendations.append("✅ No major patterns identified. Consider:")
        recommendations.append("   → Improving RAG retrieval for better context")
        recommendations.append("   → Fine-tuning LLM prompts for more accurate answers")
        recommendations.append("   → Using better answer matching (semantic similarity)")
    
    for rec in recommendations:
        print(f"  {rec}")
    
    print()

if __name__ == "__main__":
    analyze_errors()

