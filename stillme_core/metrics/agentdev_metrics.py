"""AgentDev Metrics for StillMe Framework"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class MetricType(Enum):
    PERFORMANCE = "performance"
    QUALITY = "quality"
    SECURITY = "security"
    ETHICS = "ethics"
    LEARNING = "learning"

@dataclass
class MetricRecord:
    """Metric record"""
    name: str
    value: float
    unit: str
    metric_type: MetricType
    timestamp: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class AgentDevMetrics:
    """AgentDev metrics collector"""

    def __init__(self):
        self.logger = logger
        self.metrics: List[MetricRecord] = []
        self.sessions: List[Dict[str, Any]] = []
        self.logger.info("✅ AgentDevMetrics initialized")

    def record_metric(self,
                     name: str,
                     value: float,
                     unit: str,
                     metric_type: MetricType,
                     metadata: Dict[str, Any] = None) -> MetricRecord:
        """Record a metric"""
        try:
            metric = MetricRecord(
                name=name,
                value=value,
                unit=unit,
                metric_type=metric_type,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )

            self.metrics.append(metric)
            self.logger.info(f"📊 Metric recorded: {name} = {value} {unit}")
            return metric

        except Exception as e:
            self.logger.error(f"❌ Failed to record metric: {e}")
            raise

    def record_session(self, session_data: Dict[str, Any]) -> str:
        """Record a session"""
        try:
            session_id = f"session_{len(self.sessions) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            session_data['session_id'] = session_id
            session_data['timestamp'] = datetime.now().isoformat()

            self.sessions.append(session_data)
            self.logger.info(f"📝 Session recorded: {session_id}")
            return session_id

        except Exception as e:
            self.logger.error(f"❌ Failed to record session: {e}")
            raise

    def get_metrics_by_type(self, metric_type: MetricType) -> List[MetricRecord]:
        """Get metrics by type"""
        return [m for m in self.metrics if m.metric_type == metric_type]

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        try:
            total_metrics = len(self.metrics)
            total_sessions = len(self.sessions)

            metrics_by_type = {}
            for metric in self.metrics:
                type_key = metric.metric_type.value
                metrics_by_type[type_key] = metrics_by_type.get(type_key, 0) + 1

            return {
                "total_metrics": total_metrics,
                "total_sessions": total_sessions,
                "metrics_by_type": metrics_by_type,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get metrics summary: {e}")
            return {"error": str(e)}

    def clear_metrics(self):
        """Clear all metrics"""
        self.metrics.clear()
        self.sessions.clear()
        self.logger.info("🧹 All metrics cleared")

# Global metrics instance
_metrics_instance = None

def get_metrics() -> AgentDevMetrics:
    """Get global metrics instance"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = AgentDevMetrics()
    return _metrics_instance

def get_summary() -> Dict[str, Any]:
    """Get metrics summary (convenience function)"""
    return get_metrics().get_summary()

def record_session(session_data: Dict[str, Any]) -> str:
    """Record a session (convenience function)"""
    return get_metrics().record_session(session_data)