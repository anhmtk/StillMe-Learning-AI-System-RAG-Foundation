# StillMe Gateway - Notification Service
"""
Notification service for managing push notifications
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from core.config import Settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Notification service for push notifications"""

    def __init__(self):
        self.settings = Settings()
        self.is_initialized = False
        self.notification_queue: List[Dict[str, Any]] = []
        self.processing_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the notification service"""
        try:
            # Start background processing task
            self.processing_task = asyncio.create_task(self._process_notifications())

            self.is_initialized = True
            logger.info("Notification service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize notification service: {e}")
            raise

    async def cleanup(self):
        """Cleanup the notification service"""
        try:
            # Cancel processing task
            if self.processing_task:
                self.processing_task.cancel()
                try:
                    await self.processing_task
                except asyncio.CancelledError:
                    pass

            self.is_initialized = False
            logger.info("Notification service cleaned up")

        except Exception as e:
            logger.error(f"Error during notification service cleanup: {e}")

    async def send_notification(
        self,
        title: str,
        body: str,
        target_clients: Optional[List[str]] = None,
        category: str = "general",
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send notification to clients"""
        try:
            notification = {
                "id": f"notif_{int(datetime.utcnow().timestamp() * 1000)}",
                "title": title,
                "body": body,
                "category": category,
                "target_clients": target_clients,
                "data": data or {},
                "timestamp": datetime.utcnow().timestamp(),
                "status": "pending",
            }

            # Add to queue
            self.notification_queue.append(notification)

            logger.info(f"Notification queued: {title}")
            return True

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    async def send_to_all_clients(
        self,
        title: str,
        body: str,
        category: str = "general",
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send notification to all connected clients"""
        return await self.send_notification(
            title=title,
            body=body,
            target_clients=None,  # None means all clients
            category=category,
            data=data,
        )

    async def send_to_client(
        self,
        client_id: str,
        title: str,
        body: str,
        category: str = "general",
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Send notification to specific client"""
        return await self.send_notification(
            title=title,
            body=body,
            target_clients=[client_id],
            category=category,
            data=data,
        )

    async def _process_notifications(self):
        """Background task to process notification queue"""
        while True:
            try:
                await asyncio.sleep(1)  # Check every second

                if self.notification_queue:
                    notification = self.notification_queue.pop(0)
                    await self._deliver_notification(notification)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing notifications: {e}")

    async def _deliver_notification(self, notification: Dict[str, Any]):
        """Deliver a notification"""
        try:
            # This would integrate with WebSocketManager to send to clients
            # For now, just log the notification
            logger.info(f"Delivering notification: {notification['title']}")

            # Mark as delivered
            notification["status"] = "delivered"
            notification["delivered_at"] = datetime.utcnow().timestamp()

        except Exception as e:
            logger.error(f"Error delivering notification: {e}")
            notification["status"] = "failed"
            notification["error"] = str(e)

    async def get_notification_stats(self) -> Dict[str, Any]:
        """Get notification statistics"""
        try:
            total = len(self.notification_queue)
            pending = len(
                [n for n in self.notification_queue if n.get("status") == "pending"]
            )
            delivered = len(
                [n for n in self.notification_queue if n.get("status") == "delivered"]
            )
            failed = len(
                [n for n in self.notification_queue if n.get("status") == "failed"]
            )

            return {
                "total": total,
                "pending": pending,
                "delivered": delivered,
                "failed": failed,
                "queue_size": len(self.notification_queue),
            }

        except Exception as e:
            logger.error(f"Error getting notification stats: {e}")
            return {
                "total": 0,
                "pending": 0,
                "delivered": 0,
                "failed": 0,
                "queue_size": 0,
                "error": str(e),
            }

    # Getters
    def is_healthy(self) -> bool:
        """Check if notification service is healthy"""
        return self.is_initialized

    def get_queue_size(self) -> int:
        """Get current notification queue size"""
        return len(self.notification_queue)
