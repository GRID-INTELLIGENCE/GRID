
-- ============================================================================
-- Databricks SQL Schema for Repository Analysis Data
-- ============================================================================
-- This schema is designed for read-only analysis and visualization.
-- All tables are optimized for analytical queries and join operations.

-- ============================================================================
-- FILES TABLE
-- ============================================================================
-- Stores file inventory and basic metadata
CREATE TABLE IF NOT EXISTS files (
    file_id STRING PRIMARY KEY,
    file_path STRING NOT NULL,
    file_size BIGINT,
    language STRING,
    depth INT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) USING DELTA
CLUSTER BY (language)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- MODULES TABLE
-- ============================================================================
-- Stores detailed module metrics
CREATE TABLE IF NOT EXISTS modules (
    module_id STRING PRIMARY KEY,
    file_path STRING NOT NULL,
    language STRING,
    lines INT,
    non_empty_lines INT,
    functions INT,
    classes INT,
    complexity_estimate DOUBLE,
    comment_density DOUBLE,
    has_docstrings BOOLEAN,
    side_effects ARRAY<STRING>,
    fan_in INT,
    fan_out INT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) USING DELTA
CLUSTER BY (language, fan_in)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- IMPORTS TABLE
-- ============================================================================
-- Stores import relationships (edges in dependency graph)
CREATE TABLE IF NOT EXISTS imports (
    import_id STRING PRIMARY KEY,
    source_module STRING NOT NULL,
    target_module STRING NOT NULL,
    import_name STRING,
    line_number INT,
    is_relative BOOLEAN,
    created_at TIMESTAMP,
    FOREIGN KEY (source_module) REFERENCES modules(module_id),
    FOREIGN KEY (target_module) REFERENCES modules(module_id)
) USING DELTA
CLUSTER BY (source_module, target_module)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- CANDIDATES TABLE
-- ============================================================================
-- Stores identified refactor candidates and reference components
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id STRING PRIMARY KEY,
    module_id STRING NOT NULL,
    candidate_type STRING,  -- 'refactor' or 'reference'
    score DOUBLE,
    fan_in INT,
    fan_out INT,
    lines INT,
    complexity DOUBLE,
    comment_density DOUBLE,
    has_docstrings BOOLEAN,
    rationale STRING,
    created_at TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(module_id)
) USING DELTA
CLUSTER BY (candidate_type, score)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- PARAMETER_ROUTING TABLE
-- ============================================================================
-- Stores parameter flow information (best-effort static analysis)
CREATE TABLE IF NOT EXISTS parameter_routing (
    routing_id STRING PRIMARY KEY,
    module_id STRING NOT NULL,
    function_name STRING,
    line_number INT,
    parameter_count INT,
    parameters ARRAY<STRING>,
    created_at TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(module_id)
) USING DELTA
CLUSTER BY (module_id)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- COMPARISONS TABLE
-- ============================================================================
-- Stores cross-project comparison results
CREATE TABLE IF NOT EXISTS comparisons (
    comparison_id STRING PRIMARY KEY,
    grid_module_id STRING NOT NULL,
    eufle_module_id STRING NOT NULL,
    comparison_type STRING,  -- 'similar', 'refactor', 'reference'
    similarity_score DOUBLE,
    recommendations ARRAY<STRING>,
    created_at TIMESTAMP
) USING DELTA
CLUSTER BY (comparison_type, similarity_score)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- ANALYTICAL VIEWS
-- ============================================================================

-- High-traffic modules view
CREATE OR REPLACE VIEW high_traffic_modules AS
SELECT
    m.module_id,
    m.file_path,
    m.language,
    m.fan_in,
    m.fan_out,
    m.lines,
    m.complexity_estimate,
    m.comment_density,
    m.has_docstrings,
    CASE
        WHEN m.fan_in >= 5 AND m.comment_density < 0.1 THEN 'high_traffic_low_docs'
        WHEN m.fan_in >= 5 AND m.complexity_estimate > m.lines * 0.1 THEN 'high_traffic_high_complexity'
        ELSE 'other'
    END AS risk_category
FROM modules m
WHERE m.fan_in >= 3
ORDER BY m.fan_in DESC, m.complexity_estimate DESC;

