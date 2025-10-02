"""Conversational Core V1 for StillMe Framework"""

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class ConversationType(Enum):
    CHAT = "chat"
    QUESTION = "question"
    COMMAND = "command"
    FEEDBACK = "feedback"

class ConversationStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

@dataclass
class Conversation:
    """Conversation record"""
    id: str
    type: ConversationType
    status: ConversationStatus
    messages: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class ConversationalCore:
    """Conversational core for StillMe framework"""

    def __init__(self):
        self.logger = logger
        self.conversations: List[Conversation] = []
        self.logger.info("✅ ConversationalCore initialized")

    def start_conversation(self,
                          conversation_type: ConversationType,
                          initial_message: str = "",
                          metadata: Dict[str, Any] = None) -> str:
        """Start a new conversation"""
        try:
            conversation_id = f"conv_{len(self.conversations) + 1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            messages = []
            if initial_message:
                messages.append({
                    "role": "user",
                    "content": initial_message,
                    "timestamp": datetime.now().isoformat()
                })

            conversation = Conversation(
                id=conversation_id,
                type=conversation_type,
                status=ConversationStatus.ACTIVE,
                messages=messages,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                metadata=metadata or {}
            )

            self.conversations.append(conversation)
            self.logger.info(f"💬 Conversation started: {conversation_type.value}")
            return conversation_id

        except Exception as e:
            self.logger.error(f"❌ Failed to start conversation: {e}")
            return ""

    def add_message(self,
                   conversation_id: str,
                   role: str,
                   content: str) -> bool:
        """Add message to conversation"""
        try:
            for conversation in self.conversations:
                if conversation.id == conversation_id:
                    message = {
                        "role": role,
                        "content": content,
                        "timestamp": datetime.now().isoformat()
                    }
                    conversation.messages.append(message)
                    conversation.updated_at = datetime.now()
                    self.logger.info(f"💬 Message added to conversation {conversation_id}")
                    return True
            return False

        except Exception as e:
            self.logger.error(f"❌ Failed to add message: {e}")
            return False

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID"""
        for conversation in self.conversations:
            if conversation.id == conversation_id:
                return conversation
        return None

    def update_conversation_status(self,
                                 conversation_id: str,
                                 status: ConversationStatus) -> bool:
        """Update conversation status"""
        for conversation in self.conversations:
            if conversation.id == conversation_id:
                conversation.status = status
                conversation.updated_at = datetime.now()
                self.logger.info(f"🔄 Conversation {conversation_id} status updated to {status.value}")
                return True
        return False

    def get_conversations_by_type(self, conversation_type: ConversationType) -> List[Conversation]:
        """Get conversations by type"""
        return [c for c in self.conversations if c.type == conversation_type]

    def get_conversations_by_status(self, status: ConversationStatus) -> List[Conversation]:
        """Get conversations by status"""
        return [c for c in self.conversations if c.status == status]

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get conversation summary"""
        try:
            total_conversations = len(self.conversations)
            conversations_by_type = {}
            conversations_by_status = {}

            for conversation in self.conversations:
                # Count by type
                type_key = conversation.type.value
                conversations_by_type[type_key] = conversations_by_type.get(type_key, 0) + 1

                # Count by status
                status_key = conversation.status.value
                conversations_by_status[status_key] = conversations_by_status.get(status_key, 0) + 1

            return {
                "total_conversations": total_conversations,
                "conversations_by_type": conversations_by_type,
                "conversations_by_status": conversations_by_status,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"❌ Failed to get conversation summary: {e}")
            return {"error": str(e)}

    def clear_conversations(self):
        """Clear all conversations"""
        self.conversations.clear()
        self.logger.info("🧹 All conversations cleared")
