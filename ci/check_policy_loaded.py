#!/usr/bin/env python3
"""
CI Check: Ensure all entrypoints load policy_loader
"""

import os
import sys
import re
from pathlib import Path

def find_entrypoints():
    """Find all entrypoint files"""
    entrypoints = []
    
    # Python entrypoints
    python_files = [
        "app.py",
        "stillme_desktop_app.py", 
        "app_with_core.py",
        "stable_ai_server.py"
    ]
    
    for file in python_files:
        if os.path.exists(file):
            entrypoints.append(file)
    
    # Find other Python entrypoints
    for root, dirs, files in os.walk("."):
        # Skip certain directories
        if any(skip in root for skip in ["node_modules", ".git", "__pycache__", ".venv"]):
            continue
            
        for file in files:
            if file.endswith(".py") and file in ["main.py", "app.py", "server.py", "cli.py"]:
                entrypoints.append(os.path.join(root, file))
    
    return entrypoints

def check_policy_loading(file_path):
    """Check if file loads policy_loader"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for policy_loader import
        if "policy_loader" in content or "load_policies" in content:
            return True, "Policy loader found"
        else:
            return False, "Policy loader not found"
            
    except Exception as e:
        return False, f"Error reading file: {e}"

def main():
    """Main CI check function"""
    print("🔍 Checking policy loading in entrypoints...")
    
    entrypoints = find_entrypoints()
    if not entrypoints:
        print("❌ No entrypoints found")
        return 1
    
    print(f"Found {len(entrypoints)} entrypoints:")
    for ep in entrypoints:
        print(f"  - {ep}")
    
    failed_checks = []
    
    for entrypoint in entrypoints:
        print(f"\n🔍 Checking {entrypoint}...")
        has_policy, message = check_policy_loading(entrypoint)
        
        if has_policy:
            print(f"  ✅ {message}")
        else:
            print(f"  ❌ {message}")
            failed_checks.append(entrypoint)
    
    if failed_checks:
        print(f"\n❌ {len(failed_checks)} entrypoints failed policy loading check:")
        for ep in failed_checks:
            print(f"  - {ep}")
        print("\n💡 Add this to your entrypoint:")
        print("from runtime.policy_loader import load_policies")
        print("load_policies()  # Load all policies on startup")
        return 1
    else:
        print(f"\n✅ All {len(entrypoints)} entrypoints load policies correctly!")
        return 0

if __name__ == "__main__":
    sys.exit(main())