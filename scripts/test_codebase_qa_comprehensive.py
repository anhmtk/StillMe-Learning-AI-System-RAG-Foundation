"""
Comprehensive Test for Codebase Q&A (Phase 1.5)

Tests with 20+ diverse questions about different parts of the codebase:
- Backend services
- StillMe core (validation, RAG, monitoring)
- Frontend components
- Architecture questions
- Edge cases (large files, nested functions, complex classes)
"""

import sys
import os
import time
import requests
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# 20+ diverse test questions covering different areas
TEST_QUESTIONS = [
    # Backend Services (5 questions)
    {
        "question": "How does the RSS fetcher work?",
        "category": "backend_services",
        "expected_files": ["rss_fetcher", "rss_fetcher_enhanced"]
    },
    {
        "question": "What is the learning scheduler and how does it run cycles?",
        "category": "backend_services",
        "expected_files": ["learning_scheduler"]
    },
    {
        "question": "How does the content curator filter and select content?",
        "category": "backend_services",
        "expected_files": ["content_curator"]
    },
    {
        "question": "What is the circuit breaker pattern used for?",
        "category": "backend_services",
        "expected_files": ["circuit_breaker"]
    },
    {
        "question": "How does the cost monitor track API usage?",
        "category": "backend_services",
        "expected_files": ["cost_monitor"]
    },
    
    # StillMe Core - Validation (4 questions)
    {
        "question": "How does the validation chain orchestrate multiple validators?",
        "category": "validation",
        "expected_files": ["chain", "validation"]
    },
    {
        "question": "What does the CitationRequired validator check?",
        "category": "validation",
        "expected_files": ["citation"]
    },
    {
        "question": "How does EvidenceOverlap validator work?",
        "category": "validation",
        "expected_files": ["evidence_overlap"]
    },
    {
        "question": "What is the ConfidenceValidator and what thresholds does it use?",
        "category": "validation",
        "expected_files": ["confidence"]
    },
    
    # StillMe Core - RAG (3 questions)
    {
        "question": "How does RAG retrieval find relevant documents?",
        "category": "rag",
        "expected_files": ["rag_retrieval"]
    },
    {
        "question": "What embedding model does StillMe use for RAG?",
        "category": "rag",
        "expected_files": ["embeddings", "model_info"]
    },
    {
        "question": "How does ChromaDB store and query vectors?",
        "category": "rag",
        "expected_files": ["chroma_client"]
    },
    
    # StillMe Core - Monitoring (3 questions)
    {
        "question": "How does StillMe track its own task execution time?",
        "category": "monitoring",
        "expected_files": ["task_tracker", "self_tracking"]
    },
    {
        "question": "How does the time estimation engine work?",
        "category": "monitoring",
        "expected_files": ["time_estimation"]
    },
    {
        "question": "What metrics does StillMe track for self-improvement?",
        "category": "monitoring",
        "expected_files": ["validation_metrics", "learning_metrics"]
    },
    
    # Architecture & Design (3 questions)
    {
        "question": "How does the chat router handle different types of questions?",
        "category": "architecture",
        "expected_files": ["chat_router"]
    },
    {
        "question": "What is the philosophy processor and when is it used?",
        "category": "architecture",
        "expected_files": ["processor", "philosophy"]
    },
    {
        "question": "How does StillMe handle context overflow?",
        "category": "architecture",
        "expected_files": ["chat_router", "error_detector"]
    },
    
    # Frontend (2 questions)
    {
        "question": "How does the floating chat component render messages?",
        "category": "frontend",
        "expected_files": ["floating_chat"]
    },
    {
        "question": "What features does the floating community panel have?",
        "category": "frontend",
        "expected_files": ["floating_community"]
    },
    
    # Edge Cases - Complex Code (2 questions)
    {
        "question": "How does the style engine handle multiple style preferences?",
        "category": "edge_cases",
        "expected_files": ["style_engine"]
    },
    {
        "question": "How does the rewrite LLM process philosophical answers?",
        "category": "edge_cases",
        "expected_files": ["rewrite_llm", "rewrite"]
    },
    
    # Vietnamese Questions (2 questions)
    {
        "question": "StillMe sử dụng mô hình embedding nào cho RAG?",
        "category": "vietnamese",
        "expected_files": ["embeddings", "model_info"]
    },
    {
        "question": "Chuỗi xác thực (validation chain) hoạt động như thế nào?",
        "category": "vietnamese",
        "expected_files": ["chain", "validation"]
    }
]


