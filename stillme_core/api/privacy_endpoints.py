"""
Privacy API Endpoints for StillMe AI Framework
==============================================

Provides GDPR-compliant data export and deletion endpoints.
"""

import hashlib
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/privacy", tags=["privacy"])


class DataExportRequest(BaseModel):
    """Request model for data export"""
    user_id: str
    format: str = "json"  # json, csv, xml
    include_metadata: bool = True


class DataDeletionRequest(BaseModel):
    """Request model for data deletion"""
    user_id: str
    confirmation_token: str
    delete_all: bool = True


class ConsentRequest(BaseModel):
    """Request model for consent management"""
    user_id: str
    consent_type: str  # data_collection, analytics, marketing
    granted: bool
    timestamp: Optional[datetime] = None


class PrivacyManager:
    """Privacy manager for data export and deletion"""

    def __init__(self, data_dir: str = "data/privacy"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Privacy settings
        self.retention_days = int(os.getenv("STILLME_DATA_RETENTION_DAYS", "30"))
        self.export_formats = ["json", "csv", "xml"]

        # Audit log
        self.audit_log = self.data_dir / "audit.log"

    def export_user_data(self, user_id: str, format: str = "json", include_metadata: bool = True) -> dict[str, Any]:
        """Export all user data"""
        try:
            # Validate user ID
            if not self._validate_user_id(user_id):
                raise ValueError("Invalid user ID format")

            # Collect user data from various sources
            user_data = self._collect_user_data(user_id)

            # Add metadata if requested
            if include_metadata:
                user_data["metadata"] = {
                    "export_timestamp": datetime.now().isoformat(),
                    "export_format": format,
                    "data_retention_days": self.retention_days,
                    "user_id_hash": hashlib.sha256(user_id.encode()).hexdigest()[:16]
                }

            # Log export request
            self._log_audit_event("data_export", user_id, {"format": format, "include_metadata": include_metadata})

            return user_data

        except Exception as e:
            logger.error(f"Error exporting data for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Data export failed: {str(e)}")

    def delete_user_data(self, user_id: str, confirmation_token: str, delete_all: bool = True) -> dict[str, Any]:
        """Delete user data"""
        try:
            # Validate user ID
            if not self._validate_user_id(user_id):
                raise ValueError("Invalid user ID format")

            # Validate confirmation token
            if not self._validate_confirmation_token(user_id, confirmation_token):
                raise ValueError("Invalid confirmation token")

            # Delete user data
            deleted_count = self._delete_user_data(user_id, delete_all)

            # Log deletion request
            self._log_audit_event("data_deletion", user_id, {
                "delete_all": delete_all,
                "deleted_count": deleted_count
            })

            return {
                "success": True,
                "user_id": user_id,
                "deleted_count": deleted_count,
                "deletion_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error deleting data for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Data deletion failed: {str(e)}")

    def update_consent(self, user_id: str, consent_type: str, granted: bool, timestamp: Optional[datetime] = None) -> dict[str, Any]:
        """Update user consent"""
        try:
            # Validate user ID
            if not self._validate_user_id(user_id):
                raise ValueError("Invalid user ID format")

            # Update consent
            consent_data = {
                "user_id": user_id,
                "consent_type": consent_type,
                "granted": granted,
                "timestamp": timestamp or datetime.now(),
                "updated_at": datetime.now()
            }

            # Store consent
            self._store_consent(consent_data)

            # Log consent update
            self._log_audit_event("consent_update", user_id, {
                "consent_type": consent_type,
                "granted": granted
            })

            return {
                "success": True,
                "user_id": user_id,
                "consent_type": consent_type,
                "granted": granted,
                "timestamp": consent_data["timestamp"].isoformat()
            }

        except Exception as e:
            logger.error(f"Error updating consent for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=f"Consent update failed: {str(e)}")

    def _validate_user_id(self, user_id: str) -> bool:
        """Validate user ID format"""
        if not user_id or len(user_id) < 3:
            return False

        # Basic validation - alphanumeric and common separators
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
        return all(c in allowed_chars for c in user_id)

    def _validate_confirmation_token(self, user_id: str, token: str) -> bool:
        """Validate confirmation token"""
        # In a real implementation, this would validate against a secure token
        # For now, we'll use a simple hash-based validation
        expected_token = hashlib.sha256(f"delete_{user_id}".encode()).hexdigest()[:16]
        return token == expected_token

    def _collect_user_data(self, user_id: str) -> dict[str, Any]:
        """Collect user data from various sources"""
        user_data = {
            "user_id": user_id,
            "collected_at": datetime.now().isoformat(),
            "data_sources": []
        }

        # Collect from different data sources
        data_sources = [
            ("conversation_history", self._get_conversation_history),
            ("preferences", self._get_user_preferences),
            ("analytics", self._get_analytics_data),
            ("audit_logs", self._get_audit_logs)
        ]

        for source_name, collector_func in data_sources:
            try:
                data = collector_func(user_id)
                if data:
                    user_data[source_name] = data
                    user_data["data_sources"].append(source_name)
            except Exception as e:
                logger.warning(f"Failed to collect {source_name} for user {user_id}: {e}")
                user_data[source_name] = None

        return user_data

    def _get_conversation_history(self, user_id: str) -> Optional[list[dict[str, Any]]]:
        """Get conversation history for user"""
        # Mock implementation - in real system, this would query the database
        return [
            {
                "timestamp": "2025-01-26T10:00:00Z",
                "message": "Hello, how can I help you?",
                "type": "assistant"
            },
            {
                "timestamp": "2025-01-26T10:01:00Z",
                "message": "I need help with my project",
                "type": "user"
            }
        ]

    def _get_user_preferences(self, user_id: str) -> Optional[dict[str, Any]]:
        """Get user preferences"""
        # Mock implementation
        return {
            "language": "en",
            "theme": "dark",
            "notifications": True,
            "privacy_mode": "balanced"
        }

    def _get_analytics_data(self, user_id: str) -> Optional[dict[str, Any]]:
        """Get analytics data for user"""
        # Mock implementation
        return {
            "total_interactions": 42,
            "last_active": "2025-01-26T10:00:00Z",
            "feature_usage": {
                "clarification": 15,
                "suggestions": 8,
                "multi_modal": 3
            }
        }

    def _get_audit_logs(self, user_id: str) -> Optional[list[dict[str, Any]]]:
        """Get audit logs for user"""
        # Mock implementation
        return [
            {
                "timestamp": "2025-01-26T09:00:00Z",
                "action": "login",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0..."
            }
        ]

    def _delete_user_data(self, user_id: str, delete_all: bool) -> int:
        """Delete user data"""
        deleted_count = 0

        # Delete from different data sources
        deletion_sources = [
            ("conversation_history", self._delete_conversation_history),
            ("preferences", self._delete_user_preferences),
            ("analytics", self._delete_analytics_data),
            ("audit_logs", self._delete_audit_logs)
        ]

        for source_name, deleter_func in deletion_sources:
            try:
                count = deleter_func(user_id, delete_all)
                deleted_count += count
                logger.info(f"Deleted {count} records from {source_name} for user {user_id}")
            except Exception as e:
                logger.warning(f"Failed to delete {source_name} for user {user_id}: {e}")

        return deleted_count

    def _delete_conversation_history(self, user_id: str, delete_all: bool) -> int:
        """Delete conversation history"""
        # Mock implementation - return count of deleted records
        return 42

    def _delete_user_preferences(self, user_id: str, delete_all: bool) -> int:
        """Delete user preferences"""
        # Mock implementation
        return 1

    def _delete_analytics_data(self, user_id: str, delete_all: bool) -> int:
        """Delete analytics data"""
        # Mock implementation
        return 5

    def _delete_audit_logs(self, user_id: str, delete_all: bool) -> int:
        """Delete audit logs"""
        # Mock implementation
        return 10

    def _store_consent(self, consent_data: dict[str, Any]):
        """Store consent data"""
        consent_file = self.data_dir / f"consent_{consent_data['user_id']}.json"
        try:
            with open(consent_file, 'w') as f:
                json.dump(consent_data, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error storing consent: {e}")
            raise

    def _log_audit_event(self, event_type: str, user_id: str, details: dict[str, Any]):
        """Log audit event"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details
        }

        try:
            with open(self.audit_log, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
        except Exception as e:
            logger.error(f"Error writing audit log: {e}")


# Initialize privacy manager
privacy_manager = PrivacyManager()


@router.post("/export")
async def export_user_data(request: DataExportRequest):
    """Export user data in specified format"""
    try:
        user_data = privacy_manager.export_user_data(
            user_id=request.user_id,
            format=request.format,
            include_metadata=request.include_metadata
        )

        return JSONResponse(content={
            "success": True,
            "data": user_data,
            "format": request.format,
            "exported_at": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Export endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete")
async def delete_user_data(request: DataDeletionRequest):
    """Delete user data"""
    try:
        result = privacy_manager.delete_user_data(
            user_id=request.user_id,
            confirmation_token=request.confirmation_token,
            delete_all=request.delete_all
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Delete endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consent")
async def update_consent(request: ConsentRequest):
    """Update user consent"""
    try:
        result = privacy_manager.update_consent(
            user_id=request.user_id,
            consent_type=request.consent_type,
            granted=request.granted,
            timestamp=request.timestamp
        )

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Consent endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{user_id}")
async def get_privacy_status(user_id: str):
    """Get privacy status for user"""
    try:
        # Get consent status
        consent_file = privacy_manager.data_dir / f"consent_{user_id}.json"
        consent_status = {}

        if consent_file.exists():
            with open(consent_file) as f:
                consent_status = json.load(f)

        return JSONResponse(content={
            "user_id": user_id,
            "consent_status": consent_status,
            "data_retention_days": privacy_manager.retention_days,
            "last_updated": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Privacy status endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def privacy_health_check():
    """Health check for privacy endpoints"""
    return JSONResponse(content={
        "status": "healthy",
        "service": "privacy-api",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })
