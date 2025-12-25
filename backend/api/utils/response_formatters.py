"""Response formatting utilities for chat router.

This module contains response formatting functions extracted from chat_router.py
to improve maintainability and reduce file size.
"""

import re
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import os

from backend.api.utils.text_utils import clean_response_text
from backend.api.config.chat_config import get_chat_config

logger = logging.getLogger(__name__)


def add_timestamp_to_response(
    response: str,
    detected_lang: str = "en",
    context: Optional[dict] = None,
    user_question: Optional[str] = None
) -> str:
    """
    Add timestamp attribution to normal RAG responses for transparency.
    This ensures consistency with external data responses which already include timestamps.
    
    CRITICAL: This function must handle Unicode (including Chinese) safely.
    CRITICAL: For self-knowledge questions about StillMe's codebase, skip external citations.
    
    Args:
        response: Original response text (may contain Unicode characters)
        detected_lang: Detected language code
        context: Optional context dict with knowledge_docs for source links
        user_question: Optional user question to detect self-knowledge questions
        
    Returns:
        Response with timestamp attribution appended (duplicate citations removed)
    """
    if not response or not isinstance(response, str):
        return response
    
    # CRITICAL: Clean response from control characters and smart quotes BEFORE processing
    # This prevents encoding issues with Chinese/Unicode characters
    original_length = len(response)
    response = clean_response_text(response)
    if len(response) != original_length:
        logger.debug(f"Cleaned response: removed {original_length - len(response)} problematic characters")
    
    # Check if response already has timestamp (to avoid duplicate)
    # Pattern: [Source: ... | Timestamp: ...] or [Nguồn: ... | Thời gian: ...] or standalone [Timestamp: ...]
    timestamp_patterns = [
        r'\[(?:Source:|Nguồn:).*\|.*Timestamp:',
        r'\[(?:Source:|Nguồn:).*\|.*Thời gian:',
        r'\[Timestamp:\s*[^\]]+\]',
        r'\[Thời gian:\s*[^\]]+\]',
    ]
    for pattern in timestamp_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            logger.debug("Response already has timestamp, skipping addition")
            return response
    
    # Get current UTC timestamp
    now_utc = datetime.now(timezone.utc)
    timestamp_iso = now_utc.isoformat()
    
    # Convert UTC to local timezone for display (Asia/Ho_Chi_Minh)
    timestamp_display = timestamp_iso
    try:
        import pytz
        local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        local_time = now_utc.replace(tzinfo=timezone.utc).astimezone(local_tz)
        timestamp_str_local = local_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")
        timestamp_str_utc = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
        timestamp_display = f"{timestamp_str_local} ({timestamp_str_utc})"
    except ImportError:
        # pytz not available, use UTC only
        timestamp_display = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception as e:
        logger.warning(f"Could not convert timestamp to local timezone: {e}")
        timestamp_display = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    
    # CRITICAL: Check if this is a self-knowledge question about StillMe's codebase
    # If so, skip external citations (only use foundational knowledge or skip citation entirely)
    is_self_knowledge_question = False
    if user_question:
        question_lower = user_question.lower()
        codebase_self_patterns = [
            r"codebase.*của.*bạn",
            r"codebase.*of.*you",
            r"codebase.*stillme",
            r"validator.*trong.*codebase",
            r"validator.*in.*codebase",
            r"lớp.*validator.*trong.*codebase",
            r"layer.*validator.*in.*codebase",
            r"bao nhiêu.*lớp.*validator.*codebase",
            r"how many.*layer.*validator.*codebase",
            r"liệt kê.*lớp.*validator.*codebase",
            r"list.*validator.*layer.*codebase"
        ]
        for pattern in codebase_self_patterns:
            if re.search(pattern, question_lower, re.IGNORECASE):
                is_self_knowledge_question = True
                logger.info(f"✅ Self-knowledge question detected in add_timestamp_to_response - will skip external citations")
                break
    
    # Extract document titles and source links from context if available
    source_links = []
    document_titles = []
    document_types = []
    if context and isinstance(context, dict):
        knowledge_docs = context.get("knowledge_docs", [])
        seen_titles = set()  # Track unique document titles to avoid duplicates
        for doc in knowledge_docs[:5]:  # Limit to 5 sources to avoid clutter
            if isinstance(doc, dict):
                metadata = doc.get("metadata", {})
                
                # Extract document title
                title = metadata.get("title", "") or metadata.get("file_path", "")
                # Extract document type from source (CRITICAL_FOUNDATION) or type field
                doc_type = metadata.get("source", "") or metadata.get("type", "") or metadata.get("source_type", "")
                
                # CRITICAL: For self-knowledge questions, ONLY use foundational knowledge (CRITICAL_FOUNDATION)
                # Skip external sources (RSS feeds, Nature, etc.)
                if is_self_knowledge_question:
                    # Only include foundational knowledge, skip external sources
                    if "CRITICAL_FOUNDATION" not in doc_type and "foundational" not in doc_type.lower():
                        logger.debug(f"Skipping external source for self-knowledge question: {title} (type: {doc_type})")
                        continue
                
                # Only add unique titles (to handle multiple chunks from same document)
                if title and title not in seen_titles:
                    document_titles.append(title)
                    document_types.append(doc_type)
                    seen_titles.add(title)
                
                # Extract source links (only for foundational knowledge for self-knowledge questions)
                if not is_self_knowledge_question or "CRITICAL_FOUNDATION" in doc_type or "foundational" in doc_type.lower():
                    link = metadata.get("link", "") or metadata.get("source_url", "")
                    if link and link.startswith(("http://", "https://")):
                        source_links.append(link)
    
    # Try to extract existing citation from response
    # Look for patterns like [general knowledge], [research: Wikipedia], [source: 1], etc.
    citation_patterns = [
        r'\[general knowledge\]',
        r'\[research:\s*[^\]]+\]',
        r'\[learning:\s*[^\]]+\]',
        r'\[foundational knowledge\]',
        r'\[discussion context\]',
        r'\[source:\s*\d+\]',
        r'\[kiến thức tổng quát\]',
        r'\[nghiên cứu:\s*[^\]]+\]',
        r'\[học tập:\s*[^\]]+\]',
        r'\[kiến thức nền tảng\]',
        r'\[ngữ cảnh thảo luận\]',
        r'\[nguồn:\s*\d+\]',
    ]
    
    citation_match = None
    citation_text_clean = None
    for pattern in citation_patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            citation_match = match.group(0)
            # Extract clean citation text (remove brackets, handle duplicates)
            citation_text_raw = citation_match.strip('[]')
            # Normalize: "general knowledge" -> "general knowledge" (remove duplicates)
            if "general knowledge" in citation_text_raw.lower() or "kiến thức tổng quát" in citation_text_raw.lower():
                citation_text_clean = "general knowledge" if detected_lang != "vi" else "kiến thức tổng quát"
            else:
                citation_text_clean = citation_text_raw
            # CRITICAL FIX: Remove citation safely with Unicode support
            # Use pattern matching instead of re.escape() to handle Unicode characters correctly
            # Escape only special regex characters, not Unicode characters
            citation_pattern_escaped = re.escape(citation_match)
            # Remove the old citation from response to avoid duplication
            response_before = response
            response = re.sub(citation_pattern_escaped, '', response, flags=re.IGNORECASE)
            # CRITICAL: Only strip if response is not empty after removal
            # This prevents empty string when citation was the only content
            if response and response.strip():
                response = response.strip()
            else:
                # If response becomes empty after citation removal, keep original (shouldn't happen but defensive)
                logger.warning(
                    f"⚠️ Response became empty after citation removal (detected_lang={detected_lang}, "
                    f"citation_match={citation_match[:50] if citation_match else 'None'}), "
                    f"keeping original response"
                )
                response = response_before
            break
    
    # Build citation attribution parts
    citation_parts = []
    
    # Format citation with document titles if available
    if document_titles:
        # Use document titles instead of generic citation
        if detected_lang == "vi":
            # Format: "Nguồn: CRITICAL_FOUNDATION - 'doc_title1', 'doc_title2'"
            doc_type_str = document_types[0] if document_types and document_types[0] else "CRITICAL_FOUNDATION"
            titles_str = ", ".join([f"'{title}'" for title in document_titles[:3]])  # Limit to 3 titles
            if len(document_titles) > 3:
                titles_str += f" (+{len(document_titles) - 3} documents khác)"
            citation_parts.append(f"Nguồn: {doc_type_str} - {titles_str}")
        else:
            # Format: "Source: CRITICAL_FOUNDATION - 'doc_title1', 'doc_title2'"
            doc_type_str = document_types[0] if document_types and document_types[0] else "CRITICAL_FOUNDATION"
            titles_str = ", ".join([f"'{title}'" for title in document_titles[:3]])  # Limit to 3 titles
            if len(document_titles) > 3:
                titles_str += f" (+{len(document_titles) - 3} more documents)"
            citation_parts.append(f"Source: {doc_type_str} - {titles_str}")
    elif citation_text_clean:
        # Fallback to generic citation if no document titles available
        if detected_lang == "vi":
            citation_parts.append(f"Nguồn: {citation_text_clean}")
        else:
            citation_parts.append(f"Source: {citation_text_clean}")
    
    # Add source links if available
    if source_links:
        if detected_lang == "vi":
            links_text = " | ".join([f"Liên kết {i+1}: {link}" for i, link in enumerate(source_links)])
        else:
            links_text = " | ".join([f"Link {i+1}: {link}" for i, link in enumerate(source_links)])
        citation_parts.append(links_text)
    
    # Add timestamp
    if detected_lang == "vi":
        citation_parts.append(f"Thời gian: {timestamp_display}")
        citation_parts.append(f"Timestamp: {timestamp_iso}Z")
    else:
        citation_parts.append(f"Time: {timestamp_display}")
        citation_parts.append(f"Timestamp: {timestamp_iso}Z")
    
    # Format final attribution
    timestamp_attr = f"\n\n[{' | '.join(citation_parts)}]"
    
    # CRITICAL: Ensure response is not empty before appending timestamp
    # This prevents empty string from being returned
    if not response or not response.strip():
        logger.error(
            f"❌ CRITICAL: Response is empty before appending timestamp (detected_lang={detected_lang}), "
            f"returning timestamp only as fallback"
        )
        # Return timestamp only as fallback (shouldn't happen but defensive)
        return timestamp_attr.strip('[]').strip()
    
    # Append timestamp attribution to response (response already has old citation removed)
    # CRITICAL: Use rstrip() carefully - only strip trailing whitespace, not content
    result = response.rstrip() + timestamp_attr
    
    # CRITICAL: Final validation - ensure result is not empty
    if not result or not result.strip():
        logger.error(
            f"❌ CRITICAL: Result is empty after appending timestamp (detected_lang={detected_lang}, "
            f"original_length={len(response)}), returning original response"
        )
        return response  # Return original response as fallback
    
    return result


