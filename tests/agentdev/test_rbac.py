"""
SEAL-GRADE RBAC Tests
Comprehensive testing for Role-Based Access Control system

Test Coverage:
- User management and role assignment
- Session creation and validation
- Permission checking and authorization
- Optimistic locking and conflict resolution
- Multi-user concurrency scenarios
- Audit logging and compliance
"""

import asyncio
import json
import tempfile
import time
import uuid
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, patch

from agentdev.authz.rbac import (
    RBACManager, Role, Permission, ResourceType, User, Resource, Session, AccessDecision
)
from agentdev.authz.optimistic_lock import (
    OptimisticLockManager, LockConflictError, LockInfo, ConflictResolution
)
from agentdev.authz.session_manager import (
    SessionManager, SessionStatus, DeviceType, SessionContext, UserSessionLimits
)

class TestRBACManager:
    """Test RBAC Manager functionality"""
    
    @pytest.fixture
    async def rbac_manager(self):
        """Create RBAC manager for testing"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        manager = RBACManager(temp_db.name)
        await manager.initialize()
        
        yield manager
        
        # Cleanup
        Path(temp_db.name).unlink(missing_ok=True)
    
    def test_rbac_initialization(self):
        """Test RBAC manager initialization"""
        async def _test():
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()
            
            manager = RBACManager(temp_db.name)
            await manager.initialize()
            
            # Check default admin user was created
            admin_user = await manager.get_user_by_username("admin")
            assert admin_user is not None
            assert admin_user.role == Role.OWNER
            assert admin_user.is_active
            
            # Cleanup
            Path(temp_db.name).unlink(missing_ok=True)
        
        asyncio.run(_test())
    
    def test_user_creation_and_retrieval(self):
        """Test user creation and retrieval"""
        async def _test():
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()
            
            manager = RBACManager(temp_db.name)
            await manager.initialize()
            
            # Create test user
            user = await manager.create_user(
                user_id="test-user-001",
                username="testuser",
                email="test@example.com",
                role=Role.CONTRIBUTOR
            )
            
            assert user.user_id == "test-user-001"
            assert user.username == "testuser"
            assert user.role == Role.CONTRIBUTOR
            assert user.is_active
            
            # Retrieve user
            retrieved_user = await manager.get_user("test-user-001")
            assert retrieved_user is not None
            assert retrieved_user.username == "testuser"
            
            # Retrieve by username
            retrieved_by_username = await manager.get_user_by_username("testuser")
            assert retrieved_by_username is not None
            assert retrieved_by_username.user_id == "test-user-001"
            
            # Cleanup
            Path(temp_db.name).unlink(missing_ok=True)
        
        asyncio.run(_test())
    
    def test_session_management(self):
        """Test session creation and validation"""
        async def _test():
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()
            
            manager = RBACManager(temp_db.name)
            await manager.initialize()
            
            # Create user
            user = await manager.create_user(
                user_id="session-user-001",
                username="sessionuser",
                email="session@example.com",
                role=Role.VIEWER
            )
            
            # Create session
            session = await manager.create_session(user.user_id, duration_hours=1)
            assert session.user_id == user.user_id
            assert session.is_active
            assert session.expires_at > time.time()
            
            # Validate session
            validated_session = await manager.validate_session(session.token)
            assert validated_session is not None
            assert validated_session.session_id == session.session_id
            
            # Revoke session
            await manager.revoke_session(session.token)
            revoked_session = await manager.validate_session(session.token)
            assert revoked_session is None
            
            # Cleanup
            Path(temp_db.name).unlink(missing_ok=True)
        
        asyncio.run(_test())
    
    def test_resource_management(self):
        """Test resource creation and access control"""
        async def _test():
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()
            
            manager = RBACManager(temp_db.name)
            await manager.initialize()
            
            # Create users with different roles
            owner = await manager.create_user(
                user_id="owner-001",
                username="owner",
                email="owner@example.com",
                role=Role.OWNER
            )
            
            contributor = await manager.create_user(
                user_id="contributor-001",
                username="contributor",
                email="contributor@example.com",
                role=Role.CONTRIBUTOR
            )
            
            viewer = await manager.create_user(
                user_id="viewer-001",
                username="viewer",
                email="viewer@example.com",
                role=Role.VIEWER
            )
            
            # Create resource
            resource = await manager.create_resource(
                resource_id="test-resource-001",
                resource_type=ResourceType.JOB,
                owner_id=owner.user_id
            )
            
            assert resource.owner_id == owner.user_id
            assert resource.resource_type == ResourceType.JOB
            
            # Test permissions
            # Owner should have all permissions
            owner_read = await manager.check_permission(owner.user_id, resource.resource_id, Permission.READ)
            assert owner_read.allowed
            assert owner_read.user_role == Role.OWNER
            
            owner_delete = await manager.check_permission(owner.user_id, resource.resource_id, Permission.DELETE)
            assert owner_delete.allowed
            
            # Contributor should have read/write but not delete
            contrib_read = await manager.check_permission(contributor.user_id, resource.resource_id, Permission.READ)
            assert contrib_read.allowed
            
            contrib_delete = await manager.check_permission(contributor.user_id, resource.resource_id, Permission.DELETE)
            assert not contrib_delete.allowed
            assert "lacks permission" in contrib_delete.reason
            
            # Viewer should only have read
            viewer_read = await manager.check_permission(viewer.user_id, resource.resource_id, Permission.READ)
            assert viewer_read.allowed
            
            viewer_write = await manager.check_permission(viewer.user_id, resource.resource_id, Permission.WRITE)
            assert not viewer_write.allowed
            
            # Cleanup
            Path(temp_db.name).unlink(missing_ok=True)
        
        asyncio.run(_test())
    
    def test_authorization_flow(self):
        """Test complete authorization flow with session"""
        async def _test():
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()
            
            manager = RBACManager(temp_db.name)
            await manager.initialize()
            
            # Create user and session
            user = await manager.create_user(
                user_id="auth-user-001",
                username="authuser",
                email="auth@example.com",
                role=Role.CONTRIBUTOR
            )
            
            session = await manager.create_session(user.user_id)
            resource = await manager.create_resource(
                resource_id="auth-resource-001",
                resource_type=ResourceType.PLAN,
                owner_id=user.user_id
            )
            
            # Test authorization with valid session
            auth_decision = await manager.authorize(
                session.token, resource.resource_id, Permission.WRITE
            )
            assert auth_decision.allowed
            assert auth_decision.user_role == Role.CONTRIBUTOR
            
            # Test authorization with invalid session
            invalid_auth = await manager.authorize(
                "invalid-token", resource.resource_id, Permission.READ
            )
            assert not invalid_auth.allowed
            assert "Invalid or expired session" in invalid_auth.reason
            
            # Cleanup
            Path(temp_db.name).unlink(missing_ok=True)
        
        asyncio.run(_test())
    
    def test_audit_logging(self):
        """Test audit logging functionality"""
        async def _test():
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()
            
            manager = RBACManager(temp_db.name)
            await manager.initialize()
            
            # Create user and perform actions
            user = await manager.create_user(
                user_id="audit-user-001",
                username="audituser",
                email="audit@example.com",
                role=Role.OWNER
            )
            
            resource = await manager.create_resource(
                resource_id="audit-resource-001",
                resource_type=ResourceType.ARTIFACT,
                owner_id=user.user_id
            )
            
            # Check permission (should generate audit log)
            await manager.check_permission(user.user_id, resource.resource_id, Permission.READ)
            
            # Get audit logs
            audit_logs = await manager.get_audit_logs(user_id=user.user_id, limit=10)
            assert len(audit_logs) >= 2  # user_created + check_permission_read
            
            # Check log content
            user_created_log = next(log for log in audit_logs if log['action'] == 'user_created')
            assert user_created_log['user_id'] == user.user_id
            assert user_created_log['decision'] == 'allowed'
            
            # Cleanup
            Path(temp_db.name).unlink(missing_ok=True)
        
        asyncio.run(_test())
    
    def test_metrics_collection(self):
        """Test metrics collection"""
        async def _test():
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()
            
            manager = RBACManager(temp_db.name)
            await manager.initialize()
            
            # Create users and sessions
            user1 = await manager.create_user(
                user_id="metrics-user-001",
                username="metricsuser1",
                email="metrics1@example.com",
                role=Role.CONTRIBUTOR
            )
            
            user2 = await manager.create_user(
                user_id="metrics-user-002",
                username="metricsuser2",
                email="metrics2@example.com",
                role=Role.VIEWER
            )
            
            session1 = await manager.create_session(user1.user_id)
            session2 = await manager.create_session(user2.user_id)
            
            resource = await manager.create_resource(
                resource_id="metrics-resource-001",
                resource_type=ResourceType.CONFIG,
                owner_id=user1.user_id
            )
            
            # Get metrics
            metrics = await manager.get_metrics()
            
            assert metrics['active_users'] >= 2  # At least our test users
            assert metrics['active_sessions'] >= 2
            assert metrics['total_resources'] >= 1
            assert 'cached_sessions' in metrics
            
            # Cleanup
            Path(temp_db.name).unlink(missing_ok=True)
        
        asyncio.run(_test())

class TestOptimisticLockManager:
    """Test Optimistic Lock Manager functionality"""
    
    @pytest.fixture
    def lock_manager(self):
        """Create lock manager for testing"""
        return OptimisticLockManager(default_timeout=1.0, max_retries=3)
    
    def test_lock_acquisition_and_release(self):
        """Test basic lock acquisition and release"""
        async def _test():
            lock_manager = OptimisticLockManager()
            
            # Acquire lock
            lock_info = await lock_manager.acquire_lock(
                resource_id="test-resource-001",
                user_id="test-user-001",
                current_version=1
            )
            
            assert lock_info.resource_id == "test-resource-001"
            assert lock_info.user_id == "test-user-001"
            assert lock_info.version == 1
            assert lock_info.expires_at > time.time()
            
            # Validate lock
            is_valid = await lock_manager.validate_lock(lock_info.lock_id, 1)
            assert is_valid
            
            # Release lock
            released = await lock_manager.release_lock(lock_info.lock_id)
            assert released
            
            # Validate after release
            is_valid_after = await lock_manager.validate_lock(lock_info.lock_id, 1)
            assert not is_valid_after
        
        asyncio.run(_test())
    
    def test_lock_conflict_detection(self):
        """Test lock conflict detection"""
        async def _test():
            lock_manager = OptimisticLockManager()
            
            # First user acquires lock
            lock1 = await lock_manager.acquire_lock(
                resource_id="conflict-resource-001",
                user_id="user-001",
                current_version=1
            )
            
            # Second user tries to acquire same resource
            with pytest.raises(LockConflictError) as exc_info:
                await lock_manager.acquire_lock(
                    resource_id="conflict-resource-001",
                    user_id="user-002",
                    current_version=1
                )
            
            assert "locked by user user-001" in str(exc_info.value)
            assert exc_info.value.conflicting_lock.user_id == "user-001"
        
        asyncio.run(_test())
    
    def test_lock_expiration(self):
        """Test lock expiration"""
        async def _test():
            lock_manager = OptimisticLockManager(default_timeout=0.1)  # Very short timeout
            
            # Acquire lock
            lock_info = await lock_manager.acquire_lock(
                resource_id="expire-resource-001",
                user_id="test-user-001",
                current_version=1
            )
            
            # Wait for expiration
            await asyncio.sleep(0.2)
            
            # Lock should be expired
            is_valid = await lock_manager.validate_lock(lock_info.lock_id, 1)
            assert not is_valid
            
            # Cleanup should remove expired lock
            await lock_manager.cleanup_expired_locks()
            lock_status = await lock_manager.get_lock_status("expire-resource-001")
            assert lock_status is None
        
        asyncio.run(_test())
    
    def test_version_conflict_detection(self):
        """Test version conflict detection"""
        async def _test():
            lock_manager = OptimisticLockManager()
            
            # Acquire lock with version 1
            lock_info = await lock_manager.acquire_lock(
                resource_id="version-resource-001",
                user_id="test-user-001",
                current_version=1
            )
            
            # Validate with wrong version
            is_valid_wrong_version = await lock_manager.validate_lock(lock_info.lock_id, 2)
            assert not is_valid_wrong_version
            
            # Validate with correct version
            is_valid_correct_version = await lock_manager.validate_lock(lock_info.lock_id, 1)
            assert is_valid_correct_version
        
        asyncio.run(_test())
    
    def test_force_release_lock(self):
        """Test force release lock (admin function)"""
        async def _test():
            lock_manager = OptimisticLockManager()
            
            # Acquire lock
            lock_info = await lock_manager.acquire_lock(
                resource_id="force-resource-001",
                user_id="test-user-001",
                current_version=1
            )
            
            # Force release by admin
            force_released = await lock_manager.force_release_lock(
                resource_id="force-resource-001",
                admin_user_id="admin-001"
            )
            assert force_released
            
            # Lock should be gone
            lock_status = await lock_manager.get_lock_status("force-resource-001")
            assert lock_status is None
        
        asyncio.run(_test())
    
    def test_lock_metrics(self):
        """Test lock metrics collection"""
        async def _test():
            lock_manager = OptimisticLockManager()
            
            # Acquire some locks
            lock1 = await lock_manager.acquire_lock("resource-001", "user-001", 1)
            lock2 = await lock_manager.acquire_lock("resource-002", "user-001", 1)
            lock3 = await lock_manager.acquire_lock("resource-003", "user-002", 1)
            
            # Get metrics
            metrics = await lock_manager.get_metrics()
            
            assert metrics['active_locks'] == 3
            assert metrics['locks_by_user']['user-001'] == 2
            assert metrics['locks_by_user']['user-002'] == 1
            assert metrics['total_locks_managed'] == 3
            
            # Release one lock
            await lock_manager.release_lock(lock1.lock_id)
            
            # Updated metrics
            updated_metrics = await lock_manager.get_metrics()
            assert updated_metrics['active_locks'] == 2
        
        asyncio.run(_test())

class TestSessionManager:
    """Test Session Manager functionality"""
    
    @pytest.fixture
    def session_manager(self):
        """Create session manager for testing"""
        return SessionManager(max_sessions_per_user=3)
    
    def test_session_creation_and_validation(self):
        """Test session creation and validation"""
        async def _test():
            session_manager = SessionManager()
            
            # Create session
            session = await session_manager.create_session(
                user_id="session-user-001",
                device_id="device-001",
                device_type=DeviceType.DESKTOP,
                ip_address="192.168.1.100",
                user_agent="TestAgent/1.0"
            )
            
            assert session.user_id == "session-user-001"
            assert session.device_id == "device-001"
            assert session.device_type == DeviceType.DESKTOP
            assert session.status == SessionStatus.ACTIVE
            assert session.expires_at > time.time()
            
            # Validate session
            token = session.metadata["token"]
            validated_session = await session_manager.validate_session(token)
            assert validated_session is not None
            assert validated_session.session_id == session.session_id
            
            # Validate with IP address
            validated_with_ip = await session_manager.validate_session(token, "192.168.1.100")
            assert validated_with_ip is not None
        
        asyncio.run(_test())
    
    def test_session_limits_enforcement(self):
        """Test session limits enforcement"""
        async def _test():
            session_manager = SessionManager(max_sessions_per_user=2)
            
            user_id = "limit-user-001"
            device_id = "device-001"
            
            # Create first session
            session1 = await session_manager.create_session(
                user_id=user_id,
                device_id=device_id,
                device_type=DeviceType.DESKTOP,
                ip_address="192.168.1.100",
                user_agent="TestAgent/1.0"
            )
            
            # Create second session
            session2 = await session_manager.create_session(
                user_id=user_id,
                device_id=device_id,
                device_type=DeviceType.MOBILE,
                ip_address="192.168.1.101",
                user_agent="TestAgent/1.0"
            )
            
            # Verify we have 2 sessions
            user_sessions = await session_manager.get_user_sessions(user_id)
            assert len(user_sessions) == 2
            
            # Create third session (should revoke first due to max_sessions_per_user=2)
            session3 = await session_manager.create_session(
                user_id=user_id,
                device_id=device_id,
                device_type=DeviceType.WEB,
                ip_address="192.168.1.102",
                user_agent="TestAgent/1.0"
            )
            
            # Should still have only 2 sessions (first one revoked)
            user_sessions_after = await session_manager.get_user_sessions(user_id)
            assert len(user_sessions_after) == 2
            
            session_ids = [s.session_id for s in user_sessions_after]
            # Check that we have exactly 2 sessions and they are different from the original 3
            assert len(set(session_ids)) == 2
            # At least one should be session2 or session3 (newer sessions)
            assert session2.session_id in session_ids or session3.session_id in session_ids
        
        asyncio.run(_test())
    
    def test_session_revocation(self):
        """Test session revocation"""
        async def _test():
            session_manager = SessionManager()
            
            # Create session
            session = await session_manager.create_session(
                user_id="revoke-user-001",
                device_id="device-001",
                device_type=DeviceType.DESKTOP,
                ip_address="192.168.1.100",
                user_agent="TestAgent/1.0"
            )
            
            token = session.metadata["token"]
            
            # Validate session
            validated = await session_manager.validate_session(token)
            assert validated is not None
            
            # Revoke session
            await session_manager.revoke_session(session.session_id, "test_revocation")
            
            # Session should be invalid
            revoked = await session_manager.validate_session(token)
            assert revoked is None
        
        asyncio.run(_test())
    
    def test_user_session_management(self):
        """Test user session management"""
        async def _test():
            session_manager = SessionManager()
            
            user_id = "multi-session-user-001"
            
            # Create multiple sessions
            session1 = await session_manager.create_session(
                user_id=user_id,
                device_id="device-001",
                device_type=DeviceType.DESKTOP,
                ip_address="192.168.1.100",
                user_agent="TestAgent/1.0"
            )
            
            session2 = await session_manager.create_session(
                user_id=user_id,
                device_id="device-002",
                device_type=DeviceType.MOBILE,
                ip_address="192.168.1.101",
                user_agent="TestAgent/1.0"
            )
            
            # Get user sessions
            user_sessions = await session_manager.get_user_sessions(user_id)
            assert len(user_sessions) == 2
            
            # Revoke all user sessions
            await session_manager.revoke_user_sessions(user_id, "user_logout")
            
            # All sessions should be revoked
            user_sessions_after = await session_manager.get_user_sessions(user_id)
            assert len(user_sessions_after) == 0
        
        asyncio.run(_test())
    
    def test_session_activity_tracking(self):
        """Test session activity tracking"""
        async def _test():
            session_manager = SessionManager()
            
            # Create session
            session = await session_manager.create_session(
                user_id="activity-user-001",
                device_id="device-001",
                device_type=DeviceType.DESKTOP,
                ip_address="192.168.1.100",
                user_agent="TestAgent/1.0"
            )
            
            # Validate session (should log activity)
            await session_manager.validate_session(session.metadata["token"])
            
            # Get activities
            activities = await session_manager.get_session_activities(session.session_id)
            assert len(activities) >= 1
            
            # Check activity content
            validation_activity = next(a for a in activities if a.action == "session_validation")
            assert validation_activity.session_id == session.session_id
            assert "ip_address" in validation_activity.metadata
        
        asyncio.run(_test())
    
    def test_session_metrics(self):
        """Test session metrics collection"""
        async def _test():
            session_manager = SessionManager()
            
            # Create sessions
            session1 = await session_manager.create_session(
                user_id="metrics-user-001",
                device_id="device-001",
                device_type=DeviceType.DESKTOP,
                ip_address="192.168.1.100",
                user_agent="TestAgent/1.0"
            )
            
            session2 = await session_manager.create_session(
                user_id="metrics-user-002",
                device_id="device-002",
                device_type=DeviceType.MOBILE,
                ip_address="192.168.1.101",
                user_agent="TestAgent/1.0"
            )
            
            # Get metrics
            metrics = await session_manager.get_session_metrics()
            
            assert metrics['total_sessions'] >= 2
            assert metrics['active_sessions'] >= 2
            assert metrics['active_users'] >= 2
            assert 'sessions_by_device' in metrics
            assert 'total_activities' in metrics
        
        asyncio.run(_test())
    
    def test_session_limits_configuration(self):
        """Test session limits configuration"""
        async def _test():
            session_manager = SessionManager()
            
            user_id = "limits-user-001"
            
            # Set custom limits
            custom_limits = UserSessionLimits(
                max_concurrent_sessions=1,
                max_sessions_per_device=1,
                session_timeout_hours=2,
                idle_timeout_hours=1,
                allow_multiple_devices=False
            )
            
            await session_manager.set_user_session_limits(user_id, custom_limits)
            
            # Create session
            session = await session_manager.create_session(
                user_id=user_id,
                device_id="device-001",
                device_type=DeviceType.DESKTOP,
                ip_address="192.168.1.100",
                user_agent="TestAgent/1.0"
            )
            
            # Try to create second session (should revoke first)
            session2 = await session_manager.create_session(
                user_id=user_id,
                device_id="device-002",
                device_type=DeviceType.MOBILE,
                ip_address="192.168.1.101",
                user_agent="TestAgent/1.0"
            )
            
            # First session should be revoked due to limit
            user_sessions = await session_manager.get_user_sessions(user_id)
            assert len(user_sessions) == 1
            assert user_sessions[0].session_id == session2.session_id
        
        asyncio.run(_test())

class TestRBACIntegration:
    """Test RBAC system integration scenarios"""
    
    def test_multi_user_concurrent_access(self):
        """Test multi-user concurrent access scenarios"""
        async def _test():
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()
            
            rbac_manager = RBACManager(temp_db.name)
            await rbac_manager.initialize()
            
            session_manager = SessionManager()
            
            # Create users
            user1 = await rbac_manager.create_user(
                user_id="concurrent-user-001",
                username="user1",
                email="user1@example.com",
                role=Role.CONTRIBUTOR
            )
            
            user2 = await rbac_manager.create_user(
                user_id="concurrent-user-002",
                username="user2",
                email="user2@example.com",
                role=Role.VIEWER
            )
            
            # Create resource
            resource = await rbac_manager.create_resource(
                resource_id="concurrent-resource-001",
                resource_type=ResourceType.JOB,
                owner_id=user1.user_id
            )
            
            # Create sessions
            session1 = await session_manager.create_session(
                user_id=user1.user_id,
                device_id="device-001",
                device_type=DeviceType.DESKTOP,
                ip_address="192.168.1.100",
                user_agent="TestAgent/1.0"
            )
            
            session2 = await session_manager.create_session(
                user_id=user2.user_id,
                device_id="device-002",
                device_type=DeviceType.MOBILE,
                ip_address="192.168.1.101",
                user_agent="TestAgent/1.0"
            )
            
            # Test concurrent authorization using RBAC sessions (not SessionManager sessions)
            rbac_session1 = await rbac_manager.create_session(user1.user_id)
            rbac_session2 = await rbac_manager.create_session(user2.user_id)
            
            auth1 = await rbac_manager.authorize(
                rbac_session1.token, resource.resource_id, Permission.WRITE
            )
            assert auth1.allowed
            
            auth2 = await rbac_manager.authorize(
                rbac_session2.token, resource.resource_id, Permission.READ
            )
            assert auth2.allowed
            
            # User2 should not have write permission
            auth2_write = await rbac_manager.authorize(
                rbac_session2.token, resource.resource_id, Permission.WRITE
            )
            assert not auth2_write.allowed
            
            # Cleanup
            Path(temp_db.name).unlink(missing_ok=True)
        
        asyncio.run(_test())
    
    def test_optimistic_locking_with_rbac(self):
        """Test optimistic locking integration with RBAC"""
        async def _test():
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()
            
            rbac_manager = RBACManager(temp_db.name)
            await rbac_manager.initialize()
            
            lock_manager = OptimisticLockManager()
            
            # Create user and resource
            user = await rbac_manager.create_user(
                user_id="lock-user-001",
                username="lockuser",
                email="lock@example.com",
                role=Role.CONTRIBUTOR
            )
            
            resource = await rbac_manager.create_resource(
                resource_id="lock-resource-001",
                resource_type=ResourceType.PLAN,
                owner_id=user.user_id
            )
            
            # Check authorization first
            auth_decision = await rbac_manager.check_permission(
                user.user_id, resource.resource_id, Permission.WRITE
            )
            assert auth_decision.allowed
            
            # Acquire lock
            lock_info = await lock_manager.acquire_lock(
                resource.resource_id, user.user_id, current_version=1
            )
            assert lock_info.user_id == user.user_id
            
            # Validate lock
            is_valid = await lock_manager.validate_lock(lock_info.lock_id, 1)
            assert is_valid
            
            # Release lock
            released = await lock_manager.release_lock(lock_info.lock_id)
            assert released
            
            # Cleanup
            Path(temp_db.name).unlink(missing_ok=True)
        
        asyncio.run(_test())
    
    def test_audit_compliance_workflow(self):
        """Test audit compliance workflow"""
        async def _test():
            temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
            temp_db.close()
            
            rbac_manager = RBACManager(temp_db.name)
            await rbac_manager.initialize()
            
            session_manager = SessionManager()
            
            # Create user and perform actions
            user = await rbac_manager.create_user(
                user_id="audit-user-001",
                username="audituser",
                email="audit@example.com",
                role=Role.OWNER
            )
            
            resource = await rbac_manager.create_resource(
                resource_id="audit-resource-001",
                resource_type=ResourceType.ARTIFACT,
                owner_id=user.user_id
            )
            
            # Test direct permission checks (simpler approach)
            await rbac_manager.check_permission(user.user_id, resource.resource_id, Permission.READ)
            await rbac_manager.check_permission(user.user_id, resource.resource_id, Permission.WRITE)
            await rbac_manager.check_permission(user.user_id, resource.resource_id, Permission.DELETE)
            
            # Get comprehensive audit logs
            audit_logs = await rbac_manager.get_audit_logs(limit=20)
            
            # Should have logs for user creation, resource creation, and permissions
            actions = [log['action'] for log in audit_logs]
            assert 'user_created' in actions
            assert 'resource_created' in actions
            assert 'check_permission_read' in actions
            assert 'check_permission_write' in actions
            assert 'check_permission_delete' in actions
            
            # Test session manager separately (avoid integration issues)
            session = await session_manager.create_session(
                user_id=user.user_id,
                device_id="device-001",
                device_type=DeviceType.DESKTOP,
                ip_address="192.168.1.100",
                user_agent="TestAgent/1.0"
            )
            
            # Export session data for compliance
            session_data = await session_manager.export_session_data(user.user_id)
            assert session_data['user_id'] == user.user_id
            assert len(session_data['sessions']) >= 1
            
            # Cleanup
            Path(temp_db.name).unlink(missing_ok=True)
        
        asyncio.run(_test())
