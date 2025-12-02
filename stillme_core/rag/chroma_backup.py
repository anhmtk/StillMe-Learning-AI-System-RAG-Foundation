"""
ChromaDB Backup and Recovery System
Provides automated backup and recovery mechanisms for ChromaDB persistence
"""

import os
import shutil
import logging
from datetime import datetime
from typing import Optional, List
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ChromaBackupManager:
    """Manages backup and recovery for ChromaDB"""
    
    def __init__(self, persist_directory: str, backup_directory: str = None):
        """Initialize backup manager
        
        Args:
            persist_directory: ChromaDB persistence directory
            backup_directory: Directory to store backups (defaults to persist_directory/../backups)
        """
        self.persist_directory = Path(persist_directory)
        
        if backup_directory is None:
            # Default: ../backups relative to persist_directory
            self.backup_directory = self.persist_directory.parent / "backups" / "chromadb"
        else:
            self.backup_directory = Path(backup_directory)
        
        # Ensure backup directory exists
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"ChromaDB Backup Manager initialized: {self.backup_directory}")
    
    def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create a backup of ChromaDB data
        
        Args:
            backup_name: Optional backup name (defaults to timestamp)
            
        Returns:
            Path to backup directory
        """
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"chromadb_backup_{timestamp}"
        
        backup_path = self.backup_directory / backup_name
        
        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copy ChromaDB directory
            if self.persist_directory.exists():
                shutil.copytree(
                    self.persist_directory,
                    backup_path / "chromadb",
                    dirs_exist_ok=True
                )
                
                # Create metadata file
                metadata = {
                    "backup_name": backup_name,
                    "timestamp": datetime.now().isoformat(),
                    "source_directory": str(self.persist_directory),
                    "file_count": len(list(self.persist_directory.rglob("*"))),
                    "total_size": self._get_directory_size(self.persist_directory)
                }
                
                metadata_path = backup_path / "metadata.json"
                with open(metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"✅ Backup created: {backup_path}")
                logger.info(f"   Files: {metadata['file_count']}, Size: {metadata['total_size']} bytes")
                
                return str(backup_path)
            else:
                logger.warning(f"⚠️ ChromaDB directory does not exist: {self.persist_directory}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}", exc_info=True)
            raise
    
    def restore_backup(self, backup_name: str, verify: bool = True) -> bool:
        """Restore ChromaDB from backup
        
        Args:
            backup_name: Name of backup to restore
            verify: If True, verify backup before restoring
            
        Returns:
            True if successful, False otherwise
        """
        backup_path = self.backup_directory / backup_name
        
        if not backup_path.exists():
            logger.error(f"❌ Backup not found: {backup_path}")
            return False
        
        try:
            # Verify backup
            if verify:
                metadata_path = backup_path / "metadata.json"
                if not metadata_path.exists():
                    logger.warning(f"⚠️ Backup metadata not found: {metadata_path}")
                else:
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                    logger.info(f"📋 Backup metadata: {metadata}")
            
            # Create backup of current state before restore
            current_backup = self.create_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            logger.info(f"✅ Current state backed up: {current_backup}")
            
            # Restore from backup
            chromadb_backup = backup_path / "chromadb"
            if chromadb_backup.exists():
                # Remove existing directory
                if self.persist_directory.exists():
                    shutil.rmtree(self.persist_directory)
                
                # Restore from backup
                shutil.copytree(chromadb_backup, self.persist_directory)
                logger.info(f"✅ Restored from backup: {backup_name}")
                return True
            else:
                logger.error(f"❌ ChromaDB backup directory not found: {chromadb_backup}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Restore failed: {e}", exc_info=True)
            return False
    
    def list_backups(self) -> List[dict]:
        """List all available backups
        
        Returns:
            List of backup metadata dictionaries
        """
        backups = []
        
        if not self.backup_directory.exists():
            return backups
        
        for backup_dir in self.backup_directory.iterdir():
            if backup_dir.is_dir():
                metadata_path = backup_dir / "metadata.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, "r") as f:
                            metadata = json.load(f)
                        backups.append(metadata)
                    except Exception as e:
                        logger.warning(f"⚠️ Could not read backup metadata {metadata_path}: {e}")
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return backups
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """Remove old backups, keeping only the most recent ones
        
        Args:
            keep_count: Number of backups to keep
            
        Returns:
            Number of backups removed
        """
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            logger.info(f"📊 No cleanup needed: {len(backups)} backups (keeping {keep_count})")
            return 0
        
        # Remove old backups
        removed = 0
        for backup in backups[keep_count:]:
            backup_path = self.backup_directory / backup["backup_name"]
            try:
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                    removed += 1
                    logger.info(f"🗑️ Removed old backup: {backup['backup_name']}")
            except Exception as e:
                logger.warning(f"⚠️ Could not remove backup {backup_path}: {e}")
        
        logger.info(f"✅ Cleanup complete: Removed {removed} old backups")
        return removed
    
    def _get_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory
        
        Args:
            directory: Directory path
            
        Returns:
            Total size in bytes
        """
        total_size = 0
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.warning(f"⚠️ Could not calculate directory size: {e}")
        
        return total_size
    
    def get_backup_stats(self) -> dict:
        """Get statistics about backups
        
        Returns:
            Dictionary with backup statistics
        """
        backups = self.list_backups()
        
        total_size = sum(
            self._get_directory_size(self.backup_directory / b["backup_name"])
            for b in backups
        )
        
        return {
            "backup_count": len(backups),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "backup_directory": str(self.backup_directory),
            "oldest_backup": backups[-1]["timestamp"] if backups else None,
            "newest_backup": backups[0]["timestamp"] if backups else None
        }

