#!/usr/bin/env python3
"""
Language Detection Utility for StillMe
Phát hiện ngôn ngữ theo câu người dùng
"""

import re


class LanguageDetector:
    """Simple language detector using heuristics"""

    def __init__(self):
        # Vietnamese character patterns
        self.vietnamese_patterns = [
            r'[àáạảãâầấậẩẫăằắặẳẵ]',  # a with diacritics
            r'[èéẹẻẽêềếệểễ]',        # e with diacritics
            r'[ìíịỉĩ]',              # i with diacritics
            r'[òóọỏõôồốộổỗơờớợởỡ]',  # o with diacritics
            r'[ùúụủũưừứựửữ]',        # u with diacritics
            r'[ỳýỵỷỹ]',              # y with diacritics
            r'[đ]',                  # d with stroke
        ]

        # Common Vietnamese words
        self.vietnamese_words = [
            'xin chào', 'chào', 'bạn', 'mình', 'tôi', 'anh', 'chị', 'em',
            'cảm ơn', 'xin lỗi', 'không', 'có', 'được', 'không được',
            'hôm nay', 'ngày mai', 'hôm qua', 'bây giờ', 'lúc nào',
            'ở đâu', 'như thế nào', 'tại sao', 'bao nhiêu', 'khi nào',
            'và', 'hoặc', 'nhưng', 'vì', 'nên', 'để', 'mà', 'của',
            'với', 'trong', 'ngoài', 'trên', 'dưới', 'trước', 'sau',
            'này', 'đó', 'kia', 'đây', 'đấy', 'ấy', 'nọ'
        ]

        # Common English words
        self.english_words = [
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
            'thank you', 'thanks', 'sorry', 'excuse me', 'please', 'yes', 'no',
            'today', 'tomorrow', 'yesterday', 'now', 'when', 'where', 'how', 'why',
            'what', 'who', 'which', 'and', 'or', 'but', 'because', 'so', 'to', 'for',
            'with', 'in', 'on', 'at', 'by', 'from', 'to', 'this', 'that', 'these', 'those'
        ]

        # Japanese patterns (basic)
        self.japanese_patterns = [
            r'[ひらがな]',  # hiragana
            r'[カタカナ]',  # katakana
            r'[一-龯]',    # kanji
        ]

        # Chinese patterns (basic)
        self.chinese_patterns = [
            r'[一-龯]',    # Chinese characters
        ]

        # Korean patterns (basic)
        self.korean_patterns = [
            r'[가-힣]',    # Hangul
        ]

    def detect_language(self, text: str) -> str:
        """
        Detect language from text
        Returns locale code: vi-VN, en-US, ja-JP, zh-CN, ko-KR, etc.
        """
        if not text or not text.strip():
            return 'vi-VN'  # Default to Vietnamese

        text_lower = text.lower().strip()

        # Check for Vietnamese
        vietnamese_score = self._calculate_vietnamese_score(text_lower)

        # Check for English
        english_score = self._calculate_english_score(text_lower)

        # Check for Japanese
        japanese_score = self._calculate_japanese_score(text)

        # Check for Chinese
        chinese_score = self._calculate_chinese_score(text)

        # Check for Korean
        korean_score = self._calculate_korean_score(text)

        # Find highest score
        scores = {
            'vi-VN': vietnamese_score,
            'en-US': english_score,
            'ja-JP': japanese_score,
            'zh-CN': chinese_score,
            'ko-KR': korean_score
        }

        detected_lang = max(scores, key=scores.get)

        # If no clear winner, default to Vietnamese
        if scores[detected_lang] < 0.1:
            return 'vi-VN'

        return detected_lang

    def _calculate_vietnamese_score(self, text: str) -> float:
        """Calculate Vietnamese language score"""
        score = 0.0

        # Check for Vietnamese diacritics
        for pattern in self.vietnamese_patterns:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            score += matches * 0.3

        # Check for Vietnamese words
        for word in self.vietnamese_words:
            if word in text:
                score += 0.5

        # Normalize by text length
        if len(text) > 0:
            score = score / len(text) * 100

        return min(score, 1.0)

    def _calculate_english_score(self, text: str) -> float:
        """Calculate English language score"""
        score = 0.0

        # Check for English words
        for word in self.english_words:
            if word in text:
                score += 0.3

        # Check for common English patterns
        english_patterns = [
            r'\bthe\b', r'\band\b', r'\bor\b', r'\bbut\b', r'\bin\b', r'\bon\b',
            r'\bat\b', r'\bto\b', r'\bfor\b', r'\bof\b', r'\bwith\b', r'\bby\b'
        ]

        for pattern in english_patterns:
            matches = len(re.findall(pattern, text, re.IGNORECASE))
            score += matches * 0.2

        # Normalize by text length
        if len(text) > 0:
            score = score / len(text) * 100

        return min(score, 1.0)

    def _calculate_japanese_score(self, text: str) -> float:
        """Calculate Japanese language score"""
        score = 0.0

        for pattern in self.japanese_patterns:
            matches = len(re.findall(pattern, text))
            score += matches * 0.4

        # Normalize by text length
        if len(text) > 0:
            score = score / len(text) * 100

        return min(score, 1.0)

    def _calculate_chinese_score(self, text: str) -> float:
        """Calculate Chinese language score"""
        score = 0.0

        for pattern in self.chinese_patterns:
            matches = len(re.findall(pattern, text))
            score += matches * 0.4

        # Normalize by text length
        if len(text) > 0:
            score = score / len(text) * 100

        return min(score, 1.0)

    def _calculate_korean_score(self, text: str) -> float:
        """Calculate Korean language score"""
        score = 0.0

        for pattern in self.korean_patterns:
            matches = len(re.findall(pattern, text))
            score += matches * 0.4

        # Normalize by text length
        if len(text) > 0:
            score = score / len(text) * 100

        return min(score, 1.0)

    def get_language_name(self, locale: str) -> str:
        """Get human-readable language name"""
        names = {
            'vi-VN': 'Tiếng Việt',
            'en-US': 'English',
            'ja-JP': '日本語',
            'zh-CN': '中文',
            'ko-KR': '한국어'
        }
        return names.get(locale, 'Unknown')

# Global instance
detector = LanguageDetector()

def detect_language(text: str) -> str:
    """Convenience function for language detection"""
    return detector.detect_language(text)

def get_language_name(locale: str) -> str:
    """Convenience function for language name"""
    return detector.get_language_name(locale)

# Test function
if __name__ == "__main__":
    test_cases = [
        "xin chào stillme",
        "hello how are you",
        "こんにちは",
        "你好",
        "안녕하세요",
        "hôm nay thời tiết thế nào?",
        "what's the weather like today?",
        "bạn có thể giúp tôi không?",
        "can you help me?",
        "cảm ơn bạn rất nhiều",
        "thank you very much"
    ]

    print("Language Detection Test:")
    print("=" * 50)

    for text in test_cases:
        detected = detect_language(text)
        name = get_language_name(detected)
        print(f"'{text}' -> {detected} ({name})")
