#!/usr/bin/env python3
"""
AgentDev Security Policy Gate - SEAL-GRADE
Enterprise-grade security enforcement for tool execution
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union
import yaml
import hashlib
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security levels for operations"""
    SAFE = "safe"           # Read-only, no side effects
    LOW = "low"             # Minimal side effects
    MEDIUM = "medium"       # Moderate side effects
    HIGH = "high"           # Significant side effects
    CRITICAL = "critical"   # Dangerous operations

class ApprovalStatus(Enum):
    """Approval status for operations"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"

@dataclass
class ToolPolicy:
    """Policy definition for a tool"""
    tool_name: str
    allowed: bool
    security_level: SecurityLevel
    requires_approval: bool
    max_executions_per_hour: int
    allowed_parameters: List[str]
    forbidden_parameters: List[str]
    parameter_constraints: Dict[str, Any]
    dry_run_only: bool = False
    description: str = ""

@dataclass
class ExecutionRequest:
    """Request for tool execution"""
    request_id: str
    tool_name: str
    parameters: Dict[str, Any]
    user_id: str
    session_id: str
    timestamp: float
    security_level: SecurityLevel
    requires_approval: bool
    dry_run: bool = False

@dataclass
class ApprovalDecision:
    """Decision made by policy gate"""
    request_id: str
    approved: bool
    status: ApprovalStatus
    reason: str
    constraints: Dict[str, Any]
    timestamp: float
    approved_by: Optional[str] = None
    expires_at: Optional[float] = None

class PolicyGate:
    """
    SEAL-GRADE Security Policy Gate
    
    Enforces strict security policies for all tool executions:
    - Tool allowlist/blocklist
    - Parameter validation
    - Rate limiting
    - Approval workflows
    - Dry-run enforcement
    - Audit logging
    """
    
    def __init__(self, policy_file: str = "agentdev/policy/security_policy.yaml"):
        self.policy_file = Path(policy_file)
        self.policies: Dict[str, ToolPolicy] = {}
        self.approval_queue: Dict[str, ExecutionRequest] = {}
        self.execution_history: List[ExecutionRequest] = []
        self.rate_limits: Dict[str, List[float]] = {}  # tool_name -> timestamps
        self.blocked_requests: Set[str] = set()
        
        # Load policies
        self._load_policies()
        
        # Security patterns
        self.dangerous_patterns = [
            r"rm\s+-rf",           # Dangerous file deletion
            r"sudo\s+",            # Privilege escalation
            r"chmod\s+777",        # Overly permissive permissions
            r"eval\s*\(",          # Code evaluation
            r"exec\s*\(",          # Code execution
            r"subprocess",         # Process spawning
            r"os\.system",         # System calls
            r"shell=True",         # Shell injection
            r"password\s*=",       # Password exposure
            r"secret\s*=",         # Secret exposure
            r"token\s*=",          # Token exposure
            r"key\s*=",            # Key exposure
        ]
        
        logger.info("🔒 Policy Gate initialized with SEAL-GRADE security")
    
    def _load_policies(self):
        """Load security policies from YAML file"""
        if not self.policy_file.exists():
            self._create_default_policies()
            return
        
        try:
            with open(self.policy_file, 'r', encoding='utf-8') as f:
                policy_data = yaml.safe_load(f)
            
            for tool_name, policy_config in policy_data.get('tools', {}).items():
                self.policies[tool_name] = ToolPolicy(
                    tool_name=tool_name,
                    allowed=policy_config.get('allowed', False),
                    security_level=SecurityLevel(policy_config.get('security_level', 'safe')),
                    requires_approval=policy_config.get('requires_approval', False),
                    max_executions_per_hour=policy_config.get('max_executions_per_hour', 10),
                    allowed_parameters=policy_config.get('allowed_parameters', []),
                    forbidden_parameters=policy_config.get('forbidden_parameters', []),
                    parameter_constraints=policy_config.get('parameter_constraints', {}),
                    dry_run_only=policy_config.get('dry_run_only', False),
                    description=policy_config.get('description', '')
                )
            
            logger.info(f"✅ Loaded {len(self.policies)} security policies")
            
        except Exception as e:
            logger.error(f"❌ Failed to load policies: {e}")
            self._create_default_policies()
    
    def _create_default_policies(self):
        """Create default security policies"""
        default_policies = {
            "file_read": ToolPolicy(
                tool_name="file_read",
                allowed=True,
                security_level=SecurityLevel.SAFE,
                requires_approval=False,
                max_executions_per_hour=100,
                allowed_parameters=["path", "encoding"],
                forbidden_parameters=[],
                parameter_constraints={"path": {"type": "string", "max_length": 1000}},
                description="Read file contents"
            ),
            "file_write": ToolPolicy(
                tool_name="file_write",
                allowed=True,
                security_level=SecurityLevel.MEDIUM,
                requires_approval=True,
                max_executions_per_hour=20,
                allowed_parameters=["path", "content", "encoding"],
                forbidden_parameters=["password", "secret", "token"],
                parameter_constraints={"path": {"type": "string", "max_length": 1000}},
                description="Write file contents"
            ),
            "command_execute": ToolPolicy(
                tool_name="command_execute",
                allowed=False,  # Blocked by default
                security_level=SecurityLevel.CRITICAL,
                requires_approval=True,
                max_executions_per_hour=1,
                allowed_parameters=["command"],
                forbidden_parameters=[],
                parameter_constraints={},
                dry_run_only=True,
                description="Execute system commands"
            ),
            "http_request": ToolPolicy(
                tool_name="http_request",
                allowed=True,
                security_level=SecurityLevel.MEDIUM,
                requires_approval=False,
                max_executions_per_hour=50,
                allowed_parameters=["url", "method", "headers", "data"],
                forbidden_parameters=["password", "secret", "token", "key"],
                parameter_constraints={"url": {"type": "string", "max_length": 2000}},
                description="Make HTTP requests"
            )
        }
        
        self.policies = default_policies
        self._save_policies()
        logger.info("✅ Created default security policies")
    
    def _save_policies(self):
        """Save policies to YAML file"""
        try:
            policy_data = {
                'tools': {
                    tool_name: {
                        'allowed': policy.allowed,
                        'security_level': policy.security_level.value,
                        'requires_approval': policy.requires_approval,
                        'max_executions_per_hour': policy.max_executions_per_hour,
                        'allowed_parameters': policy.allowed_parameters,
                        'forbidden_parameters': policy.forbidden_parameters,
                        'parameter_constraints': policy.parameter_constraints,
                        'dry_run_only': policy.dry_run_only,
                        'description': policy.description
                    }
                    for tool_name, policy in self.policies.items()
                }
            }
            
            with open(self.policy_file, 'w', encoding='utf-8') as f:
                yaml.dump(policy_data, f, default_flow_style=False, indent=2)
                
        except Exception as e:
            logger.error(f"❌ Failed to save policies: {e}")
    
    async def validate_request(self, tool_name: str, parameters: Dict[str, Any], 
                             user_id: str, session_id: str, dry_run: bool = False) -> ApprovalDecision:
        """
        Validate and approve/reject tool execution request
        
        SEAL-GRADE validation includes:
        - Tool allowlist check
        - Parameter validation
        - Rate limiting
        - Security pattern detection
        - Approval workflow
        """
        request_id = str(uuid.uuid4())
        timestamp = time.time()
        
        # Create execution request
        request = ExecutionRequest(
            request_id=request_id,
            tool_name=tool_name,
            parameters=parameters,
            user_id=user_id,
            session_id=session_id,
            timestamp=timestamp,
            security_level=SecurityLevel.SAFE,
            requires_approval=False,
            dry_run=dry_run
        )
        
        # Get tool policy
        policy = self.policies.get(tool_name)
        if not policy:
            return ApprovalDecision(
                request_id=request_id,
                approved=False,
                status=ApprovalStatus.REJECTED,
                reason=f"Tool '{tool_name}' not found in policy",
                constraints={},
                timestamp=timestamp
            )
        
        # Update request with policy info
        request.security_level = policy.security_level
        request.requires_approval = policy.requires_approval
        
        # 1. Tool allowlist check
        if not policy.allowed:
            return ApprovalDecision(
                request_id=request_id,
                approved=False,
                status=ApprovalStatus.REJECTED,
                reason=f"Tool '{tool_name}' is blocked by policy",
                constraints={},
                timestamp=timestamp
            )
        
        # 2. Dry-run enforcement
        if policy.dry_run_only and not dry_run:
            return ApprovalDecision(
                request_id=request_id,
                approved=False,
                status=ApprovalStatus.REJECTED,
                reason=f"Tool '{tool_name}' requires dry-run mode",
                constraints={"dry_run_required": True},
                timestamp=timestamp
            )
        
        # 3. Rate limiting check
        if not await self._check_rate_limit(tool_name, policy.max_executions_per_hour):
            return ApprovalDecision(
                request_id=request_id,
                approved=False,
                status=ApprovalStatus.REJECTED,
                reason=f"Rate limit exceeded for tool '{tool_name}'",
                constraints={"rate_limit": policy.max_executions_per_hour},
                timestamp=timestamp
            )
        
        # 4. Parameter validation
        param_validation = await self._validate_parameters(parameters, policy)
        if not param_validation["valid"]:
            return ApprovalDecision(
                request_id=request_id,
                approved=False,
                status=ApprovalStatus.REJECTED,
                reason=f"Parameter validation failed: {param_validation['reason']}",
                constraints=param_validation.get("constraints", {}),
                timestamp=timestamp
            )
        
        # 5. Security pattern detection
        security_check = await self._check_security_patterns(parameters)
        if not security_check["safe"]:
            return ApprovalDecision(
                request_id=request_id,
                approved=False,
                status=ApprovalStatus.REJECTED,
                reason=f"Security pattern detected: {security_check['reason']}",
                constraints={"security_violation": True},
                timestamp=timestamp
            )
        
        # 6. Approval workflow
        if policy.requires_approval and not dry_run:
            self.approval_queue[request_id] = request
            return ApprovalDecision(
                request_id=request_id,
                approved=False,
                status=ApprovalStatus.PENDING,
                reason=f"Tool '{tool_name}' requires manual approval",
                constraints={"approval_required": True},
                timestamp=timestamp
            )
        
        # 7. Auto-approve safe operations
        if policy.security_level in [SecurityLevel.SAFE, SecurityLevel.LOW]:
            self._record_execution(request)
            return ApprovalDecision(
                request_id=request_id,
                approved=True,
                status=ApprovalStatus.AUTO_APPROVED,
                reason=f"Auto-approved safe operation",
                constraints={},
                timestamp=timestamp
            )
        
        # 8. Default approval for medium/high risk
        self._record_execution(request)
        return ApprovalDecision(
            request_id=request_id,
            approved=True,
            status=ApprovalStatus.APPROVED,
            reason=f"Approved {policy.security_level.value} risk operation",
            constraints={},
            timestamp=timestamp
        )
    
    async def _check_rate_limit(self, tool_name: str, max_per_hour: int) -> bool:
        """Check if tool execution is within rate limits"""
        now = time.time()
        hour_ago = now - 3600
        
        # Clean old timestamps
        if tool_name in self.rate_limits:
            self.rate_limits[tool_name] = [
                ts for ts in self.rate_limits[tool_name] if ts > hour_ago
            ]
        else:
            self.rate_limits[tool_name] = []
        
        # Check limit
        if len(self.rate_limits[tool_name]) >= max_per_hour:
            return False
        
        # Add current execution
        self.rate_limits[tool_name].append(now)
        return True
    
    async def _validate_parameters(self, parameters: Dict[str, Any], 
                                 policy: ToolPolicy) -> Dict[str, Any]:
        """Validate parameters against policy constraints"""
        # Check forbidden parameters
        for param_name in parameters.keys():
            if param_name in policy.forbidden_parameters:
                return {
                    "valid": False,
                    "reason": f"Forbidden parameter: {param_name}",
                    "constraints": {"forbidden_param": param_name}
                }
        
        # Check allowed parameters (if specified)
        if policy.allowed_parameters:
            for param_name in parameters.keys():
                if param_name not in policy.allowed_parameters:
                    return {
                        "valid": False,
                        "reason": f"Parameter not allowed: {param_name}",
                        "constraints": {"disallowed_param": param_name}
                    }
        
        # Check parameter constraints
        for param_name, constraints in policy.parameter_constraints.items():
            if param_name in parameters:
                value = parameters[param_name]
                
                # Type check
                if "type" in constraints:
                    expected_type = constraints["type"]
                    if expected_type == "string" and not isinstance(value, str):
                        return {
                            "valid": False,
                            "reason": f"Parameter '{param_name}' must be string",
                            "constraints": {"type_mismatch": param_name}
                        }
                
                # Length check
                if "max_length" in constraints and isinstance(value, str):
                    if len(value) > constraints["max_length"]:
                        return {
                            "valid": False,
                            "reason": f"Parameter '{param_name}' too long",
                            "constraints": {"length_exceeded": param_name}
                        }
        
        return {"valid": True}
    
    async def _check_security_patterns(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check for dangerous security patterns in parameters"""
        param_str = json.dumps(parameters, default=str).lower()
        
        for pattern in self.dangerous_patterns:
            if re.search(pattern, param_str):
                return {
                    "safe": False,
                    "reason": f"Dangerous pattern detected: {pattern}",
                    "pattern": pattern
                }
        
        return {"safe": True}
    
    def _record_execution(self, request: ExecutionRequest):
        """Record execution in history"""
        self.execution_history.append(request)
        
        # Keep only last 1000 executions
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
    
    async def approve_request(self, request_id: str, approved_by: str, 
                            reason: str = "") -> bool:
        """Manually approve a pending request"""
        if request_id not in self.approval_queue:
            return False
        
        request = self.approval_queue[request_id]
        del self.approval_queue[request_id]
        
        # Record approval
        self._record_execution(request)
        
        logger.info(f"✅ Request {request_id} approved by {approved_by}: {reason}")
        return True
    
    async def reject_request(self, request_id: str, rejected_by: str, 
                           reason: str = "") -> bool:
        """Manually reject a pending request"""
        if request_id not in self.approval_queue:
            return False
        
        request = self.approval_queue[request_id]
        del self.approval_queue[request_id]
        
        self.blocked_requests.add(request_id)
        
        logger.warning(f"❌ Request {request_id} rejected by {rejected_by}: {reason}")
        return True
    
    def get_pending_requests(self) -> List[ExecutionRequest]:
        """Get all pending approval requests"""
        return list(self.approval_queue.values())
    
    def get_execution_history(self, limit: int = 100) -> List[ExecutionRequest]:
        """Get recent execution history"""
        return self.execution_history[-limit:]
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        total_requests = len(self.execution_history)
        pending_requests = len(self.approval_queue)
        blocked_requests = len(self.blocked_requests)
        
        # Count by security level
        level_counts = {}
        for request in self.execution_history:
            level = request.security_level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            "total_executions": total_requests,
            "pending_approvals": pending_requests,
            "blocked_requests": blocked_requests,
            "executions_by_level": level_counts,
            "rate_limits": {
                tool: len(timestamps) 
                for tool, timestamps in self.rate_limits.items()
            }
        }

# Global policy gate instance
policy_gate = PolicyGate()

# Convenience functions
async def validate_tool_request(tool_name: str, parameters: Dict[str, Any], 
                              user_id: str, session_id: str, dry_run: bool = False) -> ApprovalDecision:
    """Validate tool execution request"""
    return await policy_gate.validate_request(tool_name, parameters, user_id, session_id, dry_run)

async def approve_tool_request(request_id: str, approved_by: str, reason: str = "") -> bool:
    """Approve tool execution request"""
    return await policy_gate.approve_request(request_id, approved_by, reason)

async def reject_tool_request(request_id: str, rejected_by: str, reason: str = "") -> bool:
    """Reject tool execution request"""
    return await policy_gate.reject_request(request_id, rejected_by, reason)

def get_security_stats() -> Dict[str, Any]:
    """Get security statistics"""
    return policy_gate.get_security_stats()
