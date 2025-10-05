"""
StillMe Monitoring Module
========================

Advanced monitoring and analytics for AGI learning automation.
Includes resource monitoring, performance analysis, and real-time dashboard.

Components:
- ResourceMonitor: Real-time resource tracking
- PerformanceAnalyzer: AGI performance analysis
- MonitoringDashboard: Web-based monitoring interface

Author: StillMe AI Framework
Version: 2.0.0
Date: 2025-09-28
"""

__version__ = "2.0.0"
__author__ = "StillMe AI Framework"

# Import resource monitoring
# Import monitoring dashboard
from .dashboard import (
    MonitoringDashboard,
    get_monitoring_dashboard,
    start_monitoring_dashboard,
)

# Import performance analysis
from .performance_analyzer import (
    AGIRecommendation,
    BottleneckAnalysis,
    PerformanceAnalyzer,
    PerformanceMetrics,
    PerformancePattern,
    get_performance_analyzer,
    initialize_performance_analysis,
)
from .resource_monitor import (
    ResourceAlert,
    ResourceMetrics,
    ResourceMonitor,
    ResourceThresholds,
    TokenBudgetManager,
    get_resource_monitor,
    initialize_resource_monitoring,
)

__all__ = [
    # Resource Monitoring
    "ResourceMonitor",
    "ResourceThresholds",
    "ResourceMetrics",
    "ResourceAlert",
    "TokenBudgetManager",
    "get_resource_monitor",
    "initialize_resource_monitoring",
    # Performance Analysis
    "PerformanceAnalyzer",
    "PerformanceMetrics",
    "PerformancePattern",
    "BottleneckAnalysis",
    "AGIRecommendation",
    "get_performance_analyzer",
    "initialize_performance_analysis",
    # Monitoring Dashboard
    "MonitoringDashboard",
    "get_monitoring_dashboard",
    "start_monitoring_dashboard",
]
