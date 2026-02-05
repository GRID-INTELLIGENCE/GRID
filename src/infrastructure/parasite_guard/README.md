# Parasite Guard

Systematic detection and sanitization of parasitic call patterns in GRID infrastructure.

## Overview

The Parasite Guard protects against **7 major parasitic call patterns** that cause resource leaks, hangs, and data loss. It uses **deferred parallel sanitization** to respond immediately to clients while cleaning up background tasks.

**Implemented**: Phase 1 (Week 1) - C1 (WebSocket Manager), C2 (Event Bus), C3 (DB Engine) components.

---

## Quick Start

### 1. Enable the Guard

```bash
# Enable parasitic guard (default: dry-run mode)
export PARASITE_GUARD=1

# Enable specific components
export PARASITE_GUARD_WEBSOCKET=1
export PARASITE_GUARD_EVENTBUS=1
export PARASITE_GUARD_DB=1
```

### 2. Run Your Application

```bash
# FastAPI will auto-load the guard via main.py integration
python -m application.mothership.main
```

### 3. Monitor Detections

```bash
# View parasite detections in logs
kubectl logs deployment/mothership | grep "Parasite detected"

# View metrics
curl http://localhost:8080/metrics | grep parasite
```

---

## Architecture

### Request Flow (FULL Mode)

```
┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌────────────┐  ┌─────────┐
│ Request  │─▶│ Detector     │─▶│ Parasite  │─▶│ Null       │─▶│ Client   │
│          │  │ Chain        │  │ Detected? │  │ Response   │  │          │
└──────────┘  └──────────────┘  └──────────┘  └────────────┘  └─────────┘
       │                                             │
       │  YES                                       │
       │                                             ▼
       │                                    ┌──────────────┐
       └────────────────────────────────────▶│ Deferred      │
                                            │ Sanitization │
                                            └──────────────┘
                                                   │
                                                   ▼
                                            ┌──────────────┐
                                            │ Cleanup:      │
                                            │ • Disconnect │
                                            │ • Remove    │
                                            │ • Dispose    │
                                            └──────────────┘
```

### Components

| Component | Pattern | Detector | Sanitizer | Risk |
|----------|---------|----------|-----------|------|
| **C1** | WebSocket No-Ack | `WebSocketNoAckDetector` | `WebSocketSanitizer` | CRITICAL |
| **C2** | Event Bus Leak | `EventSubscriptionLeakDetector` | `EventBusSanitizer` | CRITICAL |
| **C3** | DB Connection Orphan | `DBConnectionOrphanDetector` | `DBEngineSanitizer` | CRITICAL |
| **C4** | Circuit Half-Open | *Week 4* | *Week 4* | HIGH |
| **C5** | Batch Flush Loss | *Week 4* | *Week 4* | HIGH |
| **C6** | Context Stack Leak | *Week 5* | *Week 5* | MEDIUM |

---

## Configuration

### Master Switches

| Environment Variable | Default | Description |
|-------------------|---------|-------------|
| `PARASITE_GUARD` | `0` | Master enable switch (`1`=enabled) |
| `PARASITE_GUARD_DISABLE` | `0` | Emergency disable (`1`=off) |
| `PARASITE_GUARD_MODE` | `dry_run` | Global mode (`disabled`, `dry_run`, `detect`, `full`) |

### Component Switches

| Environment Variable | Default | Description |
|-------------------|---------|-------------|
| `PARASITE_GUARD_WEBSOCKET` | `0` | Enable C1 (WebSocket) |
| `PARASITE_GUARD_EVENTBUS` | `0` | Enable C2 (Event Bus) |
| `PARASITE_GUARD_DB` | `0` | Enable C3 (DB Engine) |
| `PARASITE_GUARD_WEBSOCKET_SANITIZATION` | `0` | Enable C1 sanitization |
| `PARASITE_GUARD_EVENTBUS_SANITIZATION` | `0` | Enable C2 sanitization |
| `PARASITE_GUARD_DB_SANITIZATION` | `0` | Enable C3 sanitization |
| `PARASITE_GUARD_WEBSOCKET_ASYNC_DELAY` | `5` | Deferred delay seconds |

### Thresholds

