# Database Migration Planning

## Current State

### SQLite Databases (Multiple Files)
1. **`data/knowledge_retention.db`**
   - Tables: `knowledge_items`, `learning_sessions`, `knowledge_relationships`
   - Purpose: Track learned knowledge with retention scores

2. **`data/continuum_memory.db`**
   - Tables: `tier_metrics`, `tier_audit`, `forgetting_metrics`
   - Purpose: Continuum Memory tiered storage system

3. **`data/rss_fetch_history.db`**
   - Tables: `rss_fetch_cycles`, `rss_fetch_items`
   - Purpose: Track RSS fetch operations and status

4. **`data/accuracy_scores.db`**
   - Tables: `accuracy_scores`, `performance_trends`, `learning_objectives`
   - Purpose: Track accuracy and performance metrics

5. **`data/vector_db/chroma.sqlite3`**
   - Managed by ChromaDB
   - Purpose: Vector embeddings storage

### Current Schema Management
- Schema defined via `CREATE TABLE IF NOT EXISTS` in code
- No version control for schema changes
- Manual migration required for schema updates

## Migration Strategy

### Phase 1: Alembic Setup (✅ Completed)
- ✅ Alembic initialized
- ✅ Configuration files created
- ✅ Environment setup for SQLite and PostgreSQL

### Phase 2: Schema Documentation (Next)
- Document all current SQLite schemas
- Create SQLAlchemy models for each database
- Create initial Alembic migration to capture current state

### Phase 3: PostgreSQL Schema Design
- Design unified PostgreSQL database with schemas:
  - `knowledge` schema: knowledge_retention tables
  - `continuum` schema: continuum_memory tables
  - `rss` schema: rss_fetch_history tables
  - `accuracy` schema: accuracy_scores tables
  - `vector` schema: ChromaDB metadata (if needed)

### Phase 4: Data Migration Scripts
- Create scripts to migrate data from SQLite to PostgreSQL
- Handle data type conversions
- Preserve relationships and foreign keys
- Test migration on staging environment

### Phase 5: Application Updates
- Update connection strings
- Replace SQLite-specific code with SQLAlchemy ORM
- Add connection pooling
- Update tests

## PostgreSQL Schema Design (Draft)

### Unified Database Structure
```sql
-- Main database: stillme_production

-- Knowledge Retention Schema
CREATE SCHEMA IF NOT EXISTS knowledge;
CREATE TABLE knowledge.knowledge_items (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    knowledge_type TEXT NOT NULL,
    confidence_score REAL DEFAULT 0.0,
    retention_score REAL DEFAULT 0.0,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE knowledge.learning_sessions (
    id SERIAL PRIMARY KEY,
    session_type TEXT NOT NULL,
    content_learned TEXT NOT NULL,
    accuracy_score REAL DEFAULT 0.0,
    retention_improvement REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE knowledge.knowledge_relationships (
    id SERIAL PRIMARY KEY,
    source_id INTEGER NOT NULL REFERENCES knowledge.knowledge_items(id),
    target_id INTEGER NOT NULL REFERENCES knowledge.knowledge_items(id),
    relationship_type TEXT NOT NULL,
    strength REAL DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Continuum Memory Schema
CREATE SCHEMA IF NOT EXISTS continuum;
CREATE TABLE continuum.tier_metrics (
    item_id TEXT PRIMARY KEY,
    tier TEXT NOT NULL,
    surprise_score REAL DEFAULT 0.0,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE continuum.tier_audit (
    id SERIAL PRIMARY KEY,
    item_id TEXT NOT NULL,
    from_tier TEXT NOT NULL,
    to_tier TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE continuum.forgetting_metrics (
    id SERIAL PRIMARY KEY,
    tier TEXT NOT NULL,
    forgotten_count INTEGER DEFAULT 0,
    total_count INTEGER DEFAULT 0,
    forgetting_rate REAL DEFAULT 0.0,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- RSS Fetch History Schema
CREATE SCHEMA IF NOT EXISTS rss;
CREATE TABLE rss.fetch_cycles (
    id SERIAL PRIMARY KEY,
    cycle_number INTEGER NOT NULL UNIQUE,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status TEXT NOT NULL,
    items_fetched INTEGER DEFAULT 0,
    items_added INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE TABLE rss.fetch_items (
    id SERIAL PRIMARY KEY,
    cycle_id INTEGER NOT NULL REFERENCES rss.fetch_cycles(id),
    feed_url TEXT NOT NULL,
    item_title TEXT,
    item_link TEXT,
    item_published TIMESTAMP,
    status TEXT NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Accuracy Scores Schema
CREATE SCHEMA IF NOT EXISTS accuracy;
CREATE TABLE accuracy.accuracy_scores (
    id SERIAL PRIMARY KEY,
    question TEXT NOT NULL,
    expected_answer TEXT,
    actual_answer TEXT NOT NULL,
    accuracy_score REAL NOT NULL,
    scoring_method TEXT NOT NULL,
    context_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE accuracy.performance_trends (
    id SERIAL PRIMARY KEY,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE accuracy.learning_objectives (
    id SERIAL PRIMARY KEY,
    objective_text TEXT NOT NULL,
    target_score REAL NOT NULL,
    current_score REAL DEFAULT 0.0,
    status TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_knowledge_items_created_at ON knowledge.knowledge_items(created_at);
CREATE INDEX idx_knowledge_items_retention_score ON knowledge.knowledge_items(retention_score);
CREATE INDEX idx_continuum_tier_metrics_tier ON continuum.tier_metrics(tier);
CREATE INDEX idx_rss_fetch_cycles_status ON rss.fetch_cycles(status);
CREATE INDEX idx_accuracy_scores_created_at ON accuracy.accuracy_scores(created_at);
```

