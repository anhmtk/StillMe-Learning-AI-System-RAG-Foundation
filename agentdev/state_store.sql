-- AgentDev State Store Schema
-- SQLite schema for persistent state management with checkpoint/resume capabilities
-- Designed for easy migration to PostgreSQL later

-- Jobs table - main job tracking
CREATE TABLE IF NOT EXISTS jobs (
    job_id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    config JSON,
    variables JSON,
    metadata JSON,
    created_by TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Job steps table - individual steps within jobs
CREATE TABLE IF NOT EXISTS job_steps (
    step_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    step_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    order_index INTEGER NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_ms INTEGER,
    command TEXT,
    working_directory TEXT,
    environment JSON,
    output JSON,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 300,
    dependencies JSON, -- Array of step_ids this step depends on
    artifacts JSON,    -- Array of artifact paths
    metadata JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
);

-- Checkpoints table - for resume capability
CREATE TABLE IF NOT EXISTS checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    step_id TEXT,
    checkpoint_type TEXT NOT NULL, -- 'job_start', 'step_start', 'step_complete', 'manual'
    data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
    FOREIGN KEY (step_id) REFERENCES job_steps(step_id) ON DELETE CASCADE
);

-- Artifacts table - track generated artifacts
CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    job_id TEXT NOT NULL,
    step_id TEXT,
    artifact_path TEXT NOT NULL,
    artifact_type TEXT NOT NULL, -- 'file', 'directory', 'url', 'data'
    size_bytes INTEGER,
    checksum TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
    FOREIGN KEY (step_id) REFERENCES job_steps(step_id) ON DELETE CASCADE
);

-- Events table - audit trail and event sourcing
CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    job_id TEXT,
    step_id TEXT,
    event_type TEXT NOT NULL,
    event_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    correlation_id TEXT,
    causation_id TEXT,
    metadata JSON,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE,
    FOREIGN KEY (step_id) REFERENCES job_steps(step_id) ON DELETE CASCADE
);

-- State snapshots table - for state management
CREATE TABLE IF NOT EXISTS state_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL, -- 'job', 'step', 'system'
    entity_id TEXT NOT NULL,
    snapshot_data JSON NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    metadata JSON
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_jobs_type ON jobs(job_type);

CREATE INDEX IF NOT EXISTS idx_job_steps_job_id ON job_steps(job_id);
CREATE INDEX IF NOT EXISTS idx_job_steps_status ON job_steps(status);
CREATE INDEX IF NOT EXISTS idx_job_steps_order ON job_steps(job_id, order_index);

CREATE INDEX IF NOT EXISTS idx_checkpoints_job_id ON checkpoints(job_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_type ON checkpoints(checkpoint_type);
CREATE INDEX IF NOT EXISTS idx_checkpoints_expires ON checkpoints(expires_at);

CREATE INDEX IF NOT EXISTS idx_artifacts_job_id ON artifacts(job_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_step_id ON artifacts(step_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_artifacts_expires ON artifacts(expires_at);

CREATE INDEX IF NOT EXISTS idx_events_job_id ON events(job_id);
CREATE INDEX IF NOT EXISTS idx_events_step_id ON events(step_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at);
CREATE INDEX IF NOT EXISTS idx_events_correlation ON events(correlation_id);

CREATE INDEX IF NOT EXISTS idx_snapshots_entity ON state_snapshots(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_version ON state_snapshots(entity_type, entity_id, version);

-- Triggers for updated_at timestamps
CREATE TRIGGER IF NOT EXISTS update_jobs_timestamp 
    AFTER UPDATE ON jobs
    BEGIN
        UPDATE jobs SET updated_at = CURRENT_TIMESTAMP WHERE job_id = NEW.job_id;
    END;

CREATE TRIGGER IF NOT EXISTS update_job_steps_timestamp 
    AFTER UPDATE ON job_steps
    BEGIN
        UPDATE job_steps SET updated_at = CURRENT_TIMESTAMP WHERE step_id = NEW.step_id;
    END;

-- Views for common queries
CREATE VIEW IF NOT EXISTS job_summary AS
SELECT 
    j.job_id,
    j.job_type,
    j.status,
    j.created_at,
    j.started_at,
    j.completed_at,
    j.duration_ms,
    COUNT(js.step_id) as total_steps,
    COUNT(CASE WHEN js.status = 'completed' THEN 1 END) as completed_steps,
    COUNT(CASE WHEN js.status = 'failed' THEN 1 END) as failed_steps,
    COUNT(CASE WHEN js.status = 'running' THEN 1 END) as running_steps
FROM jobs j
LEFT JOIN job_steps js ON j.job_id = js.job_id
GROUP BY j.job_id, j.job_type, j.status, j.created_at, j.started_at, j.completed_at, j.duration_ms;

CREATE VIEW IF NOT EXISTS step_dependencies AS
SELECT 
    js1.step_id as step_id,
    js1.job_id as job_id,
    js1.step_name as step_name,
    js2.step_id as depends_on_step_id,
    js2.step_name as depends_on_step_name,
    js2.status as depends_on_status
FROM job_steps js1
CROSS JOIN json_each(js1.dependencies) as deps
JOIN job_steps js2 ON deps.value = js2.step_id AND js1.job_id = js2.job_id;

-- Cleanup procedures (for TTL management)
CREATE VIEW IF NOT EXISTS expired_checkpoints AS
SELECT checkpoint_id FROM checkpoints 
WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP;

CREATE VIEW IF NOT EXISTS expired_artifacts AS
SELECT artifact_id FROM artifacts 
WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP;

-- Initialize with default data if needed
INSERT OR IGNORE INTO jobs (job_id, job_type, status, created_by) 
VALUES ('system-init', 'system', 'completed', 'system');

-- Version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT OR IGNORE INTO schema_version (version, description) 
VALUES (1, 'Initial AgentDev state store schema');
