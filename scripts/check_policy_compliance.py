#!/usr/bin/env python3
"""
Policy compliance check script for NicheRadar v1.5
Ensures all required policies are loaded and enforced
"""

import os
import sys
import yaml
from pathlib import Path

def check_policy_files():
    """Check if required policy files exist"""
    required_policies = [
        "policies/network_allowlist.yaml",
        "policies/niche_weights.yaml",
        "policies/niche_radar_security.yaml",
        "config/staging.yaml"
    ]

    missing_policies = []
    for policy_file in required_policies:
        if not Path(policy_file).exists():
            missing_policies.append(policy_file)

    if missing_policies:
        print(f"❌ Missing policy files: {', '.join(missing_policies)}")
        return False

    print("✅ All required policy files exist")
    return True

def validate_policy_content():
    """Validate policy file content"""
    policies = {
        "policies/network_allowlist.yaml": ["allowed_domains", "security"],
        "policies/niche_weights.yaml": ["weights", "stillme_capabilities"],
        "policies/niche_radar_security.yaml": ["data_collection", "pii_protection", "tos_compliance"],
        "config/staging.yaml": ["web_search", "cache", "tool_gate"]
    }

    for policy_file, required_sections in policies.items():
        try:
            with open(policy_file, 'r') as f:
                content = yaml.safe_load(f)

            for section in required_sections:
                if section not in content:
                    print(f"❌ Missing section '{section}' in {policy_file}")
                    return False

            print(f"✅ {policy_file} content is valid")

        except yaml.YAMLError as e:
            print(f"❌ Invalid YAML in {policy_file}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error reading {policy_file}: {e}")
            return False

    return True

def check_policy_loading():
    """Check if policies are properly loaded in code"""
    # Check if policy loading is implemented in key files
    key_files = [
        "app.py",
        "niche_radar/collectors.py",
        "niche_radar/scoring.py",
        "policy/tool_gate.py"
    ]

    for file_path in key_files:
        if not Path(file_path).exists():
            print(f"⚠️ Key file not found: {file_path}")
            continue

        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Check for policy loading patterns
            if "load_interaction_policy" in content or "load_file_policy" in content:
                print(f"✅ {file_path} includes policy loading")
            else:
                print(f"⚠️ {file_path} may not include policy loading")

        except Exception as e:
            print(f"❌ Error reading {file_path}: {e}")
            return False

    return True

def check_security_compliance():
    """Check security compliance"""
    security_checks = [
        ("policies/network_allowlist.yaml", "require_https", True),
        ("policies/niche_radar_security.yaml", "pii_protection", True),
        ("policies/niche_radar_security.yaml", "tos_compliance", True)
    ]

    for file_path, setting, expected_value in security_checks:
        try:
            with open(file_path, 'r') as f:
                content = yaml.safe_load(f)

            # Navigate to the setting
            if setting in content:
                actual_value = content[setting]
                if actual_value == expected_value:
                    print(f"✅ {file_path}: {setting} = {actual_value}")
                else:
                    print(f"❌ {file_path}: {setting} = {actual_value} (expected {expected_value})")
                    return False
            else:
                print(f"❌ {file_path}: Missing setting {setting}")
                return False

        except Exception as e:
            print(f"❌ Error checking {file_path}: {e}")
            return False

    return True

def main():
    """Main compliance check function"""
    print("🔍 Checking policy compliance...")

    checks = [
        ("Policy Files", check_policy_files),
        ("Policy Content", validate_policy_content),
        ("Policy Loading", check_policy_loading),
        ("Security Compliance", check_security_compliance)
    ]

    all_passed = True
    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        if not check_func():
            all_passed = False

    if all_passed:
        print("\n✅ All policy compliance checks passed!")
        return 0
    else:
        print("\n❌ Some policy compliance checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
