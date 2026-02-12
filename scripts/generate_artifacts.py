#!/usr/bin/env python3
"""
Generate additional artifacts: database schema, entry points, visualization spec.
"""

import json
import re
from pathlib import Path


def generate_database_schema(output_dir: Path):
    """Generate Databricks SQL schema for repository analysis data."""

    schema = """
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
"""

    output_file = output_dir / "db_plan.sql"
    with open(output_file, "w") as f:
        f.write(schema)

    print(f"Database schema saved to {output_file}")


def identify_entry_points(analysis_dir: Path, repo_root: Path) -> list[dict]:
    """Identify entry points and integration hooks."""
    entry_points = []

    # Common entry point patterns for Python
    python_entry_patterns = {
        "main": [r'if __name__\s*==\s*["\']__main__["\']', r"def main\(", r"async def main\("],
        "cli": [r"@click\.(command|group)", r"argparse\.ArgumentParser", r"sys\.argv", r"from typer import"],
        "web_server": [r"app\s*=\s*FastAPI\(", r"app\s*=\s*Flask\(", r"uvicorn\.run\(", r"@app\.(get|post|put|delete)"],
        "setup": [r"setup\(", r"from setuptools import", r"__version__"],
    }

    # Entry point patterns for TypeScript/TSX
    typescript_entry_patterns = {
        "react_component": [
            r"export\s+(?:default\s+)?(?:function|const)\s+\w+\s*[:=]\s*(?:React\.)?(?:FC|FunctionComponent|Component)",
            r"export\s+(?:default\s+)?(?:function|const)\s+\w+\s*[:=]\s*\([^)]*\)\s*=>\s*\{",
            r"export\s+default\s+function\s+\w+\s*\(",
            r"export\s+(?:default\s+)?class\s+\w+\s+extends\s+(?:React\.)?Component",
        ],
        "exported_function": [
            r"export\s+(?:async\s+)?function\s+\w+\s*\(",
            r"export\s+const\s+\w+\s*[:=]\s*(?:async\s*)?\([^)]*\)\s*=>",
            r"export\s+default\s+(?:async\s+)?function",
        ],
        "typescript_interface": [
            r"export\s+(?:default\s+)?interface\s+\w+",
            r"export\s+(?:default\s+)?type\s+\w+\s*=",
            r"export\s+(?:default\s+)?enum\s+\w+",
        ],
        "web_entry": [r"ReactDOM\.render\(", r"createRoot\(", r"\.mount\(", r"Vite\.createApp\("],
    }

    manifest_file = analysis_dir / "manifest.json"
    if not manifest_file.exists():
        return []

    with open(manifest_file) as f:
        manifest = json.load(f)

    # Search in Python files
    python_files = [f for f in manifest.get("files", []) if f.get("language") == "Python"]

    for file_info in python_files[:500]:  # Limit search
        file_path = repo_root / file_info["path"]
        if not file_path.exists():
            continue

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for entry_type, patterns in python_entry_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content):
                        lines = content.split("\n")
                        matching_lines = [i + 1 for i, line in enumerate(lines) if re.search(pattern, line)]
                        entry_points.append(
                            {
                                "type": entry_type,
                                "path": file_info["path"],
                                "line_numbers": matching_lines[:5],
                                "pattern": pattern,
                                "safe_integration_points": identify_integration_points(
                                    content, file_info["path"], "Python"
                                ),
                            }
                        )
                        break
        except Exception:
            continue

    # Search in TypeScript/TSX files
    typescript_files = [f for f in manifest.get("files", []) if f.get("language") == "TypeScript"]

    for file_info in typescript_files[:500]:  # Limit search
        file_path = repo_root / file_info["path"]
        if not file_path.exists():
            continue

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for entry_type, patterns in typescript_entry_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content):
                        lines = content.split("\n")
                        matching_lines = [i + 1 for i, line in enumerate(lines) if re.search(pattern, line)]
                        entry_points.append(
                            {
                                "type": entry_type,
                                "path": file_info["path"],
                                "line_numbers": matching_lines[:5],
                                "pattern": pattern,
                                "safe_integration_points": identify_integration_points(
                                    content, file_info["path"], "TypeScript"
                                ),
                            }
                        )
                        break
        except Exception:
            continue

    # Deduplicate
    seen = set()
    unique_entry_points = []
    for ep in entry_points:
        key = (ep["path"], ep["type"])
        if key not in seen:
            seen.add(key)
            unique_entry_points.append(ep)

    return unique_entry_points


