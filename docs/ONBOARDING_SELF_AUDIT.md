# GRID — Self-Audit Onboarding Checklist

## Purpose
Ensure any contributor or reviewer can validate GRID’s performance guardrails, reproducibility, and local-first posture.

## 1. Quick Start Verification
- Confirm Python environment available (3.11+ recommended).
- Install dependencies:
  - `pip install -r requirements.txt`
- Run the benchmark suite (must pass):
  - `python -m pytest tests/test_grid_benchmark.py -q`

## 2. Performance Guardrails
- Confirm these artifacts are created in repo root after benchmark run:
  - `benchmark_metrics.json`
  - `benchmark_results.json`
- Confirm SLA gate is enforced by tests:
  - `full_pipeline` mean/p95/p99 must be ≤ 0.1 ms.

## 3. Concurrency / Stress Validation
- Run:
  - `python tests/async_stress_harness.py --concurrency 200 --repeats 10`
- Confirm artifact exists:
  - `data/stress_metrics.json`
- Validate tail latency:
  - Check p95/p99 in `data/stress_metrics.json` and compare to internal SLA requirements.

## 4. CI/CD Verification
- Confirm CI workflow runs benchmarks + stress harness and uploads artifacts:
  - `.github/workflows/main.yaml` job: `Performance Benchmarks & SLA`
- Confirm CI will fail if SLA regresses:
  - enforced by `tests/test_grid_benchmark.py`.

## 5. Local-First / External Integration Posture
- Ensure no required network API keys are present for running core tests/benchmarks.
- Any optional cloud paths must remain explicit opt-in, documented, and testable.

## 6. Release / Stakeholder Readiness
- Update `RESEARCH_ALIGNMENT.md` if performance numbers change.
- Include latest `data/benchmark_metrics.json` + `data/stress_metrics.json` in any submission bundle.
