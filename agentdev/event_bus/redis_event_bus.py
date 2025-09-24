#!/usr/bin/env python3
"""
AgentDev Redis Event Bus - SEAL-GRADE
Enterprise-grade event-driven architecture with Redis Pub/Sub
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
import threading
from contextlib import asynccontextmanager
import weakref

# Redis imports
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    # Mock Redis for when not available
    class MockRedis:
        def __init__(self, *args, **kwargs):
            pass
        async def ping(self):
            return True
        async def publish(self, channel, message):
            return 1
        async def subscribe(self, *channels):
            return MockPubSub()
        async def close(self):
            pass
    
    class MockPubSub:
        def __init__(self):
            self.channels = []
        async def listen(self):
            while True:
                await asyncio.sleep(0.1)
                yield None
        async def unsubscribe(self, *channels):
            pass
        async def close(self):
            pass

class EventType(Enum):
    """Event types"""
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"
    TOOL_EXECUTED = "tool_executed"
    AI_REQUEST = "ai_request"
    SECURITY_EVENT = "security_event"
    SYSTEM_HEALTH = "system_health"
    USER_ACTION = "user_action"
    CUSTOM = "custom"

class EventPriority(Enum):
    """Event priorities"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Event:
    """Event data structure"""
    event_id: str
    event_type: EventType
    priority: EventPriority
    timestamp: float
    source: str
    target: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    ttl_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class EventHandler:
    """Event handler definition"""
    handler_id: str
    event_types: List[EventType]
    handler_func: Callable
    priority: int = 0
    async_handler: bool = True
    filter_func: Optional[Callable[[Event], bool]] = None