def identify_integration_points(content: str, file_path: str, language: str = "Python") -> list[dict]:
    """Identify safe integration points for instrumentation."""
    integration_points = []

    if language == "Python":
        # Look for function definitions (potential hook points)
        function_pattern = r"def\s+(\w+)\s*\("
        for match in re.finditer(function_pattern, content):
            func_name = match.group(1)
            line_num = content[: match.start()].count("\n") + 1

            # Check if it's a public function (not starting with _)
            if not func_name.startswith("_"):
                integration_points.append(
                    {
                        "type": "function",
                        "name": func_name,
                        "line_number": line_num,
                        "wrapper_pattern": f"# Wrapper pattern:\n# def {func_name}(...):\n#     # Log entry\n#     result = original_{func_name}(...)\n#     # Log exit\n#     return result",
                    }
                )

        # Look for class definitions
        class_pattern = r"class\s+(\w+)\s*(?:\(|:)"
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            line_num = content[: match.start()].count("\n") + 1

            if not class_name.startswith("_"):
                integration_points.append(
                    {
                        "type": "class",
                        "name": class_name,
                        "line_number": line_num,
                        "wrapper_pattern": f"# Wrapper pattern:\n# class {class_name}:\n#     def __init__(self, ...):\n#         # Log initialization\n#         pass",
                    }
                )

    elif language == "TypeScript":
        # Look for exported functions
        exported_function_pattern = r"export\s+(?:async\s+)?function\s+(\w+)\s*\("
        for match in re.finditer(exported_function_pattern, content):
            func_name = match.group(1)
            line_num = content[: match.start()].count("\n") + 1
            if not func_name.startswith("_"):
                integration_points.append(
                    {
                        "type": "function",
                        "name": func_name,
                        "line_number": line_num,
                        "wrapper_pattern": f"// Wrapper pattern:\n// export function {func_name}(...): ReturnType {{\n//   // Log entry\n//   const result = original_{func_name}(...);\n//   // Log exit\n//   return result;\n// }}",
                    }
                )

        # Look for React components
        react_component_pattern = r"export\s+(?:default\s+)?(?:function|const)\s+(\w+)\s*[:=]\s*(?:React\.)?(?:FC|FunctionComponent|Component)"
        for match in re.finditer(react_component_pattern, content):
            component_name = match.group(1)
            line_num = content[: match.start()].count("\n") + 1
            if not component_name.startswith("_"):
                integration_points.append(
                    {
                        "type": "react_component",
                        "name": component_name,
                        "line_number": line_num,
                        "wrapper_pattern": "# DISABLED: f-string syntax error - escaped",
                    }
                )

        # Look for arrow function exports
        arrow_function_pattern = r"export\s+const\s+(\w+)\s*[:=]\s*(?:async\s*)?\([^)]*\)\s*=>"
        for match in re.finditer(arrow_function_pattern, content):
            func_name = match.group(1)
            line_num = content[: match.start()].count("\n") + 1
            if not func_name.startswith("_"):
                integration_points.append(
                    {
                        "type": "function",
                        "name": func_name,
                        "line_number": line_num,
                        "wrapper_pattern": "# DISABLED: f-string syntax error - escaped",
                    }
                )

        # Look for TypeScript interfaces/types
        interface_pattern = r"export\s+(?:default\s+)?interface\s+(\w+)"
        for match in re.finditer(interface_pattern, content):
            interface_name = match.group(1)
            line_num = content[: match.start()].count("\n") + 1
            if not interface_name.startswith("_"):
                integration_points.append(
                    {
                        "type": "interface",
                        "name": interface_name,
                        "line_number": line_num,
                        "wrapper_pattern": f"// Integration point: TypeScript interface\n// export interface {interface_name} {{\n//   // Add monitoring fields here\n// }}",
                    }
                )

        # Look for class definitions
        class_pattern = r"export\s+(?:default\s+)?class\s+(\w+)"
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            line_num = content[: match.start()].count("\n") + 1
            if not class_name.startswith("_"):
                integration_points.append(
                    {
                        "type": "class",
                        "name": class_name,
                        "line_number": line_num,
                        "wrapper_pattern": f"// Wrapper pattern:\n// export class {class_name} {{\n//   // Add logging in constructor or methods\n// }}",
                    }
                )

    return integration_points[:10]  # Limit per file


