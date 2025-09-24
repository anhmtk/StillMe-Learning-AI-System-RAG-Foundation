#!/usr/bin/env python3
"""
AgentDev Event Bus Tests - SEAL-GRADE
Comprehensive testing for Redis Event Bus functionality
"""

import asyncio
import pytest
import time
import json
from unittest.mock import AsyncMock, MagicMock

from agentdev.event_bus.redis_event_bus import (
    RedisEventBus, Event, EventType, EventPriority, EventHandler,
    get_event_bus, set_global_event_bus, publish_event, register_handler
)

class TestRedisEventBus:
    """Test Redis Event Bus functionality"""
    
    def test_event_bus_initialization(self):
        """Test event bus initialization"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Should have default values
            assert event_bus.namespace == "agentdev"
            assert event_bus.max_retries == 3
            assert event_bus.retry_delay == 1.0
            assert event_bus.dlq_enabled == True
            assert event_bus.running == False
            
            # Should have empty handlers
            assert len(event_bus.handlers) == 0
            
            # Should have metrics initialized
            assert event_bus.metrics["events_published"] == 0
            assert event_bus.metrics["events_processed"] == 0
            assert event_bus.metrics["events_failed"] == 0
            
        asyncio.run(_test())
    
    def test_event_creation(self):
        """Test event creation"""
        
        async def _test():
            event = Event(
                event_id="test-123",
                event_type=EventType.JOB_STARTED,
                priority=EventPriority.HIGH,
                timestamp=time.time(),
                source="test_source",
                data={"key": "value"}
            )
            
            assert event.event_id == "test-123"
            assert event.event_type == EventType.JOB_STARTED
            assert event.priority == EventPriority.HIGH
            assert event.source == "test_source"
            assert event.data == {"key": "value"}
            assert event.retry_count == 0
            assert event.max_retries == 3
            
        asyncio.run(_test())
    
    def test_handler_registration(self):
        """Test event handler registration"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Mock handler function
            def test_handler(event):
                pass
            
            # Register handler
            handler_id = event_bus.register_handler(
                event_types=[EventType.JOB_STARTED],
                handler_func=test_handler,
                priority=5
            )
            
            # Should have handler registered
            assert handler_id in event_bus.handlers
            assert event_bus.metrics["handlers_registered"] == 1
            
            handler = event_bus.handlers[handler_id]
            assert EventType.JOB_STARTED in handler.event_types
            assert handler.priority == 5
            assert handler.async_handler == False
            
        asyncio.run(_test())
    
    def test_async_handler_registration(self):
        """Test async event handler registration"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Mock async handler function
            async def async_test_handler(event):
                pass
            
            # Register async handler
            handler_id = event_bus.register_handler(
                event_types=[EventType.JOB_COMPLETED],
                handler_func=async_test_handler
            )
            
            # Should have handler registered
            assert handler_id in event_bus.handlers
            
            handler = event_bus.handlers[handler_id]
            assert EventType.JOB_COMPLETED in handler.event_types
            assert handler.async_handler == True
            
        asyncio.run(_test())
    
    def test_handler_unregistration(self):
        """Test event handler unregistration"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Mock handler function
            def test_handler(event):
                pass
            
            # Register handler
            handler_id = event_bus.register_handler(
                event_types=[EventType.JOB_STARTED],
                handler_func=test_handler
            )
            
            # Should have handler registered
            assert handler_id in event_bus.handlers
            assert event_bus.metrics["handlers_registered"] == 1
            
            # Unregister handler
            event_bus.unregister_handler(handler_id)
            
            # Should not have handler
            assert handler_id not in event_bus.handlers
            assert event_bus.metrics["handlers_registered"] == 0
            
        asyncio.run(_test())
    
    def test_channel_generation(self):
        """Test Redis channel generation"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Test different event types and priorities
            channel1 = event_bus._get_channel(EventType.JOB_STARTED, EventPriority.HIGH)
            assert channel1 == "agentdev:job_started:high"
            
            channel2 = event_bus._get_channel(EventType.AI_REQUEST, EventPriority.NORMAL)
            assert channel2 == "agentdev:ai_request:normal"
            
            channel3 = event_bus._get_channel(EventType.SECURITY_EVENT, EventPriority.CRITICAL)
            assert channel3 == "agentdev:security_event:critical"
            
        asyncio.run(_test())
    
    def test_event_publishing(self):
        """Test event publishing"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Mock Redis client
            mock_redis = AsyncMock()
            mock_redis.publish.return_value = 1
            event_bus.redis_client = mock_redis
            
            # Publish event
            event_id = await event_bus.publish(
                event_type=EventType.JOB_STARTED,
                data={"job_id": "test-job-123"},
                priority=EventPriority.HIGH,
                source="test_source"
            )
            
            # Should return event ID
            assert event_id is not None
            
            # Should call Redis publish
            mock_redis.publish.assert_called_once()
            
            # Should update metrics
            assert event_bus.metrics["events_published"] == 1
            
        asyncio.run(_test())
    
    def test_event_handling(self):
        """Test event handling"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Track handled events
            handled_events = []
            
            # Mock handler function
            def test_handler(event):
                handled_events.append(event)
            
            # Register handler
            handler_id = event_bus.register_handler(
                event_types=[EventType.JOB_STARTED],
                handler_func=test_handler
            )
            
            # Create test event
            event = Event(
                event_id="test-123",
                event_type=EventType.JOB_STARTED,
                priority=EventPriority.NORMAL,
                timestamp=time.time(),
                source="test_source",
                data={"key": "value"}
            )
            
            # Handle event
            await event_bus._handle_event(event)
            
            # Should have handled event
            assert len(handled_events) == 1
            assert handled_events[0].event_id == "test-123"
            assert event_bus.metrics["events_processed"] == 1
            
        asyncio.run(_test())
    
    def test_async_event_handling(self):
        """Test async event handling"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Track handled events
            handled_events = []
            
            # Mock async handler function
            async def async_test_handler(event):
                handled_events.append(event)
            
            # Register async handler
            handler_id = event_bus.register_handler(
                event_types=[EventType.JOB_COMPLETED],
                handler_func=async_test_handler
            )
            
            # Create test event
            event = Event(
                event_id="test-456",
                event_type=EventType.JOB_COMPLETED,
                priority=EventPriority.NORMAL,
                timestamp=time.time(),
                source="test_source"
            )
            
            # Handle event
            await event_bus._handle_event(event)
            
            # Should have handled event
            assert len(handled_events) == 1
            assert handled_events[0].event_id == "test-456"
            assert event_bus.metrics["events_processed"] == 1
            
        asyncio.run(_test())
    
    def test_event_filtering(self):
        """Test event filtering"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Track handled events
            handled_events = []
            
            # Mock handler function
            def test_handler(event):
                handled_events.append(event)
            
            # Filter function - only handle events with specific data
            def filter_func(event):
                return event.data and event.data.get("filter_me") == True
            
            # Register handler with filter
            handler_id = event_bus.register_handler(
                event_types=[EventType.JOB_STARTED],
                handler_func=test_handler,
                filter_func=filter_func
            )
            
            # Create events - one should be filtered out
            event1 = Event(
                event_id="test-1",
                event_type=EventType.JOB_STARTED,
                priority=EventPriority.NORMAL,
                timestamp=time.time(),
                source="test_source",
                data={"filter_me": True}
            )
            
            event2 = Event(
                event_id="test-2",
                event_type=EventType.JOB_STARTED,
                priority=EventPriority.NORMAL,
                timestamp=time.time(),
                source="test_source",
                data={"filter_me": False}
            )
            
            # Handle events
            await event_bus._handle_event(event1)
            await event_bus._handle_event(event2)
            
            # Should only handle event1
            assert len(handled_events) == 1
            assert handled_events[0].event_id == "test-1"
            assert event_bus.metrics["events_processed"] == 1
            
        asyncio.run(_test())
    
    def test_handler_priority(self):
        """Test handler priority ordering"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Track handler execution order
            execution_order = []
            
            # Mock handler functions
            def low_priority_handler(event):
                execution_order.append("low")
            
            def high_priority_handler(event):
                execution_order.append("high")
            
            def medium_priority_handler(event):
                execution_order.append("medium")
            
            # Register handlers with different priorities
            event_bus.register_handler(
                event_types=[EventType.JOB_STARTED],
                handler_func=low_priority_handler,
                priority=1
            )
            
            event_bus.register_handler(
                event_types=[EventType.JOB_STARTED],
                handler_func=high_priority_handler,
                priority=10
            )
            
            event_bus.register_handler(
                event_types=[EventType.JOB_STARTED],
                handler_func=medium_priority_handler,
                priority=5
            )
            
            # Create test event
            event = Event(
                event_id="test-priority",
                event_type=EventType.JOB_STARTED,
                priority=EventPriority.NORMAL,
                timestamp=time.time(),
                source="test_source"
            )
            
            # Handle event
            await event_bus._handle_event(event)
            
            # Should execute in priority order (high, medium, low)
            assert execution_order == ["high", "medium", "low"]
            assert event_bus.metrics["events_processed"] == 3
            
        asyncio.run(_test())
    
    def test_event_retry_mechanism(self):
        """Test event retry mechanism"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Mock Redis client to prevent real connection
            mock_redis = AsyncMock()
            mock_redis.publish.return_value = 1
            event_bus.redis_client = mock_redis
            
            # Track retry attempts
            retry_count = 0
            
            # Mock handler that fails first time
            def failing_handler(event):
                nonlocal retry_count
                retry_count += 1
                if retry_count < 3:
                    raise Exception("Handler failed")
            
            # Register handler
            handler_id = event_bus.register_handler(
                event_types=[EventType.JOB_STARTED],
                handler_func=failing_handler
            )
            
            # Create test event
            event = Event(
                event_id="test-retry",
                event_type=EventType.JOB_STARTED,
                priority=EventPriority.NORMAL,
                timestamp=time.time(),
                source="test_source",
                max_retries=2
            )
            
            # Handle event (should fail and retry)
            await event_bus._handle_event(event)
            
            # Should have failed and attempted retry
            assert retry_count == 1  # Only initial attempt (retry is async)
            assert event_bus.metrics["events_retried"] == 1
            
        asyncio.run(_test())
    
    def test_dead_letter_queue(self):
        """Test dead letter queue functionality"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Mock Redis client for DLQ
            mock_redis = AsyncMock()
            mock_redis.lpush.return_value = 1
            event_bus.redis_client = mock_redis
            
            # Mock handler that always fails
            def always_failing_handler(event):
                raise Exception("Always fails")
            
            # Register handler
            handler_id = event_bus.register_handler(
                event_types=[EventType.JOB_STARTED],
                handler_func=always_failing_handler
            )
            
            # Create test event with no retries
            event = Event(
                event_id="test-dlq",
                event_type=EventType.JOB_STARTED,
                priority=EventPriority.NORMAL,
                timestamp=time.time(),
                source="test_source",
                max_retries=0
            )
            
            # Handle event (should fail and go to DLQ)
            await event_bus._handle_event(event)
            
            # Should have sent to DLQ
            mock_redis.lpush.assert_called_once()
            assert event_bus.metrics["events_failed"] == 1
            
        asyncio.run(_test())
    
    def test_health_status(self):
        """Test health status functionality"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Mock Redis client
            mock_redis = AsyncMock()
            mock_redis.ping.return_value = True
            event_bus.redis_client = mock_redis
            
            # Test health status
            health = await event_bus.get_health_status()
            
            assert "status" in health
            assert "last_check" in health
            assert "running" in health
            assert "handlers" in health
            assert "metrics" in health
            
            assert health["running"] == False
            assert health["handlers"] == 0
            
        asyncio.run(_test())
    
    def test_metrics_tracking(self):
        """Test metrics tracking"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Mock Redis client
            mock_redis = AsyncMock()
            mock_redis.publish.return_value = 1
            event_bus.redis_client = mock_redis
            
            # Publish some events
            await event_bus.publish(EventType.JOB_STARTED)
            await event_bus.publish(EventType.JOB_COMPLETED)
            
            # Get metrics
            metrics = await event_bus.get_metrics()
            
            assert metrics["events_published"] == 2
            assert metrics["events_processed"] == 0  # No handlers
            assert metrics["events_failed"] == 0
            assert metrics["events_retried"] == 0
            
        asyncio.run(_test())

