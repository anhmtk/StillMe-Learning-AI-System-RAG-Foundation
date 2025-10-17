#!/usr/bin/env python3
"""
Fix Database Schema - Add missing columns to proposals table
"""

import sqlite3
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_schema():
    """Fix database schema by adding missing columns"""
    
    # Database path
    db_path = Path("data/learning/proposals.db")
    
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Check current schema
            cursor.execute("PRAGMA table_info(proposals)")
            columns = [row[1] for row in cursor.fetchall()]
            logger.info(f"Current columns: {columns}")
            
            # Add missing columns
            missing_columns = [
                ("learning_notes", "TEXT"),
                ("learning_progress", "REAL DEFAULT 0.0"),
                ("final_progress", "REAL DEFAULT 100.0"),
                ("learning_completed_at", "TEXT"),
                ("current_objective", "INTEGER DEFAULT 0"),
                ("total_objectives", "INTEGER DEFAULT 1"),
                ("learning_started_at", "TEXT"),
                ("last_updated", "TEXT"),
            ]
            
            for column_name, column_type in missing_columns:
                if column_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE proposals ADD COLUMN {column_name} {column_type}")
                        logger.info(f"✅ Added column: {column_name} {column_type}")
                    except sqlite3.Error as e:
                        logger.error(f"❌ Failed to add column {column_name}: {e}")
                else:
                    logger.info(f"⏭️ Column already exists: {column_name}")
            
            # Update existing records with default values
            cursor.execute("""
                UPDATE proposals 
                SET 
                    learning_progress = 0.0,
                    final_progress = 100.0,
                    current_objective = 0,
                    total_objectives = 1,
                    learning_started_at = created_at,
                    last_updated = created_at
                WHERE learning_progress IS NULL
            """)
            
            updated_rows = cursor.rowcount
            logger.info(f"✅ Updated {updated_rows} existing records with default values")
            
            conn.commit()
            logger.info("✅ Database schema fixed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"❌ Error fixing database schema: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing Database Schema...")
    success = fix_database_schema()
    if success:
        print("✅ Database schema fixed successfully!")
    else:
        print("❌ Failed to fix database schema!")
        exit(1)
