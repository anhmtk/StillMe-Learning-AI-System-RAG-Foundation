"""Quality Metrics for StillMe Framework"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MetricType(Enum):
    COVERAGE = "coverage"
    COMPLEXITY = "complexity"
    DUPLICATION = "duplication"
    MAINTAINABILITY = "maintainability"
    RELIABILITY = "reliability"
    SECURITY = "security"


@dataclass
class QualityMetric:
    """Quality metric record"""

    metric_id: str
    metric_type: MetricType
    value: float
    unit: str
    threshold: float
    status: str
    timestamp: datetime
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class QualityMetrics:
    """Quality metrics collector for StillMe Framework"""

    def __init__(self):
        self.logger = logger
        self.metrics: list[QualityMetric] = []
        self.thresholds = self._initialize_thresholds()
        self.logger.info("✅ QualityMetrics initialized")

    def _initialize_thresholds(self) -> dict[MetricType, float]:
        """Initialize quality thresholds"""
        return {
            MetricType.COVERAGE: 80.0,  # 80% coverage
            MetricType.COMPLEXITY: 10.0,  # Max cyclomatic complexity
            MetricType.DUPLICATION: 3.0,  # Max 3% duplication
            MetricType.MAINTAINABILITY: 7.0,  # Maintainability index (1-10)
            MetricType.RELIABILITY: 8.0,  # Reliability rating (1-10)
            MetricType.SECURITY: 9.0,  # Security rating (1-10)
        }

    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        unit: str = "percentage",
        metadata: dict[str, Any] = None,
    ) -> QualityMetric:
        """Record a quality metric"""
        try:
            metric_id = f"metric_{len(self.metrics) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            threshold = self.thresholds.get(metric_type, 0.0)

            # Determine status based on threshold
            if value >= threshold:
                status = "PASS"
            elif value >= threshold * 0.8:  # 80% of threshold
                status = "WARNING"
            else:
                status = "FAIL"

            metric = QualityMetric(
                metric_id=metric_id,
                metric_type=metric_type,
                value=value,
                unit=unit,
                threshold=threshold,
                status=status,
                timestamp=datetime.now(),
                metadata=metadata or {},
            )

            self.metrics.append(metric)
            self.logger.info(
                f"📊 Quality metric recorded: {metric_type.value} = {value} {unit} ({status})"
            )
            return metric

        except Exception as e:
            self.logger.error(f"❌ Failed to record quality metric: {e}")
            raise

    def get_metrics_by_type(self, metric_type: MetricType) -> list[QualityMetric]:
        """Get metrics by type"""
        return [m for m in self.metrics if m.metric_type == metric_type]

    def get_metrics_by_status(self, status: str) -> list[QualityMetric]:
        """Get metrics by status"""
        return [m for m in self.metrics if m.status == status]

    def get_latest_metric(self, metric_type: MetricType) -> Optional[QualityMetric]:
        """Get the latest metric of a specific type"""
        metrics = self.get_metrics_by_type(metric_type)
        if metrics:
            return max(metrics, key=lambda m: m.timestamp)
        return None

    def get_quality_summary(self) -> dict[str, Any]:
        """Get quality metrics summary"""
        try:
            total_metrics = len(self.metrics)

            metrics_by_type = {}
            metrics_by_status = {}
            latest_metrics = {}

            for metric in self.metrics:
                # By type
                type_key = metric.metric_type.value
                metrics_by_type[type_key] = metrics_by_type.get(type_key, 0) + 1

                # By status
                status_key = metric.status
                metrics_by_status[status_key] = metrics_by_status.get(status_key, 0) + 1

                # Latest metrics
                if (
                    type_key not in latest_metrics
                    or metric.timestamp > latest_metrics[type_key].timestamp
                ):
                    latest_metrics[type_key] = metric

            # Calculate overall quality score
            overall_score = self._calculate_overall_score(latest_metrics)

            return {
                "total_metrics": total_metrics,
                "metrics_by_type": metrics_by_type,
                "metrics_by_status": metrics_by_status,
                "latest_metrics": {
                    k: {
                        "value": v.value,
                        "unit": v.unit,
                        "status": v.status,
                        "timestamp": v.timestamp.isoformat(),
                    }
                    for k, v in latest_metrics.items()
                },
                "overall_quality_score": overall_score,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get quality summary: {e}")
            return {"error": str(e)}

    def _calculate_overall_score(
        self, latest_metrics: dict[str, QualityMetric]
    ) -> float:
        """Calculate overall quality score"""
        try:
            if not latest_metrics:
                return 0.0

            total_score = 0.0
            count = 0

            for metric in latest_metrics.values():
                # Convert status to score
                if metric.status == "PASS":
                    score = 100.0
                elif metric.status == "WARNING":
                    score = 70.0
                else:  # FAIL
                    score = 30.0

                total_score += score
                count += 1

            return total_score / count if count > 0 else 0.0

        except Exception as e:
            self.logger.error(f"❌ Failed to calculate overall score: {e}")
            return 0.0

    def update_threshold(self, metric_type: MetricType, threshold: float):
        """Update threshold for a metric type"""
        try:
            self.thresholds[metric_type] = threshold
            self.logger.info(f"📝 Threshold updated: {metric_type.value} = {threshold}")

        except Exception as e:
            self.logger.error(f"❌ Failed to update threshold: {e}")
            raise

    def clear_metrics(self):
        """Clear all metrics"""
        self.metrics.clear()
        self.logger.info("🧹 All quality metrics cleared")
