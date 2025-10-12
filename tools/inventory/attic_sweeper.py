#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Attic Sweeper for StillMe Cleanup
Identifies files in _attic/ that are safe to permanently delete.
"""

import os
import csv
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.parent

# Configuration
ALWAYS_PROTECT_PATHS = [
    "tools/", ".github/", "scripts/windows/attic_move.ps1", 
    "scripts/windows/attic_rollback.ps1", "config/cleanup/whitelist.yml",
    "stillme_compat/"
]
ALWAYS_PROTECT_FILENAMES = ["__init__.py"]

def load_attic_moves(file_path: Path) -> List[Dict[str, Any]]:
    """Load attic moves from CSV file."""
    if not file_path.exists():
        logger.warning(f"Attic moves file not found: {file_path}")
        return []
    
    moves = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                moves.append(row)
        logger.info(f"Loaded {len(moves)} attic moves")
    except Exception as e:
        logger.error(f"Error loading attic moves: {e}")
    
    return moves

def is_protected_file(file_path: str) -> Tuple[bool, str]:
    """Check if file is protected from eviction."""
    path_obj = Path(file_path)
    
    # Check filename protection
    if path_obj.name in ALWAYS_PROTECT_FILENAMES:
        return True, f"Protected filename: {path_obj.name}"
    
    # Check path protection
    for protect_path in ALWAYS_PROTECT_PATHS:
        if protect_path.endswith('/'):
            if file_path.startswith(protect_path):
                return True, f"Protected path: {protect_path}"
        else:
            if file_path == protect_path or file_path.startswith(protect_path + '/'):
                return True, f"Protected path: {protect_path}"
    
    return False, "Not protected"

def calculate_days_in_attic(move_timestamp: str) -> int:
    """Calculate days since file was moved to attic."""
    try:
        # Parse timestamp (assuming format: "YYYY-MM-DD HH:MM:SS")
        move_date = datetime.strptime(move_timestamp, "%Y-%m-%d %H:%M:%S")
        days_ago = (datetime.now() - move_date).days
        return days_ago
    except Exception as e:
        logger.warning(f"Could not parse timestamp '{move_timestamp}': {e}")
        return 0

def has_repo_references(original_path: str) -> bool:
    """Check if file has references in current repo."""
    try:
        # Search for imports or references to the original path
        # Convert file path to module name for searching
        module_name = original_path.replace('/', '.').replace('\\', '.')
        if module_name.endswith('.py'):
            module_name = module_name[:-3]
        
        # Search for various reference patterns
        search_patterns = [
            f"import {module_name}",
            f"from {module_name}",
            f"'{original_path}'",
            f'"{original_path}"',
            original_path
        ]
        
        for pattern in search_patterns:
            try:
                result = subprocess.run(
                    ['git', 'grep', '-r', '--exclude-dir=_attic', pattern],
                    capture_output=True, text=True, cwd=REPO_ROOT,
                    timeout=30
                )
                if result.returncode == 0 and result.stdout.strip():
                    logger.debug(f"Found reference to {original_path}: {result.stdout.strip()[:100]}")
                    return True
            except subprocess.TimeoutExpired:
                logger.warning(f"Timeout searching for pattern: {pattern}")
            except Exception as e:
                logger.debug(f"Error searching for pattern '{pattern}': {e}")
        
        return False
    except Exception as e:
        logger.warning(f"Error checking references for {original_path}: {e}")
        return False

def scan_attic_directory(attic_path: Path) -> List[Dict[str, Any]]:
    """Scan _attic directory for files."""
    if not attic_path.exists():
        logger.warning(f"Attic directory not found: {attic_path}")
        return []
    
    attic_files = []
    for py_file in attic_path.rglob("*.py"):
        rel_path = py_file.relative_to(attic_path)
        attic_files.append({
            'path_in_attic': str(rel_path),
            'full_path': str(py_file)
        })
    
    logger.info(f"Found {len(attic_files)} Python files in attic")
    return attic_files

def analyze_eviction_candidates(
    attic_moves: List[Dict[str, Any]], 
    min_days: int = 30,
    dry_run: bool = True
) -> List[Dict[str, Any]]:
    """Analyze files in attic for eviction candidates."""
    candidates = []
    
    # Create a map of original paths to move info
    move_map = {}
    for move in attic_moves:
        original_path = move.get('src', '')
        if original_path:
            move_map[original_path] = move
    
    # Scan current attic directory
    attic_path = REPO_ROOT / "_attic"
    attic_files = scan_attic_directory(attic_path)
    
    for file_info in attic_files:
        path_in_attic = file_info['path_in_attic']
        
        # Try to find original path (this is approximate)
        # In real implementation, we'd need better tracking
        original_path = path_in_attic  # Simplified for now
        
        # Check if we have move info for this file
        move_info = move_map.get(original_path)
        if not move_info:
            # File might have been moved in a different way
            days_in_attic = 0
            move_timestamp = "Unknown"
        else:
            move_timestamp = move_info.get('timestamp', '')
            days_in_attic = calculate_days_in_attic(move_timestamp)
        
        # Check protection
        is_protected, protection_reason = is_protected_file(path_in_attic)
        
        # Check references
        has_refs = has_repo_references(original_path)
        
        # Determine if candidate for eviction
        is_candidate = (
            days_in_attic >= min_days and
            not is_protected and
            not has_refs
        )
        
        reason = []
        if days_in_attic < min_days:
            reason.append(f"Too recent ({days_in_attic} days < {min_days})")
        if is_protected:
            reason.append(protection_reason)
        if has_refs:
            reason.append("Has repo references")
        
        candidate_info = {
            'path_in_attic': path_in_attic,
            'original_path': original_path,
            'days_in_attic': days_in_attic,
            'has_repo_refs': has_refs,
            'protected_flag': is_protected,
            'reason': "; ".join(reason) if reason else "Safe for eviction",
            'is_candidate': is_candidate,
            'move_timestamp': move_timestamp
        }
        
        candidates.append(candidate_info)
    
    return candidates

def save_eviction_candidates(candidates: List[Dict[str, Any]], output_file: Path):
    """Save eviction candidates to CSV."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'path_in_attic', 'original_path', 'days_in_attic', 
            'has_repo_refs', 'protected_flag', 'reason', 'is_candidate', 'move_timestamp'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidates)
    
    logger.info(f"Eviction candidates saved to: {output_file}")

