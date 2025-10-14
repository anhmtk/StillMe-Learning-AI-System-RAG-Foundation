#!/usr/bin/env python3
"""
Near-Duplicate Pilot Filter for Wave-1e
Filters near-duplicate clusters to identify pilot candidates for refactoring.
"""

import json
import os
import csv
from pathlib import Path
from typing import Dict, List, Any, Set
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.parent

# Protection lists
ALWAYS_PROTECT_PATHS = [
    "tools/**", ".github/**", "scripts/windows/attic_move.ps1", 
    "scripts/windows/attic_rollback.ps1", "config/cleanup/whitelist.yml"
]

ALWAYS_PROTECT_FILENAMES = ["__init__.py"]

def load_near_dupes(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load near-duplicate clusters data"""
    if not os.path.exists(file_path):
        logger.error(f"Near-dupes file not found: {file_path}")
        return {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('near_dupe_clusters', {})
    except Exception as e:
        logger.error(f"Could not load near-dupes data: {e}")
        return {}

def load_redundancy_report(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load redundancy report data"""
    if not os.path.exists(file_path):
        logger.error(f"Redundancy report not found: {file_path}")
        return {}
    
    try:
        file_data = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                file_data[row['path']] = {
                    'inbound_imports': int(row['inbound_imports']),
                    'executed_lines': int(row['executed_lines']),
                    'git_touches': int(row['git_touches']),
                    'days_since_last_change': int(row['days_since_last_change']),
                    'looks_backup': row['looks_backup'] == 'True',
                    'in_registry': row['in_registry'] == 'True',
                    'is_whitelisted': row['is_whitelisted'] == 'True',
                    'is_near_dupe': row['is_near_dupe'] == 'True',
                    'redundant_score': int(row['redundant_score'])
                }
        return file_data
    except Exception as e:
        logger.error(f"Could not load redundancy report: {e}")
        return {}

def is_protected_path(file_path: str) -> bool:
    """Check if file path is protected"""
    path = Path(file_path).as_posix()
    
    # Check filename protection
    if Path(file_path).name in ALWAYS_PROTECT_FILENAMES:
        return True
    
    # Check path protection
    for protect_pattern in ALWAYS_PROTECT_PATHS:
        if protect_pattern.endswith('**'):
            prefix = protect_pattern[:-2]
            if path.startswith(prefix):
                return True
        elif protect_pattern in path:
            return True
    
    return False

def filter_pilot_clusters(
    near_dupes: Dict[str, Dict[str, Any]], 
    redundancy_data: Dict[str, Dict[str, Any]],
    max_clusters: int = 20,
    max_cluster_size: int = 50
) -> Dict[str, Dict[str, Any]]:
    """
    Filter near-duplicate clusters to identify pilot candidates.
    
    Criteria:
    1. Remove clusters with any protected files
    2. Limit cluster size <= 50
    3. Canonical must have inbound_imports > 0 OR executed_lines > 0
    4. All non-canonical must have inbound_imports == 0 AND executed_lines == 0
    5. No files in registry or whitelist
    """
    
    pilot_clusters = {}
    cluster_count = 0
    
    for cluster_id, cluster_data in near_dupes.items():
        if cluster_count >= max_clusters:
            break
            
        files = cluster_data.get('files', [])
        canonical = cluster_data.get('canonical', '')
        non_canonical = cluster_data.get('non_canonical', [])
        
        # Skip if cluster too large
        if len(files) > max_cluster_size:
            logger.debug(f"Skipping {cluster_id}: cluster too large ({len(files)} files)")
            continue
        
        # Check if any file is protected
        has_protected = False
        for file_path in files:
            if is_protected_path(file_path):
                logger.debug(f"Skipping {cluster_id}: contains protected file {file_path}")
                has_protected = True
                break
        
        if has_protected:
            continue
        
        # Check if any file is in registry or whitelist
        has_registry_or_whitelist = False
        for file_path in files:
            if file_path in redundancy_data:
                file_info = redundancy_data[file_path]
                if file_info.get('in_registry', False) or file_info.get('is_whitelisted', False):
                    logger.debug(f"Skipping {cluster_id}: contains registry/whitelist file {file_path}")
                    has_registry_or_whitelist = True
                    break
        
        if has_registry_or_whitelist:
            continue
        
        # Check canonical file criteria
        if canonical not in redundancy_data:
            logger.debug(f"Skipping {cluster_id}: canonical file not in redundancy data")
            continue
        
        canonical_info = redundancy_data[canonical]
        canonical_used = (canonical_info.get('inbound_imports', 0) > 0 or 
                         canonical_info.get('executed_lines', 0) > 0)
        
        if not canonical_used:
            logger.debug(f"Skipping {cluster_id}: canonical file not used")
            continue
        
        # Check non-canonical files criteria
        all_non_canonical_unused = True
        for file_path in non_canonical:
            if file_path not in redundancy_data:
                logger.debug(f"Skipping {cluster_id}: non-canonical file not in redundancy data")
                all_non_canonical_unused = False
                break
            
            file_info = redundancy_data[file_path]
            is_unused = (file_info.get('inbound_imports', 0) == 0 and 
                        file_info.get('executed_lines', 0) == 0)
            
            if not is_unused:
                logger.debug(f"Skipping {cluster_id}: non-canonical file {file_path} is used")
                all_non_canonical_unused = False
                break
        
        if not all_non_canonical_unused:
            continue
        
        # All criteria met - add to pilot
        pilot_clusters[cluster_id] = cluster_data
        cluster_count += 1
        
        logger.info(f"✅ Added pilot cluster {cluster_id}: {canonical} (canonical) + {len(non_canonical)} unused")
    
    return pilot_clusters

def main():
    """Main function to filter pilot clusters"""
    logger.info("🎯 Starting near-duplicate pilot filtering...")
    
    # Load data
    near_dupes_file = REPO_ROOT / "artifacts" / "near_dupes.json"
    redundancy_file = REPO_ROOT / "artifacts" / "redundancy_report.csv"
    
    near_dupes = load_near_dupes(str(near_dupes_file))
    redundancy_data = load_redundancy_report(str(redundancy_file))
    
    if not near_dupes:
        logger.error("No near-duplicate data found")
        return
    
    if not redundancy_data:
        logger.error("No redundancy data found")
        return
    
    logger.info(f"📊 Loaded {len(near_dupes)} near-duplicate clusters")
    logger.info(f"📊 Loaded {len(redundancy_data)} file redundancy records")
    
    # Filter pilot clusters
    pilot_clusters = filter_pilot_clusters(near_dupes, redundancy_data)
    
    # Save pilot clusters
    output_file = REPO_ROOT / "artifacts" / "near_dupes_pilot.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({"pilot_clusters": pilot_clusters}, f, indent=2)
    
    logger.info(f"📊 Results:")
    logger.info(f"  - Total clusters analyzed: {len(near_dupes)}")
    logger.info(f"  - Pilot clusters selected: {len(pilot_clusters)}")
    logger.info(f"  - Output saved to: {output_file}")
    
    # Print pilot clusters summary
    logger.info(f"\n🔍 Pilot clusters selected:")
    for i, (cluster_id, cluster_data) in enumerate(pilot_clusters.items(), 1):
        canonical = cluster_data.get('canonical', '')
        non_canonical = cluster_data.get('non_canonical', [])
        logger.info(f"  {i}. {cluster_id}")
        logger.info(f"     Canonical: {canonical}")
        logger.info(f"     Non-canonical: {', '.join(non_canonical)}")

if __name__ == "__main__":
    main()
