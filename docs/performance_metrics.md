# Performance Metrics & Benchmarks

This document describes GRID's performance benchmarks, SLA requirements, and how to run them.

## Performance SLA

**Target**: All operations must maintain **<0.1ms** per operation (SLA enforced in tests)

**Current Status**: ✅ All 171 tests passing with SLA maintained

## Benchmark Suite

### Grid Intelligence Benchmarks

**File**: `tests/test_grid_benchmark.py`

**What it tests**:
- State creation performance
- State transformation performance
- Pattern recognition performance
- Context evolution performance
- Quantum bridge transfer performance
- Sensory processing performance
- Full pipeline performance

**How to run**:
```bash
python -m pytest tests/test_grid_benchmark.py -q
```

**Output**:
- Persists `benchmark_metrics.json` and `benchmark_results.json`
- Enforces 0.1ms SLA guardrails
- Reports mean, median, p95, p99 latencies

**Example output**:
```json
{
  "metadata": {...},
  "results": {
    "state_creation": {
      "count": 1000,
      "mean_ms": 0.012,
      "median_ms": 0.011,
      "p99_ms": 0.015
    }
  }
}
```

### Async Stress Harness

**File**: `tests/async_stress_harness.py`

**What it tests**:
- Concurrent request handling
- Latency under load (p95, p99)
- Memory usage (if `psutil` available)
- Throughput

**How to run**:
```bash
# Basic run
python tests/async_stress_harness.py --concurrency 200 --repeats 10

# With memory sampling
python tests/async_stress_harness.py --concurrency 200 --repeats 10 --save-latencies

# Custom output
python tests/async_stress_harness.py --concurrency 50 --repeats 5 --output custom_metrics.json
```

**Parameters**:
- `--concurrency`: Number of concurrent workers (default: 100)
- `--repeats`: Number of calls per worker (default: 10)
- `--mem-sample-every`: Sample memory every N calls (requires psutil, default: 5)
- `--output`: Output JSON path (default: `data/stress_metrics.json`)
- `--save-latencies`: Include per-call latencies in output

**Output**:
- Persists `stress_metrics.json` (or custom path)
- Summary includes: mean, p95, p99 latencies, wall clock time, memory stats

**Example output**:
```json
{
  "summary": {
    "concurrency": 200,
    "repeats_per_worker": 10,
    "calls": 2000,
    "latency_ms_mean": 0.012,
    "latency_ms_p95": 0.018,
    "latency_ms_p99": 0.025,
    "wall_clock_ms": 150.5
  },
  "latencies_ms": [0.011, 0.012, ...]
}
```

## CI/CD Integration

### GitHub Actions

The CI pipeline includes a **Performance Benchmarks & SLA** job:

**Location**: `.github/workflows/main.yaml` → `performance` job

**What it runs**:
1. Benchmark suite (`pytest tests/test_grid_benchmark.py`)
2. Async stress harness (`tests/async_stress_harness.py --concurrency 50 --repeats 5`)

**Artifacts**:
- `data/benchmark_metrics.json`
- `data/benchmark_results.json`
- `data/stress_metrics.json`

**Failure criteria**:
- Any operation exceeds 0.1ms SLA
- Stress test p99 exceeds acceptable threshold

## Performance Baselines

### Resonance Definitive Endpoint

**Current baseline** (per request):
- Context processing: ~5-10ms
- Path triage: ~5-10ms
- Skill orchestration: ~50-80ms
  - refine: ~10-15ms
  - transform: ~20-30ms
  - cross_reference: ~10-15ms
  - compress: ~10-15ms
  - RAG (if enabled): ~20-40ms
- Response construction: ~5-10ms
- Tracing (if enabled): ~2-5ms
- **Total**: ~75-130ms

**Note**: The <0.1ms SLA applies to individual operations, not full request latency.

### Optimization Opportunities

See `RESONANCE_OPTIMIZATION_PLAN.md` for:
- Skills pipeline parallelization (30-40% improvement potential)
- Registry caching (5-10% improvement)
- Response serialization caching (2-5% improvement)

## Monitoring Performance

### Local Development

1. **Run benchmarks before committing**:
   ```bash
   python -m pytest tests/test_grid_benchmark.py -q
   ```

2. **Stress test your changes**:
   ```bash
   python tests/async_stress_harness.py --concurrency 100 --repeats 10
   ```

3. **Check CI artifacts** after pushing:
   - Download `performance-metrics` artifact from GitHub Actions
   - Compare before/after metrics

### Production Monitoring

- Enable tracing: Set `TRACING_ENABLED=true` in router
- Review trace logs: Check `application/mothership` output
- Monitor metrics: Watch for SLA violations

## Performance Best Practices

1. **Profile before optimizing**: Use `cProfile` or `py-spy` to identify bottlenecks
2. **Test under load**: Use stress harness with realistic concurrency
3. **Monitor trends**: Track p95/p99 over time, not just mean
4. **Cache aggressively**: Pre-compute static responses (see optimization plan)
5. **Parallelize independent work**: Use `asyncio.gather` for concurrent operations

## Troubleshooting

### SLA Violations

If benchmarks fail with SLA violations:

1. **Check recent changes**: What changed since last green run?
2. **Profile the operation**: Use `time.perf_counter()` to measure
3. **Check dependencies**: Are optional deps causing slowdowns?
4. **Review optimization plan**: See `RESONANCE_OPTIMIZATION_PLAN.md`

### High Latency in Stress Tests

If stress tests show high p99:

1. **Check concurrency**: Reduce `--concurrency` to isolate issues
2. **Check memory**: Enable `--mem-sample-every` to detect leaks
3. **Review async patterns**: Ensure proper `asyncio` usage
4. **Check database**: If using DB, check connection pooling

## References

- `RESONANCE_OPTIMIZATION_PLAN.md` - Optimization roadmap
- `RESONANCE_v1_0_FINALIZATION.md` - Performance baseline documentation
- `tests/test_grid_benchmark.py` - Benchmark implementation
- `tests/async_stress_harness.py` - Stress test implementation
