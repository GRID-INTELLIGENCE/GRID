import base64
import hashlib
import hmac
import json
import os
import shutil
import subprocess
import sys
import types
import uuid
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

import pytest

# Ensure pytest temp roots stay inside the workspace (needed before sessionstart).
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_PYTEST_TEMP_ROOT = _PROJECT_ROOT / ".pytest_tmp_root"
_PYTEST_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("PYTEST_DEBUG_TEMPROOT", str(_PYTEST_TEMP_ROOT))


def _prime_test_environment() -> None:
    """Set critical test env vars before app modules are imported."""
    os.environ["MOTHERSHIP_ENVIRONMENT"] = "test"
    os.environ.setdefault("MOTHERSHIP_SECRET_KEY", "test-secret-key-at-least-32-chars-long-placeholder")
    os.environ["MOTHERSHIP_RATE_LIMIT_ENABLED"] = "false"
    os.environ["MOTHERSHIP_DATABASE_URL"] = "sqlite:///:memory:"
    os.environ["MOTHERSHIP_USE_DATABRICKS"] = "false"
    os.environ["MOTHERSHIP_REDIS_ENABLED"] = "false"
    os.environ.setdefault("GRID_TEST_TMPDIR", os.path.join(_PROJECT_ROOT, ".test_tmp"))
    os.makedirs(os.environ["GRID_TEST_TMPDIR"], exist_ok=True)
    os.environ.setdefault("GRID_SANDBOX_TMPDIR", os.path.join(_PROJECT_ROOT, ".test_tmp", "sandbox"))
    os.makedirs(os.environ["GRID_SANDBOX_TMPDIR"], exist_ok=True)
    os.environ["RAG_VECTOR_STORE_PROVIDER"] = os.environ.get("RAG_VECTOR_STORE_PROVIDER", "in_memory")
    os.environ["RAG_EMBEDDING_PROVIDER"] = os.environ.get("RAG_EMBEDDING_PROVIDER", "simple")
    os.environ["RAG_USE_RERANKER"] = "false"
    os.environ["RAG_USE_HYBRID"] = "false"
    os.environ["RAG_USE_INTELLIGENT_RAG"] = "false"
    os.environ["SAFETY_BYPASS_REDIS"] = "true"
    # CRIT-1: Allow dev-test-token in tests only (never in production)
    os.environ.setdefault("ENABLE_DEV_TOKEN", "1")
    # CRIT-2: Allow dev login bypass in tests for auth flow tests
    os.environ.setdefault("ALLOW_DEV_LOGIN_BYPASS", "1")
    os.environ.setdefault("MOTHERSHIP_ADMISSION_GATE_ENABLED", "false")


_prime_test_environment()


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
        payload_segment = _base64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
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

    jwt_module.encode = encode  # type: ignore[attr-defined]
    jwt_module.decode = decode  # type: ignore[attr-defined]
    jwt_module.InvalidTokenError = InvalidTokenError  # type: ignore[attr-defined]
    jwt_module.exceptions = exceptions_module  # type: ignore[attr-defined]
    exceptions_module.InvalidTokenError = InvalidTokenError  # type: ignore[attr-defined]

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

    _prime_test_environment()

    # DON'T call reload_settings() here - it can trigger DB connections
    # Settings will be loaded lazily when needed with test environment


@pytest.fixture
def tmp_path() -> Generator[Path]:
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
    _prime_test_environment()
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
    # Reset global singletons (circuit breaker, metrics, accountability, rate limiter)
    try:
        from tests.utils.reset_helpers import reset_all_singletons

        reset_all_singletons()
    except ImportError:
        pass
    yield
    _prime_test_environment()
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
    # Reset global singletons (circuit breaker, metrics, accountability, rate limiter)
    try:
        from tests.utils.reset_helpers import reset_all_singletons

        reset_all_singletons()
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


# ---------------------------------------------------------------------------
# Mock Service Fixtures for External Dependencies
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def mock_ollama_client():
    """Mock Ollama client for testing."""
    from unittest.mock import MagicMock, Mock

    mock_client = Mock()

    # Mock embeddings response
    def mock_embeddings(model, prompt):
        return {"embedding": [0.1] * 768}  # Return 768-dim vector

    # Mock list models response
    def mock_list():
        return {"models": [{"name": "nomic-embed-text:latest"}]}

    # Mock generate response
    def mock_generate(model, prompt, **kwargs):
        return {"response": f"Mock response for: {prompt[:50]}..."}

    mock_client.embeddings = mock_embeddings
    mock_client.list = mock_list
    mock_client.generate = mock_generate

    return mock_client


@pytest.fixture(scope="session")
def mock_chromadb_client():
    """Mock ChromaDB client for testing."""
    from unittest.mock import MagicMock, Mock

    # Mock collection
    mock_collection = Mock()
    mock_collection.count.return_value = 0
    mock_collection.add.return_value = None
    mock_collection.get.return_value = {"ids": [], "documents": [], "metadatas": []}
    mock_collection.delete.return_value = None
    mock_collection.update.return_value = None

    def mock_query(query_embeddings, n_results=10, **kwargs):
        # Return mock query results with correct list-of-lists shape
        return {
            "ids": [["doc1", "doc2"][:n_results]],
            "documents": [["Document 1", "Document 2"][:n_results]],
            "metadatas": [[{"source": "test1"}, {"source": "test2"}][:n_results]],
            "distances": [[0.1, 0.2][:n_results]],
        }

    mock_collection.query = mock_query

    # Mock client
    mock_client = Mock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_client.delete_collection.return_value = None
    mock_client.list_collections.return_value = []

    return mock_client, mock_collection


@pytest.fixture(scope="session")
def mock_redis_client():
    """Mock Redis client for testing."""
    from unittest.mock import MagicMock, Mock

    mock_client = Mock()

    # Mock basic operations
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.exists.return_value = 0
    mock_client.expire.return_value = True

    # Mock pub/sub
    mock_pubsub = Mock()
    mock_pubsub.subscribe.return_value = None
    mock_pubsub.unsubscribe.return_value = None
    mock_pubsub.listen.return_value = []  # Empty iterator
    mock_client.pubsub.return_value = mock_pubsub

    # Mock pipeline
    mock_pipeline = Mock()
    mock_pipeline.execute.return_value = []
    mock_client.pipeline.return_value = mock_pipeline

    # Mock connection
    mock_client.ping.return_value = True
    mock_client.close.return_value = None

    return mock_client
