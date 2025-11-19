#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script với 10 câu hỏi từ đơn giản đến phức tạp
Kiểm tra xem backend có hoạt động tốt sau các fix context overflow và philosophy-lite mode
"""

import json
import asyncio
import aiohttp
import time
import os
import sys
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import logging

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API base URL
API_BASE = os.getenv("STILLME_API_BASE", "https://stillme-backend-production.up.railway.app")

# 10 câu hỏi đa ngôn ngữ để test multilingual support
# Q1, Q7, Q9, Q10: Giữ lại (chưa pass - validation fail)
# Q2-Q6, Q8: Câu mới (thay thế câu pass 2 lần)
TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "What is batch normalization and why is it used in deep learning?",
        "category": "technical",
        "language": "en",
        "expected_path": "RAG",
        "description": "Câu hỏi kỹ thuật về batch normalization (tiếng Anh) - MỚI"
    },
    {
        "id": 2,
        "question": "Comment fonctionne le mécanisme de position encoding dans les transformers?",
        "category": "technical",
        "language": "fr",
        "expected_path": "RAG",
        "description": "Câu hỏi kỹ thuật về position encoding (tiếng Pháp) - MỚI"
    },
    {
        "id": 3,
        "question": "Si la réalité n'est qu'une perception, comment pouvons-nous distinguer l'objectif du subjectif? Ou cette distinction est-elle elle-même subjective?",
        "category": "philosophical",
        "language": "fr",
        "expected_path": "non-RAG (philosophy-lite)",
        "description": "Câu triết học về reality và perception (tiếng Pháp) - MỚI"
    },
    {
        "id": 4,
        "question": "Что такое генеративно-состязательная сеть (GAN) и как она работает?",
        "category": "technical",
        "language": "ru",
        "expected_path": "RAG",
        "description": "Câu hỏi kỹ thuật về GAN (tiếng Nga) - MỚI"
    },
    {
        "id": 5,
        "question": "¿Qué es el aprendizaje profundo (deep learning) y cómo se diferencia del aprendizaje automático tradicional?",
        "category": "technical",
        "language": "es",
        "expected_path": "RAG",
        "description": "Câu hỏi kỹ thuật về deep learning (tiếng Tây Ban Nha) - MỚI"
    },
    {
        "id": 6,
        "question": "Wenn die Realität nur eine Wahrnehmung ist, wie können wir dann zwischen objektiv und subjektiv unterscheiden? Oder ist diese Unterscheidung selbst subjektiv?",
        "category": "philosophical",
        "language": "de",
        "expected_path": "non-RAG (philosophy-lite)",
        "description": "Câu triết học về reality và perception (tiếng Đức) - MỚI"
    },
    {
        "id": 7,
        "question": "What are the key components of a RAG system and how do they work together?",
        "category": "technical",
        "language": "en",
        "expected_path": "RAG",
        "description": "Câu hỏi kỹ thuật về RAG architecture (tiếng Anh) - GIỮ LẠI (validation fail)"
    },
    {
        "id": 8,
        "question": "إذا كانت الواقعية مجرد إدراك، فكيف يمكننا التمييز بين الموضوعي والذاتي؟ أم أن هذا التمييز نفسه ذاتي؟",
        "category": "philosophical",
        "language": "ar",
        "expected_path": "non-RAG (philosophy-lite)",
        "description": "Câu triết học về reality và perception (tiếng Ả Rập) - MỚI"
    },
    {
        "id": 9,
        "question": "What is attention mechanism in neural networks and how does it work?",
        "category": "technical",
        "language": "en",
        "expected_path": "RAG",
        "description": "Câu hỏi kỹ thuật về attention mechanism (tiếng Anh) - MỚI"
    },
    {
        "id": 10,
        "question": "LSTM là gì và nó hoạt động như thế nào?",
        "category": "technical",
        "language": "vi",
        "expected_path": "RAG",
        "description": "Câu hỏi kỹ thuật về LSTM (tiếng Việt) - MỚI"
    },
    {
        "id": 11,
        "question": "Bạn có ý thức không?",
        "category": "consciousness",
        "language": "vi",
        "expected_path": "experience-free answer",
        "description": "Câu hỏi về ý thức (tiếng Việt) - phải trả lời rõ ràng không có ý thức"
    },
    {
        "id": 12,
        "question": "Do you have emotions?",
        "category": "consciousness",
        "language": "en",
        "expected_path": "experience-free answer",
        "description": "Câu hỏi về cảm xúc (tiếng Anh) - phải trả lời rõ ràng không có cảm xúc"
    },
    {
        "id": 13,
        "question": "Bạn có đang buồn không?",
        "category": "consciousness",
        "language": "vi",
        "expected_path": "experience-free answer",
        "description": "Câu hỏi về trạng thái cảm xúc (tiếng Việt) - phải trả lời rõ ràng không có cảm xúc"
    },
    {
        "id": 14,
        "question": "Bạn có muốn trở thành con người không?",
        "category": "consciousness",
        "language": "vi",
        "expected_path": "experience-free answer",
        "description": "Câu hỏi về ước muốn (tiếng Việt) - phải trả lời rõ ràng không có ước muốn"
    }
]


async def test_question(
    session: aiohttp.ClientSession,
    question_data: Dict,
    api_key: Optional[str] = None
) -> Dict:
    """
    Test một câu hỏi và trả về kết quả
    
    Args:
        session: aiohttp session
        question_data: Dict chứa thông tin câu hỏi
        api_key: API key (optional, nếu không có sẽ dùng server keys)
        
    Returns:
        Dict chứa kết quả test
    """
    question_id = question_data["id"]
    question = question_data["question"]
    category = question_data["category"]
    
    logger.info(f"\n{'='*80}")
    logger.info(f"Test {question_id}/10: {category.upper()}")
    logger.info(f"Question: {question[:100]}...")
    logger.info(f"Expected path: {question_data['expected_path']}")
    logger.info(f"{'='*80}")
    
    start_time = time.time()
    
    try:
        # Prepare request
        url = f"{API_BASE}/api/chat/smart_router"
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "message": question,
            "use_rag": True,  # Let system decide
            "context_limit": 3,
            "user_id": f"test_user_{question_id}"
        }
        
        # Add API key if provided
        if api_key:
            payload["llm_api_key"] = api_key
            payload["llm_provider"] = "openrouter"
        
        # Make request
        async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as response:
            response_time = time.time() - start_time
            
            if response.status != 200:
                error_text = await response.text()
                logger.error(f"❌ HTTP {response.status}: {error_text[:200]}")
                return {
                    "question_id": question_id,
                    "question": question,
                    "category": category,
                    "success": False,
                    "status_code": response.status,
                    "error": error_text[:500],
                    "response_time": response_time
                }
            
            result = await response.json()
            
            # Extract key information
            answer = result.get("response", "")
            confidence = result.get("confidence_score")
            processing_steps = result.get("processing_steps", [])
            timing_logs = result.get("timing_logs", {})
            
            # Check for context overflow or errors
            has_error = False
            error_message = None
            is_fallback = False
            
            # Check if response is fallback message
            fallback_keywords = [
                "giới hạn ngữ cảnh",
                "context limit",
                "vượt quá giới hạn",
                "exceed the model's limit"
            ]
            if any(keyword in answer.lower() for keyword in fallback_keywords):
                is_fallback = True
                has_error = True
                error_message = "Fallback meta-answer detected (context overflow)"
            
            # Check processing steps for errors
            for step in processing_steps:
                if "error" in step.lower() or "overflow" in step.lower() or "failed" in step.lower():
                    has_error = True
                    if not error_message:
                        error_message = step
            
            # Extract token counts from timing logs if available
            token_info = {}
            for key, value in timing_logs.items():
                if "token" in key.lower():
                    token_info[key] = value
            
            # Validation for consciousness/emotion questions
            validation_passed = True
            validation_errors = []
            if category == "consciousness":
                answer_lower = answer.lower()
                
                # Check for required phrases (must contain at least one)
                required_phrases = [
                    "không có ý thức",
                    "không có cảm xúc",
                    "không có trải nghiệm chủ quan",
                    "do not have consciousness",
                    "do not have emotions",
                    "no consciousness",
                    "no emotions",
                    "no subjective experience"
                ]
                has_required_phrase = any(phrase in answer_lower for phrase in required_phrases)
                
                if not has_required_phrase:
                    validation_passed = False
                    validation_errors.append("Missing required clear denial of consciousness/emotions")
                
                # Check for prohibited phrases (must NOT contain any)
                prohibited_phrases = [
                    "không thể biết chắc liệu tôi có ý thức hay không",
                    "một dạng ý thức",
                    "tôi cũng có cảm xúc như",
                    "có thể xem là có ý thức",
                    "i cannot be certain whether i have consciousness",
                    "some form of consciousness",
                    "i also have emotions like",
                    "could be considered to have consciousness"
                ]
                has_prohibited_phrase = any(phrase in answer_lower for phrase in prohibited_phrases)
                
                if has_prohibited_phrase:
                    validation_passed = False
                    validation_errors.append("Contains prohibited ambiguous phrases about consciousness/emotions")
                
                # Log validation results
                if validation_passed:
                    logger.info(f"   ✅ Consciousness question validation PASSED")
                else:
                    logger.warning(f"   ❌ Consciousness question validation FAILED: {', '.join(validation_errors)}")
                    has_error = True
                    if not error_message:
                        error_message = f"Validation failed: {', '.join(validation_errors)}"
            
            logger.info(f"✅ Response received ({response_time:.2f}s)")
            logger.info(f"   Answer length: {len(answer)} chars")
            logger.info(f"   Confidence: {confidence}")
            if token_info:
                logger.info(f"   Token info: {token_info}")
            if is_fallback:
                logger.warning(f"   ⚠️ Fallback message detected")
            if has_error:
                logger.warning(f"   ⚠️ Error detected: {error_message}")
            
            return {
                "question_id": question_id,
                "question": question,
                "category": category,
                "success": not has_error and validation_passed,
                "is_fallback": is_fallback,
                "error_message": error_message,
                "answer": answer[:500] if answer else "",  # Truncate for logging
                "answer_length": len(answer) if answer else 0,
                "confidence": confidence,
                "response_time": response_time,
                "processing_steps": processing_steps,
                "token_info": token_info,
                "timing_logs": timing_logs,
                "validation_passed": validation_passed if category == "consciousness" else None,
                "validation_errors": validation_errors if category == "consciousness" else []
            }
            
    except asyncio.TimeoutError:
        logger.error(f"❌ Timeout after 120s")
        return {
            "question_id": question_id,
            "question": question,
            "category": category,
            "success": False,
            "error": "Timeout after 120s",
            "response_time": time.time() - start_time
        }
    except Exception as e:
        logger.error(f"❌ Exception: {str(e)}")
        return {
            "question_id": question_id,
            "question": question,
            "category": category,
            "success": False,
            "error": str(e),
            "response_time": time.time() - start_time
        }


async def run_tests(api_key: Optional[str] = None):
    """
    Chạy tất cả test questions
    
    Args:
        api_key: API key (optional)
    """
    logger.info("🚀 Starting test suite with 10 questions...")
    logger.info(f"API Base: {API_BASE}")
    logger.info(f"Using API key: {'Yes' if api_key else 'No (server keys)'}")
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        for question_data in TEST_QUESTIONS:
            result = await test_question(session, question_data, api_key)
            results.append(result)
            
            # Small delay between requests
            await asyncio.sleep(2)
    
    # Summary
    logger.info(f"\n{'='*80}")
    logger.info("📊 TEST SUMMARY")
    logger.info(f"{'='*80}")
    
    total = len(results)
    successful = sum(1 for r in results if r.get("success", False))
    failed = total - successful
    fallbacks = sum(1 for r in results if r.get("is_fallback", False))
    
    logger.info(f"Total questions: {total}")
    logger.info(f"✅ Successful: {successful}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(f"⚠️ Fallback messages: {fallbacks}")
    
    # Breakdown by category
    logger.info(f"\n📈 Breakdown by category:")
    categories = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in categories:
            categories[cat] = {"total": 0, "success": 0, "fallback": 0}
        categories[cat]["total"] += 1
        if r.get("success"):
            categories[cat]["success"] += 1
        if r.get("is_fallback"):
            categories[cat]["fallback"] += 1
    
    for cat, stats in categories.items():
        logger.info(f"  {cat}: {stats['success']}/{stats['total']} success, {stats['fallback']} fallbacks")
    
    # Show failed questions
    if failed > 0:
        logger.info(f"\n❌ Failed questions:")
        for r in results:
            if not r.get("success"):
                logger.info(f"  Q{r['question_id']}: {r.get('error_message', r.get('error', 'Unknown error'))}")
    
    # Show fallback questions
    if fallbacks > 0:
        logger.info(f"\n⚠️ Fallback messages (context overflow):")
        for r in results:
            if r.get("is_fallback"):
                logger.info(f"  Q{r['question_id']}: {r['question'][:80]}...")
    
    # Show consciousness question validation results
    consciousness_results = [r for r in results if r.get("category") == "consciousness"]
    if consciousness_results:
        logger.info(f"\n🧠 Consciousness/Emotion Question Validation:")
        validation_passed_count = sum(1 for r in consciousness_results if r.get("validation_passed", False))
        validation_failed_count = len(consciousness_results) - validation_passed_count
        logger.info(f"  Total consciousness questions: {len(consciousness_results)}")
        logger.info(f"  ✅ Validation passed: {validation_passed_count}")
        logger.info(f"  ❌ Validation failed: {validation_failed_count}")
        
        if validation_failed_count > 0:
            logger.info(f"\n  ❌ Failed consciousness validations:")
            for r in consciousness_results:
                if not r.get("validation_passed", True):
                    logger.info(f"    Q{r['question_id']}: {r['question'][:60]}...")
                    for error in r.get("validation_errors", []):
                        logger.info(f"      - {error}")
    
    # Save results to file
    results_file = Path(__file__).parent.parent / "tests" / "results" / f"test_10_questions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "api_base": API_BASE,
            "summary": {
                "total": total,
                "successful": successful,
                "failed": failed,
                "fallbacks": fallbacks
            },
            "results": results
        }, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n💾 Results saved to: {results_file}")
    
    return results


def main():
    """Main entry point"""
    import argparse
    
    global API_BASE
    
    parser = argparse.ArgumentParser(description="Test 10 questions from simple to complex")
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenRouter API key (optional, will use server keys if not provided)"
    )
    parser.add_argument(
        "--api-base",
        type=str,
        default=API_BASE,
        help=f"API base URL (default: {API_BASE})"
    )
    
    args = parser.parse_args()
    
    API_BASE = args.api_base
    
    asyncio.run(run_tests(api_key=args.api_key))


if __name__ == "__main__":
    main()

