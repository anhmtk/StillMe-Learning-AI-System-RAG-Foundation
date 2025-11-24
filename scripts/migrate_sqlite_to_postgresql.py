"""
Migration Script: SQLite to PostgreSQL
Migrates data from multiple SQLite databases to unified PostgreSQL database
"""

import os
import sys
import sqlite3
import argparse
import logging
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_sqlite_databases() -> Dict[str, str]:
    """Get paths to SQLite databases"""
    base_path = os.getenv("DATA_DIR", "data")
    return {
        "knowledge_retention": os.path.join(base_path, "knowledge_retention.db"),
        "rss_fetch_history": os.path.join(base_path, "rss_fetch_history.db"),
        "accuracy_scores": os.path.join(base_path, "accuracy_scores.db"),
        "continuum_memory": os.path.join(base_path, "continuum_memory.db"),
    }


def migrate_knowledge_retention(sqlite_path: str, pg_session, dry_run: bool = False):
    """Migrate knowledge_retention.db to PostgreSQL"""
    if not os.path.exists(sqlite_path):
        logger.warning(f"SQLite database not found: {sqlite_path}")
        return 0
    
    logger.info(f"Migrating knowledge_retention from {sqlite_path}...")
    
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    try:
        # Read from SQLite
        cursor.execute("SELECT * FROM knowledge_items")
        rows = cursor.fetchall()
        
        if dry_run:
            logger.info(f"  Would migrate {len(rows)} knowledge items")
            return len(rows)
        
        # Write to PostgreSQL
        from backend.database.models import KnowledgeItem
        migrated = 0
        for row in rows:
            item = KnowledgeItem(
                id=row['id'],
                content=row['content'],
                source=row['source'],
                knowledge_type=row['knowledge_type'],
                confidence_score=row.get('confidence_score', 0.0),
                retention_score=row.get('retention_score', 0.0),
                access_count=row.get('access_count', 0),
                last_accessed=datetime.fromisoformat(row['last_accessed']) if row.get('last_accessed') else datetime.utcnow(),
                created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else datetime.utcnow(),
                metadata=row.get('metadata', '{}')
            )
            pg_session.merge(item)  # Use merge to handle existing IDs
            migrated += 1
        
        pg_session.commit()
        logger.info(f"  Migrated {migrated} knowledge items")
        return migrated
        
    except Exception as e:
        pg_session.rollback()
        logger.error(f"Error migrating knowledge_retention: {e}")
        raise
    finally:
        sqlite_conn.close()


def migrate_rss_fetch_history(sqlite_path: str, pg_session, dry_run: bool = False):
    """Migrate rss_fetch_history.db to PostgreSQL"""
    if not os.path.exists(sqlite_path):
        logger.warning(f"SQLite database not found: {sqlite_path}")
        return 0
    
    logger.info(f"Migrating rss_fetch_history from {sqlite_path}...")
    
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    try:
        # Migrate cycles first
        cursor.execute("SELECT * FROM fetch_cycles")
        cycles = cursor.fetchall()
        
        if dry_run:
            logger.info(f"  Would migrate {len(cycles)} fetch cycles")
        else:
            from backend.database.models import RSSFetchCycle
            for cycle in cycles:
                cycle_obj = RSSFetchCycle(
                    id=cycle['id'],
                    cycle_number=cycle['cycle_number'],
                    started_at=datetime.fromisoformat(cycle['started_at']) if cycle.get('started_at') else datetime.utcnow(),
                    completed_at=datetime.fromisoformat(cycle['completed_at']) if cycle.get('completed_at') else None,
                    status=cycle.get('status', 'completed'),
                    items_fetched=cycle.get('items_fetched', 0),
                    items_added=cycle.get('items_added', 0),
                    items_filtered=cycle.get('items_filtered', 0)
                )
                pg_session.merge(cycle_obj)
            pg_session.commit()
            logger.info(f"  Migrated {len(cycles)} fetch cycles")
        
        # Migrate fetch items
        cursor.execute("SELECT * FROM fetch_items")
        items = cursor.fetchall()
        
        if dry_run:
            logger.info(f"  Would migrate {len(items)} fetch items")
            return len(items)
        
        from backend.database.models import RSSFetchItem
        migrated = 0
        for item in items:
            item_obj = RSSFetchItem(
                id=item['id'],
                cycle_id=item['cycle_id'],
                title=item['title'],
                source_url=item['source_url'],
                link=item.get('link'),
                summary=item.get('summary'),
                fetch_timestamp=datetime.fromisoformat(item['fetch_timestamp']) if item.get('fetch_timestamp') else datetime.utcnow(),
                status=item['status'],
                status_reason=item.get('status_reason'),
                vector_id=item.get('vector_id'),
                added_to_rag_at=datetime.fromisoformat(item['added_to_rag_at']) if item.get('added_to_rag_at') else None
            )
            pg_session.merge(item_obj)
            migrated += 1
        
        pg_session.commit()
        logger.info(f"  Migrated {migrated} fetch items")
        return migrated
        
    except Exception as e:
        pg_session.rollback()
        logger.error(f"Error migrating rss_fetch_history: {e}")
        raise
    finally:
        sqlite_conn.close()


