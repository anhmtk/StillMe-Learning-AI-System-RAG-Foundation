#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick script to analyze test results"""

import json
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python analyze_test_results.py <test_result.json>")
    sys.exit(1)

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)

passed = [r['question_id'] for r in data['results'] if r.get('success')]
failed = [r['question_id'] for r in data['results'] if not r.get('success')]

print(f"Passed: {sorted(passed)}")
print(f"Failed: {sorted(failed)}")
