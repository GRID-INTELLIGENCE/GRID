# Ecosystem Integration Architecture

## Overview

Phase 3 completes the probe architecture by merging it with two parallel MCP server processes running in the OpenCode session. The probe's internal governance analysis (Phase 2) is joined with external ecosystem signals to form a unified intelligence surface.

## The Three Pillars

### 1. Probe (Internal — Phase 2)
**Source:** `src/grid/probe/engine.py`

The governance probe scans GRID-main's codebase to map middleware, auth, gating, and security entities. It produces:
- Entity registry with 28+ governance entities
- Coverage scores by domain
- Dependency graph
- Findings (gaps, anomalies, observations)

### 2. Echoes Enforcement Pipeline (External Process #1)
**Source:** `echoes-server` MCP tool → `~/.echoes/audit.ndjson`

The echoes enforcement system tracks *behavioral* patterns across all MCP servers:
- **Audit trail**: 1,492+ events with status, source, tool, duration
- **Precedent tracking**: Recurrence detection with escalation levels (observed → flagged → restricted → blocked)
- **Enforcement state**: Aggregated status for the entire ecosystem

### 3. Seeds Ecosystem Scan Pipeline (External Process #2)
**Source:** `seeds-server` MCP tool → `~/.seeds-server/snapshots/`

The seeds scanner tracks *structural* health of every repository:
- **Health scores**: 0-100 per repo
- **Git state**: Branch, uncommitted changes, last commit
- **Issue detection**: Stale repos, missing git, configuration drift
- **Snapshots**: Longitudinal tracking for trend analysis

## How They Merge — The Ecosystem Bridge

```
┌─────────────────────────────────────────────────────────┐
│                  EcosystemBridge                        │
│                                                         │
│  ┌──────────┐   ┌──────────────┐   ┌───────────────┐   │
│  │ Echoes   │   │   Seeds      │   │  Eligibility  │   │
│  │ Audit +  │   │   Health +   │   │  check_the_   │   │
│  │ Enforce  │   │   Snapshots  │   │  line          │   │
│  └────┬─────┘   └──────┬───────┘   └───────┬───────┘   │
│       │                │                     │           │
│       ▼                ▼                     ▼           │
│  ingest_audit    ingest_ecosystem     ingest_line_audit │
│  ingest_enforce                                         │
│       │                │                     │           │
│       └────────┬───────┴─────────────────────┘           │
│                │                                         │
│         Normalized Models                                │
│   (AuditEvent, Precedent, RepoHealth,                   │
│    EnforcementState, EcosystemSnapshot,                  │
│    LineAuditResult)                                      │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  LumosOrchestrator   │
              │  6-Phase Pipeline    │
              └──────────────────────┘
```

## Lumos 6-Phase Pipeline

### Phase 1: PROBE
Read-only signal collection. Gathers the probe report and all ecosystem bridge state into a unified signal set.

### Phase 2: QUANTIFY
Computes PATH scores using weighted formula:

```
composite = health × 0.30
           + trust × 0.25
           + (1 - drift) × 0.20
           + (1 - fail) × 0.15
           + momentum × 0.10
```

| Dimension | Source | What it measures |
|-----------|--------|-----------------|
| Health | Seeds + Probe | Overall ecosystem + governance coverage |
| Trust | Echoes + Eligibility | Enforcement state + structural cleanliness |
| Drift | Eligibility + Seeds | Structural drift + uncommitted changes |
| Fail | Echoes | Audit failure rate + blocked precedents |
| Momentum | Seeds + Probe | Activity ratio + development progress |

### Phase 3: SORT
Ranks entities and assigns verdict tiers:

| Tier | Score Range | Meaning |
|------|------------|---------|
| FAST CLEAR | 65-100 | Proceed normally |
| WATCH | 50-64 | Proceed with monitoring |
| ACT | 35-49 | Targeted remediation needed |
| URGENT | 0-34 | Stop and fix immediately |

### Phase 4: GUIDE
Generates tier-specific sweep protocols (A through F) with prioritized, concrete actions for each entity.

### Phase 5: EXECUTE
Runs dependency-ordered verification gates:
1. `composite_score_valid` — score in 0-100 range
2. `no_blocked_precedents` — no blocked enforcement precedents
3. `ecosystem_minimum_health` — overall score >= 35
4. `line_audit_clean` — no structural drift findings

### Phase 6: EVOLVE
Checks evolution eligibility. Requires:
- All verification gates passed
- Composite score >= 65
- No URGENT-tier entities

## File Map

### Python (Execution Layer)
| File | Purpose |
|------|---------|
| `src/grid/probe/ecosystem.py` | Ecosystem bridge — ingests echoes + seeds data |
| `src/grid/probe/lumos.py` | Lumos orchestrator — 6-phase pipeline |

### YAML (Integration Layer)
| File | Purpose |
|------|---------|
| `config/probe/ecosystem.yaml` | Ecosystem integration config |

### JSON (Data Contract Layer)
| File | Purpose |
|------|---------|
| `schemas/probe-lumos-result.schema.json` | Lumos result schema |

### Tests
| File | Purpose |
|------|---------|
| `tests/probe/test_ecosystem.py` | Ecosystem bridge tests |
| `tests/probe/test_lumos.py` | Lumos orchestrator tests |

## Usage

```python
from grid.probe import ProbeEngine, EcosystemBridge, LumosOrchestrator

# Step 1: Run internal probe
engine = ProbeEngine.from_config()
probe_report = engine.run()

# Step 2: Build ecosystem bridge
bridge = EcosystemBridge()
bridge.ingest_ecosystem(seeds_scan_data)
bridge.ingest_enforcement(echoes_enforcement_data)
bridge.ingest_line_audit(eligibility_check_data)

# Step 3: Run lumos pipeline
orchestrator = LumosOrchestrator(bridge)
result = orchestrator.run_full(probe_report=probe_report)

# Step 4: Check result
print(f"Verdict: {result.verdict.value}")
print(f"Score: {result.composite_score:.1f}")
print(f"Evolution eligible: {result.evolution_eligible}")
```
