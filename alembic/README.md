# Alembic Database Migrations

This directory contains database migration scripts for StillMe.

## Current Status

**Current Database**: SQLite (multiple files)
- `data/knowledge_retention.db`
- `data/continuum_memory.db`
- `data/rss_fetch_history.db`
- `data/accuracy_scores.db`
- `data/vector_db/chroma.sqlite3` (ChromaDB)

**Future Target**: PostgreSQL (single database with schemas)

## Migration Strategy

### Phase 1: Current State (SQLite)
- Alembic is set up but not actively used
- Current schema is managed via `CREATE TABLE IF NOT EXISTS` in code
- Migration scripts will be created to capture current schema

### Phase 2: PostgreSQL Migration Planning
- Design unified PostgreSQL schema
- Create migration scripts to move from SQLite to PostgreSQL
- Use Alembic for schema versioning going forward

## Usage

### Initialize Alembic (First Time)
```bash
# Alembic is already initialized
# To create first migration:
alembic revision --autogenerate -m "Initial schema"
```

### Create New Migration
```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration
alembic revision -m "Description of changes"
```

### Apply Migrations
```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific revision
alembic upgrade <revision_id>

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>
```

### Check Current Revision
```bash
# Show current revision
alembic current

# Show migration history
alembic history
```

## Configuration

- **Config File**: `alembic.ini`
- **Environment**: `alembic/env.py`
- **Database URL**: Set via `DATABASE_URL` environment variable (PostgreSQL) or `SQLITE_DB_PATH` (SQLite)

## Notes

- Alembic is currently set up for future PostgreSQL migration
- Current SQLite databases are managed directly in code
- Migration scripts will be created when PostgreSQL migration begins