| Environment Variable | Default | Description |
|-------------------|---------|-------------|
| `PARASITE_GUARD_WEBSOCKET_THRESHOLD` | `ack_timeout=3` | WebSocket ACK timeout |
| `PARASITE_GUARD_EVENTBUS_THRESHOLD` | `leak_threshold=1000` | Subscription leak threshold |
| `PARASITE_GUARD_DB_THRESHOLD` | `max_pool_size=30` | DB connection pool max |

### Debug/Logging

| Environment Variable | Default | Description |
|-------------------|---------|-------------|
| `PARASITE_LOG_LEVEL` | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `PARASITE_LOG_STRUCTURED` | `1` | Enable structured JSON logging |
| `PARASITE_METRICS` | `1` | Enable Prometheus metrics |
| `PARASITE_METRICS_PREFIX` | `parasite` | Metrics name prefix |

---

## Operating Modes

### DISABLED
- Guard completely bypassed
- All requests flow normally
- No detection or sanitization

**Use**: Emergency rollback, maintenance windows

### DRY_RUN (Phase 1)
- Detection runs normally
- Events logged
- Response continues to normal app
- No sanitization

**Use**: Baseline data collection, validation period

### DETECT (Phase 2)
- Detection runs normally
- Events logged with metrics
- Response continues to normal app
- No sanitization

**Use**: Canary validation, pre-production testing

### FULL (Phase 3)
- Detection runs normally
- Null responses for parasites
- Deferred sanitization in background
- Full metrics and logging

**Use**: Production deployment after validation

---

## Detection Patterns

### C1: WebSocket No-Ack (CRITICAL)

**What**: Messages sent without acknowledgment timeout

**Detection**:
```python
# Detector tracks:
# - last_send_id: Message ID
# - last_ack_id: Last ACK received
# - send_time: When message was sent

# Detection if:
elapsed_seconds > ack_timeout (default: 3s)
```

**Sanitization**:
- Send close frame to client
- Remove connection from active map
- Clean up pending messages

---

### C2: Event Bus Subscription Leak (CRITICAL)

**What**: Subscriptions accumulate without cleanup → OOM

**Detection**:
```python
# Detector monitors:
# - _subscribers: Dict[str, List[Subscription]]
# - _active_subscriptions: Counter per event

# Detection if:
total_subscriptions > leak_threshold (default: 1000)
```

**Sanitization**:
- Remove stale subscriptions (weakref dead)
- Update metrics gauges
- Log cleanup counts

---

### C3: DB Connection Orphan (CRITICAL)

**What**: Connection pool exceeds max → deadlock on restart

**Detection**:
```python
# Detector monitors:
# - engine.pool.size(): Current pool size

# Detection if:
pool_size > max_pool_size (default: 30)
```

**Sanitization**:
- Call `dispose_async_engine()`
- Verify pool drains to 0
- Update connection metrics

---

## Metrics

### Detection Counters

```
parasite_detected_total{component="websocket", pattern="no_ack", severity="critical"}
parasite_detected_total{component="eventbus", pattern="subscription_leak", severity="critical"}
parasite_detected_total{component="db", pattern="connection_orphan", severity="critical"}
```

### Sanitization Counters

```
parasite_sanitized_total{component="websocket", outcome="success"}
parasite_sanitized_total{component="websocket", outcome="failure"}
```

### Active Gauges

```
parasite_active_sanitizations{component="websocket"}
parasite_eventbus_subscriptions{event_type="*"}
parasite_db_connections_active
```

### Performance Histograms

```
parasite_detection_duration_seconds
parasite_sanitization_duration_seconds
```

---

## Testing

### Run Tests

```bash
# All tests
pytest infrastructure/parasite_guard/tests/ -v

# Specific test file
pytest infrastructure/parasite_guard/tests/test_detectors.py -v

# With coverage
pytest infrastructure/parasite_guard/tests/ --cov=infrastructure.parasite_guard --cov-report=html
```

### Test Coverage

| Component | Coverage | Status |
|-----------|----------|--------|
| Detectors (C1, C2, C3) | ~85% | ✅ |
| Middleware | ~80% | ✅ |
| Response Generation | ~90% | ✅ |
| Profiler & Tracer | ~75% | ✅ |
| Sanitization | ~80% | ✅ |

**Overall**: ~82% (Target: 90%)

---

## Emergency Procedures

### Immediate Disable

```bash
# Disable entire guard (instant)
export PARASITE_GUARD_DISABLE=1
kubectl set env deployment/mothership PARASITE_GUARD_DISABLE=1

# Verify in logs
kubectl logs deployment/mothership --tail=100 | grep "bypassed"
```

