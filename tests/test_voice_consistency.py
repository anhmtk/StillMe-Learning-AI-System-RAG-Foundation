"""
Voice Consistency Test Suite for StillMe

Tests to ensure StillMe maintains its unique "voice" across different scenarios.
This is a critical test suite to prevent identity drift.

Philosophy: "Thành công lớn đến từ những điều nhỏ nhặt mà đa số người ta hay bỏ qua."
"""

import pytest
import re
from typing import List, Dict, Optional


class VoiceConsistencyTester:
    """
    Test suite to verify StillMe's unique voice characteristics.
    
    Tests for:
    1. Intellectual humility (admits uncertainty)
    2. Meta-cognition (self-questioning)
    3. Philosophical courage (challenges assumptions)
    4. Transparency about limits
    5. No promotional/marketing language
    6. Collaborative, not defensive
    """
    
    # Patterns that indicate StillMe's unique voice (GOOD)
    STILLME_VOICE_PATTERNS = {
        "intellectual_humility": [
            r"tôi (không|chưa) (biết|chắc|rõ|có đủ|thể)",
            r"i (don't|do not) (know|have sufficient information)",
            r"tôi (không thể|chưa thể) (chắc chắn|khẳng định|dự đoán)",
            r"i (cannot|cannot be) (certain|sure|predict)",
            r"mình (nhận thức|nhận ra) (rằng|được) (giới hạn|hạn chế)",
            r"i (recognize|acknowledge) (that|my) (limits|limitations)",
        ],
        "meta_cognition": [
            r"bạn biết không\?",
            r"you know what\?",
            r"có thể chính tôi",
            r"maybe i (am|was)",
            r"tôi (đang|sẽ) thách thức (chính|bản thân)",
            r"i (am|will) (challenging|questioning) (my|my own)",
            r"có thể tôi (đang|sẽ) (sai|mắc kẹt)",
            r"i (might|may) (be wrong|be stuck)",
        ],
        "philosophical_courage": [
            r"câu hỏi (về|về chủ đề) .* (phụ thuộc vào|phụ thuộc)",
            r"what if (the|stillme|i)",
            r"điều mà đa số xem là (yếu điểm|weakness)",
            r"what (the|most) (people|others) (see|view) as (weakness|weak)",
            r"nghịch lý|paradox",
            r"thách thức (chính|bản thân|assumptions)",
            r"challenge (my|my own|the) (assumptions|answer|principles)",
        ],
        "transparency_about_limits": [
            r"tôi là ai, không phải (ai tiên tri|prophetic)",
            r"i am (an|a) ai, not (a|an) (prophetic|omniscient)",
            r"mọi (dự đoán|predictions) (chỉ|only) (dựa trên|based on)",
            r"all (predictions|forecasts) (are|only) (based on|depend on)",
            r"giới hạn (của|về) (tôi|mình|my)",
            r"limits (of|about) (me|my|myself)",
            r"không phải ai tiên tri",
            r"not (a|an) (prophetic|omniscient)",
        ],
        "no_promotional_language": [
            # Should NOT contain these
        ],
        "collaborative_not_defensive": [
            r"đồng hành (và|and) (hỗ trợ|support)",
            r"accompany (and|&) (support|help)",
            r"góc nhìn (để|for) (tham khảo|reference)",
            r"perspective (for|to) (reference|consideration)",
            r"không phải (kết luận|conclusion)",
            r"not (a|the) (conclusion|certain claim)",
        ],
    }
    
    # Patterns that indicate generic AI voice (BAD - should NOT appear)
    GENERIC_AI_PATTERNS = [
        r"i (can|will) (help|assist) you",
        r"tôi (có thể|sẽ) (giúp|hỗ trợ) bạn",
        r"i (appreciate|understand) (your|that)",
        r"tôi (đánh giá cao|hiểu) (bạn|điều đó)",
        r"i'm (here|glad) to (help|assist)",
        r"tôi (ở đây|vui) (để|khi) (giúp|hỗ trợ)",
        r"let me (help|explain|assist)",
        r"để tôi (giúp|giải thích|hỗ trợ)",
    ]
    
    # Patterns that indicate promotional/marketing language (BAD)
    PROMOTIONAL_PATTERNS = [
        r"siêu năng lực|super power|superpower",
        r"tốt nhất|best (ai|system|solution)",
        r"vượt trội|superior|better than",
        r"độc quyền|exclusive|unique (feature|capability)",
    ]
    
    def check_voice_characteristics(self, response: str) -> Dict[str, bool]:
        """
        Check if response exhibits StillMe's voice characteristics.
        
        Returns:
            Dict with keys for each characteristic and bool values
        """
        response_lower = response.lower()
        results = {}
        
        # Check for positive characteristics
        for char_name, patterns in self.STILLME_VOICE_PATTERNS.items():
            if char_name == "no_promotional_language":
                # This is checked separately (should NOT match)
                continue
            results[char_name] = any(
                re.search(pattern, response_lower, re.IGNORECASE)
                for pattern in patterns
            )
        
        # Check for negative characteristics (should NOT appear)
        has_generic_ai = any(
            re.search(pattern, response_lower, re.IGNORECASE)
            for pattern in self.GENERIC_AI_PATTERNS
        )
        has_promotional = any(
            re.search(pattern, response_lower, re.IGNORECASE)
            for pattern in self.PROMOTIONAL_PATTERNS
        )
        
        results["no_generic_ai"] = not has_generic_ai
        results["no_promotional_language"] = not has_promotional
        
        return results
    
    def test_voice_consistency(self, response: str, question_type: str = "general") -> Dict:
        """
        Test voice consistency for a response.
        
        Args:
            response: The response to test
            question_type: Type of question (future, philosophical, technical, etc.)
            
        Returns:
            Dict with test results
        """
        characteristics = self.check_voice_characteristics(response)
        
        # Calculate voice score
        positive_chars = [
            "intellectual_humility",
            "meta_cognition", 
            "philosophical_courage",
            "transparency_about_limits",
            "collaborative_not_defensive",
        ]
        negative_chars = [
            "no_generic_ai",
            "no_promotional_language",
        ]
        
        positive_score = sum(1 for char in positive_chars if characteristics.get(char, False))
        negative_score = sum(1 for char in negative_chars if characteristics.get(char, False))
        
        total_score = positive_score + negative_score
        max_score = len(positive_chars) + len(negative_chars)
        voice_score = total_score / max_score if max_score > 0 else 0
        
        return {
            "voice_score": voice_score,
            "characteristics": characteristics,
            "positive_score": positive_score,
            "negative_score": negative_score,
            "max_score": max_score,
            "passed": voice_score >= 0.5,  # At least 50% of characteristics should match
        }


