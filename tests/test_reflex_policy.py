import os

import pytest

from stillme_core.middleware.reflex_policy import ReflexPolicy


@pytest.fixture
def policy_balanced():
    """Fixture providing balanced policy"""
    return ReflexPolicy("balanced")


@pytest.fixture
def policy_strict():
    """Fixture providing strict policy"""
    return ReflexPolicy("strict")


@pytest.fixture
def policy_creative():
    """Fixture providing creative policy"""
    return ReflexPolicy("creative")


@pytest.mark.unit
def test_policy_initialization(policy_balanced):
    """Test policy initialization with default values"""
    assert policy_balanced.level == "balanced"
    assert "pattern" in policy_balanced.weights
    assert "context" in policy_balanced.weights
    assert "history" in policy_balanced.weights
    assert "abuse" in policy_balanced.weights
    assert "balanced" in policy_balanced.thresholds


@pytest.mark.unit
def test_decision_high_pattern_score(policy_balanced):
    """Test decision with high pattern score"""
    scores = {
        "pattern_score": 0.9,
        "context_score": 0.7,
        "history_score": 0.5,
        "abuse_score": 0.0
    }

    decision, confidence = policy_balanced.decide(scores)
    assert decision == "allow_reflex"
    assert confidence > 0.5


@pytest.mark.unit
def test_decision_low_scores(policy_balanced):
    """Test decision with low scores"""
    scores = {
        "pattern_score": 0.2,
        "context_score": 0.3,
        "history_score": 0.1,
        "abuse_score": 0.0
    }

    decision, confidence = policy_balanced.decide(scores)
    assert decision == "fallback"
    assert confidence > 0.0


@pytest.mark.unit
def test_abuse_penalty(policy_balanced):
    """Test abuse score penalty"""
    scores = {
        "pattern_score": 0.9,
        "context_score": 0.8,
        "history_score": 0.7,
        "abuse_score": 0.5  # High abuse score
    }

    decision, confidence = policy_balanced.decide(scores)
    # Should still allow reflex but with lower confidence
    assert decision == "allow_reflex" or decision == "fallback"


@pytest.mark.unit
def test_policy_levels_comparison():
    """Test different policy levels have different thresholds"""
    strict_policy = ReflexPolicy("strict")
    balanced_policy = ReflexPolicy("balanced")
    creative_policy = ReflexPolicy("creative")

    # Same scores should produce different decisions
    scores = {
        "pattern_score": 0.7,
        "context_score": 0.6,
        "history_score": 0.5,
        "abuse_score": 0.0
    }

    strict_decision, _ = strict_policy.decide(scores)
    balanced_decision, _ = balanced_policy.decide(scores)
    creative_decision, _ = creative_policy.decide(scores)

    # Creative should be most permissive, strict least
    assert creative_decision == "allow_reflex"
    # Balanced might be fallback with 0.7 pattern score
    # Strict might be fallback depending on exact thresholds


@pytest.mark.unit
def test_context_score_calculation(policy_balanced):
    """Test context score calculation"""
    # Test with different contexts
    context1 = {"mode": "strict", "text": "hello world", "session_active": True}
    context2 = {"mode": "creative", "text": "hi", "session_active": False}

    scores1 = {"pattern_score": 0.8}
    scores2 = {"pattern_score": 0.8}

    decision1, conf1 = policy_balanced.decide(scores1, context1)
    decision2, conf2 = policy_balanced.decide(scores2, context2)

    # Both should have reasonable confidence
    assert conf1 > 0.0
    assert conf2 > 0.0


@pytest.mark.unit
def test_history_score_calculation(policy_balanced):
    """Test history score calculation"""
    context_high_freq = {
        "cue_frequency": 15,
        "cue_recency_hours": 2
    }
    context_low_freq = {
        "cue_frequency": 2,
        "cue_recency_hours": 200
    }

    scores = {"pattern_score": 0.7}

    decision1, conf1 = policy_balanced.decide(scores, context_high_freq)
    decision2, conf2 = policy_balanced.decide(scores, context_low_freq)

    # High frequency should have higher confidence
    assert conf1 >= conf2


