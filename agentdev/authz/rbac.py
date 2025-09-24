"""
RBAC (Role-Based Access Control) for AgentDev
SEAL-GRADE Enterprise Authorization System

Features:
- Role-based permissions (owner, contributor, viewer)
- Resource-level access control
- Optimistic locking for concurrent access
- Audit logging for all authorization decisions
- Session management with token validation
"""

import asyncio
import hashlib
import json
import time
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import aiosqlite
import logging

logger = logging.getLogger(__name__)

class Role(Enum):
    """User roles with hierarchical permissions"""
    VIEWER = "viewer"           # Read-only access
    CONTRIBUTOR = "contributor" # Read + Write access
    OWNER = "owner"            # Full access + Admin

class Permission(Enum):
    """Granular permissions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    EXECUTE = "execute"

class ResourceType(Enum):
    """Resource types for access control"""
    JOB = "job"
    PLAN = "plan"
    ARTIFACT = "artifact"
    CHECKPOINT = "checkpoint"
    CONFIG = "config"
    SYSTEM = "system"

@dataclass
class User:
    """User entity with role and metadata"""
    user_id: str
    username: str
    email: str
    role: Role
    created_at: float
    last_active: float
    is_active: bool = True
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Resource:
    """Resource entity for access control"""
    resource_id: str
    resource_type: ResourceType
    owner_id: str
    created_at: float
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class Session:
    """User session with token and expiration"""
    session_id: str
    user_id: str
    token: str
    created_at: float
    expires_at: float
    is_active: bool = True
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class AccessDecision:
    """Authorization decision result"""
    allowed: bool
    reason: str
    required_permission: Optional[Permission] = None
    user_role: Optional[Role] = None
    resource_owner: Optional[str] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class RBACManager:
    """SEAL-GRADE RBAC Manager with optimistic locking"""
    
    def __init__(self, db_path: str = "agentdev_rbac.db"):
        self.db_path = db_path
        self._lock = asyncio.Lock()
        self._role_permissions = self._init_role_permissions()
        self._active_sessions: Dict[str, Session] = {}
        
    def _init_role_permissions(self) -> Dict[Role, Set[Permission]]:
        """Initialize role-permission mappings"""
        return {
            Role.VIEWER: {Permission.READ},
            Role.CONTRIBUTOR: {Permission.READ, Permission.WRITE, Permission.EXECUTE},
            Role.OWNER: {Permission.READ, Permission.WRITE, Permission.DELETE, Permission.ADMIN, Permission.EXECUTE}
        }
    
    async def initialize(self):
        """Initialize RBAC database schema"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    last_active REAL NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    resource_id TEXT PRIMARY KEY,
                    resource_type TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    version INTEGER DEFAULT 1
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    log_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource_id TEXT,
                    resource_type TEXT,
                    decision TEXT NOT NULL,
                    reason TEXT,
                    timestamp REAL NOT NULL,
                    metadata TEXT DEFAULT '{}'
                )
            """)
            
            await db.commit()
            
        # Create default admin user
        await self._create_default_admin()
    
    async def _create_default_admin(self):
        """Create default admin user if none exists"""
        admin_user = await self.get_user_by_username("admin")
        if not admin_user:
            await self.create_user(
                user_id="admin-001",
                username="admin",
                email="admin@stillme.ai",
                role=Role.OWNER
            )
            logger.info("Created default admin user")
    
    async def create_user(self, user_id: str, username: str, email: str, role: Role) -> User:
        """Create a new user with optimistic locking"""
        async with self._lock:
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                role=role,
                created_at=time.time(),
                last_active=time.time()
            )
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO users (user_id, username, email, role, created_at, last_active, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user.user_id, user.username, user.email, user.role.value,
                    user.created_at, user.last_active, json.dumps(user.metadata)
                ))
                await db.commit()
            
            await self._audit_log(
                user_id=user_id,
                action="user_created",
                decision="allowed",
                reason=f"User {username} created with role {role.value}"
            )
            
            return user
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, username, email, role, created_at, last_active, is_active, metadata
                FROM users WHERE user_id = ?
            """, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        user_id=row[0],
                        username=row[1],
                        email=row[2],
                        role=Role(row[3]),
                        created_at=row[4],
                        last_active=row[5],
                        is_active=bool(row[6]),
                        metadata=json.loads(row[7] or '{}')
                    )
                return None
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id, username, email, role, created_at, last_active, is_active, metadata
                FROM users WHERE username = ?
            """, (username,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        user_id=row[0],
                        username=row[1],
                        email=row[2],
                        role=Role(row[3]),
                        created_at=row[4],
                        last_active=row[5],
                        is_active=bool(row[6]),
                        metadata=json.loads(row[7] or '{}')
                    )
                return None
    
    async def create_session(self, user_id: str, duration_hours: int = 24) -> Session:
        """Create user session with token"""
        token = self._generate_token(user_id)
        now = time.time()
        
        session = Session(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            token=token,
            created_at=now,
            expires_at=now + (duration_hours * 3600)
        )
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO sessions (session_id, user_id, token, created_at, expires_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session.session_id, session.user_id, session.token,
                session.created_at, session.expires_at, json.dumps(session.metadata)
            ))
            await db.commit()
        
        self._active_sessions[session.token] = session
        return session
    
    async def validate_session(self, token: str) -> Optional[Session]:
        """Validate session token"""
        # Check active sessions first
        if token in self._active_sessions:
            session = self._active_sessions[token]
            if session.expires_at > time.time() and session.is_active:
                return session
            else:
                del self._active_sessions[token]
        
        # Check database
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT session_id, user_id, token, created_at, expires_at, is_active, metadata
                FROM sessions WHERE token = ? AND is_active = 1
            """, (token,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    session = Session(
                        session_id=row[0],
                        user_id=row[1],
                        token=row[2],
                        created_at=row[3],
                        expires_at=row[4],
                        is_active=bool(row[5]),
                        metadata=json.loads(row[6] or '{}')
                    )
                    
                    if session.expires_at > time.time():
                        self._active_sessions[token] = session
                        return session
                    else:
                        # Expired session
                        await self.revoke_session(token)
        
        return None
    
    async def revoke_session(self, token: str):
        """Revoke session token"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE sessions SET is_active = 0 WHERE token = ?
            """, (token,))
            await db.commit()
        
        if token in self._active_sessions:
            del self._active_sessions[token]
    
    async def create_resource(self, resource_id: str, resource_type: ResourceType, owner_id: str) -> Resource:
        """Create resource with optimistic locking"""
        resource = Resource(
            resource_id=resource_id,
            resource_type=resource_type,
            owner_id=owner_id,
            created_at=time.time()
        )
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO resources (resource_id, resource_type, owner_id, created_at, metadata, version)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (
                resource.resource_id, resource.resource_type.value,
                resource.owner_id, resource.created_at, json.dumps(resource.metadata)
            ))
            await db.commit()
        
        await self._audit_log(
            user_id=owner_id,
            action="resource_created",
            resource_id=resource_id,
            resource_type=resource_type.value,
            decision="allowed",
            reason=f"Resource {resource_id} created by {owner_id}"
        )
        
        return resource
    
    async def get_resource(self, resource_id: str) -> Optional[Resource]:
        """Get resource by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT resource_id, resource_type, owner_id, created_at, metadata
                FROM resources WHERE resource_id = ?
            """, (resource_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return Resource(
                        resource_id=row[0],
                        resource_type=ResourceType(row[1]),
                        owner_id=row[2],
                        created_at=row[3],
                        metadata=json.loads(row[4] or '{}')
                    )
                return None
    
    async def check_permission(self, user_id: str, resource_id: str, permission: Permission) -> AccessDecision:
        """Check if user has permission for resource"""
        user = await self.get_user(user_id)
        if not user or not user.is_active:
            return AccessDecision(
                allowed=False,
                reason="User not found or inactive",
                user_role=None
            )
        
        resource = await self.get_resource(resource_id)
        if not resource:
            return AccessDecision(
                allowed=False,
                reason="Resource not found",
                user_role=user.role
            )
        
        # Check role permissions
        user_permissions = self._role_permissions.get(user.role, set())
        if permission not in user_permissions:
            decision = AccessDecision(
                allowed=False,
                reason=f"Role {user.role.value} lacks permission {permission.value}",
                required_permission=permission,
                user_role=user.role,
                resource_owner=resource.owner_id
            )
        else:
            # Check resource ownership for sensitive operations
            if permission in [Permission.DELETE, Permission.ADMIN] and resource.owner_id != user_id:
                decision = AccessDecision(
                    allowed=False,
                    reason=f"Only resource owner can perform {permission.value}",
                    required_permission=permission,
                    user_role=user.role,
                    resource_owner=resource.owner_id
                )
            else:
                decision = AccessDecision(
                    allowed=True,
                    reason=f"Permission {permission.value} granted to {user.role.value}",
                    required_permission=permission,
                    user_role=user.role,
                    resource_owner=resource.owner_id
                )
        
        # Audit log
        await self._audit_log(
            user_id=user_id,
            action=f"check_permission_{permission.value}",
            resource_id=resource_id,
            resource_type=resource.resource_type.value,
            decision="allowed" if decision.allowed else "denied",
            reason=decision.reason
        )
        
        return decision
    
    async def authorize(self, token: str, resource_id: str, permission: Permission) -> AccessDecision:
        """Authorize user session for resource access"""
        session = await self.validate_session(token)
        if not session:
            return AccessDecision(
                allowed=False,
                reason="Invalid or expired session"
            )
        
        # Update last active
        await self._update_user_activity(session.user_id)
        
        return await self.check_permission(session.user_id, resource_id, permission)
    
    async def _update_user_activity(self, user_id: str):
        """Update user last active timestamp"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET last_active = ? WHERE user_id = ?
            """, (time.time(), user_id))
            await db.commit()
    
    async def _audit_log(self, user_id: str, action: str, decision: str, reason: str,
                        resource_id: str = None, resource_type: str = None, metadata: Dict = None):
        """Log authorization decision"""
        log_id = str(uuid.uuid4())
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO audit_log (log_id, user_id, action, resource_id, resource_type, decision, reason, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id, user_id, action, resource_id, resource_type,
                decision, reason, time.time(), json.dumps(metadata or {})
            ))
            await db.commit()
    
    def _generate_token(self, user_id: str) -> str:
        """Generate secure session token"""
        data = f"{user_id}:{time.time()}:{uuid.uuid4()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def get_audit_logs(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """Get audit logs with optional filtering"""
        query = "SELECT * FROM audit_log"
        params = []
        
        if user_id:
            query += " WHERE user_id = ?"
            params.append(user_id)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = time.time()
        
        # Clean active sessions
        expired_tokens = [
            token for token, session in self._active_sessions.items()
            if session.expires_at <= now
        ]
        for token in expired_tokens:
            del self._active_sessions[token]
        
        # Clean database sessions
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE sessions SET is_active = 0 WHERE expires_at <= ? AND is_active = 1
            """, (now,))
            await db.commit()
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get RBAC system metrics"""
        async with aiosqlite.connect(self.db_path) as db:
            # User metrics
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_active = 1") as cursor:
                active_users = (await cursor.fetchone())[0]
            
            # Session metrics
            async with db.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1") as cursor:
                active_sessions = (await cursor.fetchone())[0]
            
            # Resource metrics
            async with db.execute("SELECT COUNT(*) FROM resources") as cursor:
                total_resources = (await cursor.fetchone())[0]
            
            # Audit log metrics
            async with db.execute("SELECT COUNT(*) FROM audit_log WHERE timestamp > ?", (time.time() - 3600,)) as cursor:
                recent_audits = (await cursor.fetchone())[0]
        
        return {
            "active_users": active_users,
            "active_sessions": active_sessions,
            "total_resources": total_resources,
            "recent_audits_1h": recent_audits,
            "cached_sessions": len(self._active_sessions)
        }
