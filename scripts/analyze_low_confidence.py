#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze questions with low confidence scores
"""

import json
import sys
import io
from pathlib import Path
from collections import Counter

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def analyze_low_confidence(result_file: Path, threshold: float = 0.80):
    """Analyze questions with confidence below threshold"""
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Filter successful results with low confidence
    low_confidence = [
        r for r in data 
        if r.get('status') == 'success' and r.get('confidence_score', 1.0) < threshold
    ]
    
    # Sort by confidence (lowest first)
    low_confidence.sort(key=lambda x: x.get('confidence_score', 1.0))
    
    print("="*80)
    print(f"PHAN TICH CAU HOI CO CONFIDENCE THAP (< {threshold})")
    print("="*80)
    print(f"\nTong so cau hoi co confidence < {threshold}: {len(low_confidence)}/{len(data)}")
    print(f"Ty le: {len(low_confidence)/len(data)*100:.1f}%\n")
    
    if not low_confidence:
        print("Khong co cau hoi nao co confidence thap!")
        return
    
    # Overall statistics
    confidences = [r.get('confidence_score', 0) for r in low_confidence]
    print(f"Confidence trung binh: {sum(confidences)/len(confidences):.3f}")
    print(f"Confidence thap nhat: {min(confidences):.3f}")
    print(f"Confidence cao nhat trong nhom: {max(confidences):.3f}\n")
    
    # By category
    categories = Counter(r.get('category', 'unknown') for r in low_confidence)
    print("PHAN BO THEO CATEGORY:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {cat}: {count} cau")
    
    # By language
    languages = Counter(r.get('language', 'unknown') for r in low_confidence)
    print(f"\nPHAN BO THEO NGON NGU:")
    for lang, count in sorted(languages.items()):
        print(f"  - {lang}: {count} cau")
    
    # By difficulty
    difficulties = Counter(r.get('difficulty', 'unknown') for r in low_confidence)
    print(f"\nPHAN BO THEO DO KHO:")
    for diff, count in sorted(difficulties.items()):
        print(f"  - {diff}: {count} cau")
    
    # Analyze validation info
    print(f"\n" + "="*80)
    print("CHI TIET 10 CAU HOI CO CONFIDENCE THAP NHAT:")
    print("="*80)
    
    for i, result in enumerate(low_confidence[:10], 1):
        print(f"\n[{i}] ID: {result.get('question_id', 'unknown')}")
        print(f"    Confidence: {result.get('confidence_score', 0):.3f}")
        print(f"    Category: {result.get('category', 'unknown')}")
        print(f"    Difficulty: {result.get('difficulty', 'unknown')}")
        print(f"    Language: {result.get('language', 'unknown')}")
        print(f"    Latency: {result.get('latency', 0):.2f}s")
        print(f"\n    CAU HOI:")
        question = result.get('question', '')
        print(f"    {question[:200]}{'...' if len(question) > 200 else ''}")
        
        # Validation info
        validation = result.get('validation_info', {})
        if validation:
            print(f"\n    VALIDATION INFO:")
            print(f"      - Passed: {validation.get('passed', False)}")
            print(f"      - Used fallback: {validation.get('used_fallback', False)}")
            print(f"      - Context docs count: {validation.get('context_docs_count', 0)}")
            reasons = validation.get('reasons', [])
            if reasons:
                print(f"      - Reasons: {', '.join(reasons)}")
        
        # Response preview
        response = result.get('response', '')
        if response:
            print(f"\n    RESPONSE (preview):")
            print(f"    {response[:300]}{'...' if len(response) > 300 else ''}")
        
        # Processing steps
        steps = result.get('processing_steps', [])
        if steps:
            print(f"\n    PROCESSING STEPS:")
            for step in steps[:5]:  # Show first 5 steps
                print(f"      - {step}")
        
        print("-" * 80)
    
    # Compare with high confidence
    high_confidence = [
        r for r in data 
        if r.get('status') == 'success' and r.get('confidence_score', 0) >= 0.90
    ]
    
    if high_confidence:
        print(f"\n" + "="*80)
        print("SO SANH VOI CAU HOI CO CONFIDENCE CAO (>= 0.90):")
        print("="*80)
        print(f"\nSo luong: {len(high_confidence)} cau")
        
        # Average context docs
        low_ctx = [r.get('validation_info', {}).get('context_docs_count', 0) for r in low_confidence]
        high_ctx = [r.get('validation_info', {}).get('context_docs_count', 0) for r in high_confidence]
        
        if low_ctx and high_ctx:
            print(f"\nContext documents:")
            print(f"  - Low confidence (avg): {sum(low_ctx)/len(low_ctx):.1f}")
            print(f"  - High confidence (avg): {sum(high_ctx)/len(high_ctx):.1f}")
        
        # Average latency
        low_lat = [r.get('latency', 0) for r in low_confidence]
        high_lat = [r.get('latency', 0) for r in high_confidence]
        
        if low_lat and high_lat:
            print(f"\nLatency:")
            print(f"  - Low confidence (avg): {sum(low_lat)/len(low_lat):.2f}s")
            print(f"  - High confidence (avg): {sum(high_lat)/len(high_lat):.2f}s")
        
        # Categories comparison
        low_cats = Counter(r.get('category', 'unknown') for r in low_confidence)
        high_cats = Counter(r.get('category', 'unknown') for r in high_confidence)
        
        print(f"\nCategory distribution:")
        all_cats = set(low_cats.keys()) | set(high_cats.keys())
        for cat in sorted(all_cats):
            low_pct = (low_cats.get(cat, 0) / len(low_confidence) * 100) if low_confidence else 0
            high_pct = (high_cats.get(cat, 0) / len(high_confidence) * 100) if high_confidence else 0
            print(f"  - {cat}: Low={low_pct:.1f}%, High={high_pct:.1f}%")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result_file = Path(sys.argv[1])
        threshold = float(sys.argv[2]) if len(sys.argv) > 2 else 0.80
    else:
        # Find latest result file
        results_dir = Path(__file__).parent.parent / "tests" / "results"
        result_files = sorted(results_dir.glob("comprehensive_test_*.json"), reverse=True)
        if not result_files:
            print("Khong tim thay file ket qua!")
            sys.exit(1)
        result_file = result_files[0]
        threshold = 0.80
    
    if not result_file.exists():
        print(f"File khong ton tai: {result_file}")
        sys.exit(1)
    
    analyze_low_confidence(result_file, threshold)

