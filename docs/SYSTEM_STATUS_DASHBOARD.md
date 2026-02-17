# GRID — System Status Dashboard

## 1. Current Health
- **Test Status**: benchmark suite green (SLA guard enforced)
- **Local-first posture**: enabled by design; optional integration surfaces are explicit

## 2. Performance (Latest)
Source-of-truth artifacts:
- `benchmark_metrics.json`
- `stress_metrics.json`

### Benchmarks
Key metric: `full_pipeline` must remain ≤ 0.1 ms at mean/p95/p99.

### Stress
Use `async_stress_harness.py` to validate concurrency tail latency.

## 3. Regression Guardrails
- SLA enforced in `tests/test_grid_benchmark.py`.
- CI archives artifacts in `.github/workflows/main.yaml` (Performance job).

## 4. Pipelines
- **Essence**: `grid.essence.core_state` (state transforms + decay)
- **Awareness**: `grid.awareness.context` (context evolution: decay/drift/relational growth)
- **Patterns**: `grid.patterns.recognition` (fast path; ML optional)
- **Bridge**: `grid.interfaces.bridge` (serialize + compress + hash + optional latency)
- **Sensory**: `grid.interfaces.sensory` (audio/visual/text/structured feature extraction)
- **Orchestration**: `grid.application.IntelligenceApplication`

## 5. Open Items
- Expand macro-benchmark coverage (API endpoints, end-to-end event workflows).
- Add memory/CPU profiling in stress harness (psutil) when running in CI.
- Extend dashboard with trend graphs (artifact history).
