# StillMe Gateway - WebSocket Manager
"""
WebSocket connection manager for real-time communication
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set

from fastapi import WebSocket

from core.message_protocol import MessageProtocol, MessageType

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket connection manager"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, Dict] = {}
        self.room_connections: Dict[str, Set[str]] = {}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}

    async def connect(
        self, websocket: WebSocket, client_id: str, metadata: Optional[Dict] = None
    ):
        """Connect a new WebSocket client"""
        await websocket.accept()

        self.active_connections[client_id] = websocket
        self.connection_metadata[client_id] = metadata or {}

        # Start heartbeat task
        self.heartbeat_tasks[client_id] = asyncio.create_task(
            self._heartbeat_loop(client_id)
        )

        logger.info(f"Client {client_id} connected")

        # Notify other clients
        await self.broadcast_status(
            {
                "type": "client_connected",
                "client_id": client_id,
                "metadata": self.connection_metadata[client_id],
            },
            exclude=[client_id],
        )

    async def disconnect(self, client_id: str):
        """Disconnect a WebSocket client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]

        if client_id in self.connection_metadata:
            del self.connection_metadata[client_id]

        # Cancel heartbeat task
        if client_id in self.heartbeat_tasks:
            self.heartbeat_tasks[client_id].cancel()
            del self.heartbeat_tasks[client_id]

        # Remove from rooms
        for room_id, clients in self.room_connections.items():
            clients.discard(client_id)

        logger.info(f"Client {client_id} disconnected")

        # Notify other clients
        await self.broadcast_status(
            {"type": "client_disconnected", "client_id": client_id}
        )

    async def send_to_client(self, client_id: str, message: Dict):
        """Send message to specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_json(message)
                return True
            except Exception as e:
                logger.error(f"Error sending message to {client_id}: {e}")
                await self.disconnect(client_id)
                return False
        return False

    async def send_to_clients(self, client_ids: List[str], message: Dict):
        """Send message to multiple clients"""
        tasks = [self.send_to_client(client_id, message) for client_id in client_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def broadcast(self, message: Dict, exclude: Optional[List[str]] = None):
        """Broadcast message to all connected clients"""
        exclude = exclude or []
        tasks = []

        for client_id, websocket in self.active_connections.items():
            if client_id not in exclude:
                tasks.append(self.send_to_client(client_id, message))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        return []

    async def broadcast_status(
        self, status_message: Dict, exclude: Optional[List[str]] = None
    ):
        """Broadcast status message to all clients"""
        message = {
            "type": "status_update",
            "timestamp": status_message.get("timestamp"),
            "data": status_message,
        }
        return await self.broadcast(message, exclude)

    async def broadcast_notification(
        self, notification: Dict, target_clients: Optional[List[str]] = None
    ):
        """Broadcast notification to specific or all clients"""
        message = {
            "type": "notification",
            "timestamp": notification.get("timestamp"),
            "data": notification,
        }

        if target_clients:
            return await self.send_to_clients(target_clients, message)
        else:
            return await self.broadcast(message)

    async def join_room(self, client_id: str, room_id: str):
        """Join a client to a room"""
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()

        self.room_connections[room_id].add(client_id)
        logger.info(f"Client {client_id} joined room {room_id}")

    async def leave_room(self, client_id: str, room_id: str):
        """Remove a client from a room"""
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(client_id)
            if not self.room_connections[room_id]:
                del self.room_connections[room_id]
            logger.info(f"Client {client_id} left room {room_id}")

    async def send_to_room(
        self, room_id: str, message: Dict, exclude: Optional[List[str]] = None
    ):
        """Send message to all clients in a room"""
        if room_id in self.room_connections:
            exclude = exclude or []
            client_ids = list(self.room_connections[room_id] - set(exclude))
            return await self.send_to_clients(client_ids, message)
        return []

    async def _heartbeat_loop(self, client_id: str):
        """Heartbeat loop for a client"""
        try:
            while client_id in self.active_connections:
                await asyncio.sleep(30)  # Send heartbeat every 30 seconds

                if client_id in self.active_connections:
                    heartbeat_message = {
                        "type": "heartbeat",
                        "timestamp": asyncio.get_event_loop().time(),
                        "client_id": client_id,
                    }

                    success = await self.send_to_client(client_id, heartbeat_message)
                    if not success:
                        break

        except asyncio.CancelledError:
            logger.info(f"Heartbeat loop cancelled for client {client_id}")
        except Exception as e:
            logger.error(f"Heartbeat error for client {client_id}: {e}")
            await self.disconnect(client_id)

    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)

    def get_connected_clients(self) -> List[str]:
        """Get list of connected client IDs"""
        return list(self.active_connections.keys())

    def get_client_metadata(self, client_id: str) -> Optional[Dict]:
        """Get metadata for a client"""
        return self.connection_metadata.get(client_id)

    def get_room_clients(self, room_id: str) -> List[str]:
        """Get clients in a room"""
        return list(self.room_connections.get(room_id, set()))

    def get_rooms(self) -> List[str]:
        """Get list of active rooms"""
        return list(self.room_connections.keys())

    async def process_message(self, client_id: str, message: MessageProtocol):
        """Process incoming message from client"""
        try:
            if message.type == MessageType.HEARTBEAT:
                # Update last activity
                if client_id in self.connection_metadata:
                    self.connection_metadata[client_id][
                        "last_activity"
                    ] = message.timestamp

                # Send heartbeat acknowledgment
                await self.send_to_client(
                    client_id,
                    {
                        "type": "heartbeat_ack",
                        "timestamp": message.timestamp,
                        "client_id": client_id,
                    },
                )

            elif message.type == MessageType.COMMAND:
                # Route command to appropriate handler
                await self._route_command(client_id, message)

            elif message.type == MessageType.STATUS:
                # Broadcast status update
                await self.broadcast_status(message.to_dict(), exclude=[client_id])

            elif message.type == MessageType.NOTIFICATION:
                # Handle notification
                await self._handle_notification(client_id, message)

            else:
                logger.warning(f"Unknown message type: {message.type}")

        except Exception as e:
            logger.error(f"Error processing message from {client_id}: {e}")
            await self.send_to_client(
                client_id,
                {
                    "type": "error",
                    "message": "Failed to process message",
                    "error": str(e),
                },
            )

    async def _route_command(self, client_id: str, message: MessageProtocol):
        """Route command to appropriate handler"""
        # This will be implemented to route commands to StillMe Core
        # For now, just acknowledge receipt
        await self.send_to_client(
            client_id,
            {
                "type": "command_received",
                "command_id": message.id,
                "status": "processing",
            },
        )

    async def _handle_notification(self, client_id: str, message: MessageProtocol):
        """Handle notification message"""
        # Broadcast notification to target clients or all clients
        if message.target:
            await self.send_to_client(message.target, message.to_dict())
        else:
            await self.broadcast_notification(message.to_dict())

    async def cleanup(self):
        """Cleanup all connections and tasks"""
        # Cancel all heartbeat tasks
        for task in self.heartbeat_tasks.values():
            task.cancel()

        # Close all connections
        for client_id in list(self.active_connections.keys()):
            await self.disconnect(client_id)

        logger.info("WebSocket manager cleanup complete")
