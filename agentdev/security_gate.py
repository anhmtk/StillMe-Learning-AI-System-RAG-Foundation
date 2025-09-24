#!/usr/bin/env python3
"""
AgentDev Security Gate - SEAL-grade Tool & Parameter Validation
Enforces tool allowlist, parameter validation, and approval workflow.
"""

import yaml
import re
import json
import time
import uuid
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class ApprovalStatus(Enum):
    AUTO_APPROVED = "auto_approved"
    PENDING_APPROVAL = "pending_approval"
    MANUALLY_APPROVED = "manually_approved"
    REJECTED = "rejected"
    TIMED_OUT = "timed_out"

@dataclass
class ToolCall:
    """Tool call request structure"""
    tool_name: str
    parameters: Dict[str, Any]
    call_id: str
    user_id: str
    job_id: Optional[str] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.call_id is None:
            self.call_id = f"call_{uuid.uuid4().hex[:8]}"

@dataclass
class ValidationResult:
    """Tool validation result"""
    allowed: bool
    risk_level: RiskLevel
    requires_approval: bool
    approval_status: ApprovalStatus
    sanitized_parameters: Dict[str, Any]
    violations: List[str]
    call_id: str
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

class SecurityGate:
    """SEAL-grade security gate for tool validation"""
    
    def __init__(self, policy_path: str = None):
        self.policy_path = policy_path or Path(__file__).parent / "policy" / "tool_allowlist.yaml"
        self.policy = self._load_policy()
        self.pending_approvals: Dict[str, ToolCall] = {}
        self.approval_history: List[ValidationResult] = []
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_policy(self) -> Dict[str, Any]:
        """Load tool allowlist policy"""
        try:
            with open(self.policy_path, 'r', encoding='utf-8') as f:
                policy = yaml.safe_load(f)
            self.logger.info(f"✅ Security policy loaded: {self.policy_path}")
            return policy
        except FileNotFoundError:
            self.logger.error(f"❌ Policy file not found: {self.policy_path}")
            return {"allowed_tools": {}, "blocked_tools": []}
        except yaml.YAMLError as e:
            self.logger.error(f"❌ Policy file invalid YAML: {e}")
            return {"allowed_tools": {}, "blocked_tools": []}
    
    def validate_tool_call(self, tool_call: ToolCall) -> ValidationResult:
        """Validate a tool call against policy"""
        violations = []
        
        # Check if tool is blocked
        if tool_call.tool_name in self.policy.get("blocked_tools", []):
            violations.append(f"Tool '{tool_call.tool_name}' is explicitly blocked")
            return ValidationResult(
                allowed=False,
                risk_level=RiskLevel.HIGH,
                requires_approval=False,
                approval_status=ApprovalStatus.REJECTED,
                sanitized_parameters={},
                violations=violations,
                call_id=tool_call.call_id
            )
        
        # Check if tool is allowed
        allowed_tools = self.policy.get("allowed_tools", {})
        if tool_call.tool_name not in allowed_tools:
            violations.append(f"Tool '{tool_call.tool_name}' is not in allowlist")
            return ValidationResult(
                allowed=False,
                risk_level=RiskLevel.HIGH,
                requires_approval=False,
                approval_status=ApprovalStatus.REJECTED,
                sanitized_parameters={},
                violations=violations,
                call_id=tool_call.call_id
            )
        
        tool_config = allowed_tools[tool_call.tool_name]
        category = tool_config.get("category", "unknown")
        
        # Get category config
        categories = self.policy.get("tool_categories", {})
        category_config = categories.get(category, {})
        risk_level = RiskLevel(category_config.get("risk_level", "high"))
        requires_approval = category_config.get("requires_approval", True)
        
        # Validate and sanitize parameters
        sanitized_params, param_violations = self._validate_parameters(
            tool_call.tool_name, tool_call.parameters, tool_config
        )
        violations.extend(param_violations)
        
        # Determine approval status
        if violations:
            approval_status = ApprovalStatus.REJECTED
            allowed = False
        elif requires_approval:
            approval_status = ApprovalStatus.PENDING_APPROVAL
            allowed = False
            self.pending_approvals[tool_call.call_id] = tool_call
        else:
            approval_status = ApprovalStatus.AUTO_APPROVED
            allowed = True
        
        result = ValidationResult(
            allowed=allowed,
            risk_level=risk_level,
            requires_approval=requires_approval,
            approval_status=approval_status,
            sanitized_parameters=sanitized_params,
            violations=violations,
            call_id=tool_call.call_id
        )
        
        # Log the validation
        self._log_validation(tool_call, result)
        
        return result
    
    def _validate_parameters(self, tool_name: str, params: Dict[str, Any], 
                           tool_config: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """Validate and sanitize tool parameters"""
        violations = []
        sanitized = {}
        
        valid_params = tool_config.get("valid_parameters", {})
        
        # Check all provided parameters are valid
        for param_name, param_value in params.items():
            if param_name not in valid_params:
                violations.append(f"Unknown parameter '{param_name}' for tool '{tool_name}'")
                continue
            
            param_config = valid_params[param_name]
            sanitized_value, param_violations = self._validate_parameter(
                param_name, param_value, param_config
            )
            
            if param_violations:
                violations.extend(param_violations)
            else:
                sanitized[param_name] = sanitized_value
        
        # Check all required parameters are provided
        for param_name, param_config in valid_params.items():
            if param_config.get("required", False) and param_name not in params:
                violations.append(f"Required parameter '{param_name}' missing for tool '{tool_name}'")
        
        return sanitized, violations
    
    def _validate_parameter(self, name: str, value: Any, config: Dict[str, Any]) -> Tuple[Any, List[str]]:
        """Validate a single parameter"""
        violations = []
        sanitized_value = value
        
        param_type = config.get("type", "string")
        
        # Type validation
        if param_type == "string" and not isinstance(value, str):
            violations.append(f"Parameter '{name}' must be string, got {type(value).__name__}")
            return value, violations
        elif param_type == "integer" and not isinstance(value, int):
            violations.append(f"Parameter '{name}' must be integer, got {type(value).__name__}")
            return value, violations
        elif param_type == "boolean" and not isinstance(value, bool):
            violations.append(f"Parameter '{name}' must be boolean, got {type(value).__name__}")
            return value, violations
        elif param_type == "array" and not isinstance(value, list):
            violations.append(f"Parameter '{name}' must be array, got {type(value).__name__}")
            return value, violations
        
        # String-specific validation
        if param_type == "string" and isinstance(value, str):
            # Sanitization
            if self.policy.get("sanitization", {}).get("remove_null_bytes", True):
                sanitized_value = value.replace('\x00', '')
            
            if self.policy.get("sanitization", {}).get("unicode_normalization", True):
                import unicodedata
                sanitized_value = unicodedata.normalize('NFKC', sanitized_value)
            
            # Length validation
            max_length = config.get("max_length")
            if max_length and len(sanitized_value) > max_length:
                violations.append(f"Parameter '{name}' exceeds max length {max_length}")
            
            # Pattern validation
            pattern = config.get("pattern")
            if pattern and not re.match(pattern, sanitized_value):
                violations.append(f"Parameter '{name}' doesn't match required pattern")
            
            # Blacklist validation
            blacklist = config.get("blacklist", [])
            for blocked_pattern in blacklist:
                if blocked_pattern in sanitized_value:
                    violations.append(f"Parameter '{name}' contains blocked pattern: {blocked_pattern}")
            
            # Path traversal protection
            if self.policy.get("sanitization", {}).get("path_normalization", True):
                if "../" in sanitized_value or "..\\" in sanitized_value:
                    # Count depth
                    depth = sanitized_value.count("../") + sanitized_value.count("..\\")
                    max_depth = self.policy.get("sanitization", {}).get("max_depth_traversal", 10)
                    if depth > max_depth:
                        violations.append(f"Parameter '{name}' exceeds max path traversal depth")
        
        # Integer-specific validation
        elif param_type == "integer" and isinstance(value, int):
            min_val = config.get("min")
            max_val = config.get("max")
            
            if min_val is not None and value < min_val:
                violations.append(f"Parameter '{name}' below minimum value {min_val}")
            if max_val is not None and value > max_val:
                violations.append(f"Parameter '{name}' above maximum value {max_val}")
        
        # Array-specific validation
        elif param_type == "array" and isinstance(value, list):
            max_items = config.get("max_items")
            if max_items and len(value) > max_items:
                violations.append(f"Parameter '{name}' exceeds max items {max_items}")
        
        return sanitized_value, violations
    
    def approve_tool_call(self, call_id: str, approved_by: str) -> bool:
        """Manually approve a pending tool call"""
        if call_id not in self.pending_approvals:
            self.logger.warning(f"⚠️ Approval requested for unknown call: {call_id}")
            return False
        
        tool_call = self.pending_approvals.pop(call_id)
        
        # Create approval result
        result = ValidationResult(
            allowed=True,
            risk_level=RiskLevel.HIGH,
            requires_approval=True,
            approval_status=ApprovalStatus.MANUALLY_APPROVED,
            sanitized_parameters=tool_call.parameters,
            violations=[],
            call_id=call_id
        )
        
        self.approval_history.append(result)
        self.logger.info(f"✅ Tool call approved: {call_id} by {approved_by}")
        return True
    
    def reject_tool_call(self, call_id: str, rejected_by: str, reason: str) -> bool:
        """Manually reject a pending tool call"""
        if call_id not in self.pending_approvals:
            self.logger.warning(f"⚠️ Rejection requested for unknown call: {call_id}")
            return False
        
        tool_call = self.pending_approvals.pop(call_id)
        
        # Create rejection result
        result = ValidationResult(
            allowed=False,
            risk_level=RiskLevel.HIGH,
            requires_approval=True,
            approval_status=ApprovalStatus.REJECTED,
            sanitized_parameters={},
            violations=[f"Manually rejected: {reason}"],
            call_id=call_id
        )
        
        self.approval_history.append(result)
        self.logger.info(f"❌ Tool call rejected: {call_id} by {rejected_by} - {reason}")
        return True
    
    def cleanup_expired_approvals(self) -> int:
        """Clean up expired pending approvals"""
        timeout = self.policy.get("approval_workflow", {}).get("timeout_seconds", 300)
        current_time = time.time()
        expired_calls = []
        
        for call_id, tool_call in self.pending_approvals.items():
            if current_time - tool_call.timestamp > timeout:
                expired_calls.append(call_id)
        
        for call_id in expired_calls:
            tool_call = self.pending_approvals.pop(call_id)
            
            # Create timeout result
            result = ValidationResult(
                allowed=False,
                risk_level=RiskLevel.HIGH,
                requires_approval=True,
                approval_status=ApprovalStatus.TIMED_OUT,
                sanitized_parameters={},
                violations=["Approval request timed out"],
                call_id=call_id
            )
            
            self.approval_history.append(result)
            self.logger.warning(f"⏰ Tool call timed out: {call_id}")
        
        return len(expired_calls)
    
    def _log_validation(self, tool_call: ToolCall, result: ValidationResult):
        """Log validation result"""
        status_emoji = {
            ApprovalStatus.AUTO_APPROVED: "✅",
            ApprovalStatus.PENDING_APPROVAL: "⏳", 
            ApprovalStatus.MANUALLY_APPROVED: "👤✅",
            ApprovalStatus.REJECTED: "❌",
            ApprovalStatus.TIMED_OUT: "⏰❌"
        }
        
        emoji = status_emoji.get(result.approval_status, "❓")
        self.logger.info(f"{emoji} Tool validation: {tool_call.tool_name} -> {result.approval_status.value}")
        
        if result.violations:
            for violation in result.violations:
                self.logger.warning(f"🚫 Violation: {violation}")
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get list of pending approvals for UI display"""
        approvals = []
        for call_id, tool_call in self.pending_approvals.items():
            approvals.append({
                "call_id": call_id,
                "tool_name": tool_call.tool_name,
                "parameters": tool_call.parameters,
                "user_id": tool_call.user_id,
                "job_id": tool_call.job_id,
                "timestamp": tool_call.timestamp,
                "age_seconds": time.time() - tool_call.timestamp
            })
        return approvals
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """Get validation statistics"""
        total = len(self.approval_history)
        if total == 0:
            return {"total": 0}
        
        status_counts = {}
        risk_counts = {}
        
        for result in self.approval_history:
            status = result.approval_status.value
            risk = result.risk_level.value
            
            status_counts[status] = status_counts.get(status, 0) + 1
            risk_counts[risk] = risk_counts.get(risk, 0) + 1
        
        return {
            "total": total,
            "pending": len(self.pending_approvals),
            "status_breakdown": status_counts,
            "risk_breakdown": risk_counts,
            "approval_rate": status_counts.get("auto_approved", 0) / total * 100
        }

# Example usage and testing
if __name__ == "__main__":
    # Create security gate
    gate = SecurityGate()
    
    # Test cases
    test_cases = [
        # Allowed read-only tool
        ToolCall(
            tool_name="read_file",
            parameters={"target_file": "README.md"},
            user_id="test_user",
            call_id="test_1"
        ),
        
        # Blocked tool
        ToolCall(
            tool_name="delete_file", 
            parameters={"target_file": "important.txt"},
            user_id="test_user",
            call_id="test_2"
        ),
        
        # Dangerous tool requiring approval
        ToolCall(
            tool_name="run_terminal_cmd",
            parameters={"command": "ls -la", "is_background": False},
            user_id="test_user", 
            call_id="test_3"
        ),
        
        # Invalid parameters
        ToolCall(
            tool_name="read_file",
            parameters={"invalid_param": "value"},
            user_id="test_user",
            call_id="test_4"
        ),
        
        # Path traversal attempt
        ToolCall(
            tool_name="read_file",
            parameters={"target_file": "../../../etc/passwd"},
            user_id="test_user",
            call_id="test_5"
        )
    ]
    
    print("🔒 Security Gate Testing")
    print("=" * 50)
    
    for tool_call in test_cases:
        result = gate.validate_tool_call(tool_call)
        print(f"\nTool: {tool_call.tool_name}")
        print(f"Allowed: {result.allowed}")
        print(f"Status: {result.approval_status.value}")
        print(f"Risk: {result.risk_level.value}")
        if result.violations:
            print(f"Violations: {', '.join(result.violations)}")
    
    print(f"\n📊 Statistics:")
    stats = gate.get_validation_stats()
    print(json.dumps(stats, indent=2))
    
    print(f"\n⏳ Pending Approvals:")
    pending = gate.get_pending_approvals()
    for approval in pending:
        print(f"- {approval['call_id']}: {approval['tool_name']} (age: {approval['age_seconds']:.1f}s)")
