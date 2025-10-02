"""
Reflex Engine (Phase 1 - Shadow Mode)

Purpose:
- Orchestrator for Habit + Safety Reflex Engine in shadow mode only.
- Computes decision skeleton and always falls back to reasoning.

Notes:
- Shadow mode means: never perform side-effects or real actions.
- This skeleton wires configuration, trace_id, logging, and stubs.

Bilingual comments are omitted per repo standardization to English.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

# Local imports (stubs for Phase 1)
try:
    from .pattern_matcher import PatternMatcher
except Exception:  # pragma: no cover - pattern matcher will be added in next prompts
    class PatternMatcher:  # type: ignore
        def __init__(self, config: Dict[str, Any] | None = None):
            self.config = config or {}

        def match(self, text: str, context: Dict[str, Any] | None = None) -> Dict[str, Any]:
            return {"matches": [], "pattern_score": None}

try:
    from .reflex_policy import ReflexPolicy
except Exception:  # pragma: no cover
    class ReflexPolicy:  # type: ignore
        def __init__(self, policy_level: str = "balanced"):
            self.level = policy_level

        def decide(self, scores: Dict[str, Optional[float]]) -> Tuple[str, float]:
            # Return (decision, confidence). Shadow: always fallback
            return "fallback", 0.0

try:
    from .reflex_safety import ReflexSafety
except Exception:  # pragma: no cover
    class ReflexSafety:  # type: ignore
        def quick_check(self, text: str) -> bool:
            return True

        async def deep_check(self, text: str) -> bool:
            return True

        def safety_gate(self, text: str, intended_action: Optional[str] = None,
                       scores: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
            return {"safe": True, "reason": "stub_safety"}

try:
    from .action_sandbox import ActionSandbox
except Exception:  # pragma: no cover
    class ActionSandbox:  # type: ignore
        def __init__(self, config: Optional[Dict[str, Any]] = None):
            self.config = config or {}
            self.dry_run = self.config.get("dry_run", True)

        def execute(self, action: str, params: Dict[str, Any], trace_id: str,
                   dry_run: Optional[bool] = None) -> Dict[str, Any]:
            return {"ok": True, "dry_run": self.dry_run, "action": action, "params": params}

try:
    from .habit_store import HabitStore
except Exception:  # pragma: no cover
    class HabitStore:  # type: ignore
        def __init__(self, config: Optional[Dict[str, Any]] = None):
            self.config = config or {}

        def is_enabled(self) -> bool:
            return False

        def get_habit_score(self, cue: str) -> Tuple[float, Optional[str]]:
            return 0.0, None

        def observe_cue(self, cue: str, action: str, confidence: float = 1.0,
                       user_id: Optional[str] = None, tenant_id: Optional[str] = None) -> bool:
            return False

try:
    from .observability import ObservabilityManager
except Exception:  # pragma: no cover
    class ObservabilityManager:  # type: ignore
        def __init__(self, config: Optional[Dict[str, Any]] = None):
            self.config = config or {}

        def log_reflex_decision(self, trace_id: str, decision: str, confidence: float,
                               processing_time_ms: float, scores: Dict[str, float],
                               why_reflex: Dict[str, Any], user_id: Optional[str] = None,
                               tenant_id: Optional[str] = None, shadow_mode: bool = True):
            pass

        def log_shadow_evaluation(self, trace_id: str, reflex_decision: str,
                                 reasoning_decision: str, processing_time_ms: float,
                                 scores: Dict[str, float]):
            pass


logger = logging.getLogger(__name__)


@dataclass
class ReflexConfig:
    enabled: bool = True
    shadow_mode: bool = True
    policy: str = "balanced"


def _load_config_from_yaml() -> ReflexConfig:
    try:
        import yaml  # lazy import

        with open("config/reflex_engine.yaml", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        enabled = bool(cfg.get("enabled", True))
        shadow = bool(cfg.get("shadow_mode", True))
        policy = str(cfg.get("policy", "balanced"))
        return ReflexConfig(enabled=enabled, shadow_mode=shadow, policy=policy)
    except Exception as e:  # pragma: no cover - default on missing config
        logger.warning(f"Reflex config load failed, using defaults: {e}")
        return ReflexConfig()


class ReflexEngine:
    """Shadow-mode Reflex Engine orchestrator"""

    def __init__(self, config: Optional[ReflexConfig] = None) -> None:
        self.config = config or _load_config_from_yaml()
        self.matcher = PatternMatcher({})
        self.policy = ReflexPolicy(self.config.policy)
        self.safety = ReflexSafety()
        self.sandbox = ActionSandbox({"dry_run": True})
        self.habit_store = HabitStore({})
        self.observability = ObservabilityManager({})

    @staticmethod
    def _new_trace_id() -> str:
        return f"reflex_{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}"

    def analyze(
        self,
        *,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze input with shadow reflex logic and ALWAYS fallback.
        Returns a dict containing trace_id and decision metadata.
        """
        start_time = time.time()
        trace_id = self._new_trace_id()

        if not self.config.enabled:
            return {
                "trace_id": trace_id,
                "mode": "disabled",
                "shadow": self.config.shadow_mode,
                "decision": "bypass",
            }

        # Step 1: Safety gate (fast + deep checks)
        safety_result = self.safety.safety_gate(text, intended_action="reflex_decision", scores=None)

        # Step 2: pattern match (real implementation)
        match_result = self.matcher.match(text, context or {})

        # Step 3: Get habit score (if habit store enabled)
        habit_score, habit_action = self.habit_store.get_habit_score(text)

        scores = {
            "pattern_score": match_result.get("pattern_score"),
            "context_score": None,
            "history_score": habit_score,  # Use habit score as history score
            "abuse_score": None,
        }

        # Step 4: policy decision with context
        decision, confidence = self.policy.decide(scores, context)

        # Step 5: Action sandbox (if policy allows reflex)
        action_result = None
        if decision == "allow_reflex" and safety_result.get("safe", False):
            # In shadow mode, always execute in dry_run
            action_result = self.sandbox.execute(
                action="reflex_response",
                params={"text": text, "scores": scores, "context": context},
                trace_id=trace_id,
                dry_run=True  # Always dry_run in shadow mode
            )

        # Shadow mode: enforce fallback, never act
        original_decision = decision
        decision = "fallback"

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Prepare why_reflex payload
        why_reflex = {
            "scores": scores,
            "matches": match_result.get("matches", []),
            "pattern_hits": len(match_result.get("matches", [])),
            "pattern_score": match_result.get("pattern_score"),
            "match_time_us": match_result.get("match_time_us"),
            "habit_score": habit_score,
            "habit_action": habit_action,
            "policy": self.config.policy,
            "confidence": confidence,
            "breakdown": self.policy.get_breakdown(scores, context),
            "safety_result": safety_result,
            "action_result": action_result,
            "original_decision": original_decision,
            "processing_time_ms": processing_time_ms,
        }

        # Log via observability manager
        self.observability.log_reflex_decision(
            trace_id=trace_id,
            decision=decision,
            confidence=confidence,
            processing_time_ms=processing_time_ms,
            scores=scores,
            why_reflex=why_reflex,
            user_id=user_id,
            tenant_id=tenant_id,
            shadow_mode=True
        )

        # Log shadow evaluation (compare reflex vs reasoning decision)
        # In shadow mode, we assume reasoning would have made the same decision
        reasoning_decision = decision  # For now, assume reasoning agrees
        self.observability.log_shadow_evaluation(
            trace_id=trace_id,
            reflex_decision=original_decision,
            reasoning_decision=reasoning_decision,
            processing_time_ms=processing_time_ms,
            scores=scores
        )

        # Learn from this interaction (if habit store enabled and decision was good)
        if (self.habit_store.is_enabled() and
            original_decision == "allow_reflex" and
            safety_result.get("safe", False) and
            confidence > 0.7):
            self.habit_store.observe_cue(
                cue=text,
                action="reflex_response",
                confidence=confidence,
                user_id=user_id,
                tenant_id=tenant_id
            )

        return {
            "trace_id": trace_id,
            "decision": decision,
            "shadow": True,
            "why_reflex": why_reflex,
        }


