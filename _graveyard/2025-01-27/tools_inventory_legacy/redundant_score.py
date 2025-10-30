#!/usr/bin/env python3
"""
 cleanup/wave-1e-safe
Redundant Score Calculator for StillMe Cleanup
Calculates redundancy scores based on multiple heuristics.

Redundant Score Calculator
Calculates redundancy score for Python files based on multiple factors
 main
"""

import os
import json
import csv
import subprocess
from pathlib import Path
 cleanup/wave-1e-safe
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.parent

# Global excludes
GLOBAL_EXCLUDES = [
    ".git/", ".github/", ".venv/", "venv/", "env/", "site-packages/", "dist/", 
    "build/", "node_modules/", "artifacts/", "reports/", "htmlcov", 
    "__pycache__/", "*.egg-info/", ".sandbox/"
]

def should_exclude_path(file_path: str) -> bool:
    """Check if a file path should be excluded based on global exclude patterns."""
    path = Path(file_path).as_posix()
    for exclude in GLOBAL_EXCLUDES:
        if Path(exclude).is_absolute():
            if Path(path) == Path(exclude) or Path(path).is_relative_to(Path(exclude)):
                return True
        else:
            if exclude.endswith('/') and f"/{exclude}" in path:
                return True
            elif exclude.startswith('*') and path.endswith(exclude[1:]):
                return True
            elif exclude in path:
                return True
    return False

def load_import_inbound(file_path: str) -> Dict[str, int]:
    """Load import inbound data"""

from typing import Dict, List, Set, Any

def load_import_inbound(file_path: str) -> Dict[str, int]:
    """Load import inbound data from JSON file"""
 main
    if not os.path.exists(file_path):
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {item['module']: item['inbound_imports'] for item in data}
    except Exception as e:
 cleanup/wave-1e-safe
        logger.warning(f"Could not load import inbound data: {e}")
        return {}

def load_coverage(file_path: str) -> Dict[str, int]:
    """Load coverage data"""

        print(f"Warning: Could not load import inbound data: {e}")
        return {}

def load_coverage(file_path: str) -> Dict[str, int]:
    """Load coverage data from JSON file"""
 main
    if not os.path.exists(file_path):
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
 cleanup/wave-1e-safe
            files_data = data.get('files', {})
            
            # Convert coverage data to executed lines count
            coverage_dict = {}
            for file_path, file_data in files_data.items():
                if isinstance(file_data, dict) and 'executed_lines' in file_data:
                    # Count executed lines
                    executed_lines = file_data.get('executed_lines', [])
                    if isinstance(executed_lines, list):
                        coverage_dict[file_path] = len(executed_lines)
                    else:
                        coverage_dict[file_path] = executed_lines
                else:
                    coverage_dict[file_path] = 0
            
            return coverage_dict
    except Exception as e:
        logger.warning(f"Could not load coverage data: {e}")

            coverage = {}
            for file_path, file_data in data.get('files', {}).items():
                coverage[file_path] = file_data.get('summary', {}).get('covered_lines', 0)
            return coverage
    except Exception as e:
        print(f"Warning: Could not load coverage data: {e}")
 main
        return {}

def load_ast_dupes(file_path: str) -> Dict[str, str]:
    """Load AST duplicates data"""
    if not os.path.exists(file_path):
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
 cleanup/wave-1e-safe
            return data.get('dupe_buckets', {})
    except Exception as e:
        logger.warning(f"Could not load AST dupes data: {e}")
        return {}

def load_whitelist(file_path: str) -> List[str]:
    """Load whitelist data"""
    if not os.path.exists(file_path):
        return []

            dupes = {}
            for bucket, files in data.get('duplicate_groups', {}).items():
                for file_path in files:
                    dupes[file_path] = bucket
            return dupes
    except Exception as e:
        print(f"Warning: Could not load AST dupes data: {e}")
        return {}

def load_whitelist(file_path: str) -> Set[str]:
    """Load whitelist from YAML file"""
    if not os.path.exists(file_path):
        return set()
 main
    
    try:
        import yaml
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
 cleanup/wave-1e-safe
            return data.get('whitelist', [])
    except Exception as e:
        logger.warning(f"Could not load whitelist data: {e}")
        return []

def load_dynamic_registry(file_path: str) -> List[str]:
    """Load dynamic registry paths"""
    if not os.path.exists(file_path):
        return []

            protected_files = set(data.get('protected_files', []))
            protected_patterns = set(data.get('protected_patterns', []))
            return protected_files | protected_patterns
    except Exception as e:
        print(f"Warning: Could not load whitelist: {e}")
        return set()

def load_dynamic_registry(file_path: str) -> Set[str]:
    """Load dynamic registry paths"""
    if not os.path.exists(file_path):
        return set()
 main
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
 cleanup/wave-1e-safe
            return data.get('dynamic_paths', [])
    except Exception as e:
        logger.warning(f"Could not load dynamic registry data: {e}")
        return []

            return set(data.get('dynamic_modules', []))
    except Exception as e:
        print(f"Warning: Could not load dynamic registry: {e}")
        return set()
 main