def generate_entry_points_report(analysis_dir: Path, repo_root: Path, output_dir: Path):
    """Generate entry points and integration hooks report."""
    entry_points = identify_entry_points(analysis_dir, repo_root)

    # Add integration point details (if not already added)
    for ep in entry_points:
        if "safe_integration_points" not in ep or not ep["safe_integration_points"]:
            file_path = repo_root / ep["path"]
            if file_path.exists():
                try:
                    with open(file_path, encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    # Determine language from file extension
                    lang = (
                        "Python"
                        if ep["path"].endswith(".py")
                        else ("TypeScript" if ep["path"].endswith((".ts", ".tsx")) else "Python")
                    )
                    ep["safe_integration_points"] = identify_integration_points(content, ep["path"], lang)
                except Exception:
                    ep["safe_integration_points"] = []

    report = {"total_entry_points": len(entry_points), "entry_points_by_type": {}, "entry_points": entry_points}

    # Group by type
    for ep in entry_points:
        ep_type = ep["type"]
        if ep_type not in report["entry_points_by_type"]:
            report["entry_points_by_type"][ep_type] = []
        report["entry_points_by_type"][ep_type].append(ep)

    output_file = output_dir / "entry_points.json"
    with open(output_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Entry points report saved to {output_file}")
    return report


def generate_visualization_spec(output_dir: Path):
    """Generate data visualization app specification."""

    spec = """# Data Visualization App Specification

## Overview
A state-of-the-art, offline-first data visualization application for repository analysis data. The app provides interactive module-graph visualization, parameter routing traces, and component comparison dashboards.

## Technology Stack

### Recommended: React + D3.js (Single-Page Application)
- **Frontend**: React 18+ with TypeScript
- **Visualization**: D3.js v7+, Cytoscape.js, vis-network
- **State Management**: Zustand or Redux Toolkit
- **Data Loading**: Local JSON/GraphML files or Databricks SQL Warehouse connection
- **Build**: Vite for fast development and optimized production builds
- **Deployment**: Static files (can be served from local filesystem, Databricks workspace, or web server)

### Alternative: Databricks Notebooks
- **Platform**: Databricks SQL/Notebook environment
- **Visualization**: Plotly, Bokeh, or custom D3.js in notebooks
- **Data Source**: Databricks SQL Warehouse (tables from db_plan.sql)
- **Pros**: Direct integration with analysis data, SQL-driven queries
- **Cons**: Less interactive, requires Databricks access

## Core Features

### 1. Module Dependency Graph View
**Purpose**: Visualize import relationships and dependency flows

**Data Sources**:
- `module_graph.json` or `module_graph.graphml`
- Databricks: `dependency_graph` view

**Visualization**:
- Interactive force-directed graph (D3.js force simulation or Cytoscape.js)
- Nodes represent modules, edges represent imports
- Node sizing: proportional to fan-in (incoming dependencies)
- Node color: complexity (red = high, green = low)
- Edge thickness: number of imports between modules
- Click on node: show details panel (metrics, incoming/outgoing edges)
- Search/filter: filter by language, fan-in threshold, complexity range
- Zoom/pan: smooth interactions for large graphs

**Layouts**:
- Force-directed (default)
- Hierarchical (topological sort)
- Circular (grouped by language)
- Grid (for small subsets)

**Interactions**:
- Hover: tooltip with module name, metrics summary
- Click: select node, highlight connected nodes, show details panel
- Drag: reposition nodes manually
- Filter: hide nodes below threshold (e.g., fan-in < 2)
- Highlight: trace path from selected node to root or leaves

### 2. Parameter Routing Trace View
**Purpose**: Trace how parameters flow across module boundaries

**Data Sources**:
- `deep_dive/top_refactor_candidate.json` → `parameter_routing`
- Databricks: `parameter_routing` table

**Visualization**:
- Sankey diagram (parameter flow from source to destination)
- Flow chart with function nodes and parameter edges
- Timeline view: parameter flow through call chain
- Table view: sortable list of functions with parameter counts

**Features**:
- Select module: show all parameter routing within module
- Trace parameter: follow a parameter name through multiple functions
- Highlight hotspots: functions with high parameter counts (> 5)
- Filter: by parameter count, function name pattern

**Example Queries**:
- Show all functions with > 5 parameters
- Find longest parameter routing chain
- Identify functions that pass many parameters but don't use them

### 3. Component Comparison Dashboard
**Purpose**: Compare refactor candidates with reference components

**Data Sources**:
- `candidates.json`
- `cross_project_comparison.json` (if available)
- Databricks: `candidates` and `comparisons` tables

**Visualization**:
- Side-by-side comparison view
- Metrics radar chart (complexity, comment density, fan-in, lines, etc.)
- Before/after mockup for optimization recommendations
- Table view: sortable candidates with scores

**Features**:
- Select candidate: show comparison with top reference component
- Toggle metrics: show/hide specific metrics
- Export recommendations: generate markdown report with optimization suggestions
- Filter: by candidate type, score range, language

**Comparison Metrics**:
- Fan-in / Fan-out (traffic)
- Complexity estimate
- Comment density
- Lines of code
- Documentation quality (has_docstrings)
- Side-effect count

### 4. Language Statistics Dashboard
**Purpose**: Overview of repository composition by language

**Data Sources**:
- `language_summary.json`
- Databricks: `language_statistics` view

**Visualization**:
- Pie/bar chart: files by language
- Stacked bar: lines of code by language
- Metrics table: average complexity, comment density per language
- Heatmap: complexity vs comment density by language

### 5. Entry Points Explorer
**Purpose**: Identify runtime entry points and integration hooks

**Data Sources**:
- `entry_points.json`
- Repository files (read-only inspection)

**Visualization**:
- List view: entry points by type (main, CLI, web_server, setup)
- File tree: show entry points in context
- Code preview: show entry point code with line numbers
- Integration hook suggestions: show recommended instrumentation points

## Data Flow Architecture

```
┌─────────────────┐
│  Analysis JSON  │───┐
│   Artifacts     │   │
└─────────────────┘   │
                      │
┌─────────────────┐   │    ┌──────────────────┐
│  Databricks SQL │───┼───▶│  Data Layer      │
│   Warehouse     │   │    │  (Fetch/Transform)│
└─────────────────┘   │    └──────────────────┘
                      │           │
                      │           ▼
                      │    ┌──────────────────┐
                      │    │  State Store     │
                      │    │  (Zustand/Redux) │
                      └───▶└──────────────────┘
                                  │
                                  ▼
                           ┌──────────────────┐
                           │  Visualization   │
                           │  Components      │
                           └──────────────────┘
```

## Implementation Phases

### Phase 1: Core Setup
1. Initialize React + TypeScript project (Vite)
2. Set up routing (React Router)
3. Create data loading utilities (fetch JSON, or Databricks SQL client)
4. Set up state management

### Phase 2: Module Graph View
1. Integrate D3.js or Cytoscape.js
2. Load `module_graph.json` or query `dependency_graph` view
3. Implement force-directed layout
4. Add node/edge styling (size, color, thickness)
5. Add interactivity (hover, click, filter)

### Phase 3: Parameter Routing View
1. Load parameter routing data
2. Implement Sankey diagram (D3.js Sankey plugin)
3. Add trace functionality
4. Add filtering/search

### Phase 4: Comparison Dashboard
1. Load candidates data
2. Implement side-by-side comparison UI
3. Add radar chart (Chart.js or Recharts)
4. Generate recommendations report

### Phase 5: Additional Views
1. Language statistics
2. Entry points explorer
3. Export functionality (PNG, SVG, PDF reports)

## Data Table Schemas (for Databricks Integration)

See `db_plan.sql` for complete schemas. Key tables:
- `modules`: Core module metrics
- `imports`: Dependency edges
- `candidates`: Refactor candidates and reference components
- `parameter_routing`: Parameter flow data
- `comparisons`: Cross-project comparison results

## Sample Queries (for Databricks Version)

```sql
-- Load module graph for visualization
SELECT * FROM dependency_graph LIMIT 1000;

-- Get top refactor candidates
SELECT m.file_path, c.score, c.complexity, c.comment_density
FROM candidates c
JOIN modules m ON c.module_id = m.module_id
WHERE c.candidate_type = 'refactor'
ORDER BY c.score DESC
LIMIT 20;

-- Parameter routing for specific module
SELECT * FROM parameter_routing
WHERE module_id = 'path/to/module.py'
ORDER BY line_number;
```

## User Flows

### Flow 1: Investigate Refactor Candidate
1. User opens app → Component Comparison Dashboard
2. User selects top refactor candidate from table
3. App shows: metrics, comparison with reference component, recommendations
4. User clicks "View in Module Graph" → Module Graph View opens with candidate highlighted
5. User explores dependencies: sees incoming/outgoing edges, related modules
6. User clicks "Parameter Routing" → Parameter Routing View shows function-level analysis
7. User exports report with findings

### Flow 2: Compare Projects (GRID ↔ EUFLE)
1. User opens Comparison Dashboard
2. App loads `cross_project_comparison.json`
3. User sees list of similar modules with similarity scores
4. User selects a comparison → side-by-side view shows metrics from both projects
5. App suggests optimizations based on differences
6. User clicks "View in Graph" → Module Graph View shows both modules and their contexts

### Flow 3: Explore Architecture
1. User opens Module Graph View
2. App loads full dependency graph (may sample large graphs)
3. User filters by language: "Python only"
4. User applies layout: "Hierarchical"
5. User identifies hub modules (high fan-in) by color/size
6. User drills down: clicks on hub → sees details, parameter routing, candidates
7. User exports subgraph as PNG/SVG for documentation

## File Structure (React App)

```
apps/repo-visualizer/
├── src/
│   ├── components/
│   │   ├── ModuleGraph/
│   │   │   ├── ModuleGraphView.tsx
│   │   │   ├── GraphNode.tsx
│   │   │   └── GraphEdge.tsx
│   │   ├── ParameterRouting/
│   │   │   ├── ParameterRoutingView.tsx
│   │   │   └── SankeyDiagram.tsx
│   │   ├── Comparison/
│   │   │   ├── ComparisonDashboard.tsx
│   │   │   └── MetricsRadar.tsx
│   │   └── EntryPoints/
│   │       └── EntryPointsExplorer.tsx
│   ├── data/
│   │   ├── loaders.ts          # Load JSON or query Databricks
│   │   └── transformers.ts     # Transform data for visualization
│   ├── store/
│   │   └── analysisStore.ts    # Zustand store for app state
│   ├── types/
│   │   └── analysis.ts         # TypeScript types
│   └── App.tsx
├── public/
│   └── data/                   # Place analysis JSON files here
│       ├── module_graph.json
│       ├── candidates.json
│       └── ...
├── package.json
└── vite.config.ts
```

## Example Component (Module Graph)

```typescript
// src/components/ModuleGraph/ModuleGraphView.tsx
import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { useAnalysisStore } from '../../store/analysisStore';

export function ModuleGraphView() {
  const svgRef = useRef<SVGSVGElement>(null);
  const { moduleGraph, selectedNode, setSelectedNode } = useAnalysisStore();

  useEffect(() => {
    if (!moduleGraph || !svgRef.current) return;

    const svg = d3.select(svgRef.current);
    const width = 1200;
    const height = 800;

    // Create force simulation
    const simulation = d3.forceSimulation(moduleGraph.nodes)
      .force('link', d3.forceLink(moduleGraph.edges).id(d => d.id))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2));

    // Render edges
    const links = svg.selectAll('.link')
      .data(moduleGraph.edges)
      .enter()
      .append('line')
      .attr('class', 'link')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.6);

    // Render nodes
    const nodes = svg.selectAll('.node')
      .data(moduleGraph.nodes)
      .enter()
      .append('circle')
      .attr('class', 'node')
      .attr('r', d => Math.sqrt(d.fan_in) * 2 + 5)
      .attr('fill', d => d3.interpolateYlOrRd(d.complexity / 100))
      .on('click', (event, d) => setSelectedNode(d))
      .call(d3.drag()
        .on('start', dragStarted)
        .on('drag', dragged)
        .on('end', dragEnded));

    // Update positions
    simulation.on('tick', () => {
      links
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);

      nodes
        .attr('cx', d => d.x)
        .attr('cy', d => d.y);
    });

    function dragStarted(event, d) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(event, d) {
      d.fx = event.x;
      d.fy = event.y;
    }

    function dragEnded(event, d) {
      if (!event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
  }, [moduleGraph, selectedNode]);

  return (
    <div className="module-graph-view">
      <svg ref={svgRef} width="1200" height="800" />
      {selectedNode && (
        <div className="details-panel">
          <h3>{selectedNode.path}</h3>
          <p>Fan-in: {selectedNode.fan_in}</p>
          <p>Complexity: {selectedNode.complexity}</p>
        </div>
      )}
    </div>
  );
}
```

## Deployment Options

1. **Local Static Files**: Serve from `dist/` folder using any web server
2. **Databricks Workspace**: Upload to Databricks Files (DBFS) or use Databricks Asset Bundles
3. **GitHub Pages**: Deploy to GitHub Pages for sharing
4. **Docker Container**: Package as Docker image with nginx

## Performance Considerations

- **Large Graphs**: Use sampling/aggregation for graphs > 1000 nodes
- **Lazy Loading**: Load detailed data on demand (e.g., parameter routing)
- **Virtual Scrolling**: For large tables/lists
- **Web Workers**: Offload heavy computations (graph layout) to web workers
- **Caching**: Cache parsed JSON data in IndexedDB or localStorage

## Security & Privacy

- All data processing happens client-side (no server uploads)
- Secrets are already redacted in source JSON files
- No network requests unless explicitly connecting to Databricks (with auth)
- Data never leaves local filesystem (for static file version)
"""

    output_file = output_dir / "visualization_spec.md"
    with output_file.open("w", encoding="utf-8") as f:
        f.write(spec)

    print(f"Visualization spec saved to {output_file}")


def main():
    """Main entry point."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Generate additional artifacts")
    parser.add_argument("--analysis-dir", required=True, help="Analysis output directory")
    parser.add_argument("--repo-root", required=True, help="Repository root path")
    parser.add_argument("--output-dir", required=True, help="Output directory for artifacts")

    args = parser.parse_args()

    analysis_dir = Path(args.analysis_dir)
    repo_root = Path(args.repo_root)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate database schema
    generate_database_schema(output_dir)

    # Generate entry points report
    if analysis_dir.exists() and repo_root.exists():
        generate_entry_points_report(analysis_dir, repo_root, output_dir)

    # Generate visualization spec
    generate_visualization_spec(output_dir)

    print("All artifacts generated successfully!")


if __name__ == "__main__":
    main()
