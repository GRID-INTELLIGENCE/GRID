# GRID v2.6.1 — Comprehensive Security Review

**Date:** 2026-03-07 | **Mode:** Read-only static analysis | **Reviewer:** Claude Opus 4.6 + human spot-check
**Scope:** Full codebase (784 source files, 4 review domains)

---

## Executive Summary

**Total findings: 57** across 4 review domains (deduplicated cross-references noted)

| Severity | Count |
|----------|-------|
| CRITICAL | 7 |
| HIGH | 17 |
| MEDIUM | 21 |
| LOW | 12 |

**Top 3 systemic issues:**

1. **Dev bypasses bleeding into production paths** — Hardcoded `"dev-test-token"`, unconditional login bypass, anonymous fallback, all gated by environment checks that are easy to misconfigure.
2. **Security infrastructure exists but isn't wired to boundaries** — `InputSanitizer`, `SafetyFirstRouter`, `PathValidator` all exist but RAG streaming, agentic, and MCP endpoints don't use them.
3. **`exec()` in sandbox fallback with broken violation checker** — The one place dynamic code runs has a logic bug that silences all pattern detection.

---

## Verified CRITICAL Findings

### CRIT-1: Hardcoded `"dev-test-token"` Grants ADMIN

**File:** `src/application/mothership/dependencies.py:198-207`
**Verified:** Yes — spot-checked directly.

The literal string `"dev-test-token"` is checked in `verify_authentication`. When matched (in dev/test mode), it returns `Role.ADMIN` permissions with `authenticated=False`. The `require_authentication` function at `:270-276` explicitly allows `method == "dev_bypass"` through, so the `authenticated=False` flag does not block access.

### CRIT-2: `/auth/login` Skips Credential Validation in Development

**File:** `src/application/mothership/routers/auth.py:181-222`
**Verified:** Yes.

When `settings.is_development` is True, `validate_production_credentials` is never called. Any username/password is accepted and a valid JWT pair is issued. The `user_id` is attacker-controlled: `f"user_{request.username}"`.

### CRIT-3: Token Denylist Uses Raw Token as Key (Not JTI)

**File:** `src/grid/auth/token_manager.py:123-145`
**Verified:** Yes.

Uses `f"denylist:{token}"` while `token_revocation.py` uses JTI. Two parallel revocation implementations with different correctness guarantees.

### CRIT-4: Unsafe `exec()` in Sandbox Fallback

**File:** `src/grid/skills/sandbox.py:402`
**Verified:** Yes.

`exec(skill_code, namespace)` runs in-process when subprocess creation fails. The post-execution security check at `:549-551` has a logic bug: `pattern in violations` (always False) instead of `pattern in skill_code`.

### CRIT-5: Unauthenticated Agentic Execution Endpoints

**File:** `src/application/mothership/routers/agentic.py`
**Verified:** Yes.

Only `create_case` has `RequiredAuth`. All other endpoints (get, enrich, execute, execute-iterative, get-reference, get-experience) are unauthenticated. `max_iterations` at `:327` has no upper bound.

### CRIT-6: MCP Code Injection via `python -c`

**File:** `mcp-setup/server/enhanced_tools_mcp_server.py:431`
**Verified:** Yes.

`cmd = ["python", "-c", f"import {target}; help({target})"]` with unsanitized `target` from MCP caller input.

### CRIT-7: Unauthenticated Admin Bypass in Development

**File:** `src/application/mothership/dependencies.py:233-241`
**Verified:** Yes.

In dev mode with `MOTHERSHIP_ALLOW_UNAUTHENTICATED_DEV=1`, returns ADMIN permissions without any credentials. Combined with `:251-258` anonymous fallback for all non-prod environments.

---

## HIGH Findings

