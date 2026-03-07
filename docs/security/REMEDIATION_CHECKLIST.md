# Security Remediation Checklist

**Generated:** 2026-03-07 | **Source:** `SECURITY_REVIEW_2026-03-07.md`

Each item has: priority, file:line, what to do, and a test gate.

---

## P0 — Release Blockers

### P0-1: Remove hardcoded dev-test-token
- **File:** `src/application/mothership/dependencies.py:198-207`
- **Action:** Delete the `if bearer_token == "dev-test-token"` block entirely. If needed for integration tests, inject via `MOTHERSHIP_TEST_TOKEN` env var that is only set in test fixtures.
- **Also fix:** `:233-241` — remove unauthenticated admin bypass. `:251-258` — remove anonymous fallback (raise 401 instead for non-production non-test).
- **Also fix:** `:270-276` — remove `method == "dev_bypass"` passthrough.
- **Gate:** `Bearer dev-test-token` returns 401 in all environments except isolated test runner.

### P0-2: Remove login credential bypass
- **File:** `src/application/mothership/routers/auth.py:181-222`
- **Action:** Remove `if not settings.is_development:` guard around `validate_production_credentials`. All environments must validate credentials. For dev, use a mock credential store with known test users.
- **Gate:** `POST /auth/login` with invalid credentials returns 401 in development mode.

### P0-3: Add RequiredAuth to all agentic endpoints
- **File:** `src/application/mothership/routers/agentic.py`
- **Lines:** `:149` (get_case), `:188` (enrich_case), `:246` (execute_case), `:323` (execute_case_iterative), `:355` (get_reference_file), `:378` (get_agent_experience)
- **Action:** Add `auth: RequiredAuth` parameter to each endpoint function signature.
- **Also fix:** `:327` — change `max_iterations: int = 3` to `max_iterations: int = Query(default=3, ge=1, le=10)`.
- **Gate:** All `/agentic/*` endpoints return 401 without valid Bearer token.

### P0-4: Remove role escalation via metadata
- **File:** `src/application/mothership/security/auth.py:280-286`
- **Action:** Delete the `elif payload.metadata and "role" in payload.metadata:` branch. Role must only come from `payload.role`.
- **Gate:** JWT with `metadata: {"role": "super_admin"}` and no top-level `role` field gets `Role.READER` (default).

### P0-5: Fix sandbox exec fallback
- **File:** `src/grid/skills/sandbox.py`
- **Action (a):** `:402` — Gate `exec()` fallback behind `os.getenv("GRID_ALLOW_INPROCESS_EXEC") == "1"`. Default: return error instead of executing.
- **Action (b):** `:549-551` — Fix `if pattern in violations` to `if pattern in skill_code`.
- **Action (c):** Add AST pre-scan before any `exec()` call (reference: `arena_integration.py` pattern).
- **Gate:** `exec()` path is never reached unless env var is explicitly set. Violation patterns are detected.

### P0-6: Fix MCP code injection
- **File:** `mcp-setup/server/enhanced_tools_mcp_server.py:430-431`
- **Action:** Validate `target` against `^[a-zA-Z0-9_.]+$` before constructing command. Reject with error if invalid.
- **Gate:** `target="os; os.system('id')"` returns validation error, not execution.

---

## P1 — Fix Before Next Release

### P1-1: Unify token revocation on JTI
- **File (a):** `src/grid/auth/token_manager.py:124,145`
- **Action:** Change `f"denylist:{token}"` to `f"denylist:{jti}"` where `jti` is extracted from decoded payload.
- **File (b):** Consider deprecating `grid/auth/token_manager.py` in favor of `mothership/security/jwt.py` as single JWT authority.
- **Gate:** Revoked token's JTI is the cache key, not the raw token string.

### P1-2: Check revocation during token refresh
- **File:** `src/application/mothership/security/jwt.py:404-425`
- **Action:** After `self.verify_token(refresh_token, expected_type="refresh")`, call `get_token_validator().validate_token(payload.model_dump())` before issuing new access token.
- **Gate:** Revoked refresh token returns 401 on `/auth/refresh`.

### P1-3: Add iss/aud claims to JWT
- **File (create):** `src/application/mothership/security/jwt.py:253-258`
- **Action:** Add `"iss": "grid-mothership"` and `"aud": "mothership-api"` to payload dict.
- **File (validate):** `src/application/mothership/security/jwt.py:356-402`
- **Action:** Pass `issuer="grid-mothership"` and `audience="mothership-api"` to `jwt.decode()`.
- **Gate:** JWT from a different issuer is rejected.

