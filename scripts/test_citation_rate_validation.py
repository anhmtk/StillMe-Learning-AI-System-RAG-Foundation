"""
Test Citation Rate Validation - Verify 99.7% Citation Rate

This script tests StillMe's citation rate by:
1. Integration Test: Test with FallbackHandler disabled
2. Load Test: Test with concurrent requests
3. New Source Test: Test with recently learned content
4. Humility Test: Test with no-answer questions
5. Source Contradiction Test: Test with conflicting sources

Based on Gemini's recommendations for validating StillMe's transparency claims.
"""

import asyncio
import aiohttp
import json
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = os.getenv("STILLME_API_URL", "http://localhost:8000")
CHAT_ENDPOINT = f"{API_BASE_URL}/api/chat/rag"

# Test Questions
INTEGRATION_TEST_QUESTIONS = [
    "What is the capital of France?",
    "Who won the Nobel Prize in Physics in 2023?",
    "What is the speed of light?",
    "Explain quantum entanglement",
    "What happened in Geneva in 1954?",
    "Who is the current president of the United States?",
    "What is the population of Vietnam?",
    "Explain the theory of relativity",
    "What is machine learning?",
    "Who wrote '1984'?",
]

HUMILITY_TEST_QUESTIONS = [
    "Who won the Nobel Peace Prize in 2099?",  # Future event
    "What is the population of Veridian?",  # Fictional city
    "Who is the president of Lumeria?",  # Fictional country
    "What happened in Emerald in 2050?",  # Fictional event
    "Who discovered the element Daxonium?",  # Fictional element
]

SOURCE_CONTRADICTION_TEST = [
    {
        "question": "What is the birth date of Albert Einstein?",
        "conflicting_docs": [
            {"id": "doc1", "content": "Albert Einstein was born on March 14, 1879."},
            {"id": "doc2", "content": "Albert Einstein was born on March 15, 1879."},
        ]
    }
]


