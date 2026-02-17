# Up Next — Auth & Deployment Hardening

> Session: 2026-02-13
> Branch: `feature/test-suite-overhaul` (parent) · `main` (GRID submodule)

---

## Completed This Session

### New Modules (GRID Submodule)

| File | Purpose | Tests |
|------|---------|-------|
| `mothership/security/password_policy.py` | Password strength validation (0-4 scoring, 12-char min, common-pw dict, context-aware) | 25 pass |
| `mothership/security/audit_events.py` | Structured security event emission (14 event types, INFO/WARNING routing) | 10 pass |
| `mothership/routers/auth.py` → `/register` | Registration endpoint with password policy + audit events + rate limiting | — |
| `tests/api/test_password_policy.py` | Strength validation, boundary conditions, enforcement, context-aware | 25 pass |
| `tests/api/test_audit_events.py` | Event types, log levels, structured metadata | 10 pass |

### Modified Files (GRID Submodule)

- `mothership/security/__init__.py` — exports `validate_password_strength`, `enforce_password_policy`, `PasswordPolicyError`, `SecurityEventType`, `emit_security_event`
- `mothership/routers/auth.py` — added `RegisterRequest`/`RegisterResponse` models + `/register` endpoint

### Parent Repo Changes

- `.vscode/tasks.json` — "Daily: Verify the Wall" → `group.kind: "build"` (Ctrl+Shift+B)
- `.vscode/extensions.json` — added `bierner.markdown-mermaid`
- `Makefile` — format target: black → ruff format + ruff check --fix
- `src/grid/core/` — `database.py`, `password_policy.py`, `config.py` (PostgresDsn fix, PASSWORD_MIN_LENGTH, PASSWORD_COMPLEXITY_SCORE)
- `src/grid/core/security.py` — argon2 hashing, DB-backed `authenticate_user`
- `src/grid/api/routers/auth.py` — rate-limited `/token`, full `/register` with password policy
- `src/grid/api/limiter.py` — slowapi rate limiter
- `src/grid/crud/user.py` — CRUD operations for User model
- `src/grid/schemas/user.py` — Pydantic v2 schemas (UserBase, UserCreate, User, Token, TokenData)
- `src/grid/security/environment.py` — LOG_LEVEL=None default fix
- `tests/utils/path_manager.py` — input validation + atomic path ops
- `tests/integration/test_auth_flow.py` — registration, login, weak-password, duplicate-email tests
- `tests/verify_fixes.py` — env settings + path manager verification
- `requirements/security.txt` — zxcvbn-python, slowapi, email-validator, argon2-cffi, psycopg2-binary
- `docs/guides/CURSOR_IDE_GAP_ANALYSIS_REPORT.md` — refreshed gap analysis (14 gaps)
- `docs/guides/IDE_SETUP_VERIFICATION.md` — corrected task labels + formatting

---

## Up Next (Priority Order)

### P0 — Critical (Before Next Deploy)

- [ ] **Alembic migrations**: Create initial User table migration with indexes on `username` (unique) and `email` (unique)
- [ ] **Environment variable validation**: Add startup check that `MOTHERSHIP_SECRET_KEY`, `DATABASE_URL` are set before app boots in production
- [ ] **Rollback playbook**: Document rollback steps for auth deployment (revert migration, feature flag off)

### P1 — High (This Sprint)

- [ ] **Token expiry reduction**: Reduce `ACCESS_TOKEN_EXPIRE_MINUTES` from 8 days → 30 min (current default in JWTManager is 30 min; `config.py` Settings still has `60*24*8`)
- [ ] **Password history table**: Store last N password hashes to prevent reuse
- [ ] **CSRF protection**: Add CSRF middleware for cookie-based sessions (if applicable)
- [ ] **Secret rotation strategy**: Document key rotation procedure for `MOTHERSHIP_SECRET_KEY`

### P2 — Medium (Next Sprint)

- [ ] **Concurrent registration test**: Async test for race condition on duplicate username
- [ ] **Load test `/auth/login`**: k6 or locust script, target < 200ms p99 at 100 RPS
- [ ] **Failed login monitoring**: Alert on > 50 failed logins/min (Prometheus + alertmanager)
- [ ] **Pre-commit hooks at repo root**: Add root `.pre-commit-config.yaml` with ruff, mypy

### P3 — Low (Backlog)

- [ ] **Account email verification**: Background task to send verification email on registration
- [ ] **OAuth2 / SSO integration**: Social login providers
- [ ] **Password reset flow**: Forgot-password → email → reset-token → new-password
- [ ] **Audit log persistence**: Write `emit_security_event` records to DB table (not just logs)

---

## Test Status

```
test_password_policy.py  — 25 passed (0.11s)
test_audit_events.py     — 10 passed (0.06s)
test_auth_jwt.py         — SKIP (pre-existing import error: grid.skills.execution_tracker)
```

---

## Commit Plan

```
# GRID submodule
cd work/GRID
git add -A
git commit -m "feat(auth): password policy, audit events, registration endpoint"
git push origin main

# Parent repo
cd ../..
git add -A
git commit -m "feat: auth hardening — password policy, rate limiting, IDE config fixes"
git push origin feature/test-suite-overhaul
```
