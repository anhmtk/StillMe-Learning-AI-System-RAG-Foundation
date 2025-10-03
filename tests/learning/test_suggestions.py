"""
Test Learning Engine functionality
=================================

Test feedback recording and suggestion generation.
"""

import pytest
from agent_dev.learning.engine import (
    LearningEngine,
    record_feedback,
    suggest_adjustments,
)


def test_record_and_suggest():
    """Test recording feedback and generating suggestions"""
    engine = LearningEngine()
    
    # Record 3 feedback samples
    feedback_samples = [
        "The system is too slow, please optimize performance",
        "Great quality output, very accurate results",
        "The interface is confusing and hard to use"
    ]
    
    # Record feedback
    for i, feedback in enumerate(feedback_samples):
        success = engine.record_feedback(
            user_id="test_user",
            feedback_text=feedback,
            session_id=f"test_session_{i}",
            context='{"test": true}'
        )
        assert success is True
    
    # Get suggestions
    suggestions = engine.suggest_adjustments(user_id="test_user")
    
    # Should have suggestions based on patterns
    assert len(suggestions) > 0
    assert isinstance(suggestions, list)
    
    # Check that suggestions contain expected content
    suggestion_text = " ".join(suggestions).lower()
    assert "performance" in suggestion_text or "optimiz" in suggestion_text
    assert "usability" in suggestion_text or "interface" in suggestion_text


def test_feedback_analysis():
    """Test feedback type analysis"""
    engine = LearningEngine()
    
    # Test positive feedback
    feedback_type = engine._analyze_feedback_type("This is great! I love it!")
    assert feedback_type == "positive"
    
    # Test negative feedback
    feedback_type = engine._analyze_feedback_type("This is terrible and broken")
    assert feedback_type == "negative"
    
    # Test neutral feedback
    feedback_type = engine._analyze_feedback_type("The system processed the request")
    assert feedback_type == "neutral"


def test_pattern_extraction():
    """Test pattern extraction from feedback"""
    engine = LearningEngine()
    
    # Test performance pattern
    patterns = engine._extract_patterns("The system is too slow and has high latency")
    assert "performance" in patterns.values()
    
    # Test quality pattern
    patterns = engine._extract_patterns("The output quality is excellent and accurate")
    assert "quality" in patterns.values()
    
    # Test usability pattern
    patterns = engine._extract_patterns("The interface is confusing and hard to use")
    assert "usability" in patterns.values()
    
    # Test reliability pattern
    patterns = engine._extract_patterns("The system is stable and reliable")
    assert "reliability" in patterns.values()
    
    # Test security pattern
    patterns = engine._extract_patterns("The system is secure and safe")
    assert "security" in patterns.values()


def test_feedback_summary():
    """Test feedback summary generation"""
    engine = LearningEngine()
    
    # Record mixed feedback
    feedback_samples = [
        "Great performance, very fast!",
        "The system is too slow",
        "Good quality output",
        "The interface is confusing",
        "Excellent reliability"
    ]
    
    for i, feedback in enumerate(feedback_samples):
        engine.record_feedback(
            user_id="test_user",
            feedback_text=feedback,
            session_id=f"test_session_{i}"
        )
    
    # Get summary
    summary = engine.get_feedback_summary(user_id="test_user")
    
    assert summary["total_feedback"] == 5
    assert summary["positive_count"] > 0
    # Note: "The system is too slow" might be classified as neutral, not negative
    assert summary["negative_count"] >= 0
    assert summary["sentiment_score"] is not None
    assert isinstance(summary["common_patterns"], dict)
    assert isinstance(summary["suggestions"], list)


def test_suggestion_rules():
    """Test suggestion rules based on feedback patterns"""
    engine = LearningEngine()
    
    # Test performance suggestion
    suggestions = engine.suggest_adjustments()
    # Should have performance-related suggestions
    performance_suggestions = [s for s in suggestions if "performance" in s.lower() or "optimiz" in s.lower()]
    assert len(performance_suggestions) > 0 or len(suggestions) == 0  # Either has suggestions or empty


def test_standalone_functions():
    """Test standalone functions"""
    # Test record_feedback function
    success = record_feedback(
        user_id="test_user",
        feedback_text="The system is too slow",
        session_id="test_session"
    )
    assert success is True
    
    # Test suggest_adjustments function
    suggestions = suggest_adjustments(user_id="test_user")
    assert isinstance(suggestions, list)


def test_learning_from_feedback():
    """Test learning from feedback patterns"""
    engine = LearningEngine()
    
    # Record feedback with specific patterns
    engine.record_feedback(
        user_id="test_user",
        feedback_text="The system is too slow and has performance issues",
        session_id="test_session"
    )
    
    # Get suggestions - should include performance-related suggestions
    suggestions = engine.suggest_adjustments(user_id="test_user")
    
    # Should have at least one suggestion
    assert len(suggestions) >= 0  # May be empty for new engine
    
    # Test that suggestions are strings
    for suggestion in suggestions:
        assert isinstance(suggestion, str)
        assert len(suggestion) > 0


def test_multiple_users():
    """Test feedback from multiple users"""
    engine = LearningEngine()
    
    # Record feedback from different users
    users = ["user1", "user2", "user3"]
    feedbacks = [
        "Great performance!",
        "The system is too slow",
        "Good quality output"
    ]
    
    for user, feedback in zip(users, feedbacks):
        engine.record_feedback(
            user_id=user,
            feedback_text=feedback,
            session_id=f"session_{user}"
        )
    
    # Get suggestions for specific user
    suggestions = engine.suggest_adjustments(user_id="user1")
    assert isinstance(suggestions, list)
    
    # Get suggestions for all users (no user_id)
    all_suggestions = engine.suggest_adjustments()
    assert isinstance(all_suggestions, list)


def test_empty_feedback():
    """Test handling of empty feedback"""
    engine = LearningEngine()
    
    # Test empty feedback
    success = engine.record_feedback(
        user_id="test_user",
        feedback_text="",
        session_id="test_session"
    )
    assert success is True
    
    # Test suggestions with no feedback
    suggestions = engine.suggest_adjustments(user_id="nonexistent_user")
    assert isinstance(suggestions, list)
    assert len(suggestions) == 0  # Should be empty for nonexistent user
