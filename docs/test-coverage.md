# Test Coverage Documentation

## Overview

The project's automated test suite now achieves:

- **Total coverage:** **84.02%**
- **Test command:**
  ```bash
  pytest tests/ --cov=src
  ```
- Coverage is enforced via `--cov=src` and a threshold of **80%** (configured in CI).

The tests cover unit and integration behavior across API, Core, CLI, Database, and Plugins.

---

## How to Run Tests Locally

From the project root:

```bash
# Standard test run with coverage
pytest tests/ --cov=src

# View missing lines in the terminal
pytest tests/ --cov=src --cov-report=term-missing

# Generate HTML coverage report
pytest tests/ --cov=src --cov-report=html
# Then open htmlcov/index.html in a browser
```

---

## Coverage by Layer

### API

- **Modules:**
  - `src/api/main.py` – **100%**
  - `src/api/routes.py` – **76%**
  - `src/api/routers.py` – **85%**
  - `src/api/middleware.py` – **91%**
  - `src/api/server.py` – **72%**

- **Key tests:**
  - `tests/integration/api/test_health.py`
    - `/health` happy-path + CORS headers.
  - `tests/integration/api/test_inject.py`
    - `/inject` schema validation and success path.
  - `tests/integration/api/test_metrics.py`
    - `/metrics` response structure.
  - `tests/integration/api/test_middleware_and_dependencies.py`
    - `get_current_db_session` dependency.
  - `tests/integration/api/test_users_router.py`
    - Full CRUD flow for `/users` (create, get, list, update, delete).
  - `tests/unit/api/test_middleware.py`
    - `RequestLoggingMiddleware`, `SecurityHeadersMiddleware`, `CORSMiddleware`.
  - `tests/unit/api/test_server.py`
    - `create_app()` factory and root `/` endpoint.

### Core

- **Modules:**
  - `src/core/config.py` – **100%**
  - `src/core/dependency_injection.py` – **97%**
  - `src/core/application.py` – **71%**
  - `src/core/security.py` – **77%**

- **Key tests:**
  - `tests/unit/core/test_security.py`
    - Password hashing/verification (with mocked `pwd_context`).
    - JWT token creation, decoding, invalid/expired token handling.
  - `tests/unit/test_config.py`
    - Default settings, environment flags, and derived properties.
  - `tests/unit/test_dependency_injection.py`
    - Container and service registration behavior.

### CLI

- **Module:**
  - `src/cli/main.py` – **73%**

- **Key tests:** `tests/unit/cli/test_cli.py`
  - `status` – prints application metadata.
  - `lint` – invokes `black`, `isort`, `flake8`, `mypy` (via mocked `subprocess.run`).
  - `test` – runs pytest with and without coverage flags.
  - `migrate` – calls `run_migrations` via `asyncio.run` (mocked).
  - `create_project` – creates project skeleton (README, requirements, `src/`, etc.) in a temp directory.

### Database

- **Modules:**
  - `src/database/models.py` – **100%**
  - `src/database/session.py` – **74%**
  - `src/database/migrations.py` – **77%**

- **Key tests:**
  - `tests/integration/api/test_users_router.py`
    - Exercises `User` model via live CRUD on a SQLite test DB.
  - `tests/unit/database/test_migrations.py`
    - `run_migrations()` and `rollback_migration()` executed using a dummy engine/connection to avoid real SQL side effects.

### Plugins

- **Modules:**
  - `src/plugins/articulation.py` – **100%**
  - `src/plugins/physics.py` – **95%**

- **Key tests:** `tests/unit/plugins/test_plugins.py`
  - `ArticulationPlugin` state transitions (`Input → Ring → Output → Idle`) verified via a recording `EventBus`.
  - `PhysicsPlugin` behavior in lumped and diffusive modes:
    - Heat injection via input events.
    - Auto model switching and manual model change events.
    - Emission of `HeatUpdatedEvent` with expected data types (scalar vs grid).

---

## Test Fixtures & Infrastructure

Defined in `tests/conftest.py`:

- **App & DI fixtures:**
  - `test_settings`, `container`, `service_collection`, `app`, `async_app`.
- **Async event loop:**
  - Custom `event_loop` fixture (deprecated style; acceptable for now, but consider updating for future Python versions).
- **API and DB:**
  - `settings` – overrides env vars (`SECURITY__SECRET_KEY`, `DATABASE__URL`, etc.).
  - `engine` – **file-based** SQLite (`sqlite:///./test.db`) with `Base.metadata.create_all/drop_all`.
  - `db_session` – scoped SQLAlchemy session with rollback.
  - `client` – `TestClient` with `get_db` dependency overridden to use `db_session`.
- **CLI:**
  - `cli_runner` – Click `CliRunner`.

---

## Known Gaps & Future Improvements

The following modules are below full coverage but acceptable for the current target:

- `src/api/server.py` (~72%) – some lifespan and exception-handler branches.
- `src/cli/main.py` (~73%) – remaining paths in `serve`, `shell`, and error branches.
- `src/core/application.py` (~71%) – complex lifecycle paths.
- `src/database/migrations.py` (~77%) – some rollback and error branches.

If you raise the coverage threshold in the future (e.g. 85–90%), focus new tests on:

1. Exception and error-handling branches in:
   - `server.py`, `application.py`, `migrations.py`.
2. Failure paths in CLI commands (e.g. non-zero exits when tools/migrations fail).

---

## Continuous Integration

The coverage threshold is enforced in the test suite:

```bash
pytest tests/ --cov=src --cov-fail-under=80

Notes on running subsets of tests locally
---------------------------------------

When you run a small subset of tests (for example a single unit test file), coverage is measured across the whole `src/` tree. That means many files will be reported as "untested" when you only exercise a small slice of code — lowering the overall coverage percentage.

Because `pytest.ini` includes `--cov-fail-under=30`, running individual test files may hit a coverage-fail check even though the full test suite easily passes.

Options to avoid unexpected fail-under when debugging locally:

- Use the included helper script for PowerShell (Windows):
  ```pwsh
  ./scripts/run_unit_tests.ps1 # runs unit tests with fail-under=0
  ```

- Override the fail-under for a single run directly on the pytest command line (example):
  ```pwsh
  pytest tests/unit/test_pattern_engine_matching.py --cov-fail-under=0
  ```

- Prefer running the full test suite when verifying coverage enforcement, or make the CI pipeline pass `--cov-fail-under` explicitly (keep strict enforcement in CI while allowing flexible local workflows).

```

This ensures that any PR reducing coverage below 80% will fail CI checks.
