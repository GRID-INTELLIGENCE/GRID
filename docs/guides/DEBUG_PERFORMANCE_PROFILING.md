# Performance Profiling Guide

## 1. Profile Guardian Rule Engine (<20ms budget)

### Using cProfile

```bash
uv run python -m cProfile -o guardian.prof scripts/debug_guardian.py
uv run python -m pstats guardian.prof
> sort cumulative
> stats 20
```

### Using py-spy (sampling profiler - non-invasive)

```bash
# Install py-spy
uv pip install py-spy
# Profile running process
uv run py-spy record -o guardian.svg --pid $(pgrep -f uvicorn)
# Profile specific operation
uv run py-spy record -o guardian.svg -- python scripts/debug_guardian.py
```

## 2. Async Event Loop Profiling

### Using asyncio debug mode

```python
import asyncio
import os
# Enable debug mode
os.environ["PYTHONASYNCIODEBUG"] = "1"
asyncio.run(main(), debug=True)
```

### Detecting slow coroutines

```python
# In work/GRID/src/application/mothership/main.py
import asyncio
loop = asyncio.get_event_loop()
loop.slow_callback_duration = 0.1  # Warn if callback takes > 100ms
```

## 3. Database Query Profiling

### Using SQLAlchemy echo

```bash
export SAFETY_DB_ECHO=true
uv run python scripts/debug_guardian.py
```

### Using pg_stat_statements (PostgreSQL)

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
-- View slow queries
SELECT
    query,
    calls,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
WHERE mean_exec_time > 10  -- queries averaging > 10ms
ORDER BY mean_exec_time DESC
LIMIT 20;
```

## 4. Memory Profiling

### Using memory_profiler

```bash
uv pip install memory-profiler
# Profile specific function
uv run python -m memory_profiler scripts/profile_memory.py
```

### Using tracemalloc

```python
import tracemalloc
tracemalloc.start()
# ... your code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')
for stat in top_stats[:10]:
    print(stat)
```

## 5. Integration Latency Profiling

### Ollama Response Time

```bash
time curl -X POST http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Test",
  "stream": false
}'
```

### ChromaDB Query Latency

```python
import time
from tools.rag.vector_store.registry import get_vector_store
store = get_vector_store()
start = time.time()
results = store.query(query_texts=["test"], n_results=10)
latency_ms = (time.time() - start) * 1000
print(f"ChromaDB query latency: {latency_ms:.2f}ms")
```

## 6. Performance Budget Enforcement

### Test Suite Performance (<30s budget)

```bash
# Run with duration reporting
uv run pytest -q --tb=short --durations=10
# If exceeded, profile slowest tests
uv run pytest -q --tb=short --durations=0 | grep -E "passed in|SLOWEST"
```

### Guardian Latency Monitoring

```python
from safety.observability.metrics import PRECHECK_LATENCY
# Check p95 latency
import prometheus_client
metrics = prometheus_client.REGISTRY.collect()
for metric in metrics:
    if metric.name == "safety_precheck_latency_seconds":
        for sample in metric.samples:
            if sample[0].endswith("_bucket") and sample[2] == 0.02:  # 20ms bucket
                print(f"P95 Guardian latency: {sample[1]}ms")
```