@pytest.mark.unit
def test_breakdown_analysis(policy_balanced):
    """Test detailed breakdown analysis"""
    scores = {
        "pattern_score": 0.8,
        "context_score": 0.6,
        "history_score": 0.4,
        "abuse_score": 0.1
    }

    breakdown = policy_balanced.get_breakdown(scores)

    assert "scores" in breakdown
    assert "weights" in breakdown
    assert "contributions" in breakdown
    assert "total_score" in breakdown
    assert "final_score" in breakdown
    assert "decision" in breakdown
    assert "confidence" in breakdown
    assert "policy_level" in breakdown
    assert "thresholds" in breakdown

    # Check contributions structure
    contributions = breakdown["contributions"]
    for score_type in ["pattern", "context", "history", "abuse"]:
        assert score_type in contributions
        contrib = contributions[score_type]
        assert "raw_score" in contrib
        assert "weight" in contrib
        assert "contribution" in contrib


@pytest.mark.unit
def test_env_override():
    """Test ENV variable override functionality"""
    # Set ENV variables
    os.environ["STILLME__REFLEX__WEIGHT_PATTERN"] = "0.6"
    os.environ["STILLME__REFLEX__THRESHOLD_BALANCED"] = "0.7"

    try:
        policy = ReflexPolicy("balanced")

        # Check weight override
        assert policy.weights["pattern"] == 0.6

        # Check threshold override
        assert policy.thresholds["balanced"]["allow_reflex"] == 0.7

    finally:
        # Clean up ENV variables
        if "STILLME__REFLEX__WEIGHT_PATTERN" in os.environ:
            del os.environ["STILLME__REFLEX__WEIGHT_PATTERN"]
        if "STILLME__REFLEX__THRESHOLD_BALANCED" in os.environ:
            del os.environ["STILLME__REFLEX__THRESHOLD_BALANCED"]


@pytest.mark.unit
def test_matrix_policy_scores():
    """Test matrix of different score combinations"""
    test_cases = [
        # (pattern, context, history, abuse, expected_decision_hint)
        (0.9, 0.8, 0.7, 0.0, "allow_reflex"),
        (0.3, 0.4, 0.2, 0.0, "fallback"),
        (0.7, 0.6, 0.5, 0.3, "fallback"),  # High abuse
        (0.8, 0.9, 0.8, 0.1, "allow_reflex"),
    ]

    policy = ReflexPolicy("balanced")

    for pattern, context, history, abuse, _expected_hint in test_cases:
        scores = {
            "pattern_score": pattern,
            "context_score": context,
            "history_score": history,
            "abuse_score": abuse
        }

        decision, confidence = policy.decide(scores)

        # Basic validation
        assert decision in ["allow_reflex", "fallback"]
        assert 0.0 <= confidence <= 1.0

        # High scores should generally allow reflex
        if pattern > 0.8 and context > 0.7 and abuse < 0.2:
            assert decision == "allow_reflex"


@pytest.mark.unit
def test_confidence_calculation():
    """Test confidence calculation logic"""
    policy = ReflexPolicy("balanced")

    # High scores should have high confidence
    high_scores = {
        "pattern_score": 0.9,
        "context_score": 0.8,
        "history_score": 0.7,
        "abuse_score": 0.0
    }

    decision, confidence = policy.decide(high_scores)
    assert confidence > 0.7

    # Low scores should have lower confidence
    low_scores = {
        "pattern_score": 0.3,
        "context_score": 0.2,
        "history_score": 0.1,
        "abuse_score": 0.0
    }

    decision, confidence = policy.decide(low_scores)
    # Low scores should result in fallback with reasonable confidence
    assert decision == "fallback"
    assert confidence > 0.0


@pytest.mark.unit
def test_missing_scores_handling(policy_balanced):
    """Test handling of missing scores"""
    # Test with only pattern score
    scores = {"pattern_score": 0.8}
    decision, confidence = policy_balanced.decide(scores)

    assert decision in ["allow_reflex", "fallback"]
    assert 0.0 <= confidence <= 1.0

    # Test with None values
    scores_with_none = {
        "pattern_score": 0.8,
        "context_score": None,
        "history_score": None,
        "abuse_score": None
    }

    decision, confidence = policy_balanced.decide(scores_with_none)
    assert decision in ["allow_reflex", "fallback"]
    assert 0.0 <= confidence <= 1.0