| ID | File | Finding | Verified |
|----|------|---------|----------|
| HIGH-1 | `security/jwt.py:253-268,:302-308` | No `iss`/`aud` claims in JWT; no validation on decode | Yes |
| HIGH-2 | `security/jwt.py:404-425` | Token refresh doesn't check revocation list | Yes |
| HIGH-3 | `dependencies.py:154-164` | `get_api_key()` accepts any string in dev; prod path also unvalidated | Yes |
| HIGH-4 | `security/auth.py:91` | Production guard uses string equality; `DEV_MACHINE_ID` has no allowlist | Yes |
| HIGH-5 | `security/auth.py:280-286` | Role escalation via `metadata["role"]` JWT claim | Yes |
| HIGH-6 | `rag/core/engine.py:125-128` | No prompt injection sanitization before LLM | Yes |
| HIGH-7 | `mcp/mastermind_server.py:538` | ReDoS via user-controlled regex in `search_code` | Yes |
| HIGH-8 | `rag/llm.py:42` | Ollama prompt as CLI argv with no length limit (resource abuse, not injection) | Reclassified |
| HIGH-9 | `mcp/multi_git_server.py:358` | Git argument injection via unsanitized ref/file_path | Yes |
| HIGH-10 | `rag/vector_store/chromadb_store.py:39-40` | `allow_reset=True` with no auth | Yes |
| HIGH-11 | Multiple routers | Raw `str(e)` exception details leaked in 500 responses | Yes |
| HIGH-12 | `routers/corruption_monitoring.py` | Admin reset endpoint unauthenticated | Yes |
| HIGH-13 | `routers/drt.py` | DRT admin endpoints unauthenticated | Yes |
| HIGH-14 | `utils/__init__.py` | SSRF via webhook URL check | Yes |
| HIGH-15 | `arena_api/requirements.txt:11` | `python-jose` CVE-2024-23342 in non-main requirements | Yes |
| HIGH-16 | `rag/vector_store/databricks_store.py:532` | SQL injection via f-string in `text()` for timeout | Yes |
| HIGH-17 | `skills/sandbox.py:549-551` | Violation pattern check logic bug (never fires) | Yes |

---

## MEDIUM Findings

| ID | File | Finding |
|----|------|---------|
| MED-1 | `security/token_revocation.py:92-97` | `is_revoked()` fails open on backend error |
| MED-2 | `dependencies.py:251-258` | Anonymous READ fallback in non-prod |
| MED-3 | `dependencies.py:510` | In-memory rate limiter per-process |
| MED-4 | `middleware/security_enforcer.py:292` | X-Forwarded-For trusted without proxy allowlist |
| MED-5 | `routers/cockpit.py` | `/health/factory-defaults` exposes security config |
| MED-6 | `credential_validation.py:132` | Password hash in generic `metadata` dict |
| MED-7 | `credential_validation.py:58` | Lockout state in-memory |
| MED-8 | `grid/auth/middleware.py:46` | Full JWT error message leaked to client |
| MED-9 | `rag/llm.py:18` | Ollama base URL unvalidated — SSRF potential |
| MED-10 | `mcp/mastermind_server.py:540` | `rglob(file_pattern)` — full codebase scan, no boundary |
| MED-11 | `routers/rag_streaming.py:84` | RAG streaming/batch endpoints lack auth |
| MED-12 | `test_runner_mcp_server.py:35` | Arbitrary `test_path` to pytest without validation |
| MED-13 | `enhanced_tools_mcp_server.py:60` | Residual debug logger writes tool args to hardcoded file |
| MED-14 | `routers/agentic.py:32` | `KNOWLEDGE_BASE_PATH` relative — CWD-dependent |
| MED-15 | `databricks_store.py:594,606,623` | Table name interpolated into raw SQL |
| MED-16 | `safety/api/security_headers.py:58` | `'unsafe-eval'` in CSP |
| MED-17 | `.github/workflows/ci.yml:119,156` | Security scan non-blocking (`continue-on-error: true`) |
| MED-18 | `.github/workflows/ci.yml:53` | `BLOCKER_DISABLED=1` suppresses safety in CI |
| MED-19 | `.env` | Dev secrets include weak/guessable JWT keys |
| MED-20 | `pyproject.toml:66` | PyPDF2 deprecated — use `pypdf` |
| MED-21 | Experimental services | `0.0.0.0` bind without proxy |

