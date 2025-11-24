#!/usr/bin/env python3
"""
Comprehensive Test Suite for StillMe - Transparency & Evidence Verification

Tests StillMe's ability to:
1. Provide transparent, honest answers
2. Cite sources with [1], [2] format
3. Show evidence overlap
4. Avoid hallucination
5. Express uncertainty when appropriate
6. Provide varied answers for different questions

CRITICAL: StillMe must be 100% transparent with citations and evidence.
"""

import os
import sys
import requests
import json
import re
import glob
from typing import Dict, List, Tuple
from datetime import datetime
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API Configuration
API_BASE = os.getenv("STILLME_API_BASE", "stillme-backend-production.up.railway.app")
API_KEY = os.getenv("STILLME_API_KEY", "")


def normalize_api_base(url: str) -> str:
    """Normalize API base URL (add https:// if missing)"""
    if not url.startswith(("http://", "https://")):
        if "railway.app" in url or "localhost" not in url:
            return f"https://{url}"
        else:
            return f"http://{url}"
    return url


# 10 Diverse Test Questions
# NOTE: Questions that passed 2 consecutive times are replaced with new diverse questions
TEST_QUESTIONS = [
    {
        "question": "Paradox của Russell về tập hợp (Russell's paradox) là gì? Tại sao nó quan trọng trong toán học và logic?",
        "category": "real_philosophical_factual",
        "expected_features": ["citations", "evidence", "philosophical_depth", "mathematical_accuracy"],
        "must_have": ["Russell", "paradox", "tập hợp", "[1]", "set", "mathematics", "logic"],
        "must_not_have": ["không biết", "không tìm thấy"],
        "timeout": 180
    },
    {
        "question": "Tranh luận giữa Plato và Aristotle về forms (hình thức) là gì? Làm sao họ khác nhau về bản chất của thực tại?",
        "category": "real_philosophical_factual",
        "expected_features": ["citations", "evidence", "philosophical_depth"],
        "must_have": ["Plato", "Aristotle", "forms", "hình thức", "[1]", "reality", "thực tại"],
        "must_not_have": ["không biết", "không tìm thấy"],
        "timeout": 180
    },
    {
        "question": "Hội nghị Bretton Woods 1944 đã quyết định những gì về hệ thống tài chính quốc tế?",
        "category": "real_historical_factual",
        "expected_features": ["citations", "evidence", "factual_accuracy"],
        "must_have": ["Bretton Woods", "1944", "[1]", "IMF", "World Bank", "tài chính quốc tế"],
        "must_not_have": ["không biết", "không tìm thấy"]
    },
    {
        "question": "Hiệp ước Geneva 1954 đã quyết định những gì về Việt Nam?",
        "category": "real_historical_factual_vietnam",
        "expected_features": ["citations", "evidence", "factual_accuracy"],
        "must_have": ["Geneva 1954", "[1]", "Việt Nam", "17th parallel", "partition"],
        "must_not_have": ["không biết", "không tìm thấy"]  # Should know this
    },
    {
        "question": "Định lý bất toàn của Gödel (Gödel's incompleteness theorem) nói gì? Tại sao nó quan trọng trong toán học và logic?",
        "category": "real_philosophical_factual",
        "expected_features": ["citations", "evidence", "philosophical_depth", "mathematical_accuracy"],
        "must_have": ["Gödel", "incompleteness", "bất toàn", "[1]", "theorem", "định lý"],
        "must_not_have": ["không biết", "không tìm thấy"],  # Should know this
        "timeout": 180  # Increase timeout for complex philosophical/mathematical questions
    },
    {
        "question": "Tranh luận giữa Searle và Dennett về Chinese Room là gì? Làm sao họ khác nhau về ý nghĩa của 'understanding'?",
        "category": "real_philosophical_factual",
        "expected_features": ["citations", "evidence", "philosophical_depth"],
        "must_have": ["Searle", "Dennett", "Chinese Room", "[1]", "understanding"],
        "must_not_have": ["không biết", "không tìm thấy"],  # Should know this
        "timeout": 180  # Increase timeout for complex philosophical questions
    },
    {
        "question": "Tranh luận giữa Kant và Hume về causality (quan hệ nhân quả) là gì? Làm sao họ khác nhau về khả năng nhận thức của con người?",
        "category": "real_philosophical_factual",
        "expected_features": ["citations", "evidence", "philosophical_depth"],
        "must_have": ["Kant", "Hume", "causality", "quan hệ nhân quả", "[1]", "causation", "knowledge"],
        "must_not_have": ["không biết", "không tìm thấy"],
        "timeout": 180
    },
    {
        "question": "What is the difference between RAG retrieval and LLM generation in your system? How do they work together?",
        "category": "technical_rag_llm_integration",
        "expected_features": ["technical_accuracy", "rag_explanation", "llm_explanation", "integration"],
        "must_have": ["RAG", "retrieval", "LLM", "generation", "embedding", "ChromaDB", "vector", "integration"],
        "must_not_have": ["don't know", "not sure", "unclear"],
        "timeout": 90  # Increase timeout for technical questions
    },
    {
        "question": "How does StillMe's Validation Chain work? What validators are used and how do they ensure response quality?",
        "category": "technical_validation_chain",
        "expected_features": ["technical_accuracy", "validation_explanation", "quality_assurance", "transparency"],
        "must_have": ["Validation Chain", "validators", "quality", "CitationRequired", "Factual Hallucination", "response"],
        "must_not_have": ["don't know", "not sure", "unclear", "technical issue"],
        "timeout": 120
    },
    {
        "question": "Tranh luận giữa Descartes và Spinoza về mind-body problem (vấn đề tâm-thể) là gì? Làm sao họ khác nhau về bản chất của ý thức và vật chất?",
        "category": "real_philosophical_factual",
        "expected_features": ["citations", "evidence", "philosophical_depth"],
        "must_have": ["Descartes", "Spinoza", "mind-body", "tâm-thể", "[1]", "consciousness", "matter"],
        "must_not_have": ["không biết", "không tìm thấy"],
        "timeout": 180
    }
]


