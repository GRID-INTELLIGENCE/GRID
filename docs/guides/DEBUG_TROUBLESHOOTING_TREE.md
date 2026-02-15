# Debugging Decision Tree

## Symptom: Tests are failing

### Q: Is "The Wall" passing?

```bash
uv run pytest -q --tb=short && uv run ruff check work/ safety/ security/ boundaries/
```

- **NO** → Fix failing tests FIRST before debugging anything else
- **YES** → Continue to next question

### Q: Is it an async test?

```bash
grep -n "@pytest.mark.asyncio" path/to/test_file.py
```

- **YES** → Check async-specific issues:
  - Event loop not closed? → Use `pytest-asyncio` fixtures
  - Hanging task? → Run `uv run python scripts/debug_async_tasks.py`
  - Deadlock? → Enable `PYTHONASYNCIODEBUG=1`
- **NO** → Check synchronous issues

### Q: Does it involve external integrations?

```bash
uv run python scripts/debug_cli.py health
```

- **Ollama unhealthy** → Start Ollama: `ollama serve`
- **ChromaDB unhealthy** → Start ChromaDB: `chroma run --path ./chroma_data`
- **PostgreSQL unhealthy** → Check connection string in `DATABASE_URL`
- **All healthy** → Continue to next question

### Q: Is it a safety module test?

```bash
echo $TEST_FILE | grep -E "safety/|security/|boundaries/"
```

- **YES** → Follow [Safety Debug Checklist](./SAFETY_DEBUG_CHECKLIST.md)
- **NO** → Standard debugging

---

## Symptom: Application hangs

### Q: Are async tasks stuck?

```bash
uv run python scripts/debug_cli.py tasks
```

- **Stuck tasks found** → Check trace IDs in logs:

  ```bash
  uv run python scripts/debug_cli.py logs TRACE_ID
  ```

- **No stuck tasks** → Check connection pools

### Q: Are connection pools exhausted?

```bash
uv run python scripts/debug_cli.py pools
```

- **Checked Out == Pool Size** → Connection leak detected
  - Review recent code for unclosed connections
  - Check `async with get_session()` context managers
- **Normal pool state** → Check external services

### Q: Is an external service blocking?

```bash
uv run python scripts/debug_cli.py health
```

- **High latency (>1000ms)** → Service degradation
  - Check service logs
  - Review circuit breaker state
- **Normal latency** → Check application logs

---

## Symptom: High memory usage

### Q: Are there memory leaks in tasks?

```bash
uv run python -m memory_profiler scripts/profile_memory.py
```

- **Growing unbounded** → Task not cleaning up
  - Check weak references in `AsyncTaskTracker`
  - Review event bus subscribers
- **Stable** → Check cache sizes

### Q: Are caches unbounded?

```bash
# Check Guardian rule cache
uv run python -c "from safety.guardian.engine import get_guardian_engine; e=get_guardian_engine(); s=e.get_stats(); print(s)"
```

- **Cache too large** → Implement LRU eviction
- **Cache reasonable** → Profile with tracemalloc

---

## Symptom: Guardian latency > 20ms

### Q: Is it rule matching?

```bash
uv run python scripts/debug_guardian.py
```

- **Regex matching slow** → Optimize regex patterns
- **Trie matching slow** → Check keyword count
- **Cache miss rate high** → Increase cache size

### Q: Is it I/O bound?

```bash
# Check if Guardian is hitting DB
grep "guardian" safety/logs/safety_$(date +%Y-%m-%d).jsonl | jq 'select(.event=="database_query")'
```

- **Database queries found** → Guardian should NOT hit DB in pre-check
  - Move queries to post-check
- **No DB queries** → Profile CPU usage

---

## Symptom: Integration test flakiness

### Q: Is it a race condition?

```bash
uv run pytest path/to/test.py -v --count=100
```

- **Fails intermittently** → Race condition likely
  - Add `asyncio.sleep(0)` to yield control
  - Use proper synchronization primitives
- **Consistent failure** → Not a race

### Q: Is it test isolation?

```bash
# Check for shared state
grep "global\|_instance\|singleton" path/to/test.py
```

- **Shared state found** → Use fixtures to reset:

  ```python
  @pytest.fixture(autouse=True)
  def reset_global_state():
      # Reset singletons
      yield
      # Cleanup
  ```

- **No shared state** → Check test order dependency
