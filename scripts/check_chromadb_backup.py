#!/usr/bin/env python3
"""
Script to check ChromaDB backup status and create backup if needed.

This script:
1. Checks if ChromaDB backup exists
2. Lists available backups
3. Optionally creates a new backup
"""

import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

from stillme_core.rag.chroma_client import ChromaClient
from stillme_core.rag.chroma_backup import ChromaBackupManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_backup_status(chroma_client: ChromaClient) -> Dict[str, Any]:
    """
    Check ChromaDB backup status.
    
    Returns:
        Dict with backup status information
    """
    logger.info("="*60)
    logger.info("ChromaDB Backup Status Check")
    logger.info("="*60)
    
    if not chroma_client.backup_manager:
        logger.warning("⚠️ ChromaDB Backup Manager not available")
        return {
            "status": "error",
            "message": "Backup manager not initialized",
            "backups_found": 0
        }
    
    backup_dir = Path(chroma_client.backup_manager.backup_directory)
    persist_dir = Path(chroma_client.backup_manager.persist_directory)
    
    logger.info(f"\n1. ChromaDB Persistence Directory:")
    logger.info(f"   Path: {persist_dir}")
    logger.info(f"   Exists: {persist_dir.exists()}")
    if persist_dir.exists():
        # Count files
        files = list(persist_dir.rglob("*"))
        file_count = len([f for f in files if f.is_file()])
        dir_count = len([f for f in files if f.is_dir()])
        logger.info(f"   Files: {file_count}, Directories: {dir_count}")
    
    logger.info(f"\n2. Backup Directory:")
    logger.info(f"   Path: {backup_dir}")
    logger.info(f"   Exists: {backup_dir.exists()}")
    
    # List backups
    backups = []
    if backup_dir.exists():
        backup_dirs = [d for d in backup_dir.iterdir() if d.is_dir()]
        for backup_path in backup_dirs:
            metadata_path = backup_path / "metadata.json"
            if metadata_path.exists():
                try:
                    import json
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    backups.append({
                        "name": backup_path.name,
                        "path": str(backup_path),
                        "timestamp": metadata.get("timestamp"),
                        "file_count": metadata.get("file_count", 0),
                        "total_size": metadata.get("total_size", 0)
                    })
                except Exception as e:
                    logger.warning(f"   ⚠️ Could not read metadata for {backup_path.name}: {e}")
            else:
                # Backup without metadata (old format?)
                backups.append({
                    "name": backup_path.name,
                    "path": str(backup_path),
                    "timestamp": None,
                    "file_count": None,
                    "total_size": None
                })
    
    logger.info(f"\n3. Available Backups:")
    if backups:
        logger.info(f"   ✅ Found {len(backups)} backup(s):")
        for i, backup in enumerate(backups, 1):
            logger.info(f"\n   [{i}] {backup['name']}")
            if backup['timestamp']:
                logger.info(f"       Timestamp: {backup['timestamp']}")
            if backup['file_count']:
                logger.info(f"       Files: {backup['file_count']}")
            if backup['total_size']:
                size_mb = backup['total_size'] / (1024 * 1024)
                logger.info(f"       Size: {size_mb:.2f} MB")
            logger.info(f"       Path: {backup['path']}")
    else:
        logger.warning("   ⚠️ No backups found!")
        logger.info("   💡 Run with --create-backup to create a backup now")
    
    # Check Railway volume backup (if applicable)
    logger.info(f"\n4. Railway Volume Backup:")
    logger.info("   Note: ChromaDB is stored in Railway persistent volume")
    logger.info("   Railway volume backups are separate from application backups")
    logger.info("   Check Railway dashboard → Service → Backups for volume backups")
    
    logger.info("\n" + "="*60)
    
    return {
        "status": "success",
        "backups_found": len(backups),
        "backups": backups,
        "backup_directory": str(backup_dir),
        "persist_directory": str(persist_dir)
    }


def create_backup(chroma_client: ChromaClient, backup_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a ChromaDB backup.
    
    Args:
        chroma_client: ChromaClient instance
        backup_name: Optional backup name
        
    Returns:
        Dict with backup creation result
    """
    logger.info("="*60)
    logger.info("Creating ChromaDB Backup")
    logger.info("="*60)
    
    if not chroma_client.backup_manager:
        logger.error("❌ ChromaDB Backup Manager not available")
        return {
            "status": "error",
            "message": "Backup manager not initialized"
        }
    
    try:
        backup_path = chroma_client.backup_manager.create_backup(backup_name)
        
        if backup_path:
            logger.info("\n" + "="*60)
            logger.info("✅ Backup created successfully!")
            logger.info(f"   Path: {backup_path}")
            logger.info("="*60)
            return {
                "status": "success",
                "backup_path": backup_path
            }
        else:
            logger.error("❌ Backup creation returned None")
            return {
                "status": "error",
                "message": "Backup creation returned None"
            }
    except Exception as e:
        logger.error(f"❌ Backup creation failed: {e}", exc_info=True)
        return {
            "status": "error",
            "message": str(e)
        }


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check ChromaDB backup status and optionally create backup"
    )
    parser.add_argument(
        "--create-backup",
        action="store_true",
        help="Create a new backup"
    )
    parser.add_argument(
        "--backup-name",
        type=str,
        help="Name for the backup (defaults to timestamp)"
    )
    args = parser.parse_args()
    
    try:
        # Initialize ChromaDB client
        logger.info("Initializing ChromaDB client...")
        chroma_client = ChromaClient()
        logger.info("✅ ChromaDB client initialized")
        
        # Check backup status
        status = check_backup_status(chroma_client)
        
        # Create backup if requested
        if args.create_backup:
            logger.info("\n" + "="*60)
            create_result = create_backup(chroma_client, args.backup_name)
            if create_result.get("status") == "success":
                logger.info("\n✅ Backup created successfully!")
                sys.exit(0)
            else:
                logger.error("\n❌ Backup creation failed!")
                sys.exit(1)
        else:
            if status.get("backups_found", 0) == 0:
                logger.warning("\n⚠️ No backups found!")
                logger.info("💡 Run with --create-backup to create a backup now")
                logger.info("   Example: python scripts/check_chromadb_backup.py --create-backup")
            else:
                logger.info(f"\n✅ Found {status.get('backups_found', 0)} backup(s)")
            
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

