# Safety Module Debugging Checklist

> CRITICAL: Safety modules (safety/, security/, boundaries/) require extra caution.
> This checklist ensures debugging does NOT weaken security invariants.

## Pre-Debug Verification

- [ ] Audit trail logging is ENABLED (check safety/observability/logging_setup.py)
- [ ] Metrics collection is ACTIVE (safety/observability/metrics.py)
- [ ] Database connection is fail-closed (safety/audit/db.py:82-84)
- [ ] No eval/exec/pickle in debugging code

## Guardian Rule Engine Debugging (<20ms budget)

### Cache Effectiveness

```bash
# Check rule cache hit rate
uv run python -c "
from safety.guardian.engine import get_guardian_engine
engine = get_guardian_engine()
stats = engine.get_stats()
print(f'Cache hit rate: {stats.get(\"cache_hit_rate\", 0):.2%}')
print(f'Avg latency: {stats.get(\"avg_latency_ms\", 0):.2f}ms')
"
```

### Rule Loading Verification

```bash
# Verify dynamic rules are loaded
uv run python scripts/debug_guardian.py
```

### Latency Profiling

```python
# In safety/detectors/pre_check_guardian.py
from safety.observability.metrics import PRECHECK_LATENCY
with PRECHECK_LATENCY.time():
    result = rule_engine.check(text)
```

## Network Interceptor Debugging

### Hook Verification

```bash
# Verify interceptor hooks are registered (when available)
uv run python -c "
try:
    from security.network_interceptor import interceptor
    print(f'Registered hooks: {len(interceptor._hooks)}')
    for hook in interceptor._hooks:
        print(f'  - {hook.name}: {hook.pattern}')
except ImportError:
    print('network_interceptor not available')
"
```

### Default-Deny Verification

```bash
# Test that unknown patterns are DENIED by default
uv run pytest security/tests/test_network_interceptor.py::test_default_deny -v
```

## Database Pool Debugging

### Connection Pool State

```python
from safety.audit.db import _engine
if _engine:
    pool = _engine.pool
    print(f"Pool size: {pool.size()}")
    print(f"Checked in: {pool.checkedin()}")
    print(f"Overflow: {pool.overflow()}")
```

### Fail-Closed Verification

```bash
# Verify DB failure causes request refusal
uv run pytest safety/tests/test_audit_db.py -v -k fail
```

## Non-Invasive Debugging Patterns

### 1. Structured Logging (Preferred)

```python
from safety.observability.logging_setup import get_logger, set_trace_context
logger = get_logger("debug.my_component")
# Always set trace context
trace_id = set_trace_context(user_id="debug_user")
logger.info("debug_checkpoint",
    checkpoint="before_guardian",
    input_length=len(text),
    trace_id=trace_id
)
```

### 2. Prometheus Metrics (Performance)

```python
from prometheus_client import Histogram
DEBUG_LATENCY = Histogram(
    "safety_debug_operation_latency_seconds",
    "Debug operation latency",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1)
)
with DEBUG_LATENCY.labels(operation="rule_matching").time():
    result = rule_engine.check(text)
```

### 3. Test Isolation (Fixtures)

```python
# In safety/tests/conftest.py
@pytest.fixture
def debug_mode():
    """Enable debug mode for single test."""
    import os
    os.environ["SAFETY_DEBUG"] = "true"
    yield
    os.environ.pop("SAFETY_DEBUG", None)
```

## Forbidden Debugging Practices

- ❌ NEVER add bypass paths (e.g., `if debug_mode: skip_validation()`)
- ❌ NEVER disable audit logging
- ❌ NEVER weaken fail-closed semantics
- ❌ NEVER use print() instead of structured logging
- ❌ NEVER commit debug code to safety/security/boundaries without review

## Emergency Debugging (Production Incidents)

If debugging in production:

1. **Enable verbose logging** (non-invasive):

   ```bash
   export SAFETY_LOG_LEVEL=DEBUG
   systemctl restart mothership
   ```

2. **Check recent audit events**:

   ```sql
   SELECT * FROM audit_events
   ORDER BY timestamp DESC
   LIMIT 100;
   ```

3. **Examine Prometheus metrics**:

   ```bash
   curl http://localhost:9090/metrics | grep safety_
   ```

4. **Review structured logs**:

   ```bash
   tail -f safety/logs/safety_$(date +%Y-%m-%d).jsonl | jq 'select(.level=="error")'
   ```
