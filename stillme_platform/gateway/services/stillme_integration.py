# StillMe Gateway - StillMe Core Integration Service
"""
Integration service for communicating with StillMe Core
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp

from core.config import Settings

from ..core.message_protocol import MessageProtocol, MessageType

logger = logging.getLogger(__name__)


class StillMeIntegration:
    """Integration service for StillMe Core communication"""

    def __init__(self):
        self.settings = Settings()
        self.session: Optional[aiohttp.ClientSession] = None
        self.is_initialized = False
        self.health_check_interval = 30  # seconds
        self.health_check_task: Optional[asyncio.Task] = None

    async def initialize(self):
        """Initialize the integration service"""
        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": f"StillMe-Gateway/{self.settings.VERSION}",
                },
            )

            # Add API key if available
            if self.settings.STILLME_API_KEY:
                self.session.headers["Authorization"] = (
                    f"Bearer {self.settings.STILLME_API_KEY}"
                )

            # Start health check task
            self.health_check_task = asyncio.create_task(self._health_check_loop())

            self.is_initialized = True
            logger.info("StillMe integration service initialized")

        except Exception as e:
            logger.error(f"Failed to initialize StillMe integration: {e}")
            raise

    async def cleanup(self):
        """Cleanup the integration service"""
        try:
            # Cancel health check task
            if self.health_check_task:
                self.health_check_task.cancel()
                try:
                    await self.health_check_task
                except asyncio.CancelledError:
                    pass

            # Close HTTP session
            if self.session:
                await self.session.close()

            self.is_initialized = False
            logger.info("StillMe integration service cleaned up")

        except Exception as e:
            logger.error(f"Error during StillMe integration cleanup: {e}")

    async def process_command(self, message: MessageProtocol) -> Dict[str, Any]:
        """Process a command message from client"""
        try:
            if not self.is_initialized or not self.session:
                return self._create_error_response(
                    message.id, "StillMe integration not initialized"
                )

            # Extract command information
            command = message.content.get("command", "")
            parameters = message.content.get("parameters", {})
            context = message.content.get("context", {})

            # Prepare request payload
            payload = {
                "command": command,
                "parameters": parameters,
                "context": {
                    **context,
                    "source": message.source,
                    "timestamp": message.timestamp,
                    "message_id": message.id,
                },
                "async_execution": message.content.get("async_execution", True),
                "timeout": message.content.get("timeout", 300),
            }

            # Send request to StillMe Core
            url = f"{self.settings.STILLME_CORE_URL}/api/execute"

            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return self._create_success_response(message.id, result)
                else:
                    error_text = await response.text()
                    return self._create_error_response(
                        message.id,
                        f"StillMe Core error: {response.status} - {error_text}",
                    )

        except asyncio.TimeoutError:
            return self._create_error_response(message.id, "Command execution timeout")
        except Exception as e:
            logger.error(f"Error processing command {message.id}: {e}")
            return self._create_error_response(
                message.id, f"Command processing error: {e!s}"
            )

    async def get_status(self) -> Dict[str, Any]:
        """Get StillMe Core status"""
        try:
            if not self.is_initialized or not self.session:
                return {"status": "disconnected", "error": "Not initialized"}

            url = f"{self.settings.STILLME_CORE_URL}/api/health"

            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "error", "error": f"HTTP {response.status}"}

        except Exception as e:
            logger.error(f"Error getting StillMe Core status: {e}")
            return {"status": "error", "error": str(e)}

    async def send_notification(self, notification: Dict[str, Any]) -> bool:
        """Send notification to StillMe Core"""
        try:
            if not self.is_initialized or not self.session:
                return False

            url = f"{self.settings.STILLME_CORE_URL}/api/notifications"

            async with self.session.post(url, json=notification) as response:
                return response.status == 200

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    async def upload_file(
        self, file_data: bytes, filename: str, content_type: str
    ) -> Optional[str]:
        """Upload file to StillMe Core"""
        try:
            if not self.is_initialized or not self.session:
                return None

            url = f"{self.settings.STILLME_CORE_URL}/api/upload"

            data = aiohttp.FormData()
            data.add_field(
                "file", file_data, filename=filename, content_type=content_type
            )

            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("file_id")
                else:
                    logger.error(f"File upload failed: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None

    async def download_file(self, file_id: str) -> Optional[bytes]:
        """Download file from StillMe Core"""
        try:
            if not self.is_initialized or not self.session:
                return None

            url = f"{self.settings.STILLME_CORE_URL}/api/download/{file_id}"

            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    logger.error(f"File download failed: {response.status}")
                    return None

        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return None

    async def _health_check_loop(self):
        """Background health check loop"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)

                status = await self.get_status()
                if status.get("status") != "healthy":
                    logger.warning(f"StillMe Core health check failed: {status}")
                else:
                    logger.debug("StillMe Core health check passed")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")

    def _create_success_response(
        self, message_id: str, result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create success response message"""
        return {
            "id": f"resp_{int(datetime.utcnow().timestamp() * 1000)}",
            "type": MessageType.RESPONSE,
            "timestamp": datetime.utcnow().timestamp(),
            "source": "stillme_gateway",
            "response_to": message_id,
            "success": True,
            "result": result,
            "content": {"success": True, "result": result},
        }

    def _create_error_response(self, message_id: str, error: str) -> Dict[str, Any]:
        """Create error response message"""
        return {
            "id": f"resp_{int(datetime.utcnow().timestamp() * 1000)}",
            "type": MessageType.RESPONSE,
            "timestamp": datetime.utcnow().timestamp(),
            "source": "stillme_gateway",
            "response_to": message_id,
            "success": False,
            "error": error,
            "content": {"success": False, "error": error},
        }

    # Getters
    def is_healthy(self) -> bool:
        """Check if StillMe Core is healthy"""
        return self.is_initialized and self.session is not None

    def get_core_url(self) -> str:
        """Get StillMe Core URL"""
        return self.settings.STILLME_CORE_URL
