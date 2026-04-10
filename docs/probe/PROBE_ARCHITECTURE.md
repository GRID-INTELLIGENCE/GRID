# Probe Architecture

The governance probe is a four-layer system that maps, classifies, and reports on GRID's middleware, authentication, gating, and security entities.

## Four-Layer Design

```
+-------------------+     +-------------------+
|   YAML Config     |     |   JSON Schemas    |
|  config/probe/    |     |  schemas/probe-*  |
|                   |     |                   |
|  - probe.yaml     |     | - probe-report    |
|  - entities.yaml  |     | - probe-entity-map|
+--------+----------+     +--------+----------+
         |                          |
         |   reads config           |   validates output
         v                          v
+-------------------------------------------+
|          Python Execution Layer            |
|          src/grid/probe/                   |
|                                            |
|  config.py   - YAML loader + typed config  |
|  models.py   - Entity, Finding, Report     |
|  registry.py - Entity store + lookup       |
|  scanner.py  - AST + pattern discovery     |
|  reporter.py - JSON + Markdown output      |
|  engine.py   - Pipeline orchestrator       |
+--------+----------------------------------+
         |
         |   generates
         v
+-------------------+
|   Markdown Docs   |
|   docs/probe/     |
|                   |
|  - ARCHITECTURE   |
|  - ENTITY_CATALOG |
|  - USAGE_GUIDE    |
|  - PROBE_REPORT   |  <-- auto-generated
+-------------------+
```

## Layer Responsibilities

### YAML — Integration Layer (`config/probe/`)

- **probe.yaml**: Main configuration — scan targets, classification patterns, scoring weights, feature flags, output settings
- **entities.yaml**: Pre-seeded entity catalog from the Phase 2.1 governance audit. Contains the known 20+ middleware chain entities, auth dependencies, and governance gates

The YAML layer is the "dial" — tune scan targets, toggle features, adjust scoring weights without changing code.

### JSON — Structured Data Layer (`schemas/`)

- **probe-report.schema.json**: Full report schema — entities, findings, coverage scores, dependency graph, summary
- **probe-entity-map.schema.json**: Entity map schema — flat lookup of all entities keyed by ID with domain summaries

All JSON output from the probe conforms to these schemas. They serve as the data contract between the probe engine and any consumer (API, dashboard, CI pipeline).

### Python — Execution Layer (`src/grid/probe/`)

| Module | Purpose |
|--------|---------|
| `config.py` | Loads YAML, provides typed `ProbeConfig` with `from_yaml()` and `default()` constructors |
| `models.py` | Domain models — `Entity`, `Finding`, `CoverageScore`, `ProbeReport` (all dataclasses with `to_dict()`) |
| `registry.py` | `EntityRegistry` — central store with lookup by ID/domain/type, exports entity map |
| `scanner.py` | `EntityScanner` — AST parsing + regex pattern matching for entity discovery |
| `reporter.py` | `ProbeReporter` — generates JSON reports, entity maps, and Markdown summaries |
| `engine.py` | `ProbeEngine` — pipeline orchestrator: `run()` = seeds -> scan -> report |

### Markdown — Description Layer (`docs/probe/`)

- **PROBE_ARCHITECTURE.md** (this file): System design and layer responsibilities
- **PROBE_ENTITY_CATALOG.md**: Reference catalog of all known governance entities
- **PROBE_USAGE_GUIDE.md**: How to run the probe, interpret results, and extend it
- **PROBE_REPORT.md**: Auto-generated report from the last probe run

## Entity Discovery Pipeline

```
1. Load seed entities (config/probe/entities.yaml)
   └── 28+ pre-cataloged governance entities from Phase 2.1 audit
       (middleware chain, auth deps, governance gates)

2. AST scan (src/grid/probe/scanner.py)
   └── Parse Python files in configured scan targets
       └── Match class names against classification patterns
           (Middleware, Gate, Auth, Router, Enforcer, etc.)

3. Pattern scan (src/grid/probe/scanner.py)
   └── Regex search over file contents
       └── Match governance markers across all configured targets

4. Registration (src/grid/probe/registry.py)
   └── Deduplicate by entity ID
       └── Index by domain and type for fast lookup

5. Report generation (src/grid/probe/reporter.py)
   └── Calculate coverage scores per domain
       └── Build dependency graph (explicit + execution order)
           └── Output JSON (probe-report.schema.json) + Markdown
```

## Scoring System

Each domain gets a coverage score (0.0–1.0) weighted by importance:

| Domain | Weight | Description |
|--------|--------|-------------|
| governance | 1.5 | Governance gates, consent, value alignment |
| security | 1.4 | Security enforcers, threat detection |
| authentication | 1.3 | Auth dependencies, RBAC, JWT |
| safety | 1.3 | Safety middleware, guardrails |
| request_pipeline | 1.2 | Middleware chain, error handling |
| throttling | 1.1 | Rate limiting, circuit breakers |
| routing | 1.0 | API routers, endpoint registration |
| data_contract | 0.9 | Schema validation, Pydantic models |

**Aggregate score** = weighted average of all domain scores.

**Status thresholds:**
- >= 80% → HEALTHY
- >= 50% → DEGRADED
- < 50% → FAILING

## Integration Points

The probe integrates with existing GRID systems:

1. **Governance gates** (`src/grid/core_modules/governance_gates.py`) — entity source for GateVerdict/ConsentType/ValueCategory
2. **Legal governance** (`src/grid/legal/governance.py`) — GovernanceEngine policy registry
3. **Boundaries** (`boundaries/`) — BoundaryEngine, GateKeeper, transition gate contracts
4. **Middleware chain** (`src/application/mothership/middleware/`) — 19 middleware entities in execution order
5. **Auth system** (`src/application/mothership/dependencies.py`) — Auth/RequiredAuth/AdminAuth dependencies
6. **Feature flags** (`src/infrastructure/config/feature_flags.py`) — probe can be feature-flagged via env var
7. **API routes** (`config/api_routes.yaml`) — probe router registered for `/api/v1/probe`
