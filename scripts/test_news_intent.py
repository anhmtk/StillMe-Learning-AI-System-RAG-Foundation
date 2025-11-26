# -*- coding: utf-8 -*-
"""Test news intent detection"""
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from backend.external_data.intent_detector import detect_external_data_intent

# Test queries
test_queries = [
    "bạn có biết thông tin mới nhất về AI ngày hôm nay ko?",
    "thông tin mới nhất về AI",
    "tin tức mới nhất",
    "latest news about AI",
    "tin tức về AI",
]

print("Testing news intent detection:")
print("=" * 60)

for query in test_queries:
    intent = detect_external_data_intent(query)
    if intent:
        print(f"[OK] '{query[:50]}...'")
        print(f"  Type: {intent.type}, Confidence: {intent.confidence}")
        print(f"  Params: {intent.params}")
    else:
        print(f"[FAIL] '{query[:50]}...' - No intent detected")
    print()

