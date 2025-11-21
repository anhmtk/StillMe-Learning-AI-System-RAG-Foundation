#!/usr/bin/env python3
"""
Scan disk usage of repository folders (excluding .git)
"""

import os
from pathlib import Path
from collections import defaultdict

def get_folder_size(folder_path):
    """Calculate total size of folder in bytes"""
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, FileNotFoundError):
                    pass
    except (OSError, PermissionError):
        pass
    return total_size

def format_size(size_bytes):
    """Format size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def scan_repo(root_path="."):
    """Scan repository and return folder sizes"""
    root = Path(root_path).resolve()
    
    # Exclude patterns
    exclude_patterns = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', '.cache'}
    
    folder_sizes = {}
    
    # Scan depth 1 (direct children)
    for item in root.iterdir():
        if item.name in exclude_patterns:
            continue
        if item.is_dir():
            size = get_folder_size(item)
            if size > 0:
                folder_sizes[str(item.relative_to(root))] = size
    
    # Scan depth 2 (subdirectories of direct children)
    for item in root.iterdir():
        if item.name in exclude_patterns or not item.is_dir():
            continue
        for subitem in item.iterdir():
            if subitem.name in exclude_patterns:
                continue
            if subitem.is_dir():
                size = get_folder_size(subitem)
                if size > 0:
                    folder_sizes[str(subitem.relative_to(root))] = size
    
    return folder_sizes

if __name__ == "__main__":
    print("Scanning repository disk usage...")
    print("=" * 80)
    
    folder_sizes = scan_repo()
    
    # Sort by size (descending)
    sorted_folders = sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\nTop {min(20, len(sorted_folders))} largest folders:\n")
    print(f"{'Folder':<60} {'Size':>15}")
    print("-" * 80)
    
    for folder, size in sorted_folders[:20]:
        print(f"{folder:<60} {format_size(size):>15}")