def load_near_dupes(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load near-duplicate data"""
    if not os.path.exists(file_path):
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('near_dupe_clusters', {})
    except Exception as e:
 cleanup/wave-1e-safe
        logger.warning(f"Could not load near-dupes data: {e}")

        print(f"Warning: Could not load near-dupes data: {e}")
 main
        return {}

def get_git_touches(file_path: str) -> int:
    """Get number of git touches for a file"""
    try:
        result = subprocess.run(
            ['git', 'log', '--oneline', '--', file_path],
 cleanup/wave-1e-safe
            capture_output=True, text=True, cwd=REPO_ROOT
        )
        if result.returncode == 0:
            return len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    except Exception as e:
        logger.debug(f"Error getting git touches for {file_path}: {e}")
    return 0

def get_days_since_last_change(file_path: str) -> int:
    """Get days since last change for a file"""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ct', '--', file_path],
            capture_output=True, text=True, cwd=REPO_ROOT

            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
    except Exception:
        pass
    return 0

def get_days_since_last_change(file_path: str) -> int:
    """Get days since last change"""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ct', '--', file_path],
            capture_output=True, text=True, timeout=10
 main
        )
        if result.returncode == 0 and result.stdout.strip():
            import time
            last_commit = int(result.stdout.strip())
 cleanup/wave-1e-safe
            days_ago = (time.time() - last_commit) / (24 * 3600)
            return int(days_ago)
    except Exception as e:
        logger.debug(f"Error getting days since last change for {file_path}: {e}")
    return 0

def is_backup_file(file_path: str) -> bool:
    """Check if file looks like a backup file"""
    path_lower = file_path.lower()
    backup_patterns = ['backup', '_old', '_copy', '_tmp', '.save', '.py~']
    return any(pattern in path_lower for pattern in backup_patterns)

def is_whitelisted(file_path: str, whitelist: List[str]) -> bool:
    """Check if file is whitelisted"""
    for pattern in whitelist:
        if pattern in file_path:
            return True
    return False

def is_in_registry(file_path: str, dynamic_modules: List[str]) -> bool:
    """Check if file is in dynamic registry"""
    for pattern in dynamic_modules:
        if pattern in file_path:

            days = (time.time() - last_commit) / (24 * 3600)
            return int(days)
    except Exception:
        pass
    return 0

def is_backup_file(file_path: str) -> bool:
    """Check if file looks like a backup"""
    backup_patterns = [
        'backup', 'old', 'copy', 'tmp', '.save', '.py~', 
        '_backup', '_old', '_copy', '_tmp', '_save'
    ]
    path_lower = file_path.lower()
    return any(pattern in path_lower for pattern in backup_patterns)

def is_in_registry(file_path: str, dynamic_modules: Set[str]) -> bool:
    """Check if file is in dynamic registry"""
    path_parts = Path(file_path).parts
    for i in range(len(path_parts)):
        partial_path = str(Path(*path_parts[:i+1]))
        if partial_path in dynamic_modules:
            return True
    return False

def is_whitelisted(file_path: str, whitelist: Set[str]) -> bool:
    """Check if file is whitelisted"""
    for pattern in whitelist:
        if pattern in file_path or file_path.endswith(pattern):
 main
            return True
    return False

def is_near_dupe_of_canonical(file_path: str, near_dupes: Dict[str, Dict[str, Any]]) -> bool:
    """Check if file is a near-duplicate of a canonical file"""
    for cluster_data in near_dupes.values():
        if file_path in cluster_data.get('non_canonical', []):
            return True
    return False

def calculate_redundant_score(
    file_path: str,
    inbound_imports: int,
    executed_lines: int,
    git_touches: int,
    days_since_last_change: int,
    looks_backup: bool,
    in_registry: bool,
    is_whitelisted: bool,
    dupe_bucket: str = "",
    is_near_dupe: bool = False
) -> int:
    """Calculate redundant score (0-100)"""
    
    score = 0
    
    # Hard protection for __init__.py
    if file_path.endswith('__init__.py'):
        return 0
    
    # Heuristics
    if inbound_imports == 0:
        score += 40
    if executed_lines == 0:
        score += 30
    if git_touches <= 1:
        score += 10
    if days_since_last_change > 180:
        score += 10
    if looks_backup:
        score += 10
    if is_near_dupe and inbound_imports == 0 and executed_lines == 0:
        score += 15  # Bonus for unused near-duplicates
    
    # Protections
    if is_whitelisted:
        score -= 30
    if in_registry:
        score -= 20
    
    # Ensure score is between 0 and 100
    return max(0, min(100, score))

 cleanup/wave-1e-safe

def should_exclude_path(file_path: str) -> bool:
    """Check if path should be excluded"""
    excludes = [
        ".git/", ".github/", ".venv/", "venv/", "env/", "site-packages/",
        "dist/", "build/", "node_modules/", "artifacts/", "reports/",
        "htmlcov", "__pycache__/", "*.egg-info/", ".sandbox/"
    ]
    
    path = Path(file_path).as_posix()
    for exclude in excludes:
        if exclude.endswith('/') and f"/{exclude}" in path:
            return True
        elif exclude.startswith('*') and path.endswith(exclude[1:]):
            return True
        elif exclude in path:
            return True
    return False

 main
def analyze_all_files(
    root_path: str = ".",
    import_inbound_file: str = "artifacts/import_inbound.json",
    coverage_file: str = "artifacts/coverage.json",
    ast_dupes_file: str = "artifacts/ast_dupes.json",
    whitelist_file: str = "config/cleanup/whitelist.yml",
    dynamic_registry_file: str = "artifacts/dynamic_registry_paths.json",
    near_dupes_file: str = "artifacts/near_dupes.json"
) -> List[Dict[str, Any]]:
    """Analyze all Python files and calculate redundant scores"""
    
 cleanup/wave-1e-safe
    logger.info("📊 Loading analysis data...")

    print("📊 Loading analysis data...")
 main
    import_inbound = load_import_inbound(import_inbound_file)
    coverage = load_coverage(coverage_file)
    ast_dupes = load_ast_dupes(ast_dupes_file)
    whitelist = load_whitelist(whitelist_file)
    dynamic_modules = load_dynamic_registry(dynamic_registry_file)
    near_dupes = load_near_dupes(near_dupes_file)
    
 cleanup/wave-1e-safe
    logger.info("🔍 Analyzing Python files...")
    results = []
    
    for root, dirs, files in os.walk(root_path):
        for file in files:
            if file.endswith(".py"):
                file_path = Path(root) / file

    print("🔍 Analyzing Python files...")
    results = []
    
    for root, dirs, files in os.walk(root_path):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not should_exclude_path(os.path.join(root, d))]
        
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
 main
                rel_path = os.path.relpath(file_path, root_path)
                
                if should_exclude_path(rel_path):
                    continue
                
                # Get data
                inbound_imports = import_inbound.get(rel_path, 0)
                executed_lines = coverage.get(rel_path, 0)
                git_touches = get_git_touches(rel_path)
                days_since_last_change = get_days_since_last_change(rel_path)
                looks_backup = is_backup_file(rel_path)
                in_registry = is_in_registry(rel_path, dynamic_modules)
                whitelisted = is_whitelisted(rel_path, whitelist)
                dupe_bucket = ast_dupes.get(rel_path, "")
                is_near_dupe = is_near_dupe_of_canonical(rel_path, near_dupes)
                
                # Calculate score
                score = calculate_redundant_score(
                    rel_path, inbound_imports, executed_lines, git_touches,
                    days_since_last_change, looks_backup, in_registry, whitelisted, dupe_bucket, is_near_dupe
                )
                
                results.append({
                    'path': rel_path,
                    'inbound_imports': inbound_imports,
                    'executed_lines': executed_lines,
                    'git_touches': git_touches,
                    'days_since_last_change': days_since_last_change,
                    'looks_backup': looks_backup,
                    'in_registry': in_registry,
                    'is_whitelisted': whitelisted,
                    'dupe_bucket': dupe_bucket,
                    'is_near_dupe': is_near_dupe,
                    'redundant_score': score
                })
    
    # Sort by score descending
    results.sort(key=lambda x: x['redundant_score'], reverse=True)
    
    return results

def main():
 cleanup/wave-1e-safe
    """Main function to calculate redundant scores"""
    logger.info("🎯 Starting redundant score analysis...")
    

    """Main function"""
    print("🎯 Starting redundant score analysis...")
    
    # Ensure artifacts directory exists
 main
    os.makedirs("artifacts", exist_ok=True)
    
    # Analyze files
    results = analyze_all_files()
    
    # Save to CSV
    output_file = "artifacts/redundancy_report.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'path', 'inbound_imports', 'executed_lines', 'git_touches',
            'days_since_last_change', 'looks_backup', 'in_registry',
            'is_whitelisted', 'dupe_bucket', 'is_near_dupe', 'redundant_score'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
 cleanup/wave-1e-safe
    logger.info(f"📊 Analysis complete:")
    logger.info(f"  - Files analyzed: {len(results)}")
    logger.info(f"  - High risk files (score ≥ 70): {len([r for r in results if r['redundant_score'] >= 70])}")
    logger.info(f"  - Results saved to: {output_file}")
    
    # Print top 10 candidates for quick review
    logger.info("\n🔝 Top candidates (score ≥ 70):")
    for i, r in enumerate([r for r in results if r['redundant_score'] >= 70][:10]):
        logger.info(f"  {i+1}. {r['path']} (score: {r['redundant_score']})")

if __name__ == "__main__":
    main()

    print(f"📊 Analysis complete:")
    print(f"  - Files analyzed: {len(results)}")
    print(f"  - High risk files (score ≥ 70): {len([r for r in results if r['redundant_score'] >= 70])}")
    print(f"  - Results saved to: {output_file}")
    
    # Show top candidates
    top_candidates = [r for r in results if r['redundant_score'] >= 70][:10]
    if top_candidates:
        print(f"\n🔝 Top candidates (score ≥ 70):")
        for i, candidate in enumerate(top_candidates, 1):
            print(f"  {i}. {candidate['path']} (score: {candidate['redundant_score']})")

if __name__ == "__main__":
    main()
 main
