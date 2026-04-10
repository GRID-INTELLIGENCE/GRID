# Probe Usage Guide

## Quick Start

### Python API

```python
from grid.probe import ProbeEngine

# Load from YAML config (config/probe/probe.yaml + entities.yaml)
engine = ProbeEngine.from_config()
report = engine.run(write_output=True)

print(f"Entities: {report.total_entities}")
print(f"Score: {report.aggregate_score:.2%} ({report.aggregate_status.value})")
```

### Step-by-Step Execution

```python
from grid.probe import ProbeEngine

engine = ProbeEngine.from_config()

# 1. Load seed entities from catalog
seeds = engine.load_seeds()
print(f"Loaded {seeds} seed entities")

# 2. Discover new entities via AST + pattern scanning
discovered = engine.scan()
print(f"Discovered {discovered} new entities")

# 3. Generate report
report = engine.report(write_output=True)
```

### Default Config (no YAML required)

```python
from grid.probe import ProbeEngine

engine = ProbeEngine.with_defaults()
report = engine.run()
```

## Configuration

### Main Config: `config/probe/probe.yaml`

Controls scan targets, classification patterns, scoring weights, and feature flags.

**Key settings:**
- `probe.enabled` — Master switch (default: `true`)
- `scan.roots` — Directories to scan with entity type hints
- `classification.patterns` — Regex patterns for entity classification
- `scoring.domain_weights` — Importance multipliers per domain
- `scoring.thresholds` — Coverage score thresholds (healthy/degraded)
- `features.*` — Toggle individual probe subsystems

### Entity Catalog: `config/probe/entities.yaml`

Pre-seeded governance entities from the Phase 2.1 audit. The probe loads these first, then augments with discovered entities.

## Output Files

| File | Location | Description |
|------|----------|-------------|
| `probe-report.json` | `data/probe/` | Full structured report (conforms to `schemas/probe-report.schema.json`) |
| `entity-map.json` | `data/probe/` | Entity lookup map (conforms to `schemas/probe-entity-map.schema.json`) |
| `PROBE_REPORT.md` | `docs/probe/` | Human-readable Markdown report |

## Interpreting Results

### Coverage Scores

Each domain gets a score from 0.0 to 1.0:
- **HEALTHY** (>= 0.80): Domain is well-covered with mapped entities
- **DEGRADED** (>= 0.50): Partial coverage, gaps may exist
- **FAILING** (< 0.50): Significant gaps in entity mapping

### Findings

| Category | Meaning |
|----------|---------|
| `gap` | Missing entity or coverage hole |
| `anomaly` | Unexpected entity configuration |
| `observation` | Neutral finding for awareness |
| `recommendation` | Suggested improvement |

### Dependency Graph

The graph shows relationships between entities:
- `precedes` — Middleware A runs before Middleware B in the chain
- `depends_on` — Entity A requires Entity B to function
- `enforces` — Entity A enforces rules defined by Entity B
- `validates` — Entity A validates input/output for Entity B

## Extending the Probe

### Adding New Scan Targets

Edit `config/probe/probe.yaml`:

```yaml
scan:
  roots:
    # ... existing targets ...
    - path: "src/grid/new_module"
      entity_types: ["custom_type"]
```

### Adding Classification Patterns

```yaml
classification:
  patterns:
    # ... existing patterns ...
    - id: "cls-custom"
      match: "class.*CustomHandler"
      entity_type: "custom_type"
      domain: "custom_domain"
```

### Adding Seed Entities

Edit `config/probe/entities.yaml`:

```yaml
entities:
  # ... existing entities ...
  - id: "ent-custom-handler"
    label: "CustomHandler"
    type: "custom_type"
    domain: "custom_domain"
    source: "src/grid/new_module/handler.py"
    description: "Handles custom operations"
```
