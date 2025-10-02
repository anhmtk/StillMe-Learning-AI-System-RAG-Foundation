"""
📊 StillMe Metrics Registry
==========================

Registry quản lý định nghĩa metrics, validation, và metadata.
Đảm bảo consistency và type safety cho metrics system.

Tính năng:
- Metric definitions và validation
- Unit standardization
- Tag management
- Metadata schemas
- Performance optimization

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-28
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"          # Monotonically increasing
    GAUGE = "gauge"             # Can go up or down
    HISTOGRAM = "histogram"     # Distribution of values
    SUMMARY = "summary"         # Quantiles over time

class MetricUnit(Enum):
    """Standard metric units"""
    # Time
    SECONDS = "s"
    MILLISECONDS = "ms"
    MICROSECONDS = "us"
    NANOSECONDS = "ns"

    # Memory
    BYTES = "bytes"
    KILOBYTES = "KB"
    MEGABYTES = "MB"
    GIGABYTES = "GB"

    # Count
    COUNT = "count"
    PERCENT = "%"
    RATIO = "ratio"

    # Tokens
    TOKENS = "tokens"
    TOKENS_PER_SECOND = "tokens/s"

    # Custom
    CUSTOM = "custom"

@dataclass
class MetricDefinition:
    """Definition of a metric"""
    name: str
    description: str
    metric_type: MetricType
    unit: MetricUnit
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default_value: Optional[float] = None

class MetricsRegistry:
    """
    Registry quản lý định nghĩa metrics
    
    Đảm bảo consistency, validation, và type safety
    cho toàn bộ metrics system.
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/metrics_registry.yaml"
        self.definitions: Dict[str, MetricDefinition] = {}
        self._load_default_definitions()

        # Load from config if exists
        if Path(self.config_path).exists():
            self._load_from_config()

        logger.info(f"MetricsRegistry initialized with {len(self.definitions)} definitions")

    def _load_default_definitions(self):
        """Load default metric definitions"""
        default_metrics = [
            # Learning metrics
            MetricDefinition(
                name="learning_pass_rate",
                description="Learning test pass rate",
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.RATIO,
                tags=["stage", "component"],
                min_value=0.0,
                max_value=1.0
            ),
            MetricDefinition(
                name="learning_accuracy",
                description="Learning accuracy score",
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.RATIO,
                tags=["stage", "component"],
                min_value=0.0,
                max_value=1.0
            ),
            MetricDefinition(
                name="ingested_items",
                description="Number of items ingested",
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                tags=["source", "type"]
            ),
            MetricDefinition(
                name="latency_ms",
                description="Operation latency in milliseconds",
                metric_type=MetricType.HISTOGRAM,
                unit=MetricUnit.MILLISECONDS,
                tags=["operation", "component"],
                min_value=0.0
            ),
            MetricDefinition(
                name="tokens_used",
                description="Number of tokens consumed",
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.TOKENS,
                tags=["model", "operation"]
            ),
            MetricDefinition(
                name="memory_usage_mb",
                description="Memory usage in megabytes",
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.MEGABYTES,
                tags=["component"],
                min_value=0.0
            ),
            MetricDefinition(
                name="cpu_usage_percent",
                description="CPU usage percentage",
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.PERCENT,
                tags=["component"],
                min_value=0.0,
                max_value=100.0
            ),
            MetricDefinition(
                name="errors_count",
                description="Number of errors",
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                tags=["type", "component"]
            ),
            MetricDefinition(
                name="rollback_count",
                description="Number of rollbacks",
                metric_type=MetricType.COUNTER,
                unit=MetricUnit.COUNT,
                tags=["reason", "component"]
            ),
            MetricDefinition(
                name="self_assessment_score",
                description="Self-assessment score",
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.RATIO,
                tags=["category", "stage"],
                min_value=0.0,
                max_value=1.0
            ),
            MetricDefinition(
                name="evolution_stage",
                description="Current evolution stage",
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.COUNT,
                tags=["stage"],
                min_value=0.0,
                max_value=4.0
            ),
            MetricDefinition(
                name="approval_rate",
                description="Content approval rate",
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.RATIO,
                tags=["content_type", "source"],
                min_value=0.0,
                max_value=1.0
            ),
            MetricDefinition(
                name="quality_score",
                description="Content quality score",
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.RATIO,
                tags=["content_type", "source"],
                min_value=0.0,
                max_value=1.0
            ),
            MetricDefinition(
                name="risk_score",
                description="Content risk score",
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.RATIO,
                tags=["content_type", "source"],
                min_value=0.0,
                max_value=1.0
            ),
            MetricDefinition(
                name="throughput_items_per_second",
                description="Processing throughput",
                metric_type=MetricType.GAUGE,
                unit=MetricUnit.COUNT,
                tags=["operation", "component"],
                min_value=0.0
            )
        ]

        for metric in default_metrics:
            self.definitions[metric.name] = metric

    def _load_from_config(self):
        """Load metric definitions from config file"""
        try:
            import yaml
            with open(self.config_path, encoding='utf-8') as f:
                config = yaml.safe_load(f)

            for metric_config in config.get('metrics', []):
                metric = MetricDefinition(
                    name=metric_config['name'],
                    description=metric_config['description'],
                    metric_type=MetricType(metric_config['type']),
                    unit=MetricUnit(metric_config['unit']),
                    tags=metric_config.get('tags', []),
                    metadata=metric_config.get('metadata', {}),
                    min_value=metric_config.get('min_value'),
                    max_value=metric_config.get('max_value'),
                    default_value=metric_config.get('default_value')
                )
                self.definitions[metric.name] = metric

            logger.info(f"Loaded {len(config.get('metrics', []))} metrics from config")
        except Exception as e:
            logger.warning(f"Failed to load metrics config: {e}")

    def register_metric(self, definition: MetricDefinition):
        """Register a new metric definition"""
        self.definitions[definition.name] = definition
        logger.info(f"Registered metric: {definition.name}")

    def get_definition(self, name: str) -> Optional[MetricDefinition]:
        """Get metric definition by name"""
        return self.definitions.get(name)

    def validate_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> bool:
        """Validate metric value and tags"""
        definition = self.get_definition(name)
        if not definition:
            logger.warning(f"Unknown metric: {name}")
            return False

        # Validate value range
        if definition.min_value is not None and value < definition.min_value:
            logger.warning(f"Metric {name} value {value} below minimum {definition.min_value}")
            return False

        if definition.max_value is not None and value > definition.max_value:
            logger.warning(f"Metric {name} value {value} above maximum {definition.max_value}")
            return False

        # Validate tags
        if tags:
            required_tags = set(definition.tags)
            provided_tags = set(tags.keys())
            missing_tags = required_tags - provided_tags
            if missing_tags:
                logger.warning(f"Metric {name} missing required tags: {missing_tags}")
                return False

        return True

    def get_all_metrics(self) -> List[MetricDefinition]:
        """Get all registered metric definitions"""
        return list(self.definitions.values())

    def get_metrics_by_type(self, metric_type: MetricType) -> List[MetricDefinition]:
        """Get metrics by type"""
        return [m for m in self.definitions.values() if m.metric_type == metric_type]

    def get_metrics_by_tag(self, tag: str) -> List[MetricDefinition]:
        """Get metrics that use a specific tag"""
        return [m for m in self.definitions.values() if tag in m.tags]

    def export_definitions(self, output_path: str):
        """Export metric definitions to file"""
        export_data = {
            'metrics': [
                {
                    'name': m.name,
                    'description': m.description,
                    'type': m.metric_type.value,
                    'unit': m.unit.value,
                    'tags': m.tags,
                    'metadata': m.metadata,
                    'min_value': m.min_value,
                    'max_value': m.max_value,
                    'default_value': m.default_value
                }
                for m in self.definitions.values()
            ]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(self.definitions)} metric definitions to {output_path}")

    def get_metric_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        summary = {
            'total_metrics': len(self.definitions),
            'by_type': {},
            'by_unit': {},
            'by_tag': {}
        }

        # Count by type
        for metric in self.definitions.values():
            metric_type = metric.metric_type.value
            summary['by_type'][metric_type] = summary['by_type'].get(metric_type, 0) + 1

        # Count by unit
        for metric in self.definitions.values():
            unit = metric.unit.value
            summary['by_unit'][unit] = summary['by_unit'].get(unit, 0) + 1

        # Count by tag
        for metric in self.definitions.values():
            for tag in metric.tags:
                summary['by_tag'][tag] = summary['by_tag'].get(tag, 0) + 1

        return summary

# Global instance
_metrics_registry_instance: Optional[MetricsRegistry] = None

def get_metrics_registry() -> MetricsRegistry:
    """Get global metrics registry instance"""
    global _metrics_registry_instance
    if _metrics_registry_instance is None:
        _metrics_registry_instance = MetricsRegistry()
    return _metrics_registry_instance

def initialize_metrics_registry(config_path: Optional[str] = None) -> MetricsRegistry:
    """Initialize global metrics registry with config"""
    global _metrics_registry_instance
    _metrics_registry_instance = MetricsRegistry(config_path)
    return _metrics_registry_instance
