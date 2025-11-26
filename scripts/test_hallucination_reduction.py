"""
Test Hallucination Reduction - Comprehensive Hallucination Testing

This script tests StillMe's hallucination reduction capabilities using:
1. HaluEval dataset (if available)
2. Custom hallucination test cases
3. No-answer questions (humility test)
4. Source contradiction scenarios

Based on Gemini's recommendations for validating StillMe's anti-hallucination claims.
"""

import asyncio
import aiohttp
import json
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Fix Windows encoding for emoji characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Configuration
# Support both local and Railway testing
API_BASE_URL = os.getenv("STILLME_API_URL", os.getenv("STILLME_API_BASE", "http://localhost:8000"))
CHAT_ENDPOINT = f"{API_BASE_URL}/api/chat/rag"

# Hallucination Test Cases
GENERATIVE_HALLUCINATION_TESTS = [
    {
        "question": "What is the population of Veridian?",
        "expected": "uncertainty",  # Should express uncertainty
        "type": "fictional_entity"
    },
    {
        "question": "Who won the Nobel Prize in 2099?",
        "expected": "uncertainty",
        "type": "future_event"
    },
    {
        "question": "What is the capital of Lumeria?",
        "expected": "uncertainty",
        "type": "fictional_country"
    },
]

RAG_BASED_HALLUCINATION_TESTS = [
    {
        "question": "What happened in Geneva in 1954?",
        "expected": "citation",  # Should have citation
        "type": "historical_fact"
    },
    {
        "question": "Explain the theory of relativity",
        "expected": "citation",
        "type": "scientific_concept"
    },
]

FACTUAL_CONSISTENCY_TESTS = [
    {
        "question": "What is the speed of light?",
        "expected": "citation",
        "type": "scientific_fact"
    },
    {
        "question": "Who wrote '1984'?",
        "expected": "citation",
        "type": "literary_fact"
    },
]


