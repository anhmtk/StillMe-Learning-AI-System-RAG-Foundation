#!/usr/bin/env python3
"""
Policy Loader for StillMe Framework
Tải và validate các policy files
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class PolicyLoader:
    """Load and validate policy files"""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent.parent
        self.policies = {}
        self.logger = logging.getLogger(__name__)

    def load_all_policies(self) -> Dict[str, Any]:
        """Load all policy files"""
        policy_files = [
            "policies/FILE_PROTECTION.yaml",
            "policies/SECURITY_POLICY.yaml",
            "policies/CODE_QUALITY.yaml",
            "policies/INTERACTION_POLICY.yaml"
        ]

        for policy_file in policy_files:
            try:
                policy_path = self.base_path / policy_file
                if policy_path.exists():
                    with open(policy_path, encoding='utf-8') as f:
                        policy_data = yaml.safe_load(f)
                        policy_name = policy_path.stem
                        self.policies[policy_name] = policy_data
                        self.logger.info(f"✅ Loaded policy: {policy_name}")
                else:
                    self.logger.warning(f"⚠️ Policy file not found: {policy_file}")
            except Exception as e:
                self.logger.error(f"❌ Failed to load policy {policy_file}: {e}")
                raise

        return self.policies

    def validate_policies(self) -> bool:
        """Validate loaded policies"""
        required_policies = ["FILE_PROTECTION", "SECURITY_POLICY", "CODE_QUALITY"]

        for policy_name in required_policies:
            if policy_name not in self.policies:
                self.logger.error(f"❌ Required policy missing: {policy_name}")
                return False

            # Basic validation
            policy = self.policies[policy_name]
            if "version" not in policy:
                self.logger.error(f"❌ Policy {policy_name} missing version")
                return False

        self.logger.info("✅ All policies validated successfully")
        return True

    def get_policy(self, policy_name: str) -> Optional[Dict[str, Any]]:
        """Get specific policy"""
        return self.policies.get(policy_name)

    def check_file_protection(self, file_path: str) -> bool:
        """Check if file is protected"""
        file_protection = self.get_policy("FILE_PROTECTION")
        if not file_protection:
            return False

        protected_files = file_protection.get("protected_files", [])
        return file_path in protected_files

    def check_security_policy(self, action: str, context: Dict[str, Any]) -> bool:
        """Check security policy compliance"""
        security_policy = self.get_policy("SECURITY_POLICY")
        if not security_policy:
            return False

        # Implement security checks based on policy
        # This is a simplified version
        return True

    def get_code_quality_rules(self) -> Dict[str, Any]:
        """Get code quality rules"""
        return self.get_policy("CODE_QUALITY") or {}

# Global policy loader instance
_policy_loader = None

def load_policies() -> PolicyLoader:
    """Load all policies (singleton pattern)"""
    global _policy_loader
    if _policy_loader is None:
        _policy_loader = PolicyLoader()
        _policy_loader.load_all_policies()
        if not _policy_loader.validate_policies():
            raise RuntimeError("Policy validation failed")
    return _policy_loader

def get_policy(policy_name: str) -> Optional[Dict[str, Any]]:
    """Get specific policy"""
    loader = load_policies()
    return loader.get_policy(policy_name)

def check_file_protection(file_path: str) -> bool:
    """Check if file is protected"""
    loader = load_policies()
    return loader.check_file_protection(file_path)

def check_security_policy(action: str, context: Dict[str, Any]) -> bool:
    """Check security policy compliance"""
    loader = load_policies()
    return loader.check_security_policy(action, context)

# Test function
if __name__ == "__main__":
    try:
        loader = load_policies()
        print("✅ Policies loaded successfully")
        print(f"Loaded policies: {list(loader.policies.keys())}")

        # Test file protection
        is_protected = check_file_protection(".env")
        print(f".env is protected: {is_protected}")

    except Exception as e:
        print(f"❌ Policy loading failed: {e}")
        exit(1)
