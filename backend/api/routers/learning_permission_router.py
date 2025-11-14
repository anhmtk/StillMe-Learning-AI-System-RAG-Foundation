"""
Learning Permission Router
Handles user responses to learning permission requests
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter()


class PermissionResponse(BaseModel):
    """User response to learning permission request"""
    proposal_id: str = Field(..., description="ID of the learning proposal")
    user_response: str = Field(..., description="User response: 'yes', 'no', or edited content")
    user_id: Optional[str] = Field(None, description="User identifier")


@router.post("/permission/respond")
async def respond_to_learning_permission(request: Request, permission_response: PermissionResponse):
    """
    Handle user response to learning permission request
    
    User can:
    - Accept: "yes", "đồng ý", "ok", "agree"
    - Decline: "no", "không", "refuse"
    - Edit: Provide edited content
    """
    try:
        from backend.services.learning_proposal_storage import get_learning_proposal_storage
        from backend.services.conversation_learning_extractor import validate_learning_content
        from backend.api.main import rag_retrieval
        from backend.validators.ethics_adapter import EthicsAdapter
        
        storage = get_learning_proposal_storage()
        user_response_lower = permission_response.user_response.lower().strip()
        
        # Retrieve proposal from storage
        proposal = storage.get_proposal(permission_response.proposal_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Learning proposal not found or expired")
        
        # Check if user accepted
        accept_keywords = ["yes", "đồng ý", "ok", "agree", "chấp nhận", "được", "có"]
        decline_keywords = ["no", "không", "refuse", "từ chối", "không đồng ý"]
        
        is_accepted = any(keyword in user_response_lower for keyword in accept_keywords)
        is_declined = any(keyword in user_response_lower for keyword in decline_keywords)
        
        if is_declined:
            storage.update_proposal_status(
                proposal_id=permission_response.proposal_id,
                status="declined",
                user_response=permission_response.user_response
            )
            logger.info(f"User declined learning permission for proposal: {permission_response.proposal_id}")
            return {
                "status": "declined",
                "message": "Learning permission declined. Information will not be saved."
            }
        
        # Determine content to add (original or edited)
        content_to_add = proposal["knowledge_snippet"]
        if not is_accepted and len(permission_response.user_response) > 50:
            # User provided edited content
            content_to_add = permission_response.user_response
            storage.update_proposal_status(
                proposal_id=permission_response.proposal_id,
                status="edited",
                user_response=permission_response.user_response
            )
        elif is_accepted:
            storage.update_proposal_status(
                proposal_id=permission_response.proposal_id,
                status="accepted",
                user_response=permission_response.user_response
            )
        
        # Validate content before adding to RAG
        is_valid, validation_error = validate_learning_content(content_to_add)
        if not is_valid:
            logger.warning(f"Content validation failed: {validation_error}")
            return {
                "status": "validation_failed",
                "message": f"Content validation failed: {validation_error}",
                "error": validation_error
            }
        
        # Ethics validation
        if rag_retrieval:
            try:
                from backend.services.ethics_guard import check_content_ethics
                ethics_adapter = EthicsAdapter(guard_callable=check_content_ethics)  # Real ethics guard implementation
                from backend.validators.base import ValidationResult
                ethics_result = ethics_adapter.run(content_to_add, [])
                
                if not ethics_result.passed:
                    logger.warning(f"Ethics validation failed: {ethics_result.reasons}")
                    return {
                        "status": "ethics_failed",
                        "message": "Content failed ethics validation and cannot be added to knowledge base.",
                        "reasons": ethics_result.reasons
                    }
            except Exception as ethics_error:
                logger.warning(f"Ethics validation error: {ethics_error}")
                # Continue if ethics check fails (graceful degradation)
        
        # Add to RAG
        if rag_retrieval:
            try:
                success = rag_retrieval.add_learning_content(
                    content=content_to_add,
                    source=f"user_conversation:{permission_response.proposal_id}",
                    content_type="knowledge",
                    metadata={
                        "proposal_id": permission_response.proposal_id,
                        "user_id": permission_response.user_id or proposal.get("user_id"),
                        "original_proposal_score": proposal.get("knowledge_score", 0.0),
                        "added_at": datetime.now().isoformat(),
                        "was_edited": not is_accepted and len(permission_response.user_response) > 50
                    }
                )
                
                if success:
                    # Track learning success
                    storage.track_learning_success(
                        proposal_id=permission_response.proposal_id,
                        knowledge_snippet=content_to_add,
                        added_to_rag=True
                    )
                    
                    status_msg = "edited" if not is_accepted and len(permission_response.user_response) > 50 else "accepted"
                    logger.info(f"Successfully added learning content to RAG (proposal: {permission_response.proposal_id})")
                    return {
                        "status": status_msg,
                        "message": "Thank you! The information has been added to StillMe's knowledge base.",
                        "proposal_id": permission_response.proposal_id
                    }
                else:
                    logger.error(f"Failed to add content to RAG (proposal: {permission_response.proposal_id})")
                    return {
                        "status": "error",
                        "message": "Failed to add content to knowledge base. Please try again later."
                    }
            except Exception as rag_error:
                logger.error(f"RAG addition error: {rag_error}")
                return {
                    "status": "error",
                    "message": f"Error adding content to knowledge base: {str(rag_error)}"
                }
        
        return {
            "status": "unclear",
            "message": "Response unclear. Please reply 'yes' to accept, 'no' to decline, or provide edited content."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling permission response: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing permission response: {str(e)}")


@router.get("/permission/stats")
async def get_learning_stats():
    """Get learning statistics"""
    try:
        from backend.services.learning_proposal_storage import get_learning_proposal_storage
        storage = get_learning_proposal_storage()
        stats = storage.get_learning_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting learning stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving learning stats: {str(e)}")

