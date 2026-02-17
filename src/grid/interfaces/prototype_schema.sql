-- SQLite Schema for Interfaces Metrics Dashboard (Local Prototype)
-- Mirrors Databricks schema for local testing

-- =============================================================================
-- Bridge Metrics Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS interfaces_bridge_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    trace_id TEXT NOT NULL,
    transfer_latency_ms REAL,
    compressed_size INTEGER,
    raw_size INTEGER,
    compression_ratio REAL,
    coherence_level REAL,
    entanglement_count INTEGER,
    integrity_check TEXT,
    success INTEGER NOT NULL DEFAULT 1, -- SQLite uses INTEGER for BOOLEAN
    source_module TEXT,
    metadata TEXT -- JSON string
);

-- Indexes for bridge metrics
CREATE INDEX IF NOT EXISTS idx_bridge_timestamp ON interfaces_bridge_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_bridge_trace_id ON interfaces_bridge_metrics(trace_id);
CREATE INDEX IF NOT EXISTS idx_bridge_source_module ON interfaces_bridge_metrics(source_module);
CREATE INDEX IF NOT EXISTS idx_bridge_timestamp_success ON interfaces_bridge_metrics(timestamp, success);

-- =============================================================================
-- Sensory Metrics Table
-- =============================================================================

CREATE TABLE IF NOT EXISTS interfaces_sensory_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    trace_id TEXT NOT NULL,
    modality TEXT NOT NULL, -- text, visual, audio, structured
    duration_ms REAL,
    coherence REAL,
    raw_size INTEGER,
    source TEXT,
    success INTEGER NOT NULL DEFAULT 1, -- SQLite uses INTEGER for BOOLEAN
    error_message TEXT,
    metadata TEXT -- JSON string
);

-- Indexes for sensory metrics
CREATE INDEX IF NOT EXISTS idx_sensory_timestamp ON interfaces_sensory_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_sensory_trace_id ON interfaces_sensory_metrics(trace_id);
CREATE INDEX IF NOT EXISTS idx_sensory_modality ON interfaces_sensory_metrics(modality);
CREATE INDEX IF NOT EXISTS idx_sensory_timestamp_modality ON interfaces_sensory_metrics(timestamp, modality);
CREATE INDEX IF NOT EXISTS idx_sensory_timestamp_success ON interfaces_sensory_metrics(timestamp, success);

-- =============================================================================
-- Metrics Summary Table (Aggregated)
-- =============================================================================

CREATE TABLE IF NOT EXISTS interfaces_metrics_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time_bucket TIMESTAMP NOT NULL, -- Hourly bucket
    interface_type TEXT NOT NULL, -- bridge or sensory
    total_operations INTEGER NOT NULL DEFAULT 0,
    successful_operations INTEGER NOT NULL DEFAULT 0,
    failed_operations INTEGER NOT NULL DEFAULT 0,
    avg_latency_ms REAL,
    p50_latency_ms REAL,
    p95_latency_ms REAL,
    p99_latency_ms REAL,
    avg_coherence REAL,
    throughput_per_second REAL,

    -- Additional aggregations for bridge
    avg_compression_ratio REAL,
    avg_entanglement_count REAL,

    -- Additional aggregations for sensory
    modality_distribution TEXT, -- JSON string with modality counts

    -- Unique constraint to prevent duplicate aggregations
    UNIQUE (time_bucket, interface_type)
);

-- Indexes for summary table
CREATE INDEX IF NOT EXISTS idx_summary_time_bucket ON interfaces_metrics_summary(time_bucket);
CREATE INDEX IF NOT EXISTS idx_summary_interface_type ON interfaces_metrics_summary(interface_type);
CREATE INDEX IF NOT EXISTS idx_summary_time_bucket_interface ON interfaces_metrics_summary(time_bucket, interface_type);

-- =============================================================================
-- Views for Common Queries
-- =============================================================================

-- View: Recent Bridge Metrics (last 24 hours)
DROP VIEW IF EXISTS interfaces_bridge_metrics_recent;
CREATE VIEW interfaces_bridge_metrics_recent AS
SELECT
    *,
    CASE
        WHEN raw_size > 0 THEN compressed_size * 100.0 / raw_size
        ELSE 0.0
    END AS compression_percentage
FROM interfaces_bridge_metrics
WHERE timestamp >= datetime('now', '-24 hours');

-- View: Recent Sensory Metrics (last 24 hours)
DROP VIEW IF EXISTS interfaces_sensory_metrics_recent;
CREATE VIEW interfaces_sensory_metrics_recent AS
SELECT
    *,
    CASE
        WHEN duration_ms > 0 THEN raw_size * 1000.0 / duration_ms
        ELSE 0.0
    END AS throughput_bytes_per_second
FROM interfaces_sensory_metrics
WHERE timestamp >= datetime('now', '-24 hours');

-- View: Hourly Summary
DROP VIEW IF EXISTS interfaces_metrics_hourly_summary;
CREATE VIEW interfaces_metrics_hourly_summary AS
SELECT
    time_bucket,
    interface_type,
    total_operations,
    successful_operations,
    failed_operations,
    CAST(successful_operations * 100.0 / NULLIF(total_operations, 0) AS REAL) AS success_rate_percentage,
    avg_latency_ms,
    p95_latency_ms,
    p99_latency_ms,
    throughput_per_second,
    avg_coherence
FROM interfaces_metrics_summary
ORDER BY time_bucket DESC;

-- View: Modality Distribution
DROP VIEW IF EXISTS interfaces_sensory_modality_distribution;
CREATE VIEW interfaces_sensory_modality_distribution AS
SELECT
    modality,
    COUNT(*) AS operation_count,
    AVG(duration_ms) AS avg_duration_ms,
    AVG(coherence) AS avg_coherence,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) AS success_count,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) AS failure_count,
    CAST(SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS REAL) AS success_rate_percentage
FROM interfaces_sensory_metrics
WHERE timestamp >= datetime('now', '-7 days')
GROUP BY modality
ORDER BY operation_count DESC;

-- =============================================================================
-- Notes
-- =============================================================================

-- SQLite Notes:
-- - Uses INTEGER (0/1) for BOOLEAN instead of BOOLEAN type
-- - Uses TEXT instead of STRING
-- - Uses REAL instead of DOUBLE
-- - Uses datetime('now', '-N hours/days') instead of INTERVAL syntax
-- - Views are created with DROP VIEW IF EXISTS for idempotency
-- - APPROX_PERCENTILE is not available in SQLite, use percentile calculations in Python
