# Intelligent Skills System (ISS)

The Intelligent Skills System (ISS) is a dynamic, self-organizing ecosystem for managing and executing computational skills within the GRID framework. It extends the basic skills framework with automated discovery, persistent intelligence, performance guarding, and lifecycle management.

## Core Pillars

### 1. Automated Skill Discovery
The system automatically identifies skills in `src/grid/skills/` using the `SkillDiscoveryEngine`.
- **Zero-Config Registration**: No need to manually add files to a list.
- **Dependency Validation**: Skills are only registered if their external dependencies are satisfied.
- **Hot-Reload**: Active watching of the skills directory for rapid development.

### 2. Persistent Intelligence
All skill executions and decisions are tracked in a persistent SQLite database (`data/skills_intelligence.db`).
- **Execution Tracking**: Captures status, latency, and success rates.
- **Intelligence Tracking**: Captures decision rationales, confidence scores, and alternatives.
- **Batch Persistence**: Optimized I/O using a batching buffer (10 records or 30s timer).

### 3. Performance Guarding
A dedicated `PerformanceGuard` monitors execution metrics to ensure system reliability.
- **Regression Detection**: Alerts when a skill's latency exceeds its baseline by more than 20%.
- **Prometheus Metrics**: Exporting performance data for external observability.
- **NSR Tracking**: Monitoring Noise-to-Signal Ratio to distinguish genuine regressions from environmental spikes.

### 4. Lifecycle & Version Management
- **Snapshot Versioning**: Accurate code snapshots combined with git SHA integration.
- **Zero-Latency Rollback**: Instantly revert to a previous working version if a deployment fails.
- **A/B Testing**: Gradual rollout of new skill variants with statistical evaluation (10% to 100% rollout increments).

## API Endpoints

The ISS provides a comprehensive management API via the Mothership application:

| Endpoint | Method | Description |
|:---|:---|:---|
| `/api/v1/skills/health` | `GET` | Overall health status of all registered skills. |
| `/api/v1/skills/intelligence/{id}` | `GET` | Detailed decision patterns and latency for a specific skill. |
| `/api/v1/skills/signal-quality` | `GET` | Global NSR (Noise-to-Signal Ratio) metrics. |
| `/api/v1/skills/diagnostics` | `GET` | Full diagnostic report of ISS components. |

## CLI Tools

Access diagnostics and maintenance tools via the debug CLI:

```bash
# Run persistence verification
python -m grid.skills.persistence_verifier

# Run full system diagnostics
python -m grid.skills.diagnostics
```

## Configuration

| Environment Variable | Default | Description |
|:---|:---|:---|
| `GRID_SKILLS_PERSIST` | `true` | Enable/disable persistence layer. |
| `GRID_SKILLS_BATCH_SIZE` | `10` | Records per batch flush. |
| `GRID_SKILLS_FLUSH_INTERVAL` | `30` | Max seconds between flushes. |
| `GRID_SKILLS_REGRESSION_THRESHOLD` | `1.2` | Alert at 20% degradation. |
| `GRID_SKILLS_NSR_THRESHOLD` | `0.10` | Acceptable noise level (10%). |

## Audio Engineering Analogy
The system applies concepts from signal processing to software quality:
- **Signal**: Valid, representative execution data.
- **Noise**: Environmental spikes, timeouts, or transient errors.
- **NSR**: The ratio of Noise to Signal, used to tune alert sensitivities.
- **Fading**: Gradual transition between skill variants in A/B testing.
