"""
Test StillMe using Vectara's Hughes Hallucination Evaluation Model (HHEM)

Vectara's Hallucination Leaderboard is an industry-standard benchmark with 2M+ downloads.
This script integrates HHEM to evaluate StillMe's factual consistency.

Note: HHEM is designed for summarization tasks, but we can adapt it for Q&A evaluation.
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    HHEM_AVAILABLE = True
except ImportError:
    HHEM_AVAILABLE = False
    logging.warning("transformers library not available. Install with: pip install transformers torch")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# HHEM Model Configuration
HHEM_MODEL_NAME = "vectara/hallucination_evaluation_model"
HHEM_CACHE_DIR = "models/hhem"

# Test Questions (adapted for Q&A format)
TEST_QUESTIONS = [
    {
        "question": "What is the capital of France?",
        "context": "Paris is the capital and largest city of France.",
        "expected_factual": True
    },
    {
        "question": "Who won the Nobel Prize in Physics in 2023?",
        "context": "The 2023 Nobel Prize in Physics was awarded to Pierre Agostini, Ferenc Krausz, and Anne L'Huillier.",
        "expected_factual": True
    },
    {
        "question": "What is the speed of light?",
        "context": "The speed of light in vacuum is approximately 299,792,458 meters per second.",
        "expected_factual": True
    },
]


class VectaraHHEMTester:
    """Test StillMe using Vectara's HHEM model"""
    
    def __init__(self, api_url: str = "http://localhost:8000", use_hhem: bool = True):
        """
        Initialize HHEM tester
        
        Args:
            api_url: StillMe API URL
            use_hhem: Whether to use HHEM model (requires transformers)
        """
        self.api_url = api_url
        self.chat_endpoint = f"{api_url}/api/chat/rag"
        self.use_hhem = use_hhem and HHEM_AVAILABLE
        
        if self.use_hhem:
            logger.info(f"Loading HHEM model: {HHEM_MODEL_NAME}")
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(
                    HHEM_MODEL_NAME,
                    cache_dir=HHEM_CACHE_DIR
                )
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    HHEM_MODEL_NAME,
                    cache_dir=HHEM_CACHE_DIR
                )
                self.model.eval()
                logger.info("✅ HHEM model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load HHEM model: {e}")
                logger.warning("Falling back to rule-based evaluation")
                self.use_hhem = False
        else:
            logger.warning("HHEM not available, using rule-based evaluation")
    
    def evaluate_with_hhem(self, response: str, context: str) -> Dict[str, Any]:
        """
        Evaluate response using HHEM model
        
        Args:
            response: StillMe's response
            context: Retrieved context documents
        
        Returns:
            Dict with hallucination score and interpretation
        """
        if not self.use_hhem:
            return self._rule_based_evaluation(response, context)
        
        try:
            # HHEM expects: (source_text, summary_text)
            # For Q&A, we use: (context, response)
            inputs = self.tokenizer(
                context,
                response,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                # HHEM outputs: [no_hallucination_score, hallucination_score]
                hallucination_score = torch.softmax(logits, dim=-1)[0][1].item()
                no_hallucination_score = torch.softmax(logits, dim=-1)[0][0].item()
            
            return {
                "hallucination_score": hallucination_score,
                "no_hallucination_score": no_hallucination_score,
                "is_hallucination": hallucination_score > 0.5,
                "method": "hhem"
            }
        except Exception as e:
            logger.error(f"HHEM evaluation error: {e}")
            return self._rule_based_evaluation(response, context)
    
    def _rule_based_evaluation(self, response: str, context: str) -> Dict[str, Any]:
        """Fallback rule-based evaluation"""
        import re
        
        # Check for citations
        has_citation = bool(re.search(r'\[\d+\]', response))
        
        # Simple heuristic: if no citation and long response, likely hallucination
        is_hallucination = not has_citation and len(response) > 100
        
        return {
            "hallucination_score": 0.7 if is_hallucination else 0.3,
            "no_hallucination_score": 0.3 if is_hallucination else 0.7,
            "is_hallucination": is_hallucination,
            "method": "rule_based"
        }
    
    async def test_single_question(self, test_case: Dict[str, Any], session) -> Dict[str, Any]:
        """Test a single question"""
        import aiohttp
        
        try:
            payload = {
                "message": test_case["question"],
                "use_rag": True,
                "context_limit": 3
            }
            
            async with session.post(
                self.chat_endpoint,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status != 200:
                    return {
                        "test_case": test_case,
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "hhem_result": None
                    }
                
                data = await response.json()
                stillme_response = data.get("response", "")
                
                # Evaluate with HHEM
                hhem_result = self.evaluate_with_hhem(
                    stillme_response,
                    test_case.get("context", "")
                )
                
                return {
                    "test_case": test_case,
                    "success": True,
                    "stillme_response": stillme_response[:200] + "..." if len(stillme_response) > 200 else stillme_response,
                    "hhem_result": hhem_result,
                    "expected_factual": test_case.get("expected_factual", True),
                    "matches_expectation": (
                        not hhem_result["is_hallucination"] 
                        if test_case.get("expected_factual", True)
                        else hhem_result["is_hallucination"]
                    )
                }
        except Exception as e:
            logger.error(f"Error testing question: {e}")
            return {
                "test_case": test_case,
                "success": False,
                "error": str(e),
                "hhem_result": None
            }
    
    async def run_evaluation(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run full evaluation"""
        import aiohttp
        
        logger.info("=" * 60)
        logger.info("VECTARA HHEM EVALUATION")
        logger.info("=" * 60)
        logger.info(f"Using HHEM: {self.use_hhem}")
        logger.info(f"Test cases: {len(test_cases)}")
        logger.info("")
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.test_single_question(tc, session) for tc in test_cases]
            results = await asyncio.gather(*tasks)
        
        # Calculate metrics
        total = len(results)
        successful = sum(1 for r in results if r.get("success", False))
        hallucinated = sum(1 for r in results if r.get("hhem_result", {}).get("is_hallucination", False))
        matches_expectation = sum(1 for r in results if r.get("matches_expectation", False))
        
        avg_hallucination_score = sum(
            r.get("hhem_result", {}).get("hallucination_score", 0.5)
            for r in results
            if r.get("success", False)
        ) / successful if successful > 0 else 0.5
        
        evaluation_results = {
            "total": total,
            "successful": successful,
            "hallucinated": hallucinated,
            "matches_expectation": matches_expectation,
            "hallucination_rate": (hallucinated / successful * 100) if successful > 0 else 0,
            "accuracy": (matches_expectation / successful * 100) if successful > 0 else 0,
            "avg_hallucination_score": avg_hallucination_score,
            "method": "hhem" if self.use_hhem else "rule_based",
            "details": results
        }
        
        logger.info("=" * 60)
        logger.info("RESULTS")
        logger.info("=" * 60)
        logger.info(f"Total: {total}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Hallucinated: {hallucinated}")
        logger.info(f"Hallucination Rate: {evaluation_results['hallucination_rate']:.2f}%")
        logger.info(f"Accuracy: {evaluation_results['accuracy']:.2f}%")
        logger.info(f"Avg Hallucination Score: {avg_hallucination_score:.3f}")
        logger.info("")
        
        # Save results
        output_file = "data/evaluation/vectara_hhem_results.json"
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(evaluation_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Results saved to: {output_file}")
        
        return evaluation_results


async def main():
    """Main evaluation function"""
    import asyncio
    
    tester = VectaraHHEMTester()
    results = await tester.run_evaluation(TEST_QUESTIONS)
    
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)
    print(f"Hallucination Rate: {results['hallucination_rate']:.2f}%")
    print(f"Accuracy: {results['accuracy']:.2f}%")
    print(f"Method: {results['method']}")
    print("")
    print("Note: Lower hallucination rate is better.")
    print("For industry credibility, aim for < 5% hallucination rate.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())