def migrate_accuracy_scores(sqlite_path: str, pg_session, dry_run: bool = False):
    """Migrate accuracy_scores.db to PostgreSQL"""
    if not os.path.exists(sqlite_path):
        logger.warning(f"SQLite database not found: {sqlite_path}")
        return 0
    
    logger.info(f"Migrating accuracy_scores from {sqlite_path}...")
    
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM accuracy_scores")
        rows = cursor.fetchall()
        
        if dry_run:
            logger.info(f"  Would migrate {len(rows)} accuracy scores")
            return len(rows)
        
        from backend.database.models import AccuracyScore
        migrated = 0
        for row in rows:
            score = AccuracyScore(
                id=row['id'],
                question=row['question'],
                answer=row['answer'],
                score=row['score'],
                feedback=row.get('feedback'),
                user_id=row.get('user_id'),
                created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else datetime.utcnow()
            )
            pg_session.merge(score)
            migrated += 1
        
        pg_session.commit()
        logger.info(f"  Migrated {migrated} accuracy scores")
        return migrated
        
    except Exception as e:
        pg_session.rollback()
        logger.error(f"Error migrating accuracy_scores: {e}")
        raise
    finally:
        sqlite_conn.close()


def migrate_continuum_memory(sqlite_path: str, pg_session, dry_run: bool = False):
    """Migrate continuum_memory.db to PostgreSQL"""
    if not os.path.exists(sqlite_path):
        logger.warning(f"SQLite database not found: {sqlite_path}")
        return 0
    
    logger.info(f"Migrating continuum_memory from {sqlite_path}...")
    
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM continuum_memory_items")
        rows = cursor.fetchall()
        
        if dry_run:
            logger.info(f"  Would migrate {len(rows)} continuum memory items")
            return len(rows)
        
        from backend.database.models import ContinuumMemoryItem
        migrated = 0
        for row in rows:
            item = ContinuumMemoryItem(
                id=row['id'],
                content=row['content'],
                tier=row['tier'],
                access_count=row.get('access_count', 0),
                last_accessed=datetime.fromisoformat(row['last_accessed']) if row.get('last_accessed') else datetime.utcnow(),
                created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else datetime.utcnow(),
                metadata=row.get('metadata', '{}')
            )
            pg_session.merge(item)
            migrated += 1
        
        pg_session.commit()
        logger.info(f"  Migrated {migrated} continuum memory items")
        return migrated
        
    except Exception as e:
        pg_session.rollback()
        logger.error(f"Error migrating continuum_memory: {e}")
        raise
    finally:
        sqlite_conn.close()


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite databases to PostgreSQL")
    parser.add_argument("--postgres-url", type=str, help="PostgreSQL connection URL (or set DATABASE_URL env var)")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making changes")
    parser.add_argument("--create-tables", action="store_true", help="Create tables in PostgreSQL before migration")
    
    args = parser.parse_args()
    
    # Get PostgreSQL URL
    postgres_url = args.postgres_url or os.getenv("DATABASE_URL")
    if not postgres_url:
        logger.error("PostgreSQL URL required. Set DATABASE_URL env var or use --postgres-url")
        return 1
    
    if not postgres_url.startswith("postgresql://"):
        logger.error("Invalid PostgreSQL URL. Must start with postgresql://")
        return 1
    
    logger.info(f"Connecting to PostgreSQL: {postgres_url.split('@')[-1] if '@' in postgres_url else postgres_url}")
    
    # Create PostgreSQL engine
    engine = create_engine(postgres_url, echo=False)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Create tables if requested
        if args.create_tables:
            logger.info("Creating tables in PostgreSQL...")
            Base.metadata.create_all(engine)
            logger.info("✅ Tables created")
        
        # Get SQLite databases
        sqlite_dbs = get_sqlite_databases()
        
        total_migrated = 0
        
        # Migrate each database
        if os.path.exists(sqlite_dbs["knowledge_retention"]):
            total_migrated += migrate_knowledge_retention(sqlite_dbs["knowledge_retention"], session, args.dry_run)
        
        if os.path.exists(sqlite_dbs["rss_fetch_history"]):
            total_migrated += migrate_rss_fetch_history(sqlite_dbs["rss_fetch_history"], session, args.dry_run)
        
        if os.path.exists(sqlite_dbs["accuracy_scores"]):
            total_migrated += migrate_accuracy_scores(sqlite_dbs["accuracy_scores"], session, args.dry_run)
        
        if os.path.exists(sqlite_dbs["continuum_memory"]):
            total_migrated += migrate_continuum_memory(sqlite_dbs["continuum_memory"], session, args.dry_run)
        
        if args.dry_run:
            logger.info(f"✅ Dry run complete. Would migrate {total_migrated} total records")
        else:
            logger.info(f"✅ Migration complete. Migrated {total_migrated} total records")
        
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())

