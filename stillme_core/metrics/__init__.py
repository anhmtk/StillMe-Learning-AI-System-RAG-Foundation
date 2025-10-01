"""
📊 StillMe Metrics System
========================

Hệ thống thu thập và phân tích metrics cho learning dashboard.
Cung cấp real-time tracking, historical analysis, và community engagement.

Tính năng:
- Real-time metrics collection
- Historical data analysis
- Learning curve visualization
- Performance tracking
- Cost analysis
- Community engagement metrics

Author: StillMe AI Framework
Version: 1.0.0
Date: 2025-09-28
"""

__version__ = "1.0.0"
__author__ = "StillMe AI Framework"

# Import core metrics components
from .emitter import Metric, MetricsEmitter, get_metrics_emitter
from .privacy import PIIRedactor, PrivacyManager, get_privacy_manager
from .queries import MetricsQueries, get_metrics_queries
from .registry import MetricDefinition, MetricsRegistry, get_metrics_registry

__all__ = [
    # Core components
    'MetricsEmitter',
    'Metric',
    'get_metrics_emitter',

    # Registry
    'MetricsRegistry',
    'MetricDefinition',
    'get_metrics_registry',

    # Privacy
    'PrivacyManager',
    'PIIRedactor',
    'get_privacy_manager',

    # Queries
    'MetricsQueries',
    'get_metrics_queries',
]