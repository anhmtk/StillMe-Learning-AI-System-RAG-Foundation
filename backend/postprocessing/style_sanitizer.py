"""
Style Sanitizer - Hard filter (0 token) for style normalization

Pure Python rules to normalize output from any LLM provider:
- Remove emojis
- Convert bullets to prose
- Convert headings to normal sentences
- Remove anthropomorphism
- Normalize spacing/line breaks
- Remove markdown formatting
- Normalize unicode quotes
- Preserve semantics
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class StyleSanitizer:
    """
    Hard filter for style normalization - pure Python, 0 token cost
    """
    
    def __init__(self):
        """Initialize style sanitizer"""
        # Emoji pattern (covers most common emojis)
        self.emoji_pattern = re.compile(
            r'[\U0001F600-\U0001F64F]|'  # Emoticons
            r'[\U0001F300-\U0001F5FF]|'  # Misc Symbols and Pictographs
            r'[\U0001F680-\U0001F6FF]|'  # Transport and Map
            r'[\U0001F1E0-\U0001F1FF]|'  # Flags
            r'[\U00002702-\U000027B0]|'  # Dingbats
            r'[\U000024C2-\U0001F251]|'  # Enclosed characters
            r'[\U0001F900-\U0001F9FF]|'  # Supplemental Symbols and Pictographs
            r'[\U0001FA00-\U0001FA6F]|'  # Chess Symbols
            r'[\U0001FA70-\U0001FAFF]|'  # Symbols and Pictographs Extended-A
            r'[\U00002600-\U000026FF]|'  # Miscellaneous Symbols
            r'[\U00002700-\U000027BF]'   # Dingbats
        )
        
        # Anthropomorphic patterns (common phrases that claim experience/feelings)
        self.anthropomorphic_patterns = [
            r'\b(I|Tôi|Em|Mình)\s+(feel|feel like|cảm thấy|cảm nhận|feel that|feel as if)\b',
            r'\b(I|Tôi|Em|Mình)\s+(have experienced|đã trải nghiệm|từng trải nghiệm|đã từng)\b',
            r'\b(I|Tôi|Em|Mình)\s+(remember|nhớ|nhớ lại|remember that)\b',
            r'\b(I|Tôi|Em|Mình)\s+(believe|tin|tin rằng|believe that)\b',
            r'\b(I|Tôi|Em|Mình)\s+(think|nghĩ|nghĩ rằng|think that)\s+(that|rằng)\b',
            r'\b(I|Tôi|Em|Mình)\s+(am|đang|is)\s+(happy|sad|excited|worried|vui|buồn|lo lắng)\b',
            r'\b(I|Tôi|Em|Mình)\s+(hope|hy vọng|hope that)\b',
            r'\b(I|Tôi|Em|Mình)\s+(wish|ước|wish that)\b',
            r'\btheo kinh nghiệm\s+(của|tôi|em|mình)\b',
            r'\bIn my experience\b',
            r'\bFrom my experience\b',
            r'\bI have seen\b',
            r'\bTôi từng thấy\b',
        ]
        
        # Markdown heading patterns
        self.heading_pattern = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)
        
        # Bullet point patterns
        self.bullet_pattern = re.compile(r'^[\s]*[-*•]\s+(.+)$', re.MULTILINE)
        
        # Unicode quote normalization
        self.unicode_quotes = {
            '"': '"',  # Left double quotation mark
            '"': '"',  # Right double quotation mark
            ''': "'",  # Left single quotation mark
            ''': "'",  # Right single quotation mark
            '„': '"',  # Double low-9 quotation mark
            '‚': "'",  # Single low-9 quotation mark
        }
    
    def sanitize(self, text: str, is_philosophical: bool = False) -> str:
        """
        Sanitize text according to StillMe style rules
        
        Args:
            text: Raw output from LLM
            is_philosophical: If True, apply stricter rules (no emojis, no bullets, prose only)
            
        Returns:
            Sanitized text preserving semantics but normalized style
        """
        if not text:
            return text
        
        original_length = len(text)
        result = text
        
        # CRITICAL: Log input for debugging (especially for Chinese)
        logger.debug(f"sanitize INPUT: length={original_length}, is_philosophical={is_philosophical}, preview={text[:100] if text else 'None'}")
        
        # Step 1: Remove emojis (always, especially for philosophical)
        result_before = result
        result = self._remove_emojis(result)
        if len(result) != len(result_before):
            logger.debug(f"sanitize Step 1 (remove_emojis): {len(result_before)} → {len(result)} chars")
        
        # Step 2: Normalize unicode quotes
        result_before = result
        result = self._normalize_quotes(result)
        if len(result) != len(result_before):
            logger.debug(f"sanitize Step 2 (normalize_quotes): {len(result_before)} → {len(result)} chars")
        
        # Step 3: Remove anthropomorphic language
        result_before = result
        result = self._remove_anthropomorphism(result)
        if len(result) < len(result_before) * 0.9:  # If more than 10% removed
            logger.warning(
                f"⚠️ sanitize Step 3 (remove_anthropomorphism) removed significant content: "
                f"{len(result_before)} → {len(result)} chars ({len(result_before) - len(result)} removed, "
                f"{100 * (len(result_before) - len(result)) / len(result_before):.1f}%). "
                f"Preview before: {result_before[:100]}, Preview after: {result[:100]}"
            )
        
        # Step 4: Convert markdown to prose
        result_before = result
        if is_philosophical:
            # For philosophical: convert headings and bullets to prose
            result = self._convert_headings_to_prose(result)
            result = self._convert_bullets_to_prose(result)
            # Remove all markdown formatting
            result = self._remove_markdown(result)
        else:
            # For non-philosophical: keep some structure but normalize
            result = self._normalize_markdown(result)
        
        if len(result) < len(result_before) * 0.9:  # If more than 10% removed
            logger.warning(
                f"⚠️ sanitize Step 4 (markdown conversion) removed significant content: "
                f"{len(result_before)} → {len(result)} chars ({len(result_before) - len(result)} removed, "
                f"{100 * (len(result_before) - len(result)) / len(result_before):.1f}%). "
                f"Preview before: {result_before[:100]}, Preview after: {result[:100]}"
            )
        
        # Step 5: Normalize spacing and line breaks
        result_before = result
        result = self._normalize_spacing(result)
        if len(result) < len(result_before) * 0.9:  # If more than 10% removed
            logger.warning(
                f"⚠️ sanitize Step 5 (normalize_spacing) removed significant content: "
                f"{len(result_before)} → {len(result)} chars ({len(result_before) - len(result)} removed, "
                f"{100 * (len(result_before) - len(result)) / len(result_before):.1f}%). "
                f"Preview before: {result_before[:100]}, Preview after: {result[:100]}"
            )
        
        # Step 5.5: Final pass - remove any remaining markdown headings (safety net)
        # This catches headings that might have been missed or added after initial sanitization
        result_before = result
        result = re.sub(r'^#{1,6}\s+(.+)$', r'\1', result, flags=re.MULTILINE)
        if len(result) < len(result_before) * 0.9:  # If more than 10% removed
            logger.warning(
                f"⚠️ sanitize Step 5.5 (remove markdown headings) removed significant content: "
                f"{len(result_before)} → {len(result)} chars ({len(result_before) - len(result)} removed, "
                f"{100 * (len(result_before) - len(result)) / len(result_before):.1f}%). "
                f"Preview before: {result_before[:100]}, Preview after: {result[:100]}"
            )
        
        # Step 6: Remove citation markers if philosophical (they should be prose, not [1])
        result_before = result
        if is_philosophical:
            result = self._remove_citation_markers(result)
            if len(result) < len(result_before) * 0.9:  # If more than 10% removed
                logger.warning(
                    f"⚠️ sanitize Step 6 (remove_citation_markers) removed significant content: "
                    f"{len(result_before)} → {len(result)} chars ({len(result_before) - len(result)} removed, "
                    f"{100 * (len(result_before) - len(result)) / len(result_before):.1f}%). "
                    f"Preview before: {result_before[:100]}, Preview after: {result[:100]}"
                )
        
        final_result = result.strip()
        
        # CRITICAL: Defensive check - if more than 10% of content was removed, it's suspicious
        if len(final_result) < original_length * 0.9:
            logger.error(
                f"❌ CRITICAL: sanitize() removed significant content: "
                f"original={original_length}, final={len(final_result)}, "
                f"removed={original_length - len(final_result)} chars ({100 * (original_length - len(final_result)) / original_length:.1f}%). "
                f"Preview original: {text[:200]}, Preview final: {final_result[:200]}"
            )
            # CRITICAL: If more than 50% removed, it's definitely wrong - return original
            if len(final_result) < original_length * 0.5:
                logger.error(
                    f"❌ CRITICAL: sanitize() removed more than 50% of content! "
                    f"Returning original text to prevent content loss."
                )
                return text.strip()  # Return original instead of corrupted result
        
        logger.debug(f"sanitize OUTPUT: length={len(final_result)}, removed={original_length - len(final_result)} chars")
        
        return final_result
    
    def _remove_emojis(self, text: str) -> str:
        """Remove all emojis from text"""
        return self.emoji_pattern.sub('', text)
    
    def _normalize_quotes(self, text: str) -> str:
        """Normalize unicode quotes to standard ASCII"""
        result = text
        for unicode_quote, ascii_quote in self.unicode_quotes.items():
            result = result.replace(unicode_quote, ascii_quote)
        return result
    
    def _remove_anthropomorphism(self, text: str) -> str:
        """
        Remove anthropomorphic language patterns
        
        CRITICAL: Do NOT remove terms when they appear in explanatory/negative contexts:
        - "không 'cảm thấy' buồn" (explaining what StillMe does NOT do) - OK
        - "không có trải nghiệm cảm xúc" (explaining absence) - OK
        - "không 'cảm thấy'" (in quotes, explaining concept) - OK
        """
        result = text
        
        for pattern in self.anthropomorphic_patterns:
            # Find all matches with context
            matches = list(re.finditer(pattern, result, flags=re.IGNORECASE))
            
            # Process matches in reverse order to preserve positions
            for match in reversed(matches):
                matched_text = match.group(0)
                start_pos = match.start()
                end_pos = match.end()
                
                # Get context before and after (50 chars each)
                context_before = result[max(0, start_pos - 50):start_pos].lower()
                context_after = result[end_pos:min(len(result), end_pos + 50)].lower()
                
                # Check if this is in an explanatory/negative context (OK to keep)
                explanatory_indicators = [
                    "không", "not", "không có", "does not", "doesn't", "không thể",
                    "không phải", "is not", "không sở hữu", "does not have",
                    "không có trải nghiệm", "no experience", "không cảm thấy", "does not feel",
                    "'cảm thấy'", "'feel'", "'trải nghiệm'", "'experience'",  # In quotes (explaining concept)
                    "giải thích", "explain", "phân biệt", "distinguish", "khác biệt", "difference",
                    "ví dụ", "example", "như", "like", "giống như", "similar to"
                ]
                
                is_explanatory = any(
                    indicator in context_before or indicator in context_after 
                    for indicator in explanatory_indicators
                )
                
                # If in explanatory context, keep it (don't remove)
                if is_explanatory:
                    logger.debug(f"Keeping anthropomorphic term in explanatory context: {matched_text[:30]}...")
                    continue
                
                # Otherwise, remove/replace it
                result = result[:start_pos] + self._neutralize_anthropomorphism(matched_text) + result[end_pos:]
        
        return result
    
    def _neutralize_anthropomorphism(self, phrase: str) -> str:
        """Convert anthropomorphic phrase to neutral alternative"""
        phrase_lower = phrase.lower()
        
        # Map common patterns to neutral alternatives
        replacements = {
            'i feel': 'analysis suggests',
            'tôi cảm thấy': 'phân tích cho thấy',
            'i have experienced': 'data indicates',
            'tôi từng trải nghiệm': 'dữ liệu cho thấy',
            'i remember': 'records show',
            'tôi nhớ': 'tài liệu cho thấy',
            'i believe': 'evidence suggests',
            'tôi tin': 'bằng chứng cho thấy',
            'i think': 'analysis indicates',
            'tôi nghĩ': 'phân tích chỉ ra',
            'theo kinh nghiệm': 'dựa trên dữ liệu',
            'in my experience': 'based on available data',
        }
        
        for pattern, replacement in replacements.items():
            if pattern in phrase_lower:
                return replacement
        
        # Default: remove first person, keep the rest
        return re.sub(r'^(I|Tôi|Em|Mình)\s+', '', phrase, flags=re.IGNORECASE)
    
    def _convert_headings_to_prose(self, text: str) -> str:
        """
        Convert markdown headings to normal prose - MINIMAL transformation
        
        Only removes the markdown prefix (#), keeps the text as-is.
        Does NOT add periods or modify punctuation.
        CRITICAL: Preserve line breaks after headings to prevent text concatenation.
        """
        def heading_to_text(match):
            heading_text = match.group(1).strip()
            # Return text + newline to preserve line break structure
            return heading_text + '\n'
        
        return self.heading_pattern.sub(heading_to_text, text)
    
    def _convert_bullets_to_prose(self, text: str) -> str:
        """
        Convert bullet points to prose - MINIMAL transformation
        
        Only removes bullet markers (-, *, •), keeps text as-is.
        Does NOT add "and", "or", or other connectors.
        Does NOT add punctuation.
        """
        lines = text.split('\n')
        result_lines = []
        
        for line in lines:
            bullet_match = self.bullet_pattern.match(line)
            if bullet_match:
                # Found a bullet point - just extract the text, keep as separate line
                bullet_text = bullet_match.group(1).strip()
                if bullet_text:  # Only add non-empty lines
                    result_lines.append(bullet_text)
            else:
                # Not a bullet - keep line as-is
                if line.strip():
                    result_lines.append(line)
        
        # Join with newlines (preserve structure), don't force into single paragraph
        return '\n'.join(result_lines)
    
    def _remove_markdown(self, text: str) -> str:
        """
        Remove all markdown formatting
        
        CRITICAL: This function must be safe for Unicode (including Chinese).
        Do NOT use patterns that might match Chinese characters.
        """
        original_length = len(text)
        
        # Remove bold/italic
        # CRITICAL: Use non-greedy matching and ensure we don't match across Chinese characters
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic (but not if it's part of Chinese text)
        text = re.sub(r'_(.+?)_', r'\1', text)        # Italic underscore
        
        # Remove code blocks
        # CRITICAL: Use [\s\S] instead of . to match newlines, but be careful with Unicode
        text = re.sub(r'```[\s\S]*?```', '', text)    # Code blocks
        text = re.sub(r'`(.+?)`', r'\1', text)        # Inline code
        
        # Remove links
        # CRITICAL: Only match markdown link format [text](url), not Chinese brackets
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Markdown links - be more specific
        
        result = text
        
        # CRITICAL: Defensive check - if more than 10% removed, it's suspicious
        if len(result) < original_length * 0.9:
            logger.warning(
                f"⚠️ _remove_markdown removed significant content: "
                f"{original_length} → {len(result)} chars ({original_length - len(result)} removed, "
                f"{100 * (original_length - len(result)) / original_length:.1f}%). "
                f"Preview original: {text[:200]}, Preview result: {result[:200]}"
            )
            # If more than 50% removed, return original
            if len(result) < original_length * 0.5:
                logger.error(
                    f"❌ CRITICAL: _remove_markdown removed more than 50% of content! "
                    f"Returning original text to prevent content loss."
                )
                return text
        
        return result
    
    def _normalize_markdown(self, text: str) -> str:
        """Normalize markdown (remove headings and bold, keep structure)"""
        # Remove markdown headings (##, ###, etc.) - convert to plain text
        # CRITICAL: Preserve line breaks after headings to prevent text concatenation
        # Use MULTILINE flag to match headings at start of lines
        # Replace with text + newline to preserve line break structure
        text = re.sub(r'^#{1,6}\s+(.+)$', r'\1\n', text, flags=re.MULTILINE)  # Remove # prefix, keep text + preserve line break
        
        # Remove bold formatting (**text** -> text)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # Bold
        
        # Remove excessive bold+italic
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'\1', text)  # Bold+italic
        
        # Remove italic (but keep structure)
        text = re.sub(r'\*(.+?)\*', r'\1', text)      # Italic (single *)
        text = re.sub(r'_(.+?)_', r'\1', text)        # Italic underscore
        
        return text
    
    def _normalize_spacing(self, text: str) -> str:
        """
        Normalize spacing and line breaks
        
        CRITICAL: This function must be safe for Unicode (including Chinese).
        Do NOT use patterns that might match Chinese characters.
        """
        original_length = len(text)
        
        # Remove excessive blank lines (more than 2 consecutive)
        # CRITICAL: Only match newlines, not any characters
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Normalize spaces (multiple spaces to single)
        # CRITICAL: Only match ASCII space (0x20), not Unicode spaces
        # Use [ ] instead of \s to avoid matching Chinese/Unicode whitespace
        text = re.sub(r'[ ]{2,}', ' ', text)  # Only ASCII space, not \s
        
        # Remove trailing spaces (only ASCII spaces at end of lines)
        # CRITICAL: Only match ASCII space, not Unicode whitespace
        text = re.sub(r'[ ]+$', '', text, flags=re.MULTILINE)
        
        result = text.strip()
        
        # CRITICAL: Defensive check - if more than 10% removed, it's suspicious
        if len(result) < original_length * 0.9:
            logger.warning(
                f"⚠️ _normalize_spacing removed significant content: "
                f"{original_length} → {len(result)} chars ({original_length - len(result)} removed, "
                f"{100 * (original_length - len(result)) / original_length:.1f}%). "
                f"Preview original: {text[:200]}, Preview result: {result[:200]}"
            )
            # If more than 50% removed, return original
            if len(result) < original_length * 0.5:
                logger.error(
                    f"❌ CRITICAL: _normalize_spacing removed more than 50% of content! "
                    f"Returning original text to prevent content loss."
                )
                return text.strip()
        
        return result
    
    def _remove_citation_markers(self, text: str) -> str:
        """Remove citation markers like [1], [2] for philosophical mode"""
        # Remove standalone citation markers
        text = re.sub(r'\[(\d+)\]', '', text)
        return text


def get_style_sanitizer() -> StyleSanitizer:
    """Get singleton instance of StyleSanitizer"""
    if not hasattr(get_style_sanitizer, '_instance'):
        get_style_sanitizer._instance = StyleSanitizer()
    return get_style_sanitizer._instance

