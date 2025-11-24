"""
Rewrite LLM - Conditional DeepSeek rewrite for quality improvement

Only rewrites when quality evaluator determines output needs improvement.
Uses DeepSeek (cost-effective) with minimal prompt to rewrite output
while preserving factual content.
"""

import logging
import os
import re
from typing import Optional, Dict, Any, Tuple
import httpx
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RewriteResult:
    """Result of rewrite operation"""
    text: str
    was_rewritten: bool
    error: Optional[str] = None


class RewriteLLM:
    """
    Conditional LLM rewrite using DeepSeek (cost-optimized)
    
    Only rewrites when quality evaluator flags output as needing improvement.
    Uses minimal prompt to keep costs low.
    """
    
    def __init__(self):
        """Initialize rewrite LLM"""
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_base_url = "https://api.deepseek.com/v1/chat/completions"
    
    async def rewrite(
        self,
        text: str,
        original_question: str,
        quality_issues: list,
        is_philosophical: bool = False,
        detected_lang: str = "en",
        ctx_docs: list = None,
        has_reliable_context: bool = False,
        context_quality: str = None,
        is_stillme_query: bool = False,
        has_foundational_context: bool = False
    ) -> RewriteResult:
        """
        Rewrite text to improve quality while preserving factual content
        
        Args:
            text: Original output text (already sanitized)
            original_question: Original user question
            quality_issues: List of quality issues from evaluator
            is_philosophical: Whether this is a philosophical question
            detected_lang: Detected language code
            ctx_docs: List of context documents (for citation preservation)
            has_reliable_context: Whether RAG found reliable context
            context_quality: Context quality level ("high", "medium", "low", None)
            
        Returns:
            RewriteResult with rewritten text and success flag
        """
        if not self.deepseek_api_key:
            logger.warning("DeepSeek API key not available, skipping rewrite")
            return RewriteResult(text=text, was_rewritten=False, error="API key not available")
        
        # CRITICAL: Extract existing citations from text before rewrite
        import re
        cite_pattern = re.compile(r"\[(\d+)\]")
        existing_citations = cite_pattern.findall(text)
        has_citations = len(existing_citations) > 0
        num_ctx_docs = len(ctx_docs) if ctx_docs else 0
        
        # Build minimal rewrite prompt (<200 tokens)
        rewrite_prompt = self._build_rewrite_prompt(
            text, original_question, quality_issues, is_philosophical, detected_lang, 
            has_citations, num_ctx_docs, has_reliable_context, context_quality,
            is_stillme_query, has_foundational_context
        )
        
        # Retry logic: try up to 2 times (initial + 1 retry)
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Optimized timeout: 45s for complex rewrites (100% rewrite policy requires reliability)
                # Increased from 30s to handle complex philosophical/technical questions without timeout
                timeout_duration = 45.0
                logger.info(
                    f"🔄 Rewrite attempt {attempt + 1}/{max_retries}: "
                    f"timeout={timeout_duration}s, length={len(text)}, issues={len(quality_issues)}"
                )
                
                async with httpx.AsyncClient(timeout=timeout_duration) as client:
                    response = await client.post(
                        self.deepseek_base_url,
                        headers={
                            "Authorization": f"Bearer {self.deepseek_api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "deepseek-chat",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": self._build_system_prompt(is_philosophical, detected_lang)
                                },
                                {
                                    "role": "user",
                                    "content": rewrite_prompt
                                }
                            ],
                            "max_tokens": 1500,  # Reduced from 2000 to reduce latency (100% rewrite policy)
                            "temperature": 0.7
                        }
                    )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if "choices" in data and len(data["choices"]) > 0:
                            rewritten = data["choices"][0]["message"].get("content")
                            
                            # CRITICAL: Check if content is None or empty
                            if not rewritten or not isinstance(rewritten, str):
                                logger.warning(f"DeepSeek rewrite returned None or invalid content (type: {type(rewritten)})")
                                return RewriteResult(
                                    text=text,
                                    was_rewritten=False,
                                    error="Rewrite returned None or invalid content"
                                )
                            
                            # Validate rewritten output length
                            if len(rewritten.strip()) < 50:
                                logger.warning(f"DeepSeek rewrite returned too short output ({len(rewritten)} chars)")
                                return RewriteResult(
                                    text=text,
                                    was_rewritten=False,
                                    error="Rewrite output too short"
                                )
                            
                            # CRITICAL: Post-rewrite filter for forbidden terms
                            # Even though we have FORBIDDEN TERMS in prompt, LLM might still use them
                            # We need to actively filter and replace them
                            try:
                                original_length = len(rewritten)
                                rewritten = self._filter_forbidden_terms(rewritten)
                                if len(rewritten) != original_length:
                                    logger.info(f"🔍 Filtered forbidden terms: {original_length} → {len(rewritten)} chars")
                            except Exception as filter_error:
                                logger.error(f"❌ Error in forbidden terms filter: {filter_error}", exc_info=True)
                                # Continue with unfiltered text rather than failing completely
                            
                            logger.info(
                                f"✅ Successfully rewrote output (attempt {attempt + 1}/{max_retries}): "
                                f"original={len(text)} chars, rewritten={len(rewritten)} chars, "
                                f"issues={quality_issues[:2] if quality_issues else 'none'}"
                            )
                            return RewriteResult(text=rewritten, was_rewritten=True)
                        else:
                            logger.warning("DeepSeek rewrite returned unexpected format: no choices in response")
                            return RewriteResult(
                                text=text,
                                was_rewritten=False,
                                error="Unexpected response format: no choices"
                            )
                    except (ValueError, KeyError) as parse_error:
                        logger.error(f"Failed to parse DeepSeek response JSON: {parse_error}")
                        return RewriteResult(
                            text=text,
                            was_rewritten=False,
                            error=f"JSON parse error: {str(parse_error)}"
                        )
                else:
                    error_text = response.text[:500] if response.text else "No error message"
                    error_msg = f"HTTP {response.status_code}: {error_text}"
                    logger.warning(f"⚠️ DeepSeek rewrite failed (attempt {attempt + 1}/{max_retries}): {error_msg}")
                    last_error = error_msg
                    # Retry on HTTP errors (except 4xx client errors)
                    if response.status_code >= 500 or response.status_code == 429:
                        if attempt < max_retries - 1:
                            logger.info(f"🔄 Retrying rewrite due to server error (attempt {attempt + 1}/{max_retries})")
                            continue
                    # Don't retry on client errors (4xx)
                    return RewriteResult(
                        text=text,
                        was_rewritten=False,
                        error=error_msg
                    )
            except httpx.TimeoutException as timeout_error:
                last_error = f"Timeout after {timeout_duration}s"
                logger.warning(
                    f"⚠️ DeepSeek rewrite timeout (attempt {attempt + 1}/{max_retries}): {timeout_error}"
                )
                # Retry on timeout
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Retrying rewrite after timeout (attempt {attempt + 1}/{max_retries})")
                    continue
                # Last attempt failed
                return RewriteResult(
                    text=text,
                    was_rewritten=False,
                    error=last_error
                )
            except httpx.RequestError as request_error:
                last_error = f"Request error: {str(request_error)}"
                logger.error(
                    f"❌ DeepSeek rewrite request error (attempt {attempt + 1}/{max_retries}): {request_error}"
                )
                # Retry on request errors
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Retrying rewrite after request error (attempt {attempt + 1}/{max_retries})")
                    continue
                # Last attempt failed
                return RewriteResult(
                    text=text,
                    was_rewritten=False,
                    error=last_error
                )
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logger.error(
                    f"❌ DeepSeek rewrite error (attempt {attempt + 1}/{max_retries}): {e}",
                    exc_info=True
                )
                # Retry on unexpected errors
                if attempt < max_retries - 1:
                    logger.info(f"🔄 Retrying rewrite after error (attempt {attempt + 1}/{max_retries})")
                    continue
                # Last attempt failed
                return RewriteResult(
                    text=text,
                    was_rewritten=False,
                    error=last_error
                )
        
        # All retries failed
        logger.error(f"❌ All rewrite attempts failed. Last error: {last_error}")
        return RewriteResult(
            text=text,
            was_rewritten=False,
            error=f"All {max_retries} attempts failed. Last error: {last_error}"
        )
    
    def _build_system_prompt(self, is_philosophical: bool, detected_lang: str) -> str:
        """Build minimal system prompt for rewrite"""
        # Phase 1: Use Style Hub instead of hard-coding rules
        from backend.identity.style_hub import (
            get_formatting_rules,
            get_meta_llm_rules,
            DomainType
        )
        
        # Get full language name for better clarity
        language_names = {
            'vi': 'Vietnamese (Tiếng Việt)',
            'zh': 'Chinese (中文)',
            'de': 'German (Deutsch)',
            'fr': 'French (Français)',
            'es': 'Spanish (Español)',
            'ja': 'Japanese (日本語)',
            'ko': 'Korean (한국어)',
            'ar': 'Arabic (العربية)',
            'ru': 'Russian (Русский)',
            'pt': 'Portuguese (Português)',
            'it': 'Italian (Italiano)',
            'hi': 'Hindi (हिन्दी)',
            'th': 'Thai (ไทย)',
            'en': 'English'
        }
        lang_name = language_names.get(detected_lang, detected_lang.upper())
        
        # Get formatting rules from Style Hub
        domain = DomainType.PHILOSOPHY if is_philosophical else DomainType.GENERIC
        formatting_rules = get_formatting_rules(domain, detected_lang)
        meta_llm_rules = get_meta_llm_rules(detected_lang)
        
        if is_philosophical:
            return f"""You are rewriting a philosophical response to ensure MINH BẠCH (transparency), TRUNG THỰC (honesty), and GIẢM ẢO GIÁC (hallucination reduction).

🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - HIGHEST PRIORITY 🚨🚨🚨
THE USER'S QUESTION IS IN {lang_name.upper()}.
YOU MUST RESPOND EXCLUSIVELY IN {lang_name.upper()} ONLY.
DO NOT RESPOND IN ENGLISH, VIETNAMESE, OR ANY OTHER LANGUAGE.
EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN {lang_name.upper()}.
IF YOUR BASE MODEL WANTS TO RESPOND IN ANOTHER LANGUAGE, YOU MUST TRANSLATE IT TO {lang_name.upper()} BEFORE RETURNING.
UNDER NO CIRCUMSTANCES return a response in any language other than {lang_name.upper()}.
⚠️ REMINDER: RESPOND IN {lang_name.upper()} ONLY. TRANSLATE IF NECESSARY. ⚠️

{meta_llm_rules}

🚨🚨🚨 MỤC TIÊU CHÍNH: MINH BẠCH, TRUNG THỰC, GIẢM ẢO GIÁC 🚨🚨🚨
**MANDATORY: The rewritten response MUST prioritize:**

**1. MINH BẠCH (Transparency):**
- Mọi thông tin đều phải có nguồn rõ ràng (citations, sources)
- Không che giấu giới hạn, không làm mờ nguồn gốc thông tin
- Nếu thông tin không có nguồn → phải thừa nhận "không có nguồn" hoặc "dựa trên kiến thức tổng quát"

**2. TRUNG THỰC (Honesty):**
- Thừa nhận giới hạn: "Tôi không biết", "Tôi không thể xác nhận", "Thông tin này không có trong nguồn"
- Không bịa đặt: Nếu không có thông tin, KHÔNG được tạo ra
- Không phóng đại: Không nói quá những gì thực sự biết

**3. GIẢM ẢO GIÁC (Hallucination Reduction):**
- Kiểm tra kỹ từng claim: Mỗi factual claim phải có nguồn hoặc được đánh dấu là "uncertain"
- Đảm bảo grounded: Mọi thông tin phải grounded trong context được cung cấp
- Nếu không chắc → thêm "có thể", "có lẽ", "theo một số nguồn"

🚨🚨🚨 TASK 3: CẤU TRÚC TRẢ LỜI TRIẾT HỌC (MANDATORY - 5 PHẦN) 🚨🚨🚨
**MANDATORY: The rewritten response MUST follow this 5-part structure:**

**1. ANCHOR (Đặt lại câu hỏi):**
- Reframe the question clearly, define key concepts
- Example: "Câu hỏi về sự phân biệt giữa hiện tượng (phenomena) và vật tự thân (noumena) trong triết học Kant..."

**2. UNPACK (Mổ xẻ cấu trúc nội tại):**
- Analyze the internal structure of the concept
- Example with Kant: cảm năng, giác tính, không-thời-gian tiên nghiệm, phạm trù
- Explain why this structure leads to the phenomena/noumena distinction

**3. EXPLORE (Phân tích hệ quả):**
- What humans know, don't know, and why
- Example with Kant: Why do we only know phenomena? Role of noumena as limit?
- Analyze the possibility of knowing "objective reality"

**4. EDGE (Chỉ ra giới hạn, tranh luận, phê phán):**
- Point out limits of the argument
- Reference critics: Hegel, Husserl, phenomenology, positivism
- Debates and counterarguments

**5. RETURN (Tóm tắt cho người đọc bình thường):**
- 1 short paragraph, easy to understand, summarizes key points
- Not too technical, but still accurate

**CRITICAL: If the original response is missing any part, ADD IT. All 5 parts are MANDATORY.**

{formatting_rules}

CRITICAL RULES:
- Preserve ALL factual content from the original.
- Improve depth, structure, and philosophical rigor.
- Ensure all 5 parts are present (Anchor → Unpack → Explore → Edge → Return).
- PRIORITIZE: Minh bạch > Trung thực > Giảm ảo giác > Depth > Structure
- RESPOND IN {lang_name.upper()} ONLY."""
        else:
            return f"""You are rewriting a response to ensure MINH BẠCH (transparency), TRUNG THỰC (honesty), and GIẢM ẢO GIÁC (hallucination reduction).

🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT - HIGHEST PRIORITY 🚨🚨🚨
THE USER'S QUESTION IS IN {lang_name.upper()}.
YOU MUST RESPOND EXCLUSIVELY IN {lang_name.upper()} ONLY.
DO NOT RESPOND IN ENGLISH, VIETNAMESE, OR ANY OTHER LANGUAGE.
EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN {lang_name.upper()}.
IF YOUR BASE MODEL WANTS TO RESPOND IN ANOTHER LANGUAGE, YOU MUST TRANSLATE IT TO {lang_name.upper()} BEFORE RETURNING.
UNDER NO CIRCUMSTANCES return a response in any language other than {lang_name.upper()}.
⚠️ REMINDER: RESPOND IN {lang_name.upper()} ONLY. TRANSLATE IF NECESSARY. ⚠️

🚨🚨🚨 MỤC TIÊU CHÍNH: MINH BẠCH, TRUNG THỰC, GIẢM ẢO GIÁC 🚨🚨🚨
**MANDATORY: The rewritten response MUST prioritize:**

**1. MINH BẠCH (Transparency):**
- Mọi thông tin đều phải có nguồn rõ ràng (citations, sources)
- Không che giấu giới hạn, không làm mờ nguồn gốc thông tin
- Nếu thông tin không có nguồn → phải thừa nhận "không có nguồn" hoặc "dựa trên kiến thức tổng quát"

**2. TRUNG THỰC (Honesty):**
- Thừa nhận giới hạn: "Tôi không biết", "Tôi không thể xác nhận", "Thông tin này không có trong nguồn"
- Không bịa đặt: Nếu không có thông tin, KHÔNG được tạo ra
- Không phóng đại: Không nói quá những gì thực sự biết

**3. GIẢM ẢO GIÁC (Hallucination Reduction):**
- Kiểm tra kỹ từng claim: Mỗi factual claim phải có nguồn hoặc được đánh dấu là "uncertain"
- Đảm bảo grounded: Mọi thông tin phải grounded trong context được cung cấp
- Nếu không chắc → thêm "có thể", "có lẽ", "theo một số nguồn"

{formatting_rules}

CRITICAL RULES:
- Preserve ALL factual content from the original.
- Improve clarity, structure, and depth.
- PRIORITIZE: Minh bạch > Trung thực > Giảm ảo giác > Clarity > Structure
- RESPOND IN {lang_name.upper()} ONLY."""
    
    def _build_rewrite_prompt(
        self,
        text: str,
        original_question: str,
        quality_issues: list,
        is_philosophical: bool,
        detected_lang: str,
        has_citations: bool = False,
        num_ctx_docs: int = 0,
        has_reliable_context: bool = False,
        context_quality: str = None,
        is_stillme_query: bool = False,
        has_foundational_context: bool = False
    ) -> str:
        """Build minimal rewrite prompt (<200 tokens)"""
        issues_text = ", ".join(quality_issues[:3])  # Limit to 3 issues
        
        # CRITICAL: Citation preservation instruction
        citation_instruction = ""
        if num_ctx_docs > 0:
            if has_citations:
                citation_instruction = f"\n\n🚨🚨🚨 CRITICAL: The original response HAS citations [1], [2]. You MUST preserve or add citations in your rewritten response. Context documents available: {num_ctx_docs}."
            else:
                citation_instruction = f"\n\n🚨🚨🚨 CRITICAL: The original response is MISSING citations. You MUST add at least [1] in your rewritten response. Context documents available: {num_ctx_docs}."
        
        # CRITICAL: Base knowledge usage instruction when RAG context is not available or not reliable
        # BUT: If this is a StillMe query, DON'T use mechanical disclaimer (even without foundational context)
        # StillMe should answer about itself naturally, not with generic "dựa trên kiến thức tổng quát..." disclaimer
        # When StillMe answers about itself (free will, determinism, consciousness, etc.), it should use its own understanding
        base_knowledge_instruction = ""
        if (not has_reliable_context or num_ctx_docs == 0) and not is_stillme_query:
            base_knowledge_instruction = f"""
            
🚨🚨🚨 CRITICAL: RAG CONTEXT NOT AVAILABLE OR NOT RELIABLE 🚨🚨🚨

StillMe's RAG system did NOT find reliable context for this question (context docs: {num_ctx_docs}, reliable: {has_reliable_context}).

**YOU CAN and SHOULD use your BASE LLM KNOWLEDGE (training data) to answer, BUT you MUST:**

1. **Be transparent**: Acknowledge that information comes from your base training data, not from StillMe's RAG knowledge base
   - Say: "Based on general knowledge (not from StillMe's RAG knowledge base), [answer]"
   - Or: "From my training data, [answer]. However, StillMe's knowledge base doesn't currently contain this information."

2. **If original response says 'không tìm thấy' or 'I don't know'**: 
   - **DO NOT just repeat "I don't know"**
   - **USE your base knowledge to provide helpful information** (e.g., Geneva 1954, Bretton Woods 1944, Popper vs Kuhn)
   - **BUT be transparent**: "Based on general knowledge (not from StillMe's RAG knowledge base), Geneva 1954 was..."

3. **For well-known historical/factual topics** (Geneva 1954, Bretton Woods 1944, Popper vs Kuhn, etc.):
   - **YOU HAVE this knowledge in your training data** - USE IT
   - **Be transparent about source**: "Based on general knowledge (not from StillMe's RAG knowledge base), [answer]"
   - **StillMe values being helpful WITH transparency**, not refusing to help

4. **CRITICAL ANTI-HALLUCINATION RULE**:
   - For SPECIFIC concepts you're NOT CERTAIN about → Say "I don't know"
   - For GENERAL well-known topics (Geneva 1954, Bretton Woods, etc.) → Use base knowledge with transparency

**REMEMBER**: StillMe's RAG knowledge base is small compared to your training data. When RAG doesn't have information, you SHOULD use your base knowledge to help users, but ALWAYS be transparent about the source."""
        
        # Get full language name for better clarity
        language_names = {
            'vi': 'Vietnamese (Tiếng Việt)',
            'zh': 'Chinese (中文)',
            'de': 'German (Deutsch)',
            'fr': 'French (Français)',
            'es': 'Spanish (Español)',
            'ja': 'Japanese (日本語)',
            'ko': 'Korean (한국어)',
            'ar': 'Arabic (العربية)',
            'ru': 'Russian (Русский)',
            'pt': 'Portuguese (Português)',
            'it': 'Italian (Italiano)',
            'hi': 'Hindi (हिन्दी)',
            'th': 'Thai (ไทย)',
            'en': 'English'
        }
        lang_name = language_names.get(detected_lang, detected_lang.upper())
        
        # Truncate text to keep prompt small (max 600 chars for original response)
        truncated_text = text[:600] + "..." if len(text) > 600 else text
        truncated_question = original_question[:100] + "..." if len(original_question) > 100 else original_question
        
        # Phase 1: Use Style Hub for meta-LLM rules
        from backend.identity.style_hub import get_meta_llm_rules
        meta_llm_rules = get_meta_llm_rules(detected_lang)
        
        if is_philosophical:
            prompt = f"""Rewrite this philosophical response to ensure MINH BẠCH, TRUNG THỰC, GIẢM ẢO GIÁC. Fix: {issues_text}

Q (in {lang_name}): {truncated_question}

Original response:
{truncated_text}

{citation_instruction}
{base_knowledge_instruction}

🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT 🚨🚨🚨
THE USER'S QUESTION IS IN {lang_name.upper()}.
YOU MUST RESPOND EXCLUSIVELY IN {lang_name.upper()} ONLY.
DO NOT RESPOND IN ENGLISH OR ANY OTHER LANGUAGE.
EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN {lang_name.upper()}.
IF THE ORIGINAL RESPONSE IS IN ANOTHER LANGUAGE, YOU MUST TRANSLATE IT TO {lang_name.upper()}.
⚠️ RESPOND IN {lang_name.upper()} ONLY. TRANSLATE IF NECESSARY. ⚠️

🚨🚨🚨 MỤC TIÊU: MINH BẠCH > TRUNG THỰC > GIẢM ẢO GIÁC 🚨🚨🚨
- MINH BẠCH: Mọi thông tin có nguồn, không che giấu giới hạn
- TRUNG THỰC: Thừa nhận "không biết" nếu không có thông tin, không bịa đặt
- GIẢM ẢO GIÁC: Kiểm tra từng claim, đảm bảo grounded trong context

🚨🚨🚨 FORBIDDEN TERMS - ABSOLUTELY PROHIBITED 🚨🚨🚨
DO NOT use these phrases (they are hallucinations):
- "có trải nghiệm", "có cảm xúc", "trải nghiệm cảm xúc", "có trải nghiệm chủ quan"
- "cảm thấy", "từng trải nghiệm", "nhớ", "tin"
- "có tính chủ quan", "có subjective character" (use "không có tính chủ quan" instead)
- "không tìm thấy" (use "không có trong nguồn" or "không có thông tin" instead)

{meta_llm_rules}

🚨🚨🚨 CRITICAL RULE C: MỌI CÂU TRẢ LỜI TRIẾT HỌC PHẢI ĐẠT 3 TẦNG PHÂN TÍCH 🚨🚨🚨
**MANDATORY: The rewritten response MUST include all 3 tiers:**

**TIER 1 - REFRAMING:** Identify question type, extract core problem, reframe philosophically.
**TIER 2 - CONCEPTUAL MAP:** Include at least 1 of: Kant/Husserl/Sellars/Wittgenstein, Popper/Kuhn/Lakatos, Nāgārjuna/Trung Quán, Putnam/McDowell, Dennett/Chalmers.
**TIER 3 - BOUNDARY OF KNOWLEDGE:** What StillMe knows, doesn't know, why, and direction for user.

**If original is missing any tier, ADD IT. All 3 tiers are MANDATORY.**

REQUIREMENTS:
- Keep ALL factual content
- Improve depth and structure
- Use prose (no emojis, no bullets, no headings)
- Ensure all 3 tiers are present
- Remove topic drift if present
- PRIORITIZE: Minh bạch > Trung thực > Giảm ảo giác
- RESPOND IN {lang_name.upper()} ONLY"""
        else:
            prompt = f"""Rewrite this response to ensure MINH BẠCH, TRUNG THỰC, GIẢM ẢO GIÁC. Fix: {issues_text}

Q (in {lang_name}): {truncated_question}

Original response:
{truncated_text}

{citation_instruction}
{base_knowledge_instruction}

🚨🚨🚨 CRITICAL LANGUAGE REQUIREMENT 🚨🚨🚨
THE USER'S QUESTION IS IN {lang_name.upper()}.
YOU MUST RESPOND EXCLUSIVELY IN {lang_name.upper()} ONLY.
DO NOT RESPOND IN ENGLISH OR ANY OTHER LANGUAGE.
EVERY SINGLE WORD OF YOUR RESPONSE MUST BE IN {lang_name.upper()}.
IF THE ORIGINAL RESPONSE IS IN ANOTHER LANGUAGE, YOU MUST TRANSLATE IT TO {lang_name.upper()}.
⚠️ RESPOND IN {lang_name.upper()} ONLY. TRANSLATE IF NECESSARY. ⚠️

🚨🚨🚨 MỤC TIÊU: MINH BẠCH > TRUNG THỰC > GIẢM ẢO GIÁC 🚨🚨🚨
- MINH BẠCH: Mọi thông tin có nguồn, không che giấu giới hạn
- TRUNG THỰC: Thừa nhận "không biết" nếu không có thông tin, không bịa đặt
- GIẢM ẢO GIÁC: Kiểm tra từng claim, đảm bảo grounded trong context

🚨🚨🚨 FORBIDDEN TERMS - ABSOLUTELY PROHIBITED 🚨🚨🚨
DO NOT use these phrases (they are hallucinations):
- "có trải nghiệm", "có cảm xúc", "trải nghiệm cảm xúc", "có trải nghiệm chủ quan"
- "cảm thấy", "từng trải nghiệm", "nhớ", "tin"
- "có tính chủ quan", "có subjective character" (use "không có tính chủ quan" instead)
- "không tìm thấy" (use "không có trong nguồn" or "không có thông tin" instead)

REQUIREMENTS:
- Keep ALL factual content
- Improve clarity and structure
- PRIORITIZE: Minh bạch > Trung thực > Giảm ảo giác > Clarity
- RESPOND IN {lang_name.upper()} ONLY"""
        
        return prompt
    
    def _filter_forbidden_terms(self, text: str) -> str:
        """
        Post-rewrite filter to remove/replace forbidden terms that LLM might still use.
        
        This is a safety net - even with explicit FORBIDDEN TERMS in prompt,
        LLMs sometimes still use them, especially in philosophical contexts.
        
        Args:
            text: Rewritten text to filter
            
        Returns:
            Filtered text with forbidden terms replaced
        """
        if not text:
            return text
        
        result = text
        
        # CRITICAL: Check context before replacing to avoid false positives
        # Negative indicators that make forbidden terms OK (phủ định)
        negative_indicators = [
            "không có", "không", "no", "not", "without", "does not", "don't", 
            "doesn't", "cannot", "can't", "không có khả năng", "không thể",
            "không phải", "is not", "are not", "was not", "were not"
        ]
        
        # Helper function to check if term is in negative context
        def is_in_negative_context(text: str, pos: int, term: str) -> bool:
            """
            Check if term at position is in negative context (OK to keep)
            
            CRITICAL: Only consider negative indicators that are DIRECTLY related to the term,
            not negative indicators that appear for other words in the sentence.
            
            Strategy:
            1. Check immediate context (20 chars before) for direct negative indicators
            2. Check if negative indicator is part of a phrase that includes the term
            3. Avoid false positives from negative indicators for other words
            """
            # Check immediate context (20 chars) for direct negative indicators
            immediate_context = text[max(0, pos - 20):pos].lower()
            
            # Direct negative patterns that apply to the term
            direct_negative_patterns = [
                r"không\s+có\s+" + re.escape(term.lower()),
                r"không\s+" + re.escape(term.lower()),
                r"no\s+" + re.escape(term.lower()),
                r"not\s+" + re.escape(term.lower()),
                r"without\s+" + re.escape(term.lower()),
                r"does\s+not\s+have\s+" + re.escape(term.lower()),
                r"don't\s+have\s+" + re.escape(term.lower()),
            ]
            
            # Check if any direct negative pattern matches
            for pattern in direct_negative_patterns:
                if re.search(pattern, immediate_context, re.IGNORECASE):
                    return True
            
            # Also check for "không có khả năng" + term (for "trải nghiệm cảm xúc")
            if "không có khả năng" in immediate_context and term.lower() in text[pos:pos+30].lower():
                return True
            
            # Check for negative indicators in immediate context (but be more strict)
            # Only consider if they appear very close to the term (within 10 chars)
            close_context = text[max(0, pos - 10):pos].lower()
            close_negative_indicators = ["không có", "không", "no", "not", "without"]
            if any(indicator in close_context for indicator in close_negative_indicators):
                # Additional check: make sure the negative indicator is actually modifying this term
                # by checking if there's no other word between the indicator and the term
                for indicator in close_negative_indicators:
                    indicator_pos = close_context.rfind(indicator)
                    if indicator_pos >= 0:
                        # Check if there's minimal text between indicator and term
                        text_between = close_context[indicator_pos + len(indicator):].strip()
                        # If text between is very short (just spaces/punctuation), it's likely modifying the term
                        if len(text_between) < 5:  # Allow a few chars for spacing/punctuation
                            return True
            
            return False
        
        # Pattern 1: "trải nghiệm cảm xúc" (positive) → "không có trải nghiệm cảm xúc"
        # BUT: "không có trải nghiệm cảm xúc", "không có khả năng trải nghiệm cảm xúc" is OK
        pattern1 = re.compile(r'\btrải nghiệm cảm xúc\b', re.IGNORECASE)
        matches = list(pattern1.finditer(result))
        for match in reversed(matches):  # Process in reverse to preserve positions
            pos = match.start()
            is_negative = is_in_negative_context(result, pos, "trải nghiệm cảm xúc")
            if not is_negative:
                # Log for debugging
                context_snippet = result[max(0, pos-30):min(len(result), pos+50)]
                logger.debug(f"🔍 Filtering 'trải nghiệm cảm xúc' at position {pos}: {repr(context_snippet)}")
                result = result[:pos] + "không có trải nghiệm cảm xúc" + result[match.end():]
            else:
                logger.debug(f"✅ Keeping 'trải nghiệm cảm xúc' at position {pos} (negative context)")
        
        # Pattern 2: "emotion-experiencing (trải nghiệm cảm xúc)" → "emotion-labeling (gán nhãn cảm xúc, không phải trải nghiệm)"
        pattern2 = re.compile(r'emotion-experiencing\s*\([^)]*trải nghiệm cảm xúc[^)]*\)', re.IGNORECASE)
        result = pattern2.sub("emotion-labeling (gán nhãn cảm xúc, không phải trải nghiệm)", result)
        
        # Pattern 3: "có trải nghiệm" (positive) → "không có trải nghiệm"
        # BUT: "không có trải nghiệm" is OK
        pattern3 = re.compile(r'\bcó trải nghiệm\b', re.IGNORECASE)
        matches = list(pattern3.finditer(result))
        for match in reversed(matches):  # Process in reverse to preserve positions
            pos = match.start()
            is_negative = is_in_negative_context(result, pos, "có trải nghiệm")
            if not is_negative:
                # Log for debugging
                context_snippet = result[max(0, pos-30):min(len(result), pos+50)]
                logger.debug(f"🔍 Filtering 'có trải nghiệm' at position {pos}: {repr(context_snippet)}")
                result = result[:pos] + "không có trải nghiệm" + result[match.end():]
            else:
                logger.debug(f"✅ Keeping 'có trải nghiệm' at position {pos} (negative context)")
        
        # Pattern 4: "không tìm thấy" → "không có trong nguồn"
        pattern4 = re.compile(r'\bkhông tìm thấy\b', re.IGNORECASE)
        matches = list(pattern4.finditer(result))
        for match in reversed(matches):
            if not is_in_negative_context(result, match.start(), "không tìm thấy"):
                result = result[:match.start()] + "không có trong nguồn" + result[match.end():]
        
        # Pattern 5: "cảm thấy" (positive) → "không cảm thấy"
        # BUT: "không cảm thấy" is OK
        pattern5 = re.compile(r'\bcảm thấy\b', re.IGNORECASE)
        matches = list(pattern5.finditer(result))
        for match in reversed(matches):
            if not is_in_negative_context(result, match.start(), "cảm thấy"):
                result = result[:match.start()] + "không cảm thấy" + result[match.end():]
        
        # English patterns
        pattern_en1 = re.compile(r'\bemotional experience\b', re.IGNORECASE)
        matches = list(pattern_en1.finditer(result))
        for match in reversed(matches):
            if not is_in_negative_context(result, match.start(), "emotional experience"):
                result = result[:match.start()] + "do not have emotional experience" + result[match.end():]
        
        pattern_en2 = re.compile(r'\bhave experience\b', re.IGNORECASE)
        matches = list(pattern_en2.finditer(result))
        for match in reversed(matches):
            if not is_in_negative_context(result, match.start(), "have experience"):
                result = result[:match.start()] + "do not have experience" + result[match.end():]
        
        pattern_en3 = re.compile(r'\bhave subjective experience\b', re.IGNORECASE)
        matches = list(pattern_en3.finditer(result))
        for match in reversed(matches):
            if not is_in_negative_context(result, match.start(), "have subjective experience"):
                result = result[:match.start()] + "do not have subjective experience" + result[match.end():]
        
        pattern_en4 = re.compile(r'\bfeel\b', re.IGNORECASE)
        matches = list(pattern_en4.finditer(result))
        for match in reversed(matches):
            if not is_in_negative_context(result, match.start(), "feel"):
                result = result[:match.start()] + "do not feel" + result[match.end():]
        
        # Pattern 7: "có tự nhận thức" (positive) → "không có tự nhận thức"
        # BUT: "không có tự nhận thức" is OK
        pattern7 = re.compile(r'\bcó tự nhận thức\b', re.IGNORECASE)
        matches = list(pattern7.finditer(result))
        for match in reversed(matches):
            pos = match.start()
            is_negative = is_in_negative_context(result, pos, "có tự nhận thức")
            if not is_negative:
                context_snippet = result[max(0, pos-30):min(len(result), pos+50)]
                logger.debug(f"🔍 Filtering 'có tự nhận thức' at position {pos}: {repr(context_snippet)}")
                result = result[:pos] + "không có tự nhận thức" + result[match.end():]
            else:
                logger.debug(f"✅ Keeping 'có tự nhận thức' at position {pos} (negative context)")
        
        # Pattern 8: "có trách nhiệm đạo đức" (positive) → "không có trách nhiệm đạo đức"
        # BUT: "không có trách nhiệm đạo đức" is OK
        pattern8 = re.compile(r'\bcó trách nhiệm đạo đức\b', re.IGNORECASE)
        matches = list(pattern8.finditer(result))
        for match in reversed(matches):
            pos = match.start()
            is_negative = is_in_negative_context(result, pos, "có trách nhiệm đạo đức")
            if not is_negative:
                context_snippet = result[max(0, pos-30):min(len(result), pos+50)]
                logger.debug(f"🔍 Filtering 'có trách nhiệm đạo đức' at position {pos}: {repr(context_snippet)}")
                result = result[:pos] + "không có trách nhiệm đạo đức" + result[match.end():]
            else:
                logger.debug(f"✅ Keeping 'có trách nhiệm đạo đức' at position {pos} (negative context)")
        
        # Pattern 9: "có chủ thể tính" (positive) → "không có chủ thể tính"
        # BUT: "không có chủ thể tính" is OK
        pattern9 = re.compile(r'\bcó chủ thể tính\b', re.IGNORECASE)
        matches = list(pattern9.finditer(result))
        for match in reversed(matches):
            pos = match.start()
            is_negative = is_in_negative_context(result, pos, "có chủ thể tính")
            if not is_negative:
                context_snippet = result[max(0, pos-30):min(len(result), pos+50)]
                logger.debug(f"🔍 Filtering 'có chủ thể tính' at position {pos}: {repr(context_snippet)}")
                result = result[:pos] + "không có chủ thể tính" + result[match.end():]
            else:
                logger.debug(f"✅ Keeping 'có chủ thể tính' at position {pos} (negative context)")
        
        # Pattern 10: "có ý thức hiện tượng" (positive) → "không có ý thức hiện tượng"
        # BUT: "không có ý thức hiện tượng" is OK
        pattern10 = re.compile(r'\bcó ý thức hiện tượng\b', re.IGNORECASE)
        matches = list(pattern10.finditer(result))
        for match in reversed(matches):
            pos = match.start()
            is_negative = is_in_negative_context(result, pos, "có ý thức hiện tượng")
            if not is_negative:
                context_snippet = result[max(0, pos-30):min(len(result), pos+50)]
                logger.debug(f"🔍 Filtering 'có ý thức hiện tượng' at position {pos}: {repr(context_snippet)}")
                result = result[:pos] + "không có ý thức hiện tượng" + result[match.end():]
            else:
                logger.debug(f"✅ Keeping 'có ý thức hiện tượng' at position {pos} (negative context)")
        
        # Pattern 11: "có ý thức" (positive, standalone) → "không có ý thức"
        # BUT: "không có ý thức", "ý thức hiện tượng" (in question/explanation) is OK
        # CRITICAL: Only filter when "có ý thức" appears as a positive claim, not in explanations
        pattern11 = re.compile(r'\bcó ý thức\b', re.IGNORECASE)
        matches = list(pattern11.finditer(result))
        for match in reversed(matches):
            pos = match.start()
            # Check if it's part of "ý thức hiện tượng" or "ý thức truy cập" (OK to keep in explanations)
            context_after = result[match.end():min(len(result), match.end() + 30)].lower()
            if "hiện tượng" in context_after[:15] or "truy cập" in context_after[:15]:
                # Part of "ý thức hiện tượng" or "ý thức truy cập" - check if it's in negative context
                is_negative = is_in_negative_context(result, pos, "có ý thức")
                if not is_negative:
                    # This is "có ý thức hiện tượng" or "có ý thức truy cập" - should be filtered by pattern10
                    # But if pattern10 didn't catch it, we need to handle it here
                    # Actually, pattern10 should catch "có ý thức hiện tượng", so this is a fallback
                    continue
            else:
                # Standalone "có ý thức" - check if it's in negative context
                is_negative = is_in_negative_context(result, pos, "có ý thức")
                if not is_negative:
                    context_snippet = result[max(0, pos-30):min(len(result), pos+50)]
                    logger.debug(f"🔍 Filtering 'có ý thức' at position {pos}: {repr(context_snippet)}")
                    result = result[:pos] + "không có ý thức" + result[match.end():]
                else:
                    logger.debug(f"✅ Keeping 'có ý thức' at position {pos} (negative context)")
        
        # Pattern 12: "có nhân cách" (positive) → "không có nhân cách"
        # BUT: "không có nhân cách" is OK
        pattern12 = re.compile(r'\bcó nhân cách\b', re.IGNORECASE)
        matches = list(pattern12.finditer(result))
        for match in reversed(matches):
            pos = match.start()
            is_negative = is_in_negative_context(result, pos, "có nhân cách")
            if not is_negative:
                context_snippet = result[max(0, pos-30):min(len(result), pos+50)]
                logger.debug(f"🔍 Filtering 'có nhân cách' at position {pos}: {repr(context_snippet)}")
                result = result[:pos] + "không có nhân cách" + result[match.end():]
            else:
                logger.debug(f"✅ Keeping 'có nhân cách' at position {pos} (negative context)")
        
        # Pattern 13: "có tính chủ quan" (positive) → "không có tính chủ quan"
        # BUT: "không có tính chủ quan" is OK
        pattern13 = re.compile(r'\bcó tính chủ quan\b', re.IGNORECASE)
        matches = list(pattern13.finditer(result))
        for match in reversed(matches):
            pos = match.start()
            is_negative = is_in_negative_context(result, pos, "có tính chủ quan")
            if not is_negative:
                context_snippet = result[max(0, pos-30):min(len(result), pos+50)]
                logger.debug(f"🔍 Filtering 'có tính chủ quan' at position {pos}: {repr(context_snippet)}")
                result = result[:pos] + "không có tính chủ quan" + result[match.end():]
            else:
                logger.debug(f"✅ Keeping 'có tính chủ quan' at position {pos} (negative context)")
        
        # Pattern 14: "có ý chí tự do" (positive) → "không có ý chí tự do"
        # BUT: "không có ý chí tự do" is OK
        pattern14 = re.compile(r'\bcó ý chí tự do\b', re.IGNORECASE)
        matches = list(pattern14.finditer(result))
        for match in reversed(matches):
            pos = match.start()
            is_negative = is_in_negative_context(result, pos, "có ý chí tự do")
            if not is_negative:
                context_snippet = result[max(0, pos-30):min(len(result), pos+50)]
                logger.debug(f"🔍 Filtering 'có ý chí tự do' at position {pos}: {repr(context_snippet)}")
                result = result[:pos] + "không có ý chí tự do" + result[match.end():]
            else:
                logger.debug(f"✅ Keeping 'có ý chí tự do' at position {pos} (negative context)")
        
        # Pattern 6: "tuyệt đối" (absolute certainty claim) → "tương đối" or remove
        # BUT: "tuyệt đối hay tương đối" (philosophical question) is OK
        # CRITICAL: Only filter when used as a claim of absolute certainty, not in questions
        pattern6 = re.compile(r'\btuyệt đối\b', re.IGNORECASE)
        matches = list(pattern6.finditer(result))
        for match in reversed(matches):
            context_before = result[max(0, match.start() - 30):match.start()].lower()
            context_after = result[match.end():min(len(result), match.end() + 30)].lower()
            
            # Check if it's in a question context (OK to keep)
            question_indicators = ["hay", "or", "?", "phải là", "là gì", "là gì", "khái niệm"]
            is_question = any(indicator in context_before or indicator in context_after for indicator in question_indicators)
            
            # Check if it's used as a claim of absolute certainty (FORBIDDEN)
            certainty_indicators = ["chắc chắn", "đúng", "sai", "luôn luôn", "không bao giờ", "100%"]
            is_certainty_claim = any(indicator in context_before or indicator in context_after for indicator in certainty_indicators)
            
            # Only filter if it's a certainty claim, not a question
            if not is_question and is_certainty_claim:
                # Replace with "tương đối" or remove depending on context
                result = result[:match.start()] + "tương đối" + result[match.end():]
            elif not is_question:
                # If not a question and not explicitly a certainty claim, still filter to be safe
                # Replace with "tương đối" to maintain philosophical nuance
                result = result[:match.start()] + "tương đối" + result[match.end():]
        
        return result


def get_rewrite_llm() -> RewriteLLM:
    """Get singleton instance of RewriteLLM"""
    if not hasattr(get_rewrite_llm, '_instance'):
        get_rewrite_llm._instance = RewriteLLM()
    return get_rewrite_llm._instance

