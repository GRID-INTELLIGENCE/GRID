# AGENTS.md

## Cursor Cloud specific instructions

### Services overview

| Service | Port | How to start |
|---------|------|-------------|
| Mothership API (FastAPI) | 8080 | `uv run python -m application.mothership.main` |
| Frontend (Vite dev) | 5173 | `npm run dev:renderer` (from `frontend/`) |

Standard commands for lint, test, and build are documented in the `README.md`, `Makefile`, and `CONTRIBUTING.md`.

### Non-obvious startup caveats

- **Python 3.13 required.** The project pins `>=3.13,<3.14`. The deadsnakes PPA provides it on Ubuntu (`python3.13`).
- **uv is the only supported Python package manager.** Do not use `pip install` directly. Use `uv sync --group dev --group test` to install all dev/test dependencies.
- **Frontend uses npm** (not pnpm/yarn). Lockfile is `frontend/package-lock.json`.
- **Safety middleware blocks POST requests without Redis.** Set `SAFETY_BYPASS_REDIS=true` to bypass Redis health checks in local dev.
- **Parasite Guard blocks requests with missing/unusual headers.** Set `PARASITE_GUARD=0` to disable it in local dev. Without this, most non-health endpoints return `_parasite_meta` refusal responses.
- **Minimum env vars for the API server:**
  ```
  MOTHERSHIP_SECRET_KEY=ci_test_secret_key_change_me
  MOTHERSHIP_DATABASE_URL=sqlite+aiosqlite:///./data/dev.db
  RAG_VECTOR_STORE_PROVIDER=in_memory
  GRID_ENVIRONMENT=development
  MOTHERSHIP_REDIS_ENABLED=false
  STRIPE_ENABLED=false
  MOTHERSHIP_USE_DATABRICKS=false
  MOTHERSHIP_RATE_LIMIT_ENABLED=false
  SAFETY_BYPASS_REDIS=true
  PARASITE_GUARD=0
  ```
- **CI env vars for tests** (also set in `.github/workflows/ci.yml`):
  ```
  MOTHERSHIP_SECRET_KEY=ci_test_secret_key_change_me
  MOTHERSHIP_DATABASE_URL=sqlite:///:memory:
  RAG_VECTOR_STORE_PROVIDER=in_memory
  GRID_ENVIRONMENT=testing
  ```
- **`UV_TORCH_BACKEND=cpu`** can be set during `uv sync` to avoid downloading ~2GB CUDA packages (CI does this).
- **Swagger UI** at `/docs` may render blank due to Content Security Policy headers from the security middleware. The OpenAPI spec at `/openapi.json` works fine.
- The `uv` binary installs to `~/.local/bin`; ensure that directory is on `PATH`.
