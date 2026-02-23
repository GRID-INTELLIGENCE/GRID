"""Ollama connectivity smoke test — skips gracefully when Ollama is not running."""

import pytest

httpx = pytest.importorskip("httpx", reason="httpx not installed")

OLLAMA_URL = "http://localhost:11434/api/tags"


def _ollama_reachable() -> bool:
    """Check if Ollama is reachable with a short timeout."""
    try:
        import httpx

        r = httpx.get(OLLAMA_URL, timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


# Module-level skip: skip entire module if Ollama is not running
# This prevents tests from even being collected if Ollama is unavailable
_ollama_available = _ollama_reachable()
if not _ollama_available:
    pytest.skip("Ollama service not available at localhost:11434", allow_module_level=True)


@pytest.fixture(scope="session")
def ollama_available():
    """Session-scoped check for Ollama availability."""
    return _ollama_available


class TestOllama:
    """Tests that require Ollama to be running."""

    @pytest.mark.timeout(15)  # Prevent hanging on network issues
    def test_ollama_tags(self):
        """Test that Ollama API is accessible."""
        r = httpx.get(OLLAMA_URL, timeout=10.0)
        assert r.status_code == 200
