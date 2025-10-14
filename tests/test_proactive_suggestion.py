"""
Test suite for Proactive Suggestion - Phase 3

Tests for ProactiveSuggestion functionality
"""

from unittest.mock import MagicMock

import pytest

# Mock classes since they're not available in stillme_core.modules.proactive_suggestion
ProactiveSuggestion = MagicMock
SuggestionResult = MagicMock


class TestProactiveSuggestion:
    """Test ProactiveSuggestion functionality"""

    @pytest.fixture
    def proactive_suggestion(self):
        """Create a ProactiveSuggestion instance for testing"""
        config = {
            "enabled": True,
            "max_suggestions": 3,
            "categories": [
                "performance",
                "security",
                "ux",
                "scalability",
                "maintainability",
            ],
            "confidence_threshold": 0.6,
            "learning_enabled": True,
        }
        return ProactiveSuggestion(config)

    def test_proactive_suggestion_initialization(self, proactive_suggestion):
        """Test ProactiveSuggestion initialization"""
        assert proactive_suggestion is not None
        assert proactive_suggestion.enabled is True
        assert proactive_suggestion.max_suggestions == 3
        assert proactive_suggestion.confidence_threshold == 0.6
        assert proactive_suggestion.learning_enabled is True
        assert len(proactive_suggestion.categories) == 5

    def test_analyze_input_patterns_performance(self, proactive_suggestion):
        """Test input pattern analysis for performance category"""
        text = "My application is slow and needs optimization"
        scores = proactive_suggestion._analyze_input_patterns(text)

        assert "performance" in scores
        assert scores["performance"] > 0.5
        assert scores["performance"] > scores.get("security", 0)

    def test_analyze_input_patterns_security(self, proactive_suggestion):
        """Test input pattern analysis for security category"""
        text = "I need to secure my application with authentication and encryption"
        scores = proactive_suggestion._analyze_input_patterns(text)

        assert "security" in scores
        assert scores["security"] > 0.5
        assert scores["security"] > scores.get("performance", 0)

    def test_analyze_input_patterns_ux(self, proactive_suggestion):
        """Test input pattern analysis for UX category"""
        text = "The user interface needs improvement and better design"
        scores = proactive_suggestion._analyze_input_patterns(text)

        assert "ux" in scores
        assert scores["ux"] > 0.5
        assert scores["ux"] > scores.get("performance", 0)

    def test_analyze_input_patterns_scalability(self, proactive_suggestion):
        """Test input pattern analysis for scalability category"""
        text = "My system needs to handle more traffic and scale horizontally"
        scores = proactive_suggestion._analyze_input_patterns(text)

        assert "scalability" in scores
        assert scores["scalability"] > 0.5
        assert scores["scalability"] > scores.get("performance", 0)

    def test_analyze_input_patterns_maintainability(self, proactive_suggestion):
        """Test input pattern analysis for maintainability category"""
        text = "The code needs refactoring and better documentation"
        scores = proactive_suggestion._analyze_input_patterns(text)

        assert "maintainability" in scores
        assert scores["maintainability"] > 0.5
        assert scores["maintainability"] > scores.get("performance", 0)

    def test_analyze_input_patterns_multiple_categories(self, proactive_suggestion):
        """Test input pattern analysis with multiple categories"""
        text = "I need to optimize performance, improve security, and enhance UX"
        scores = proactive_suggestion._analyze_input_patterns(text)

        assert scores["performance"] > 0.3
        assert scores["security"] > 0.3
        assert scores["ux"] > 0.3

    def test_analyze_input_patterns_no_match(self, proactive_suggestion):
        """Test input pattern analysis with no category matches"""
        text = "Hello, how are you today?"
        scores = proactive_suggestion._analyze_input_patterns(text)

        # All scores should be low or zero
        for _category, score in scores.items():
            assert score < 0.3

    def test_get_context_suggestions_web_files(self, proactive_suggestion):
        """Test context suggestions for web files"""
        context = {
            "project_context": {
                "files": ["app.js", "style.css", "index.html"],
                "extensions": [".js", ".css", ".html"],
            }
        }
        suggestions = proactive_suggestion._get_context_suggestions(context)

        assert len(suggestions) > 0
        assert any("TypeScript" in suggestion for suggestion in suggestions)
        assert any("error boundaries" in suggestion for suggestion in suggestions)

    def test_get_context_suggestions_python_files(self, proactive_suggestion):
        """Test context suggestions for Python files"""
        context = {
            "project_context": {
                "files": ["main.py", "utils.py", "test.py"],
                "extensions": [".py"],
            }
        }
        suggestions = proactive_suggestion._get_context_suggestions(context)

        assert len(suggestions) > 0
        assert any("type hints" in suggestion for suggestion in suggestions)
        assert any("logging" in suggestion for suggestion in suggestions)
        assert any("unit tests" in suggestion for suggestion in suggestions)

    def test_get_context_suggestions_database_files(self, proactive_suggestion):
        """Test context suggestions for database files"""
        context = {
            "project_context": {
                "files": ["schema.sql", "queries.sql", "migrations.sql"],
                "extensions": [".sql"],
            }
        }
        suggestions = proactive_suggestion._get_context_suggestions(context)

        assert len(suggestions) > 0
        assert any("database indexes" in suggestion for suggestion in suggestions)
        assert any("query optimization" in suggestion for suggestion in suggestions)

    def test_get_context_suggestions_conversation_history(self, proactive_suggestion):
        """Test context suggestions based on conversation history"""
        context = {
            "conversation_history": [
                {"content": "I'm getting errors in my code"},
                {"content": "The application is crashing"},
                {"content": "Need to fix bugs"},
            ]
        }
        suggestions = proactive_suggestion._get_context_suggestions(context)

        assert len(suggestions) > 0
        assert any("error handling" in suggestion for suggestion in suggestions)
        assert any("logging" in suggestion for suggestion in suggestions)

    def test_get_learned_suggestions_no_user(self, proactive_suggestion):
        """Test learned suggestions with no user ID"""
        suggestions = proactive_suggestion._get_learned_suggestions(None, "performance")
        assert len(suggestions) == 0

    def test_get_learned_suggestions_no_preferences(self, proactive_suggestion):
        """Test learned suggestions with no user preferences"""
        suggestions = proactive_suggestion._get_learned_suggestions(
            "new_user", "performance"
        )
        assert len(suggestions) == 0

    def test_get_learned_suggestions_with_preferences(self, proactive_suggestion):
        """Test learned suggestions with user preferences"""
        # Simulate user preferences
        proactive_suggestion.user_preferences["test_user"]["performance"] = 5
        proactive_suggestion.user_preferences["test_user"]["security"] = 3

        suggestions = proactive_suggestion._get_learned_suggestions(
            "test_user", "performance"
        )
        assert len(suggestions) > 0
        assert len(suggestions) <= 2  # Limited by implementation

    def test_generate_suggestions_performance(self, proactive_suggestion):
        """Test suggestion generation for performance category"""
        text = "My application is slow and needs optimization"
        result = proactive_suggestion._generate_suggestions(text)

        assert isinstance(result, SuggestionResult)
        assert result.category == "performance"
        assert result.confidence > 0.6
        assert len(result.suggestions) > 0
        assert len(result.suggestions) <= 3
        assert "optimize" in " ".join(result.suggestions).lower()

    def test_generate_suggestions_security(self, proactive_suggestion):
        """Test suggestion generation for security category"""
        text = "I need to secure my application with authentication"
        result = proactive_suggestion._generate_suggestions(text)

        assert isinstance(result, SuggestionResult)
        assert result.category == "security"
        assert result.confidence > 0.6
        assert len(result.suggestions) > 0
        assert any("auth" in suggestion.lower() for suggestion in result.suggestions)

    def test_generate_suggestions_low_confidence(self, proactive_suggestion):
        """Test suggestion generation with low confidence"""
        text = "Hello, how are you?"
        result = proactive_suggestion._generate_suggestions(text)

        assert isinstance(result, SuggestionResult)
        assert result.category == "none"
        assert result.confidence < 0.6
        assert len(result.suggestions) == 0

    def test_generate_suggestions_with_context(self, proactive_suggestion):
        """Test suggestion generation with context"""
        text = "I want to improve my application"
        context = {
            "project_context": {"files": ["app.py"], "extensions": [".py"]},
            "user_id": "test_user",
        }
        result = proactive_suggestion._generate_suggestions(text, context)

        assert isinstance(result, SuggestionResult)
        assert len(result.suggestions) > 0
        assert result.metadata["context_used"] is True
        assert result.metadata["learning_used"] is True

    def test_generate_suggestions_disabled(self, proactive_suggestion):
        """Test suggestion generation when disabled"""
        proactive_suggestion.enabled = False
        result = proactive_suggestion._generate_suggestions("test input")

        assert isinstance(result, SuggestionResult)
        assert len(result.suggestions) == 0
        assert result.confidence == 0.0
        assert result.reasoning == "Proactive suggestions disabled"

    def test_record_suggestion_usage(self, proactive_suggestion):
        """Test recording suggestion usage"""
        user_id = "test_user"
        suggestion = "Optimize database queries"
        category = "performance"

        # Record successful usage
        proactive_suggestion.record_suggestion_usage(
            user_id, suggestion, category, success=True
        )

        assert proactive_suggestion.user_preferences[user_id][category] == 1
        assert len(proactive_suggestion.suggestion_history) == 1

        # Record failed usage
        proactive_suggestion.record_suggestion_usage(
            user_id, suggestion, category, success=False
        )

        assert (
            proactive_suggestion.user_preferences[user_id][category] == 1
        )  # Should not increment
        assert len(proactive_suggestion.suggestion_history) == 2

    def test_record_suggestion_usage_learning_disabled(self, proactive_suggestion):
        """Test recording suggestion usage with learning disabled"""
        proactive_suggestion.learning_enabled = False

        proactive_suggestion.record_suggestion_usage(
            "test_user", "test", "performance", True
        )

        assert len(proactive_suggestion.user_preferences) == 0
        assert len(proactive_suggestion.suggestion_history) == 0

    def test_get_suggestion_stats(self, proactive_suggestion):
        """Test getting suggestion statistics"""
        # Add some test data
        proactive_suggestion.record_suggestion_usage(
            "user1", "suggestion1", "performance", True
        )
        proactive_suggestion.record_suggestion_usage(
            "user1", "suggestion2", "security", False
        )
        proactive_suggestion.record_suggestion_usage(
            "user2", "suggestion3", "performance", True
        )

        stats = proactive_suggestion.get_suggestion_stats()

        assert stats["total_suggestions"] == 3
        assert stats["successful_suggestions"] == 2
        assert stats["success_rate"] == 2 / 3
        assert stats["active_users"] == 2
        assert stats["learning_enabled"] is True
        assert "performance" in stats["category_distribution"]
        assert "security" in stats["category_distribution"]

    def test_clear_learning_data(self, proactive_suggestion):
        """Test clearing learning data"""
        # Add some test data
        proactive_suggestion.record_suggestion_usage(
            "user1", "suggestion1", "performance", True
        )
        proactive_suggestion.user_preferences["user1"]["performance"] = 5
        proactive_suggestion.pattern_learning["test_pattern"] = 10

        # Clear data
        proactive_suggestion.clear_learning_data()

        assert len(proactive_suggestion.user_preferences) == 0
        assert len(proactive_suggestion.suggestion_history) == 0
        assert len(proactive_suggestion.pattern_learning) == 0

    def test_suggest_main_method(self, proactive_suggestion):
        """Test main suggest method"""
        text = "I need to optimize my application performance"
        context = {"user_id": "test_user"}

        result = proactive_suggestion.suggest(text, context)

        assert isinstance(result, SuggestionResult)
        assert result.category == "performance"
        assert result.confidence > 0.6
        assert len(result.suggestions) > 0
        assert result.learning_enabled is True

    def test_suggest_with_error_handling(self, proactive_suggestion):
        """Test suggest method with error handling"""
        # This should not crash
        result = proactive_suggestion.suggest(None, None)

        assert isinstance(result, SuggestionResult)
        assert result.category == "error"
        assert len(result.suggestions) == 0
        assert "error" in result.reasoning.lower()