def main():
    """Main function for attic sweeper."""
    parser = argparse.ArgumentParser(description='Attic Sweeper - Identify files safe to delete')
    parser.add_argument('--days', type=int, default=30, help='Minimum days in attic (default: 30)')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Dry run mode (default: True)')
    parser.add_argument('--attic-moves', type=str, default='artifacts/attic_moves.csv', help='Path to attic moves CSV')
    parser.add_argument('--output', type=str, default='artifacts/attic_eviction_candidates.csv', help='Output CSV file')
    
    args = parser.parse_args()
    
    logger.info(f"Starting attic sweeper (dry-run: {args.dry_run}, min_days: {args.days})")
    
    # Load attic moves
    attic_moves_file = REPO_ROOT / args.attic_moves
    attic_moves = load_attic_moves(attic_moves_file)
    
    # Analyze candidates
    candidates = analyze_eviction_candidates(attic_moves, args.days, args.dry_run)
    
    # Save results
    output_file = REPO_ROOT / args.output
    save_eviction_candidates(candidates, output_file)
    
    # Print summary
    total_files = len(candidates)
    eviction_candidates = [c for c in candidates if c['is_candidate']]
    
    logger.info(f"Analysis complete:")
    logger.info(f"  - Total files in attic: {total_files}")
    logger.info(f"  - Eviction candidates: {len(eviction_candidates)}")
    logger.info(f"  - Results saved to: {output_file}")
    
    if eviction_candidates:
        logger.info("\nEviction candidates:")
        for i, candidate in enumerate(eviction_candidates[:10], 1):  # Show top 10
            logger.info(f"  {i}. {candidate['path_in_attic']} ({candidate['days_in_attic']} days)")
    else:
        logger.info("No eviction candidates found")

if __name__ == "__main__":
    main()
