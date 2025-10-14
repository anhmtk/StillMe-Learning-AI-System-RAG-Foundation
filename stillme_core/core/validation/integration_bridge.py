"""
🌉 INTEGRATION BRIDGE

Integration bridge for StillMe validation framework.

Author: AgentDev System
Version: 1.0.0
Phase: 0.1 - Security Remediation
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class IntegrationEvent:
    """Represents an integration event"""

    event_type: str
    source: str
    target: str
    data: dict[str, Any]
    timestamp: datetime
    status: str = "pending"


class IntegrationHandler(ABC):
    """Abstract base class for integration handlers"""

    @abstractmethod
    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can handle the event type"""
        pass

    @abstractmethod
    def handle(self, event: IntegrationEvent) -> dict[str, Any]:
        """Handle the integration event"""
        pass


class ValidationIntegrationHandler(IntegrationHandler):
    """Handler for validation integration events"""

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can handle validation events"""
        return event_type.startswith("validation_")

    def handle(self, event: IntegrationEvent) -> dict[str, Any]:
        """Handle validation integration event"""
        logger.info(f"Handling validation event: {event.event_type}")

        # Simulate validation processing
        result = {
            "event_id": event.event_type,
            "status": "processed",
            "result": "validation_completed",
            "timestamp": datetime.now().isoformat(),
            "details": event.data,
        }

        return result


class SecurityIntegrationHandler(IntegrationHandler):
    """Handler for security integration events"""

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can handle security events"""
        return event_type.startswith("security_")

    def handle(self, event: IntegrationEvent) -> dict[str, Any]:
        """Handle security integration event"""
        logger.info(f"Handling security event: {event.event_type}")

        # Simulate security processing
        result = {
            "event_id": event.event_type,
            "status": "processed",
            "result": "security_check_completed",
            "timestamp": datetime.now().isoformat(),
            "details": event.data,
        }

        return result


