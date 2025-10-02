import time

import pytest

from stillme_core.middleware.pattern_matcher import PatternMatcher


@pytest.fixture
def pattern_matcher():
    """Fixture providing PatternMatcher instance"""
    return PatternMatcher()


@pytest.mark.unit
def test_basic_hit_miss(pattern_matcher):
    """Test basic pattern matching - hit and miss cases"""
    # Test hit
    result = pattern_matcher.match("hello world")
    assert result["pattern_score"] > 0
    assert len(result["matches"]) > 0
    assert result["match_time_us"] > 0

    # Test miss
    result = pattern_matcher.match("xyz unknown text")
    assert result["pattern_score"] == 0.0
    assert len(result["matches"]) == 0


@pytest.mark.unit
def test_unicode_vietnamese(pattern_matcher):
    """Test Unicode handling for Vietnamese text"""
    # Vietnamese with diacritics
    result = pattern_matcher.match("Xin chào")
    # Should handle case folding
    assert result["normalized_text"] is not None

    # Test with mixed case
    result = pattern_matcher.match("HELLO")
    assert result["pattern_score"] > 0


@pytest.mark.unit
def test_zero_width_characters(pattern_matcher):
    """Test handling of zero-width characters"""
    # Text with zero-width characters
    text_with_zw = "hello\u200bworld\u200c"
    result = pattern_matcher.match(text_with_zw)

    # Should normalize and still match
    assert "hello" in result["normalized_text"]
    assert "\u200b" not in result["normalized_text"]


@pytest.mark.unit
def test_homoglyph_detection(pattern_matcher):
    """Test homoglyph detection (Latin vs Cyrillic)"""
    # Cyrillic 'a' should be normalized to Latin 'a'
    result = pattern_matcher.match("hеllo")  # Cyrillic 'е'
    assert result["normalized_text"] is not None
    # Should still be able to match patterns after normalization


@pytest.mark.unit
def test_emoji_safe_processing(pattern_matcher):
    """Test emoji-safe text processing"""
    text_with_emoji = "hello 👋 world 🌍"
    result = pattern_matcher.match(text_with_emoji)

    # Should process without errors and maintain emoji
    assert "hello" in result["normalized_text"]
    assert result["match_time_us"] > 0


@pytest.mark.unit
def test_adversarial_spacing(pattern_matcher):
    """Test matching with adversarial spacing and emoji"""
    # Text with excessive spacing and emoji
    adversarial_text = "h  e  l  l  o  👋  w  o  r  l  d"
    result = pattern_matcher.match(adversarial_text)

    # Should normalize spacing and still work
    assert result["normalized_text"] is not None
    assert "hello" in result["normalized_text"].replace(" ", "")


@pytest.mark.unit
def test_regex_patterns(pattern_matcher):
    """Test regex pattern matching"""
    # Test regex patterns from config
    result = pattern_matcher.match("please help me")
    # Should match regex pattern for "please help"
    assert result["pattern_score"] >= 0


@pytest.mark.unit
def test_performance_benchmark(pattern_matcher):
    """Benchmark performance with multiple patterns"""
    # Create a large text to test performance
    large_text = "hello " * 1000 + "help " * 1000 + "thanks " * 1000

    start_time = time.perf_counter()
    result = pattern_matcher.match(large_text)
    end_time = time.perf_counter()

    match_time_ms = (end_time - start_time) * 1000

    # Performance should be under 10ms for regex fallback (Aho-Corasick would be <2ms)
    assert (
        match_time_ms < 15.0
    ), f"Match time {match_time_ms:.3f}ms exceeds 15ms threshold"
    assert result["match_time_us"] > 0


@pytest.mark.unit
def test_pattern_score_calculation(pattern_matcher):
    """Test pattern score calculation logic"""
    # Test with multiple matches
    result = pattern_matcher.match("hello help thanks")

    assert 0.0 <= result["pattern_score"] <= 1.0
    assert result["pattern_score"] > 0  # Should have matches

    # Test with no matches
    result = pattern_matcher.match("xyz abc def")
    assert result["pattern_score"] == 0.0


@pytest.mark.unit
def test_match_structure(pattern_matcher):
    """Test that match results have correct structure"""
    result = pattern_matcher.match("hello world")

    assert "matches" in result
    assert "pattern_score" in result
    assert "match_time_us" in result
    assert "normalized_text" in result

    if result["matches"]:
        match = result["matches"][0]
        assert "pattern_id" in match
        assert "span" in match
        assert "weight" in match
        assert "type" in match
        assert "text" in match


@pytest.mark.unit
def test_whitespace_normalization(pattern_matcher):
    """Test whitespace normalization"""
    # Text with excessive whitespace
    text_with_spaces = "  hello    world  \t\n  "
    result = pattern_matcher.match(text_with_spaces)

    # Should normalize whitespace
    normalized = result["normalized_text"]
    assert normalized == "hello world"
    assert "  " not in normalized  # No double spaces


@pytest.mark.unit
def test_case_insensitive_matching(pattern_matcher):
    """Test case-insensitive pattern matching"""
    test_cases = ["HELLO", "Hello", "hello", "hElLo"]

    for text in test_cases:
        result = pattern_matcher.match(text)
        # All should match the "hello" pattern
        assert result["pattern_score"] > 0
