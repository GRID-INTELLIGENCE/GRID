import os
import shutil
import subprocess
import sys
import uuid
import base64
import hashlib
import hmac
import json
import types
from datetime import UTC, datetime
from pathlib import Path

import pytest

# Ensure pytest temp roots stay inside the workspace (needed before sessionstart).
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PYTEST_TEMP_ROOT = _PROJECT_ROOT / ".pytest_tmp_root"
_PYTEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(_PYTEST_TEMP_ROOT))


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _install_jwt_test_shim() -> None:
    try:
        import jwt  # noqa: F401

        return
    except ImportError:
        pass

    jwt_module = types.ModuleType("jwt")
    exceptions_module = types.ModuleType("jwt.exceptions")

    class InvalidTokenError(Exception):
        pass

    def encode(payload: dict[str, object], key: str, algorithm: str = "HS256", **_: object) -> str:
        if algorithm != "HS256":
            raise ValueError(f"Unsupported JWT algorithm without PyJWT: {algorithm}")

        header = {"alg": algorithm, "typ": "JWT"}
        header_segment = _base64url_encode(json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8"))
        payload_segment = _base64url_encode(
            json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        )
        signing_input = f"{header_segment}.{payload_segment}"
        signature = hmac.new(key.encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        return f"{signing_input}.{_base64url_encode(signature)}"

    def decode(
        token: str,
        key: str | None = None,
        algorithms: list[str] | None = None,
        options: dict[str, object] | None = None,
        **_: object,
    ) -> dict[str, object]:
        selected_algorithms = algorithms or ["HS256"]
        if len(selected_algorithms) != 1 or selected_algorithms[0] != "HS256":
            raise ValueError(f"Unsupported JWT algorithm without PyJWT: {selected_algorithms}")

        verify_signature = True
        verify_exp = True
        if options is not None:
            verify_signature = bool(options.get("verify_signature", True))
            verify_exp = bool(options.get("verify_exp", True))

        try:
            header_segment, payload_segment, signature_segment = token.split(".")
            header = json.loads(_base64url_decode(header_segment).decode("utf-8"))
            if header.get("alg") != "HS256":
                raise InvalidTokenError("Algorithm mismatch")

            if verify_signature:
                if key is None:
                    raise InvalidTokenError("Missing secret key")
                signing_input = f"{header_segment}.{payload_segment}"
                expected_signature = hmac.new(
                    key.encode("utf-8"),
                    signing_input.encode("ascii"),
                    hashlib.sha256,
                ).digest()
                actual_signature = _base64url_decode(signature_segment)
                if not hmac.compare_digest(expected_signature, actual_signature):
                    raise InvalidTokenError("Signature verification failed")

            payload = json.loads(_base64url_decode(payload_segment).decode("utf-8"))
            exp = payload.get("exp")
            if verify_exp and exp is not None and float(exp) < datetime.now(UTC).timestamp():
                raise InvalidTokenError("Signature has expired")
            return payload
        except ValueError as exc:
            raise InvalidTokenError("Malformed token") from exc
        except (TypeError, json.JSONDecodeError) as exc:
            raise InvalidTokenError("Invalid token payload") from exc

    jwt_module.encode = encode
    jwt_module.decode = decode
    jwt_module.InvalidTokenError = InvalidTokenError
    jwt_module.exceptions = exceptions_module
    exceptions_module.InvalidTokenError = InvalidTokenError

    sys.modules["jwt"] = jwt_module
    sys.modules["jwt.exceptions"] = exceptions_module


_install_jwt_test_shim()


def pytest_configure(config):
    """Re-ensure src is at sys.path[0] after any plugin/pytest path changes."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    src = os.path.join(root, "src")
    for path in [src, root]:
        while path in sys.path:
            sys.path.remove(path)
    sys.path.insert(0, src)
    if root not in sys.path:
        sys.path.append(root)

    # Windows sandbox environments can fail during xdist temp-root setup.
    # Force single-process execution there for deterministic collection/runs.
    if os.name == "nt" and hasattr(config.option, "numprocesses"):
        if getattr(config.option, "numprocesses", None):
            config.option.numprocesses = 0


# ---------------------------------------------------------------------------
# Auto-marker: apply markers based on directory structure so selective runs
# work even when individual tests are not explicitly decorated.
# Usage: uv run pytest -m unit          (only fast unit tests)
#        uv run pytest -m safety        (safety enforcement)
#        uv run pytest -m "not slow"    (skip slow tests)
#        uv run pytest --lf             (last-failed only — incremental)
#        uv run pytest -n auto          (parallel via xdist)
# ---------------------------------------------------------------------------
_DIR_MARKER_MAP = {
    "unit": "unit",
    "integration": "integration",
    "api": "api",
    "e2e": "integration",
    "chaos": "slow",
    "smoke": "smoke",
    "skills": "unit",
    "redteam": "redteam",
    "performance": "slow",
    "load": "slow",
}


def pytest_collection_modifyitems(config, items):
    """Auto-apply markers based on test file path."""
    for item in items:
        rel = str(item.fspath)
        # Safety subtree
        if "safety" + os.sep + "tests" in rel:
            item.add_marker(pytest.mark.safety)
        # Boundaries subtree
        if "boundaries" + os.sep + "tests" in rel:
            item.add_marker(pytest.mark.safety)
        # Directory-based markers
        for dirname, marker_name in _DIR_MARKER_MAP.items():
            if os.sep + dirname + os.sep in rel:
                item.add_marker(getattr(pytest.mark, marker_name))
                break


# Additional paths needed for legacy modules (appended so src stays first)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LOTS_OUTER_DIR = os.path.join(ROOT_DIR, "light_of_the_seven")
ARCHIVE_DIR = os.path.join(ROOT_DIR, "archive")
LEGACY_SRC_DIR = os.path.join(ARCHIVE_DIR, "legacy_src")
LEGACY_DIR = os.path.join(ARCHIVE_DIR, "legacy")
ARCHIVE_LOTS_DIR = os.path.join(ARCHIVE_DIR, "light_of_the_seven")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")
CONTEXT_DIR = os.path.join(ROOT_DIR, "src", "cognitive", "context")

# Insert additional paths AFTER src (index 1+) so src remains first
additional_paths = [
    LOTS_OUTER_DIR,
    LEGACY_SRC_DIR,
    LEGACY_DIR,
    ARCHIVE_LOTS_DIR,
    SCRIPTS_DIR,
    ROOT_DIR,
    CONTEXT_DIR,
]

for path in additional_paths:
    if os.path.exists(path) and path not in sys.path:
        sys.path.append(path)


@pytest.fixture(scope="session", autouse=True)
def setup_env():
    """Set test environment variables without triggering DB connections.

    CRITICAL: Do NOT call reload_settings() here as it can trigger database
    connection attempts that may hang or timeout. Settings will be loaded
    lazily when needed with the test environment variables set.
    """
    import os

    os.environ["MOTHERSHIP_ENVIRONMENT"] = "test"
    # Generate secure test key: python -c "import secrets; print(secrets.token_urlsafe(32))"
    os.environ["MOTHERSHIP_SECRET_KEY"] = os.environ.get(
        "MOTHERSHIP_SECRET_KEY", "test-secret-key-at-least-32-chars-long-placeholder"
    )
    os.environ["MOTHERSHIP_RATE_LIMIT_ENABLED"] = "false"

    # CRITICAL: Disable database connections in test mode to prevent hangs
    # Use in-memory SQLite: each pytest-xdist worker gets its own DB, avoiding
    # file locking when running with -n auto. For file-based SQLite, use worker_id.
    os.environ["MOTHERSHIP_DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["MOTHERSHIP_USE_DATABRICKS"] = "false"
    os.environ["MOTHERSHIP_REDIS_ENABLED"] = "false"
    os.environ.setdefault("GRID_TEST_TMPDIR", os.path.join(ROOT_DIR, ".test_tmp"))
    os.makedirs(os.environ["GRID_TEST_TMPDIR"], exist_ok=True)
    os.environ.setdefault("GRID_SANDBOX_TMPDIR", os.path.join(ROOT_DIR, ".test_tmp", "sandbox"))
    os.makedirs(os.environ["GRID_SANDBOX_TMPDIR"], exist_ok=True)

    # Avoid loading chromadb in tests (chromadb.config.Settings + pydantic v1 fails on Python 3.13+)
    os.environ["RAG_VECTOR_STORE_PROVIDER"] = os.environ.get("RAG_VECTOR_STORE_PROVIDER", "in_memory")

    # Bypass Redis safety checks in test mode (middleware fails closed without Redis)
    os.environ["SAFETY_BYPASS_REDIS"] = "true"

    # DON'T call reload_settings() here - it can trigger DB connections
    # Settings will be loaded lazily when needed with test environment


@pytest.fixture
def tmp_path() -> Path:
    """Workspace-scoped temporary path fixture.

    Uses a deterministic writable directory inside the repo instead of pytest's
    default temp root. This avoids intermittent Windows ACL errors around
    ``.../pytest-of-<user>`` in constrained/sandboxed environments.
    """
    base = Path(os.environ.get("GRID_TEST_TMPDIR", os.path.join(ROOT_DIR, ".test_tmp")))
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"case_{uuid.uuid4().hex}"
    path.mkdir(parents=False, exist_ok=False)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)


@pytest.fixture(autouse=True)
def reset_services():
    """Reset singleton services before and after each test for isolation."""
    os.environ["MOTHERSHIP_ENVIRONMENT"] = "test"
    os.environ["MOTHERSHIP_DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["MOTHERSHIP_USE_DATABRICKS"] = "false"
    os.environ["MOTHERSHIP_REDIS_ENABLED"] = "false"
    try:
        from application.mothership.config import reload_settings

        reload_settings()
    except ImportError:
        pass
    try:
        from application.mothership.security.jwt import reset_jwt_manager

        reset_jwt_manager()
    except ImportError:
        pass
    try:
        from application.resonance.api.dependencies import reset_resonance_service

        if reset_resonance_service:
            reset_resonance_service()
    except ImportError:
        pass
    yield
    os.environ["MOTHERSHIP_ENVIRONMENT"] = "test"
    os.environ["MOTHERSHIP_DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["MOTHERSHIP_USE_DATABRICKS"] = "false"
    os.environ["MOTHERSHIP_REDIS_ENABLED"] = "false"
    try:
        from application.mothership.config import reload_settings

        reload_settings()
    except ImportError:
        pass
    try:
        from application.mothership.security.jwt import reset_jwt_manager

        reset_jwt_manager()
    except ImportError:
        pass
    try:
        from application.resonance.api.dependencies import reset_resonance_service

        if reset_resonance_service:
            reset_resonance_service()
    except ImportError:
        pass


from unittest.mock import AsyncMock, Mock


@pytest.fixture(scope="session")
def ollama_models_available(ollama_available):
    """Check if required Ollama models are available.

    Returns a set of available model names, or empty set if Ollama unavailable.
    """
    if not ollama_available:
        return set()

    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Parse model names from output (format: "NAME\tID\tSIZE\tMODIFIED")
            models = set()
            for line in result.stdout.strip().split("\n"):
                if line and not line.startswith("NAME"):
                    model_name = line.split()[0]
                    models.add(model_name)
            return models
    except Exception:
        pass
    return set()


# ---------------------------------------------------------------------------
# Mock Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_event_bus():
    """Shared mock for EventBus."""
    bus = Mock()
    bus.publish = AsyncMock()
    bus.subscribe = Mock()
    bus.get_history = Mock(return_value=[])
    return bus


@pytest.fixture
def mock_cockpit_service():
    """Shared mock for CockpitService."""
    service = Mock()
    service.state = Mock()
    service.state.components = {}
    service.state.alerts = {}
    service.state.started_at = None
    service.state.uptime_seconds = 0.0
    service.execute_task = AsyncMock(return_value={"status": "completed"})
    return service


@pytest.fixture
def mock_rag_engine():
    """Shared mock for RAG Engine."""
    engine = Mock()
    engine.query = AsyncMock(return_value={"answer": "Mocked answer", "sources": []})
    engine.index = AsyncMock(return_value={"status": "success"})
    return engine


@pytest.fixture
def mock_agentic_system(mock_event_bus):
    """Shared mock for AgenticSystem."""
    system = Mock()
    system.event_bus = mock_event_bus
    system.process_case = AsyncMock(return_value={"case_id": "test_case", "status": "completed"})
    system.get_case = AsyncMock(return_value={"case_id": "test_case", "status": "completed"})
    return system


# ---------------------------------------------------------------------------
# Service Availability Fixtures
# These fixtures check if external services are available and skip tests
# gracefully if they are not. Using session scope so checks run once per session.
# ---------------------------------------------------------------------------


def _check_ollama_available() -> bool:
    """Check if Ollama service is running on localhost:11434."""
    try:
        import httpx

        response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


def _check_api_server_available(port: int = 8000) -> bool:
    """Check if API server is running on localhost:<port>."""
    try:
        import httpx

        response = httpx.get(f"http://localhost:{port}/health", timeout=2.0)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def ollama_available():
    """Session-scoped check for Ollama availability.

    Returns True if Ollama is running on localhost:11434, False otherwise.
    Use with @pytest.mark.skipif(not ollama_available) to skip tests.
    """
    return _check_ollama_available()


@pytest.fixture(scope="session")
def api_server_available():
    """Session-scoped check for API server availability on port 8000.

    Returns True if API server health endpoint returns 200, False otherwise.
    Use with @pytest.mark.skipif to skip tests that require the API server.
    """
    return _check_api_server_available(8000)


@pytest.fixture(scope="session")
def resonance_server_available():
    """Session-scoped check for Resonance service on port 8080."""
    return _check_api_server_available(8080)