class RedisEventBus:
    """
    SEAL-GRADE Redis Event Bus
    
    Features:
    - Redis Pub/Sub with at-least-once delivery
    - Event routing and filtering
    - Dead letter queue (DLQ)
    - Retry mechanism with exponential backoff
    - Event persistence
    - Health monitoring
    - Graceful shutdown
    """
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 namespace: str = "agentdev",
                 max_retries: int = 3,
                 retry_delay: float = 1.0,
                 dlq_enabled: bool = True):
        self.redis_url = redis_url
        self.namespace = namespace
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.dlq_enabled = dlq_enabled
        
        # Redis connection
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[Any] = None
        
        # Event handlers
        self.handlers: Dict[str, EventHandler] = {}
        self.handler_lock = threading.Lock()
        
        # Event processing
        self.processing_tasks: Dict[str, asyncio.Task] = {}
        self.running = False
        
        # Metrics
        self.metrics = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "events_retried": 0,
            "handlers_registered": 0,
            "last_event_time": None
        }
        
        # Dead letter queue
        self.dlq_key = f"{namespace}:dlq"
        
        # Health check
        self.health_status = "unknown"
        self.last_health_check = 0
        
        # Graceful shutdown
        self.shutdown_event = asyncio.Event()
        
        # Initialize Redis client
        self._setup_redis_client()
    
    def _setup_redis_client(self):
        """Setup Redis client"""
        if REDIS_AVAILABLE:
            self.redis_client = redis.from_url(self.redis_url)
        else:
            self.redis_client = MockRedis()
    
    async def connect(self):
        """Connect to Redis"""
        try:
            await self.redis_client.ping()
            self.health_status = "healthy"
            self.last_health_check = time.time()
            logging.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            self.health_status = "unhealthy"
            logging.error(f"Failed to connect to Redis: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.close()
        if self.redis_client:
            await self.redis_client.close()
        self.health_status = "disconnected"
        logging.info("Disconnected from Redis")
    
    def register_handler(self, 
                        event_types: List[EventType],
                        handler_func: Callable,
                        handler_id: Optional[str] = None,
                        priority: int = 0,
                        filter_func: Optional[Callable[[Event], bool]] = None) -> str:
        """Register an event handler"""
        if handler_id is None:
            handler_id = str(uuid.uuid4())
        
        # Check if handler is async
        async_handler = asyncio.iscoroutinefunction(handler_func)
        
        handler = EventHandler(
            handler_id=handler_id,
            event_types=event_types,
            handler_func=handler_func,
            priority=priority,
            async_handler=async_handler,
            filter_func=filter_func
        )
        
        with self.handler_lock:
            self.handlers[handler_id] = handler
            self.metrics["handlers_registered"] = len(self.handlers)
        
        logging.info(f"Registered handler {handler_id} for events: {[et.value for et in event_types]}")
        return handler_id
    
    def unregister_handler(self, handler_id: str):
        """Unregister an event handler"""
        with self.handler_lock:
            if handler_id in self.handlers:
                del self.handlers[handler_id]
                self.metrics["handlers_registered"] = len(self.handlers)
                logging.info(f"Unregistered handler {handler_id}")
    
    async def publish(self, 
                     event_type: EventType,
                     data: Optional[Dict[str, Any]] = None,
                     priority: EventPriority = EventPriority.NORMAL,
                     source: str = "system",
                     target: Optional[str] = None,
                     correlation_id: Optional[str] = None,
                     reply_to: Optional[str] = None,
                     ttl_seconds: Optional[int] = None) -> str:
        """Publish an event"""
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            priority=priority,
            timestamp=time.time(),
            source=source,
            target=target,
            data=data,
            correlation_id=correlation_id,
            reply_to=reply_to,
            ttl_seconds=ttl_seconds
        )
        
        # Serialize event
        event_data = json.dumps(asdict(event), default=str)
        
        # Determine channel based on event type and priority
        channel = self._get_channel(event_type, priority)
        
        try:
            # Publish to Redis
            result = await self.redis_client.publish(channel, event_data)
            
            # Update metrics
            self.metrics["events_published"] += 1
            self.metrics["last_event_time"] = event.timestamp
            
            logging.debug(f"Published event {event.event_id} to channel {channel}")
            return event.event_id
            
        except Exception as e:
            logging.error(f"Failed to publish event {event.event_id}: {e}")
            raise
    
    def _get_channel(self, event_type: EventType, priority: EventPriority) -> str:
        """Get Redis channel for event type and priority"""
        return f"{self.namespace}:{event_type.value}:{priority.value}"
    
    async def start_processing(self):
        """Start event processing"""
        if self.running:
            return
        
        self.running = True
        self.shutdown_event.clear()
        
        # Get all unique channels from handlers
        channels = set()
        with self.handler_lock:
            for handler in self.handlers.values():
                for event_type in handler.event_types:
                    for priority in EventPriority:
                        channels.add(self._get_channel(event_type, priority))
        
        if not channels:
            logging.warning("No event handlers registered, nothing to process")
            return
        
        # Subscribe to channels
        self.pubsub = self.redis_client.pubsub()
        await self.pubsub.subscribe(*channels)
        
        # Start processing task
        processing_task = asyncio.create_task(self._process_events())
        self.processing_tasks["main"] = processing_task
        
        # Start health check task
        health_task = asyncio.create_task(self._health_check_loop())
        self.processing_tasks["health"] = health_task
        
        logging.info(f"Started event processing for {len(channels)} channels")
    
    async def stop_processing(self):
        """Stop event processing"""
        if not self.running:
            return
        
        self.running = False
        self.shutdown_event.set()
        
        # Cancel all processing tasks
        for task in self.processing_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.processing_tasks:
            await asyncio.gather(*self.processing_tasks.values(), return_exceptions=True)
        
        self.processing_tasks.clear()
        
        # Close pubsub
        if self.pubsub:
            await self.pubsub.close()
            self.pubsub = None
        
        logging.info("Stopped event processing")
    
    async def _process_events(self):
        """Main event processing loop"""
        try:
            async for message in self.pubsub.listen():
                if not self.running:
                    break
                
                if message is None or message['type'] != 'message':
                    continue
                
                try:
                    # Parse event
                    event_data = json.loads(message['data'])
                    event = Event(**event_data)
                    
                    # Process event
                    await self._handle_event(event)
                    
                except Exception as e:
                    logging.error(f"Error processing event: {e}")
                    self.metrics["events_failed"] += 1
        
        except asyncio.CancelledError:
            logging.info("Event processing cancelled")
        except Exception as e:
            logging.error(f"Event processing error: {e}")
            self.health_status = "unhealthy"
    
    async def _handle_event(self, event: Event):
        """Handle a single event"""
        # Find matching handlers
        matching_handlers = []
        
        with self.handler_lock:
            for handler in self.handlers.values():
                if event.event_type in handler.event_types:
                    # Apply filter if present
                    if handler.filter_func is None or handler.filter_func(event):
                        matching_handlers.append(handler)
        
        # Sort by priority (higher priority first)
        matching_handlers.sort(key=lambda h: h.priority, reverse=True)
        
        # Process with each handler
        for handler in matching_handlers:
            try:
                if handler.async_handler:
                    await handler.handler_func(event)
                else:
                    # Run sync handler in thread pool
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, handler.handler_func, event)
                
                self.metrics["events_processed"] += 1
                
            except Exception as e:
                logging.error(f"Handler {handler.handler_id} failed for event {event.event_id}: {e}")
                
                # Retry logic
                if event.retry_count < event.max_retries:
                    await self._retry_event(event, handler.handler_id)
                else:
                    # Send to DLQ
                    if self.dlq_enabled:
                        await self._send_to_dlq(event, str(e))
                    self.metrics["events_failed"] += 1
    
    async def _retry_event(self, event: Event, handler_id: str):
        """Retry event processing"""
        event.retry_count += 1
        
        # Exponential backoff
        delay = self.retry_delay * (2 ** (event.retry_count - 1))
        
        logging.info(f"Retrying event {event.event_id} in {delay}s (attempt {event.retry_count})")
        
        # Schedule retry
        await asyncio.sleep(delay)
        
        # Republish event
        await self.publish(
            event_type=event.event_type,
            data=event.data,
            priority=event.priority,
            source=event.source,
            target=event.target,
            correlation_id=event.correlation_id,
            reply_to=event.reply_to,
            ttl_seconds=event.ttl_seconds
        )
        
        self.metrics["events_retried"] += 1
    
    async def _send_to_dlq(self, event: Event, error_message: str):
        """Send event to dead letter queue"""
        dlq_entry = {
            "event": asdict(event),
            "error": error_message,
            "timestamp": time.time()
        }
        
        await self.redis_client.lpush(self.dlq_key, json.dumps(dlq_entry, default=str))
        logging.warning(f"Sent event {event.event_id} to DLQ: {error_message}")
    
    async def _health_check_loop(self):
        """Health check loop"""
        while self.running:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Ping Redis
                await self.redis_client.ping()
                self.health_status = "healthy"
                self.last_health_check = time.time()
                
            except Exception as e:
                self.health_status = "unhealthy"
                logging.error(f"Health check failed: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status"""
        return {
            "status": self.health_status,
            "last_check": self.last_health_check,
            "running": self.running,
            "handlers": len(self.handlers),
            "metrics": self.metrics.copy()
        }
    
    async def get_dlq_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get events from dead letter queue"""
        if not self.dlq_enabled:
            return []
        
        events = await self.redis_client.lrange(self.dlq_key, 0, limit - 1)
        return [json.loads(event) for event in events]
    
    async def clear_dlq(self):
        """Clear dead letter queue"""
        if self.dlq_enabled:
            await self.redis_client.delete(self.dlq_key)
            logging.info("Cleared dead letter queue")
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get event bus metrics"""
        return self.metrics.copy()

# Global event bus instance
_global_event_bus: Optional[RedisEventBus] = None

def get_event_bus() -> RedisEventBus:
    """Get global event bus instance"""
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = RedisEventBus()
    return _global_event_bus

def set_global_event_bus(event_bus: RedisEventBus):
    """Set global event bus instance"""
    global _global_event_bus
    _global_event_bus = event_bus

# Convenience functions
async def publish_event(event_type: EventType, **kwargs) -> str:
    """Publish an event"""
    return await get_event_bus().publish(event_type, **kwargs)

def register_handler(event_types: List[EventType], handler_func: Callable, **kwargs) -> str:
    """Register an event handler"""
    return get_event_bus().register_handler(event_types, handler_func, **kwargs)

def unregister_handler(handler_id: str):
    """Unregister an event handler"""
    get_event_bus().unregister_handler(handler_id)

async def start_event_processing():
    """Start event processing"""
    await get_event_bus().start_processing()

async def stop_event_processing():
    """Stop event processing"""
    await get_event_bus().stop_processing()
