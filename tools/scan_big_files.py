#!/usr/bin/env python3
"""
Scan repository for largest files (excluding .git)
"""

import os
from pathlib import Path

def format_size(size_bytes):
    """Format size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

def get_file_extension(filepath):
    """Get file extension"""
    return Path(filepath).suffix.lower()

def scan_big_files(root_path=".", top_n=30):
    """Scan repository for largest files"""
    root = Path(root_path).resolve()
    
    # Exclude patterns
    exclude_dirs = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', '.cache', 'venv', '.venv'}
    
    file_sizes = []
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip excluded directories
        dirpath_obj = Path(dirpath)
        if any(excluded in dirpath_obj.parts for excluded in exclude_dirs):
            continue
        
        for filename in filenames:
            filepath = dirpath_obj / filename
            try:
                size = filepath.stat().st_size
                if size > 0:
                    rel_path = filepath.relative_to(root)
                    ext = get_file_extension(filepath)
                    file_sizes.append((str(rel_path), size, ext))
            except (OSError, FileNotFoundError, PermissionError):
                pass
    
    # Sort by size (descending)
    file_sizes.sort(key=lambda x: x[1], reverse=True)
    
    return file_sizes[:top_n]

if __name__ == "__main__":
    print("Scanning repository for largest files...")
    print("=" * 80)
    
    big_files = scan_big_files(top_n=30)
    
    print(f"\nTop {len(big_files)} largest files:\n")
    print(f"{'File':<70} {'Size':>15} {'Type':>10}")
    print("-" * 100)
    
    for filepath, size, ext in big_files:
        print(f"{filepath:<70} {format_size(size):>15} {ext:>10}")
    
    # Summary by size thresholds
    print("\n" + "=" * 80)
    print("Summary by size thresholds:\n")
    
    over_20mb = [f for f in big_files if f[1] > 20 * 1024 * 1024]
    over_5mb = [f for f in big_files if f[1] > 5 * 1024 * 1024]
    
    print(f"Files > 20 MB: {len(over_20mb)}")
    for filepath, size, ext in over_20mb:
        print(f"  - {filepath} ({format_size(size)})")
    
    print(f"\nFiles > 5 MB: {len(over_5mb)}")
    for filepath, size, ext in over_5mb[:10]:  # Show first 10
        print(f"  - {filepath} ({format_size(size)})")

