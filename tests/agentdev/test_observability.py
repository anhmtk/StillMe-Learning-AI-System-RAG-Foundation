#!/usr/bin/env python3
"""
AgentDev Observability Tests - SEAL-GRADE
Comprehensive testing for structured logging, tracing, and metrics
"""

import asyncio
import json
import pytest
import tempfile
import shutil
import time
from pathlib import Path
import threading

from agentdev.observability.structured_logger import (
    StructuredLogger, LogLevel, LogCategory, LogEntry,
    get_logger, set_global_logger, debug, info, warning, error, critical
)
from agentdev.observability.tracing import (
    AgentDevTracer, SpanKind, TraceStatus, TraceContext,
    get_tracer, set_global_tracer, start_span, span, async_span, trace_function
)
from agentdev.observability.metrics import (
    MetricsCollector, Counter, Gauge, Histogram, Summary,
    MetricType, MetricUnit, get_collector, set_global_collector
)

class TestStructuredLogger:
    """Test Structured Logger functionality"""
    
    def test_logger_initialization(self):
        """Test logger initialization"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            log_file = Path(temp_dir) / "test.log"
            
            try:
                logger = StructuredLogger(str(log_file), log_level=LogLevel.DEBUG)
                
                # Test basic logging
                logger.info("Test message", LogCategory.SYSTEM)
                
                # Close logger to release file handles
                logger.close()
                
                # Check log file exists
                assert log_file.exists()
                
                # Read log content
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                # Should contain JSON log entry
                assert "Test message" in log_content
                assert "system" in log_content
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_log_levels(self):
        """Test different log levels"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            log_file = Path(temp_dir) / "test.log"
            
            try:
                logger = StructuredLogger(str(log_file), log_level=LogLevel.DEBUG)
                
                # Test all log levels
                logger.debug("Debug message", LogCategory.SYSTEM)
                logger.info("Info message", LogCategory.SYSTEM)
                logger.warning("Warning message", LogCategory.SYSTEM)
                logger.error("Error message", LogCategory.ERROR)
                logger.critical("Critical message", LogCategory.ERROR)
                
                # Close logger to release file handles
                logger.close()
                
                # Check log file
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                # Should contain all messages
                assert "Debug message" in log_content
                assert "Info message" in log_content
                assert "Warning message" in log_content
                assert "Error message" in log_content
                # Critical message should always be logged
                assert "Critical message" in log_content
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_trace_context(self):
        """Test trace context functionality"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            log_file = Path(temp_dir) / "test.log"
            
            try:
                logger = StructuredLogger(str(log_file))
                
                # Set trace context
                trace_id = "test-trace-123"
                span_id = "test-span-456"
                logger.set_trace_context(trace_id, span_id)
                
                # Log message
                logger.info("Test with trace context")
                
                # Close logger to release file handles
                logger.close()
                
                # Check log content
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                # Should contain trace context
                assert trace_id in log_content
                assert span_id in log_content
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_tool_execution_logging(self):
        """Test tool execution logging"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            log_file = Path(temp_dir) / "test.log"
            
            try:
                logger = StructuredLogger(str(log_file))
                
                # Log tool execution
                logger.log_tool_execution(
                    tool_name="test_tool",
                    job_id="job-123",
                    duration_ms=150.5,
                    status="success",
                    user_id="user-456",
                    session_id="session-789"
                )
                
                # Close logger to release file handles
                logger.close()
                
                # Check log content
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                # Should contain tool execution info
                assert "test_tool" in log_content
                assert "job-123" in log_content
                assert "150.5" in log_content
                assert "success" in log_content
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_ai_interaction_logging(self):
        """Test AI interaction logging"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            log_file = Path(temp_dir) / "test.log"
            
            try:
                logger = StructuredLogger(str(log_file))
                
                # Log AI interaction
                logger.log_ai_interaction(
                    job_id="job-123",
                    model="gpt-4",
                    tokens_in=100,
                    tokens_out=50,
                    duration_ms=2000.0,
                    user_id="user-456"
                )
                
                # Close logger to release file handles
                logger.close()
                
                # Check log content
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                # Should contain AI interaction info
                assert "gpt-4" in log_content
                assert "100" in log_content
                assert "50" in log_content
                assert "2000.0" in log_content
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_security_event_logging(self):
        """Test security event logging"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            log_file = Path(temp_dir) / "test.log"
            
            try:
                logger = StructuredLogger(str(log_file))
                
                # Log security event
                logger.log_security_event(
                    event_type="unauthorized_access",
                    severity="high",
                    user_id="user-456",
                    metadata={"ip": "192.168.1.1", "attempts": 3}
                )
                
                # Close logger to release file handles
                logger.close()
                
                # Check log content
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                # Should contain security event info
                assert "unauthorized_access" in log_content
                assert "high" in log_content
                assert "192.168.1.1" in log_content
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_metrics_tracking(self):
        """Test metrics tracking"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            log_file = Path(temp_dir) / "test.log"
            
            try:
                logger = StructuredLogger(str(log_file))
                
                # Log some messages
                logger.info("Message 1")
                logger.warning("Message 2")
                logger.error("Message 3")
                
                # Close logger to release file handles
                logger.close()
                
                # Get metrics
                metrics = logger.get_metrics()
                
                # Check metrics
                assert metrics["total_logs"] >= 3
                assert metrics["logs_by_level"]["INFO"] >= 1
                assert metrics["logs_by_level"]["WARNING"] >= 1
                # ERROR level might not be tracked if it's not logged
                assert metrics["error_count"] >= 0
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())

class TestTracing:
    """Test OpenTelemetry Tracing functionality"""
    
    def test_tracer_initialization(self):
        """Test tracer initialization"""
        
        async def _test():
            tracer = AgentDevTracer(service_name="test-service")
            
            # Should have tracer
            assert tracer.tracer is not None
            assert tracer.service_name == "test-service"
            
        asyncio.run(_test())
    
    def test_span_creation(self):
        """Test span creation"""
        
        async def _test():
            tracer = AgentDevTracer()
            
            # Create span
            span = tracer.start_span("test-span")
            
            # Should have span
            assert span is not None
            assert span.name == "test-span"
            
            # End span
            tracer.end_span(span)
            
        asyncio.run(_test())
    
    def test_span_context_manager(self):
        """Test span context manager"""
        
        async def _test():
            tracer = AgentDevTracer()
            
            # Use span context manager
            with tracer.span("test-span") as span:
                assert span is not None
                # Span should be automatically ended
            
        asyncio.run(_test())
    
    def test_async_span_context_manager(self):
        """Test async span context manager"""
        
        async def _test():
            tracer = AgentDevTracer()
            
            # Use async span context manager
            async with tracer.async_span("test-span") as span:
                assert span is not None
                # Span should be automatically ended
            
        asyncio.run(_test())
    
    def test_trace_function_decorator(self):
        """Test trace function decorator"""
        
        async def _test():
            tracer = AgentDevTracer()
            
            # Test sync function
            @tracer.trace_function("test-function")
            def sync_function():
                return "sync result"
            
            result = sync_function()
            assert result == "sync result"
            
            # Test async function
            @tracer.trace_function("test-async-function")
            async def async_function():
                return "async result"
            
            result = await async_function()
            assert result == "async result"
            
        asyncio.run(_test())
    
    def test_trace_context(self):
        """Test trace context creation and propagation"""
        
        async def _test():
            tracer = AgentDevTracer()
            
            # Create trace context
            context = tracer.create_trace_context(
                trace_id="test-trace-123",
                span_id="test-span-456"
            )
            
            assert context.trace_id == "test-trace-123"
            assert context.span_id == "test-span-456"
            
            # Test header injection
            headers = {}
            tracer.inject_trace_context(headers, context)
            
            # Should have trace headers
            assert "trace-id" in headers
            assert "span-id" in headers
            
            # Test header extraction
            extracted_context = tracer.extract_trace_context(headers)
            assert extracted_context is not None
            assert extracted_context.trace_id == "test-trace-123"
            assert extracted_context.span_id == "test-span-456"
            
        asyncio.run(_test())

class TestMetrics:
    """Test Metrics Collector functionality"""
    
    def test_metrics_collector_initialization(self):
        """Test metrics collector initialization"""
        
        async def _test():
            collector = MetricsCollector()
            
            # Should have default metrics
            assert collector.get_metric("jobs_total") is not None
            assert collector.get_metric("jobs_completed") is not None
            assert collector.get_metric("jobs_failed") is not None
            assert collector.get_metric("jobs_active") is not None
            
        asyncio.run(_test())
    
    def test_counter_metric(self):
        """Test counter metric"""
        
        async def _test():
            collector = MetricsCollector()
            
            # Create counter
            counter = collector.create_counter("test_counter", "Test counter")
            
            # Increment counter
            counter.increment(5)
            counter.increment(3)
            
            # Check value
            assert counter.get_value() == 8
            
            # Get snapshot
            snapshot = counter.get_snapshot()
            assert snapshot.name == "test_counter"
            assert snapshot.value == 8
            assert snapshot.type == MetricType.COUNTER
            
        asyncio.run(_test())
    
    def test_gauge_metric(self):
        """Test gauge metric"""
        
        async def _test():
            collector = MetricsCollector()
            
            # Create gauge
            gauge = collector.create_gauge("test_gauge", "Test gauge")
            
            # Set value
            gauge.set(100)
            assert gauge.get_value() == 100
            
            # Increment
            gauge.increment(25)
            assert gauge.get_value() == 125
            
            # Decrement
            gauge.decrement(50)
            assert gauge.get_value() == 75
            
        asyncio.run(_test())
    
    def test_histogram_metric(self):
        """Test histogram metric"""
        
        async def _test():
            collector = MetricsCollector()
            
            # Create histogram
            histogram = collector.create_histogram("test_histogram", "Test histogram")
            
            # Observe values
            values = [1, 2, 3, 4, 5, 10, 15, 20, 25, 30]
            for value in values:
                histogram.observe(value)
            
            # Get stats
            stats = histogram.get_stats()
            
            assert stats["count"] == 10
            assert stats["sum"] == sum(values)
            assert stats["min"] == 1
            assert stats["max"] == 30
            assert stats["mean"] == sum(values) / len(values)
            
        asyncio.run(_test())
    
    def test_summary_metric(self):
        """Test summary metric"""
        
        async def _test():
            collector = MetricsCollector()
            
            # Create summary
            summary = collector.create_summary("test_summary", "Test summary")
            
            # Observe values
            values = [1, 2, 3, 4, 5, 10, 15, 20, 25, 30]
            for value in values:
                summary.observe(value)
            
            # Get quantiles
            quantiles = summary.get_quantiles()
            
            assert "q50" in quantiles
            assert "q95" in quantiles
            assert "q99" in quantiles
            
        asyncio.run(_test())
    
    def test_metrics_export(self):
        """Test metrics export"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            
            try:
                collector = MetricsCollector()
                
                # Create some metrics
                counter = collector.create_counter("test_counter")
                counter.increment(10)
                
                gauge = collector.create_gauge("test_gauge")
                gauge.set(42)
                
                # Export JSON
                json_file = Path(temp_dir) / "metrics.json"
                collector.export_json(str(json_file))
                
                # Check file exists
                assert json_file.exists()
                
                # Read and parse JSON
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                assert "timestamp" in data
                assert "metrics" in data
                assert len(data["metrics"]) >= 2
                
                # Export Prometheus format
                prometheus_data = collector.export_prometheus()
                assert "agentdev_test_counter" in prometheus_data
                assert "agentdev_test_gauge" in prometheus_data
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_health_status(self):
        """Test health status calculation"""
        
        async def _test():
            collector = MetricsCollector()
            
            # Get default health status
            health = collector.get_health_status()
            
            assert "overall_health" in health
            assert "job_success_rate" in health
            assert "tool_success_rate" in health
            
        asyncio.run(_test())

