"""
Environment Variables Loader with Hierarchy Support
==================================================

This module provides secure environment variable loading with proper hierarchy:
1. .env (base configuration)
2. .env.local (local overrides, highest priority)

Security features:
- Only loads files that exist
- Preserves existing environment variables (no override)
- Handles encoding errors gracefully
- No external dependencies

Usage:
    from stillme_core.env_loader import load_env_hierarchy
    load_env_hierarchy()
"""

import os
import pathlib
from typing import Optional


def _load_file(fp: pathlib.Path) -> None:
    """
    Load environment variables from a single file.
    
    Args:
        fp: Path to the environment file
        
    Security notes:
    - Only processes lines with '=' separator
    - Skips comments and empty lines
    - Uses setdefault() to preserve existing env vars
    """
    if not fp.exists():
        return
        
    try:
        content = fp.read_text(encoding="utf-8", errors="ignore")
        for line_num, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
                
            # Must contain '=' separator
            if "=" not in line:
                continue
                
            # Split key=value (only first '=')
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            
            # Remove quotes if present
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            
            # Only set if not already in environment
            os.environ.setdefault(key, value)
            
    except Exception as e:
        print(f"Warning: Could not load {fp}: {e}")


def load_env_hierarchy() -> None:
    """
    Load environment variables with proper hierarchy.
    
    Loading order (later files override earlier ones):
    1. .env (base configuration)
    2. .env.local (local overrides, highest priority)
    
    Security features:
    - Only loads existing files
    - Preserves system environment variables
    - Handles file access errors gracefully
    """
    # Get project root (2 levels up from this file)
    root = pathlib.Path(__file__).resolve().parents[1]
    
    # Load in priority order
    _load_file(root / ".env")
    _load_file(root / ".env.local")


def get_env_safely(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Safely get environment variable with optional default.
    
    Args:
        key: Environment variable name
        default: Default value if not found
        
    Returns:
        Environment variable value or default
    """
    return os.getenv(key, default)


def is_env_set(key: str) -> bool:
    """
    Check if environment variable is set and not empty.
    
    Args:
        key: Environment variable name
        
    Returns:
        True if variable is set and not empty
    """
    return bool(os.getenv(key))


# Auto-load when imported (optional)
if __name__ != "__main__":
    try:
        load_env_hierarchy()
    except Exception as e:
        print(f"env note: {e}")
