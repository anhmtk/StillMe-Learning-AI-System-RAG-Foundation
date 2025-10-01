#!/usr/bin/env python3
"""
StillMe Performance Tracker
Tracks model performance metrics including tokens, latency, and model info
"""
import time
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

class PerformanceMetrics:
    """Container for performance metrics"""

    def __init__(self,
                 model: str,
                 engine: str,
                 tokens_in: int = 0,
                 tokens_out: int = 0,
                 latency_ms: float = 0.0,
                 timestamp: Optional[datetime] = None):
        self.model = model
        self.engine = engine
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.latency_ms = latency_ms
        self.timestamp = timestamp or datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "model": self.model,
            "engine": self.engine,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "latency_ms": self.latency_ms,
            "timestamp": self.timestamp.isoformat()
        }

    def get_display_text(self) -> str:
        """Get formatted display text for UI"""
        return f"Model: {self.model} | In: {self.tokens_in} | Out: {self.tokens_out} | Latency: {self.latency_ms:.1f}s"

    def get_detailed_log(self) -> str:
        """Get detailed log information"""
        return f"""Performance Details:
- Model: {self.model}
- Engine: {self.engine}
- Input Tokens: {self.tokens_in}
- Output Tokens: {self.tokens_out}
- Total Tokens: {self.tokens_in + self.tokens_out}
- Latency: {self.latency_ms:.1f}ms
- Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"""

class PerformanceTracker:
    """Tracks and manages performance metrics"""

    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.session_metrics: Dict[str, List[PerformanceMetrics]] = {}

    def start_timing(self) -> float:
        """Start timing a request"""
        return time.perf_counter()

    def end_timing(self, start_time: float) -> float:
        """End timing and return latency in milliseconds"""
        return (time.perf_counter() - start_time) * 1000

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        if not text:
            return 0
        # Rough estimation: 1 token ≈ 4 characters for English, 2-3 for other languages
        return max(1, len(text) // 3)

    def create_metrics(self,
                      model: str,
                      engine: str,
                      input_text: str,
                      output_text: str,
                      latency_ms: float,
                      session_id: str = "default") -> PerformanceMetrics:
        """Create performance metrics from request data"""

        tokens_in = self.estimate_tokens(input_text)
        tokens_out = self.estimate_tokens(output_text)

        metrics = PerformanceMetrics(
            model=model,
            engine=engine,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms
        )

        # Store in history
        self.metrics_history.append(metrics)

        # Store in session
        if session_id not in self.session_metrics:
            self.session_metrics[session_id] = []
        self.session_metrics[session_id].append(metrics)

        return metrics

    def get_session_summary(self, session_id: str = "default") -> Dict[str, Any]:
        """Get performance summary for a session"""
        if session_id not in self.session_metrics:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_latency": 0.0,
                "average_latency": 0.0,
                "models_used": []
            }

        metrics = self.session_metrics[session_id]
        total_requests = len(metrics)
        total_tokens = sum(m.tokens_in + m.tokens_out for m in metrics)
        total_latency = sum(m.latency_ms for m in metrics)
        average_latency = total_latency / total_requests if total_requests > 0 else 0
        models_used = list(set(m.model for m in metrics))

        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "total_latency": total_latency,
            "average_latency": average_latency,
            "models_used": models_used
        }

    def get_recent_metrics(self, count: int = 10) -> List[PerformanceMetrics]:
        """Get recent performance metrics"""
        return self.metrics_history[-count:] if self.metrics_history else []

# Global instance
performance_tracker = PerformanceTracker()