## Migration Steps

### 1. Backup Current Data
```bash
# Backup all SQLite databases
cp data/knowledge_retention.db data/knowledge_retention.db.backup
cp data/continuum_memory.db data/continuum_memory.db.backup
cp data/rss_fetch_history.db data/rss_fetch_history.db.backup
cp data/accuracy_scores.db data/accuracy_scores.db.backup
```

### 2. Create PostgreSQL Database
```sql
CREATE DATABASE stillme_production;
\c stillme_production
```

### 3. Run Alembic Migrations
```bash
# Set DATABASE_URL environment variable
export DATABASE_URL=postgresql://user:password@localhost/stillme_production

# Run migrations
alembic upgrade head
```

### 4. Migrate Data
```bash
# Run data migration script
python scripts/migrate_sqlite_to_postgres.py
```

### 5. Verify Data Integrity
```bash
# Run verification script
python scripts/verify_migration.py
```

### 6. Update Application
- Update `.env` with PostgreSQL connection string
- Deploy updated code
- Monitor for errors

## Rollback Plan

If migration fails:
1. Stop application
2. Restore SQLite databases from backup
3. Revert code changes
4. Restart application with SQLite

## Timeline Estimate

- **Phase 1**: ✅ Completed (Alembic setup)
- **Phase 2**: 1-2 weeks (Schema documentation)
- **Phase 3**: 1 week (PostgreSQL schema design)
- **Phase 4**: 2-3 weeks (Data migration scripts)
- **Phase 5**: 1-2 weeks (Application updates)
- **Testing**: 1 week
- **Total**: 6-9 weeks

## Risks & Mitigation

### Risk: Data Loss
- **Mitigation**: Full backup before migration, test on staging first

### Risk: Downtime
- **Mitigation**: Zero-downtime migration strategy, dual-write during transition

### Risk: Performance Issues
- **Mitigation**: Load testing, connection pooling, query optimization

### Risk: Schema Mismatches
- **Mitigation**: Comprehensive testing, migration scripts with validation

## Next Steps

1. ✅ Complete Alembic setup (Done)
2. Document all current SQLite schemas
3. Create SQLAlchemy models
4. Design PostgreSQL schema
5. Create migration scripts
6. Test on staging environment