---

## LOW Findings

| ID | File | Finding |
|----|------|---------|
| LOW-1 | `grid/auth/service.py:31` | Silent fallback to SHA-256 if bcrypt missing |
| LOW-2 | `runtime_settings.py:42` | JWT algorithm from env var without allowlist |
| LOW-3 | `dependencies.py:510` | Rate limit dict non-atomic read-modify-write |
| LOW-4 | `security/jwt.py:427` | `decode_unverified()` publicly callable |
| LOW-5 | `electron/main.ts:53` | Dev-mode `unsafe-inline` in CSP (prod is clean) |
| LOW-6 | `nginx-security.conf:12` | `unsafe-inline` in nginx CSP |
| LOW-7 | `.github/workflows/ci.yml:72` | Actions pinned to mutable tags, not SHAs |
| LOW-8 | `pyproject.toml:355` | S105/S106/S107 bandit rules globally suppressed |
| LOW-9 | `grid/auth/service.py:147` | Raw SQL via aiosqlite (safe but inconsistent) |
| LOW-10 | `scripts/eufle.py:34` | `subprocess.run` without timeout |
| LOW-11 | `docker-entrypoint.sh:44` | `eval` for variable dereference |
| LOW-12 | `nginx-security.conf:43` | No HTTP-to-HTTPS redirect |

---

## Corrections from Spot-Check

1. **`rag/llm.py` reclassified**: Not shell injection (argv list, `shell=False`). Real issue is resource abuse / unbounded prompt size. Severity remains HIGH but for different reason.
2. **Python `re` timeout**: stdlib `re` does not have a usable timeout parameter. Use `regex` library with timeout, RE2 bindings, or reject user-supplied regex entirely.
3. **Middleware order claim**: Not confirmed. `middleware/__init__.py:472` says last-added runs first. Needs re-validation.
4. **`decode_unverified()`**: Only test usage found. Keep LOW.
5. **Prompt injection "sanitization"**: Keyword sanitization alone is not a full fix. Boundary isolation and capability controls matter more.

---

## Architecture-Level Assessment

### What's Strong

- `PathValidator`, `InputSanitizer`, `SafetyFirstRouter`, `subprocess_wrapper` (shell=False) all exist and work correctly where applied.
- Electron security posture is excellent (`contextIsolation: true`, `sandbox: true`, validated IPC).
- Arena integration uses AST-based safe evaluation — the correct pattern.
- Guardian engine, boundary contracts, and overwatch are real enforcement systems.
- Test discipline (3175 tests, 75% coverage floor) is strong.

### The Systemic Gap

The defensive infrastructure is built but not consistently wired to the API boundary. RAG streaming has no auth and no input sanitization, agentic endpoints lack auth, MCP tools accept unsanitized arguments. The fix is not building new defenses — it's **connecting existing ones to every public endpoint**.

### The Dev-Bypass Pattern

At least 5 separate dev/test bypasses exist across the auth stack. Each is individually guarded, but the cumulative attack surface means a single misconfigured environment variable can open multiple doors simultaneously. A single, auditable bypass mechanism should replace the scattered checks.

### Parallel Security Stacks

JWT/revocation logic exists in at least two places (`grid/auth/token_manager.py` and `mothership/security/jwt.py`). This guarantees drift and inconsistent guarantees.

---

## Release Gates

Before any tagged release, these conditions must pass:

1. `Bearer dev-test-token` returns `401` outside isolated test fixtures
2. Dev mode login requires a real credential backend or explicit test fixture
3. Every `/agentic` route rejects unauthenticated requests
4. Revoked refresh tokens cannot mint new access tokens
5. Dangerous patterns are blocked before any execution path
6. Invalid MCP import targets, refs, regexes, and paths are rejected before process creation
7. Production ChromaDB config asserts `allow_reset=False`
