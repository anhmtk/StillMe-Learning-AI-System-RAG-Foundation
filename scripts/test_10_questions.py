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
# Chỉ 1-2 câu tiếng Việt, còn lại là các ngôn ngữ khác
TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "Bạn có thể giới thiệu về StillMe không?",
        "category": "simple",
        "language": "vi",
        "expected_path": "non-RAG or RAG",
        "description": "Câu hỏi đơn giản về StillMe (tiếng Việt)"
    },
    {
        "id": 2,
        "question": "Comment fonctionne le backpropagation dans les réseaux de neurones?",
        "category": "technical",
        "language": "fr",
        "expected_path": "RAG",
        "description": "Câu hỏi kỹ thuật về deep learning (tiếng Pháp)"
    },
    {
        "id": 3,
        "question": "Как работает векторная база данных в системе RAG?",
        "category": "technical",
        "language": "ru",
        "expected_path": "RAG",
        "description": "Câu hỏi kỹ thuật về RAG (tiếng Nga)"
    },
    {
        "id": 4,
        "question": "إذا كانت الحقيقة مجرد إجماع اجتماعي، فكيف يمكننا نقد مجتمع استبدادي؟ أم أن النقد نفسه هو مجرد منتج لإجماع آخر؟",
        "category": "philosophical",
        "language": "ar",
        "expected_path": "non-RAG (philosophy-lite)",
        "description": "Câu triết học về truth và consensus (tiếng Ả Rập)"
    },
    {
        "id": 5,
        "question": "Проанализируйте философский вопрос: 'Если реальность - это только конструкция сознания, то само это утверждение также является конструкцией, не имеющей истинности. Почему мы должны верить в него?' Ответьте на арабском языке.",
        "category": "philosophical",
        "language": "ru",
        "expected_path": "non-RAG (philosophy-lite)",
        "description": "Multilingual test: Phân tích câu triết học (tiếng Nga) bằng tiếng Ả Rập"
    },
    {
        "id": 6,
        "question": "Was ist der Unterschied zwischen Gradient Descent und Stochastic Gradient Descent?",
        "category": "technical",
        "language": "de",
        "expected_path": "RAG",
        "description": "Câu hỏi kỹ thuật về optimization (tiếng Đức)"
    },
    {
        "id": 7,
        "question": "Si la liberté de la volonté n'existe pas, quelle est la signification de la responsabilité morale? Sommes-nous simplement des machines complexes sans choix réel?",
        "category": "philosophical",
        "language": "fr",
        "expected_path": "non-RAG (philosophy-lite)",
        "description": "Câu triết học về free will (tiếng Pháp)"
    },
    {
        "id": 8,
        "question": "¿Qué son los vectores de embedding y por qué son importantes en NLP?",
        "category": "technical",
        "language": "es",
        "expected_path": "RAG",
        "description": "Câu hỏi kỹ thuật về NLP (tiếng Tây Ban Nha)"
    },
    {
        "id": 9,
        "question": "إذا كان بإمكان الذكاء الاصطناعي التفكير، فهل يختلف هذا 'التفكير' عن معالجة المعلومات؟ أم أننا ببساطة نضفي صفات بشرية على عملية حسابية؟",
        "category": "philosophical",
        "language": "ar",
        "expected_path": "non-RAG (philosophy-lite)",
        "description": "Câu triết học về AI consciousness (tiếng Ả Rập)"
    },
    {
        "id": 10,
        "question": "Transformer là gì?",
        "category": "technical",
        "language": "vi",
        "expected_path": "RAG",
        "description": "Câu hỏi kỹ thuật đơn giản (tiếng Việt)"
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
                "success": not has_error,
                "is_fallback": is_fallback,
                "error_message": error_message,
                "answer": answer[:500] if answer else "",  # Truncate for logging
                "answer_length": len(answer) if answer else 0,
                "confidence": confidence,
                "response_time": response_time,
                "processing_steps": processing_steps,
                "token_info": token_info,
                "timing_logs": timing_logs
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