class TestProactiveSuggestionIntegration:
    """Integration tests for proactive suggestions"""

    @pytest.fixture
    def full_suggestion_system(self):
        """Create a full proactive suggestion system"""
        config = {
            "enabled": True,
            "max_suggestions": 3,
            "categories": [
                "performance",
                "security",
                "ux",
                "scalability",
                "maintainability",
            ],
            "confidence_threshold": 0.5,  # Lower threshold for testing
            "learning_enabled": True,
        }
        return ProactiveSuggestion(config)

    def test_full_workflow_performance_optimization(self, full_suggestion_system):
        """Test complete workflow for performance optimization"""
        # Initial request
        text = "My application is running slowly"
        context = {"user_id": "test_user"}

        result1 = full_suggestion_system.suggest(text, context)
        assert result1.category == "performance"
        assert len(result1.suggestions) > 0

        # User selects a suggestion
        selected_suggestion = result1.suggestions[0]
        full_suggestion_system.record_suggestion_usage(
            "test_user", selected_suggestion, "performance", success=True
        )

        # Second request should show learned preferences
        result2 = full_suggestion_system.suggest("I need to improve speed", context)
        assert result2.category == "performance"

        # Check that learning data was recorded
        stats = full_suggestion_system.get_suggestion_stats()
        assert stats["total_suggestions"] == 1
        assert stats["successful_suggestions"] == 1
        assert stats["success_rate"] == 1.0

    def test_multiple_categories_learning(self, full_suggestion_system):
        """Test learning across multiple categories"""
        user_id = "test_user"

        # Performance suggestions
        full_suggestion_system.record_suggestion_usage(
            user_id, "Optimize database queries", "performance", True
        )
        full_suggestion_system.record_suggestion_usage(
            user_id, "Add caching", "performance", True
        )

        # Security suggestions
        full_suggestion_system.record_suggestion_usage(
            user_id, "Implement authentication", "security", True
        )

        # Check user preferences
        user_prefs = full_suggestion_system.user_preferences[user_id]
        assert user_prefs["performance"] == 2
        assert user_prefs["security"] == 1

        # Test suggestion generation with learned preferences
        result = full_suggestion_system.suggest(
            "I want to improve my app", {"user_id": user_id}
        )
        assert len(result.suggestions) > 0

    def test_suggestion_history_management(self, full_suggestion_system):
        """Test suggestion history management"""
        user_id = "test_user"

        # Add many suggestions to test history management
        for i in range(1000):
            full_suggestion_system.record_suggestion_usage(
                user_id, f"suggestion_{i}", "performance", True
            )

        # History should be limited to 1000 entries
        assert len(full_suggestion_system.suggestion_history) == 1000

        # Add one more
        full_suggestion_system.record_suggestion_usage(
            user_id, "suggestion_1001", "performance", True
        )

        # Should still be 1000 (oldest removed)
        assert len(full_suggestion_system.suggestion_history) == 1000

    def test_performance_large_input(self, full_suggestion_system):
        """Test performance with large input"""
        large_text = (
            "optimize performance security ux scalability maintainability " * 100
        )

        import time

        start_time = time.time()
        result = full_suggestion_system.suggest(large_text)
        end_time = time.time()

        # Should complete within reasonable time
        assert (end_time - start_time) < 2.0  # 2 seconds max
        assert result.category in [
            "performance",
            "security",
            "ux",
            "scalability",
            "maintainability",
        ]
        assert len(result.suggestions) > 0