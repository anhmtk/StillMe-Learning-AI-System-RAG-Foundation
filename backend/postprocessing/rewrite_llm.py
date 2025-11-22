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
        context_quality: str = None
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
            has_citations, num_ctx_docs, has_reliable_context, context_quality
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
                            rewritten = self._filter_forbidden_terms(rewritten)
                            
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
        context_quality: str = None
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
        base_knowledge_instruction = ""
        if not has_reliable_context or num_ctx_docs == 0:
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
        
        # Forbidden term replacements (case-insensitive)
        # CRITICAL: Use word boundaries and negative lookbehind to avoid false positives
        forbidden_replacements = [
            # "không tìm thấy" → "không có trong nguồn" or "không có thông tin"
            (r"(?<!không có )(?<!không )(?<!no )\bkhông tìm thấy\b", "không có trong nguồn"),
            (r"(?<!don't )(?<!do not )(?<!cannot )\bI don't find\b", "I don't have information"),
            (r"(?<!don't )(?<!do not )(?<!cannot )\bcannot find\b", "do not have information"),
            
            # "trải nghiệm cảm xúc" (positive) → "không có trải nghiệm cảm xúc"
            # BUT: "không có trải nghiệm cảm xúc" is OK - we need to be careful
            # Pattern: "có trải nghiệm cảm xúc" or "trải nghiệm cảm xúc" (without "không có" before it)
            # CRITICAL: Also catch "emotion-experiencing (trải nghiệm cảm xúc)" pattern
            (r"(?<!không có )(?<!không )(?<!no )(?<!not )\btrải nghiệm cảm xúc\b", "không có trải nghiệm cảm xúc"),
            (r"(?<!don't have )(?<!no )(?<!without )\bemotional experience\b", "do not have emotional experience"),
            (r"emotion-experiencing\s*\([^)]*trải nghiệm cảm xúc[^)]*\)", "emotion-labeling (gán nhãn cảm xúc, không phải trải nghiệm)"),
            
            # "có trải nghiệm" (positive) → "không có trải nghiệm"
            (r"(?<!không )(?<!no )\bcó trải nghiệm\b", "không có trải nghiệm"),
            (r"(?<!don't )(?<!do not )(?<!no )\bhave experience\b", "do not have experience"),
            (r"(?<!don't )(?<!do not )(?<!no )\bhave subjective experience\b", "do not have subjective experience"),
            
            # "cảm thấy" → "không cảm thấy" (if used positively)
            # BUT: "không cảm thấy" is OK
            (r"(?<!không )(?<!don't )(?<!do not )\bcảm thấy\b", "không cảm thấy"),
            (r"(?<!don't )(?<!do not )(?<!cannot )\bfeel\b", "do not feel"),
        ]
        
        result = text
        for pattern, replacement in forbidden_replacements:
            # Use case-insensitive replacement
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        
        return result


def get_rewrite_llm() -> RewriteLLM:
    """Get singleton instance of RewriteLLM"""
    if not hasattr(get_rewrite_llm, '_instance'):
        get_rewrite_llm._instance = RewriteLLM()
    return get_rewrite_llm._instance