class TestEventBusIntegration:
    """Test Event Bus integration scenarios"""
    
    def test_job_lifecycle_events(self):
        """Test job lifecycle event flow"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Track job events
            job_events = []
            
            # Mock handler for job events
            def job_handler(event):
                job_events.append({
                    "type": event.event_type.value,
                    "data": event.data
                })
            
            # Register handler for all job events
            event_bus.register_handler(
                event_types=[EventType.JOB_STARTED, EventType.JOB_COMPLETED, EventType.JOB_FAILED],
                handler_func=job_handler
            )
            
            # Mock Redis client
            mock_redis = AsyncMock()
            mock_redis.publish.return_value = 1
            event_bus.redis_client = mock_redis
            
            # Simulate job lifecycle
            job_id = "test-job-123"
            
            # Job started
            await event_bus.publish(
                EventType.JOB_STARTED,
                data={"job_id": job_id, "user_id": "user-456"}
            )
            
            # Job completed
            await event_bus.publish(
                EventType.JOB_COMPLETED,
                data={"job_id": job_id, "duration_ms": 1500}
            )
            
            # Handle events
            for event_data in [
                {"event_id": "1", "event_type": EventType.JOB_STARTED, "priority": EventPriority.NORMAL, 
                 "timestamp": time.time(), "source": "system", "data": {"job_id": job_id}},
                {"event_id": "2", "event_type": EventType.JOB_COMPLETED, "priority": EventPriority.NORMAL, 
                 "timestamp": time.time(), "source": "system", "data": {"job_id": job_id}}
            ]:
                event = Event(**event_data)
                await event_bus._handle_event(event)
            
            # Should have handled both events
            assert len(job_events) == 2
            assert job_events[0]["type"] == "job_started"
            assert job_events[1]["type"] == "job_completed"
            
        asyncio.run(_test())
    
    def test_ai_request_events(self):
        """Test AI request event flow"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Track AI events
            ai_events = []
            
            # Mock handler for AI events
            def ai_handler(event):
                ai_events.append({
                    "type": event.event_type.value,
                    "model": event.data.get("model"),
                    "tokens": event.data.get("tokens_in", 0)
                })
            
            # Register handler
            event_bus.register_handler(
                event_types=[EventType.AI_REQUEST],
                handler_func=ai_handler
            )
            
            # Create AI request event
            event = Event(
                event_id="ai-123",
                event_type=EventType.AI_REQUEST,
                priority=EventPriority.HIGH,
                timestamp=time.time(),
                source="ai_service",
                data={
                    "model": "gpt-4",
                    "tokens_in": 100,
                    "tokens_out": 50
                }
            )
            
            # Handle event
            await event_bus._handle_event(event)
            
            # Should have handled AI event
            assert len(ai_events) == 1
            assert ai_events[0]["type"] == "ai_request"
            assert ai_events[0]["model"] == "gpt-4"
            assert ai_events[0]["tokens"] == 100
            
        asyncio.run(_test())
    
    def test_security_event_handling(self):
        """Test security event handling"""
        
        async def _test():
            event_bus = RedisEventBus()
            
            # Track security events
            security_events = []
            
            # Mock handler for security events
            def security_handler(event):
                security_events.append({
                    "type": event.event_type.value,
                    "severity": event.data.get("severity"),
                    "event": event.data.get("event_type")
                })
            
            # Register handler
            event_bus.register_handler(
                event_types=[EventType.SECURITY_EVENT],
                handler_func=security_handler
            )
            
            # Create security event
            event = Event(
                event_id="sec-123",
                event_type=EventType.SECURITY_EVENT,
                priority=EventPriority.CRITICAL,
                timestamp=time.time(),
                source="security_service",
                data={
                    "event_type": "unauthorized_access",
                    "severity": "high",
                    "ip": "192.168.1.100"
                }
            )
            
            # Handle event
            await event_bus._handle_event(event)
            
            # Should have handled security event
            assert len(security_events) == 1
            assert security_events[0]["type"] == "security_event"
            assert security_events[0]["severity"] == "high"
            assert security_events[0]["event"] == "unauthorized_access"
            
        asyncio.run(_test())