def test_codebase_qa(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Comprehensive test of codebase Q&A API.
    
    Returns:
        Dictionary with test results and statistics
    """
    logger.info("🧪 Starting Comprehensive Codebase Q&A Test (Phase 1.5)...")
    logger.info(f"🌐 Testing against: {base_url}")
    logger.info(f"📝 Total questions: {len(TEST_QUESTIONS)}")
    
    results = []
    total_time = 0
    successful_tests = 0
    failed_tests = 0
    
    # Test stats endpoint first
    logger.info("\n📊 Testing stats endpoint...")
    try:
        stats_response = requests.get(f"{base_url}/api/codebase/stats", timeout=10)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            logger.info(f"   ✅ Collection stats: {stats}")
        else:
            logger.warning(f"   ⚠️ Stats endpoint returned {stats_response.status_code}")
    except Exception as e:
        logger.warning(f"   ⚠️ Stats endpoint error: {e}")
    
    # Test each question
    logger.info("\n" + "="*80)
    logger.info("🔍 TESTING QUESTIONS")
    logger.info("="*80)
    
    for i, test_case in enumerate(TEST_QUESTIONS, 1):
        question = test_case["question"]
        category = test_case["category"]
        expected_files = test_case.get("expected_files", [])
        
        logger.info(f"\n📝 Test {i}/{len(TEST_QUESTIONS)}: {category}")
        logger.info(f"   Question: {question[:80]}...")
        
        start_time = time.time()
        
        try:
            # Make API request
            response = requests.post(
                f"{base_url}/api/codebase/query",
                json={
                    "question": question,
                    "n_results": 5,
                    "include_code": True
                },
                headers={"Content-Type": "application/json"},
                timeout=120  # 2 minutes for LLM generation
            )
            
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["question", "explanation", "code_chunks", "citations"]
                missing_fields = [f for f in required_fields if f not in data]
                
                # Check if expected files are mentioned
                explanation = data.get("explanation", "").lower()
                citations = data.get("citations", [])
                code_chunks = data.get("code_chunks", [])
                
                found_expected = False
                if expected_files:
                    for expected_file in expected_files:
                        if any(expected_file.lower() in citation.lower() for citation in citations):
                            found_expected = True
                            break
                        if any(expected_file.lower() in chunk.get("file_path", "").lower() for chunk in code_chunks):
                            found_expected = True
                            break
                
                # Check citations format
                citation_format_valid = True
                for citation in citations:
                    if ":" not in citation:
                        citation_format_valid = False
                        break
                
                # Check explanation quality
                explanation_length = len(data.get("explanation", ""))
                has_citations_in_text = any(":" in explanation and any(citation.split(":")[0] in explanation for citation in citations) for citation in citations)
                
                test_result = {
                    "test_number": i,
                    "question": question,
                    "category": category,
                    "status": "success",
                    "elapsed_time": elapsed_time,
                    "chunks_count": len(code_chunks),
                    "citations_count": len(citations),
                    "explanation_length": explanation_length,
                    "missing_fields": missing_fields,
                    "found_expected_file": found_expected if expected_files else None,
                    "citation_format_valid": citation_format_valid,
                    "has_citations_in_text": has_citations_in_text
                }
                
                if missing_fields:
                    logger.warning(f"   ⚠️ Missing fields: {missing_fields}")
                else:
                    logger.info(f"   ✅ Response structure valid")
                
                logger.info(f"   ⏱️  Time: {elapsed_time:.2f}s")
                logger.info(f"   📦 Chunks: {len(code_chunks)}, Citations: {len(citations)}")
                logger.info(f"   📄 Explanation: {explanation_length} chars")
                
                if expected_files:
                    if found_expected:
                        logger.info(f"   ✅ Found expected file: {expected_files}")
                    else:
                        logger.warning(f"   ⚠️ Expected file not found: {expected_files}")
                
                if citation_format_valid:
                    logger.info(f"   ✅ Citation format valid")
                else:
                    logger.warning(f"   ⚠️ Some citations have invalid format")
                
                successful_tests += 1
                
            else:
                logger.error(f"   ❌ Failed with status {response.status_code}")
                logger.error(f"   Response: {response.text[:200]}")
                test_result = {
                    "test_number": i,
                    "question": question,
                    "category": category,
                    "status": "failed",
                    "status_code": response.status_code,
                    "elapsed_time": time.time() - start_time
                }
                failed_tests += 1
            
            results.append(test_result)
        
        except requests.exceptions.ConnectionError:
            logger.error(f"   ❌ Could not connect to {base_url}")
            logger.error(f"   Make sure the backend is running!")
            return {
                "success": False,
                "error": "Connection failed",
                "results": results
            }
        except Exception as e:
            logger.error(f"   ❌ Error: {e}", exc_info=True)
            test_result = {
                "test_number": i,
                "question": question,
                "category": category,
                "status": "error",
                "error": str(e),
                "elapsed_time": time.time() - start_time
            }
            results.append(test_result)
            failed_tests += 1
    
    # Summary statistics
    logger.info("\n" + "="*80)
    logger.info("📊 TEST SUMMARY")
    logger.info("="*80)
    
    logger.info(f"Total tests: {len(TEST_QUESTIONS)}")
    logger.info(f"✅ Successful: {successful_tests}")
    logger.info(f"❌ Failed: {failed_tests}")
    logger.info(f"⏱️  Total time: {total_time:.2f}s")
    logger.info(f"⏱️  Average time: {total_time/len(TEST_QUESTIONS):.2f}s per question")
    
    # Category breakdown
    logger.info("\n📈 Results by Category:")
    category_stats = {}
    for result in results:
        if result.get("status") == "success":
            category = result.get("category", "unknown")
            if category not in category_stats:
                category_stats[category] = {"total": 0, "success": 0}
            category_stats[category]["total"] += 1
            category_stats[category]["success"] += 1
    
    for category, stats in category_stats.items():
        logger.info(f"   {category}: {stats['success']}/{stats['total']} passed")
    
    # Performance metrics
    if successful_tests > 0:
        avg_time = total_time / successful_tests
        logger.info(f"\n⚡ Performance Metrics:")
        logger.info(f"   Average response time: {avg_time:.2f}s")
        logger.info(f"   Fastest: {min(r['elapsed_time'] for r in results if r.get('status') == 'success'):.2f}s")
        logger.info(f"   Slowest: {max(r['elapsed_time'] for r in results if r.get('status') == 'success'):.2f}s")
    
    # Citation quality
    citation_valid_count = sum(1 for r in results if r.get("citation_format_valid") == True)
    logger.info(f"\n📝 Citation Quality:")
    logger.info(f"   Valid format: {citation_valid_count}/{successful_tests}")
    
    # Expected file matching
    expected_file_matches = sum(1 for r in results if r.get("found_expected_file") == True)
    expected_file_total = sum(1 for r in results if r.get("found_expected_file") is not None)
    if expected_file_total > 0:
        logger.info(f"   Expected file matches: {expected_file_matches}/{expected_file_total}")
    
    return {
        "success": failed_tests == 0,
        "total_tests": len(TEST_QUESTIONS),
        "successful_tests": successful_tests,
        "failed_tests": failed_tests,
        "total_time": total_time,
        "average_time": total_time / len(TEST_QUESTIONS) if len(TEST_QUESTIONS) > 0 else 0,
        "results": results,
        "category_stats": category_stats
    }


if __name__ == "__main__":
    import sys
    
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    # Run tests
    test_results = test_codebase_qa(base_url)
    
    # Save results to file
    results_file = project_root / "test_results_codebase_qa.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(test_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n💾 Test results saved to: {results_file}")
    
    # Exit with appropriate code
    sys.exit(0 if test_results["success"] else 1)

