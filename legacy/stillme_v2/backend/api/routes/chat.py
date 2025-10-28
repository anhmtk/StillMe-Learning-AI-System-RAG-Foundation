"""
Chat API routes for StillMe V2
Handles chat interactions with the AI
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging
import time
from datetime import datetime

from ...database.schema import get_db_session, ChatSession, ChatMessage
from ..models.chat import ChatRequest, ChatResponse, ChatSessionResponse
from ...services.ai_service import AIService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize AI service
ai_service = AIService()

@router.post("/send", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db_session)
):
    """
    Send a message to the AI and get a response
    """
    try:
        logger.info(f"Processing chat message: {request.message[:50]}...")
        
        # Get or create chat session
        if request.session_id:
            session = db.query(ChatSession).filter(
                ChatSession.session_id == request.session_id
            ).first()
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
        else:
            # Create new session
            session = ChatSession(
                session_id=f"session_{int(time.time())}",
                created_at=datetime.now()
            )
            db.add(session)
            db.commit()
        
        # Save user message
        user_message = ChatMessage(
            message_id=f"msg_{int(time.time())}_{hash(request.message) % 10000}",
            session_id=session.session_id,
            role="user",
            content=request.message,
            created_at=datetime.now()
        )
        db.add(user_message)
        
        # Get AI response
        ai_result = await ai_service.generate_response(
            message=request.message,
            context=request.context
        )
        
        ai_response = ai_result["response"]
        model = ai_result["model"]
        latency_ms = ai_result["latency_ms"]
        tokens_used = ai_result["tokens_used"]
        
        # Save AI response
        ai_message = ChatMessage(
            message_id=f"msg_{int(time.time())}_{hash(ai_response) % 10000}",
            session_id=session.session_id,
            role="assistant",
            content=ai_response,
            created_at=datetime.now()
        )
        return ChatResponse(
            response=ai_response,
            session_id=session.session_id,
            timestamp=datetime.now(),
            model=model,
            latency_ms=latency_ms,
            tokens_used=tokens_used
        )
        return ChatResponse(
            response=ai_response,
            session_id=session.session_id,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    db: Session = Depends(get_db_session)
):
    """
    Get all chat sessions
    """
    try:
        sessions = db.query(ChatSession).order_by(ChatSession.created_at.desc()).all()
        
        return [
            ChatSessionResponse(
                session_id=session.session_id,
                created_at=session.created_at,
                message_count=session.message_count
            )
            for session in sessions
        ]
        
    except Exception as e:
        logger.error(f"Get sessions error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Get sessions error: {str(e)}")

@router.get("/history/{session_id}")
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db_session)
):
    """
    Get chat history for a specific session
    """
    try:
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        return [
            {
                "role": message.role,
                "content": message.content,
                "timestamp": message.created_at
            }
            for message in messages
        ]
        
    except Exception as e:
        logger.error(f"Get history error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Get history error: {str(e)}")