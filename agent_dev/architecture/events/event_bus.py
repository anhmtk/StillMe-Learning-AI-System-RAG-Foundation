#!/usr/bin/env python3
"""
StillMe AgentDev - Event Bus
Enterprise-grade event-driven architecture
"""

import asyncio
import json
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import aiofiles


class EventType(Enum):
    """Event types for AgentDev system"""

    # Task events
    TASK_CREATED = "task.created"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"

    # Planning events
    PLAN_GENERATED = "plan.generated"
    PLAN_VALIDATED = "plan.validated"
    PLAN_APPROVED = "plan.approved"
    PLAN_REJECTED = "plan.rejected"

    # Execution events
    EXECUTION_STARTED = "execution.started"
    EXECUTION_STEP_STARTED = "execution.step.started"
    EXECUTION_STEP_COMPLETED = "execution.step.completed"
    EXECUTION_STEP_FAILED = "execution.step.failed"
    EXECUTION_COMPLETED = "execution.completed"
    EXECUTION_FAILED = "execution.failed"

    # Security events
    SECURITY_SCAN_STARTED = "security.scan.started"
    SECURITY_VIOLATION_DETECTED = "security.violation.detected"
    SECURITY_SCAN_COMPLETED = "security.scan.completed"

    # Policy events
    POLICY_VIOLATION = "policy.violation"
    POLICY_ENFORCED = "policy.enforced"

    # System events
    SERVICE_REGISTERED = "service.registered"
    SERVICE_UNREGISTERED = "service.unregistered"
    SERVICE_HEALTH_CHECK_FAILED = "service.health_check.failed"

    # User events
    USER_ACTION = "user.action"
    USER_FEEDBACK = "user.feedback"


@dataclass
class Event:
    """Base event class"""

    event_id: str
    event_type: EventType
    timestamp: float
    source: str
    data: dict[str, Any]
    correlation_id: str | None = None
    causation_id: str | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class EventHandler:
    """Event handler definition"""

    handler_id: str
    event_types: list[EventType]
    handler_func: Callable[[Event], Any]
    priority: int = 0
    async_handler: bool = False


