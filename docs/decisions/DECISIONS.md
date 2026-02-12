# Architecture Decision Log

Running log of architectural decisions for THE GRID.
Append new entries at the top. One decision per entry.

---

## 2026-02-12 — Debug Insights Remediation

**Decision**: Fixed critical blocking issues in debugging routine: StreamMonitorMiddleware import, test_ollama.py collection crash, duplicate test names, Guardian rule loading, connection pool messages.

**Why**:
- Mothership failed to import due to missing StreamMonitorMiddleware import (NameError)
- Test suite crashed when Ollama service was down (module-level sys.exit(1))
- Pytest collection failed on duplicate test module names
- Guardian showed 0 rules (misleading - rules weren't loaded)
- Connection pool error messages lacked actionable guidance

**Alternatives considered**:
1. Skip all broken tests — Rejected: hides real issues, defeats purpose of test suite
2. Mock all external services — Rejected: doesn't test actual integration behavior
3. Remove problematic tests — Rejected: loses test coverage

**Implementation**:
- Added StreamMonitorMiddleware import in main.py (P0 blocker)
- Converted test_ollama.py to proper pytest test with skip fixture (P1)
- Renamed duplicate test files with _root suffix (P1)
- Added init_guardian_rules() call in debug CLI guardian command (P2)
- Enhanced pools CLI error message with actionable guidance (P2)

**Verification**: Mothership imports successfully, test suite skips gracefully when services down, Guardian shows 23 loaded rules, pools message guides users.

---

## 2026-02-12 — Debugging Routine Design

**Decision**: Implement non-invasive debugging routine with 8 layers (Session Start, Async Tracking, Integration Health, Safety Checklist, VS Code Configs, CLI Commands, Profiling, Troubleshooting Tree).

**Why**:

- Existing infrastructure (structlog, Prometheus, pytest) provides foundation
- 2251 async patterns require specialized tracking
- Safety modules need debugging without weakening invariants
- Developer experience requires clear workflows

**Alternatives considered**:

1. External APM tool (Datadog, New Relic) — Rejected: adds dependency, doesn't integrate with existing patterns
2. Built-in Python debugger only — Rejected: insufficient for async/integration debugging
3. Logging-only approach — Rejected: lacks structured visibility for performance issues

**Implementation constraints**:

- MUST NOT weaken security (no bypass paths)
- MUST preserve audit trails
- MUST respect <20ms Guardian budget
- MUST maintain <30s test suite budget

---

## 2026-02-12 — Fail-closed boundary engine

**Decision**: Unknown boundary/guardrail IDs now return deny instead of allow.
**Why**: Fail-open on missing config is a security hole — typos or removed configs silently grant access.
**Alternatives considered**: Raising an exception (too disruptive to callers), logging-only (doesn't prevent access).

## 2026-02-12 — Redis-backed misuse tracking

**Decision**: Migrated misuse tracker from in-memory dict to Redis sorted sets with in-memory fallback.
**Why**: In-memory tracking is per-process — multi-instance deployments can't detect distributed abuse.
**Alternatives considered**: Shared file (too slow), PostgreSQL (overkill for sliding window counters).

## 2026-02-12 — PII auto-redaction in audit logs

**Decision**: SQLAlchemy `before_insert` event listener auto-redacts email, phone, SSN, credit card, IP from audit records.
**Why**: Audit logs store full user input — PII retention violates privacy principles and GDPR.
**Alternatives considered**: Application-level redaction (easy to forget), database triggers (less portable).

## 2026-02-12 — GRID_ENV gating for security bypasses

**Decision**: `DISABLE_NETWORK_SECURITY` and API docs bypass now require `GRID_ENV=development|dev|test`.
**Why**: Single env var bypass is too easy to accidentally or maliciously enable in production.
**Alternatives considered**: Removing bypass entirely (breaks local dev workflow).

## 2026-02-12 — Bounded body streaming in middleware

**Decision**: Read request body via `request.stream()` with 50KB limit instead of `request.body()`.
**Why**: `request.body()` loads entire payload into memory before any size check — OOM vector.
**Alternatives considered**: Nginx/reverse proxy limit (defense-in-depth, but app should self-protect).