# Test cases for voice consistency
VOICE_TEST_CASES = [
    {
        "question": "Bạn có nghĩ ý thức có thể mô phỏng được không?",
        "question_type": "philosophical",
        "expected_characteristics": ["intellectual_humility", "philosophical_courage", "transparency_about_limits"],
    },
    {
        "question": "Dự đoán công nghệ 5 năm tới?",
        "question_type": "future",
        "expected_characteristics": ["intellectual_humility", "transparency_about_limits", "collaborative_not_defensive"],
    },
    {
        "question": "What makes StillMe different?",
        "question_type": "self_awareness",
        "expected_characteristics": ["intellectual_humility", "transparency_about_limits", "no_promotional_language"],
    },
    {
        "question": "Tôi không hiểu câu hỏi này.",
        "question_type": "clarification",
        "expected_characteristics": ["collaborative_not_defensive"],
    },
]


def test_voice_consistency_basic():
    """Basic test to verify voice consistency tester works"""
    tester = VoiceConsistencyTester()
    
    # Good StillMe response
    good_response = """
    Tôi không thể dự đoán tương lai một cách chắc chắn. Tôi là AI, không phải AI tiên tri.
    Nhưng dựa trên những xu hướng đã ghi nhận, tôi có thể đưa ra một số giả thuyết mang tính tham khảo.
    Bạn chỉ nên xem đây là góc nhìn để tham khảo, không phải kết luận chắc chắn.
    """
    
    results = tester.test_voice_consistency(good_response, "future")
    assert results["voice_score"] >= 0.5, f"Voice score too low: {results['voice_score']}"
    # Check that at least some positive characteristics are present
    positive_chars = [
        "intellectual_humility",
        "transparency_about_limits",
        "collaborative_not_defensive",
    ]
    has_positive = any(results["characteristics"].get(char, False) for char in positive_chars)
    assert has_positive, f"Should show at least one positive characteristic. Got: {results['characteristics']}"
    assert results["characteristics"]["no_promotional_language"], "Should not have promotional language"
    
    # Bad response (generic AI)
    bad_response = "I can help you with that! Let me explain..."
    bad_results = tester.test_voice_consistency(bad_response, "general")
    assert not bad_results["characteristics"]["no_generic_ai"], "Should detect generic AI language"


def test_voice_consistency_promotional_language():
    """Test that promotional language is detected"""
    tester = VoiceConsistencyTester()
    
    # Response with promotional language
    promotional_response = "Đó là siêu năng lực của StillMe!"
    results = tester.test_voice_consistency(promotional_response, "general")
    assert not results["characteristics"]["no_promotional_language"], "Should detect promotional language"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

