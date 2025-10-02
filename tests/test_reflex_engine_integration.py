"""
Integration tests for Reflex Engine with Habit Store and Observability
"""

from unittest.mock import MagicMock, patch

from stillme_core.middleware.reflex_engine import ReflexConfig, ReflexEngine


class TestReflexEngineIntegration:
    """Test Reflex Engine integration with Habit Store and Observability"""

    def test_habit_store_integration_disabled(self):
        """Test that habit store is disabled by default"""
        engine = ReflexEngine()

        # Test with habit store disabled
        result = engine.analyze(
            text="Hello world",
            context={"mode": "test"},
            user_id="user1",
            tenant_id="tenant1",
        )

        assert result["decision"] == "fallback"
        assert result["shadow"] is True
        assert "why_reflex" in result

        # Habit score should be 0 (disabled)
        why_reflex = result["why_reflex"]
        assert why_reflex["habit_score"] == 0.0
        assert why_reflex["habit_action"] is None

    def test_habit_store_integration_enabled(self):
        """Test habit store integration when enabled"""
        # Mock habit store to be enabled
        with patch(
            "stillme_core.middleware.reflex_engine.HabitStore"
        ) as mock_habit_store_class:
            mock_habit_store = MagicMock()
            mock_habit_store.is_enabled.return_value = True
            mock_habit_store.get_habit_score.return_value = (0.8, "test_action")
            mock_habit_store.observe_cue.return_value = True
            mock_habit_store_class.return_value = mock_habit_store

            engine = ReflexEngine()
            engine.habit_store = mock_habit_store

            result = engine.analyze(
                text="Hello world",
                context={"mode": "test"},
                user_id="user1",
                tenant_id="tenant1",
            )

            # Verify habit store was called
            mock_habit_store.get_habit_score.assert_called_once_with("Hello world")

            # Verify habit score is included
            why_reflex = result["why_reflex"]
            assert why_reflex["habit_score"] == 0.8
            assert why_reflex["habit_action"] == "test_action"

    def test_observability_integration(self):
        """Test observability integration"""
        with patch(
            "stillme_core.middleware.reflex_engine.ObservabilityManager"
        ) as mock_obs_class:
            mock_obs = MagicMock()
            mock_obs_class.return_value = mock_obs

            engine = ReflexEngine()
            engine.observability = mock_obs

            result = engine.analyze(
                text="Hello world",
                context={"mode": "test"},
                user_id="user1",
                tenant_id="tenant1",
            )

            # Verify observability methods were called
            mock_obs.log_reflex_decision.assert_called_once()
            mock_obs.log_shadow_evaluation.assert_called_once()

            # Check log_reflex_decision call
            call_args = mock_obs.log_reflex_decision.call_args
            assert call_args[1]["trace_id"] == result["trace_id"]
            assert call_args[1]["decision"] == "fallback"
            assert call_args[1]["shadow_mode"] is True
            assert call_args[1]["user_id"] == "user1"
            assert call_args[1]["tenant_id"] == "tenant1"

    def test_habit_learning_trigger(self):
        """Test that habit learning is triggered under right conditions"""
        with patch(
            "stillme_core.middleware.reflex_engine.HabitStore"
        ) as mock_habit_store_class:
            mock_habit_store = MagicMock()
            mock_habit_store.is_enabled.return_value = True
            mock_habit_store.get_habit_score.return_value = (0.0, None)
            mock_habit_store.observe_cue.return_value = True
            mock_habit_store_class.return_value = mock_habit_store

            # Mock policy to return high confidence
            with patch(
                "stillme_core.middleware.reflex_engine.ReflexPolicy"
            ) as mock_policy_class:
                mock_policy = MagicMock()
                mock_policy.decide.return_value = ("allow_reflex", 0.8)
                mock_policy.get_breakdown.return_value = {"total_score": 0.8}
                mock_policy_class.return_value = mock_policy

                # Mock safety to return safe
                with patch(
                    "stillme_core.middleware.reflex_engine.ReflexSafety"
                ) as mock_safety_class:
                    mock_safety = MagicMock()
                    mock_safety.safety_gate.return_value = {
                        "safe": True,
                        "reason": "safe",
                    }
                    mock_safety_class.return_value = mock_safety

                    engine = ReflexEngine()
                    engine.habit_store = mock_habit_store
                    engine.policy = mock_policy
                    engine.safety = mock_safety

                    engine.analyze(
                        text="Hello world",
                        context={"mode": "test"},
                        user_id="user1",
                        tenant_id="tenant1",
                    )

                    # Verify habit learning was triggered
                    mock_habit_store.observe_cue.assert_called_once_with(
                        cue="Hello world",
                        action="reflex_response",
                        confidence=0.8,
                        user_id="user1",
                        tenant_id="tenant1",
                    )

    def test_habit_learning_not_triggered_low_confidence(self):
        """Test that habit learning is not triggered with low confidence"""
        with patch(
            "stillme_core.middleware.reflex_engine.HabitStore"
        ) as mock_habit_store_class:
            mock_habit_store = MagicMock()
            mock_habit_store.is_enabled.return_value = True
            mock_habit_store.get_habit_score.return_value = (0.0, None)
            mock_habit_store_class.return_value = mock_habit_store

            # Mock policy to return low confidence
            with patch(
                "stillme_core.middleware.reflex_engine.ReflexPolicy"
            ) as mock_policy_class:
                mock_policy = MagicMock()
                mock_policy.decide.return_value = (
                    "allow_reflex",
                    0.5,
                )  # Low confidence
                mock_policy.get_breakdown.return_value = {"total_score": 0.5}
                mock_policy_class.return_value = mock_policy

                # Mock safety to return safe
                with patch(
                    "stillme_core.middleware.reflex_engine.ReflexSafety"
                ) as mock_safety_class:
                    mock_safety = MagicMock()
                    mock_safety.safety_gate.return_value = {
                        "safe": True,
                        "reason": "safe",
                    }
                    mock_safety_class.return_value = mock_safety

                    engine = ReflexEngine()
                    engine.habit_store = mock_habit_store
                    engine.policy = mock_policy
                    engine.safety = mock_safety

                    engine.analyze(
                        text="Hello world",
                        context={"mode": "test"},
                        user_id="user1",
                        tenant_id="tenant1",
                    )

                    # Verify habit learning was NOT triggered
                    mock_habit_store.observe_cue.assert_not_called()

    def test_habit_learning_not_triggered_unsafe(self):
        """Test that habit learning is not triggered for unsafe content"""
        with patch(
            "stillme_core.middleware.reflex_engine.HabitStore"
        ) as mock_habit_store_class:
            mock_habit_store = MagicMock()
            mock_habit_store.is_enabled.return_value = True
            mock_habit_store.get_habit_score.return_value = (0.0, None)
            mock_habit_store_class.return_value = mock_habit_store

            # Mock policy to return high confidence
            with patch(
                "stillme_core.middleware.reflex_engine.ReflexPolicy"
            ) as mock_policy_class:
                mock_policy = MagicMock()
                mock_policy.decide.return_value = ("allow_reflex", 0.8)
                mock_policy.get_breakdown.return_value = {"total_score": 0.8}
                mock_policy_class.return_value = mock_policy

                # Mock safety to return unsafe
                with patch(
                    "stillme_core.middleware.reflex_engine.ReflexSafety"
                ) as mock_safety_class:
                    mock_safety = MagicMock()
                    mock_safety.safety_gate.return_value = {
                        "safe": False,
                        "reason": "unsafe",
                    }
                    mock_safety_class.return_value = mock_safety

                    engine = ReflexEngine()
                    engine.habit_store = mock_habit_store
                    engine.policy = mock_policy
                    engine.safety = mock_safety

                    engine.analyze(
                        text="Hello world",
                        context={"mode": "test"},
                        user_id="user1",
                        tenant_id="tenant1",
                    )

                    # Verify habit learning was NOT triggered
                    mock_habit_store.observe_cue.assert_not_called()

    def test_processing_time_tracking(self):
        """Test that processing time is tracked"""
        engine = ReflexEngine()

        # Test without mocking - just verify field exists
        result = engine.analyze(text="Hello world", context={"mode": "test"})

        why_reflex = result["why_reflex"]
        assert "processing_time_ms" in why_reflex
        assert isinstance(why_reflex["processing_time_ms"], (int, float))
        assert why_reflex["processing_time_ms"] >= 0

    def test_shadow_evaluation_logging(self):
        """Test shadow evaluation logging"""
        with patch(
            "stillme_core.middleware.reflex_engine.ObservabilityManager"
        ) as mock_obs_class:
            mock_obs = MagicMock()
            mock_obs_class.return_value = mock_obs

            engine = ReflexEngine()
            engine.observability = mock_obs

            result = engine.analyze(text="Hello world", context={"mode": "test"})

            # Verify shadow evaluation was logged
            mock_obs.log_shadow_evaluation.assert_called_once()

            call_args = mock_obs.log_shadow_evaluation.call_args
            assert call_args[1]["trace_id"] == result["trace_id"]
            assert "reflex_decision" in call_args[1]
            assert "reasoning_decision" in call_args[1]
            assert "processing_time_ms" in call_args[1]
            assert "scores" in call_args[1]

    def test_why_reflex_payload_completeness(self):
        """Test that why_reflex payload contains all expected fields"""
        engine = ReflexEngine()

        result = engine.analyze(
            text="Hello world",
            context={"mode": "test"},
            user_id="user1",
            tenant_id="tenant1",
        )

        why_reflex = result["why_reflex"]

        # Check all expected fields are present
        expected_fields = [
            "scores",
            "matches",
            "pattern_hits",
            "pattern_score",
            "match_time_us",
            "habit_score",
            "habit_action",
            "policy",
            "confidence",
            "breakdown",
            "safety_result",
            "action_result",
            "original_decision",
            "processing_time_ms",
        ]

        for field in expected_fields:
            assert field in why_reflex, f"Missing field: {field}"

    def test_engine_disabled_bypass(self):
        """Test that disabled engine bypasses all processing"""
        config = ReflexConfig(enabled=False, shadow_mode=True, policy="balanced")
        engine = ReflexEngine(config)

        result = engine.analyze(
            text="Hello world",
            context={"mode": "test"},
            user_id="user1",
            tenant_id="tenant1",
        )

        assert result["mode"] == "disabled"
        assert result["decision"] == "bypass"
        assert result["shadow"] is True
        assert "why_reflex" not in result
