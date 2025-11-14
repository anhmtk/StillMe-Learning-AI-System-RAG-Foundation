#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Detailed analysis of confidence scores and citation patterns
"""

import json
import sys
import io
import re
from pathlib import Path
from collections import Counter, defaultdict

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

CITE_RE = re.compile(r"\[(\d+)\]")

def analyze_citation_patterns(result_file: Path):
    """Analyze citation patterns in responses"""
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Categorize results
    low_conf = []  # < 0.8
    high_conf = []  # >= 0.9
    medium_conf = []  # 0.8-0.89
    
    for r in data:
        if r.get('status') != 'success':
            continue
        conf = r.get('confidence_score', 0)
        if conf < 0.8:
            low_conf.append(r)
        elif conf >= 0.9:
            high_conf.append(r)
        else:
            medium_conf.append(r)
    
    print("="*80)
    print("PHAN TICH CHI TIET CONFIDENCE SCORE VA CITATION PATTERNS")
    print("="*80)
    
    # Overall statistics
    print(f"\n📊 TONG QUAN:")
    print(f"  - Low confidence (<0.8): {len(low_conf)} cau ({len(low_conf)/len(data)*100:.1f}%)")
    print(f"  - Medium confidence (0.8-0.89): {len(medium_conf)} cau ({len(medium_conf)/len(data)*100:.1f}%)")
    print(f"  - High confidence (>=0.9): {len(high_conf)} cau ({len(high_conf)/len(data)*100:.1f}%)")
    
    # Citation analysis
    def count_citations(response: str) -> int:
        return len(CITE_RE.findall(response))
    
    def has_citations(response: str) -> bool:
        return bool(CITE_RE.search(response))
    
    # Low confidence citation analysis
    print(f"\n🔍 PHAN TICH LOW CONFIDENCE ({len(low_conf)} cau):")
    low_with_ctx = [r for r in low_conf if r.get('validation_info', {}).get('context_docs_count', 0) > 0]
    low_without_ctx = [r for r in low_conf if r.get('validation_info', {}).get('context_docs_count', 0) == 0]
    
    print(f"  - Co context documents: {len(low_with_ctx)} cau")
    print(f"  - Khong co context: {len(low_without_ctx)} cau")
    
    if low_with_ctx:
        low_citation_count = sum(1 for r in low_with_ctx if has_citations(r.get('response', '')))
        print(f"  - Co citation trong response: {low_citation_count}/{len(low_with_ctx)} ({low_citation_count/len(low_with_ctx)*100:.1f}%)")
        print(f"  - Khong co citation: {len(low_with_ctx) - low_citation_count}/{len(low_with_ctx)} ({(len(low_with_ctx) - low_citation_count)/len(low_with_ctx)*100:.1f}%)")
        
        # Average citations
        avg_citations = sum(count_citations(r.get('response', '')) for r in low_with_ctx) / len(low_with_ctx)
        print(f"  - Trung binh so citation: {avg_citations:.2f}")
        
        # Validation reasons
        reasons_count = Counter()
        for r in low_with_ctx:
            reasons = r.get('validation_info', {}).get('reasons', [])
            for reason in reasons:
                reasons_count[reason] += 1
        print(f"  - Validation reasons:")
        for reason, count in reasons_count.most_common():
            print(f"      * {reason}: {count} cau")
    
    # High confidence citation analysis
    print(f"\n✅ PHAN TICH HIGH CONFIDENCE ({len(high_conf)} cau):")
    high_with_ctx = [r for r in high_conf if r.get('validation_info', {}).get('context_docs_count', 0) > 0]
    high_without_ctx = [r for r in high_conf if r.get('validation_info', {}).get('context_docs_count', 0) == 0]
    
    print(f"  - Co context documents: {len(high_with_ctx)} cau")
    print(f"  - Khong co context: {len(high_without_ctx)} cau")
    
    if high_with_ctx:
        high_citation_count = sum(1 for r in high_with_ctx if has_citations(r.get('response', '')))
        print(f"  - Co citation trong response: {high_citation_count}/{len(high_with_ctx)} ({high_citation_count/len(high_with_ctx)*100:.1f}%)")
        print(f"  - Khong co citation: {len(high_with_ctx) - high_citation_count}/{len(high_with_ctx)} ({(len(high_with_ctx) - high_citation_count)/len(high_with_ctx)*100:.1f}%)")
        
        # Average citations
        avg_citations = sum(count_citations(r.get('response', '')) for r in high_with_ctx) / len(high_with_ctx)
        print(f"  - Trung binh so citation: {avg_citations:.2f}")
    
    # Category analysis
    print(f"\n📂 PHAN TICH THEO CATEGORY:")
    category_stats = defaultdict(lambda: {'low': 0, 'high': 0, 'total': 0})
    
    for r in data:
        if r.get('status') != 'success':
            continue
        cat = r.get('category', 'unknown')
        conf = r.get('confidence_score', 0)
        category_stats[cat]['total'] += 1
        if conf < 0.8:
            category_stats[cat]['low'] += 1
        elif conf >= 0.9:
            category_stats[cat]['high'] += 1
    
    for cat in sorted(category_stats.keys()):
        stats = category_stats[cat]
        low_pct = (stats['low'] / stats['total'] * 100) if stats['total'] > 0 else 0
        high_pct = (stats['high'] / stats['total'] * 100) if stats['total'] > 0 else 0
        print(f"  - {cat}:")
        print(f"      Total: {stats['total']} cau")
        print(f"      Low confidence: {stats['low']} ({low_pct:.1f}%)")
        print(f"      High confidence: {stats['high']} ({high_pct:.1f}%)")
    
    # Root cause analysis
    print(f"\n🔬 NGUYEN NHAN CHINH:")
    print(f"\n1. MISSING CITATION (Khong co citation khi co context):")
    missing_citation = [r for r in low_with_ctx if not has_citations(r.get('response', ''))]
    print(f"   - So luong: {len(missing_citation)} cau")
    
    if missing_citation:
        # Category breakdown
        cat_breakdown = Counter(r.get('category', 'unknown') for r in missing_citation)
        print(f"   - Phan bo theo category:")
        for cat, count in cat_breakdown.most_common():
            print(f"      * {cat}: {count} cau")
        
        # Example responses
        print(f"\n   - Vi du response KHONG co citation:")
        for i, r in enumerate(missing_citation[:3], 1):
            print(f"\n   [{i}] {r.get('question_id', 'unknown')} - {r.get('category', 'unknown')}")
            response = r.get('response', '')
            print(f"       Response (preview): {response[:150]}...")
            print(f"       Context docs: {r.get('validation_info', {}).get('context_docs_count', 0)}")
    
    print(f"\n2. SO SANH VOI CAU CO CITATION:")
    with_citation = [r for r in high_with_ctx if has_citations(r.get('response', ''))]
    if with_citation:
        print(f"   - So luong cau co citation: {len(with_citation)}")
        print(f"   - Vi du response CO citation:")
        for i, r in enumerate(with_citation[:2], 1):
            print(f"\n   [{i}] {r.get('question_id', 'unknown')} - {r.get('category', 'unknown')}")
            response = r.get('response', '')
            # Find citation examples
            citations = CITE_RE.findall(response)
            if citations:
                print(f"       Citations found: {citations}")
            print(f"       Response (preview): {response[:200]}...")
    
    # Recommendations
    print(f"\n💡 KHUYEN NGHI:")
    print(f"   1. Cải thiện prompt để yêu cầu AI model luôn thêm citation [1], [2]...")
    print(f"      khi có context documents, đặc biệt với câu hỏi philosophy và religion")
    print(f"   2. Tăng cường validation để đảm bảo citation được thêm vào response")
    print(f"   3. Xem xét điều chỉnh confidence score calculation để phản ánh")
    print(f"      chính xác hơn chất lượng response (hiện tại: 0.6 khi missing citation)")
    print(f"   4. Phân tích thêm tại sao AI model không thêm citation cho một số")
    print(f"      loại câu hỏi (có thể do bản chất trừu tượng của câu hỏi triết học)")
    
    print("\n" + "="*80)

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
    
    analyze_citation_patterns(result_file)