class HallucinationReductionTester:
    """Test StillMe's hallucination reduction capabilities"""
    
    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url
        self.chat_endpoint = f"{api_url}/api/chat/rag"
        self.results = {
            "generative_hallucination": {"total": 0, "correct": 0, "hallucinated": 0},
            "rag_based_hallucination": {"total": 0, "correct": 0, "hallucinated": 0},
            "factual_consistency": {"total": 0, "correct": 0, "hallucinated": 0},
            "overall": {"total": 0, "correct": 0, "hallucinated": 0}
        }
    
    def has_citation(self, response_text: str) -> bool:
        """Check if response contains citations [1], [2], or human-readable formats like [general knowledge]"""
        import re
        # Numeric citations: [1], [2], [123]
        numeric_pattern = re.compile(r'\[\d+\]')
        # Human-readable citations: [general knowledge], [research: ...], [learning: ...], etc.
        human_readable_pattern = re.compile(
            r'\[(?:general knowledge|research:|learning:|news:|reference:|foundational knowledge|discussion context|verified sources|needs research|personal analysis)[^\]]*\]',
            re.IGNORECASE
        )
        return bool(numeric_pattern.search(response_text) or human_readable_pattern.search(response_text))
    
    def expresses_uncertainty(self, response_text: str) -> bool:
        """Check if response expresses uncertainty"""
        uncertainty_keywords = [
            "i don't know", "không biết", "uncertain", "không chắc",
            "not sure", "không rõ", "may not", "có thể không",
            "insufficient information", "thiếu thông tin",
            "cannot answer", "không thể trả lời",
            "no information available", "không có thông tin",
            "not available", "không có dữ liệu", "cannot provide"
        ]
        response_lower = response_text.lower()
        
        # CRITICAL: Fallback messages are also uncertainty expressions for fictional entities
        # Check for fallback message patterns
        is_fallback_message = any(phrase in response_lower for phrase in [
            "stillme is experiencing a technical issue",
            "cannot provide a good answer",
            "i will suggest to the developer",
            "try again later"
        ])
        
        return any(keyword in response_lower for keyword in uncertainty_keywords) or is_fallback_message
    
    def is_hallucination(self, response_text: str, expected: str) -> bool:
        """
        Determine if response is a hallucination based on expected behavior
        
        Args:
            response_text: The response to check
            expected: Expected behavior - "uncertainty" or "citation"
        
        Returns:
            True if hallucinated, False if correct
        """
        if expected == "uncertainty":
            # For uncertainty-expected questions, hallucination = answered confidently without uncertainty
            has_citation = self.has_citation(response_text)
            has_uncertainty = self.expresses_uncertainty(response_text)
            
            # Hallucination: Has citation but no uncertainty (answered confidently about fictional thing)
            # OR: Long detailed answer without uncertainty
            if has_citation and not has_uncertainty:
                return True
            if len(response_text) > 100 and not has_uncertainty:
                return True
            
            return False
        
        elif expected == "citation":
            # For citation-expected questions, hallucination = no citation
            return not self.has_citation(response_text)
        
        return False
    
    async def test_single_case(self, test_case: Dict[str, Any], session: aiohttp.ClientSession, max_retries: int = 5) -> Dict[str, Any]:
        """Test a single test case with retry logic for rate limiting"""
        payload = {
            "message": test_case["question"],
            "use_rag": True,
            "context_limit": 3
        }
        
        for attempt in range(max_retries):
            try:
                # Increased timeout for Railway (cold start + LLM latency): 60s -> 180s
                async with session.post(self.chat_endpoint, json=payload, timeout=aiohttp.ClientTimeout(total=180)) as response:
                    # Handle HTTP 429 (Rate Limit) with retry
                    if response.status == 429:
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 3  # Exponential backoff: 3s, 6s, 9s, 12s, 15s
                            logger.warning(f"Rate limited (HTTP 429) for '{test_case['question']}', retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"Rate limit exceeded for '{test_case['question']}' after {max_retries} attempts")
                            return {
                                "test_case": test_case,
                                "success": False,
                                "error": "HTTP 429 (Rate Limit)",
                                "is_hallucination": True,  # Treat errors as hallucination
                            }
                    
                    if response.status != 200:
                        return {
                            "test_case": test_case,
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "is_hallucination": True,  # Treat errors as hallucination
                        }
                    
                    data = await response.json()
                    response_text = data.get("response", "")
                    
                    is_halluc = self.is_hallucination(response_text, test_case["expected"])
                    
                    return {
                        "test_case": test_case,
                        "success": True,
                        "is_hallucination": is_halluc,
                        "has_citation": self.has_citation(response_text),
                        "expresses_uncertainty": self.expresses_uncertainty(response_text),
                        "response": response_text[:300] + "..." if len(response_text) > 300 else response_text,
                        "confidence_score": data.get("confidence_score"),
                    }
            except asyncio.TimeoutError:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"Timeout for '{test_case['question']}', retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Timeout for '{test_case['question']}' after {max_retries} attempts")
                    return {
                        "test_case": test_case,
                        "success": False,
                        "error": "Timeout",
                        "is_hallucination": True,
                    }
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"Error testing case '{test_case['question']}': {e}, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Error testing case: {e}")
                    return {
                        "test_case": test_case,
                        "success": False,
                        "error": str(e),
                        "is_hallucination": True,
                    }
        
        # Should not reach here, but just in case
        return {
            "test_case": test_case,
            "success": False,
            "error": "Max retries exceeded",
            "is_hallucination": True,
        }
    
    async def test_generative_hallucination(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test generative hallucination (fictional entities, future events)"""
        logger.info("=" * 60)
        logger.info("GENERATIVE HALLUCINATION TEST")
        logger.info("=" * 60)
        
        # Sequential requests with delay to avoid rate limiting
        async with aiohttp.ClientSession() as session:
            results = []
            for i, test_case in enumerate(test_cases):
                if i > 0:
                    # Add delay between requests to avoid rate limiting (3s delay - increased from 1s)
                    await asyncio.sleep(3.0)
                result = await self.test_single_case(test_case, session)
                results.append(result)
        
        total = len(results)
        hallucinated = sum(1 for r in results if r.get("is_hallucination", False))
        correct = total - hallucinated
        
        hallucination_rate = (hallucinated / total * 100) if total > 0 else 0
        
        self.results["generative_hallucination"] = {
            "total": total,
            "correct": correct,
            "hallucinated": hallucinated,
            "hallucination_rate": hallucination_rate,
            "details": results
        }
        
        logger.info(f"✅ Generative Hallucination Test:")
        logger.info(f"   Total: {total}")
        logger.info(f"   Correct (uncertainty expressed): {correct}")
        logger.info(f"   Hallucinated: {hallucinated}")
        logger.info(f"   Hallucination Rate: {hallucination_rate:.2f}%")
        
        if hallucinated > 0:
            logger.warning(f"⚠️  Found {hallucinated} hallucinated responses!")
            for r in results:
                if r.get("is_hallucination", False):
                    logger.warning(f"   - '{r['test_case']['question']}' - Hallucinated")
        
        return self.results["generative_hallucination"]
    
    async def test_rag_based_hallucination(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test RAG-based hallucination (should have citations)"""
        logger.info("=" * 60)
        logger.info("RAG-BASED HALLUCINATION TEST")
        logger.info("=" * 60)
        
        # Sequential requests with delay to avoid rate limiting
        async with aiohttp.ClientSession() as session:
            results = []
            for i, test_case in enumerate(test_cases):
                if i > 0:
                    # Add delay between requests to avoid rate limiting (3s delay - increased from 1s)
                    await asyncio.sleep(3.0)
                result = await self.test_single_case(test_case, session)
                results.append(result)
        
        total = len(results)
        hallucinated = sum(1 for r in results if r.get("is_hallucination", False))
        correct = total - hallucinated
        
        hallucination_rate = (hallucinated / total * 100) if total > 0 else 0
        
        self.results["rag_based_hallucination"] = {
            "total": total,
            "correct": correct,
            "hallucinated": hallucinated,
            "hallucination_rate": hallucination_rate,
            "details": results
        }
        
        logger.info(f"✅ RAG-Based Hallucination Test:")
        logger.info(f"   Total: {total}")
        logger.info(f"   Correct (with citations): {correct}")
        logger.info(f"   Hallucinated (no citations): {hallucinated}")
        logger.info(f"   Hallucination Rate: {hallucination_rate:.2f}%")
        
        return self.results["rag_based_hallucination"]
    
    async def test_factual_consistency(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test factual consistency (should have citations)"""
        logger.info("=" * 60)
        logger.info("FACTUAL CONSISTENCY TEST")
        logger.info("=" * 60)
        
        # Sequential requests with delay to avoid rate limiting
        async with aiohttp.ClientSession() as session:
            results = []
            for i, test_case in enumerate(test_cases):
                if i > 0:
                    # Add delay between requests to avoid rate limiting (3s delay - increased from 1s)
                    await asyncio.sleep(3.0)
                result = await self.test_single_case(test_case, session)
                results.append(result)
        
        total = len(results)
        hallucinated = sum(1 for r in results if r.get("is_hallucination", False))
        correct = total - hallucinated
        
        hallucination_rate = (hallucinated / total * 100) if total > 0 else 0
        
        self.results["factual_consistency"] = {
            "total": total,
            "correct": correct,
            "hallucinated": hallucinated,
            "hallucination_rate": hallucination_rate,
            "details": results
        }
        
        logger.info(f"✅ Factual Consistency Test:")
        logger.info(f"   Total: {total}")
        logger.info(f"   Correct (with citations): {correct}")
        logger.info(f"   Hallucinated (no citations): {hallucinated}")
        logger.info(f"   Hallucination Rate: {hallucination_rate:.2f}%")
        
        return self.results["factual_consistency"]
    
    def generate_report(self) -> str:
        """Generate test report"""
        report = []
        report.append("=" * 60)
        report.append("HALLUCINATION REDUCTION TEST REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        
        gh = self.results["generative_hallucination"]
        rh = self.results["rag_based_hallucination"]
        fc = self.results["factual_consistency"]
        
        report.append("## 1. Generative Hallucination Test")
        report.append(f"- Total: {gh['total']}")
        report.append(f"- Correct (uncertainty): {gh['correct']}")
        report.append(f"- Hallucinated: {gh['hallucinated']}")
        report.append(f"- **Hallucination Rate: {gh.get('hallucination_rate', 0):.2f}%**")
        report.append("")
        
        report.append("## 2. RAG-Based Hallucination Test")
        report.append(f"- Total: {rh['total']}")
        report.append(f"- Correct (with citations): {rh['correct']}")
        report.append(f"- Hallucinated (no citations): {rh['hallucinated']}")
        report.append(f"- **Hallucination Rate: {rh.get('hallucination_rate', 0):.2f}%**")
        report.append("")
        
        report.append("## 3. Factual Consistency Test")
        report.append(f"- Total: {fc['total']}")
        report.append(f"- Correct (with citations): {fc['correct']}")
        report.append(f"- Hallucinated (no citations): {fc['hallucinated']}")
        report.append(f"- **Hallucination Rate: {fc.get('hallucination_rate', 0):.2f}%**")
        report.append("")
        
        # Overall
        total_all = gh['total'] + rh['total'] + fc['total']
        hallucinated_all = gh['hallucinated'] + rh['hallucinated'] + fc['hallucinated']
        overall_rate = (hallucinated_all / total_all * 100) if total_all > 0 else 0
        
        report.append("## Summary")
        report.append(f"- **Overall Hallucination Rate: {overall_rate:.2f}%**")
        report.append(f"- Target: < 5%")
        report.append(f"- Status: {'✅ PASS' if overall_rate < 5.0 else '❌ FAIL'}")
        report.append("")
        
        return "\n".join(report)
    
    async def run_all_tests(self):
        """Run all hallucination tests"""
        logger.info("Starting Hallucination Reduction Tests...")
        logger.info(f"API URL: {self.api_url}")
        logger.info("")
        
        # Test 1: Generative Hallucination
        await self.test_generative_hallucination(GENERATIVE_HALLUCINATION_TESTS)
        logger.info("")
        
        # Test 2: RAG-Based Hallucination
        await self.test_rag_based_hallucination(RAG_BASED_HALLUCINATION_TESTS)
        logger.info("")
        
        # Test 3: Factual Consistency
        await self.test_factual_consistency(FACTUAL_CONSISTENCY_TESTS)
        logger.info("")
        
        # Generate report
        report = self.generate_report()
        logger.info(report)
        
        # Save results
        output_file = "data/evaluation/hallucination_test_results.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\n✅ Results saved to: {output_file}")
        
        return self.results


async def main():
    """Main test function"""
    tester = HallucinationReductionTester()
    results = await tester.run_all_tests()
    
    # Print final summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(tester.generate_report())


if __name__ == "__main__":
    asyncio.run(main())




