#!/usr/bin/env python3
"""
CI Check: Ensure protected files are not deleted/renamed
"""

import os
import sys
import yaml
from pathlib import Path

def load_file_protection_policy():
    """Load file protection policy"""
    policy_path = Path("policies/FILE_PROTECTION.yaml")
    if not policy_path.exists():
        print("❌ FILE_PROTECTION.yaml not found")
        return None
    
    try:
        with open(policy_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error loading policy: {e}")
        return None

def check_protected_files():
    """Check if protected files exist"""
    policy = load_file_protection_policy()
    if not policy:
        return False
    
    protected_files = policy.get("protected_files", [])
    if not protected_files:
        print("⚠️ No protected files defined in policy")
        return True
    
    print(f"🔍 Checking {len(protected_files)} protected files...")
    
    missing_files = []
    for file_path in protected_files:
        if os.path.exists(file_path):
            print(f"  ✅ {file_path} exists")
        else:
            print(f"  ❌ {file_path} missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ {len(missing_files)} protected files are missing:")
        for file in missing_files:
            print(f"  - {file}")
        print("\n💡 Protected files should not be deleted or renamed")
        return False
    else:
        print(f"\n✅ All {len(protected_files)} protected files exist!")
        return True

def check_env_example():
    """Check if .env.example exists"""
    if os.path.exists(".env.example"):
        print("✅ .env.example exists")
        return True
    else:
        print("❌ .env.example missing")
        print("💡 Create .env.example as a template for environment variables")
        return False

def main():
    """Main CI check function"""
    print("🔍 Checking protected files...")
    
    # Check protected files
    protected_ok = check_protected_files()
    
    # Check .env.example
    env_example_ok = check_env_example()
    
    if protected_ok and env_example_ok:
        print("\n✅ All file protection checks passed!")
        return 0
    else:
        print("\n❌ File protection checks failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())