class PerformanceIntegrationHandler(IntegrationHandler):
    """Handler for performance integration events"""

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can handle performance events"""
        return event_type.startswith("performance_")

    def handle(self, event: IntegrationEvent) -> dict[str, Any]:
        """Handle performance integration event"""
        logger.info(f"Handling performance event: {event.event_type}")

        # Simulate performance processing
        result = {
            "event_id": event.event_type,
            "status": "processed",
            "result": "performance_analysis_completed",
            "timestamp": datetime.now().isoformat(),
            "details": event.data,
        }

        return result


class IntegrationBridge:
    """
    Integration bridge for connecting different components
    """

    def __init__(self):
        self.handlers: list[IntegrationHandler] = []
        self.event_queue: list[IntegrationEvent] = []
        self.processed_events: list[IntegrationEvent] = []
        self.integration_stats = {
            "total_events": 0,
            "processed_events": 0,
            "failed_events": 0,
            "handler_counts": {},
        }

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default integration handlers"""
        default_handlers = [
            ValidationIntegrationHandler(),
            SecurityIntegrationHandler(),
            PerformanceIntegrationHandler(),
        ]

        for handler in default_handlers:
            self.register_handler(handler)

    def register_handler(self, handler: IntegrationHandler):
        """Register an integration handler"""
        self.handlers.append(handler)
        logger.info(f"Registered integration handler: {handler.__class__.__name__}")

    def unregister_handler(self, handler: IntegrationHandler):
        """Unregister an integration handler"""
        if handler in self.handlers:
            self.handlers.remove(handler)
            logger.info(
                f"Unregistered integration handler: {handler.__class__.__name__}"
            )

    def send_event(
        self, event_type: str, source: str, target: str, data: dict[str, Any]
    ) -> str:
        """Send an integration event"""
        event = IntegrationEvent(
            event_type=event_type,
            source=source,
            target=target,
            data=data,
            timestamp=datetime.now(),
        )

        self.event_queue.append(event)
        self.integration_stats["total_events"] += 1

        logger.info(f"Sent integration event: {event_type} from {source} to {target}")
        return event.event_type

    def process_events(self) -> dict[str, Any]:
        """Process pending integration events"""
        processed_count = 0
        failed_count = 0

        while self.event_queue:
            event = self.event_queue.pop(0)

            try:
                # Find appropriate handler
                handler = self._find_handler(event.event_type)
                if handler:
                    handler.handle(event)
                    event.status = "processed"
                    self.processed_events.append(event)
                    processed_count += 1

                    # Update handler stats
                    handler_name = handler.__class__.__name__
                    self.integration_stats["handler_counts"][handler_name] = (
                        self.integration_stats["handler_counts"].get(handler_name, 0)
                        + 1
                    )

                    logger.info(
                        f"Processed event: {event.event_type} with {handler_name}"
                    )
                else:
                    event.status = "failed"
                    self.processed_events.append(event)
                    failed_count += 1
                    logger.warning(f"No handler found for event: {event.event_type}")

            except Exception as e:
                event.status = "failed"
                self.processed_events.append(event)
                failed_count += 1
                logger.error(f"Error processing event {event.event_type}: {e}")

        self.integration_stats["processed_events"] += processed_count
        self.integration_stats["failed_events"] += failed_count

        return {
            "processed_count": processed_count,
            "failed_count": failed_count,
            "remaining_events": len(self.event_queue),
            "total_processed": self.integration_stats["processed_events"],
            "total_failed": self.integration_stats["failed_events"],
        }

    def _find_handler(self, event_type: str) -> IntegrationHandler | None:
        """Find appropriate handler for event type"""
        for handler in self.handlers:
            if handler.can_handle(event_type):
                return handler
        return None

    def get_integration_summary(self) -> dict[str, Any]:
        """Get integration summary"""
        return {
            "total_events": self.integration_stats["total_events"],
            "processed_events": self.integration_stats["processed_events"],
            "failed_events": self.integration_stats["failed_events"],
            "success_rate": (
                self.integration_stats["processed_events"]
                / max(self.integration_stats["total_events"], 1)
                * 100
            ),
            "registered_handlers": len(self.handlers),
            "handler_types": [handler.__class__.__name__ for handler in self.handlers],
            "handler_counts": self.integration_stats["handler_counts"],
            "pending_events": len(self.event_queue),
            "recent_events": [
                {
                    "event_type": event.event_type,
                    "source": event.source,
                    "target": event.target,
                    "status": event.status,
                    "timestamp": event.timestamp.isoformat(),
                }
                for event in self.processed_events[-10:]
            ],
        }

    def clear_old_events(self, hours: int = 24):
        """Clear old processed events"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        self.processed_events = [
            event for event in self.processed_events if event.timestamp >= cutoff_time
        ]

        logger.info(f"Cleared events older than {hours} hours")


def main():
    """Test the integration bridge"""
    bridge = IntegrationBridge()

    print("🌉 Integration Bridge Test:")

    # Send some test events
    test_events = [
        ("validation_input", "user_input", "validation_engine", {"input": "test data"}),
        ("security_scan", "security_scanner", "security_engine", {"threats": []}),
        ("performance_metrics", "performance_monitor", "analytics_engine", {"cpu": 50}),
        ("unknown_event", "unknown_source", "unknown_target", {"data": "test"}),
    ]

    for event_type, source, target, data in test_events:
        event_id = bridge.send_event(event_type, source, target, data)
        print(f"✅ Sent event: {event_id}")

    # Process events
    result = bridge.process_events()
    print("\n📊 Processing Results:")
    print(f"Processed: {result['processed_count']}")
    print(f"Failed: {result['failed_count']}")
    print(f"Remaining: {result['remaining_events']}")

    # Get integration summary
    summary = bridge.get_integration_summary()
    print("\n📈 Integration Summary:")
    print(f"Total events: {summary['total_events']}")
    print(f"Success rate: {summary['success_rate']:.1f}%")
    print(f"Registered handlers: {summary['registered_handlers']}")
    print(f"Handler types: {summary['handler_types']}")
    print(f"Handler counts: {summary['handler_counts']}")


if __name__ == "__main__":
    main()