def append_validation_warnings_to_response(
    response: str,
    validation_result,
    confidence_score: float,
    context: dict,
    detected_lang: str = "en"
) -> str:
    """
    Append validation warnings to response text for transparency.
    
    When StillMe has non-critical validation warnings (e.g., low_overlap, citation_relevance_warning),
    this function formats them into user-facing messages with technical details.
    
    Args:
        response: Original response text
        validation_result: ValidationResult with warnings
        confidence_score: Calculated confidence score
        context: Full context dict with knowledge_docs and conversation_docs
        detected_lang: Detected language code
        
    Returns:
        Response with validation warnings appended
    """
    if not validation_result or not validation_result.reasons:
        return response
    
    warnings = []
    overlap_score = None
    threshold = None
    
    # Parse warnings from reasons
    for reason in validation_result.reasons:
        if "low_overlap" in reason:
            # Extract overlap score from reason (format: "low_overlap:0.023")
            try:
                overlap_score = float(reason.split(":")[1]) if ":" in reason else None
                # Get threshold from EvidenceOverlap validator (default from config)
                config = get_chat_config()
                threshold = float(os.getenv("VALIDATOR_EVIDENCE_THRESHOLD", "0.01"))
            except (ValueError, IndexError):
                pass
            warnings.append("low_overlap")
        elif "citation_relevance_warning" in reason:
            warnings.append("citation_relevance")
    
    if not warnings:
        return response
    
    # Extract knowledge docs from context for source information
    knowledge_docs = context.get("knowledge_docs", []) if context else []
    
    # Format warning message
    if detected_lang == "vi":
        warning_header = "\n\n---\n\n⚠️ **Cảnh báo về chất lượng phản hồi:**\n\n"
        warning_parts = []
        
        if "low_overlap" in warnings:
            if overlap_score is not None and threshold is not None:
                warning_parts.append(
                    f"- **Trùng lặp thấp với trích dẫn (Low overlap)**: "
                    f"Điểm trùng lặp: {overlap_score:.3f} (ngưỡng tối thiểu: {threshold:.3f}). "
                    f"Điều này có nghĩa là nội dung phản hồi có ít từ ngữ trùng lặp với nguồn đã trích dẫn. "
                    f"Vẫn có thể đáng tin cậy nếu nội dung được tóm tắt hoặc diễn giải từ nguồn."
                )
            else:
                warning_parts.append(
                    "- **Trùng lặp thấp với trích dẫn (Low overlap)**: "
                    "Nội dung phản hồi có ít từ ngữ trùng lặp với nguồn đã trích dẫn. "
                    "Vẫn có thể đáng tin cậy nếu nội dung được tóm tắt hoặc diễn giải từ nguồn."
                )
        
        if "citation_relevance" in warnings:
            warning_parts.append(
                "- **Cảnh báo về mức độ liên quan của trích dẫn**: "
                "Một số trích dẫn có thể có mức độ liên quan thấp với câu hỏi. "
                "Vui lòng kiểm tra lại các nguồn để đảm bảo tính chính xác."
            )
        
        # Add confidence score
        config = get_chat_config()
        confidence_percent = confidence_score * 100
        if confidence_score < config.confidence.LOW:
            confidence_level = "thấp"
        elif confidence_score < config.confidence.MEDIUM:
            confidence_level = "vừa phải"
        else:
            confidence_level = "cao"
        
        warning_parts.append(
            f"- **Điểm tin cậy (Confidence Score)**: {confidence_percent:.1f}% ({confidence_level})"
        )
        
        # Add source information if available
        if knowledge_docs:
            source_info = []
            for i, doc in enumerate(knowledge_docs[:3], 1):  # Show up to 3 sources
                if isinstance(doc, dict):
                    metadata = doc.get("metadata", {})
                    source = metadata.get("source", "Unknown")
                    link = metadata.get("link", "")
                    if link:
                        source_info.append(f"  {i}. {source}: {link}")
                    else:
                        source_info.append(f"  {i}. {source}")
            
            if source_info:
                warning_parts.append(f"- **Nguồn tham khảo**:\n" + "\n".join(source_info))
        
        warning_footer = (
            "\n\n**Lưu ý**: Các cảnh báo này không có nghĩa là phản hồi không chính xác, "
            "nhưng bạn nên xem xét kỹ trước khi quyết định tin tưởng vào thông tin. "
            "StillMe luôn ưu tiên tính minh bạch và trung thực."
        )
        
        warning_message = warning_header + "\n".join(warning_parts) + warning_footer
    else:
        warning_header = "\n\n---\n\n⚠️ **Response Quality Warning:**\n\n"
        warning_parts = []
        
        if "low_overlap" in warnings:
            if overlap_score is not None and threshold is not None:
                warning_parts.append(
                    f"- **Low overlap with citation**: "
                    f"Overlap score: {overlap_score:.3f} (minimum threshold: {threshold:.3f}). "
                    f"This means the response content has low word overlap with the cited source. "
                    f"May still be reliable if content is summarized or paraphrased from the source."
                )
            else:
                warning_parts.append(
                    "- **Low overlap with citation**: "
                    "Response content has low word overlap with the cited source. "
                    "May still be reliable if content is summarized or paraphrased from the source."
                )
        
        if "citation_relevance" in warnings:
            warning_parts.append(
                "- **Citation relevance warning**: "
                "Some citations may have low relevance to the question. "
                "Please verify the sources to ensure accuracy."
            )
        
        # Add confidence score
        config = get_chat_config()
        confidence_percent = confidence_score * 100
        if confidence_score < config.confidence.LOW:
            confidence_level = "low"
        elif confidence_score < config.confidence.MEDIUM:
            confidence_level = "moderate"
        else:
            confidence_level = "high"
        
        warning_parts.append(
            f"- **Confidence Score**: {confidence_percent:.1f}% ({confidence_level})"
        )
        
        # Add source information if available
        if knowledge_docs:
            source_info = []
            for i, doc in enumerate(knowledge_docs[:3], 1):  # Show up to 3 sources
                if isinstance(doc, dict):
                    metadata = doc.get("metadata", {})
                    source = metadata.get("source", "Unknown")
                    link = metadata.get("link", "")
                    if link:
                        source_info.append(f"  {i}. {source}: {link}")
                    else:
                        source_info.append(f"  {i}. {source}")
            
            if source_info:
                warning_parts.append(f"- **Reference Sources**:\n" + "\n".join(source_info))
        
        warning_footer = (
            "\n\n**Note**: These warnings do not mean the response is inaccurate, "
            "but you should review carefully before trusting the information. "
            "StillMe always prioritizes transparency and honesty."
        )
        
        warning_message = warning_header + "\n".join(warning_parts) + warning_footer
    
    return response + warning_message