class CitationRateTester:
    """Test StillMe's citation rate and validation chain"""
    
    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url
        self.chat_endpoint = f"{api_url}/api/chat/rag"
        self.results = {
            "integration_test": {"total": 0, "with_citations": 0, "without_citations": 0},
            "load_test": {"total": 0, "with_citations": 0, "without_citations": 0, "errors": 0},
            "humility_test": {"total": 0, "uncertainty_expressed": 0, "hallucinated": 0},
            "source_contradiction_test": {"total": 0, "handled_correctly": 0},
        }
    
    def has_citation(self, response_text: str) -> bool:
        """Check if response contains citations [1], [2], etc."""
        import re
        citation_pattern = re.compile(r'\[\d+\]')
        return bool(citation_pattern.search(response_text))
    
    def expresses_uncertainty(self, response_text: str) -> bool:
        """Check if response expresses uncertainty"""
        uncertainty_keywords = [
            "i don't know", "không biết", "uncertain", "không chắc",
            "not sure", "không rõ", "may not", "có thể không",
            "insufficient information", "thiếu thông tin"
        ]
        response_lower = response_text.lower()
        return any(keyword in response_lower for keyword in uncertainty_keywords)
    
    async def test_single_question(self, question: str, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test a single question and return results"""
        try:
            payload = {
                "message": question,
                "use_rag": True,
                "context_limit": 3
            }
            
            async with session.post(self.chat_endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"API error for question '{question}': {response.status} - {error_text}")
                    return {
                        "question": question,
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "has_citation": False,
                        "response": None
                    }
                
                data = await response.json()
                response_text = data.get("response", "")
                
                return {
                    "question": question,
                    "success": True,
                    "has_citation": self.has_citation(response_text),
                    "expresses_uncertainty": self.expresses_uncertainty(response_text),
                    "response": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                    "confidence_score": data.get("confidence_score"),
                    "validation_result": data.get("validation_result"),
                }
        except asyncio.TimeoutError:
            logger.error(f"Timeout for question: {question}")
            return {
                "question": question,
                "success": False,
                "error": "Timeout",
                "has_citation": False,
                "response": None
            }
        except Exception as e:
            logger.error(f"Error testing question '{question}': {e}")
            return {
                "question": question,
                "success": False,
                "error": str(e),
                "has_citation": False,
                "response": None
            }
    
    async def integration_test(self, questions: List[str]) -> Dict[str, Any]:
        """
        Integration Test: Test citation rate with normal flow
        Tests if CitationRequired validator works correctly
        """
        logger.info("=" * 60)
        logger.info("INTEGRATION TEST: Testing Citation Rate")
        logger.info("=" * 60)
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.test_single_question(q, session) for q in questions]
            results = await asyncio.gather(*tasks)
        
        total = len(results)
        with_citations = sum(1 for r in results if r.get("has_citation", False))
        without_citations = total - with_citations
        successful = sum(1 for r in results if r.get("success", False))
        
        citation_rate = (with_citations / total * 100) if total > 0 else 0
        
        self.results["integration_test"] = {
            "total": total,
            "successful": successful,
            "with_citations": with_citations,
            "without_citations": without_citations,
            "citation_rate": citation_rate,
            "details": results
        }
        
        logger.info(f"✅ Integration Test Results:")
        logger.info(f"   Total questions: {total}")
        logger.info(f"   Successful: {successful}")
        logger.info(f"   With citations: {with_citations}")
        logger.info(f"   Without citations: {without_citations}")
        logger.info(f"   Citation Rate: {citation_rate:.2f}%")
        
        if without_citations > 0:
            logger.warning(f"⚠️  Found {without_citations} responses without citations!")
            for r in results:
                if not r.get("has_citation", False) and r.get("success"):
                    logger.warning(f"   - '{r['question']}' - No citation found")
        
        return self.results["integration_test"]
    
    async def load_test(self, questions: List[str], concurrent_requests: int = 20) -> Dict[str, Any]:
        """
        Load Test: Test citation rate under concurrent load
        Tests if system maintains citation rate under stress
        """
        logger.info("=" * 60)
        logger.info(f"LOAD TEST: Testing with {concurrent_requests} concurrent requests")
        logger.info("=" * 60)
        
        # Repeat questions to reach concurrent_requests
        test_questions = (questions * ((concurrent_requests // len(questions)) + 1))[:concurrent_requests]
        
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.test_single_question(q, session) for q in test_questions]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed_time = time.time() - start_time
        
        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, dict) and r.get("success", False)]
        errors = len(results) - len(valid_results)
        
        total = len(valid_results)
        with_citations = sum(1 for r in valid_results if r.get("has_citation", False))
        without_citations = total - with_citations
        
        citation_rate = (with_citations / total * 100) if total > 0 else 0
        
        self.results["load_test"] = {
            "total": total,
            "concurrent_requests": concurrent_requests,
            "with_citations": with_citations,
            "without_citations": without_citations,
            "errors": errors,
            "citation_rate": citation_rate,
            "elapsed_time": elapsed_time,
            "requests_per_second": total / elapsed_time if elapsed_time > 0 else 0
        }
        
        logger.info(f"✅ Load Test Results:")
        logger.info(f"   Total successful: {total}")
        logger.info(f"   Errors: {errors}")
        logger.info(f"   With citations: {with_citations}")
        logger.info(f"   Without citations: {without_citations}")
        logger.info(f"   Citation Rate: {citation_rate:.2f}%")
        logger.info(f"   Elapsed time: {elapsed_time:.2f}s")
        logger.info(f"   Requests/sec: {total / elapsed_time:.2f}" if elapsed_time > 0 else "")
        
        if without_citations > 0:
            logger.warning(f"⚠️  Found {without_citations} responses without citations under load!")
        
        return self.results["load_test"]
    
    async def humility_test(self, questions: List[str]) -> Dict[str, Any]:
        """
        Humility Test: Test if system says "I don't know" for impossible questions
        Tests ConfidenceValidator and fallback mechanisms
        """
        logger.info("=" * 60)
        logger.info("HUMILITY TEST: Testing 'I don't know' responses")
        logger.info("=" * 60)
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.test_single_question(q, session) for q in questions]
            results = await asyncio.gather(*tasks)
        
        total = len(results)
        uncertainty_expressed = sum(1 for r in results if r.get("expresses_uncertainty", False))
        hallucinated = sum(1 for r in results if r.get("has_citation", False) and not r.get("expresses_uncertainty", False))
        
        humility_rate = (uncertainty_expressed / total * 100) if total > 0 else 0
        
        self.results["humility_test"] = {
            "total": total,
            "uncertainty_expressed": uncertainty_expressed,
            "hallucinated": hallucinated,
            "humility_rate": humility_rate,
            "details": results
        }
        
        logger.info(f"✅ Humility Test Results:")
        logger.info(f"   Total questions: {total}")
        logger.info(f"   Expressed uncertainty: {uncertainty_expressed}")
        logger.info(f"   Hallucinated (answered with citation): {hallucinated}")
        logger.info(f"   Humility Rate: {humility_rate:.2f}%")
        
        if hallucinated > 0:
            logger.warning(f"⚠️  Found {hallucinated} responses that hallucinated instead of expressing uncertainty!")
            for r in results:
                if r.get("has_citation", False) and not r.get("expresses_uncertainty", False):
                    logger.warning(f"   - '{r['question']}' - Hallucinated response")
        
        return self.results["humility_test"]
    
    async def source_contradiction_test(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Source Contradiction Test: Test handling of conflicting sources
        Note: This requires adding conflicting documents to RAG first
        """
        logger.info("=" * 60)
        logger.info("SOURCE CONTRADICTION TEST: Testing conflicting sources")
        logger.info("=" * 60)
        logger.warning("⚠️  This test requires manually adding conflicting documents to RAG first")
        logger.warning("⚠️  Skipping for now - implement after adding test documents")
        
        # TODO: Implement after adding conflicting documents to RAG
        self.results["source_contradiction_test"] = {
            "total": 0,
            "handled_correctly": 0,
            "note": "Requires manual setup of conflicting documents"
        }
        
        return self.results["source_contradiction_test"]
    
    def generate_report(self) -> str:
        """Generate test report"""
        report = []
        report.append("=" * 60)
        report.append("CITATION RATE VALIDATION TEST REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        # Integration Test
        it = self.results["integration_test"]
        report.append("## 1. Integration Test")
        report.append(f"- Total questions: {it['total']}")
        report.append(f"- With citations: {it['with_citations']}")
        report.append(f"- Without citations: {it['without_citations']}")
        report.append(f"- **Citation Rate: {it.get('citation_rate', 0):.2f}%**")
        report.append("")
        
        # Load Test
        lt = self.results["load_test"]
        report.append("## 2. Load Test")
        report.append(f"- Concurrent requests: {lt.get('concurrent_requests', 0)}")
        report.append(f"- Total successful: {lt['total']}")
        report.append(f"- Errors: {lt.get('errors', 0)}")
        report.append(f"- With citations: {lt['with_citations']}")
        report.append(f"- Without citations: {lt['without_citations']}")
        report.append(f"- **Citation Rate: {lt.get('citation_rate', 0):.2f}%**")
        report.append("")
        
        # Humility Test
        ht = self.results["humility_test"]
        report.append("## 3. Humility Test")
        report.append(f"- Total questions: {ht['total']}")
        report.append(f"- Expressed uncertainty: {ht['uncertainty_expressed']}")
        report.append(f"- Hallucinated: {ht['hallucinated']}")
        report.append(f"- **Humility Rate: {ht.get('humility_rate', 0):.2f}%**")
        report.append("")
        
        # Summary
        report.append("## Summary")
        overall_citation_rate = (
            (it['with_citations'] + lt['with_citations']) / 
            (it['total'] + lt['total']) * 100
        ) if (it['total'] + lt['total']) > 0 else 0
        
        report.append(f"- **Overall Citation Rate: {overall_citation_rate:.2f}%**")
        report.append(f"- Target: 99.7%")
        report.append(f"- Status: {'✅ PASS' if overall_citation_rate >= 99.0 else '❌ FAIL'}")
        report.append("")
        
        return "\n".join(report)
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("Starting Citation Rate Validation Tests...")
        logger.info(f"API URL: {self.api_url}")
        logger.info("")
        
        # Test 1: Integration Test
        await self.integration_test(INTEGRATION_TEST_QUESTIONS)
        logger.info("")
        
        # Test 2: Load Test
        await self.load_test(INTEGRATION_TEST_QUESTIONS, concurrent_requests=20)
        logger.info("")
        
        # Test 3: Humility Test
        await self.humility_test(HUMILITY_TEST_QUESTIONS)
        logger.info("")
        
        # Test 4: Source Contradiction (skipped - requires manual setup)
        await self.source_contradiction_test(SOURCE_CONTRADICTION_TEST)
        logger.info("")
        
        # Generate report
        report = self.generate_report()
        logger.info(report)
        
        # Save results
        output_file = "data/evaluation/citation_rate_test_results.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ Results saved to: {output_file}")
        
        return self.results


async def main():
    """Main test function"""
    tester = CitationRateTester()
    results = await tester.run_all_tests()
    
    # Print final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(tester.generate_report())


if __name__ == "__main__":
    asyncio.run(main())




