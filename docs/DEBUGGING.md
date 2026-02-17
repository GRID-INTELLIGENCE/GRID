# GRID Debugging Guide

## Overview
This guide provides practices for debugging the GRID system, covering tracing, logging, and test failure analysis.

## 1. Tracing System
The GRID tracing system (`grid/tracing/`) provides insights into action execution.

### Key Concepts
- **TraceContext**: Carries metadata (trace_id, span_id) across calls.
- **ActionTrace**: Records specifics of an action (inputs, outputs, duration).

### usage
```python
from src.grid.tracing import TraceContext, trace_action

@trace_action(op_name="process_event")
def process(event, context: TraceContext):
    # ...
```

## 2. Logging
Use structured logging to capture machine-readable events.

### Best Practices
- **Levels**:
    - `DEBUG`: Verbose details (payloads).
    - `INFO`: Lifecycle events (startup, shutdown, job completion).
    - `ERROR`: Exceptions and critical failures.
- **Context**: Always include `trace_id` in logs if available.

## 3. Test Failures
Run tests with varying verbosity to diagnose issues.

- **Collect Only**: `pytest --collect-only` (Verify environment/imports)
- **Fast Fail**: `pytest -x` (Stop on first failure)
- **Verbose**: `pytest -v` (See full assertion details)
- **Output**: `pytest -s` (View stdout/stderr during execution)

### Common Issues
- **UnicodeDecodeError**: Ensure `encoding="utf-8"` is used in `subprocess.run` or file opens.
- **Pydantic Warnings**: Use `model_config = ConfigDict(...)` for V2 compatibility.
- **PermissionError**: Windows file locking can cause these during cleanup. Retry or inspect process handles.
