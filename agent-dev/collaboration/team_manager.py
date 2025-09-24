#!/usr/bin/env python3
"""
StillMe AgentDev - Team Manager
Enterprise-grade multi-user support and team collaboration
"""

import asyncio
import json
import time
import uuid
import hashlib
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import aiofiles
from pathlib import Path
import yaml

class UserRole(Enum):
    """User roles in AgentDev"""
    ADMIN = "admin"
    LEAD_DEVELOPER = "lead_developer"
    DEVELOPER = "developer"
    QA_ENGINEER = "qa_engineer"
    DEVOPS_ENGINEER = "devops_engineer"
    VIEWER = "viewer"

class TaskStatus(Enum):
    """Task status for collaboration"""
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"

class ConflictType(Enum):
    """Conflict types in collaborative work"""
    FILE_EDIT = "file_edit"
    CONFIG_CHANGE = "config_change"
    DEPENDENCY_UPDATE = "dependency_update"
    RESOURCE_LOCK = "resource_lock"
    PERMISSION_CONFLICT = "permission_conflict"

@dataclass
class User:
    """User information"""
    user_id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    permissions: List[str]
    created_at: float
    last_active: float
    preferences: Dict[str, Any]
    avatar_url: Optional[str] = None

@dataclass
class Team:
    """Team information"""
    team_id: str
    name: str
    description: str
    members: List[str]  # User IDs
    roles: Dict[str, UserRole]  # User ID -> Role mapping
    permissions: Dict[str, List[str]]  # Role -> Permissions mapping
    created_at: float
    updated_at: float
    settings: Dict[str, Any]

@dataclass
class TaskAssignment:
    """Task assignment for collaboration"""
    task_id: str
    assigned_to: str  # User ID
    assigned_by: str  # User ID
    assigned_at: float
    status: TaskStatus
    priority: int
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    dependencies: List[str]
    blockers: List[str]
    notes: str

@dataclass
class Conflict:
    """Conflict in collaborative work"""
    conflict_id: str
    conflict_type: ConflictType
    description: str
    involved_users: List[str]
    affected_resources: List[str]
    created_at: float
    resolved_at: Optional[float]
    resolution: Optional[str]
    resolved_by: Optional[str]
    severity: str  # low, medium, high, critical

@dataclass
class CollaborationSession:
    """Active collaboration session"""
    session_id: str
    task_id: str
    participants: List[str]
    started_at: float
    last_activity: float
    shared_resources: List[str]
    chat_messages: List[Dict[str, Any]]
    screen_shares: List[Dict[str, Any]]
    voice_enabled: bool
    video_enabled: bool