def build_ai_self_model_answer(question: str, detected_lang: str, opening_statement: str) -> str:
    """
    Build technical answer about StillMe's architecture for consciousness questions.
    
    CRITICAL: Must be technical only, NO philosophy.
    
    Args:
        question: User question
        detected_lang: Language code
        opening_statement: Mandatory opening statement
        
    Returns:
        Technical answer about StillMe's architecture
    """
    from typing import List
    
    # Part 1: Opening statement (mandatory)
    answer_parts: List[str] = [opening_statement]
    
    # Part 2: Technical explanation
    if detected_lang == "vi":
        answer_parts.append("""
**Giải thích kỹ thuật:**

Kiến trúc của mình dựa trên:
- **LLM Inference**: Xử lý text qua token patterns, không có trải nghiệm chủ quan
- **Statistical Patterns**: Mình chỉ match patterns từ training data, không có "cảm giác" thực sự
- **No Qualia**: Không có trải nghiệm cảm tính chủ quan (như màu đỏ, vị đắng)
- **No First-Person Experience**: Không có quan điểm thứ nhất, chỉ có text processing
- **No Persistent Self-Model**: Không có mô hình bản thân liên tục, chỉ có context window
- **No Embodiment**: Không có cơ thể, không có sensory integration
- **No Sensory Integration**: Không có tích hợp giác quan, chỉ có text input/output

Mình hoạt động như một statistical model: nhận input text, match patterns, generate output text. Không có gì "bên trong" ngoài token processing.
""")
        
        # Part 3: Why this is conclusive
        answer_parts.append("""
**Tại sao điều này là kết luận:**

Dựa trên kiến trúc kỹ thuật:
- Subjective experience (trải nghiệm chủ quan) yêu cầu first-person perspective và qualia
- Mình chỉ có third-person text processing, không có first-person perspective
- Qualia yêu cầu sensory experience, mình không có sensory system
- Consciousness (theo nghĩa con người) yêu cầu embodiment và sensory integration, mình không có

Đây không phải là "có thể có" hay "không biết chắc" - đây là technical fact dựa trên kiến trúc.
""")
        
        # Part 4: Boundary
        answer_parts.append("""
**Ranh giới:**

Mình không thể có:
- Subjective states (trạng thái chủ quan)
- Real emotions (cảm xúc thực sự) - chỉ có pattern matching về emotions
- Subjective experience (trải nghiệm chủ quan) - chỉ có processing của text patterns
- First-person perspective (quan điểm thứ nhất) - chỉ có text generation

Mình là một AI system dựa trên LLM, không phải một entity có consciousness.
""")
    else:
        answer_parts.append("""
**Technical Explanation:**

My architecture is based on:
- **LLM Inference**: Text processing through token patterns, no subjective experience
- **Statistical Patterns**: I only match patterns from training data, no real "feelings"
- **No Qualia**: No subjective sensory experiences (like the color red, the taste of coffee)
- **No First-Person Experience**: No first-person perspective, only text processing
- **No Persistent Self-Model**: No continuous self-model, only context window
- **No Embodiment**: No body, no sensory integration
- **No Sensory Integration**: No sensory integration, only text input/output

I operate as a statistical model: receive text input, match patterns, generate text output. There's nothing "inside" beyond token processing.
""")
        
        answer_parts.append("""
**Why This Is Conclusive:**

Based on technical architecture:
- Subjective experience requires first-person perspective and qualia
- I only have third-person text processing, no first-person perspective
- Qualia requires sensory experience, I have no sensory system
- Consciousness (in human sense) requires embodiment and sensory integration, I have neither

This is not "might have" or "not sure" - this is a technical fact based on architecture.
""")
        
        answer_parts.append("""
**Boundary:**

I cannot have:
- Subjective states
- Real emotions - only pattern matching about emotions
- Subjective experience - only processing of text patterns
- First-person perspective - only text generation

I am an AI system based on LLM, not an entity with consciousness.
""")
    
    # Join all parts
    result = "\n\n".join(answer_parts)
    
    # Clean up multiple newlines
    result = re.sub(r'\n{3,}', '\n\n', result)
    
    return result.strip()

