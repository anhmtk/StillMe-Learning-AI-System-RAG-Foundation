"""
Multi-user Session Management for AgentDev
SEAL-GRADE Session Security & Concurrency

Features:
- Secure session token generation and validation
- Session concurrency limits per user
- Automatic session cleanup and expiration
- Cross-device session management
- Session activity tracking and analytics
"""

import asyncio
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Set, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SessionStatus(Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"

class DeviceType(Enum):
    """Device type enumeration"""
    DESKTOP = "desktop"
    MOBILE = "mobile"
    WEB = "web"
    API = "api"

@dataclass
class SessionContext:
    """Session context information"""
    session_id: str
    user_id: str
    device_id: str
    device_type: DeviceType
    ip_address: str
    user_agent: str
    created_at: float
    last_activity: float
    expires_at: float
    status: SessionStatus
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class SessionActivity:
    """Session activity record"""
    activity_id: str
    session_id: str
    action: str
    resource_id: Optional[str]
    timestamp: float
    duration_ms: Optional[float]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class UserSessionLimits:
    """User session limits configuration"""
    max_concurrent_sessions: int = 5
    max_sessions_per_device: int = 2
    session_timeout_hours: int = 24
    idle_timeout_hours: int = 2
    allow_multiple_devices: bool = True

class SessionManager:
    """SEAL-GRADE Multi-user Session Manager"""
    
    def __init__(self, rbac_manager=None, max_sessions_per_user: int = 5):
        self.rbac_manager = rbac_manager
        self.max_sessions_per_user = max_sessions_per_user
        self._active_sessions: Dict[str, SessionContext] = {}
        self._user_sessions: Dict[str, Set[str]] = {}  # user_id -> set of session_ids
        self._device_sessions: Dict[str, Set[str]] = {}  # device_id -> set of session_ids
        self._session_activities: Dict[str, List[SessionActivity]] = {}
        self._lock = asyncio.Lock()
        self._session_limits: Dict[str, UserSessionLimits] = {}
        
    async def create_session(self, user_id: str, device_id: str, device_type: DeviceType,
                           ip_address: str, user_agent: str, 
                           session_duration_hours: int = 24) -> SessionContext:
        """Create new user session with concurrency limits"""
        async with self._lock:
            # Check session limits
            await self._enforce_session_limits(user_id, device_id)
            
            # Generate secure session token
            session_token = self._generate_session_token(user_id, device_id)
            
            now = time.time()
            session_id = str(uuid.uuid4())
            
            session = SessionContext(
                session_id=session_id,
                user_id=user_id,
                device_id=device_id,
                device_type=device_type,
                ip_address=ip_address,
                user_agent=user_agent,
                created_at=now,
                last_activity=now,
                expires_at=now + (session_duration_hours * 3600),
                status=SessionStatus.ACTIVE,
                metadata={"token": session_token}
            )
            
            # Store session
            self._active_sessions[session_id] = session
            
            # Update user sessions
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = set()
            self._user_sessions[user_id].add(session_id)
            
            # Update device sessions
            if device_id not in self._device_sessions:
                self._device_sessions[device_id] = set()
            self._device_sessions[device_id].add(session_id)
            
            # Initialize activity tracking
            self._session_activities[session_id] = []
            
            logger.info(f"Session created: {session_id} for user {user_id} on {device_type.value}")
            
            return session
    
    async def validate_session(self, session_token: str, ip_address: str = None) -> Optional[SessionContext]:
        """Validate session token and update activity"""
        async with self._lock:
            # Find session by token
            session = None
            for s in self._active_sessions.values():
                if s.metadata.get("token") == session_token:
                    session = s
                    break
            
            if not session:
                return None
            
            # Check if session is expired
            if session.expires_at <= time.time():
                await self._expire_session(session.session_id)
                return None
            
            # Check if session is revoked
            if session.status != SessionStatus.ACTIVE:
                return None
            
            # Update last activity
            session.last_activity = time.time()
            
            # Log activity
            await self._log_session_activity(
                session.session_id, "session_validation", 
                metadata={"ip_address": ip_address}
            )
            
            return session
    
    async def revoke_session(self, session_id: str, reason: str = "manual_revoke"):
        """Revoke specific session"""
        async with self._lock:
            if session_id in self._active_sessions:
                session = self._active_sessions[session_id]
                session.status = SessionStatus.REVOKED
                
                # Remove from user and device tracking
                if session.user_id in self._user_sessions:
                    self._user_sessions[session.user_id].discard(session_id)
                if session.device_id in self._device_sessions:
                    self._device_sessions[session.device_id].discard(session_id)
                
                logger.info(f"Session revoked: {session_id} ({reason})")
    
    async def revoke_user_sessions(self, user_id: str, reason: str = "user_logout"):
        """Revoke all sessions for a user"""
        async with self._lock:
            if user_id in self._user_sessions:
                session_ids = list(self._user_sessions[user_id])
                for session_id in session_ids:
                    if session_id in self._active_sessions:
                        session = self._active_sessions[session_id]
                        session.status = SessionStatus.REVOKED
                        
                        # Remove from user and device tracking
                        if session.user_id in self._user_sessions:
                            self._user_sessions[session.user_id].discard(session_id)
                        if session.device_id in self._device_sessions:
                            self._device_sessions[session.device_id].discard(session_id)
                        
                        logger.info(f"Session revoked: {session_id} ({reason})")
    
    async def revoke_device_sessions(self, device_id: str, reason: str = "device_logout"):
        """Revoke all sessions for a device"""
        async with self._lock:
            if device_id in self._device_sessions:
                session_ids = list(self._device_sessions[device_id])
                for session_id in session_ids:
                    if session_id in self._active_sessions:
                        session = self._active_sessions[session_id]
                        session.status = SessionStatus.REVOKED
                        
                        # Remove from user and device tracking
                        if session.user_id in self._user_sessions:
                            self._user_sessions[session.user_id].discard(session_id)
                        if session.device_id in self._device_sessions:
                            self._device_sessions[session.device_id].discard(session_id)
                        
                        logger.info(f"Session revoked: {session_id} ({reason})")
    
    async def _enforce_session_limits(self, user_id: str, device_id: str):
        """Enforce session limits for user and device"""
        # Get user limits (use constructor default if not set)
        limits = self._session_limits.get(user_id, UserSessionLimits())
        
        # Use constructor max_sessions_per_user if no custom limits set
        max_user_sessions = limits.max_concurrent_sessions if limits.max_concurrent_sessions != 5 else self.max_sessions_per_user
        
        # Check user session limit
        user_sessions = self._user_sessions.get(user_id, set())
        if len(user_sessions) >= max_user_sessions:
            # Revoke oldest session
            if user_sessions:
                oldest_session_id = min(
                    user_sessions,
                    key=lambda sid: self._active_sessions[sid].created_at
                )
                # Inline revocation to avoid deadlock
                if oldest_session_id in self._active_sessions:
                    session = self._active_sessions[oldest_session_id]
                    session.status = SessionStatus.REVOKED
                    
                    # Remove from user and device tracking
                    if session.user_id in self._user_sessions:
                        self._user_sessions[session.user_id].discard(oldest_session_id)
                    if session.device_id in self._device_sessions:
                        self._device_sessions[session.device_id].discard(oldest_session_id)
                    
                    logger.info(f"Session revoked: {oldest_session_id} (session_limit_exceeded)")
        
        # Check device session limit
        device_sessions = self._device_sessions.get(device_id, set())
        if len(device_sessions) >= limits.max_sessions_per_device:
            # Revoke oldest session for this device
            if device_sessions:
                oldest_session_id = min(
                    device_sessions,
                    key=lambda sid: self._active_sessions[sid].created_at
                )
                # Inline revocation to avoid deadlock
                if oldest_session_id in self._active_sessions:
                    session = self._active_sessions[oldest_session_id]
                    session.status = SessionStatus.REVOKED
                    
                    # Remove from user and device tracking
                    if session.user_id in self._user_sessions:
                        self._user_sessions[session.user_id].discard(oldest_session_id)
                    if session.device_id in self._device_sessions:
                        self._device_sessions[session.device_id].discard(oldest_session_id)
                    
                    logger.info(f"Session revoked: {oldest_session_id} (device_session_limit_exceeded)")
    
    async def _expire_session(self, session_id: str):
        """Mark session as expired"""
        if session_id in self._active_sessions:
            session = self._active_sessions[session_id]
            session.status = SessionStatus.EXPIRED
            
            # Remove from tracking
            if session.user_id in self._user_sessions:
                self._user_sessions[session.user_id].discard(session_id)
            if session.device_id in self._device_sessions:
                self._device_sessions[session.device_id].discard(session_id)
            
            logger.debug(f"Session expired: {session_id}")
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = time.time()
        expired_sessions = []
        
        async with self._lock:
            for session_id, session in self._active_sessions.items():
                if session.expires_at <= now:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                await self._expire_session(session_id)
    
    async def cleanup_idle_sessions(self):
        """Clean up idle sessions based on user limits"""
        now = time.time()
        idle_sessions = []
        
        async with self._lock:
            for session_id, session in self._active_sessions.items():
                if session.status == SessionStatus.ACTIVE:
                    limits = self._session_limits.get(session.user_id, UserSessionLimits())
                    idle_timeout = limits.idle_timeout_hours * 3600
                    
                    if now - session.last_activity > idle_timeout:
                        idle_sessions.append(session_id)
            
            for session_id in idle_sessions:
                await self._expire_session(session_id)
                logger.info(f"Idle session expired: {session_id}")
    
    async def _log_session_activity(self, session_id: str, action: str, 
                                  resource_id: str = None, duration_ms: float = None,
                                  metadata: Dict[str, Any] = None):
        """Log session activity"""
        activity = SessionActivity(
            activity_id=str(uuid.uuid4()),
            session_id=session_id,
            action=action,
            resource_id=resource_id,
            timestamp=time.time(),
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        
        if session_id in self._session_activities:
            self._session_activities[session_id].append(activity)
            
            # Keep only last 100 activities per session
            if len(self._session_activities[session_id]) > 100:
                self._session_activities[session_id] = self._session_activities[session_id][-100:]
    
    async def get_user_sessions(self, user_id: str) -> List[SessionContext]:
        """Get all active sessions for a user"""
        async with self._lock:
            sessions = []
            if user_id in self._user_sessions:
                for session_id in self._user_sessions[user_id]:
                    if session_id in self._active_sessions:
                        session = self._active_sessions[session_id]
                        if session.status == SessionStatus.ACTIVE:
                            sessions.append(session)
            return sessions
    
    async def get_session_activities(self, session_id: str, limit: int = 50) -> List[SessionActivity]:
        """Get session activities"""
        async with self._lock:
            activities = self._session_activities.get(session_id, [])
            return activities[-limit:] if limit else activities
    
    async def set_user_session_limits(self, user_id: str, limits: UserSessionLimits):
        """Set session limits for a user"""
        async with self._lock:
            self._session_limits[user_id] = limits
    
    async def get_session_metrics(self) -> Dict[str, Any]:
        """Get session management metrics"""
        async with self._lock:
            now = time.time()
            
            # Count sessions by status
            status_counts = {}
            for session in self._active_sessions.values():
                status = session.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count sessions by device type
            device_counts = {}
            for session in self._active_sessions.values():
                if session.status == SessionStatus.ACTIVE:
                    device_type = session.device_type.value
                    device_counts[device_type] = device_counts.get(device_type, 0) + 1
            
            # Count active users
            active_users = len(self._user_sessions)
            
            # Count total activities
            total_activities = sum(len(activities) for activities in self._session_activities.values())
            
            return {
                "total_sessions": len(self._active_sessions),
                "active_sessions": status_counts.get("active", 0),
                "expired_sessions": status_counts.get("expired", 0),
                "revoked_sessions": status_counts.get("revoked", 0),
                "active_users": active_users,
                "sessions_by_device": device_counts,
                "total_activities": total_activities,
                "sessions_with_limits": len(self._session_limits)
            }
    
    def _generate_session_token(self, user_id: str, device_id: str) -> str:
        """Generate secure session token"""
        data = f"{user_id}:{device_id}:{time.time()}:{uuid.uuid4()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def export_session_data(self, user_id: str) -> Dict[str, Any]:
        """Export session data for user (GDPR compliance)"""
        async with self._lock:
            sessions = await self.get_user_sessions(user_id)
            activities = []
            
            for session in sessions:
                session_activities = await self.get_session_activities(session.session_id)
                activities.extend(session_activities)
            
            return {
                "user_id": user_id,
                "sessions": [asdict(session) for session in sessions],
                "activities": [asdict(activity) for activity in activities],
                "exported_at": time.time()
            }
    
    async def delete_user_data(self, user_id: str):
        """Delete all session data for user (GDPR compliance)"""
        async with self._lock:
            # Revoke all user sessions
            await self.revoke_user_sessions(user_id, "data_deletion")
            
            # Remove from limits
            if user_id in self._session_limits:
                del self._session_limits[user_id]
            
            # Clean up activities
            for session_id in list(self._session_activities.keys()):
                if session_id in self._active_sessions:
                    session = self._active_sessions[session_id]
                    if session.user_id == user_id:
                        del self._session_activities[session_id]
            
            logger.info(f"User data deleted: {user_id}")
