# StillMe Gateway - Message Routes
"""
Message handling endpoints
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from core.auth import get_current_user
from core.message_protocol import MessageProtocol, MessageType
from services.stillme_integration import StillMeIntegration

logger = logging.getLogger(__name__)

router = APIRouter()
stillme_integration = StillMeIntegration()


class MessageRequest(BaseModel):
    type: str
    content: Dict[str, Any]
    target: Optional[str] = None
    priority: str = "normal"


class MessageResponse(BaseModel):
    id: str
    type: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/send", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> MessageResponse:
    """Send a message to StillMe Core"""
    try:
        # Create message protocol
        message = MessageProtocol(
            id=f"msg_{int(__import__('time').time() * 1000)}",
            type=MessageType(request.type),
            content=request.content,
            source=current_user["user_id"],
            target=request.target,
            priority=request.priority
        )
        
        # Process command if it's a command message
        if message.type == MessageType.COMMAND:
            result = await stillme_integration.process_command(message)
            
            return MessageResponse(
                id=result["id"],
                type=result["type"],
                success=result["success"],
                result=result.get("result"),
                error=result.get("error")
            )
        else:
            # For non-command messages, just acknowledge
            return MessageResponse(
                id=message.id,
                type=message.type,
                success=True,
                result={"message": "Message received"}
            )
            
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


@router.get("/history")
async def get_message_history(
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get message history for current user"""
    try:
        # TODO: Implement message history retrieval from database
        return {
            "messages": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting message history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get message history"
        )


@router.delete("/history")
async def clear_message_history(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """Clear message history for current user"""
    try:
        # TODO: Implement message history clearing
        return {"message": "Message history cleared"}
        
    except Exception as e:
        logger.error(f"Error clearing message history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear message history"
        )