-- Dependency graph view (for visualization)
CREATE OR REPLACE VIEW dependency_graph AS
SELECT
    i.source_module,
    i.target_module,
    COUNT(*) as import_count,
    MAX(i.line_number) as last_import_line,
    m1.fan_in as source_fan_in,
    m2.fan_in as target_fan_in
FROM imports i
JOIN modules m1 ON i.source_module = m1.module_id
JOIN modules m2 ON i.target_module = m2.module_id
GROUP BY i.source_module, i.target_module, m1.fan_in, m2.fan_in;

-- Language statistics view
CREATE OR REPLACE VIEW language_statistics AS
SELECT
    language,
    COUNT(*) as module_count,
    SUM(lines) as total_lines,
    AVG(complexity_estimate) as avg_complexity,
    AVG(comment_density) as avg_comment_density,
    SUM(fan_in) as total_fan_in,
    SUM(fan_out) as total_fan_out
FROM modules
WHERE language IS NOT NULL
GROUP BY language
ORDER BY module_count DESC;

-- ============================================================================
-- EXAMPLE ANALYTICAL QUERIES
-- ============================================================================

-- Query 1: Top refactor candidates by score
-- SELECT
--     c.candidate_id,
--     m.file_path,
--     c.score,
--     c.fan_in,
--     c.complexity,
--     c.comment_density,
--     c.rationale
-- FROM candidates c
-- JOIN modules m ON c.module_id = m.module_id
-- WHERE c.candidate_type = 'refactor'
-- ORDER BY c.score DESC
-- LIMIT 20;

-- Query 2: Modules with most incoming dependencies
-- SELECT
--     m.module_id,
--     m.file_path,
--     m.fan_in,
--     m.complexity_estimate,
--     m.comment_density,
--     COUNT(i.import_id) as actual_import_count
-- FROM modules m
-- LEFT JOIN imports i ON i.target_module = m.module_id
-- GROUP BY m.module_id, m.file_path, m.fan_in, m.complexity_estimate, m.comment_density
-- ORDER BY m.fan_in DESC
-- LIMIT 20;

-- Query 3: Strongly connected components (circular dependencies)
-- WITH RECURSIVE dependency_path AS (
--     SELECT source_module, target_module, 1 as depth,
--            ARRAY(source_module) as path
--     FROM imports
--     WHERE source_module = target_module  -- Self-loops
--     UNION ALL
--     SELECT i.source_module, i.target_module, dp.depth + 1,
--            ARRAY_CONCAT(dp.path, ARRAY(i.target_module))
--     FROM imports i
--     JOIN dependency_path dp ON i.source_module = dp.target_module
--     WHERE dp.depth < 10  -- Limit depth
--       AND NOT ARRAY_CONTAINS(dp.path, i.target_module)  -- Avoid cycles
-- )
-- SELECT DISTINCT
--     source_module,
--     target_module,
--     depth
-- FROM dependency_path
-- WHERE source_module = target_module OR depth > 5;

-- Query 4: Parameter routing hotspots
-- SELECT
--     pr.module_id,
--     m.file_path,
--     COUNT(DISTINCT pr.function_name) as function_count,
--     AVG(pr.parameter_count) as avg_parameters,
--     MAX(pr.parameter_count) as max_parameters
-- FROM parameter_routing pr
-- JOIN modules m ON pr.module_id = m.module_id
-- GROUP BY pr.module_id, m.file_path
-- HAVING AVG(pr.parameter_count) > 5  -- High parameter count
-- ORDER BY avg_parameters DESC;

-- Query 5: Side-effect density by module
-- SELECT
--     module_id,
--     file_path,
--     language,
--     SIZE(side_effects) as side_effect_count,
--     lines,
--     ROUND(SIZE(side_effects)::DOUBLE / lines::DOUBLE * 100, 2) as side_effect_density
-- FROM modules
-- WHERE SIZE(side_effects) > 0
-- ORDER BY side_effect_density DESC
-- LIMIT 20;

-- ============================================================================
-- PARTITIONED TABLES FOR ENTERPRISE DECISION STUDIO
-- ============================================================================

-- ============================================================================
-- RELIABILITY_ASSETS TABLE (Partitioned by asset_type)
-- ============================================================================
-- Stores cache, properties, and reliability assets with threshold-based metrics
CREATE TABLE IF NOT EXISTS reliability_assets (
    asset_id STRING PRIMARY KEY,
    module_id STRING NOT NULL,
    asset_type STRING NOT NULL,  -- 'cache', 'property', 'metric'
    threshold_value DOUBLE,
    opportunistic_score DOUBLE,
    event_driven_score DOUBLE,
    hunch_score DOUBLE,
    reliability_rating DOUBLE,
    last_validated_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(module_id)
) USING DELTA
PARTITIONED BY (asset_type)
CLUSTER BY (module_id, asset_type)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

