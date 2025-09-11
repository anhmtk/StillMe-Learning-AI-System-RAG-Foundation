# StillMe Gateway - Message Protocol
"""
Message protocol for StillMe multi-platform communication
"""

import json
import time
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Message types"""
    COMMAND = "command"
    RESPONSE = "response"
    STATUS = "status"
    NOTIFICATION = "notification"
    SYNC = "sync"
    HEARTBEAT = "heartbeat"
    ERROR = "error"


class MessagePriority(str, Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MessageStatus(str, Enum):
    """Message status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessageProtocol(BaseModel):
    """Message protocol for StillMe communication"""
    
    # Core fields
    id: str = Field(..., description="Unique message ID")
    type: MessageType = Field(..., description="Message type")
    timestamp: float = Field(default_factory=time.time, description="Message timestamp")
    
    # Content
    content: Dict[str, Any] = Field(..., description="Message content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    # Routing
    source: str = Field(..., description="Source client/device ID")
    target: Optional[str] = Field(default=None, description="Target client/device ID")
    broadcast: bool = Field(default=False, description="Broadcast to all clients")
    
    # Priority and status
    priority: MessagePriority = Field(default=MessagePriority.NORMAL, description="Message priority")
    status: MessageStatus = Field(default=MessageStatus.PENDING, description="Message status")
    
    # Security
    signature: Optional[str] = Field(default=None, description="Message signature")
    encrypted: bool = Field(default=False, description="Is message encrypted")
    
    # Response handling
    response_to: Optional[str] = Field(default=None, description="ID of message this responds to")
    requires_response: bool = Field(default=False, description="Requires response")
    response_timeout: Optional[int] = Field(default=None, description="Response timeout in seconds")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def parse(cls, data: Union[str, Dict[str, Any]]) -> "MessageProtocol":
        """Parse message from JSON string or dict"""
        if isinstance(data, str):
            data = json.loads(data)
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.dict()
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return self.json()
    
    def is_expired(self, timeout: Optional[int] = None) -> bool:
        """Check if message is expired"""
        if timeout is None:
            timeout = self.response_timeout
        if timeout is None:
            return False
        return time.time() - self.timestamp > timeout
    
    def mark_processing(self):
        """Mark message as processing"""
        self.status = MessageStatus.PROCESSING
    
    def mark_completed(self):
        """Mark message as completed"""
        self.status = MessageStatus.COMPLETED
    
    def mark_failed(self):
        """Mark message as failed"""
        self.status = MessageStatus.FAILED


class CommandMessage(MessageProtocol):
    """Command message for StillMe Core"""
    
    type: MessageType = MessageType.COMMAND
    
    # Command specific fields
    command: str = Field(..., description="Command to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    context: Dict[str, Any] = Field(default_factory=dict, description="Command context")
    
    # Execution
    async_execution: bool = Field(default=True, description="Execute asynchronously")
    timeout: int = Field(default=300, description="Command timeout in seconds")
    
    # Results
    result_location: Optional[str] = Field(default=None, description="Result file location")
    result_type: Optional[str] = Field(default=None, description="Result type")


class ResponseMessage(MessageProtocol):
    """Response message from StillMe Core"""
    
    type: MessageType = MessageType.RESPONSE
    
    # Response specific fields
    success: bool = Field(..., description="Command success status")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Command result")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    
    # Execution info
    execution_time: Optional[float] = Field(default=None, description="Execution time in seconds")
    memory_usage: Optional[int] = Field(default=None, description="Memory usage in bytes")
    
    # Files
    files: Optional[Dict[str, str]] = Field(default=None, description="Generated files")


class StatusMessage(MessageProtocol):
    """Status update message"""
    
    type: MessageType = MessageType.STATUS
    
    # Status specific fields
    component: str = Field(..., description="Component name")
    status: str = Field(..., description="Status value")
    progress: Optional[float] = Field(default=None, description="Progress percentage (0-100)")
    message: Optional[str] = Field(default=None, description="Status message")
    
    # Metrics
    metrics: Optional[Dict[str, Any]] = Field(default=None, description="Component metrics")


class NotificationMessage(MessageProtocol):
    """Notification message"""
    
    type: MessageType = MessageType.NOTIFICATION
    
    # Notification specific fields
    title: str = Field(..., description="Notification title")
    body: str = Field(..., description="Notification body")
    category: str = Field(default="general", description="Notification category")
    
    # Actions
    actions: Optional[Dict[str, str]] = Field(default=None, description="Available actions")
    action_url: Optional[str] = Field(default=None, description="Action URL")
    
    # Display
    icon: Optional[str] = Field(default=None, description="Notification icon")
    sound: Optional[str] = Field(default=None, description="Notification sound")
    badge: Optional[int] = Field(default=None, description="Badge count")


class HeartbeatMessage(MessageProtocol):
    """Heartbeat message"""
    
    type: MessageType = MessageType.HEARTBEAT
    
    # Heartbeat specific fields
    client_info: Dict[str, Any] = Field(default_factory=dict, description="Client information")
    system_info: Dict[str, Any] = Field(default_factory=dict, description="System information")
    
    # Health
    health_status: str = Field(default="healthy", description="Health status")
    last_activity: Optional[float] = Field(default=None, description="Last activity timestamp")


# Message factory functions
def create_command(
    command: str,
    source: str,
    parameters: Optional[Dict[str, Any]] = None,
    target: Optional[str] = None,
    **kwargs
) -> CommandMessage:
    """Create a command message"""
    return CommandMessage(
        id=f"cmd_{int(time.time() * 1000)}",
        command=command,
        source=source,
        target=target,
        parameters=parameters or {},
        content={"command": command, "parameters": parameters or {}},
        **kwargs
    )


def create_response(
    response_to: str,
    source: str,
    success: bool,
    result: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    **kwargs
) -> ResponseMessage:
    """Create a response message"""
    return ResponseMessage(
        id=f"resp_{int(time.time() * 1000)}",
        response_to=response_to,
        source=source,
        success=success,
        result=result,
        error=error,
        content={"success": success, "result": result, "error": error},
        **kwargs
    )


def create_status(
    component: str,
    status: str,
    source: str,
    progress: Optional[float] = None,
    message: Optional[str] = None,
    **kwargs
) -> StatusMessage:
    """Create a status message"""
    return StatusMessage(
        id=f"status_{int(time.time() * 1000)}",
        component=component,
        status=status,
        source=source,
        progress=progress,
        message=message,
        content={"component": component, "status": status, "progress": progress, "message": message},
        **kwargs
    )


def create_notification(
    title: str,
    body: str,
    source: str,
    target: Optional[str] = None,
    **kwargs
) -> NotificationMessage:
    """Create a notification message"""
    return NotificationMessage(
        id=f"notif_{int(time.time() * 1000)}",
        title=title,
        body=body,
        source=source,
        target=target,
        content={"title": title, "body": body},
        **kwargs
    )


def create_heartbeat(
    source: str,
    client_info: Optional[Dict[str, Any]] = None,
    **kwargs
) -> HeartbeatMessage:
    """Create a heartbeat message"""
    return HeartbeatMessage(
        id=f"hb_{int(time.time() * 1000)}",
        source=source,
        client_info=client_info or {},
        content={"heartbeat": True},
        **kwargs
    )

