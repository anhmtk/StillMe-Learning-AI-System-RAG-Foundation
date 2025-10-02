"""
Transparency logging module for StillMe AI Framework.
Provides detailed logging of AI decision-making processes.
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class TransparencyLevel(Enum):
    """Levels of transparency logging."""
    NONE = "none"
    BASIC = "basic"
    DETAILED = "detailed"
    FULL = "full"


@dataclass
class TransparencyEvent:
    """Represents a transparency logging event."""
    event_id: str
    timestamp: datetime
    event_type: str
    module: str
    input_data: Any
    output_data: Any
    decision_factors: list[dict[str, Any]]
    confidence_scores: dict[str, float]
    reasoning: str
    metadata: dict[str, Any]
    trace_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class TransparencyLogger:
    """Logger for AI decision transparency."""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.level = TransparencyLevel(self.config.get("level", "basic"))
        self.log_rationale = self.config.get("log_rationale", False)
        self.trace_id_header = self.config.get("trace_id_header", "X-StillMe-Trace-ID")
        self._logger = logging.getLogger("stillme.transparency")

        # Configure transparency logger
        if self.enabled:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def log_decision(
        self,
        event_type: str,
        module: str,
        input_data: Any,
        output_data: Any,
        decision_factors: list[dict[str, Any]],
        confidence_scores: dict[str, float],
        reasoning: str,
        metadata: Optional[dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Log a decision event with full transparency."""
        if not self.enabled:
            return ""

        event_id = str(uuid.uuid4())
        event = TransparencyEvent(
            event_id=event_id,
            timestamp=datetime.now(),
            event_type=event_type,
            module=module,
            input_data=input_data,
            output_data=output_data,
            decision_factors=decision_factors,
            confidence_scores=confidence_scores,
            reasoning=reasoning,
            metadata=metadata or {},
            trace_id=trace_id,
            user_id=user_id,
            session_id=session_id
        )

        # Log based on transparency level
        if self.level == TransparencyLevel.BASIC:
            self._log_basic(event)
        elif self.level == TransparencyLevel.DETAILED:
            self._log_detailed(event)
        elif self.level == TransparencyLevel.FULL:
            self._log_full(event)

        return event_id

    def _log_basic(self, event: TransparencyEvent):
        """Log basic transparency information."""
        log_data = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "module": event.module,
            "confidence_scores": event.confidence_scores,
            "reasoning": event.reasoning
        }

        if event.trace_id:
            log_data["trace_id"] = event.trace_id

        self._logger.info(f"TRANSPARENCY: {json.dumps(log_data)}")

    def _log_detailed(self, event: TransparencyEvent):
        """Log detailed transparency information."""
        log_data = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "module": event.module,
            "input_data": self._sanitize_data(event.input_data),
            "output_data": self._sanitize_data(event.output_data),
            "decision_factors": event.decision_factors,
            "confidence_scores": event.confidence_scores,
            "reasoning": event.reasoning,
            "metadata": event.metadata
        }

        if event.trace_id:
            log_data["trace_id"] = event.trace_id
        if event.user_id:
            log_data["user_id"] = event.user_id
        if event.session_id:
            log_data["session_id"] = event.session_id

        self._logger.info(f"TRANSPARENCY: {json.dumps(log_data)}")

    def _log_full(self, event: TransparencyEvent):
        """Log full transparency information."""
        log_data = asdict(event)
        log_data["timestamp"] = event.timestamp.isoformat()

        # Sanitize sensitive data
        log_data["input_data"] = self._sanitize_data(event.input_data)
        log_data["output_data"] = self._sanitize_data(event.output_data)

        self._logger.info(f"TRANSPARENCY: {json.dumps(log_data)}")

    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize data for logging (remove sensitive information)."""
        if isinstance(data, str):
            # Remove potential API keys, tokens, etc.
            import re
            # Remove API keys (sk-*, pk-*, etc.)
            data = re.sub(r'sk-[a-zA-Z0-9]{20,}', '[REDACTED:API_KEY]', data)
            data = re.sub(r'pk-[a-zA-Z0-9]{20,}', '[REDACTED:API_KEY]', data)
            # Remove email addresses
            data = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[REDACTED:EMAIL]', data)
            # Remove phone numbers
            data = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[REDACTED:PHONE]', data)
            return data
        elif isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        else:
            return data

    def get_trace_id(self, headers: dict[str, str]) -> Optional[str]:
        """Extract trace ID from request headers."""
        return headers.get(self.trace_id_header)

    def create_trace_id(self) -> str:
        """Create a new trace ID."""
        return str(uuid.uuid4())

    def log_rationale(self, rationale: str, trace_id: Optional[str] = None):
        """Log AI decision rationale."""
        if not self.enabled or not self.log_rationale:
            return

        log_data = {
            "timestamp": datetime.now().isoformat(),
            "type": "rationale",
            "rationale": rationale
        }

        if trace_id:
            log_data["trace_id"] = trace_id

        self._logger.info(f"RATIONALE: {json.dumps(log_data)}")


# Global transparency logger instance
_transparency_logger: Optional[TransparencyLogger] = None


def get_transparency_logger() -> TransparencyLogger:
    """Get the global transparency logger instance."""
    global _transparency_logger

    if _transparency_logger is None:
        _transparency_logger = TransparencyLogger()

    return _transparency_logger


def set_transparency_logger(logger: TransparencyLogger):
    """Set the global transparency logger instance."""
    global _transparency_logger
    _transparency_logger = logger