CREATE INDEX IF NOT EXISTS idx_reliability_assets_rating ON reliability_assets (reliability_rating DESC);
CREATE INDEX IF NOT EXISTS idx_reliability_assets_module ON reliability_assets (module_id, asset_type);

-- ============================================================================
-- CACHE_PROPERTIES TABLE (Partitioned by cache_backend)
-- ============================================================================
-- Stores cache configuration and performance metrics aligned with GRID cache patterns
CREATE TABLE IF NOT EXISTS cache_properties (
    cache_id STRING PRIMARY KEY,
    module_id STRING NOT NULL,
    cache_backend STRING NOT NULL,  -- 'InMemory', 'Redis', 'IndexedDB'
    ttl_seconds INT,
    hit_rate DOUBLE,
    eviction_policy STRING,
    max_size INT,
    current_size INT,
    properties_json STRING,  -- JSON string for flexible property storage
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(module_id)
) USING DELTA
PARTITIONED BY (cache_backend)
CLUSTER BY (module_id)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- CUSTOM_AGENCY_ATTRIBUTES TABLE
-- ============================================================================
-- Defines custom agency attributes for autonomous decision-making
CREATE TABLE IF NOT EXISTS custom_agency_attributes (
    agency_id STRING PRIMARY KEY,
    module_id STRING NOT NULL,
    attribute_name STRING NOT NULL,
    attribute_value STRING,
    attribute_type STRING NOT NULL,  -- 'boolean', 'string', 'number', 'json'
    validation_rule STRING,
    is_autonomous BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(module_id)
) USING DELTA
CLUSTER BY (module_id, attribute_name)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- ACCOUNTABILITY_DECISIONS TABLE (Partitioned by decision_status)
-- ============================================================================
-- Tracks accountability, responsibilities, rewards, setbacks, and handshake protocols
CREATE TABLE IF NOT EXISTS accountability_decisions (
    decision_id STRING PRIMARY KEY,
    review_id STRING,
    module_id STRING NOT NULL,
    decision_status STRING NOT NULL,  -- 'pending', 'approved', 'rejected', 'deferred'
    responsibility_owner STRING,
    reward_structure STRING,
    setback_conditions STRING,
    rules_json STRING,
    deliverables_json STRING,
    handshake_protocol_version STRING,
    transparency_level DOUBLE,
    feedback_loop_enabled BOOLEAN,
    deadline_timestamp TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (module_id) REFERENCES modules(module_id)
) USING DELTA
PARTITIONED BY (decision_status)
CLUSTER BY (review_id, decision_status)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- EXECUTIVE_REVIEW_VERIFICATION TABLE
-- ============================================================================
-- Tracks technical and executive review verification status
CREATE TABLE IF NOT EXISTS executive_review_verification (
    verification_id STRING PRIMARY KEY,
    project_folder STRING NOT NULL,
    technical_verification_passed BOOLEAN,
    executive_review_passed BOOLEAN,
    verification_timestamp TIMESTAMP,
    verification_metadata_json STRING,
    created_at TIMESTAMP
) USING DELTA
CLUSTER BY (project_folder)
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true'
);

-- ============================================================================
-- EXECUTIVE REVIEW SUMMARY VIEW
-- ============================================================================
CREATE OR REPLACE VIEW executive_review_summary AS
SELECT
    ra.asset_id,
    ra.module_id,
    m.file_path,
    ra.asset_type,
    ra.reliability_rating,
    ra.opportunistic_score,
    ra.event_driven_score,
    ra.hunch_score,
    CASE
        WHEN ra.reliability_rating >= 0.8 THEN 'PASS'
        WHEN ra.reliability_rating >= 0.6 THEN 'REVIEW'
        ELSE 'FAIL'
    END as threshold_status,
    ra.last_validated_at
FROM reliability_assets ra
JOIN modules m ON ra.module_id = m.module_id
WHERE ra.reliability_rating IS NOT NULL
ORDER BY ra.reliability_rating DESC;
