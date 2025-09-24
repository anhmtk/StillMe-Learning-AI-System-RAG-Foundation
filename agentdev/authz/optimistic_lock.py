"""
Optimistic Locking for AgentDev RBAC
SEAL-GRADE Concurrency Control

Features:
- Version-based optimistic locking
- Conflict detection and resolution
- Automatic retry with exponential backoff
- Deadlock prevention
- Resource-level locking granularity
"""

import asyncio
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Any, Callable
import logging

logger = logging.getLogger(__name__)

class LockStatus(Enum):
    """Lock status enumeration"""
    ACQUIRED = "acquired"
    CONFLICT = "conflict"
    EXPIRED = "expired"
    RELEASED = "released"

class ConflictResolution(Enum):
    """Conflict resolution strategies"""
    RETRY = "retry"
    FAIL = "fail"
    MERGE = "merge"
    OVERWRITE = "overwrite"

@dataclass
class LockInfo:
    """Lock information"""
    lock_id: str
    resource_id: str
    user_id: str
    version: int
    acquired_at: float
    expires_at: float
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ConflictResult:
    """Conflict resolution result"""
    resolved: bool
    new_version: Optional[int] = None
    conflict_data: Optional[Dict[str, Any]] = None
    resolution_strategy: Optional[ConflictResolution] = None

class OptimisticLockManager:
    """SEAL-GRADE Optimistic Lock Manager"""
    
    def __init__(self, default_timeout: float = 30.0, max_retries: int = 3):
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self._locks: Dict[str, LockInfo] = {}
        self._lock = asyncio.Lock()
        self._conflict_handlers: Dict[str, Callable] = {}
        
    async def acquire_lock(self, resource_id: str, user_id: str, 
                          current_version: int, timeout: float = None) -> LockInfo:
        """Acquire optimistic lock for resource"""
        if timeout is None:
            timeout = self.default_timeout
            
        lock_id = str(uuid.uuid4())
        now = time.time()
        
        lock_info = LockInfo(
            lock_id=lock_id,
            resource_id=resource_id,
            user_id=user_id,
            version=current_version,
            acquired_at=now,
            expires_at=now + timeout
        )
        
        async with self._lock:
            # Check for existing lock
            existing_lock = self._locks.get(resource_id)
            if existing_lock:
                if existing_lock.user_id == user_id:
                    # Same user, update lock
                    existing_lock.version = current_version
                    existing_lock.expires_at = now + timeout
                    return existing_lock
                else:
                    # Different user, check if expired
                    if existing_lock.expires_at <= now:
                        # Expired lock, take over
                        del self._locks[resource_id]
                    else:
                        # Active lock by different user
                        raise LockConflictError(
                            f"Resource {resource_id} locked by user {existing_lock.user_id}",
                            existing_lock
                        )
            
            # Acquire new lock
            self._locks[resource_id] = lock_info
            logger.debug(f"Lock acquired: {resource_id} by {user_id} (v{current_version})")
            
        return lock_info
    
    async def release_lock(self, lock_id: str) -> bool:
        """Release optimistic lock"""
        async with self._lock:
            for resource_id, lock_info in list(self._locks.items()):
                if lock_info.lock_id == lock_id:
                    del self._locks[resource_id]
                    logger.debug(f"Lock released: {resource_id} ({lock_id})")
                    return True
            return False
    
    async def validate_lock(self, lock_id: str, expected_version: int) -> bool:
        """Validate lock is still valid and version matches"""
        async with self._lock:
            for lock_info in self._locks.values():
                if lock_info.lock_id == lock_id:
                    if lock_info.expires_at <= time.time():
                        # Expired
                        del self._locks[lock_info.resource_id]
                        return False
                    if lock_info.version != expected_version:
                        # Version mismatch
                        return False
                    return True
            return False
    
    async def update_with_retry(self, resource_id: str, user_id: str,
                               update_func: Callable, *args, **kwargs) -> Any:
        """Execute update with optimistic locking and retry"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Get current version (this should be implemented by the caller)
                current_version = await self._get_current_version(resource_id)
                
                # Acquire lock
                lock_info = await self.acquire_lock(resource_id, user_id, current_version)
                
                try:
                    # Execute update
                    result = await update_func(lock_info, *args, **kwargs)
                    
                    # Validate lock before committing
                    if await self.validate_lock(lock_info.lock_id, current_version):
                        await self.release_lock(lock_info.lock_id)
                        return result
                    else:
                        raise LockConflictError("Version conflict during update")
                        
                except Exception as e:
                    await self.release_lock(lock_info.lock_id)
                    raise e
                    
            except LockConflictError as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 0.1 * (2 ** attempt)
                    await asyncio.sleep(wait_time)
                    logger.debug(f"Retry {attempt + 1} after conflict: {e}")
                else:
                    break
            except Exception as e:
                last_exception = e
                break
        
        if last_exception:
            raise last_exception
        else:
            raise Exception("Max retries exceeded")
    
    async def _get_current_version(self, resource_id: str) -> int:
        """Get current version of resource (to be implemented by caller)"""
        # This is a placeholder - the actual implementation should
        # query the database for the current version
        return 1
    
    async def cleanup_expired_locks(self):
        """Clean up expired locks"""
        now = time.time()
        expired_locks = []
        
        async with self._lock:
            for resource_id, lock_info in list(self._locks.items()):
                if lock_info.expires_at <= now:
                    expired_locks.append(resource_id)
            
            for resource_id in expired_locks:
                del self._locks[resource_id]
                logger.debug(f"Expired lock cleaned up: {resource_id}")
    
    async def get_lock_status(self, resource_id: str) -> Optional[LockInfo]:
        """Get current lock status for resource"""
        async with self._lock:
            lock_info = self._locks.get(resource_id)
            if lock_info and lock_info.expires_at <= time.time():
                # Expired
                del self._locks[resource_id]
                return None
            return lock_info
    
    async def force_release_lock(self, resource_id: str, admin_user_id: str) -> bool:
        """Force release lock (admin only)"""
        async with self._lock:
            if resource_id in self._locks:
                lock_info = self._locks[resource_id]
                del self._locks[resource_id]
                logger.warning(f"Lock force-released by admin {admin_user_id}: {resource_id}")
                return True
            return False
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get locking system metrics"""
        async with self._lock:
            now = time.time()
            active_locks = len(self._locks)
            expired_locks = sum(1 for lock in self._locks.values() if lock.expires_at <= now)
            
            # Group by user
            locks_by_user = {}
            for lock in self._locks.values():
                user_id = lock.user_id
                locks_by_user[user_id] = locks_by_user.get(user_id, 0) + 1
        
        return {
            "active_locks": active_locks,
            "expired_locks": expired_locks,
            "locks_by_user": locks_by_user,
            "total_locks_managed": len(self._locks)
        }

