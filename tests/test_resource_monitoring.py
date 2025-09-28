"""
Test suite for Resource Monitoring
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from stillme_core.monitoring.resource_monitor import (
    ResourceMonitor,
    ResourceThresholds,
    ResourceMetrics,
    ResourceAlert,
    TokenBudgetManager,
    get_resource_monitor
)
from stillme_core.monitoring.performance_analyzer import (
    PerformanceAnalyzer,
    PerformanceMetrics,
    PerformancePattern,
    BottleneckAnalysis,
    AGIRecommendation,
    get_performance_analyzer
)

class TestResourceThresholds:
    """Test ResourceThresholds"""
    
    def test_default_thresholds(self):
        """Test default threshold values"""
        thresholds = ResourceThresholds()
        
        assert thresholds.cpu_percent == 70.0
        assert thresholds.memory_percent == 80.0
        assert thresholds.memory_mb == 1024
        assert thresholds.disk_percent == 90.0
        assert thresholds.network_bandwidth_mbps == 100.0
        assert thresholds.token_budget_daily == 10000
        assert thresholds.token_budget_hourly == 1000
        assert thresholds.learning_session_duration_minutes == 30
        assert thresholds.max_concurrent_sessions == 1
    
    def test_custom_thresholds(self):
        """Test custom threshold values"""
        thresholds = ResourceThresholds(
            cpu_percent=80.0,
            memory_percent=85.0,
            memory_mb=2048,
            token_budget_daily=20000,
            token_budget_hourly=2000
        )
        
        assert thresholds.cpu_percent == 80.0
        assert thresholds.memory_percent == 85.0
        assert thresholds.memory_mb == 2048
        assert thresholds.token_budget_daily == 20000
        assert thresholds.token_budget_hourly == 2000

class TestTokenBudgetManager:
    """Test TokenBudgetManager"""
    
    def test_initialization(self):
        """Test token budget manager initialization"""
        manager = TokenBudgetManager(daily_budget=1000, hourly_budget=100)
        
        assert manager.daily_budget == 1000
        assert manager.hourly_budget == 100
        assert manager.daily_usage == 0
        assert manager.hourly_usage == 0
    
    def test_consume_tokens_success(self):
        """Test successful token consumption"""
        manager = TokenBudgetManager(daily_budget=1000, hourly_budget=100)
        
        result = manager.consume_tokens(50)
        
        assert result == True
        assert manager.daily_usage == 50
        assert manager.hourly_usage == 50
    
    def test_consume_tokens_exceed_daily(self):
        """Test token consumption exceeding daily budget"""
        manager = TokenBudgetManager(daily_budget=100, hourly_budget=1000)
        
        result = manager.consume_tokens(150)
        
        assert result == False
        assert manager.daily_usage == 0
        assert manager.hourly_usage == 0
    
    def test_consume_tokens_exceed_hourly(self):
        """Test token consumption exceeding hourly budget"""
        manager = TokenBudgetManager(daily_budget=1000, hourly_budget=100)
        
        result = manager.consume_tokens(150)
        
        assert result == False
        assert manager.daily_usage == 0
        assert manager.hourly_usage == 0
    
    def test_get_remaining_tokens(self):
        """Test getting remaining tokens"""
        manager = TokenBudgetManager(daily_budget=1000, hourly_budget=100)
        manager.consume_tokens(50)  # Within both budgets
        
        daily_remaining, hourly_remaining = manager.get_remaining_tokens()
        
        assert daily_remaining == 950
        assert hourly_remaining == 50
    
    def test_get_usage_stats(self):
        """Test getting usage statistics"""
        manager = TokenBudgetManager(daily_budget=1000, hourly_budget=100)
        manager.consume_tokens(50)  # Within both budgets
        
        stats = manager.get_usage_stats()
        
        assert stats['daily_budget'] == 1000
        assert stats['hourly_budget'] == 100
        assert stats['daily_usage'] == 50
        assert stats['hourly_usage'] == 50
        assert stats['daily_remaining'] == 950
        assert stats['hourly_remaining'] == 50
        assert stats['daily_usage_percent'] == 5.0
        assert stats['hourly_usage_percent'] == 50.0

class TestResourceMonitor:
    """Test ResourceMonitor"""
    
    @pytest.fixture
    def thresholds(self):
        """Test thresholds"""
        return ResourceThresholds(
            cpu_percent=70.0,
            memory_percent=80.0,
            memory_mb=1024,
            token_budget_daily=1000,
            token_budget_hourly=100
        )
    
    @pytest.fixture
    def monitor(self, thresholds):
        """Test resource monitor"""
        return ResourceMonitor(thresholds)
    
    @pytest.mark.asyncio
    async def test_start_monitoring(self, monitor):
        """Test starting resource monitoring"""
        result = await monitor.start_monitoring(interval=1)
        
        assert monitor.is_monitoring == True
        assert monitor.monitoring_task is not None
        
        # Stop monitoring
        await monitor.stop_monitoring()
        assert monitor.is_monitoring == False
    
    @pytest.mark.asyncio
    async def test_stop_monitoring(self, monitor):
        """Test stopping resource monitoring"""
        await monitor.start_monitoring(interval=1)
        result = await monitor.stop_monitoring()
        
        assert monitor.is_monitoring == False
        # Note: monitoring_task may still exist but be cancelled
    
    @pytest.mark.asyncio
    async def test_collect_metrics_with_psutil(self, monitor):
        """Test collecting metrics with psutil available"""
        with patch('stillme_core.monitoring.resource_monitor.PSUTIL_AVAILABLE', True), \
             patch('stillme_core.monitoring.resource_monitor.psutil') as mock_psutil:
            
            # Mock psutil responses
            mock_psutil.cpu_percent.return_value = 50.0
            mock_memory = Mock()
            mock_memory.percent = 60.0
            mock_memory.used = 512 * 1024 * 1024  # 512MB
            mock_memory.available = 1024 * 1024 * 1024  # 1GB
            mock_psutil.virtual_memory.return_value = mock_memory
            
            mock_disk = Mock()
            mock_disk.percent = 70.0
            mock_disk.free = 10 * 1024 * 1024 * 1024  # 10GB
            mock_psutil.disk_usage.return_value = mock_disk
            
            mock_network = Mock()
            mock_network.bytes_sent = 100 * 1024 * 1024  # 100MB
            mock_network.bytes_recv = 200 * 1024 * 1024  # 200MB
            mock_psutil.net_io_counters.return_value = mock_network
            
            mock_psutil.pids.return_value = [1, 2, 3, 4, 5]
            mock_psutil.getloadavg.return_value = (1.0, 2.0, 3.0)
            
            metrics = await monitor._collect_metrics()
            
            assert isinstance(metrics, ResourceMetrics)
            assert metrics.cpu_percent == 50.0
            assert metrics.memory_percent == 60.0
            assert metrics.memory_used_mb == 512.0
            assert metrics.memory_available_mb == 1024.0
            assert metrics.disk_percent == 70.0
            assert metrics.disk_free_gb == 10.0
            assert metrics.processes_count == 5
            assert metrics.load_average == (1.0, 2.0, 3.0)
    
    @pytest.mark.asyncio
    async def test_collect_metrics_without_psutil(self, monitor):
        """Test collecting metrics without psutil"""
        with patch('stillme_core.monitoring.resource_monitor.PSUTIL_AVAILABLE', False):
            metrics = await monitor._collect_metrics()
            
            assert isinstance(metrics, ResourceMetrics)
            assert metrics.cpu_percent == 0.0
            assert metrics.memory_percent == 0.0
            assert metrics.processes_count == 0
    
    @pytest.mark.asyncio
    async def test_check_thresholds_cpu_high(self, monitor):
        """Test threshold checking with high CPU"""
        # Create metrics with high CPU
        metrics = ResourceMetrics(
            timestamp=datetime.now(),
            cpu_percent=80.0,  # Above threshold of 70.0
            memory_percent=50.0,
            memory_used_mb=512.0,
            memory_available_mb=1024.0,
            disk_percent=60.0,
            disk_free_gb=20.0,
            network_sent_mb=100.0,
            network_recv_mb=200.0,
            network_speed_mbps=10.0,
            processes_count=10,
            load_average=(1.0, 2.0, 3.0),
            token_usage_daily=100,
            token_usage_hourly=10,
            token_remaining_daily=900,
            token_remaining_hourly=90,
            learning_sessions_active=0,
            learning_sessions_total=0
        )
        
        await monitor._check_thresholds(metrics)
        
        # Check that alert was generated
        assert len(monitor.alerts) > 0
        cpu_alert = monitor.alerts[-1]
        assert cpu_alert.alert_type == "cpu_high"
        assert cpu_alert.severity == "medium"  # 80% is medium severity, not high
        assert cpu_alert.current_value == 80.0
        assert cpu_alert.threshold_value == 70.0
    
    @pytest.mark.asyncio
    async def test_check_thresholds_memory_high(self, monitor):
        """Test threshold checking with high memory"""
        # Create metrics with high memory
        metrics = ResourceMetrics(
            timestamp=datetime.now(),
            cpu_percent=50.0,
            memory_percent=85.0,  # Above threshold of 80.0
            memory_used_mb=1024.0,
            memory_available_mb=256.0,
            disk_percent=60.0,
            disk_free_gb=20.0,
            network_sent_mb=100.0,
            network_recv_mb=200.0,
            network_speed_mbps=10.0,
            processes_count=10,
            load_average=(1.0, 2.0, 3.0),
            token_usage_daily=100,
            token_usage_hourly=10,
            token_remaining_daily=900,
            token_remaining_hourly=90,
            learning_sessions_active=0,
            learning_sessions_total=0
        )
        
        await monitor._check_thresholds(metrics)
        
        # Check that alert was generated
        assert len(monitor.alerts) > 0
        memory_alert = monitor.alerts[-1]
        assert memory_alert.alert_type == "memory_high"
        assert memory_alert.severity == "high"
        assert memory_alert.current_value == 85.0
        assert memory_alert.threshold_value == 80.0
    
    def test_can_start_learning_session_success(self, monitor):
        """Test successful learning session start check"""
        # Add some metrics to history
        metrics = ResourceMetrics(
            timestamp=datetime.now(),
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_used_mb=512.0,
            memory_available_mb=1024.0,
            disk_percent=60.0,
            disk_free_gb=20.0,
            network_sent_mb=100.0,
            network_recv_mb=200.0,
            network_speed_mbps=10.0,
            processes_count=10,
            load_average=(1.0, 2.0, 3.0),
            token_usage_daily=100,
            token_usage_hourly=10,
            token_remaining_daily=900,
            token_remaining_hourly=90,
            learning_sessions_active=0,
            learning_sessions_total=0
        )
        monitor.metrics_history.append(metrics)
        
        can_start, reason = monitor.can_start_learning_session()
        
        assert can_start == True
        assert reason == "All checks passed"
    
    def test_can_start_learning_session_high_cpu(self, monitor):
        """Test learning session start check with high CPU"""
        # Add metrics with high CPU
        metrics = ResourceMetrics(
            timestamp=datetime.now(),
            cpu_percent=80.0,  # Above threshold
            memory_percent=60.0,
            memory_used_mb=512.0,
            memory_available_mb=1024.0,
            disk_percent=60.0,
            disk_free_gb=20.0,
            network_sent_mb=100.0,
            network_recv_mb=200.0,
            network_speed_mbps=10.0,
            processes_count=10,
            load_average=(1.0, 2.0, 3.0),
            token_usage_daily=100,
            token_usage_hourly=10,
            token_remaining_daily=900,
            token_remaining_hourly=90,
            learning_sessions_active=0,
            learning_sessions_total=0
        )
        monitor.metrics_history.append(metrics)
        
        can_start, reason = monitor.can_start_learning_session()
        
        assert can_start == False
        assert "CPU usage too high" in reason
    
    def test_start_learning_session(self, monitor):
        """Test starting learning session tracking"""
        session_id = "test_session_123"
        
        result = monitor.start_learning_session(session_id)
        
        assert result == True
        assert session_id in monitor.learning_processes
        assert session_id in monitor.process_start_times
    
    def test_end_learning_session(self, monitor):
        """Test ending learning session tracking"""
        session_id = "test_session_123"
        monitor.start_learning_session(session_id)
        
        result = monitor.end_learning_session(session_id)
        
        assert result == True
        assert session_id not in monitor.learning_processes
        assert session_id not in monitor.process_start_times
    
    def test_get_metrics_summary(self, monitor):
        """Test getting metrics summary"""
        # Add some metrics
        metrics = ResourceMetrics(
            timestamp=datetime.now(),
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_used_mb=512.0,
            memory_available_mb=1024.0,
            disk_percent=60.0,
            disk_free_gb=20.0,
            network_sent_mb=100.0,
            network_recv_mb=200.0,
            network_speed_mbps=10.0,
            processes_count=10,
            load_average=(1.0, 2.0, 3.0),
            token_usage_daily=100,
            token_usage_hourly=10,
            token_remaining_daily=900,
            token_remaining_hourly=90,
            learning_sessions_active=0,
            learning_sessions_total=0
        )
        monitor.metrics_history.append(metrics)
        
        summary = monitor.get_metrics_summary()
        
        assert 'current' in summary
        assert 'averages' in summary
        assert 'token_budget' in summary
        assert 'alerts_count' in summary
        assert 'learning_sessions' in summary
        assert 'monitoring_status' in summary

class TestPerformanceAnalyzer:
    """Test PerformanceAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Test performance analyzer"""
        return PerformanceAnalyzer(analysis_window_hours=1)
    
    @pytest.mark.asyncio
    async def test_start_analysis(self, analyzer):
        """Test starting performance analysis"""
        result = await analyzer.start_analysis(interval=1)
        
        assert analyzer.is_analyzing == True
        assert analyzer.analysis_task is not None
        
        # Stop analysis
        await analyzer.stop_analysis()
        assert analyzer.is_analyzing == False
    
    @pytest.mark.asyncio
    async def test_stop_analysis(self, analyzer):
        """Test stopping performance analysis"""
        await analyzer.start_analysis(interval=1)
        result = await analyzer.stop_analysis()
        
        assert analyzer.is_analyzing == False
        # Note: analysis_task may still exist but be cancelled
    
    def test_add_performance_metrics(self, analyzer):
        """Test adding performance metrics"""
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            session_id="test_session",
            learning_stage="infant",
            response_time_ms=1000.0,
            memory_usage_mb=512.0,
            cpu_usage_percent=50.0,
            tokens_consumed=100,
            accuracy_score=0.8,
            learning_rate=0.1,
            convergence_rate=0.5,
            error_rate=0.1,
            throughput_items_per_second=1.0,
            efficiency_score=0.7
        )
        
        analyzer.add_performance_metrics(metrics)
        
        assert len(analyzer.performance_history) == 1
        assert analyzer.performance_history[0] == metrics
        assert "infant" in analyzer.learning_curves
        assert len(analyzer.learning_curves["infant"]) == 1
    
    def test_detect_trend_improvement(self, analyzer):
        """Test trend detection for improvement"""
        values = [0.5, 0.6, 0.7, 0.8, 0.9]  # Improving trend
        
        pattern = analyzer._detect_trend(values, "accuracy")
        
        assert pattern is not None
        assert pattern.pattern_type == "improvement"
        assert pattern.trend == "increasing"
        assert "improvement" in pattern.description.lower()
    
    def test_detect_trend_degradation(self, analyzer):
        """Test trend detection for degradation"""
        values = [0.9, 0.8, 0.7, 0.6, 0.5]  # Degrading trend
        
        pattern = analyzer._detect_trend(values, "accuracy")
        
        assert pattern is not None
        assert pattern.pattern_type == "degradation"
        assert pattern.trend == "decreasing"
        assert "degradation" in pattern.description.lower()
    
    def test_detect_trend_stable(self, analyzer):
        """Test trend detection for stable performance"""
        values = [0.8, 0.81, 0.79, 0.8, 0.82]  # Stable trend
        
        pattern = analyzer._detect_trend(values, "accuracy")
        
        assert pattern is not None
        assert pattern.pattern_type == "stable"
        assert pattern.trend == "stable"
        assert "stable" in pattern.description.lower()
    
    def test_get_analysis_report(self, analyzer):
        """Test getting analysis report"""
        # Add some metrics
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            session_id="test_session",
            learning_stage="infant",
            response_time_ms=1000.0,
            memory_usage_mb=512.0,
            cpu_usage_percent=50.0,
            tokens_consumed=100,
            accuracy_score=0.8,
            learning_rate=0.1,
            convergence_rate=0.5,
            error_rate=0.1,
            throughput_items_per_second=1.0,
            efficiency_score=0.7
        )
        analyzer.add_performance_metrics(metrics)
        
        report = analyzer.get_analysis_report()
        
        assert 'analysis_timestamp' in report
        assert 'analysis_window_hours' in report
        assert 'performance_summary' in report
        assert 'patterns' in report
        assert 'bottlenecks' in report
        assert 'agi_recommendations' in report
        assert 'evolution_milestones' in report
        assert 'learning_curves' in report
        assert 'baselines' in report
        assert 'thresholds' in report

class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_resource_monitor_with_performance_analyzer(self):
        """Test integration between resource monitor and performance analyzer"""
        # Create instances
        monitor = ResourceMonitor()
        analyzer = PerformanceAnalyzer()
        
        # Start monitoring
        await monitor.start_monitoring(interval=1)
        await analyzer.start_analysis(interval=1)
        
        # Add performance metrics
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            session_id="integration_test",
            learning_stage="infant",
            response_time_ms=1000.0,
            memory_usage_mb=512.0,
            cpu_usage_percent=50.0,
            tokens_consumed=100,
            accuracy_score=0.8,
            learning_rate=0.1,
            convergence_rate=0.5,
            error_rate=0.1,
            throughput_items_per_second=1.0,
            efficiency_score=0.7
        )
        analyzer.add_performance_metrics(metrics)
        
        # Check that both are working
        assert monitor.is_monitoring == True
        assert analyzer.is_analyzing == True
        
        # Stop both
        await monitor.stop_monitoring()
        await analyzer.stop_analysis()
        
        assert monitor.is_monitoring == False
        assert analyzer.is_analyzing == False
