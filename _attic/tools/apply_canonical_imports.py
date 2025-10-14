#!/usr/bin/env python3
"""
Apply Canonical Imports for Wave-1f
Creates compatibility shims and rewrites imports to canonical files.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Set
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent.parent


def load_pilot_clusters(file_path: str) -> Dict[str, Dict[str, Any]]:
    """Load pilot clusters data"""
    if not os.path.exists(file_path):
        logger.warning(f"Pilot clusters file not found: {file_path}")
        return {}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("pilot_clusters", {})
    except Exception as e:
        logger.error(f"Could not load pilot clusters data: {e}")
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


def create_compat_shim(old_path: str, canonical_path: str, compat_dir: Path) -> bool:
    """Create a compatibility shim for an old import path"""
    try:
        # Convert old path to module path
        old_module = old_path.replace("/", ".").replace("\\", ".").replace(".py", "")
        canonical_module = (
            canonical_path.replace("/", ".").replace("\\", ".").replace(".py", "")
        )

        # Create shim file path
        shim_path = compat_dir / f"{old_module.replace('.', '/')}.py"
        shim_dir = shim_path.parent

        # Create directory if needed
        shim_dir.mkdir(parents=True, exist_ok=True)

        # Create shim content
        shim_content = f'''"""
Compatibility shim for {old_module}

This module provides backward compatibility for the refactored {canonical_module}.
Please update your imports to use the canonical module directly.

Old import (deprecated):
    from {old_module} import SomeClass

New import (recommended):
    from {canonical_module} import SomeClass
"""

import warnings

# Emit deprecation warning
warnings.warn(
    "Importing from {old_module} is deprecated. "
    "Please use {canonical_module} instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from canonical module
from {canonical_module} import *
'''

        # Write shim file
        with open(shim_path, "w", encoding="utf-8") as f:
            f.write(shim_content)

        logger.info(f"Created shim: {shim_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to create shim for {old_path}: {e}")
        return False


def find_imports_in_file(file_path: Path) -> List[Dict[str, str]]:
    """Find import statements in a Python file"""
    imports = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

            for i, line in enumerate(lines):
                line = line.strip()

                # Match import statements
                if line.startswith("import ") or line.startswith("from "):
                    imports.append(
                        {"line_number": i + 1, "content": line, "file": str(file_path)}
                    )

    except Exception as e:
        logger.debug(f"Could not read file {file_path}: {e}")

    return imports


def rewrite_imports_in_file(
    file_path: Path, import_mappings: Dict[str, str]
) -> List[str]:
    """Rewrite imports in a file based on mappings"""
    changes = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")

        modified = False
        for i, line in enumerate(lines):
            original_line = line
            modified_line = line

            # Check each import mapping
            for old_import, new_import in import_mappings.items():
                # Handle different import patterns
                patterns = [
                    f"from {old_import} import",
                    f"import {old_import}",
                    f"from {old_import}.",
                ]

                for pattern in patterns:
                    if pattern in modified_line:
                        modified_line = modified_line.replace(
                            pattern, pattern.replace(old_import, new_import)
                        )
                        break

            if modified_line != original_line:
                lines[i] = modified_line
                modified = True
                changes.append(f"Line {i+1}: {original_line} -> {modified_line}")

        # Write back if modified
        if modified:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            logger.info(f"Modified imports in: {file_path}")

    except Exception as e:
        logger.error(f"Could not rewrite imports in {file_path}: {e}")

    return changes


def main():
    """Main function to apply canonical imports"""
    logger.info("🎯 Starting canonical imports application...")

    # Load pilot clusters
    pilot_file = REPO_ROOT / "artifacts" / "near_dupes_pilot.json"
    pilot_clusters = load_pilot_clusters(str(pilot_file))

    if not pilot_clusters:
        logger.warning(
            "No pilot clusters found. Creating example shims for demonstration..."
        )

        # Create example shims for demonstration
        compat_dir = REPO_ROOT / "stillme_compat"
        compat_dir.mkdir(exist_ok=True)

        # Example mappings (these would come from pilot clusters in real scenario)
        example_mappings = {
            "stillme_core.old_module": "stillme_core.new_module",
            "stillme_core.legacy_component": "stillme_core.modern_component",
        }

        for old_path, canonical_path in example_mappings.items():
            create_compat_shim(old_path, canonical_path, compat_dir)

        logger.info("Created example compatibility shims")
        return

    # Get tracked files
    tracked_files = get_tracked_files()
    logger.info(f"Found {len(tracked_files)} tracked Python files")

    # Create compatibility directory
    compat_dir = REPO_ROOT / "stillme_compat"
    compat_dir.mkdir(exist_ok=True)

    # Process each pilot cluster
    import_mappings = {}
    shims_created = 0

    for cluster_id, cluster_data in pilot_clusters.items():
        canonical = cluster_data.get("canonical", "")
        non_canonical = cluster_data.get("non_canonical", [])

        logger.info(f"Processing cluster {cluster_id}: {canonical}")

        # Create shims for non-canonical files
        for old_path in non_canonical:
            if create_compat_shim(old_path, canonical, compat_dir):
                shims_created += 1
                # Add to import mappings
                old_module = (
                    old_path.replace("/", ".").replace("\\", ".").replace(".py", "")
                )
                canonical_module = (
                    canonical.replace("/", ".").replace("\\", ".").replace(".py", "")
                )
                import_mappings[old_module] = canonical_module

    # Rewrite imports in tracked files
    files_modified = 0
    all_changes = []

    for file_path in tracked_files:
        if not file_path.startswith("stillme_compat/"):  # Don't modify our own shims
            path_obj = REPO_ROOT / file_path
            if path_obj.exists():
                changes = rewrite_imports_in_file(path_obj, import_mappings)
                if changes:
                    files_modified += 1
                    all_changes.extend(changes)

    # Save import rewrite diff
    diff_file = REPO_ROOT / "artifacts" / "import_rewrite_diff.txt"
    diff_file.parent.mkdir(parents=True, exist_ok=True)

    with open(diff_file, "w", encoding="utf-8") as f:
        f.write("Import Rewrite Diff\n")
        f.write("==================\n\n")
        f.write(f"Pilot clusters processed: {len(pilot_clusters)}\n")
        f.write(f"Compatibility shims created: {shims_created}\n")
        f.write(f"Files modified: {files_modified}\n")
        f.write(f"Total changes: {len(all_changes)}\n\n")
        f.write("Changes:\n")
        f.write("--------\n")
        for change in all_changes:
            f.write(f"{change}\n")

    logger.info("📊 Results:")
    logger.info(f"  - Pilot clusters processed: {len(pilot_clusters)}")
    logger.info(f"  - Compatibility shims created: {shims_created}")
    logger.info(f"  - Files modified: {files_modified}")
    logger.info(f"  - Total changes: {len(all_changes)}")
    logger.info(f"  - Import rewrite diff saved to: {diff_file}")


if __name__ == "__main__":
    main()
