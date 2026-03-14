# GRID Code Quality Highlights

**Version:** v2.7.0 | **Date:** March 2026

Synthesized snapshot of the code quality standards, tooling, and metrics across the GRID codebase.

---

## Summary

| Metric | Value |
|--------|-------|
| **Lint errors** | 0 (ruff clean) |
| **Tests passing** | 2953+ ✅ |
| **Code coverage** | ≥75% (enforced) |
| **Source files** | 828+ |
| **Lines of code** | 310k+ |
| **Python version** | 3.13+ |
| **Type checking** | mypy + pyright configured |
| **Package manager** | UV (uv sync) |

---

## 1. Linting & Formatting

**Tool:** [Ruff](https://github.com/astral-sh/ruff) — configured in `pyproject.toml` (`[tool.ruff.lint]`)

- **Rule sets active:** `E`, `F`, `B`, `I`, `W`, `UP`, `ASYNC`, `S`, `SIM`, `C4`, `PERF`
- **Line length:** 120 characters
- **Target:** Python 3.13
- **Current status:** 0 errors across all packages, including `boundaries/toolkit/`
- **Isort:** Enforced via `ruff.lint.isort`; all first-party packages declared
- **Per-file overrides:** `__init__.py` and `__main__.py` allow `F401` (intentional re-exports and runtime-checked imports); demo files allow `F401`/`F841`

**Running lint:**
```bash
ruff check .           # check
ruff check . --fix     # auto-fix safe issues
ruff format .          # format
```

---

## 2. Type Safety

**Tools:** mypy (`pyproject.toml` `[tool.mypy]`) + pyrightconfig.json (root)

- **Python version target:** 3.13
- **`warn_return_any`:** enabled
- **`warn_unused_configs`:** enabled
- **Namespace packages:** enabled (required for multi-root `src/` layout)
- **206 type issues resolved** historically (see `.github/COMPLETION_REPORT.md`)
- `TYPE_CHECKING` guards used for heavy optional imports (torch, transformers) to avoid import-time failures when optional groups are not installed

**Running type check:**
```bash
mypy src/grid/ src/application/ src/tools/ src/search/ src/cognitive/ src/mycelium/
```

---

## 3. Test Infrastructure

**Framework:** pytest with asyncio auto-mode (`asyncio_mode = "auto"`)

- **Test roots:** `tests/`, `safety/tests/`, `boundaries/tests/`
- **Total test directories:** 37 themed directories (unit, integration, api, security, safety, agentic, auth, billing, cognitive, mycelium, resilience, chaos, load, performance, unified_fabric, …)
- **Async:** `asyncio_mode = auto` — no `@pytest.mark.asyncio` decorators needed
- **Timeout:** 30 s default per test
- **Parallel execution:** `pytest-xdist` with auto worker count
- **Coverage minimum:** 75% (`--cov-fail-under=75`)
- **Test isolation:** `reset_services()` autouse fixture clears singletons between tests; `setup_env` disables DB/Redis connections; `MOTHERSHIP_DATABASE_URL=sqlite:///:memory:` in CI
- **Strict markers:** all markers must be declared; unknown markers fail collection

**Registered markers:**
`unit` · `integration` · `safety` · `security` · `api` · `critical` · `slow` · `flaky` · `redteam` · `smoke` · `scratch`

**Running tests:**
```bash
pytest tests/unit/ -v                        # fast unit tests
pytest tests/ safety/tests/ boundaries/tests/ -q --tb=short  # full suite
pytest -m "not slow and not scratch"         # CI-equivalent run
```

---

## 4. CI/CD Pipeline

**File:** `.github/workflows/ci.yml`

### Jobs (in order)

1. **secrets-scan** — Validates version/changelog consistency; checks for hardcoded secrets; asserts no `DEBUG=true` or `ENABLE_DEV_TOKEN` in production paths
2. **lint** — Ruff check + format check
3. **type-check** — mypy
4. **test-unit** — Fast unit tests with coverage
5. **test-integration** — Cross-module integration tests
6. **test-security** — Attack surface and guardrail tests
7. **test-api** — FastAPI endpoint tests
8. **build-wheel** — Validates all 9 wheel packages build cleanly

### Gate features

- **Version/changelog gate:** `pyproject.toml` version must match the top `CHANGELOG.md` heading — blocks misaligned releases
- **Git hygiene gate:** No untracked files allowed in `src/` or `tests/` at CI time
- **No-debug gate:** `scripts/assert_no_debug_in_prod.py` — blocks `DEBUG=true` / `ENABLE_DEV_TOKEN` in production config
- **Concurrency:** Cancel-in-progress per workflow ref — no stale runs

---

## 5. Security Guardrails (Code Quality Dimension)

GRID's security model is enforced at multiple code quality layers:

- **API attack surface:** 4-phase guardrails covering auth, body-size limits, rate limiting, input sanitization, error message sanitization (no `str(e)` to client), and SSRF-safe outbound URL validation
- **Path traversal prevention:** `validate_path_safety()` normalizes backslashes and rejects Windows absolute paths on Linux
- **Transition Gate:** Sealed-envelope HMAC-SHA256 handshake with single-use nonces and timing-safe comparison (`boundaries/transition_gate/`)
- **Parasite Guard:** Middleware detects malicious code injection patterns at request time
- **Safety module:** GUARDIAN rule engine (Aho-Corasick + regex) with pre/post content checks, PII privacy engine, and canary tokens (`safety/`)
- **Boundary contracts:** Overwatch + consent/refusal rights enforcement (`boundaries/`)

---

## 6. Code Organisation & Architecture Quality

- **Layered architecture (DDD):** Core → Service → Application; no upward imports from core
- **9 wheel packages** with clean namespace boundaries (`grid`, `application`, `cognitive`, `tools`, `mycelium`, `search`, `infrastructure`, `unified_fabric`, `vection`)
- **Import discipline:** Absolute imports only; no wildcard imports; `__all__` exports declared on public API modules
- **Dead code elimination:** Orphan module audit in v2.7.0 removed unused stubs (e.g. `src/realtime/glimpse/`)
- **Dependency groups:** Separated `dev`, `test`, `finetuning`, `workers` optional groups — torch/transformers only installed when needed
- **Configuration consolidation:** Centralized quality thresholds in `config/qualityGates.json` and `config/qualityGates.py`

---

## 7. Documentation Quality

- **CHANGELOG.md** — Kept current; version-gated by CI
- **DECISIONS.md** (`docs/decisions/`) — Running ADR log with rationale and alternatives
- **API Reference** (`docs/API_REFERENCE.md`) — Endpoint inventory
- **Security policy** (`SECURITY.md`) — Vulnerability reporting instructions
- **CONTRIBUTING.md** — Linter commands, test isolation guidelines, pipeline green checklist

---

## Key Improvements in v2.7.0

| Area | Change |
|------|--------|
| **Lint** | 0 errors maintained; deprecated `[tool.ruff]` top-level keys migrated to `[tool.ruff.lint]` |
| **Test isolation** | `importlib.reload()` replaced with `reload_settings()` to prevent DI identity mismatch |
| **CI reliability** | Git hygiene + no-debug gates added to block silent regressions |
| **Security** | Phase 1–4 API guardrails with dedicated test suite (`tests/api/test_phase3_security_guardrails.py`) |
| **Import safety** | Import guards and lazy loading across ecosystem; pytest collection fully restored |
| **Cross-platform** | Windows backslash path traversal hardened on Linux hosts |

---

## Running the Full Quality Suite

```bash
# Lint
ruff check .

# Type check
mypy src/grid/ src/application/ src/tools/ src/search/ src/cognitive/ src/mycelium/

# Tests (unit + integration + security + api)
pytest tests/unit tests/integration tests/security tests/api -q --tb=short

# Safety module tests
pytest safety/tests -q --tb=short

# Boundary module tests
pytest boundaries/tests -q --tb=short
```

All commands are also available via `make lint`, `make test`, and `make format`.
