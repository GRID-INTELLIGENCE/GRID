# Architecture Decision Log

Running log of architectural decisions for THE GRID.
Append new entries at the top. One decision per entry.

---

## 2026-03-12 — CI Enforcement: Two-Track Gate Design (Nourishment Principle)

**Decision**: Introduced two distinct GitHub Actions gates at workspace root:
1. `secrets-gate.yml` — deterministic pattern scan for secrets/credentials (hard-block, no judgment call).
2. `boundary-gate.yml` + `scripts/boundary_review.py` — structural invariant review for `safety/`, `security/`, `boundaries/` changes (blocking only on CRITICAL/HIGH findings, always accompanied by rationale, recommendation, and a clear remediation path).

The governing principle: **patterns and repetitions need nourishment, not restrictions.**

A committed secret has no legitimate variant — the pattern IS the violation, restriction is the only correct response. But a weakened boundary invariant is a development signal, not a terminal event. Every blocking finding in the boundary gate must carry a `rationale` (why the invariant exists), a `recommendation` (how to preserve intent while making the change), and a documented path back to approval. The gate does not end the conversation; it redirects it.

This maps directly to the GATE contract's AX-03/AX-04 axioms: every difference has a name and every response is proportional to the measured difference. Secrets have a scalar difference (present/absent) — response is binary. Boundary weakening has a dimensional difference (which invariant, which scope, what severity) — response is proportional and constructive.

**Why**: The previous state had no root-level CI enforcement. The PR template had a "Requested AI review" checkbox backed by nothing. The boundary gate fulfills that contract; the secrets gate fulfills the GATE never-rule ("never store user_secret in any file").

**Alternatives considered**:
1. Single gate for both concerns — Rejected: deterministic pattern scanning and structural reasoning are categorically different operations. Mixing them produces ambiguous failure messages and makes it harder to reason about what failed.
2. Block all findings regardless of severity — Rejected: violates the nourishment principle. LOW/MEDIUM findings become PR comments, not merge blocks — they inform without halting.
3. Use a third-party SAST tool for boundary review — Rejected: the boundary invariants are domain-specific (GATE contract axioms, RefusalRights, Consent revocability) and require codebase-aware semantic analysis, not generic SAST rules.

---

## 2026-02-24 — Community Readiness: Entry Point Cleanup & CVE Fix

**Decision**: Removed 4 broken `[project.scripts]` entries from `pyproject.toml` (`grid-agentic`, `grid-workflow`, `grid-context`, `databricks-cli`). Bumped `grid-safety` to 1.0.1 to publish the `python-jose` removal (CVE-2024-23342 fix) to PyPI. Added PyPI badge, CONTRIBUTING.md, and updated stale installation docs.

**Why**: Users installing via `pip install grid-intelligence` hit broken entry points and pulled in a vulnerable transitive dependency. The repo lacked basic community-facing metadata (description, topics, contribution guide).

**Alternatives considered**: Creating stub `__main__.py` files for the 3 missing entry points — rejected because stub commands with no behavior mislead users. Moving `src/integration` into the wheel for `databricks-cli` — rejected because it requires Databricks credentials and adds unnecessary weight.

---

## 2026-02-24 — Release v2.4.1

**Decision**: Tagged and released v2.4.1 from main (commit `def11d7`). Merged 11 Dependabot PRs, deferred 5 breaking-change PRs (#9 FastAPI, #13 pytest-asyncio, #18 npm group, #19 zod 4, #20 eslint 10). Fixed release workflow (`tomllib` stdlib instead of third-party `toml`, `uv venv` for build job). PyPI publish deferred (trusted publisher not yet configured on PyPI).

**Why**: 161 commits behind last tag (v2.2.4). CI green, dependency updates include CVE fix (cryptography 44->46). Release pipeline itself needed fixes discovered during execution.

**Alternatives considered**:
1. Merge all 16 Dependabot PRs — Rejected: FastAPI 0.132, pytest-asyncio 1.x, zod 4, eslint 10 are breaking changes requiring dedicated migration.
2. Skip to v3.0.0 — Rejected: no breaking API changes warrant major bump.
3. Wait for PyPI trusted publisher setup — Rejected: GitHub Release + artifacts are sufficient for now.

---

## 2026-02-24 — Reject `copilot-worktree-2026-02-17T11-02-39` branch

**Decision**: Branch blocked from merge. No changes applied to main.

**Why**: Senior review identified critical safety regressions — 13 safety-critical tests deleted (`tests/cognitive/test_pattern_learning.py`), overflow protection (`_sigmoid` clamping) removed, L2 regularization removed, breaking API change (`actual_label` → `confidence`), shared mutable state introduced, and `predict_proba` eliminated. The branch replaces a production-hardened Online Logistic Regression system with an unbounded EMA approach lacking convergence guarantees.

**Alternatives considered**:
1. Cherry-pick non-destructive changes — Rejected: 277 files changed with interleaved regressions make safe extraction impractical.
2. Merge and fix forward — Rejected: safety invariants must never be weakened, even temporarily (fail-closed principle).
3. Archive as tag then delete — Deferred: branch retained for now pending any future audit needs.

**Verification**: All 13 tests in `tests/cognitive/test_pattern_learning.py` pass on main (sigmoid clamping, L2 decay, convergence, JSON persistence, overflow protection, learning guard). Main safety features confirmed intact.

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
