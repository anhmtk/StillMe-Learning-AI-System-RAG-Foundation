#!/usr/bin/env python3
"""
Near-Duplicate Pilot Selector for Wave-1f
Selects pilot clusters for consolidation, including both tracked and attic files.
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, Any, Set
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.parent

# Protection lists
ALWAYS_PROTECT_PATHS = [
    "tools/**",
    ".github/**",
    "scripts/windows/attic_move.ps1",
    "scripts/windows/attic_rollback.ps1",
    "config/cleanup/whitelist.yml",
]

ALWAYS_PROTECT_FILENAMES = ["__init__.py"]


def load_near_dupes(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load near-duplicate clusters data"""
    if not os.path.exists(file_path):
        logger.error(f"Near-dupes file not found: {file_path}")
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("near_dupe_clusters", {})
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
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                file_data[row["path"]] = {
                    "inbound_imports": int(row["inbound_imports"]),
                    "executed_lines": int(row["executed_lines"]),
                    "git_touches": int(row["git_touches"]),
                    "days_since_last_change": int(row["days_since_last_change"]),
                    "looks_backup": row["looks_backup"] == "True",
                    "in_registry": row["in_registry"] == "True",
                    "is_whitelisted": row["is_whitelisted"] == "True",
                    "is_near_dupe": row["is_near_dupe"] == "True",
                    "redundant_score": int(row["redundant_score"]),
                }
        return file_data
    except Exception as e:
        logger.error(f"Could not load redundancy report: {e}")
        return {}


def get_tracked_files() -> Set[str]:
    """Get list of tracked Python files"""
    try:
        import subprocess

        result = subprocess.run(
            ["git", "ls-files", "*.py"], capture_output=True, text=True, cwd=REPO_ROOT
        )
        if result.returncode == 0:
            return (
                set(result.stdout.strip().split("\n"))
                if result.stdout.strip()
                else set()
            )
    except Exception as e:
        logger.warning(f"Could not get tracked files: {e}")
    return set()


def is_protected_path(file_path: str) -> bool:
    """Check if file path is protected"""
    path = Path(file_path).as_posix()

    # Check filename protection
    if Path(file_path).name in ALWAYS_PROTECT_FILENAMES:
        return True

    # Check path protection
    for protect_pattern in ALWAYS_PROTECT_PATHS:
        if protect_pattern.endswith("**"):
            prefix = protect_pattern[:-2]
            if path.startswith(prefix):
                return True
        elif protect_pattern in path:
            return True

    return False


def is_file_in_attic(file_path: str) -> bool:
    """Check if file is in attic directory"""
    return file_path.startswith("_attic/") or "_attic/" in file_path