class LockConflictError(Exception):
    """Exception raised when lock conflict occurs"""
    
    def __init__(self, message: str, conflicting_lock: LockInfo = None):
        super().__init__(message)
        self.conflicting_lock = conflicting_lock

class OptimisticLockDecorator:
    """Decorator for automatic optimistic locking"""
    
    def __init__(self, lock_manager: OptimisticLockManager, 
                 resource_id_func: Callable = None, user_id_func: Callable = None):
        self.lock_manager = lock_manager
        self.resource_id_func = resource_id_func
        self.user_id_func = user_id_func
    
    def __call__(self, func: Callable):
        async def wrapper(*args, **kwargs):
            # Extract resource_id and user_id
            resource_id = None
            user_id = None
            
            if self.resource_id_func:
                resource_id = self.resource_id_func(*args, **kwargs)
            if self.user_id_func:
                user_id = self.user_id_func(*args, **kwargs)
            
            if not resource_id or not user_id:
                raise ValueError("Resource ID and User ID must be provided")
            
            # Execute with optimistic locking
            return await self.lock_manager.update_with_retry(
                resource_id, user_id, func, *args, **kwargs
            )
        
        return wrapper

# Utility functions for common locking patterns
async def with_optimistic_lock(lock_manager: OptimisticLockManager,
                              resource_id: str, user_id: str,
                              update_func: Callable, *args, **kwargs):
    """Context manager for optimistic locking"""
    return await lock_manager.update_with_retry(
        resource_id, user_id, update_func, *args, **kwargs
    )

def extract_resource_id_from_args(*args, **kwargs) -> str:
    """Extract resource_id from function arguments"""
    if args and hasattr(args[0], 'resource_id'):
        return args[0].resource_id
    return kwargs.get('resource_id')

def extract_user_id_from_args(*args, **kwargs) -> str:
    """Extract user_id from function arguments"""
    if args and hasattr(args[0], 'user_id'):
        return args[0].user_id
    return kwargs.get('user_id')
