"""
Manifest Loader - Dynamic Source of Truth for StillMe Architecture

This module provides a single source of truth for StillMe's validation framework
structure by reading directly from stillme_manifest.json, which is automatically
generated from the codebase.

CRITICAL: This replaces all hardcoded validator counts and layer information.
When validators are added/removed/modified, generate_manifest.py updates the JSON,
and this module ensures StillMe always reads the latest information.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class ManifestLoader:
    """Loads and provides access to StillMe structural manifest"""
    
    _manifest: Optional[Dict] = None
    _manifest_path: Optional[Path] = None
    _last_load_time: Optional[datetime] = None
    
    @classmethod
    def _get_manifest_path(cls) -> Path:
        """Get path to manifest file"""
        if cls._manifest_path is None:
            # Try to find project root
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent
            manifest_path = project_root / "data" / "stillme_manifest.json"
            cls._manifest_path = manifest_path
        return cls._manifest_path
    
    @classmethod
    def load_manifest(cls, force_reload: bool = False) -> Optional[Dict]:
        """
        Load manifest from JSON file
        
        Args:
            force_reload: If True, reload even if already loaded
            
        Returns:
            Manifest dict or None if file not found
        """
        manifest_path = cls._get_manifest_path()
        
        # Return cached manifest if available and not forcing reload
        if not force_reload and cls._manifest is not None:
            return cls._manifest
        
        if not manifest_path.exists():
            logger.warning(f"⚠️ Manifest not found: {manifest_path}")
            logger.warning("💡 Run 'python scripts/generate_manifest.py' to generate manifest")
            return None
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                cls._manifest = json.load(f)
            cls._last_load_time = datetime.now()
            logger.debug(f"✅ Manifest loaded from {manifest_path}")
            return cls._manifest
        except Exception as e:
            logger.error(f"❌ Error loading manifest: {e}")
            return None
    
    @classmethod
    def get_validator_count(cls) -> Tuple[int, int]:
        """
        Get validator count and layer count from manifest
        
        Returns:
            Tuple of (total_validators, num_layers)
            Returns (0, 0) if manifest not available
        """
        manifest = cls.load_manifest()
        if not manifest:
            return (0, 0)
        
        try:
            vf = manifest.get("validation_framework", {})
            total_validators = vf.get("total_validators", 0)
            num_layers = len(vf.get("layers", []))
            return (total_validators, num_layers)
        except Exception as e:
            logger.error(f"❌ Error extracting validator count from manifest: {e}")
            return (0, 0)
    
    @classmethod
    def get_layers_info(cls) -> list:
        """
        Get detailed layer information from manifest
        
        Returns:
            List of layer dicts with structure:
            {
                "layer": int,
                "name": str,
                "description": str,
                "members": List[str]
            }
        """
        manifest = cls.load_manifest()
        if not manifest:
            return []
        
        try:
            vf = manifest.get("validation_framework", {})
            return vf.get("layers", [])
        except Exception as e:
            logger.error(f"❌ Error extracting layers from manifest: {e}")
            return []
    
    @classmethod
    def get_validator_summary(cls) -> str:
        """
        Get human-readable summary of validators and layers
        
        Returns:
            String like "19 validators total, organized into 7 layers"
        """
        total_validators, num_layers = cls.get_validator_count()
        if total_validators == 0 or num_layers == 0:
            return "Unknown (manifest not available)"
        return f"{total_validators} validators total, organized into {num_layers} layers"
    
    @classmethod
    def get_manifest_text_for_prompt(cls) -> str:
        """
        Get formatted text from manifest for injection into prompts
        
        Returns:
            Formatted string with validator and layer information
        """
        manifest = cls.load_manifest()
        if not manifest:
            return ""
        
        try:
            vf = manifest.get("validation_framework", {})
            total_validators = vf.get("total_validators", 0)
            num_layers = len(vf.get("layers", []))
            layers = vf.get("layers", [])
            
            text = f"**StillMe Validation Framework (from manifest):**\n"
            text += f"- Total Validators: {total_validators}\n"
            text += f"- Number of Layers: {num_layers}\n"
            text += f"- Active Validators per Response: {vf.get('min_active_validators', 0)}-{vf.get('max_active_validators', 0)} (depending on context)\n\n"
            
            text += "**Layers:**\n"
            for layer in layers:
                layer_num = layer.get("layer", 0)
                layer_name = layer.get("name", "")
                description = layer.get("description", "")
                members = layer.get("members", [])
                text += f"- Layer {layer_num} ({layer_name}): {', '.join(members)}\n"
                text += f"  {description}\n\n"
            
            return text
        except Exception as e:
            logger.error(f"❌ Error formatting manifest text: {e}")
            return ""
    
    @classmethod
    def get_validation_logic_hash(cls) -> Optional[str]:
        """Get validation logic hash from manifest"""
        manifest = cls.load_manifest()
        if not manifest:
            return None
        
        try:
            vf = manifest.get("validation_framework", {})
            return vf.get("validation_logic_hash")
        except Exception:
            return None


# Convenience functions for easy access
def get_validator_count() -> Tuple[int, int]:
    """Get validator count and layer count"""
    return ManifestLoader.get_validator_count()


def get_validator_summary() -> str:
    """Get human-readable validator summary"""
    return ManifestLoader.get_validator_summary()


def get_layers_info() -> list:
    """Get detailed layer information"""
    return ManifestLoader.get_layers_info()


def get_manifest_text_for_prompt() -> str:
    """Get formatted manifest text for prompt injection"""
    return ManifestLoader.get_manifest_text_for_prompt()