class EventBus:
    """Enterprise event bus with persistence and replay capabilities"""

    def __init__(self, config_path: str | None = None):
        self.handlers: dict[EventType, list[EventHandler]] = {}
        self.event_store: list[Event] = []
        self.config = self._load_config(config_path)
        self.persistence_enabled = self.config.get("persistence", {}).get(
            "enabled", True
        )
        self.event_store_file = Path(
            self.config.get("persistence", {}).get("file", ".agentdev/events.json")
        )
        self.max_events = self.config.get("max_events", 10000)
        self.running = False

    def _load_config(self, config_path: str | None = None) -> dict[str, Any]:
        """Load event bus configuration"""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path("agent-dev/config/event_bus.yaml")

        if config_file.exists():
            import yaml

            with open(config_file) as f:
                return yaml.safe_load(f)
        else:
            return {
                "persistence": {"enabled": True, "file": ".agentdev/events.json"},
                "max_events": 10000,
                "replay_enabled": True,
            }

    def subscribe(
        self,
        event_types: list[EventType],
        handler_func: Callable[[Event], Any],
        handler_id: str | None = None,
        priority: int = 0,
        async_handler: bool = False,
    ) -> str:
        """Subscribe to events"""
        if handler_id is None:
            handler_id = f"handler_{uuid.uuid4().hex[:8]}"

        handler = EventHandler(
            handler_id=handler_id,
            event_types=event_types,
            handler_func=handler_func,
            priority=priority,
            async_handler=async_handler,
        )

        for event_type in event_types:
            if event_type not in self.handlers:
                self.handlers[event_type] = []

            self.handlers[event_type].append(handler)
            # Sort by priority (higher priority first)
            self.handlers[event_type].sort(key=lambda h: h.priority, reverse=True)

        return handler_id

    def add_handler(
        self,
        event_type: EventType,
        handler_func: Callable[[Event], Any],
        handler_id: str | None = None,
        priority: int = 0,
        async_handler: bool = False,
    ) -> str:
        """Add a single handler for an event type (alias for subscribe)"""
        handler_id = self.subscribe(
            event_types=[event_type],
            handler_func=handler_func,
            handler_id=handler_id,
            priority=priority,
            async_handler=async_handler,
        )

        print(f"✅ Event handler registered: {handler_id} for {event_type.value}")
        return handler_id

    def unsubscribe(self, handler_id: str) -> bool:
        """Unsubscribe event handler"""
        removed = False

        for event_type, handlers in self.handlers.items():
            original_count = len(handlers)
            self.handlers[event_type] = [
                h for h in handlers if h.handler_id != handler_id
            ]

            if len(self.handlers[event_type]) < original_count:
                removed = True

        if removed:
            print(f"❌ Event handler unregistered: {handler_id}")

        return removed

    async def publish(
        self,
        event_type: EventType,
        data: dict[str, Any],
        source: str,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Publish an event"""
        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=time.time(),
            source=source,
            data=data,
            correlation_id=correlation_id,
            causation_id=causation_id,
            metadata=metadata or {},
        )

        # Store event
        self.event_store.append(event)

        # Persist to disk
        if self.persistence_enabled:
            await self._persist_event(event)

        # Cleanup old events
        if len(self.event_store) > self.max_events:
            self.event_store = self.event_store[-self.max_events :]

        # Notify handlers
        await self._notify_handlers(event)

        print(f"📢 Event published: {event_type.value} from {source}")
        return event.event_id

    async def _notify_handlers(self, event: Event):
        """Notify all handlers for an event"""
        handlers = self.handlers.get(event.event_type, [])

        for handler in handlers:
            try:
                if handler.async_handler:
                    result = handler.handler_func(event)
                    # Proper type checking for awaitable result
                    if result is not None and isinstance(result, Awaitable):
                        await result
                else:
                    handler.handler_func(event)
            except Exception as e:
                print(f"⚠️ Event handler error: {handler.handler_id} - {e}")

    async def _persist_event(self, event: Event):
        """Persist event to disk"""
        try:
            self.event_store_file.parent.mkdir(parents=True, exist_ok=True)

            # Convert event to serializable format
            event_data = {**asdict(event), "event_type": event.event_type.value}

            # Append to file
            async with aiofiles.open(self.event_store_file, "a") as f:
                await f.write(json.dumps(event_data) + "\n")

        except Exception as e:
            print(f"⚠️ Failed to persist event: {e}")

    async def replay_events(
        self,
        event_types: list[EventType] | None = None,
        from_timestamp: float | None = None,
        to_timestamp: float | None = None,
    ) -> list[Event]:
        """Replay events from store"""
        events: list[Event] = []

        for event in self.event_store:
            # Filter by event type
            if event_types and event.event_type not in event_types:
                continue

            # Filter by timestamp
            if from_timestamp and event.timestamp < from_timestamp:
                continue

            if to_timestamp and event.timestamp > to_timestamp:
                continue

            events.append(event)

        return events

    async def load_events_from_disk(self):
        """Load events from disk"""
        if not self.event_store_file.exists():
            return

        try:
            async with aiofiles.open(self.event_store_file) as f:
                async for line in f:
                    if line.strip():
                        event_data = json.loads(line)

                        event = Event(
                            event_id=event_data["event_id"],
                            event_type=EventType(event_data["event_type"]),
                            timestamp=event_data["timestamp"],
                            source=event_data["source"],
                            data=event_data["data"],
                            correlation_id=event_data.get("correlation_id"),
                            causation_id=event_data.get("causation_id"),
                            metadata=event_data.get("metadata", {}),
                        )

                        self.event_store.append(event)

            print(f"📂 Loaded {len(self.event_store)} events from disk")

        except Exception as e:
            print(f"⚠️ Failed to load events from disk: {e}")

    def get_event_statistics(self) -> dict[str, Any]:
        """Get event bus statistics"""
        event_counts: dict[str, int] = {}
        for event in self.event_store:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        return {
            "total_events": len(self.event_store),
            "event_types": len({e.event_type for e in self.event_store}),
            "event_counts": event_counts,
            "handlers_registered": sum(
                len(handlers) for handlers in self.handlers.values()
            ),
            "oldest_event": min(e.timestamp for e in self.event_store)
            if self.event_store
            else None,
            "newest_event": max(e.timestamp for e in self.event_store)
            if self.event_store
            else None,
        }

    async def start(self):
        """Start the event bus"""
        if self.running:
            return

        self.running = True

        # Load events from disk
        await self.load_events_from_disk()

        print("🚀 Event Bus started")

    async def stop(self):
        """Stop the event bus"""
        self.running = False
        print("🛑 Event Bus stopped")


# Global event bus instance
event_bus = EventBus()


# Convenience functions
async def publish_task_event(
    event_type: EventType,
    task_id: str,
    data: dict[str, Any],
    correlation_id: str | None = None,
) -> str:
    """Publish task-related event"""
    return await event_bus.publish(
        event_type=event_type,
        data={**data, "task_id": task_id},
        source="agentdev-task",
        correlation_id=correlation_id,
    )


async def publish_security_event(
    event_type: EventType, data: dict[str, Any], correlation_id: str | None = None
) -> str:
    """Publish security-related event"""
    return await event_bus.publish(
        event_type=event_type,
        data=data,
        source="agentdev-security",
        correlation_id=correlation_id,
    )


async def publish_system_event(
    event_type: EventType, data: dict[str, Any], correlation_id: str | None = None
) -> str:
    """Publish system-related event"""
    return await event_bus.publish(
        event_type=event_type,
        data=data,
        source="agentdev-system",
        correlation_id=correlation_id,
    )


# Event decorators
def event_handler(
    event_types: list[EventType], priority: int = 0, async_handler: bool = False
):
    """Decorator for event handlers"""

    def decorator(func: Any):
        handler_id = event_bus.subscribe(
            event_types=event_types,
            handler_func=func,
            priority=priority,
            async_handler=async_handler,
        )
        func._event_handler_id = handler_id
        return func

    return decorator


if __name__ == "__main__":

    async def main():
        # Example usage
        bus = EventBus()
        await bus.start()

        # Define event handlers
        @event_handler([EventType.TASK_CREATED], priority=1)
        def handle_task_created(event: Event) -> None:
            print(f"🎯 Task created: {event.data.get('task_id')}")

        @event_handler([EventType.SECURITY_VIOLATION_DETECTED], priority=10)
        async def handle_security_violation(event: Event) -> None:
            print(f"🚨 Security violation: {event.data.get('violation_type')}")

        # Register handlers
        bus.add_handler(EventType.TASK_CREATED, handle_task_created)
        bus.add_handler(
            EventType.SECURITY_VIOLATION_DETECTED, handle_security_violation
        )

        # Publish events
        await publish_task_event(
            EventType.TASK_CREATED,
            "task_123",
            {"task_type": "deploy_edge", "user": "developer"},
        )

        await publish_security_event(
            EventType.SECURITY_VIOLATION_DETECTED,
            {"violation_type": "hardcoded_secret", "file": "config.py"},
        )

        # Get statistics
        stats = bus.get_event_statistics()
        print(f"Event statistics: {stats}")

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await bus.stop()

    asyncio.run(main())
