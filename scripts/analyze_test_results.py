#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analyze comprehensive test results
"""

import json
import sys
from pathlib import Path
from collections import Counter

def analyze_results(result_file: Path):
    """Analyze test results and print statistics"""
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("="*60)
    print("PHAN TICH CHI TIET KET QUA TEST")
    print("="*60)
    print(f"\nFile: {result_file.name}\n")
    
    # Overall statistics
    print("THONG KE TONG QUAN:")
    print(f"  - Tong so cau hoi: {len(data)}")
    
    success = [r for r in data if r.get('status') == 'success']
    errors = [r for r in data if r.get('status') == 'error']
    timeouts = [r for r in data if r.get('status') == 'timeout']
    
    print(f"  - Thanh cong: {len(success)} ({len(success)/len(data)*100:.1f}%)")
    print(f"  - Loi: {len(errors)}")
    print(f"  - Timeout: {len(timeouts)}")
    
    if success:
        # Latency statistics
        latencies = [r.get('latency', 0) for r in success if r.get('latency')]
        if latencies:
            print(f"\nTHOI GIAN XU LY:")
            print(f"  - Trung binh: {sum(latencies)/len(latencies):.2f}s")
            print(f"  - Nhanh nhat: {min(latencies):.2f}s")
            print(f"  - Cham nhat: {max(latencies):.2f}s")
        
        # Confidence statistics
        confidences = [r.get('confidence_score', 0) for r in success if r.get('confidence_score')]
        if confidences:
            print(f"\nCONFIDENCE SCORE:")
            print(f"  - Trung binh: {sum(confidences)/len(confidences):.2f}")
            print(f"  - Cao nhat: {max(confidences):.2f}")
            print(f"  - Thap nhat: {min(confidences):.2f}")
        
        # By category
        categories = Counter(r.get('category', 'unknown') for r in success)
        print(f"\nTHEO CATEGORY:")
        for cat, count in sorted(categories.items()):
            cat_results = [r for r in success if r.get('category') == cat]
            avg_conf = sum(r.get('confidence_score', 0) for r in cat_results) / len(cat_results) if cat_results else 0
            print(f"  - {cat}: {count} cau (confidence: {avg_conf:.2f})")
        
        # By language
        languages = Counter(r.get('language', 'unknown') for r in success)
        print(f"\nTHEO NGON NGU:")
        for lang, count in sorted(languages.items()):
            print(f"  - {lang}: {count} cau")
    
    if errors:
        print(f"\nLOI CHI TIET:")
        for err in errors[:5]:  # Show first 5 errors
            print(f"  - {err.get('question_id', 'unknown')}: {err.get('error', 'unknown error')}")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result_file = Path(sys.argv[1])
    else:
        # Find latest result file
        results_dir = Path(__file__).parent.parent / "tests" / "results"
        result_files = sorted(results_dir.glob("comprehensive_test_*.json"), reverse=True)
        if not result_files:
            print("Khong tim thay file ket qua!")
            sys.exit(1)
        result_file = result_files[0]
    
    if not result_file.exists():
        print(f"File khong ton tai: {result_file}")
        sys.exit(1)
    
    analyze_results(result_file)

