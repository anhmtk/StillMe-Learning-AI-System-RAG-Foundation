#!/usr/bin/env python3
"""
Feature Smoke Test for Coverage Generation
Safely imports modules from specific feature groups to generate coverage data.
"""

import os
import importlib.util
import sys
import pkgutil
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

def is_excluded(file_path: str, global_excludes: list) -> bool:
    """Checks if a file path should be excluded based on global exclude patterns."""
    path = Path(file_path).as_posix()
    for exclude in global_excludes:
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

def smoke_import_modules(root_packages: list[str], global_excludes: list[str]):
    """
    Attempts to import all Python modules under the given root packages safely.
    Logs warnings for failures but does not stop execution.
    """
    imported_count = 0
    failed_count = 0
    total_modules = 0
    
    # Add current directory to sys.path to ensure local modules are discoverable
    sys.path.insert(0, os.getcwd())

    all_modules = set()
    for root_package in root_packages:
        try:
            # Attempt to find the path for the root package
            spec = importlib.util.find_spec(root_package)
            if spec and spec.submodule_search_locations:
                root_path = spec.submodule_search_locations[0]
            else:
                # Fallback for packages not yet installed or in sys.path
                root_path = os.path.join(os.getcwd(), *root_package.split('.'))
                if not os.path.exists(root_path):
                    logger.warning(f"Root package path not found for {root_package}. Skipping.")
                    continue

            for importer, modname, ispkg in pkgutil.walk_packages([root_path], prefix=f"{root_package}."):
                module_path = os.path.join(importer.path, modname.replace('.', os.sep))
                if ispkg:
                    module_path = os.path.join(module_path, '__init__.py')
                else:
                    module_path += '.py'

                if is_excluded(module_path, global_excludes):
                    logger.debug(f"Excluding module: {modname} ({module_path})")
                    continue
                all_modules.add(modname)
        except Exception as e:
            logger.warning(f"Could not walk packages for {root_package}: {e}")

    total_modules = len(all_modules)
    logger.info(f"📦 Found {total_modules} modules to import")

    for modname in sorted(list(all_modules)):
        try:
            importlib.import_module(modname)
            imported_count += 1
        except (ImportError, SyntaxError, Exception) as e:
            logger.warning(f"Could not import {modname}: {e}")
            failed_count += 1
    
    logger.info(f"✅ Successfully imported: {imported_count}")
    logger.warning(f"❌ Failed to import: {failed_count}")
    logger.info(f"📊 Total modules processed: {total_modules}")

if __name__ == "__main__":
    from pathlib import Path
    REPO_ROOT = Path(__file__).parent.parent.parent
    
    # Define root packages and global excludes as per user's request
    ROOT_PACKAGES = ["stillme_core", "stillme_ethical_core"]
    GLOBAL_EXCLUDES = [
        ".git/", ".github/", ".venv/", "venv/", "env/", "site-packages/", "dist/", 
        "build/", "node_modules/", "artifacts/", "reports/", "htmlcov", 
        "__pycache__/", "*.egg-info/", ".sandbox/"
    ]
    
    logger.info("🔥 Starting smoke import for coverage generation...")
    smoke_import_modules(ROOT_PACKAGES, GLOBAL_EXCLUDES)