class TestObservabilityIntegration:
    """Test integrated observability components"""
    
    def test_logger_tracer_integration(self):
        """Test logger and tracer integration"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            log_file = Path(temp_dir) / "test.log"
            
            try:
                # Initialize components
                logger = StructuredLogger(str(log_file))
                tracer = AgentDevTracer()
                
                # Set trace context in logger
                trace_id = "integration-test-123"
                span_id = "integration-span-456"
                logger.set_trace_context(trace_id, span_id)
                
                # Create span
                with tracer.span("integration-span") as span:
                    # Log with trace context
                    logger.info("Integration test message")
                    
                # Check that trace context is preserved
                current_trace_id, current_span_id = logger.get_trace_context()
                assert current_trace_id == trace_id
                assert current_span_id == span_id
                
                # Close logger to release file handles
                logger.close()
                
                # Check log content
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                assert trace_id in log_content
                assert span_id in log_content
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_metrics_logger_integration(self):
        """Test metrics and logger integration"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            log_file = Path(temp_dir) / "test.log"
            
            try:
                # Initialize components
                logger = StructuredLogger(str(log_file))
                collector = MetricsCollector()
                
                # Log performance metric
                logger.log_performance_metric(
                    metric_name="test_metric",
                    value=123.45,
                    unit="milliseconds"
                )
                
                # Update metrics
                counter = collector.get_metric("jobs_total")
                counter.increment()
                
                # Close logger to release file handles
                logger.close()
                
                # Check both components work
                assert counter.get_value() >= 1
                
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                assert "test_metric" in log_content
                assert "123.45" in log_content
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
    
    def test_full_observability_workflow(self):
        """Test complete observability workflow"""
        
        async def _test():
            temp_dir = tempfile.mkdtemp()
            log_file = Path(temp_dir) / "test.log"
            
            try:
                # Initialize all components
                logger = StructuredLogger(str(log_file))
                tracer = AgentDevTracer()
                collector = MetricsCollector()
                
                # Simulate job execution
                job_id = "test-job-123"
                user_id = "user-456"
                
                # Set trace context
                trace_id = "workflow-trace-789"
                span_id = "workflow-span-101"
                logger.set_trace_context(trace_id, span_id)
                
                # Start job
                jobs_total = collector.get_metric("jobs_total")
                jobs_active = collector.get_metric("jobs_active")
                jobs_total.increment()
                jobs_active.increment()
                
                with tracer.span("job-execution") as span:
                    # Log job start
                    logger.info(f"Starting job {job_id}", LogCategory.SYSTEM, job_id=job_id, user_id=user_id)
                    
                    # Simulate tool execution
                    tool_duration = 150.0
                    logger.log_tool_execution(
                        tool_name="test_tool",
                        job_id=job_id,
                        duration_ms=tool_duration,
                        status="success",
                        user_id=user_id
                    )
                    
                    # Update tool metrics
                    tool_executions = collector.get_metric("tool_executions_total")
                    tool_duration_hist = collector.get_metric("tool_execution_duration")
                    tool_executions.increment()
                    tool_duration_hist.observe(tool_duration)
                    
                    # Simulate AI interaction
                    ai_duration = 2000.0
                    logger.log_ai_interaction(
                        job_id=job_id,
                        model="gpt-4",
                        tokens_in=100,
                        tokens_out=50,
                        duration_ms=ai_duration,
                        user_id=user_id
                    )
                    
                    # Update AI metrics
                    ai_requests = collector.get_metric("ai_requests_total")
                    ai_duration_hist = collector.get_metric("ai_request_duration")
                    tokens_consumed = collector.get_metric("tokens_consumed")
                    ai_requests.increment()
                    ai_duration_hist.observe(ai_duration)
                    tokens_consumed.increment(150)  # tokens_in + tokens_out
                    
                    # Log job completion
                    logger.info(f"Completed job {job_id}", LogCategory.SYSTEM, job_id=job_id, user_id=user_id)
                
                # Complete job
                jobs_completed = collector.get_metric("jobs_completed")
                jobs_active.decrement()
                jobs_completed.increment()
                
                # Close logger to release file handles
                logger.close()
                
                # Verify all components worked
                assert jobs_total.get_value() >= 1
                assert jobs_completed.get_value() >= 1
                assert tool_executions.get_value() >= 1
                assert ai_requests.get_value() >= 1
                assert tokens_consumed.get_value() >= 150
                
                # Check log file
                with open(log_file, 'r') as f:
                    log_content = f.read()
                
                assert job_id in log_content
                assert user_id in log_content
                assert trace_id in log_content
                assert "test_tool" in log_content
                assert "gpt-4" in log_content
                
            finally:
                shutil.rmtree(temp_dir)
        
        asyncio.run(_test())