### P1-4: Fail-closed revocation check
- **File:** `src/application/mothership/security/token_revocation.py:92-97`
- **Action:** Change `return False` to `return True` in the except block (treat unknown status as revoked).
- **Gate:** Redis outage causes token rejection, not acceptance.

### P1-5: Wire InputSanitizer to RAG endpoints
- **File:** `src/application/mothership/routers/rag_streaming.py`
- **Action (a):** Add `auth: RequiredAuth` or at minimum `_: RateLimited` to `:84` (query/stream) and `:218` (query/batch).
- **Action (b):** Call `InputSanitizer.sanitize_text_full()` on `request.query` before dispatching to engine.
- **Gate:** RAG endpoints require auth. Known injection patterns are stripped.

### P1-6: ChromaDB allow_reset=False
- **File:** `src/tools/rag/vector_store/chromadb_store.py:39-40`
- **Action:** Change `allow_reset=True` to `allow_reset=os.getenv("GRID_CHROMA_ALLOW_RESET", "false").lower() == "true"`.
- **Gate:** Default ChromaDB config rejects reset requests.

### P1-7: Parameterize Databricks timeout
- **File:** `src/tools/rag/vector_store/databricks_store.py:532`
- **Action:** Replace f-string interpolation with `int(self._query_timeout)` bounded to `[1, 300]` before string insertion. Better: use a parameterized form if the driver supports it.
- **Gate:** Non-integer timeout value raises ValueError, not SQL injection.

### P1-8: Remove python-jose from stale requirements
- **File (a):** `arena_api/requirements.txt:11`
- **File (b):** `docs/requirements.txt:22`
- **Action:** Remove `python-jose[cryptography]` lines. Replace with `PyJWT[crypto]>=2.8.0` if JWT is still needed in those contexts.
- **Gate:** `pip-audit` clean across all requirements files.

---

## P2 — Fix in Sprint

### P2-1: Generic error responses
- **Files:** `routers/agentic.py:146,243,320,353`, `routers/rag_streaming.py:314`, `grid/auth/middleware.py:46`
- **Action:** Replace `str(e)` in HTTPException detail with generic message + correlation ID. Log full error server-side.

### P2-2: Restrict MCP search_code regex
- **File:** `src/grid/mcp/mastermind_server.py:538`
- **Action:** Either reject user-supplied regex (use literal string matching) or use `regex` library with `timeout` parameter. Validate `file_pattern` against allowlist.

### P2-3: Validate git refs
- **File:** `src/grid/mcp/multi_git_server.py:358,328`
- **Action:** Validate `ref` against `^[a-zA-Z0-9._/\-]+$`. Add `--` separator where applicable.

### P2-4: Redis-backed rate limiting and lockout
- **Files:** `dependencies.py:510`, `credential_validation.py:58`
- **Action:** Gate production to require Redis. Persist rate limit and lockout state in shared cache.

### P2-5: Remove unsafe-eval from safety CSP
- **File:** `safety/api/security_headers.py:58`
- **Action:** Remove `'unsafe-eval'` from `script-src`.

### P2-6: Make CI security checks blocking
- **File:** `.github/workflows/ci.yml:119,156`
- **Action:** Remove `continue-on-error: true` from security job. Run on every PR.

### P2-7: Investigate BLOCKER_DISABLED
- **File:** `.github/workflows/ci.yml:53`
- **Action:** Document what it disables. Add at least one CI job with blockers enabled.

### P2-8: Pin GitHub Actions to SHAs
- **File:** `.github/workflows/ci.yml:72` and all workflow files
- **Action:** Replace `@v6` etc. with full SHA digests.

### P2-9: Replace PyPDF2
- **File:** `pyproject.toml:66`
- **Action:** Replace `pypdf2>=3.0.0` with `pypdf>=3.0.0`.

### P2-10: Validate Databricks table names
- **File:** `databricks_store.py` constructor
- **Action:** Validate `chunk_table` against `^[a-zA-Z0-9_.]+$` at init time.

### P2-11: MCP debug logger cleanup
- **File:** `mcp-setup/server/enhanced_tools_mcp_server.py:56-73`
- **Action:** Remove `_debug_log` calls and the `# region agent log` block.

### P2-12: Cap Ollama prompt length
- **File:** `src/tools/rag/llm.py:42`
- **Action:** Add `if len(prompt) > 32768: raise ValueError("Prompt too long")` before subprocess call.