class TestGlobalEventBus:
    """Test global event bus functionality"""
    
    def test_global_event_bus_singleton(self):
        """Test global event bus singleton"""
        
        async def _test():
            # Get global event bus
            event_bus1 = get_event_bus()
            event_bus2 = get_event_bus()
            
            # Should be the same instance
            assert event_bus1 is event_bus2
            
        asyncio.run(_test())
    
    def test_global_event_bus_replacement(self):
        """Test global event bus replacement"""
        
        async def _test():
            # Create new event bus
            new_event_bus = RedisEventBus(namespace="test")
            
            # Set as global
            set_global_event_bus(new_event_bus)
            
            # Get global event bus
            global_event_bus = get_event_bus()
            
            # Should be the new instance
            assert global_event_bus is new_event_bus
            assert global_event_bus.namespace == "test"
            
        asyncio.run(_test())
    
    def test_convenience_functions(self):
        """Test convenience functions"""
        
        async def _test():
            # Mock Redis client
            mock_redis = AsyncMock()
            mock_redis.publish.return_value = 1
            
            # Get global event bus and set mock
            event_bus = get_event_bus()
            event_bus.redis_client = mock_redis
            
            # Test publish_event convenience function
            event_id = await publish_event(
                EventType.JOB_STARTED,
                data={"test": "data"},
                priority=EventPriority.HIGH
            )
            
            assert event_id is not None
            mock_redis.publish.assert_called_once()
            
        asyncio.run(_test())
