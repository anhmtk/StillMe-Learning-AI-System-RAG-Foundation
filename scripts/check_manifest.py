#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check if manifest is up-to-date with validator files

This script checks if any validator files are newer than the manifest
and prompts to regenerate if needed.
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))


def get_file_mtime(file_path: Path) -> float:
    """Get file modification time"""
    try:
        return file_path.stat().st_mtime
    except Exception:
        return 0


def find_validator_files() -> list:
    """Find all validator-related Python files"""
    validator_dirs = [
        project_root / "stillme_core" / "validation",
        project_root / "backend" / "validators",
        project_root / "backend" / "core" / "validation",
    ]
    
    validator_files = []
    for dir_path in validator_dirs:
        if dir_path.exists():
            for py_file in dir_path.rglob("*.py"):
                if py_file.is_file() and not py_file.name.startswith("__"):
                    validator_files.append(py_file)
    
    return validator_files


def check_manifest_up_to_date() -> tuple[bool, str]:
    """
    Check if manifest is up-to-date
    
    Returns:
        (is_up_to_date, message)
    """
    manifest_path = project_root / "data" / "stillme_manifest.json"
    
    if not manifest_path.exists():
        return False, "Manifest not found - needs to be generated"
    
    manifest_mtime = get_file_mtime(manifest_path)
    validator_files = find_validator_files()
    
    if not validator_files:
        return True, "No validator files found (unexpected)"
    
    newer_files = []
    for validator_file in validator_files:
        file_mtime = get_file_mtime(validator_file)
        if file_mtime > manifest_mtime:
            newer_files.append(validator_file)
    
    if newer_files:
        file_list = "\n  - ".join([str(f.relative_to(project_root)) for f in newer_files[:5]])
        if len(newer_files) > 5:
            file_list += f"\n  - ... and {len(newer_files) - 5} more files"
        return False, f"Manifest is outdated. Newer validator files:\n  - {file_list}"
    
    return True, "Manifest is up-to-date"


def main():
    """Main function"""
    is_up_to_date, message = check_manifest_up_to_date()
    
    if is_up_to_date:
        print(f"[OK] {message}")
        return 0
    else:
        print(f"[WARNING] {message}")
        print("\n[INFO] To update manifest, run:")
        print("   python scripts/update_manifest.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())

