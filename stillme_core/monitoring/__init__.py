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
from .resource_monitor import (
    ResourceMonitor,
    ResourceThresholds,
    ResourceMetrics,
    ResourceAlert,
    TokenBudgetManager,
    get_resource_monitor,
    initialize_resource_monitoring
)

# Import performance analysis
from .performance_analyzer import (
    PerformanceAnalyzer,
    PerformanceMetrics,
    PerformancePattern,
    BottleneckAnalysis,
    AGIRecommendation,
    get_performance_analyzer,
    initialize_performance_analysis
)

# Import monitoring dashboard
from .dashboard import (
    MonitoringDashboard,
    get_monitoring_dashboard,
    start_monitoring_dashboard
)

__all__ = [
    # Resource Monitoring
    'ResourceMonitor',
    'ResourceThresholds',
    'ResourceMetrics',
    'ResourceAlert',
    'TokenBudgetManager',
    'get_resource_monitor',
    'initialize_resource_monitoring',
    
    # Performance Analysis
    'PerformanceAnalyzer',
    'PerformanceMetrics',
    'PerformancePattern',
    'BottleneckAnalysis',
    'AGIRecommendation',
    'get_performance_analyzer',
    'initialize_performance_analysis',
    
    # Monitoring Dashboard
    'MonitoringDashboard',
    'get_monitoring_dashboard',
    'start_monitoring_dashboard'
]