class TeamManager:
    """Enterprise team management and collaboration system"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.users: Dict[str, User] = {}
        self.teams: Dict[str, Team] = {}
        self.task_assignments: Dict[str, TaskAssignment] = {}
        self.conflicts: Dict[str, Conflict] = {}
        self.active_sessions: Dict[str, CollaborationSession] = {}
        self.user_sessions: Dict[str, str] = {}  # User ID -> Session ID
        self.locks: Dict[str, Dict[str, Any]] = {}  # Resource locks
        self.running = False
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load team management configuration"""
        if config_path:
            config_file = Path(config_path)
        else:
            config_file = Path("agent-dev/config/team_manager.yaml")
            
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            return {
                'default_permissions': {
                    'admin': ['*'],
                    'lead_developer': ['task.create', 'task.assign', 'task.review', 'team.manage'],
                    'developer': ['task.create', 'task.execute', 'task.review'],
                    'qa_engineer': ['task.review', 'task.test', 'security.scan'],
                    'devops_engineer': ['deploy.execute', 'infrastructure.manage', 'monitoring.view'],
                    'viewer': ['task.view', 'logs.view']
                },
                'conflict_resolution': {
                    'auto_resolve': True,
                    'escalation_threshold': 300,  # 5 minutes
                    'notification_enabled': True
                },
                'collaboration': {
                    'max_session_duration': 3600,  # 1 hour
                    'max_participants': 10,
                    'auto_cleanup': True
                },
                'data_directory': '.agentdev/team_data'
            }
    
    def create_user(self, username: str, email: str, full_name: str,
                   role: UserRole, password_hash: str) -> str:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        
        # Get default permissions for role
        permissions = self.config['default_permissions'].get(role.value, [])
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            permissions=permissions,
            created_at=time.time(),
            last_active=time.time(),
            preferences={}
        )
        
        self.users[user_id] = user
        print(f"✅ User created: {username} ({role.value})")
        return user_id
    
    def create_team(self, name: str, description: str, creator_id: str) -> str:
        """Create a new team"""
        team_id = str(uuid.uuid4())
        
        team = Team(
            team_id=team_id,
            name=name,
            description=description,
            members=[creator_id],
            roles={creator_id: UserRole.ADMIN},
            permissions=self.config['default_permissions'].copy(),
            created_at=time.time(),
            updated_at=time.time(),
            settings={}
        )
        
        self.teams[team_id] = team
        print(f"✅ Team created: {name}")
        return team_id
    
    def add_user_to_team(self, team_id: str, user_id: str, role: UserRole) -> bool:
        """Add user to team"""
        if team_id not in self.teams:
            return False
        
        if user_id not in self.users:
            return False
        
        team = self.teams[team_id]
        team.members.append(user_id)
        team.roles[user_id] = role
        team.updated_at = time.time()
        
        print(f"✅ User {user_id} added to team {team_id} as {role.value}")
        return True
    
    def remove_user_from_team(self, team_id: str, user_id: str) -> bool:
        """Remove user from team"""
        if team_id not in self.teams:
            return False
        
        team = self.teams[team_id]
        if user_id in team.members:
            team.members.remove(user_id)
            if user_id in team.roles:
                del team.roles[user_id]
            team.updated_at = time.time()
            print(f"✅ User {user_id} removed from team {team_id}")
            return True
        
        return False
    
    def assign_task(self, task_id: str, assigned_to: str, assigned_by: str,
                   priority: int = 1, estimated_hours: Optional[float] = None) -> bool:
        """Assign task to user"""
        if assigned_to not in self.users:
            return False
        
        assignment = TaskAssignment(
            task_id=task_id,
            assigned_to=assigned_to,
            assigned_by=assigned_by,
            assigned_at=time.time(),
            status=TaskStatus.ASSIGNED,
            priority=priority,
            estimated_hours=estimated_hours,
            actual_hours=None,
            dependencies=[],
            blockers=[],
            notes=""
        )
        
        self.task_assignments[task_id] = assignment
        print(f"✅ Task {task_id} assigned to {assigned_to}")
        return True
    
    def update_task_status(self, task_id: str, status: TaskStatus, 
                          user_id: str, notes: str = "") -> bool:
        """Update task status"""
        if task_id not in self.task_assignments:
            return False
        
        assignment = self.task_assignments[task_id]
        
        # Check permissions
        if not self._can_update_task(user_id, assignment):
            return False
        
        old_status = assignment.status
        assignment.status = status
        assignment.notes = notes
        
        # Log status change
        print(f"📝 Task {task_id} status changed from {old_status.value} to {status.value} by {user_id}")
        
        # Check for conflicts
        if status == TaskStatus.IN_PROGRESS:
            self._check_for_conflicts(task_id, user_id)
        
        return True
    
    def _can_update_task(self, user_id: str, assignment: TaskAssignment) -> bool:
        """Check if user can update task"""
        # Task assignee can always update
        if assignment.assigned_to == user_id:
            return True
        
        # Check team permissions
        user = self.users.get(user_id)
        if not user:
            return False
        
        # Admins and lead developers can update any task
        if user.role in [UserRole.ADMIN, UserRole.LEAD_DEVELOPER]:
            return True
        
        return False
    
    def _check_for_conflicts(self, task_id: str, user_id: str):
        """Check for potential conflicts when starting task"""
        # Check for resource locks
        for resource, lock_info in self.locks.items():
            if lock_info['locked_by'] != user_id and lock_info['expires_at'] > time.time():
                self._create_conflict(
                    ConflictType.RESOURCE_LOCK,
                    f"Resource {resource} is locked by {lock_info['locked_by']}",
                    [user_id, lock_info['locked_by']],
                    [resource]
                )
    
    def _create_conflict(self, conflict_type: ConflictType, description: str,
                        involved_users: List[str], affected_resources: List[str],
                        severity: str = "medium") -> str:
        """Create a new conflict"""
        conflict_id = str(uuid.uuid4())
        
        conflict = Conflict(
            conflict_id=conflict_id,
            conflict_type=conflict_type,
            description=description,
            involved_users=involved_users,
            affected_resources=affected_resources,
            created_at=time.time(),
            resolved_at=None,
            resolution=None,
            resolved_by=None,
            severity=severity
        )
        
        self.conflicts[conflict_id] = conflict
        
        # Auto-resolve if configured
        if self.config['conflict_resolution']['auto_resolve']:
            asyncio.create_task(self._auto_resolve_conflict(conflict_id))
        
        print(f"⚠️ Conflict created: {conflict_id} - {description}")
        return conflict_id
    
    async def _auto_resolve_conflict(self, conflict_id: str):
        """Attempt to auto-resolve conflict"""
        await asyncio.sleep(self.config['conflict_resolution']['escalation_threshold'])
        
        conflict = self.conflicts.get(conflict_id)
        if not conflict or conflict.resolved_at:
            return
        
        # Simple auto-resolution logic
        if conflict.conflict_type == ConflictType.RESOURCE_LOCK:
            # Check if lock has expired
            for resource in conflict.affected_resources:
                if resource in self.locks:
                    lock_info = self.locks[resource]
                    if lock_info['expires_at'] <= time.time():
                        # Lock expired, resolve conflict
                        self._resolve_conflict(conflict_id, "auto", "Lock expired automatically")
                        return
    
    def _resolve_conflict(self, conflict_id: str, resolved_by: str, resolution: str):
        """Resolve a conflict"""
        conflict = self.conflicts.get(conflict_id)
        if not conflict:
            return
        
        conflict.resolved_at = time.time()
        conflict.resolved_by = resolved_by
        conflict.resolution = resolution
        
        print(f"✅ Conflict resolved: {conflict_id} by {resolved_by}")
    
    def lock_resource(self, resource: str, user_id: str, duration: int = 300) -> bool:
        """Lock a resource for exclusive access"""
        current_time = time.time()
        
        # Check if resource is already locked
        if resource in self.locks:
            lock_info = self.locks[resource]
            if lock_info['expires_at'] > current_time and lock_info['locked_by'] != user_id:
                return False
        
        # Lock the resource
        self.locks[resource] = {
            'locked_by': user_id,
            'locked_at': current_time,
            'expires_at': current_time + duration
        }
        
        print(f"🔒 Resource locked: {resource} by {user_id}")
        return True
    
    def unlock_resource(self, resource: str, user_id: str) -> bool:
        """Unlock a resource"""
        if resource not in self.locks:
            return False
        
        lock_info = self.locks[resource]
        if lock_info['locked_by'] != user_id:
            return False
        
        del self.locks[resource]
        print(f"🔓 Resource unlocked: {resource} by {user_id}")
        return True
    
    def start_collaboration_session(self, task_id: str, initiator_id: str) -> str:
        """Start a collaboration session"""
        session_id = str(uuid.uuid4())
        
        session = CollaborationSession(
            session_id=session_id,
            task_id=task_id,
            participants=[initiator_id],
            started_at=time.time(),
            last_activity=time.time(),
            shared_resources=[],
            chat_messages=[],
            screen_shares=[],
            voice_enabled=False,
            video_enabled=False
        )
        
        self.active_sessions[session_id] = session
        self.user_sessions[initiator_id] = session_id
        
        print(f"👥 Collaboration session started: {session_id}")
        return session_id
    
    def join_collaboration_session(self, session_id: str, user_id: str) -> bool:
        """Join a collaboration session"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        
        # Check session capacity
        if len(session.participants) >= self.config['collaboration']['max_participants']:
            return False
        
        session.participants.append(user_id)
        session.last_activity = time.time()
        self.user_sessions[user_id] = session_id
        
        print(f"👥 User {user_id} joined session {session_id}")
        return True
    
    def leave_collaboration_session(self, user_id: str) -> bool:
        """Leave collaboration session"""
        if user_id not in self.user_sessions:
            return False
        
        session_id = self.user_sessions[user_id]
        session = self.active_sessions.get(session_id)
        
        if session:
            session.participants.remove(user_id)
            session.last_activity = time.time()
            
            # End session if no participants left
            if not session.participants:
                del self.active_sessions[session_id]
                print(f"👥 Session ended: {session_id}")
        
        del self.user_sessions[user_id]
        print(f"👥 User {user_id} left session")
        return True
    
    def send_chat_message(self, session_id: str, user_id: str, message: str) -> bool:
        """Send chat message in collaboration session"""
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        if user_id not in session.participants:
            return False
        
        chat_message = {
            'message_id': str(uuid.uuid4()),
            'user_id': user_id,
            'message': message,
            'timestamp': time.time()
        }
        
        session.chat_messages.append(chat_message)
        session.last_activity = time.time()
        
        print(f"💬 Chat message in session {session_id}: {user_id} - {message}")
        return True
    
    def get_user_tasks(self, user_id: str) -> List[TaskAssignment]:
        """Get tasks assigned to user"""
        user_tasks = []
        for assignment in self.task_assignments.values():
            if assignment.assigned_to == user_id:
                user_tasks.append(assignment)
        
        # Sort by priority and assignment time
        user_tasks.sort(key=lambda x: (-x.priority, x.assigned_at))
        return user_tasks
    
    def get_team_tasks(self, team_id: str) -> List[TaskAssignment]:
        """Get all tasks for team members"""
        if team_id not in self.teams:
            return []
        
        team = self.teams[team_id]
        team_tasks = []
        
        for assignment in self.task_assignments.values():
            if assignment.assigned_to in team.members:
                team_tasks.append(assignment)
        
        return team_tasks
    
    def get_active_conflicts(self) -> List[Conflict]:
        """Get all unresolved conflicts"""
        return [conflict for conflict in self.conflicts.values() if not conflict.resolved_at]
    
    def get_collaboration_statistics(self) -> Dict[str, Any]:
        """Get collaboration statistics"""
        total_users = len(self.users)
        total_teams = len(self.teams)
        total_tasks = len(self.task_assignments)
        active_sessions = len(self.active_sessions)
        active_conflicts = len(self.get_active_conflicts())
        
        # Task status breakdown
        task_status_counts = {}
        for assignment in self.task_assignments.values():
            status = assignment.status.value
            task_status_counts[status] = task_status_counts.get(status, 0) + 1
        
        # User activity
        active_users = len([user for user in self.users.values() 
                          if time.time() - user.last_active < 3600])  # Last hour
        
        return {
            'total_users': total_users,
            'total_teams': total_teams,
            'total_tasks': total_tasks,
            'active_sessions': active_sessions,
            'active_conflicts': active_conflicts,
            'active_users': active_users,
            'task_status_breakdown': task_status_counts,
            'user_roles': {
                role.value: len([u for u in self.users.values() if u.role == role])
                for role in UserRole
            }
        }
    
    async def cleanup_inactive_sessions(self):
        """Cleanup inactive collaboration sessions"""
        current_time = time.time()
        max_duration = self.config['collaboration']['max_session_duration']
        
        sessions_to_remove = []
        for session_id, session in self.active_sessions.items():
            if current_time - session.last_activity > max_duration:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            session = self.active_sessions[session_id]
            
            # Remove users from session
            for user_id in session.participants:
                if user_id in self.user_sessions:
                    del self.user_sessions[user_id]
            
            del self.active_sessions[session_id]
            print(f"🧹 Cleaned up inactive session: {session_id}")
    
    async def start_team_manager(self):
        """Start team manager service"""
        if self.running:
            return
        
        self.running = True
        print("👥 Team Manager started")
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_task())
    
    async def stop_team_manager(self):
        """Stop team manager service"""
        self.running = False
        print("🛑 Team Manager stopped")
    
    async def _cleanup_task(self):
        """Background cleanup task"""
        while self.running:
            try:
                await asyncio.sleep(300)  # 5 minutes
                await self.cleanup_inactive_sessions()
            except Exception as e:
                print(f"⚠️ Cleanup task error: {e}")

# Global team manager instance
team_manager = TeamManager()

# Convenience functions
def create_user(username: str, email: str, full_name: str, role: UserRole) -> str:
    """Create a new user"""
    return team_manager.create_user(username, email, full_name, role, "")

def assign_task(task_id: str, assigned_to: str, assigned_by: str) -> bool:
    """Assign task to user"""
    return team_manager.assign_task(task_id, assigned_to, assigned_by)

def get_user_tasks(user_id: str) -> List[TaskAssignment]:
    """Get tasks for user"""
    return team_manager.get_user_tasks(user_id)

def start_collaboration(task_id: str, user_id: str) -> str:
    """Start collaboration session"""
    return team_manager.start_collaboration_session(task_id, user_id)

if __name__ == "__main__":
    async def main():
        # Example usage
        manager = TeamManager()
        await manager.start_team_manager()
        
        # Create users
        admin_id = manager.create_user("admin", "admin@example.com", "Admin User", UserRole.ADMIN)
        dev_id = manager.create_user("developer", "dev@example.com", "Developer", UserRole.DEVELOPER)
        
        # Create team
        team_id = manager.create_team("Development Team", "Main development team", admin_id)
        manager.add_user_to_team(team_id, dev_id, UserRole.DEVELOPER)
        
        # Assign task
        manager.assign_task("task_123", dev_id, admin_id)
        
        # Start collaboration
        session_id = manager.start_collaboration_session("task_123", dev_id)
        manager.join_collaboration_session(session_id, admin_id)
        
        # Send chat message
        manager.send_chat_message(session_id, dev_id, "Working on the task now")
        
        # Get statistics
        stats = manager.get_collaboration_statistics()
        print(f"Collaboration statistics: {stats}")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await manager.stop_team_manager()
    
    asyncio.run(main())