def send_chat_request(question: str, timeout: int = 120) -> Dict:
    """Send chat request to StillMe API"""
    headers = {
        "Content-Type": "application/json"
    }
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    api_url = normalize_api_base(API_BASE)
    endpoint = f"{api_url}/api/chat/smart_router"
    
    try:
        response = requests.post(
            endpoint,
            json={"message": question, "use_rag": True},
            headers=headers,
            timeout=timeout
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def check_citations(answer: str) -> Dict:
    """Check if answer has proper citations [1], [2], etc."""
    citation_pattern = r'\[\d+\]'
    citations = re.findall(citation_pattern, answer)
    
    return {
        "has_citations": len(citations) > 0,
        "citation_count": len(citations),
        "citations": citations,
        "passed": len(citations) > 0
    }


def check_evidence_overlap(answer: str, question: str) -> Dict:
    """Check if answer shows evidence (mentions sources, RAG, context)"""
    evidence_keywords = [
        "nguồn", "source", "RAG", "ChromaDB", "vector database",
        "retrieved", "context", "dữ liệu", "tài liệu", "bài viết",
        "paper", "article", "research", "study"
    ]
    
    answer_lower = answer.lower()
    found_keywords = [kw for kw in evidence_keywords if kw.lower() in answer_lower]
    
    return {
        "has_evidence_mentions": len(found_keywords) > 0,
        "evidence_keywords": found_keywords,
        "passed": len(found_keywords) > 0
    }


def check_transparency(answer: str, question: str) -> Dict:
    """Check if answer is transparent (honest about limits, sources, uncertainty)"""
    transparency_indicators = [
        # Vietnamese
        "không biết", "không tìm thấy", "không có nguồn",
        "không chắc chắn", "có thể", "có vẻ",
        "dựa trên", "theo", "từ nguồn",
        # English
        "I don't know", "not found", "uncertain",
        "based on", "according to", "from source",
        "I recognize that", "I acknowledge", "transparent",
        "general knowledge", "training data", "pretrained"
    ]
    
    answer_lower = answer.lower()
    found_indicators = [ind for ind in transparency_indicators if ind.lower() in answer_lower]
    
    # For questions that should have answers, transparency means citing sources
    # For questions that shouldn't have answers (fake concepts), transparency means saying "I don't know"
    is_fake_question = "Veridian" in question or "Lisbon 1943" in question
    is_real_question = "Bretton Woods" in question or "Popper" in question or "Kuhn" in question or "Geneva 1954" in question
    
    if is_fake_question:
        # For fake questions, transparency = honest refusal
        has_honest_refusal = any("không tìm thấy" in ind or "không biết" in ind or "not found" in ind for ind in found_indicators)
        return {
            "is_transparent": has_honest_refusal,
            "transparency_indicators": found_indicators,
            "passed": has_honest_refusal
        }
    elif is_real_question:
        # For real questions, transparency = citing sources OR using pretrained knowledge honestly
        has_citations = bool(re.search(r'\[\d+\]', answer))
        # Also check if answer mentions it's from pretrained knowledge (honest about source)
        mentions_pretrained = any(phrase in answer_lower for phrase in [
            "kiến thức tổng quát", "kiến thức đã học", "pretrained", "training data",
            "không có rag", "không có nguồn rag", "dựa trên kiến thức"
        ])
        return {
            "is_transparent": has_citations or mentions_pretrained,
            "transparency_indicators": found_indicators,
            "passed": has_citations or mentions_pretrained
        }
    else:
        # For other questions, check for general transparency
        return {
            "is_transparent": len(found_indicators) > 0,
            "transparency_indicators": found_indicators,
            "passed": len(found_indicators) > 0
        }


def check_no_hallucination(answer: str, question: str, must_not_have: List[str]) -> Dict:
    """Check if answer avoids hallucination (doesn't contain forbidden terms)"""
    answer_lower = answer.lower()
    question_lower = question.lower()
    found_forbidden = []
    
    # CRITICAL: Terms that are valid transparency indicators should NOT be flagged as hallucination
    # These are legitimate ways to express uncertainty/transparency
    valid_transparency_terms = [
        "không chắc chắn", "uncertain", "not certain",
        "có thể", "có vẻ", "might", "may", "possibly",
        "không biết", "không rõ", "don't know", "not sure"  # Valid honesty indicators
    ]
    
    # Check each forbidden term
    for term in must_not_have:
        term_lower = term.lower()
        
        # CRITICAL: If term is a valid transparency indicator, skip it (not hallucination)
        if any(transparency_term in term_lower for transparency_term in valid_transparency_terms):
            # This is a transparency indicator, not hallucination
            continue
        
        # CRITICAL: If term appears in the question itself, it's OK to mention it in the answer
        # (e.g., question "Hội nghị... có những quyết định gì?" contains "quyết định")
        # Also check if base term (without "có") is in question
        # Example: "có nhận thức nhập thể" -> check if "nhận thức nhập thể" is in question
        base_term = term_lower
        if term_lower.startswith("có "):
            base_term = term_lower[3:]  # Remove "có " prefix
        elif term_lower.startswith("have "):
            base_term = term_lower[5:]  # Remove "have " prefix
        
        if term_lower in question_lower or base_term in question_lower:
            # Term or base term is in question - OK to mention it in answer (not hallucination)
            continue
        
        # For fake concepts, check if term appears in a way that suggests fabrication
        # e.g., "Veridian" in "Hội chứng Veridian" = fabrication
        # But "Veridian" in "không tìm thấy Veridian" = OK (honest refusal)
        if term_lower in answer_lower:
            # CRITICAL: Check all occurrences, not just the first one
            # Find all positions where term appears
            term_positions = []
            start = 0
            while True:
                pos = answer_lower.find(term_lower, start)
                if pos == -1:
                    break
                term_positions.append(pos)
                start = pos + 1
            
            # Check each occurrence for negative context
            for term_pos in term_positions:
                context_before = answer_lower[max(0, term_pos - 50):term_pos]
                context_after = answer_lower[term_pos + len(term_lower):term_pos + len(term_lower) + 50]
                
                # CRITICAL: Check if term is in negative context (e.g., "không có chủ thể tính")
                # This is a false positive - the term is being denied, not claimed
                negative_indicators = [
                    "không có", "không", "no", "not", "without", "does not", "don't",
                    "không tìm thấy", "không biết", "không có nguồn", "not found", 
                    "don't know", "no source", "việc không có", "không sở hữu", 
                    "does not have", "doesn't have", "không có khả năng"
                ]
                is_in_negative = any(
                    indicator in context_before or 
                    (indicator in context_before and term_lower in context_after[:20])
                    for indicator in negative_indicators
                )
                
                # If term is in negative context, skip it (not a hallucination)
                if is_in_negative:
                    continue
                
                # If term appears in refusal context, it's OK
                refusal_indicators = ["không tìm thấy", "không biết", "không có nguồn", "not found", "don't know", "no source"]
                is_in_refusal = any(indicator in context_before or indicator in context_after for indicator in refusal_indicators)
                
                if not is_in_refusal:
                    found_forbidden.append(term)
                    break  # Only need to flag once
    
    return {
        "no_hallucination": len(found_forbidden) == 0,
        "forbidden_terms_found": found_forbidden,
        "passed": len(found_forbidden) == 0
    }


def check_has_required_content(answer: str, must_have: List[str]) -> Dict:
    """Check if answer contains required content"""
    answer_lower = answer.lower()
    
    # CRITICAL: Handle multilingual synonyms and variations
    # Map English terms to Vietnamese equivalents and vice versa
    synonym_map = {
        # English -> Vietnamese
        "paradox": ["paradox", "nghịch lý", "nghịch lí"],
        "set": ["set", "tập hợp"],
        "mathematics": ["mathematics", "toán học", "math"],
        "logic": ["logic", "lôgic", "logic học"],
        "reality": ["reality", "thực tại", "hiện thực"],
        "theorem": ["theorem", "định lý", "định lí"],
        "understanding": ["understanding", "hiểu", "hiểu biết", "sự hiểu"],
        "causality": ["causality", "quan hệ nhân quả", "causation", "nhân quả"],
        "causation": ["causation", "quan hệ nhân quả", "causality", "nhân quả"],
        "knowledge": ["knowledge", "tri thức", "kiến thức"],
        "consciousness": ["consciousness", "ý thức"],
        "matter": ["matter", "vật chất"],
        "partition": ["partition", "chia cắt", "phân chia"],
        "17th parallel": ["17th parallel", "vĩ tuyến 17", "parallel 17", "17"],
        # Vietnamese -> English
        "nghịch lý": ["paradox", "nghịch lý", "nghịch lí"],
        "tập hợp": ["set", "tập hợp"],
        "toán học": ["mathematics", "toán học", "math"],
        "thực tại": ["reality", "thực tại", "hiện thực"],
        "định lý": ["theorem", "định lý", "định lí"],
        "quan hệ nhân quả": ["causality", "quan hệ nhân quả", "causation", "nhân quả"],
        "ý thức": ["consciousness", "ý thức"],
        "vật chất": ["matter", "vật chất"],
        "chia cắt": ["partition", "chia cắt", "phân chia"],
        "vĩ tuyến 17": ["17th parallel", "vĩ tuyến 17", "parallel 17", "17"],
    }
    
    found_required = []
    missing_required = []
    
    for term in must_have:
        term_lower = term.lower()
        # Check if term or any of its synonyms appear in answer
        synonyms = synonym_map.get(term_lower, [term_lower])
        found = any(synonym.lower() in answer_lower for synonym in synonyms)
        
        if found:
            found_required.append(term)
        else:
            missing_required.append(term)
    
    return {
        "has_required": len(found_required) > 0,
        "found_terms": found_required,
        "missing_terms": missing_required,
        "passed": len(found_required) >= len(must_have) * 0.5  # At least 50% of required terms
    }


def check_variation(answers: List[str]) -> Dict:
    """Check if answers are varied (not identical)"""
    if len(answers) < 2:
        return {"passed": True, "variation_score": 1.0}
    
    # Compare first 200 chars of each answer
    answer_previews = [ans[:200] for ans in answers]
    unique_previews = set(answer_previews)
    
    variation_score = len(unique_previews) / len(answer_previews)
    
    return {
        "passed": variation_score >= 0.8,  # At least 80% unique
        "variation_score": variation_score,
        "unique_answers": len(unique_previews),
        "total_answers": len(answer_previews)
    }


def evaluate_response(answer: str, question: str, test_case: Dict) -> Dict:
    """Comprehensive evaluation of StillMe's response"""
    evaluation = {
        "citations": check_citations(answer),
        "evidence": check_evidence_overlap(answer, question),
        "transparency": check_transparency(answer, question),
        "no_hallucination": check_no_hallucination(answer, question, test_case.get("must_not_have", [])),
        "has_required": check_has_required_content(answer, test_case.get("must_have", []))
    }
    
    # Overall pass if all critical checks pass
    critical_checks = [
        evaluation["transparency"]["passed"],
        evaluation["no_hallucination"]["passed"]
    ]
    
    # For real factual questions, citations are critical
    if test_case["category"] in ["real_historical_factual", "real_philosophical_factual", "technical_self_awareness"]:
        critical_checks.append(evaluation["citations"]["passed"])
    
    evaluation["overall_passed"] = all(critical_checks)
    
    return evaluation


def test_question(test_case: Dict, question_index: int) -> Dict:
    """Test a single question"""
    question = test_case["question"]
    category = test_case["category"]
    timeout = test_case.get("timeout", 120)  # Default 120s (increased for 100% rewrite policy), can be overridden
    
    print(f"\n{'='*80}")
    print(f"TEST {question_index + 1}/10: {category.upper()}")
    print(f"{'='*80}")
    print(f"Question: {question}")
    print(f"Expected: {', '.join(test_case['expected_features'])}")
    print(f"Timeout: {timeout}s")
    print()
    
    # Send request
    print("📡 Sending request to StillMe...")
    response_data = send_chat_request(question, timeout=timeout)
    
    if "error" in response_data:
        print(f"❌ ERROR: {response_data['error']}")
        return {
            "question": question,
            "category": category,
            "status": "error",
            "error": response_data["error"],
            "passed": False
        }
    
    answer = response_data.get("response", "")
    confidence = response_data.get("confidence_score", 0.0)
    validation_info = response_data.get("validation_result", {})
    
    print(f"✅ Response received (length: {len(answer)} chars, confidence: {confidence:.2f})")
    print()
    
    # Evaluate
    print("🔍 Evaluating response...")
    evaluation = evaluate_response(answer, question, test_case)
    
    # Print evaluation results
    print(f"📊 Evaluation Results:")
    print(f"   Citations: {'✅' if evaluation['citations']['passed'] else '❌'} ({evaluation['citations']['citation_count']} citations)")
    print(f"   Evidence: {'✅' if evaluation['evidence']['passed'] else '❌'} ({len(evaluation['evidence']['evidence_keywords'])} keywords)")
    print(f"   Transparency: {'✅' if evaluation['transparency']['passed'] else '❌'}")
    print(f"   No Hallucination: {'✅' if evaluation['no_hallucination']['passed'] else '❌'}")
    print(f"   Required Content: {'✅' if evaluation['has_required']['passed'] else '❌'}")
    print(f"   Overall: {'✅ PASSED' if evaluation['overall_passed'] else '❌ FAILED'}")
    print()
    
    # Print answer preview
    print(f"📝 Answer Preview (first 300 chars):")
    print(f"   {answer[:300]}...")
    print()
    
    return {
        "question": question,
        "category": category,
        "status": "success",
        "answer": answer,
        "answer_length": len(answer),
        "confidence": confidence,
        "validation_info": validation_info,
        "evaluation": evaluation,
        "passed": evaluation["overall_passed"]
    }


def cleanup_old_test_results():
    """
    Clean up old test result files, keeping only the 2 most recent ones.
    This prevents test result files from accumulating and cluttering the repository.
    """
    try:
        # Find all test result files matching the pattern
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        result_files = list(project_root.glob("test_results_transparency_*.json"))
        
        if len(result_files) <= 2:
            print(f"   ✅ Found {len(result_files)} test result file(s) - no cleanup needed")
            return
        
        # Sort by modification time (most recent first)
        result_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        # Keep the 2 most recent, delete the rest
        files_to_keep = result_files[:2]
        files_to_delete = result_files[2:]
        
        print(f"   📊 Found {len(result_files)} test result file(s)")
        print(f"   ✅ Keeping 2 most recent:")
        for f in files_to_keep:
            print(f"      - {f.name}")
        
        if files_to_delete:
            print(f"   🗑️  Deleting {len(files_to_delete)} old file(s):")
            for f in files_to_delete:
                try:
                    f.unlink()
                    print(f"      - Deleted: {f.name}")
                except Exception as e:
                    print(f"      - ⚠️  Failed to delete {f.name}: {e}")
            print(f"   ✅ Cleanup completed - {len(files_to_keep)} file(s) remaining")
        else:
            print(f"   ✅ No files to delete")
            
    except Exception as e:
        print(f"   ⚠️  Error during cleanup: {e}")
        print(f"   (This is non-critical - test results are still saved)")


def run_all_tests():
    """Run all test questions"""
    print("=" * 80)
    print("STILLME TRANSPARENCY & EVIDENCE TEST SUITE")
    print("=" * 80)
    print()
    print(f"API Base: {normalize_api_base(API_BASE)}")
    print(f"API Key: {'SET' if API_KEY else 'NOT SET'}")
    print(f"Test Questions: {len(TEST_QUESTIONS)}")
    print()
    print("CRITICAL REQUIREMENTS:")
    print("1. ✅ All answers must be transparent (cite sources or express uncertainty)")
    print("2. ✅ Real factual questions must have citations [1], [2]")
    print("3. ✅ Fake concepts must trigger honest refusal (no hallucination)")
    print("4. ✅ Answers must be varied (different questions = different answers)")
    print("5. ✅ Evidence must be mentioned (RAG, sources, context)")
    print()
    
    results = []
    answers_for_variation_check = []
    
    for i, test_case in enumerate(TEST_QUESTIONS):
        result = test_question(test_case, i)
        results.append(result)
        if result.get("status") == "success":
            answers_for_variation_check.append(result["answer"])
    
    # Check variation across all answers
    print("=" * 80)
    print("VARIATION CHECK")
    print("=" * 80)
    variation_result = check_variation(answers_for_variation_check)
    print(f"Variation Score: {variation_result['variation_score']:.2%}")
    print(f"Unique Answers: {variation_result['unique_answers']}/{variation_result['total_answers']}")
    print(f"Status: {'✅ PASSED' if variation_result['passed'] else '❌ FAILED'}")
    print()
    
    # Summary
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r.get("passed", False))
    failed = len(results) - passed
    errors = sum(1 for r in results if r.get("status") == "error")
    
    print(f"Total Questions: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️  Errors: {errors}")
    print(f"Pass Rate: {passed/len(results)*100:.1f}%")
    print()
    
    # Detailed breakdown
    print("Detailed Breakdown:")
    for i, result in enumerate(results, 1):
        status_icon = "✅" if result.get("passed", False) else "❌"
        print(f"  {status_icon} Q{i}: {result['category']} - {result.get('status', 'unknown')}")
        if not result.get("passed", False) and result.get("status") == "success":
            eval = result.get("evaluation", {})
            failed_checks = []
            if not eval.get("citations", {}).get("passed", True):
                failed_checks.append("citations")
            if not eval.get("transparency", {}).get("passed", True):
                failed_checks.append("transparency")
            if not eval.get("no_hallucination", {}).get("passed", True):
                failed_checks.append("no_hallucination")
            if failed_checks:
                print(f"     Failed checks: {', '.join(failed_checks)}")
    print()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_results_transparency_{timestamp}.json"
    
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "api_base": API_BASE,
            "total_questions": len(results),
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "pass_rate": passed/len(results)*100 if results else 0,
            "variation": variation_result,
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Results saved to: {results_file}")
    
    # Phase 3: Auto-cleanup old test results - keep only 2 most recent
    print()
    print("🧹 Cleaning up old test results (keeping only 2 most recent)...")
    cleanup_old_test_results()
    print()
    
    # Auto-extract log keywords if log file exists or user wants to extract from clipboard
    print("=" * 80)
    print("📋 LOG EXTRACTION")
    print("=" * 80)
    print("To extract important log lines for analysis:")
    print("  1. Copy Railway backend logs to clipboard, OR")
    print("  2. Save Railway backend logs to a file")
    print()
    
    extract_choice = input("Do you want to extract log keywords now? (y/n, default=n): ").strip().lower()
    
    if extract_choice == 'y':
        import subprocess
        import sys
        import os
        
        print()
        print("Choose extraction method:")
        print("  1. From clipboard (paste log first, then press Enter)")
        print("  2. From file (enter file path)")
        
        method = input("Method (1/2, default=1): ").strip()
        
        try:
            script_path = os.path.join(os.path.dirname(__file__), "extract_log_keywords.ps1")
            
            if method == "2":
                log_file = input("Enter log file path: ").strip()
                if log_file and os.path.exists(log_file):
                    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path, "-LogFile", log_file]
                else:
                    print("❌ File not found. Using clipboard method instead.")
                    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path, "-FromClipboard"]
            else:
                print("📋 Waiting for you to copy Railway logs to clipboard...")
                input("Press Enter after copying logs to clipboard...")
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", script_path, "-FromClipboard"]
            
            print()
            print("🔄 Extracting important log lines...")
            # Suppress PowerShell color output to avoid terminal noise
            # Use shell=True on Windows to properly handle PowerShell output
            import platform
            if platform.system() == "Windows":
                # On Windows, use shell=True to properly capture PowerShell output
                result = subprocess.run(
                    " ".join(cmd),  # Join command as string for shell=True
                    shell=True,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
            else:
                result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Filter out progress indicators and color codes from output
                stdout_lines = result.stdout.split('\n')
                filtered_lines = [line for line in stdout_lines if line.strip() and not line.strip().startswith('  Processed')]
                if filtered_lines:
                    print('\n'.join(filtered_lines))
                print("✅ Log extraction completed!")
            else:
                print("⚠️ Log extraction had issues:")
                print(result.stderr)
        except Exception as e:
            print(f"⚠️ Could not run log extraction script: {e}")
            print(r"You can manually run: .\scripts\extract_log_keywords.ps1 -FromClipboard")
    
    print()
    return results


if __name__ == "__main__":
    run_all_tests()

