# Data Visualization App Specification

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
