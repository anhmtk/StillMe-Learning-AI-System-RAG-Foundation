#!/usr/bin/env python3
"""Quick script to verify downloaded datasets"""

import json
from pathlib import Path

def verify_datasets():
    """Verify downloaded datasets"""
    benchmarks_dir = Path("data/benchmarks")
    
    # Check TruthfulQA
    truthfulqa_path = benchmarks_dir / "truthfulqa.json"
    if truthfulqa_path.exists():
        with open(truthfulqa_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            print(f"[OK] TruthfulQA: {len(data.get('questions', []))} questions")
    else:
        print("[FAIL] TruthfulQA: Not found")
    
    # Check HaluEval
    halu_eval_path = benchmarks_dir / "halu_eval.json"
    if halu_eval_path.exists():
        with open(halu_eval_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            questions = data.get('questions', [])
            status = "[OK]" if len(questions) > 10 else "[WARN]"
            print(f"{status} HaluEval: {len(questions)} questions")
            if len(questions) <= 10:
                print("   (Sample dataset - full dataset download failed)")
    else:
        print("[FAIL] HaluEval: Not found")

if __name__ == "__main__":
    verify_datasets()

