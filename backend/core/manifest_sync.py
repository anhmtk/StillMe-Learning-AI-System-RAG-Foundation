"""
Realtime Manifest Sync Module

This module provides realtime checking and auto-updating of StillMe's structural manifest.
When StillMe answers about its own architecture, it automatically checks if the manifest
is outdated and regenerates/injects it if needed.

This ensures StillMe always knows the truth about itself, even if developers forget to
update the manifest after code changes.
"""

import json
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def get_file_mtime(file_path: Path) -> float:
    """Get file modification time"""
    try:
        return file_path.stat().st_mtime
    except Exception:
        return 0


def find_validator_files(project_root: Path) -> list:
    """Find all validator-related Python files"""
    validator_files = []
    
    # Check stillme_core/validation/ directory
    validation_dir = project_root / "stillme_core" / "validation"
    if validation_dir.exists():
        for py_file in validation_dir.rglob("*.py"):
            if py_file.name != "__init__.py":
                validator_files.append(py_file)
    
    # Check backend/validators/ directory
    validators_dir = project_root / "backend" / "validators"
    if validators_dir.exists():
        for py_file in validators_dir.rglob("*.py"):
            if py_file.name != "__init__.py":
                validator_files.append(py_file)
    
    return validator_files


def is_manifest_outdated(project_root: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Check if manifest is outdated by comparing modification times with validator files.
    
    Args:
        project_root: Project root path (defaults to detecting from current file)
        
    Returns:
        (is_outdated, message) tuple
    """
    if project_root is None:
        # Detect project root from current file location
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
    
    manifest_path = project_root / "data" / "stillme_manifest.json"
    
    if not manifest_path.exists():
        return True, "Manifest not found - needs to be generated"
    
    manifest_mtime = get_file_mtime(manifest_path)
    validator_files = find_validator_files(project_root)
    
    if not validator_files:
        # No validator files found - assume manifest is up-to-date
        return False, "No validator files found (unexpected, but manifest exists)"
    
    newer_files = []
    for validator_file in validator_files:
        file_mtime = get_file_mtime(validator_file)
        if file_mtime > manifest_mtime:
            newer_files.append(validator_file)
    
    if newer_files:
        file_list = ", ".join([f.name for f in newer_files[:3]])
        if len(newer_files) > 3:
            file_list += f" (+{len(newer_files) - 3} more)"
        return True, f"Manifest outdated: {len(newer_files)} validator file(s) newer than manifest ({file_list})"
    
    return False, "Manifest is up-to-date"


def auto_regenerate_manifest(project_root: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Automatically regenerate manifest from codebase.
    
    Args:
        project_root: Project root path (defaults to detecting from current file)
        
    Returns:
        (success, message) tuple
    """
    if project_root is None:
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
    
    try:
        # Import generate_manifest function
        import sys
        sys.path.insert(0, str(project_root))
        
        from scripts.generate_manifest import generate_manifest
        
        # Generate manifest
        manifest = generate_manifest()
        
        # Save to file
        manifest_path = project_root / "data" / "stillme_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        total_validators = manifest.get("validation_framework", {}).get("total_validators", 0)
        num_layers = len(manifest.get("validation_framework", {}).get("layers", []))
        
        logger.info(f"✅ Auto-regenerated manifest: {total_validators} validators, {num_layers} layers")
        return True, f"Manifest regenerated: {total_validators} validators, {num_layers} layers"
        
    except Exception as e:
        logger.error(f"❌ Failed to auto-regenerate manifest: {e}", exc_info=True)
        return False, f"Failed to regenerate manifest: {str(e)}"


def auto_inject_manifest_to_rag(project_root: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Automatically inject manifest into RAG (ChromaDB).
    
    Args:
        project_root: Project root path (defaults to detecting from current file)
        
    Returns:
        (success, message) tuple
    """
    if project_root is None:
        current_file = Path(__file__).resolve()
        project_root = current_file.parent.parent.parent
    
    try:
        import sys
        sys.path.insert(0, str(project_root))
        
        from scripts.inject_manifest_to_rag import inject_manifest_to_rag
        
        # Inject manifest to RAG
        success = inject_manifest_to_rag()
        
        if success:
            logger.info("✅ Auto-injected manifest into RAG")
            return True, "Manifest injected into RAG successfully"
        else:
            logger.warning("⚠️ Failed to inject manifest into RAG")
            return False, "Failed to inject manifest into RAG"
            
    except Exception as e:
        logger.error(f"❌ Failed to auto-inject manifest to RAG: {e}", exc_info=True)
        return False, f"Failed to inject manifest: {str(e)}"


def ensure_manifest_synced(project_root: Optional[Path] = None, auto_fix: bool = True) -> Tuple[bool, str]:
    """
    Ensure manifest is synced with codebase. Check if outdated, and optionally auto-fix.
    
    This is the main function to call when StillMe answers about its architecture.
    
    Args:
        project_root: Project root path (defaults to detecting from current file)
        auto_fix: If True, automatically regenerate and inject manifest if outdated
        
    Returns:
        (is_synced, message) tuple
    """
    is_outdated, message = is_manifest_outdated(project_root)
    
    if not is_outdated:
        return True, message
    
    if not auto_fix:
        return False, message
    
    # Auto-fix: regenerate and inject
    logger.info(f"🔄 Manifest outdated detected: {message}")
    logger.info("🔄 Auto-regenerating manifest...")
    
    # Step 1: Regenerate manifest
    regen_success, regen_message = auto_regenerate_manifest(project_root)
    if not regen_success:
        return False, f"Manifest outdated and auto-regeneration failed: {regen_message}"
    
    # Step 2: Inject into RAG
    logger.info("🔄 Auto-injecting manifest into RAG...")
    inject_success, inject_message = auto_inject_manifest_to_rag(project_root)
    if not inject_success:
        return False, f"Manifest regenerated but injection failed: {inject_message}"
    
    return True, f"Manifest auto-synced: {regen_message}, {inject_message}"