def select_pilot_clusters(
    near_dupes: Dict[str, Dict[str, Any]],
    redundancy_data: Dict[str, Dict[str, Any]],
    tracked_files: Set[str],
    max_clusters: int = 20,
    min_cluster_size: int = 2,
    max_cluster_size: int = 15,
) -> Dict[str, Dict[str, Any]]:
    """
    Select pilot clusters for consolidation.

    Criteria:
    1. Remove clusters with any protected files
    2. Limit cluster size 2-15
    3. Canonical must have inbound_imports > 0 OR executed_lines > 0
    4. All non-canonical must have inbound_imports == 0 AND executed_lines == 0
    5. No files in registry or whitelist
    6. Accept files from both tracked and attic (read-only for attic)
    """

    pilot_clusters = {}
    cluster_count = 0

    for cluster_id, cluster_data in near_dupes.items():
        if cluster_count >= max_clusters:
            break

        files = cluster_data.get("files", [])
        canonical = cluster_data.get("canonical", "")
        non_canonical = cluster_data.get("non_canonical", [])

        # Skip if cluster too small or too large
        if len(files) < min_cluster_size or len(files) > max_cluster_size:
            logger.debug(
                f"Skipping {cluster_id}: cluster size {len(files)} not in range [{min_cluster_size}, {max_cluster_size}]"
            )
            continue

        # Check if any file is protected
        has_protected = False
        for file_path in files:
            if is_protected_path(file_path):
                logger.debug(
                    f"Skipping {cluster_id}: contains protected file {file_path}"
                )
                has_protected = True
                break

        if has_protected:
            continue

        # Check if any file is in registry or whitelist
        has_registry_or_whitelist = False
        for file_path in files:
            if file_path in redundancy_data:
                file_info = redundancy_data[file_path]
                if file_info.get("in_registry", False) or file_info.get(
                    "is_whitelisted", False
                ):
                    logger.debug(
                        f"Skipping {cluster_id}: contains registry/whitelist file {file_path}"
                    )
                    has_registry_or_whitelist = True
                    break

        if has_registry_or_whitelist:
            continue

        # Check canonical file criteria
        if canonical not in redundancy_data:
            logger.debug(
                f"Skipping {cluster_id}: canonical file not in redundancy data"
            )
            continue

        canonical_info = redundancy_data[canonical]
        canonical_used = (
            canonical_info.get("inbound_imports", 0) > 0
            or canonical_info.get("executed_lines", 0) > 0
        )

        if not canonical_used:
            logger.debug(f"Skipping {cluster_id}: canonical file not used")
            continue

        # Check non-canonical files criteria
        all_non_canonical_unused = True
        for file_path in non_canonical:
            if file_path not in redundancy_data:
                logger.debug(
                    f"Skipping {cluster_id}: non-canonical file not in redundancy data"
                )
                all_non_canonical_unused = False
                break

            file_info = redundancy_data[file_path]
            is_unused = (
                file_info.get("inbound_imports", 0) == 0
                and file_info.get("executed_lines", 0) == 0
            )

            if not is_unused:
                logger.debug(
                    f"Skipping {cluster_id}: non-canonical file {file_path} is used"
                )
                all_non_canonical_unused = False
                break

        if not all_non_canonical_unused:
            continue

        # All criteria met - add to pilot
        pilot_clusters[cluster_id] = cluster_data
        cluster_count += 1

        # Mark files as in_attic for tracking
        for file_path in files:
            if is_file_in_attic(file_path):
                cluster_data.setdefault("attic_files", []).append(file_path)

        logger.info(
            f"✅ Added pilot cluster {cluster_id}: {canonical} (canonical) + {len(non_canonical)} unused"
        )
        logger.info(f"   Files: {', '.join(files)}")

    return pilot_clusters


def main():
    """Main function to select pilot clusters"""
    logger.info("🎯 Starting near-duplicate pilot selection...")

    # Load data
    near_dupes_file = REPO_ROOT / "artifacts" / "near_dupes.json"
    redundancy_file = REPO_ROOT / "artifacts" / "redundancy_report.csv"

    near_dupes = load_near_dupes(str(near_dupes_file))
    redundancy_data = load_redundancy_report(str(redundancy_file))
    tracked_files = get_tracked_files()

    if not near_dupes:
        logger.error("No near-duplicate data found")
        return

    if not redundancy_data:
        logger.error("No redundancy data found")
        return

    logger.info(f"📊 Loaded {len(near_dupes)} near-duplicate clusters")
    logger.info(f"📊 Loaded {len(redundancy_data)} file redundancy records")
    logger.info(f"📊 Found {len(tracked_files)} tracked Python files")

    # Select pilot clusters
    pilot_clusters = select_pilot_clusters(near_dupes, redundancy_data, tracked_files)

    # Save pilot clusters
    output_file = REPO_ROOT / "artifacts" / "near_dupes_pilot.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"pilot_clusters": pilot_clusters}, f, indent=2)

    logger.info("📊 Results:")
    logger.info(f"  - Total clusters analyzed: {len(near_dupes)}")
    logger.info(f"  - Pilot clusters selected: {len(pilot_clusters)}")
    logger.info(f"  - Output saved to: {output_file}")

    # Print pilot clusters summary
    logger.info("\n🔍 Pilot clusters selected:")
    for i, (cluster_id, cluster_data) in enumerate(pilot_clusters.items(), 1):
        canonical = cluster_data.get("canonical", "")
        non_canonical = cluster_data.get("non_canonical", [])
        attic_files = cluster_data.get("attic_files", [])
        logger.info(f"  {i}. {cluster_id}")
        logger.info(f"     Canonical: {canonical}")
        logger.info(f"     Non-canonical: {', '.join(non_canonical)}")
        if attic_files:
            logger.info(f"     Attic files: {', '.join(attic_files)}")


if __name__ == "__main__":
    main()
