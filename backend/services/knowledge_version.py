"""
Knowledge Version Tracking Service

Tracks knowledge base version to enable cache invalidation when knowledge is updated.
Version increments after each learning cycle or manual knowledge update.
"""

import logging
import os
import json
import time
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Version file path
VERSION_FILE = Path("data/knowledge_version.json")


class KnowledgeVersionService:
    """
    Service to track and manage knowledge base version
    
    Version increments:
    - After each learning cycle (automated)
    - After manual knowledge updates (e.g., foundational knowledge added)
    - After ChromaDB collection changes
    
    Version format: timestamp-based (Unix timestamp) for easy comparison
    """
    
    def __init__(self):
        """Initialize knowledge version service"""
        self.version_file = VERSION_FILE
        self.version_file.parent.mkdir(parents=True, exist_ok=True)
        self._current_version: Optional[str] = None
    
    def get_current_version(self) -> str:
        """
        Get current knowledge version
        
        Returns:
            Version string (Unix timestamp as string)
        """
        # Always reload from file to get latest version (in case another process updated it)
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._current_version = data.get("version", self._generate_new_version())
            except Exception as e:
                logger.warning(f"Failed to load knowledge version: {e}, generating new version")
                self._current_version = self._generate_new_version()
        else:
            # First time - generate initial version
            self._current_version = self._generate_new_version()
            self._save_version()
        
        return self._current_version
    
    def _generate_new_version(self) -> str:
        """Generate new version based on current timestamp"""
        return str(int(time.time()))
    
    def _save_version(self):
        """Save version to file"""
        try:
            data = {
                "version": self._current_version,
                "updated_at": time.time(),
                "updated_at_iso": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            }
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save knowledge version: {e}")
    
    def increment_version(self) -> str:
        """
        Increment knowledge version (call after learning cycle or knowledge update)
        
        Returns:
            New version string
        """
        self._current_version = self._generate_new_version()
        self._save_version()
        logger.info(f"📦 Knowledge version incremented to: {self._current_version}")
        return self._current_version
    
    def reset(self):
        """Reset version (for testing or manual reset)"""
        self._current_version = self._generate_new_version()
        self._save_version()
        logger.info(f"🔄 Knowledge version reset to: {self._current_version}")


# Global instance
_knowledge_version_service: Optional[KnowledgeVersionService] = None


def get_knowledge_version_service() -> KnowledgeVersionService:
    """Get global knowledge version service instance"""
    global _knowledge_version_service
    if _knowledge_version_service is None:
        _knowledge_version_service = KnowledgeVersionService()
    return _knowledge_version_service


def get_knowledge_version() -> str:
    """Get current knowledge version (convenience function)"""
    return get_knowledge_version_service().get_current_version()


def increment_knowledge_version() -> str:
    """Increment knowledge version (convenience function)"""
    return get_knowledge_version_service().increment_version()