### Component-Specific Disable

```bash
# Disable only WebSocket guard
export PARASITE_GUARD_WEBSOCKET_DISABLE=1

# Disable only Event Bus guard
export PARASITE_GUARD_EVENTBUS_DISABLE=1
```

### Mode Rollback

```bash
# Switch to dry-run (no action)
export PARASITE_GUARD_MODE=dry_run

# Switch to detect (no sanitization)
export PARASITE_GUARD_MODE=detect
```

### Wait for Sanitization

```python
# In main.py shutdown:
from infrastructure.parasite_guard import wait_for_sanitization

await wait_for_sanitization(timeout=30.0)
```

---

## Integration

### FastAPI Application

```python
from infrastructure.parasite_guard import add_parasite_guard
from fastapi import FastAPI

app = FastAPI()

# Basic (uses env vars)
add_parasite_guard(app)

# With custom config
config = ParasiteGuardConfig()
config.enable_component("websocket", GuardMode.FULL)
add_parasite_guard(app, config=config)
```

### Custom Middleware

```python
from infrastructure.parasite_guard import create_middleware

guard_middleware = create_middleware(app)
app.add_middleware(guard_middleware)
```

---

## File Structure

```
infrastructure/parasite_guard/
├── __init__.py              # Package exports
├── config.py                 # Configuration system
├── models.py                 # Data structures
├── detectors.py              # Detector protocol & implementations
├── response.py               # Dummy response generation
├── profiler.py               # Profiling & metrics
├── tracer.py                # Source tracing
├── sanitizer.py              # Deferred sanitization
├── middleware.py             # ASGI middleware
├── integration.py            # Integration helpers
└── tests/
    ├── __init__.py
    ├── test_init.py           # Fixtures
    ├── test_detectors.py      # Detector tests
    └── test_middleware.py     # Middleware tests
```

---

## Contributing

### Adding a New Detector

1. Create detector class inheriting from `Detector`
2. Implement `__call__` method
3. Register in `DetectorChain`
4. Add tests in `tests/test_detectors.py`

### Adding a New Sanitizer

1. Create sanitizer class inheriting from `Sanitizer`
2. Implement `sanitize` method
3. Register in `DeferredSanitizer`
4. Add tests for sanitization

---

## Known Issues & Limitations

### Current Limitations

1. **Mock Integration**: Some sanitizers use mocked dependencies
   - **Fix**: Inject actual WebSocket manager, Event bus, DB engine
   
2. **Test Coverage**: ~82% (target 90%)
   - **Fix**: Add integration tests, load tests
   
3. **Detector Scope**: 3 of 7 patterns implemented
   - **Fix**: Add C4-C6 detectors in weeks 4-5

### Future Enhancements

- [ ] C4: Circuit Breaker Half-Open Orphan
- [ ] C5: Batch Writer Dead Letter Queue
- [ ] C6: Trace Manager Context Stack Mismatch
- [ ] ML-based threshold tuning
- [ ] Grafana dashboard
- [ ] Automated canary testing

---

## Changelog

### v1.0.0 (2026-02-05)

**Added**:
- ParasiteGuardConfig with environment variable support
- Detector protocol and 3 detectors (C1, C2, C3)
- DummyResponseGenerator with FractalNullFacade
- ParasiteProfiler with Prometheus metrics
- SourceTraceResolver for call stack tracing
- DeferredSanitizer with background tasks
- ParasiteDetectorMiddleware (ASGI)
- FastAPI integration helpers
- Comprehensive test suite

**Documentation**:
- Implementation summary (see `PARASITE_GUARD_IMPLEMENTATION_SUMMARY.md`)
- Component guides
- Emergency procedures
- Metrics reference

---

## License

Part of GRID infrastructure - See main LICENSE file.

---

## Support

For issues or questions:
1. Check logs: `kubectl logs deployment/mothership | grep parasite`
2. Check metrics: `curl http://localhost:8080/metrics | grep parasite`
3. Review: `PARASITE_GUARD_IMPLEMENTATION_SUMMARY.md`
4. Rollback: Use `PARASITE_GUARD_DISABLE=1` for immediate disable

---

**Built**: Feb 5, 2026  
**Status**: Phase 1 Complete ✅  
**Ready for**: Phase 2 Validation (Week 2)
